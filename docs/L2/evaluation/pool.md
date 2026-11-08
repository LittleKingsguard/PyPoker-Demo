# evaluation — the pool at the surface

- **Layer:** L2 · **Module:** `evaluation` · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-09
- **Owner of this file:** the four pool entry points of `e2e-surface.md` §3.4 — `build_pool`,
  `pool_members`, `offer` and `opponent`: each one's arguments, its returned record, its refusals and its
  determinism, and the **families** a heterogeneous window is grouped into (D-16, ASM-18, ASM-26, ASM-27)
- **Rev 3:** D-19's rule reaches the pool — a member declares `rule`, a window is grouped into families and
  evicts fair-share, the id digests each version's rule, and the read-back states the `rules` it holds
  (§2–§5, `rules.md` §2–§3)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `surface.md` §1–§2 (the shared rules and the member at this edge), `surface.md` §10 and
  §12 (`matrix`, `policy_from`), `rules.md` §2–§3 (the rule and the fair-share window)

These four sections were `surface.md` §5–§8 until D-19 added the rule to all four; they moved here, one
owner per document, and `surface.md` §5–§8 keeps a redirect naming this file (`surface.md` §1, D-12).

## 1. `build_pool` — one pool from one declaration (`general` row)

- **Signature:** `build_pool(declaration)`.
- **Arguments:** `records.md` §8's declaration — `members` (the versions, by id, lineage **and rule**),
  `m` (the bound) and `frozen` (whether it may change while it is used), all three **required**
  (`records.md` §8, `records.md` §7).
- **Returns:** a pool — the opaque value `pool_members`, `offer` and `opponent` take (`surface.md` §1). It
  holds the declared versions in **families** — one lineage chain each, its members under one rule, listed
  contiguously oldest to newest, the families in entry order — windowed to `m` by the **fair-share
  eviction** rule `offer` uses (`rules.md` §3, ASM-26, `docs/L1/league.md` §2). The three baselines are
  pinned first, and the pool carries the id `records.md` §8 requires, which digests each version's `id` and
  `rule` (`rules.md` §3, ASM-27).
- **Refusals:** a declaration missing one of §8's three keys, with that key named; an `m` that is not a
  positive integer or that exceeds the league's M, with the bound named (D-16, `docs/L1/league.md` §2); a
  declared member missing its `id`, its `lineage` or its `rule`, naming the member and the key
  (`records.md` §7, §8, `rules.md` §2); a `rule` the catalogue does not carry, or one that is empty or
  holds the digest's separator, naming the member, the name and the catalogue (`rules.md` §2, ASM-27); two
  declared members sharing one `id`, or a version declared under one of the three pinned baselines' names,
  naming the member (`surface.md` §9, `records.md` §7, §8); a declared `path` that names no readable file,
  naming the member (`protocol.md` §5); a member list whose lineage does not order — two members descending
  from one, or a chain that reaches no start — naming the member (`records.md` §7, `docs/L1/league.md` §2);
  a declaration holding more than `m` families, naming the count and the bound (`rules.md` §3, ASM-26). A
  member declared without a `path` is admitted, and `matrix` and `opponent` refuse it when it is asked to be
  a policy (`surface.md` §10, §8, `records.md` §7).
- **Determinism:** one declaration yields one ordered member list and one id, and the id is a function of
  the ordered member lines — a baseline's id alone, a version's `id` and its `rule` — and of nothing else,
  so it changes when and only when the membership does, and a **baselines-only pool keeps the id it had**
  (`records.md` §8, ASM-2, ASM-27, `battery.md` §3 FAM-6).

## 2. `pool_members` — the pool read back (`general` row)

- **Signature:** `pool_members(pool)`.
- **Arguments:** a pool from `build_pool` or `offer`.
- **Returns:** `records.md` §8's pool record — `id`, `m`, `frozen`, `members` and `rules`: the three
  baselines first, in `agents.baselines()`'s order, each marked `pinned` with the `params` of `0` the
  catalogue declares, then the version window oldest to newest — each family contiguously, the families in
  entry order — each member the `records.md` §7 record its declaration carried; and `rules`, the
  **distinct** rules its version members declare, in the window's order, which is the population a table
  over it measured. R1's pool declares the **empty tuple**, because a baseline is a fixed rule and not a
  trained estimator (`records.md` §8, ASM-16, `rules.md` §4, D-19).
- **Refusals:** a value that is not a pool this module built (`e2e-surface.md` §2).
- **Determinism:** one pool reads back one record, and a frozen pool's read-back does not change while it
  is used — which is how a pair's parity is read (`records.md` §8, ASM-16).

## 3. `offer` — advance a pool by one version (`general` row)

- **Signature:** `offer(pool, version)`.
- **Arguments:** an unfrozen pool, and one version as a `records.md` §7 record — its `rule` included.
- **Returns:** the pool advanced: the version extends **one family** and joins that family's newest end,
  the baselines are untouched, and the id is recomputed (`docs/L1/league.md` §2, ASM-18, `rules.md` §3). A
  full window evicts **fair-share** — the oldest member of the family that holds the most — so no family is
  emptied while another holds two or more, and a window holding one family rolls as it always did
  (`rules.md` §3, ASM-26). A lineage that is **no member's `id`** opens a new family, which is how a second
  arm's first snapshot — naming the rung start its sibling's names — joins the window (`rules.md` §3). The
  argument pool is unchanged, so a caller may keep it.
- **Refusals:** a frozen pool, naming the frozen flag (`records.md` §8, ASM-16); a value that is not a
  pool; a version missing its `id`, its `lineage` or its `rule`, naming which (`records.md` §7); a `rule`
  the catalogue does not carry or that holds the digest's separator, naming the member and the name
  (`rules.md` §2); a version already a member, naming it; a version whose `lineage` names a member that is
  **not its family's newest**, naming the lineage and that family's newest, because the chain would fork —
  while a lineage no member carries opens a **new family** (`docs/L1/league.md` §2, ASM-26); a version whose
  `rule` differs from the rule of the family it extends, naming the member and both values (`rules.md` §2,
  ASM-26); an offer that would open the **(m+1)th family**, naming the count and the bound (`rules.md` §3,
  ASM-26).
- **Determinism:** one pool and one version give one membership and one id, and offering plays no hand and
  moves no stream (ASM-2, `battery.md` §3 FAM-6).

## 4. `opponent` — the training loop's draw (`general` row)

- **Signature:** `opponent(pool, seed)`.
- **Arguments:** a pool, and an integer seed.
- **Returns:** one policy in the sense of `surface.md` §2, drawn from the pool's ordered membership by the
  seed: a baseline is `agents.build_baseline(name, seed)`, and a version is `policy_from` of its checkpoint
  beside its member record (`docs/L1/league.md` §3, D-16, `module-map.md` §2). A drawn version's policy
  carries the rule its container records, and the record's own `rule` is held to it (`rules.md` §6,
  `surface.md` §12).
- **Refusals:** a value that is not a pool; a seed that is not an integer (ASM-2); a pool whose drawn
  member carries no `path`, naming the member, because a version that cannot be loaded cannot be an
  opponent (`records.md` §7, `protocol.md` §5); a drawn member record whose declared `rule` contradicts the
  rule its checkpoint records, naming the member and both values (`rules.md` §6, `errors.md` §4, D-19).
- **Determinism:** one pool and one seed draw one opponent, and the draw is the seed reduced modulo the
  membership's size, so a spread of seeds samples the whole pool and not one fixed policy (ASM-2, FAM-7);
  the drawn policy answers one decision one way, because only the deal uses the global stream (ASM-2).
