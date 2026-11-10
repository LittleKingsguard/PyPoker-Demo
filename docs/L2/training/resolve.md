# training — resolving, and the registry (`rungs`, `rung`)

- **Layer:** L2 · **Module:** `training` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-09
- **Owner of this file:** the two entry points that resolve rather than train — `rungs` and `rung`, their argument and
  returned records, their refusals and their determinism, and the one rule about a pool's id (D-3, `ladder.md` §2–§3,
  `e2e-surface.md` §3.5) — split out of `surface.md` §2–§3 at that file's ceiling, with the numbering kept
- **Reads:** `surface.md` §1, §4, §7; `loop.md` §1–§2, §7; `registry.md` §1–§5, `records.md` §2, §7–§8
- **Ceiling:** 60 lines. At the ceiling, split by owner — never append

## 2. `rungs` — the registry (`fixed` row)

- **Signature:** `rungs()`.
- **Arguments:** none: the six rungs are brief §2's, so no parameter can vary them (`e2e-surface.md` §3.5, D-3).
- **Returns:** one mapping keyed by the six rung names in brief §2's order — `R1` … `R6` — each value the resolved
  configuration §3 returns, so the registry is read one way and not two (`ladder.md` §2, D-3).
- **Refusals:** none; it has no argument.
- **Determinism and ordering:** two calls return equal records in that order, and the order is never rearranged
  without an L0 decision (D-2, D-3, `ladder.md` §2). The registry's content — each rung's axis, variants,
  primary, `carried_from` and pool — is `loop.md` §1's table and is data, not a code path (D-3). No row declares a
  `game`: every rung is the catalogue's **first** shape, and a configuration that names another reaches the same loop
  through `run` (`shapes.md` §1, §3, D-29).

## 3. `rung` — one resolved configuration (`general` row)

- **Signature:** `rung(name)`.
- **Arguments:** one rung name, a string, one of the six `rungs()` declares.
- **Returns:** one resolved configuration in `ladder.md` §3's schema — `name`, `axis`, `carried_from`
  (`None` for R1, the previous rung's primary variant for R2–R6), `primary`, `variants` (one or two
  `records.md` §2 entries) and `pool` — plus this module's own keys, which `loop.md` §2 lists. The `pool` entry
  is the declaration `run` freezes: the inherited `lineage`, the bound `m`, `frozen`, the `members` (the
  version window, `records.md` §7 records in lineage order) and the `id` every arm's run record carries
  (`ladder.md` §3, `records.md` §8).
- **Behaviour:** resolving is not training: it builds no learner, plays no hand and writes nothing (D-3). The
  window is read from the shipped index `surface.md` §7 returns, and a lineage checkpoint the repository does not carry
  leaves the window short, so the pool holds the baselines and whatever versions are present
  (`protocol.md` §5, `league.md` §2).
- **Refusals:** a name the registry does not carry, naming it — and never resolving it as a configuration,
  because a configuration reaches the loop through `run` and through no other entry point (`e2e-surface.md` §2,
  `ladder.md` §3, `battery.md` §3 FAM-15, FAM-16).
- **Determinism:** one name resolves one configuration. The declared `pool.id` is the id the run record will
  carry, because it is the read-back `id` of the membership through `evaluation.pool_members`
  (`ladder.md` §3, `records.md` §8, `evaluation/surface.md` §6).

### 3.1 A pool's id is read once (Rev 2, measured)

Resolving reads the window the repository carries — an absent checkpoint is not a member (`loop.md` §3) — and takes the id from
`pool_members`' read-back, so a registry rung's declared id *is* the digest and its record carries one id, not two (two would make
"both arms trained against one pool" unreadable, FAM-3.18); a configuration in no registry that declares its own `id` has that id
carried, with the digest of what it froze not listed beside it (FAM-15.2). A `pool` entry declaring no `baselines` keeps the id it
has today, so the six registry rows resolve to exactly the ids they resolve to now (ASM-32, D-21). The shape is **not** in the
digest either, on the same rule: two pools of one membership on two shapes are one id and are never one table, which is why the
shape is a required field of a pool record and not of its id (`records.md` §8, `shapes.md` §3, D-29).
