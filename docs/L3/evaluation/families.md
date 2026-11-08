# evaluation — the families of the version window

- **Owner:** the **family** — how a window holding several estimators is grouped (§1), the order its members are
  listed in (§2), the **fair-share eviction** and the (m+1)th-family refusal (§3), the **id digest** that certifies
  each version's rule (§4), `offer`'s rolling (§5), the refusals this design adds (§6) and what is free (§7)
  (`docs/L1/league.md` §2, `docs/L1/records.md` §7–§8, ASM-26, ASM-27, D-19)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `pool.md` §1–§2, §5, §7–§9, `scheduler.md` §5, `matrix.md` §5, `errors.md` §2, §4; at the surface
  `docs/L2/evaluation/pool.md` §1, §3 and `rules.md` §2–§5. `pool.md` §3, §4 and §6 redirect here.

## 1. A family: one chain, under one rule

D-19 makes the pool deliberately heterogeneous, so a window can hold versions trained under different estimators
(`docs/L1/league.md` §1–§2, D-18). The smallest grouping the records already declare is the **lineage chain**:
`records.md` §7 makes `lineage` required, so descent is data this module reads already (`records.md` §7, D-19).

- A **family** is one chain: a **start** — a member whose `lineage` is no declared `id`, a rung label such as
  `"R6-residual"` (`records.md` §7) — then each member whose `lineage` is its predecessor's `id`; and its
  **label** is the label its first member names, that member's own `lineage` value, the one string the declaration
  already carries for it, so nothing is named twice (`records.md` §8, ASM-26).
- Every member declares **one rule**, the start's: `docs/L2/evaluation/rules.md` §3's contract at the surface, held
  here as the invariant this design enforces (ASM-26, D-19). Two rules in one chain is `RuleMismatch`, naming the
  member and both rules (§6): a family is one estimator's line of descent, so a version that changed rule mid-line is
  a different lineage and not a continuation of this one.

Rejected: a `family` or `rule_group` key on the member record, a second declaration of a fact the lineage and the
`rule` already carry; grouping by rule alone, which merges two independent chains into a family whose "newest" member
is ambiguous and so cannot be extended; one declaration as one family, the rule before D-19, which cannot hold a
second estimator (`docs/L1/league.md` §2, ASM-26). Three declarations also cannot be ordered and are refused rather
than guessed (§6): one id in two records (`MemberDuplicate`), one lineage with two successors (`LineageConflict`), a
chain reaching no start (`LineageCycle`) — the last two because a family with two successors or none has no order at
all (`records.md` §7, `docs/L2/evaluation/pool.md` §1).

## 2. The ordered window

A window is one list, and its order is the only thing a caller sees (`pool_members`, `pool.md` §5), the only thing §4
digests, and what `offer`'s "newest" resolves against (§5) — so it is fixed here as three rules:

1. each family's members **contiguously, oldest to newest**;
2. the families in **the order they entered the window** — for a declared membership, the position of each family's
   start in the declaration's `members` sequence;
3. the three pinned baselines first and never inside the window (`pool.md` §2 step 5, ASM-16).

The grouping is derivable from the records alone — a member whose `lineage` is not its predecessor's `id` begins a
family — which is what lets `offer` regroup a window it is handed with no stored family list to fall out of step with
the members (`docs/L1/league.md` §2, `docs/L2/evaluation/pool.md` §1, §2). Rejected: ordering by `step` or `samples`,
keys `records.md` §7 does not require, so an order reading them would refuse a legal record or invent a value
(ASM-26's own rejected alternative); and the declaration's own sequence, the order the links replaced
(`docs/L2/evaluation/pool.md` §1). A window holding **one** family therefore lists exactly what it listed before D-19 — its chain, oldest to
newest — so every pool in the shipped tree reads back unchanged (`docs/L1/league.md` §2, ASM-18).

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
exactly what this section exists to prevent (ASM-26, `docs/L2/evaluation/rules.md` §3). The bound is the
declaration's own `m`, never the league's M when a declaration is tighter (`docs/L1/league.md` §2, D-16).

Rejected: oldest-first over the concatenated window (the rule before D-19, ASM-26's rejected alternative), and raising
M to hold every family, which multiplies the cells as K(K−1)/2 and is capped by the live-table budget (D-18, ASM-14).

## 4. The id digest

    payload = "\n".join(one line per member, in the pool's order)     # no trailing separator
      a baseline's line: <id>          a version's line: <id> "\x1f" <rule>
    id      = "pool-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

Why the rule is inside: D-19 requires the id to certify each version's estimator, so two pools of one membership under
two estimators do not wear one id, and a table can say which population a rating was fitted over (ASM-27, D-19,
`records.md` §8). Why the baselines' lines stay bare: they carry no rule, so a **baselines-only pool digests exactly
as it did before the catalogue existed** — R1's pool, the one id a shipped artefact records, which therefore survives
this change without a regeneration (ASM-27, ASM-14, `protocol.md` §5, `tables.md` §7).

Outside the payload, deliberately: `m`, `frozen` and every other member field, so a corrected `seed` or `step` or a
re-declared bound does not rename the pool (`records.md` §8, `docs/L2/evaluation/pool.md` §1). `"\x1f"` is the
digest's own separator, so no field may carry it, nor a newline: an `id`, a `lineage` or a `rule` that did is
`MemberInvalid` at `build_pool` and at `offer`, before any digest is taken (§6, ASM-27). The id is the pool record's
first key, and what a run record, a matrix and two arms of a pair are compared by (`records.md` §8, §12).

Rejected: digesting the whole member record, which renames a pool when a `seed` or `step` is corrected and so breaks
"changes when and only when the membership does"; digesting the ids alone, where a label cannot be certified and one
member could say `masked-q-learning` while its neighbour said `double-q-learning` under one id (ASM-27's own rejected
alternative); prefixing the baselines' lines to separate the fields by shape, which renames every pool in the tree; and
`hash()`, which is process-salted (ASM-16).

## 5. `offer` extends exactly one family

`offer(pool, version)` returns a new pool, and the version joins **one** family (`pool.md` §7, `surface.md` §7), its
`rule` checked against the catalogue first (§6):

1. its `lineage` names a member that is its own family's **newest** → that family advances; a lineage that is **no
   member's `id`** → a **new family** opens, labelled by that lineage, refused if it would be the (m+1)th (§3) — which
   is how a second arm's first snapshot, naming the rung start its sibling's names, joins the window (ASM-26, D-19);
2. its `lineage` names a member that is not its family's newest → `LineageNotExtended`, naming the lineage and that
   family's newest: the chain would fork, and a fork has no order (`records.md` §7, ASM-26);
3. its `rule` differs from the rule of the family it extends → `RuleMismatch`, naming the version and both rules: one
   family is one estimator (§1);
4. then, if the window now holds `m+1` versions, §3's member is evicted; the baselines are untouched and the id is
   recomputed (§4).

Step 1 is what D-19 bought: before it only one chain was extendable, so a second family could be declared and never
rolled — the finding V-F4 records (D-19, `docs/L1/league.md` §2). Step 2 keeps the window one-directional: an offer is
a snapshot of a lineage, never a fork of it (ASM-18, `pool.md` §7), and `offer` plays no hand and re-reads no
checkpoint, so rolling stays a declaration operation (ASM-2, `docs/L1/league.md` §1).

## 6. The refusals this design adds

| Where | Class | The contract it names |
|---|---|---|
| `build_pool`, `offer` | `UnknownRule` | the name is not one the catalogue carries — named beside the catalogue, never mapped onto the declared default |
| `build_pool` | `RuleMismatch` | a family's members declare two rules — the member, its rule, the family's rule, the family's label |
| `offer` | `RuleMismatch` | the version's rule differs from the family it extends — the version, both rules, that family's newest |
| `build_pool`, `offer` | `FamilyBoundExceeded` | the families asked for exceed the bound `m` — the family count and the bound |
| `offer` | `LineageNotExtended` | the lineage is not its family's newest — the lineage and that family's newest |
| `build_pool` | `MemberDuplicate`, `LineageConflict`, `LineageCycle` | §1's three unorderable declarations |

Canonical spellings, as `src/evaluation/pool.py` raises them (`errors.md` §4 owns the table):

    build_pool(member 'version-kestrel'): the member is missing the required key 'rule'
    build_pool(member 'version-kestrel'): the rule must be a non-empty string without a newline or the digest's separator, got ''
    build_pool(member 'version-kestrel'): the rule 'masked-q' is not one of the catalogue's ('masked-q-learning', 'double-q-learning')
    build_pool(member 'version-osprey'): the rule 'double-q-learning' is not the rule 'masked-q-learning' of the family it extends, whose start is 'R3/start'
    build_pool(m): the declaration holds 6 families, and a window of 5 cannot keep one member of each
    offer(version 'version-osprey'): its lineage 'version-thistle' is not the newest member of its family, which is 'version-marlin'
    offer(version 'version-osprey'): the rule 'double-q-learning' is not the rule 'masked-q-learning' of the family it extends, whose newest member is 'version-marlin'
    offer(version 'version-osprey'): the pool holds 5 families under a bound of 5, so a new family would leave another without a member

Each follows `errors.md` §3's grammar; a `rule` that is absent, empty or carrying `"\n"`, `"\r"` or `"\x1f"` is
`MemberInvalid` at both entry points. A member **record** whose declared `rule` disagrees with its checkpoint's is the
other `RuleMismatch`, raised in `policy.py` and owned by `scheduler.md` §5–§6: it is about a load, not a window.

## 7. What is deliberately free

- how the families are held while computing — lists, a label→chain mapping, one pass or two: only that §1's grouping
  and §2's order are the result, and whether the window is regrouped per `offer` or carried inside `Pool` (`pool.md` §9);
- how §3's tie is decided — index order, chain sizes or an explicit age — provided ties go to the earlier family, and the wording of each message beyond §6's parts (`errors.md` §3 fixes the grammar).
