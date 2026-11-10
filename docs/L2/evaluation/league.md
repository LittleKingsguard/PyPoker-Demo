# evaluation — the league: pool, scheduler, matrix, rating, tables, report

- **Layer:** L2 · **Module:** `evaluation` · **Unit:** phase1 · **Rev:** 5 · **Date:** 2026-11-09 · §5, §7: the band and the
  direction, not the figure (ASM-23) · **Rev 4:** the id certifies each version's rule **and utility**, and the
  matrix states two populations (§1, §3 — D-20, `utilities.md` §7, §9) · **Rev 5:** D-21's catalogue — the pinned set is the
  catalogue's `anchor: True` members, a declaration may add the folders, and `league()` gains a `catalogue` key (§1, §3–§5)
- **Owner of this file:** the league itself — the bounded pool and its rolling window, the scheduler, the
  matrix, the rating, the two tables and the shipped `full` one, the seven evidence families the report is
  judged against, the contracts this module holds at its edge, and the battery invariants it carries
  (D-16, ASM-14, ASM-17, ASM-26, ASM-27, `battery.md` §3 FAM-6..FAM-11, FAM-16, FAM-18)
- **Ceiling:** 210 lines. At the ceiling, split by owner — never append

## 1. The pool

A pool is an ordered member list plus its bound, and it is both the opposition the training loop samples
and the table the agent is measured in — one object, one owner, no second evaluation pool (D-16,
`e2e-surface.md` §2, `module-map.md` §6, ASM-19).

- **Membership is at most M = 5 versions and always the three anchor baselines**, which are pinned and never
  evicted, plus a folding baseline when the declaration names one — so a pool holds between 3 and 8 members, one more
  per declared folder (`docs/L1/league.md` §2, D-16, ASM-14, ASM-32, D-21). M is the league's and `league()` declares
  it; a declaration may carry a **tighter** `m` and none may exceed M (D-16, `records.md` §8, `pool.md` §1).
- **The window is a set of families, ordered by lineage**: a family is one chain of a declaration's versions,
  its members under one rule and one utility, and the window lists each family's members contiguously oldest to
  newest, the families in the order they entered (ASM-26, `rules.md` §3, `utilities.md` §8, `records.md` §8). A declaration richer than the
  bound is windowed and never refused, unless it holds more families than the bound allows (D-16, ASM-18,
  ASM-26). A rung's own snapshots are what the next rung's window is built from, and `offer` advances a
  window by one version — extending one family — so rolling is a declared operation and not a training side
  effect (`protocol.md` §5, ASM-18, `records.md` §8).
- **Eviction is fair-share, so heterogeneity survives the bound**: the version that leaves a full window is
  the oldest member of the family that currently holds the most, so no family is emptied while another holds
  two or more, each family keeps a member while F ≤ M, and an offer that would open the (M+1)th family is
  refused by name rather than emptying one (ASM-26, `rules.md` §3, `pool.md` §3). A window holding one
  family still keeps the last `m` of its chain, which is what R1–R6's pools are (ASM-18).
- **R1's pool is the three baselines alone**, because R1 inherits no lineage: the report says so with the
  baselines it actually had and invents no version (`docs/L1/league.md` §2, `protocol.md` §5, `records.md` §13).
- **A pool is frozen before a rung's variants train and does not change while either arm trains or is
  tabled** — that is what makes D-16's "identical frozen pool" true of R4, R5 and R6 while D-3 keeps the rung
  to one axis (D-16, D-3, ASM-16): `build_pool` freezes what the declaration says to freeze, `offer` refuses
  a frozen pool, and `matrix` refuses one that is not frozen (`pool.md` §1, §3, `surface.md` §10).
- **The pool is deterministic and its id certifies both populations**: the id is a digest of one line per
  member — a baseline's bare id, a version's `id`, its `rule` and its `utility` — so it changes when and only when
  the membership does, a corrected seed or step does not rename it, two pools of one membership under two
  estimators or two objectives do not wear one id, and a declaration naming no folder keeps the id it has today
  (D-16, ASM-2, ASM-27, `records.md` §8, `utilities.md` §7, D-19, D-20, ASM-32, D-21).

## 2. The scheduler

- **One cell at a time.** A cell is one unordered pair played at the cell's hand count, hand after hand through
  `engine`, so two cells are never interleaved and none runs concurrently: concurrency is not a cost fix, and
  cost is bought with cell size alone (D-16, ASM-2, ASM-15, `protocol.md` §4).
- **`match` is the scheduler** (`surface.md` §9). The i-th hand of a cell at seed `s` is dealt at a seed
  derived from `s` and `i` alone, so one pair, one hand count and one seed give one cell however much was played
  before it, and the derivation may not draw from the global stream (ASM-2, `battery.md` §3 FAM-7, `protocol.md` §4).
  Its record carries a `rules` entry per member (`records.md` §9, D-19).
- **Seats alternate hand by hand**, so each member holds the button for half of them and the cell reports
  the split as two counts summing to `hands` and differing by at most one (D-16, `docs/L1/league.md` §3,
  `records.md` §9); a result that gives one member the button throughout is a positional artefact (`protocol.md` §1).
- **The two directions are the same hands seen from each seat**, so a cell costs its hand count and not twice
  it, and `directions` is position-aligned with `members`: one direction's wins are the other's losses, a
  tied hand is a tie for both, and the two mean chip deltas negate each other because the hand was zero-sum
  (ASM-14, `docs/L1/league.md` §3, `records.md` §9, ASM-12). A hand is a member's **win** when its net chip
  delta is positive, a **loss** when negative and a **tie** when zero (`protocol.md` §2, ASM-6).
- **Every cell of one table is played at one hand count, every baseline cell included**, so no member's
  row is measured more precisely than another's (D-16, `docs/L1/league.md` §3, `records.md` §10, D-21), and
  **`opponent` is the training loop's draw** from the same frozen pool (D-16, `module-map.md` §2, `surface.md` §8).

## 3. The matrix

- **Membership is the frozen pool plus the rung's variants**: K = |pool| + V, with V = 1 or 2, so K is 4 for
  R1, 9 for a single-variant rung with a full window and 10 for a two-variant rung with one — and **12 or 13** when
  the three folders are declared (ASM-14, ASM-33, `docs/L1/league.md` §4, `ladder.md` §2, `records.md` §10, D-21). The order is `pool_members`'s, then the variants in
  argument order, so one pool and one variant list have one membership (`surface.md` §10). Nothing here assumes the
  membership is three baselines plus a window: it is whatever the pool holds plus V (`docs/L1/folders.md` §4).
- **Every member carries its rule and its utility, and the table states both populations it measured**: the record
  names each member's rule and utility by its id — `None` for a baseline, which is a fixed rule and not an estimator
  or an objective — and its `population` and `utility_population`, the distinct rules and utilities those members
  declared, sorted (D-19, D-20, `records.md` §10, `utilities.md` §9); the rating reads none of those keys (`docs/L1/league.md` §4).
- **The cells are exactly K(K−1)/2 unordered pairs** — 6, 36 or 45, and **66 or 78** with the folders declared — one cell per pair and no
  repeat (D-16, ASM-14, ASM-33, D-21, `records.md` §10). Each cell's seed is derived from the table seed and the pair, and each member's
  policy is built at a seed derived from the table seed and its position, so a table is reproduced from its table seed and its membership and from nothing else (ASM-2, `battery.md` §3 FAM-8).
- **The baselines are rows and columns at that same hand count** — always the three anchors and, when the declaration
  names them, the three folders — and their mutual cells are in the table, so the matrix carries cells no model influences,
  the only fixed standard a self-play league has (D-16, `protocol.md` §3, `docs/L1/league.md` §4, D-21).
- **A matrix that is not a table is refused, not repaired**: cells of differing hand count, a cell count other than K(K−1)/2, a pair
  present twice, a membership that is not the pool's plus the variants, a cell naming a foreign member, a missing baseline, or cells
  naming two shapes (`docs/L1/league.md` §4, `records.md` §10, D-16). `matrix` refuses a variant count, a label, an unfrozen pool or a
  variant whose shape is not the pool's (`surface.md` §10); `rating` refuses everything else on the record it is handed, whatever produced
  it (`surface.md` §11); `report` refuses a matrix whose membership is not the record's pool plus the rung's variants (`surface.md` §13).
  A matrix is one shape's: its record and every cell of it carry the `game` it was played on (`shapes.md` §6, `surface.md` §10).
- **The matrix is reported raw and is never reduced to a ranking**: both directions of every cell, its
  counts, chip deltas and seat split, because a summary that assumes a transitive order is exactly what a
  payoff need not have (D-16, `docs/L1/league.md` §4, `protocol.md` §2).

## 4. The rating

- **The fitted rating is Bradley-Terry**, fitted over the matrix's cells on each cell's win/tie/loss counts
  with a tie counted as half a win to each side (ASM-17, D-16, `docs/L1/league.md` §5). It is a statement
  about the table's named members on this game at this cell size, and **never a claim of poker skill**
  (D-16, `docs/L1/league.md` §8, brief §8). It is a function of the matrix and does not read `rules`, `population`,
  `utilities` or `utility_population` (`records.md` §10, D-19, D-20), and it reads K members whatever K is — but **one shape's**
  cells only: a matrix whose cells name two shapes is refused naming them, and the returned record carries the one shape it fitted,
  so two shapes' ratings are never tabulated together (`shapes.md` §6, ASM-17, `surface.md` §11).
- **Each member carries a 95% confidence interval from a hand-level bootstrap**: the hands inside each cell
  are resampled, the fit repeated, and the interval is the 2.5th to 97.5th percentile of the resulting values.
  The bootstrap is seeded from the table seed, its seed is recorded as `bootstrap_seed`, and the interval is
  widened if need be so the fitted value lies inside it (ASM-17, D-16, `records.md` §11).
- **The fit is anchored by the catalogue's three flagged baselines, whose mean value is fixed at 0**, so every value reads as a
  distance from the only fixed standard in the table, and `anchor` names them — `random`, `always-call`, `oracle` — so a reader is not left to
  infer it and no folding baseline D-21 adds is ever in it (D-16, ASM-17, ASM-32, D-21, `records.md` §11).
- **A member that won or lost every cell has no finite maximum-likelihood value**: the fit bounds it,
  `bound_applied` says the bound was applied, and the interval then states that the evidence pinned it
  (ASM-17, D-16, `docs/L1/league.md` §5). `converged` records the fit's convergence, and `values` gives each member
  the `hands_per_cell × (K−1)` hands behind its value (D-6, `records.md` §11); the rating and the matrix travel
  together, and a rank outside that table is a claim nothing here supports (D-16, `docs/L1/league.md` §8).

## 5. The two tables, and the one that ships

| Quantity | `live` | `full` |
|---|---|---|
| Membership | the frozen pool plus the rung's variants (K = 9 or 10; 12 or 13 with the folders declared) | exactly the same membership (D-16, ASM-33) |
| Hands per cell | 120, seats alternating | 1,500, seats alternating (ASM-14) |
| Hands played | 4,320 or 5,400; 7,920 or 9,360 with the folders declared (ASM-14, ASM-33) | 54,000 or 67,500; 99,000 or 117,000 (ASM-14, ASM-33) |
| Produced by | the talk, on the fly (D-8) | precomputed offline and shipped under `tables/` (D-16, D-8) |
| Per-cell resolution | about ±9 percentage points of win rate | about ±2.5 percentage points (ASM-14) |

- **One membership, two cell sizes**: the live table is the full table's skeleton read coarsely, so a live
  order is a demonstration and the full table with the fitted intervals is what a claim rests on (ASM-14, D-16).
- **What ships is a data artefact under `tables/`**: one JSON document holding the `full` matrix record of
  `records.md` §10, the pool record of §8 it was measured over, and the rating record of §11 fitted to it —
  evidence read with the standard library, which no entry point reads and none is invented for (D-12, `module-map.md` §5, D-8, D-16, `ladder.md` §7).
- **The budget is arithmetic on K, and the cost of playing it is a measurement**: ASM-21 ratifies the measured band **0.105–0.153 s of CPU per hand**, wide
  because the oracle decides it — 0.255–0.315 s/hand in an oracle-bearing cell against 0.002–0.004 without, in half a table's hands — so the live table is
  ≈95–110 s at K = 4 and ≈10–12 minutes at K = 9–10 (≈7–20 minutes to ≈1.4–3.6 hours at K = 12), and the full one ≈20 min at K = 4 and ≈2 hours at K = 9–10.
  **`league()` carries no per-hand figure and this page quotes no build's measured seconds** (ASM-23): each artefact keeps its own — the live table's `stages.matrix_live` in `checkpoints/evidence/r1-live.json`,
  the `full` table's `cost` block in `tables/league-full.json` — and `harness.timings` reports the measured figure, no case asserting a wall clock was beaten
  (`battery.md` §3 FAM-10, ASM-21, ASM-15, ASM-14, ASM-33, D-16, D-8, `docs/L1/league.md` §7, `docs/L1/folders.md` §5).
- **`variant-1` is a slot, not a player.** `matrix` names a variant by the argument position it was handed
  (`surface.md` §10), so the shipped `full` table's `variant-1` and a live table's `variant-1` are two different
  learners — the producer's **untrained** learner at its recipe seed against the rung's **trained** seed-0 final
  (`checkpoints/evidence/r1-live.json`, ASM-18). The two rows are **never compared**, not even as one member at two
  cell sizes, and `provenance.member_status` names which player each is (`tables.md` §2, §5, `matrix.md` §5).

## 6. The evidence contract, and what a report refuses

`protocol()` declares the seven families of `protocol.md` §1 and `report` judges `records.md` §13's record
against them: a family that is absent is refused **by its own name**, never filled in, and an explicit `n/a`
row is a value and never a blank (D-6, D-16, `records.md` §13).

| Evidence family | What the report must carry | The word its absence is refused with |
|---|---|---|
| curves | per variant, per seed: the sample axis and at least one learning signal from `agents.learn`, with the spread across seeds (D-6) | `curves` |
| pool | the frozen pool's id, M and ordered members with lineage, the `rules` and `utilities` its versions declare, and one id where both arms of a pair trained (D-16, ASM-16, records.md §8, D-19, D-20) | `pool` |
| matrix | the §10 matrix at one table budget: one cell per pair, both directions, the hand count, the seat split and the mean chip delta per hand (D-16) | `matrix` |
| rating | the §11 rating: one value and a 95% interval per member, with the method, the anchor and the hands behind each value (D-16, ASM-17) | `rating` |
| baselines | every baseline row of the catalogue the configuration declares inside that matrix — always the three anchors, and the three folders of D-21 when it names them — each at the same hand count as every league cell (D-16, `protocol.md` §3, ASM-32, D-21) | `baselines` |
| axis row | R4, R5 and R6's own pair's cell plus the matched budgets of `ladder.md` §4; R1–R3 carry the explicit value `n/a, single variant` (`protocol.md` §1) | `axis row` |
| header | the game's configuration, **the shape it is** — the one shape the run, the pool and the matrix agree on —, the action space, every member's parameter counts, the sample budget, the cell size, the seed set, the table seed, the device and the checkpoint paths (D-6, `protocol.md` §1, `shapes.md` §3, D-29) | `header` |

Members are reported by the id the pool gave them and never by rank order alone, and the report carries the
seed set `0, 1, 2`, its matrix's table seed and the device the run used, so a GPU run and a CPU run are never
confused (D-6, `protocol.md` §1, §2, §6). The pool family and the header also name the rules and utilities the measured
population held, and no family is added for them: a report gains **no new required content item**, which would refuse records other batteries hand-build (`rules.md` §4, `errors.md` §5, D-19, D-20).

## 7. Contracts at this edge

Calls go one way along `module-map.md` §2's arrows, and each row below is what this module requires of the module it calls, or grants to the one that calls it (D-13, `module-map.md` §2).

- **`agents`** — a table's members are `baselines()`'s catalogue — the three anchors in every pool, a folder when a
  declaration names it — and the policies `build_baseline` and `as_policy` return; every member's capacity is `param_count`'s integer, and a baseline's is the `0` the
  catalogue declares (ASM-10, `records.md` §9, ASM-32, D-21). `load(None, path)` restores a member from its path alone and
  records the seed and the encoding `as_policy` needs, so `policy_from` builds the policy at the member's own
  seed and it decides as the saved learner decided (`agents/surface.md` §9, §10, `agents/learner.md` §4, §8,
  `protocol.md` §5). No baseline learns from a match, so no cell's opponent drifts while the table is played
  (D-6, `protocol.md` §3).
- **`features`** — `build_encoder` and `encode` are the two calls this module is granted, and they are why a
  checkpoint becomes a policy at all: the encoder is built for the encoding name a restore records
  (`module-map.md` §2, `features/surface.md` §4, §6).
- **`engine`** — `new_hand` and `play_hand` are the only seeding point and the only deal, so a cell is a run
  of hands and nothing here re-deals or seeds twice; `readout`, `legal_actions` and `payoffs` are the facts a
  policy acts on and the chips a cell counts (D-2, ASM-2, `engine/surface.md` §1, §4, §9). **One measured
  exception.** A cell that pairs the `oracle` is *not* reproduced from its recorded seeds across processes: two runs of the
  producer at one table seed, membership and budget gave different counts in the `oracle`-pairing cells, because `engine.equity`'s
  run-out deck is drawn in a per-interpreter hash order — measured in `docs/L3/training/evidence.md` §6, and no count of it is
  quotable here (ASM-23), so such a table is read as measured once and never as a replay (`protocol.md` §4, ASM-2, `tables.md` §4, FAM-10.2).
- **`training`** (the caller) — it freezes one pool through `build_pool`, draws each hand's opponent through
  `opponent`, declares its variants' rules and hands `report` a run record with the seven families attached
  (D-16, ASM-16, `records.md` §12, §13, D-19).
- **`tables/`'s producer** — the offline job that ships the `full` table (§5) stands where `training` stands:
  a rung's variant policies are `training`'s to hand `matrix`, and the producer ships R1's table by building its
  own untrained learner at the recipe the artefact records — that call is the offline job's alone (D-8, D-16,
  ASM-20). It builds a **baselines-only** pool and declares no rule of its own, so the rule's arrival needs no
  change in the producer; no entry point reads the file, and it is evidence for a notebook (§5).

## 8. The battery invariants this module carries

| Family | The entry points it drives | What is asserted here (`battery.md` §3) |
|---|---|---|
| FAM-6 | `league`, `build_pool`, `pool_members`, `offer` | at most M versions and always the three pinned anchor baselines; a declaration's `baselines` adds a folder after them and in the catalogue's order, and a name the catalogue lacks is refused by name; a member declares its rule and a pool record the `rules` it holds; the id digests each version's rule and a baselines-only pool keeps its id; a second family is accepted and fair-share eviction leaves one member of each; the (m+1)th family is refused; R1's pool is the baselines alone (D-16, ASM-14, ASM-16, ASM-26, ASM-27, ASM-32, D-21) |
| FAM-7 | `match`, `opponent` | a cell accounts for every hand, seats alternate and the split covers both, both directions are the same hands and their deltas sum to zero, a cell plays the hand count it was given and carries two parameter counts, its `rules`, its seed and its `utilities` (FAM-18.10), two cells are never interleaved, and `opponent` draws a pool member (D-16, ASM-2, D-19, D-20) |
| FAM-8 | `matrix` | membership is the pool plus the variants, the cells are exactly K(K−1)/2 pairs, every cell carries the table's one hand count with the baseline cells included, the table names each member's rule and the `population` it measured, and each member's utility and the `utility_population` it measured (FAM-18.10), and an unequal cell, a missing baseline or a foreign member is refused (D-16, ASM-14, `records.md` §10, D-19, D-20) |
| FAM-9 | `rating` | one value and a 95% interval per member, Bradley-Terry, the anchor set so the flagged three baselines' mean is 0 and never a declared folder, the hands behind each value, a member that won everything bounded rather than infinite, and convergence and bootstrap seed recorded (D-16, ASM-17, ASM-32, D-21) |
| FAM-10 | `league`, `matrix` | both budgets declared with their cell sizes, the live table's hands played equal to cells × hands per cell, the cell count following from K, and a cost record carrying hands and seconds per hand (D-8, ASM-14, ASM-21) |
| FAM-11 | `report`, `protocol` | a complete record yields a report carrying all seven families, a record missing one is refused with that family named, R1's pool row is the baselines it had, the pool family names the rules the measured population held, a single-variant rung's axis row is an explicit value, and the report carries the seeds, the table seed and the device (D-6, D-16, D-19) |
| FAM-16 | the nine `general` rows | one invented instance apiece — a seed, a membership, a cell size, a checkpoint — from this surface alone (D-15, `battery.md` §4) |
| FAM-18 | `build_pool`, `pool_members`, `match`, `matrix` | a member's uncatalogued utility is refused by `build_pool` and a version's utility is digested into the pool's id; a cell names each member's utility; and a table over two utility populations carries each member's utility and the `utility_population` it measured (D-20, `utilities.md` §7, §9, `records.md` §8–§10) |

The joins a single module cannot check are these: that the pool the loop samples is the pool the table
measures, that both arms of a pair held one pool and were asked one question each per axis, that a table's rows are
comparable because its cells were played at one hand count, and that a member's record, its checkpoint and the pool's `rules` and `utilities` agree (D-16, ASM-16, ASM-26, D-20).
