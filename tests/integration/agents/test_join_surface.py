"""JOIN-AGT-1 — the ten names of `agents` at the join.

`docs/L1/e2e-surface.md` §3.3 fixes the ten entry points and their kinds; this
family judges the surface as a caller meets it: each name is callable with objects
built by the *other* two modules' entry points (`features.build_encoder`,
`engine.new_hand`, `engine.play_hand`), and a minimal call returns the declared kind
(`docs/L2/agents/surface.md` §1, §4–§12).  `learners()` is read under the four keys
§3 declares, the rule catalogue among them: D-19 makes it `learning_rules`, carrying
more than one member and never the singular constant it replaced (`docs/L1/rules.md`
§2, D-19).  A name that is absent, or that returns a shape the next module cannot
consume, is one finding per name (`battery.md` §3 FAM-1).
"""

import importlib.util
import os
import sys
import unittest
from collections.abc import Mapping

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "agents_join_support" in sys.modules:
    J = sys.modules["agents_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "agents_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["agents_join_support"] = J
    _spec.loader.exec_module(J)

# The ten names in the L1 order (docs/L1/e2e-surface.md §3.3).
THE_TEN = (
    "learners",
    "build_learner",
    "param_count",
    "act",
    "learn",
    "save",
    "load",
    "as_policy",
    "baselines",
    "build_baseline",
)


class SurfaceAtTheJoin(J.JoinCase):
    """The ten names, called as the other modules' objects let a caller call them."""

    def test_join_agt_1_1_each_of_the_ten_is_a_module_level_callable(self):
        """JOIN-AGT-1.1 the ten are module-level callables, and no eleventh is exported.

        `docs/L2/agents/surface.md` §1: each of the ten names is a *module-level name*
        of the `agents` package and nothing below one of them is contract, while the
        ten themselves are fixed — L2 adds, removes and renames none
        (`docs/L1/e2e-surface.md` §1, §3.3).  `__all__` is the layout's (L3:
        `docs/L3/agents/README.md` §4, guardrail G1) and not L2's, so this case
        requires no `__all__`, never asserts its order and reads it only where a
        package declares one: the ten names without `__all__` satisfy L2.  Caught
        here are a package that renames or drops one of the ten, one that leaves a
        name reachable only inside a submodule or on a class instead of at the
        package's own module level, and, where `__all__` exists — the one place a
        package lists what a `from agents import *` exports — one that exports a name
        outside the ten.
        """
        package = J.mod("agents")
        namespace = vars(package)
        for name in THE_TEN:
            with self.subTest(name=name):
                self.assertIn(
                    name,
                    namespace,
                    "agents.%s must be a module-level name of the package, not a name "
                    "reachable only inside a submodule or on a class "
                    "(docs/L2/agents/surface.md §1, docs/L1/e2e-surface.md §1)"
                    % (name,),
                )
                self.assertTrue(
                    callable(getattr(package, name)),
                    "agents.%s must be a module-level callable "
                    "(docs/L1/e2e-surface.md §3.3, docs/L2/agents/surface.md §1)"
                    % (name,),
                )
        declared = getattr(package, "__all__", None)
        if declared is None:
            # L2 declares no `__all__`: a package with the ten names and none
            # satisfies it, so there is no export list to read here.
            return
        listed = list(declared)
        self.assertEqual(
            [name for name in listed if name not in THE_TEN],
            [],
            "a package that declares __all__ must export the ten and no eleventh "
            "name (docs/L2/agents/surface.md §1, docs/L1/e2e-surface.md §3.3): %r"
            % (listed,),
        )
        for name in listed:
            with self.subTest(exported=name):
                self.assertTrue(
                    callable(getattr(package, name, None)),
                    "an exported name must be callable on the package itself "
                    "(docs/L2/agents/surface.md §1): %r" % (name,),
                )

    def test_join_agt_1_2_every_name_makes_a_minimal_call_of_its_declared_kind(self):
        """JOIN-AGT-1.2 each of the ten makes a minimal call with crossed objects.

        The objects are the ones this layer builds from the other modules' entry
        points: a `features.build_encoder` encoder, an `engine.new_hand` deal with
        its readout and its legal descriptors, an `engine.play_hand` episode, and a
        checkpoint `agents.save` wrote.  The declared kinds are
        `docs/L1/e2e-surface.md` §3.3's (`records.md` §3–§7 for the records).
        """
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        spec = J.learner_spec(
            "naive-stack", J.WIDTH_ONE, J.DEPTH_ONE, J.LEARNER_SEED
        )
        built = J.build_learner(spec)
        hand = J.new_hand(J.DEAL_DECISION_A)
        facts = J.readout(hand)
        legal = J.legal_actions(hand)
        observation = J.encode(encoder, facts)
        mask = J.legal_indices(legal)
        episode = J.play_hand(J.DEAL_REWARD_A, J.caller, J.caller)
        batch = J.seat_transitions(episode, 0, encoder)
        checkpoint = self.checkpoint_path(J.CHECKPOINT_ALPHA)

        def check_catalogue():
            declared = J.learners()
            self.assertIsInstance(
                declared, Mapping, "learners() must return one mapping (surface §3)"
            )
            for key in (
                "backends",
                "architectures",
                "learning_rules",
                "hyper",
            ):
                self.assertIn(
                    key,
                    declared,
                    "learners() must carry the %r key (docs/L2/agents/surface.md §3, "
                    "docs/L1/rules.md §2, D-19)" % (key,),
                )
            self.assertEqual(
                len(declared["backends"]), 2, "learners() declares two backends"
            )
            self.assertGreater(
                len(declared["architectures"]),
                0,
                "learners() must declare its architecture kinds",
            )
            self.assertGreaterEqual(
                len(declared["learning_rules"]),
                2,
                "learners() publishes the rule catalogue, and it carries more than one "
                "member — a spec selects from it and every member is a training target "
                "(docs/L2/agents/surface.md §3, docs/L1/rules.md §2, D-19)",
            )

        def check_build():
            self.assertIsInstance(
                J.param_count(built),
                int,
                "build_learner must return a learner a caller can measure with "
                "param_count (docs/L1/e2e-surface.md §3.3)",
            )

        def check_count():
            count = J.param_count(built)
            self.assertIsInstance(count, int)
            self.assertGreater(
                count,
                0,
                "param_count must return the positive trainable count of a built "
                "learner (docs/L2/agents/surface.md §5)",
            )

        def check_act():
            index = J.action_index(J.act(built, observation, mask))
            self.assert_index_in(index, mask, "agents.act at the join")

        def check_learn():
            statistics = J.learn(built, batch)
            self.assertTrue(
                J.finite(J.td_error(statistics)),
                "learn must return a finite td_error (docs/L2/agents/surface.md §7)",
            )
            self.assertEqual(J.transitions_consumed(statistics), len(batch))

        def check_save():
            written = J.save(built, checkpoint)
            self.assertTrue(
                os.path.exists(str(written)),
                "save must return a path that names the checkpoint it wrote "
                "(docs/L2/agents/surface.md §8): %r" % (written,),
            )

        def check_load():
            restored = J.load(None, checkpoint)
            self.assertIsInstance(J.param_count(restored), int)

        def check_policy():
            policy = J.as_policy(built, encoder, J.LEARNER_SEED)
            self.assertTrue(
                callable(policy),
                "as_policy must return a callable in the policy protocol "
                "(docs/L1/e2e-surface.md §2)",
            )
            self.assert_descriptor_in(legal, policy(facts, legal), "as_policy")

        def check_baselines():
            declared = J.baselines()
            self.assertIsInstance(declared, Mapping)
            self.assertEqual(
                set(declared),
                {"random", "always-call", "oracle"},
                "baselines() must name exactly the three of D-6 "
                "(docs/L2/agents/surface.md §11)",
            )

        def check_baseline():
            policy = J.build_baseline("always-call", J.BASELINE_SEED)
            self.assertTrue(callable(policy))
            self.assert_descriptor_in(
                legal, policy(facts, legal), "build_baseline"
            )

        minimal = (
            ("learners", check_catalogue),
            ("build_learner", check_build),
            ("param_count", check_count),
            ("act", check_act),
            ("learn", check_learn),
            ("save", check_save),
            ("load", check_load),
            ("as_policy", check_policy),
            ("baselines", check_baselines),
            ("build_baseline", check_baseline),
        )
        for name, check in minimal:
            with self.subTest(entry=name):
                check()


if __name__ == "__main__":
    unittest.main()
