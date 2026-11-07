# PyPoker-Demo — L1 Phase 1 design

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 6 · **Date:** 2026-11-06
- **Scope:** the technique ladder on one fixed game (brief §2) and its league evaluation (brief §3, D-16)
- **Ceiling:** 40 lines. At the ceiling, split by owner — never append

## What changed at Rev 2, Rev 3, Rev 4, Rev 5 and Rev 6

D-16 replaced D-6's head-to-head opponent with a bounded round-robin league — the model's last M versions plus the three fixed baselines — as both training and evaluation opposition (Rev 2): `league.md` owns the pool, scheduler, matrix, rating and tables, and `e2e-surface.md` replaces `evaluation.head_to_head` with the league's entry points, 11 `evaluation` endpoints and 49 across the map. Rev 3 and Rev 4 repair the two blind walkthroughs (`strata/records/phase1-walkthrough.md`): the matrix is separated from the rating and a rank asserts no head-to-head win (`league.md` §3.1, §8), the measured per-hand cost and the live table's higher own figure replace ASM-15's 40 ms bound (`league.md` §7, ASM-21), `battery.md` §2 gives the supported way to run the batteries and says where they write, `ladder.md` §7 says which notebook ships and that it finds the repository root itself, `getting-started.md` is the newcomer route and warns where a run writes, `records.md` §9 states what a recorded cell seed reproduces, `protocol.md` §4 records that reproducibility is one build's and one pinned interpreter's, and the evidence bundle names its own build (`protocol.md` §5). Rev 5 adds `gpu.md`, which D-17 requires: the measurement that a delegated agent cannot reach the GPU, the code being CPU-only regardless, the commands a user runs in their own shell to verify the card, and the device rule that keeps a CPU figure and a GPU figure apart.

Rev 6 closes the four findings of walkthrough run 3 (`strata/records/phase1-walkthrough.md`). `league.md` §7 and `assumptions.md`'s ASM-15 quote the band and the projections the brief's ASM-21 states after L0 amended it — 0.105–0.153 s/hand, ≈95–110 s at K = 4, ≈10–12 minutes at K = 9–10 and ≈2 hours full — and that band is carried down to `docs/L2/evaluation/league.md` §5, `docs/L3/evaluation/tables.md` §1/§6 and `docs/L3/evaluation/declarations.md` §4.1 by those layers, so no layer below this one quotes an older figure. `gpu.md` §5 states the measured R1/R2 speed-up (0.1111 → 0.0451 s/hand, 2.46×, recorded in `strata/records/r2-speed.md`) in place of claiming that no PyTorch figure exists. And `ladder.md` §7 records that the R1 notebook's run targets the shipped checkpoint set unless its write root is redirected — as it did during walkthrough run 3 — and that the notebook now redirects it by default (`PYPOKER_CHECKPOINT_ROOT`, `/tmp/pypoker-notebook-r1`) and says so in its opening markdown.

## Reading order

| Document | What it answers |
|---|---|
| `getting-started.md` | the route in: Python, dependencies, `PYTHONPATH=src`, one training run, one league table |
| `gpu.md` | what runs on CPU today, why an agent cannot run the GPU path, and the commands a user runs to verify the card and measure the PyTorch-versus-NumPy difference (D-17, D-7, D-8) |
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
