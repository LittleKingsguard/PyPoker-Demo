"""The readout: the acting seat's ten facts (docs/L3/engine/readout.md).

The information set is closed: exactly these ten keys, derived from the state on
demand and never cached, and nothing of the opponent, the deck or the rung (D-3).
`readout` refuses a handle that is not a `Hand` and a hand that is over, because a
hand with no acting seat has no readout (readout.md §1).
"""

from __future__ import annotations

from .actions import legal_actions
from .cards import card_spelling
from .config import SEAT_COUNT, STREETS
from .hand import Hand, player_index, require_live_hand, seat_of


def readout(hand: Hand) -> dict:
    """The ten facts of the acting seat at this decision (readout.md §2).

    A fresh mapping each call whose lists are copies, so a caller cannot reach back
    into the handle through what it was handed (readout.md §1, guardrails.md G1).
    """
    require_live_hand(hand, "readout")
    return facts(hand)


def facts(hand: Hand) -> dict:
    """The ten-key mapping, derived from the state (readout.md §2).

    The caller has already established that the handle is live; this derivation
    reads the state and adds nothing (D-3).
    """
    state = hand._state
    seat = seat_of(state.actor_index)
    return {
        # The street is `STREETS[street_index]`, never `streets.index(state.street)`:
        # the turn and river `Street` values are equal by value (platform.md §3).
        "street": STREETS[state.street_index],
        "seat": (seat, seat == 0),
        "hole": tuple(
            card_spelling(card) for card in state.hole_cards[player_index(seat)]
        ),
        # The board is `get_board_cards(0)`, never `board_cards[0]`, which is one row
        # per dealing operation (platform.md §2, readout.md §2).
        "board": tuple(card_spelling(card) for card in state.get_board_cards(0)),
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
    }
