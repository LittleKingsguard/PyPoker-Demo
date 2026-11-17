"""AGT-21 — the pad is not a token: the pool is over the real rows, and so is its gradient.

`docs/L3/agents/architecture.md` §2 gives the token family an embedding `V → W`, squashed and
mean-pooled (`input-read.md` §1), and `docs/L1/normalisation.md` §3 puts INV-2's bound on the
value the trunk consumes — but neither of those says over **which** positions the mean runs.
The fixed width makes that the decisive question: a six-seat observation is 122 ids wide and a
preflop decision fills 14 of them, the rest carrying the pad id 0 (`strata/decisions.md` D-79).
An unmasked mean therefore makes one constant vector 89 % of what the trunk reads **and** gives
the pad's row the same share of every gradient, which is the dilution D-75 measured at 0.3 % and
the per-row asymmetry D-78 measured at 8.4×. D-79 states the repair — "keep 122 tokens, exclude
pads from pool and scatter" — and D-80 measures it: with the mask the pad row moves **exactly**
zero. These five cases hold both halves of that repair at this module's own boundary, where the
cached `(rows, ids)` block and the parameters after one step are both readable (`input-read.md`
§3, `backends.md` §2 item 1):

* **AGT-21.1** the pool of `[card, 0, 0, 0]` is the card's **own** squashed row, bit for bit,
  and never the quarter of it the unmasked mean would produce; a mixed sequence pools to the
  mean of its real rows and of no other position;
* **AGT-21.2** the pool and the `A` values are **invariant** to how many trailing pads the
  sequence carries — up to and including the default shape's declared width — bit for bit;
* **AGT-21.3** one `rule.md` §3 step at `α·td = 1` leaves the pad's table row **exactly** where
  it was and moves each addressed card row, while no unaddressed row moves at all;
* **AGT-21.4** a sequence that is padding throughout pools to the **zero vector** and leaves the
  whole embedding block where it was, without raising — the empty mean's division is not taken;
* **AGT-21.5** the two backends pool one mixed padded sequence **identically** and take the same
  step on its table block, inside the case's stated tolerance of `rtol 0.0, atol 1e-12`.

Nothing here imports `torch`: the package's lazy import is the code under test (`backends.md`
§4), the learners are small (width 8, depth 2) and CPU-only, and no case reads a private
spelling beyond the two backends' own `forward`/`apply` and a learner's `.state`, `.layout` and
`.backend` — the same readers `test_normalisation.py` (AGT-20) uses for the same block.

`input-read.md` §1-§2 still writes the pool as a mean over the observation's **every** id and the
gather as `(upstream / len(ids))`, and `backends.md` §2 item 1 still says "divided by the position
count"; D-79/D-80 are the decisions this change implements, and those sentences are the
statements it makes false. They are reported, not edited here.
"""

import unittest

import numpy

from _agents_support import (
    AgentsCase,
    declared_module,
    features,
    plain_int,
    token_encoder,
)

#: Invented instances: no number below appears in a design document. The two card ids are
#: invented and both inside every declared token vocabulary; the width and depth are this
#: battery's own, and depth 2 is what makes the pool readable at the first trunk layer while
#: leaving a trunk behind it (`architecture.md` §2).
TOKEN_WIDTH, TOKEN_DEPTH = 8, 2
CARD, OTHER = 7, 23

#: The one pad of the token encoding: the id a fixed-width sequence leaves where a decision
#: carries no token (`card-tokens.md` §3, D-79). It is a slot's filler and not a token.
PAD = 0

#: The trailing pads AGT-21.2 varies the sequence by; the last is appended per run so the
#: longest sequence is the default shape's own declared width, read from the encoder.
TAILS = (0, 1, 2, 6)


def squashed(table):
    """`row = (1 + tanh θ)/2`, the one squash of the token family's input read (§3, §2)."""
    return (1.0 + numpy.tanh(numpy.asarray(table, dtype=numpy.float64))) / 2.0


def expected_pool(table, ids):
    """The pool the case expects: the mean over the rows whose id is not `PAD`.

    A sequence that is padding throughout addressed no row and has no mean, so its pool is the
    zero vector and no division is taken (D-79).
    """
    table = numpy.asarray(table, dtype=numpy.float64)
    ids = numpy.asarray(ids)
    real = squashed(table[ids])[ids != PAD]
    if real.shape[0] == 0:
        return numpy.zeros(table.shape[1], dtype=numpy.float64)
    return real.sum(axis=0) / float(real.shape[0])


class PoolingTest(AgentsCase):
    """The mask on the token pool and on the gradient that reaches the table."""

    # -- the readers a case needs, all off declared spellings ------------------
    def backend_module(self, name):
        """`agents.<name>_backend`, the one module that performs that backend's arithmetic."""
        return declared_module("%s_backend" % (name,))

    def token_learner(self, backend="numpy"):
        """One `token-embedding` learner at this battery's invented width and depth.

        A `card-tokens` encoder is handed to the build, so the learner's sizing record is the
        encoding's — an id sequence inside a declared vocabulary (`architecture.md` §1, §6,
        `features/surface.md` §5).
        """
        return self.build(
            backend=backend,
            kind="token-embedding",
            width=TOKEN_WIDTH,
            depth=TOKEN_DEPTH,
            encoder=token_encoder(),
        )

    def declared_width(self):
        """The token sequence's declared width, read off the encoder and never written down."""
        spec = features().observation_spec(token_encoder())
        return plain_int(spec["shape"][0], "observation_spec['shape'][0]")

    def sequence(self, ids, tail=0):
        """One token observation of these ids with `tail` pads behind them.

        The dtype is the declaration's: `token_observation` reads the `(40,) int32` family
        (`features/surface.md` §5), and the ids below are invented members of its vocabulary.
        """
        from _agents_support import token_observation

        return token_observation(list(ids) + [PAD] * tail)

    def parameters(self, learner):
        """A copy of the online `P` parameters the learner's own backend holds."""
        count = plain_int(learner.layout.count, "layout.count")
        values = numpy.asarray(learner.backend.parameters(learner.state), dtype=numpy.float64)
        return numpy.array(values[:count], copy=True)

    def table(self, learner):
        """The embedding table `E` as `(V, W)` float64, read off the learner's own state.

        `architecture.md` §2 gives the token input block that shape and no bias, and the block
        lives at `layout.w_in` of the online parameter array (`backends.md` §2).
        """
        layout = learner.layout
        offset, length = layout.w_in
        return self.parameters(learner)[offset : offset + length].reshape(
            plain_int(layout.input_dim, "layout.input_dim"),
            plain_int(layout.width, "layout.width"),
        )

    def pool(self, cache, backend="numpy"):
        """The vector the trunk consumed: the carried value entering its **first** layer.

        `cache['carried']` is the last trunk layer's output and not the pool, so the pool is
        read at `cache['layers'][0][0]`, which every trunk stores as the value it read — the
        reader `test_normalisation.py` uses for the same block (`backends.md` §2 item 2).
        """
        self.assertGreaterEqual(
            len(cache["layers"]),
            1,
            "this learner has no trunk layer, so no case here could read the value the pool "
            "handed it (architecture.md §2)",
        )
        layer = cache["layers"][0][0]
        if backend == "torch":
            layer = layer.detach().numpy()
        return numpy.array(layer, dtype=numpy.float64, copy=True)

    def read_ids(self, cache, backend="numpy"):
        """The ids the forward pass gathered at, as a numpy array."""
        ids = cache["input"][1]
        if backend == "torch":
            ids = ids.detach().numpy()
        return numpy.asarray(ids)

    def read_rows(self, cache, backend="numpy"):
        """The squashed rows the forward pass gathered, as a numpy array."""
        rows = cache["input"][0]
        if backend == "torch":
            rows = rows.detach().numpy()
        return numpy.asarray(rows, dtype=numpy.float64)

    def step(self, module, learner, observation, action=0):
        """The embedding block of one `rule.md` §3 step at `α·td = 1`, as `(V, W)`.

        `apply` takes `θ ← θ + rate·delta·∂q[a]/∂θ`, so at `delta = rate = 1` the block of
        `P1 − P0` **is** the gradient the backward pass produced for the table, which is the
        quantity D-79 and D-80 measure. The step is taken on the learner's own state from a
        cache built just before it, and the block is a difference of two copies, so the views
        the cache holds into the live parameter array cannot smear one step into the next
        (`backends.md` §2, `rule.md` §3).
        """
        layout = learner.layout
        before = self.parameters(learner)
        _values, cache = module.forward(
            learner.state, layout, observation, need_cache=True
        )
        module.apply(learner.state, layout, cache, int(action), 1.0, 1.0)
        after = self.parameters(learner)
        offset, length = layout.w_in
        return (after[offset : offset + length] - before[offset : offset + length]).reshape(
            plain_int(layout.input_dim, "layout.input_dim"),
            plain_int(layout.width, "layout.width"),
        )

    # -- AGT-21.1 ----------------------------------------------------------
    def test_agt21_1_the_pool_is_the_card_s_own_row_and_never_a_quarter_of_it(self):
        """AGT-21.1 for one `[card, 0, 0, 0]` observation the vector the trunk consumed is the card's own squashed row **bit for bit** — and not the quarter of it the unmasked mean divides by four — while a sequence of `[card, 0, other, 0, 0]` pools to the mean of exactly those two rows, in the numpy backend and in the torch one (D-79, D-80, `architecture.md` §2, `backends.md` §2 item 1, `normalisation.md` §3).

        The pad is the width's filler and not a token, so it is neither pooled nor given a
        share: the pool's denominator is the real count. The discriminating half is the
        **quarter**: with one real id in a sequence of four, the unmasked mean is
        `row/4` exactly, so a pass that only renamed the cache block reads that quarter and
        is red here.
        """
        for backend_name in ("numpy", "torch"):
            module = self.backend_module(backend_name)
            with self.subTest(backend=backend_name):
                learner = self.token_learner(backend_name)
                table = self.table(learner)
                rows = squashed(table)
                observation = self.sequence([CARD])
                _values, cache = module.forward(
                    learner.state, learner.layout, observation, need_cache=True
                )
                self.assertEqual(
                    self.read_ids(cache, backend_name).tolist(),
                    observation.tolist(),
                    "the pass did not gather at the observation's own ids, in its own position "
                    "order, so this case would assert the pool of another sequence "
                    "(backends.md §2 item 1)",
                )
                pool = self.pool(cache, backend_name)
                numpy.testing.assert_array_equal(
                    pool,
                    rows[CARD],
                    err_msg="the value the trunk consumed for [%d, 0, 0, 0] on the %s backend is "
                    "not the card's own squashed row bit for bit: the pool is a mean over the "
                    "real rows and the three pads are not rows (D-79, D-80)"
                    % (CARD, backend_name),
                )
                self.assertGreater(
                    float(numpy.abs(pool - rows[CARD] / 4.0).max()),
                    1e-3,
                    "the pool and the card's row divided by four agree to within 1e-3 on the %s "
                    "backend, so this case cannot tell the masked pool from the unmasked mean "
                    "a sequence of four positions would take: %r against %r"
                    % (backend_name, pool[:3].tolist(), (rows[CARD] / 4.0)[:3].tolist()),
                )
                mixed = self.sequence([CARD, OTHER], tail=3)
                _mixed_values, mixed_cache = module.forward(
                    learner.state, learner.layout, mixed, need_cache=True
                )
                read_rows = self.read_rows(mixed_cache, backend_name)
                mixed_pool = self.pool(mixed_cache, backend_name)
                numpy.testing.assert_array_equal(
                    mixed_pool,
                    expected_pool(table, mixed),
                    err_msg="a sequence carrying two real ids and three pads does not pool to "
                    "the mean of its two real rows on the %s backend: the pad positions were "
                    "averaged in (D-79, D-80)" % (backend_name,),
                )
                self.assertGreater(
                    float(numpy.abs(read_rows.sum(axis=0) / 5.0 - mixed_pool).max()),
                    1e-3,
                    "the pooled value equals the unmasked mean over all five positions on the "
                    "%s backend, so the two ids and the three pads were averaged together "
                    "(D-79)" % (backend_name,),
                )

    # -- AGT-21.2 ----------------------------------------------------------
    def test_agt21_2_the_pool_is_invariant_to_the_trailing_pads_the_width_reserves(self):
        """AGT-21.2 one sequence of two real ids pools to the same vector and returns the same `A` values however many pads follow them — 0, 1, 2, 6 and enough to reach the default shape's own declared width — bit for bit in the numpy backend and in the torch one (D-79, D-80, `architecture.md` §2, `backends.md` §2 item 1).

        The width fits the worst case, so the same decision on the same street is a different
        observation when its tail is padded to another length: the quantity the trunk must read
        is the decision's tokens, and the pad count is the allocator's business. The case reads
        the declared width off the encoder rather than writing it down, and the values are held
        to exact equality because one pool and one parameter set leave nothing to round
        (`backends.md` §3).
        """
        tails = TAILS + (self.declared_width() - 2,)
        for backend_name in ("numpy", "torch"):
            module = self.backend_module(backend_name)
            with self.subTest(backend=backend_name):
                learner = self.token_learner(backend_name)
                table = self.table(learner)
                reference = None
                for tail in tails:
                    with self.subTest(backend=backend_name, tail=tail):
                        observation = self.sequence([CARD, OTHER], tail=tail)
                        self.assertEqual(
                            len(observation),
                            tail + 2,
                            "the sequence this case forwarded is not the length it varies by, so "
                            "the invariance below would be between other sequences: %r"
                            % (len(observation),),
                        )
                        values, cache = module.forward(
                            learner.state, learner.layout, observation, need_cache=True
                        )
                        pool = self.pool(cache, backend_name)
                        if backend_name == "numpy":
                            values = numpy.asarray(values, dtype=numpy.float64)
                        else:
                            values = values.detach().numpy()
                        numpy.testing.assert_array_equal(
                            pool,
                            expected_pool(table, observation),
                            err_msg="the pool with %d trailing pads is not the mean of the two "
                            "real rows on the %s backend" % (tail, backend_name),
                        )
                        if reference is None:
                            reference = (pool, values)
                            continue
                        numpy.testing.assert_array_equal(
                            pool,
                            reference[0],
                            err_msg="the pool moved when the sequence's trailing pads were "
                            "resized to %d on the %s backend: the pad count is the allocator's "
                            "and not the decision's (D-79, D-80)"
                            % (tail, backend_name),
                        )
                        numpy.testing.assert_array_equal(
                            values,
                            reference[1],
                            err_msg="the `A` values moved when %d trailing pads were appended on "
                            "the %s backend, so a pad position still reaches the trunk "
                            "(D-79, backends.md §2 item 1)" % (tail, backend_name),
                        )

    # -- AGT-21.3 ----------------------------------------------------------
    def test_agt21_3_the_pad_row_receives_no_gradient_after_one_step(self):
        """AGT-21.3 after one `rule.md` §3 step at `α·td = 1` the embedding table's row 0 — the pad's — is **exactly** where it was, each addressed card row moved, and no other row moved at all, in both backends (D-79, D-80, `backends.md` §2 item 5, `rule.md` §3).

        D-80's first measured fact is that with the mask "the padding row moves exactly zero in
        both surviving arms", and that is a property of the scatter rather than of the reward:
        the pad is scattered into by nothing, so its row's gradient is the zero vector and the
        step cannot move it even in the last bit. The addressed rows must move, or the mask
        would have removed the learning signal with the dilution; the unaddressed non-pad rows
        must not, or the gather would be a dense write.
        """
        observation_ids = [CARD, PAD, OTHER, PAD, PAD]
        observation = self.sequence(observation_ids)
        for backend_name in ("numpy", "torch"):
            module = self.backend_module(backend_name)
            with self.subTest(backend=backend_name):
                learner = self.token_learner(backend_name)
                block = self.step(module, learner, observation)
                pad_row = numpy.asarray(block[PAD], dtype=numpy.float64)
                numpy.testing.assert_array_equal(
                    pad_row,
                    numpy.zeros(pad_row.shape, dtype=numpy.float64),
                    err_msg="the pad's table row moved by %r on the %s backend after one step: "
                    "id 0 is the fixed width's filler and not a token, so it is scattered into "
                    "by nothing and its gradient is identically zero (D-79, D-80)"
                    % (float(numpy.abs(pad_row).max()), backend_name),
                )
                for addressed in (CARD, OTHER):
                    with self.subTest(backend=backend_name, row=addressed):
                        self.assertGreater(
                            float(numpy.abs(block[addressed]).max()),
                            0.0,
                            "the addressed row %d did not move on the %s backend, so masking the "
                            "pool took the table's learning signal with the dilution: a row the "
                            "observation addresses receives the upstream gradient divided by the "
                            "real count (D-79, D-80, rule.md §3)"
                            % (addressed, backend_name),
                        )
                others = [
                    row
                    for row in range(block.shape[0])
                    if row not in (PAD, CARD, OTHER)
                ]
                stray = float(numpy.abs(numpy.asarray(block[others], dtype=numpy.float64)).max())
                self.assertEqual(
                    stray,
                    0.0,
                    "a row the observation does not address moved by %r on the %s backend: the "
                    "scatter reaches the addressed positions only (D-79, backends.md §2 item 5)"
                    % (stray, backend_name),
                )

    # -- AGT-21.4 ----------------------------------------------------------
    def test_agt21_4_an_all_pad_sequence_pools_to_zeros_and_moves_no_table_row(self):
        """AGT-21.4 a sequence that is padding throughout pools to the **zero vector**, returns finite values without raising, and leaves every row of the embedding table exactly where it was after one step, in both backends (D-79, `backends.md` §2 items 1 and 5, `normalisation.md` §3).

        The width fits the worst case, so an observation of nothing but pads is expressible and
        the pool has no real row to average: the masked mean would divide by zero, so the pool
        **chooses** the zero vector — the one value the squash cannot produce, which is what
        makes "this observation carried no token" a distinct value rather than a silent one. A
        zero pool then hands the trunk a zero vector, and a zero vector's share of the table's
        gradient is zero, so every row of the block stays put. The trunk's own blocks still move
        (`relu(0 @ W + b)` is `relu(b)`), which is why this case asserts the embedding block and
        not the whole parameter step.
        """
        observation = self.sequence([], tail=4)
        for backend_name in ("numpy", "torch"):
            module = self.backend_module(backend_name)
            with self.subTest(backend=backend_name):
                learner = self.token_learner(backend_name)
                values, cache = module.forward(
                    learner.state, learner.layout, observation, need_cache=True
                )
                if backend_name == "numpy":
                    values = numpy.asarray(values, dtype=numpy.float64)
                else:
                    values = values.detach().numpy()
                self.assertTrue(
                    numpy.isfinite(values).all(),
                    "the pass over a sequence of nothing but pads returned a non-finite value "
                    "on the %s backend: %r" % (backend_name, values),
                )
                pool = self.pool(cache, backend_name)
                numpy.testing.assert_array_equal(
                    pool,
                    numpy.zeros(pool.shape, dtype=numpy.float64),
                    err_msg="an all-pad sequence on the %s backend pooled to %r and not to the "
                    "zero vector: its mean has no row to average, so the vector is chosen and "
                    "not computed (D-79)" % (backend_name, pool.tolist()),
                )
                self.assertEqual(
                    self.read_ids(cache, backend_name).tolist(),
                    observation.tolist(),
                    "the all-pad pass did not gather at the observation's own ids, so it is not "
                    "the sequence this case calls all-pad (backends.md §2 item 1)",
                )
                block = self.step(module, learner, observation)
                moved = float(numpy.abs(block).max())
                self.assertEqual(
                    moved,
                    0.0,
                    "an all-pad sequence moved the embedding table by %r on the %s backend: a "
                    "zero pool addresses no row, so the block's gradient is identically zero and "
                    "no division by the real count is taken (D-79, D-80)"
                    % (moved, backend_name),
                )

    # -- AGT-21.5 ----------------------------------------------------------
    def test_agt21_5_the_two_backends_pool_one_mixed_padded_sequence_identically(self):
        """AGT-21.5 the numpy and the torch backend, from one spec at one seed, width and depth — hence bit-identical tables — pool one mixed padded sequence to vectors that agree within `rtol 0.0, atol 1e-12`, return `A` values within `atol 1e-10`, and take the same step on the embedding block within `atol 1e-12` (`backends.md` §1-§3, `architecture.md` §2, §4, D-79).

        `backends.md` §3 puts the parity obligation on decisions because two libraries need not
        round alike, so the tolerance is written into every message below: `rtol 0.0` and an
        `atol` of `1e-12` for the pool and the step, `1e-10` for the `A` values, the same
        tolerances AGT-20.4 holds the unmasked pass to. Both arms start from one draw (§4's one
        initialisation, copied and never redrawn), and the case first asserts the two tables
        coincide, so the comparison is between two evaluations of one expression and not
        between two models. The sequence carries three pads, and the pooled value is asserted
        away from the unmasked mean, so a pass that pooled every position could not pass here
        by coincidence.
        """
        numpy_backend = self.backend_module("numpy")
        torch_backend = self.backend_module("torch")
        numpy_learner = self.token_learner("numpy")
        torch_learner = self.token_learner("torch")
        observation = self.sequence([CARD, OTHER], tail=3)
        numpy_table = self.table(numpy_learner)
        numpy.testing.assert_array_equal(
            numpy_table,
            self.table(torch_learner),
            err_msg="the two backends' tables differ, so this case would compare two models and "
            "not one expression evaluated twice (backends.md §4, architecture.md §4)",
        )
        numpy_values, numpy_cache = numpy_backend.forward(
            numpy_learner.state, numpy_learner.layout, observation, need_cache=True
        )
        torch_values, torch_cache = torch_backend.forward(
            torch_learner.state, torch_learner.layout, observation, need_cache=True
        )
        numpy.testing.assert_array_equal(
            self.read_ids(numpy_cache),
            self.read_ids(torch_cache, "torch"),
            err_msg="the two backends gathered their rows at different ids for one observation, "
            "so they read two different sequences (backends.md §2 item 1)",
        )
        numpy_pool = self.pool(numpy_cache)
        torch_pool = self.pool(torch_cache, "torch")
        numpy.testing.assert_array_equal(
            numpy_pool,
            expected_pool(numpy_table, observation),
            err_msg="the numpy pool is not the mean over the sequence's non-pad rows (D-79)",
        )
        self.assertGreater(
            float(
                numpy.abs(
                    numpy_pool - self.read_rows(numpy_cache).sum(axis=0) / float(len(observation))
                ).max()
            ),
            1e-3,
            "the pooled value and the unmasked mean over all %d positions agree to within 1e-3, "
            "so this case cannot discriminate the mask and could pass on a pass that pooled "
            "every position" % (len(observation),),
        )
        numpy.testing.assert_allclose(
            numpy_pool,
            torch_pool,
            rtol=0.0,
            atol=1e-12,
            err_msg="the value the two trunks consumed differs by more than the case's tolerance "
            "rtol 0.0, atol 1e-12: the masked pool is not one expression in both backends "
            "(backends.md §2 item 1, D-79)",
        )
        numpy.testing.assert_allclose(
            self.read_rows(numpy_cache),
            self.read_rows(torch_cache, "torch"),
            rtol=0.0,
            atol=1e-12,
            err_msg="the two backends' squashed rows differ by more than the case's tolerance "
            "rtol 0.0, atol 1e-12 from bit-identical parameters and one pass (backends.md §2, §4)",
        )
        numpy.testing.assert_allclose(
            numpy.asarray(numpy_values, dtype=numpy.float64),
            torch_values.detach().numpy(),
            rtol=0.0,
            atol=1e-10,
            err_msg="the two backends' `A` values differ by more than the case's tolerance "
            "rtol 0.0, atol 1e-10 on one observation from one parameter set "
            "(backends.md §2-§3)",
        )
        numpy_block = self.step(numpy_backend, numpy_learner, observation)
        torch_block = self.step(torch_backend, torch_learner, observation)
        for label, block in (("numpy", numpy_block), ("torch", torch_block)):
            with self.subTest(backend=label, row="pad"):
                pad_row = numpy.asarray(block[PAD], dtype=numpy.float64)
                numpy.testing.assert_array_equal(
                    pad_row,
                    numpy.zeros(pad_row.shape, dtype=numpy.float64),
                    err_msg="the pad's row moved in the %s arm, so the gradient is not masked "
                    "there: its share is exactly zero (D-79, D-80)" % (label,),
                )
        numpy.testing.assert_allclose(
            numpy_block,
            torch_block,
            rtol=0.0,
            atol=1e-12,
            err_msg="the embedding block the two backends stepped by differs by more than the "
            "case's tolerance rtol 0.0, atol 1e-12: the masked scatter and the division by the "
            "real count are not one expression in both backends (backends.md §2 item 5, D-79)",
        )


if __name__ == "__main__":  # pragma: no cover - a case file, run by pytest
    unittest.main()
