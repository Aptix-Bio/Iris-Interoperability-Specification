"""The witness: every fact of the specification a consumer depends on.

A key's name, version, short name, DICOM counterpart, value type, multiplicity,
identity class and PHI flag (with its absent default) are what a writer puts in a file and a reader looks up, so
each is witnessed. Descriptions, notes and verification sources are not: they
may be clarified without changing what any file means.

The committed copy (tests/witness/witness.json) is the baseline the
append-only gate compares against; witness_hash() goes into every generated
file's banner so --check can tell whether a file came from the current spec.
"""
# RTM AppendOnly_01, PhiFlag_02
from __future__ import annotations

import hashlib
import json

from .model import Json, Spec


def witness(spec: Spec) -> dict[str, Json]:
    keys: dict[str, Json] = {}
    for key in spec.keys:
        dicom: Json = None
        if key.dicom is not None:
            sequence: Json = None
            if key.dicom.sequence is not None:
                sequence = {"keyword": key.dicom.sequence.keyword, "tag": str(key.dicom.sequence.tag)}
            dicom = {"keyword": key.dicom.keyword, "tag": str(key.dicom.tag),
                     "vr": key.dicom.vr, "sequence": sequence}
        keys[key.name] = {
            "since": str(key.since),
            "short_name": key.short_name,
            "dicom": dicom,
            "value_type": key.value_type,
            "multiplicity": key.multiplicity.text,
            "identity": key.identity,
            "phi_flag": None if key.phi_flag is None else {
                "key": key.phi_flag.key, "absent_means_phi": key.phi_flag.absent_means_phi},
        }
    return {
        "value_types": {m.name: str(m.since) for m in spec.value_types},
        "identity_classes": {m.name: str(m.since) for m in spec.identity_classes},
        "keys": keys,
    }


def canonical(facts: Json) -> str:
    """The one text form of a witness: the committed file and the hash use it."""
    return json.dumps(facts, indent=2, sort_keys=True) + "\n"


def witness_hash(spec: Spec) -> str:
    return hashlib.sha256(canonical(witness(spec)).encode("utf-8")).hexdigest()
