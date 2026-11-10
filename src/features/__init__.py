"""`features` -- the ladder's representation axis (docs/L3/features/README.md).

The package declares exactly the seven entry points of `docs/L2/features/surface.md`
§1 and nothing else public: `Encoder`, the error classes, the declaration table, the
card map, the history parser and every block writer stay in the submodules
(layout.md §2, guardrails.md G14).  Each entry point is a thin wrapper, so the
package's namespace cannot grow a second export when an owner module gains a helper.

Three of the seven name a game shape as an **optional keyword** whose absence is the
default shape, and one rule is why it is a keyword and not a positional: the pre-existing
arity cases pin each name's positional argument to the one it had, and a keyword-only
optional adds the shape without moving any of them (surface.md §1, D-29).  No other name
takes a shape, and none needs one -- the shape is the encoder's once it is built, and a
spec record does not depend on it (sizing.md §5).
"""

from . import encode as _encode
from . import encoder as _encoder
from . import vocabulary as _vocabulary

__all__ = (
    "encodings",
    "build_encoder",
    "observation_spec",
    "encode",
    "action_space",
    "legal_indices",
    "decode_action",
)


def encodings():
    """The two declared encodings and their spec records (surface.md §3)."""
    return _encoder.encodings()


def build_encoder(name, *, shape=None):
    """One encoder, by a declared encoding's name, on one declared shape (§4)."""
    return _encoder.build_encoder(name, shape)


def observation_spec(encoder):
    """The six-key spec record of one encoder (surface.md §5)."""
    return _encoder.observation_spec(encoder)


def encode(encoder, readout):
    """One readout, one observation (surface.md §6)."""
    return _encode.encode(encoder, readout)


def action_space(*, shape=None):
    """One shape's action vocabulary, in that shape's index order (surface.md §7)."""
    return _vocabulary.action_space(shape)


def legal_indices(legal_actions):
    """A decision's legal indices, position-aligned (surface.md §8)."""
    return _vocabulary.legal_indices(legal_actions)


def decode_action(index, *, shape=None):
    """The descriptor of one index in one shape's vocabulary (surface.md §9)."""
    return _vocabulary.decode_action(index, shape)
