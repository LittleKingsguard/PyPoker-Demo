"""AGT-12 — the internals `rule.md` §8 declares, driven directly.

Drives the private names the design fixes for this battery and no other: the
exploration rate `rule._epsilon`, the keyed draw `rule._decision_key`, the
tie-break `rule._tie_break`, and the parameter formula and one initialisation
`model._param_count_for` / `model._initial_parameters` (`rule.md` §4-§5, §8,
`architecture.md` §4-§5). None of them is observable through an entry point on
its own — a fresh learner explores at the schedule's `start` (1.0), so no case
that builds one reads a value, and the tie-break has no caller-visible input at
all — which is exactly why §8 declares the spellings and their signatures. Their
bodies stay L4's; what is asserted is the stated arithmetic, the schedule's own
values read back from `learners()`, and the properties §5 and §4 name
(backend-independent, order-independent, stateless and total). G4, G5 and G10 are
the guardrails this case closes (`guardrails.md`).
"""

import itertools
import unittest

import numpy as np

from _agents_support import (
    ALL_MASK,
    LEARNER_SEED,
    NONEMPTY_MASKS,
    OTHER_SEED,
    AgentsCase,
    decision_draw,
    declared_internal,
    dense_observation,
    learner_spec,
    schedule,
    token_observation,
)


class RuleInternalsTest(AgentsCase):
    def test_agt12_1_the_exploration_rate_is_the_schedule(self):
        """AGT-12.1 `_epsilon(0)` is `start`, `_epsilon(samples)` is `end`, linear between and clamped past `samples` (`rule.md` §4, §8, `surface.md` §3)."""
        epsilon = declared_internal("rule", "_epsilon")
        fixed = schedule()
        start = float(fixed["start"])
        end = float(fixed["end"])
        samples = int(fixed["samples"])
        self.assertGreater(samples, 0)
        self.assertGreater(start, end)
        self.assertAlmostEqual(
            float(epsilon(0)),
            start,
            places=12,
            msg="the rate at position 0 is not the schedule's start",
        )
        self.assertAlmostEqual(
            float(epsilon(samples)),
            end,
            places=12,
            msg="the rate at the annealed end is not the schedule's end",
        )
        for position in (samples + 1, samples + 977, samples * 4):
            with self.subTest(position=position):
                self.assertAlmostEqual(
                    float(epsilon(position)),
                    end,
                    places=12,
                    msg="the rate is not clamped to end past samples",
                )
        previous = None
        for step in range(11):
            position = int(round(samples * step / 10.0))
            rate = float(epsilon(position))
            expected = start + (end - start) * min(position, samples) / samples
            with self.subTest(position=position):
                self.assertAlmostEqual(
                    rate,
                    expected,
                    places=12,
                    msg="the rate is not linear between start and end",
                )
                self.assertEqual(
                    rate, float(epsilon(position)), "the rate is not stateless"
                )
                if previous is not None:
                    self.assertLessEqual(
                        rate,
                        previous + 1e-12,
                        "the schedule does not anneal monotonically from start to end",
                    )
                previous = rate

    def test_agt12_2_the_decision_key_is_order_independent_and_keyed_by_its_seed(self):
        """AGT-12.2 `_decision_key` is one `sha256` digest per decision: equal on repeat, byte-stable per family, order-independent in the mask and different when the seed or the mask differs (`rule.md` §4, §8, G3, ASM-2)."""
        key = declared_internal("rule", "_decision_key")
        for family, observation in (
            ("dense-numeric", dense_observation(0.0)),
            ("token-sequence", token_observation()),
        ):
            with self.subTest(family=family):
                digest = key(LEARNER_SEED, family, observation, ALL_MASK)
                self.assertIsInstance(
                    digest, bytes, "the key must be a hashlib digest, never a salted hash()"
                )
                self.assertEqual(len(digest), 32, "sha256 gives 32 bytes")
                self.assertEqual(
                    digest,
                    key(LEARNER_SEED, family, observation, ALL_MASK),
                    "one decision did not hash to one key, so the draw is not a "
                    "function of the decision",
                )
                self.assertNotEqual(
                    digest,
                    key(OTHER_SEED, family, observation, ALL_MASK),
                    "two seeds of one decision hashed to one key, so the seed is "
                    "not in the payload",
                )
                for permuted in itertools.permutations(ALL_MASK):
                    self.assertEqual(
                        digest,
                        key(LEARNER_SEED, family, observation, permuted),
                        "the mask is not sorted before hashing, so the key depends "
                        "on the order it was handed",
                    )
                for other_mask in ((0, 1), (0, 2), (1, 2), (1,), (2,)):
                    self.assertNotEqual(
                        digest,
                        key(LEARNER_SEED, family, observation, other_mask),
                        "two different masks hashed to one key",
                    )
                u, v = decision_draw(LEARNER_SEED, family, observation, ALL_MASK)
                self.assertGreaterEqual(u, 0.0)
                self.assertLess(u, 1.0)
                self.assertGreaterEqual(v, 0.0)
                self.assertLess(v, 1.0)

    def test_agt12_3_the_tie_break_is_the_tolerance_rule(self):
        """AGT-12.3 `_tie_break` picks the smallest masked index among equal values, the smallest of a near-tie inside `1e-9 x max(1, |best|)`, the strict maximum outside it, and never leaves the mask (`rule.md` §5, §8, `backends.md` §3, G5)."""
        tie_break = declared_internal("rule", "_tie_break")

        # Three values exactly equal: the smallest masked index, for every mask.
        for mask in NONEMPTY_MASKS:
            with self.subTest(mask=mask, values="all-zero"):
                self.assertEqual(
                    int(tie_break((0.0, 0.0, 0.0), mask)),
                    min(mask),
                    "equal values did not decide on the smallest masked index",
                )
        self.assertEqual(int(tie_break((-3.0, -3.0, -3.0), (1, 2))), 1)
        self.assertEqual(int(tie_break((-3.0, -3.0, -3.0), (2,))), 2)

        # A near-tie inside the design's tolerance resolves to the smallest index.
        near = (2.0, 2.0 + 1e-9, 0.5)
        self.assertEqual(
            int(tie_break(near, ALL_MASK)),
            0,
            "a difference inside 1e-9 x max(1, |best|) did not resolve to the "
            "smallest masked index",
        )
        self.assertEqual(int(tie_break(near, (1, 2))), 1)
        self.assertEqual(int(tie_break(near, (0, 2))), 0)

        # A strict maximum outside the tolerance wins, at whichever index it sits.
        strict = (0.0, 5.0, 4.0)
        self.assertEqual(int(tie_break(strict, ALL_MASK)), 1)
        self.assertEqual(int(tie_break((5.0, 4.0, 0.0), ALL_MASK)), 0)
        self.assertEqual(int(tie_break((0.0, 4.0, 5.0), ALL_MASK)), 2)

        # Total over the mask: one member per mask, never an index outside it.
        values = (0.1, 0.9, 0.5)
        for mask in NONEMPTY_MASKS:
            with self.subTest(mask=mask, values="distinct"):
                index = int(tie_break(values, mask))
                self.assertIn(index, mask)
                self.assertEqual(index, max(mask, key=lambda position: values[position]))
        self.assertEqual(
            int(tie_break(strict, ALL_MASK)),
            int(tie_break(strict, ALL_MASK)),
            "the tie-break is not stateless",
        )

    def test_agt12_4_the_parameter_formula(self):
        """AGT-12.4 `_param_count_for` is `architecture.md` §5's sum at those settings, and `param_count` reports the same one (`architecture.md` §5, `rule.md` §8, G10, ASM-10)."""
        count = declared_internal("model", "_param_count_for")
        architectures = self.agents().learners()["architectures"]
        dense_size = int(architectures["naive-stack"]["observation_size"])
        vocabulary = int(architectures["deep"]["observation_size"])
        width, depth = 6, 2
        dense_total = (
            dense_size * width + width + depth * (width * width + width) + 3 * width + 3
        )
        token_total = (
            vocabulary * width + depth * (width * width + width) + 3 * width + 3
        )
        self.assertEqual(int(count("naive-stack", width, depth)), dense_total)
        for kind in ("token-embedding", "deep", "plain", "residual"):
            with self.subTest(kind=kind):
                self.assertEqual(int(count(kind, width, depth)), token_total)
        kept = round((1.0 - 0.5) * width * width)
        self.assertEqual(
            int(count("sparse", width, depth, 0.5)),
            vocabulary * width + depth * (kept + width) + 3 * width + 3,
            "the sparse trunk term is not D x (k + W) with k = round((1 - s) W^2)",
        )
        self.assertEqual(
            int(count("sparse", width, depth, 0.0)),
            token_total,
            "a sparsity of 0 must be the dense layer (k = W^2)",
        )
        self.assertNotEqual(
            int(count("deep", width + 1, depth)),
            int(count("deep", width, depth)),
            "the count did not move with the width",
        )

        # The entry point reports the internal's number at one shape, and the
        # internal is a function of the four settings alone.
        cases = (
            ("naive-stack", 0.0),
            ("deep", 0.0),
            ("sparse", 0.5),
            ("wide", 0.0),
        )
        for kind, sparsity in cases:
            architecture = {"kind": kind, "width": width, "depth": depth}
            if kind == "sparse":
                architecture["sparsity"] = sparsity
            learner = self.agents().build_learner(learner_spec(architecture=architecture))
            with self.subTest(kind=kind, sparsity=sparsity):
                self.assertEqual(
                    self.agents().param_count(learner),
                    int(count(kind, width, depth, sparsity)),
                    "param_count and _param_count_for disagree at one shape",
                )

        # `wide` reads no depth (`architecture.md` §2): whatever the internal does,
        # it is the same number the entry point reports at that depth.
        for trunk_depth in (1, 2, 3):
            learner = self.agents().build_learner(
                learner_spec(architecture={"kind": "wide", "width": width, "depth": trunk_depth})
            )
            with self.subTest(kind="wide", depth=trunk_depth):
                self.assertEqual(
                    self.agents().param_count(learner),
                    int(count("wide", width, trunk_depth, 0.0)),
                )

    def test_agt12_5_the_initial_parameters_are_one_draw(self):
        """AGT-12.5 `_initial_parameters` is `architecture.md` §4's steps 1-3 as one float64 1-D array in declaration order: one seed gives one draw, the biases are exactly zero and `sparsity` changes nothing (`architecture.md` §4, `rule.md` §8, G4)."""
        initial = declared_internal("model", "_initial_parameters")
        count = declared_internal("model", "_param_count_for")
        architectures = self.agents().learners()["architectures"]
        vocabulary = int(architectures["deep"]["observation_size"])
        width, depth = 6, 1

        for kind in ("naive-stack", "deep", "plain", "residual", "wide"):
            with self.subTest(kind=kind):
                values = np.asarray(initial(kind, width, depth, 0.0, LEARNER_SEED))
                self.assertEqual(values.ndim, 1, "the array is one 1-D array")
                self.assertEqual(values.dtype, np.dtype("float64"))
                self.assertEqual(
                    int(values.shape[0]),
                    int(count(kind, width, depth, 0.0)),
                    "the draw's length is not the parameter formula's count",
                )
                self.assertTrue(np.isfinite(values).all())
                self.assertTrue(
                    np.array_equal(
                        values, np.asarray(initial(kind, width, depth, 0.0, LEARNER_SEED))
                    ),
                    "one seed did not draw one set of parameters",
                )
                self.assertFalse(
                    np.array_equal(
                        values, np.asarray(initial(kind, width, depth, 0.0, OTHER_SEED))
                    ),
                    "two seeds drew one set of parameters",
                )
                biases = (width if kind == "naive-stack" else 0) + depth * width + 3
                self.assertEqual(
                    int(np.count_nonzero(values == 0.0)),
                    biases,
                    "every bias must be exactly 0.0 and draw nothing, so the only "
                    "zeros are the biases (%d of them)" % biases,
                )

        # A sparse learner's mask comes last, so the weight draws are the draws
        # its shapes would give any other kind and the sparsity changes none of
        # them (`architecture.md` §4).
        sparse = np.asarray(initial("sparse", width, depth, 0.5, LEARNER_SEED))
        deep = np.asarray(initial("deep", width, depth, 0.0, LEARNER_SEED))
        self.assertEqual(sparse.ndim, 1)
        self.assertEqual(sparse.dtype, np.dtype("float64"))
        self.assertTrue(np.isfinite(sparse).all())
        input_block = vocabulary * width
        self.assertTrue(
            np.array_equal(sparse[:input_block], deep[:input_block]),
            "a sparse learner's input block is not the draw its shapes give any "
            "other kind (architecture.md §4's step 4 comes last)",
        )
        self.assertTrue(
            np.array_equal(
                sparse[:input_block],
                np.asarray(initial("sparse", width, depth, 0.0, LEARNER_SEED))[:input_block],
            ),
            "sparsity changed the parameters drawn before the masks",
        )


if __name__ == "__main__":
    unittest.main()
