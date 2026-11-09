"""The readout: the acting seat's eleven facts (docs/L3/engine/readout.md).

The information set is closed: exactly these eleven keys, derived from the state on
demand and never cached, and nothing of the opponent, the deck or the rung (D-3).
`readout` refuses a handle that is not a `Hand` and a hand that is over, because a
hand with no acting seat has no readout (readout.md §1).

The eleventh key, `hand_class`, is D-21's derived fact (ASM-30): the class of the
acting seat's best five-card hand of hole plus board, from `pokerkit`'s own
evaluator rather than a second one.  It is a function of `hole` and `board`, which
the readout already carries, so it widens no information set, and no encoding
carries it (readout.md §2, `features`'s `fields`).
"""

from __future__ import annotations

from pokerkit.hands import StandardHighHand
from pokerkit.lookups import Label

from .actions import legal_actions
from .cards import card_spelling
from .config import SEAT_COUNT, STREETS
from .hand import Hand, player_index, require_live_hand, seat_of

#: The nine hand classes, keyed by `pokerkit`'s own `Label` in its declaration order:
#: 0 high card, 1 one pair, 2 two pair, 3 three of a kind, 4 straight, 5 flush,
#: 6 full house, 7 four of a kind, 8 straight flush (readout.md §2, ASM-30).  The
#: order is read off `Label` and never written down a second time.
CLASS_OF = {label: position for position, label in enumerate(Label)}


def readout(hand: Hand) -> dict:
    """The eleven facts of the acting seat at this decision (readout.md §2).

    A fresh mapping each call whose lists are copies, so a caller cannot reach back
    into the handle through what it was handed (readout.md §1, guardrails.md G1).
    """
    require_live_hand(hand, "readout")
    return facts(hand)


def hand_class(hole, board):
    """The class of the best five-card hand of `hole` plus `board`, or `None` (ASM-30).

    `None` while fewer than five cards are known — before the flop, where no
    five-card hand exists — and an integer 0-8 from the flop onward.
    `StandardHighHand.from_game_or_none` is the library's own best-hand search: it
    tries the C(n, 5) five-card combinations and keeps the greatest, so this module
    evaluates no hand itself (readout.md §2).
    """
    best = StandardHighHand.from_game_or_none(hole, board)
    if best is None:
        return None
    return CLASS_OF[best.entry.label]


def facts(hand: Hand) -> dict:
    """The eleven-key mapping, derived from the state (readout.md §2).

    The caller has already established that the handle is live; this derivation
    reads the state and adds nothing (D-3).
    """
    state = hand._state
    seat = seat_of(state.actor_index)
    hole_cards = state.hole_cards[player_index(seat)]
    # The board is `get_board_cards(0)`, never `board_cards[0]`, which is one row per
    # dealing operation (platform.md §2, readout.md §2).  It is materialised once, because
    # the library yields it as an iterator and two facts read it: the `board` spelling and
    # the eleventh fact, which evaluates the best hand over exactly these cards.
    board_cards = tuple(state.get_board_cards(0))
    return {
        # The street is `STREETS[street_index]`, never `streets.index(state.street)`:
        # the turn and river `Street` values are equal by value (platform.md §3).
        "street": STREETS[state.street_index],
        "seat": (seat, seat == 0),
        "hole": tuple(card_spelling(card) for card in hole_cards),
        "board": tuple(card_spelling(card) for card in board_cards),
        "stacks": tuple(
            state.stacks[player_index(index)] for index in range(SEAT_COUNT)
        ),
        "pot": state.total_pot_amount,
        "to_call": state.checking_or_calling_amount,
        "limit": (
            state.street.min_completion_betting_or_raising_amount,
            state.completion_betting_or_raising_count,
        ),
        "history": list(hand._history),
        "legal": legal_actions(hand),
        "hand_class": hand_class(hole_cards, board_cards),
    }
