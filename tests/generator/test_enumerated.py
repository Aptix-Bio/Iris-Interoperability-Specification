"""ENUMERATED keys and the scan-time keys that use them (Decision_18).

An ENUMERATED key lists its values, each a CS term that is also a C++
identifier, so the generated header can name each one. The generator refuses
an ENUMERATED key without values, values on any other key, a value that is not
such a term, a value listed twice, and, under the append-only gate, a value
removed or moved; a value appended at the end passes as an addition."""
# RTM Enumerated_01, ScanTimeKeys_01
from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path

import pytest

from generator import pipeline
from generator.model import Json, SpecError, parse
from generator.validate import append_only

ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / "spec" / "i2s_header.json"
KEYS = ROOT / "spec" / "i2s_keys.json"
WITNESS = ROOT / "tests" / "witness" / "witness.json"


def _obj(value: Json) -> dict[str, Json]:
    assert isinstance(value, dict)
    return value


def _key(keys: Json, name: str) -> dict[str, Json]:
    return _obj(_obj(_obj(_obj(_obj(keys)["keys"])["i2s_version"])["0.1"])[name])


def _refused(edit: Callable[[Json], None], message: str) -> None:
    keys = copy.deepcopy(pipeline.load_json(KEYS))
    edit(keys)
    with pytest.raises(SpecError) as raised:
        parse(pipeline.load_json(HEADER), keys)
    assert message in str(raised.value)


def _gate(edit: Callable[[Json], None]) -> tuple[list[str], list[str]]:
    keys = copy.deepcopy(pipeline.load_json(KEYS))
    edit(keys)
    return append_only(pipeline.load_json(WITNESS), parse(pipeline.load_json(HEADER), keys))


def _set_values(name: str, values: Json) -> Callable[[Json], None]:
    return lambda keys: _key(keys, name).__setitem__("values", values)


def test_an_enumerated_key_without_values_is_refused() -> None:
    _refused(_set_values("FocusMethod", None),
             "keys.FocusMethod.values: an ENUMERATED key lists its values")


def test_values_on_a_key_that_is_not_enumerated_are_refused() -> None:
    _refused(_set_values("Manufacturer", {"LEICA": {"description": "Leica."}}),
             "keys.Manufacturer.values: only an ENUMERATED key lists values; Manufacturer is TEXT")


@pytest.mark.parametrize("term", ["auto", "AUTO FOCUS", "2D", "A_VERY_LONG_TERM_X"])
def test_a_value_that_is_not_a_cs_term_naming_a_cpp_enumerator_is_refused(term: str) -> None:
    _refused(_set_values("FocusMethod", {term: {"description": "A focus method."}}),
             f"keys.FocusMethod.values: {term!r} is not")


def test_a_value_listed_twice_is_refused(tmp_path: Path) -> None:
    text = KEYS.read_text(encoding="utf-8")
    manual = text.index('"MANUAL": {')
    doubled = text[:manual] + '"AUTO": {"description": "Autofocus."},\n' + text[manual:]
    path = tmp_path / "i2s_keys.json"
    path.write_text(doubled, encoding="utf-8")
    with pytest.raises(SpecError, match="duplicate name 'AUTO'"):
        pipeline.load_json(path)


def test_a_removed_value_is_refused() -> None:
    def edit(keys: Json) -> None:
        del _obj(_key(keys, "FocusMethod")["values"])["MANUAL"]
    problems, _ = _gate(edit)
    assert problems == ["REMOVED keys.FocusMethod.values.MANUAL"]


def test_a_moved_value_is_refused() -> None:
    def edit(keys: Json) -> None:
        values = _obj(_key(keys, "FocusMethod")["values"])
        _key(keys, "FocusMethod")["values"] = {"MANUAL": values["MANUAL"], "AUTO": values["AUTO"]}
    problems, _ = _gate(edit)
    assert problems == ['CHANGED keys.FocusMethod.values: ["AUTO", "MANUAL"] -> ["MANUAL", "AUTO"]']


def test_a_value_appended_passes_as_an_addition() -> None:
    def edit(keys: Json) -> None:
        _obj(_key(keys, "FocusMethod")["values"])["SEMI_AUTO"] = {"description": "An example value."}
    assert _gate(edit) == ([], ["ADDED keys.FocusMethod.values.SEMI_AUTO"])


def test_the_scan_time_keys_carry_their_dicom_attributes() -> None:
    spec = parse(pipeline.load_json(HEADER), pipeline.load_json(KEYS))
    found = {k.name: k for k in spec.keys}
    expected = {
        "BurnedInAnnotation": ("(0028,0301)", "CS", "BOOLEAN", None),
        "ObjectiveLensNumericalAperture": ("(0048,0113)", "DS", "DECIMAL", "(0048,0105)"),
        "FocusMethod": ("(0048,0011)", "CS", "ENUMERATED", None),
        "ExtendedDepthOfField": ("(0048,0012)", "CS", "BOOLEAN", None),
    }
    for name, (tag, vr, value_type, sequence) in expected.items():
        key = found[name]
        assert key.dicom is not None, name
        assert (str(key.dicom.tag), key.vr, key.value_type, key.identity, key.multiplicity.text) == (
            tag, vr, value_type, "NONE", "1"), name
        assert (None if key.dicom.sequence is None else str(key.dicom.sequence.tag)) == sequence, name
    assert [v.name for v in found["FocusMethod"].values] == ["AUTO", "MANUAL"]
    assert all(found[n].values == () for n in found if n != "FocusMethod")


def test_the_witness_records_each_keys_values() -> None:
    recorded = json.loads(WITNESS.read_text(encoding="utf-8"))
    assert recorded["keys"]["FocusMethod"]["values"] == ["AUTO", "MANUAL"]
    assert recorded["keys"]["Manufacturer"]["values"] is None


def test_the_document_lists_each_enumerated_keys_values(tmp_path: Path) -> None:
    assert pipeline.run(ROOT, tmp_path / "source", tmp_path / "docs") == 0
    sections = (tmp_path / "docs" / "key_sections.adoc").read_text(encoding="utf-8")
    focus = sections[sections.index("=== FocusMethod"):]
    line = next(line for line in focus.splitlines() if line.startswith("Values::"))
    assert line.index("`AUTO`") < line.index("`MANUAL`")
