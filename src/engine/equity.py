"""The equity question (docs/L3/engine/equity.md).

The answer is conditional on what the acting seat has seen: the seat's two cards and
the board, the unseen deck's every two-card combination as a uniform opponent range,
and nothing else — not the pot, not the stacks, not the street (equity.md §2).  The
hand path reads the board as `readout` does (`get_board_cards(0)`), so a hand and its
readout hand back the same ordered pair of cards and answer the same number
(equity.md §2, guardrails.md G10).
"""

from __future__ import annotations

import itertools
import random
from collections.abc import Iterable, Mapping

from pokerkit.analysis import calculate_equities
from pokerkit.hands import StandardHighHand
from pokerkit.utilities import Deck

from .cards import is_card_spelling, parse_card
from .errors import InvalidDecision, InvalidSamples
from .hand import Hand, player_index, seat_of, validate_seed

HOLE_DEALING_COUNT = 2
BOARD_DEALING_COUNT = 5
HAND_TYPES = (StandardHighHand,)
HOLE_CARDS = 2
BOARD_CARDS = (0, 3, 4, 5)

_MALFORMED = (
    "equity(decision): a readout must carry two distinct cards in 'hole' "
    "and 0, 3, 4 or 5 distinct cards in 'board'"
)


def equity(decision, seed: int, samples: int) -> float:
    """The acting seat's share of the pot against a uniform opponent (equity.md §3).

    A query and not a step: it neither advances nor mutates the hand, and it hands the
    global stream back in the state it found it — saving it, seeding it with the
    caller's seed so the estimate is a function of `(decision, seed, samples)`, and
    restoring it in a `finally` (stream.md §1, surface.md §11).
    """
    hole, board = _cards_of(decision)
    validate_seed(seed, "equity")
    if not isinstance(samples, int) or isinstance(samples, bool) or samples < 1:
        raise InvalidSamples(
            "equity(samples): the sample count must be a positive int, got %r" % (samples,)
        )

    # Built in `Deck.STANDARD` order over the unseen cards, never from a `set`
    # iteration, so the sample universe is the same on every call (equity.md §3).
    unseen = [card for card in Deck.STANDARD if card not in set(hole + board)]
    opponent_range = [[first, second] for first, second in itertools.combinations(unseen, 2)]

    saved = random.getstate()
    try:
        random.seed(seed)
        values = calculate_equities(
            ([list(hole)], opponent_range),
            list(board),
            HOLE_DEALING_COUNT,
            BOARD_DEALING_COUNT,
            Deck.STANDARD,
            HAND_TYPES,
            sample_count=samples,
        )
    finally:
        random.setstate(saved)
    return float(values[0])


def _cards_of(decision):
    """The acting seat's two cards and the board, from a hand or its readout."""
    if isinstance(decision, Hand):
        state = decision._state
        if not state.status:
            raise InvalidDecision(
                "equity(decision): the hand is over, so there is no acting seat"
            )
        seat = seat_of(state.actor_index)
        return (
            tuple(state.hole_cards[player_index(seat)]),
            tuple(state.get_board_cards(0)),
        )
    if isinstance(decision, Mapping):
        return _cards_of_readout(decision)
    raise InvalidDecision(
        "equity(decision): the decision must be a hand or its readout, got %s"
        % type(decision).__name__
    )


def _cards_of_readout(readout: Mapping):
    """The two facts the question needs, parsed back to cards (equity.md §1, §2).

    A mapping is a decision only when `hole` is exactly two card strings of the
    declared spelling and `board` is 0, 3, 4 or 5 of them, all distinct; extra keys
    beside those two facts are ignored (errors.md §4).  One card named twice is refused
    here and not sampled: the library drops a selection whose cards collide and then
    draws from an empty universe, so a duplicate would surface as its `IndexError`
    rather than as this module's refusal (equity.md §1).
    """
    hole = _spelled_cards(readout.get("hole"))
    board = _spelled_cards(readout.get("board"))
    if (
        hole is None
        or board is None
        or len(hole) != HOLE_CARDS
        or len(board) not in BOARD_CARDS
        or len(set(hole + board)) != len(hole) + len(board)
    ):
        raise InvalidDecision(_MALFORMED)
    return (
        tuple(parse_card(card) for card in hole),
        tuple(parse_card(card) for card in board),
    )


def _spelled_cards(value):
    """The cards a sequence of spellings names, or `None` when it is no such thing."""
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Iterable):
        return None
    cards = tuple(value)
    if not all(is_card_spelling(card) for card in cards):
        return None
    return cards
