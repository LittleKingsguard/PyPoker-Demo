"""The forward and backward arithmetic in NumPy (`backends.md` §2).

One arithmetic order, written out: the input block, the trunk layers in ascending
order, the output layer; and for `learn` the same expressions again for the successor
from the target copy, then the backward pass layer by layer in descending order with
the ReLU derivative taken from the pre-activation's sign and the sparse mask applied
to the gradient as well as to the weight (`backends.md` §2 item 5).  Every parameter,
intermediate and accumulation is `float64` (§4).
"""

from __future__ import annotations

import numpy

DTYPE = numpy.float64


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


def forward(state, layout, observation, target=False, need_cache=True):
    """The three values of one observation, and the cache the backward pass reads."""
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
        carried = table[ids].mean(axis=0)
        block = (table, ids)
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
    output = state.params[base + offset : base + offset + length].reshape(width, 3)
    output_bias = state.params[base + layout.b_out : base + layout.b_out + 3]
    values = carried @ output + output_bias
    if need_cache:
        cache = {"carried": carried, "layers": layers, "output": output, "input": block}
    return values, cache


def apply(state, layout, cache, action, delta, rate):
    """`rule.md` §3's step: `θ ← θ + α·td·∂q[a]/∂θ`, on the online parameters."""
    width = layout.width
    gradient = numpy.zeros(layout.count, dtype=DTYPE)
    chosen = numpy.zeros(3, dtype=DTYPE)
    chosen[int(action)] = 1.0
    offset, length = layout.w_out
    gradient[offset : offset + length] = numpy.outer(cache["carried"], chosen).reshape(-1)
    gradient[layout.b_out : layout.b_out + 3] = chosen
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
        table, ids = cache["input"]
        offset, length = layout.w_in
        gathered = numpy.zeros((layout.input_dim, width), dtype=DTYPE)
        numpy.add.at(gathered, ids, upstream / len(ids))
        gradient[offset : offset + length] = gathered.reshape(-1)
    state.params[: layout.count] += (rate * delta) * gradient
