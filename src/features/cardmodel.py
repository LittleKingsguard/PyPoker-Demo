"""The frozen card model: one declared source table, one builder, four entry points.

`ASM-47`'s value has a producer, and this module is it.  A supervised estimator trained
outside the product predicts one seat's win probability for a decision's own deal, and the
product reads that number as the observation's tenth declared field (`ASM-46`) and, when a
variant seeds its embedding table, copies the estimator's **card rows** into the learner's
parameter block (`ASM-49`).

**Not a seventh module.**  `module-map.md` §7's doctrine is that an addition costs an entry
point rather than a subtree, so the estimator is four names on `features` and not a module
of its own: it is a frozen *input* and not a policy feature, which is why it is not a sixth
catalogue member either.  It is deliberately not in `evaluation`'s or `agents`' charge: it
neither learns nor measures.

**Two layouts, one architecture.**  The two shipped artefacts were written by two probe
scripts whose modules differ in three attribute names and in nothing else: the positional
embedding and the two LayerNorms.  So `_builder` is **one** statement of the forward pass and
a declared row supplies the three names, which is what makes a third layout a row and never
a second module.  A state dict that matches neither row is refused by name (`ASM-51`).

**`torch` is imported lazily, inside the functions that use it.**  A non-strength import of
`features` therefore pulls no torch, which is the boundary `layout.md` §3 states and
`test_features_purity.py` asserts in a child interpreter: the import is where the work is,
exactly as `torch_backend` does it, and no module-level edge has to be kept in step.

**The declared table is restated in `training/declarations.py`** and held equal to this one
row for row by the join battery, exactly as `SHAPE_NAMES` and `SHAPE_HISTORY` are
(`D-13`): `training` is not granted this module's internals and a private copy of a path
would drift.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Mapping

import numpy

from . import cards
from .errors import InvalidModel, InvalidReadout, UnknownSource

#: The declared frozen estimators, in the declared order, one row each (`ASM-51`).  A row
#: names the artefact's repository-relative path and the **three attribute names** that
#: differ between the two layouts -- the positional embedding, the LayerNorm after the
#: attention block and the LayerNorm after the feed-forward block.  `emb`, `ff`, `mha` and
#: `head` are the same names in both, so they are written once in `_builder` and never
#: restated here.
STRENGTH_SOURCES = {
    "attn-60": {
        "path": ".probe/attn60.pt",
        "position": "pos",
        "attention_norm": "n1",
        "output_norm": "n2",
    },
    "attn-400": {
        "path": ".probe/attnconv.pt",
        "position": "posemb",
        "attention_norm": "norm",
        "output_norm": "ffn",
    },
}

#: The estimator's own dimensions, read off both shipped artefacts: a `(53, 50)` card
#: table whose row 0 is the pad and rows 1..52 are the fifty-two cards, a seven-position
#: positional table (two hole cards and five board cards), two layers of five heads, a
#: 50-wide residual stream and a 96-wide feed-forward block.  They are declared once, and a
#: state dict that carries a different shape is refused naming it (`ASM-51`).
EMBEDDINGS = 53
WIDTH = 50
POSITIONS = 7
LAYERS = 2
HEADS = 5
HIDDEN = 96

#: The card rows a seed copies: ids 1..52, one per card, and the first id a copy writes to.
CARD_ROWS = 52
FIRST_CARD_ROW = 1

#: How deep the two character fields of one card are, for the readout's own refusal.
HOLE = 2
BOARD = 5


def _torch():
    """The library, imported on the first call that needs it and nowhere else."""
    import torch

    return torch


def require_source(source, entry_point, argument="source"):
    """One declared source's name, or the refusal naming it and the declared names.

    A source is matched exactly -- case-sensitively and not stripped -- because a spelling
    that is not the declared one names a different artefact, and it is **never** defaulted
    onto the first row: `ASM-51` recommends `attn-60` as a default in a *configuration*, and
    a default in a configuration is a declared value and not a substitution here
    (`errors.md` §2-§3).
    """
    for declared in STRENGTH_SOURCES:
        if isinstance(source, str) and source == declared:
            return declared
    raise UnknownSource(
        "%s(%s): the source must be one of %r, got %r"
        % (entry_point, argument, tuple(STRENGTH_SOURCES), source)
    )


def _builder(row):
    """One frozen estimator's module for one declared layout row (`ASM-51`).

    The architecture, written **once** and parameterised by the row's three attribute
    names: an embedding table, a positional embedding added to it, `LAYERS` blocks of
    masked multi-head self-attention and a feed-forward net around two LayerNorms, and a
    three-layer head whose last activation is a sigmoid, so the forward pass's value is a
    probability by construction.  The positional table is indexed by slot, so a decision
    with fewer than five board cards pads with the pad id and the pad is masked out of the
    mean.
    """
    torch = _torch()
    network = torch.nn

    class Frozen(network.Module):
        """One card model: the shared architecture, three attribute names from a row."""

        def __init__(self):
            super().__init__()
            self.emb = network.Embedding(EMBEDDINGS, WIDTH)
            setattr(self, row["position"], network.Embedding(POSITIONS, WIDTH))
            self.mha = network.ModuleList(
                [
                    network.MultiheadAttention(WIDTH, HEADS, batch_first=True)
                    for _layer in range(LAYERS)
                ]
            )
            setattr(
                self,
                row["attention_norm"],
                network.ModuleList([network.LayerNorm(WIDTH) for _ in range(LAYERS)]),
            )
            setattr(
                self,
                row["output_norm"],
                network.ModuleList([network.LayerNorm(WIDTH) for _ in range(LAYERS)]),
            )
            self.ff = network.ModuleList(
                [
                    network.Sequential(
                        network.Linear(WIDTH, HIDDEN),
                        network.ReLU(),
                        network.Linear(HIDDEN, WIDTH),
                    )
                    for _layer in range(LAYERS)
                ]
            )
            self.head = network.Sequential(
                network.Linear(WIDTH, HIDDEN),
                network.ReLU(),
                network.Linear(HIDDEN, HIDDEN),
                network.ReLU(),
                network.Linear(HIDDEN, 1),
                network.Sigmoid(),
            )

        def forward(self, ids):
            """`p` for one batch of padded card-id rows (`ASM-47`)."""
            pad = ids == 0
            positions = torch.arange(ids.shape[1], dtype=torch.long).unsqueeze(0)
            carried = self.emb(ids) + getattr(self, row["position"])(positions)
            norms = getattr(self, row["attention_norm"])
            outputs = getattr(self, row["output_norm"])
            for attention, norm, feed, output in zip(self.mha, norms, self.ff, outputs):
                attended, _weights = attention(
                    carried, carried, carried, key_padding_mask=pad, need_weights=False
                )
                carried = norm(carried + attended)
                carried = output(carried + feed(carried))
            mask = (~pad).unsqueeze(-1).to(carried.dtype)
            pooled = (carried * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1.0)
            return self.head(pooled)

    return Frozen()


class FrozenModel:
    """One loaded frozen estimator, and no way to read its weights (`ASM-47`).

    Opaque on purpose, exactly as `Encoder` is: it holds the module, the declared source it
    came from and the width its rows are, offers no way to read any of them, and its
    `__repr__` names the source and nothing else.  A caller hands it back to `strength`,
    `stated` and `card_rows`, and to nothing else.
    """

    __slots__ = ("_source", "_row", "_width", "_module")

    def __init__(self, source, row, width, module):
        self._source = source
        self._row = row
        self._width = int(width)
        self._module = module

    def __repr__(self):
        return "FrozenModel(%r)" % (self._source,)


def require_model(value, entry_point):
    """The model, or the refusal its contract states (`errors.md` §2).

    The one home for the rule all three consumers call, so the refusals cannot drift apart
    (`layout.md` §2): the argument must be a value `load_strength` returned.
    """
    if not isinstance(value, FrozenModel):
        raise InvalidModel(
            "%s(model): the argument must be a frozen model returned by load_strength, "
            "got %s" % (entry_point, type(value).__name__)
        )
    return value


def _repo_root():
    """The repository root this module's declared paths are relative to.

    Derived from this file's own location -- `src/features/cardmodel.py` is three
    directories below the root -- so a declared path is one spelling and no caller passes
    one (guardrails.md G6).
    """
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def load_strength(source):
    """One declared frozen estimator, or the refusal naming the source and the table.

    Five checks before a model exists (`ASM-51`): the source is one of the declared names;
    its artefact exists where the row says; the file reads as a state dict; the dict's
    attribute names are **exactly** the row's, which is checked by loading it into the
    module that row builds; and its `emb.weight` is `(53, 50)` and every weight is 50 wide.
    A dict that matches the other row is refused naming the sources, so two layouts are two
    rows and never a guess.
    """
    name = require_source(source, "load_strength")
    row = STRENGTH_SOURCES[name]
    path = os.path.join(_repo_root(), row["path"])
    if not os.path.isfile(path):
        raise UnknownSource(
            "load_strength(source): the source %r declares the artefact %r, and no such "
            "file exists (ASM-51)" % (name, row["path"])
        )
    torch = _torch()
    try:
        state = torch.load(path, map_location="cpu", weights_only=True)
    except Exception as error:
        raise InvalidModel(
            "load_strength(source): the source %r declares the artefact %r, and it does "
            "not read as a state dict (%s: %s) (ASM-51)"
            % (name, row["path"], type(error).__name__, error)
        ) from None
    if not isinstance(state, dict):
        raise InvalidModel(
            "load_strength(source): the source %r declares the artefact %r, and it holds "
            "%s and not a state dict (ASM-51)"
            % (name, row["path"], type(state).__name__)
        )
    module = _builder(row)
    try:
        module.load_state_dict(state, strict=True)
    except Exception as error:
        raise InvalidModel(
            "load_strength(source): the artefact %r does not match the layout the source "
            "%r declares -- the positional embedding %r, the attention norm %r and the "
            "output norm %r -- so it is one of %s or nothing (%s) (ASM-51)"
            % (
                row["path"],
                name,
                row["position"],
                row["attention_norm"],
                row["output_norm"],
                ", ".join(STRENGTH_SOURCES),
                error,
            )
        ) from None
    # The card table's own shape, read off the **file** and not off the module the row
    # just built (a module always has the declared shape): a seed copies rows 1..52 of a
    # `(53, width)` table, so a table of another shape has no rows to copy (`ASM-49`).
    embeddings = tuple(int(size) for size in state["emb.weight"].shape)
    if embeddings != (EMBEDDINGS, WIDTH):
        raise InvalidModel(
            "load_strength(source): the source %r's embedding table is %r, and a card "
            "model's is %r -- one pad row and %d cards at a %d-wide row (ASM-49, ASM-51)"
            % (name, embeddings, (EMBEDDINGS, WIDTH), CARD_ROWS, WIDTH)
        )
    module.eval()
    for parameter in module.parameters():
        parameter.requires_grad_(False)
    return FrozenModel(name, row, WIDTH, module)


def _card_ids(readout):
    """The decision's deal as seven padded card ids, or the refusal naming the field.

    `hole` is exactly two cards and `board` at most five; the two together are at most the
    seven slots the positional table declares, and every slot past the deal is the pad 0,
    which the forward pass masks out of its mean.  A malformed fact is refused by name
    rather than padded over, because a silently shortened deal is a different question
    (`errors.md` §3, `ASM-47`).
    """
    ids = [0] * POSITIONS
    for position, field in enumerate(("hole", "board")):
        value = readout[field]
        capacity = HOLE if field == "hole" else BOARD
        try:
            entries = list(value)
        except TypeError:
            raise InvalidReadout(
                "strength(readout): %r must be %s cards, got %r"
                % (
                    field,
                    "exactly two" if field == "hole" else "at most five",
                    value,
                )
            ) from None
        exact = field == "hole"
        if (len(entries) != capacity) if exact else (len(entries) > capacity):
            raise InvalidReadout(
                "strength(readout): %r must be %s cards, got %r"
                % (field, "exactly two" if exact else "at most five", value)
            )
        offset = 0 if field == "hole" else HOLE
        for slot, card in enumerate(entries):
            ids[offset + slot] = cards.card_id(card, field)
    return ids


def strength(model, readout):
    """`p in [0, 1]` for one decision's deal, through the source's own forward pass.

    The value is a probability by the head's own last activation, so nothing here clips it:
    a caller that receives a value outside `[0, 1]` has a broken artefact and `encode`
    refuses it by name (`ASM-46`, `ASM-47`).  A readout that is not a mapping, or whose
    `hole`/`board` cannot be read as cards, is refused naming the field.
    """
    held = require_model(model, "strength")
    if not isinstance(readout, Mapping):
        raise InvalidReadout(
            "strength(readout): the readout must be a mapping of the decision's facts, "
            "got %s" % type(readout).__name__
        )
    for field in ("hole", "board"):
        if field not in readout:
            raise InvalidReadout(
                "strength(readout): the readout is missing %r, which the card model reads"
                % (field,)
            )
    torch = _torch()
    ids = torch.tensor([_card_ids(readout)], dtype=torch.long)
    with torch.no_grad():
        value = held._module(ids).reshape(-1)[0]
    return float(value)


def stated(model, readout):
    """The injection, written once: `readout` plus `{"strength": p}`, as a **fresh** mapping.

    Never a mutation.  The readout a policy or a transition step is handed stays the
    eleven facts it arrived with -- `test_join_purity.py` and FEA-3.7 both assert that an
    encode leaves its argument untouched -- so the value is carried by a copy and the
    caller's mapping is left exactly as it was (`ASM-47`).
    """
    held = require_model(model, "stated")
    if not isinstance(readout, Mapping):
        raise InvalidReadout(
            "stated(readout): the readout must be a mapping of the decision's facts, got "
            "%s" % type(readout).__name__
        )
    record = dict(readout)
    record["strength"] = strength(held, readout)
    return record


def card_rows(model):
    """The source's fifty-two card rows as a fresh `(52, width)` float64 array, and a digest.

    Rows **1..52**: row 0 is the pad's and is not a card, so it is never copied.  The
    conversion is `numpy.asarray(..., dtype=numpy.float64)`, and the digest is taken over
    the converted rows, so a replay compares like with like (`ASM-49`).  The copy is
    parameter-exact: the product reads its own embedding through `(1 + tanh theta)/2`, so
    the learner reads `squash(v)` and not `v`, and the composition is asserted by the
    seeding battery rather than assumed here.
    """
    held = require_model(model, "card_rows")
    table = held._module.emb.weight.detach().cpu().numpy()
    rows = numpy.array(
        table[FIRST_CARD_ROW : FIRST_CARD_ROW + CARD_ROWS], dtype=numpy.float64
    )
    if rows.shape != (CARD_ROWS, held._width):
        raise InvalidModel(
            "card_rows(model): the source %r's card rows are %r, and a seed copies %r "
            "(ASM-49)" % (repr(held), tuple(rows.shape), (CARD_ROWS, held._width))
        )
    digest = hashlib.sha256(
        numpy.ascontiguousarray(rows).tobytes()
    ).hexdigest()[:16]
    return rows, digest


def sources():
    """The declared source table, as a fresh copy (`ASM-51`)."""
    return {name: dict(row) for name, row in STRENGTH_SOURCES.items()}
