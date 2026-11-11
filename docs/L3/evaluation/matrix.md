# evaluation — the pairwise matrix

- **Owner:** `matrix` — the membership and the one **shape** the table is on, the **pair enumeration**, the per-cell and
  per-member seeds (§3), how each member's policy is built (§4), the record's keys (§5), the two budgets (§6) and every
  refusal (`surface.md` §10, `records.md` §10, `league.md` §3, `shape.md` §4)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Rev 6:** D-29's second shape — the table's shape is the **pool's** and `matrix` takes no shape argument, a variant of another shape is refused by slot, and the record's own required `game` is carried by every cell and every member record (§1, §4–§5, §7, `shape.md` §4) · **Rev 7:** D-33's third shape — a matrix is **two seats'**: a pool on a shape above the pairwise instrument's seat count is refused naming the shape and its seat count, before a variant is looked at and before a checkpoint is touched (§1, §7, `seats.md` §1, §5, D-22, D-33)
- **Read with:** `shape.md` §2–§4, `pool.md` §5, `utility.md` §3–§4, `scheduler.md` §3–§5, `rating.md` §1, `tables.md` §1,
  `errors.md` §2–§4, `seats.md` §1, §5

## 1. The membership, and it is frozen — and it is on one shape

`matrix(pool, variants, table)` plays one round robin over **the frozen pool's members plus the rung's variants**:
`K = |pool| + V` with `V` one or two, so `K` is 4 for R1, 9 for a one-variant rung with a full window and 10 for a
two-variant rung (`league.md` §3, ASM-14). `_membership(pool, variants)` returns the ordered ids:

    <the pool record's members, in pool_members's order>   then   "variant-1", "variant-2"   (argument order)

The pool's order is `records.md` §8's — the **pinned** baselines first, in `agents.baselines()`'s order: the flagged three,
then any folding baseline the declaration named, then the window oldest
to newest (`pool.md` §5, ASM-32, D-21). A variant is named `variant-1` or `variant-2` by its position in the argument list **whatever it
carries**: a variant is the rung's own policy, named by the slot it was handed in, so one pool and one variant list have
one membership (`surface.md` §10). The pool must be **frozen**: a pool that may still change is no table (`surface.md` §10, ASM-16).
Nothing here assumes the pool holds three baselines and a window: `K` is whatever it holds, plus `V` (`docs/L1/folders.md` §4, ASM-33).

**The table's shape is the pool's.** `matrix` takes no shape argument: the pool carries the one shape every member of it
plays (`pool.md` §1, §5), so the table is played on that shape and its record states it (§5, `shape.md` §4). A variant is
the rung's own policy, so it may name that shape or none — naming **another** one is refused naming the variant's slot
(`variant-1`, `variant-2`) and both shapes, because a table is measured on one shape and no row of it is a second game
(`ShapeMismatch`, §7, `docs/L1/shapes.md` §6).

**A matrix is two seats', and the refusal comes first.** The seat count is read through `engine.game_config` — the granted arrow, never a literal — and a pool on a shape whose count is above the pairwise instrument's is refused as `SeatCountExceeded`, naming the shape and its seat count, because a cell is an unordered pair and a six-way hand produces a placement (§5, §7, `module-map.md` §2, `seats.md` §1, §3, §5, `league.md` §4, D-22, D-33). The check sits **straight after the frozen-pool check and before `_variant_list`**, so no variant is looked at and no checkpoint is touched for a table that will not exist; both two-seat shapes pass untouched, and every table they produce today is exactly what it was (`seats.md` §3, §5). **No matrix, and therefore no rating and no report, exists for the six-seat shape in this pass**: a run on it writes its curves, its pool, its checkpoints and its greedy pass, and no table (`seats.md` §5, `league.md` §4, D-22, D-33).

## 2. The pairs, and the order the cells are played in

The cells are exactly the `K(K−1)/2` unordered pairs — 6, 36 or 45, and 66 or 78 when D-21's three folders are declared —
one cell per pair and no repeat (`league.md` §3, ASM-14, ASM-33, D-21). `_pairs(k)` enumerates them lexicographically by membership position:

    for i in range(k):
        for j in range(i + 1, k):
            yield (i, j)          # (0,1) (0,2) … (0,k−1) (1,2) … (k−2,k−1)

and `matrix` plays them in exactly that order, one after another, calling `scheduler._play_cell` for each — so the
`cells` sequence is position-for-position this enumeration, and every cell is played to completion before the next
begins (`scheduler.md` §1, `league.md` §2). A pair is unordered: `(i, j)` and `(j, i)` are one cell, whose two
`directions` report both seats (`records.md` §9).

## 3. The seeds: `(table seed, membership, budget)` and nothing else

`matrix` takes **no seed**, because the table seed is the league's one integer (`surface.md` §4, §10). The design
reads it from `declarations.TABLE_SEED` — the same value `league()["table_seed"]` declares (`declarations.md` §6) —
and derives both seeds from it, through `seeds.py`'s one digest (`scheduler.md` §3):

    cell_seed[i, j]  = seeds._cell_seed(table_seed, i, j)          # the cell's `seed` argument and its record
    member_seed[p]   = seeds._member_seed(table_seed, p)           # a baseline at position p — and only a baseline

So a table is reproduced from its table seed, its membership and its budget: the cells depend on the seed and the pair positions only, the baselines' policies on the seed and their positions only, and a version's policy on the facts its own checkpoint records (§4). Nothing here reads the global `random` stream, and **no shape enters a derivation** (`scheduler.md` §3, ASM-2). The record carries the seed as `table_seed`, which is also what `rating` seeds its bootstrap from (`rating.md` §4). **One measured exception**, recorded at `docs/L2/evaluation/league.md` §7: a cell that pairs the `oracle` is not reproduced across processes, because the equity estimate it queries samples a run-out deck in a per-interpreter hash order.

## 4. How each member's policy is built

Every member is played through `scheduler._side`'s rules, resolved once per table and reused for every cell it
appears in, so one member is one player throughout a table (`scheduler.md` §5):

| Member | Its policy | Its seed | Its `game` |
|---|---|---|---|
| a baseline (any `agents.baselines()` name the pool pins) | `agents.build_baseline(name, member_seed[p])` | `member_seed[p]` — the table seed and the member's **position** (§3) | `None` — shape-silent, so it plays the table's shape |
| a version (a pool member with a `path`) | `policy._member_policy(record)` — i.e. `policy_from`'s builder | the seed its **checkpoint records** (`scheduler.md` §5.1, `surface.md` §10, §12) | the shape its container records, and its record's `game` is held to it (`shape.md` §3) |
| a variant (the rung's policy) | the callable it was handed as, unchanged | the caller's; it is already built (`scheduler.md` §5) | `getattr(variant, "game", None)` — the pool's shape, or none, and another one is refused (§1, §7) |

Every baseline cell is in the table like every other cell — the flagged three's and a declared folder's alike — and the baselines' policies are built at the
derived seeds, so their mutual cells are as reproducible as any other and no model influences them (`league.md` §3, D-21). A
version's policy is built at its checkpoint's own seed and not at the table's:
the member is the same player in two tables, which is what makes one checkpoint one row (`protocol.md` §5). **Every
member's rule, utility and shape are resolved in this same pass, with its side** — `_side` returns all three beside the policy
(`scheduler.md` §5), so §5's `rules`, `utilities`, `population`, `utility_population`, `member_records` and `game` come off the
sides the table plays (`records.md` §10, `utility.md` §3, D-19, D-20, `shape.md` §4).

> **The rule `surface.md` §10 now states** — and it is what this design pinned: `_member_seed(table_seed, position)` applies to
> policies this module builds **from a name** (the three baselines and nothing else), while a version member is built at the seed
> its checkpoint records (`surface.md` §12, `scheduler.md` §5.1). One checkpoint is one player. The shipped artefact's variant
> (`tables.md` §2) is a policy handed in from its own recipe, so no table seed moves it either.

## 5. The record

`records.md` §10's nine keys come first, then this module's own keys, which no caller may depend on (`records.md`
§1, D-13). `matrix` returns exactly these keys, in this order:

| Key | Content |
|---|---|
| `members` | the K ids of §1, in membership order — the pool's members, then `variant-1`, `variant-2` (`records.md` §10) |
| `cells` | the `K(K−1)/2` cell records of §2, in the enumeration's order, **each carrying the table's `game`** (`records.md` §9, `scheduler.md` §1) |
| `rules` | each member's rule **by id** — the rule its policy carries, `None` for a baseline and for an opaque policy that carries none: `records.md` §9's `rules` one level up (`records.md` §10, D-19) |
| `population` | the distinct rules those members declared, **sorted** — the population this table measured, so a reader of the rating knows which estimators it was fitted across (`records.md` §10, `league.md` §4, D-19) |
| `utilities` | each member's utility **by id**, on the same terms: the catalogue name its policy carries, `None` for a baseline or an opaque policy that carries none (`records.md` §10, `utility.md` §3, D-20) |
| `utility_population` | the distinct utilities those members declared, **sorted** — the objectives this table measured (`records.md` §10, `utilities.md` §9, D-20) |
| `hands_per_cell` | the one hand count every cell was played at: 120 `live`, 1500 `full` (§6) |
| `table_seed` | `declarations.TABLE_SEED` (§3, `records.md` §10) |
| `table` | the label it was asked for, `live` or `full`, as a value (`records.md` §10) |
| **`game`** | **required** and this module's own key (`records.md` §10 does not list it): the one shape the table was played on — the pool's (§1, §4) — so no reader infers it (`shape.md` §4) |
| `pool` | the frozen pool's id — the string `pool_members` returns, so a table names the pool it measured (`records.md` §8, `league.md` §3) |
| `member_records` | one record per member, in `members` order, **each carrying its `rule`, its `utility` and its `game`**: a baseline's `{"id", "baseline": True, "pinned": True, "params": 0, "rule": None, "utility": None, "game": None}`, a version's `records.md` §7 record with the three its policy reports, a variant's `{"id": "variant-1", "params": <int>, "unlabelled": <bool>, "rule": <str or None>, "utility": <str or None>, "game": <str or None>}` |
| `unlabelled` | the ids of the members whose capacity is unmeasured — the variants handed in as opaque policies, whose `params` is `0` and whose `0` is not a measurement (`surface.md` §2, ASM-10) |
| `cell_count` | `K(K−1)/2`, the same number `league()["cell_count"](K)` returns (`declarations.md` §5) |

The required keys are what `rating` and `report` read (`rating.md` §1, `report.md` §3); `pool`, `member_records`, `unlabelled` and `cell_count` are this module's own, and they are there so a table names *what* it measured and a reader can tell a measured `0` from an unmeasured one (`surface.md` §2, `records.md` §10). **The rating is a function of the matrix and reads neither `rules` nor `population`, neither `utilities` nor `utility_population`** (`league.md` §4, `rating.md` §1, D-19, D-20): the four keys are evidence about who played and which questions they were asked, not inputs to the fit — and `game` is the fifth such key, read by `rating` only to hold the fit to one shape (`rating.md` §1, §6). `unlabelled` says that `matrix` was handed a policy already built and measured no capacity itself: a statement about provenance, never about whether that policy's learner was trained, which a table cannot know (`tables.md` §2, §5).

## 6. The two budgets

`table` is the label `live` or `full`, and it fixes exactly two things: `hands_per_cell`, from `league()["tables"][table]["hands_per_cell"]` — 120 and 1500 — and nothing else (`league.md` §5, ASM-14). One membership, two cell sizes: the live table is the full table's skeleton read coarsely, so a live order is a demonstration and the full table with its intervals is what a claim rests on (`league.md` §5, D-16). Every cell is played at that one count, every baseline cell included, so no member's row is measured more precisely than another's (`league.md` §3), and a table plays `cell_count × hands_per_cell` hands — 720, 4,320 or 5,400 live and 9,000, 54,000 or 67,500 full, or `docs/L1/folders.md` §5's 7,920/9,360 and 99,000/117,000 with the folders declared (ASM-33, `tables.md` §1). A budget fixes no shape: one pool's membership is one shape's, and the two budgets are the same game read at two cell sizes (`shape.md` §4).

## 7. Refusals, in this order

| Class | Raised when |
|---|---|
| `InvalidPool` | the first argument is not a pool this module built (`surface.md` §10) |
| `PoolNotFrozen` | the pool is not frozen, naming it — a pool does not change while it is tabled (`surface.md` §10, ASM-16) |
| `UnknownTable` | the label is not the string `live` or `full` (`records.md` §10, `league.md` §5) |
| `SeatCountExceeded` | the pool's shape has more seats than the pairwise instrument's, naming the shape and its seat count — a cell is one pair of two seats — raised before a variant is looked at and before a checkpoint is touched (§1, `seats.md` §5, `league.md` §4, D-22, D-33) |
| `VariantCountInvalid` | the variant list holds anything other than one or two policies (`ladder.md` §2, `league.md` §3) |
| `VariantInvalid` | a variant is not callable, naming it (`surface.md` §10) |
| `ShapeMismatch` | a variant's `game` is not the pool's, naming the variant's slot and both shapes — a table is measured on one shape (`surface.md` §10, `shape.md` §3, `docs/L1/shapes.md` §6) |
| `MemberDuplicate` | the membership of §1 is **not distinct** — a pool member's id is `variant-1` or `variant-2` and a variant is in that slot, naming the id, because a cell pairs two **distinct** members (`surface.md` §10, `records.md` §9, `errors.md` §2) |
| `MemberUnloadable` | a pool version member carries no `path`, or its `path` names no readable file, naming the member (`surface.md` §10) |
| `CheckpointRecordMissing` | a version's container records no seed or no encoding name, or records either in a form this module does not read — naming the fact, the member and the path (`scheduler.md` §5.1, §6) |
| `UnknownShape` | a version member's record or a variant names a shape `SHAPE_NAMES` does not carry, naming it and the declared shapes (`shape.md` §2) |
| `RuleMismatch`, `UtilityMismatch`, `ShapeMismatch` | a version member's record declares a `rule`, a `utility` or a `game` its own policy contradicts — naming the member and both values, after the load and **before any cell is played** (`scheduler.md` §5, `families.md` §6, `utility.md` §4, `shape.md` §3, D-19, D-20) |

The order is the table's: cheap checks first, then the pool's seat count, then the variant's shape (before a member is built,
because it is the table's own premise), then the members that must be loaded — so an unfrozen pool is reported before a single
checkpoint is touched, a pool no pair can table before a variant is looked at, a variant of another shape before a row exists,
and no cell is played for a table that will be refused. A matrix is never
repaired and never partially returned (`e2e-surface.md` §2). The `MemberDuplicate` guard is **defensive on the pool's side** —
`build_pool` and `offer` already refuse two members carrying one id (`pool.md` §2, §8) — and it is reachable through §1 and no
other way: a declared version whose id is `variant-1` collides with a variant's slot label, and the table refuses rather than
pair a member with itself. Every row of this table is **driven**, and so is §4's version row (`guardrails.md` G16, G20).

## 8. What is deliberately free

- the container of `members`, `cells` and `member_records`: a sequence or a mapping a reader can walk — the enumeration order is what is fixed, not the type (`records.md` §10);
- whether the cells are built lazily and collected, or played into a list — only that every cell is played at the table's one hand count and that two cells are never interleaved (`scheduler.md` §1);
- the repr of a member record for a variant beyond §5's six keys; `pool` is **the pool record's `id` string** and nothing else, because `pool_identity` must not mistake a member's id for the pool's (`pool.md` §5, README §3).
