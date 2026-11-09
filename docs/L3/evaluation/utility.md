# evaluation — the utility axis

- **Owner:** the **utility** a member was trained under, as this module reads and records it — the catalogue through
  the granted arrow (§1), the declared default and what `records.md` §7's required key means here (§2), the records
  that name one (§3), the disagreements that are refused (§4) and what is free (§5) (`utilities.md` §2, §5, §7, §9, D-20)
- **Ceiling:** 100 lines. At the ceiling, split by owner — never append
- **Read with:** `pool.md` §2, §5, §8, `families.md` §1, §4, §6, `scheduler.md` §4–§6, `matrix.md` §5, `report.md` §2,
  `tables.md` §5, `errors.md` §2–§4

D-20 makes the terminal reward a second catalogue beside the estimator, and this module carries it exactly as D-19 made
it carry the rule beside the estimator (`rules.md` §4, D-19, D-20). This document owns the utility-facing rules;
`pool.md`, `families.md`, `scheduler.md` and `matrix.md` each state the utility **field** in their own record and cite
this document for the rule it obeys, so no rule has a second home to drift from (`module-map.md` §2, D-13).

## 1. The catalogue, through the granted arrow

`agents.learners()["utilities"]` publishes the catalogue in declared order — `net-chips` first, `stack-shortfall`
second, each stated with the reward it delivers (`utilities.md` §2, D-20). `pool._utility_catalogue()` reads it on
**every call** and keeps no copy of the names, because a copy is a second catalogue that drifts from the one a learner
spec selects from (`utilities.md` §5, `module-map.md` §2, D-19, D-20). A name this module accepts is therefore a name
`agents.build_learner` accepts.

A catalogue that publishes nothing is no catalogue: `_utility_catalogue()` returns the empty tuple, so a member
naming any name is refused by name (§4). `agents.learners()`'s mapping is the only place it is read from (D-20).

## 2. The declared default, and what "required" means at this edge

`records.md` §7 makes `utility` a **required** key of a version record, and at this edge that requirement is met by
**refusing an absent key by name** — `MemberInvalid`, "the member is missing the required key 'utility'" (§4) — and never
by reading a default: the pool is the only witness of what its member was trained under, so silence is not admissible in
a membership declaration (`build_pool`) or in a version offered to a pool (`offer`) (`records.md` §7, §8, `utilities.md` §5, ASM-27, D-20).

The default of `utilities.md` §5 speaks for exactly two places, and for neither of those: a **variant entry**'s `utility`
and a **learner spec**'s (`records.md` §2, §3); it is declared there and never inferred from a caller. A name that **is**
declared but uncatalogued is `UnknownUtility`, never mapped onto it (`utilities.md` §5, §4, D-19, D-20).

The one reading that stays optional is the **bare §7 record** handed to a policy entry point — `_member_policy`, so
`match`, `matrix` and `opponent` — where the record declares nothing into a pool: its `utility` is read only to be
compared with the one its checkpoint records, and declaring none is admitted because the container is the witness there
(`scheduler.md` §5, `utilities.md` §6, `policy.py`'s `_utility(..., required=False)`, D-20).

The name's own shape is the rule's: a `utility` must be a non-empty `str` with no `"\n"`, no `"\r"` and none of the
digest's `"\x1f"`, or it is `MemberInvalid` exactly as such an `id`, `lineage` or `rule` is (`families.md` §4, §6, D-20),
because a field that carried the separator could smuggle one member's utility into another's line (`families.md` §4).

## 3. The records that name a utility

One utility is named in several places, and they agree wherever a place names one: silence is the declared default only
where §2 admits it and refused by name where §2 requires the key (`utilities.md` §5, §7). The places:

| The record | What it carries | Its owner |
|---|---|---|
| a version record (`records.md` §7) | its `utility`, required by the shape and refused by name when absent (§2) | `pool.md` §2, `families.md` §1 |
| a pool record (`records.md` §8) | each version's `utility`, and `utilities`: the distinct names in the window's order, the **empty tuple** for R1's baselines-only pool | `pool.md` §5 |
| a cell record (`records.md` §9) | `utilities`: each member's by its id, `None` for a baseline or an opaque policy that carries none | `scheduler.md` §4 |
| a matrix record (`records.md` §10) | `utilities` by id, and `utility_population`: the distinct names, **sorted** | `matrix.md` §5 |
| the report's pool family (`records.md` §13) | `utilities`, completed to the population the table measured | `report.md` §2 |
| a variant's recipe in the artefact (`tables.md` §5) | the `utility` the offline recipe built it under, where the recipe records one | `tables.md` §5 |

A **baseline** carries none: it is a fixed policy and not a trained member, so a cell or a matrix states `None` for it
and a baselines-only pool's `utilities` is the empty tuple (`records.md` §9, §10, `scheduler.md` §4, D-20). An **opaque
policy** handed in from outside carries whatever its own `utility` attribute says, `None` for a plain function, which
is the same rule `params` and `rule` get (`scheduler.md` §5, ASM-10, D-20).

The **rating reads none of them**: a fit is a function of the cells, so `utilities` and `utility_population` are evidence
about who played and not inputs to it (`rating.md` §1, `league.md` §4, D-20). A reader comparing two members reads the
population first, because two models asked different questions are not like-for-like (`utilities.md` §9, D-20).

## 4. The three disagreements, and the refusals

A utility is declared in more than one place, and a disagreement between two declarations is refused where it is
found, before anything is built or played (`errors.md` §1, §3):

| Where | Class | The rule it names |
|---|---|---|
| a family's members, at `build_pool` | `UtilityMismatch` | two utilities in one chain — the member, its utility, its family's utility and that family's label (`families.md` §1, §6) |
| `offer` | `UtilityMismatch` | the version's utility differs from the family it extends — the version, both utilities and that family's newest member (`families.md` §5) |
| a member record as a policy — `_member_policy`, so `opponent`, `match` and `matrix` | `UtilityMismatch` | the record's `utility` contradicts the one its checkpoint records — the member, both utilities and the path, **after** the load and before a hand (`scheduler.md` §5, `utilities.md` §6) |
| `build_pool`, `offer` | `UnknownUtility` | the name is not one the catalogue carries — the member, the name and the catalogue (`utilities.md` §5, D-20) |
| `build_pool`, `offer` | `MemberInvalid` | the utility is **absent**, so nothing declares the objective the member was trained under, or it is empty, or not a `str`, or carries `"\n"`, `"\r"` or the digest's separator — the member and the value, the absent key by name (§2) |

The second and third rows are the rule's own two refusals with the objective in their place: `RuleMismatch` is
`UtilityMismatch`'s twin in both, and neither is raised in the other's stead (`families.md` §1, §5, `scheduler.md` §5,
D-19, D-20). Canonical spellings, as `src/evaluation/pool.py` and `policy.py` raise them (`errors.md` §4 owns them):

    build_pool(member 'version-kestrel'): the member is missing the required key 'utility'
    offer(version 'version-osprey'): the member is missing the required key 'utility'
    build_pool(member 'version-kestrel'): the utility must be a non-empty string without a newline or the digest's separator, got ''
    build_pool(member 'version-kestrel'): the utility 'chips-per-hour' is not one of the catalogue's ('net-chips', 'stack-shortfall')
    build_pool(member 'version-osprey'): the utility 'stack-shortfall' is not the utility 'net-chips' of the family it extends, whose start is 'R3/start'
    offer(version 'version-osprey'): the utility 'stack-shortfall' is not the utility 'net-chips' of the family it extends, whose newest member is 'version-marlin'
    match(left): the member 'version-kestrel' records the utility 'stack-shortfall' and its checkpoint 'checkpoints/x.pt' records 'net-chips', and a member is trained under one objective

Each follows `errors.md` §3's grammar, naming the entry point, the member by its id and both values, the absent key by name (§3–§4).

## 5. What is deliberately free

- the container of a cell's or a matrix's `utilities` — a mapping keyed by member id, this design's, or a sequence of
  entries — because `records.md` §9–§10 fix one entry per member and not the container (`matrix.md` §5, §8);
- the wording of each §4 message beyond the parts §4 names (`errors.md` §3 fixes the grammar, not the wording).
