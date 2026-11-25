"""The linter's two whole-file rules: the append-only gate and the canonical form.

The append-only gate compares the current witness with the committed
baseline. A published fact never changes and a published key or member never
disappears; retirement is by `deprecated`, which may be set and never cleared.
Additions pass, reported as notes so --check can insist the baseline records
them, but only under the current version, and never while it is ratified. The
one other fact allowed to change is the identity class of a key the baseline
holds as UNDER_REVIEW: that class exists to be decided. An ENUMERATED key's
values may grow at the end, each new value an addition; a value removed is
refused by name, and a value moved changes the list, which is refused.

The canonical form is the one text each spec document may have: two-space
indent, a trailing newline, UTF-8 written as itself, and every object's fields
in schema order (model.*_FIELDS). Order that carries meaning is kept: a
document's top level (its `// MARK` comments head the section after them),
members in document order (the C++ enumeration order), and version groups in
version order.
"""
# RTM AppendOnly_01, AppendOnly_02, Lint_01, Lint_05, Enumerated_01
from __future__ import annotations

import json

from . import model
from .model import UNDER_REVIEW, Json, Spec
from .witness import witness


def _show(value: Json) -> str:
    # Sorted JSON, so a message names a changed object the same way every run.
    return json.dumps(value, sort_keys=True)


def _may_change(field: str, old: Json, new: Json) -> bool:
    return (field == "identity" and old == UNDER_REVIEW) or (field == "deprecated" and old is False and new is True)


def _listed(where: str, old: Json, new: Json, ratified: bool) -> tuple[list[str], list[str]]:
    """(problems, additions) for a key's listed values: kept in place, appended at the end."""
    if not isinstance(old, list) or not isinstance(new, list):
        return ([] if old == new else [f"CHANGED {where}: {_show(old)} -> {_show(new)}"]), []
    removed = [f"REMOVED {where}.{v}" for v in old if v not in new]
    if removed:
        return removed, []
    if new[:len(old)] != old:
        return [f"CHANGED {where}: {_show(old)} -> {_show(new)}"], []
    added = [f"ADDED {where}.{v}" for v in new[len(old):]]
    return ([f"{a}, under a ratified version" for a in added], []) if ratified else ([], added)


def append_only(baseline: Json, spec: Spec) -> tuple[list[str], list[str]]:
    """(problems, additions), each a list of messages naming the fact."""
    current = witness(spec)
    if not isinstance(baseline, dict):
        return [f"witness: expected an object, found {baseline!r}"], []
    version = str(spec.version)
    problems: list[str] = []
    additions: list[str] = []
    for section in sorted(set(baseline) | set(current)):
        old_section = baseline.get(section, {})
        new_section = current.get(section, {})
        if not isinstance(old_section, dict) or not isinstance(new_section, dict):
            problems.append(f"witness.{section}: expected an object")
            continue
        for name in sorted(set(old_section) | set(new_section)):
            where = f"{section}.{name}"
            if name not in new_section:
                problems.append(f"REMOVED {where}")
                continue
            old, new = old_section.get(name), new_section[name]
            if name not in old_section:
                since = new.get("since") if isinstance(new, dict) else new
                if since != version:
                    problems.append(f"ADDED {where} under {since}, older than the current version {version}")
                elif spec.status == model.RATIFIED:
                    problems.append(f"ADDED {where} under {version}, which is ratified")
                else:
                    additions.append(f"ADDED {where}")
                continue
            if not isinstance(old, dict) or not isinstance(new, dict):
                if old != new:
                    problems.append(f"CHANGED {where}: {_show(old)} -> {_show(new)}")
                continue
            for field in sorted(set(old) | set(new)):
                if field not in old:
                    additions.append(f"ADDED {where}.{field}")
                elif field not in new:
                    problems.append(f"REMOVED {where}.{field}")
                elif field == "values":
                    listed = _listed(f"{where}.values", old[field], new[field], spec.status == model.RATIFIED)
                    problems += listed[0]
                    additions += listed[1]
                elif old[field] != new[field] and not _may_change(field, old[field], new[field]):
                    problems.append(f"CHANGED {where}.{field}: {_show(old[field])} -> {_show(new[field])}")
    return problems, additions


def _ordered(obj: Json, fields: tuple[str, ...]) -> dict[str, Json]:
    assert isinstance(obj, dict)
    comments = {k: v for k, v in obj.items() if k.startswith("//")}
    return comments | {f: obj[f] for f in fields if f in obj}


def _version_key(label: str) -> tuple[int, int]:
    major, minor = label.split(".")
    return int(major), int(minor)


def _key_entry(entry: Json) -> dict[str, Json]:
    out = _ordered(entry, model.KEY_FIELDS)
    if isinstance(out["dicom"], dict):
        dicom = _ordered(out["dicom"], model.DICOM_FIELDS)
        if isinstance(dicom["sequence"], dict):
            dicom["sequence"] = _ordered(dicom["sequence"], model.SEQUENCE_FIELDS)
        verified = dicom["verified"]
        assert isinstance(verified, list)
        dicom["verified"] = [_ordered(v, model.VERIFIED_FIELDS) for v in verified]
        out["dicom"] = dicom
    if isinstance(out["phi_flag"], dict):
        out["phi_flag"] = _ordered(out["phi_flag"], model.PHI_FLAG_FIELDS)
    if isinstance(out.get("values"), dict):
        values = out["values"]
        assert isinstance(values, dict)
        out["values"] = {term: _ordered(v, model.LISTED_VALUE_FIELDS) for term, v in values.items()}
    return out


def _member(section: str, entry: Json) -> dict[str, Json]:
    if section == "keys":
        return _key_entry(entry)
    if section == "value_representations":
        out = _ordered(entry, model.VR_FIELDS)
        verified = out["verified"]
        assert isinstance(verified, list)
        out["verified"] = [_ordered(v, model.VERIFIED_FIELDS) for v in verified]
        return out
    fields = model.VALUE_TYPE_FIELDS if section == "value_types" else model.IDENTITY_CLASS_FIELDS
    return _ordered(entry, fields)


def canonical(file: str, doc: Json) -> str:
    """The canonical text of a spec document that model.parse accepted."""
    assert isinstance(doc, dict)
    out = dict(doc)
    if file == model.HEADER_FILE:
        out["version"] = _ordered(doc["version"], model.VERSION_FIELDS)
        revisions = doc["revisions"]
        assert isinstance(revisions, list)
        out["revisions"] = [_ordered(r, model.REVISION_FIELDS) for r in revisions]
    else:
        for section in model.KEYS_DOCUMENT_FIELDS:
            ordered = _ordered(doc[section], model.SECTION_FIELDS)
            versions = ordered["i2s_version"]
            assert isinstance(versions, dict)
            groups: dict[str, Json] = {}
            for label in sorted(versions, key=_version_key):
                members = versions[label]
                assert isinstance(members, dict)
                groups[label] = {name: _member(section, entry) for name, entry in members.items()}
            ordered["i2s_version"] = groups
            out[section] = ordered
    return json.dumps(out, indent=2, ensure_ascii=False) + "\n"
