"""JOIN-AGT-3 — `as_policy` exercised by `engine.play_hand`.

`docs/L1/e2e-surface.md` §2 fixes the policy protocol: a callable taking
`(readout, legal_actions)` and returning one of those descriptors.  `engine` calls
policies and never imports one; `agents.as_policy` returns one.  This family judges
that handshake — a whole episode completes with a learner in one seat and each of the
three baselines in the other, the record carries the chosen actions, the payoffs sum
to zero, and every descriptor a policy answered was one it had been handed
(`docs/L2/agents/surface.md` §10, §12; `docs/L2/engine/surface.md` §10).
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

BASELINE_NAMES = ("random", "always-call", "oracle")


class PolicyProtocol(J.JoinCase):
    """The learner's policy and the baselines' policies inside a real episode."""

    def learner(self):
        return J.learner(
            "naive-stack", J.WIDTH_ONE, J.DEPTH_TWO, J.LEARNER_SEED
        )

    def test_join_agt_3_1_a_whole_episode_completes_and_every_answer_was_offered(self):
        """JOIN-AGT-3.1 a learner seat plus each baseline seat plays one full episode.

        `docs/L2/engine/surface.md` §10 calls the acting seat's policy with the
        readout and the legal descriptors and applies what comes back; `docs/L1/
        records.md` §5 fixes the episode record's decisions (`seat`, `readout`,
        `legal`, `action`, `reward`) and its payoffs.  The recording wrappers are
        policies of the same protocol, so the assertion is made at the join and not
        on a module's inside.  One invented deal per baseline.
        """
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        learner = self.learner()
        for name in BASELINE_NAMES:
            with self.subTest(baseline=name):
                learner_policy = J.recording(
                    J.as_policy(learner, encoder, J.LEARNER_SEED)
                )
                opponent = J.recording(J.build_baseline(name, J.BASELINE_SEED))
                record = J.play_hand(J.DEAL_POLICY_A, learner_policy, opponent)
                decisions = J.episode_decisions(record)
                self.assertTrue(
                    decisions,
                    "a played episode records at least one decision "
                    "(docs/L1/records.md §5)",
                )
                self.assertEqual(
                    J.episode_seed(record),
                    J.DEAL_POLICY_A,
                    "the episode record carries the seed it was played at "
                    "(docs/L1/records.md §5)",
                )
                for decision in decisions:
                    legal = J.decision_legal(decision)
                    self.assert_descriptor_in(
                        legal,
                        J.decision_action(decision),
                        "episode decision vs %r" % (name,),
                    )
                for role, policy in (("learned", learner_policy),
                                     (name, opponent)):
                    self.assertTrue(
                        policy.calls,
                        "the %s policy must be called by engine.play_hand "
                        "(docs/L2/engine/surface.md §10)" % (role,),
                    )
                    for _facts, legal, chosen in policy.calls:
                        self.assert_descriptor_in(
                            legal,
                            chosen,
                            "the %s policy at the join" % (role,),
                        )
                paid = J.episode_payoffs(record)
                self.assertEqual(
                    sorted(paid),
                    [0, 1],
                    "the episode's payoffs are one net delta per seat "
                    "(docs/L1/records.md §5): %r" % (paid,),
                )
                self.assertAlmostEqual(
                    sum(paid.values()),
                    0.0,
                    places=9,
                    msg="the episode's payoffs must sum to zero "
                    "(docs/L1/records.md §5): %r" % (paid,),
                )

    def test_join_agt_3_2_at_its_own_seed_the_policy_decides_as_act_does(self):
        """JOIN-AGT-3.2 as_policy at the learner's seed answers act's decision.

        `docs/L2/agents/surface.md` §10: the policy applies the learner's own decision
        rule to the decision its arguments name, so at the learner's own seed it
        decides exactly as `act` decides on the same decision.  Compared over two
        invented deals through `features.encode`, `features.legal_indices` and
        `features.decode_action`, which are the only declared translators.
        """
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        learner = self.learner()
        policy = J.as_policy(learner, encoder, J.LEARNER_SEED)
        decisions = 0
        for deal in (J.DEAL_POLICY_B, J.DEAL_DECISION_A):
            with self.subTest(deal=deal):
                hand = J.new_hand(deal)
                steps = 0
                while not J.is_terminal(hand) and steps < 200:
                    facts = J.readout(hand)
                    legal = J.legal_actions(hand)
                    mask = J.legal_indices(legal)
                    by_act = J.action_index(
                        J.act(learner, J.encode(encoder, facts), mask)
                    )
                    chosen = policy(facts, legal)
                    self.assert_descriptor_in(legal, chosen, "deal %r" % (deal,))
                    self.assertEqual(
                        J.descriptor_index(legal, chosen),
                        by_act,
                        "at the learner's own seed the policy and act are one "
                        "decision boundary (docs/L2/agents/surface.md §10)",
                    )
                    decisions += 1
                    hand = J.apply_action(hand, chosen)
                    steps += 1
                self.assertGreater(
                    steps, 0, "a dealt hand offers at least one decision"
                )
        self.assertGreaterEqual(
            decisions,
            2,
            "the comparison must cover at least two decisions",
        )


if __name__ == "__main__":
    unittest.main()
