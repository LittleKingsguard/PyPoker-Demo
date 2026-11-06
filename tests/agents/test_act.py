"""AGT-5 — `act(learner, observation, legal_mask)`.

Drives `docs/L2/agents/surface.md` §6, `docs/L3/agents/rule.md` §1, §4-§5 and
`docs/L3/agents/errors.md` §3: a mapping carrying a plain `int` under `action`,
a member of the mask and of {0, 1, 2}; one state and one decision give one
index whatever the call order; a total tie decides in the greedy arm on the
smallest masked index; the mask, observation (shape, dtype and family) and
learner refusals name their contract (D-2, ASM-5).
"""

import unittest

import numpy as np
from collections.abc import Mapping

from _agents_support import (
    ALL_MASK,
    NONEMPTY_MASKS,
    TIE_SEEDS,
    AgentsCase,
    dense_observation,
    features,
    flat_encoder,
    observation_template,
    token_encoder,
    token_observation,
)


class ActTest(AgentsCase):
    def test_agt5_1_the_action_is_a_plain_int_in_a_mapping(self):
        """AGT-5.1 the decision record is a mapping whose `action` is a plain Python `int` (`surface.md` §6, G2, `records.md` §6)."""
        package = self.agents()
        learner = self.build(kind="naive-stack")
        record = package.act(learner, dense_observation(), ALL_MASK)
        self.assertIsInstance(record, Mapping)
        self.assertIn("action", record)
        action = record["action"]
        self.assertNotIsInstance(action, bool)
        self.assertIsInstance(action, int)
        self.assertIn(action, ALL_MASK)

    def test_agt5_2_the_chosen_index_is_a_member_of_the_mask(self):
        """AGT-5.2 the chosen index is one of the mask's members, for every mask shape (`surface.md` §2, §6, D-2)."""
        package = self.agents()
        learner = self.build(kind="naive-stack")
        for mask in NONEMPTY_MASKS:
            with self.subTest(mask=mask):
                action = package.act(learner, dense_observation(), mask)["action"]
                self.assertIn(action, mask)
                self.assertIn(action, ALL_MASK)

    def test_agt5_3_a_mask_without_zero_never_yields_zero(self):
        """AGT-5.3 a mask of {1, 2} never yields fold (`surface.md` §2, D-2)."""
        package = self.agents()
        learner = self.build(kind="naive-stack")
        for mask in ((1,), (2,), (1, 2)):
            with self.subTest(mask=mask):
                for offset in (0.0, 0.25, -0.4):
                    action = package.act(learner, dense_observation(offset), mask)["action"]
                    self.assertNotEqual(action, 0)

    def test_agt5_4_two_calls_at_one_decision_agree(self):
        """AGT-5.4 one state and one decision give one index, in either call order (`surface.md` §6, `rule.md` §4, G3, ASM-5)."""
        package = self.agents()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        probes = [
            (dense_observation(0.0), ALL_MASK),
            (dense_observation(0.35), (1, 2)),
            (dense_observation(-0.7), (0, 2)),
        ]
        forward = [
            package.act(learner, observation, mask)["action"]
            for observation, mask in probes
        ]
        backward = [
            package.act(learner, observation, mask)["action"]
            for observation, mask in reversed(probes)
        ]
        self.assertEqual(forward, list(reversed(backward)))
        for index in (0, 1, 2):
            with self.subTest(probe=index):
                self.assertIn(forward[index], probes[index][1])

    def test_agt5_5_the_refusals(self):
        """AGT-5.5 each refused argument is refused naming the entry point and the key (`surface.md` §6, `errors.md` §3)."""
        package = self.agents()
        dense = self.build(kind="naive-stack")
        token = self.build(kind="deep")
        observation = dense_observation()
        cases = (
            ("a dict as the learner", package.act, ({"action": 1}, observation, ALL_MASK),
             (("learner",),)),
            ("a baseline as the learner", package.act,
             (package.build_baseline("always-call", 7314), observation, ALL_MASK),
             (("learner",),)),
            ("an empty mask", package.act, (dense, observation, ()),
             (("mask",),)),
            ("a mask repeating an index", package.act, (dense, observation, (1, 1)),
             (("mask",),)),
            ("a mask outside the vocabulary", package.act, (dense, observation, (0, 1, 3)),
             (("mask",), ("3",))),
            ("a negative mask index", package.act, (dense, observation, (-1, 1)),
             (("mask",), ("-1",))),
            ("a token observation on a dense learner", package.act,
             (dense, token_observation(), ALL_MASK),
             (("observation",), ("token",), ("dense",))),
            ("a dense observation on a token learner", package.act,
             (token, dense_observation(), ALL_MASK),
             (("observation",), ("token",), ("dense",))),
            ("a dense observation of the wrong width", package.act,
             (dense, dense_observation(width=96), ALL_MASK),
             (("observation",), ("96",), ("203",))),
            ("a NaN observation", package.act,
             (dense, np.full(203, np.nan, dtype=np.float32), ALL_MASK),
             (("observation",), ("finite", "nan"))),
            ("an infinite observation", package.act,
             (dense, np.full(203, np.inf, dtype=np.float32), ALL_MASK),
             (("observation",), ("finite", "inf"))),
        )
        for label, fn, args, groups in cases:
            with self.subTest(case=label):
                self.assert_refused(fn, *args, entry="act", groups=groups, label=label)

    def test_agt5_6_a_total_tie_is_the_smallest_masked_index(self):
        """AGT-5.6 a zero observation of the declared shape, dtype and family gives three values of exactly 0.0, so at the annealed position the greedy answer is the smallest masked index: over 105 invented decisions every index is a mask member and at least 85 of them are that index (`rule.md` §2, §4-§5, `architecture.md` §4, G5)."""
        package = self.agents()
        zero, spec = observation_template("dense-numeric")
        self.assertEqual(np.dtype(spec["dtype"]), np.dtype("float32"))
        probes = 0
        agreements = 0
        for seed in TIE_SEEDS:
            # A quiet batch reaches the annealed rate without moving a value: the
            # initialisation of `architecture.md` §4 has zero biases, so every
            # value at the zero observation is exactly 0.0 and §5's tolerance
            # makes the smallest masked index the greedy answer.
            learner = self.annealed_learner(
                "tie-%d" % seed,
                {"kind": "naive-stack", "width": 4, "depth": 1, "seed": seed},
                quiet=True,
            )
            for mask in NONEMPTY_MASKS:
                action = package.act(learner, zero, mask)["action"]
                probes += 1
                self.assertIn(action, mask)
                if action == min(mask):
                    agreements += 1
        self.assertGreaterEqual(probes, 100)
        self.assertGreaterEqual(
            agreements,
            85,
            "%d of %d total-tie decisions took the smallest masked index; at the "
            "annealed rate only 5%% of them should explore, so the greedy arm's "
            "tie-break is not §5's" % (agreements, probes),
        )

    def test_agt5_7_the_observation_dtype_is_checked(self):
        """AGT-5.7 an observation of the declared shape in the wrong dtype is refused naming both dtypes (`surface.md` §6, `errors.md` §3, `features/surface.md` §5, `backends.md` §4)."""
        package = self.agents()
        dense = self.build(kind="naive-stack", encoder=flat_encoder())
        token = self.build(kind="deep", encoder=token_encoder())
        dense_spec = features().observation_spec(flat_encoder())
        token_spec = features().observation_spec(token_encoder())
        wrong_dense = np.zeros(tuple(dense_spec["shape"]), dtype=np.float64)
        wrong_token = np.zeros(tuple(token_spec["shape"]), dtype=np.int64)
        cases = (
            (
                "a float64 dense observation",
                dense,
                wrong_dense,
                (("observation", "dtype"), ("float64",), ("float32",)),
            ),
            (
                "an int64 token observation",
                token,
                wrong_token,
                (("observation", "dtype"), ("int64",), ("int32",)),
            ),
        )
        for label, learner, observation, groups in cases:
            with self.subTest(case=label):
                self.assert_refused(
                    package.act,
                    learner,
                    observation,
                    ALL_MASK,
                    entry="act",
                    groups=groups,
                    label=label,
                )


if __name__ == "__main__":
    unittest.main()
