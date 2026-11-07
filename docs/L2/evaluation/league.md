# evaluation — the league: pool, scheduler, matrix, rating, tables, report

- **Layer:** L2 · **Module:** `evaluation` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-05
- **Owner of this file:** the league itself — the bounded pool and its rolling window, the scheduler, the
  matrix, the rating, the two tables and the shipped `full` one, the seven evidence families the report is
  judged against, the contracts this module holds at its edge, and the battery invariants it carries
  (D-16, ASM-14, ASM-17, `battery.md` §3 FAM-6..FAM-11, FAM-16)
- **Ceiling:** 210 lines. At the ceiling, split by owner — never append

## 1. The pool

A pool is an ordered member list plus its bound, and it is both the opposition the training loop samples
and the table the agent is measured in — one object, one owner, no second evaluation pool (D-16,
`e2e-surface.md` §2, `module-map.md` §6, ASM-19).

- **Membership is at most M = 5 versions and always the three baselines**, which are pinned and never
  evicted, so a pool holds between 3 and 8 members (D-16, ASM-14). M is the league's and `league()` declares
  it; a declaration may carry a **tighter** `m` and no declaration may exceed M, which `build_pool` refuses
  by name (D-16, `records.md` §8, `surface.md` §5).
- **The window is ordered by lineage** and keeps the last `m` versions of the declaration, so a declaration
  richer than the bound is windowed to its newest members and never refused (D-16, ASM-18, `records.md` §7).
  A rung's own snapshots are what the next rung's window is built from, and `offer` advances a window by one
  version, so rolling is a declared operation on a named object and not a side effect of training
  (`protocol.md` §5, ASM-18, `records.md` §8).
- **R1's pool is the three baselines alone**, because R1 inherits no lineage: the report says so with the
  baselines it actually had and invents no version (`docs/L1/league.md` §2, `protocol.md` §5, `records.md` §13).
- **A pool is frozen before a rung's variants train and does not change while either arm trains or is
  tabled** — that is what makes D-16's "identical frozen pool" true of R4, R5 and R6 while D-3 keeps the rung
  to one axis (D-16, D-3, ASM-16). `build_pool` freezes what the declaration says to freeze, `offer` refuses
  a frozen pool, and `matrix` refuses one that is not frozen (`surface.md` §5, §7, §10).
- **The pool is deterministic**: one declaration yields one ordered member list, and the id changes when and
  only when the membership does, so a run record and a table are compared by the id alone and two arms of a
  pair prove they held one pool (D-16, ASM-2, ASM-16, `records.md` §8).

## 2. The scheduler

- **One cell at a time.** A cell is one unordered pair played at the cell's hand count, and the scheduler
  plays it hand after hand through `engine`, so two cells are never interleaved and none runs concurrently:
  concurrency is not available as a cost fix, and cost is bought with cell size alone (D-16, ASM-2, ASM-15,
  `protocol.md` §4).
- **`match` is the scheduler** (`surface.md` §9). The i-th hand of a cell at seed `s` is dealt at a seed
  derived from `s` and `i` alone, so one pair, one hand count and one seed give one cell however much was
  played before it; the derivation is L3's to fix and may not draw from the global stream, which only the
  deal moves through `engine.new_hand` (ASM-2, `battery.md` §3 FAM-7, `protocol.md` §4).
- **Seats alternate hand by hand**, so each member holds the button for half of them and the cell reports
  the split as two counts summing to `hands` and differing by at most one (D-16, `docs/L1/league.md` §3, `records.md`
  §9). A heads-up result that gives one member the button throughout is a positional artefact and not a
  measurement (`protocol.md` §1).
- **The two directions are the same hands seen from each seat**, so a cell costs its hand count and not twice
  it, and `directions` is position-aligned with `members`: one direction's wins are the other's losses, a
  tied hand is a tie for both, and the two mean chip deltas negate each other because the hand was zero-sum
  (ASM-14, `docs/L1/league.md` §3, `records.md` §9, ASM-12). A hand is a member's **win** when that member's net chip
  delta for it is positive, a **loss** when negative and a **tie** when zero (`protocol.md` §2, ASM-6).
- **Every cell of one table is played at one hand count, the three baseline cells included**, so no member's
  row is measured more precisely than another's (D-16, `docs/L1/league.md` §3, `records.md` §10).
- **`opponent` is the training loop's draw**, not the scheduler: the loop freezes one pool and draws one
  policy per hand from it, which is what makes the training opposition and the evaluation opposition the same
  object (D-16, `module-map.md` §2, `docs/L1/league.md` §3, `surface.md` §8).

## 3. The matrix

- **Membership is the frozen pool plus the rung's variants**: K = |pool| + V, with V = 1 or 2, so K is 4 for
  R1, 9 for a single-variant rung with a full window and 10 for a two-variant rung with one (ASM-14,
  `docs/L1/league.md` §4, `ladder.md` §2, `records.md` §10). The order is `pool_members`'s, then the variants in
  argument order, so one pool and one variant list have one membership (`surface.md` §10).
- **The cells are exactly K(K−1)/2 unordered pairs** — 6, 36 or 45 — one cell per pair and no repeat
  (D-16, ASM-14, `records.md` §10). Each cell's seed is derived from the table seed and the pair, and each
  member's policy is built at a seed derived from the table seed and its position, so a table is reproduced
  from its table seed and its membership and from nothing else (ASM-2, `battery.md` §3 FAM-8).
- **The three baselines are rows and columns at that same hand count**, and their three mutual cells are in
  the table, so the matrix carries cells no model influences — the only fixed standard a self-play league
  has (D-16, `protocol.md` §3, `docs/L1/league.md` §4).
- **A matrix that is not a table is refused, not repaired**: cells of differing hand count, a cell count
  other than K(K−1)/2, a pair present twice, a membership that is not the pool's plus the variants, a cell
  naming a foreign member, or a missing baseline (`docs/L1/league.md` §4, `records.md` §10, D-16). `matrix` refuses a
  variant count, a label or an unfrozen pool (`surface.md` §10); `rating` refuses everything else on the
  record it is handed, whatever produced it (`surface.md` §11); `report` refuses a matrix whose membership is
  not the record's pool plus the rung's variants (`surface.md` §13).
- **The matrix is reported raw and is never reduced to a ranking**: both directions of every cell, its
  counts, its chip deltas and its seat split, because a summary that assumes a transitive order is exactly
  what a poker payoff need not have (D-16, `docs/L1/league.md` §4, `protocol.md` §2).

## 4. The rating

- **The fitted rating is Bradley-Terry**, fitted over the matrix's cells on each cell's win/tie/loss counts
  with a tie counted as half a win to each side (ASM-17, D-16, `docs/L1/league.md` §5). It is a statement
  about the table's named members on this game at this cell size, and **never a claim of poker skill**
  (D-16, `docs/L1/league.md` §8, brief §8).
- **Each member carries a 95% confidence interval from a hand-level bootstrap**: the hands inside each cell
  are resampled, the fit repeated, and the interval is the 2.5th to 97.5th percentile of the resulting values.
  The bootstrap is seeded from the table seed, its seed is recorded as `bootstrap_seed`, and the interval is
  widened if need be so the fitted value lies inside it (ASM-17, D-16, `records.md` §11).
- **The fit is anchored by the three baselines, whose mean value is fixed at 0**, so every value reads as a
  distance from the only fixed standard in the table and two tables are comparable on one scale — and
  `anchor` names that rule so a reader is not left to infer it (D-16, ASM-17, `records.md` §11).
- **A member that won or lost every cell has no finite maximum-likelihood value**: the fit bounds it,
  `bound_applied` says the bound was applied, and the interval then states that the evidence pinned it
  (ASM-17, D-16, `docs/L1/league.md` §5). `converged` records the fit's convergence, and `values` gives each member
  the `hands_per_cell × (K−1)` hands behind its value (D-6, `records.md` §11).
- **The rating and the matrix travel together**, and the rating is fitted over one matrix, one cell size and
  one membership — a rank outside that table is a claim nothing here supports (D-16, `docs/L1/league.md` §8).

## 5. The two tables, and the one that ships

| Quantity | `live` | `full` |
|---|---|---|
| Membership | the frozen pool plus the rung's variants (K = 9 or 10) | exactly the same membership (D-16) |
| Hands per cell | 120, seats alternating | 1,500, seats alternating (ASM-14) |
| Hands played | 4,320 or 5,400 (ASM-14) | 54,000 or 67,500 (ASM-14) |
| Produced by | the talk, on the fly (D-8) | precomputed offline and shipped under `tables/` (D-16, D-8) |
| Per-cell resolution | about ±9 percentage points of win rate | about ±2.5 percentage points (ASM-14) |

- **One membership, two cell sizes**: the live table is the full table's skeleton read coarsely and not a
  different design, so a live order is a demonstration and the full table with the fitted intervals is what a
  claim rests on (D-16, ASM-14, `docs/L1/league.md` §6).
- **What ships is a data artefact under `tables/`**: one JSON document holding the `full` matrix record of
  `records.md` §10, the pool record of §8 it was measured over, and the rating record of §11 fitted to it, so
  its membership and its budget are recorded in the file and a third party can reproduce it with `matrix` and
  `rating` at the `full` budget (`module-map.md` §5, `records.md` §10–§11, D-8, D-16). No entry point reads
  `tables/` and none is invented for it (D-12): the file is evidence, and a D-5 notebook reads it with the
  standard library (`ladder.md` §7).
- **The budget is arithmetic on K, and the cost of playing it is a measurement**: ASM-21 ratifies the measured band **0.105–0.153 s
  of CPU per hand**, wide because the oracle decides it: 0.255–0.315 s/hand in an oracle-bearing cell against 0.002–0.004 without,
  and it sits in half a table's hands. The live table is ≈95–110 s at K = 4 (720 hands: 110.29 s at 0.1532 s/hand; 107.4 s
  re-measured) and ≈10–12 minutes at K = 9–10; the full table ≈2 hours (≈2¼–2¾ hours at that slowest rate), the shipped K = 4 `full`
  table's own `cost` block recorded 1,191.37 s (≈20 min) (ASM-21, ASM-15, ASM-14, D-16, D-8, `docs/L1/league.md` §7). `harness.timings`
  reports the measured figure and no case asserts a wall clock was beaten (`battery.md` §3 FAM-10); no per-hand figure
  travels in `league()`: a cost is a run record's `timings` and an artefact's `cost` block (`records.md` §12, `tables.md` §5).
- **`variant-1` is a slot, not a player.** `matrix` names a variant by the argument position it was handed
  (`surface.md` §10), so the shipped `full` table's `variant-1` and a live table's `variant-1` are two different
  learners: the shipped one is the offline producer's **untrained** learner at its recipe seed 31415, while the R1
  live run's is the rung's **trained** seed-0 final model at 10,119 parameters with `unlabelled: false`
  (`checkpoints/evidence/r1-live.json`, ASM-18). The two rows are **never compared**, not even as one member at two
  cell sizes; the artefact's `provenance.member_status` names which player every row is, and the untrained row's
  capacity is the producer's own measurement while the matrix block's `params: 0` with that id in `unlabelled` says
  only that `matrix` was handed a policy already built (`tables.md` §2, §5, `matrix.md` §5).

## 6. The evidence contract, and what a report refuses

`protocol()` declares the seven families of `protocol.md` §1 and `report` judges `records.md` §13's record
against them: a family that is absent is refused **by its own name**, never filled in (D-6, D-16,
`records.md` §13). An explicit `n/a` row is a value, never a blank (D-6, `records.md` §13).

| Evidence family | What the report must carry | The word its absence is refused with |
|---|---|---|
| curves | per variant, per seed: the sample axis and at least one learning signal from `agents.learn`, with the spread across seeds (D-6) | `curves` |
| pool | the frozen pool's id, M and ordered members with lineage, and one id where both arms of a pair trained (D-16, ASM-16) | `pool` |
| matrix | the §10 matrix at one table budget: one cell per pair, both directions, the hand count, the seat split and the mean chip delta per hand (D-16) | `matrix` |
| rating | the §11 rating: one value and a 95% interval per member, with the method, the anchor and the hands behind each value (D-16, ASM-17) | `rating` |
| baselines | the three baseline rows inside that matrix, each at the same hand count as every league cell (D-16, `protocol.md` §3) | `baselines` |
| axis row | R4, R5 and R6's own pair's cell plus the matched budgets of `ladder.md` §4; R1–R3 carry the explicit value `n/a, single variant` (`protocol.md` §1) | `axis row` |
| header | the game, the action space, every member's parameter counts, the sample budget, the cell size, the seed set, the table seed, the device and the checkpoint paths (D-6, `protocol.md` §1) | `header` |

Members are reported by the id the pool gave them and never by rank order alone, and the report carries the
seed set `0, 1, 2`, its matrix's table seed and the device the run used, so a GPU run and a CPU run are never
confused (D-6, `protocol.md` §1, §2, §6).

## 7. Contracts at this edge

Calls go one way along `module-map.md` §2's arrows, and each row below is what this module requires of the
module it calls, or grants to the one that calls it (D-13, `module-map.md` §2).

- **`agents`** — a table's members are `baselines()`'s three and the policies `build_baseline` and
  `as_policy` return; every member's capacity is `param_count`'s integer, and a baseline's is the `0` the
  catalogue declares (ASM-10, `records.md` §9). `load(None, path)` restores a member from its path alone and
  records the seed and the encoding `as_policy` needs, so `policy_from` builds the policy at the member's own
  seed and it decides as the saved learner decided (`agents/surface.md` §9, §10, `agents/learner.md` §4, §8,
  `protocol.md` §5). No baseline learns from a match, so no cell's opponent drifts while the table is played
  (D-6, `protocol.md` §3).
- **`features`** — `build_encoder` and `encode` are the two calls this module is granted, and they are why a
  checkpoint becomes a policy at all: an encoder is built for the encoding name a restore records, and a
  policy encodes its readout with it (D-16, `module-map.md` §2, `features/surface.md` §4, §6).
- **`engine`** — `new_hand` and `play_hand` are the only seeding point and the only deal, so a cell is a run
  of hands and nothing here re-deals or seeds twice; `readout`, `legal_actions` and `payoffs` are the facts a
  policy acts on and the chips a cell counts (D-2, ASM-2, `engine/surface.md` §1, §4, §9). **One measured
  exception.** A cell that pairs the `oracle` is *not* reproduced from its recorded seeds across processes: two
  runs of this module's own producer at one table seed, membership and budget gave different counts in the two
  oracle cells — as `random` reports its direction, 680/34/786 became 676/36/788, and `oracle` against
  `variant-1` 817/43/640 became 817/42/641 — while the four cells pairing no `oracle` were identical, and all
  four rating values moved with the fit. The cause is `engine.equity`'s sampled run-out deck, whose card order is
  a per-interpreter hash order, so a seed cannot carry `protocol.md` §4's exactness claim for that cell; a table
  that pairs the oracle must therefore be read as measured once and never as a replay
  (`protocol.md` §4, ASM-2, `tables.md` §4, FAM-10.2).
- **`training`** (the caller) — it freezes one pool through `build_pool`, draws each hand's opponent through
  `opponent`, and hands `report` a run record with the seven families attached; `protocol` and `league` are
  what it reads to declare its own budget, cell size and table seed (D-16, ASM-16, `records.md` §12, §13).
- **`tables/`'s producer** — the offline job that ships the `full` table (§5) stands where `training` stands,
  because a rung's variant policies are `training`'s to hand `matrix` and no entry point here builds one. `training`
  has shipped snapshot lineages, so a rung's own variants are its to hand over; the producer ships R1's table, and
  because a variant handed to `matrix` is a policy already built (`surface.md` §10), the one it has no rung to take
  from it builds itself with `agents.build_learner` at the recipe the artefact records, and that call is that offline
  job's alone (D-8, D-16, ASM-20, `module-map.md` §2). No entry point reads `tables/`, and the file is evidence for a
  notebook (§5).

## 8. The battery invariants this module carries

| Family | The entry points it drives | What is asserted here (`battery.md` §3) |
|---|---|---|
| FAM-6 | `league`, `build_pool`, `pool_members`, `offer` | at most M versions and always the three pinned baselines; `offer` drops the oldest evictable version and nothing else and changes the id; R1's pool is the baselines alone; one declaration yields one ordered membership (D-16, ASM-14, ASM-16) |
| FAM-7 | `match`, `opponent` | a cell accounts for every hand, seats alternate and the split covers both, both directions are the same hands and their deltas sum to zero, a cell plays the hand count it was given and carries two parameter counts and its seed, two cells are never interleaved, and `opponent` draws a pool member (D-16, ASM-2) |
| FAM-8 | `matrix` | membership is the pool plus the variants, the cells are exactly K(K−1)/2 pairs, every cell carries the table's one hand count with the baseline cells included, and an unequal cell, a missing baseline or a foreign member is refused (D-16, ASM-14) |
| FAM-9 | `rating` | one value and a 95% interval per member, Bradley-Terry, the anchor set so the baselines' mean is 0, the hands behind each value, a member that won everything bounded rather than infinite, and convergence and bootstrap seed recorded (D-16, ASM-17) |
| FAM-10 | `league`, `matrix` | both budgets declared with their cell sizes, the live table's hands played equal to cells × hands per cell, the cell count following from K, and a cost record carrying hands and seconds per hand (D-8, ASM-14, ASM-21) |
| FAM-11 | `report`, `protocol` | a complete record yields a report carrying all seven families, a record missing one is refused with that family named, R1's pool row is the baselines it had, a single-variant rung's axis row is an explicit value, and the report carries the seeds, the table seed and the device (D-6, D-16) |
| FAM-16 | the nine `general` rows | one invented instance apiece — a seed, a membership, a cell size, a checkpoint — from this surface alone (D-15, `battery.md` §4) |

The joins a single module cannot check are these: that the pool the loop samples is the pool the table
measures, that both arms of a pair held one pool, and that a table's rows are comparable because its cells
were played at one hand count (`battery.md` §5, D-16, ASM-16). No invariant here asserts a table's *values*:
a member outranking a baseline is what a run measures, not what this surface promises (D-6, `battery.md` §5).
