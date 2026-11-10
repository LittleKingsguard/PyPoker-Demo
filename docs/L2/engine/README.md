# engine — L2 integration interface

- **Layer:** L2 · **Module:** `engine` · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-09
- **Covers:** the ten entry points of `docs/L1/e2e-surface.md` §3.1 and the environments they expose, on both declared game shapes (D-2, ASM-2, D-29)
- **Reads:** `docs/L1/module-map.md` §2–§3, `e2e-surface.md` §1, §2, §3.1 and §5, `shapes.md` §2–§5, `sizing.md` §2–§3 and §5, `records.md` §1, §5 and §15, `ladder.md` §4, `protocol.md` §2–§4, `league.md` §3, `battery.md` §3–§4, `assumptions.md` (ASM-6, ASM-12), `strata/platform.md`
- **Ceiling:** 62 lines. At the ceiling, split by owner — never append

## 1. The one job

`engine` is the declared game shapes presented as reinforcement-learning environments: it deals a
hand, says who acts and what that seat knows, says what that seat may do, advances the hand by one
chosen action, says when it is over, pays it, and answers the equity question the oracle baseline
asks (ASM-4, `module-map.md` §1). The game's own parameters are the module's — nine of them are a
shape's row and the tenth, `game_shapes`, publishes the rows (`shapes.md` §2, §4). No entry point
takes a rung or an encoding, and `play_hand`'s only arguments beside a seed are the two policies and
the shape, so a rung-to-rung difference can never be the game's (D-2, D-3).

## 2. The two documents

| Document | The owner of that question | What it fixes |
|---|---|---|
| `surface.md` | the callable surface | for each of the ten entry points: what it takes, what it returns, what it refuses, and its ordering and determinism guarantee (`e2e-surface.md` §3.1) |
| `environment.md` | the environment, and its callers | how a hand is dealt, advanced, ended and paid; the eleven readout facts and what they must never expose; the episode record and its legal-amount facts; `equity`; seeding and the sequential rule; the contracts `features`, `agents`, `evaluation` and `training` hold at this edge; the battery invariants this module carries (`battery.md` §3) |

## 3. Boundaries

`engine` is the bottom of the map and depends on `pokerkit` and the standard library alone
(`module-map.md` §2, §3). Each of the following is a boundary and not a preference (D-1, D-2):

- never imports another project module, so no encoder, learner, pool, cell or reporter is reachable from here (`module-map.md` §3, D-13);
- never encodes an observation: the readout is the facts, and turning them into a tensor is `features`' work, and the shape's normalisers are `features`' to apply (D-3, `sizing.md` §5);
- never chooses an action: a policy chooses and this module only asks one and applies the answer, resolving a raise to the amount its descriptor names (D-2, `e2e-surface.md` §2, `sizing.md` §2);
- never records a result: no cell, curve, matrix, rating or checkpoint is produced here (D-16, `module-map.md` §3);
- never owns a match: one cell, its hand count, its seat alternation and its opponent are `evaluation`'s (D-16, `league.md` §1);
- never leaves the global `random` seeded to anything but what `new_hand` left it: the deal stream has one seeding point, and every other call hands the stream back as it found it (ASM-2, `protocol.md` §4).

## 4. The count and the cap

Ten entry points, and L2 adds, removes and renames none of them: the one new name is `game_shapes`,
and the second shape reaches the rest by an optional argument whose absence is today's value — so the
count moves 9 → 10 and no caller in the tree changes (`shapes.md` §4, `e2e-surface.md` §3.1, §4).
Needing an eleventh is a defect that returns as an adjudication to L1 and is never invented here
(D-12, `e2e-surface.md` §1). The harness files that drive this module are capped at
`50 + 10 × 10 = 150` lines, computed by `strata-lint` and never asserted by a harness author
(brief §5, `module-map.md` §4). Eight of the ten rows are `general`, so the battery carries eight
instances invented from the surface alone; `game_shapes` and `game_config` are the `fixed` rows,
because the catalogue is the declaration itself and no caller can invent a shape through this
surface (D-15, `battery.md` §4, `e2e-surface.md` §5).

## 5. What is left to L3

This document stops at the entry point. `role_l3_designer` owns the module design: the shape
catalogue's home and the state each row creates, the hand's data structure and its wrapper over a
`pokerkit` state, how the eleven facts are assembled and which card spelling they use, how the four
raise bands resolve and are masked, how `equity` obtains its sample and leaves the global stream
where it found it, the error classes the refusals raise, and the file layout under `src/engine/`
(D-1, `module-map.md` §5). Every one of those is named as free here and is designed there, not here
(D-12, D-13).
