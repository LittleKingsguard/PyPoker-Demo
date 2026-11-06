"""ENG-7 -- is the hand over, and what it paid.

``docs/L2/engine/surface.md`` §8, §9; ``docs/L3/engine/hand.md`` §5;
``docs/L2/engine/environment.md`` §1, §3; ``docs/L1/battery.md`` §3 FAM-16,
ASM-6, ASM-12.

A hand ends when a seat folds or at showdown; short stacks and the four-bet cap
bound it far below the 200 decisions the contract allows.  The payoffs are the
net chip delta per seat in *engine* seat order, two numbers that sum to zero --
which is why a fold of the first decision pays the button -1 and the big blind
+1, and not the other way round.
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


class ENG7Terminal(S.EngineCase):
    """`is_terminal` and `payoffs` on finished hands."""

    def test_eng7_1_is_terminal_is_a_real_bool_and_is_pure(self):
        """ENG-7.1 is_terminal returns a boolean (not a truthy object), is false on a
        fresh hand, true after the last action, and mutates nothing (surface.md §8,
        hand.md §5)."""
        hand = self.hand(S.SEED_A)
        answer = self.terminal(hand)
        self.assertIsInstance(answer, bool, "is_terminal returns a boolean, not a truthy object")
        self.assertFalse(answer, "a freshly dealt hand is not terminal")
        before = self.readout(hand)
        self.terminal(hand)
        self.assertEqual(self.readout(hand), before, "is_terminal mutates nothing (surface.md §8)")

        walk, finished = self.drive(S.SEED_B, S.always_call)
        self.assertTrue(len(walk) >= 2, "a hand takes at least two decisions")
        last = self.hand(S.SEED_B)
        for _facts, _legal, action in walk[:-1]:
            self.assertFalse(self.terminal(last), "the hand is live before its last action")
            last = self.step(last, action)
        final = self.step(last, walk[-1][2])
        self.assertIsInstance(self.terminal(final), bool, "is_terminal is still a boolean")
        self.assertTrue(
            self.terminal(final),
            "applying the last action of a hand returns a handle for which is_terminal is true "
            "(surface.md §7)",
        )
        self.assertFalse(self.terminal(last), "the handle before the last step is still live")
        self.assertTrue(self.terminal(finished), "the driven hand ended")

    def test_eng7_2_every_hand_ends_within_two_hundred_applied_actions(self):
        """ENG-7.2 for twelve invented seeds, playing to the end with always-check-or-call
        and separately with always-raise terminates in at most 200 applied actions
        (surface.md §8, ASM-6, guardrails G5)."""
        walk, finished = self.drive(S.SEED_A, S.always_call)
        self.assertTrue(self.terminal(finished), "every hand ends: seed 20260101, always-call")
        self.assertLessEqual(len(walk), S.MAX_DECISIONS,
                             "a hand ends within 200 applied actions (surface.md §8)")
        for seed in S.SEEDS:
            for policy, name in ((S.always_call, "always-call"), (S.always_raise, "always-raise")):
                with self.subTest(seed=seed, policy=name):
                    walk, finished = self.drive(seed, policy)
                    self.assertLessEqual(
                        len(walk), S.MAX_DECISIONS,
                        "a hand must end within %d applied actions (surface.md §8): seed %r "
                        "under %s took %d" % (S.MAX_DECISIONS, seed, name, len(walk)),
                    )
                    self.assertTrue(
                        self.terminal(finished),
                        "every hand ends: seed %r under %s (ASM-6)" % (seed, name),
                    )

    def test_eng7_3_payoffs_are_two_zero_sum_seat_values_and_are_deterministic(self):
        """ENG-7.3 payoffs of a finished hand is one number per seat, summing to zero,
        deterministic, and it refuses a running hand and a non-hand (surface.md §9,
        hand.md §5)."""
        finished = self.played_out(S.SEED_D, S.always_call)
        payoffs = self.payoffs(finished)
        self.assertTrue(S.is_mapping(payoffs), "payoffs returns a per-seat mapping")
        self.assertEqual(set(payoffs), {0, 1}, "the record is keyed by both seats: %r" % (payoffs,))
        values = list(S.numbers(payoffs))
        self.assertEqual(len(values), 2, "exactly one number per seat and nothing else numeric")
        self.assertEqual(sum(values), 0, "the payoffs are zero-sum: %r" % (payoffs,))
        self.assertEqual(self.payoffs(finished), payoffs,
                         "the payoffs are a function of the completed hand alone (surface.md §9)")

        running = self.hand(S.SEED_E)
        exc = self.refusal(S.ep("payoffs"), running)
        self.assert_mentions(exc, "hand", "over", "running")
        for bad in (None, 7, self.readout(running)):
            with self.subTest(argument=type(bad).__name__):
                exc = self.refusal(S.ep("payoffs"), bad)
                self.assert_mentions(exc, "hand")

    def test_eng7_4_a_fold_of_the_first_decision_pays_the_button_minus_one(self):
        """ENG-7.4 the button folding pre-flop pays {0: -1, 1: 1}: the payoffs are net
        deltas in engine seat order (hand.md §3, §5, ASM-12)."""
        folded = self.step(self.hand(S.SEED_F), "fold")
        self.assertTrue(self.terminal(folded), "a fold ends the hand")
        payoffs = self.payoffs(folded)
        self.assertEqual(
            dict(payoffs), {0: -1, 1: 1},
            "seat 0 posted the small blind of 1 and folded, so it loses exactly one chip and "
            "seat 1 wins exactly one (hand.md §3: engine seat 0 is pokerkit player 1): %r"
            % (payoffs,),
        )


if __name__ == "__main__":
    unittest.main()
