"""The generated header reads vocabulary first: right after the version
constants, the Key enumeration and the I2S::Attribute constants, one line per
key, before any table or lookup (decided 2026-11-25)."""
# RTM ReadableHeaders_01
from __future__ import annotations

import re
from pathlib import Path

from generator import pipeline
from generator.emit.cpp import emit_header
from generator.model import Spec, parse

ROOT = Path(__file__).resolve().parents[2]


def _spec() -> Spec:
    return parse(pipeline.load_json(ROOT / "spec" / "i2s_header.json"), pipeline.load_json(ROOT / "spec" / "i2s_keys.json"))


def _header() -> list[str]:
    return emit_header(_spec(), "0" * 64).splitlines()


def _index(lines: list[str], pattern: str) -> int:
    return next(i for i, line in enumerate(lines) if re.search(pattern, line))


def _constant_name(line: str) -> str:
    match = re.search(r"> +(\w+)\{\};", line)
    assert match is not None, line
    return match.group(1)


def test_the_vocabulary_comes_before_every_table() -> None:
    lines = _header()
    version = _index(lines, r"kVersionMajor")
    key_enum = _index(lines, r"^enum class Key\b")
    attribute = _index(lines, r"^namespace Attribute \{")
    first_table = _index(lines, r"^(struct|enum class) (?!Key\b|TypedKey\b)|^inline constexpr std::array")
    assert version < key_enum < attribute < first_table


def test_each_key_and_short_name_is_one_aligned_line_in_namespace_attribute() -> None:
    lines = _header()
    start = _index(lines, r"^namespace Attribute \{")
    end = _index(lines[start:], r"^\} // namespace Attribute") + start
    constants = [line for line in lines[start:end] if line.startswith("inline constexpr TypedKey")]
    spec = _spec()
    names = [k.name for k in spec.keys] + [k.short_name for k in spec.keys if k.short_name]
    assert [_constant_name(line) for line in constants] == names
    # Aligned: every trailing comment starts in the same column.
    assert len({line.index("///<") for line in constants}) == 1
    manufacturer = next(line for line in constants if _constant_name(line) == "Manufacturer")
    assert re.search(r"///< TEXT +LO +1 +\(0008,0070\) Manufacturer$", manufacturer)


def test_a_key_constant_exists_only_in_namespace_attribute() -> None:
    lines = _header()
    start = _index(lines, r"^namespace Attribute \{")
    end = _index(lines[start:], r"^\} // namespace Attribute") + start
    outside = [line for i, line in enumerate(lines) if "constexpr TypedKey<" in line and not start < i < end]
    assert outside == []
