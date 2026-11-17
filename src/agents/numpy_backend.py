"""The forward and backward arithmetic in NumPy (`backends.md` §2).

One arithmetic order, written out: the input block, the trunk layers in ascending
order, the output layer; and for `learn` the same expressions again for the successor
from the target copy, then the backward pass layer by layer in descending order with
the ReLU derivative taken from the pre-activation's sign and the sparse mask applied
to the gradient as well as to the weight (`backends.md` §2 item 5).  Every parameter,
intermediate and accumulation is `float64` (§4).

**The token family's input block is the bounded embedding** (`input-read.md` §1-§2,
D-61): each addressed row is read through the one squash `row = (1 + tanh θ)/2`, so the
value the trunk consumes is a mean over the sequence's **real** rows — the positions
whose id is not the pad — of values in `(0, 1)` whatever the table holds, and the
backward pass carries the squash's derivative `(1 - tanh²θ)/2` gathered at each
addressed id, dividing by that same real count and scattering nothing into the pad's
row (D-79, D-80).  The dense family's block is untouched: `relu(x @ W_in + b_in)`, with
no squash anywhere (`normalisation.md` §3-§5).
"""

from __future__ import annotations

import numpy

DTYPE = numpy.float64

#: The one pad of the token encoding: the id a fixed-width sequence leaves where a
#: decision carries no token, and not a token itself (`card-tokens.md` §3, D-79).  The
#: pool and its gradient read it once here and nowhere else.
PAD = 0


class State:
    """The online and target parameters, the sparse masks and the kept slots."""

    __slots__ = ("params", "masks", "kept")

    def __init__(self, params, masks, layout):
        self.params = numpy.array(params, dtype=DTYPE)
        self.masks = numpy.array(masks, dtype=DTYPE)
        if layout.sparse:
            kept = []
            for layer in range(layout.trunk):
                start = layer * layout.mask_length
                block = self.masks[start : start + layout.mask_length]
                kept.append(numpy.flatnonzero(block > 0.5).astype(numpy.int64))
            self.kept = tuple(kept)
        else:
            self.kept = ()


def new_state(layout, parameters, masks):
    """A fresh learner's state: the online parameters, their target copy, the masks."""
    full = numpy.empty(2 * layout.count, dtype=DTYPE)
    full[: layout.count] = numpy.asarray(parameters, dtype=DTYPE)
    full[layout.count :] = full[: layout.count]
    return State(full, masks, layout)


def load_state(layout, params, masks):
    """A restored state: the `2·P + M` array a checkpoint carries, already split."""
    return State(numpy.asarray(params, dtype=DTYPE), numpy.asarray(masks, dtype=DTYPE), layout)


def parameters(state):
    """A copy of the whole `2·P` parameter array, online values first."""
    return numpy.array(state.params, dtype=DTYPE)


def masks(state):
    """A copy of the `M` sparse mask values, `0.0`/`1.0` in ascending layer order."""
    return numpy.array(state.masks, dtype=DTYPE)


def copy_online_to_target(state, layout):
    """`rule.md` §3's refresh: every parameter, in the declaration order."""
    count = layout.count
    state.params[count : 2 * count] = state.params[:count]


def _weight(state, layout, layer, base):
    """One trunk layer's weight matrix, its mask materialised before the matmul."""
    offset, length = layout.trunk_w[layer]
    values = state.params[base + offset : base + offset + length]
    if not layout.sparse:
        return values.reshape(layout.width, layout.width)
    matrix = numpy.zeros(layout.mask_length, dtype=DTYPE)
    matrix[state.kept[layer]] = values
    return matrix.reshape(layout.width, layout.width)


def _pooled(rows, real, width):
    """The mean of the sequence's **real** rows, and zeros when it has none.

    `real` marks the positions whose id is not `PAD`.  The denominator is the count of
    those positions, never `len(rows)`: a pad position carries no token, so it is no part
    of the value the trunk reads (D-79, `backends.md` §2 item 1).  A sequence that is
    padding throughout addressed no row at all and therefore has **no** mean — the width
    is a fixed allocation and not a statement that this decision carried a token — so its
    pooled value is the **zero vector**, chosen rather than computed: an empty mean would
    divide by zero.  The zero vector is the one value the squash cannot produce, which is
    what makes "this observation carried no token" a distinct value in the trunk, and it is
    the value the frozen card model's own masked pool reads when its mask is empty
    (`features/cardmodel.py`).
    """
    count = int(real.sum())
    if count == 0:
        return numpy.zeros(width, dtype=DTYPE)
    return rows[real].sum(axis=0) / DTYPE(count)


def forward(state, layout, observation, target=False, need_cache=True):
    """The three values of one observation, and the cache the backward pass reads.

    The cache's `input` is the block the backward pass differentiates through, and for
    the token family it is the value the trunk actually consumed: `(rows, ids)`, one
    squashed row per position in the observation's own order and the ids those rows were
    read at — never the raw table, which the trunk never sees (`input-read.md` §3).  For
    the dense family it stays `(observation, pre_activation)`.
    """
    base = layout.count if target else 0
    width = layout.width
    cache = None
    if layout.dense:
        offset, length = layout.w_in
        weights = state.params[base + offset : base + offset + length].reshape(
            layout.input_dim, width
        )
        bias = state.params[base + layout.b_in : base + layout.b_in + width]
        dense = numpy.asarray(observation, dtype=DTYPE)
        pre = dense @ weights + bias
        carried = numpy.maximum(pre, 0.0)
        block = (dense, pre)
    else:
        offset, length = layout.w_in
        table = state.params[base + offset : base + offset + length].reshape(
            layout.input_dim, width
        )
        ids = numpy.asarray(observation, dtype=numpy.int64)
        # The bounded embedding (`input-read.md` §1, `normalisation.md` §3): each
        # addressed row is read through one squash, so every row lies in (0, 1) for
        # every finite parameter value and so does any mean of rows.
        rows = (1.0 + numpy.tanh(table[ids])) / 2.0
        # The pool covers the positions that carry a token and not the width the
        # encoding reserves: `PAD` is a slot's filler, not a token, and at six seats a
        # preflop decision is 14 real ids of 122, so an unmasked mean would make one
        # constant vector 89 % of the value the trunk consumes (D-79, D-80).
        real = ids != PAD
        carried = _pooled(rows, real, width)
        block = (rows, ids)
    layers = []
    for layer in range(layout.trunk):
        matrix = _weight(state, layout, layer, base)
        b_off = base + layout.trunk_b[layer]
        bias = state.params[b_off : b_off + width]
        pre = carried @ matrix + bias
        rectified = numpy.maximum(pre, 0.0)
        layers.append((carried, matrix, pre))
        carried = carried + rectified if layout.residual else rectified
    offset, length = layout.w_out
    output = state.params[base + offset : base + offset + length].reshape(
        width, layout.actions
    )
    output_bias = state.params[
        base + layout.b_out : base + layout.b_out + layout.actions
    ]
    values = carried @ output + output_bias
    if need_cache:
        cache = {"carried": carried, "layers": layers, "output": output, "input": block}
    return values, cache


def apply(state, layout, cache, action, delta, rate):
    """`rule.md` §3's step: `θ ← θ + α·td·∂q[a]/∂θ`, on the online parameters."""
    width = layout.width
    gradient = numpy.zeros(layout.count, dtype=DTYPE)
    chosen = numpy.zeros(layout.actions, dtype=DTYPE)
    chosen[int(action)] = 1.0
    offset, length = layout.w_out
    gradient[offset : offset + length] = numpy.outer(cache["carried"], chosen).reshape(-1)
    gradient[layout.b_out : layout.b_out + layout.actions] = chosen
    upstream = cache["output"] @ chosen
    for layer in range(layout.trunk - 1, -1, -1):
        carried, matrix, pre = cache["layers"][layer]
        below = upstream * (pre > 0.0)
        offset, length = layout.trunk_w[layer]
        delta_w = numpy.outer(carried, below).reshape(-1)
        if layout.sparse:
            gradient[offset : offset + length] = delta_w[state.kept[layer]]
        else:
            gradient[offset : offset + length] = delta_w
        b_off = layout.trunk_b[layer]
        gradient[b_off : b_off + width] = below
        back = below @ matrix.T
        upstream = upstream + back if layout.residual else back
    if layout.dense:
        dense, pre = cache["input"]
        below = upstream * (pre > 0.0)
        offset, length = layout.w_in
        gradient[offset : offset + length] = numpy.outer(dense, below).reshape(-1)
        gradient[layout.b_in : layout.b_in + width] = below
    else:
        rows, ids = cache["input"]
        offset, length = layout.w_in
        gathered = numpy.zeros((layout.input_dim, width), dtype=DTYPE)
        # The squash's derivative, read off the squashed row the forward pass stored:
        # `(1 - tanh²θ)/2` is `(1 - (2·row - 1)²)/2` (`input-read.md` §2).  Dropping it
        # would step the table by a gradient no squash produces, and clipping instead
        # of squashing would zero it exactly where the reward scale pushed hardest.
        slope = (1.0 - (2.0 * rows - 1.0) ** 2) / 2.0
        # The scatter is the pool's own mask: the step divides by the **real** count the
        # forward pass pooled over, and only an addressed, non-pad position is scattered
        # into, so the pad's row receives **no** gradient at all and stays exactly where
        # it was (D-79, D-80).  A sequence that is padding throughout pooled to the zero
        # vector `_pooled` chose and addressed no row, so it has no share to divide and
        # the whole block's gradient stays zero rather than dividing by zero.
        real = ids != PAD
        count = int(real.sum())
        if count:
            share = (upstream / DTYPE(count)) * slope
            numpy.add.at(gathered, ids[real], share[real])
        gradient[offset : offset + length] = gathered.reshape(-1)
    state.params[: layout.count] += (rate * delta) * gradient
