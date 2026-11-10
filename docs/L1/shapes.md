# PyPoker-Demo — L1 game shapes

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-09
- **Covers:** the second declared game shape D-29 authorises for design — what a shape is, the catalogue `engine` publishes for it, the identity a run, a pool member, a checkpoint and a report each name, what the declaration costs in endpoints and in e2e cases, and the fixed-limit boundary it may not move (D-29, D-28, D-2)
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append

## 1. A shape is a declaration, not a rung and not a module

D-29 authorises the sized-action artefact path for a second game shape beside D-2's; it authorises no build (`sizing.md` §7). A shape is **data**: one row of a catalogue `engine` publishes, named by a configuration, and carried by every record that reports a result. It is not a rung — the ladder's axis stays the technique, and a rung that changed the game would change two things at once (D-3) — and it is not a module: the second shape adds no seventh module and no Phase 2 seam, because a shape is a game parameter, and game parameters are `engine`'s (`module-map.md` §7, D-13).

The second shape is reached the way any configuration outside the registry is reached: as a value through `training.run` (`ladder.md` §3, `battery.md` §3 FAM-15). So no rung of brief §2 changes, and the ladder's six rows keep one shape between them (D-3).

Rejected: a seventh rung whose axis is the game. A rung is a comparison, and §6 shows the two shapes' evidence is not comparable at all, so such a rung could not be read — it would be a second design dressed as one row of the ladder.

## 2. The catalogue — `engine.game_shapes()`

One new entry point publishes the declared shapes, default first: its instance set is the declaration itself, so the row is `fixed` and no instance of it can be invented (`e2e-surface.md` §5). `engine.game_config(shape)` takes a shape name and returns that shape's row; called with no argument it returns the **default** shape's row, which is byte-for-byte the mapping `engine.game_config()` returns today (D-2, ASM-6). A name outside the catalogue is refused **naming it and the declared names** — never defaulted, because a default on a name is the silent substitution `e2e-surface.md` §2 forbids (D-13).

| Key | `fixed-limit-20` — the default (D-2, ASM-6) | `no-limit-100` (D-27, D-29) |
|---|---|---|
| seats, blinds | two seats, blinds 1/2, one blind level that never rises | the same |
| starting stack | 20 chips | 100 chips |
| chips in play | 40 — `pot + sum(stacks)` at every decision | 200 — the same invariant at the new total |
| betting | fixed bets of 2 and 4, raise cap four bet-or-raise actions a street | no fixed bet and no cap: any legal amount up to the stack |
| action vocabulary | `fold`, `check-call`, `raise` — three indices | `fold`, `check-call`, `raise-quarter`, `raise-half`, `raise-all-in`, `raise-minimum` — six, in that index order (`sizing.md` §2–§3) |
| head width | 3, the vocabulary's size | 6, the vocabulary's size (`sizing.md` §6) |
| amount normalisers | stack ÷20, pot ÷40, `to_call` ÷20, bet size ÷4, action count ÷4 (ASM-6) | stack ÷100, pot ÷200, `to_call` ÷100, amount in force ÷100, action count ÷50 (`sizing.md` §5) |
| declared pool additions | the three anchor baselines of D-6 | the same, plus the three folders of D-21: the price is folder-borne, so a baselines-only pool holds no opponent it applies to (D-26, D-21) |

The two shapes share every **fact** of the readout and every **slot** of both encodings: what changes is what the facts mean and what the divisors and buckets are, because a divisor of 40 on a 200-chip game is not a normalisation but a clip (`sizing.md` §5, D-25).

## 3. Identity — the four carriers

A run, a pool member, a checkpoint and a report each name the shape they are about, and no record names a shape it did not measure:

- the **configuration** carries `game` (a shape name), and `training.run`'s record repeats it under `game` (`records.md` §2, §12);
- a **checkpoint** records it in its container, and the container's format version is what says whether the field is there (`sizing.md` §6);
- a **pool** carries it on its declaration and its record, so a frozen pool is a pool *on one shape* and its membership cannot mix two (`records.md` §8);
- a **report** states it in its `header` family, beside the parameter counts and the seeds it already states (`protocol.md` §1).

The refusals are what make the identity load-bearing: a pool declaration naming one shape and a member of another is refused by name; a `load` whose spec names a shape its container contradicts is refused naming both, as a contradictory rule already is; and `evaluation.report` refuses a record whose run, pool and matrix do not name one shape. Each refusal is a case in `battery.md` §3 FAM-19.

An absent `game` reads as the **default** shape, in a configuration, a run record, a pool declaration and a version-1-to-3 container alike — the same way an absent `learning_rule` reads as the catalogue's first (D-19). That is what keeps every record the repository already holds readable without being rewritten (§5).

## 4. What the declaration costs

**Endpoints: one new and eight widened.** `engine.game_shapes()` is the only new name — 50 endpoints across the map against 49 — so `engine` is 10 and its harness ceiling is 150 rather than 140 (`e2e-surface.md` §4, brief §5). The eight widened rows are `engine.game_config`, `features.action_space`, `features.build_encoder`, `agents.build_learner`, `agents.as_policy`, `evaluation.build_pool`, `evaluation.policy_from` and `training.run`; every widening is an **optional argument or key whose absence reproduces today's value exactly**, which is why no caller in the tree changes. `modules.json`'s `endpoints` for `engine` must go 9 → 10 in the same change; this revision states the number and does not edit that file.

**The e2e battery does not lose a case.** Ten cases and one shared helper assert one game or three indices today — FAM-1.1 and FAM-1.14, FAM-2.1, FAM-2.2, FAM-2.9, FAM-2.10 and FAM-2.11, FAM-5.3's index assertion, FAM-7.8's drawn opponent, FAM-16.10's blind walk, and FAM-14's seam walk — and each becomes the same assertion **for the shape in force** rather than for the fixed game: extended, never weakened, as D-21 extended the baseline family (`battery.md` §2, §5). FAM-1 gains one case for the new name, and FAM-19 (the shape catalogue and the four refusals) and FAM-20 (the sized action) are new families, so the battery's 268 rises and nothing in it is dropped (`battery.md` §3).

**The blind instances do not move.** The catalogue row is `fixed`, the widened rows keep their kind, and the `general` count stays 37 with the `fixed` count rising 12 → 13 (`e2e-surface.md` §5, `battery.md` §4).

**What the layers below owe.** This pass writes `docs/L1/` only, and the two layers under it still state the fixed game and the three-index vocabulary as the game's own — `docs/L2/engine/surface.md` §3's heading, `docs/L2/features/surface.md` §7, `docs/L2/training/loop.md`'s fairness list, `docs/L3/features/vocabulary.md` §1, `docs/L3/agents/architecture.md` §2's `W → 3` and §5's `param_count` formula beside it, `docs/L3/evaluation/declarations.md` §2's header fields, and `docs/L3/engine/readout.md` §2's "the map stays at 49 endpoints" among them. Each is re-issued per shape when a build is authorised, in the dependency order of `module-map.md` §2, and none is edited here: the design is what they will be re-issued against, and no document is changed to make another true (D-13, D-29).

## 5. The fixed-limit path is unchanged

This is the constraint the whole design is written under, and the design meets it without an exception: every widening's absence reproduces today's value, the only new entry point is one no fixed-limit path calls, `engine.game_config()` and `features.action_space()` return today's mappings unchanged, both encodings keep their slot counts, widths and vocabulary, and the fixed-limit shape's head width is 3 — so `param_count` at that shape is today's formula and today's 10,119 holds (`docs/L3/agents/architecture.md` §5). The readout keeps eleven facts in both shapes and no twelfth is added (`records.md` §5, `docs/L3/engine/readout.md` §2).

The 18 shipped checkpoints are version-1 containers and stay version 1, read as the default shape's — which is what the absence of the field means (§3). `checkpoints/evidence/r1-live.json` and `tables/league-full.json` are records of one fixed-limit run and one fixed-limit table; neither is re-measured, neither is rewritten, and no field is added to them (D-8, ASM-18, `protocol.md` §5). A future fixed-limit run writes a version-3 container exactly as today and its payload is byte-identical; only a run on another shape writes version 4 (`sizing.md` §6).

## 6. The boundary, and what is never compared across it

The 18 checkpoints, `checkpoints/evidence/r1-live.json`, `tables/league-full.json`, the six rungs of brief §2 and both deep runs of D-8 are **Phase 1's fixed-limit evidence**. They stay exactly that: no member, cell, rating, curve or cost on one shape is compared with one on the other, and no table mixes the two, because the games differ in the stack, the amounts, the action space and the price of every decision (D-2, D-16, D-26).

- A matrix is measured on one shape, and its members carry that shape; a cell between two shapes is refused by name (`league.md` §4).
- A rating is fitted over one shape's cells and reads as a distance from the baselines *in that game*; two shapes' ratings are not on one scale and are never tabulated together (D-16, ASM-17).
- The `live` and `full` table budgets, the seed contract, the sequential-play rule and the per-hand cost band are one contract for both shapes; what differs is the hand's price, which is the measurement's to report (`protocol.md` §2, §4, ASM-21).

So a figure the talk quotes about R1 keeps its meaning, and the second shape's figures are new figures about a new game rather than a correction of them (D-29, ASM-23).

## 7. The supersessions this design requires

The register's rule is that a later row names what it supersedes, and four rows are ACTIVE and would be false the day the second shape exists (`strata/decisions.md`). Naming them is L1's; filing them is L0's, because the register is not this layer's write scope:

- **D-2** ("the game never changes across the ladder") — superseded as to the number of declared shapes: the ladder is one shape, and the project declares a second. D-2's ladder invariant survives inside the shape.
- **D-3** ("changing the game is Phase 2+ work, not a rung") — superseded: the second shape is designed now, and it is still not a rung, so what D-3 protects (one axis per comparison) is unchanged.
- **D-4** ("Phase 2 moves the techniques to heads-up no-limit") — superseded as to placement: no-limit's artefact path is designed in Phase 1 and its build is gated on `sizing.md` §7's criterion, not on a phase boundary.
- **ASM-6** (20-chip stacks, fixed bets, a cap of four) — superseded as the *only* parameterisation: it stays the default shape's row (§2) and stops being the game's.

D-25, D-26, D-27 and D-28 already record the retractions and the gates this design answers, and D-29 records the authorisation; none of them is reworded here (D-29).
