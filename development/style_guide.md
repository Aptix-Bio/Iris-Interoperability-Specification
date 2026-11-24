# Style Guide

Binding conventions for I2S's code and plans: the JSON specification, the
generated C++20 header and its tests, and the Python generator. Project
specifics live in [CONTRIBUTING.md](../CONTRIBUTING.md); where they are more
specific than this guide, they win. Adopted 2026-11-24 from the style guide Ryan keeps for the
Iris repositories, as Iris-Slide adopted it, with the parts that concern
libraries I2S does not have (codecs, threads, bindings) cut to what applies.

## Principles

- **Minimum code surface.** Fewest functions, variables, branches and
  dependencies: each one is a risk vector. If two routines move similar data in
  similar ways, merge them into one with an enum or optional argument, and
  delete code to do it.
- **Concise over clever; explicit over implicit.** The obvious loop beats the
  one-liner. Comments explain *why*, never *what*.
- **Strongly typed, everywhere.** Types state the contract so the compiler, not
  the reader, enforces it (Typing, below).
- **Fail loudly.** A failing subsystem says so, with the offending value; it
  never returns empty and hopes the caller notices.
- **Self-cleaning.** Resources release themselves at scope exit.
- **Test first.** The test is shown red before the code that makes it green.
- **Measure before deciding.** Numbers, not assumptions; anything unmeasured
  is marked *(to measure)*.

## Planning

An agent's knowledge is a prior, not evidence. Versions, APIs, product plans
and standards change after a model's training, and a confident recollection
can be wrong.

After drafting a plan, and before presenting it as ready or starting work on
it, verify every external fact it depends on with an internet search against
primary sources (vendor documentation, release notes, the package registry,
the standard itself): versions, pins, commit SHAs, API shapes and flags; what a
product provides and its limits; prices, quotas and licences; the clauses of
standards cited (DICOM PS3, HL7, FHIR, ICC.1).

Record each check beside the claim it supports: the source URL and the date it
was read. A claim that could not be verified stays marked *(to confirm)* and is
never presented as fact. When a search contradicts the plan, fix the plan and
say what changed and why. Facts internal to the workspace (code, history,
documents) are verified by reading them, not by searching.

## Modules and Reuse

Modules are organized by domain, not layer. A module's public API is a small
surface; everything else is file-`static`, in an anonymous namespace, or
`_private`. Two modules that share no dependency graph share no file or
library target, and nothing links what it does not use (no umbrella targets).

Repeated code is extracted, to a place set by its dependencies:

| Scenario | Destination |
|---|---|
| Dependency-free, trivially small | a `static` helper / local `_helper()` |
| Dependency-free, non-trivial | a domain-grouped utility file |
| External dependencies (the test framework) | its own build target, so dependencies do not bleed into the header |

Reuse before writing: the standard library before a dependency, and a
pattern IFE's generator already proved before a new one. The header depends
on nothing but the C++ standard library; the generator on nothing but
Python's.

## Cross-Platform Code

Platform branches live side by side in one function body behind `#if`: one
audit point, one signature, no duplication. Separate per-platform files,
chosen by the build system, only when a whole algorithm or module diverges,
not a few intrinsics.

## State

Use the fewest variables possible: compute in place unless the value is
expensive and reused, outlives its scope, or naming it fixes a real
readability problem. Declare at first use. No dead writes: a value set but
never read is deleted; a single-use intermediate is folded inline. No members
or globals that could be locals.

## Resources

- **C++:** RAII always. No raw `new`/`delete`; every handle, file descriptor
  and mapping is owned by an RAII type or a `unique_ptr` with a custom deleter. Move over
  copy. `std::array`/`std::vector` over C arrays; `std::span` and
  `std::string_view` where ownership is not needed.
- **Python:** `with` for files, locks and subprocesses; a context manager on
  any class that owns a resource; generators where the consumer streams.

## Control Flow

- **Early return.** Check preconditions at the top and leave; never wrap a
  whole body in `if (valid)`. Preconditions are stated in a comment at the top
  of the body (non-null, aligned, initialized, …).
- **Linear over branchy.** Lookup tables and state-machine dispatch over
  `if`/`else if` cascades. Nesting at most 3 levels; deeper becomes a helper.
  No `goto`.
- **Never recurse; queue the calls.** No function calls itself, directly or
  through another (including through a callback or a function pointer, such as
  a library's element iterator). A walk over a tree (a DICOM sequence), a retry,
  a "repeat until settled" is a loop over an explicit queue: push the pending
  call and run the front entry until the queue is empty. FIFO (breadth first)
  by default; a stack only when the order demands it. Pending work is then
  data, not stack depth: deep input cannot overflow the stack, and a cycle
  shows as a queue that never drains, which a bound turns into a loud error.
  Within a thread, a plain container serves (`std::deque`,
  `collections.deque`).
- **No side effects in conditions.** `x = foo(); if (x)`, never
  `if (x = foo())`.

## Errors

- **The generated header is `constexpr` and throws nothing.** A lookup that
  can find nothing returns `std::optional`, so absence is a value the caller
  must handle (`I2S::key_from_name` returns `std::nullopt` for a name I2S does
  not define); nothing falls back silently to another key. A table that could
  be wrong is checked by `static_assert`, so the build fails instead of a run.
- **The generator raises specific exceptions** (`SpecError`) at the point of
  failure, chained with `raise ... from e`, and its command line turns them
  into a message and a non-zero exit. A spec problem stops generation before
  any file is written.
- **Every error carries the offending value and where it is:**
  `keys.Manufacturer.value_type: unknown value type 'STRING'`, never
  `bad value type`.
- **Catch specific types.** A bare `except:` never appears; nothing is printed
  in place of failing.
- **C++:** `noexcept` on every function that cannot fail. An `assert`
  documents an invariant for debug builds; it is never the only guard on a
  path a release build can reach.

## Typing

- **C++:** warnings as errors; `concepts` state every template's contract;
  exhaustive `switch` with no `default:`; signed and unsigned mixed only with
  an explicit conversion; `constexpr`, `inline` or templates instead of macros;
  non-`const` reference parameters only for outputs, so call sites show
  mutation.
- **Python:** `mypy --strict` with `disallow_any_explicit`; no `Any`; frozen
  dataclasses and `StrEnum`; annotated signatures everywhere; no
  `import *`, no mutable defaults.
- **Define conventions once.** Reused constants and behaviours become enums
  early and are dispatched on, not copied into a family of functions (one
  `bytes_per_pixel(Format)`, not seven switches).
- **Named values for named things.** A value with a meaning is referred to by
  a scoped enumeration or a named constant in code and tests, defined in one
  place. A bare number ties nothing at one call site to the same number
  elsewhere, so its uses cannot be searched for, and a change of meaning
  ripples silently through every copy. When the values live in data (I2S's
  `spec/*.json`, as IFE's), the names come from that data, so the data stays the one
  source. A name becomes its raw number only at the boundary that needs it
  (the file, the wire).

## Naming

Files, modules and functions `snake_case`; classes and structs `PascalCase`;
private `_leading_underscore` (Python) or file-`static` (C++); constants
`UPPER_SNAKE_CASE` or `kCamelCase` (C++); macros `UPPER_SNAKE_CASE`; template
parameters short (`T`, `Key`), descriptive where public. A C++ data
member is `_leading_underscore`, the underscore followed by a lowercase letter
(`_parser`); the C++ standard reserves a leading underscore followed by an
uppercase letter, and any name with two underscores in a row.

Accessors name their kind. A predicate returning `bool` is `is_*`. A getter is
the bare noun (`size`, `path`), never `get_*`. A setter is `set_*` taking the
value, so mutation is visible at the call site.

Plan and trace identifiers are spelled out, never abbreviated:
`SpecScaffold_1.2`, `AppendOnly_01`.

## Writing

Prose (comments, documents, commit messages, pull request descriptions) names
the exact mechanism and states why it was chosen.

- **The precise term.** Use the technical name of what was built ("scoped
  enumeration", "FIFO queue", "RAII handle", "content hash") instead of a
  loose stand-in ("by name", "a list", "cleaned up", "a fingerprint") that
  fits several implementations.
- **The reason.** State the risk removed or the requirement met. A change
  described without its reason cannot be checked against it.
- **No contrast pairs for emphasis.** A claim restated as its own negation
  ("X, never Y", "X, not Y") adds rhythm and no information. State the
  positive claim once; mention a replaced approach only to say what changed,
  plainly ("instead of by number").

## Comments and Documentation

Block comments state the intent wherever the *why* is not visible in the code:
the generator's append-only gate, the layout of generated tables, serialization layouts (byte order,
alignment, tags). A comment that restates the code is replaced by clearer code.
Dead code (commented-out blocks, unreachable branches, orphaned functions,
declarations with no definition) is deleted; git keeps the history.

Documents describing more than one type or component carry **Mermaid
diagrams**, reviewed like code, kept true to the source, and placed beside the
prose they illustrate. Every diagram must render.

- `classDiagram` for any set of collaborating types: key members and the
  relationships (`<|--` inheritance, `..|>` implementation, `*--`
  composition, `-->` association).
- `flowchart` for dependencies and control or data flow; `sequenceDiagram`
  for multi-actor lifecycles.
