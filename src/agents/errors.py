"""The refusal hierarchy of `agents` (`docs/L3/agents/errors.md` §2).

One base and sixteen subclasses, one per refusal family of
`docs/L2/agents/surface.md` §4-§12: a caller catches `AgentsError` when it wants to
know that *this* module refused it, and never has to catch a `KeyError` from a
mistyped record key, a `numpy` `ValueError` or a `torch` error that escaped.

The classes are below the entry points and are not surface (`README.md` §3): a
battery asserts the *behaviour* — that the call raises, and what the message says —
and never the class, because the class is this module's freedom (errors.md §2).
"""

from __future__ import annotations


class AgentsError(Exception):
    """Base of every refusal of this module (errors.md §2)."""


class InvalidLearner(AgentsError):
    """`param_count`, `act`, `learn`, `save`, `as_policy`: the value is not a learner."""


class InvalidSpec(AgentsError):
    """`build_learner`: not a mapping, a missing required key, a bare kind with no sizes."""


class UnknownBackend(AgentsError):
    """`build_learner`: a backend `learners()['backends']` does not declare."""


class UnknownArchitecture(AgentsError):
    """`build_learner`: a kind `learners()['architectures']` does not declare."""


class InvalidSetting(AgentsError):
    """`build_learner`: width or depth not a positive integer, sparsity outside `[0, 1]`."""


class InvalidSeed(AgentsError):
    """`build_learner`, `as_policy`, `build_baseline`: the seed is not an integer."""


class InvalidEncoder(AgentsError):
    """`build_learner`, `as_policy`: the value is not an encoder `features` built."""


class EncoderMismatch(AgentsError):
    """`build_learner`, `as_policy`: the encoder's family or size contradicts the learner's."""


class InvalidObservation(AgentsError):
    """`act`, `learn`: shape, dtype, family or finiteness contradicts the learner's."""


class InvalidMask(AgentsError):
    """`act`, `learn`: a mask that is empty, repeats an index, or leaves `{0, 1, 2}`."""


class InvalidBatch(AgentsError):
    """`learn`: an empty batch, a missing required key, an action outside its own mask."""


class InvalidReadout(AgentsError):
    """A policy: not a mapping, or missing a fact the rule needs."""


class UnknownBaseline(AgentsError):
    """`build_baseline`: a name the three fixed baselines do not include."""


class CheckpointUnwritable(AgentsError):
    """`save`: a path that is not a writable file location."""


class CheckpointUnreadable(AgentsError):
    """`load`: missing, unreadable, or a form this module does not read."""


class CheckpointMismatch(AgentsError):
    """`load`: the spec disagrees with the file on a compared key."""
