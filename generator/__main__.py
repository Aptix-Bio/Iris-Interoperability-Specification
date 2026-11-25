"""Command line: python -m generator [--validate | --check | --fix | --refresh-witness].

CMakeLists.txt runs `python -m generator -d <root>` at configure time; change
the flags here and there in the same commit.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m generator",
        description="Compile the I2S specification into C++20 and a specification document.",
    )
    parser.add_argument("-d", "--directory", default=".", type=Path,
                        help="repository root holding spec/ and tests/witness/ (default: .)")
    parser.add_argument("--out-dir", default="generated_source", type=Path,
                        help="where the C++ header is written, relative to the root")
    parser.add_argument("--docs-dir", default="generated_docs", type=Path,
                        help="where the specification document is written, relative to the root")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--validate", action="store_const", const=pipeline.Mode.VALIDATE, dest="mode",
                      help="check the spec and the append-only gate; write nothing")
    mode.add_argument("--check", action="store_const", const=pipeline.Mode.CHECK, dest="mode",
                      help="fail on a stale witness or a generated file not produced from the current spec")
    mode.add_argument("--fix", action="store_const", const=pipeline.Mode.FIX, dest="mode",
                      help="rewrite the spec files in canonical form, then validate")
    mode.add_argument("--refresh-witness", action="store_const", const=pipeline.Mode.REFRESH_WITNESS,
                      dest="mode", help="record the spec's additions in tests/witness/witness.json")
    args = parser.parse_args(argv)
    root: Path = args.directory
    mode_value: pipeline.Mode = args.mode or pipeline.Mode.GENERATE
    return pipeline.run(root, root / args.out_dir, root / args.docs_dir, mode_value)


if __name__ == "__main__":
    sys.exit(main())
