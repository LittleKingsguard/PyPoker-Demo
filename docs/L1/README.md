# PyPoker-Demo — L1 Phase 1 design

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-05
- **Scope:** the technique ladder on one fixed game (brief §2) and its league evaluation (brief §3, D-16)
- **Ceiling:** 40 lines. At the ceiling, split by owner — never append

## What changed at rev 2

Rev 1 designed a head-to-head protocol under D-6. D-16 replaced the opponent with a bounded round-robin
league — the model's last M versions plus the three fixed baselines — which is both the training
opposition and the evaluation opposition (D-16). So `league.md` is new and owns the pool, the scheduler,
the matrix, the rating and the live/offline tables; `protocol.md` reports a matrix and a rating instead
of a head-to-head row; and `e2e-surface.md` replaces `evaluation.head_to_head` and
`evaluation.against_baselines` with the league's entry points — hence 11 `evaluation` endpoints and 49
across the map. Kept from Rev 1: the six-module map, the boundaries, the endpoint counting rule and the
harness ceiling (brief §5), the rung ladder with its matched budgets (D-3, ASM-8), the seed contract
(ASM-2), checkpoint retention as D-16 amends it (ASM-5), and ASM-6..ASM-12 (assumptions.md).

## Reading order

| Document | What it answers |
|---|---|
| `module-map.md` | the six modules, the league's owner, their interactions, path ownership, and the harness contract of brief §5 |
| `e2e-surface.md` | every entry point the battery drives, the shared contracts behind them, the endpoint counts in `modules.json`, and which surfaces are general-purpose |
| `records.md` | the mapping shape each entry point exchanges, the league's pool, cell, matrix and rating records included, so no module reads another's type (D-13) |
| `ladder.md` | the six rungs as configurations of one machinery, what a comparison holds constant, the budgets, and where the D-5 notebooks live |
| `protocol.md` | the evidence a rung must report (D-6, D-16), the three fixed baselines (ASM-4), the seed contract (ASM-2), checkpoint retention (ASM-5, D-16), and the device rule (D-8) |
| `league.md` | the pool, the scheduler, the matrix and the rating, the live and offline tables, and what M, the cell size and the cells cost (D-16, ASM-13, ASM-14) |
| `battery.md` | what `tests/e2e/` covers, and what green means before the code exists (D-11) |
| `assumptions.md` | what L1 decided where the brief left the answer here, each with the alternative it rejected |

`modules.json` at the repository root is the declaration `strata-lint` reads: one row per module, its
owned paths and its endpoint count (modules.md §4). The game is heads-up fixed-limit Hold'em (D-2), the
ladder's order is brief §2's (D-3), and the league is D-16; Phase 2 is not designed here (D-4, D-9).

## Next layer

Each module of `module-map.md` §1 goes to `role_l2_integration` with its `modules.json` row, in the
dependency order of `module-map.md` §2, and each return carries the envelope of `strata/envelope.md`.
