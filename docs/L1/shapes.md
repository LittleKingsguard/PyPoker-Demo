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

| Key | `fixed-limit-20` — the default (D-2, ASM-6) | `no-limit-100` (D-27, D-29) | `six-seat-no-limit-100` (D-33) |
|---|---|---|---|
| seats, blinds | two seats, blinds 1/2, one blind level that never rises | the same | six seats, the same blinds and the same single level (`seats.md` §2) |
| starting stack | 20 chips | 100 chips | 100 chips a seat |
| chips in play | 40 — `pot + sum(stacks)` at every decision | 200 — the same invariant at the new total | 600 — the same invariant at the six-seat total |
| history capacity | 24, the fixed-limit cap's bound (§8) | 66, the uncapped shape's derived bound (§8) | 98, its own derived bound (§8) |
| betting | fixed bets of 2 and 4, raise cap four bet-or-raise actions a street | no fixed bet and no cap: any legal amount up to the stack | the same, at six seats |
| action vocabulary | `fold`, `check-call`, `raise` — three indices | `fold`, `check-call`, `raise-quarter`, `raise-half`, `raise-all-in`, `raise-minimum` — six, in that index order (`sizing.md` §2–§3) | the same six, in the same order — the vocabulary is the shape's, and a seat count does not add a descriptor |
| head width | 3, the vocabulary's size | 6, the vocabulary's size (`sizing.md` §6) | 6, the vocabulary's |
| amount normalisers | stack ÷20, pot ÷40, `to_call` ÷20, bet size ÷4, action count ÷4 (ASM-6) | stack ÷100, pot ÷200, `to_call` ÷100, amount in force ÷100, action count ÷50 (`sizing.md` §5) | the same, with the pot ÷600 — the six-seat total (`sizing.md` §5) |
| layout widths | 203 dense, 40 tokens, vocabulary 96 | 329 dense, 82 tokens, vocabulary 96 (§8) | 433 dense, 122 tokens, vocabulary 102 (§8, `seats.md` §3) |
| declared pool additions | the three anchor baselines of D-6 | the same, plus the three folders of D-21: the price is folder-borne, so a baselines-only pool holds no opponent it applies to (D-26, D-21) | the same six, and version members of its own shape: the pool must hold folders **and** raisers (D-33 §2, `seats.md` §4) |

The three shapes share every **fact** of the readout; what changes is what the facts are worth — the seat count, the seats a `stacks` fact carries, what the divisors divide — because a divisor of 40 on a 200-chip game is not a normalisation but a clip (`sizing.md` §5, D-25, `seats.md` §3).

## 3. Identity — the four carriers

A run, a pool member, a checkpoint and a report each name the shape they are about, and no record names a shape it did not measure:

- the **configuration** carries `game` (a shape name), and `training.run`'s record repeats it under `game` (`records.md` §2, §12);
- a **checkpoint** records it in its container, and the container's format version is what says whether the field is there (`sizing.md` §6);
- a **pool** carries it on its declaration and its record, so a frozen pool is a pool *on one shape* and its membership cannot mix two (`records.md` §8);
- a **report** states it in its `header` family, beside the parameter counts and the seeds it already states (`protocol.md` §1).

The refusals are what make the identity load-bearing: a pool declaration naming one shape and a member of another is refused by name; a `load` whose spec names a shape its container contradicts is refused naming both, as a contradictory rule already is; and `evaluation.report` refuses a record whose run, pool and matrix do not name one shape. Each refusal is a case in `battery.md` §3 FAM-19.

An absent `game` reads as the **default** shape, in a configuration, a run record, a pool declaration and a version-1-to-3 container alike — the same way an absent `learning_rule` reads as the catalogue's first (D-19). That is what keeps every record the repository already holds readable without being rewritten (§5).

## 4. What the declaration costs

**Endpoints: one new and eleven widened.** `engine.game_shapes()` is the only new name — 50 endpoints across the map against 49 — so `engine` is 10 and its harness ceiling is 150 rather than 140 (`e2e-surface.md` §4, brief §5). The eight rows this page first declared are `engine.game_config`, `features.action_space`, `features.build_encoder`, `agents.build_learner`, `agents.as_policy`, `evaluation.build_pool`, `evaluation.policy_from` and `training.run`; the build added three more that a hand and an index cannot be told the shape without — `engine.new_hand`, `engine.play_hand` and `features.decode_action` — because `battery.md` §3 FAM-20 drives a sized hand through `engine.play_hand` and no other declared route creates one (`records.md` §5, §15). Every widening is an **optional argument or key whose absence reproduces today's value exactly**, which is why no caller in the tree changes, and an optional argument moves no row's count or kind: the map stays 50 and the `fixed`/`general` split stays 13/37. `modules.json`'s `endpoints` for `engine` must go 9 → 10 in the same change; this revision states the number and does not edit that file.

**The e2e battery does not lose a case.** Ten cases and one shared helper assert one game or three indices today — FAM-1.1 and FAM-1.14, FAM-2.1, FAM-2.2, FAM-2.9, FAM-2.10 and FAM-2.11, FAM-5.3's index assertion, FAM-7.8's drawn opponent, FAM-16.10's blind walk, and FAM-14's seam walk — and each becomes the same assertion **for the shape in force** rather than for the fixed game: extended, never weakened, as D-21 extended the baseline family (`battery.md` §2, §5). FAM-1 gains one case for the new name, and FAM-19 (the shape catalogue and the four refusals) and FAM-20 (the sized action) are new families, so the battery's 268 rises and nothing in it is dropped (`battery.md` §3).

**The blind instances do not move.** The catalogue row is `fixed`, the widened rows keep their kind, and the `general` count stays 37 with the `fixed` count rising 12 → 13 (`e2e-surface.md` §5, `battery.md` §4).

**What the layers below owe.** This pass writes `docs/L1/` only, and the two layers under it still state the fixed game and the three-index vocabulary as the game's own — `docs/L2/engine/surface.md` §3's heading, `docs/L2/features/surface.md` §7, `docs/L2/training/loop.md`'s fairness list, `docs/L3/features/vocabulary.md` §1, `docs/L3/agents/architecture.md` §2's `W → 3` and §5's `param_count` formula beside it, `docs/L3/evaluation/declarations.md` §2's header fields, and `docs/L3/engine/readout.md` §2's "the map stays at 49 endpoints" among them. Each is re-issued per shape when a build is authorised, in the dependency order of `module-map.md` §2, and none is edited here: the design is what they will be re-issued against, and no document is changed to make another true (D-13, D-29).

## 5. The fixed-limit path is unchanged

This is the constraint the whole design is written under, and the design meets it without an exception: every widening's absence reproduces today's value, the only new entry point is one no fixed-limit path calls, `engine.game_config()` and `features.action_space()` return today's mappings unchanged, the **default** shape keeps its slot counts, its widths, its capacity, its vocabulary and its head width of 3 — so `param_count` at that shape is today's formula and today's 10,119 holds (`docs/L3/agents/architecture.md` §5). D-33 widens the uncapped shapes' history and nothing of the default shape's (§8). The readout keeps eleven facts on every shape and no twelfth is added; what the seat count changes is the seats a `stacks` fact carries (`records.md` §5, `seats.md` §3, `docs/L3/engine/readout.md` §2).

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

## 8. The history block's capacity is the shape's (D-33)

Keeping one 203-slot layout for both shapes left the uncapped shape's history overflow latent until a raiser was
seated: a pool holding one trained no-limit model trains until a hand reaches 25 decisions and the encoder refuses
it, because the 24 slots are the **fixed-limit cap's** bound. D-33 widened the block per shape rather than
coarsening it — which loses the resolution the price lives in — or truncating it
(`strata/records/pool-without-raiser.md` §2, `decisions.md` D-33, D-31, D-32, ASM-42).

A shape's capacity is therefore **derived from its own betting and declared in its row**. A bet or raise
advances the street's bet level by at least the minimum bet of 2, and each seat commits that level on every
street it plays, so the levels summed over the four streets are at most the chips in play divided by the seats;
each seat also takes at most two non-bet actions on a street. So `no-limit-100` gives 200 ÷ 4 = 50 raises plus
4 × 2 × 2 = 16 = **66**, `six-seat-no-limit-100` gives 600 ÷ 12 = 50 plus 4 × 6 × 2 = 48 = **98**, and
`fixed-limit-20` keeps **24**, the number its cap gives (ASM-6, ASM-42). A longer history is refused naming the
field, the capacity and the count — never truncated (`sizing.md` §5).

| Quantity | `fixed-limit-20` | `no-limit-100` | `six-seat-no-limit-100` |
|---|---|---|---|
| dense width, `4 + seats + 34 + 85 + seats + 1 + 1 + 2 + 3 × slots` | 203 | **329** | **433** |
| token width, `1 + seats + 2 + 5 + seats + 1 + 1 + 2 + slots` | 40 | **82** | **122** |
| token vocabulary | 96 | 96 | **102** — six seat ids above the current top id (`seats.md` §3) |
| `param_count` at `W = 36`, `D = 2` — input + trunk + `A·W + A` | 10,119 | **14,766** | **18,510** |

Three consequences are accepted rather than absorbed, and each is a fact a record carries:

- **A kind's declared observation size is the default shape's.** `naive-stack`'s 203 and the token kinds' 96
  stay as they are; a learner on another shape takes its input width from that shape's encoder, and an
  encoder-less build on a non-default shape is refused by name rather than sized from a number that is not that
  shape's (`e2e-surface.md` §3.3, ASM-44).
- **The container carries the shape's width.** A version-4 container names its shape and records that shape's
  own `representation.size` and `representation.shape`; a reader checks the geometry against them rather than
  against the kind's 203, so a widened container restores to the head it was written at. A version-1, 2 or 3
  container is a default-shape one, is read as 203, and the **18 shipped containers still load untouched**
  (§5, `sizing.md` §6, ASM-40).
- **A greedy pass's record bound follows the shape**: at most 1,000 hands × the shape's capacity per variant per
  seed — 24,000 at the default shape, 66,000 and 98,000 on the uncapped ones — refused beyond and never
  truncated, because the pass records the learner's own decisions (`sizing.md` §4, ASM-38, D-31).
