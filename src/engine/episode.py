"""`play_hand`: one whole hand as a record (docs/L3/engine/episode.md).

The policy protocol is a callable taking `(readout, legal)` and returning one member
of `legal`; the engine knows no builder by name, does not inspect the policy, and
lets the policy's own exception propagate unchanged (episode.md §1, §4, G8).  One
hand is in flight and no re-entry: `play_hand` deals through `new_hand` and seeds
nothing itself (episode.md §2, D-16).

The **seating** is the shape's.  A shape with more than two seats seats more than two
policies, so the seating is an optional `seats` argument — the shape's whole seating,
in seat order — and its absence is exactly the two positional policies this entry
point has always played (seats.md §4, e2e-surface.md §3.1).  A seating of the wrong
length, or one handed beside two positional policies, is refused by name and never
truncated or padded (seats.md §4, errors.md §2).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .actions import apply_action, raise_amount, raise_interval
from .config import SEAT_COUNT, require_shape, seat_count
from .errors import InvalidAction, InvalidPolicy, InvalidSeating
from .hand import is_terminal, new_hand, payoffs, validate_seed
from .readout import readout

#: The two positional policies' argument names, which is what a two-policy refusal names
#: (episode.md §1, surface.md §10).
POSITIONAL = ("seat0_policy", "seat1_policy")


def play_hand(
    seed: int,
    seat0_policy=None,
    seat1_policy=None,
    shape=None,
    seats=None,
) -> dict:
    """One episode: its seed, its decisions and the hand's payoffs (episode.md §3).

    `shape` is optional and absence is the default shape, so today's call plays today's
    hand (surface.md §10, shapes.md §3).  Each decision is created with reward 0; at the
    end each seat's **last** decision takes that seat's net chip delta and every other
    decision stays 0, so a hand carries at most one non-zero reward per seat and it is
    the hand's outcome (episode.md §3, ASM-12, guardrails.md G9).

    With the optional `seats` argument the two positional policies are **absent** and the
    sequence is the shape's whole seating, one policy per seat in seat order, so a
    six-seat hand is six policies of which one is the learner's (seats.md §4).  A call
    naming neither form, a `seats` whose length is not the shape's seat count, and a
    `seats` given beside a positional policy are each refused by name (seats.md §4,
    e2e-surface.md §3.1).

    Each decision carries the three amount facts beside its five:
    `minimum`/`maximum`, the bounds of the legal raise interval at that decision and
    `None` exactly when no raise was legal, and `amount`, the raise-to the engine
    resolved — `None` whenever the chosen descriptor was not a raise (records.md §5,
    sizing.md §2).  `seat` is the readout's own seat fact, so a seat index means the
    same thing in the record as in the facts (records.md §5, seats.md §3).
    """
    validate_seed(seed)
    name = require_shape(shape, "play_hand")
    policies, labels = _seating(name, seat0_policy, seat1_policy, seats)

    hand = new_hand(seed, name)
    decisions = []
    while not is_terminal(hand):
        facts = readout(hand)
        legal = facts["legal"]
        seat = facts["seat"][0]
        action = policies[seat](facts, legal)
        if action not in legal:
            raise InvalidAction(
                "play_hand(%s): the policy returned %r, which is not legal at this decision"
                % (labels[seat], action)
            )
        bounds = raise_interval(hand)
        decisions.append(
            {
                "seat": facts["seat"],
                "readout": facts,
                "legal": legal,
                "action": action,
                "reward": 0,
                "amount": raise_amount(hand, action),
                "minimum": None if bounds is None else bounds[0],
                "maximum": None if bounds is None else bounds[1],
            }
        )
        hand = apply_action(hand, action)

    outcome = payoffs(hand)
    last = {}
    for position, decision in enumerate(decisions):
        last[decision["seat"][0]] = position
    for seat, position in last.items():
        decisions[position]["reward"] = outcome[seat]
    return {"seed": seed, "decisions": decisions, "payoffs": outcome}


def _seating(name: str, seat0_policy, seat1_policy, seats):
    """The policy of every seat in seat order, and the argument name to refuse with.

    The two forms are exclusive: the positional pair is what this entry point has always
    taken, and it is what an absent `seats` still means, so a two-seat caller changes
    nothing (e2e-surface.md §3.1, seats.md §4).  Every refusal happens before the deal, so
    a refused call cannot move the global stream (hand.md §2).
    """
    count = seat_count(name)
    if seats is None:
        for label, policy in zip(POSITIONAL, (seat0_policy, seat1_policy)):
            if not callable(policy):
                raise InvalidPolicy(
                    "play_hand(%s): the policy must be callable, got %s"
                    % (label, type(policy).__name__)
                )
        if count != SEAT_COUNT:
            raise InvalidSeating(
                "play_hand(shape): the shape %r seats %d, so its hand needs %d policies "
                "and the two positional policies seat %d; the seating is the optional "
                "`seats` argument, one policy per seat in seat order (seats.md §4)"
                % (name, count, count, SEAT_COUNT)
            )
        return (seat0_policy, seat1_policy), POSITIONAL
    if seat0_policy is not None or seat1_policy is not None:
        raise InvalidSeating(
            "play_hand(seats): the seating is given, so the two positional policies "
            "seat0_policy and seat1_policy are absent, and one of them was given; the "
            "seating and the positional pair are exclusive (seats.md §4, "
            "e2e-surface.md §3.1)"
        )
    if isinstance(seats, (str, bytes, Mapping)) or not isinstance(seats, Iterable):
        raise InvalidSeating(
            "play_hand(seats): the seating must be an ordered sequence of one policy per "
            "seat, got %s (seats.md §4)" % type(seats).__name__
        )
    ordered = tuple(seats)
    if len(ordered) != count:
        raise InvalidSeating(
            "play_hand(seats): the shape %r seats %d, so the seating must hold %d "
            "policies in seat order, got %d (seats.md §4)" % (name, count, count, len(ordered))
        )
    labels = tuple("seats[%d]" % position for position in range(count))
    for label, policy in zip(labels, ordered):
        if not callable(policy):
            raise InvalidPolicy(
                "play_hand(%s): the policy must be callable, got %s"
                % (label, type(policy).__name__)
            )
    return ordered, labels
