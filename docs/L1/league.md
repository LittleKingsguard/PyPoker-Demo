# PyPoker-Demo — L1 league: pool, scheduler, matrix, rating, tables

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 7 · **Date:** 2026-11-08
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

### 3.1 What a cell's recorded seed reproduces, and the replay recipe

A cell's `seed` (`records.md` §9) is the seed its hands were dealt from, derived from the table seed and
the pair's membership positions — not a key that replays the cell. `evaluation.match(a, b, hands, seed)`
builds a **baseline** at the seed it is handed, while a table builds each baseline from the table seed and
that baseline's position, so a cell with a baseline in it replayed from its recorded seed is a different
cell and a different count (one measured replay read `51/3/66` where the cell recorded `57/3/60` — the cell-replay
finding in `strata/records/phase1-walkthrough.md`).
Two checkpoint members do replay from it, because a version is built at the seed its own checkpoint records
either way. What always reproduces a cell is the table it came from: replay `evaluation.matrix(pool,
[variant], "live")` over the same frozen pool, whose id and whose `table_seed` — one declared constant —
are what a third party needs, and neither is a per-cell number (D-16, ASM-14, `records.md` §10).

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

- The per-hand cost is a **measurement, not a bound**, and each artefact reports its own, in its own shape: a record's `seconds_per_hand` per seed over 3,000 hands (`checkpoints/evidence/r1-live.json`'s `run.timings`), the shipped `full` table's over 9,000 hands (`tables/league-full.json`'s `cost` block), and the `live` table's over 720 hands (that bundle's `stages.matrix_live`). **This document states the band and the shape and quotes no figure of its own**: the band is ASM-21's **0.105–0.153 s/hand** (6.5–9.5 hands/s) — 0.105–0.120 for a live run, 0.1299–0.1324 for the shipped full table and 0.1415–0.1532 for the live table, every live-table pass measured so far inside its own — and it is the band **both** L1's own ASM-15 (`assumptions.md`) **and** the brief's ASM-21 state. The exact seconds are **read from the artefact and never from this page**, because a regeneration moves every one of them and leaves only the band, so a document that quotes a build's seconds is stale as soon as the next build ships (`protocol.md` §2); the live table is not inside the run's own band, and the next bullet is why (ASM-21, ASM-15, D-16).
- **Why the table costs more per hand than the run that fed it**, measured rather than asserted: an oracle-bearing cell measured **0.255–0.315 s/hand** and an oracle-free cell **0.002–0.004 s/hand**, so the oracle's per-decision equity sample is virtually all of a table's cost (ASM-4); and the oracle's share of the hands differs — a K = 4 table has it in 3 of its 6 cells, half of the 720 hands, while R1's run draws each hand's opponent from a three-baseline pool and so faces it in one hand in three. Policy construction is not a factor (`evaluation.build_pool` is a one-off per table, microseconds in the bundle's own `stages`, and `policy_from` one-off per member) and neither is seat alternation (both paths alternate and every cell reports its 60/60 split): the band's midpoints give half the oracle rate plus half the oracle-free rate, 0.5·0.285 + 0.5·0.003 = 0.144 s/hand, within 7 % of the measured table, and a third of it plus two thirds of the cheap rate, plus the learner step, predicts the measured run (ASM-15, ASM-4).
- What that implies, at the measured band: the live table is **≈95–110 s at K = 4** (720 hands, every measured pass inside its own band) and **≈10–12 minutes at K = 9–10** at the live table's fast end; the full table **≈2 hours at K = 9–10** (2.0 h at K = 9 and 2.5 h at K = 10 at the shipped rate). Holding the slowest measured 0.1532 s/hand instead is the **conservative bound** — **≈14 minutes at K = 10** live and **≈2.3–2.9 hours** full (4,320–5,400 and 54,000–67,500 hands) — and it over-states, because a wider table pairs the oracle in a smaller share of its hands than K = 4's half (the previous bullet). The shipped K = 4 full table is 9,000 hands and recorded ≈20 min of wall clock in its own `cost` block. A ten-minute live table is what a talk has to plan for at a full window, not the under-four-minute figure the old bound reported (ASM-21, ASM-14, D-8, `tables/league-full.json`).
- Cost is bought with cell size and never with concurrency, because one global `random` stream deals every hand (§3, D-16, ASM-2); and no case asserts that a wall clock was beaten. `harness.timings` reports seconds per hand from a real run, and the battery asserts that the record exists and that the live table's hands played match §6 — never a stopwatch (ASM-21, `battery.md` §3 FAM-10).
- The parameters are L1's under ASM-13. Their alternatives — a larger M, cells of a few dozen hands, wall-clock-derived cell sizes — are recorded with ASM-14 and ASM-15 (assumptions.md).

## 8. Where a table can and cannot be read

The **matrix is the evidence; the rating is a summary of it.** A Bradley-Terry rating is one global fit over
every cell at once, so a rank says where a member stands in that fit and **never** asserts a head-to-head win
over any other member: the cell is the head-to-head, and both directions of it are reported beside the rating
(D-16, `protocol.md` §1, §2). The shipped live table for R1 shows why the distinction is not pedantry — `variant-1`
carries the table's highest rating (+0.518, 95% interval [0.345, 0.709]) while losing 51–63 to `always-call`
(+0.186) and drawing 58–58 with `oracle` (+0.143), because the fit is carried by its 111–9 against `random`; a reader
given the ranking alone would be told the opposite of one of its six cells and half of another (the live table
recorded in `checkpoints/evidence/r1-live.json`, D-16).

So a version that **outranks** a baseline has shown only that the fitted order over the whole matrix places it
there; a version that **beats** a baseline has shown that it wins more hands than it loses against that fixed
rule at this cell size on this game, and that is said of a cell and never of a rank (D-16). Neither is a claim
of poker skill, and the table says nothing about a member it does not name (D-16, brief §8). A rung's learning
claim is a curve plus its cells against the baselines — never a rank among versions alone, because self-play in
a bounded pool can reward beating one's own earlier selves (D-16, D-6). §9 names the two artifacts that ship and
the one member id that is two players, which is the other way a row can be read as measuring something it did not.

## 9. The two artifacts that ship, and the one member id that is two players

- Two artifacts ship and neither is an interface: `tables/league-full.json`, the `full` table `evaluation` precomputes offline — for R1 it is K = 4 (the three pinned baselines plus one variant), six cells, 9,000 hands — and `checkpoints/evidence/r1-live.json`, `training`'s record of the R1 live run: its run record, its four-member/six-cell live table, its rating, its report and the shipped checkpoint index (`protocol.md` §5, D-8, D-16).
- **A member id is not a player.** The shipped `full` table's `variant-1` is the offline producer's *untrained* learner at its recipe seed 31415, while a live table's `variant-1` is the rung's *trained* final model — the shipped R1 evidence records the trained seed-0 final at 10,119 parameters. The two rows measure two different players and are never compared, not even as "the same member at two cell sizes". Each artifact **must say which of the two it holds** — the evidence bundle by the final model it names, the shipped table by a provenance block that states its variant's recipe and that the member is untrained — so no reader is left to guess (D-16, ASM-18).
- Neither file is a cache and no entry point reads either: the table is evidence and the evidence bundle is a record, so nothing a talk does can be silently influenced by a file that was committed once (D-8, D-12, `tables/league-full.json`'s own `provenance`).
