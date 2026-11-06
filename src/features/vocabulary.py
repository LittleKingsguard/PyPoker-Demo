"""The three-index action vocabulary (vocabulary.md).

The vocabulary is the game's and is held constant across the whole ladder: three
indices, three descriptors, and never an amount (D-2).  The descriptor spelling is
the one `engine.apply_action` accepts, restated here instead of imported -- this
module imports no other project module (layout.md §3, guardrails.md G12).
"""

from __future__ import annotations

from collections.abc import Sequence
from numbers import Integral

from .errors import InvalidActionIndex, InvalidActionList, UnknownAction

# Indices 0, 1, 2, in ascending order (vocabulary.md §1).  The descriptors are
# hand-independent and carry no amount.
ACTIONS = ("fold", "check-call", "raise")

# The raise denotes the engine's minimum legal completion for the decision.  Prose,
# never a number: no string in `action_space`'s record contains a digit
# (vocabulary.md §2, guardrails.md G6).
_RAISE_COMPLETION = "the engine's minimum legal completion for the decision"


def action_space():
    """The declared vocabulary, rebuilt fresh on every call (surface.md §7).

    The keys are the three indices and the only integers in the record: no bet size,
    no chip count, no id beyond `0`, `1` and `2` (guardrails.md G6).
    """
    return {
        0: {"name": ACTIONS[0]},
        1: {"name": ACTIONS[1]},
        2: {"name": ACTIONS[2], "completion": _RAISE_COMPLETION},
    }


def legal_indices(legal_actions):
    """One index per descriptor, position-aligned and never sorted (surface.md §8).

    The i-th index is the vocabulary index of the i-th descriptor, so an argument out
    of the engine's order yields its indices in that same order -- the alignment is
     contract, and this function never sorts, de-duplicates or decides legality
    (vocabulary.md §3, guardrails.md G7).
    """
    if isinstance(legal_actions, (str, bytes)) or not isinstance(legal_actions, Sequence):
        raise InvalidActionList(
            "legal_indices(legal_actions): the argument must be a non-empty sequence of "
            "action descriptors, got %r" % (legal_actions,)
        )
    if not legal_actions:
        raise InvalidActionList(
            "legal_indices(legal_actions): a decision has at least one legal action, "
            "got %r" % (legal_actions,)
        )
    indices = []
    for descriptor in legal_actions:
        # Gated on `str` first: a foreign type that defines its own equality protocol
        # must not talk its way into the vocabulary (vocabulary.md §5, errors.md §1).
        if not isinstance(descriptor, str) or descriptor not in ACTIONS:
            raise UnknownAction(
                "legal_indices(legal_actions): %r is not one of %r"
                % (descriptor, ACTIONS)
            )
        indices.append(ACTIONS.index(descriptor))
    return tuple(indices)


def decode_action(index):
    """The descriptor of one index, and nothing else (surface.md §9).

    Two checks and a lookup: no coercion, no clamping against a decision's legal set,
    and no default descriptor for an unknown index (vocabulary.md §4, guardrails.md G8).
    """
    if isinstance(index, bool) or not isinstance(index, Integral):
        raise InvalidActionIndex(
            "decode_action(index): the index must be an integer, got %r" % (index,)
        )
    if not 0 <= index <= 2:
        raise InvalidActionIndex(
            "decode_action(index): the index must be one of 0, 1 or 2, got %r" % (index,)
        )
    return ACTIONS[int(index)]
