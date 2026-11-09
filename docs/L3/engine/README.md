# engine — module design (L3)

- **Layer:** L3 · **Module:** `engine` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-09
- **Realises:** `docs/L2/engine/surface.md` (the nine entry points) and `docs/L2/engine/environment.md` (the hand's life, the eleven facts, the episode, `equity`, seeding)
- **Reads:** `docs/L1/e2e-surface.md` §2–§3.1, §5, `docs/L1/folders.md` §3, `docs/L1/records.md` §1, §5, `docs/L1/module-map.md` §2–§3, `docs/L1/battery.md` §2–§4, `docs/L1/assumptions.md` (ASM-6, ASM-12, ASM-15, ASM-30), `strata/brief.md` §5, §7, `strata/decisions.md` (D-2, D-3, D-6, D-11, D-12, D-13, D-16, D-21), `strata/platform.md`
- **Ceiling:** 75 lines. At the ceiling, split by owner — never append
- **Implements:** `src/engine/` (written by L4, never by L3). `tests/engine/` is this design's unit battery

## 1. What this module is

`engine` is the fixed game of D-2 as an RL environment, and the bottom of the dependency map: it
imports `pokerkit` and the Python standard library and **nothing of this project** — no `features`,
no `agents`, no `evaluation`, no `training`, no `harness`, ever (`module-map.md` §3, D-1).

It deals a hand from a seed, says who acts and what that seat knows, says what that seat may do,
advances the hand by one chosen action, says when it is over, pays it, and answers the equity
question the oracle asks. It never encodes, never chooses, never records a result and never owns a
match (`docs/L2/engine/README.md` §3).

## 2. The documents, one per owner

| Document | Owner of that question | What it fixes |
|---|---|---|
| `hand.md` | the hand | the `Hand` handle over a `pokerkit` state, the **seat mapping**, `new_hand`'s seeding, `is_terminal`, `payoffs` |
| `advance.md` | one applied action | the advance by copy (and the rejected replay) |
| `history.md` | the public history | the one-entry-per-action rule, the entry grammar, the `<amount>` and `<index>` definitions, and why a card never appears |
| `actions.md` | the action vocabulary | the three descriptors: their type, value equality, stable text, and how `raise` resolves to the minimum legal completion |
| `stepping.md` | legality and the step | `legal_actions`’ order and refusals, `apply_action`’s validation and its three-method idiom |
| `readout.md` | the eleven facts | each fact's derivation and type, the card spelling, the seat fact's shape, the derived hand-class fact, what the readout may never expose |
| `episode.md` | `play_hand` | the policy protocol, the episode record, the decision records, where the reward lands |
| `equity.md` | the equity question | what the answer is conditional on, and hand-or-readout equivalence |
| `equity-sample.md` | the equity sample | the unseen deck, the `calculate_equities` call, the library's tie share, and the five things that bind the implementation |
| `stream.md` | the global `random` stream | one seeding point, `equity`'s save/seed/restore, and the measured cost |
| `errors.md` | refusals | the error hierarchy, and what is deliberately *not* refused |
| `messages.md` | the message grammar | the message form, the canonical message per refusal, and the two properties the battery relies on |
| `layout.md` | the files | the file layout of `src/engine/`, the nine exported names, what is not surface |
| `guardrails.md` | L4 | one note per risk this design identified, in the order they bite |
| `cost.md` | the cost of a hand | ASM-15's measurement question, what dominates it, the one knob that decides it, and what was not measured |
| `platform.md` | the platform | the measured `pokerkit` 0.7.7 facts this design rests on, and the three received claims they correct |

## 3. The nine names, and what is *not* a name

The `engine` package exports exactly nine entry points and adds, removes and renames none
(`e2e-surface.md` §1, D-12):

    game_config()                                        -> Mapping
    new_hand(seed)                                       -> Hand
    readout(hand)                                        -> Mapping          (eleven keys)
    legal_actions(hand)                                  -> tuple[str, ...]
    apply_action(hand, action)                           -> Hand
    is_terminal(hand)                                    -> bool
    payoffs(hand)                                        -> Mapping[int, int]
    play_hand(seed, seat0_policy, seat1_policy)          -> Mapping
    equity(hand_or_readout, seed, samples)               -> float

Every rule that holds of all nine is `docs/L2/engine/surface.md` §1 and is not restated here: an
invalid argument raises an error naming the violated contract, no coercion, no substituted default,
no swallowed error, no partial record; no entry point mutates the hand it is given; `new_hand` is the
single seeding point and every other call hands the global `random` stream back as it found it.

A `Hand`, the error classes, the card spelling helper, the constants and every helper below an entry
point are **not** surface (`e2e-surface.md` §1, brief §5): an L4 change to any of them is not a
contract change, and the unit battery drives the nine names only.

## 4. Two decisions a later module must not re-derive

1. **One spelling of a card and of an action exists in the project, and it is this module's**
   (`e2e-surface.md` §2, `features/encodings.md` reads it). A card is a two-character plain `str`
   such as `"Td"`; an action is one of the plain `str`s `"fold"`, `"check-call"`, `"raise"`. Neither
   is a class from `pokerkit` and neither needs `pokerkit` to be read: `features` parses the spelling,
   it does not import the library (`readout.md` §3, `actions.md` §2).
2. **The engine's seat 0 is `pokerkit`'s player 1.** The mapping is fixed in `hand.md` §3 and every
   per-seat fact (stacks, payoffs, the readout's `seat`, a decision's `seat`) is expressed in *engine
   seat order*. A module that reads a `pokerkit` index directly will invert the button.
