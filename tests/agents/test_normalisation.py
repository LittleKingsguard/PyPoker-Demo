"""AGT-20 — the token family's bounded input read: one squash, its cache, its derivative.

Drives `docs/L1/normalisation.md` §1, §3, §5 (D-61) at this module's own boundary. §3
states the token reading of "bounded" in two parts, and only the second reaches the
network: the label is an id inside the shape's vocabulary, and **the value the trunk
consumes is the mean of the addressed embedding rows read through the bounded embedding**
`row = (1 + tanh θ)/2`, so every row lies in `(0, 1)` and so does any mean of rows,
"whatever the parameters do". §1 says why the token family is where the change bites — its
only magnitude is the table, which is where the reward scale lands — and §5 says where
INV-2's second half is asserted: here, because the cache's `input` block is a value no entry
point returns. `act` answers an index, `learn` two statistics, `save` a path, so a sweep of
real hands can say what `features.encode` emitted but never *what the trunk consumed* or
*what derivative the table was stepped by* — D-61's two token-side claims, which only a case
calling a backend's `forward` and reading the returned cache can state (`battery.md` §5,
`architecture.md` §2, `rule.md` §3, §8).

The five cases: **AGT-20.1** the cache's `input` is `(rows, ids)` and the trunk consumed
exactly `rows.mean(axis=0)`, recomputed through the whole pass from the container's
parameters and discriminated from the old raw-row arithmetic; **AGT-20.2** a table doctored
to alternating `±1e6` still feeds the trunk a value in `[0, 1]` in both backends, while the
raw mean of the same rows keeps a magnitude of the doctored order; **AGT-20.3** the table
block of `P1 − P0` is `(rate·td)·Σ_ids (upstream/len(ids))·(1 − (2·row − 1)²)/2`, it moved,
and the derivative-free expression differs from it; **AGT-20.4** the two backends agree on
one parameter set and one observation, before and after the doctoring; **AGT-20.5** what the
change does not move — `param_count`, a container's round trip, and the dense family's
forward, which carries no squash anywhere (`architecture.md` §2, §5, `checkpoint.md` §1-§4).

Every number is read from the module or invented (`battery.md` §4, D-15): vocabulary, width,
offsets, counts and parameter count come from the container `save` writes (`checkpoint.md`
§2.1) and the rate from `agents.learners()['hyper']`. Below the ten entry points nothing is
spelled but the two backends' `forward`, a learner's `.state`, `.layout` and `.backend`, and
the one internal `rule.md` §8 declares for §5's formula. The design of record is
`input-read.md` — §1 the bounded embedding, §2 the derivative, §3 what the cache carries,
§4 what the change leaves alone, §5 the assignment of these five cases to this battery —
which is the same statements `normalisation.md` §3 and `backends.md` §2 publish.
"""

import io
import os
import unittest

import numpy as np

from _agents_support import (
    AgentsCase,
    container_document,
    declared_internal,
    declared_module,
    decisions,
    finite_float,
    hyper,
    plain_int,
    token_encoder,
    transition,
    write_container,
)

#: Invented instances: no number below appears in a design document. The width is even on
#: purpose — the doctored table alternates sign along the block's flat index, and with an
#: even width that sign is a function of the row's own coordinate rather than of the row's
#: index, so a mean over an observation's ids cannot cancel to nothing.
TOKEN_WIDTH, TOKEN_DEPTH = 8, 2
DENSE_WIDTH, DENSE_DEPTH = 8, 2

#: The magnitude the doctored tables are set to: far past the band a squashed row can leave,
#: and far past what a raw mean of such rows would carry into the trunk. No case calls
#: `learn` on a doctored learner, so the declared parameter band's own guard is not in play.
DOCTORED_MAGNITUDE = 1e6

#: The invented reward of AGT-20.3's terminal transition, and the invented rewards, episode
#: boundary and read count of AGT-20.5 (`rule.md` §2, D-43).
PROBE_REWARD = 0.75
BATCH_REWARDS = (2.5, -1.25, 4.0)
BATCH_EPISODE = 6607
DECIDED = 6


def squashed(values):
    """`row = (1 + tanh θ)/2`, the one squash of the token family's input read (§3, §2)."""
    return (1.0 + np.tanh(np.asarray(values, dtype=np.float64))) / 2.0


def squash_slope(rows):
    """`(1 − tanh²θ)/2` off a squashed row: the derivative the backward pass carries.

    `backends.md` §2 item 5 makes the backward pass the explicit semi-gradient, and
    `1 − tanh²θ` is `1 − (2·row − 1)²` once the row is the value the forward pass stored.
    """
    return (1.0 - (2.0 * np.asarray(rows, dtype=np.float64) - 1.0) ** 2) / 2.0


class NormalisationTest(AgentsCase):
    """The bounded embedding: the cache's input, the band it keeps, and its derivative."""

    # -- the readers a case needs, all off declared spellings ------------------
    def backend_module(self, name):
        """`agents.<name>_backend`, the one module that performs that backend's arithmetic.

        `backends.md` §1-§2 make each backend one module; `declared_module` hands an `agents`
        submodule back or raises `SurfaceAbsent`, so an absent `src/agents/` is one clean
        failure per case and never a collection error (`battery.md` §5, D-13).
        """
        return declared_module("%s_backend" % (name,))

    def workspace(self):
        """This case's own scratch directory, one per case and removed with it."""
        if getattr(self, "_workspace", None) is None:
            self._workspace = self.tempdir()
        return self._workspace

    def token_learner(self, backend="numpy"):
        """One `token-embedding` learner at this battery's invented width and depth.

        A `card-tokens` encoder is handed to the build, so the learner's sizing record is the
        encoding's — a `(40,) int32` sequence and the encoder's own vocabulary — and the
        observations a case forwards are real decisions' encodings of it (`architecture.md`
        §1, §6, `features/surface.md` §5).
        """
        return self.build(
            backend=backend,
            kind="token-embedding",
            width=TOKEN_WIDTH,
            depth=TOKEN_DEPTH,
            encoder=token_encoder(),
        )

    def document(self, path):
        """`(metadata, array)` of one container: the document, and the `2·P + M` array."""
        metadata, blob = container_document(path)
        return metadata, np.load(io.BytesIO(blob), allow_pickle=False)

    def saved(self, learner, name):
        """One container of this learner, written into this case's own directory."""
        return self.agents().save(learner, os.path.join(self.workspace(), name))

    def tensor_record(self, metadata, name):
        """One tensor's `{name, shape, offset, count}` record out of `params.tensors`.

        `checkpoint.md` §2.1 makes that table the one statement of where a block lives, so no
        offset, count or width is written down in this file.
        """
        records = [item for item in metadata["params"]["tensors"] if item["name"] == name]
        if len(records) != 1:
            self.fail(
                "the container's params.tensors table does not name %r exactly once, so the "
                "block this case reads has no declared position (checkpoint.md §2.1): %r"
                % (name, [item["name"] for item in metadata["params"]["tensors"]])
            )
        return records[0]

    def has_tensor(self, metadata, name):
        """Whether the container records a tensor of that name at all."""
        return any(item["name"] == name for item in metadata["params"]["tensors"])

    def tensor(self, array, metadata, name):
        """One tensor's values, read at the `offset`/`count` its container records."""
        record = self.tensor_record(metadata, name)
        offset = plain_int(record["offset"], "params.tensors[%r].offset" % (name,))
        count = plain_int(record["count"], "params.tensors[%r].count" % (name,))
        return np.array(array[offset : offset + count], copy=True)

    def table(self, array, metadata):
        """The embedding table `E` at the `(V, W)` shape its container records.

        `architecture.md` §2 gives the token input block that shape and no bias, and §5 makes
        `V·W` its whole parameter term.
        """
        shape = tuple(
            plain_int(size, "params.tensors['input.weights'].shape")
            for size in self.tensor_record(metadata, "input.weights")["shape"]
        )
        if len(shape) != 2:
            self.fail(
                "the token family's input block is recorded at %r and architecture.md §2 gives "
                "it the table shape `(V, W)`" % (shape,)
            )
        return self.tensor(array, metadata, "input.weights").reshape(shape), shape

    def recomputed(self, metadata, array, carried):
        """The rest of the pass from the container's parameters, given what the trunk consumes.

        `carried` is the mean of the squashed rows for the token family and
        `relu(x @ W_in + b_in)` for the dense one. From there it is `architecture.md` §2's
        walk — every trunk layer `relu(h @ W_ℓ + b_ℓ)` ascending, then `h @ W_out + b_out` —
        and `token-embedding` and `naive-stack` read neither the residual rule nor a mask, so
        the plain chain is the declared one (`checkpoint.md` §2.1).
        """
        width = plain_int(metadata["settings"]["width"], "settings.width")
        carried = np.asarray(carried, dtype=np.float64)
        layers = 0
        while self.has_tensor(metadata, "trunk.%d.weights" % (layers + 1,)):
            layer = layers + 1
            matrix = self.tensor(array, metadata, "trunk.%d.weights" % (layer,))
            bias = self.tensor(array, metadata, "trunk.%d.bias" % (layer,))
            carried = np.maximum(carried @ matrix.reshape(width, width) + bias, 0.0)
            layers += 1
        self.assertGreaterEqual(
            layers,
            1,
            "the container records no trunk layer, so this recomputation would be the input "
            "block and the head alone and not architecture.md §2's stack",
        )
        actions = plain_int(
            self.tensor_record(metadata, "output.bias")["count"],
            "params.tensors['output.bias'].count",
        )
        output = self.tensor(array, metadata, "output.weights").reshape(width, actions)
        return carried @ output + self.tensor(array, metadata, "output.bias")

    def assert_unit_band(self, label, rows):
        """Assert one arm's cached rows and their mean lie in `[0, 1]`, and answer the mean.

        §3 bounds the read in two steps — every row in `(0, 1)`, hence any mean of rows — and
        `[0, 1]` is the closed form a doctored table is held to: a saturated row reads exactly
        `0.0` or `1.0` without leaving the band.
        """
        rows = np.asarray(rows, dtype=np.float64)
        carried = rows.mean(axis=0)
        for what, low, high in (
            ("a cached row", float(rows.min()), float(rows.max())),
            ("the value the trunk consumed", float(carried.min()), float(carried.max())),
        ):
            self.assertGreaterEqual(
                low,
                0.0,
                "%s, on %s, read %r, below the 0 a mean of values in (0, 1) cannot cross "
                "(normalisation.md §3, §5)" % (what, label, low),
            )
            self.assertLessEqual(
                high,
                1.0,
                "%s, on %s, read %r, above the 1 a mean of values in (0, 1) cannot cross "
                "(normalisation.md §3, §5)" % (what, label, high),
            )
        return carried

    def doctored(self, source, label, sign, backend=None):
        """One container whose `input.weights` block is alternating `±DOCTORED_MAGNITUDE`.

        The pattern alternates along the block's flat index, `+M` first when `sign` is `+1` and
        `−M` first when it is `−1`, so the two variants are one table's mirror image. The array
        is rewritten into a buffer and `write_container` writes the file back, so no shipped
        container is touched (`checkpoint.md` §2, §3); a named `backend` writes the same bytes
        with that backend recorded, which is how one parameter set reaches the torch arm, the
        geometry being backend-independent (`backends.md` §1-§2). Answers `(path, table)` at
        the block's recorded `(V, W)` shape.
        """
        metadata, array = self.document(source)
        record = self.tensor_record(metadata, "input.weights")
        offset = plain_int(record["offset"], "params.tensors['input.weights'].offset")
        count = plain_int(record["count"], "params.tensors['input.weights'].count")
        shape = tuple(
            plain_int(size, "params.tensors['input.weights'].shape") for size in record["shape"]
        )
        rewritten = np.array(array, copy=True)
        rewritten[offset : offset + count] = np.where(
            np.arange(count) % 2 == 0,
            float(sign) * DOCTORED_MAGNITUDE,
            -float(sign) * DOCTORED_MAGNITUDE,
        )
        if backend is not None:
            metadata["backend"] = backend
        buffer = io.BytesIO()
        np.save(buffer, np.ascontiguousarray(rewritten), allow_pickle=False)
        path = write_container(os.path.join(self.workspace(), label), metadata, buffer.getvalue())
        return path, rewritten[offset : offset + count].reshape(shape)

    def snapshot(self, cache):
        """The forward cache's blocks copied, so the cache stays the pre-step one.

        A necessary copy, not a convenience: the trunk matrices and the output matrix the
        forward pass stores are views into the live `2·P` array, so they follow the parameters
        a `learn` call moves, and differentiating them afterwards would compare a step to a
        different step (`backends.md` §2, `rule.md` §3).
        """
        rows, ids = cache["input"]
        return {
            "output": np.array(cache["output"], copy=True),
            "layers": tuple(
                tuple(np.array(part, copy=True) for part in layer) for layer in cache["layers"]
            ),
            "rows": np.array(rows, copy=True),
            "ids": np.array(ids, copy=True),
        }

    def table_gradient(self, held, action, shape, with_slope=True):
        """The table block's expected gradient for one action, from a cache snapshot.

        `backends.md` §2 item 5's walk: `upstream = output @ chosen`, then each trunk layer
        descending with the ReLU derivative taken from that layer's pre-activation, the input
        block's upstream last; its table gradient is the gather of `(upstream / len(ids)) ·
        slope` at the addressed ids, `slope` being the squash's `(1 − (2·row − 1)²)/2`.
        `with_slope=False` is the derivative-free expression AGT-20.3 discriminates against
        (`normalisation.md` §3, `rule.md` §3).
        """
        chosen = np.zeros(int(np.asarray(held["output"]).shape[1]), dtype=np.float64)
        chosen[int(action)] = 1.0
        upstream = held["output"] @ chosen
        for _carried, matrix, pre in reversed(held["layers"]):
            upstream = (upstream * (pre > 0.0)) @ matrix.T
        share = upstream / float(len(held["ids"]))
        if with_slope:
            share = share * squash_slope(held["rows"])
        gathered = np.zeros(shape, dtype=np.float64)
        np.add.at(gathered, held["ids"], share)
        return gathered

    def invented_batch(self, rows):
        """One invented batch over real decisions' own token observations.

        The observations are real, so the batch is one the module's encoder could have emitted;
        the actions, rewards, terminal flags and episode boundary are this battery's invention
        (`battery.md` §4, D-15). Each action is a member of that decision's own mask and the
        batch holds both arms of `rule.md` §2 (`records.md` §4, D-43).
        """
        records = []
        for position, row in enumerate(rows):
            mask = tuple(row["mask"])
            records.append(
                transition(
                    row["tokens"],
                    action=mask[position % len(mask)],
                    reward=float(BATCH_REWARDS[position % len(BATCH_REWARDS)]),
                    terminal=position % 3 == 0,
                    legal=mask,
                    next_legal=mask,
                    next_observation=rows[(position + 1) % len(rows)]["tokens"],
                    episode=BATCH_EPISODE,
                )
            )
        return records

    # -- AGT-20.1 ----------------------------------------------------------
    def test_agt20_1_the_forward_cache_carries_the_squashed_rows_and_their_mean(self):
        """AGT-20.1 the token cache's `input` is `(rows, ids)` — the `(n, W)` rows `(1 + tanh θ)/2` at the observation's own ids, every entry strictly inside `(0, 1)` — and the trunk consumed exactly `rows.mean(axis=0)`, recomputed through the whole pass from the container's parameters, while the raw mean of the same rows differs from it by more than `1e-3` (`normalisation.md` §1, §3, §5, `architecture.md` §2, `backends.md` §2 item 1, D-61).

        §3's second part is the one that reaches the network, and the cache is the only place a
        case can see it happen: the block is the **value the trunk consumed**, `(rows, ids)`,
        never the raw table. The case pins the ids as the observation's own in its own position
        order, the rows as the squash of the container's table at those ids, the bound as open
        at both ends — a clip would read exactly `0.0` or `1.0` — and the mean as what the
        trunk read, by recomputing `relu(h @ W + b)` per trunk layer and `h @ W_out + b_out`
        (`architecture.md` §2, §5). The last assertion is the discriminating half: the old
        `table[ids].mean(axis=0)` differs by more than `1e-3`, so a pass that only renamed the
        cache block is red.
        """
        numpy_backend = self.backend_module("numpy")
        learner = self.token_learner("numpy")
        metadata, array = self.document(self.saved(learner, "agt20-1-token.pt"))
        table, shape = self.table(array, metadata)
        observation = decisions(1)[0]["tokens"]
        values, cache = numpy_backend.forward(
            learner.state, learner.layout, observation, need_cache=True
        )
        block = cache["input"]
        self.assertEqual(
            len(block),
            2,
            "the token cache's input is the 2-sequence `(rows, ids)`, and a block holding the "
            "table is the arithmetic D-61 replaced (normalisation.md §3, architecture.md §2)",
        )
        rows, ids = block
        rows = np.asarray(rows, dtype=np.float64)
        ids = np.asarray(ids)
        self.assertEqual(
            tuple(rows.shape),
            (len(observation), shape[1]),
            "the cached rows are one squashed row per position, each as wide as the table the "
            "container records: %r against %d positions and the (V, W) shape %r"
            % (tuple(rows.shape), len(observation), shape),
        )
        np.testing.assert_array_equal(
            ids,
            np.asarray(observation, dtype=np.int64),
            err_msg="the cached ids are not the observation's own, in its own position order, so "
            "the trunk would have read another observation (backends.md §2 item 1)",
        )
        np.testing.assert_allclose(
            rows,
            squashed(table[ids]),
            rtol=0.0,
            atol=1e-12,
            err_msg="the cached rows are not `(1 + tanh θ)/2` of the container's own table at "
            "those ids, so the bound of normalisation.md §3 is not the one the pass wrote: the "
            "token path's only magnitude is this row",
        )
        self.assertGreater(
            float(rows.min()),
            0.0,
            "a cached row read exactly 0.0, and the squash lies strictly inside (0, 1) for every "
            "finite parameter value — a clip reads the closed bound instead (normalisation.md §3)",
        )
        self.assertLess(
            float(rows.max()),
            1.0,
            "a cached row read exactly 1.0, and the bound of normalisation.md §3 is open at both "
            "ends for a table at ordinary magnitudes",
        )
        carried = rows.mean(axis=0)
        np.testing.assert_allclose(
            np.asarray(values, dtype=np.float64),
            self.recomputed(metadata, array, carried),
            rtol=0.0,
            atol=1e-10,
            err_msg="recomputing the pass from the container's parameters with "
            "`rows.mean(axis=0)` as what the trunk consumes does not reproduce the returned "
            "values, so the trunk read a table, a sum, or an unsquashed vector "
            "(architecture.md §2, backends.md §2 item 1)",
        )
        self.assertGreater(
            float(np.abs(table[ids].mean(axis=0) - carried).max()),
            1e-3,
            "the raw mean and the squashed mean agree to within 1e-3, so this case cannot tell "
            "the bounded embedding of normalisation.md §3 from the old `mean(E[ids])`",
        )

    # -- AGT-20.2 ----------------------------------------------------------
    def test_agt20_2_a_table_far_past_the_band_still_feeds_the_trunk_a_value_in_the_unit_interval(self):
        """AGT-20.2 a table doctored to alternating `±1e6` still feeds the trunk a value in `[0, 1]` — every cached row and the carried mean — and returns finite values, in the numpy backend and, from the same bytes, in the torch one, while the raw mean of the same rows over the same ids keeps a magnitude of the doctored order (`normalisation.md` §3, §5, `architecture.md` §2, `backends.md` §2 item 1, D-61, INV-2).

        §3's claim is about **any** parameters: every row lies in `(0, 1)` and so does any mean
        of rows, whatever the parameters do. So the case builds a table the training could never
        produce — alternating `+M`/`−M` along the block, and its mirror image at the negative
        sign — and reads the cache as AGT-20.1 does. The discriminating half is the **raw**
        mean: at every coordinate it keeps a magnitude above 1, of the doctored order, so a pass
        reading `mean(E[ids])` would have handed the trunk a vector far outside the band (§5).
        The torch arm loads the same rewritten bytes with `metadata['backend']` set to `torch`
        and is held to the same bound — one arithmetic order expressed twice
        (`backends.md` §2).
        """
        package = self.agents()
        numpy_backend = self.backend_module("numpy")
        torch_backend = self.backend_module("torch")
        learner = self.token_learner("numpy")
        self.assertIs(
            learner.backend,
            numpy_backend,
            "a numpy learner's `.backend` is agents.numpy_backend, the module that performs its "
            "arithmetic (backends.md §1-§2, surface.md §4)",
        )
        source = self.saved(learner, "agt20-2-source.pt")
        observation = decisions(1)[0]["tokens"]
        raw_means = {}
        for label, sign in (("plus", 1.0), ("minus", -1.0)):
            with self.subTest(variant=label):
                numpy_path, table = self.doctored(source, "agt20-2-%s-numpy.pt" % label, sign)
                restored = package.load(None, numpy_path)
                values, cache = numpy_backend.forward(
                    restored.state, restored.layout, observation, need_cache=True
                )
                self.assert_unit_band("%s's numpy arm" % label, cache["input"][0])
                self.assertTrue(
                    np.isfinite(np.asarray(values, dtype=np.float64)).all(),
                    "the pass over a %s-doctored table returned a non-finite value, and a "
                    "bounded input block keeps the trunk inside float64 at this magnitude "
                    "(backends.md §4): %r" % (label, values),
                )
                raw_means[label] = table[np.asarray(cache["input"][1])].mean(axis=0)
                self.assertGreater(
                    float(np.abs(raw_means[label]).min()),
                    1.0,
                    "the raw mean of the doctored rows over the observation's ids stays inside "
                    "±1 at a coordinate, so this case cannot discriminate the squash from the old "
                    "arithmetic, which would have consumed %r, far outside the band "
                    "(normalisation.md §3, §5)" % (raw_means[label],),
                )
                torch_path, _same = self.doctored(
                    source, "agt20-2-%s-torch.pt" % label, sign, backend="torch"
                )
                torch_learner = package.load(None, torch_path)
                self.assertIs(
                    torch_learner.backend,
                    torch_backend,
                    "the container records `torch` and `load` rebuilt the learner in that "
                    "backend, which is how one parameter set reaches the second arm "
                    "(checkpoint.md §1-§3)",
                )
                torch_values, torch_cache = torch_backend.forward(
                    torch_learner.state, torch_learner.layout, observation, need_cache=True
                )
                self.assert_unit_band(
                    "%s's torch arm" % label, torch_cache["input"][0].detach().numpy()
                )
                self.assertTrue(
                    np.isfinite(torch_values.detach().numpy()).all(),
                    "the torch pass over a %s-doctored table returned a non-finite value "
                    "(backends.md §4): %r" % (label, torch_values),
                )
        np.testing.assert_allclose(
            raw_means["minus"],
            -raw_means["plus"],
            rtol=0.0,
            atol=1e-9,
            err_msg="the two variants are one table's mirror image and the raw mean did not "
            "mirror with it, so the doctoring did not run through the ids this case forwarded",
        )

    # -- AGT-20.3 ----------------------------------------------------------
    def test_agt20_3_the_backward_pass_carries_the_squash_s_derivative(self):
        """AGT-20.3 the table block of `P1 − P0` after one terminal transition is `(rate·td)·Σ_ids (upstream/len(ids))·(1 − (2·row − 1)²)/2` read off the cache's own rows and ids, the block moved, and the same expression **without** that factor differs from the observed delta by more than `1e-6` (`normalisation.md` §3, `backends.md` §2 item 5, `rule.md` §2-§3, `architecture.md` §2).

        §3 rejects a clamp on the table precisely because it zeroes a gradient exactly where the
        reward scale has driven it, which makes the derivative part of the bound: the
        semi-gradient is `θ ← θ + α·td·∂q[a]/∂θ`, and `∂(mean of squashed rows)/∂θ_id` is `1/n`
        times the squash's `(1 − tanh²θ)/2` (`rule.md` §3). The case builds a `token-embedding`
        learner — the plain chain, no residual delta and no mask — saves it as `P0`, forwards
        one real token observation with a cache, and drives **one terminal** transition, so the
        target is the reward alone and `td = reward − values[action]` (`rule.md` §2). It then
        walks the same cache in the backend's own descending order and holds the block to
        `(rate·td)` times that gather. The block must move, so a zeroed derivative is red; the
        derivative-free gather must differ, so a dropped factor is red rather than a rounding
        difference.
        """
        package = self.agents()
        numpy_backend = self.backend_module("numpy")
        learner = self.token_learner("numpy")
        row = decisions(1)[0]
        observation, mask = row["tokens"], tuple(row["mask"])
        metadata, parameters = self.document(self.saved(learner, "agt20-3-before.pt"))
        shape = tuple(
            plain_int(size, "params.tensors['input.weights'].shape")
            for size in self.tensor_record(metadata, "input.weights")["shape"]
        )
        self.assertFalse(
            bool(learner.layout.residual),
            "this case's chain is the plain one: `token-embedding` reads neither a residual "
            "connection nor a mask, so the backward pass has no delta to add and no slot to "
            "filter (architecture.md §2-§3)",
        )
        values, cache = numpy_backend.forward(
            learner.state, learner.layout, observation, need_cache=True
        )
        held = self.snapshot(cache)
        action = int(mask[0])
        self.assertIn(
            action,
            mask,
            "the transition's action must be one of the decision's legal indices, or `learn` "
            "refuses the record before any arithmetic (rule.md §2, surface.md §7)",
        )
        td = float(PROBE_REWARD) - float(np.asarray(values, dtype=np.float64)[action])
        statistics = package.learn(
            learner,
            [
                transition(
                    observation,
                    action=action,
                    reward=PROBE_REWARD,
                    terminal=True,
                    legal=mask,
                    next_legal=mask,
                )
            ],
        )
        self.assertEqual(
            finite_float(float(statistics["td_error"]), "learn()['td_error']"),
            td,
            "a terminal transition's target is its reward alone (rule.md §2), so the figure "
            "`learn` reports is `reward − q[action]`, the residual this case's expected step is "
            "scaled by: %r against %r" % (statistics["td_error"], td),
        )
        after = self.document(self.saved(learner, "agt20-3-after.pt"))[1]
        rate = finite_float(
            float(hyper()["learning_rate"]), "learners()['hyper']['learning_rate']"
        )
        record = self.tensor_record(metadata, "input.weights")
        offset = plain_int(record["offset"], "params.tensors['input.weights'].offset")
        count = plain_int(record["count"], "params.tensors['input.weights'].count")
        observed = np.array(after[offset : offset + count] - parameters[offset : offset + count])
        self.assertGreater(
            float(np.abs(observed).max()),
            0.0,
            "the table block of `P1 − P0` did not move, and a step of rule.md §3 was taken with a "
            "terminal residual of %r: a step that changes no table slot is a gradient whose "
            "input-block derivative was zeroed, the failure normalisation.md §3 rejects a clamp "
            "for" % (td,),
        )
        scaled = (rate * td) * self.table_gradient(held, action, shape).reshape(-1)
        scale = float(np.abs(scaled).max())
        self.assertGreater(
            scale,
            0.0,
            "the expected table gradient is identically zero, so this case asserts nothing about "
            "the squash's derivative (rule.md §3, backends.md §2 item 5)",
        )
        difference = float(np.abs(observed - scaled).max())
        floor = float(np.finfo(np.float64).eps) * float(
            np.abs(parameters[offset : offset + count]).max()
        )
        self.assertLessEqual(
            difference,
            1e-12 * scale + floor,
            "the table block's delta is not (rate·td) times the gather "
            "`Σ_ids (upstream/len(ids))·(1 − (2·row − 1)²)/2` read off the cache's own rows: "
            "max |Δ − expected| = %r against a block scale of %r, so the backward pass dropped "
            "the squash's derivative or differentiated another function (backends.md §2 item 5). "
            "The second tolerance term is float64 addition's own rounding floor, %r"
            % (difference, scale, floor),
        )
        derivative_free = (rate * td) * self.table_gradient(
            held, action, shape, with_slope=False
        ).reshape(-1)
        self.assertGreater(
            float(np.abs(observed - derivative_free).max()),
            1e-6,
            "the observed delta matches the derivative-free expression as closely as the "
            "squash-carrying one, so this case cannot tell a backward pass that carried "
            "`(1 − (2·row − 1)²)/2` from one that dropped it — and squashing rather than clipping "
            "is precisely what keeps the table learning (normalisation.md §3)",
        )

    # -- AGT-20.4 ----------------------------------------------------------
    def test_agt20_4_the_two_backends_agree_on_the_same_table_and_the_same_observation(self):
        """AGT-20.4 the numpy and the torch backend, from one spec at one seed, width and depth, answer the same rows, the same carried mean and the same values on one real token observation — within `1e-12`, `1e-12` and `1e-10`, both inside `[0, 1]` — and still agree on the rows and the carried value after both are handed the same doctored `±1e6` table (`backends.md` §1-§3, `architecture.md` §2, §4, `normalisation.md` §3).

        §2 makes the two backends "the same expressions in the same sequence", and §3's parity
        obligation lands on decisions because two libraries are not guaranteed to round
        identically. This case is the tighter statement the design's words allow: both arms start
        from **bit-identical** parameters (§4's one initialisation, copied and never redrawn) and
        take **one forward pass**, so there is no chain of steps to drift and no tie-break to
        hide a difference — which is why the assertion here is on the values and not on a
        decision, the looser claim FAM-13 makes because it must (`backends.md` §3).
        """
        numpy_backend = self.backend_module("numpy")
        torch_backend = self.backend_module("torch")
        numpy_learner = self.token_learner("numpy")
        torch_learner = self.token_learner("torch")
        observation = decisions(1)[0]["tokens"]
        numpy_values, numpy_cache = numpy_backend.forward(
            numpy_learner.state, numpy_learner.layout, observation, need_cache=True
        )
        torch_values, torch_cache = torch_backend.forward(
            torch_learner.state, torch_learner.layout, observation, need_cache=True
        )
        numpy_rows = numpy_cache["input"][0]
        torch_rows = torch_cache["input"][0].detach().numpy()
        np.testing.assert_array_equal(
            np.asarray(numpy_cache["input"][1]),
            np.asarray(torch_cache["input"][1].detach().numpy()),
            err_msg="the two backends gathered their rows at different ids for one observation, "
            "so they read two different observations (backends.md §2 item 1)",
        )
        numpy_carried = self.assert_unit_band("the numpy arm", numpy_rows)
        torch_carried = self.assert_unit_band("the torch arm", torch_rows)
        np.testing.assert_allclose(
            numpy_rows,
            torch_rows,
            rtol=0.0,
            atol=1e-12,
            err_msg="the two backends' squashed rows differ by more than 1e-12 from "
            "bit-identical parameters and one forward pass: `(1 + tanh θ)/2` is one expression "
            "and both libraries evaluate it on the same values (backends.md §2, §4)",
        )
        np.testing.assert_allclose(
            numpy_carried,
            torch_carried,
            rtol=0.0,
            atol=1e-12,
            err_msg="the value the two trunks consumed differs by more than 1e-12, so the "
            "mean-pool over positions is not the same expression in both backends "
            "(backends.md §2 item 1)",
        )
        np.testing.assert_allclose(
            np.asarray(numpy_values, dtype=np.float64),
            torch_values.detach().numpy(),
            rtol=0.0,
            atol=1e-10,
            err_msg="the two backends' `A` values differ by more than 1e-10 on one observation "
            "from one parameter set: this is not a decision and claims no tie-break, it is the "
            "one pass the design calls one arithmetic order expressed twice (backends.md §2-§3)",
        )
        source = self.saved(numpy_learner, "agt20-4-source.pt")
        for label, sign in (("plus", 1.0), ("minus", -1.0)):
            with self.subTest(variant=label):
                numpy_path, table = self.doctored(source, "agt20-4-%s-numpy.pt" % label, sign)
                torch_path, _same = self.doctored(
                    source, "agt20-4-%s-torch.pt" % label, sign, backend="torch"
                )
                doctored_numpy = self.agents().load(None, numpy_path)
                doctored_torch = self.agents().load(None, torch_path)
                _values, doctored_numpy_cache = numpy_backend.forward(
                    doctored_numpy.state, doctored_numpy.layout, observation, need_cache=True
                )
                _other, doctored_torch_cache = torch_backend.forward(
                    doctored_torch.state, doctored_torch.layout, observation, need_cache=True
                )
                doctored_rows = doctored_numpy_cache["input"][0]
                doctored_other = doctored_torch_cache["input"][0].detach().numpy()
                self.assertEqual(
                    tuple(np.asarray(doctored_rows).shape),
                    (len(observation), table.shape[1]),
                    "the doctored pass read rows of another shape than the container's own "
                    "(V, W) table gives, so the parity below is between two tables "
                    "(checkpoint.md §2.1)",
                )
                doctored_carried = self.assert_unit_band(
                    "%s's doctored numpy arm" % label, doctored_rows
                )
                other_carried = self.assert_unit_band(
                    "%s's doctored torch arm" % label, doctored_other
                )
                np.testing.assert_allclose(
                    doctored_rows,
                    doctored_other,
                    rtol=0.0,
                    atol=1e-12,
                    err_msg="on a %s-doctored table the two backends' rows differ by more than "
                    "1e-12, so the squash is not one expression in both libraries at the "
                    "magnitudes normalisation.md §3 says it must bound" % (label,),
                )
                np.testing.assert_allclose(
                    doctored_carried,
                    other_carried,
                    rtol=0.0,
                    atol=1e-12,
                    err_msg="on a %s-doctored table the value the two trunks consumed differs by "
                    "more than 1e-12 (backends.md §2 item 1, normalisation.md §3)" % (label,),
                )

    # -- AGT-20.5 ----------------------------------------------------------
    def test_agt20_5_the_squash_moves_no_count_no_round_trip_and_no_dense_forward(self):
        """AGT-20.5 (a) a token learner's `param_count` is `model._param_count_for(kind, width, depth)` and its container's `params.count`, with the input block at `(V, W)` and no input bias; (b) a `save`→`load` round trip reports the same count, decides as its source over six real decisions and reports the same next `td_error` to the last digit; (c) the dense family's forward carries no squash anywhere — recomputed by hand from the container — and its cache `input` is `(observation, pre-activation)` (`input-read.md` §4, `architecture.md` §2, §5, `checkpoint.md` §1-§4, `normalisation.md` §3-§5, `rule.md` §3, D-61, ASM-10).

        §3 says the squash keeps the table's width and therefore `param_count`,
        `observation_size` and the matched-budget comparison, and §5 says the change is **added**.
        (a) is the formula, read through the internal `rule.md` §8 declares for this battery and
        through the container's tensor table — the token block is a table and no bias
        (`architecture.md` §2, §5). (b) is the restore: loss-free means the restored learner
        decides as its source and takes the same next step to the digit (`checkpoint.md` §1, §4,
        ASM-5). (c) is the other family: `naive-stack`'s block is `relu(x @ W_in + b_in)` with no
        squash, so a pass that squashed it too is red (`normalisation.md` §3-§5).
        """
        package = self.agents()
        numpy_backend = self.backend_module("numpy")
        count_for = declared_internal("model", "_param_count_for")
        learner = self.token_learner("numpy")
        reported = plain_int(package.param_count(learner), "param_count(token learner)")
        self.assertEqual(
            reported,
            plain_int(
                count_for("token-embedding", TOKEN_WIDTH, TOKEN_DEPTH),
                "_param_count_for(kind, width, depth)",
            ),
            "(a) a token learner's count is not architecture.md §5's sum at its own settings: the "
            "squash changes no width and adds no parameter, so the table's term is still `V·W` "
            "(ASM-10, D-7): %r" % (reported,),
        )
        metadata, array = self.document(self.saved(learner, "agt20-5-token.pt"))
        self.assertEqual(
            plain_int(metadata["params"]["count"], "params.count"),
            reported,
            "(a) the container records another count than `param_count` reports, so the squash "
            "added or removed a slot the container had to carry (checkpoint.md §2.1, §4)",
        )
        _table, shape = self.table(array, metadata)
        self.assertEqual(
            shape[0] * shape[1],
            plain_int(
                self.tensor_record(metadata, "input.weights")["count"],
                "params.tensors['input.weights'].count",
            ),
            "(a) the block's recorded shape and its recorded count disagree, so its term of "
            "architecture.md §5 is not `V·W` in this container",
        )
        self.assertFalse(
            self.has_tensor(metadata, "input.bias"),
            "(a) the token container names an `input.bias`, and architecture.md §2 gives the "
            "embedding block a table and no bias — a squash needs none, so such a slot would be a "
            "parameter the formula does not count",
        )
        rows = decisions(DECIDED)
        restored = package.load(None, self.saved(learner, "agt20-5-token-trip.pt"))
        self.assertEqual(
            plain_int(package.param_count(restored), "param_count(restored)"),
            reported,
            "(b) the restored learner reports another capacity than its source, so the container "
            "did not carry the model the squash left unchanged (checkpoint.md §1, §4)",
        )
        for row in rows:
            with self.subTest(hand=row["readout"]["hole"]):
                decision = package.act(restored, row["tokens"], row["mask"])["action"]
                self.assertEqual(
                    decision,
                    package.act(learner, row["tokens"], row["mask"])["action"],
                    "(b) the restored token learner did not decide as its source on a real "
                    "readout, so the restore is lossy at the decision boundary for a token kind "
                    "(checkpoint.md §4, ASM-5, rule.md §4-§5)",
                )
                self.assertIn(
                    decision,
                    row["mask"],
                    "(b) the decision is an index of the decision's own legal mask "
                    "(rule.md §4-§5, surface.md §6)",
                )
        batch = self.invented_batch(rows)
        source_result = package.learn(learner, [dict(record) for record in batch])
        restored_result = package.learn(restored, [dict(record) for record in batch])
        self.assertEqual(
            finite_float(float(restored_result["td_error"]), "the restored td_error"),
            finite_float(float(source_result["td_error"]), "the saved td_error"),
            "(b) the restored learner's first update did not report the saved learner's own "
            "td_error to the last digit, after %r transitions each, so a parameter, the target "
            "copy, the position or a mask did not travel through the container "
            "(checkpoint.md §1, §4, rule.md §3, ASM-5)"
            % (plain_int(restored_result["transitions"], "transitions"),),
        )
        dense = self.build(kind="naive-stack", width=DENSE_WIDTH, depth=DENSE_DEPTH)
        dense_metadata, dense_array = self.document(self.saved(dense, "agt20-5-dense.pt"))
        dense_observation = decisions(1)[0]["dense"]
        dense_values, dense_cache = numpy_backend.forward(
            dense.state, dense.layout, dense_observation, need_cache=True
        )
        input_dim = plain_int(
            self.tensor_record(dense_metadata, "input.weights")["shape"][0],
            "params.tensors['input.weights'].shape",
        )
        weights = self.tensor(dense_array, dense_metadata, "input.weights").reshape(
            input_dim,
            plain_int(dense_metadata["settings"]["width"], "settings.width"),
        )
        observation = np.asarray(dense_observation, dtype=np.float64)
        pre_activation = observation @ weights + self.tensor(
            dense_array, dense_metadata, "input.bias"
        )
        self.assertEqual(
            len(dense_cache["input"]),
            2,
            "(c) the dense cache's input is the 2-sequence `(observation, pre-activation)` and "
            "this block is not one (backends.md §2 item 1)",
        )
        cached_observation, cached_pre = dense_cache["input"]
        np.testing.assert_allclose(
            np.asarray(cached_observation, dtype=np.float64),
            observation,
            rtol=0.0,
            atol=0.0,
            err_msg="(c) the dense block's cache does not carry the observation itself, so a case "
            "could not tell its arithmetic from the token family's (architecture.md §2)",
        )
        np.testing.assert_allclose(
            np.asarray(cached_pre, dtype=np.float64),
            pre_activation,
            rtol=0.0,
            atol=1e-12,
            err_msg="(c) the cached pre-activation is not `x @ W_in + b_in` from the container's "
            "own parameters, so the dense input block is not the expression architecture.md §2 "
            "gives it",
        )
        np.testing.assert_allclose(
            np.asarray(dense_values, dtype=np.float64),
            self.recomputed(dense_metadata, dense_array, np.maximum(pre_activation, 0.0)),
            rtol=0.0,
            atol=1e-10,
            err_msg="(c) recomputing the dense pass by hand — `relu(x @ W_in + b_in)`, the trunk "
            "layers, `h @ W_out + b_out`, with no squash anywhere — does not reproduce the "
            "returned values, so the dense family is not untouched by the token family's change "
            "(normalisation.md §3-§5, architecture.md §2)",
        )
        self.assertGreater(
            float(np.abs(pre_activation - squashed(pre_activation)).max()),
            1e-6,
            "(c) the dense block's pre-activation is the same value squashed and unsquashed, so "
            "this case could not tell a pass that squashed the dense family too from the one "
            "architecture.md §2 declares — the bound of normalisation.md §3 is the token "
            "family's, and the dense map is §2's",
        )


if __name__ == "__main__":
    unittest.main()
