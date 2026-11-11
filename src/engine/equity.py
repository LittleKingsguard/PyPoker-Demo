"""The equity question (docs/L3/engine/equity.md).

The answer is conditional on what the acting seat has seen: the seat's two cards and
the board, the unseen deck's every two-card combination as a uniform opponent range,
and nothing else — not the pot, not the stacks, not the street (equity.md §2).  The
hand path reads the board as `readout` does (`get_board_cards(0)`), so a hand and its
readout hand back the same ordered pair of cards and answer the same number
(equity.md §2, guardrails.md G10).

A shape with more than two seats is asked a **multi-way** question: the opponents are
the other seats', each one's hand a uniform draw from what the acting seat has not
seen, so a six-seat call is six-way (seats.md §2, e2e-surface.md §3.1).  `pokerkit`'s
one hole range per player is the tool for both: an explicit enumeration of the unseen
two-card combinations for the two-seat question, which is what this module has always
answered, and one empty range per opponent — the form `calculate_hand_strength` builds
— for a shape with more seats, where the enumeration is combinatorially out of reach
and the library deals the opponents' cards at random (analysis.py:225, :311, :340,
:404-406).
"""

from __future__ import annotations

import itertools
import random
from collections.abc import Iterable, Mapping

from pokerkit.analysis import calculate_equities
from pokerkit.hands import StandardHighHand
from pokerkit.utilities import Deck

from .cards import is_card_spelling, parse_card
from .config import SEAT_COUNT, seat_count
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
    """The acting seat's share of the pot against uniform opponents (equity.md §3).

    A query and not a step: it neither advances nor mutates the hand, and it hands the
    global stream back in the state it found it — saving it, seeding it with the
    caller's seed so the estimate is a function of `(decision, seed, samples)`, and
    restoring it in a `finally` (stream.md §1, surface.md §11).

    The **opponent count** is the shape's, so a six-seat decision is asked six-way and
    its answer is the acting seat's share against five random hands (seats.md §2).
    """
    hole, board, seats = _cards_of(decision)
    validate_seed(seed, "equity")
    if not isinstance(samples, int) or isinstance(samples, bool) or samples < 1:
        raise InvalidSamples(
            "equity(samples): the sample count must be a positive int, got %r" % (samples,)
        )

    hole_ranges = _hole_ranges(hole, board, seats)

    saved = random.getstate()
    try:
        random.seed(seed)
        values = calculate_equities(
            hole_ranges,
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


def _hole_ranges(hole, board, seats: int):
    """One hole range per player in the pot, the acting seat's first (equity.md §3).

    The two-seat question enumerates the unseen deck's every two-card combination, in
    `Deck.STANDARD` order and never from a `set` iteration, so its sample universe is the
    same on every call and its answer is the one this module has always given
    (equity.md §3, shapes.md §5).

    A shape with more seats cannot enumerate — six players would be the product of five
    combinations over a fifty-card deck — so each opponent gets a range list holding one
    **empty** range, which is the form `calculate_hand_strength` builds
    (`[[] for _ in range(player_count - 1)]`, analysis.py:404-406).  `calculate_equities`
    takes the product of the range lists and then fills every hole card a selection left
    out by sampling from what the selection did not name (`analysis.py:311-316`, `:157-175`),
    so an empty range is "deal this player's cards at random from what is left" — and a
    truly **empty range list** would make the product empty and raise the library's own
    `IndexError` instead, which is why the range list holds one empty range and not none
    (seats.md §2).
    """
    if seats == SEAT_COUNT:
        unseen = [card for card in Deck.STANDARD if card not in set(hole + board)]
        return (
            [list(hole)],
            [[first, second] for first, second in itertools.combinations(unseen, 2)],
        )
    return [[list(hole)]] + [[[]] for _ in range(seats - 1)]


def _cards_of(decision):
    """The acting seat's two cards, the board and the seat count, from a hand or readout."""
    if isinstance(decision, Hand):
        state = decision._state
        if not state.status:
            raise InvalidDecision(
                "equity(decision): the hand is over, so there is no acting seat"
            )
        seats = seat_count(decision._shape)
        seat = seat_of(state.actor_index, seats)
        return (
            tuple(state.hole_cards[player_index(seat, seats)]),
            tuple(state.get_board_cards(0)),
            seats,
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
        _opponents_of_readout(readout),
    )


def _opponents_of_readout(readout: Mapping) -> int:
    """The seat count a readout declares, read off the one fact whose length is it.

    `stacks` is one entry per seat in seat order (seats.md §3), so its length is the
    number of seats the decision was taken at and the number of opponents is that less
    one.  A mapping that carries no such sequence is a two-seat decision, which is what
    an absent shape reads as and what this entry point has always assumed
    (shapes.md §3, seats.md §2).
    """
    stacks = readout.get("stacks")
    if isinstance(stacks, (str, bytes, Mapping)) or not isinstance(stacks, Iterable):
        return SEAT_COUNT
    counted = len(tuple(stacks))
    return counted if counted > SEAT_COUNT else SEAT_COUNT


def _spelled_cards(value):
    """The cards a sequence of spellings names, or `None` when it is no such thing."""
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Iterable):
        return None
    cards = tuple(value)
    if not all(is_card_spelling(card) for card in cards):
        return None
    return cards
