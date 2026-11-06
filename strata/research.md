# PyPoker-Demo — L0 research

Procedure for D-15: fact-finding before a design commitment. Ceiling: 40 lines.

## 1. When it runs

A note, a feature request, or a question whose answer depends on something outside this project:
a package's real API, a paradigm's trade-offs, a specification, a competing tool (D-15).

The work is delegated to `role_l0_research`. When that role cannot be mounted — as measured in
`strata/platform.md`, where its tool wall names tools this deployment does not have — L0 performs
the intake research itself under this same procedure: sources staged locally, every claim cited,
and the same finding record written (D-15).

## 2. What it may conclude

It establishes what is true and cites it. It never commits a design, a dependency, or a rule —
those are L0 decisions, and a decision that needs user intent goes to the user (D-1).

Every claim carries a source: a URL, a path, or a command whose output is quoted. An unsourced
claim is recorded as `unsourced` and can never be the sole basis of a decision (D-15).

## 3. The over-fit firewall

A named package or technology is an **option**, never a rule. Each one is recorded with the
acceptance predicate it satisfies, so a substitute is judged against that predicate rather than
against the named example. Recording the name alone is how one recommendation becomes a locked
dependency list (D-15).

## 4. Output

`strata/records/<topic>-research.md`, at most 40 lines, replaced on every pass and never appended
(D-15). One row per finding: claim, source, confidence, and what it would change if false.

## 5. Return

The envelope in `strata/envelope.md` (D-11): `PASS` with the record's path as its citation, or
`FAIL` with the question that could not be answered — which L0 then takes to the user (D-1).
