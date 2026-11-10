"""The opaque encoder, the six-key spec and the declared catalogue (encoder.md).

`Encoder` is a type of its own so that `observation_spec` can refuse "a value that is
not an encoder this module built", and so that an encoder exists only by a declared
encoding (surface.md §4, §5).  It defines no `__eq__`, holds three things, offers no way
to read any of them, and its `__repr__` names the encoding and nothing else (encoder.md
§1, guardrails.md G2).

An encoder carries the **encoding** it was built by and the **shape** it was built for,
because the second game shape changes the divisor and bucket tables of both encodings and
nothing else about them (sizing.md §5, shapes.md §2).  The shape is not readable from
outside: a caller names it to `build_encoder` and reads its effect through `encode`.
"""

from __future__ import annotations

from .declarations import ENCODING_NAMES, declaration, require_shape, spec
from .errors import InvalidEncoder, UnknownEncoding


class Encoder:
    """One declared encoding on one declared shape, and no way to read either (§1)."""

    __slots__ = ("_name", "_shape", "_declaration")

    def __init__(self, name, shape, record):
        self._name = name
        self._shape = shape
        self._declaration = record

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


def build_encoder(name, shape=None):
    """One encoder, by one of the names `encodings` declares, on one declared shape (§4).

    The name is matched exactly -- case-sensitively and not stripped -- because a
    spelling that is not the declared one names a different thing (encoder.md §2).  The
    shape is optional and its absence is the **default** shape, so every caller that
    named no shape gets the encoder it always got, on the tables it always had
    (shapes.md §3, D-29).  An encoding name outside the two is refused before the shape
    is looked at, and a shape name outside the catalogue is refused naming it and the
    declared names -- never defaulted.
    """
    for declared in ENCODING_NAMES:
        if isinstance(name, str) and name == declared:
            resolved = require_shape(shape, "build_encoder")
            return Encoder(declared, resolved, declaration(declared, resolved))
    raise UnknownEncoding(
        "build_encoder(name): the encoding must be one of %r, got %r"
        % (ENCODING_NAMES, name)
    )


def observation_spec(encoder):
    """The six-key spec record, built fresh on every call (surface.md §5, encoder.md §3).

    Every value is plain data -- a `str`, an `int`, a `tuple` of those or `None` -- so
    a report's header may quote the record and a caller's mutation of the mapping
    cannot reach the declaration table (guardrails.md G11).  The record is the
    **shape-invariant** part of a declaration: the slot counts, the block widths, the
    dtype and the token vocabulary are the same on every declared shape, so no seventh
    key names the shape or the normalisers (sizing.md §5, encoder.md §3).
    """
    record = require_encoder(encoder, "observation_spec")._declaration
    return {
        "representation": record["representation"],
        "kind": record["kind"],
        "fields": record["fields"],
        "shape": record["shape"],
        "dtype": record["dtype"],
        "vocabulary": record["vocabulary"],
    }


def encodings():
    """The two declared encodings, in the ladder's order, each with its spec record.

    The catalogue is rebuilt from the declaration table on every call, and each
    entry is equal to `observation_spec(build_encoder(name))` (surface.md §3).  It takes
    no shape because a spec record does not depend on one: the two shapes declare the
    same slot counts, widths, dtype and vocabulary, which is what keeps every
    fixed-limit observation and every embedding table where it is (sizing.md §5).
    """
    return {name: spec(name) for name in ENCODING_NAMES}
