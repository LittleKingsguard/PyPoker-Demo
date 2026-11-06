"""records.md §5, ASM-12 — one whole episode, and what its record must carry.

`docs/L2/engine/surface.md` §10 and `environment.md` §3, `records.md` §5.  A record
carries the seed unchanged, the ordered decisions — each with its own seat, the whole
ten-fact readout for that decision, its legal descriptors, the descriptor the policy
returned and the applied action's reward — and the payoffs of the completed hand,
summing to zero.  The policies are called as `policy(readout, legal_actions)` and
their answer is what is applied; the reward is the hand's outcome at a seat's last
decision and zero at every other; a seat that never acted carries no decision; and
the record names no hand handle.
"""

import os
import sys
import unittest

try:
    from . import _support as S
except ImportError:
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _support as S  # noqa: E402


class Episode(S.EngineCase):
    """The episode record, decision by decision."""

    def test_episode_01_the_record_carries_the_three_required_keys(self):
        """§5 the record carries `seed`, `decisions` and `payoffs`."""
        episode = self.play_hand(
            S.SEED_A, S.PolicyProbe(S.choose_raise, name="seat 0"),
            S.PolicyProbe(S.choose_call, name="seat 1"),
        )
        self.assertTrue(S.is_mapping(episode), "play_hand returns one mapping (records.md §5)")
        for fact in S.EPISODE_FACTS:
            S.required(episode, "the episode record of play_hand", fact)
        decisions = S.decision_list(episode)
        self.assertTrue(
            decisions,
            "an episode of a hand with at least one decision records it (records.md §5, "
            "environment.md §1)",
        )
        S.seat_keyed(
            S.required(episode, "the episode record of play_hand", "payoffs"),
            "the episode's payoffs",
        )

    def test_episode_02_every_decision_carries_its_five_facts(self):
        """§5 each decision carries seat, readout, legal, action and reward."""
        episode = self.play_hand(
            S.SEED_B, S.PolicyProbe(S.choose_raise, name="seat 0"),
            S.PolicyProbe(S.choose_call, name="seat 1"),
        )
        decisions = S.decision_list(episode)
        self.assertTrue(
            decisions, "an episode of this game records at least one decision (records.md §5)")
        for position, decision in enumerate(decisions):
            for fact in S.DECISION_FACTS:
                S.decision_fact(decision, fact)
            readout = S.decision_fact(decision, "readout")
            self.assertEqual(
                set(readout), set(S.READOUT_FACTS),
                "the decision's readout is the whole ten-fact mapping of that decision "
                "(environment.md §3, D-3): decision %d carried %r"
                % (position, sorted(str(key) for key in readout)),
            )
            self.assertEqual(
                len(readout["history"]), position,
                "the decisions are ordered in the order they were taken (records.md §5): "
                "decision %d read a history of %d actions" % (position, len(readout["history"])),
            )
            index, _ = S.seat_fact(S.decision_fact(decision, "seat"))
            readout_index, _ = S.seat_fact(readout["seat"])
            self.assertEqual(
                index, readout_index,
                "a decision's seat is that decision's own acting seat, in the shape of the "
                "seat fact (environment.md §3): decision %d said %r against %r"
                % (position, index, readout_index),
            )
            self.assertTrue(
                S.is_number(S.decision_fact(decision, "reward")),
                "a reward is a number (records.md §5): decision %d read %r"
                % (position, S.decision_fact(decision, "reward")),
            )

    def test_episode_03_the_policies_are_called_with_the_readout_and_the_legal_descriptors(self):
        """§10 the engine asks a policy with (readout, legal) and applies its answer."""
        seed = S.SEED_C
        seat0 = S.PolicyProbe(S.choose_raise, name="seat 0")
        seat1 = S.PolicyProbe(S.choose_call, name="seat 1")
        episode = self.play_hand(seed, seat0, seat1)
        decisions = S.decision_list(episode)
        taken = {0: 0, 1: 0}
        for position, decision in enumerate(decisions):
            index, _ = S.seat_fact(S.decision_fact(decision, "seat"))
            probe = seat0 if index == 0 else seat1
            self.assertLess(
                taken[index], len(probe.calls),
                "decision %d of seat %d has no matching policy call, so the engine did not "
                "ask that seat's policy for it (surface.md §10)" % (position, index),
            )
            call = probe.calls[taken[index]]
            taken[index] += 1
            self.assertEqual(
                S.canon(S.decision_fact(decision, "readout")), S.canon(call["readout"]),
                "the decision's readout is the one its policy was called with "
                "(environment.md §3): decision %d differed" % (position,),
            )
            self.assertTrue(
                S.descriptors_equal(S.decision_fact(decision, "legal"), call["legal"]),
                "the decision's legal list is the list its policy was called with "
                "(environment.md §3): decision %d differed" % (position,),
            )
            self.assertTrue(
                S.same_descriptor(
                    S.decision_fact(decision, "action"), call["action"]
                ),
                "the descriptor the record carries is the one the policy returned and the "
                "engine applied (surface.md §10): decision %d recorded %r against %r"
                % (position, S.decision_fact(decision, "action"), call["action"]),
            )
        self.assertEqual(
            taken[0], len(seat0.calls),
            "the engine asks the seat's policy once per decision it takes (surface.md §10)",
        )
        self.assertEqual(taken[1], len(seat1.calls), "the engine asks one policy per decision")
        self.assertGreaterEqual(
            taken[0] + taken[1], 2, "an episode played by these policies has both seats acting"
        )

    def test_episode_04_the_decisions_are_ordered_and_one_step_apart(self):
        """§10 the decisions are the hand's steps, in order, one action each."""
        seed = S.SEED_D
        seat0 = S.PolicyProbe(S.choose_raise, name="seat 0")
        seat1 = S.PolicyProbe(S.choose_call, name="seat 1")
        episode = self.play_hand(seed, seat0, seat1)
        decisions = S.decision_list(episode)
        hand = self.new_hand(seed)
        for position, decision in enumerate(decisions):
            readout = self.readout(hand)
            self.assertEqual(
                S.canon(readout["history"]),
                S.canon(S.decision_fact(decision, "readout")["history"]),
                "decision %d records the history the hand had when it was taken "
                "(records.md §5, surface.md §7)" % (position,),
            )
            hand = self.apply_action(hand, S.decision_fact(decision, "action"))
        self.assertTrue(
            self.is_terminal(hand),
            "the episode's decisions play that seed's hand to its end (surface.md §10)",
        )

    def test_episode_05_its_payoffs_are_the_completed_hand_s_payoffs(self):
        """§10 the record's payoffs are the payoffs of that completed hand."""
        seed = S.SEED_E
        seat0 = S.PolicyProbe(S.choose_raise, name="seat 0")
        seat1 = S.PolicyProbe(S.choose_call, name="seat 1")
        episode = self.play_hand(seed, seat0, seat1)
        hand = self.new_hand(seed)
        for decision in S.decision_list(episode):
            hand = self.apply_action(hand, S.decision_fact(decision, "action"))
        self.assertTrue(self.is_terminal(hand), "the replayed hand is over (surface.md §10)")
        recorded = S.seat_keyed(
            S.required(episode, "the episode record of play_hand", "payoffs"),
            "the episode's payoffs",
        )
        returned = S.seat_keyed(
            self.payoffs(hand), "payoffs of the hand the episode played"
        )
        self.assertEqual(
            S.canon(recorded), S.canon(returned),
            "the episode's payoffs are the same record payoffs returns for that completed "
            "hand (records.md §5, environment.md §3): %r against %r"
            % (recorded, returned),
        )
        self.assertAlmostEqual(
            float(sum(recorded.values())), 0.0, places=9,
            msg="an episode's payoffs sum to zero (records.md §5, ASM-12): %r" % (recorded,),
        )

    def test_episode_06_rewards_are_the_outcome_at_each_seat_s_last_decision(self):
        """§10 reward is the seat's net delta at its last decision and zero elsewhere."""
        seed = S.SEED_F
        episode = self.play_hand(
            seed, S.PolicyProbe(S.choose_raise, name="seat 0"),
            S.PolicyProbe(S.choose_call, name="seat 1"),
        )
        decisions = S.decision_list(episode)
        self.assertTrue(
            decisions,
            "an episode of this game records the decisions its seats took (records.md §5)",
        )
        payoffs = S.seat_keyed(
            S.required(episode, "the episode record of play_hand", "payoffs"),
            "the episode's payoffs",
        )
        for index in (0, 1):
            owned = [
                (position, float(S.decision_fact(decision, "reward")))
                for position, decision in enumerate(decisions)
                if S.seat_fact(S.decision_fact(decision, "seat"))[0] == index
            ]
            if not owned:
                continue
            non_zero = [(position, reward) for position, reward in owned if reward != 0.0]
            self.assertLessEqual(
                len(non_zero), 1,
                "a seat carries at most one non-zero reward (records.md §5, ASM-12): "
                "seat %r carried %r" % (index, non_zero),
            )
            self.assertAlmostEqual(
                float(sum(reward for _, reward in owned)), float(payoffs[index]),
                places=9,
                msg="a seat's rewards are the hand's net chip delta and nothing else "
                    "(ASM-12): seat %r carried %r against a payoff of %r"
                    % (index, owned, payoffs[index]),
            )
            if non_zero:
                self.assertEqual(
                    non_zero[0][0], owned[-1][0],
                    "the non-zero reward sits at that seat's last decision (records.md §5, "
                    "ASM-12): seat %r carried %r and last acted at decision %d"
                    % (index, non_zero, owned[-1][0]),
                )

    def test_episode_07_a_seat_that_never_acted_carries_no_decision(self):
        """§3 a seat that never acted carries no decision and therefore no reward."""
        seed = S.SEED_G
        seat0 = S.PolicyProbe(S.choose_fold, name="seat 0")
        seat1 = S.PolicyProbe(S.choose_call, name="seat 1")
        episode = self.play_hand(seed, seat0, seat1)
        decisions = S.decision_list(episode)
        self.assertGreaterEqual(
            len(decisions), 1,
            "the button acts first preflop and folds, so the hand records one decision "
            "(environment.md §1)",
        )
        for position, decision in enumerate(decisions):
            index, _ = S.seat_fact(S.decision_fact(decision, "seat"))
            self.assertEqual(
                index, 0,
                "the big blind never acts when the button folds preflop, so no decision "
                "belongs to it (environment.md §3): decision %d named seat %r"
                % (position, index),
            )
        self.assertEqual(
            seat1.calls, [],
            "a seat that never acts is never asked for a decision (environment.md §3)",
        )
        payoffs = S.seat_keyed(
            S.required(episode, "the episode record of play_hand", "payoffs"),
            "the episode's payoffs",
        )
        self.assertAlmostEqual(
            float(payoffs[0]), -float(S.SMALL_BLIND), places=9,
            msg="the button folds after posting the small blind, so it loses it "
                "(environment.md §1): %r" % (payoffs,),
        )
        self.assertAlmostEqual(
            float(payoffs[1]), float(S.SMALL_BLIND), places=9,
            msg="the big blind wins the small blind and the two sum to zero (ASM-12): %r"
                % (payoffs,),
        )

    def test_episode_08_the_seed_is_unchanged_and_the_decisions_are_recorded(self):
        """§10 the record's seed is the seed the call was made with, unchanged."""
        for seed in (S.SEED_H, S.SEED_I):
            episode = self.play_hand(
                seed, S.PolicyProbe(S.choose_raise, name="seat 0"),
                S.PolicyProbe(S.choose_call, name="seat 1"),
            )
            recorded = S.required(episode, "the episode record of play_hand", "seed")
            self.assertEqual(
                recorded, seed,
                "the record carries the seed the call was made with, unchanged "
                "(records.md §5): %r for seed %r" % (recorded, seed),
            )
            self.assertTrue(
                S.decision_list(episode),
                "one seed deals one hand, so its episode records the decisions taken "
                "(records.md §5)",
            )

    def test_episode_09_the_record_exposes_no_hand_handle(self):
        """§10 the record names no hand handle, because nothing below an entry point is surface."""
        episode = self.play_hand(
            S.SEED_J, S.PolicyProbe(S.choose_raise, name="seat 0"),
            S.PolicyProbe(S.choose_call, name="seat 1"),
        )
        for value in S.leaves(episode):
            if isinstance(value, (str, bytes, int, float, bool, type(None))):
                continue
            self.assert_refused(
                lambda value=value: self.is_terminal(value),
                "is_terminal on a value the episode record exposes",
                ("hand", "handle"),
            )
            self.assert_refused(
                lambda value=value: self.readout(value),
                "readout on a value the episode record exposes",
                ("hand", "handle", "over", "terminal"),
            )

    def test_episode_10_a_bad_policy_is_refused_or_its_error_propagates(self):
        """§10 a non-callable policy and an illegal answer are refused; an error propagates."""
        seed = S.SEED_K
        good = S.PolicyProbe(name="the battery's other seat")
        for bad in (None, 7, "a policy", {}, object()):
            self.assert_refused(
                lambda bad=bad: self.play_hand(seed, bad, good),
                "play_hand with a seat-0 policy that is not callable (%r)" % (bad,),
                ("policy", "callable"),
            )
            self.assert_refused(
                lambda bad=bad: self.play_hand(seed, good, bad),
                "play_hand with a seat-1 policy that is not callable (%r)" % (bad,),
                ("policy", "callable"),
            )
        fold = self.fold_descriptor(self.legal_actions(self.new_hand(seed)))
        self.assert_refused(
            lambda: self.play_hand(seed, S.FoldWhenFree(fold), good),
            "play_hand with a policy that answers a free decision with a fold",
            ("legal", "action", "descriptor"),
        )
        self.assert_refused(
            lambda: self.play_hand(seed, S.IllegalAnswer(), good),
            "play_hand with a policy whose answer names no action of the decision",
            ("legal", "action", "descriptor"),
        )
        try:
            self.play_hand(seed, S.ExplodingPolicy(), good)
        except S.PolicyFailure as exc:
            self.assertIn(
                "refuses to choose", str(exc),
                "the policy's own exception propagates unchanged (surface.md §10)",
            )
        except Exception as exc:
            self.fail(
                "play_hand must not catch a policy's own exception and turn it into an "
                "action (surface.md §10); it raised %s: %s"
                % (type(exc).__name__, exc)
            )
        else:
            self.fail(
                "play_hand returned a record for a policy that raised (surface.md §10)"
            )


if __name__ == "__main__":
    unittest.main()
