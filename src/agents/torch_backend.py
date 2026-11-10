"""The same arithmetic in PyTorch (`backends.md` §1-§4).

One arithmetic order, expressed twice: the input block, the trunk layers in ascending
order, the output layer, the successor's values from the target copy, and the
backward pass written out in descending order.  `torch.autograd` is not used,
because an autograd graph's summation order is the framework's and not this design's
(§2).  Every value is `torch.float64`, every tensor is created on CPU, and the
parameters are the values `model._initial_parameters` drew — copied, never redrawn
with `torch.randn` (§2, §4, `architecture.md` §4).

This is the only module of the project that imports `torch`, and it does so inside a
function, on the first torch learner's build (§4).
"""

from __future__ import annotations

import numpy

DTYPE = "float64"


def _torch():
    """The library, imported on the first torch learner's build and nowhere else."""
    import torch

    return torch


class State:
    """The online and target parameters, the sparse masks and the kept slots."""

    __slots__ = ("params", "masks", "kept")

    def __init__(self, params, masks, layout):
        torch = _torch()
        self.params = torch.from_numpy(numpy.array(params, dtype=numpy.float64))
        self.masks = torch.from_numpy(numpy.array(masks, dtype=numpy.float64))
        if layout.sparse:
            kept = []
            for layer in range(layout.trunk):
                start = layer * layout.mask_length
                block = numpy.array(masks, dtype=numpy.float64)[
                    start : start + layout.mask_length
                ]
                kept.append(
                    torch.from_numpy(numpy.flatnonzero(block > 0.5).astype(numpy.int64))
                )
            self.kept = tuple(kept)
        else:
            self.kept = ()


def new_state(layout, parameters, masks):
    """A fresh learner's state: the online parameters, their target copy, the masks."""
    online = numpy.array(parameters, dtype=numpy.float64)
    full = numpy.empty(2 * layout.count, dtype=numpy.float64)
    full[: layout.count] = online
    full[layout.count :] = online
    return State(full, masks, layout)


def load_state(layout, params, masks):
    """A restored state: the `2·P + M` array a checkpoint carries, already split."""
    return State(params, masks, layout)


def parameters(state):
    """A copy of the whole `2·P` parameter array, online values first."""
    return numpy.array(state.params.detach().numpy(), dtype=numpy.float64)


def masks(state):
    """A copy of the `M` sparse mask values, `0.0`/`1.0` in ascending layer order."""
    return numpy.array(state.masks.detach().numpy(), dtype=numpy.float64)


def copy_online_to_target(state, layout):
    """`rule.md` §3's refresh: every parameter, in the declaration order."""
    count = layout.count
    state.params[count : 2 * count] = state.params[:count]


def _weight(state, layout, layer, base):
    """One trunk layer's weight matrix, its mask materialised before the matmul."""
    torch = _torch()
    offset, length = layout.trunk_w[layer]
    values = state.params[base + offset : base + offset + length]
    if not layout.sparse:
        return values.reshape(layout.width, layout.width)
    matrix = torch.zeros(layout.mask_length, dtype=torch.float64)
    matrix[state.kept[layer]] = values
    return matrix.reshape(layout.width, layout.width)


def forward(state, layout, observation, target=False, need_cache=True):
    """The three values of one observation, and the cache the backward pass reads."""
    torch = _torch()
    base = layout.count if target else 0
    width = layout.width
    cache = None
    if layout.dense:
        offset, length = layout.w_in
        weights = state.params[base + offset : base + offset + length].reshape(
            layout.input_dim, width
        )
        bias = state.params[base + layout.b_in : base + layout.b_in + width]
        dense = torch.from_numpy(
            numpy.ascontiguousarray(
                numpy.asarray(observation, dtype=numpy.float64).reshape(-1)
            )
        )
        pre = dense @ weights + bias
        carried = torch.clamp_min(pre, 0.0)
        block = (dense, pre)
    else:
        offset, length = layout.w_in
        table = state.params[base + offset : base + offset + length].reshape(
            layout.input_dim, width
        )
        ids = torch.from_numpy(
            numpy.ascontiguousarray(
                numpy.asarray(observation, dtype=numpy.int64).reshape(-1)
            )
        )
        carried = table.index_select(0, ids).mean(dim=0)
        block = (table, ids)
    layers = []
    for layer in range(layout.trunk):
        matrix = _weight(state, layout, layer, base)
        b_off = base + layout.trunk_b[layer]
        bias = state.params[b_off : b_off + width]
        pre = carried @ matrix + bias
        rectified = torch.clamp_min(pre, 0.0)
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
    torch = _torch()
    width = layout.width
    gradient = torch.zeros(layout.count, dtype=torch.float64)
    chosen = torch.zeros(layout.actions, dtype=torch.float64)
    chosen[int(action)] = 1.0
    offset, length = layout.w_out
    gradient[offset : offset + length] = torch.outer(cache["carried"], chosen).reshape(-1)
    gradient[layout.b_out : layout.b_out + layout.actions] = chosen
    upstream = cache["output"] @ chosen
    for layer in range(layout.trunk - 1, -1, -1):
        carried, matrix, pre = cache["layers"][layer]
        below = upstream * (pre > 0.0)
        offset, length = layout.trunk_w[layer]
        delta_w = torch.outer(carried, below).reshape(-1)
        if layout.sparse:
            gradient[offset : offset + length] = delta_w.index_select(0, state.kept[layer])
        else:
            gradient[offset : offset + length] = delta_w
        b_off = layout.trunk_b[layer]
        gradient[b_off : b_off + width] = below
        back = below @ matrix.t()
        upstream = upstream + back if layout.residual else back
    if layout.dense:
        dense, pre = cache["input"]
        below = upstream * (pre > 0.0)
        offset, length = layout.w_in
        gradient[offset : offset + length] = torch.outer(dense, below).reshape(-1)
        gradient[layout.b_in : layout.b_in + width] = below
    else:
        table, ids = cache["input"]
        offset, length = layout.w_in
        gathered = torch.zeros(
            (layout.input_dim, width), dtype=torch.float64
        )
        share = (upstream / float(len(ids))).unsqueeze(0).expand(len(ids), width)
        gathered.index_add_(0, ids, share)
        gradient[offset : offset + length] = gathered.reshape(-1)
    state.params[: layout.count] += (rate * delta) * gradient
