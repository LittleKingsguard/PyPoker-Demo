# evaluation — the callable surface

- **Layer:** L2 · **Module:** `evaluation` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-05
- **Owner of this file:** the surface — the eleven module-level names of `src/evaluation/`, each with its
  argument contract, its returned record, its refusals and its determinism (D-12, `e2e-surface.md` §1, §3.4)
- **Rev 2:** §12 reads a checkpoint's recorded seed and encoding from its container and checks the name by
  `build_encoder`'s refusal (ASM-20); §8's draw, §10's policy seed and §5/§10's distinct membership restated
- **Ceiling:** 260 lines. At the ceiling, split by owner — never append

## 1. Rules that hold of every entry point

Each of the eleven names is a module-level name of the `evaluation` package, and nothing below one of them
is contract (`e2e-surface.md` §1, brief §5). Six rules are shared and are stated here once (D-12, D-13):

- The eleven names are fixed: L2 refines types, record keys, defaults and error classes and never adds,
  removes or renames an entry point (D-12, `e2e-surface.md` §1, modules.md §3).
- An invalid argument is refused by raising an error that names the violated contract; no entry point
  coerces a value, substitutes a default, swallows an error or returns part of a record (`e2e-surface.md` §2).
- `protocol` and `league` take no argument, so their one instance is the project's and cannot be varied
  (D-6, D-16, `e2e-surface.md` §5); the other nine are defined for any valid instance (D-15, `battery.md` §4).
- Play is the only thing that moves Python's global `random` stream, and it moves it only through
  `engine.new_hand`, the project's single seeding point (ASM-2, `protocol.md` §4, `engine/surface.md` §4).
  `protocol`, `league`, `build_pool`, `pool_members`, `offer`, `opponent`, `rating`, `policy_from` and
  `report` play nothing and leave the stream where they found it; the one entry point that must sample,
  `rating`'s bootstrap, draws from its own generator seeded from the table seed and records that seed
  (ASM-17, ASM-2).
- A returned value is plain data except three: a pool, a policy, and the callable `league()` declares. A
  pool and a policy are opaque values a caller only passes back, and no record returned here exposes one
  (`e2e-surface.md` §1, D-1).
- A record returned here carries the keys `records.md` marks **required** and, beyond them, only this
  module's own keys, which no caller may depend on (`records.md` §1, D-13). Exactness is promised on CPU:
  one `(configuration, seed set, budget, pool membership)` reproduces a table value for value
  (`protocol.md` §4), with the measured exception `league.md` §7 records for a cell pairing the `oracle`.

This module never trains and never edits a curve; it owns the pool, plays the cells and assembles the
evidence (`module-map.md` §3, D-16). It calls `agents`, `features` and `engine` and no fourth module: the
run record, the rung label and the record's families arrive as data (`module-map.md` §2, D-13).

## 2. The policy and the member at this edge

- A **policy** is a callable taking `(readout, legal_actions)` and returning one descriptor from
  `legal_actions`; a policy that returns an illegal descriptor is a contract violation and never a fold
  (D-2, `e2e-surface.md` §2). This module calls policies and imports none: `policy_from` and `opponent`
  return one, and `agents.as_policy` and `agents.build_baseline` return the ones it loads and draws
  (D-2, `module-map.md` §2).
- A **member** is a version — a checkpoint with `records.md` §7's record — or one of the three pinned
  baselines, and no cell is played against a policy that is not a named member (`e2e-surface.md` §2,
  `docs/L1/league.md` §1, D-16). A cell, a matrix and a rating name their members by **id** and never by rank
  order (`protocol.md` §1, `records.md` §7).
- A side is named by its member record whenever this module holds one: a pool member, one of the three
  baseline names given in the call, or a checkpoint `policy_from` loaded — a policy it built carries its own
  id and capacity. A callable handed in from outside carries none, so it is named for its position in the
  call — `policy-1`, `policy-2`, in argument order — and its capacity is recorded as unmeasured, which the
  cell states in `unlabelled`: an opaque policy cannot be asked for a parameter count, and this module
  invents no number it did not measure (`agents/surface.md` §1, §5, ASM-10).
- `params` therefore carries one integer per member: `agents.param_count` of the learner behind a member
  this module built; `0` for a baseline — the zero `agents.baselines()` declares; and `0` for an unlabelled
  policy, so that a reader can tell a measured zero from an unmeasured one (`records.md` §9, ASM-10).

## 3. `protocol` — the evidence contract (`fixed` row)

- **Signature:** `protocol()`.
- **Arguments:** none: the protocol is D-6's and D-16's, so no argument can vary it (`protocol.md` §1,
  `e2e-surface.md` §3.4).
- **Returns:** one mapping read under these keys — `families` (the seven of `protocol.md` §1, in its order:
  `curves`, `pool`, `matrix`, `rating`, `baselines`, `axis row`, `header`, each value a record of that
  family's `required` items and the `refusal` its absence is named by), `seeds` (`0, 1, 2`), `header` (the
  nine items `protocol.md` §1 requires: the game, the action space, the parameter counts, the sample
  budget, the cell size, the seed set, the table seed, the device, the checkpoint paths), `table_budgets`
  (`live`, `full`), `baselines` (the three names `agents.baselines()` declares) and `rating` (the method,
  the interval's confidence and the anchor, `docs/L1/league.md` §5).
- **Refusals:** none; it has no argument (`e2e-surface.md` §3.4).
- **Determinism and ordering:** two calls return equal records, written in this order and in `protocol.md`
  §1's. It is plain data, and the seven family names are strings in it exactly as `protocol.md` §1 spells
  them, because a report's families are judged against it (`battery.md` §3 FAM-4, FAM-11).

## 4. `league` — the league's parameters (`fixed` row)

- **Signature:** `league()`.
- **Arguments:** none: M, the cell sizes and the table seed are ASM-14's, and no parameter varies them
  (D-16, `assumptions.md` ASM-13–ASM-15).
- **Returns:** one mapping read under these keys — `m` = 5; `baselines` (the three pinned names);
  `tables`, keyed `live` and `full`, each carrying `hands_per_cell` (120 and 1,500), the `hands_played` a
  K = 9 and a K = 10 membership costs (4,320 or 5,400 live, 54,000 or 67,500 full) and what produces it
  (the talk on the fly, or an offline job shipped under `tables/`); `cell_count`, a callable taking K or a
  membership and returning K(K−1)/2, so a talk sizes its table before it plays one; `table_seed`, the one
  integer every matrix is played from; and `rating`, the method, the 95% interval and the anchor.
- **Refusals:** none (`e2e-surface.md` §3.4).
- **Determinism:** two calls return equal records, and the numbers are `docs/L1/league.md` §6's table and no
  other — and no per-hand cost figure at all, since ASM-21 supersedes ASM-15's bound (ASM-14, ASM-21).

## 5. `build_pool` — one pool from one declaration (`general` row)

- **Signature:** `build_pool(declaration)`.
- **Arguments:** `records.md` §8's declaration — `members` (the versions, by id and lineage), `m` (the
  bound) and `frozen` (whether it may change while it is used), all three **required** (`records.md` §8).
- **Returns:** a pool — the opaque value `pool_members`, `offer` and `opponent` take (§1). It holds the
  declared versions in lineage order, windowed to their last `m`, plus the three baselines pinned, and it
  carries the id `records.md` §8 requires (`docs/L1/league.md` §2).
- **Refusals:** a declaration missing one of §8's three keys, with that key named; an `m` that is not a
  positive integer or that exceeds the league's M, with the bound named (D-16, `docs/L1/league.md` §2); a
  declared member missing its `id` or its `lineage`, naming the member and the key, because those two are
  how §8 declares a version and how the window is ordered (`records.md` §7, §8); two declared members
  sharing one `id`, or a version declared under one of the three pinned baselines' names, naming the
  member, because a membership names its members once and a cell pairs two distinct ones (§9, `records.md`
  §7, §8); a declared `path` that
  names no readable file, naming the member, because a pool never pretends a version it could not load
  (`protocol.md` §5); a member list whose lineage does not order — two members descending from one, or a
  chain that reaches no start — naming the member (`records.md` §7, `docs/L1/league.md` §2). A member
  declared without a `path` is admitted, and `matrix` and `opponent` refuse it when it is asked to be a
  policy (§10, §8, `records.md` §7).
- **Determinism:** one declaration yields one ordered member list and one id, and the id is a function of
  the ordered member ids and of nothing else, so it changes when and only when the membership does
  (`records.md` §8, ASM-2, `battery.md` §3 FAM-6).

## 6. `pool_members` — the pool read back (`general` row)

- **Signature:** `pool_members(pool)`.
- **Arguments:** a pool from `build_pool` or `offer`.
- **Returns:** `records.md` §8's pool record — `id`, `m`, `frozen` and `members` in order: the three
  baselines first, in `agents.baselines()`'s order, each marked `pinned` and carrying the `params` of `0`
  the catalogue declares, then the version window oldest to newest, each the `records.md` §7 record its
  declaration carried (`records.md` §8, ASM-16).
- **Refusals:** a value that is not a pool this module built (`e2e-surface.md` §2).
- **Determinism:** one pool reads back one record, and a frozen pool's read-back does not change while it
  is used — which is how a pair's parity is read (`records.md` §8, ASM-16).

## 7. `offer` — advance a pool by one version (`general` row)

- **Signature:** `offer(pool, version)`.
- **Arguments:** an unfrozen pool, and one version as a `records.md` §7 record.
- **Returns:** the pool advanced: the version joins the window at its head, the oldest version leaves when
  the window already holds `m`, the baselines are untouched and the id is recomputed
  (`docs/L1/league.md` §2, ASM-18, `records.md` §8). The argument pool is unchanged, so a caller may keep it.
- **Refusals:** a frozen pool, naming the frozen flag, because a frozen membership does not change while
  it is used (`records.md` §8, ASM-16); a value that is not a pool; a version missing its `id` or its
  `lineage`, naming which (`records.md` §7); a version already a member, naming it; a version whose
  `lineage` is not the window's newest version member, naming the lineage, because the window has one order
  and an offer extends it — while a window holding no version accepts any version and begins its order
  (`docs/L1/league.md` §2, `records.md` §7).
- **Determinism:** one pool and one version give one membership and one id, and offering plays no hand and
  moves no stream (ASM-2, `battery.md` §3 FAM-6).

## 8. `opponent` — the training loop's draw (`general` row)

- **Signature:** `opponent(pool, seed)`.
- **Arguments:** a pool, and an integer seed.
- **Returns:** one policy in the sense of §2, drawn from the pool's ordered membership by the seed: a
  baseline is `agents.build_baseline(name, seed)`, and a version is `policy_from` of its checkpoint beside
  its member record (`docs/L1/league.md` §3, D-16, `module-map.md` §2).
- **Refusals:** a value that is not a pool; a seed that is not an integer (ASM-2); a pool whose drawn member
  carries no `path`, naming the member, because a version that cannot be loaded cannot be an opponent
  (`records.md` §7, `protocol.md` §5).
- **Determinism:** one pool and one seed draw one opponent, and the draw is the seed reduced modulo the
  membership's size, so a spread of seeds samples the whole pool and not one fixed policy — no map from the
  integers into a membership of more than one makes every distinct seed a distinct member (ASM-2, FAM-7);
  the drawn policy answers one decision one way, because only the deal uses the global stream (ASM-2).

## 9. `match` — the scheduler's one cell (`general` row)

- **Signature:** `match(left, right, hands, seed)`.
- **Arguments:** two policies or two member records — a §7 version record, or one of the three baseline
  names; `hands`, a positive integer; `seed`, an integer (`e2e-surface.md` §3.4).
- **Returns:** `records.md` §9's cell record — `members` (the two ids in argument order), `hands`,
  `directions` (two entries, position-aligned with `members`, each carrying `wins`, `ties`, `losses`,
  `mean_chip_delta` and `seat_split`), `params` (§2) and `seed` (`records.md` §9).
- **Behaviour:** it is the scheduler, and `docs/L1/league.md` §3 fixes what it does — one cell at a time,
  seats alternating, both directions from one set of hands, a cell costing its hand count and not twice it
  (D-16, ASM-14).
- **Refusals:** a value that is neither callable nor a member; a hand count that is not a positive integer;
  a seed that is not an integer; two members carrying one id, because a cell pairs two distinct members
  (`records.md` §9, `docs/L1/league.md` §3). An illegal descriptor from either policy is `engine`'s refusal
  and is not caught or repaired here (D-2, `engine/surface.md` §10).
- **Determinism:** one pair, one hand count and one seed give one cell, whatever was played before it, and
  a different seed deals different hands (`battery.md` §3 FAM-7, FAM-4, ASM-2).

## 10. `matrix` — the pairwise table (`general` row)

- **Signature:** `matrix(pool, variants, table)`.
- **Arguments:** a frozen pool; the rung's one or two variant policies; and a table budget, `live` or
  `full` (`ladder.md` §2, `docs/L1/league.md` §4, §6).
- **Returns:** `records.md` §10's matrix record — `members` (the membership **by id**, the pool's members in
  `pool_members`'s order and then the variants as `variant-1`, `variant-2` in argument order), `cells`
  (exactly K(K−1)/2 §9 records, one per unordered pair of that membership), `hands_per_cell` (the one hand
  count of §4's `tables`, the three baseline cells included), `table_seed` (the league's) and `table` (the
  budget), plus this module's own keys, the pool's id and each member's record among them (`records.md` §10,
  `docs/L1/league.md` §4).
- **Refusals:** a pool that is not frozen, naming it, because a pool does not change while it is tabled
  (`docs/L1/league.md` §2, §4, `records.md` §8); a pool member the declaration gave no `path`, naming the
  member (`records.md` §7, `protocol.md` §5); a variant count other than one or two, or a variant that is
  not a policy, naming it (`ladder.md` §2, `docs/L1/league.md` §4); a membership that is not distinct — two
  members carrying one id, which no cell can pair (§9, `records.md` §9); a `table` label that is not `live` or
  `full` (`records.md` §10, `docs/L1/league.md` §6).
- **Determinism:** one pool, one variant list and one budget give one matrix: every cell's seed is derived
  from the table seed and the pair, and every policy the table builds is built at a seed the table fixes — a
  baseline at a seed derived from the table seed and its position, a version member at the seed its
  checkpoint records (§12), because one checkpoint is one player; the variants are the caller's own policies
  (`docs/L1/league.md` §3, ASM-2, `protocol.md` §5, `battery.md` §3 FAM-8).

## 11. `rating` — the fitted rating (`general` row)

- **Signature:** `rating(matrix)`.
- **Arguments:** a matrix record in `records.md` §10's shape — this module's own or a hand-built one,
  because what is checked is the record and not its provenance (`records.md` §10, `docs/L1/league.md` §4).
- **Returns:** `records.md` §11's rating record — `values` (one entry per matrix member, keyed by the
  member's id, each carrying the fitted value, the two bounds of its 95% interval and the hands behind it:
  `hands_per_cell × (K−1)`), `method` = `Bradley-Terry`, `anchor` = the three baselines' mean fixed at
  zero, `bound_applied`, `bootstrap_seed` and `converged` (`records.md` §11, `docs/L1/league.md` §5, ASM-17).
- **Refusals:** a matrix that is not a table — a cell whose hand count differs from `hands_per_cell`, a
  cell count other than K(K−1)/2, a pair present twice, a missing one of the three baselines, a member a
  cell names that the membership does not, or an absent `hands_per_cell`, `table_seed` or `table` label —
  each naming the violated rule, and nothing is fitted anyway (`docs/L1/league.md` §4, `records.md` §10, D-16).
- **Determinism:** one matrix gives one rating: the fit is deterministic and the bootstrap is seeded from
  the table seed, whose value the record carries (ASM-17, ASM-2). A rating states where a member stands
  among the table's named members on this game at this cell size, and is never a claim of poker skill
  (D-16, `docs/L1/league.md` §5).

## 12. `policy_from` — a checkpoint as a policy (`general` row)

- **Signature:** `policy_from(path)`.
- **Arguments:** one checkpoint path `agents.save` wrote; a member is loadable from its path alone, which is
  why a checkpoint records the seed and the encoding it was built at (`e2e-surface.md` §3.4, `records.md` §7).
- **Returns:** a policy in the sense of §2 — a member policy carrying the member record it was loaded for,
  so a cell names it and reports its capacity (§2, `records.md` §7). It is `agents.as_policy` of
  `agents.load(None, path)` over the encoder `features.build_encoder` makes for the encoding name the
  checkpoint records, at the seed the checkpoint records (`agents/surface.md` §9, §10, `protocol.md` §5,
  ASM-5). Both facts are read from the checkpoint's own container — what `agents` requires a restore to
  recover *from the file alone* and its surface declines to hand back (`agents/learner.md` §4, ASM-20);
  reading them is not a restore, since the learner and its rule are `agents.load`'s alone.
- **Evaluation mode** qualifies it: the learner is never trained, never updated and never frozen from its
  exploration, and holds the state the checkpoint holds, so it decides as its learner decided
  (`agents/surface.md` §1, §10, `protocol.md` §5, ASM-5).
- **Refusals:** a path that names no readable file, naming it; a checkpoint whose container records no seed
  or no encoding name — or records them in a form this module does not read — naming which, because no seed
  is ever substituted (`records.md` §7, `protocol.md` §5, ASM-20); an encoding name `features.build_encoder`
  refuses (`features/surface.md` §5), the check that stays inside the granted arrows.
- **Determinism:** one checkpoint gives one policy, it chooses the action its learner chooses on the same
  readout, and it plays no hand and moves no stream (`battery.md` §3 FAM-12, `protocol.md` §5, ASM-2).

## 13. `report` — the complete rung report (`general` row)

- **Signature:** `report(rung_name, record, matrix, rating)`.
- **Arguments:** the rung's name — or an unregistered configuration's own label, since a rung is data and
  not a registry entry (`ladder.md` §1, `records.md` §12); the run record of `records.md` §12 with the
  seven families of `protocol.md` §1 attached (`records.md` §13); and the matrix and the rating the report
  is about (`e2e-surface.md` §3.4).
- **Returns:** the complete per-rung report — one record keyed by the seven family names `protocol()`
  declares, each carrying what that family must carry, with the rung, the seeds, the table budget, the
  table seed and the device beside them, and no family reduced to a blank (`protocol.md` §1, §2,
  `records.md` §13). The pool family is `pool_members`'s record shape (`protocol.md` §1, `records.md` §8).
- **Refusals:** an absent family, naming it exactly as `protocol()` spells it, `axis row` included; a
  matrix that is not a table (§11's checks, `docs/L1/league.md` §4); a matrix whose membership is not the
  pool family's members plus the rung's variants — every pool member present, the three baselines present,
  and no more than two members outside the pool — naming the foreign member, the missing pool member or the
  missing baseline (`docs/L1/league.md` §4, `ladder.md` §2, `protocol.md` §1); a rating that does not name
  exactly the matrix's members, naming the difference (`records.md` §11); a header missing one of
  `protocol.md` §1's nine items, naming it. No family is invented and none is filled in (D-6, `records.md` §13).
- **Determinism:** one record, one matrix and one rating give one report, which carries the seeds, the table
  seed and the device, so a third party can re-run what it describes (`protocol.md` §2, §6, D-6); it plays no
  hand, moves no stream and reads no file, so a report is assembled from records alone (`module-map.md` §3, D-13).
