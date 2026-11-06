"""The one learning rule's arithmetic: epsilon, the keyed draw, the tie-break.

`rule.md` §4-§5 stated once, as functions with no state: the schedule's rate at one
position, one `sha256` digest per decision and the two draws a caller takes from it,
and the tolerance rule that decides a near tie the same way in both backends.  A
decision is a function of the observation and the mask, never of how many decisions
came before it, so nothing here advances and nothing here is cached (`surface.md` §1).
"""

from __future__ import annotations

import hashlib

import numpy

from . import declarations

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


def _tie_break(values, mask):
    """`rule.md` §5: the smallest masked index within `tol` of the masked maximum."""
    members = list(mask)
    best = max(values[index] for index in members)
    tolerance = TOLERANCE * max(1.0, abs(best))
    return int(min(index for index in members if values[index] >= best - tolerance))


def decide(seed, family, position, values, observation, mask):
    """`rule.md` §4's decision: the exploring arm or §5's greedy one, one index."""
    members = tuple(mask)
    exploring, uniform = _draws(seed, family, observation, members)
    if exploring < _epsilon(position):
        return int(members[min(int(uniform * len(members)), len(members) - 1)])
    return _tie_break(values, members)
