# phase1 walkthrough — blind documentation pass (D-14) · run 3, 2026-11-06

Runner: a fresh agent, staged at `/tmp/wt3` as a listener's clone. Scenarios: 13 (the run-1/run-2
twelve, plus the GPU scenario D-17 added). Verdict: **STALE**, but of a different kind from runs 1
and 2 — **every one of the 13 steps completed from the documentation alone, and every documented
command worked as written**. What remains is documentation that two earlier repairs did not finish.

## What run 3 confirms as repaired

Orientation and the reading order; the fixed game's parameters (2 seats, blinds 1/2, one blind
level, stacks 20, bets 2/4, raise cap 4); dependencies and setup; the battery run rule (the five
documented collection errors reproduce exactly); a redirected live R1 run (3,000 hands, 340 s,
0.110–0.116 s/hand, shipped set md5-unchanged); the curves and how to read them; the live table
(6 cells × 120 hands, 60/60 seats, 107.4 s) and two cells; the rating and its rank-versus-head-to-head
rule; the shipped full table's provenance (`variant-1` untrained, 38,499 params); the notebook
headless from `notebooks/` (exit 0, reproduces the shipped evidence digit for digit); the claims and
refusals; a decision from a shipped checkpoint; and the GPU section, whose four commands all behaved
exactly as documented (`rocminfo` exit 1 on the read-write open, `torch.cuda.is_available()` False,
`devices()` listing `cpu`, `cuda` refused with `UnknownDevice`).

## Findings (routed)

| # | Finding | Owner |
|---|---|---|
| 1 | The cost repair stopped at L1: `docs/L2/evaluation/league.md` §5, `docs/L3/evaluation/tables.md` §1/§6 and `docs/L3/evaluation/declarations.md` still say 0.105–0.130 s/hand and ≈94 s, against the artefacts' own 0.153 s/hand and 110 s | L2/L3, via L1 |
| 2 | `docs/L1/league.md` §7 claims both L1's own cost assumption and the brief's ASM-21 carry the wider band; ASM-21 did not until this pass amended it | L1 |
| 3 | `docs/L1/gpu.md` §5 says no measured PyTorch figure exists; `strata/records/r2-speed.md`, the README and the documented R2 command all contradict it (0.0451–0.0453 s/hand, 2.45–2.46×) | L1 |
| 4 | The R1 notebook, reached by `README.md` §Quickstart and `ladder.md` §7, rewrites all 33 shipped checkpoint files in place and says so nowhere; `getting-started.md` §4 warns only about the shell one-liner | L1 + `notebooks/` |

Root cause, as the runner stated it: the repairs were **incomplete rather than the artefact wrong** —
each stopped at the layer that authored the text, leaving every layer below it quoting the old
number.

## L0's own share

`strata/brief.md` ASM-21 was the upstream defect for finding 1: it still carried a single 0.13 s
scalar and ≈94 s. Amended this pass to the measured 0.105–0.153 band with the spread attributed to
the oracle's per-decision equity sampling, so the layers now have one authoritative figure to quote.

A unit is recommended as ready only on a `PASS` (D-14); this is a loop recommendation, not readiness.
