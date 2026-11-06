"""The seven kinds: their stacks, the one parameter formula, the initialisation order.

`architecture.md` §2-§5 expressed as data and as a draw.  A `Layout` says where every
tensor of one kind at one set of settings lives in the flat parameter vector, in the
declaration order of `architecture.md` §4; `_draw` works that order from one
`numpy.random.Generator(numpy.random.PCG64(seed))` — He-normal weights, zero biases
that draw nothing, and the sparse masks last — for both backends, the torch one
copying these values instead of drawing its own (`backends.md` §2, §4).
"""

from __future__ import annotations

import numpy

from . import declarations


def kind_row(kind):
    """The catalogue row of one kind, or a `KeyError` naming it."""
    return declarations.kind_row(kind)


def trunk_layers(kind, depth):
    """`D`: the number of `W -> W` trunk layers, which is exactly one for `wide`."""
    return 1 if kind == "wide" else int(depth)


def kept_slots(width, sparsity):
    """`k = round((1 - s)·W²)`: the weights one sparse trunk layer keeps."""
    return int(round((1.0 - float(sparsity)) * int(width) * int(width)))


def _param_count_for(kind, width, depth, sparsity=0.0):
    """`architecture.md` §5's sum at those settings, and nothing else.

    The input block first (the dense matrix with its bias, or the embedding table),
    then `D` trunk layers, then the output layer.  `sparse` replaces the trunk term
    with `D·(k + W)` where `k = round((1 - s)·W²)`; the target copy, the masks and the
    schedule are not counted (`architecture.md` §5, ASM-10).
    """
    row = kind_row(kind)
    layer_width = int(width)
    layers = trunk_layers(kind, depth)
    total = row["observation_size"] * layer_width
    if row["observation"] == declarations.DENSE_FAMILY:
        total += layer_width
    if kind == "sparse":
        total += layers * (kept_slots(layer_width, sparsity) + layer_width)
    else:
        total += layers * (layer_width * layer_width + layer_width)
    return total + 3 * layer_width + 3


class Layout:
    """One kind at one set of settings: every tensor's offset and length.

    The declaration order of `architecture.md` §4 is this class's field order: the
    input block, the trunk layers in ascending order, the output layer.  The sparse
    masks live in a section of their own (the checkpoint's `[2P, 2P + M)`), and a
    sparse trunk layer's weight block holds only the `k` slots its mask keeps.

    The two optional settings are **resolved from the kind**, never from a flag: the
    connection is `kind == "residual"` and the connectivity is the spec's `s` for
    `sparse` and `0.0` for every other kind (`architecture.md` §3).  A caller's
    `residual` flag mirrors the kind and is read nowhere.
    """

    __slots__ = (
        "kind",
        "family",
        "dense",
        "input_dim",
        "width",
        "trunk",
        "sparsity",
        "residual",
        "sparse",
        "w_in",
        "b_in",
        "trunk_w",
        "trunk_b",
        "w_out",
        "b_out",
        "block_lengths",
        "count",
        "mask_count",
        "mask_length",
    )

    def __init__(self, kind, width, depth, sparsity, size, family):
        row = kind_row(kind)
        self.kind = kind
        self.family = family
        self.dense = family == declarations.DENSE_FAMILY
        self.width = int(width)
        self.trunk = trunk_layers(kind, depth)
        self.sparse = kind == "sparse"
        # `architecture.md` §3: the kind decides.  `residual` adds the delta whatever
        # the spec says, `plain` replaces whatever it says, and only `sparse` reads
        # the connectivity — for every other kind the kind's own `0.0` stands.
        self.sparsity = float(sparsity) if self.sparse else 0.0
        self.residual = kind == "residual"
        self.input_dim = int(size)
        self.mask_length = self.width * self.width
        layer_width = self.width
        offset = 0
        self.w_in = (offset, self.input_dim * layer_width)
        offset += self.w_in[1]
        if self.dense:
            self.b_in = offset
            offset += layer_width
        else:
            self.b_in = None
        kept = kept_slots(layer_width, self.sparsity) if self.sparse else None
        self.block_lengths = tuple(
            kept if self.sparse else self.mask_length for _ in range(self.trunk)
        )
        self.trunk_w = []
        self.trunk_b = []
        for length in self.block_lengths:
            self.trunk_w.append((offset, length))
            offset += length
            self.trunk_b.append(offset)
            offset += layer_width
        self.w_out = (offset, 3 * layer_width)
        offset += self.w_out[1]
        self.b_out = offset
        offset += 3
        self.count = offset
        self.mask_count = self.trunk * self.mask_length if self.sparse else 0


def layout_for(kind, width, depth, sparsity=0.0, size=None, family=None):
    """The `Layout` of one kind, sized by `size` or by the kind's declared size."""
    row = kind_row(kind)
    if size is None:
        size = row["observation_size"]
    if family is None:
        family = row["observation"]
    return Layout(kind, width, depth, sparsity, size, family)


def _draw(kind, width, depth, sparsity, seed, size=None, family=None):
    """`architecture.md` §4's steps 1-4: the parameters, then the masks.

    One generator, one order: the input block, the trunk layers in ascending order,
    the output layer, and — for `sparse` last — each trunk layer's mask.  Every bias
    is exactly `0.0` and draws nothing, so the draw sequence is over weight matrices
    only and `sparsity` changes none of the values it does not mask.
    """
    layout = layout_for(kind, width, depth, sparsity, size, family)
    layer_width = layout.width
    generator = numpy.random.Generator(numpy.random.PCG64(int(seed)))
    parameters = numpy.zeros(layout.count, dtype=numpy.float64)

    offset, length = layout.w_in
    fan_in = layout.input_dim
    parameters[offset : offset + length] = (
        generator.standard_normal((fan_in, layer_width)) * numpy.sqrt(2.0 / fan_in)
    ).reshape(-1)

    trunk = []
    for _layer in range(layout.trunk):
        trunk.append(
            generator.standard_normal((layer_width, layer_width))
            * numpy.sqrt(2.0 / layer_width)
        )

    offset, length = layout.w_out
    parameters[offset : offset + length] = (
        generator.standard_normal((layer_width, 3)) * numpy.sqrt(2.0 / layer_width)
    ).reshape(-1)

    masks = numpy.zeros(layout.mask_count, dtype=numpy.float64)
    kept = []
    if layout.sparse:
        for layer in range(layout.trunk):
            wanted = layout.block_lengths[layer]
            slots = numpy.sort(generator.permutation(layout.mask_length)[:wanted])
            kept.append(slots)
            masks[layer * layout.mask_length + slots] = 1.0

    for layer, matrix in enumerate(trunk):
        offset, length = layout.trunk_w[layer]
        flat = matrix.reshape(-1)
        parameters[offset : offset + length] = flat[kept[layer]] if layout.sparse else flat

    return layout, parameters, masks, tuple(kept)


def initial_draw(kind, width, depth, sparsity, seed, size=None, family=None):
    """The whole draw: the layout, `[0, P)`'s values, the masks and the kept slots."""
    return _draw(kind, width, depth, sparsity, seed, size, family)


def _initial_parameters(kind, width, depth, sparsity, seed):
    """`architecture.md` §4's steps 1-3 as one 1-D `float64` array in declaration order."""
    return _draw(kind, width, depth, sparsity, seed)[1]
