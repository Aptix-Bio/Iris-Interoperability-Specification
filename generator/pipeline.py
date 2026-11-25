"""Orchestration and the generator's only file I/O.

Load the two spec documents and the committed witness, parse, run the
append-only gate, then generate, check or refresh. Every generated file is
rendered in memory into `outputs` (relative path -> text) before anything is
written, so --check and the writer share one list of outputs.
"""
# RTM UniqueNames_01, AppendOnly_01, SingleHeader_01
from __future__ import annotations

import json
import re
import sys
from enum import StrEnum
from pathlib import Path

from .emit.cpp import SOURCES, emit_header, emit_single_header, emit_vr_examples
from .emit.docs import emit_documents
from .model import HEADER_FILE, KEYS_FILE, Json, Spec, SpecError, parse
from .validate import append_only, canonical
from .witness import witness, witness_hash, witness_text

WITNESS = Path("tests") / "witness" / "witness.json"
_HASH = re.compile(r"Witness: sha256 ([0-9a-f]{64})")


class Mode(StrEnum):
    GENERATE = "generate"
    VALIDATE = "validate"
    CHECK = "check"
    REFRESH_WITNESS = "refresh-witness"
    FIX = "fix"


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


def _outputs(spec: Spec, digest: str, root: Path, out_dir: Path, docs_dir: Path) -> dict[Path, str]:
    sources = {rel: (root / rel).read_text(encoding="utf-8") for rel in SOURCES}
    outputs = {out_dir / "I2S_Keys.hpp": emit_header(spec, digest),
               out_dir / "I2S.hpp": emit_single_header(spec, digest, sources),
               out_dir / "I2S_VrExamples.hpp": emit_vr_examples(spec, digest)}
    for name, text in emit_documents(spec, digest).items():
        outputs[docs_dir / name] = text
    return outputs


# Extensions the generator owns in its output directories. A file with one of
# them that this render does not produce (a renamed output, the Markdown
# document AsciiDoc replaced) would be compiled or published with no source,
# so generation deletes it and --check fails on it. README.md is committed.
_OWNED = frozenset({".hpp", ".adoc", ".md"})


def _orphans(outputs: dict[Path, str]) -> list[Path]:
    expected = {p.resolve() for p in outputs}
    found: list[Path] = []
    for directory in sorted({p.parent for p in outputs}):
        if directory.is_dir():
            found += [p for p in sorted(directory.iterdir())
                      if p.suffix in _OWNED and p.name != "README.md" and p.resolve() not in expected]
    return found


def _check(outputs: dict[Path, str], digest: str) -> int:
    stale = 0
    for orphan in _orphans(outputs):
        print(f"generator: {orphan} is not produced from the current spec", file=sys.stderr)
        stale += 1
    for path, text in outputs.items():
        found = path.read_text(encoding="utf-8") if path.is_file() else ""
        witnessed = _HASH.search(found)
        if witnessed is None or witnessed.group(1) != digest:
            print(f"generator: {path} was not generated from the current spec", file=sys.stderr)
            stale += 1
        elif found != text:
            # I2S.hpp also depends on the sources in include/, which the
            # witness hash does not cover, so the whole text is compared.
            print(f"generator: {path} differs from what the current spec and sources produce", file=sys.stderr)
            stale += 1
    if stale:
        return 1
    print("generator: the witness and every output are current")
    return 0


def _canonical_problems(root: Path, docs: dict[str, Json], fix: bool) -> list[str]:
    """The spec files not in canonical form, or, with fix, rewrites them."""
    problems: list[str] = []
    for rel, doc in docs.items():
        path = root / rel
        text = canonical(rel, doc)
        found = path.read_text(encoding="utf-8")
        if found == text:
            continue
        if fix:
            path.write_text(text, encoding="utf-8")
            print(f"generator: rewrote {rel} in canonical form")
            continue
        line = next(
            (n for n, (a, b) in enumerate(zip(found.splitlines(True), text.splitlines(True)), 1) if a != b),
            min(len(found.splitlines()), len(text.splitlines())) + 1,
        )
        problems.append(f"{rel}: not in canonical form at line {line}; run python -m generator --fix")
    return problems


def run(root: Path, out_dir: Path, docs_dir: Path, mode: Mode = Mode.GENERATE) -> int:
    """Exit status: 0 success, 1 a rule broken or an output stale."""
    witness_path = root / WITNESS
    try:
        docs = {rel: load_json(root / rel) for rel in (HEADER_FILE, KEYS_FILE)}
        spec = parse(docs[HEADER_FILE], docs[KEYS_FILE])
        baseline = load_json(witness_path) if witness_path.is_file() else None
    except (OSError, SpecError) as error:
        print(f"generator: {error}", file=sys.stderr)
        return 1
    if baseline is None and mode is not Mode.REFRESH_WITNESS:
        print(f"generator: {witness_path} is missing; record it with --refresh-witness", file=sys.stderr)
        return 1
    problems, additions = append_only(baseline or {}, spec)
    problems = [f"{KEYS_FILE}: {p}" for p in problems]
    # Format is a lint rule: --validate, --check and --fix apply it, while the
    # configure-time generation does not, so a hand edit still builds.
    if mode in (Mode.VALIDATE, Mode.CHECK, Mode.FIX):
        problems += _canonical_problems(root, docs, mode is Mode.FIX)
    for problem in problems:
        print(f"generator: {problem}", file=sys.stderr)
    if problems:
        return 1

    if mode is Mode.REFRESH_WITNESS:
        witness_path.parent.mkdir(parents=True, exist_ok=True)
        witness_path.write_text(witness_text(witness(spec)), encoding="utf-8")
        print(f"generator: recorded {len(additions)} addition(s) in {witness_path}")
        return 0
    for addition in additions:
        print(f"generator: note: {addition} is not in {witness_path} yet", file=sys.stderr)
    if mode in (Mode.VALIDATE, Mode.FIX):
        print("generator: the specification is valid, canonical and append-only")
        return 0

    digest = witness_hash(spec)
    try:
        outputs = _outputs(spec, digest, root, out_dir, docs_dir)
    except (OSError, SpecError) as error:
        print(f"generator: {error}", file=sys.stderr)
        return 1
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
    for orphan in _orphans(outputs):
        orphan.unlink()
        print(f"generator: removed {orphan}, which the current spec does not produce")
    print(f"generator: {len(spec.keys)} key(s) into {out_dir} and {docs_dir}")
    return 0
