"""ENG-8 -- `play_hand`: one whole episode as a record.

``docs/L2/engine/surface.md`` §10; ``docs/L2/engine/environment.md`` §3;
``docs/L3/engine/episode.md`` §1-§5; ``docs/L1/battery.md`` §3 FAM-4, FAM-16,
ASM-12.

The record carries the seed it was called with, the ordered decisions and the
payoffs; every decision carries its own seat, the whole eleven-fact readout taken
before the action, the legal descriptors, the action applied and a reward that is
zero except at that seat's last decision, where it is the seat's net chip delta.
The record is the hand: driving the same seed by hand with the recorded actions
reproduces it.
"""

import os
import sys
import unittest

try:  # discovered as part of a tests.engine package
    from . import _engine_support as S
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _engine_support as S  # noqa: E402

DECISION_KEYS = ("seat", "readout", "legal", "action", "reward")


class ENG8Episode(S.EngineCase):
    """The episode record, its decisions, its rewards, and the policy protocol."""

    def test_eng8_1_the_record_carries_its_seed_decisions_and_payoffs(self):
        """ENG-8.1 the record carries seed, decisions and payoffs; the seed is the seed it
        was called with, the decisions are non-empty and at most 200, and the payoffs sum
        to zero (surface.md §10, environment.md §3, episode.md §3)."""
        record = self.episode(S.SEED_A, S.always_call, S.always_call)
        self.assertTrue(S.is_mapping(record), "play_hand returns a record mapping")
        self.assertEqual(record["seed"], S.SEED_A,
                         "the record carries the seed the call was made with, unchanged")
        self.assertIn("decisions", record, "the record carries its decisions")
        self.assertIn("payoffs", record, "the record carries its payoffs")
        for seed in (S.SEED_A, S.SEED_E):
            with self.subTest(seed=seed):
                record = self.episode(seed, S.always_call, S.always_call)
                for key in ("seed", "decisions", "payoffs"):
                    self.assertIn(key, record, "the record carries its %r (environment.md §3)" % key)
                self.assertEqual(record["seed"], seed,
                                 "the record carries the seed the call was made with, unchanged")
                decisions = record["decisions"]
                self.assertGreaterEqual(len(decisions), 1, "a hand takes at least one decision")
                self.assertLessEqual(len(decisions), S.MAX_DECISIONS,
                                     "an episode holds at most 200 decisions (surface.md §8)")
                payoffs = record["payoffs"]
                self.assertTrue(S.is_mapping(payoffs), "the record carries the payoffs mapping")
                self.assertEqual(sum(S.numbers(payoffs)), 0, "the episode's payoffs are zero-sum")

    def test_eng8_2_every_decision_carries_its_five_facts(self):
        """ENG-8.2 each decision carries seat, readout, legal, action and reward; its
        readout holds the eleven facts, its action is a member of its legal descriptors, and
        its seat is the readout's seat (environment.md §3, episode.md §3, ASM-30)."""
        record = self.episode(S.SEED_B, S.always_raise, S.always_call)
        for index, decision in enumerate(record["decisions"]):
            with self.subTest(decision=index):
                self.assertTrue(S.is_mapping(decision), "a decision is a record")
                for key in DECISION_KEYS:
                    self.assertIn(key, decision,
                                  "every decision carries its %r (records.md §5)" % key)
                facts = decision["readout"]
                self.assertEqual(set(facts), set(S.FACTS),
                                 "the decision's readout is the whole eleven-fact mapping of that "
                                 "decision (environment.md §3): %r" % (sorted(facts),))
                self.assertEqual(tuple(decision["seat"]), tuple(facts["seat"]),
                                 "a decision's seat is its readout's seat fact")
                self.assertEqual(list(decision["legal"]), list(facts["legal"]),
                                 "a decision's legal is that decision's descriptor list")
                self.assertIn(decision["action"], list(decision["legal"]),
                              "the action a decision records is a member of its own legal "
                              "descriptors (episode.md §3): %r" % (decision["action"],))
                self.assertIn(decision["action"], S.ACTIONS,
                              "the recorded action is one of the three declared descriptors")

    def test_eng8_3_the_reward_is_the_hands_outcome_at_each_seats_last_decision(self):
        """ENG-8.3 the non-zero rewards are the hand's outcome: an episode whose first
        decision is a fold pays {0: -1, 1: 1} and carries exactly one non-zero reward,
        seat 0's, equal to its payoff and at its only decision; in two further episodes
        that certainly end in a fold the multiset of non-zero rewards equals the multiset
        of non-zero payoffs, every non-zero reward sitting at its seat's last decision
        (episode.md §3, ASM-12, guardrails G9)."""
        # (a) a known outcome: the button folds the first decision, so it loses its small
        # blind and the big blind wins it; only the button has a decision.
        record = self.episode(S.SEED_C, S.always_fold, S.always_fold)
        decisions = record["decisions"]
        payoffs = record["payoffs"]
        self.assertEqual(
            dict(payoffs), {0: -1, 1: 1},
            "a pre-flop fold of the button pays -1 and +1 in engine seat order (hand.md §5): %r"
            % (payoffs,),
        )
        non_zero = [(index, decision) for index, decision in enumerate(decisions)
                    if decision["reward"] != 0]
        self.assertEqual(
            len(non_zero), 1,
            "the record carries exactly one non-zero reward -- the folded seat's, because the "
            "big blind never acted and so carries no decision (episode.md §3): %r"
            % (decisions,),
        )
        index, decision = non_zero[0]
        rewarded_seat = decision["seat"][0]
        last_of_seat = {}
        for position, entry in enumerate(decisions):
            last_of_seat[entry["seat"][0]] = position
        self.assertNotEqual(
            payoffs[rewarded_seat], 0,
            "the rewarded decision's seat is one whose payoff is non-zero: %r" % (payoffs,),
        )
        self.assertEqual(
            decision["reward"], payoffs[rewarded_seat],
            "the terminal reward equals that seat's net chip delta, never a shaped per-decision "
            "term (ASM-12, guardrails G9): %r, payoffs %r" % (decision["reward"], payoffs),
        )
        self.assertEqual(
            index, last_of_seat[rewarded_seat],
            "the terminal reward sits at that seat's last decision of the record "
            "(episode.md §3, guardrails G9)",
        )

        # (b) the general property, stated without a guard: each policy pair below certainly
        # ends in a fold, so some seat is certainly paid and the rewards cannot all be zero.
        def bet_a_free_postflop(readout, legal):
            if readout["street"] != "preflop" and readout["to_call"] == 0:
                return "raise"
            return "check-call"

        for label, seed, seat0_policy, seat1_policy in (
            ("raise-then-fold", S.SEED_B, S.always_raise, S.always_fold),
            ("bet-then-fold", S.SEED_D, bet_a_free_postflop, S.always_fold),
        ):
            with self.subTest(policy=label):
                record = self.episode(seed, seat0_policy, seat1_policy)
                decisions = record["decisions"]
                payoffs = record["payoffs"]
                last_of_seat = {}
                for position, entry in enumerate(decisions):
                    last_of_seat[entry["seat"][0]] = position
                self.assertEqual(
                    set(last_of_seat), {0, 1},
                    "both seats act in this episode, so both carry a decision: %r" % (decisions,),
                )
                rewards = sorted(d["reward"] for d in decisions if d["reward"] != 0)
                paid = sorted(value for value in S.numbers(payoffs) if value != 0)
                self.assertTrue(
                    rewards,
                    "a hand that ends in a fold pays a non-zero amount, so the record carries a "
                    "non-zero reward (episode.md §3, ASM-12): payoffs %r" % (payoffs,),
                )
                self.assertEqual(
                    rewards, paid,
                    "the multiset of non-zero rewards is the multiset of non-zero payoffs "
                    "(episode.md §3, ASM-12): rewards %r, payoffs %r" % (rewards, payoffs),
                )
                for position, entry in enumerate(decisions):
                    if entry["reward"] == 0:
                        continue
                    self.assertEqual(
                        position, last_of_seat[entry["seat"][0]],
                        "every decision with a non-zero reward is its seat's last decision "
                        "(episode.md §3, guardrails G9): %r" % (decisions,),
                    )

    def test_eng8_4_the_record_replays_as_the_same_hand(self):
        """ENG-8.4 driving new_hand(seed) and applying the recorded actions in order gives
        the same readouts at every decision, the same history and the same payoffs
        (episode.md §5, surface.md §10)."""
        seed = S.SEED_D
        record = self.episode(seed, S.always_raise, S.always_raise)
        hand = self.hand(seed)
        applied = 0
        for index, decision in enumerate(record["decisions"]):
            self.assertEqual(
                self.readout(hand), decision["readout"],
                "decision %d of the episode is the decision the same seed deals and the same "
                "actions reach (episode.md §5)" % index,
            )
            hand = self.step(hand, decision["action"])
            applied += 1
        self.assertEqual(
            applied, len(record["decisions"]),
            "the record holds one entry per applied action of that hand (episode.md §2)",
        )
        self.assertTrue(self.terminal(hand), "the replayed hand reaches its end")
        self.assertEqual(
            dict(self.payoffs(hand)), dict(record["payoffs"]),
            "the replayed hand pays what the episode recorded (episode.md §5)",
        )

    def test_eng8_5_one_seed_and_one_policy_pair_give_one_record(self):
        """ENG-8.5 two identical calls give equal records and two different seeds give
        different ones (surface.md §10, episode.md §4, FAM-4)."""
        first = self.episode(S.SEED_A, S.always_call, S.always_call)
        second = self.episode(S.SEED_A, S.always_call, S.always_call)
        self.assertEqual(first, second,
                         "one seed and one pair of policies give one record (surface.md §10)")
        other = self.episode(S.SEED_F, S.always_call, S.always_call)
        self.assertNotEqual(
            first["decisions"], other["decisions"],
            "a different seed deals a different hand, so its decisions differ (surface.md §10)",
        )

    def test_eng8_6_the_policy_protocol_is_a_callable_taking_the_readout_and_the_legal_set(self):
        """ENG-8.6 a policy is called with (readout, legal) and its answer is applied; a
        recording policy sees an eleven-fact mapping and a sequence holding its answer, and
        first/last/lambda policies all work (e2e-surface.md §2, episode.md §4, ASM-30)."""
        seen = []

        def recording(readout, legal):
            seen.append((readout, legal))
            return legal[-1]

        record = self.episode(S.SEED_E, recording, recording)
        self.assertTrue(seen, "play_hand calls the acting seat's policy (surface.md §10)")
        for readout, legal in seen:
            self.assertTrue(S.is_mapping(readout),
                            "the policy's first argument is the readout mapping (e2e-surface §2)")
            self.assertEqual(set(readout), set(S.FACTS),
                             "the policy sees the whole eleven-fact readout: %r" % (sorted(readout),))
            self.assertIsNotNone(legal, "the policy's second argument is the legal descriptors")
            self.assertTrue(list(legal), "the legal sequence the policy sees is never empty")
        self.assertTrue(
            any(record["decisions"][i]["action"] == record["decisions"][i]["legal"][-1]
                for i in range(len(record["decisions"]))),
            "the engine applies the descriptor the policy returned (surface.md §10)",
        )
        for label, policy in (
            ("first", S.first_legal),
            ("last", S.last_legal),
            ("lambda", lambda readout, legal: legal[-1] if len(legal) > 1 else legal[0]),
        ):
            with self.subTest(policy=label):
                played = self.episode(S.SEED_E, policy, policy)
                self.assertTrue(played["decisions"], "a %s policy drives a whole hand" % (label,))

    def test_eng8_7_a_fold_of_the_first_decision_records_one_decision(self):
        """ENG-8.7 when the button folds pre-flop the big blind has no decision in the
        record, and the payoffs are {0: -1, 1: 1} (environment.md §3, episode.md §3)."""
        record = self.episode(S.SEED_B, S.always_fold, S.always_fold)
        decisions = record["decisions"]
        self.assertEqual(len(decisions), 1,
                         "the big blind never acts when the button folds pre-flop, so it carries "
                         "no decision (environment.md §3): %r" % (decisions,))
        self.assertEqual(decisions[0]["seat"][0], 0, "the folded seat is the button")
        self.assertEqual(decisions[0]["action"], "fold", "the decision records the fold")
        self.assertEqual(dict(record["payoffs"]), {0: -1, 1: 1},
                         "a pre-flop fold of the button pays -1 and +1 in engine seat order "
                         "(hand.md §5)")
        self.assertEqual(decisions[0]["reward"], -1,
                         "the button's only decision carries its net chip delta (episode.md §3)")


if __name__ == "__main__":
    unittest.main()
