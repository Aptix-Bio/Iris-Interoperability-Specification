# Contributing to I2S

I2S is a vocabulary that slide files are written against, so a published key
has to mean the same thing forever. Read `README.md`, this page and
`development/README.md` before opening a pull request.

## The absolutes

1. **Append-only.** A key, value type or identity class in `spec/*.json`
   is never removed, renamed, retyped or re-mapped: its name, version group,
   short name, DICOM counterpart, value type, multiplicity and PHI flag are
   fixed once committed. An `ENUMERATED` key's values may be added to at the
   end; a value is never removed, renamed or moved. New facts arrive by addition: a new key at the end of
   the current draft version's group, or a new version group. A key is retired
   by setting `deprecated` to the reason, and stays defined so that files
   written with it can still be read.
2. **The one fact that may change** is the identity class of a key that is
   `UNDER_REVIEW`: that class records an open question, and answering it moves
   the key to `NONE`. A key found to identify a person is deprecated and its
   fact moves to the clinical metadata stream, since a file's I2S attributes
   promise to identify no individual.
3. **Never hand-edit generated output.** `generated_source/` and
   `generated_docs/` carry a DO-NOT-EDIT banner and are rewritten at every
   configure. Change the JSON, the emitter in `generator/emit/`, or, for the
   attributes API in `I2S.hpp`, its sources in `include/` (the lines between
   each file's `// BEGIN I2S.hpp` and `// END I2S.hpp` markers are copied).
4. **`tests/witness/witness.json` is evidence.** It records every witnessed
   fact of the committed specification, and `python -m generator --validate`
   compares the current spec against it: a removed or changed fact fails,
   naming the key and both values. It is refreshed only with
   `python -m generator --refresh-witness`, which refuses while any fact is
   removed or changed, so the refresh can only record additions. Before the
   first release, a deliberate break (the rename of 2026-11-24) is made by
   deleting the old entries from the witness by hand, in a reviewed commit.
5. **A deprecated key stays deprecated**, and nothing is added under a
   version older than the current one, or under a ratified one.

## The schema

`spec/i2s_header.json` holds the specification's name, version and status
(`draft` until ratified) and its revision history: each revision's
`version`, `status`, `date` (ISO 8601, `YYYY-MM-DD`), `authors` and
`summary`. The header's version is the newest revision; revisions follow one
another without a gap or repeat, and only the newest may be a draft. Every
version group in `spec/i2s_keys.json` is a revision. `spec/i2s_keys.json` holds
four sections, each grouped by the version that introduced its members
(`i2s_version` → `"0.1"` → members), as IFE's `spec/*.json` are:

| Section | Member fields |
|---|---|
| `value_representations` | a DICOM VR (PS3.5 section 6.2) as I2S writes one value: `description`, `max_length`, `length_unit` (`bytes` or `characters`), `multiple_values` (whether values may be joined by the backslash), `example` (checked by the VR's rule in `generator/model.py`, and read through the C++ codec by a test; a VR without a rule is refused), `verified` |
| `value_types` | `description`: what a value is; `vrs`: the VRs it may be written as |
| `identity_classes` | `description`: whether a value can identify an individual |
| `keys` | the fields below, every one present, `null` where it does not apply |

| Key field | Meaning |
|---|---|
| (the member name) | the key, PascalCase; the attribute key in a file and the C++ enumerator `I2S::Key::<name>` |
| `short_name` | a shorter name the maintainer gave the key (`DII`), or `null`; `I2S::key_from_name` accepts it too, so names and short names share one namespace |
| `dicom` | the DICOM attribute the key corresponds to (`keyword`, `tag` as `GGGG,EEEE`, `vr`, one of DICOM's value representations (PS3.5 Table 6.2-1), the `sequence` whose items carry it or `null`, and `verified`: a list of the sources the mapping was checked against, each a `title`, an https `url` and the ISO 8601 date it was `read`), or `null` where I2S diverges from DICOM |
| `value_type` | a member of `value_types` |
| `vr` | the VR the value is written as: one of its value type's `vrs`, and the DICOM attribute's VR where the key has one |
| `multiplicity` | how many values: `1`, `1-3`, or `1-n` for no upper bound; more than one only for a `TEXT` key whose VR allows several values |
| `values` | for an `ENUMERATED` key, the values it may hold, in order: each a CS term that also names a C++ enumerator (an upper-case letter, then upper-case letters, digits and underscores, at most 16 bytes) with its `description`; `null` for every other key |
| `identity` | a member of `identity_classes` |
| `identity_note` | the open question, present exactly when `identity` is `UNDER_REVIEW` |
| `phi_flag` | the `BOOLEAN` key that states per file whether this key's value is protected health information, with `absent_means_phi`: what a reader and a de-identifier assume when the flag is absent; or `null` |
| `deprecated` | the reason the key was retired, or `null` |
| `description` | what the value is |

## Canonical form

Each spec file has exactly one text: two-space indent, a trailing newline,
UTF-8 written as itself, and every object's fields in schema order (the
`*_FIELDS` tuples in `generator/model.py`, the order of the tables above).
Order that carries meaning is kept: a document's top level, where a
`// MARK` comment heads the section after it; members in document order, which
is the C++ enumeration order; version groups in version order.
`python -m generator --validate` names the first line that differs, and
`python -m generator --fix` rewrites the files in canonical form.

## What a vocabulary change requires

1. Edit `spec/i2s_keys.json` by addition, with each DICOM mapping checked
   against the current standard and its URL and date recorded in `verified`.
2. `python -m generator --fix` canonicalizes and validates the files.
3. `python -m generator --refresh-witness` records the addition in the same
   commit; `--check` fails in CI until it does.
4. A C++ or generator test covers any new rule.

## Gates

One command runs every gate, in the order CI runs them: the linter
(`--validate`), the generator check (`--check`), the tests (pytest, mypy,
Catch2, the compile-fail test, the document guards), then the document
render into `build/release/doc/i2s_spec.{html,pdf}`.

```bash
uv sync                               # mypy and pytest into .venv/
bundle install                        # Asciidoctor and Asciidoctor PDF, from Gemfile.lock
cmake --workflow --preset gates
```

For a debug build while working: `cmake --preset debug && cmake --build
--preset debug && ctest --preset debug`.

Chain the build and the tests with `&&`: `ctest` reports results from stale
binaries after a failed build.
