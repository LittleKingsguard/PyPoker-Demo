"""The opaque encoder, the six-key spec and the declared catalogue (encoder.md).

`Encoder` is a type of its own so that `observation_spec` can refuse "a value that is
not an encoder this module built", and so that an encoder exists only by a declared
encoding (surface.md §4, §5).  It defines no `__eq__`, holds two things, offers no way
to read either, and its `__repr__` names the encoding and nothing else (encoder.md
§1, guardrails.md G2).
"""

from __future__ import annotations

from .declarations import ENCODINGS
from .errors import InvalidEncoder, UnknownEncoding


class Encoder:
    """One declared encoding, and no way to read it (encoder.md §1)."""

    __slots__ = ("_name", "_declaration")

    def __init__(self, name, declaration):
        self._name = name
        self._declaration = declaration

    def __repr__(self):
        return "Encoder(%r)" % (self._name,)


def require_encoder(value, entry_point):
    """The encoder, or the refusal its contract states (errors.md §3, guardrails.md G2).

    Both entry points that take an encoder call this one home for the rule, so the
    two refusals cannot drift apart (layout.md §2).
    """
    if not isinstance(value, Encoder):
        raise InvalidEncoder(
            "%s(encoder): the argument must be an encoder returned by build_encoder, "
            "got %s" % (entry_point, type(value).__name__)
        )
    return value


def build_encoder(name):
    """One encoder, by one of the names `encodings` declares (surface.md §4).

    The name is matched exactly -- case-sensitively and not stripped -- because a
    spelling that is not the declared one names a different thing (encoder.md §2).
    """
    if not isinstance(name, str) or name not in ENCODINGS:
        raise UnknownEncoding(
            "build_encoder(name): the encoding must be one of %r, got %r"
            % (tuple(ENCODINGS), name)
        )
    return Encoder(name, ENCODINGS[name])


def observation_spec(encoder):
    """The six-key spec record, built fresh on every call (surface.md §5, encoder.md §3).

    Every value is plain data -- a `str`, an `int`, a `tuple` of those or `None` -- so
    a report's header may quote the record and a caller's mutation of the mapping
    cannot reach the declaration table (guardrails.md G11).
    """
    declaration = require_encoder(encoder, "observation_spec")._declaration
    return {
        "representation": declaration["representation"],
        "kind": declaration["kind"],
        "fields": declaration["fields"],
        "shape": declaration["shape"],
        "dtype": declaration["dtype"],
        "vocabulary": declaration["vocabulary"],
    }


def encodings():
    """The two declared encodings, in the ladder's order, each with its spec record.

    The catalogue is rebuilt from the declaration table on every call, and each
    entry is equal to `observation_spec(build_encoder(name))` (surface.md §3).
    """
    return {name: observation_spec(build_encoder(name)) for name in ENCODINGS}
