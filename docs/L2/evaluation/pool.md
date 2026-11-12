# evaluation — the pool at the surface

- **Layer:** L2 · **Module:** `evaluation` · **Unit:** phase1 · **Rev:** 9 · **Date:** 2026-11-10
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Owner of this file:** the four pool entry points of `e2e-surface.md` §3.4 — `build_pool`,
  `pool_members`, `offer` and `opponent`: each one's arguments, its returned record, its refusals and its
  determinism, and the **families** a heterogeneous window is grouped into (D-16, ASM-18, ASM-26, ASM-27)
- **Rev 3–4:** D-19's rule and D-20's utility reach the pool — a member declares `rule` and `utility`, a window is grouped into families
  that evict fair-share, the id digests each version's rule and utility, and the read-back states the `rules` and `utilities` it holds
  (§1–§5, `rules.md` §2–§3, `utilities.md` §5–§8)
- **Rev 5–6:** a version declaration naming no `utility` is **refused by name**, never read as the catalogue's first — the declared
  default speaks for a variant entry and a learner spec only, while a bare §7 record handed to `match`/`_side` is read as silence (§1,
  §3); and D-21 adds the **optional** `baselines` key, a name outside the catalogue being `UnknownBaseline`, a declared folder joining
  pinned after the three and in the catalogue's order, with `offer` reading its own baselines back (§1, §3, ASM-32)
- **Rev 7–8:** D-29's second shape makes `game` the declaration's optional key and the record's required one — another shape's member
  refused naming both, an unknown name `UnknownShape`, the id still digesting the membership alone; and D-33 adds `opponent`'s
  **optional draw count** and builds every baseline the pool pins and draws for **the pool's own shape** (§1, §4, `seats.md` §2, §4, D-33)
- **Rev 9:** D-43's third catalogue at the pool — a version member's `counterfactual` is a **conditional** key, read where the record declares one and refused by name where the catalogue lacks it, the read-back stating the `counterfactuals` set its members declare and no such key when every one is `none`, the id digesting it only then (`docs/L3/evaluation/pool.md` §2, §4–§5, §8, `counterfactual.md` §6, D-43)
- **Read with:** `surface.md` §1–§2 (the shared rules and the member at this edge), `surface.md` §10 and
  §12 (`matrix`, `policy_from`), `seats.md` §2 and §4 (the counted draw and the pool's own shape), `rules.md` §2–§3 (the rule and the
  fair-share window), `docs/L3/evaluation/utility.md` (the utility rule at this edge) and `docs/L1/utilities.md` §5–§7

These four sections were `surface.md` §5–§8 until D-19 added the rule to all four and D-20 its utility; they moved
here, one owner per document, and `surface.md` §5–§8 keeps a redirect naming this file (`surface.md` §1, D-12).

## 1. `build_pool` — one pool from one declaration (`general` row)

- **Signature:** `build_pool(declaration)`.
- **Arguments:** `records.md` §8's declaration — `members` (the versions, by id, lineage, **rule** and **utility**), `m` (the
  bound) and `frozen` (whether it may change while it is used), all three **required** (`records.md` §8, `records.md` §7,
  D-20), plus one **optional** key: `baselines`, a sequence of the catalogue baseline names the configuration admits beyond
  the pinned three — D-21's folders join by declaration and never silently, and absent, `None` or empty means the pinned
  three alone (ASM-32, D-21, `league()`'s `catalogue`). A version member's `rule` and `utility` are both **required of the
  member record**, and one that names none is refused by name and never read as a declared default: that default speaks for a variant entry and a learner spec, never for a pool member (`utilities.md` §5, `records.md` §7) — while its `counterfactual` is the **conditional** key of §7, read where the record declares one, a name the third catalogue lacks refused naming the member, the name and the catalogue, and no key gained for a member under `none` (`counterfactual.md` §6, D-43).
- **The shape:** the declaration's fourth optional key is `game` — the shape the pool is on, absent meaning the default
  (`records.md` §8, `shapes.md` §3, D-29). A version member carries `game` itself, **required of a non-default member and
  absent for a default-shape one**, and a member of another shape is refused before the window is grouped; each baseline
  the pool pins must be one the catalogue can construct for that shape, and one it cannot is refused by name rather than
  silently held unplayed (`shapes.md` §3, §6).
- **Returns:** a pool — the opaque value `pool_members`, `offer` and `opponent` take (`surface.md` §1). It
  holds the declared versions in **families** — one lineage chain each, its members under one rule **and one
  utility**, listed contiguously oldest to newest, the families in entry order — windowed to `m` by the **fair-share
  eviction** rule `offer` uses (`rules.md` §3, `utilities.md` §8, ASM-26, `docs/L1/league.md` §2). The baselines are pinned first: the
  three the catalogue flags as anchors, then each declared folder, both in `agents.baselines()`'s order and never the
  declaration's, so membership is 3–8 pinned baselines plus the window (`docs/L1/folders.md` §5, ASM-32, ASM-33). The pool carries the id `records.md` §8 requires, which digests each version's
  `id`, its `rule`, its `utility` and — **only when it is not `none`** — its `counterfactual`, and each baseline's bare id — so a declaration naming no folder keeps the membership,
  the order and the id it has today (`families.md` §4, `utilities.md` §7, ASM-27, D-20, D-21, `counterfactual.md` §6, D-43). The pool also carries the
  **one shape** it is on, which `pool_members` reports and every other entry point reads — never a second window per shape
  (`shapes.md` §3, §6, D-29).
- **Refusals:** a declaration missing one of §8's three keys, with that key named; a `game` the catalogue does not carry,
  naming it and the declared names (`UnknownShape`, `shapes.md` §2, D-29); a member whose `game`, or a pinned baseline whose
  catalogue construction, belongs to **another shape** than the declaration's, naming the member and both shapes
  (`ShapeMismatch`, `shapes.md` §3, §6); an `m` that is not a
  positive integer or that exceeds the league's M, with the bound named (D-16, `docs/L1/league.md` §2); a
  declared member missing its `id`, its `lineage`, its `rule` or its `utility`, naming the member and the key —
  a `utility`'s absence refused exactly as a `rule`'s is (`records.md` §7, §8, `utilities.md` §5); a `rule` or
  a `utility` the catalogue does not carry, or one that is empty or holds the digest's separator, naming the
  member, the name and the catalogue (`rules.md` §2, `utilities.md` §5, ASM-27); a `counterfactual` declared empty or holding the separator, and one the **third** catalogue does not carry, naming
  the member, the name and the catalogue (`MemberInvalid`, `counterfactual.md` §6, `records.md` §7, D-43); two
  declared members sharing one `id`, or a version declared under one of the names this pool pins,
  naming the member (`surface.md` §9, `records.md` §7, §8); a declared baseline **name the catalogue does not carry**, or a
  `baselines` value that is not a sequence of names — `UnknownBaseline` / `PoolDeclarationInvalid`, naming the name and the
  catalogue, and naming an anchor is accepted and adds nothing, the three being members whether declared or not (ASM-32, D-21); a declared `path` that names no readable file,
  naming the member (`protocol.md` §5); a member list whose lineage does not order — two members descending
  from one, or a chain that reaches no start — naming the member (`records.md` §7, `docs/L1/league.md` §2); an
  offer that would open the **(m+1)th family**, naming the count and the bound (`rules.md` §3, ASM-26); a family
  whose members declare two rules or two utilities, naming the member, the second value and the family's
  (`families.md` §1, `utilities.md` §8, D-20). A
  member declared without a `path` is admitted, and `matrix` and `opponent` refuse it when it is asked to be
  a policy (`surface.md` §10, §8, `records.md` §7).
- **Determinism:** one declaration yields one ordered member list and one id, and the id is a function of
  the ordered member lines — a baseline's id alone, a version's `id`, its `rule` and its `utility`, and its `counterfactual` only when it is not `none` — and of nothing
  else, so it changes when and only when the membership does, a **baselines-only pool keeps the id it had**, a pool of versions all trained under `none` keeps it too, and
  two pools of one membership under two objectives do not wear one id (`records.md` §8, ASM-2, ASM-27, `utilities.md`
  §7, D-20, `counterfactual.md` §6, D-43, `battery.md` §3 FAM-6, FAM-18). **The shape is not in the digest**: it is a required field of the record and
  not of the id, so two pools of one membership on two shapes wear one id and are never one table, and a declaration
  naming no folder and no shape keeps exactly the id it has today (`records.md` §8, ASM-27, `shapes.md` §3, §6).

## 2. `pool_members` — the pool read back (`general` row)

- **Signature:** `pool_members(pool)`.
- **Arguments:** a pool from `build_pool` or `offer`.
- **Returns:** `records.md` §8's pool record — `id`, `m`, `frozen`, **`game`**, `members`, `rules`, `utilities` and, when a version member is not `none`, `counterfactuals`: the
  **pinned** baselines first, in `agents.baselines()`'s order (the flagged three, then any folder the declaration
  named), each marked `pinned` with the `params` of `0` the
  catalogue declares, then the version window oldest to newest — each family contiguously, the families in
  entry order — each member the `records.md` §7 record its declaration carried; and `rules` and `utilities`, the
  **distinct** rules and utilities its version members declare, in the window's order, which are the two populations a
  table over it measured. `counterfactuals` is the third of them — the distinct counterfactual members those versions declare, in that order — and the key is **absent** when every one of them is `none`, so a baselines-only pool and a pool of versions all trained under `none` read back the record they always did (`records.md` §8, `counterfactual.md` §6, §9, D-43). `game` is **required** and names the one shape every member of the pool plays — absent from a
  declaration it is the default, and a record that names it is the fact a table and a report read (`records.md` §8, §10,
  `shapes.md` §3, D-29). R1's pool declares the **empty tuples**, because a baseline is a fixed rule and not a
  trained estimator or objective (`records.md` §8, ASM-16, `utilities.md` §7, D-19, D-20).
- **Refusals:** a value that is not a pool this module built (`e2e-surface.md` §2).
- **Determinism:** one pool reads back one record, and a frozen pool's read-back does not change while it
  is used — which is how a pair's parity is read (`records.md` §8, ASM-16).

## 3. `offer` — advance a pool by one version (`general` row)

- **Signature:** `offer(pool, version)`.
- **Arguments:** an unfrozen pool, and one version as a `records.md` §7 record — its `rule`, its `utility`, its `counterfactual` when
  it declares one and, for a member of a non-default shape, its `game` included, each required of the record as §7 declares it and none read as a declared default
  (`records.md` §7, §8, `utilities.md` §5, `shapes.md` §3, `counterfactual.md` §6, D-43).
- **Returns:** the pool advanced: the version extends **one family** and joins that family's newest end,
  every baseline stays exactly where it was — the pool reads its own pinned members back, so a declared folder
  rolls with the window untouched — and the id is recomputed (`docs/L1/league.md` §2, ASM-18, ASM-32, `rules.md` §3, D-21). A
  full window evicts **fair-share** — the oldest member of the family that holds the most — so no family is
  emptied while another holds two or more, and a window holding one family rolls as it always did
  (`rules.md` §3, ASM-26). A lineage that is **no member's `id`** opens a new family, which is how a second
  arm's first snapshot — naming the rung start its sibling's names — joins the window (`rules.md` §3). The
  argument pool is unchanged, so a caller may keep it.
- **Refusals:** a frozen pool, naming the frozen flag (`records.md` §8, ASM-16); a value that is not a
  pool; a version missing its `id`, its `lineage`, its `rule` or its `utility`, naming which — the absent
  `utility` refused by name as the absent `rule` is, because the pool is the only witness of what its member was
  trained under (`records.md` §7, `utilities.md` §5); a `rule` or a `utility` the catalogue does not carry or that
  holds the digest's separator, naming the member and the name
  (`utilities.md` §5); a `counterfactual` the third catalogue does not carry, declared empty or holding the separator, naming the version, the name and the catalogue — and a version declaring none admitted and gaining no key (`counterfactual.md` §6, D-43); a version already a member, naming it; a version whose `lineage` names a member that is
  **not its family's newest**, naming the lineage and that family's newest, because the chain would fork —
  while a lineage no member carries opens a **new family** (`docs/L1/league.md` §2, ASM-26); a version whose
  `rule` or `utility` differs from its family's, naming the member and both values (`utilities.md` §8, ASM-26); an
  offer that would open the **(m+1)th family**, naming the count and the bound (`rules.md` §3, ASM-26); a version whose
  `game` — or whose absent `game` read as the default — is not the pool's, naming the member and both shapes, because a
  pool is one shape's and no window mixes two (`ShapeMismatch`, `shapes.md` §3, §6, D-29); and a version naming a shape
  the catalogue does not carry, `UnknownShape`, refused naming it and the declared names (`shapes.md` §2).
- **Determinism:** one pool and one version give one membership and one id, and offering plays no hand and
  moves no stream (ASM-2, `battery.md` §3 FAM-6).

## 4. `opponent` — the training loop's draw (`general` row)

- **Signature:** `opponent(pool, seed, count=None)` — the count is optional and its absence is today's call (`seats.md` §2).
- **Arguments:** a pool, an integer seed, and — optionally — the **draw count**: a positive integer of distinct members, or none.
- **Returns:** **without a count**, one policy in the sense of `surface.md` §2, drawn from the pool's ordered membership by the
  seed: a baseline is `agents.build_baseline(name, seed, pool.game)`, and a version is `policy_from` of its checkpoint beside its
  member record (`docs/L1/league.md` §3, D-16, `module-map.md` §2). A drawn version's policy carries the rule, the utility and the
  **shape** its container records, and the record's own `rule`, `utility` and `game` are held to them (`rules.md` §6, `utilities.md`
  §6, `shapes.md` §3, `surface.md` §12); a drawn baseline is built for the **pool's** shape, so a six-seat pool's `fold-large-bet`
  reads 100 and its `oracle` is asked a six-way question (`seats.md` §4, `docs/L1/seats.md` §4, §6, ASM-31, D-33). **With a count**,
  a tuple of that many policies: the members at the draw's positions, **distinct**, drawn without replacement and in the draw's
  order, so a six-seat hand never seats one member twice, the first being the member the uncounted draw names
  (`seats.md` §2, `docs/L1/seats.md` §4, ASM-43).
- **Refusals:** a value that is not a pool; a seed that is not an integer (ASM-2); a count that is not a positive integer, naming it
  (`InvalidDrawCount`); a count larger than the membership, naming **both counts** (`DrawExceedsMembership`), because a substitute
  seat would be an opponent the membership does not carry (`records.md` §8, `seats.md` §2, ASM-43); a pool whose drawn member carries
  no `path`, naming the member, because a version that cannot be loaded cannot be an opponent (`records.md` §7, `protocol.md` §5); a
  drawn member record whose declared `rule`, `utility` or `game` contradicts what its checkpoint records, naming the member and both
  values (`utility.md` §4, `shapes.md` §3, D-19, D-20, D-29).
- **Determinism:** one pool and one seed draw one opponent, and the draw is the seed reduced modulo the membership's size, so a
  spread of seeds samples the whole pool and not one fixed policy (ASM-2, FAM-7); a counted draw is a function of the seed and the
  pool's own ordered membership, two calls at one seed agreeing on the same members in the same order (`seats.md` §2, ASM-43); the
  drawn policy answers one decision one way, because only the deal uses the global stream (ASM-2).
