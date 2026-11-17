"""`features` -- the ladder's representation axis (docs/L3/features/README.md).

The package declares exactly the eleven entry points of `docs/L2/features/surface.md`
§1 and nothing else public: `Encoder`, `FrozenModel`, the error classes, the declaration
table, the card map, the history parser and every block writer stay in the submodules
(layout.md §2, guardrails.md G14).  Each entry point is a thin wrapper, so the
package's namespace cannot grow a second export when an owner module gains a helper.

Three of the eleven names take a game shape as an **optional keyword** whose absence is the
default shape, and one rule is why it is a keyword and not a positional: the pre-existing
arity cases pin each name's positional argument to the one it had, and a keyword-only
optional adds the shape without moving any of them (surface.md §1, D-29).  No
other name takes a shape, and none needs one -- the shape is the encoder's once it is
built, and the spec record it yields reads that shape's own width and nothing else of it,
because the history block's capacity is the shape's (`docs/L1/shapes.md` §8, ASM-42,
ASM-44).

`build_encoder`'s second optional keyword is the **strength member** (`ASM-46`), and the
last four names are the frozen card model's (`ASM-47`, `ASM-49`, `ASM-51`): the value the
observation's tenth block carries is produced by `strength`, injected by `stated` into a
copy of the readout, seeded into a learner's embedding table by `card_rows`, and both are
reached through `load_strength`'s opaque estimator.  `torch` is imported inside those
functions and never at this module's top, so a non-strength import of `features` still pulls
no torch (layout.md §3).
"""

from . import cardmodel as _cardmodel
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
    "load_strength",
    "strength",
    "stated",
    "card_rows",
)


def encodings():
    """The two declared encodings and their spec records (surface.md §3)."""
    return _encoder.encodings()


def build_encoder(name, *, shape=None, strength=None):
    """One encoder, by a declared encoding's name, on one declared shape (§4).

    `strength` is the optional tenth block's member; its absence is today's declaration
    and an uncatalogued member is refused by name (`ASM-46`).
    """
    return _encoder.build_encoder(name, shape, strength)


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


def load_strength(source):
    """One declared frozen estimator, or the refusal naming the source (`ASM-51`)."""
    return _cardmodel.load_strength(source)


def strength(model, readout):
    """The frozen estimator's predicted win probability for one decision (`ASM-47`)."""
    return _cardmodel.strength(model, readout)


def stated(model, readout):
    """`readout` plus `{"strength": p}`, as a **fresh** mapping (`ASM-47`)."""
    return _cardmodel.stated(model, readout)


def card_rows(model):
    """The source's fifty-two card rows and a digest of them (`ASM-49`)."""
    return _cardmodel.card_rows(model)
