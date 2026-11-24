"""The append-only gate: the current witness against the committed baseline.

A published fact never changes and a published key or member never disappears;
retirement is by `deprecated`. Additions pass, reported as notes so --check can
insist the baseline records them. The one fact allowed to change is the
identity class of a key the baseline holds as UNDER_REVIEW: that class exists
to be decided.
"""
# RTM AppendOnly_01
from __future__ import annotations

import json

from .model import UNDER_REVIEW, Json


def _show(value: Json) -> str:
    # Sorted JSON, so a message names a changed object the same way every run.
    return json.dumps(value, sort_keys=True)


def append_only(baseline: Json, current: Json) -> tuple[list[str], list[str]]:
    """(problems, additions), each a list of messages naming the fact."""
    if not isinstance(baseline, dict) or not isinstance(current, dict):
        return [f"witness: expected objects, found {baseline!r} and {current!r}"], []
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
            if name not in old_section:
                additions.append(f"ADDED {where}")
                continue
            old, new = old_section[name], new_section[name]
            if not isinstance(old, dict) or not isinstance(new, dict):
                if old != new:
                    problems.append(f"CHANGED {where}: {_show(old)} -> {_show(new)}")
                continue
            for field in sorted(set(old) | set(new)):
                if field not in old:
                    additions.append(f"ADDED {where}.{field}")
                elif field not in new:
                    problems.append(f"REMOVED {where}.{field}")
                elif old[field] != new[field] and not (field == "identity" and old[field] == UNDER_REVIEW):
                    problems.append(f"CHANGED {where}.{field}: {_show(old[field])} -> {_show(new[field])}")
    return problems, additions
