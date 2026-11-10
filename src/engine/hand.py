"""The hand: the handle, the seat map, the seeding point and the advance
(docs/L3/engine/hand.md, advance.md).

A `Hand` is an opaque handle over a `pokerkit` state, this project's public history and
the name of the shape it is dealt from, and nothing in it is surface (hand.md §1,
guardrails.md G11).  The module keeps no state of its own, so two handles are
independent (ASM-2).
"""

from __future__ import annotations

import copy
import random

from pokerkit import Automation, FixedLimitTexasHoldem, NoLimitTexasHoldem

from .config import SEAT_COUNT, STREETS, require_shape, shape_row
from .errors import InvalidHand, InvalidSeed

# The automations make the betting decisions the only manual operations: hole cards
# exist from the first decision on and each street's board is dealt as the previous
# street's betting closes (hand.md §2, strata/platform.md).
AUTOMATIONS = (
    Automation.ANTE_POSTING,
    Automation.BET_COLLECTION,
    Automation.BLIND_OR_STRADDLE_POSTING,
    Automation.CARD_BURNING,
    Automation.HOLE_DEALING,
    Automation.BOARD_DEALING,
    Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
    Automation.HAND_KILLING,
    Automation.CHIPS_PUSHING,
    Automation.CHIPS_PULLING,
)

# engine seat -> pokerkit player index.  pokerkit's heads-up blinds are reversed
# twice, so engine seat 0 (the button, posts 1, acts first pre-flop) is pokerkit
# player 1 (hand.md §3, guardrails.md G2).
SEAT_TO_PLAYER = (1, 0)


def player_index(seat: int) -> int:
    """The `pokerkit` player index of an engine seat (hand.md §3)."""
    return SEAT_TO_PLAYER[seat]


def seat_of(index: int) -> int:
    """The engine seat of a `pokerkit` player index (hand.md §3)."""
    return 1 - index


class Hand:
    """An opaque handle: the state, the public history and the shape (hand.md §1)."""

    __slots__ = ("_state", "_history", "_shape")

    def __init__(self, state, history: tuple[str, ...], shape: str) -> None:
        self._state = state
        self._history = history
        self._shape = shape

    def __repr__(self) -> str:
        """Constant, because nothing in a handle is surface (hand.md §1)."""
        return "<engine.Hand>"


def validate_seed(seed, entry_point: str = "new_hand") -> None:
    """Refuse a seed that is not an `int` and not a `bool` (hand.md §2, errors.md §3).

    `bool` is refused although it is an `int` subclass: a recorded seed is an
    integer, and `True` as a seed is a defect a test can see (protocol.md §2).
    """
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise InvalidSeed(
            "%s(seed): the seed must be an int, got %s"
            % (entry_point, type(seed).__name__)
        )


def create_state(row: dict):
    """The `pokerkit` state one row of the catalogue declares (config.md §2).

    The two bet structures are the two the catalogue declares.  The fixed-limit row is
    created exactly as this module always created it, so the default shape's deals are
    unchanged card for card (shapes.md §5).  A row with no fixed bet hands `pokerkit` the
    big blind as its minimum bet and carries no cap, which is what makes a legal amount
    anything up to the acting seat's stack (shapes.md §2, sizing.md §2).
    """
    blinds = tuple(row["blinds"])
    if row["bet_structure"] == "fixed-limit":
        return FixedLimitTexasHoldem.create_state(
            AUTOMATIONS,
            True,  # ante_trimming_status
            0,  # raw_antes
            blinds,  # raw_blinds_or_straddles
            row["small_bet"],
            row["big_bet"],
            row["starting_stack"],  # raw_starting_stacks
            SEAT_COUNT,  # player_count
        )
    return NoLimitTexasHoldem.create_state(
        AUTOMATIONS,
        True,  # ante_trimming_status
        0,  # raw_antes
        blinds,  # raw_blinds_or_straddles
        blinds[1],  # min_bet: the big blind, as the no-cap shape declares it
        row["starting_stack"],  # raw_starting_stacks
        SEAT_COUNT,  # player_count
    )


def new_hand(seed: int, shape=None) -> Hand:
    """Deal one hand from `seed` on `shape`, the project's only seeding point (hand.md §2).

    `shape` is optional and **absence is the default shape**, so today's call deals
    today's hand (surface.md §4, shapes.md §3).  Both refusals happen before
    `random.seed`, so a refused call cannot move the stream.  `pokerkit` shuffles the
    deck inside `create_state`, so seeding the global stream immediately before creation
    fixes the whole deck order (ASM-2).
    """
    validate_seed(seed)
    name = require_shape(shape, "new_hand")
    row = shape_row(name)
    random.seed(seed)
    return Hand(create_state(row), (), name)


def advance(hand: Hand, action: str, amount=None) -> Hand:
    """The hand one validated action on, at `amount` for a raise (advance.md §1).

    The state is copied first and the action applied to the copy, so the argument
    handle is untouched by construction (guardrails.md G1).  The global stream is
    saved and restored because `pokerkit` draws while advancing (platform.md §4),
    and a step must hand the caller's stream back as it found it (stream.md §1).

    `amount` is the raise-to the engine resolved for the descriptor, and is `None` for
    a fold and for a check/call.  It is `None` for the fixed-limit `raise` too, because
    that shape's raise is `pokerkit`'s own minimum completion, exactly as before
    (actions.md §2).
    """
    saved = random.getstate()
    try:
        state = copy.deepcopy(hand._state)
        operation = _apply_one(state, action, amount)
    finally:
        random.setstate(saved)
    entry = _history_entry(hand._state, action, operation)
    return Hand(state, hand._history + (entry,), hand._shape)


def _apply_one(state, action: str, amount=None):
    """The three-method idiom: a `can_*` predicate, then the method (stepping.md §2).

    The predicate is the caller's: `apply_action` validates the descriptor against
    the argument hand's legal set before the state is copied.  `complete_bet_or_raise_to`
    is called with no argument for the fixed-limit shape, because in fixed-limit games
    `pokerkit` resolves that to the minimum legal completion, and with the resolved
    amount for a sized shape (actions.md §2, stepping.md §2).
    """
    if action == "fold":
        return state.fold()
    if action == "check-call":
        return state.check_or_call()
    if amount is None:
        return state.complete_bet_or_raise_to()
    return state.complete_bet_or_raise_to(amount)


def _history_entry(state, action: str, operation) -> str:
    """One entry per applied action, built from the pre-step state (advance.md §2).

    `<amount>` is the value `pokerkit` reports on the operation it returns: the chips
    added for a call, the total street bet level for a raise.  `<index>` is the
    engine seat, never a `pokerkit` index.  A card never appears here.
    """
    street = STREETS[state.street_index]
    seat = seat_of(state.actor_index)
    if action == "fold":
        return "%s seat %d folds" % (street, seat)
    if action == "check-call":
        if operation.amount == 0:
            return "%s seat %d checks" % (street, seat)
        return "%s seat %d calls %d" % (street, seat, operation.amount)
    return "%s seat %d raises to %d" % (street, seat, operation.amount)


def require_hand(value, entry_point: str, argument: str = "hand") -> Hand:
    """The handle, or the refusal its contract states (errors.md §3)."""
    if not isinstance(value, Hand):
        raise InvalidHand(
            "%s(%s): the argument must be a hand returned by new_hand, got %s"
            % (entry_point, argument, type(value).__name__)
        )
    return value


def require_live_hand(value, entry_point: str, argument: str = "hand") -> Hand:
    """A handle with an acting seat, or the refusal (errors.md §3, readout.md §1)."""
    hand = require_hand(value, entry_point, argument)
    if not hand._state.status:
        raise InvalidHand(
            "%s(%s): the hand is over, so there is no acting seat"
            % (entry_point, argument)
        )
    return hand


def is_terminal(hand: Hand) -> bool:
    """Whether the hand is over, as a real `bool` (hand.md §5, surface.md §8)."""
    require_hand(hand, "is_terminal")
    return bool(not hand._state.status)


def payoffs(hand: Hand) -> dict[int, int]:
    """The net chip delta per engine seat of a completed hand (hand.md §5).

    A running hand has paid nothing and is refused (surface.md §9).  A split is a
    zero payoff and is legal (ASM-12).
    """
    require_hand(hand, "payoffs")
    if hand._state.status:
        raise InvalidHand("payoffs(hand): the hand is still running, so it has paid nothing")
    return {seat: hand._state.payoffs[player_index(seat)] for seat in range(SEAT_COUNT)}
