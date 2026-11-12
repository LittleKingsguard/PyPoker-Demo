"""JOIN-AGT-4 — transitions and the reward's shape at the join.

`docs/L1/records.md` §4 fixes the transition record `agents.learn` consumes and
`docs/L1/records.md` §5 / ASM-12 fix the reward: the seat's net chip delta for the
completed hand, delivered at that seat's terminal decision and zero at every other
one, with no shaped term.  The reward is `engine`'s — this module adds none — so the
shape is a join: the episode record's rewards, the seat's payoff and a transition
batch built from real decisions must all agree.
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

REQUIRED_TRANSITION_KEYS = (
    "observation",
    "next_observation",
    "action",
    "reward",
    "terminal",
    "legal",
    "next_legal",
    # D-43 makes the episode boundary **required** of every transition (`records.md` §4,
    # `counterfactual.md` §2): one hand's transitions carry one number, and a batch that
    # omitted it would be refused by name before any arithmetic.  The conditional ninth
    # key, `counterfactual`, is not listed here: a hand `counterfactual.md` §4 refuses to
    # resolve carries none, so its presence is a property of the hand and not of the record
    # shape (D-43).
    "episode",
)


class TransitionsAtTheJoin(J.JoinCase):
    """Real transition records, and the unshaped reward they carry."""

    def test_join_agt_4_1_a_real_batch_is_learnable_and_counted(self):
        """JOIN-AGT-4.1 a batch of real transitions yields a finite td_error and a count.

        `docs/L2/agents/surface.md` §7: `learn` consumes a non-empty sequence of
        `records.md` §4's transitions and returns `td_error` and `transitions`;
        `docs/L1/records.md` §4: the observation and its successor come from
        `features.encode`, the action from the mask alignment and `legal` /
        `next_legal` are `features.legal_indices`' answers.  The batch is built from
        one seat of one played episode at an invented deal.
        """
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        record = J.play_hand(J.DEAL_REWARD_A, J.caller, J.caller)
        batch = J.seat_transitions(record, 0, encoder)
        self.assertTrue(
            batch,
            "the episode must report at least one decision for the seat "
            "(docs/L1/records.md §5)",
        )
        for transition in batch:
            missing = [
                key for key in REQUIRED_TRANSITION_KEYS if key not in transition
            ]
            self.assertFalse(
                missing,
                "a transition record carries the required keys of "
                "docs/L1/records.md §4; missing %r in %r" % (missing, transition),
            )
        for transition in batch[:-1]:
            self.assertEqual(
                float(transition["reward"]),
                0.0,
                "the reward is zero at every decision but the seat's terminal one "
                "(ASM-12, docs/L1/records.md §4)",
            )
            self.assertFalse(
                bool(transition["terminal"]),
                "only the seat's last decision is terminal in the batch",
            )
        self.assertTrue(
            bool(batch[-1]["terminal"]),
            "the seat's terminal decision is the last record of the batch",
        )
        learner = J.learner(
            "naive-stack", J.WIDTH_ONE, J.DEPTH_ONE, J.LEARNER_SEED
        )
        statistics = J.learn(learner, batch)
        self.assertTrue(
            J.finite(J.td_error(statistics)),
            "learn must report a finite mean absolute TD error "
            "(docs/L2/agents/surface.md §7)",
        )
        self.assertEqual(
            J.transitions_consumed(statistics),
            len(batch),
            "learn reports the transitions it consumed "
            "(docs/L2/agents/surface.md §7)",
        )

    def test_join_agt_4_2_the_reward_is_unshaped_and_equals_the_engine_payoff(self):
        """JOIN-AGT-4.2 the reward is unshaped and equals the engine's payoff.

        `docs/L1/records.md` §5 and ASM-12: rewards are zero except at most one
        non-zero reward per seat, at that seat's terminal decision, and the value is
        the hand's outcome.  The episode's decisions are replayed through
        `engine.apply_action` to a terminal handle, so `engine.payoffs` is the
        independent second reading of the same payoff.  Two invented deals.
        """
        for deal in (J.DEAL_REWARD_A, J.DEAL_REWARD_B):
            with self.subTest(deal=deal):
                record = J.play_hand(deal, J.caller, J.caller)
                decisions = J.episode_decisions(record)
                self.assertTrue(decisions)
                paid = J.episode_payoffs(record)
                self.assertEqual(
                    sorted(paid),
                    [0, 1],
                    "the episode's payoffs are one net delta per seat: %r" % (paid,),
                )
                last = {}
                for position, decision in enumerate(decisions):
                    last[J.decision_seat(decision)] = position
                for seat, position in last.items():
                    self.assertEqual(
                        float(J.decision_reward(decisions[position])),
                        paid[seat],
                        "seat %r's terminal decision must carry that seat's payoff "
                        "(ASM-12, docs/L1/records.md §5)" % (seat,),
                    )
                terminal = set(last.values())
                for position, decision in enumerate(decisions):
                    if position not in terminal:
                        self.assertEqual(
                            float(J.decision_reward(decision)),
                            0.0,
                            "a decision that is not the seat's terminal one carries "
                            "no reward (ASM-12): decision %d" % (position,),
                        )
                non_zero = {}
                for decision in decisions:
                    if float(J.decision_reward(decision)) != 0.0:
                        seat = J.decision_seat(decision)
                        non_zero[seat] = non_zero.get(seat, 0) + 1
                for seat, count in non_zero.items():
                    self.assertEqual(
                        count,
                        1,
                        "at most one non-zero reward per seat (ASM-12): seat %r "
                        "carries %d" % (seat, count),
                    )
                self.assertTrue(
                    non_zero,
                    "a played hand pays one seat or the other, so at least one "
                    "reward is non-zero (ASM-12)",
                )
                hand = J.new_hand(deal)
                for decision in decisions:
                    hand = J.apply_action(hand, J.decision_action(decision))
                self.assertTrue(
                    J.is_terminal(hand),
                    "the replayed decisions end the hand "
                    "(docs/L2/engine/surface.md §7)",
                )
                from_engine = J.payoffs(hand)
                self.assertEqual(
                    {int(seat): float(value) for seat, value in from_engine.items()},
                    paid,
                    "the episode's rewards are the engine's payoffs: replaying the "
                    "decisions must pay what the record reports "
                    "(docs/L2/engine/surface.md §9, ASM-12)",
                )
                self.assertAlmostEqual(
                    sum(paid.values()),
                    0.0,
                    places=9,
                    msg="the payoffs sum to zero (docs/L2/engine/surface.md §9)",
                )


if __name__ == "__main__":
    unittest.main()
