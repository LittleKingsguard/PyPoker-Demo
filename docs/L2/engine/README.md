# engine — L2 integration interface

- **Layer:** L2 · **Module:** `engine` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-09
- **Covers:** the nine entry points of `docs/L1/e2e-surface.md` §3.1 and the environment they expose (D-2, ASM-2)
- **Reads:** `docs/L1/module-map.md` §2–§3, `e2e-surface.md` §1, §2, §3.1 and §5, `records.md` §1 and §5, `ladder.md` §4, `protocol.md` §2–§4, `league.md` §3, `battery.md` §3–§4, `assumptions.md` (ASM-6, ASM-12), `strata/platform.md`
- **Ceiling:** 60 lines. At the ceiling, split by owner — never append

## 1. The one job

`engine` is the fixed game of D-2 presented as a reinforcement-learning environment: it deals a
hand, says who acts and what that seat knows, says what that seat may do, advances the hand by one
chosen action, says when the hand is over, pays it, and answers the equity question the oracle
baseline asks (ASM-4, `module-map.md` §1). The game never varies: no entry point takes a rung, an
encoding, a bet size or any other game parameter, and the only arguments `play_hand` takes beside a
seed are the two policies whose actions it applies, so a rung-to-rung difference can never be the
game's (D-2, D-3).

## 2. The two documents

| Document | The owner of that question | What it fixes |
|---|---|---|
| `surface.md` | the callable surface | for each of the nine entry points: what it takes, what it returns, what it refuses, and its ordering and determinism guarantee (`e2e-surface.md` §3.1) |
| `environment.md` | the environment, and its callers | how a hand is dealt, advanced, ended and paid; the eleven readout facts and what they must never expose; the episode record; `equity`; seeding and the sequential rule; the contracts `features`, `agents`, `evaluation` and `training` hold at this edge; the battery invariants this module carries (`battery.md` §3) |

## 3. Boundaries

`engine` is the bottom of the map and depends on `pokerkit` and the standard library alone
(`module-map.md` §2, §3). Each of the following is a boundary and not a preference (D-1, D-2):

- never imports another project module, so no encoder, learner, pool, cell or reporter is reachable from here (`module-map.md` §3, D-13);
- never encodes an observation: the readout is the facts, and turning them into a tensor is `features`' work (D-3, `module-map.md` §3);
- never chooses an action: a policy chooses and this module only asks one and applies the answer (D-2, `e2e-surface.md` §2);
- never records a result: no cell, curve, matrix, rating or checkpoint is produced here (D-16, `module-map.md` §3);
- never owns a match: one cell, its hand count, its seat alternation and its opponent are `evaluation`'s (D-16, `league.md` §1);
- never leaves the global `random` seeded to anything but what `new_hand` left it: the deal stream has one seeding point, and every other call hands the stream back as it found it (ASM-2, `protocol.md` §4).

## 4. The count and the cap

Nine entry points, and L2 adds, removes and renames none of them: needing a tenth is a defect that
returns as an adjudication to L1 and is never invented here (D-12, `e2e-surface.md` §1). The harness
files that drive this module are capped at `50 + 10 × 9 = 140` lines, computed by `strata-lint` and
never asserted by a harness author (brief §5, `module-map.md` §4). Eight of the nine rows are
`general`, so the battery carries eight instances invented from the surface alone: the seeds, the
hands and the sample counts are the caller's to invent, and every valid instance of them is admitted
(D-15, `battery.md` §4).

## 5. What is left to L3

This document stops at the entry point. `role_l3_designer` owns the module design: the hand's data
structure and its wrapper over a `pokerkit` state, how the eleven facts are assembled and which card
spelling they use, how `equity` obtains its sample and leaves the global stream where it found it,
the error classes the refusals raise, and the file layout under `src/engine/` (D-1, `module-map.md` §5). Every
one of those is named as free here and is designed there, not here (D-12, D-13).
