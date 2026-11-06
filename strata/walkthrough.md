# PyPoker-Demo — the L0 exit walkthrough

Procedure for D-14. A unit is not recommended as ready until this pass is green. Ceiling: 60 lines.

## 1. What it is

A subagent that has never seen the code attempts a scenario set using only the documentation and
the built surface. It tests whether the docs are **current** and **sufficient** — not whether the
feature works. Correctness is the batteries' job (D-11); size is the brief's ceiling (D-1).

## 2. Scenarios

L0 authors the scenarios at exit, from the documentation and the brief — never from the source
tree (D-14). One scenario set, at most 12 steps. A step names a user-visible goal and the
observable outcome that would satisfy it. Scenarios are the user's acceptance path, so L0 shows
them to the user with the report.

## 3. Staging

The runner sees exactly three things: a copy of the docs tree, the built artifact installed, and
an empty working directory. Its workspace is that scratch root. The real source tree is not
staged, so an undocumented shortcut is not reachable (D-14).

## 4. The runner

A fresh subagent — never the session that built the unit — with `read`, `glob`, `grep` and `bash`
scoped to the scratch root (D-14). Its persona states the quarantine, and one rule carries the
weight: **if a step cannot be completed from the documentation, that is the finding.** It may not
ask for source access, may not infer an API from the artifact's internals, and may guess only
when it flags the guess.

## 5. Report

One row per step: `step · action taken · citation · outcome · guessed?`. The citation is a doc
path plus section, and it is resolved against the staged docs — an unresolvable citation is a
DOC-GAP. Three lists follow: `docs-insufficient` (a step needed knowledge no doc supplies),
`docs-stale` (a doc claim contradicted by the surface), `undocumented` (surface behaviour a user
would hit with no doc at all).

## 6. Verdict and routing

Closed vocabulary: `PASS` | `DOC-GAP` | `STALE` | `UNUSABLE` (D-14).

- `DOC-GAP` and `STALE` route by the **owning layer of the cited document** — L1, L2 or L3; L0
  never edits another layer's doc (D-13).
- `UNUSABLE` routes to L1.
- A non-`PASS` verdict still reaches the user in the summary, with a loop recommendation, never as
  readiness (D-14).

## 7. Record

The report is L0-owned design output at `strata/records/<unit>-walkthrough.md`, at most 40 lines,
replaced on every run (git holds history) and archived with the unit when it closes.
