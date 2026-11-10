# evaluation — the bounded pool

- **Owner:** the pool — the `Pool` value and its one shape (§1), the declaration (§2), the read-back (§5), the draw
  `opponent` makes (§7), every refusal (§8) and what is free (§9); the **lineage order**, the **id digest** and
  `offer`'s eviction are `families.md`'s (§3, §4, §6), the utility a member declares is `utility.md`'s and the
  shape it declares is `shape.md`'s (`surface.md` §5–§8, `league.md` §1–§2, `shape.md` §2–§4)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Rev 6:** D-29's second shape — a `Pool` carries the one shape it is on, the declaration's `game` key and each member's `game` are held to it, each pinned baseline is probed once, and the read-back's `game` is required (`shape.md` §2–§4)
- **Read with:** `shape.md` §1–§4, `families.md` §1–§6, `utility.md` §1–§4, `declarations.md` §4, `scheduler.md` §5,
  `matrix.md` §1, `errors.md` §2–§4

D-19 gave the window more than one estimator, so the three sections that followed from it — the lineage order, the id digest and `offer`'s eviction — moved to `families.md` under their own owner; their **numbers stay here as redirects**, because other layers cite `pool.md` §3, §4 and §6 by number (`README.md` §2, D-12, ASM-26, ASM-27).

## 1. The value

A pool is one ordered member list plus its bound, its frozen flag, its id and its **shape** — both the opposition the training loop samples and a table's rows and columns, on **one** shape (`league.md` §1, `shape.md` §4, D-16). It is **opaque**: a caller only passes it back to `pool_members`, `offer`, `opponent` and `matrix` (`surface.md` §1):

    class Pool:                       # immutable; no caller reads it, no record exposes it
        id:      str                  # families.md §4's digest
        m:       int                  # the bound this pool holds to, 1 … league()["m"]
        frozen:  bool                 # records.md §8's required flag
        game:    str                  # the one shape every member of it plays (shape.md §2, §4)
        members: tuple                # §5's ordered records, the families contiguous (families.md §2)

`offer` returns a **new** `Pool` and leaves its argument unchanged, so a caller may keep an earlier pool; nothing here
caches, registers or mutates (`surface.md` §7), and no pool is ever a window of two shapes (`shape.md` §4).

## 2. From a declaration to a membership

`build_pool(declaration)` reads exactly three keys — `members`, `m` and `frozen` — and every one is **required**, plus two **optional** ones: `baselines`, the catalogue baseline names the configuration admits beyond the pinned three, and `game`, the shape the pool is on (`records.md` §8, `surface.md` §5, ASM-32, D-21, `shape.md` §2):

1. `game` is read **first**, before a member is looked at: absent it is `DEFAULT_SHAPE` and a name the restated
   catalogue does not carry is `UnknownShape`, naming the entry point, the field, the name and `SHAPE_NAMES` — never
   mapped onto the default (`shape.md` §2–§3). The pool's shape is then the fact every following step is checked against.
2. `members` is a sequence of member records, possibly empty: R1's pool is the three anchor baselines alone (`league.md` §2), and each record must carry an `id`, a `lineage`, a `rule` and a `utility`, all four non-empty `str` and required by the shape as `utility.md` §2 states (`records.md` §7, §8, `utility.md` §1–§2). An `id` that **is one of the pinned baselines' names** — the three anchors plus any folder this declaration admits — is refused, naming the member: the baselines are pinned in every pool, so such a version would name one member twice (`surface.md` §5, `errors.md` §4, ASM-32, D-21). A `rule` the catalogue does not carry is `UnknownRule`, naming the member, the name and the catalogue — never mapped onto the declared default (`families.md` §6, D-19); a `utility` the catalogue does not carry is `UnknownUtility` on the same terms, and a member naming **none** is refused as a missing required key — `MemberInvalid`, naming the member and the key — never read as the catalogue's first member, because the pool is the only witness of what its member was trained under (`utility.md` §2, `records.md` §7, ASM-27, D-20). A member's `game` is `records.md` §7's key — **required of a non-default member, absent for a default-shape one** — and it is held to step 1's: a member whose shape, read with an absent `game` as the default, is not the pool's is `ShapeMismatch`, naming the member and both shapes, and a member naming an uncatalogued shape is `UnknownShape` (`records.md` §7, `shape.md` §2–§3, D-29).
3. `m` is a positive integer no larger than `league()["m"]`: a declaration may be **tighter** than M and never wider (`league.md` §2, D-16). A `bool` is refused — a flag is not a bound.
4. `frozen` is a boolean flag (`bool` or the NumPy scalar `bool_`). It is stored, not interpreted: `offer` refuses a frozen pool and `matrix` refuses an unfrozen one (`surface.md` §7, §10).
5. The versions are grouped into **families** and ordered, then **windowed to `m`** by the fair-share eviction rule `offer` uses: a declaration richer than the bound is windowed, never refused, unless it holds more than `m` families (`families.md` §2–§3, `league.md` §2, ASM-18, ASM-26).
6. The **pinned** baselines are added **first**, in `agents.baselines()`'s order: the catalogue's `anchor: True` three, then each folding baseline the declaration's `baselines` names, both in the catalogue's order and never the declaration's, each as `{"id": <name>, "baseline": True, "pinned": True, "params": 0, "game": None}` — a baseline's id is its name, and its `game` is `None` because a baseline carries no shape (§2, §7, D-16, ASM-32, D-21, `shape.md` §4); naming an anchor is accepted and adds nothing, and a name outside the catalogue is `UnknownBaseline`, naming it.
7. The id is computed from the ordered member lines (`families.md` §4) and the pool returned, carrying step 1's shape.

**The baseline probe, and why its firing set is empty.** Each pinned baseline is probed **once** with `agents.build_baseline(name, PROBE_SEED)` — a **construction** only: no hand is played, no file is read and no stream moves, which is what keeps `build_pool`'s "plays nothing, moves no stream" true (ASM-2). A baseline the catalogue cannot construct is refused naming the member and both shapes rather than silently held unplayable. **Under today's catalogue the probe's firing set is empty**, and honestly so: `agents` declares **one** catalogue of six for both declared shapes and `build_baseline(name, seed)` takes no shape, so every one of the six constructs and every one of them plays both shapes (`shape.md` §4, README §6) — the probe is the guard for the day a catalogue carries a shape-dependent baseline. Rejected: probing by **playing a hand** at the pool's shape, the only other way to learn whether a baseline can play it — that seeds the global `random` stream and breaks the one promise `build_pool` makes (ASM-2, `surface.md` §1).

A member's other keys — `path`, `rung`, `variant`, `seed`, `step`, `samples` — are **carried, not required**; `id`,
`lineage` and `rule` are the three that are refused when absent, because the first two declare a version and order the
window and the third says which population it belongs to (`records.md` §7, D-19, `surface.md` §5); `utility` is the
fourth the shape requires and the one this edge **refuses by name** when it is absent too (`utility.md` §2, D-20). A member
declared **without** `path` is admitted, and `matrix` and `opponent` refuse it when it is asked to be a policy (`pool.md`
§8).

## 3. The lineage order — the families' order: `families.md` §1–§2

The order that stood here is now the **families** — one lineage chain each, every member under one rule, the chains listed contiguously oldest to newest, the families in entry order — and §2 step 5 applies it (`families.md` §1–§2, ASM-26).

## 4. The id digest — `families.md` §4

The payload is one line per member — a baseline's `id` alone, a version's `id`, `"\x1f"`, its `rule`, `"\x1f"` and its `utility` — joined by `"\n"`, and the id is `"pool-" + sha256(payload).hexdigest()[:16]`. `families.md` §4 owns the digest, why the rule and the utility are inside it, why the **shape is not** — two pools of one membership on two shapes wear one id (`ASM-27`, `D-20`, `shape.md` §4, `records.md` §8).

## 5. `pool_members` — the read-back

`pool_members(pool)` returns `records.md` §8's pool record, freshly built on each call so a caller that edits it
changes nothing:

    {"id": <families.md §4's id>, "m": <the bound>, "frozen": <the flag>, "game": <the pool's shape>,
     "members": (<the ordered records>,), "rules": (<the distinct rules the versions declare>,),
     "utilities": (<the distinct utilities the versions declare>,)}

`game` is **required** and names the one shape every member of the pool plays — an absent declaration key reads as the
default, and a record that names it is the fact a table and a report read (`records.md` §8, §10, `shape.md` §2, §4).
`members` is §1's tuple: the pinned baselines first — the flagged three, then any declared folder — then the window **oldest to newest**, each family contiguously
(`families.md` §2, ASM-32). Each baseline is its five-key record of §2 step 6; each version is the `records.md` §7 record the
declaration carried — its `rule`, its `utility` and its `game` the declaration's own, refused by name when a required one is absent, and
nothing filled in — with its own keys and values otherwise untouched. `rules` is the **distinct** rules its version members declare, in the
window's order, and `utilities` their counterpart on the same terms; both are the **empty tuple** for R1's pool, because
a baseline is a fixed policy and not a trained member, so it contributes neither, and the pair is the two populations a
table over this pool measured (`records.md` §8, `families.md` §2, `utility.md` §3, D-19, D-20, ASM-16, D-21). A frozen pool's
read-back does not change while it is used, which is how a pair's parity is read (`surface.md` §6).

## 6. `offer`'s rolling — `families.md` §3, §5

`offer(pool, version)` returns a new pool in which the version extends **exactly one family** — the one whose newest
member it names, or a new family when its `lineage` names no member — and a full window evicts **fair-share**, the
oldest member of the family that holds the most, so no family is emptied while another holds two or more
(`families.md` §3, §5, ASM-26), and the returned pool keeps the **pool's** shape (`shape.md` §4). `families.md` §5 owns
the four outcomes and §6 their refusals. What this section keeps is §2's guarantee at the pool's surface: the baselines are
pinned and never evicted, the argument pool is unchanged, the version's own `rule` and `utility` are required and checked
exactly as §2 step 2 checks a declared member's (`league.md` §2, `surface.md` §7, `utility.md` §4), and a version whose `game` — or
whose absent `game`, read as the default — is **not the pool's** is `ShapeMismatch`, naming the member and both shapes,
because a pool is one shape's and no window mixes two (`shape.md` §3, §4).

## 7. `opponent` — the training loop's draw

`opponent(pool, seed)` draws exactly one member from the pool's ordered membership and returns it as a policy
(`surface.md` §8, D-16):

    index  = seeds._draw_index(seed, len(pool.members))       # seed % the size; scheduler.md §3
    member = pool.members[index]
    policy = agents.build_baseline(member["id"], seed)        if member is a baseline
             policy._member_policy(member)                     otherwise (scheduler.md §5)

A baseline is drawn at the caller's seed and a version at the seed its checkpoint records, read from the container
(`scheduler.md` §5.1, `records.md` §7), so a drawn opponent is one policy that answers one decision one way
(`agents/surface.md` §10, ASM-2). A drawn version's policy carries the **shape its container records**, and the
record's own `game` is held to it: a disagreement is `ShapeMismatch` naming the member and both shapes, after the load
and before a hand — and a `rule` or a `utility` disagreement is `RuleMismatch` or `UtilityMismatch` on the same terms
(`scheduler.md` §5–§6, `shape.md` §3). A **baseline** is shape-silent and plays whatever shape the hands are dealt on, so
a pool on the second shape draws opponents for that shape and none for the default (`shape.md` §4). It refuses a seed
that is not an integer (`InvalidSeed`), a value that is not a pool (`InvalidPool`), and a drawn version carrying no
`path` (`MemberUnloadable`, naming the member) — a version that cannot be loaded cannot be an opponent (`records.md` §7,
`protocol.md` §5). Nothing else: the draw is the seed's position in the ordering (`league.md` §3, FAM-7.9).

**What `seed % n` promises.** One seed draws one member every time, and it does **not** make distinct seeds distinct
members — only `n` residues exist, so two seeds congruent modulo `n` draw one member. It promises a spread: `n`
consecutive seeds visit each member once, so sampling many seeds samples the whole pool — the satisfiable reading
`surface.md` §8 asserts (FAM-7.9).

## 8. Refusals

| Where | Class | The rule it names |
|---|---|---|
| `build_pool` | `PoolDeclarationInvalid` | the argument is not a mapping, or is missing `members`, `m` or `frozen`, or `frozen` is not a boolean — the key is named |
| `build_pool` | `PoolBoundInvalid` | `m` is not a positive integer, is a `bool`, or exceeds `league()["m"]` — the bound is named |
| `build_pool`, `offer` | `MemberInvalid` | a member is not a mapping, or its `id`, `lineage`, `rule` or `utility` is missing, empty, or holds a newline or the digest's separator — the absent key named, and the `utility`'s absence refused like the other three (`utility.md` §2, `families.md` §6) |
| `build_pool`, `offer` | `UnknownRule`, `UnknownUtility` | the `rule` or the `utility` is not one its catalogue carries — the member, the name and the catalogue (`families.md` §6, `utility.md` §4, D-19, D-20) |
| `build_pool`, `offer`, `opponent` | `UnknownShape` | a `game` the restated catalogue does not carry — the declaration's, a member's, an offered version's or a drawn record's — naming the field, the name and `SHAPE_NAMES`, never the default (`shape.md` §2–§3) |
| `build_pool`, `offer`, `opponent` | `ShapeMismatch` | two declarations of one shape disagree — a member's or an offered version's `game` against the pool's, or a drawn record's against its container's — naming the member and both shapes (`shape.md` §3, §4) |
| `build_pool` | `UnknownBaseline` | the declaration's `baselines` names a baseline the catalogue does not carry — the name and the catalogue, and never a silent drop (`records.md` §8, ASM-32, D-21); a `baselines` value that is not a sequence of names is `PoolDeclarationInvalid` |
| `build_pool` | `MemberUnloadable` | a declared `path` names no readable file — the member is named (`protocol.md` §5) |
| `build_pool`, `offer` | `MemberDuplicate` | two records carry one id, or a declared id is one of the names this pool pins, or an offered version is already a member |
| `build_pool` | `LineageConflict`, `LineageCycle` | two members descend from one, or a chain reaches no start — §3's order has none (`families.md` §1) |
| `build_pool` | `RuleMismatch`, `UtilityMismatch` | a family's members declare two rules or two utilities — the member and both values (`families.md` §1, §6) |
| `build_pool`, `offer` | `FamilyBoundExceeded` | the families asked for exceed the bound `m` — the count and the bound (`families.md` §3) |
| `pool_members`, `offer`, `opponent` | `InvalidPool` | the argument is not a pool this module built (`surface.md` §6) |
| `offer` | `PoolFrozen` | the pool is frozen and its membership does not change while it is used |
| `offer` | `LineageNotExtended` | the lineage is not its family's newest member (`families.md` §5) |
| `offer` | `RuleMismatch`, `UtilityMismatch` | the version's rule or utility differs from the family it extends — the version and both values (`families.md` §5) |
| `opponent` | `InvalidSeed` | the seed is not an integer |
| `opponent` | `MemberUnloadable`, `CheckpointRecordMissing`, `RuleMismatch`, `UtilityMismatch` | the drawn version carries no `path`, its container records no seed or no encoding name, or records either in a form this module does not read, or its policy contradicts the record's `rule`, `utility` or `game` — `scheduler.md` §5–§6's classes |

The order is §2's: the declaration's shape, then a member's `path`, `rule`, `utility` and `game`, then the families and the
window — so an uncatalogued shape is reported before a single member is windowed and no pool is built for a window that
will be refused. Each message follows `errors.md` §3's grammar and is raised before anything is built; `errors.md` §4 has
the strings.

## 9. What is deliberately free

- the `Pool`'s storage (a class, a `NamedTuple`, a dataclass) and its repr: only §1's five facts and their immutability are contract; whether `members` reads back as a tuple or a list, and whether a record is copied deeply or shallowly — a caller compares values;
- the order of the pinned baselines within their leading positions is `agents.baselines()`'s — the anchors first, then the declared folders — and that they carry `game: None` is §2 step 6's, while that they are never inside a family is `families.md` §2's;
- whether the probe of §2 is run once per declaration or once per pinned name, and whether its result is kept or discarded: only that it constructs and plays nothing (ASM-2).
