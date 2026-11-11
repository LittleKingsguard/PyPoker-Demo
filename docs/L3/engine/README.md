# engine — module design (L3)

- **Layer:** L3 · **Module:** `engine` · **Unit:** phase1 · **Rev:** 4 · **Date:** 2026-11-10
- **Realises:** `docs/L2/engine/surface.md` (the ten entry points) and `docs/L2/engine/environment.md` (the hand's life, the eleven facts, the episode, `equity`, seeding) — on all three declared game shapes (D-29, D-33)
- **Reads:** `docs/L1/e2e-surface.md` §2–§3.1, §5, `docs/L1/shapes.md` §1–§5, §8, `docs/L1/seats.md` §2–§6, `docs/L1/sizing.md` §2–§3, §5, `docs/L1/folders.md` §3, `docs/L1/records.md` §1, §5, `docs/L1/module-map.md` §2–§4, `docs/L1/battery.md` §2–§5, `docs/L1/assumptions.md` (ASM-6, ASM-12, ASM-15, ASM-30, ASM-42, ASM-43, ASM-44), `strata/decisions.md` (D-2, D-3, D-6, D-11, D-12, D-13, D-16, D-21, D-25, D-26, D-29, D-30, D-33), `strata/platform.md`
- **Ceiling:** 104 lines — raised from 85 for the third declared shape: a seventh row in the document table's sense of a shape, the seat count as shape data, the `seats` argument of `play_hand`, and the general seat map. At the ceiling, split by owner — never append
- **Implements:** `src/engine/` (written by L4, never by L3). `tests/engine/` is this design's unit battery

## 1. What this module is

`engine` is the project's poker environment, and the bottom of the dependency map: it imports
`pokerkit` and the Python standard library and **nothing of this project** — no `features`, no
`agents`, no `evaluation`, no `training`, no `harness`, ever (`module-map.md` §3, D-1).

It deals a hand from a seed, says who acts and what that seat knows, says what that seat may do,
advances it by one chosen action, says when it is over, pays it, and answers the equity question the
oracle asks — and never encodes, chooses, records a result or owns a match (`docs/L2/engine/README.md` §3).

It plays the **declared shapes** and not one fixed game: `fixed-limit-20` (D-2's game, ASM-6's
parameters), `no-limit-100` (D-29's) and `six-seat-no-limit-100` (D-33's), published as one catalogue
(`config.md` §1). A shape is **data** — one row of that catalogue — and is neither a rung nor a module:
the ladder's axis stays the technique, no rung's game changes, and a further shape adds no file, no seam
and no row of the ladder (`shapes.md` §1, D-3, D-13, D-33). A row's **seat count** is that data like its
stack or its blinds: it sizes the readout's `stacks`, the `payoffs` mapping and `play_hand`'s seating, so
nothing below this module may assume two seats (`seats.md` §2–§4, ASM-44).

## 2. The documents, one per owner

| Document | Owner of that question | What it fixes |
|---|---|---|
| `config.md` | the declared shapes | the catalogue and its home in `config.py`, the three rows, the default and the refusal, `seat_count` and the row's `history` capacity, `game_config`'s fifteen keys, the chips-in-play invariant, the divisors per row, the four raise bands, the index order, and the `pokerkit` state each row creates |
| `hand.md` | the hand | the `Hand` handle over a `pokerkit` state and the shape's name, the **seat mapping** and its derivation, `new_hand`'s seeding, `is_terminal`, `payoffs` as one entry per seat |
| `advance.md` | one applied action | the advance by copy (and the rejected replay) |
| `history.md` | the public history | the one-entry-per-action rule, the entry grammar, the `<amount>` and `<index>` definitions, and why a card never appears |
| `actions.md` | the action vocabulary | the shape's descriptors: their type, value equality, stable text, how each raise resolves to an amount, and why a seat count adds none |
| `stepping.md` | legality and the step | `legal_actions`' order and refusals, `apply_action`'s validation and its three-method idiom |
| `readout.md` | the eleven facts | each fact's derivation and type, the card spelling, the per-seat `stacks` and the seat fact's range, the derived hand-class fact, what the readout may never expose |
| `episode.md` | `play_hand` | the policy protocol, the shape's seating and its refusals, the episode record, the decision records, where the reward lands |
| `equity.md` | the equity question | what the answer is conditional on, where the seat count comes from, the opposition on a shape with more seats, and hand-or-readout equivalence |
| `equity-sample.md` | the equity sample | the unseen deck, the `calculate_equities` call, the two range forms, the library's tie share, and the five things that bind the implementation |
| `stream.md` | the global `random` stream | one seeding point, `equity`'s save/seed/restore, and the measured cost |
| `errors.md` | refusals | the error hierarchy (including `InvalidSeating`), and what is deliberately *not* refused |
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
    payoffs(hand)                                         -> Mapping[int, int]   (one entry per seat)
    play_hand(seed, seat0_policy=None, seat1_policy=None, shape=None, seats=None) -> Mapping
    equity(decision, seed, samples)                       -> float

Every rule that holds of all ten is `docs/L2/engine/surface.md` §1 and is not restated here: an
invalid argument raises an error naming the violated contract — no coercion, no substituted default,
no swallowed error, no partial record; no entry point mutates the hand it is given; `new_hand` is the
single seeding point and every other call hands the global `random` stream back as it found it. The
shape is reached only through the optional argument of `new_hand`, `game_config` and `play_hand`, whose
absence is the default shape — never beside a hand — and a shape's **seating** through `play_hand`'s own
optional `seats`, whose absence is the two positional policies (`surface.md` §1, §3, §4, §10, §12,
`seats.md` §4).

A `Hand`, the error classes, the card spelling helper, the constants, the shape rows and every helper
below an entry point are **not** surface (`e2e-surface.md` §1): an L4 change to any of them
is not a contract change, and the unit battery drives the ten names only — **ten**, because D-33 added
no name: the map stays at 50 endpoints and `engine` still holds 10 of them (`seats.md` §6, `layout.md` §2).

## 4. Two decisions a later module must not re-derive

1. **One spelling of a card and of an action exists in the project, and it is this module's**
   (`e2e-surface.md` §2, `features/encodings.md` reads it). A card is a two-character plain `str` such
   as `"Td"`; an action is one of the plain `str`s its shape declares — three in the fixed-limit shape,
   six in **both** no-cap shapes, the six-seat one included (`config.md` §2, §6). Neither is a
   `pokerkit` class and neither needs the library read: `features` parses the spelling (`readout.md` §3,
   `actions.md` §2).
2. **The engine's seat 0 is the button, in every shape.** It is `pokerkit`'s player 1 on a two-seat shape
   and player `seats − 1` on a shape with more seats — `seat_map(seats) = ((s - 1) % seats)`: `(1, 0)` at
   two seats and `(5, 0, 1, 2, 3, 4)` at six (`hand.md` §3, `seats.md` §3). The mapping is fixed there and
   every per-seat fact (stacks, payoffs, the readout's `seat`, a decision's `seat`, the seat a history
   entry names) is expressed in *engine seat order*. A module that reads a `pokerkit` index directly
   will invert the button — and on six seats it will also read the wrong player's blind.
