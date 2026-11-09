# evaluation — L2 integration interface

- **Layer:** L2 · **Module:** `evaluation` · **Unit:** phase1 · **Rev:** 4 · **Date:** 2026-11-09
- **Ceiling:** 62 lines. At the ceiling, split by owner — never append
- **Covers:** the eleven entry points of `docs/L1/e2e-surface.md` §3.4 — the bounded pool, the match
  scheduler, the pairwise matrix, the fitted rating, the two tables and the per-rung report (D-16) — the
  learning rule and the terminal-reward utility each of them carries since D-19 and D-20 (ASM-26, ASM-27,
  `utilities.md` §7), and `tables/`, where the precomputed
  offline table ships (`module-map.md` §5, D-8); **Rev 4:** a member declares `utility` beside `rule`, a window holds several
  families under one rule and one utility, the id digests both, and five records name the utility (`utilities.md` §5–§9)
- **Reads:** `docs/L1/module-map.md` §1–§6, `e2e-surface.md` §1, §2, §3.4–§3.5 and §5, `records.md` §1,
  §7–§13, `rules.md` §1–§8, `league.md` §1–§8, `protocol.md` §1–§6, `ladder.md` §1–§6, `battery.md` §2–§5,
  `assumptions.md` (ASM-2, ASM-5, ASM-10, ASM-14–ASM-21, ASM-26, ASM-27); and at the consumed edge
  `docs/L2/engine/surface.md` §1–§11, `docs/L2/features/surface.md` §3–§9, `docs/L2/agents/surface.md`
  §1–§12 and `docs/L2/agents/learner.md` §4–§5, §8

## 1. The one job

`evaluation` is the league: a bounded rolling pool of the model's last M versions plus the three pinned
baselines, the scheduler that plays one cell at a time, the pairwise matrix of a membership, the
Bradley-Terry rating fitted over that matrix, the two tables and the complete per-rung report
(`module-map.md` §1, D-16). The same pool is the training opposition and the evaluation opposition, so
there is no separate evaluation opponent and one owner holds both (`module-map.md` §6, ASM-19, D-16). It
measures; it never trains, never edits a curve and never chooses a pool's membership, and the pool is
deliberately heterogeneous: each member carries its rule and its utility and the id certifies both (`module-map.md` §3, ASM-16, D-20).

## 2. The documents, one per owner

| Document | The owner of that question | What it fixes |
|---|---|---|
| `surface.md` | the callable surface | for each of the eleven entry points: its arguments, its returned record, its refusals and its determinism — with §5–§8 redirected to `pool.md`; the six shared rules and the policy and the member at this edge (`e2e-surface.md` §3.4) |
| `pool.md` | the four pool entry points | `build_pool`, `pool_members`, `offer`, `opponent` — the declaration, the families and the fair-share window, the read-back's `rules` and `utilities`, the rolling, the draw (`records.md` §8, ASM-26, `utilities.md` §5–§7, D-20) |
| `rules.md` | the estimator axis | the catalogue read through the arrow; the `rule` a member declares; the families and the id that certifies it; the records that name it; `policy_from`'s rule and `RuleMismatch`; the population a report states (D-19, ASM-26, ASM-27); its sibling for D-20's axis is `docs/L3/evaluation/utility.md` |
| `league.md` | the league, the edge and the battery | the pool and its rolling window (§1); the scheduler (§2); the matrix (§3); the rating (§4); the two tables and the shipped `full` table (§5); the seven families and what a report refuses (§6); the edge's contracts (§7); the battery invariants (§8) (D-16, ASM-14, ASM-17) |

## 3. Boundaries

Each of the following is a boundary and not a preference (`module-map.md` §3, D-16):

- never trains, updates, tunes or loads a learner for training: a member is played in evaluation mode and
  never changed (`module-map.md` §3, `protocol.md` §5, ASM-5);
- never edits a curve and never writes a run record — `training` produces the run and measures no cell —
  and never chooses the pool's membership nor invents a rule a record does not declare (`records.md` §13, ASM-16, D-19);
- never reports a table whose members it cannot name or whose cells differ in hand count, and never reduces
  the matrix to a ranking or calls a rating a claim of poker skill (`league.md` §3–§4, `records.md` §10, D-16);
- never imports `training`, and never rebuilds a member from a checkpoint: it restores through `agents.load`
  and reads only the recorded seed and encoding name (`pool.md` §4, D-13); it never seeds the global
  `random` stream except through `engine`'s single seeding point (ASM-2, `protocol.md` §4).

## 4. Counts, cap and blind instances

Eleven entry points, and L2 adds, removes and renames none of them: needing a twelfth is a defect that
returns as an adjudication to L1 and is never invented here (D-12, `e2e-surface.md` §1, §5). The harness
files that drive this module are capped at `50 + 10 × 11 = 160` lines, computed by `strata-lint` and never
asserted by a harness author (brief §5, `module-map.md` §4). Two rows are `fixed` and nine are `general`
(`e2e-surface.md` §5, `battery.md` §4).

## 5. What is left to L3

This document stops at the entry point and at the records they exchange. `role_l3_designer` owns the module
design: the pool's type, the family grouping and the id's digest, the fair-share eviction, the seed
derivations, the rating's solver and bound, the layout of `src/evaluation/` and `tables/`, and the error classes the refusals raise (D-1, `module-map.md` §5, D-12, ASM-26, D-20).
