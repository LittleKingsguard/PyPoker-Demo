"""JOIN-AGT-2 — the decision path across the two consumed edges.

`docs/L2/agents/surface.md` §2, §6 and `docs/L2/features/surface.md` §6, §8, §9:
`engine.new_hand` → `engine.readout` → `features.encode` → `agents.act` →
`features.decode_action` → `engine.apply_action` is the whole of one training-time
decision, and each hop is another module's contract.  No single module can check the
chain: `agents` chooses an index, `features` says which indices are legal, and
`engine` is the only authority on whether the decoded descriptor may be applied.
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

# docs/L1/battery.md §3 FAM-16: a hand that has not ended after 200 decisions is a
# defect, so the walk below is bounded by that number.
DECISION_LIMIT = 200


class DecisionPath(J.JoinCase):
    """One real hand driven decision by decision through both edges."""

    def learner(self):
        return J.learner(
            "naive-stack", J.WIDTH_ONE, J.DEPTH_ONE, J.LEARNER_SEED
        )

    def test_join_agt_2_1_the_chosen_index_is_legal_and_its_descriptor_applies(self):
        """JOIN-AGT-2.1 every index is in the mask and every decoded action applies.

        `docs/L2/features/surface.md` §8 makes the mask `legal_indices`' answer for
        the very descriptors `engine.legal_actions` returned; `docs/L2/agents/
        surface.md` §2 and §6 require the chosen index to be a member of it;
        `docs/L2/features/surface.md` §9 and `docs/L2/engine/surface.md` §7 require
        the decoded descriptor to be applied without a refusal.  Driven for two
        invented deals.
        """
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        learner = self.learner()
        for deal in (J.DEAL_DECISION_A, J.DEAL_DECISION_B):
            with self.subTest(deal=deal):
                hand = J.new_hand(deal)
                steps = 0
                while not J.is_terminal(hand) and steps < DECISION_LIMIT:
                    facts = J.readout(hand)
                    legal = J.legal_actions(hand)
                    mask = J.legal_indices(legal)
                    observation = J.encode(encoder, facts)
                    index = J.action_index(J.act(learner, observation, mask))
                    self.assert_index_in(index, mask, "deal %r" % (deal,))
                    descriptor = J.decode_action(index)
                    self.assert_descriptor_in(
                        legal,
                        descriptor,
                        "deal %r: decode_action(index) must be an applied action"
                        % (deal,),
                    )
                    hand = J.apply_action(hand, descriptor)
                    steps += 1
                self.assertGreater(
                    steps,
                    0,
                    "a dealt hand offers at least one decision (engine/surface.md §6)",
                )

    def test_join_agt_2_2_the_driven_hand_terminates_and_pays_a_zero_sum(self):
        """JOIN-AGT-2.2 the encoded/decoded chain ends a hand whose payoffs sum to 0.

        `docs/L2/engine/surface.md` §7: applying the last action returns a handle for
        which `is_terminal` is true; §9: `payoffs` is one number per seat and the
        numbers sum to zero.  `docs/L2/agents/surface.md` §6 is the only source of
        the indices in between.  Driven for two more invented deals.
        """
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        learner = self.learner()
        for deal in (J.DEAL_DECISION_C, J.DEAL_POLICY_A):
            with self.subTest(deal=deal):
                hand = J.new_hand(deal)
                steps = 0
                while not J.is_terminal(hand) and steps < DECISION_LIMIT:
                    facts = J.readout(hand)
                    mask = J.legal_indices(J.legal_actions(hand))
                    index = J.action_index(
                        J.act(learner, J.encode(encoder, facts), mask)
                    )
                    hand = J.apply_action(hand, J.decode_action(index))
                    steps += 1
                self.assertTrue(
                    J.is_terminal(hand),
                    "the agents/features/engine chain must end the hand within %d "
                    "decisions (docs/L2/engine/surface.md §8)" % (DECISION_LIMIT,),
                )
                paid = J.payoffs(hand)
                self.assertEqual(
                    len(paid),
                    2,
                    "payoffs carries one net chip delta per seat "
                    "(docs/L2/engine/surface.md §9): %r" % (paid,),
                )
                self.assertAlmostEqual(
                    sum(float(value) for value in paid.values()),
                    0.0,
                    places=9,
                    msg="the two seats' payoffs must sum to zero "
                    "(docs/L2/engine/surface.md §9): %r" % (paid,),
                )


if __name__ == "__main__":
    unittest.main()
