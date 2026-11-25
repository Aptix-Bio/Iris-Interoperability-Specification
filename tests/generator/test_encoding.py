"""Every key's value is text encoded as a DICOM value representation (VR).

The spec defines each VR it uses (its length limit and unit, whether it may
hold several values, an example), each value type lists the VRs it may be
written as, and each key names its VR. These tests break one rule each.
"""
# RTM Encoding_01, TypedKeys_01
from __future__ import annotations

import copy
from collections.abc import Callable
from pathlib import Path

import pytest

from generator import pipeline
from generator.model import Json, SpecError, parse

ROOT = Path(__file__).resolve().parents[2]
KEYS = "spec/i2s_keys.json"


def _obj(value: Json) -> dict[str, Json]:
    assert isinstance(value, dict)
    return value


def _section(keys: dict[str, Json], section: str) -> dict[str, Json]:
    return _obj(_obj(_obj(keys[section])["i2s_version"])["0.1"])


def _refused(edit: Callable[[dict[str, Json]], None], message: str) -> None:
    keys = copy.deepcopy(_obj(pipeline.load_json(ROOT / KEYS)))
    edit(keys)
    with pytest.raises(SpecError) as raised:
        parse(pipeline.load_json(ROOT / "spec" / "i2s_header.json"), keys)
    assert message in str(raised.value)


def _set(section: str, name: str, field: str, value: Json) -> Callable[[dict[str, Json]], None]:
    return lambda keys: _obj(_section(keys, section)[name]).__setitem__(field, value)


def test_every_key_states_its_vr() -> None:
    def edit(keys: dict[str, Json]) -> None:
        del _obj(_section(keys, "keys")["Manufacturer"])["vr"]
    _refused(edit, f"{KEYS}: keys.Manufacturer: missing field 'vr'")


def test_a_vr_the_value_type_does_not_allow_is_refused() -> None:
    _refused(_set("keys", "Manufacturer", "vr", "DT"),
             f"{KEYS}: keys.Manufacturer.vr: TEXT is written as SH, LO, ST, LT or UT, not DT")


def test_a_vr_unlike_the_dicom_attribute_is_refused() -> None:
    _refused(_set("keys", "Manufacturer", "vr", "SH"),
             f"{KEYS}: keys.Manufacturer.vr: SH differs from the DICOM attribute's LO")


def test_several_values_under_a_single_valued_vr_are_refused() -> None:
    _refused(_set("keys", "UniqueDeviceIdentifier", "multiplicity", "1-n"),
             f"{KEYS}: keys.UniqueDeviceIdentifier.multiplicity: UT holds a single value")


def test_a_vr_dicom_does_not_define_is_refused() -> None:
    def edit(keys: dict[str, Json]) -> None:
        section = _section(keys, "value_representations")
        section["XX"] = copy.deepcopy(section["LO"])
    _refused(edit, f"{KEYS}: value_representations.XX: 'XX' is not a DICOM value representation")


def test_an_example_longer_than_its_vr_allows_is_refused() -> None:
    _refused(_set("value_representations", "SH", "example", "A" * 17),
             f"{KEYS}: value_representations.SH.example: 17 characters, over SH's 16")


def test_a_backslash_in_a_string_vr_is_refused() -> None:
    _refused(_set("value_representations", "LO", "example", "GT\\\\450"),
             f"{KEYS}: value_representations.LO.example: 'GT\\\\\\\\450' is not a LO: it contains a backslash")


def test_a_key_named_like_the_generated_api_is_refused() -> None:
    def edit(keys: dict[str, Json]) -> None:
        members = _section(keys, "keys")
        members["Attributes"] = members.pop("SoftwareVersions")
    _refused(edit, f"{KEYS}: keys.Attributes: 'Attributes' is a name the generated C++ already uses")


def test_scan_time_is_acquisition_date_time() -> None:
    spec = parse(pipeline.load_json(ROOT / "spec" / "i2s_header.json"), pipeline.load_json(ROOT / KEYS))
    key = next(k for k in spec.keys if k.name == "AcquisitionDateTime")
    assert (key.short_name, key.vr, key.value_type) == ("ScanTime", "DT", "DATE_TIME")
    assert key.dicom is not None and str(key.dicom.tag) == "(0008,002A)"
