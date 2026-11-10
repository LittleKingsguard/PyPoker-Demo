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


class UnknownShape(EngineError):
    """A shape name outside the catalogue (errors.md §2, config.md §1, D-29)."""
