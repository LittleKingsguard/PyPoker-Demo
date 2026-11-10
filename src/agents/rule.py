"""The one learning rule's arithmetic: epsilon, the keyed draw, the tie-break.

`rule.md` §4-§5 stated once, as functions with no state: the schedule's rate at one
position, one `sha256` digest per decision and the two draws a caller takes from it,
and the tolerance rule that decides a near tie the same way in both backends.  A
decision is a function of the observation and the mask, never of how many decisions
came before it, so nothing here advances and nothing here is cached (`surface.md` §1).

Two arms are two functions: `decide` takes the keyed draw of §4 and falls through to the
greedy arm, `decide_greedy` **is** that arm and takes no draw at all — the mode an `off`
policy is built with (`shapes.md` §4).  Both report the index with the `tie` flag `act`
records (`records.md` §6, §15).
"""

from __future__ import annotations

import hashlib
import math

import numpy

from . import declarations
from .errors import LearningDiverged

#: `rule.md` §5's design constant: the relative tolerance, with an absolute floor,
#: inside which the smallest masked index wins (`backends.md` §3).
TOLERANCE = 1e-9

#: `rule.md` §4's payload tag, so a key is this module's and versioned.
PAYLOAD = b"pypoker-agents/explore/v1"

#: The one separator every field of the payload is joined with.
SEPARATOR = b"\x1f"


def _epsilon(position):
    """`rule.md` §4's rate at one schedule position: `start` at `0`, `end` from `samples`."""
    schedule = declarations.HYPER["exploration"]
    start = float(schedule["start"])
    end = float(schedule["end"])
    samples = int(schedule["samples"])
    return start + (end - start) * min(int(position), samples) / samples


def _observation_bytes(family, observation):
    """One observation's payload bytes: little-endian, so one decision hashes once."""
    if family == declarations.DENSE_FAMILY:
        return numpy.ascontiguousarray(
            numpy.asarray(observation).astype("<f8")
        ).tobytes()
    return numpy.ascontiguousarray(numpy.asarray(observation).astype("<i8")).tobytes()


def _decision_key(seed, family, observation, mask):
    """`rule.md` §4's payload's `sha256` digest (32 bytes) for one decision."""
    payload = (
        PAYLOAD
        + SEPARATOR
        + str(int(seed)).encode("ascii")
        + SEPARATOR
        + str(family).encode("ascii")
        + SEPARATOR
        + _observation_bytes(family, observation)
        + SEPARATOR
        + ",".join(str(int(index)) for index in sorted(mask)).encode("ascii")
    )
    return hashlib.sha256(payload).digest()


def _draws(seed, family, observation, mask):
    """`(u, v)`, the two `float64` draws `rule.md` §4 takes from the decision key."""
    key = _decision_key(seed, family, observation, mask)
    generator = numpy.random.Generator(
        numpy.random.PCG64(int.from_bytes(key[:16], "big"))
    )
    return float(generator.random()), float(generator.random())


def _finite(values, members, site):
    """`divergence.md` §2: the masked values are finite, or the refusal naming the first that is not."""
    for index in members:
        value = float(values[index])
        if not math.isfinite(value):
            raise LearningDiverged(
                "%s(values): the masked value at index %d is not finite and the "
                "learner has diverged, got %r" % (site, int(index), value)
            )


def _tie_break(values, mask):
    """`rule.md` §5: the smallest masked index within `tol` of the masked maximum."""
    members = list(mask)
    _finite(values, members, "_tie_break")
    best = max(values[index] for index in members)
    tolerance = TOLERANCE * max(1.0, abs(best))
    return int(min(index for index in members if values[index] >= best - tolerance))


def decide_greedy(values, mask):
    """The greedy arm alone: §5's index, and whether the tie-break chose it.

    This is the arm an `off` policy takes (`shapes.md` §4, `sizing.md` §4), and it is
    also `decide`'s own greedy branch, so the two modes cannot disagree on an index.  No
    payload, no key and no generator are touched here: the decision is the masked maximum
    and §5's tolerance rule, and nothing in this function samples anything.

    The second value is the `tie` flag `act` records (`records.md` §6, §15): true exactly
    when the **tie-break**, and not a strict maximum, chose the index — at least two
    masked values sat within `TOLERANCE` of the masked maximum — so a one-element mask is
    never a tie, and the order the tie resolves in is the shape's own declared order and
    never this module's (`shapes.md` §3, ASM-37).
    """
    members = tuple(mask)
    _finite(values, members, "decide_greedy")
    index = _tie_break(values, members)
    best = max(values[member] for member in members)
    tolerance = TOLERANCE * max(1.0, abs(best))
    near = 0
    for member in members:
        if values[member] >= best - tolerance:
            near += 1
    return index, bool(near >= 2)


def decide(seed, family, position, values, observation, mask):
    """`rule.md` §4's decision: the exploring arm or §5's greedy one, and its tie flag.

    The record `act` returns carries the index **and** whether the tie-break chose it, so
    this returns the pair: the exploring arm drew the index and consulted no maximum, so
    its flag is false, while the greedy arm answers exactly as `decide_greedy` does
    (`shapes.md` §3-§4, `records.md` §6).
    """
    members = tuple(mask)
    _finite(values, members, "decide")
    exploring, uniform = _draws(seed, family, observation, members)
    if exploring < _epsilon(position):
        return int(members[min(int(uniform * len(members)), len(members) - 1)]), False
    return decide_greedy(values, members)
