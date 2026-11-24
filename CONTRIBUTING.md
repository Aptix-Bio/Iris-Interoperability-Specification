# Contributing to I2S

I2S is a vocabulary that slide files are written against, so a published key
has to mean the same thing forever. Read `README.md`, this page and
`development/README.md` before opening a pull request.

## The absolutes

1. **Append-only.** A key, value type or identity class in `spec/*.json`
   is never removed, renamed, retyped or re-mapped: its name, version group,
   short name, DICOM counterpart, value type, multiplicity and PHI flag are
   fixed once committed. New facts arrive by addition: a new key at the end of
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
   configure. Change the JSON or the emitter in `generator/emit/`.
4. **`tests/witness/witness.json` is evidence.** It records every witnessed
   fact of the committed specification, and `python -m generator --validate`
   compares the current spec against it: a removed or changed fact fails,
   naming the key and both values. It is refreshed only with
   `python -m generator --refresh-witness`, which refuses while any fact is
   removed or changed, so the refresh can only record additions.

## The schema

`spec/i2s_header.json` holds the specification's name, version and status
(`draft` until ratified) and its revision history. `spec/i2s_keys.json` holds
three sections, each grouped by the version that introduced its members
(`i2s_version` → `"0.1"` → members), as IFE's `spec/*.json` are:

| Section | Member fields |
|---|---|
| `value_types` | `description`: the lexical form of a value |
| `identity_classes` | `description`: whether a value can identify an individual |
| `keys` | the fields below, every one present, `null` where it does not apply |

| Key field | Meaning |
|---|---|
| (the member name) | the key, PascalCase; the attribute key in a file and the C++ enumerator `I2S::Key::<name>` |
| `short_name` | a shorter name the maintainer gave the key (`DII`), or `null`; `I2S::key_from_name` accepts it too, so names and short names share one namespace |
| `dicom` | the DICOM attribute the key corresponds to (`keyword`, `tag` as `GGGG,EEEE`, `vr`, the `sequence` whose items carry it or `null`, and `verified`: the URLs and date the mapping was checked against the standard), or `null` where I2S diverges from DICOM |
| `value_type` | a member of `value_types` |
| `multiplicity` | how many values: `1`, `1-3`, or `1-n` for no upper bound |
| `identity` | a member of `identity_classes` |
| `identity_note` | the open question, present exactly when `identity` is `UNDER_REVIEW` |
| `phi_flag` | the `BOOLEAN` key that states per file whether this key's value is protected health information, with `absent_means_phi`: what a reader and a de-identifier assume when the flag is absent; or `null` |
| `deprecated` | the reason the key was retired, or `null` |
| `description` | what the value is |

## What a vocabulary change requires

1. Edit `spec/i2s_keys.json` by addition, with each DICOM mapping checked
   against the current standard and its URL and date recorded in `verified`.
2. `python -m generator --validate` stays green.
3. `python -m generator --refresh-witness` records the addition in the same
   commit; `--check` fails in CI until it does.
4. A C++ or generator test covers any new rule.

## Build and test

```bash
uv sync                                   # mypy and pytest into .venv/
uv run pytest && uv run mypy
cmake --preset debug && cmake --build --preset debug && ctest --preset debug
python3 -m generator --check
```

Chain the build and the tests with `&&`: `ctest` reports results from stale
binaries after a failed build.
