"""The AsciiDoc document's generated half and its contract with the narrative."""
# RTM Document_02
from __future__ import annotations

import re
from pathlib import Path

from generator import pipeline
from generator.model import parse
from generator.witness import witness_hash

ROOT = Path(__file__).resolve().parents[2]
GENERATED = {"attributes.adoc", "revision_history.adoc", "value_types.adoc",
             "identity_classes.adoc", "value_representations.adoc", "keys_table.adoc", "key_sections.adoc"}


def _generate(tmp_path: Path) -> Path:
    assert pipeline.run(ROOT, tmp_path / "source", tmp_path / "docs") == 0
    return tmp_path / "docs"


def test_every_generated_document_carries_the_witness_hash(tmp_path: Path) -> None:
    docs = _generate(tmp_path)
    digest = witness_hash(parse(pipeline.load_json(ROOT / "spec" / "i2s_header.json"),
                                pipeline.load_json(ROOT / "spec" / "i2s_keys.json")))
    assert {p.name for p in docs.iterdir()} == GENERATED
    for path in docs.iterdir():
        text = path.read_text(encoding="utf-8")
        assert f"Witness: sha256 {digest}" in text, path.name
        assert "DO NOT EDIT BY HAND" in text, path.name


def test_the_narrative_includes_every_generated_document_at_column_zero() -> None:
    narrative = (ROOT / "spec" / "i2s_spec.adoc").read_text(encoding="utf-8")
    included = set(re.findall(r"^include::\{generated\}/([a-z_]+\.adoc)\[\]$", narrative, re.MULTILINE))
    assert included == GENERATED


def test_a_document_the_render_no_longer_produces_is_removed(tmp_path: Path) -> None:
    stale = tmp_path / "docs" / "i2s_specification.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale", encoding="utf-8")
    (tmp_path / "docs" / "README.md").write_text("kept", encoding="utf-8")
    _generate(tmp_path)
    assert not stale.exists()
    assert (tmp_path / "docs" / "README.md").exists()
