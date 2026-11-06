"""JOIN-AGT-9 — the R1↔R2 same-work parity (D-7, `ladder.md` §5).

`docs/L2/agents/learner.md` §2: R2 recreates R1 in PyTorch so the speed difference is
measured on identical work, so the two backends may change which library performs the
arithmetic and nothing a decision reads — not the model, not the rule, not the sample
order, not the tie-break.  `docs/L2/agents/surface.md` §10 and §5 carry the two
observable halves: one model shape is one parameter count, and one learned state is
one decision boundary.

This is the module's own share of `docs/L1/battery.md` §3 FAM-13's same-work check,
which the L1 battery cannot reach while `training` does not exist: FAM-13 asks
`training.run` for two rungs' seeded hands, and here the same question is asked of the
two backends directly, on real readouts, after the same real batch.  The comparison is
made after learning — the exploration draw is keyed by the seed and the decision
(`docs/L3/agents/rule.md` §4), so a fresh learner's agreement would prove nothing about
the greedy arm — and the case proves the state is past its initial one by requiring the
learned decisions to differ from a fresh learner's somewhere.
"""

import importlib.util
import os
import sys
import unittest

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


class SameWorkParity(J.JoinCase):
    """One spec, two backends, one batch, one decision boundary."""

    def spec(self, backend="numpy"):
        return J.learner_spec(
            "naive-stack",
            J.WIDTH_ONE,
            J.DEPTH_TWO,
            J.LEARNER_SEED,
            backend=backend,
        )

    def test_join_agt_9_1_one_shape_is_one_parameter_count(self):
        """JOIN-AGT-9.1 the two backends report one capacity for one model shape.

        `docs/L2/agents/learner.md` §2–§3 and ASM-10: the counting rule is one rule
        over every trainable value, so the two backends' counts coincide; `docs/L2/
        agents/surface.md` §5 makes the count the matched-budget measurement a
        comparison pair is held to.
        """
        numpy_learner = J.build_learner(self.spec("numpy"))
        torch_learner = J.build_learner(self.spec("torch"))
        count = J.param_count(numpy_learner)
        self.assertIsInstance(count, int)
        self.assertGreater(
            count,
            0,
            "a learner holds the positive trainable count of its model "
            "(docs/L2/agents/surface.md §5)",
        )
        self.assertEqual(
            J.param_count(torch_learner),
            count,
            "the backend may change the arithmetic and not the capacity "
            "(D-7, docs/L2/agents/learner.md §2, ASM-10)",
        )

    def test_join_agt_9_2_the_two_backends_choose_the_same_index_after_one_batch(self):
        """JOIN-AGT-9.2 after the same real batch, numpy and torch decide alike.

        `docs/L2/agents/learner.md` §2 and `docs/L1/ladder.md` §5: on the same seeded
        hands the two variants must choose the same actions; the check is on decisions
        and not on values, because two numerical libraries need not round identically.
        The batch is real and the schedule is annealed past the catalogue's `samples`
        so the compared decisions are mostly greedy, and a fresh learner of the same
        spec is the control: it must differ somewhere, which is what shows the greedy
        arm — not the keyed exploration draw alone — decided.
        """
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        numpy_learner = J.build_learner(self.spec("numpy"))
        torch_learner = J.build_learner(self.spec("torch"))
        control = J.build_learner(self.spec("numpy"))
        episode = J.play_hand(J.DEAL_POLICY_B, J.caller, J.caller)
        batch = J.seat_transitions(episode, 0, encoder)
        decisions = []
        for deal in (J.DEAL_DECISION_A, J.DEAL_DECISION_B):
            decisions.extend(J.observations(deal, J.caller, encoder))
        self.assertGreaterEqual(
            len(decisions),
            10,
            "the parity must be shown over at least ten decisions of two real hands "
            "(docs/L1/ladder.md §5)",
        )
        fresh = [
            J.action_index(J.act(control, observation, mask))
            for observation, mask in decisions
        ]
        samples = J.exploration_samples()
        batch = J.tiled(batch, samples)
        for label, learner in (("numpy", numpy_learner), ("torch", torch_learner)):
            self.assertEqual(
                J.param_count(learner),
                J.param_count(numpy_learner),
                "the pair is matched on capacity (ASM-10): %s" % (label,),
            )
            statistics = J.learn(learner, batch)
            self.assertEqual(
                J.transitions_consumed(statistics),
                len(batch),
                "learn consumes the caller's batch (%s)" % (label,),
            )
            self.assertTrue(
                J.finite(J.td_error(statistics)),
                "learn reports a finite td_error (%s)" % (label,),
            )
        by_numpy = [
            J.action_index(J.act(numpy_learner, observation, mask))
            for observation, mask in decisions
        ]
        by_torch = [
            J.action_index(J.act(torch_learner, observation, mask))
            for observation, mask in decisions
        ]
        self.assertEqual(
            by_torch,
            by_numpy,
            "on the same real readouts the two backends must choose the same "
            "actions (D-7, docs/L1/ladder.md §5, docs/L1/battery.md §3 FAM-13)",
        )
        self.assertNotEqual(
            by_numpy,
            fresh,
            "the comparison must be decided after learning: the keyed exploration "
            "draw is one decision, so a fresh learner agreeing everywhere would "
            "show that no greedy decision was compared "
            "(docs/L3/agents/rule.md §4, §5)",
        )


if __name__ == "__main__":
    unittest.main()
