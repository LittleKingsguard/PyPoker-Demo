# evaluation — the callable surface

- **Layer:** L2 · **Module:** `evaluation` · **Unit:** phase1 · **Rev:** 7 · **Date:** 2026-11-10
- **Ceiling:** 260 lines. At the ceiling, split by owner — never append
- **Owner of this file:** the surface — the eleven module-level names of `src/evaluation/`, each with its argument contract, its returned
  record, its refusals and its determinism (D-12, `e2e-surface.md` §1, §3.4)
- **Rev 2–5:** §12 reads a checkpoint's recorded seed and encoding from its container (ASM-20); D-19's rule and D-20's utility reach
  every record — a member declares `rule` and `utility`, a window is grouped into families and evicts fair-share, the id digests both,
  a side is six elements — and D-21 makes the **pinned** set the catalogue's `anchor: True` members, adds `league()`'s `catalogue` and
  a declaration's optional `baselines` (§2–§4, §11, §13, `rules.md` §2–§3, `utilities.md` §5–§9, ASM-20, ASM-32)
- **Rev 6:** D-29's second shape at the edge — every record names **one shape** and refuses a second one by name, and `policy_from`
  gains the exploration mode `off` (§2, §5–§13, `shapes.md` §3, §6, `sizing.md` §4)
- **Rev 7:** D-33's seat count at the edge — the catalogue restates **three** names, `opponent` takes an optional draw count and
  four entry points refuse a shape with more than two seats; the seat count has its own owner, `seats.md` §1–§4
  (§2, §8, §9–§13, `docs/L1/seats.md` §2–§5, ASM-43, D-33)

## 1. Rules that hold of every entry point

Each of the eleven names is a module-level name of the `evaluation` package, and nothing below one of them is contract
(`e2e-surface.md` §1, brief §5). Six rules are shared and are stated here once (D-12, D-13):

- The eleven names are fixed, and each one keeps the arguments `e2e-surface.md` §3.4 declares: L2 refines types, record keys,
  defaults and error classes and never adds, removes or renames an entry point or a positional argument. A widening is an
  **optional** argument or key whose absence reproduces today's value — `shape`, `exploration`, `count` — and never a twelfth
  name or a required one (`e2e-surface.md` §1, `shapes.md` §4, `seats.md` §6, D-12, D-33).
- An invalid argument is refused by raising an error that names the violated contract; no entry point coerces a value,
  substitutes a default, swallows an error or returns part of a record (`e2e-surface.md` §2).
- `protocol` and `league` take no argument, so their one instance is the project's and cannot be varied (D-6, D-16,
  `e2e-surface.md` §5); the other nine are defined for any valid instance (D-15, `battery.md` §4).
- Play is the only thing that moves Python's global `random` stream, and only through `engine.new_hand` (ASM-2, `protocol.md` §4,
  `engine/surface.md` §4): the nine entry points that play nothing leave it where they found it, while `rating`'s bootstrap draws
  from its own generator seeded from the table seed and records that seed (ASM-17, ASM-2).
- A returned value is plain data except three: a pool, a policy, and the callable `league()` declares. A pool and a policy are
  opaque values a caller only passes back, and no record returned here exposes one (`e2e-surface.md` §1, D-1).
- A record returned here carries the keys `records.md` marks **required** and, beyond them, only this module's own keys, which no
  caller may depend on (`records.md` §1, D-13). Exactness is promised on CPU: one `(configuration, seed set, budget, pool
  membership, shape)` reproduces a table value for value (`protocol.md` §4), with the measured exception `league.md` §7 records for
  a cell pairing the `oracle`.

This module never trains and never edits a curve; it owns the pool, plays the cells and assembles the evidence (`module-map.md` §3,
D-16). It calls `agents`, `features` and `engine` and no fourth module: the run record, the rung label, the shape the run was played
on and the record's families arrive as data (`module-map.md` §2, D-13).

## 2. The shape, the policy and the member at this edge

- A **shape** is one row of `engine.game_shapes()`, named by a string, default first: `fixed-limit-20` is the default and what a record
  naming none is read as, in this module's declaration, its members, its cells, its matrix, its rating, its report and its containers
  alike (`shapes.md` §2–§3, `sizing.md` §6). A name outside the catalogue is refused **naming it and the declared names** and never
  defaulted; two declarations of one shape that disagree are refused **naming both** (`ShapeMismatch`). The **three** names are read off
  this module's own declaration and held equal to `engine.game_shapes()` by the join battery; a shape's **seat count** is the one fact
  this module reads through `engine.game_config` instead of restating (`module-map.md` §2, `seats.md` §1, D-13, D-33).
- A **policy** is a callable taking `(readout, legal_actions)` and returning one descriptor from `legal_actions`; a policy that returns
  an illegal descriptor is a contract violation and never a fold (D-2, `e2e-surface.md` §2). This module calls policies and imports
  none: `policy_from` and `opponent` return one, and `agents.as_policy` and `agents.build_baseline` return the ones it loads and draws
  (`module-map.md` §2). A policy built from a learner also carries `learning_rule`, `utility` and **`game`** — the catalogue members
  its model learned under and was trained on, and the shape whose vocabulary it decodes its index in (`rules.md` §7, `utilities.md`
  §7, `shapes.md` §3, D-19, D-20, D-29). A baseline carries none of the three and records no shape: a baseline side of a **cell** is
  **shape-silent** and plays the shape the cell is on, while a pool builds its own baselines for the pool's shape (§9, `seats.md` §4).
- A **member** is a version — a checkpoint with `records.md` §7's record, its `rule`, its `utility` and its `game` included — or one of
  the catalogue's baselines a pool pins: the three anchor ones always, and a folding baseline only when the declaration names it
  (`e2e-surface.md` §2, `docs/L1/league.md` §2, D-16, D-20, ASM-32, D-21). No cell is played against a policy that is not a named
  member. A cell, a matrix and a rating name their members by **id** and never by rank order (`protocol.md` §1, `records.md` §7, §9,
  §10). A version member's `game` is **required of a non-default member and absent for a default-shape one**, read off its
  container's `game` field, which only a version-4 container carries (`records.md` §7, `sizing.md` §6).
- A side is named by its member record whenever this module holds one: a pool member, one of the catalogue's baseline names given in
  the call, or a checkpoint `policy_from` loaded. A callable handed in from outside carries none, so it is named for its position —
  `policy-1`, `policy-2` — and its capacity is recorded as unmeasured, which the cell states in `unlabelled`: an opaque policy cannot
  be asked for a parameter count, and this module invents no number it did not measure (`agents/surface.md` §1, §5, ASM-10).
- `params` therefore carries one integer per member: `agents.param_count` of the learner behind a member this module built; `0` for a
  baseline; and `0` for an unlabelled policy, so a reader tells a measured zero from an unmeasured one (`records.md` §9, ASM-10).

## 3. `protocol` — the evidence contract (`fixed` row)

- **Signature:** `protocol()`.
- **Arguments:** none: the protocol is D-6's and D-16's, so no argument can vary it (`protocol.md` §1, `e2e-surface.md` §3.4).
- **Returns:** one mapping read under these keys — `families` (the seven of `protocol.md` §1, in its order: `curves`, `pool`, `matrix`,
  `rating`, `baselines`, `axis row`, `header`, each value a record of that family's `required` items and the `refusal` its absence is
  named by), `seeds` (`0, 1, 2`), `header` (the nine items `protocol.md` §1 requires of a **record**: the game, the action space, the
  parameter counts, the sample budget, the cell size, the seed set, the table seed, the device, the checkpoint paths), `table_budgets`
  (`live`, `full`), `baselines` (the **pinned** three — the `anchor: True` members of `agents.baselines()`, which are D-6's three and
  never a folder, so D-21 leaves the key unchanged, ASM-32) and `rating` (the method, the interval's confidence and the anchor,
  `docs/L1/league.md` §5). A report's header family carries one fact beyond these nine — the shape — and §13 has the report resolve it
  from the run, the pool and the matrix rather than demand it of a record, so this list is unchanged and every record already on disk
  stays reportable (`shapes.md` §3).
- **Refusals:** none; it has no argument (`e2e-surface.md` §3.4).
- **Determinism and ordering:** two calls return equal records, written in this order and in `protocol.md` §1's, the seven family names
  spelled exactly as `protocol.md` §1 spells them (`battery.md` §3 FAM-4, FAM-11).

## 4. `league` — the league's parameters (`fixed` row)

- **Signature:** `league()`.
- **Arguments:** none: M, the cell sizes and the table seed are ASM-14's and no parameter varies them (D-16, `assumptions.md`
  ASM-13–ASM-15). No shape is a league parameter either: a table is one shape's, and the shape is the pool's (`shapes.md` §6).
- **Returns:** one mapping read under these seven keys, in this order — `m` = 5; `baselines` (the **pinned** three, its meaning
  unchanged by D-21); `catalogue` (all six names `agents.baselines()` declares, in the catalogue's order — the names a membership
  declaration may add beyond the pinned set, `records.md` §8, ASM-32, D-21); `tables`, keyed `live` and `full`, each carrying
  `hands_per_cell` (120 and 1,500), the `hands_played` a K = 9 and a K = 10 membership costs (4,320 or 5,400 live, 54,000 or 67,500
  full) and what produces it (the talk on the fly, or an offline job shipped under `tables/`); `cell_count`, a callable taking K or a
  membership and returning K(K−1)/2, so a talk sizes its table before it plays one; `table_seed`, the one integer every matrix is played
  from; and `rating`, the method, the 95% interval and the anchor.
- **Refusals:** none (`e2e-surface.md` §3.4).
- **Determinism:** two calls return equal records, and the numbers are `docs/L1/league.md` §6's table and no other — and no per-hand cost
  figure at all, since ASM-21 supersedes ASM-15's bound (ASM-14, ASM-21). A talk that declares the three folders counts 66 or 78 cells
  rather than 36 or 45 (`docs/L1/folders.md` §5, ASM-33).

## 5–8. The four pool entry points — `pool.md`

`build_pool`, `pool_members`, `offer` and `opponent` are §5–§8 of the surface, and each one's arguments, returned record, refusals and
determinism are **`pool.md` §1–§4** — the one carrier of them since D-19 added a member's `rule`, D-20 its `utility` and D-29 the
pool's `game`, the families a window is grouped into and the id that certifies each version's rule and utility to all four (`pool.md`
§1, `rules.md` §2–§3, `utilities.md` §5–§7, ASM-26, ASM-27, `shapes.md` §3). What this file keeps of them is the boundary: a pool is an
**opaque value** a caller only passes back (§1); `pool_members` returns `records.md` §8's record, `id`, `m`, `frozen`, `game`,
`members`, `rules` and `utilities` included (`records.md` §8); and `offer` returns a **new** pool, leaving its argument unchanged,
refusing a version of another shape, with the pool's **id not digesting the shape** — two pools of one membership on two shapes share
one id and are never one table (`surface.md` §1, `pool.md` §1–§3, `shapes.md` §3, ASM-27, D-12). `opponent`'s third argument — the
**draw count** — and the two refusals it adds are `pool.md` §4's and `seats.md` §2's (`docs/L1/seats.md` §4, ASM-43).

## 9. `match` — the scheduler's one cell (`general` row)

- **Signature:** `match(left, right, hands, seed)` — four arguments and no fifth: the cell's shape is the one its sides name, never an
  argument this call accepts (`e2e-surface.md` §3.4, `shapes.md` §4).
- **Arguments:** two policies or two member records — a §7 version record, or one of the three baseline names; `hands`, a positive
  integer; `seed`, an integer (`e2e-surface.md` §3.4).
- **Returns:** `records.md` §9's cell record — `members` (the two ids in argument order), `hands`, `directions` (two entries,
  position-aligned with `members`, each carrying `wins`, `ties`, `losses`, `mean_chip_delta` and `seat_split`), `params` (§2), `rules`
  and `utilities` — each member's rule and utility **by id**: the catalogue names its policy carries, `None` for a baseline and for an
  opaque policy that carries neither, so a cell says which estimators and which objectives met — `seed` (`records.md` §9, `rules.md`
  §4, `utilities.md` §7, §9, D-19, D-20) and **`game`**, the one shape the hands were played on: this module's own key, which
  `records.md` §9 does not require and which a cell of two shape-silent sides carries as the default (`shapes.md` §3, §6).
- **Behaviour:** it is the scheduler, and `docs/L1/league.md` §3 fixes what it does — one cell at a time, seats alternating, both
  directions from one set of hands, a cell costing its hand count and not twice it (D-16, ASM-14). Its shape is the one its sides name:
  a version member's `game`, a policy's `game`, and a baseline's or an opaque callable's **none** — so a cell between two baselines is
  played on the **default** shape exactly as it is today, and a baseline opposite a version plays that version's shape (`shapes.md` §3).
- **Refusals:** a value that is neither callable nor a member; a hand count that is not a positive integer; a seed that is not an
  integer; two members carrying one id, because a cell pairs two distinct members (`records.md` §9, `docs/L1/league.md` §3); a member
  **record** whose declared `rule`, `utility` or `game` contradicts what its checkpoint records, naming the member and both values
  (`RuleMismatch`, `UtilityMismatch`, `ShapeMismatch`, §12, `shapes.md` §3, D-20); a pair whose two sides name **two shapes**,
  naming both sides and both shapes, because a cell is played on one game (`ShapeMismatch`, `shapes.md` §6); and a shape whose seat
  count is above the pairwise instrument's, refused after the cell's one shape is resolved and before its first hand, naming the
  shape and its seat count (`SeatCountExceeded`, `seats.md` §3, `docs/L1/seats.md` §5, D-33). An illegal descriptor from
  either policy is `engine`'s refusal and is not caught or repaired here (D-2).
- **Determinism:** one pair, one hand count and one seed give one cell, whatever was played before it, and a different seed deals
  different hands (`battery.md` §3 FAM-7, FAM-4, ASM-2); the shape adds no draw, no seed and no policy build, so a cell of two
  shape-silent sides is the cell it was before the shape existed.

## 10. `matrix` — the pairwise table (`general` row)

- **Signature:** `matrix(pool, variants, table)`.
- **Arguments:** a frozen pool; the rung's one or two variant policies; and a table budget, `live` or `full` (`ladder.md` §2,
  `docs/L1/league.md` §4, §6). The table's shape is the **pool's**, never an argument (`shapes.md` §6).
- **Returns:** `records.md` §10's matrix record — `members` (the membership **by id**, the pool's members in `pool_members`'s order and
  then the variants as `variant-1`, `variant-2` in argument order), `cells` (exactly K(K−1)/2 §9 records, one per unordered pair, each
  carrying the table's `game`), `rules` and `utilities` (each member's rule and utility by id), `population` and `utility_population`
  (the distinct rules and utilities those members declared, **sorted**), `hands_per_cell` (the one hand count of §4's `tables`, the
  baseline cells included), `table_seed` (the league's) and `table` (the budget), plus this module's own keys — **`game`**, the shape the
  table was played on, which `records.md` §10 does not list and which this entry point **requires** of what it returns so that no reader
  infers it (`records.md` §10, `shapes.md` §6) — the pool's id and each member's record among them (`docs/L1/league.md` §4,
  `utilities.md` §7, §9, D-19, D-20).
- **Refusals:** a pool that is not frozen, naming it, because a pool does not change while it is tabled (`docs/L1/league.md` §2, §4,
  `records.md` §8); a pool member the declaration gave no `path`, naming the member (`records.md` §7, `protocol.md` §5); a variant count
  other than one or two, or a variant that is not a policy, naming it (`ladder.md` §2, `docs/L1/league.md` §4); a membership that is not
  distinct — two members carrying one id, which no cell can pair (§9, `records.md` §9); a `table` label that is not `live` or `full`
  (`records.md` §10, `docs/L1/league.md` §6); a **variant whose `game` is not the pool's**, naming the variant's slot and both shapes,
  because a table is measured on one shape (`ShapeMismatch`, `shapes.md` §6); and a **pool on a shape with more seats than a pair
  has**, refused before a variant is looked at and before a checkpoint is touched, naming the shape and its seat count
  (`SeatCountExceeded`, `seats.md` §3, `docs/L1/seats.md` §5, D-33). A version record whose `rule`, `utility` or `game`
  contradicts its own checkpoint's is `RuleMismatch`/`UtilityMismatch`/`ShapeMismatch`, before a cell is played (§12, `utilities.md`
  §6, D-20).
- **Determinism:** one pool, one variant list and one budget give one matrix: every cell's seed is derived from the table seed and the
  pair, and every policy the table builds is built at a seed the table fixes — a baseline at a seed derived from the table seed and its
  position, a version member at the seed its checkpoint records (§12), because one checkpoint is one player; the variants are the
  caller's own policies (`docs/L1/league.md` §3, ASM-2, `protocol.md` §5, `battery.md` §3 FAM-8). The shape moves none of them: a table
  on the second shape is a table of its own, never a re-measurement of one on the default (`shapes.md` §6).

## 11. `rating` — the fitted rating (`general` row)

- **Signature:** `rating(matrix)`.
- **Arguments:** a matrix record in `records.md` §10's shape — this module's own or a hand-built one, because what is checked is the
  record and not its provenance (`records.md` §10, `docs/L1/league.md` §4).
- **Returns:** `records.md` §11's rating record — `values` (one entry per matrix member, keyed by the member's id, each carrying the
  fitted value, the two bounds of its 95% interval and the hands behind it: `hands_per_cell × (K−1)`), `method` = `Bradley-Terry`,
  `anchor` = the **pinned** three's mean fixed at zero — one string, naming the baselines it zeroes the fit on (`random`,
  `always-call`, `oracle`) and never a folder (ASM-32, D-21) — `bound_applied`, `bootstrap_seed` and `converged` (`records.md` §11,
  `docs/L1/league.md` §5, ASM-17) — plus this module's own **`game`**: the shape whose cells it fitted, so two shapes' ratings are never
  tabulated together (`shapes.md` §6, ASM-17). The arithmetic is unchanged by the shape: the fit reads the cells' counts and never a game
  parameter, a rule or a utility (`docs/L1/league.md` §4).
- **Refusals:** a matrix that is not a table — a cell whose hand count differs from `hands_per_cell`, a cell count other than K(K−1)/2,
  a pair present twice, a missing one of the pinned three, a member a cell names that the membership does not, or an absent
  `hands_per_cell`, `table_seed` or `table` label — each naming the violated rule, and nothing is fitted anyway (`docs/L1/league.md`
  §4, `records.md` §10, D-16); and a matrix whose **cells name more than one shape**, or whose own `game` is not the shape its cells
  name, refused naming the shapes (`ShapeMismatch`), because a rating is fitted over **one shape's** cells and reads as a distance from
  that game's baselines (`shapes.md` §6, ASM-17); and a table on a shape whose seat count is above the pairwise instrument's, refused
  with the record's other table checks and before a value is fitted, naming the shape and its seat count (`SeatCountExceeded`,
  `seats.md` §3, `docs/L1/seats.md` §5, D-33).
- **Determinism:** one matrix gives one rating: the fit is deterministic and the bootstrap is seeded from the table seed, whose value
  the record carries (ASM-17, ASM-2); it states where a member stands among the table's named members at this cell size and is never a
  claim of poker skill (D-16, `docs/L1/league.md` §5). An absent `game` on the matrix or on a cell reads as the default shape, which is
  what keeps every table and every rating already recorded ratable (`shapes.md` §3).

## 12. `policy_from` — a checkpoint as a policy (`general` row)

- **Signature:** `policy_from(path, exploration="schedule")` — the mode is optional and its absence is today's behaviour
  (`e2e-surface.md` §3.4, `sizing.md` §4).
- **Arguments:** one checkpoint path `agents.save` wrote; and the exploration mode, one of the two `agents.as_policy` declares:
  **`schedule`**, the default, where a decision is the keyed draw of the exploration schedule, and **`off`**, where it is the masked
  maximum and the tie-break alone and **no generator is drawn from** — the greedy reading `sizing.md` §7's census is computed over
  (`sizing.md` §4, `shapes.md` §4, D-29). A member is loadable from its path alone, which is why a checkpoint records the seed, the
  encoding and the shape it was built at (`e2e-surface.md` §3.4, `records.md` §7).
- **Returns:** a policy in the sense of §2 — a member policy carrying the member record it was loaded for, so a cell names it and
  reports its capacity (§2, `records.md` §7), and carrying **`learning_rule`**, **`utility`** and **`game`**: the catalogue members its
  learner was built under and trained on, and the shape its container records, which the policy `agents.as_policy` built reports
  (`rules.md` §6, `utilities.md` §6, `shapes.md` §3, §3.4 of `e2e-surface.md`, D-19, D-20, D-29). It is `agents.as_policy` of
  `agents.load(None, path)` over the encoder `features.build_encoder` makes **for the recorded name and the recorded shape**, at the
  seed the checkpoint records and with the mode it was handed (`agents/surface.md` §9, §10, `protocol.md` §5, ASM-5). All three facts
  are read from the checkpoint's own container — what `agents` requires a restore to recover *from the file alone* and its surface
  declines to hand back (`agents/learner.md` §4, ASM-20); an absent `game` is the default shape, which is what makes the 18 shipped
  version-1 containers loadable (`shapes.md` §3, §5).
- **Refusals:** a path that names no readable file, naming it; a checkpoint whose container records no seed or no encoding name — or
  records them in a form this module does not read — naming which, because no seed is ever substituted (`records.md` §7, `protocol.md`
  §5, ASM-20); an encoding name `features.build_encoder` refuses (`features/surface.md` §5); a **shape its container records which the
  catalogue does not carry**, refused naming it and the declared names (`UnknownShape`, `shapes.md` §2); an **exploration mode that is
  neither `schedule` nor `off`**, refused naming it and both modes (`UnknownExploration`), because the mode is the policy's and no third
  reading of a container exists (`sizing.md` §4); and, for a **member record** a caller hands `match`, `matrix` or `opponent`, a
  declared `rule`, `utility` or `game` that disagrees with what its policy carries — `RuleMismatch`, `UtilityMismatch`,
  `ShapeMismatch`, naming the member and both values, after the load and before a hand is played (`rules.md` §6, `errors.md` §4,
  `shapes.md` §3).
- **Evaluation mode, and determinism:** the learner is never trained, updated or frozen from its exploration, and holds the state the
  checkpoint holds, so it decides as its learner decided (`agents/surface.md` §1, §10, ASM-5); one checkpoint gives one policy, it
  chooses the action its learner chooses on the same readout, and it plays no hand and moves no stream (`battery.md` §3 FAM-12, ASM-2).
  In the `off` mode two policies at two seeds decide **identically** on one readout and no draw is taken at all, so the greedy reading
  is a function of the model and not of a seed (`sizing.md` §4, `shapes.md` §4).

## 13. `report` — the complete rung report (`general` row)

- **Signature:** `report(rung_name, record, matrix, rating)`.
- **Arguments:** the rung's name — or an unregistered configuration's own label, since a rung is data and not a registry entry
  (`ladder.md` §1, `records.md` §12); the run record of `records.md` §12 with the seven families of `protocol.md` §1 attached
  (`records.md` §13); and the matrix and the rating the report is about (`e2e-surface.md` §3.4).
- **Returns:** the complete per-rung report — one record keyed by the seven family names `protocol()` declares, each carrying what that
  family must carry, with the rung, the seeds, the table budget, the table seed and the device beside them, and no family reduced to a
  blank (`protocol.md` §1, §2, `records.md` §13). The pool family is `pool_members`'s record shape (`protocol.md` §1, `records.md` §8)
  and it names the rules and the utilities the measured population held: a report gains **no family and no new required content item**
  for D-19 or D-20 — both ride inside the pool family — and a pool block declaring none of its own is completed on the report's own
  copy with the population its matrix names, never by editing the record it was handed (`rules.md` §4, §6, `utilities.md` §7, §9,
  D-19, D-20). Its **header family names the shape** the run, the pool and the matrix agree on — one fact written onto the report's own
  copy of that family, beside the nine items the record states (`records.md` §13, `protocol.md` §1, `shapes.md` §3, D-29).
- **Refusals:** an absent family, naming it exactly as `protocol()` spells it, `axis row` included; a matrix that is not a table
  (§11's checks, `docs/L1/league.md` §4); a matrix whose membership is not the pool family's members plus the rung's variants — **every**
  pool member present, a declared folder included, the pinned three present, and no more than two members outside the pool — naming the
  foreign member, the missing pool member or the missing baseline (`docs/L1/league.md` §4, `ladder.md` §2, `protocol.md` §1, ASM-32,
  D-21); a rating that does not name exactly the matrix's members, naming the difference (`records.md` §11); a header missing one of
  `protocol.md` §1's nine items, naming it; a record whose **run, pool and matrix do not name one shape**, refused naming the three and
  the shape each names (`ShapeMismatch`, `records.md` §13, `shapes.md` §3, §6); and a matrix on a shape with more seats than a pair has,
  refused through §11's table checks before a family is assembled (`SeatCountExceeded`, `seats.md` §3, `docs/L1/seats.md` §5, D-33). No
  family is invented and none is filled in (D-6, `records.md` §13).
- **Determinism:** one record, one matrix and one rating give one report, which carries the seeds, the table seed and the device, so a
  third party can re-run what it describes (`protocol.md` §2, §6, D-6); it plays no hand, moves no stream and reads no file, so a report
  is assembled from records alone (`module-map.md` §3, D-13). An absent `game` on the run record, on the pool family or on the matrix
  reads as the **default** shape, which is what keeps every record the repository already holds reportable without being rewritten
  (`shapes.md` §3, §5).
