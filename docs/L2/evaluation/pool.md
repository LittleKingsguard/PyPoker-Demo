# evaluation — the pool at the surface

- **Layer:** L2 · **Module:** `evaluation` · **Unit:** phase1 · **Rev:** 6 · **Date:** 2026-11-09
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Owner of this file:** the four pool entry points of `e2e-surface.md` §3.4 — `build_pool`,
  `pool_members`, `offer` and `opponent`: each one's arguments, its returned record, its refusals and its
  determinism, and the **families** a heterogeneous window is grouped into (D-16, ASM-18, ASM-26, ASM-27)
- **Rev 3:** D-19's rule reaches the pool — a member declares `rule`, a window is grouped into families and
  evicts fair-share, the id digests each version's rule, and the read-back states the `rules` it holds
  (§2–§5, `rules.md` §2–§3)
- **Rev 4:** D-20's utility reaches all four — a member declares `utility` beside `rule`, a family declares one
  rule and one utility, the id digests both, and the read-back states the `utilities` it holds
  (§1–§5, `utilities.md` §5–§8)
- **Rev 5:** L1's "required means required" reaches this edge — a version declaration that names no `utility` is
  **refused by name** (`MemberInvalid`, the missing key), never read as the catalogue's first; the declared default
  speaks only for a variant entry and a learner spec, and only a bare §7 record handed to `match` or `_side` is
  still read as silence, the container being the witness there (§1, §3, `utilities.md` §5, `records.md` §7, D-20)
- **Rev 6:** D-21 reaches the declaration — an **optional** `baselines` key names the catalogue baselines a configuration
  admits beyond the pinned three, a name outside the catalogue is `UnknownBaseline`, a declared folder joins pinned
  **after** the three and in the catalogue's order, and `offer` reads its own baselines back so a window rolls and no
  baseline moves (§1, §3, `records.md` §8, ASM-32)
- **Read with:** `surface.md` §1–§2 (the shared rules and the member at this edge), `surface.md` §10 and
  §12 (`matrix`, `policy_from`), `rules.md` §2–§3 (the rule and the fair-share window), `docs/L3/evaluation/utility.md`
  (the utility rule at this edge) and `docs/L1/utilities.md` §5–§7

These four sections were `surface.md` §5–§8 until D-19 added the rule to all four and D-20 its utility; they moved
here, one owner per document, and `surface.md` §5–§8 keeps a redirect naming this file (`surface.md` §1, D-12).

## 1. `build_pool` — one pool from one declaration (`general` row)

- **Signature:** `build_pool(declaration)`.
- **Arguments:** `records.md` §8's declaration — `members` (the versions, by id, lineage, **rule** and
  **utility**), `m` (the bound) and `frozen` (whether it may change while it is used), all three **required**
  (`records.md` §8, `records.md` §7, D-20), plus one **optional** key: `baselines`, a sequence of the catalogue
  baseline names the configuration admits beyond the pinned three — D-21's folders join by declaration and never
  silently, and absent, `None` or empty means the pinned three alone (ASM-32, D-21, `league()`'s `catalogue`). A version member's `rule` and `utility` are both **required of the
  member record**, and one that names none is refused by name and never read as a declared default: the declared
  default speaks for a variant entry and a learner spec, never for a pool member (`utilities.md` §5, `records.md` §7).
- **Returns:** a pool — the opaque value `pool_members`, `offer` and `opponent` take (`surface.md` §1). It
  holds the declared versions in **families** — one lineage chain each, its members under one rule **and one
  utility**, listed contiguously oldest to newest, the families in entry order — windowed to `m` by the **fair-share
  eviction** rule `offer` uses (`rules.md` §3, `utilities.md` §8, ASM-26, `docs/L1/league.md` §2). The baselines are pinned first: the
  three the catalogue flags as anchors, then each declared folder, both in `agents.baselines()`'s order and never the
  declaration's, so membership is 3–8 pinned baselines plus the window (`docs/L1/folders.md` §5, ASM-32, ASM-33). The pool carries the id `records.md` §8 requires, which digests each version's
  `id`, its `rule` and its `utility` and each baseline's bare id — so a declaration naming no folder keeps the membership,
  the order and the id it has today (`families.md` §4, `utilities.md` §7, ASM-27, D-20, D-21).
- **Refusals:** a declaration missing one of §8's three keys, with that key named; an `m` that is not a
  positive integer or that exceeds the league's M, with the bound named (D-16, `docs/L1/league.md` §2); a
  declared member missing its `id`, its `lineage`, its `rule` or its `utility`, naming the member and the key —
  a `utility`'s absence refused exactly as a `rule`'s is (`records.md` §7, §8, `utilities.md` §5); a `rule` or
  a `utility` the catalogue does not carry, or one that is empty or holds the digest's separator, naming the
  member, the name and the catalogue (`rules.md` §2, `utilities.md` §5, ASM-27); two
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
  the ordered member lines — a baseline's id alone, a version's `id`, its `rule` and its `utility` — and of nothing
  else, so it changes when and only when the membership does, a **baselines-only pool keeps the id it had**, and
  two pools of one membership under two objectives do not wear one id (`records.md` §8, ASM-2, ASM-27, `utilities.md`
  §7, D-20, `battery.md` §3 FAM-6, FAM-18).

## 2. `pool_members` — the pool read back (`general` row)

- **Signature:** `pool_members(pool)`.
- **Arguments:** a pool from `build_pool` or `offer`.
- **Returns:** `records.md` §8's pool record — `id`, `m`, `frozen`, `members`, `rules` and `utilities`: the
  **pinned** baselines first, in `agents.baselines()`'s order (the flagged three, then any folder the declaration
  named), each marked `pinned` with the `params` of `0` the
  catalogue declares, then the version window oldest to newest — each family contiguously, the families in
  entry order — each member the `records.md` §7 record its declaration carried; and `rules` and `utilities`, the
  **distinct** rules and utilities its version members declare, in the window's order, which are the two populations a
  table over it measured. R1's pool declares the **empty tuples**, because a baseline is a fixed rule and not a
  trained estimator or objective (`records.md` §8, ASM-16, `utilities.md` §7, D-19, D-20).
- **Refusals:** a value that is not a pool this module built (`e2e-surface.md` §2).
- **Determinism:** one pool reads back one record, and a frozen pool's read-back does not change while it
  is used — which is how a pair's parity is read (`records.md` §8, ASM-16).

## 3. `offer` — advance a pool by one version (`general` row)

- **Signature:** `offer(pool, version)`.
- **Arguments:** an unfrozen pool, and one version as a `records.md` §7 record — its `rule` and its `utility`
  included, both required of the record and neither read as a declared default (`records.md` §7, `utilities.md` §5).
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
  (`utilities.md` §5); a version already a member, naming it; a version whose `lineage` names a member that is
  **not its family's newest**, naming the lineage and that family's newest, because the chain would fork —
  while a lineage no member carries opens a **new family** (`docs/L1/league.md` §2, ASM-26); a version whose
  `rule` or `utility` differs from its family's, naming the member and both values (`utilities.md` §8, ASM-26); an
  offer that would open the **(m+1)th family**, naming the count and the bound (`rules.md` §3, ASM-26).
- **Determinism:** one pool and one version give one membership and one id, and offering plays no hand and
  moves no stream (ASM-2, `battery.md` §3 FAM-6).

## 4. `opponent` — the training loop's draw (`general` row)

- **Signature:** `opponent(pool, seed)`.
- **Arguments:** a pool, and an integer seed.
- **Returns:** one policy in the sense of `surface.md` §2, drawn from the pool's ordered membership by the
  seed: a baseline is `agents.build_baseline(name, seed)`, and a version is `policy_from` of its checkpoint
  beside its member record (`docs/L1/league.md` §3, D-16, `module-map.md` §2). A drawn version's policy
  carries the rule and the utility its container records, and the record's own `rule` and `utility` are held to
  them (`rules.md` §6, `utilities.md` §6, `surface.md` §12).
- **Refusals:** a value that is not a pool; a seed that is not an integer (ASM-2); a pool whose drawn
  member carries no `path`, naming the member, because a version that cannot be loaded cannot be an
  opponent (`records.md` §7, `protocol.md` §5); a drawn member record whose declared `rule` or `utility`
  contradicts the one its checkpoint records, naming the member and both values (`utility.md` §4, D-19, D-20).
- **Determinism:** one pool and one seed draw one opponent, and the draw is the seed reduced modulo the
  membership's size, so a spread of seeds samples the whole pool and not one fixed policy (ASM-2, FAM-7);
  the drawn policy answers one decision one way, because only the deal uses the global stream (ASM-2).
