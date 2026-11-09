# PyPoker-Demo — L1 Phase 1 design

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 14 · **Date:** 2026-11-09
- **Scope:** the technique ladder on one fixed game (brief §2) and its league evaluation (brief §3, D-16), whose learning rules, reward utilities and fixed baselines are parameters of it (D-19, D-20, D-21)
- **Ceiling:** 40 lines. At the ceiling, split by owner — never append

## What changed at Rev 2 … Rev 14

Rev 2 answered D-16: a bounded round-robin league — the model's last M versions plus the three fixed baselines — became both the training and the evaluation opposition, `league.md` owns the pool, the scheduler, the matrix, the rating and the tables, and `e2e-surface.md` replaced `evaluation.head_to_head` with the league's entry points, 11 `evaluation` endpoints and 49 across the map. Rev 3–Rev 9 repaired the blind walkthroughs of D-14, and each repair is carried by the document that owns its question: the matrix is separated from the rating and a rank asserts no head-to-head win (`league.md` §3.1, §8), a measured per-hand band replaced ASM-15's 40 ms bound (`league.md` §7, ASM-15, ASM-21), `battery.md` §2 gives the supported way to run the batteries and where they write, `ladder.md` §7 says which notebook ships and that it finds the repository root and its own write root, `getting-started.md` is the newcomer route, `records.md` §9 states what a recorded cell seed reproduces, `protocol.md` §4 records that reproducibility is one build's and one pinned interpreter's, `gpu.md` carries D-17's measurement that a delegated agent cannot reach the GPU, and ASM-20 states that a checkpoint records the seed and the encoding it was built at. Rev 10 added ASM-23: a document states a result's **shape** and the **band** it lives in and points at the artefact for the number, so no prose figure outlives its build (`protocol.md` §2).

Rev 11–Rev 13 answered D-19 and D-20, and together they made the two things a learner is built from into catalogues. `rules.md` owns the learning-rule catalogue (`masked-q-learning`, `double-q-learning`), `utilities.md` owns the terminal-reward catalogue (`net-chips`, `stack-shortfall`), every variant a configuration declares is **trained**, and a pool member, a cell, a matrix, a run record and a report each name the rule and the utility they measured, with the pool id digesting both (D-19, D-20, ASM-25–ASM-29). Rev 14 answers D-21: the baseline catalogue grows from three to six — the three of D-6 that anchor the rating and three simple folding baselines — and `folders.md` owns them: their exact rules, the `hand_class` fact they need and what carrying it costs, the anchor that does not move, what the full declared set does to K and to the tables' cost, and the live-budget verification the change exists for (D-21, ASM-30–ASM-33).

## Reading order

| Document | What it answers |
|---|---|
| `getting-started.md` | the route in: Python, dependencies, `PYTHONPATH=src`, one training run, one league table |
| `gpu.md` | what runs on CPU today, why an agent cannot run the GPU path, and the commands a user runs to verify the card and measure the PyTorch-versus-NumPy difference (D-17, D-7, D-8) |
| `module-map.md` | the six modules, the league's owner, their interactions, path ownership, and the harness contract of brief §5 |
| `e2e-surface.md` | every entry point the battery drives, the shared contracts behind them, the endpoint counts in `modules.json`, and which surfaces are general-purpose |
| `records.md` | the mapping shape each entry point exchanges, the league's pool, cell, matrix and rating records included, so no module reads another's type (D-13) |
| `ladder.md` | the six rungs as configurations of one machinery, what a comparison holds constant, the budgets, and where the D-5 notebooks live |
| `rules.md` | the learning-rule catalogue: what each rule's target is, the one contract they share, what a checkpoint records, how a configuration declares several, and the fairness rule that replaces a single rule (D-19) |
| `utilities.md` | the utility catalogue: the reward each member delivers, where the transform is consumed and why there, what every checkpoint, record, pool, cell and matrix carries, the fairness axis, what the table may not be read as, and the two-variant verification of D-20 (D-20) |
| `folders.md` | the folding baselines of D-21: their three rules and pinned readings, the `hand_class` readout fact and what it costs the map, the anchor that does not move, K and the cells and the cost of declaring the full set, and the live-budget verification (D-21, ASM-30–ASM-33) |
| `protocol.md` | the evidence a rung must report (D-6, D-16), the six fixed baselines (ASM-4, D-21), the seed contract (ASM-2), checkpoint retention (ASM-5, D-16), and the device rule (D-8) |
| `league.md` | the pool, the scheduler, the matrix and the rating, the live and offline tables, what M, the cell size and the cells cost, and how to read a rank (D-16, ASM-13, ASM-14, ASM-21) |
| `battery.md` | what `tests/e2e/` covers, how the batteries are run, and what green means here (D-11) |
| `assumptions.md` | what L1 decided where the brief left the answer here, each with the alternative it rejected |

`modules.json` at the repository root is the declaration `strata-lint` reads (modules.md §4); `README.md` at the root is L0's front page and links this file (D-1). The game is heads-up fixed-limit Hold'em (D-2), the ladder's order is brief §2's (D-3), and the league is D-16; Phase 2 is not designed here (D-4, D-9). **A citation names the rule's carrier, never the walkthrough record**: a document cites a `D-n`, an `ASM-n` or the section that carries the rule — `battery.md` §2 for where a battery writes, `ladder.md` §7 for where a notebook writes, never the redirect a split leaves behind (`assumptions.md` ASM-24) — and never a finding, by subject or by number, in `strata/records/phase1-walkthrough.md`, because that record is replaced on every run (§7 of `strata/walkthrough.md`, D-14, ASM-22).

## Next layer
Each module of `module-map.md` §1 goes to `role_l2_integration` with its `modules.json` row, in the dependency order of `module-map.md` §2, and each return carries the envelope of `strata/envelope.md`.
