"""`features` -- the ladder's representation axis (docs/L3/features/README.md).

The package declares exactly the seven entry points of `docs/L2/features/surface.md`
§1 and nothing else public: `Encoder`, the error classes, the declaration table, the
card map, the history parser and every block writer stay in the submodules
(layout.md §2, guardrails.md G14).  Each entry point is a thin wrapper, so the
package's namespace cannot grow a second export when an owner module gains a helper.
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


def build_encoder(name):
    """One encoder, by a declared encoding's name (surface.md §4)."""
    return _encoder.build_encoder(name)


def observation_spec(encoder):
    """The six-key spec record of one encoder (surface.md §5)."""
    return _encoder.observation_spec(encoder)


def encode(encoder, readout):
    """One readout, one observation (surface.md §6)."""
    return _encode.encode(encoder, readout)


def action_space():
    """The three-index action vocabulary (surface.md §7)."""
    return _vocabulary.action_space()


def legal_indices(legal_actions):
    """A decision's legal indices, position-aligned (surface.md §8)."""
    return _vocabulary.legal_indices(legal_actions)


def decode_action(index):
    """The descriptor of one action index (surface.md §9)."""
    return _vocabulary.decode_action(index)
