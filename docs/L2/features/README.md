# features — L2 integration interface

- **Layer:** L2 · **Module:** `features` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-05
- **Covers:** the seven entry points of `docs/L1/e2e-surface.md` §3.2, the two encodings of D-3 and the
  three-index action vocabulary of D-2
- **Reads:** `docs/L1/module-map.md` §2–§3, `e2e-surface.md` §1, §2, §3.2–§3.3 and §5, `records.md` §1, §2,
  §4 and §6, `ladder.md` §2–§5, `protocol.md` §1 and §4, `battery.md` §2–§4, `assumptions.md` (ASM-2, ASM-6,
  ASM-10); and at the consumed edge `docs/L2/engine/surface.md` §2, §4, §6–§7, `environment.md` §1–§2, §5–§6
  and engine `README.md` §5
- **Ceiling:** 60 lines. At the ceiling, split by owner — never append

## 1. The one job

`features` turns one readout into one observation and one action index into one action descriptor, in one
of two declared representations (D-3, `module-map.md` §1). It is the ladder's representation axis and
nothing else: the game, the information set and the three-index vocabulary are held constant across every
rung, and this module is what changes between them (`ladder.md` §2, §4, D-2). No entry point here takes a
seed, a hand, a learner, a rung, an opponent or a game parameter (`e2e-surface.md` §3.2, D-3, ASM-2).

## 2. The two documents

| Document | The owner of that question | What it fixes |
|---|---|---|
| `surface.md` | the callable surface | for each of the seven entry points: what it takes, what it returns, what it refuses, and its ordering and determinism (`e2e-surface.md` §3.2) |
| `encodings.md` | the representation axis, and the contracts at this edge | the nine carried fields and why they never move; the shape, dtype and vocabulary of each encoding; what `engine` and `agents` may rely on; the battery invariants this module carries (`battery.md` §3) |

## 3. Boundaries

Each of the following is a boundary and not a preference (`module-map.md` §3, D-3):

- never decides legality: a decision's legal set is the engine's and this module only names its indices
  (`module-map.md` §3, D-2);
- never applies, simulates or scores an action: it decodes an index and the engine refuses or advances
  (`engine/surface.md` §7, D-2);
- never counts a parameter, sizes a model or chooses an architecture: it declares what a learner consumes
  (`module-map.md` §2, ASM-10);
- never learns which opponent it faces and never carries a rung beyond the encoding's name
  (`module-map.md` §3, D-3);
- never draws randomness, seeds or advances the global `random` stream, because `engine.new_hand` is the
  project's single seeding point (ASM-2, `protocol.md` §4);
- never imports a project module: the readout arrives as a mapping and leaves as an array, and the modules
  that call this one read it through this interface (`module-map.md` §2, D-13).

## 4. Count, cap and the blind instances

Seven entry points, and L2 adds, removes and renames none of them: needing an eighth is a defect that
returns as an adjudication to L1 and is never invented here (D-12, `e2e-surface.md` §1). The harness files
that drive this module are capped at `50 + 10 × 7 = 120` lines, computed by `strata-lint` and never
asserted by a harness author (brief §5, `module-map.md` §4). Four rows are `fixed` — `encodings`,
`build_encoder`, `observation_spec`, `action_space` — and three are `general`, so the battery carries three
instances invented from this surface alone (`e2e-surface.md` §5, `battery.md` §4, D-15).

## 5. What is left to L3

This document stops at the entry point and at the two representations' declared fields, block sizes, shape,
dtype and vocabulary. `role_l3_designer` owns the module design: the encoder's type, the order of the blocks
and the slot order inside each, the bucket edges of `card-tokens`, the map from a card's rank and suit to
its slot and to its id, the error classes the refusals raise and the file layout under `src/features/`
(D-1, D-12). Every one of those is named as free here and is designed there, not here.
