# evaluation — the bounded pool

- **Owner:** the pool — the `Pool` value (§1), the declaration (§2), the read-back (§5), the draw `opponent` makes (§7),
  every refusal (§8) and what is free (§9); the **lineage order**, the **id digest** and `offer`'s eviction are
  `families.md`'s (§3, §4, §6), and the utility a member declares is `utility.md`'s (`surface.md` §5–§8, `league.md` §1–§2)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `families.md` §1–§6, `utility.md` §1–§4, `declarations.md` §4, `scheduler.md` §5, `matrix.md` §1,
  `errors.md` §2–§4

D-19 gave the window more than one estimator, and the three sections that followed from it — the lineage order, the id
digest and `offer`'s eviction — moved to `families.md` under their own owner. Their **numbers stay here as redirects**,
because other layers cite `pool.md` §3, §4 and §6 by number (`README.md` §2, D-12, ASM-26, ASM-27).

## 1. The value

A pool is one ordered member list plus its bound, its frozen flag and its id — both the opposition the training loop
samples and a table's rows and columns (`league.md` §1, D-16). It is **opaque**: a caller only passes it back to
`pool_members`, `offer`, `opponent` and `matrix` (`surface.md` §1). `src/evaluation/pool.py`:

    class Pool:                       # immutable; no caller reads it, no record exposes it
        id:      str                  # families.md §4's digest
        m:       int                  # the bound this pool holds to, 1 … league()["m"]
        frozen:  bool                 # records.md §8's required flag
        members: tuple                # §5's ordered records, the families contiguous (families.md §2)

`offer` returns a **new** `Pool` and leaves its argument unchanged, so a caller may keep an earlier pool; nothing here
caches, registers or mutates (`surface.md` §7).

## 2. From a declaration to a membership

`build_pool(declaration)` reads exactly three keys — `members`, `m` and `frozen` — and every one is **required**
(`records.md` §8, `surface.md` §5):

1. `members` is a sequence of member records, possibly empty: R1's pool is the three baselines alone (`league.md` §2), and each record must carry an `id`, a `lineage`, a `rule` and a `utility`, all four non-empty `str` and required by the shape as `utility.md` §2 states (`records.md` §7, §8, `utility.md` §1–§2). An `id` that **is one of the three pinned baselines' names** is refused, naming the member: the three are pinned in every pool, so such a version would name one member twice (`surface.md` §5, `errors.md` §4). A `rule` the catalogue does not carry is `UnknownRule`, naming the member, the name and the catalogue — never mapped onto the declared default (`families.md` §6, D-19); a `utility` the catalogue does not carry is `UnknownUtility` on the same terms, and a member naming **none** is refused as a missing required key — `MemberInvalid`, naming the member and the key — never read as the catalogue's first member, because the pool is the only witness of what its member was trained under (`utility.md` §2, `records.md` §7, ASM-27, D-20).
2. `m` is a positive integer no larger than `league()["m"]`: a declaration may be **tighter** than M and never
   wider (`league.md` §2, D-16). A `bool` is refused — a flag is not a bound.
3. `frozen` is a boolean flag (`bool` or the NumPy scalar `bool_`). It is stored, not interpreted: `offer`
   refuses a frozen pool and `matrix` refuses an unfrozen one (`surface.md` §7, §10).
4. The versions are grouped into **families** and ordered, then **windowed to `m`** by the fair-share eviction rule
   `offer` uses: a declaration richer than the bound is windowed, never refused, unless it holds more than `m`
   families (`families.md` §2–§3, `league.md` §2, ASM-18, ASM-26).
5. The three baselines are added **first**, in `agents.baselines()`'s order, each as `{"id": <name>, "baseline": True, "pinned": True, "params": 0}` — a baseline's id is its name (D-16).
6. The id is computed from the ordered member lines (`families.md` §4) and the pool returned.

A member's other keys — `path`, `rung`, `variant`, `seed`, `step`, `samples` — are **carried, not required**; `id`,
`lineage` and `rule` are the three that are refused when absent, because the first two declare a version and order the
window and the third says which population it belongs to (`records.md` §7, D-19, `surface.md` §5); `utility` is the
fourth the shape requires and the one this edge **refuses by name** when it is absent too (`utility.md` §2, D-20). A member
declared **without** `path` is admitted, and `matrix` and `opponent` refuse it when it is asked to be a policy (`pool.md`
§8).

## 3. The lineage order — the families' order: `families.md` §1–§2

The order that stood here is now the **families**: one lineage chain each, every member under one rule, the chains
listed contiguously oldest to newest and the families in the order they entered the window. §2 step 4 above applies it
and `families.md` §1–§2 owns it, with its three unorderable declarations (`ASM-26`, `records.md` §7).

## 4. The id digest — `families.md` §4

The payload is one line per member — a baseline's `id` alone, a version's `id`, `"\x1f"`, its `rule`, `"\x1f"` and its
`utility` — joined by `"\n"`, and the id is `"pool-" + sha256(payload).hexdigest()[:16]`. `families.md` §4 owns the
digest, why the rule and the utility are inside it, and why a baselines-only pool keeps the id it had (`ASM-27`, `D-20`,
`records.md` §8).

## 5. `pool_members` — the read-back

`pool_members(pool)` returns `records.md` §8's pool record, freshly built on each call so a caller that edits it
changes nothing:

    {"id": <families.md §4's id>, "m": <the bound>, "frozen": <the flag>,
     "members": (<the ordered records>,), "rules": (<the distinct rules the versions declare>,),
     "utilities": (<the distinct utilities the versions declare>,)}

`members` is §1's tuple: the three baselines first, then the window **oldest to newest**, each family contiguously
(`families.md` §2). Each baseline is its four-key record of §2 step 5; each version is the `records.md` §7 record the
declaration carried — its `rule` and its `utility` both the declaration's own, refused by name when either is absent, and
nothing filled in — with its own keys and values otherwise untouched. `rules` is the **distinct** rules its version members declare, in the
window's order, and `utilities` their counterpart on the same terms; both are the **empty tuple** for R1's pool, because
a baseline is a fixed policy and not a trained member, so it contributes neither, and the pair is the two populations a
table over this pool measured (`records.md` §8, `families.md` §2, `utility.md` §3, D-19, D-20, ASM-16). A frozen pool's
read-back does not change while it is used, which is how a pair's parity is read (`surface.md` §6).

## 6. `offer`'s rolling — `families.md` §3, §5

`offer(pool, version)` returns a new pool in which the version extends **exactly one family** — the one whose newest
member it names, or a new family when its `lineage` names no member — and a full window evicts **fair-share**, the
oldest member of the family that holds the most, so no family is emptied while another holds two or more
(`families.md` §3, §5, ASM-26). `families.md` §5 owns the four outcomes and §6 their refusals. What this section keeps
is §2's guarantee at the pool's surface: the baselines are pinned and never evicted, the argument pool is unchanged, and
the version's own `rule` and `utility` are required and checked exactly as §2 step 1 checks a declared member's
(`league.md` §2, `surface.md` §7, `utility.md` §4).

## 7. `opponent` — the training loop's draw

`opponent(pool, seed)` draws exactly one member from the pool's ordered membership and returns it as a policy
(`surface.md` §8, D-16):

    index  = seeds._draw_index(seed, len(pool.members))       # seed % the size; scheduler.md §3
    member = pool.members[index]
    policy = agents.build_baseline(member["id"], seed)        if member is a baseline
             policy._member_policy(member)                     otherwise (scheduler.md §5)

A baseline is drawn at the caller's seed and a version at the seed its checkpoint records, read from the container
(`scheduler.md` §5.1, `records.md` §7), so a drawn opponent is one policy that answers one decision one way
(`agents/surface.md` §10, ASM-2). A drawn version's record carries a `rule` and a `utility`, and the policy its file records must agree: a disagreement
is `RuleMismatch` or `UtilityMismatch`, naming the member and both values, raised after the load and before a hand is
played (`scheduler.md` §5–§6, `utility.md` §4, D-19, D-20). It refuses a seed that is not an integer (`InvalidSeed`), a
value that is not a pool (`InvalidPool`), and a drawn version carrying no `path` (`MemberUnloadable`, naming the
member) — a version that cannot be loaded cannot be an opponent (`records.md` §7, `protocol.md` §5). Nothing else: the
draw is the seed's position in the ordering (`league.md` §3, FAM-7.9).

**What `seed % n` promises.** One seed draws one member every time, and it does **not** make distinct seeds distinct
members — only `n` residues exist, so two seeds congruent modulo `n` draw one member. It promises a spread: `n`
consecutive seeds visit each member once, so sampling many seeds samples the whole pool — the satisfiable reading
`surface.md` §8 asserts, where the battery's eight invented seeds over a six-member pool must not all answer one fixed
policy (FAM-7.9).

## 8. Refusals

| Where | Class | The rule it names |
|---|---|---|
| `build_pool` | `PoolDeclarationInvalid` | the argument is not a mapping, or is missing `members`, `m` or `frozen`, or `frozen` is not a boolean — the key is named |
| `build_pool` | `PoolBoundInvalid` | `m` is not a positive integer, is a `bool`, or exceeds `league()["m"]` — the bound is named |
| `build_pool`, `offer` | `MemberInvalid` | a member is not a mapping, or its `id`, `lineage`, `rule` or `utility` is missing, empty, or holds a newline or the digest's separator — the absent key named, and the `utility`'s absence refused like the other three (`utility.md` §2, `families.md` §6) |
| `build_pool`, `offer` | `UnknownRule`, `UnknownUtility` | the `rule` or the `utility` is not one its catalogue carries — the member, the name and the catalogue (`families.md` §6, `utility.md` §4, D-19, D-20) |
| `build_pool` | `MemberUnloadable` | a declared `path` names no readable file — the member is named (`protocol.md` §5) |
| `build_pool`, `offer` | `MemberDuplicate` | two records carry one id, or a declared id is one of the three baselines' names, or an offered version is already a member |
| `build_pool` | `LineageConflict`, `LineageCycle` | two members descend from one, or a chain reaches no start — §3's order has none (`families.md` §1) |
| `build_pool` | `RuleMismatch`, `UtilityMismatch` | a family's members declare two rules or two utilities — the member and both values (`families.md` §1, §6) |
| `build_pool`, `offer` | `FamilyBoundExceeded` | the families asked for exceed the bound `m` — the count and the bound (`families.md` §3) |
| `pool_members`, `offer`, `opponent` | `InvalidPool` | the argument is not a pool this module built (`surface.md` §6) |
| `offer` | `PoolFrozen` | the pool is frozen and its membership does not change while it is used |
| `offer` | `LineageNotExtended` | the lineage is not its family's newest member (`families.md` §5) |
| `offer` | `RuleMismatch`, `UtilityMismatch` | the version's rule or utility differs from the family it extends — the version and both values (`families.md` §5) |
| `opponent` | `InvalidSeed` | the seed is not an integer |
| `opponent` | `MemberUnloadable`, `CheckpointRecordMissing`, `RuleMismatch`, `UtilityMismatch` | the drawn version carries no `path`, its container records no seed or encoding name, or its policy contradicts the record's `rule` or `utility` — `scheduler.md` §5–§6's classes |

Each message follows `errors.md` §3's grammar and is raised before anything is built; `errors.md` §4 has the strings.

## 9. What is deliberately free

- the `Pool`'s storage (a class, a `NamedTuple`, a dataclass) and its repr: only §1's four facts and their
  immutability are contract; whether `members` reads back as a tuple or a list, and whether a record is copied deeply or
  shallowly — a caller compares values;
- the order of the three baselines within the first three positions is `agents.baselines()`'s; that they come first is
  this design's (§2 step 5), and that they are never inside a family is `families.md` §2's.
