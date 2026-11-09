# evaluation — the families of the version window

- **Owner:** the **family** — how a window holding several estimators is grouped (§1), the order its members are
  listed in (§2), the **fair-share eviction** and the (m+1)th-family refusal (§3), the **id digest** that certifies
  each version's rule and its utility (§4), `offer`'s rolling (§5), the refusals this design adds (§6) and what is free (§7)
  (`docs/L1/league.md` §2, `docs/L1/records.md` §7–§8, ASM-26, ASM-27, D-19, D-20)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `pool.md` §1–§2, §5, §7–§9, `utility.md` §1–§4, `scheduler.md` §5, `matrix.md` §5, `errors.md` §2, §4;
  at the surface `docs/L2/evaluation/pool.md` §1, §3 and `rules.md` §2–§5. `pool.md` §3, §4 and §6 redirect here.

## 1. A family: one chain, under one rule and one utility

D-19 makes the pool deliberately heterogeneous, so a window can hold versions trained under different estimators, and
D-20 adds the utility — the reward a member was trained on — as the second axis of the same kind (`docs/L1/league.md`
§1–§2, D-18, D-20). The smallest grouping the records already declare is the **lineage chain**: `records.md` §7 makes
`lineage` required, so descent is data this module reads already (`records.md` §7, D-19).

- A **family** is one chain: a **start** — a member whose `lineage` is no declared `id`, a rung label such as
  `"R6-residual"` (`records.md` §7) — then each member whose `lineage` is its predecessor's `id`; and its
  **label** is the label its first member names, that member's own `lineage` value, the one string the declaration
  already carries for it, so nothing is named twice (`records.md` §8, ASM-26).
- Every member declares **one rule** and **one utility**, both the start's: `docs/L2/evaluation/rules.md` §3's contract
  at the surface for the rule, `utilities.md` §7's for the utility, held here as the invariants this design enforces
  (ASM-26, D-19, D-20). Two rules in one chain is `RuleMismatch` and two utilities is `UtilityMismatch`, each naming the
  member and both values (§6): a family is one estimator's line of descent toward one objective, so a version that
  changed either mid-line is a different lineage and not a continuation of this one.

Rejected: a `family`, `rule_group` or `utility_group` key on the member record, a second declaration of a fact the
lineage, the `rule` and the `utility` already carry; grouping by rule or by utility alone, which merges two independent
chains into a family whose "newest" member is ambiguous and so cannot be extended; one declaration as one family, the
rule before D-19, which cannot hold a second estimator (`docs/L1/league.md` §2, ASM-26). Three declarations also cannot
be ordered and are refused rather than guessed (§6): one id in two records (`MemberDuplicate`), one lineage with two
successors (`LineageConflict`), a chain reaching no start (`LineageCycle`) — the last two because a family with two
successors or none has no order at all (`records.md` §7, `docs/L2/evaluation/pool.md` §1).

## 2. The ordered window

A window is one list, and its order is the only thing a caller sees (`pool_members`, `pool.md` §5), the only thing §4
digests, and what `offer`'s "newest" resolves against (§5) — so it is fixed here as three rules:

1. each family's members **contiguously, oldest to newest**;
2. the families in **the order they entered the window** — for a declared membership, the position of each family's
   start in the declaration's `members` sequence;
3. the **pinned** baselines first and never inside the window: the three the catalogue flags as anchors, then each
   folding baseline the declaration names, both in `agents.baselines()`'s order and never the declaration's (`pool.md` §2 step 5, ASM-16, ASM-32, D-21).

The grouping is derivable from the records alone — a member whose `lineage` is not its predecessor's `id` begins a
family — which is what lets `offer` regroup a window it is handed with no stored family list to fall out of step with
the members (`docs/L1/league.md` §2, `docs/L2/evaluation/pool.md` §1, §2). That regrouping is `_window_families`'s, and
every member it regroups carries the `rule` and the `utility` `offer` then holds it to (`utility.md` §4, D-20). Rejected:
ordering by `step` or `samples`, keys `records.md` §7 does not require, so an order reading them would refuse a legal
record or invent a value (ASM-26's own rejected alternative); and the declaration's own sequence, the order the links
replaced (`docs/L2/evaluation/pool.md` §1). A window holding **one** family therefore lists what it listed before D-19 —
its chain, oldest to newest — so every pool in the shipped tree reads back unchanged (`docs/L1/league.md` §2, ASM-18).

## 3. Fair-share eviction, and the (m+1)th family

When the window already holds `m` versions one member leaves, and which one leaves is this design's choice:

    the oldest member of the family that currently holds the most members;
    ties broken by which family's oldest member is the older — the earlier family,
    because §2 lists the families in entry order.

Three consequences are the point of the rule (ASM-26, `docs/L1/league.md` §2): no family is emptied while another
holds two or more, so a window never silently drops the estimator it claims to hold — the measured failure ASM-26
records against oldest-first; with F families resident, each keeps a member while F ≤ m; and a window holding **one**
family keeps the last `m` of its chain, exactly as before the catalogue, which is what every pool in the tree holds
(ASM-16, ASM-18).

`build_pool` windows a declaration richer than `m` by the same rule and not by "the last m of the concatenation", so
a rich declaration and an equal series of offers reach one membership (`pool.md` §2 step 4,
`docs/L2/evaluation/pool.md` §1). A declaration or an offer that would leave `m+1` families is refused —
`FamilyBoundExceeded` — because a window of `m` cannot keep one member of each, and emptying a family to make room is
exactly what this section exists to prevent (ASM-26, `docs/L2/evaluation/rules.md` §3). The bound is the declaration's own
`m`, never the league's M when a declaration is tighter — and no baseline is ever evicted, because eviction is the window's (`docs/L1/league.md` §2, ASM-32, D-16).

Rejected: oldest-first over the concatenated window (the rule before D-19, ASM-26's rejected alternative), and raising
M to hold every family, which multiplies the cells as K(K−1)/2 and is capped by the live-table budget (D-18, ASM-14).

## 4. The id digest

    payload = "\n".join(one line per member, in the pool's order)     # no trailing separator
      a baseline's line: <id>          a version's line: <id> "\x1f" <rule> "\x1f" <utility>
    id      = "pool-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

Why the rule **and the utility** are inside: D-19 requires the id to certify each version's estimator, so two pools of
one membership under two estimators do not wear one id, and D-20 adds the same requirement for the objective — so a
pool's id changes when its members' objective changes, and a table can say which population and which objectives a
rating was fitted over (ASM-27, D-19, D-20, `records.md` §8, `utility.md` §3). Why the baselines' lines stay bare — their
id alone, no flag and no position: they carry no rule and no utility, so a **baselines-only pool digests exactly as it did
before either catalogue existed**, and a declaration that names no folder yields exactly the membership, the order and the
id it has today — R1's pool, the `pool-bcbea031cb617939` a shipped artefact records, which therefore survives both changes
without a regeneration; a declaration that names a folder simply carries one more bare line (ASM-27, ASM-32, ASM-14, D-21, `protocol.md` §5, `tables.md` §2).

Outside the payload, deliberately: `m`, `frozen` and every other member field, so a corrected `seed` or `step` or a
re-declared bound does not rename the pool (`records.md` §8, `docs/L2/evaluation/pool.md` §1). `"\x1f"` is the digest's
own separator, so no field may carry it, nor a newline: an `id`, a `lineage`, a `rule` **or a `utility`** that did is
`MemberInvalid` at `build_pool` and at `offer`, before any digest is taken (§6, `utility.md` §2, ASM-27). The id is the
pool record's first key, and what a run record, a matrix and two arms of a pair are compared by (`records.md` §8, §12).

Rejected: digesting the whole member record, which renames a pool when a `seed` or `step` is corrected and so breaks
"changes when and only when the membership does"; digesting the ids alone, where a label cannot be certified and one
member could say `masked-q-learning` while its neighbour said `double-q-learning` under one id (ASM-27's own rejected
alternative); leaving the utility out, which repeats that finding for the objective; prefixing the baselines' lines,
which renames every pool in the tree; and `hash()`, which is process-salted (ASM-16).

## 5. `offer` extends exactly one family

`offer(pool, version)` returns a new pool, and the version joins **one** family (`pool.md` §6, `surface.md` §7), its
`rule` and its `utility` checked against the catalogue first (§6, `utility.md` §4):

1. its `lineage` names a member that is its own family's **newest** → that family advances; a lineage that is **no
   member's `id`** → a **new family** opens, labelled by that lineage, refused if it would be the (m+1)th (§3) — which
   is how a second arm's first snapshot, naming the rung start its sibling's names, joins the window (ASM-26, D-19);
2. its `lineage` names a member that is not its family's newest → `LineageNotExtended`, naming the lineage and that
   family's newest: the chain would fork, and a fork has no order (`records.md` §7, ASM-26);
3. its `rule` or its `utility` differs from the value its family's **first** member declares → `RuleMismatch` or
   `UtilityMismatch`, naming the version and both values: one family is one estimator trained toward one objective
   (§1, `utility.md` §4, D-19, D-20);
4. then, if the window now holds `m+1` versions, §3's member is evicted; the baselines are untouched and the id is
   recomputed (§4).

Step 1 is what D-19 bought: before it only one chain was extendable, so a second family could be declared and never
rolled — the finding V-F4 records (D-19, `docs/L1/league.md` §2). Step 2 keeps the window one-directional: an offer is
a snapshot of a lineage, never a fork of it (ASM-18, `pool.md` §7), and `offer` plays no hand and re-reads no
checkpoint, so rolling stays a declaration operation (ASM-2, `docs/L1/league.md` §1).

## 6. The refusals this design adds

| Where | Class | The contract it names |
|---|---|---|
| `build_pool`, `offer` | `UnknownRule`, `UnknownUtility` | the name is not one of its catalogue's — named beside the catalogue, never mapped onto the declared default |
| `build_pool` | `RuleMismatch`, `UtilityMismatch` | a family's members declare two rules or two utilities — the member, its value, the family's value, the family's label |
| `offer` | `RuleMismatch`, `UtilityMismatch` | the version's rule or utility differs from the family it extends — the version, both values, that family's newest |
| `build_pool`, `offer` | `FamilyBoundExceeded` | the families asked for exceed the bound `m` — the family count and the bound |
| `offer` | `LineageNotExtended` | the lineage is not its family's newest — the lineage and that family's newest |
| `build_pool` | `MemberDuplicate`, `LineageConflict`, `LineageCycle` | §1's three unorderable declarations |

Canonical spellings are `errors.md` §4's table — the rule's rows and, beside them, the utility's (`utility.md` §4) —
each following `errors.md` §3's grammar. A `rule` that is absent, empty or carrying `"\n"`, `"\r"` or `"\x1f"` is
`MemberInvalid` at both entry points, and so is a `utility` that is absent, empty or carries one of those — a member that
declares **no** `utility` is refused by name, never read as the catalogue's first member (`utility.md` §2). A member
**record** whose declared `rule` or `utility` disagrees with its checkpoint's is the other pair of refusals, raised in
`policy.py` and owned by `scheduler.md` §5–§6: they are about a load, not a window (`utility.md` §4).

## 7. What is deliberately free

- how the families are held while computing — lists, a label→chain mapping, one pass or two: only that §1's grouping
  and §2's order are the result, and whether the window is regrouped per `offer` or carried inside `Pool` (`pool.md` §9);
- how §3's tie is decided — index order, chain sizes or an explicit age — provided ties go to the earlier family (`errors.md` §3's grammar covers the wording).