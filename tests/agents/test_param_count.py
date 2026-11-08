"""AGT-4 — `param_count(learner)`.

Drives `docs/L2/agents/surface.md` §5, `docs/L2/agents/learner.md` §3,
`docs/L3/agents/architecture.md` §5 and `docs/L1/rules.md` §3: one plain
integer, a function of the spec alone, equal in both backends (one model, D-7)
and under both catalogue members (D-19), strictly larger at a larger width,
unchanged by `learn`, refused for a baseline, and reported by a restored learner
(ASM-10, ASM-5).
"""

import unittest

from _agents_support import (
    AgentsCase,
    batch,
    dense_observation,
    learner_spec,
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

    def test_agt4_8_one_architecture_counts_the_same_under_both_rules(self):
        """AGT-4.8 the same architecture reports one `param_count` under either catalogue member (`surface.md` §5, `rules.md` §3, ASM-10, D-19).

        A rule changes the arithmetic of a target and nothing of the state layout —
        the online parameters and their target copy — so the counting rule of
        `learner.md` §3, one rule over every trainable value, cannot move with it.
        This is the capacity half of the pair `rules.md` §8 makes comparable: two
        arms may differ on the rule and still be capacity-matched.
        """
        package = self.agents()
        catalogue = tuple(package.learners()["learning_rules"])
        self.assertGreaterEqual(len(catalogue), 2)
        for kind in ("naive-stack", "deep", "sparse"):
            with self.subTest(kind=kind):
                counts = {}
                for rule in catalogue:
                    learner = package.build_learner(
                        learner_spec(kind=kind, extra={"learning_rule": rule})
                    )
                    count = package.param_count(learner)
                    self.assertNotIsInstance(count, bool, "a flag is not a count")
                    self.assertIsInstance(count, int)
                    self.assertGreater(count, 0)
                    counts[rule] = count
                undeclared = package.param_count(
                    package.build_learner(learner_spec(kind=kind))
                )
                self.assertEqual(
                    sorted(counts.values()),
                    [undeclared] * len(catalogue),
                    "the %r kind reports %r under the catalogue's members and %d "
                    "under the declared default alone: a rule may not move the "
                    "trainable count (surface.md §5, rules.md §3, ASM-10, D-19)"
                    % (kind, counts, undeclared),
                )


if __name__ == "__main__":
    unittest.main()
