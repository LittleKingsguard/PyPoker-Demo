# evaluation — the bounded pool

- **Owner:** the pool — the `Pool` value, `build_pool`, `pool_members`, `offer` and the draw `opponent` makes:
  the declaration, the **lineage order**, the window, the **id digest**, the frozen flag, the read-back, the
  eviction rule and every refusal (`surface.md` §5–§8, `league.md` §1–§2)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `declarations.md` §4, `scheduler.md` §5, `matrix.md` §1, `errors.md` §2–§4

## 1. The value

A pool is one ordered member list plus its bound, its frozen flag and its id — both the opposition the training
loop samples and a table's rows and columns (`league.md` §1, D-16). It is **opaque**: a caller only passes it
back to `pool_members`, `offer`, `opponent` and `matrix` (`surface.md` §1). `src/evaluation/pool.py`:

    class Pool:                       # immutable; no caller reads it, no record exposes it
        id:      str                  # §4's digest
        m:       int                  # the bound this pool holds to, 1 … league()["m"]
        frozen:  bool                 # records.md §8's required flag
        members: tuple                # §5's ordered records, the three baselines first

`offer` returns a **new** `Pool` and leaves its argument unchanged, so a caller may keep an earlier pool; nothing here caches, registers or mutates (`surface.md` §7).

## 2. From a declaration to a membership

`build_pool(declaration)` reads exactly three keys — `members`, `m` and `frozen` — and every one is
**required** (`records.md` §8, `surface.md` §5):

1. `members` is a sequence of member records, possibly empty: R1's pool is the three baselines alone (`league.md` §2), and each record must carry an `id` and a `lineage`, both non-empty `str` (`records.md` §7). An `id` that **is one of the three pinned baselines' names** is refused, naming the member: the three are pinned in every pool, so such a version would name one member twice (`surface.md` §5, `errors.md` §2, §4).
2. `m` is a positive integer no larger than `league()["m"]`: a declaration may be **tighter** than M and never
   wider (`league.md` §2, D-16). A `bool` is refused — a flag is not a bound.
3. `frozen` is a boolean flag (`bool` or the NumPy scalar `bool_`). It is stored, not interpreted: `offer`
   refuses a frozen pool and `matrix` refuses an unfrozen one (`surface.md` §7, §10).
4. The versions are ordered by §3 and **windowed to their last `m`**: a declaration richer than the bound is
   windowed, never refused (`league.md` §2, ASM-18).
5. The three baselines are added **first**, in `agents.baselines()`'s order, each as `{"id": <name>, "baseline": True, "pinned": True, "params": 0}` — a baseline's id is its name (D-16).
6. The id is computed from the ordered ids (§4) and the pool returned.

A member's other keys — `path`, `rung`, `variant`, `seed`, `step`, `samples` — are **carried, not required**: only `id`
and `lineage` are refused when absent, because only those two declare a version and order the window (`surface.md` §5). A
member declared **without** `path` is admitted, and `matrix` and `opponent` refuse it when it is asked to be a policy.

## 3. The lineage order — one chain per link

A version's `lineage` is the id of the version it descends from, or its rung's own start label for the first
(`records.md` §7, ASM-18). `_lineage_order(members)` therefore:

1. indexes the declaration by `id`; two records carrying one id are refused (`MemberDuplicate`);
2. indexes it by `lineage`; **two members descending from one** are refused (`LineageConflict`), naming both —
   the window would have two successors for one link and so no order (`surface.md` §5);
3. calls a member whose `lineage` is not a declared `id` a **start** — `"R3/start"`, a rung label such as
   `"R6-residual"`, or any id the declaration does not hold;
4. walks each start by following `lineage == id`; the walk's members, oldest first, are one **chain**;
5. refuses a chain that reaches no start (`LineageCycle`, naming a member on it): a walk that revisits a member
   is a cycle, and a declared member no walk visits sits on one (`records.md` §7, `surface.md` §5);
6. orders the chains by **the position of their start in the declaration's `members` sequence** and concatenates
   them, each chain oldest to newest. One chain is the common case — a rung inherits one lineage — and then this
   step does nothing; a declaration holding two (R4's two arms, say) is taken in the order it lists them.

The result is the ordered version list, **oldest first**, which §5 reads back and §6 rolls.

## 4. The id digest

The id is a function of the **ordered member ids and of nothing else**, so it changes when and only when the
membership does, and two arms of a pair prove they held one pool by comparing it (`records.md` §8, ASM-16):

    payload = "\n".join(ids).encode("utf-8")          # ids: §5's order, baselines first, then versions
    id      = "pool-" + hashlib.sha256(payload).hexdigest()[:16]

`ids` are the member ids exactly as their records spell them, joined by a single `"\n"` with no trailing
separator; the digest is SHA-256, lowercase hex, truncated to its first **16** characters, prefixed `pool-`. An
id that is empty or carries a `"\n"` is refused at `build_pool` and at `offer` (`MemberInvalid`), because a
separator inside an id would make two memberships digest alike.

Excluded from the payload, deliberately: `m`, `frozen` and every other member field — a corrected `seed` or `step` does not rename the pool, and neither does a re-declared bound (`surface.md` §5's "and of nothing else"). The id is a plain `str`, it is the pool record's first key, and it is what a run record and a matrix are compared by (`records.md` §8, §12).

## 5. `pool_members` — the read-back

`pool_members(pool)` returns `records.md` §8's pool record, freshly built on each call so a caller that edits it
changes nothing:

    {"id": <§4's id>, "m": <the bound>, "frozen": <the flag>, "members": (<the ordered records>,)}

`members` is §1's tuple: the three baselines first, then the window **oldest to newest**. Each baseline is its
four-key record of §2 step 5; each version is the `records.md` §7 record the declaration carried, its own keys
and values untouched. A frozen pool's read-back does not change while it is used, which is how a pair's parity
is read (`surface.md` §6).

## 6. `offer` — advance a pool by one version

`offer(pool, version)` returns a new pool whose window has one more version at its head (`surface.md` §7):

1. the argument must be a `Pool` (`InvalidPool`) and must be **unfrozen** (`PoolFrozen`, naming the flag);
2. the version must carry `id` and `lineage` (§2 item 1's rule, `MemberInvalid`) and must not already be a
   member (`MemberDuplicate`, naming it);
3. when the window holds a version, the offered version's `lineage` must be the **newest** version member's `id`
   (`LineageNotExtended`, naming the lineage given and the id it had to extend) — the window has one order and
   an offer extends it (`league.md` §2). A window holding no version accepts any version and begins its order;
4. the version joins at the head, and **when the window already holds `m` versions the oldest one leaves and
   nothing else does**: the baselines are pinned and never evicted (`surface.md` §7, ASM-16);
5. the id is recomputed from the new ordered ids (§4) and the new pool returned; the argument is unchanged.

`offer` plays no hand, moves no stream and re-reads no checkpoint: it is a declaration operation on a named
object, not a side effect of training (`league.md` §1, ASM-2).

## 7. `opponent` — the training loop's draw

`opponent(pool, seed)` draws exactly one member from the pool's ordered membership and returns it as a policy
(`surface.md` §8, D-16):

    index  = seeds._draw_index(seed, len(pool.members))       # seed % the size; scheduler.md §3
    member = pool.members[index]
    policy = agents.build_baseline(member["id"], seed)        if member is a baseline
             policy._member_policy(member)                     otherwise (scheduler.md §5)

A baseline is drawn at the caller's seed and a version at the seed its checkpoint records, read from the container
(`scheduler.md` §5.1, `records.md` §7), so a drawn opponent is one policy that answers one decision one way
(`agents/surface.md` §10, ASM-2). It refuses a seed that is not an integer (`InvalidSeed`), a value that is not a pool
(`InvalidPool`), and a drawn version carrying no `path` (`MemberUnloadable`, naming the member) — a version that cannot be
loaded cannot be an opponent (`records.md` §7, `protocol.md` §5). Nothing else: the draw is the seed's position in the
ordering (`league.md` §3, FAM-7.9).

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
| `build_pool`, `offer` | `MemberInvalid` | a member is not a mapping, or its `id` or `lineage` is missing, empty or holds a newline |
| `build_pool` | `MemberUnloadable` | a declared `path` names no readable file — the member is named (`protocol.md` §5) |
| `build_pool`, `offer` | `MemberDuplicate` | two records carry one id, a declared id is one of the three baselines' names (`surface.md` §5), or an offered version is already a member |
| `build_pool` | `LineageConflict` | two members descend from one (`surface.md` §5) |
| `build_pool` | `LineageCycle` | a chain reaches no start (`surface.md` §5) |
| `pool_members`, `offer`, `opponent` | `InvalidPool` | the argument is not a pool this module built (`surface.md` §6) |
| `offer` | `PoolFrozen` | the pool is frozen and its membership does not change while it is used |
| `offer` | `LineageNotExtended` | the version's lineage is not the window's newest version member |
| `opponent` | `InvalidSeed` | the seed is not an integer |
| `opponent` | `MemberUnloadable`, `CheckpointRecordMissing` | the drawn version carries no `path`, or its container records no seed or encoding name — `scheduler.md` §6's classes |

Each message follows `errors.md` §3's grammar and is raised before anything is built; `errors.md` §4 has the strings.

## 9. What is deliberately free

- the `Pool`'s storage (a class, a `NamedTuple`, a dataclass) and its repr: only §1's four facts and their immutability are contract; whether `members` reads back as a tuple or a list, and whether a record is copied deeply or shallowly — a caller compares values;
- the order of the three baselines within the first three positions is `agents.baselines()`'s; that they come first is this design's (§2 step 5).
