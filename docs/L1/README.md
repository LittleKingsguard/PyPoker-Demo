# PyPoker-Demo — L1 Phase 1 design

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-05
- **Scope:** the technique ladder on one fixed game (brief §2) and its league evaluation (brief §3, D-16)
- **Ceiling:** 40 lines. At the ceiling, split by owner — never append

## What changed at Rev 2 and Rev 3

Rev 1 designed a head-to-head protocol under D-6; D-16 replaced the opponent with a bounded round-robin league — the
model's last M versions plus the three fixed baselines — as both training and evaluation opposition, so `league.md` is
new and owns the pool, scheduler, matrix, rating and tables, `protocol.md` reports a matrix and a rating, and
`e2e-surface.md` replaces `evaluation.head_to_head` with the league's entry points: 11 `evaluation` endpoints, 49 across
the map. Rev 3 repairs the first blind walkthrough's findings (D-14, `strata/records/phase1-walkthrough.md`): `league.md`
§8 separates the matrix from the rating and says a rank never asserts a head-to-head win, §7 states the measured
0.105–0.132 s/hand that ASM-21 ratifies in place of ASM-15's 40 ms bound, `battery.md` §2 gives the supported way to run
the batteries, `ladder.md` §7 says which notebook ships, and `getting-started.md` is new — the route from an empty
checkout to a training run and a league table.

## Reading order

| Document | What it answers |
|---|---|
| `getting-started.md` | the route in: Python, dependencies, `PYTHONPATH=src`, one training run, one league table |
| `module-map.md` | the six modules, the league's owner, their interactions, path ownership, and the harness contract of brief §5 |
| `e2e-surface.md` | every entry point the battery drives, the shared contracts behind them, the endpoint counts in `modules.json`, and which surfaces are general-purpose |
| `records.md` | the mapping shape each entry point exchanges, the league's pool, cell, matrix and rating records included, so no module reads another's type (D-13) |
| `ladder.md` | the six rungs as configurations of one machinery, what a comparison holds constant, the budgets, and where the D-5 notebooks live |
| `protocol.md` | the evidence a rung must report (D-6, D-16), the three fixed baselines (ASM-4), the seed contract (ASM-2), checkpoint retention (ASM-5, D-16), and the device rule (D-8) |
| `league.md` | the pool, the scheduler, the matrix and the rating, the live and offline tables, what M, the cell size and the cells cost, and how to read a rank (D-16, ASM-13, ASM-14, ASM-21) |
| `battery.md` | what `tests/e2e/` covers, how the batteries are run, and what green means here (D-11) |
| `assumptions.md` | what L1 decided where the brief left the answer here, each with the alternative it rejected |

`modules.json` at the repository root is the declaration `strata-lint` reads (modules.md §4); `README.md` at the root is
L0's front page and links this file (D-1). The game is heads-up fixed-limit Hold'em (D-2), the ladder's order is brief
§2's (D-3), and the league is D-16; Phase 2 is not designed here (D-4, D-9).

## Next layer

Each module of `module-map.md` §1 goes to `role_l2_integration` with its `modules.json` row, in the dependency
order of `module-map.md` §2, and each return carries the envelope of `strata/envelope.md`.
