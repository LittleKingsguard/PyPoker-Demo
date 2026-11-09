# agents — L2 integration interface

- **Layer:** L2 · **Module:** `agents` · **Unit:** phase1 · **Rev:** 6 · **Date:** 2026-11-09
- **Covers:** the ten entry points of `docs/L1/e2e-surface.md` §3.3 — one learner family, the learning-rule
  catalogue and the three fixed baselines (D-6, ASM-7, D-19) — and the `agents` → `features` edge that
  `module-map.md` §2 grants (D-3)
- **Reads:** `docs/L1/module-map.md` §1–§5 (rev 2's amended `agents` row in §2), `e2e-surface.md` §1, §2,
  §3.3, §3.4 and §5, `records.md` §1–§4, §6, §7, §9 and §12, `ladder.md` §1–§6, `protocol.md` §1–§5,
  `rules.md` §1–§8, `league.md` §2–§4, `battery.md` §3–§5, `assumptions.md` (ASM-2, ASM-4, ASM-5, ASM-7,
  ASM-10, ASM-12, ASM-15, ASM-18, ASM-25); and at the consumed edge `docs/L2/features/surface.md` §1–§9,
  `encodings.md` §1–§6, `docs/L2/engine/surface.md` §2–§11, `environment.md` §1–§6
- **Ceiling:** 60 lines. At the ceiling, split by owner — never append

## 1. The one job

`agents` is everything that chooses or learns an action: one learner family, the learning-rule catalogue it learns
under, the terminal-reward utility catalogue whose reward its target carries, and the three fixed baselines
(`module-map.md` §1, D-6, ASM-7, D-19, D-20). It acts and it learns; it never deals a
hand, never measures a match, never schedules an opponent and never writes a report (`module-map.md` §3). What a rung
holds constant is the **set** of rules its variants declare and the **set** of utilities they name, beside the action vocabulary and the readout
facts, so a rung-to-rung difference is never either axis's (D-3, ASM-7, ASM-12, `rules.md` §8, `utilities.md` §8, D-19, D-20).

## 2. The two documents

| Document | The owner of that question | What it fixes |
|---|---|---|
| `surface.md` | the callable surface | for each of the ten entry points: what it takes, what it returns, what it refuses, and its determinism (`e2e-surface.md` §3.3) |
| `learner.md` | the learner family, the backend axis, the baselines, a version, and the contracts at this edge | the catalogue's two rules and the one contract they answer, and the R1↔R2 backend swap (§1–§2); the parameter budget (§3); `save`/`load` as a version under the rule and the utility it records (§4); the three baselines' rules (§5); the granted `features` edge and the sizing rule, and what `engine`, `training` and `evaluation` hold here (§6–§8); the battery invariants this module carries (§9) (D-7, D-6, ASM-5, ASM-10, ASM-25, D-19, D-20) |
| `utility.md` | the terminal-reward utility at this edge | the fifth catalogue `learners()` publishes (§1), the spec's optional `utility` and the declared default (§2), what a learner and a policy carry (§3), the container's field and the three format versions (§4), the four refusals side by side (§5) and what the surface does not become (§6) (`utilities.md` §2–§7, D-20) |

## 3. Boundaries

Each of the following is a boundary and not a preference (`module-map.md` §3, D-6, D-7):

- never deals, advances or pays a hand: a hand is `engine`'s and an episode belongs to its owner (D-2, `environment.md` §1);
- never decides legality: the legal set is the engine's and this module only chooses one of its indices (D-2, `features/surface.md` §2);
- never implements an encoding and never builds an encoder: `module-map.md` §2 grants this module five
  `features` calls — `encode`, `observation_spec`, `action_space`, `legal_indices`, `decode_action` — and no
  sixth, so `build_encoder` stays the caller's and the encoder always arrives in a spec or in `as_policy`
  (D-3, `module-map.md` §2, `learner.md` §6);
- never measures a match, plays a cell, schedules an opponent or counts a table: the pool, the cells, the matrix and the rating are `evaluation`'s (D-16, `league.md` §1);
- never writes a curve, a run record or a report: it returns an update's own statistics and the caller assembles the evidence (D-6, `protocol.md` §1);
- never seeds, advances or reads the global `random` stream, because `engine.new_hand` is the project's single seeding point (ASM-2, `protocol.md` §4);
- never claims skill: a version's worth is a table position beside the baselines, never a rating this module produces (D-16, `league.md` §8).

## 4. Count, cap and the blind instances

Ten entry points, and L2 adds, removes and renames none of them: needing an eleventh is a defect that
returns as an adjudication to L1 and is never invented here (D-12, `e2e-surface.md` §1). The harness files
that drive this module are capped at `50 + 10 × 10 = 150` lines, computed by `strata-lint` and never
asserted by a harness author (brief §5, `module-map.md` §4). Three rows are `fixed` — `learners`,
`baselines`, `build_baseline` — and seven are `general`, so the battery carries seven instances invented
from this surface alone (`e2e-surface.md` §5, `battery.md` §4, D-15).

## 5. What is left to L3

This document stops at the entry point and at the records they exchange. `role_l3_designer` owns the module
design: the learner's own type and how a backend realises it, the initialisation order and the tie-break rule, how
the keyed exploration draw is derived from the learner's generator, **how each rule's target is computed**, the
checkpoint format's bytes, version and fields, the error classes the refusals raise, and the layout under `src/agents/` (D-1, `module-map.md` §5, `rules.md` §3, D-20).
