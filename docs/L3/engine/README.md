# engine — module design (L3)

- **Layer:** L3 · **Module:** `engine` · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-09
- **Realises:** `docs/L2/engine/surface.md` (the ten entry points) and `docs/L2/engine/environment.md` (the hand's life, the eleven facts, the episode, `equity`, seeding) — on both declared game shapes (D-29)
- **Reads:** `docs/L1/e2e-surface.md` §2–§3.1, §5, `docs/L1/shapes.md` §1–§5, `docs/L1/sizing.md` §2–§3, §5, `docs/L1/folders.md` §3, `docs/L1/records.md` §1, §5, `docs/L1/module-map.md` §2–§4, `docs/L1/battery.md` §2–§5, `docs/L1/assumptions.md` (ASM-6, ASM-12, ASM-15, ASM-30), `strata/decisions.md` (D-2, D-3, D-6, D-11, D-12, D-13, D-16, D-21, D-25, D-26, D-29, D-30), `strata/platform.md`
- **Ceiling:** 85 lines — raised from 75 for the second declared shape: a tenth export, a tenth document and the shape-is-data rule. At the ceiling, split by owner — never append
- **Implements:** `src/engine/` (written by L4, never by L3). `tests/engine/` is this design's unit battery

## 1. What this module is

`engine` is the project's poker environment, and the bottom of the dependency map: it imports
`pokerkit` and the Python standard library and **nothing of this project** — no `features`, no
`agents`, no `evaluation`, no `training`, no `harness`, ever (`module-map.md` §3, D-1).

It deals a hand from a seed, says who acts and what that seat knows, says what that seat may do,
advances it by one chosen action, says when it is over, pays it, and answers the equity question the
oracle asks — and never encodes, chooses, records a result or owns a match (`docs/L2/engine/README.md` §3).

It plays the **declared shapes** and not one fixed game: `fixed-limit-20` (D-2's game, ASM-6's
parameters) and `no-limit-100` (D-29's), published as one catalogue (`config.md` §1). A shape is
**data** — one row of that catalogue — and is neither a rung nor a module: the ladder's axis stays the
technique, no rung's game changes, and the second shape adds no file, no seam and no row of the
ladder (`shapes.md` §1, D-3, D-13).

## 2. The documents, one per owner

| Document | Owner of that question | What it fixes |
|---|---|---|
| `config.md` | the declared shapes | the catalogue and its home in `config.py`, the two rows, the default and the refusal, `game_config`'s fifteen keys, the chips-in-play invariant, the divisors per row, the four raise bands, the index order, and the `pokerkit` state each row creates |
| `hand.md` | the hand | the `Hand` handle over a `pokerkit` state and the shape's name, the **seat mapping**, `new_hand`'s seeding, `is_terminal`, `payoffs` |
| `advance.md` | one applied action | the advance by copy (and the rejected replay) |
| `history.md` | the public history | the one-entry-per-action rule, the entry grammar, the `<amount>` and `<index>` definitions, and why a card never appears |
| `actions.md` | the action vocabulary | the shape's descriptors: their type, value equality, stable text, and how each raise resolves to an amount |
| `stepping.md` | legality and the step | `legal_actions`' order and refusals, `apply_action`'s validation and its three-method idiom |
| `readout.md` | the eleven facts | each fact's derivation and type, the card spelling, the seat fact's shape, the derived hand-class fact, what the readout may never expose |
| `episode.md` | `play_hand` | the policy protocol, the episode record, the decision records, where the reward lands |
| `equity.md` | the equity question | what the answer is conditional on, and hand-or-readout equivalence |
| `equity-sample.md` | the equity sample | the unseen deck, the `calculate_equities` call, the library's tie share, and the five things that bind the implementation |
| `stream.md` | the global `random` stream | one seeding point, `equity`'s save/seed/restore, and the measured cost |
| `errors.md` | refusals | the error hierarchy, and what is deliberately *not* refused |
| `messages.md` | the message grammar | the message form, the canonical message per refusal, and the two properties the battery relies on |
| `layout.md` | the files | the file layout of `src/engine/`, the ten exported names, what is not surface |
| `guardrails.md` | L4 | one note per risk this design identified, in the order they bite |
| `cost.md` | the cost of a hand | ASM-15's measurement question, what dominates it, the one knob that decides it, and what was not measured |
| `platform.md` | the platform | the measured `pokerkit` 0.7.7 facts this design rests on, and the three received claims they correct |

## 3. The ten names, and what is *not* a name

The `engine` package exports exactly ten entry points and adds, removes and renames none
(`e2e-surface.md` §1, D-12). `game_shapes` is the tenth and is `surface.md` §12's; the other nine are
`surface.md` §3–§11's, in the order they are declared there:

    game_shapes()                                         -> Mapping      (the catalogue, default first)
    game_config(shape=None)                               -> Mapping      (fifteen keys)
    new_hand(seed, shape=None)                            -> Hand
    readout(hand)                                         -> Mapping      (eleven keys)
    legal_actions(hand)                                   -> tuple[str, ...]
    apply_action(hand, action)                            -> Hand
    is_terminal(hand)                                     -> bool
    payoffs(hand)                                         -> Mapping[int, int]
    play_hand(seed, seat0_policy, seat1_policy, shape=None) -> Mapping
    equity(decision, seed, samples)                       -> float

Every rule that holds of all ten is `docs/L2/engine/surface.md` §1 and is not restated here: an
invalid argument raises an error naming the violated contract — no coercion, no substituted default,
no swallowed error, no partial record; no entry point mutates the hand it is given; `new_hand` is the
single seeding point and every other call hands the global `random` stream back as it found it. The
shape is reached only through the optional argument of `new_hand`, `game_config` and `play_hand`,
whose absence is the default shape — never beside a hand (`surface.md` §1, §3, §4, §10, §12).

A `Hand`, the error classes, the card spelling helper, the constants, the shape rows and every helper
below an entry point are **not** surface (`e2e-surface.md` §1): an L4 change to any of them
is not a contract change, and the unit battery drives the ten names only.

## 4. Two decisions a later module must not re-derive

1. **One spelling of a card and of an action exists in the project, and it is this module's**
   (`e2e-surface.md` §2, `features/encodings.md` reads it). A card is a two-character plain `str` such
   as `"Td"`; an action is one of the plain `str`s its shape declares — three in the fixed-limit shape,
   six in the no-cap one (`config.md` §2, §6). Neither is a `pokerkit` class and neither needs the
   library read: `features` parses the spelling (`readout.md` §3, `actions.md` §2).
2. **The engine's seat 0 is `pokerkit`'s player 1, in every shape.** The mapping is fixed in
   `hand.md` §3 and every per-seat fact (stacks, payoffs, the readout's `seat`, a decision's `seat`)
   is expressed in *engine seat order*. A module that reads a `pokerkit` index directly will invert
   the button.
