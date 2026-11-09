# evaluation — the two declarations

- **Owner:** `protocol()` and `league()` — the two `fixed` rows of `surface.md` §3–§4, key by key and in order,
  and the seven evidence families a report is judged against
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `README.md` §3–§4, `report.md` §1–§3, `tables.md` §1, `errors.md` §2

## 1. What these two are

Both are `fixed` rows: neither takes an argument, so neither has an instance that varies (`surface.md` §1,
`e2e-surface.md` §5). Each is rebuilt on every call and equal on two calls, and each is plain data — except
`league()`'s `cell_count`, which is a callable (`surface.md` §1, §4). Neither plays a hand, reads a file or
draws on any stream; the numbers are `league.md` §5's and no others (ASM-14, ASM-21). The two records are the
module's own declaration of itself, so every other document quotes them instead of restating a number: `M` is
`league()["m"]`, a cell size is `league()["tables"][budget]["hands_per_cell"]`, the family names are
`protocol()["families"]`'s keys, and the refusal word for an absent family is that family's `refusal` value.

## 2. `protocol()` — the evidence contract

One mapping, read under exactly these six keys, in this order (`surface.md` §3):

| Key | Value |
|---|---|
| `families` | a mapping keyed by the seven family names of `protocol.md` §1 in its order — `curves`, `pool`, `matrix`, `rating`, `baselines`, `axis row`, `header` — each value §3's record |
| `seeds` | the tuple `(0, 1, 2)`, the fixed seed set (`protocol.md` §2, ASM-2) |
| `header` | the nine header item names, in the order of §2.1, as a tuple of `str` |
| `table_budgets` | the tuple `("live", "full")`, in that order (`records.md` §10, `league.md` §5) |
| `baselines` | the tuple `("random", "always-call", "oracle")` — the catalogue's `anchor: True` members, in `agents.baselines()`'s order, so a folding baseline D-21 adds is never in it (ASM-32, `agents/surface.md` §11) |
| `rating` | §2.2's record: the method, the interval's confidence and the anchor (`docs/L1/league.md` §5) |

### 2.1 The nine header items

`protocol()["header"]` is exactly these nine names, in this order, because they are what a third party needs to
re-run a table (`protocol.md` §1, `records.md` §12):

    game                the fixed game's configuration          engine.game_config()
    action space        the three-index action vocabulary       features.action_space()
    parameter counts    every member's measured parameter count
    sample budget       the hands a run trained for
    cell size           league()["tables"][budget]["hands_per_cell"]
    seeds               the seed set the run used
    table seed          league()["table_seed"]
    device              the device the run used, and `cpu` inside the sandbox (protocol.md §6)
    checkpoints         the checkpoint paths the run retained (records.md §12)

`report` reads a header family by these names (`report.md` §3, item 5). **The presence rule, exactly:** let
`token(text)` be `text` lowercased with every character outside `[a-z0-9]` removed; an item is present when some header
key's `token` equals the item's, or contains it, or is contained by it — so `checkpoint paths` satisfies `checkpoints`,
their tokens being `checkpointpaths` and `checkpoints`. No other leniency exists.

### 2.2 The rating row

`protocol()["rating"]` and `league()["rating"]` are one value, equal on both sides:

    {"method": "Bradley-Terry", "confidence": 0.95,
     "anchor": "the mean of the three anchor baselines fixed at 0 — random, always-call, oracle"}

`method` is the one `str` `Bradley-Terry`, which is also `rating()["method"]`; `confidence` is `0.95`, the interval's level;
`anchor` is **this section's sentence**, the one home of a value whose tokens are fixed rather than whose spelling is: it
**names** the three the fit zeroes on, spelled from `BASELINES` rather than copied, so a reader is told which baselines the scale
is relative to and a folder — a member a declaration may add — is never among them (`rating.md` §5, ASM-17, ASM-32, D-21).

## 3. The seven families

`protocol()["families"][name]` is one record per family, with two keys: `required`, the tuple of item names the
family's value must carry, and `refusal`, the exact `str` a report raises when the family is **absent** — the
same word `protocol.md` §1 spells, `axis row`'s space included (D-6, `records.md` §13).

| Family | `required` | `refusal` | What the value is |
|---|---|---|---|
| `curves` | `("samples", "signal", "spread")` | `curves` | per variant, per seed: the sample axis, at least one learning signal from `agents.learn`, and the spread across seeds (D-6) |
| `pool` | `("id", "m", "frozen", "members")` | `pool` | `records.md` §8's pool record, i.e. the shape `pool_members` returns, its `rules` and `utilities` included (D-16, ASM-16, D-20) |
| `matrix` | `("members", "cells", "hands_per_cell", "table_seed", "table")` | `matrix` | `records.md` §10's matrix record at one budget (§4) |
| `rating` | `("values", "method", "anchor", "bound_applied", "bootstrap_seed", "converged")` | `rating` | `records.md` §11's rating record (`rating.md` §5) |
| `baselines` | `("rows",)` | `baselines` | every baseline row of the catalogue the configuration declares inside that matrix — always the three anchor baselines, and the three folders of D-21 when it names them — each at the table's one hand count (`protocol.md` §3, ASM-32, D-21) |
| `axis row` | `("value",)` | `axis row` | R4–R6: the rung's own pair's cell beside its matched budgets; R1–R3: the explicit value `n/a, single variant` (`protocol.md` §1) |
| `header` | the nine names of §2.1 | `header` | the header record itself (D-6) |

A family's `required` tuple names the **content items** that family's value is about, and it is what the report (and
the unit battery) promises to carry; it is *not* a list of keys inside a value. That is why `baselines` is
`("rows",)` and `axis row` is `("value",)`: a single-variant rung's axis row *is* the string `n/a, single variant`,
and `report` copies it through verbatim, never wrapping it into a record to satisfy a key name — it checks a
family's **presence** and its key name's spelling, and nothing deeper (`report.md` §1–§2, §4).

**D-19 adds no family and no required item, and D-20 adds neither on the utility axis; D-21 adds only a key.** The
rules and the utilities a run held ride inside two things that already exist: the `pool` family's value, which is
`records.md` §8's record and carries `rules` and `utilities`, and the `header`, which the run record already fills
(`records.md` §8, §12, D-19, D-20). So `protocol()`'s `families` keeps its seven names with their `required` tuples
unchanged, `HEADER_ITEMS` keeps its nine items, and `league()`'s one addition is `catalogue`, which names the baselines a
declaration may add and which no family reads; a new required item would refuse a record another battery hand-builds (`rules.md` §4, `errors.md` §5, ASM-32, D-21).

## 4. `league()` — the league's parameters

One mapping, read under exactly these seven keys, in this order (`surface.md` §4):

| Key | Value |
|---|---|
| `m` | `5` — M, the window's bound (`league.md` §2, ASM-14); no declaration may exceed it (`surface.md` §5) |
| `baselines` | `("random", "always-call", "oracle")`, the **pinned** three (D-6, ASM-32) |
| `catalogue` | all six names `agents.baselines()` declares, in its order: the names a membership declaration may add beyond the pinned set, which is why `build_pool` refuses an uncatalogued name and admits a catalogued one (D-21, `records.md` §8) |
| `tables` | §4.1's mapping, keyed `live` then `full` |
| `cell_count` | the callable of §5 (`surface.md` §4) |
| `table_seed` | `20261105` — the one integer every matrix is played from (§6) |
| `rating` | §2.2's three-key record |

### 4.1 The two budget rows

`league()["tables"]` is keyed `live` then `full`; each row carries three keys, in this order:

    hands_per_cell   live 120, full 1500 — the one hand count of every cell (ASM-14, league.md §5)
    hands_played     {4: 720, 9: 4320, 10: 5400} live, {4: 9000, 9: 54000, 10: 67500} full
    produced_by      live: "the talk, on the fly"; full: "an offline job shipped under tables/" (D-8, D-16)

`hands_played` is keyed by K, the membership's size, and each value is `cell_count(K) × hands_per_cell`'s
product — the arithmetic `tables.md` §1 tabulates. The K = 4 row is the baselines-plus-one-variant table a first
rung plays (`league.md` §2); K = 9 and K = 10 are a full window with one and with two variants (ASM-14). A configuration
that declares D-21's three folders plays K = 12 or 13 and 66 or 78 cells, `docs/L1/folders.md` §5's arithmetic and not a row
declared here (ASM-33, D-21). No row carries a per-hand cost figure: ASM-21 ratifies the measured 0.105–0.153 s/hand —
wide because the oracle decides it, 0.255–0.315 s/hand in an oracle-bearing cell against 0.002–0.004 without, in half a table's
hands — and supersedes ASM-15's 40 ms bound, so a "ceiling" here would have no ratified source, and a measured cost is
recorded only in a run record's `timings` and in the shipped artefact's cost block (`records.md` §12, ASM-21, `docs/L1/league.md` §7).

## 5. `cell_count` — the one callable

`league()["cell_count"]` is a callable returning `K(K−1)/2`, so a talk sizes its table before it plays one
(`surface.md` §4, D-16). It accepts three shapes and refuses the rest: an integer `K` — `cell_count(9)` is `36`,
`cell_count(10)` is `45`, `cell_count(4)` is `6`; a membership sequence, `len(members) × (len(members) − 1) // 2`; and a mapping
carrying `members`, the same of `len(value["members"])`.

It refuses a `K` below `2` (fewer than two members has no unordered pair), a `bool`, a `str`, and any value that is
none of the three shapes, raising `InvalidMembership` (errors.md §2). It is the only callable `league()` carries and the
only non-plain value this module returns besides a pool and a policy; nothing calls it as a mapping key, so its identity is free (§8).

## 6. The table seed

`table_seed` is the league's one integer and the value every matrix record carries as its `table_seed`
(`surface.md` §10, `records.md` §10). This design fixes it at **`20261105`** — the design revision's own date, so it is
recognisable as the league's and is no battery instance. Three consequences: `matrix` takes no seed argument and reads this
one from `declarations.py` (`matrix.md` §3); `rating` seeds its bootstrap from the matrix's own `table_seed` (`rating.md` §4);
and the shipped artefact records it beside its membership (`tables.md` §3) — a different table seed is a different experiment, never a parameter of an entry point (`surface.md` §4).

## 7. Refusals

Neither entry point refuses anything: both have no argument (`surface.md` §3–§4); the one error either can raise is
`InvalidMembership` from the `cell_count` callable (§5) — a callable's argument and not a declaration.

## 8. What is deliberately free

- the container of `seeds`, `table_budgets`, `baselines`, `catalogue` and `header`: a tuple or a list — a reader compares values and order, never a type; this design builds tuples;
- the identity of the `cell_count` callable — a closure, a `functools.partial` or a method: only that it has §5's behaviour, so `surface.md` §4's "equal records" is equal value for value, with the callable equal in behaviour and never by identity.
