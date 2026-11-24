"""Orchestration and the generator's only file I/O.

Load the two spec documents and the committed witness, parse, run the
append-only gate, then generate, check or refresh. Every generated file is
rendered in memory into `outputs` (relative path -> text) before anything is
written, so --check and the writer share one list of outputs.
"""
# RTM UniqueNames_01, AppendOnly_01
from __future__ import annotations

import json
import re
import sys
from enum import StrEnum
from pathlib import Path

from .emit.cpp import emit_header
from .emit.docs import emit_document
from .model import Json, Spec, SpecError, parse
from .validate import append_only
from .witness import canonical, witness, witness_hash

WITNESS = Path("tests") / "witness" / "witness.json"
_HASH = re.compile(r"Witness: sha256 ([0-9a-f]{64})")


class Mode(StrEnum):
    GENERATE = "generate"
    VALIDATE = "validate"
    CHECK = "check"
    REFRESH_WITNESS = "refresh-witness"


def _refuse_duplicates(pairs: list[tuple[str, Json]]) -> dict[str, Json]:
    # json.loads keeps the last of two equal names in an object, which would
    # silently drop a key defined twice.
    out: dict[str, Json] = {}
    for name, value in pairs:
        if name in out:
            raise SpecError(f"duplicate name {name!r}")
        out[name] = value
    return out


def load_json(path: Path) -> Json:
    try:
        value: Json = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_refuse_duplicates)
    except SpecError as error:
        raise SpecError(f"{path}: {error}") from error
    return value


def _outputs(spec: Spec, digest: str, out_dir: Path, docs_dir: Path) -> dict[Path, str]:
    return {
        out_dir / "I2S_Keys.hpp": emit_header(spec, digest),
        docs_dir / "i2s_specification.md": emit_document(spec, digest),
    }


def _check(outputs: dict[Path, str], digest: str) -> int:
    stale = 0
    for path in outputs:
        found = _HASH.search(path.read_text(encoding="utf-8")) if path.is_file() else None
        if found is None or found.group(1) != digest:
            print(f"generator: {path} was not generated from the current spec", file=sys.stderr)
            stale += 1
    if stale:
        return 1
    print("generator: the witness and every output are current")
    return 0


def run(root: Path, out_dir: Path, docs_dir: Path, mode: Mode = Mode.GENERATE) -> int:
    """Exit status: 0 success, 1 a rule broken or an output stale."""
    witness_path = root / WITNESS
    try:
        spec = parse(load_json(root / "spec" / "i2s_header.json"), load_json(root / "spec" / "i2s_keys.json"))
        baseline = load_json(witness_path) if witness_path.is_file() else None
    except (OSError, SpecError) as error:
        print(f"generator: {error}", file=sys.stderr)
        return 1
    current = witness(spec)
    if baseline is None and mode is not Mode.REFRESH_WITNESS:
        print(f"generator: {witness_path} is missing; record it with --refresh-witness", file=sys.stderr)
        return 1
    problems, additions = append_only(baseline or {}, current)
    for problem in problems:
        print(f"generator: {problem}", file=sys.stderr)
    if problems:
        return 1

    if mode is Mode.REFRESH_WITNESS:
        witness_path.parent.mkdir(parents=True, exist_ok=True)
        witness_path.write_text(canonical(current), encoding="utf-8")
        print(f"generator: recorded {len(additions)} addition(s) in {witness_path}")
        return 0
    for addition in additions:
        print(f"generator: note: {addition} is not in {witness_path} yet", file=sys.stderr)
    if mode is Mode.VALIDATE:
        print("generator: the specification is valid and append-only")
        return 0

    digest = witness_hash(spec)
    outputs = _outputs(spec, digest, out_dir, docs_dir)
    if mode is Mode.CHECK:
        if additions:
            print("generator: the witness is stale; record additions with --refresh-witness", file=sys.stderr)
            return 1
        return _check(outputs, digest)
    for path, text in outputs.items():
        # Unchanged files keep their modification time, so CMake rebuilds nothing.
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    print(f"generator: {len(spec.keys)} key(s) into {out_dir} and {docs_dir}")
    return 0
