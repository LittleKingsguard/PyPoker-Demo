"""FAM-16, ASM-12 — the hand ends, and the end is paid.

`docs/L2/engine/surface.md` §8–§9, `environment.md` §1 (ended, paid), ASM-6, ASM-12.
A fresh hand is not terminal; every hand of this short-stack game ends within 200
decisions, because short stacks and the raise cap bound it; a terminal hand has no
readout and no legal action; `payoffs` of a running hand is refused; and the payoffs
of a completed hand are keyed by seat, carry exactly one number per seat, nothing
else numeric, and sum to zero — a zero payoff being a legal value, since ties and
splits are common at these stacks.
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


class FAM16Outcome(S.EngineCase):
    """Termination and payoff."""

    def test_fam16_30_a_fresh_hand_is_not_terminal_and_every_hand_ends(self):
        """FAM-16.30 every hand of thirteen invented seeds ends within 200 decisions."""
        for seed in S.SEED_DISTINCT:
            hand = self.new_hand(seed)
            self.assertFalse(
                self.is_terminal(hand),
                "a freshly dealt hand is not terminal (surface.md §8); seed %r" % (seed,),
            )
            steps, finished = self.walk(seed, limit=S.DECISION_BOUND)
            self.assertLess(
                len(steps), S.DECISION_BOUND,
                "short stacks and the raise cap bound a hand, so one that has not ended "
                "after 200 decisions is a defect (surface.md §8, ASM-6); seed %r was "
                "still running" % (seed,),
            )
            self.assertTrue(
                self.is_terminal(finished),
                "the walk reached a completed hand (surface.md §8); seed %r" % (seed,),
            )
            self.assertGreaterEqual(
                len(steps), 1, "a hand has at least one decision (environment.md §1)"
            )

    def test_fam16_31_a_terminal_hand_has_no_readout_and_no_legal_action(self):
        """FAM-16.31 a hand with no acting seat has no readout and nothing legal (§5, §6)."""
        finished = self.finished_hand(S.SEED_G)
        self.assertTrue(self.is_terminal(finished), "the hand is over (surface.md §8)")
        self.assert_refused(
            lambda: self.readout(finished),
            "readout of a hand that is over",
            ("over", "terminal", "finished", "ended", "acting"),
        )
        self.assert_refused(
            lambda: self.legal_actions(finished),
            "legal_actions of a hand that is over",
            ("over", "terminal", "finished", "ended", "acting"),
        )
        fold = self.fold_descriptor(self.legal_actions(self.new_hand(S.SEED_G)))
        self.assert_refused(
            lambda: self.apply_action(finished, fold),
            "apply_action on a hand that is over",
            ("over", "terminal", "finished", "ended"),
        )

    def test_fam16_32_payoffs_of_a_running_hand_is_refused(self):
        """FAM-16.32 a running hand has paid nothing, so payoffs refuses it (§9)."""
        hand = self.new_hand(S.SEED_H)
        self.assertFalse(self.is_terminal(hand), "the hand is still running")
        self.assert_refused(
            lambda: self.payoffs(hand),
            "payoffs of a hand that is still running",
            ("running", "over", "terminal", "finished", "complete"),
        )
        advanced = self.apply_action(
            hand, S.choose_call(self.readout(hand), self.legal_actions(hand))
        )
        self.assertFalse(self.is_terminal(advanced), "one step does not end the hand")
        self.assert_refused(
            lambda: self.payoffs(advanced),
            "payoffs of a running hand one step on",
            ("running", "over", "terminal", "finished", "complete"),
        )

    def test_fam16_33_payoffs_is_keyed_by_seat_and_sums_to_zero(self):
        """FAM-16.33 payoffs carries one number per seat and the two sum to zero (§9)."""
        for seed in S.SEED_DISTINCT[:8]:
            payoffs = S.seat_keyed(
                self.payoffs(self.finished_hand(seed)), "payoffs of seed %r" % (seed,)
            )
            for index, value in payoffs.items():
                self.assertTrue(
                    S.is_number(value),
                    "a per-seat payoff is a number (surface.md §9); seat %r of seed %r "
                    "read %r" % (index, seed, value),
                )
            self.assertAlmostEqual(
                float(sum(payoffs.values())), 0.0, places=9,
                msg="the two seats' net chip deltas sum to zero (surface.md §9, ASM-12): "
                    "seed %r paid %r" % (seed, payoffs),
            )

    def test_fam16_34_payoffs_carries_nothing_else_numeric(self):
        """FAM-16.34 the payoff record is two keys, two numbers and no total (§9)."""
        payoffs = self.payoffs(self.finished_hand(S.SEED_I))
        self.assertTrue(S.is_mapping(payoffs), "payoffs is a mapping (surface.md §9)")
        self.assertEqual(
            len(payoffs), 2,
            "a heads-up hand pays two seats and carries no total, because a second number "
            "would no longer be a per-seat payoff (surface.md §9, ASM-12): %r" % (payoffs,),
        )
        self.assertEqual(
            len(S.numbers_in(payoffs)), 2,
            "exactly one number per seat and nothing else numeric (surface.md §9): %r"
            % (payoffs,),
        )

    def test_fam16_35_a_zero_payoff_is_a_legal_value(self):
        """FAM-16.35 a tied hand splits the pot, so a zero payoff is legal (environment §1)."""
        zeros = []
        played = 0
        for seed in S.SEED_SAMPLE:
            payoffs = S.seat_keyed(
                self.payoffs(self.finished_hand(seed, chooser=S.choose_raise)),
                "payoffs of seed %r" % (seed,),
            )
            played += 1
            self.assertAlmostEqual(
                float(sum(payoffs.values())), 0.0, places=9,
                msg="a split pays two opposite deltas (ASM-12): seed %r paid %r"
                    % (seed, payoffs),
            )
            if any(float(value) == 0.0 for value in payoffs.values()):
                zeros.append(seed)
                break
        self.assertTrue(
            zeros,
            "ties and splits are common at these stacks, so a payoff may be zero "
            "(environment.md §1, ASM-12): none of the %d hands this case played paid one"
            % (played,),
        )


if __name__ == "__main__":
    unittest.main()
