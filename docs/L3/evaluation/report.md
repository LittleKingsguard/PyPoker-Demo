# evaluation — the per-rung report

- **Owner:** `report` — the seven evidence families and their order (§1), the report record (§2), the refusal
  grammar and its order (§3), the membership rule (§3), and what a report never does (§4) (`surface.md` §13,
  `records.md` §13, `protocol.md` §1)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Rev 6:** D-29's second shape — the run, the pool family and the matrix must name one shape (refused naming all three), and the header family names the resolved shape as a tenth key on the report's own copy while `HEADER_ITEMS` stays nine (§1–§4, `shape.md` §4) · **Rev 7:** D-33's third shape — a report is a report of a table, so the six-seat refusal reaches it through the table checks, before a family is assembled, and a six-seat run has no report at all (§1, §3, `seats.md` §5, D-22, D-33)
- **Read with:** `shape.md` §2–§4, `declarations.md` §2–§3, `matrix.md` §1, §5, `utility.md` §3, `rating.md` §6, `errors.md` §2–§4, `seats.md` §1, §5

## 1. The seven families, in this order

`report(rung_name, record, matrix, rating)` judges `record` — the run record with the seven evidence families
attached (`records.md` §12–§13) — against `protocol()`'s declaration, and returns one record carrying them
(`protocol.md` §1, D-6, D-16):

| # | Family | What the report carries | The word its absence is refused with |
|---|---|---|---|
| 1 | `curves` | per variant, per seed: the sample axis and at least one learning signal from `agents.learn`, with the spread across seeds | `curves` |
| 2 | `pool` | `records.md` §8's pool record — id, M, the ordered members with lineage, and `rules` **and** `utilities`: the two **populations the report's table was measured over** — i.e. the shape `pool_members` returns, completed where it must be (`rules.md` §4, `utility.md` §3, D-19, D-20) | `pool` |
| 3 | `matrix` | the matrix record the report is about (§2) — and it must be a table a pair can express: a matrix on a shape with more than two seats is refused by §3's table checks, so no report exists for such a shape (`seats.md` §5, D-22, D-33) | `matrix` |
| 4 | `rating` | the rating record fitted to it | `rating` |
| 5 | `baselines` | every baseline row of the catalogue the configuration declares inside that matrix — always the three anchor baselines, and the three folders of D-21 when the declaration names them — each at the table's one hand count (`protocol.md` §3, ASM-32, D-21) | `baselines` |
| 6 | `axis row` | R4–R6's own pair's cell beside its matched budgets; R1–R3's explicit value `n/a, single variant` | `axis row` |
| 7 | `header` | the nine header items of `declarations.md` §2.1 — and, on the report's own copy, the tenth key `shape` (§2) | `header` |

The names are `protocol()["families"]`'s keys, `axis row`'s space included, and they are the same seven strings in
the report's own keys: a report is machine-readable evidence and a reader finds a family by the name the protocol
spells (`surface.md` §13, `battery.md` §3 FAM-4, FAM-11).

**The header family names the shape.** Its nine items are what a **record** must state, and they do not grow; the shape is
what the **report** resolves, from the three records it judges — the run record's own `game`, the `pool` family's `game`
and the matrix's `game`, each absent reading as the default shape — and then writes as a tenth key onto its own copy of that
family (§2–§3, `records.md` §13, `shape.md` §2, §4). So `protocol()["header"]` and `HEADER_ITEMS` stay at nine, no record
already on disk is refused for a missing one, and `declarations.md` §3's `header` row claims no ten-item `required` tuple.

**D-19 adds no eighth family and no new required item, and D-20 and D-29 add neither on their own axes.** The rules, the
utilities and the shape a run held ride inside things that already exist: the `pool` family, which is `records.md` §8's
record and carries `rules`, `utilities` and `game`, and the `header`, which the run record already fills and which the report
completes with the shape it resolved (`records.md` §8, §12, `protocol.md` §1, D-19, D-20, D-29). A new *required* item would
refuse a record another battery hand-builds, which is over-refusal and therefore a defect of its own (`errors.md` §5,
`report.md` §4).

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
report copies and never merges, so no family is reshaped into a second spelling of itself. **The report's own keys stay
the twelve**: these five facts and the seven families, with **no top-level `game`** — the shape rides inside the header
family, which is where a reader looks for what a table was measured on (`shape.md` §4).

Two completions are therefore written onto the report's own copies, and never onto an argument: the pool family's `rules` and its `utilities` (below), and the header family's tenth key **`shape`** — the one shape the run, the pool and the matrix agree on (§1, §3), written beside the nine items that family already carries, `n/a` and a hand-built header alike (§4).

**The facts a report completes are the pool family's `rules` and its `utilities`** (`rules.md` §4, `utility.md` §3,
D-19, D-20). The population the report's table was measured over is the pool's own version members' rules plus the rung's
variants' — the members a table holds outside the pool — and that is exactly the matrix's `population`; its utilities are
the same sum and exactly the matrix's `utility_population` (`matrix.md` §5, `records.md` §10). So a report states both
labels of the population it fitted over, and **the same rule completes `utilities` as completes `rules`**: when the pool
block already names a population, that label is copied as it stands; when it declares fewer, the report states the
population on its own copy of that family, adding the names the pool's block lacks in `population`'s order (and, for
`utilities`, in `utility_population`'s) and nothing else (§4). A pool block that states neither gains both keys, which is
a completion of a copy and not a new required item (§1, §4). The record handed in — the run record, and the pool block
inside it — is never edited, so a caller keeps what `training` gave it and a second call on the same arguments gives an
equal report (`surface.md` §13, `records.md` §13, D-20).

## 3. The refusals, and the membership rule

`report` refuses before it builds anything, in this order. The first two are about presence, because a family that
is absent cannot be judged (`records.md` §13, D-6):

1. **an absent family** — `MissingFamily`, naming it **exactly as `protocol()` spells it**, `axis row` included. A
   family is present when `record` carries a key whose letters-and-digits token equals the family's (`axis row`,
   `axis_row` and `axisrow` are one name, `_surface.has_family`'s tolerance) **and** that key's value is not `None`:
   an explicit `n/a` value — a `str`, an empty container, a record of `n/a` rows — satisfies a family, while a
   missing key or a `None` value is refused (`records.md` §13, D-6);
2. **a matrix that is not a table** — `rating.md` §6's nine checks, reused verbatim: the same rules and the same
   messages, so a refusal names the violated rule (`cells`, `hands`, `pair`, the missing baseline, the seat count) and
   not this entry point, because the check is the rating's own (`errors.md` §3, `surface.md` §13, `league.md` §4); a shape
   with more than two seats is refused there, naming the shape and its seat count, before a family is assembled into a
   report, so a run on that shape has no report at all (`seats.md` §5, D-22, D-33). The report never repairs a table and
   never rates one itself;
3. **the membership rule** — `MembershipMismatch`, naming what it found:
   - the pool family's members are read from the report's `pool` family as a pool record (§1 item 2), and **every one
     of them must be in the matrix's membership** (`league.md` §3) — a missing pool member is named, and a folding baseline a
     declaration admitted is a pool member like any other (ASM-32, D-21);
   - **the three anchor baselines must be in the membership** by id — `random`, `always-call`, `oracle` are the table's only
     fixed standard, and the anchor the rating is zeroed on (`protocol.md` §3, ASM-32) — a missing baseline is named;
   - **at most two members may lie outside the pool**, and each is named as a foreign member: those two are the
     rung's variants, which `matrix` named `variant-1` and `variant-2` (`matrix.md` §1, `ladder.md` §2);
4. **the rating's member identity** — `RatingMismatch`: `rating["values"]` must name **exactly** the matrix's
   members, no more and no fewer, and the difference is named (`records.md` §11, FAM-16.25);
5. **a header missing one of the nine items** — `HeaderIncomplete`, naming the item (`declarations.md` §2.1);
6. **a run, a pool and a matrix that do not name one shape** — `ShapeMismatch`, naming **all three** records and the shape
   each names: the run record's own `game`, the `pool` family's `game` and the matrix's `game`, each absent reading as the
   default shape (`records.md` §13, `shape.md` §2–§3, `docs/L1/shapes.md` §6). It sits last because it is the only check that
   reads all three records — item 2 has already refused a matrix that is not internally one shape (`rating.md` §6), and item 1
   has already refused a family that is absent and so has no shape to resolve — and it names all three rather than the first
   disagreement, so a reader is told which record to re-derive: a run on one shape and a table on another is not a missing fact
   but a contradiction, and the report neither picks one nor reports a table whose header would be true of only two of its three
   records. A shape a record names that the catalogue does not carry is `UnknownShape` on the same three terms (`shape.md` §2).

A `rung_name` that is not a `str`, or a `record` that is not a mapping, is `InvalidArgument` (errors.md §2),
raising the same way rather than returning a partial report.

## 4. What a report never does

- **It never invents a family, and never fills one in** — not an empty `curves`, not a zeroed `baselines` row, not a
  header item it could guess (`protocol.md` §1, D-6). An absent family is refused by name, which is why §3's first
  refusal comes before every other check.
- **It never invents a version, and never requires a folder.** R1 has no lineage, so its `pool` family is the three baselines
  and nothing else, and a configuration that declares no folder reports exactly what it reported before D-21: the
  pinned three are the check, and a folder is present only because a pool held it (`league.md` §2, FAM-11.9, ASM-32, D-21).
- **It never *requires* a new content item, and never edits an argument to make one fit.** D-19's population is carried
  inside the `pool` family's own `rules` key, D-20's inside its `utilities` (§1–§2), and D-29's shape inside the header's own
  tenth key — and no family's `required` tuple grows, so a record another battery hand-builds is still a reportable record
  and every record already on disk stays reportable, the **shape included**: the report never demands a shape item of a
  record (`declarations.md` §3, `errors.md` §5, `shape.md` §4, D-19, D-20, D-29).
- **It never reduces the matrix to a ranking**, and it never sorts members by rating: the matrix is carried raw, both
  directions of every cell, and the rating travels beside it because a fit assumes a transitive order that poker
  payoffs need not have (`league.md` §3, `protocol.md` §2, D-16).
- **It never plays a hand, reads a file or moves a stream**: a report is assembled from records alone
  (`module-map.md` §3, D-13, `surface.md` §13).
- **It never claims more than the table says.** A rating inside the report is a statement about the table's named
  members on this game at this cell size, and nothing in the report upgrades it into a claim of poker skill
  (`league.md` §8, D-16).
- **It never edits the run record it is handed**: the argument is read, not mutated, so a caller keeps what `training` gave it, and the completed `rules`, `utilities` and shape are written onto the report's own copies of the pool and header families (`records.md` §13, `rules.md` §4, `utility.md` §3, `shape.md` §4).

## 5. What is deliberately free

- the container of `seeds` (a tuple or a list) and whether the report's copies are shallow or deep, as long as a
  caller cannot reach back into the run record through the report;
- the identity of each copied family's value — the report may copy or share, but it never reshapes;
- how a **hand-built** matrix's utilities are read — from its `utility_population`, else its per-member `utilities`, else
  its `member_records`: the report takes what the record states, in that order, and infers nothing a record does not say
  (`matrix.md` §5, `errors.md` §5);
- the wording of a `MembershipMismatch` message beyond naming the member or the baseline at fault, and whether the three baseline checks report the first missing one or the first *in `agents.baselines()`'s order* — both are conforming (`errors.md` §3 fixes the grammar, not that order);
- where the tenth header key is placed among the nine, and whether it is written before or after the pool family is completed: only that it is on the report's copy, never in the argument (`shape.md` §4).
