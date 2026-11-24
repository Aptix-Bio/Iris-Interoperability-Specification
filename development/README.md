# development/

How I2S is planned, tracked and verified while it is a private draft. The
specification's own rules (append-only, the schema, the witness) are in
[CONTRIBUTING.md](../CONTRIBUTING.md); this folder breaks the work down into
sprints, tasks and requirements.

| File | Use it to… |
|---|---|
| [WBS.md](WBS.md) | track the work sprint by sprint: each sprint's milestone and pull request, its tasks and their red-first steps, each tick with its evidence; the decisions and the open questions |
| [RTM.md](RTM.md) | trace each requirement back to the project's goals and forward to code and tests, with status |
| [style_guide.md](style_guide.md) | the binding conventions for code, plans and prose |
| [ci_runners.md](ci_runners.md) | the rules every workflow follows: when a runner runs, reuse, caches, robustness |

```mermaid
flowchart LR
    G["RTM goals<br/>dated requirements"] --> R["RTM requirements"]
    R --> WBS["WBS<br/>sprint → task → step"]
    WBS -->|"evidence"| R
    WBS -->|"each sprint's commits"| PR["the repository's one pull request<br/>milestones shown, CI green"]
    PR -->|"merged"| WBS
```

## How a sprint runs

A sprint is one work package of the WBS: a few days of work that ends in a
milestone someone can see working. The repository has one branch and one pull
request at a time (`feature/SpecScaffold_1`, pull request #1), never stacked;
each sprint's commits stay distinct and its WBS section intact, so the pull
request's description lists the sprints in order.

1. The branch keeps its name once pushed, since renaming a pull request's head
   branch closes the pull request.
2. Each task starts with a test shown red, recorded with its failure; then the
   code that turns it green, with the evidence (test counts, the command run).
3. The milestone is demonstrated: a command anyone can run, and its output.
4. The sprint ends with a **VERIFY** step for the maintainer and a **Gate** step: CI
   green on the pull request. The next sprint starts once the previous one's
   Gate is green, in new commits on the same branch.

The pull request's description has these sections, in this order: Summary ·
WBS (the sprint's tasks, ticked, with evidence and commit links) · RTM (rows
changed, with evidence) · Decisions (dated, each stated as a requirement) · Measurements
(when any were taken) · Test results (per cell, local and CI) · Red first ·
Failures fixed (symptom, root cause, fix, commit) · Clinical impact (what a
pathologist would see differently) · Security impact (new input parsed? new
dependency? patient data in the diff, logs or fixtures?).

**Naming:** every ID says what it is. A WBS item is `PascalCaseName_<number>`
(`VocabularyFromScanners_2`, `PhiFlag_1.6`); an RTM row is
`PascalCaseArea_<nn>` (`AppendOnly_01`); a goal is `Goal_<nn>`. No
abbreviations.

**Update rule:** a commit that changes code updates the WBS steps it completes
and the RTM rows it touches, in the same commit, and the step names the
commit once it exists. Commits are staged by explicit path.
