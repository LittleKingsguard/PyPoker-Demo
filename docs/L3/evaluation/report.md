# evaluation — the per-rung report

- **Owner:** `report` — the seven evidence families and their order (§1), the report record (§2), the refusal
  grammar and its order (§3), the membership rule (§3), and what a report never does (§4) (`surface.md` §13,
  `records.md` §13, `protocol.md` §1)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `declarations.md` §2–§3, `matrix.md` §1, `rating.md` §6, `errors.md` §2–§4

## 1. The seven families, in this order

`report(rung_name, record, matrix, rating)` judges `record` — the run record with the seven evidence families
attached (`records.md` §12–§13) — against `protocol()`'s declaration, and returns one record carrying them
(`protocol.md` §1, D-6, D-16):

| # | Family | What the report carries | The word its absence is refused with |
|---|---|---|---|
| 1 | `curves` | per variant, per seed: the sample axis and at least one learning signal from `agents.learn`, with the spread across seeds | `curves` |
| 2 | `pool` | `records.md` §8's pool record — id, M, the ordered members with lineage, and `rules`: the **population the report's table was measured over** — i.e. the shape `pool_members` returns, completed where it must be (`rules.md` §4, D-19) | `pool` |
| 3 | `matrix` | the matrix record the report is about (§2) | `matrix` |
| 4 | `rating` | the rating record fitted to it | `rating` |
| 5 | `baselines` | the three baseline rows inside that matrix, each at the table's one hand count | `baselines` |
| 6 | `axis row` | R4–R6's own pair's cell beside its matched budgets; R1–R3's explicit value `n/a, single variant` | `axis row` |
| 7 | `header` | the nine header items of `declarations.md` §2.1 | `header` |

The names are `protocol()["families"]`'s keys, `axis row`'s space included, and they are the same seven strings in
the report's own keys: a report is machine-readable evidence and a reader finds a family by the name the protocol
spells (`surface.md` §13, `battery.md` §3 FAM-4, FAM-11).

**D-19 adds no eighth family and no new required item.** The rules a run held ride inside two keys that already exist: the
`pool` family, which is `records.md` §8's record and carries `rules`, and the `header`, which the run record already fills
with the facts a third party needs (`records.md` §8, §12, `protocol.md` §1, D-19). A new *required* item would refuse a
record another battery hand-builds, which is over-refusal and therefore a defect of its own (`errors.md` §5, D-19).

## 2. The record

`report` returns one mapping. Its keys, in order: the five facts beside the families, then the seven families
(`records.md` §13, `protocol.md` §2):

| Key | Content |
|---|---|
| `rung` | `rung_name` as given — a rung's name, or an unregistered configuration's own label (`ladder.md` §1, `records.md` §12) |
| `seeds` | the seed set the run used, read from `record`'s own `seeds`, else from its header family's seed item (`protocol.md` §2) |
| `table` | `matrix["table"]` — `live` or `full`, the budget the report's table was measured at |
| `table seed` | `matrix["table_seed"]` — the league's one integer, so a third party re-plays the same table (`league.md` §3) |
| `device` | the header family's device item — `cpu` inside the sandbox — so a GPU run and a CPU run are never confused (`protocol.md` §6, D-8) |
| `curves` … `header` | the seven families, in §1's order, each copied **by value** from `record` |

`matrix` and `rating` are the report's own arguments, and they are what the `matrix` and `rating` keys carry: the
report is *about* them, and `surface.md` §13 hands them to it directly as well as through the record. Every other
family is a copy of the record's value, unchanged — a `curves` list stays that list, a `baselines` row-record stays
that record, and `axis row` stays the string `n/a, single variant` when that is what the run wrote (FAM-11.10). The
report copies and never merges, so no family is reshaped into a second spelling of itself.

**The one fact a report completes is the pool family's `rules`** (`rules.md` §4, D-19). The population the report's table
was measured over is the pool's own version members' rules plus the rung's variants' — the members a table holds outside
the pool — and that is exactly the matrix's `population` (`matrix.md` §5, `records.md` §10). When the pool block already
names it, the family is copied as it stands; when it declares fewer, the report states the population on its own copy of
that family, adding the names the pool's block lacks in `population`'s order and nothing else (§4). The record
handed in — the run record, and the pool block inside it — is never edited, so a caller keeps what `training` gave it and a
second call on the same arguments gives an equal report (`surface.md` §13, `records.md` §13).

## 3. The refusals, and the membership rule

`report` refuses before it builds anything, in this order. The first two are about presence, because a family that
is absent cannot be judged (`records.md` §13, D-6):

1. **an absent family** — `MissingFamily`, naming it **exactly as `protocol()` spells it**, `axis row` included. A
   family is present when `record` carries a key whose letters-and-digits token equals the family's (`axis row`,
   `axis_row` and `axisrow` are one name, `_surface.has_family`'s tolerance) **and** that key's value is not `None`:
   an explicit `n/a` value — a `str`, an empty container, a record of `n/a` rows — satisfies a family, while a
   missing key or a `None` value is refused (`records.md` §13, D-6);
2. **a matrix that is not a table** — `rating.md` §6's seven checks, reused verbatim: the same rules and the same
   messages, so a refusal names the violated rule (`cells`, `hands`, `pair`, the missing baseline) and not this entry
   point, because the check is the rating's own (`errors.md` §3, `surface.md` §13, `league.md` §4). The report never
   repairs a table and never rates one itself;
3. **the membership rule** — `MembershipMismatch`, naming what it found:
   - the pool family's members are read from the report's `pool` family as a pool record (§1 item 2), and **every one
     of them must be in the matrix's membership** (`league.md` §3) — a missing pool member is named;
   - **the three baselines must be in the membership** by id — `random`, `always-call`, `oracle` are the table's only
     fixed standard (`protocol.md` §3) — a missing baseline is named;
   - **at most two members may lie outside the pool**, and each is named as a foreign member: those two are the
     rung's variants, which `matrix` named `variant-1` and `variant-2` (`matrix.md` §1, `ladder.md` §2);
4. **the rating's member identity** — `RatingMismatch`: `rating["values"]` must name **exactly** the matrix's
   members, no more and no fewer, and the difference is named (`records.md` §11, FAM-16.25);
5. **a header missing one of the nine items** — `HeaderIncomplete`, naming the item (`declarations.md` §2.1).

A `rung_name` that is not a `str`, or a `record` that is not a mapping, is `InvalidArgument` (errors.md §2),
raising the same way rather than returning a partial report.

## 4. What a report never does

- **It never invents a family, and never fills one in** — not an empty `curves`, not a zeroed `baselines` row, not a
  header item it could guess (`protocol.md` §1, D-6). An absent family is refused by name, which is why §3's first
  refusal comes before every other check.
- **It never invents a version.** R1 has no lineage, so its `pool` family is the three baselines and nothing else:
  the report carries the pool record it was handed and adds no member to it (`league.md` §2, FAM-11.9).
- **It never *requires* a new content item, and never edits an argument to make one fit.** D-19's population is carried
  inside the `pool` family's own `rules` key (§1–§2) and no family's `required` tuple grows, so a record another battery
  hand-builds is still a reportable record (`declarations.md` §3, `errors.md` §5, D-19).
- **It never reduces the matrix to a ranking**, and it never sorts members by rating: the matrix is carried raw, both
  directions of every cell, and the rating travels beside it because a fit assumes a transitive order that poker
  payoffs need not have (`league.md` §3, `protocol.md` §2, D-16).
- **It never plays a hand, reads a file or moves a stream**: a report is assembled from records alone
  (`module-map.md` §3, D-13, `surface.md` §13).
- **It never claims more than the table says.** A rating inside the report is a statement about the table's named
  members on this game at this cell size, and nothing in the report upgrades it into a claim of poker skill
  (`league.md` §8, D-16).
- **It never edits the run record it is handed**: the argument is read, not mutated, so a caller keeps what
  `training` gave it, and the completed `rules` is written onto the report's own copy of the pool family (`records.md`
  §13, `rules.md` §4).

## 5. What is deliberately free

- the container of `seeds` (a tuple or a list) and whether the report's copies are shallow or deep, as long as a
  caller cannot reach back into the run record through the report;
- the identity of each copied family's value — the report may copy or share, but it never reshapes;
- the wording of a `MembershipMismatch` message beyond naming the member or the baseline at fault, and whether the
  three baseline checks report the first missing one or the first *in `agents.baselines()`'s order* — both are
  conforming (`errors.md` §3 fixes the grammar, not that order).
