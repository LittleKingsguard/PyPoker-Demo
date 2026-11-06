"""AGT-10 — seeds and purity.

Drives `docs/L2/agents/surface.md` §1, §4, `docs/L3/agents/rule.md` §4 and
`docs/L1/protocol.md` §4: no entry point advances or reads the global `random`
module or `numpy.random`'s global state, two learners from one spec make one
decision on a **learned** learner (20 decisions, at least 16 greedy-expected),
and a learner at another seed explores differently because the draw is its own
(ASM-2, D-6).
"""

import random
import unittest

import numpy as np

from _agents_support import (
    ALL_MASK,
    BASELINE_SEED,
    CHECKPOINT_NAMES,
    EXTRA_LEARNER_SEED,
    LEARNER_SEED,
    AgentsCase,
    anneal_batch,
    dense_observation,
    flat_encoder,
    learner_spec,
    transition,
)

GLOBAL_SEED = 51231


class SeedTest(AgentsCase):
    def test_agt10_1_no_entry_point_touches_a_global_random_stream(self):
        """AGT-10.1 the global `random` and `numpy.random` streams continue as if no `agents` call had happened (`surface.md` §1, rule.md §4, ASM-2)."""
        package = self.agents()
        rows = self.decisions(4)  # materialised before the streams are seeded
        dense = [row["dense"] for row in rows]
        masks = [row["mask"] for row in rows]
        encoder = flat_encoder()
        folder = self.tempdir()

        def draw():
            return random.random(), float(np.random.random())

        random.seed(GLOBAL_SEED)
        np.random.seed(GLOBAL_SEED + 1)
        expected = draw()

        random.seed(GLOBAL_SEED)
        np.random.seed(GLOBAL_SEED + 1)
        learner = package.build_learner(learner_spec(kind="naive-stack"))
        package.learners()
        package.baselines()
        package.param_count(learner)
        package.act(learner, dense[0], masks[0])
        package.learn(learner, [transition(dense[0]), transition(dense[1])])
        path = package.save(learner, folder + "/" + CHECKPOINT_NAMES[0])
        package.load(None, path)
        package.as_policy(learner, encoder, LEARNER_SEED)
        for name in ("random", "always-call", "oracle"):
            package.build_baseline(name, BASELINE_SEED)
        observed = draw()

        self.assertEqual(
            observed,
            expected,
            "an agents entry point advanced the global random stream",
        )

    def test_agt10_2_one_spec_two_learners_make_one_decision(self):
        """AGT-10.2 two learners from one spec, taught one batch, make one decision on 20 decisions of which at least 16 are greedy-expected (`surface.md` §4, `rule.md` §4, ASM-2)."""
        package = self.agents()
        records = anneal_batch("naive-stack")
        first = self.annealed_learner(
            "two-a", {"kind": "naive-stack", "width": 8, "depth": 1}, records
        )
        second = self.annealed_learner(
            "two-b", {"kind": "naive-stack", "width": 8, "depth": 1}, records
        )
        rows = self.decisions(20)
        observations, masks = map(list, zip(*self.decision_observations(rows, "naive-stack")))
        self.greedy_arm(LEARNER_SEED, "naive-stack", observations, masks, 16)
        for row in rows:
            with self.subTest(hand=row["readout"]["hole"]):
                self.assertEqual(
                    package.act(first, row["dense"], row["mask"])["action"],
                    package.act(second, row["dense"], row["mask"])["action"],
                    "two learners from one spec disagreed after one batch, so the "
                    "initialisation is not the seed's alone",
                )

    def test_agt10_3_another_seed_explores_differently(self):
        """AGT-10.3 a learner at another seed draws its own exploration, differing on at least one decision (`surface.md` §6, `rule.md` §4, ASM-2)."""
        package = self.agents()
        mine = self.build(kind="naive-stack", width=8, depth=1, seed=LEARNER_SEED)
        other = self.build(kind="naive-stack", width=8, depth=1, seed=EXTRA_LEARNER_SEED)
        differences = 0
        for step in range(10):
            observation = dense_observation(0.11 * step)
            if (
                package.act(mine, observation, ALL_MASK)["action"]
                != package.act(other, observation, ALL_MASK)["action"]
            ):
                differences += 1
        self.assertGreater(
            differences,
            0,
            "two learners at two seeds answered ten decisions identically, so "
            "the draw is not the learner's own",
        )


if __name__ == "__main__":
    unittest.main()
