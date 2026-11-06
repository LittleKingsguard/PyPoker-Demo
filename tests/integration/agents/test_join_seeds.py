"""JOIN-AGT-10 — seeds and purity at the join.

`docs/L2/agents/surface.md` §1 and `docs/L1/protocol.md` §4 (ASM-2): no `agents` entry
point leaves the global `random` stream moved, and none takes a seed for the deal —
`engine.new_hand` is the project's single seeding point (`docs/L2/engine/surface.md`
§1).  A learner's exploration is drawn from its own seeded generator keyed by the
decision, so two learners from one spec are one learner and another seed explores
differently (`docs/L2/agents/surface.md` §4, §6; `docs/L3/agents/rule.md` §4).
"""

import importlib.util
import os
import random
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


class SeedsAndPurity(J.JoinCase):
    """The global stream, and the one-seed/other-seed properties."""

    def spec(self, seed=J.LEARNER_SEED):
        return J.learner_spec(
            "naive-stack", J.WIDTH_ONE, J.DEPTH_ONE, seed
        )

    def draws(self):
        return [random.random() for _ in range(J.STREAM_DRAWS)]

    def test_join_agt_10_1_no_learner_call_moves_the_global_stream(self):
        """JOIN-AGT-10.1 the stream after act/learn/save/load/as_policy is the control's.

        The control runs the same *engine* call — `new_hand`, the one legitimate
        moving call — with every `agents` call absent, so the only difference is the
        module under judgement.  The observation, the mask and the readout handed to
        the policy are prepared before the stream is seeded, so nothing but an `agents`
        entry point (and its own inside) can be blamed for a moved stream.
        """
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        spec = self.spec()
        held = J.new_hand(J.DEAL_SEED_A)
        facts = J.readout(held)
        legal = J.legal_actions(held)
        observation = J.encode(encoder, facts)
        mask = J.legal_indices(legal)
        episode = J.play_hand(J.DEAL_CHECKPOINT_A, J.caller, J.caller)
        batch = J.seat_transitions(episode, 0, encoder)

        random.seed(J.STREAM_SEED_A)
        J.new_hand(J.DEAL_SEED_A)
        learner = J.build_learner(spec)
        J.action_index(J.act(learner, observation, mask))
        J.learn(learner, batch)
        path = J.save(learner, self.checkpoint_path(J.CHECKPOINT_GAMMA))
        restored = J.load(None, path)
        J.as_policy(restored, encoder, J.LEARNER_SEED)(facts, legal)
        after = self.draws()

        random.seed(J.STREAM_SEED_A)
        J.new_hand(J.DEAL_SEED_A)
        control = self.draws()
        self.assertEqual(
            after,
            control,
            "no agents entry point may advance the global random stream; the deal is "
            "the only legitimately moving call (ASM-2, docs/L2/agents/surface.md §1)",
        )

    def test_join_agt_10_2_a_baseline_s_whole_episode_moves_no_stream(self):
        """JOIN-AGT-10.2 a baseline played to the end leaves the stream where the deal did.

        `docs/L3/agents/baselines.md` §1: a baseline advances no state and seeds, reads
        or advances nothing.  The control applies the same descriptors through the same
        engine calls with the baseline absent, so the deal (`new_hand`) is the only
        difference left.
        """
        random.seed(J.STREAM_SEED_B)
        hand = J.new_hand(J.DEAL_SEED_B)
        policy = J.build_baseline("random", J.BASELINE_SEED)
        applied = []
        steps = 0
        while not J.is_terminal(hand) and steps < 200:
            chosen = policy(J.readout(hand), J.legal_actions(hand))
            applied.append(chosen)
            hand = J.apply_action(hand, chosen)
            steps += 1
        self.assertGreater(steps, 0, "the baseline must play a whole episode")
        self.assertTrue(J.is_terminal(hand), "the episode must end")
        after = self.draws()

        random.seed(J.STREAM_SEED_B)
        hand = J.new_hand(J.DEAL_SEED_B)
        for chosen in applied:
            if not J.is_terminal(hand):
                J.readout(hand)
                J.legal_actions(hand)
            hand = J.apply_action(hand, chosen)
        control = self.draws()
        self.assertEqual(
            after,
            control,
            "a baseline played through a whole episode may not advance the global "
            "random stream (ASM-2, docs/L3/agents/baselines.md §1)",
        )

    def test_join_agt_10_3_two_learners_from_one_spec_are_one_decision_boundary(self):
        """JOIN-AGT-10.3 one spec builds one learner: one count, one decision.

        `docs/L2/agents/surface.md` §4: completion happens at construction and draws
        from the learner's own seeded generator, so two learners from one spec are one
        learner in capacity and in every decision; §6: one state, one observation and
        one mask give one index, on a real readout.
        """
        spec = self.spec()
        first = J.build_learner(spec)
        second = J.build_learner(spec)
        self.assertEqual(
            J.param_count(second),
            J.param_count(first),
            "two learners from one spec carry one parameter count "
            "(docs/L2/agents/surface.md §4)",
        )
        hand = J.new_hand(J.DEAL_POLICY_A)
        facts = J.readout(hand)
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        observation = J.encode(encoder, facts)
        mask = J.legal_indices(J.legal_actions(hand))
        by_first = J.action_index(J.act(first, observation, mask))
        by_second = J.action_index(J.act(second, observation, mask))
        self.assert_index_in(by_first, mask)
        self.assertEqual(
            by_second,
            by_first,
            "two learners from one spec make one decision on one real readout "
            "(docs/L2/agents/surface.md §4, §6)",
        )
        self.assertEqual(
            J.action_index(J.act(second, observation, mask)),
            by_second,
            "one state and one decision give one answer "
            "(docs/L2/agents/surface.md §1, §6)",
        )

    def test_join_agt_10_4_another_seed_explores_differently(self):
        """JOIN-AGT-10.4 one spec at another seed explores a decision differently.

        `docs/L3/agents/rule.md` §4: the exploration draw is keyed by the learner's own
        seed and the decision, so two learners at two seeds explore differently on one
        decision (`docs/L2/agents/surface.md` §6).  The comparison covers several
        decisions of two real hands, because a single decision's uniform draw may
        coincide.
        """
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        first = J.build_learner(self.spec(J.LEARNER_SEED))
        second = J.build_learner(self.spec(J.LEARNER_SEED_OTHER))
        decisions = []
        for deal in (J.DEAL_DECISION_A, J.DEAL_DECISION_B):
            decisions.extend(J.observations(deal, J.caller, encoder))
        self.assertGreaterEqual(
            len(decisions),
            4,
            "the comparison must cover several real decisions",
        )
        one = []
        other = []
        for observation, mask in decisions:
            one.append(J.action_index(J.act(first, observation, mask)))
            other.append(J.action_index(J.act(second, observation, mask)))
            self.assert_index_in(one[-1], mask)
            self.assert_index_in(other[-1], mask)
        self.assertNotEqual(
            one,
            other,
            "a learner at another seed must explore differently on the same decisions "
            "(docs/L3/agents/rule.md §4, docs/L2/agents/surface.md §6)",
        )


if __name__ == "__main__":
    unittest.main()
