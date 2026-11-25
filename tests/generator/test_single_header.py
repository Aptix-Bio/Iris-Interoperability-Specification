"""I2S.hpp, the one installed header: the generated vocabulary, then the
public declarations, then the implementation, stitched from the hand-written
sources in include/. Its non-template function bodies compile only where
I2S_IMPLEMENTATION is defined (decided 2026-11-25)."""
# RTM SingleHeader_01, SingleHeader_02
from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from generator import pipeline
from generator.emit.cpp import SOURCES

ROOT = Path(__file__).resolve().parents[2]


def _generate(root: Path, tmp_path: Path) -> list[str]:
    assert pipeline.run(root, tmp_path / "source", tmp_path / "docs") == 0
    return (tmp_path / "source" / "I2S.hpp").read_text(encoding="utf-8").splitlines()


def _index(lines: list[str], pattern: str) -> int:
    return next(i for i, line in enumerate(lines) if re.search(pattern, line))


def _implementation(lines: list[str]) -> list[str]:
    start = _index(lines, r"^#ifdef I2S_IMPLEMENTATION$")
    return lines[start + 1:_index(lines[start:], r"^#endif // I2S_IMPLEMENTATION$") + start]


def test_the_header_is_guarded_and_self_contained(tmp_path: Path) -> None:
    lines = _generate(ROOT, tmp_path)
    code = [line for line in lines if line and not line.startswith("//")]
    assert code[:2] == ["#ifndef I2S_HPP", "#define I2S_HPP"]
    assert code[-1] == "#endif // I2S_HPP"
    assert [line for line in lines if line.startswith('#include "')] == []
    includes = [i for i, line in enumerate(lines) if line.startswith("#include <")]
    assert len({lines[i] for i in includes}) == len(includes)
    assert max(includes) < _index(lines, r"^namespace I2S \{")


def test_vocabulary_then_declarations_then_implementation(tmp_path: Path) -> None:
    lines = _generate(ROOT, tmp_path)
    keys = (tmp_path / "source" / "I2S_Keys.hpp").read_text(encoding="utf-8").splitlines()
    start = _index(lines, r"^namespace Attribute \{")
    end = _index(lines, r"^\} // namespace Attribute")
    # The same block, documentation and all, as I2S_Keys.hpp opens with.
    assert lines[start:end] == keys[_index(keys, r"^namespace Attribute \{"):_index(keys, r"^\} // namespace Attribute")]
    order = [_index(lines, pattern) for pattern in (
        r"^namespace Attribute \{", r"kVersionMajor", r"^inline constexpr std::array<KeyInfo",
        r"^concept TextValue", r"^class Attributes \{", r"^class Attributes::Iterator \{",
        r"^#ifdef I2S_IMPLEMENTATION$")]
    assert order == sorted(order)


def test_the_implementation_section_holds_only_non_template_non_inline_definitions(tmp_path: Path) -> None:
    section = _implementation(_generate(ROOT, tmp_path))
    assert any(re.search(r"Attributes::to_pairs\(\) const noexcept$", line) for line in section)
    assert [line for line in section if re.search(r"\btemplate\b", line)] == []
    assert [line for line in section if re.search(r"\binline\b", line)] == []


def test_a_source_without_its_markers_fails_generation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "root"
    for part in ("spec", "tests/witness", "include"):
        shutil.copytree(ROOT / part, root / part)
    source = root / SOURCES[0]
    source.write_text(source.read_text(encoding="utf-8").replace("// END I2S.hpp", ""), encoding="utf-8")
    assert pipeline.run(root, tmp_path / "source", tmp_path / "docs") == 1
    assert f"{SOURCES[0]}: " in capsys.readouterr().err


def test_check_fails_on_an_i2s_hpp_its_sources_no_longer_produce(tmp_path: Path) -> None:
    _generate(ROOT, tmp_path)
    assert pipeline.run(ROOT, tmp_path / "source", tmp_path / "docs", pipeline.Mode.CHECK) == 0
    header = tmp_path / "source" / "I2S.hpp"
    header.write_text(header.read_text(encoding="utf-8") + "// edited\n", encoding="utf-8")
    assert pipeline.run(ROOT, tmp_path / "source", tmp_path / "docs", pipeline.Mode.CHECK) == 1
