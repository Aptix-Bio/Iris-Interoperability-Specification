"""The generated header opens with the keys: the first code after the banner
and the includes is namespace I2S::Attribute, one constant per key with its
full documentation block, each short name right after its key. Only the Key
enumeration and TypedKey, which the constants are declared with, come before
it; the version constants and every table come after (decided 2026-11-25)."""
# RTM ReadableHeaders_01, ReadableHeaders_02
from __future__ import annotations

import re
from pathlib import Path

from generator import pipeline
from generator.emit.cpp import emit_header
from generator.model import Key, Spec, parse

ROOT = Path(__file__).resolve().parents[2]


def _spec() -> Spec:
    return parse(pipeline.load_json(ROOT / "spec" / "i2s_header.json"), pipeline.load_json(ROOT / "spec" / "i2s_keys.json"))


def _header() -> list[str]:
    return emit_header(_spec(), "0" * 64).splitlines()


def _index(lines: list[str], pattern: str) -> int:
    return next(i for i, line in enumerate(lines) if re.search(pattern, line))


def _attribute_block(lines: list[str]) -> tuple[int, int]:
    start = _index(lines, r"^namespace Attribute \{")
    return start, _index(lines[start:], r"^\} // namespace Attribute") + start


def _code(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith(("//", "#"))


def _doc_block(key: Key) -> list[str]:
    """The three lines an IDE shows on hover over the key's constant."""
    if key.dicom is None:
        dicom = "none: I2S diverges from DICOM"
    else:
        dicom = f"{key.dicom.keyword} {key.dicom.tag}"
        if key.dicom.sequence is not None:
            dicom += f", in {key.dicom.sequence.keyword} {key.dicom.sequence.tag} items"
    short = f" (short name {key.short_name})" if key.short_name else ""
    return [
        f"/// {key.name}{short}: {' '.join(key.description.split())}",
        f"/// Value type {key.value_type}, written as the DICOM VR {key.vr}, multiplicity {key.multiplicity.text}.",
        f"/// DICOM: {dicom}. Identity class: {key.identity}." + (" Deprecated." if key.deprecated else ""),
    ]


def test_the_attribute_constants_are_the_first_code_after_the_includes() -> None:
    lines = _header()
    opening = _index(lines, r"^namespace I2S \{")
    assert all(line.startswith(("//", "#")) or not line for line in lines[:opening])
    start, end = _attribute_block(lines)
    # Before the constants: only the Key enumeration and TypedKey they are declared with.
    preamble = [line for line in lines[opening + 1:start] if _code(line)]
    key_enum = _index(preamble, r"^enum class Key\b")
    typed_key = _index(preamble, r"^template <Key K>$")
    assert key_enum == 0 and preamble[typed_key + 1:] == ["struct TypedKey {", "    static constexpr Key key = K;", "};"]
    # The enumeration is names only, so it stays a few lines however many keys there are.
    assert preamble[typed_key - 1] == "};"
    assert all(re.fullmatch(r"    (\w+, )*\w+,", line) for line in preamble[1:typed_key - 1])
    assert end < _index(lines, r"kVersionMajor")
    assert end < _index(lines, r"^(struct|enum class) (?!Key\b|TypedKey\b)|^inline constexpr std::array")


def test_each_key_constant_carries_its_full_documentation_block() -> None:
    lines = _header()
    for key in _spec().keys:
        at = _index(lines, rf"^inline constexpr TypedKey<Key::{key.name}> {key.name}\{{\}};$")
        assert lines[at - 3:at] == _doc_block(key), key.name


def test_each_short_name_follows_its_key() -> None:
    lines = _header()
    for key in _spec().keys:
        if key.short_name is None:
            continue
        at = _index(lines, rf"^inline constexpr TypedKey<Key::{key.name}> {key.name}\{{\}};$")
        assert lines[at + 1:at + 3] == [
            f"/// {key.short_name}: the short name of {key.name}, the same key.",
            f"inline constexpr TypedKey<Key::{key.name}> {key.short_name}{{}};",
        ]


def test_a_key_constant_exists_only_in_namespace_attribute() -> None:
    lines = _header()
    start, end = _attribute_block(lines)
    outside = [line for i, line in enumerate(lines) if "constexpr TypedKey<" in line and not start < i < end]
    assert outside == []
    names = [re.search(r"> (\w+)\{\};", line) for line in lines[start:end] if line.startswith("inline constexpr")]
    spec = _spec()
    assert sorted(m.group(1) for m in names if m) == sorted(
        [k.name for k in spec.keys] + [k.short_name for k in spec.keys if k.short_name])
