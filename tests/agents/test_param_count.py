"""AGT-4 — `param_count(learner)`.

Drives `docs/L2/agents/surface.md` §5, `docs/L2/agents/learner.md` §3 and
`docs/L3/agents/architecture.md` §5: one plain integer, a function of the spec
alone, equal in both backends (one model, D-7), strictly larger at a larger
width, unchanged by `learn`, refused for a baseline, and reported by a restored
learner (ASM-10, ASM-5).
"""

import unittest

from _agents_support import (
    AgentsCase,
    batch,
    dense_observation,
)


class ParamCountTest(AgentsCase):
    def test_agt4_1_the_count_is_a_plain_positive_int(self):
        """AGT-4.1 `param_count` is a plain `int` (not a `bool`), positive (`surface.md` §5, G10, ASM-10)."""
        package = self.agents()
        for kind in ("naive-stack", "deep", "wide", "sparse"):
            with self.subTest(kind=kind):
                count = package.param_count(self.build(kind=kind))
                self.assertNotIsInstance(count, bool)
                self.assertIsInstance(count, int)
                self.assertGreater(count, 0)

    def test_agt4_2_one_spec_one_count(self):
        """AGT-4.2 two learners from one spec report one count (`surface.md` §5, ASM-10)."""
        package = self.agents()
        first = package.param_count(self.build())
        second = package.param_count(self.build())
        self.assertEqual(first, second)

    def test_agt4_3_both_backends_report_one_capacity(self):
        """AGT-4.3 the same kind/width/depth counts equally in `numpy` and `torch` (D-7, `learner.md` §2, ASM-10)."""
        package = self.agents()
        for kind in ("naive-stack", "deep"):
            with self.subTest(kind=kind):
                numpy_count = package.param_count(self.build(backend="numpy", kind=kind))
                torch_count = package.param_count(self.build(backend="torch", kind=kind))
                self.assertEqual(numpy_count, torch_count)

    def test_agt4_4_a_larger_width_is_strictly_more_capacity(self):
        """AGT-4.4 width 96 counts more than width 61, and a wider token kind more than a narrow one (`architecture.md` §5)."""
        package = self.agents()
        self.assertGreater(
            package.param_count(self.build(kind="naive-stack", width=96, depth=1)),
            package.param_count(self.build(kind="naive-stack", width=61, depth=1)),
        )
        self.assertGreater(
            package.param_count(self.build(kind="deep", width=24, depth=1)),
            package.param_count(self.build(kind="deep", width=12, depth=1)),
        )

    def test_agt4_5_learn_does_not_change_the_capacity(self):
        """AGT-4.5 capacity is a function of the spec alone, not of a step (`surface.md` §5, `learner.md` §3)."""
        package = self.agents()
        learner = self.build(kind="naive-stack", width=8, depth=1)
        before = package.param_count(learner)
        package.learn(learner, batch([dense_observation(offset) for offset in (0.1, 0.2)]))
        self.assertEqual(package.param_count(learner), before)

    def test_agt4_6_a_baseline_is_refused(self):
        """AGT-4.6 a baseline is not a learner, so its count is refused (`surface.md` §5, `baselines.md` §1, ASM-10)."""
        package = self.agents()
        baseline = package.build_baseline("random", 7314)
        self.assert_refused(
            package.param_count,
            baseline,
            entry="param_count",
            groups=(("learner",), ("baseline",)),
            label="param_count of a baseline",
        )

    def test_agt4_7_a_restored_learner_reports_the_saved_count(self):
        """AGT-4.7 a restored learner reports the saved count (`surface.md` §5, `checkpoint.md` §4, ASM-5)."""
        package = self.agents()
        learner = self.build(kind="deep", width=8, depth=1)
        kept = package.param_count(learner)
        path = package.save(learner, self.tempdir() + "/v-8127-count.pt")
        restored = package.load(None, path)
        self.assertEqual(package.param_count(restored), kept)


if __name__ == "__main__":
    unittest.main()
