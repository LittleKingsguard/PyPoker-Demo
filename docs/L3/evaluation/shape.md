# evaluation — the shape at this edge

- **Owner:** the game **shape** as this module declares and carries it — the catalogue restated at the edge and the seat count
  read rather than written (§1), absence as the default shape and never a defaulting of a name (§2), the three shape refusals
  and where each fires (§3), which record carries a shape and which one must not (§4), the two exploration modes
  `policy_from` takes (§5), what is free (§6) (`docs/L1/shapes.md` §2, §3, §6, `sizing.md` §4, `seats.md` §1–§4, `surface.md` §2,
  D-29, D-33)
- **Ceiling:** 100 lines. At the ceiling, split by owner — never append
- **Read with:** `pool.md` §1–§8, `scheduler.md` §1, §5–§6, `matrix.md` §1, §4–§5, §7, `rating.md` §1, §5–§6,
  `report.md` §1–§3, `declarations.md` §2.1, §3, `families.md` §4, `seats.md` §1–§4, `errors.md` §2–§5

D-29 declares a second game shape beside D-2's fixed-limit one and D-33 a third with six seats, and a shape is **data**: one
row of a catalogue `engine` publishes, named by a string and carried by every record that reports a result
(`docs/L1/shapes.md` §1–§2, `docs/L1/seats.md` §2). This document owns the shape-facing rules at this edge; `pool.md`,
`scheduler.md`, `matrix.md`, `rating.md`, `report.md`, `seats.md` and `declarations.md` each state the shape **field** of their
own record and cite this document for the rule it obeys, so no rule has a second home (`module-map.md` §2, D-13).

## 1. The catalogue, restated here, and the seat count read here

`src/evaluation/declarations.py` declares these constants, the seat count's beside the shape names', beside `M` and `TABLE_SEED`:

    SHAPE_NAMES         = ("fixed-limit-20", "no-limit-100", "six-seat-no-limit-100")  # the declared shapes, default first
    DEFAULT_SHAPE       = SHAPE_NAMES[0]                 # what an absent `game` reads as (§2)
    PAIRWISE_SEATS      = 2                              # the *instrument's* arity, and not a game's seat count (§3)
    EXPLORATION_MODES   = ("schedule", "off")            # the modes `policy_from` accepts (§5)
    EXPLORATION_DEFAULT = EXPLORATION_MODES[0]           # absence is today's behaviour (§5)
    PROBE_SEED          = 0                              # the seed a baseline's probe is built at (pool.md §2)

**Why the names are restated, and the seat count is not.** `module-map.md` §2 grants this module five names on `engine` and
`game_config` beside them, but **not** `game_shapes`: the catalogue's *names* cannot be read and are restated, while a shape's
*seat count* is read through the granted `game_config` and written down nowhere (`module-map.md` §2, `seats.md` §1, D-13,
D-33). The restatement is the one `agents` and `features` make at their own edges, and the **join battery** holds it true —
`SHAPE_NAMES` equal to `engine.game_shapes()`'s names in that order, `EXPLORATION_MODES` exactly the set `as_policy` accepts —
so a restatement that drifts is a red join case and never a silent second catalogue (`e2e-surface.md` §3.1, `surface.md` §2,
`agents/surface.md` §9, D-29). Rejected: calling `game_shapes()` through a widened arrow, which is L1's to grant (D-12), and
naming only the default shape (`records.md` §8).

**The two seat-count validators.** `seat_count(shape=None)` returns `int(engine.game_config(require_shape(shape,
"game_config"))["seats"])` and `require_pairwise(shape, entry, argument)` returns its `shape` when that count is the
instrument's, raising `errors.SeatCountExceeded` above it; their contracts and the four sites are `seats.md` §1–§3's, and **no
game's seat count is written down** here — a literal `2` or a literal `6` standing as a game's seats is a copied game parameter,
and `PAIRWISE_SEATS` is the arity of a pairwise measurement and not a shape's row (`module-map.md` §2, `seats.md` §1, §3, D-13,
D-22, D-33). Both are private and neither is surface.

## 2. Absence is the default shape, and it is never a defaulting of a name

An **absent** `game` reads as `DEFAULT_SHAPE` — in a pool declaration, a member record, a version offered to a pool, a cell, a
matrix, a rating, a report's three records and a checkpoint's container alike — and that is what keeps the records the
repository already holds readable without being rewritten: the shipped version-1 containers are the default shape's,
`tables/league-full.json` is a default-shape table and `checkpoints/evidence/r1-live.json` a default-shape run
(`docs/L1/shapes.md` §3, §5, `docs/L1/sizing.md` §6, ASM-18). Absence is **not** a defaulting of a present name: a field that
says nothing is read as the default, while one naming an uncatalogued shape is refused by name (`UnknownShape`, §3) and never
mapped onto it (`rules.md` §4, `docs/L1/e2e-surface.md` §2, D-19, D-13).

## 3. The three shape refusals

| Class | The contract it names |
|---|---|
| `UnknownShape` | a shape name the restated catalogue does not carry — a pool declaration's `game`, a member record's `game`, an offered version's `game`, a container's recorded `game`. Named: the entry point, the field, the name and `SHAPE_NAMES`; never defaulted (`docs/L1/shapes.md` §2) |
| `ShapeMismatch` | two declarations of **one** shape disagree — a member's record against its pool's shape, a member's record against its container's shape, an offered version against the pool, a cell's two sides, a matrix's variant against its pool, a matrix's cells against each other or against its own `game`, and the run, pool and matrix a report is handed. Named: the entry point, both (or all three) declarations and the shape each names |
| `UnknownExploration` | `policy_from`'s mode is neither `schedule` nor `off`. Named: the entry point, the mode and `EXPLORATION_MODES` (§5) |

One class per contract and not one per site — a class per site would add seven names no caller could act on differently: a caller
routes on "two shapes disagree", never on which pair disagreed, exactly as `RuleMismatch` covers both a record against a checkpoint
and a version against its family (`families.md` §6, `errors.md` §2, §4). **A fourth refusal is not here**: `SeatCountExceeded` is
about one shape's seat count and not about two declarations disagreeing, so its owner is `seats.md` §3 (`errors.md` §2, D-33).

## 4. Where a shape rides, and the one place it must not

| Carrier | Carries `game`? | Owner |
|---|---|---|
| a `Pool` value and its record | yes — the record's `game` is **required** (`records.md` §8) | `pool.md` §1, §5 |
| a version member record | **required of a non-default member, absent for a default-shape one** (`records.md` §7) | `pool.md` §2 |
| a cell record | yes — this module's own key; `records.md` §9 does not require it, and it names the shape **every hand of the cell was dealt on** | `scheduler.md` §1, §5 |
| a matrix record | yes — this module's own key, **required** of what `matrix` returns, and every cell and member record of it carries the table's (`records.md` §10) | `matrix.md` §5 |
| a rating record | yes — this module's own key (`records.md` §11 requires none) | `rating.md` §5 |
| the report's header family | yes — a tenth key on the report's **own copy**, while `protocol()["header"]` keeps nine | `report.md` §1–§2 |
| a member policy (`_MemberPolicy`), a baseline side | yes, in a `game` slot beside `learning_rule` and `utility` — except a **baseline side**, whose `game` is `None`: it is built for the pool's shape and this module records no shape of it, so the side is **shape-silent** | `scheduler.md` §5, `seats.md` §4 |
| the pool id, and the report's own keys | **never**: the digest is the membership's alone (ASM-27), and the report has no top-level `game` — its twelve keys do not grow | `families.md` §4, `report.md` §2 |

Two consequences follow. A baseline plays **every** declared shape — it answers whatever readout it is handed — so a cell between
two baselines is played on the default shape with today's numbers (`scheduler.md` §1, §5, `seats.md` §4); and the shape is a
**field of records and not of the id**, so two pools of one membership on two shapes share one id and are never one table
(`families.md` §4, `docs/L1/shapes.md` §3).

## 5. The two exploration modes

`policy_from(path, exploration="schedule")`'s mode is a new optional argument whose absence is today's behaviour (`surface.md`
§12, `docs/L1/e2e-surface.md` §3.4): **`schedule`**, the default, is the keyed draw `agents.as_policy` already makes
(`docs/L3/agents/rule.md` §4); **`off`** is the masked maximum and the tie-break alone, with **no generator drawn from** — the
greedy reading `sizing.md` §7's census is computed over. The mode is the **policy's** and not the schedule's, because the hyper
block is one declaration for the whole catalogue and the schedule anneals to 0.05 and never to 0 (`sizing.md` §4, D-19); anything
else is `UnknownExploration` naming it and `EXPLORATION_MODES`, and `EXPLORATION_DEFAULT` is `schedule`, so a caller naming no mode
gets the policy it got before the argument existed (`scheduler.md` §5.1, §7).

## 6. What is deliberately free

- whether `SHAPE_NAMES` and its siblings are module constants or one call returning them: only that they are the **three** names, default first, and equal to `engine.game_shapes()`'s — the join battery compares values, never a spelling;
- how a shape's seat count is read — through `seat_count` alone or once inside `require_pairwise`: only that it comes from `engine.game_config`, that no literal `2` or `6` stands here as a game's seats, and that `PAIRWISE_SEATS` is the instrument's arity and not a shape's row (`seats.md` §1, §3);
- how a record's `game` is validated — one helper reused by every entry point (`pool.py`'s and `policy.py`'s) or a check per record: only that an uncatalogued name is `UnknownShape` and two disagreeing declarations are `ShapeMismatch`, in the order each document's refusal list states (`errors.md` §4).
