"""The action vocabulary, legality, and the step (docs/L3/engine/actions.md,
stepping.md).

A descriptor is a plain `str` and carries no amount.  The **fixed-limit** shape's `raise`
denotes the minimum legal completion for the decision it is applied to, which
fixed-limit makes unique (actions.md §1–§2).  The **no-cap** shape declares four raise
descriptors that partition the legal integer interval `[m, A]` between the minimum legal
raise-to `m` and the all-in raise-to `A`, and each resolves to its own maximum
(sizing.md §2).

The engine declares no legality of its own beyond `pokerkit`'s three `can_*` predicates
and the band arithmetic, so `legal_actions` and `apply_action` cannot disagree
(stepping.md §1).
"""

from __future__ import annotations

from .config import shape_row
from .errors import InvalidAction
from .hand import Hand, advance, require_live_hand

#: The two descriptors every declared shape carries, in index order 0 and 1
#: (e2e-surface.md §2, sizing.md §3).
BASES = ("fold", "check-call")

#: The four raise descriptors of a shape without a cap, in the index order the shape
#: declares: the measured price order, worst first (sizing.md §3, D-29).
SIZED = ("raise-quarter", "raise-half", "raise-all-in", "raise-minimum")


def vocabulary(hand: Hand) -> tuple[str, ...]:
    """The hand's own shape's descriptors, in that shape's index order (actions.md §1)."""
    return shape_row(hand._shape)["actions"]


def raise_interval(hand: Hand):
    """The bounds of the legal raise interval at this decision, or `None` (sizing.md §2).

    `(minimum, maximum)` are `pokerkit`'s own minimum and maximum
    completion-betting-or-raising-to amounts, so the engine derives no bound of its own.
    `None` exactly when no raise is legal at this decision — the cap is reached, the
    actor is already covered, or every other player has folded or gone all-in
    (stepping.md §1).
    """
    state = hand._state
    if not state.can_complete_bet_or_raise_to():
        return None
    minimum = state.min_completion_betting_or_raising_to_amount
    maximum = state.max_completion_betting_or_raising_to_amount
    if minimum is None or maximum is None:
        return None
    return (int(minimum), int(maximum))


def raise_amount(hand: Hand, descriptor):
    """The raise-to `descriptor` resolves to at this decision, or `None` if it is illegal.

    The bands are `sizing.md` §2's, in legal amounts rather than nominal pot fractions:
    with `L = A − m`, `raise-minimum` owns `{m}`, `raise-quarter` owns
    `(m, m + ⌊L/4⌋]`, `raise-half` owns `(m + ⌊L/4⌋, m + ⌊L/2⌋]` and `raise-all-in` owns
    `(m + ⌊L/2⌋, A]`, each resolving to its own band's maximum.  A band with no legal
    integer in it is **empty and masked out**, never collapsed onto its neighbour, so at
    `L = 0` only `raise-minimum` is legal and at `L = 1` only it and `raise-all-in`
    (sizing.md §2).

    The fixed-limit shape's `raise` is `pokerkit`'s minimum legal completion, which is
    what it always was (actions.md §2).
    """
    if descriptor in BASES:
        return None
    interval = raise_interval(hand)
    if interval is None:
        return None
    minimum, maximum = interval
    span = maximum - minimum
    if descriptor == "raise":
        return minimum
    if descriptor == "raise-minimum":
        return minimum
    if descriptor == "raise-quarter":
        return minimum + span // 4 if span // 4 >= 1 else None
    if descriptor == "raise-half":
        return minimum + span // 2 if span // 2 > span // 4 else None
    if descriptor == "raise-all-in":
        return maximum if maximum > minimum + span // 2 else None
    return None


def legal_actions(hand: Hand) -> tuple[str, ...]:
    """What the acting seat may do, in the shape's own index order (stepping.md §1).

    At most one entry per vocabulary index, no duplicates, never empty for a live hand,
    and deterministic.  `fold` appears only when `to_call` is non-zero because `pokerkit`
    refuses a fold when the actor's bet already equals the maximum bet, and a raise
    descriptor appears only when its band holds at least one legal amount (sizing.md §2).
    """
    require_live_hand(hand, "legal_actions")
    state = hand._state
    legal = []
    for descriptor in vocabulary(hand):
        if descriptor == "fold":
            if state.can_fold():
                legal.append(descriptor)
        elif descriptor == "check-call":
            if state.can_check_or_call():
                legal.append(descriptor)
        elif raise_amount(hand, descriptor) is not None:
            legal.append(descriptor)
    return tuple(legal)


def apply_action(hand: Hand, action: str) -> Hand:
    """The advanced hand, as a new handle (stepping.md §2, advance.md §1).

    Validation is against the argument handle's own shape's vocabulary and its legal
    tuple, by value, before any state is copied: an illegal descriptor is a contract
    violation and is never turned into a fold or a call on the violator's behalf
    (surface.md §7, D-2).

    A raise is resolved to an amount and passed to the step for a shape without a fixed
    bet; the fixed-limit shape's `raise` is left amount-less, so `pokerkit` resolves it
    exactly as it always did (actions.md §2).
    """
    require_live_hand(hand, "apply_action")
    declared = vocabulary(hand)
    if not isinstance(action, str) or action not in declared:
        raise InvalidAction(
            "apply_action(hand, action): %r is not one of %r" % (action, declared)
        )
    legal = legal_actions(hand)
    if action not in legal:
        raise InvalidAction(
            "apply_action(hand, action): %r is not legal at this decision, legal are %r"
            % (action, legal)
        )
    resolved = raise_amount(hand, action)
    if shape_row(hand._shape)["bet_structure"] == "fixed-limit":
        return advance(hand, action)
    return advance(hand, action, resolved)
