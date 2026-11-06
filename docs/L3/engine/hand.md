# engine — the hand

- **Owner:** the hand’s data structure and its wrapper over a `pokerkit` state: the handle, `new_hand` (the project’s single seeding point), the **seat mapping**, and the two entry points that are a pure function of a finished or running hand (`is_terminal`, `payoffs`)
- **Ceiling:** 110 lines. At the ceiling, split by owner — never append

## 1. The value

    class Hand:                    # src/engine/hand.py — NOT surface
        _state: pokerkit.state.State
        _history: tuple[str, ...]  # one entry per applied action, oldest first (advance.md §2)

A `Hand` is an **opaque handle**: no public attribute, no mapping access, no iterator, no `__eq__`
(identity equality only), and a constant `__repr__` such as `<engine.Hand>`. A caller only ever
passes it back; nothing in it is surface (`e2e-surface.md` §1, brief §5).

The module keeps **no state of its own**: the whole state of a hand lives in its handle, so two
handles are independent and a hand dealt earlier is unaffected by a hand dealt later (`L2
environment.md` §1, ASM-2). No module-level cache, no "current hand", no registry.

Internally a `Hand` is exactly two things: the `pokerkit` state and this project’s public history.
Everything a readout needs is derived from the state on demand and never cached in the handle — a
cache would be a second source of truth that a `deepcopy` could desynchronise.

## 2. `new_hand(seed)`

    def new_hand(seed: int) -> Hand

    refuse unless isinstance(seed, int) and not isinstance(seed, bool)      # errors.md, InvalidSeed
    random.seed(seed)                       # THE single seeding point of the project (ASM-2)
    state = FixedLimitTexasHoldem.create_state(
                AUTOMATIONS, True, 0, (1, 2), 2, 4, 20, 2,
            )                               # automations, ante_trimming, antes, blinds, small, big,
                                            # starting stacks, player count
    return Hand(state, ())

Why this is enough: `pokerkit` shuffles the deck inside `create_state` (`state.py:1241`,
`shuffle(self.deck_cards)`, `from random import shuffle`), so seeding the global stream immediately
before creation fixes the **whole** deck order, and every later card comes from that order — a step
consumes a few incidental draws (the reserved-card shuffle of `platform.md` §4) but cannot change the
deal, and `advance` hands those draws back (`advance.md` §1).

`bool` is refused although `bool` is an `int` subclass: a recorded seed is an integer, and `True` as
a seed is a defect a test can see (`protocol.md` §2). The refusal happens **before** `random.seed`,
so a refused call cannot move the stream.

`AUTOMATIONS` is the module’s constant: `ANTE_POSTING, BET_COLLECTION, BLIND_OR_STRADDLE_POSTING,
CARD_BURNING, HOLE_DEALING, BOARD_DEALING, HOLE_CARDS_SHOWING_OR_MUCKING, HAND_KILLING,
CHIPS_PUSHING, CHIPS_PULLING`. It is what makes the *betting decisions* the only manual operations:
hole cards exist from the first decision on, and each street’s board cards are dealt automatically as
the previous street’s betting closes (`strata/platform.md`).

## 3. The seat mapping — the single most dangerous detail

`pokerkit` reverses the blinds for `player_count == 2` (`state.py:3336-3339`, the effective blind is
`abs(self.blinds_or_straddles[not player_index])`) and `_begin_betting` reverses them again when it
computes the pre-flop opener (`state.py:4203-4212`). With `raw_blinds_or_straddles=(1, 2)` and two
players the consequence is fixed, and it is the opposite of this project’s contract:

| | `pokerkit` index 1 | `pokerkit` index 0 |
|---|---|---|
| posts | the small blind 1 | the big blind 2 |
| acts first | pre-flop | flop, turn, river |
| chips behind at the first decision | 19 | 18 |

`docs/L2/engine/environment.md` §1 requires **seat 0 to be the button**: it posts the small blind of
1, it acts first pre-flop, and seat 1 acts first on every later street. Therefore

    SEAT_TO_PLAYER = (1, 0)          # engine seat -> pokerkit player index
    player_index(seat) = 1 - seat    # helper, not surface
    seat_of(player_index) = 1 - player_index

**Every** per-seat fact is translated exactly once, where it is read: `stacks`, `payoffs`, `hole`, the
readout’s `seat` fact, the acting seat of a decision, and the policy `play_hand` calls. No `pokerkit`
index ever reaches a caller. Do not "simplify" this by passing `(2, 1)` to `create_state`: the library
reverses an already-reversed pair again and the button lands back on the wrong seat
(`guardrails.md` G2).

## 4. The first decision, as a check on the whole mapping

At any seed the first decision must read: `street == "preflop"`, `pot == 3`, `stacks == (19, 18)`,
`to_call == 1`, `seat == (0, True)`, `len(hole) == 2`, `board == ()`, `history == []`. If a build
reads `stacks == (18, 19)` or `seat == (1, False)`, the seat map is inverted and nothing else in the
module can be trusted (`readout.md` §2).

Conservation, asserted at every decision: `pot + sum(stacks) == 40` (`L2 environment.md` §1) —
committed chips sit in the pot, never in a stack, and `state.total_pot_amount` includes the current
street’s outstanding bets (`state.py:2601-2606`).

## 5. `is_terminal` and `payoffs`

    def is_terminal(hand: Hand) -> bool          # bool(), never a truthy object
    def payoffs(hand: Hand) -> dict[int, int]    # {0: p0, 1: p1} — engine seat order

`is_terminal` is `bool(not state.status)` and refuses only a value that is not a `Hand`: every handle
states whether it is over, a freshly dealt one included (`L2 surface.md` §8). The e2e edge asserts
`assertIsInstance(..., bool)`.

`payoffs` refuses a handle that is still running (`L2 surface.md` §9) and maps
`{seat: state.payoffs[player_index(seat)]}` — the net chip delta `stack - starting_stack`
(`state.py:1095-1103`) — so exactly two numbers, summing to zero, keyed by seat and carrying no
total. A split is a zero payoff and is legal (ASM-12).
