"""The action vocabulary, legality, and the step (docs/L3/engine/actions.md,
stepping.md).

A descriptor is one of three plain `str` values and carries no amount: `raise`
denotes the minimum legal completion for the decision it is applied to, which
fixed-limit makes unique (actions.md §1–§2).  The engine declares no legality of
its own beyond `pokerkit`'s three `can_*` predicates, so `legal_actions` and
`apply_action` cannot disagree (stepping.md §1).
"""

from __future__ import annotations

from .errors import InvalidAction
from .hand import Hand, advance, require_live_hand

# The vocabulary, in the order `legal_actions` returns it and the order
# `features`' indices follow (actions.md §1, e2e-surface.md §2).
ACTIONS = ("fold", "check-call", "raise")


def legal_actions(hand: Hand) -> tuple[str, ...]:
    """What the acting seat may do, in the vocabulary's order (stepping.md §1).

    At most one entry per vocabulary index, no duplicates, never empty for a live
    hand, and deterministic.  `fold` appears only when `to_call` is non-zero because
    `pokerkit` refuses a fold when the actor's bet already equals the maximum bet.
    """
    require_live_hand(hand, "legal_actions")
    state = hand._state
    legal = []
    if state.can_fold():
        legal.append("fold")
    if state.can_check_or_call():
        legal.append("check-call")
    if state.can_complete_bet_or_raise_to():
        legal.append("raise")
    return tuple(legal)


def apply_action(hand: Hand, action: str) -> Hand:
    """The advanced hand, as a new handle (stepping.md §2, advance.md §1).

    Validation is against the argument handle's legal tuple, by value, before any
    state is copied: an illegal descriptor is a contract violation and is never
    turned into a fold or a call on the violator's behalf (surface.md §7, D-2).
    """
    require_live_hand(hand, "apply_action")
    if not isinstance(action, str) or action not in ACTIONS:
        raise InvalidAction(
            "apply_action(hand, action): %r is not one of %r" % (action, ACTIONS)
        )
    legal = legal_actions(hand)
    if action not in legal:
        raise InvalidAction(
            "apply_action(hand, action): %r is not legal at this decision, legal are %r"
            % (action, legal)
        )
    return advance(hand, action)
