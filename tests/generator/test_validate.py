"""The generator refuses a specification that breaks the append-only rule or
names a key twice, naming the offending key. Each test edits an in-memory copy
of the committed spec and checks it against the committed witness."""
# RTM Schema_01, AppendOnly_01, UniqueNames_01, Document_01
from __future__ import annotations

import copy
from pathlib import Path

import pytest

from generator import pipeline
from generator.model import Json, SpecError, parse
from generator.validate import append_only
from generator.witness import witness

ROOT = Path(__file__).resolve().parents[2]


def _documents() -> tuple[Json, Json, Json]:
    return (
        pipeline.load_json(ROOT / "spec" / "i2s_header.json"),
        pipeline.load_json(ROOT / "spec" / "i2s_keys.json"),
        pipeline.load_json(ROOT / "tests" / "witness" / "witness.json"),
    )


def _keys_01(keys: Json) -> dict[str, Json]:
    assert isinstance(keys, dict)
    group = keys["keys"]
    assert isinstance(group, dict)
    versions = group["i2s_version"]
    assert isinstance(versions, dict)
    members = versions["0.1"]
    assert isinstance(members, dict)
    return members


def _gate(header: Json, keys: Json, baseline: Json) -> tuple[list[str], list[str]]:
    return append_only(baseline, witness(parse(header, keys)))


def test_committed_spec_passes() -> None:
    header, keys, baseline = _documents()
    assert _gate(header, keys, baseline) == ([], [])


def test_removed_key_is_rejected() -> None:
    header, keys, baseline = _documents()
    edited = copy.deepcopy(keys)
    del _keys_01(edited)["Manufacturer"]
    problems, _ = _gate(header, edited, baseline)
    assert problems == ["REMOVED keys.Manufacturer"]


def test_retyped_key_is_rejected() -> None:
    header, keys, baseline = _documents()
    edited = copy.deepcopy(keys)
    entry = _keys_01(edited)["Manufacturer"]
    assert isinstance(entry, dict)
    entry["value_type"] = "INTEGER"
    problems, _ = _gate(header, edited, baseline)
    assert problems == ['CHANGED keys.Manufacturer.value_type: "TEXT" -> "INTEGER"']


def test_added_key_passes_as_a_note() -> None:
    header, keys, baseline = _documents()
    edited = copy.deepcopy(keys)
    members = _keys_01(edited)
    members["ScannerFieldOfView"] = copy.deepcopy(members["Manufacturer"])
    problems, additions = _gate(header, edited, baseline)
    assert problems == []
    assert additions == ["ADDED keys.ScannerFieldOfView"]


def test_identity_under_review_may_be_decided() -> None:
    header, keys, baseline = _documents()
    edited = copy.deepcopy(keys)
    entry = _keys_01(edited)["DigitalSlideIdentifier"]
    assert isinstance(entry, dict)
    entry["identity"] = "NONE"
    entry["identity_note"] = None
    assert _gate(header, edited, baseline)[0] == []


def test_duplicate_name_in_one_object_is_rejected(tmp_path: Path) -> None:
    # json.loads keeps the last of two equal names, so a duplicate key would
    # vanish silently without the loader's own check.
    path = tmp_path / "keys.json"
    path.write_text('{"Manufacturer": 1, "Manufacturer": 2}')
    with pytest.raises(SpecError, match="duplicate name 'Manufacturer'"):
        pipeline.load_json(path)


def test_duplicate_name_across_version_groups_is_rejected() -> None:
    header, keys, _ = _documents()
    header_02 = copy.deepcopy(header)
    assert isinstance(header_02, dict)
    header_02["version"] = {"major": 0, "minor": 2}
    edited = copy.deepcopy(keys)
    assert isinstance(edited, dict)
    group = edited["keys"]
    assert isinstance(group, dict)
    versions = group["i2s_version"]
    assert isinstance(versions, dict)
    versions["0.2"] = {"Manufacturer": copy.deepcopy(_keys_01(edited)["Manufacturer"])}
    with pytest.raises(SpecError, match="keys.Manufacturer: defined in 0.1 and 0.2"):
        parse(header_02, edited)


def test_short_name_equal_to_a_key_name_is_rejected() -> None:
    header, keys, _ = _documents()
    edited = copy.deepcopy(keys)
    entry = _keys_01(edited)["DeviceSerialNumber"]
    assert isinstance(entry, dict)
    entry["short_name"] = "Manufacturer"
    with pytest.raises(SpecError, match="short name 'Manufacturer' of DeviceSerialNumber"):
        parse(header, edited)


def test_unknown_value_type_is_rejected() -> None:
    header, keys, _ = _documents()
    edited = copy.deepcopy(keys)
    entry = _keys_01(edited)["Manufacturer"]
    assert isinstance(entry, dict)
    entry["value_type"] = "STRING"
    with pytest.raises(SpecError, match="keys.Manufacturer.value_type: unknown value type 'STRING'"):
        parse(header, edited)


def test_generation_is_deterministic(tmp_path: Path) -> None:
    for run in ("a", "b"):
        assert pipeline.run(ROOT, tmp_path / run / "source", tmp_path / run / "docs") == 0
    first = sorted(p.relative_to(tmp_path / "a") for p in (tmp_path / "a").rglob("*") if p.is_file())
    second = sorted(p.relative_to(tmp_path / "b") for p in (tmp_path / "b").rglob("*") if p.is_file())
    assert first == second and first
    for rel in first:
        assert (tmp_path / "a" / rel).read_bytes() == (tmp_path / "b" / rel).read_bytes()


# RTM PhiFlag_01
def test_phi_flag_must_name_a_boolean_key() -> None:
    header, keys, _ = _documents()
    edited = copy.deepcopy(keys)
    entry = _keys_01(edited)["DigitalSlideIdentifier"]
    assert isinstance(entry, dict)
    entry["phi_flag"] = {"key": "Manufacturer", "absent_means_phi": True}
    with pytest.raises(SpecError, match="keys.DigitalSlideIdentifier.phi_flag: Manufacturer is TEXT, not BOOLEAN"):
        parse(header, edited)


# RTM PhiFlag_01
def test_phi_flag_must_name_a_defined_key() -> None:
    header, keys, _ = _documents()
    edited = copy.deepcopy(keys)
    entry = _keys_01(edited)["DigitalSlideIdentifier"]
    assert isinstance(entry, dict)
    entry["phi_flag"] = {"key": "DSI_is_PHI_typo", "absent_means_phi": True}
    with pytest.raises(SpecError, match="keys.DigitalSlideIdentifier.phi_flag: no key named 'DSI_is_PHI_typo'"):
        parse(header, edited)


# RTM PhiFlag_02
def test_changed_absent_default_is_rejected() -> None:
    header, keys, baseline = _documents()
    edited = copy.deepcopy(keys)
    entry = _keys_01(edited)["DigitalSlideIdentifier"]
    assert isinstance(entry, dict)
    entry["phi_flag"] = {"key": "DigitalSlideIdentifierIsPHI", "absent_means_phi": False}
    problems, _ = _gate(header, edited, baseline)
    assert problems == [
        'CHANGED keys.DigitalSlideIdentifier.phi_flag: '
        '{"absent_means_phi": true, "key": "DigitalSlideIdentifierIsPHI"} -> '
        '{"absent_means_phi": false, "key": "DigitalSlideIdentifierIsPHI"}'
    ]
