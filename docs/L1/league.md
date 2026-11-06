# PyPoker-Demo — L1 league: pool, scheduler, matrix, rating, tables

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 2 (new) · **Date:** 2026-11-05
- **Covers:** brief §3 — the bounded round-robin league of D-16, its parameters (ASM-13) and what they cost
- **Ceiling:** 110 lines. At the ceiling, split by owner — never append

## 1. What the league is

A bounded round-robin league: a rolling pool of the model's last M versions plus the three fixed
baselines, used as both the training opponent and the evaluation opponent (D-16). The agent learns
against the pool during a run, and the same pool is the table it is measured in; there is no separate
evaluation opponent, and no cell is played against a policy that is not a named member (D-16). The pool,
the scheduler, the matrix and the rating are `evaluation`'s, in that order of assembly (`module-map.md`
§2, ASM-19).

## 2. The pool

- A version is a snapshot of a run: a checkpoint with an id, the rung, the variant, the seed and the training step it came from (D-16, ASM-18).
- The pool holds **at most M = 5 versions** and **always the three baselines**, which are pinned and never evicted, so the pool has between 3 and 8 members (D-16, ASM-14). The bound is a declaration's own field: a configuration may declare a tighter `m` than the league's M, and no declaration may exceed it (D-16, `records.md` §8).
- A rung's pool is the last M versions of the rung it inherits, by lineage order, plus the baselines; R1 has no lineage, so its pool is the three baselines alone and the report says so instead of inventing a version (D-16, `ladder.md` §2).
- The pool is **frozen before a rung's variants train** and does not change while either arm of a pair trains or is tabled. That is what makes D-16's "identical frozen pool" true of R4, R5 and R6 while D-3 keeps the rung to one axis: both arms sample the same opponents, in the same window, and their run records carry the same pool id (D-16, D-3, ASM-16).
- A rung's own snapshots are what the next rung's window is built from; `evaluation.offer` advances a pool by one version and `evaluation.pool_members` reads one back, so rolling is a declared operation on a named object rather than a side effect of training (D-16, ASM-18).
- The pool is deterministic: the same membership declaration yields the same ordered member list, and a pool's id changes when and only when its members do (D-16, ASM-2).

## 3. The match scheduler

- One cell at a time. A cell is one unordered pair played at the cell's hand count, and the scheduler plays it hand after hand from the one global `random` stream (D-16, ASM-2). No cell is interleaved with another and none runs concurrently: concurrency is not available as a cost fix, so cost is bought with cell size only (D-16, ASM-15).
- Seats alternate across a cell's hands, so each member holds the button for half of them, and the cell reports the split (D-16).
- The two directions a cell is reported in are the same hands seen from each seat; a cell costs its hand count, not twice its hand count (ASM-14).
- Every cell of one table is played at one hand count, the three baseline cells included, so no member's row is measured more precisely than another's (D-16).
- `evaluation.match` is the scheduler's surface: it plays one cell and returns it; `evaluation.opponent` is how the training loop draws a single opponent from the same pool (D-16, `e2e-surface.md` §3.4).

## 4. The matrix

- Membership is the frozen pool plus the rung's variants: K = |pool| + V, with V = 1 or 2 (`ladder.md` §2). K is therefore 4 for R1, 9 for a single-variant rung with a full window and 10 for a two-variant rung with a full window (ASM-14).
- Cells = K(K−1)/2 unordered pairs, each played at the table budget's hand count: 6 cells for R1, 36 for K = 9 and 45 for K = 10 (D-16, ASM-14).
- The three baselines are rows *and* columns at that same hand count, and their three mutual cells are in the table, so the matrix carries cells no model influences (D-16, `protocol.md` §3).
- The matrix is reported raw — both directions of every cell, its counts, chip deltas and seat split — and is never reduced to a ranking in the report. A summary statistic that assumes a transitive order is exactly what a poker payoff need not have (D-16).
- A matrix whose cells differ in hand count, whose membership is not the pool's, or which is missing a baseline, is a contract violation and not a table (D-16, `e2e-surface.md` §2).

## 5. The rating

- The fitted rating is **Bradley-Terry**, fitted over the matrix's cells on each cell's win/tie/loss counts with a tie counted as half a win to each side (ASM-17, D-16).
- Each member's rating carries a **95% confidence interval** from a hand-level bootstrap: the hands inside each cell are resampled, the fit is repeated, and the interval is the 2.5th to 97.5th percentile of the resulting ratings. The bootstrap is seeded from the table seed and its seed is recorded (ASM-17, D-16).
- The fit is **anchored by the three baselines**, whose mean rating is fixed at 0, so every value reads as a distance from the only fixed standard in the table and two tables can be compared on one scale (D-16).
- A member that won or lost every cell has no finite maximum-likelihood rating; the fit bounds it, reports that the bound was applied, and the interval then says the evidence pinned it (ASM-17, D-16).
- The rating and the matrix travel together in the report, and neither is a claim of poker skill: a rank states where a version stands among the table's named members on this game at this cell size (D-16, brief §8).

## 6. The two tables

| Quantity | `live` | `full` |
|---|---|---|
| Membership | the frozen pool plus the rung's variants (K = 9 or 10) | exactly the same membership (D-16) |
| Hands per cell | 120, seats alternating | 1,500, seats alternating (ASM-14) |
| Cells | 36 or 45 | 36 or 45 (ASM-14) |
| Hands played | 4,320 or 5,400 | 54,000 or 67,500 (ASM-14) |
| Produced by | the talk, on the fly (D-8) | precomputed offline and shipped under `tables/` (D-16, D-8) |
| Per-cell resolution | about ±9 percentage points of win rate | about ±2.5 percentage points (ASM-14) |

The two tables share one membership and differ only in cell size, so the live table is the full table's
skeleton read coarsely and not a different design (D-16). The live table's per-cell noise means a rank
difference under roughly a hundred rating points is not resolvable from it: a live-table order is a
demonstration, and the full table with the fitted intervals is what a claim rests on (D-16, ASM-14).

## 7. What it costs

- L1 has no measurement channel, so the per-hand cost is a stated bound and not a measurement: **at most 40 ms of CPU per hand**, a hand being at most 24 decisions — the raise cap of ASM-6 permits about eight applied actions on each of four streets — at about 1.5 ms per decision for a pure-Python `pokerkit` step plus one policy evaluation (ASM-15).
- At that bound the live table is at most 5,400 hands, i.e. under four minutes wall-clock, and the full table at most 67,500 hands, i.e. under an hour — the difference between a talk and an offline job, which is what D-8 asks for (ASM-15, D-8). Most hands are far shorter than the cap; the bound is the worst case and the battery measures the real figure (ASM-6, ASM-15).
- The bound, not the observed cost, is what sizes the table, so a faster engine only buys margin; `harness.timings` reports seconds per hand from a real run and the battery asserts that the record exists and that the live table's hands played match §6, never that a wall clock was beaten (ASM-15, `battery.md` §3 FAM-10).
- The parameters are L1's under ASM-13. Their alternatives — a larger M, cells of a few dozen hands, wall-clock-derived cell sizes — are recorded with ASM-14 and ASM-15 (assumptions.md).

## 8. Where a table can and cannot be read

A version that outranks a baseline in this table has shown that it beats that fixed rule at this cell
size on this game; it has not shown poker skill, and the table says nothing about a member it does not
name (D-16, brief §8). A rung's learning claim is a curve plus a table position relative to the
baselines, never a rank among versions alone, because self-play in a bounded pool can reward beating
one's own earlier selves (D-16, D-6).
