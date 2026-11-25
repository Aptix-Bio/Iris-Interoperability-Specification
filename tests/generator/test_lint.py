"""The linter: `python -m generator --validate` over the current specification.

Each test breaks one rule in a copy of the committed spec and checks that the
failure names the file, the field and the offending value. Format is checked
on files in a temporary repository root; the other rules on in-memory copies.
"""
# RTM Lint_01, Lint_02, Lint_03, Lint_04, Lint_05, Lint_06, AppendOnly_02
from __future__ import annotations

import copy
import json
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from generator import pipeline
from generator.model import Json, SpecError, parse
from generator.validate import append_only

ROOT = Path(__file__).resolve().parents[2]
HEADER = "spec/i2s_header.json"
KEYS = "spec/i2s_keys.json"
WITNESS = "tests/witness/witness.json"


def _load(rel: str) -> dict[str, Json]:
    value = pipeline.load_json(ROOT / rel)
    assert isinstance(value, dict)
    return value


def _obj(value: Json) -> dict[str, Json]:
    assert isinstance(value, dict)
    return value


def _key(keys: dict[str, Json], name: str, version: str = "0.1") -> dict[str, Json]:
    return _obj(_obj(_obj(_obj(keys["keys"])["i2s_version"])[version])[name])


def _member(keys: dict[str, Json], section: str, name: str) -> dict[str, Json]:
    return _obj(_obj(_obj(_obj(keys[section])["i2s_version"])["0.1"])[name])


def _revisions(header: dict[str, Json]) -> list[Json]:
    revisions = header["revisions"]
    assert isinstance(revisions, list)
    return revisions


def _refused(header: dict[str, Json], keys: dict[str, Json], message: str) -> None:
    with pytest.raises(SpecError) as raised:
        parse(header, keys)
    assert message in str(raised.value)


def _edited_keys(edit: Callable[[dict[str, Json]], None]) -> tuple[dict[str, Json], dict[str, Json]]:
    keys = copy.deepcopy(_load(KEYS))
    edit(keys)
    return _load(HEADER), keys


def _root_copy(tmp_path: Path) -> Path:
    for rel in (HEADER, KEYS, WITNESS):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)
    return tmp_path


# --- Format -----------------------------------------------------------------

def test_committed_files_are_canonical(tmp_path: Path) -> None:
    root = _root_copy(tmp_path)
    assert pipeline.run(root, root / "out", root / "docs", pipeline.Mode.VALIDATE) == 0


def test_reindented_file_fails_and_fix_restores_it(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _root_copy(tmp_path)
    original = (root / KEYS).read_text(encoding="utf-8")
    (root / KEYS).write_text(json.dumps(json.loads(original), indent=4), encoding="utf-8")
    assert pipeline.run(root, root / "out", root / "docs", pipeline.Mode.VALIDATE) == 1
    assert f"{KEYS}: not in canonical form at line 2" in capsys.readouterr().err
    assert pipeline.run(root, root / "out", root / "docs", pipeline.Mode.FIX) == 0
    assert (root / KEYS).read_text(encoding="utf-8") == original


def test_missing_trailing_newline_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _root_copy(tmp_path)
    (root / HEADER).write_text((root / HEADER).read_text(encoding="utf-8").rstrip("\n"), encoding="utf-8")
    assert pipeline.run(root, root / "out", root / "docs", pipeline.Mode.VALIDATE) == 1
    assert f"{HEADER}: not in canonical form" in capsys.readouterr().err


def test_fields_out_of_schema_order_fail(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _root_copy(tmp_path)
    keys = _load(KEYS)
    entry = _key(keys, "Manufacturer")
    reordered = dict(sorted(entry.items()))
    _obj(_obj(_obj(keys["keys"])["i2s_version"])["0.1"])["Manufacturer"] = reordered
    (root / KEYS).write_text(json.dumps(keys, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    assert pipeline.run(root, root / "out", root / "docs", pipeline.Mode.VALIDATE) == 1
    assert f"{KEYS}: not in canonical form" in capsys.readouterr().err


# --- Names ------------------------------------------------------------------

def _renamed(old: str, new: str) -> Callable[[dict[str, Json]], None]:
    def edit(keys: dict[str, Json]) -> None:
        members = _obj(_obj(_obj(keys["keys"])["i2s_version"])["0.1"])
        members[new] = members.pop(old)
    return edit


def test_key_name_not_pascal_case_is_refused() -> None:
    _refused(*_edited_keys(_renamed("Manufacturer", "manufacturer_name")),
             f"{KEYS}: keys.manufacturer_name: 'manufacturer_name' is not a PascalCase name")


def test_key_name_outside_ascii_is_refused() -> None:
    _refused(*_edited_keys(_renamed("Manufacturer", "Manufacturér")),
             f"{KEYS}: keys.Manufacturér: 'Manufacturér' is not a PascalCase name")


def test_short_name_shared_by_two_keys_is_refused() -> None:
    _refused(*_edited_keys(lambda k: _key(k, "ManufacturerModelName").__setitem__("short_name", "DII")),
             f"{KEYS}: keys.ManufacturerModelName.short_name: short name 'DII' of ManufacturerModelName")


# --- DICOM ------------------------------------------------------------------

def _dicom(keys: dict[str, Json], name: str) -> dict[str, Json]:
    return _obj(_key(keys, name)["dicom"])


def _verified(keys: dict[str, Json], name: str) -> dict[str, Json]:
    entries = _dicom(keys, name)["verified"]
    assert isinstance(entries, list)
    return _obj(entries[0])


def test_malformed_tag_is_refused() -> None:
    _refused(*_edited_keys(lambda k: _dicom(k, "Manufacturer").__setitem__("tag", "0008,70")),
             f"{KEYS}: keys.Manufacturer.dicom.tag: '0008,70' is not a DICOM tag")


def test_unknown_vr_is_refused() -> None:
    _refused(*_edited_keys(lambda k: _dicom(k, "Manufacturer").__setitem__("vr", "XX")),
             f"{KEYS}: keys.Manufacturer.dicom.vr: 'XX' is not a DICOM value representation")


def test_verified_without_iso_date_is_refused() -> None:
    _refused(*_edited_keys(lambda k: _verified(k, "Manufacturer").__setitem__("read", "24 Nov 2026")),
             f"{KEYS}: keys.Manufacturer.dicom.verified[0].read: '24 Nov 2026' is not an ISO 8601 date")


def test_verified_without_url_is_refused() -> None:
    _refused(*_edited_keys(lambda k: _verified(k, "Manufacturer").__setitem__("url", "PS3.6")),
             f"{KEYS}: keys.Manufacturer.dicom.verified[0].url: 'PS3.6' is not an https URL")


# --- Times ------------------------------------------------------------------

def test_date_time_without_offset_is_refused() -> None:
    # A DATE_TIME is DICOM's DT, and I2S requires DT's optional UTC offset.
    _refused(*_edited_keys(lambda k: _member(k, "value_representations", "DT").__setitem__("example", "20261124103000")),
             f"{KEYS}: value_representations.DT.example: '20261124103000' is not a DT: it has no UTC offset")


def test_date_time_not_a_calendar_time_is_refused() -> None:
    _refused(*_edited_keys(lambda k: _member(k, "value_representations", "DT").__setitem__("example", "20260230103000+0000")),
             f"{KEYS}: value_representations.DT.example: '20260230103000+0000' is not a DT")


def test_date_time_offset_out_of_range_is_refused() -> None:
    _refused(*_edited_keys(lambda k: _member(k, "value_representations", "DT").__setitem__("example", "20261124103000+1500")),
             f"{KEYS}: value_representations.DT.example: '20261124103000+1500' is not a DT: its UTC offset +1500 is outside -1200 to +1400")


def test_example_of_another_vr_is_checked() -> None:
    _refused(*_edited_keys(lambda k: _member(k, "value_representations", "CS").__setitem__("example", "yes")),
             f"{KEYS}: value_representations.CS.example: 'yes' is not a CS")


def test_revision_date_not_iso_is_refused() -> None:
    header = copy.deepcopy(_load(HEADER))
    _obj(_revisions(header)[0])["date"] = "2026-13-01"
    _refused(header, _load(KEYS), f"{HEADER}: header.revisions[0].date: '2026-13-01' is not an ISO 8601 date")


# --- Versions ---------------------------------------------------------------

def _revision(version: str, status: str) -> Json:
    return {"version": version, "status": status, "date": "2026-11-24",
            "authors": ["Example Author"], "summary": "Example revision."}


def test_header_version_must_be_the_newest_revision() -> None:
    header = copy.deepcopy(_load(HEADER))
    header["version"] = {"major": 0, "minor": 2}
    _refused(header, _load(KEYS), f"{HEADER}: header.version: 0.2 is not the newest revision, 0.1")


def test_revisions_with_a_gap_are_refused() -> None:
    header = copy.deepcopy(_load(HEADER))
    _obj(_revisions(header)[0])["status"] = "ratified"
    _revisions(header).append(_revision("0.3", "draft"))
    header["version"] = {"major": 0, "minor": 3}
    _refused(header, _load(KEYS), f"{HEADER}: header.revisions[1].version: 0.3 does not follow 0.1")


def test_repeated_revision_is_refused() -> None:
    header = copy.deepcopy(_load(HEADER))
    _obj(_revisions(header)[0])["status"] = "ratified"
    _revisions(header).append(_revision("0.1", "draft"))
    _refused(header, _load(KEYS), f"{HEADER}: header.revisions[1].version: 0.1 does not follow 0.1")


def test_only_the_newest_revision_may_be_a_draft() -> None:
    header = copy.deepcopy(_load(HEADER))
    _revisions(header).append(_revision("0.2", "draft"))
    header["version"] = {"major": 0, "minor": 2}
    _refused(header, _load(KEYS), f"{HEADER}: header.revisions[0].status: only the newest revision may be 'draft'")


def test_version_group_without_a_revision_is_refused() -> None:
    def edit(keys: dict[str, Json]) -> None:
        versions = _obj(_obj(keys["keys"])["i2s_version"])
        versions["0.0"] = {"ScannerFieldOfView": copy.deepcopy(_key(keys, "Manufacturer"))}
    _refused(*_edited_keys(edit), f"{KEYS}: keys.i2s_version.0.0: no revision 0.0 in {HEADER}")


def _version_02() -> tuple[dict[str, Json], dict[str, Json]]:
    header = copy.deepcopy(_load(HEADER))
    _obj(_revisions(header)[0])["status"] = "ratified"
    _revisions(header).append(_revision("0.2", "draft"))
    header["version"] = {"major": 0, "minor": 2}
    header["status"] = "draft"
    return header, copy.deepcopy(_load(KEYS))


def test_key_added_under_an_older_version_is_refused() -> None:
    header, keys = _version_02()
    members = _obj(_obj(_obj(keys["keys"])["i2s_version"])["0.1"])
    members["ScannerFieldOfView"] = copy.deepcopy(_key(keys, "Manufacturer"))
    problems, _ = append_only(_load(WITNESS), parse(header, keys))
    assert problems == ["ADDED keys.ScannerFieldOfView under 0.1, older than the current version 0.2"]


def test_key_added_under_the_current_version_passes() -> None:
    header, keys = _version_02()
    _obj(_obj(keys["keys"])["i2s_version"])["0.2"] = {"ScannerFieldOfView": copy.deepcopy(_key(keys, "Manufacturer"))}
    problems, additions = append_only(_load(WITNESS), parse(header, keys))
    assert problems == [] and additions == ["ADDED keys.ScannerFieldOfView"]


# --- Nothing dropped --------------------------------------------------------

def _gate(edit: Callable[[dict[str, Json]], None], baseline: Json | None = None) -> list[str]:
    header, keys = _edited_keys(edit)
    return append_only(baseline if baseline is not None else _load(WITNESS), parse(header, keys))[0]


def test_key_moved_between_version_groups_is_refused() -> None:
    header, keys = _version_02()
    versions = _obj(_obj(keys["keys"])["i2s_version"])
    versions["0.2"] = {"Manufacturer": _obj(versions["0.1"]).pop("Manufacturer")}
    problems, _ = append_only(_load(WITNESS), parse(header, keys))
    assert problems == ['CHANGED keys.Manufacturer.since: "0.1" -> "0.2"']


def test_short_name_removed_is_refused() -> None:
    assert _gate(lambda k: _key(k, "DigitalImageIdentifier").__setitem__("short_name", None)) == [
        'CHANGED keys.DigitalImageIdentifier.short_name: "DII" -> null']


def test_phi_flag_removed_is_refused() -> None:
    assert _gate(lambda k: _key(k, "DigitalImageIdentifier").__setitem__("phi_flag", None)) == [
        'CHANGED keys.DigitalImageIdentifier.phi_flag: '
        '{"absent_means_phi": true, "key": "DigitalImageIdentifierIsPHI"} -> null']


def test_deprecating_a_key_passes() -> None:
    assert _gate(lambda k: _key(k, "SoftwareVersions").__setitem__("deprecated", "Example retirement.")) == []


def test_un_deprecating_a_key_is_refused() -> None:
    baseline = copy.deepcopy(_load(WITNESS))
    _obj(_obj(baseline["keys"])["SoftwareVersions"])["deprecated"] = True
    assert _gate(lambda k: None, baseline) == ["CHANGED keys.SoftwareVersions.deprecated: true -> false"]


# --- Consistency ------------------------------------------------------------

def test_identity_note_without_under_review_is_refused() -> None:
    _refused(*_edited_keys(lambda k: _key(k, "Manufacturer").__setitem__("identity_note", "Why.")),
             f"{KEYS}: keys.Manufacturer.identity_note: required exactly when identity is UNDER_REVIEW")


def test_under_review_without_identity_note_is_refused() -> None:
    _refused(*_edited_keys(lambda k: _key(k, "DeviceSerialNumber").__setitem__("identity_note", None)),
             f"{KEYS}: keys.DeviceSerialNumber.identity_note: required exactly when identity is UNDER_REVIEW")


@pytest.mark.parametrize("multiplicity", ["0", "n", "1-0", "2-1", "1-", "one"])
def test_multiplicity_outside_the_allowed_forms_is_refused(multiplicity: str) -> None:
    _refused(*_edited_keys(lambda k: _key(k, "Manufacturer").__setitem__("multiplicity", multiplicity)),
             f"{KEYS}: keys.Manufacturer.multiplicity: '{multiplicity}'")
