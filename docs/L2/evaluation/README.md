# evaluation — L2 integration interface

- **Layer:** L2 · **Module:** `evaluation` · **Unit:** phase1 · **Rev:** 6 · **Date:** 2026-11-09
- **Ceiling:** 62 lines. At the ceiling, split by owner — never append
- **Covers:** the eleven entry points of `docs/L1/e2e-surface.md` §3.4 — the bounded pool, the match scheduler, the pairwise matrix,
  the fitted rating, the two tables and the per-rung report (D-16) — the learning rule, the terminal-reward utility and the **one
  shape** each of them carries since D-19, D-20 and D-29 (ASM-26, ASM-27, `utilities.md` §7, `shapes.md` §3), and `tables/`, where
  the precomputed offline table ships (`module-map.md` §5, D-8); **Rev 4:** a member declares `utility` beside `rule`, a window holds
  several families under one rule and one utility, the id digests both, and five records name the utility (`utilities.md` §5–§9);
  **Rev 5:** D-21's catalogue — the **pinned** set is its `anchor: True` members, `league()` gains `catalogue`, the declaration an
  optional `baselines` key refused by `UnknownBaseline`, and the anchor names its three (`folders.md` §2, §4, ASM-32); **Rev 6:**
  D-29's second shape — a pool, a member, a cell, a matrix, a rating, a policy and a report each name one shape, `policy_from` gains
  the exploration mode `off`, and no id, no rating and no header loses the shape it measured (`shapes.md` §6, `sizing.md` §4)
- **Reads:** `docs/L1/module-map.md` §1–§6, `e2e-surface.md` §1, §2, §3.4–§3.5 and §5, `records.md` §1, §7–§13, `rules.md` §1–§8,
  `league.md` §1–§8, `protocol.md` §1–§6, `ladder.md` §1–§6, `battery.md` §2–§5, `shapes.md` §2–§6, `sizing.md` §4–§7 and
  `assumptions.md` (ASM-2, ASM-5, ASM-10, ASM-14–ASM-21, ASM-26, ASM-27); and at the consumed edge `docs/L2/engine/surface.md`
  §1–§11, `docs/L2/features/surface.md` §3–§9, `docs/L2/agents/surface.md` §1–§12 and `docs/L2/agents/learner.md` §4–§5, §8

## 1. The one job

`evaluation` is the league: a bounded rolling pool of the model's last M versions plus the pinned baselines — the catalogue's
flagged three and any folder a declaration names — the scheduler that plays one cell at a time, the pairwise matrix of a membership,
the Bradley-Terry rating fitted over it, the two tables and the per-rung report (`module-map.md` §1, D-16, ASM-32). The same pool is
the training and the evaluation opposition (`module-map.md` §6, ASM-19) and it is one **shape's** — a pool, a cell, a table, a rating
and a report each name that one shape and none mixes two (`shapes.md` §3, §6, D-29) — and it never trains, never edits a curve or a
pool's membership: each member carries its rule, its utility and its shape while the id certifies the first two (ASM-16, D-20).

## 2. The documents, one per owner

| Document | The owner of that question | What it fixes |
|---|---|---|
| `surface.md` | the callable surface | for each of the eleven entry points: its arguments, its returned record, its refusals and its determinism — with §5–§8 redirected to `pool.md`; the six shared rules, and the shape, the policy and the member at this edge (`e2e-surface.md` §3.4, `shapes.md` §3) |
| `pool.md` | the four pool entry points | `build_pool`, `pool_members`, `offer`, `opponent` — the declaration with its optional `baselines` and `game` keys, the families and the fair-share window, the read-back's required `game`, `rules` and `utilities`, the rolling, the draw (`records.md` §8, ASM-26, ASM-32, D-20, D-21, D-29) |
| `rules.md` | the estimator axis | the catalogue read through the arrow; the `rule` a member declares; the families and the id that certifies it; the records that name it; `policy_from`'s rule and `RuleMismatch`; the population a report states (D-19, ASM-26, ASM-27); its sibling for D-20's axis is `docs/L3/evaluation/utility.md` |
| `league.md` | the league, the edge and the battery | the pool and its rolling window (§1); the scheduler (§2); the matrix (§3); the rating (§4); the two tables and the shipped `full` table (§5); the seven families, the shape the header names and what a report refuses (§6); the edge's contracts (§7); the battery invariants (§8) (D-16, ASM-14, ASM-17, D-29) |

## 3. Boundaries

Each of the following is a boundary and not a preference (`module-map.md` §3, D-16):

- never trains, updates, tunes or loads a learner for training: a member is played in evaluation mode and never changed
  (`module-map.md` §3, `protocol.md` §5, ASM-5);
- never edits a curve and never writes a run record — `training` produces the run and measures no cell — and never chooses the
  pool's membership nor invents a rule a record does not declare (`records.md` §13, ASM-16, D-19);
- never reports a table whose members it cannot name, whose cells differ in hand count or whose cells name two shapes, and never
  reduces the matrix to a ranking or calls a rating a claim of poker skill (`league.md` §3–§4, `records.md` §10, D-16);
- never imports `training`, never rebuilds a member from a checkpoint — it restores through `agents.load` and reads only the
  recorded seed, encoding name and shape (`pool.md` §4, D-13) — and never seeds the global `random` stream (`protocol.md` §4).

## 4. Counts, cap and blind instances

Eleven entry points, and L2 adds, removes and renames none of them: needing a twelfth is a defect that returns as an adjudication to
L1 and is never invented here (D-12, `e2e-surface.md` §1, §5). The harness files that drive this module are capped at
`50 + 10 × 11 = 160` lines, computed by `strata-lint` and never asserted by a harness author (brief §5); two rows are `fixed` and
nine are `general` (`battery.md` §4).

## 5. What is left to L3

This document stops at the entry point and at the records they exchange; `role_l3_designer` owns the module design — the pool's
type, the family grouping and the id's digest, the fair-share eviction, the pinned set read off the catalogue's flag, the seed
derivations, the shape a member, a cell and a header name, the rating's solver and bound, the layout of `src/evaluation/` and
`tables/`, and the refusals' classes (D-1, `module-map.md` §5, ASM-32, D-20, D-29).
