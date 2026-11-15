"""The refusals of `engine` (docs/L3/engine/errors.md §2).

Every invalid argument is refused by raising one of these, before the first side
effect, with a message of the grammar of errors.md §3.  The classes are not surface:
they live below an entry point (errors.md §2, guardrails.md G11).
"""

from __future__ import annotations


class EngineError(Exception):
    """The base of every refusal of this module (errors.md §2)."""


class InvalidSeed(EngineError):
    """A seed that is not an `int` (errors.md §2, hand.md §2)."""


class InvalidHand(EngineError):
    """Not a hand handle, or a hand that is over (errors.md §2, hand.md §5)."""


class InvalidAction(EngineError):
    """A descriptor outside `legal_actions`, or not a descriptor (errors.md §2)."""


class InvalidDecision(EngineError):
    """`equity`'s first argument, when it is no decision (errors.md §2, equity.md §1)."""


class InvalidSamples(EngineError):
    """An equity sample count that is not a positive `int` (errors.md §2)."""


class InvalidPolicy(EngineError):
    """A `play_hand` policy that is not callable (errors.md §2, episode.md §1)."""


class InvalidDeal(EngineError):
    """A prescribed deal that breaks one of the six named rules (errors.md §2, loaded-deal.md §3).

    A deal names hole cards per seat and a board, and every malformation is a refusal of
    **one** of six named rules — `not-a-deal`, `seat-coverage`, `hole-size`,
    `board-length`, `card-outside-deck`, `duplicate-card` — tried in that order, so one
    malformed deal has exactly one message.  It sits beside `InvalidSeed` because both are
    `new_hand`'s: one refuses the stream's input and the other the cards'.
    """


class InvalidSeating(EngineError):
    """A `play_hand` seating of the wrong length, or beside the positional policies.

    A shape seats its own number of policies, so a seating that is not one policy per
    seat — a sequence of the wrong length, a sequence handed beside the two positional
    policies, or two positional policies on a shape with more seats — is refused naming
    the shape, its seat count and the count it was handed (errors.md §2, episode.md §1,
    seats.md §4).  It sits beside `InvalidPolicy` because both are `play_hand`'s: one is
    a seat with no policy, the other a policy with no seat.
    """


class UnknownShape(EngineError):
    """A shape name outside the catalogue (errors.md §2, config.md §1, D-29)."""
