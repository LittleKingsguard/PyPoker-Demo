"""ASM-4, FAM-5, FAM-16 — the oracle's question, asked at the edge.

`docs/L2/engine/surface.md` §11 and `environment.md` §4.  `equity(hand, seed,
samples)` and `equity(readout, seed, samples)` denote the same decision and return
the same number; a mapping is a decision only when it carries two distinct cards under
`hole` and 0, 3, 4 or 5 distinct cards under `board`, and a fact beyond those two is
ignored; the value is a share of the pot in [0, 1]; one decision, seed and sample
count give one estimate; a coarse sample count is a legal call; and the query neither
advances nor mutates the hand and hands the caller's stream back as it found it.
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


class Equity(S.EngineCase):
    """The equity question, its shapes, its refusals and its purity."""

    def test_equity_01_the_hand_and_its_readout_are_one_question(self):
        """§11 a hand and its own readout denote the same decision and the same number."""
        seed = S.SEED_A
        hand = self.new_hand(seed)
        readout = self.readout(hand)
        from_hand = self.equity(hand, seed, S.SAMPLES_FINE)
        from_readout = self.equity(readout, seed, S.SAMPLES_FINE)
        self.assertTrue(S.is_number(from_hand), "equity returns a number (surface.md §11)")
        self.assertAlmostEqual(
            float(from_hand), float(from_readout), places=12,
            msg="a hand and its own readout denote the same decision and return the same "
                "number (surface.md §11): %r against %r" % (from_hand, from_readout),
        )

    def test_equity_02_the_decision_is_its_two_cards_and_the_board(self):
        """§11 a mapping with hole and board alone answers, and the other facts are ignored."""
        seed = S.SEED_B
        readout = self.readout(self.new_hand(seed))
        decision = {"hole": readout["hole"], "board": readout["board"]}
        whole = self.equity(readout, seed, S.SAMPLES_ODD)
        bare = self.equity(decision, seed, S.SAMPLES_ODD)
        self.assertAlmostEqual(
            float(whole), float(bare), places=12,
            msg="a fact beyond hole and board is ignored, and the same decision answers "
                "with the same number (surface.md §11): %r against %r" % (whole, bare),
        )

    def test_equity_03_the_value_is_a_share_in_the_unit_interval(self):
        """§11 the acting seat's win probability is a number in [0, 1]."""
        for seed in (S.SEED_C, S.SEED_D, S.SEED_E):
            hand = self.new_hand(seed)
            value = self.equity(hand, seed, S.SAMPLES_COARSE)
            self.assertTrue(S.is_number(value), "equity returns a number (surface.md §11)")
            self.assertGreaterEqual(float(value), 0.0, "a share of the pot is never negative")
            self.assertLessEqual(float(value), 1.0, "a share of the pot never exceeds one")

    def test_equity_04_one_decision_seed_and_sample_count_give_one_estimate(self):
        """§11 one decision, seed and sample count give one estimate."""
        seed = S.SEED_F
        hand = self.new_hand(seed)
        first = self.equity(hand, seed, S.SAMPLES_FINE)
        second = self.equity(hand, seed, S.SAMPLES_FINE)
        self.assertEqual(
            float(first), float(second),
            "its estimate is a function of the decision, its seed and the sample count and "
            "of nothing else, which is what makes it repeatable (surface.md §11, ASM-4): "
            "%r against %r" % (first, second),
        )
        same_decision = self.equity(self.new_hand(seed), seed, S.SAMPLES_FINE)
        self.assertEqual(
            float(first), float(same_decision),
            "a second hand at that seed reads the same decision, so the estimate repeats "
            "(surface.md §11)",
        )

    def test_equity_05_a_coarse_sample_count_is_legal(self):
        """§11 a coarse sample count is a legal call and not an error."""
        seed = S.SEED_G
        hand = self.new_hand(seed)
        for samples in (S.SAMPLES_COARSE, S.SAMPLES_HUGE):
            value = self.equity(hand, seed, samples)
            self.assertTrue(
                S.is_number(value),
                "a coarse sample count is a legal call and not an error (surface.md §11): "
                "%r samples returned %r" % (samples, value),
            )
            self.assertGreaterEqual(float(value), 0.0)
            self.assertLessEqual(float(value), 1.0)

    def test_equity_06_it_neither_advances_nor_mutates_the_hand(self):
        """§11 equity is a query and not a step."""
        seed = S.SEED_H
        hand = self.new_hand(seed)
        before = self.readout(hand)
        legal = self.legal_actions(hand)
        self.equity(hand, seed, S.SAMPLES_COARSE)
        after = self.readout(hand)
        self.assertEqual(
            S.canon(before), S.canon(after),
            "the query neither advances nor mutates the hand (surface.md §11)",
        )
        self.assertFalse(
            self.is_terminal(hand),
            "asking the oracle's question does not end the hand (surface.md §11)",
        )
        advanced = self.apply_action(hand, S.choose_call(after, legal))
        self.assertEqual(
            len(self.readout(advanced)["history"]), 1,
            "the hand can still be stepped after the query, so the query kept it whole "
            "(surface.md §11)",
        )

    def test_equity_07_it_hands_the_stream_back(self):
        """§11 equity samples, and still returns the caller's stream as it found it."""
        seed = S.SEED_I
        hand = self.new_hand(seed)
        readout = self.readout(hand)
        self.assert_stream_unchanged(
            lambda: self.equity(hand, seed, S.SAMPLES_COARSE), "equity of a hand"
        )
        self.assert_stream_unchanged(
            lambda: self.equity(readout, seed, S.SAMPLES_COARSE), "equity of a readout"
        )
        self.assertEqual(
            S.canon(self.readout(hand)), S.canon(readout),
            "and the hand the query was asked about is untouched (surface.md §11)",
        )

    def test_equity_08_it_refuses_a_finished_decision_a_bad_seed_and_a_bad_sample_count(self):
        """§11 a decision that is over, a non-integer seed and a bad sample count are refused."""
        finished = self.finished_hand(S.SEED_J)
        self.assert_refused(
            lambda: self.equity(finished, S.SEED_J, S.SAMPLES_COARSE),
            "equity of a decision that is over",
            ("over", "terminal", "finished", "ended"),
        )
        hand = self.new_hand(S.SEED_K)
        for bad in (1.5, "60617", None, True):
            self.assert_refused(
                lambda bad=bad: self.equity(hand, bad, S.SAMPLES_COARSE),
                "equity with a seed that is not an integer (%r)" % (bad,),
                ("seed", "integer", "int"),
            )
        for bad in (0, -7, 2.5, "83", None):
            self.assert_refused(
                lambda bad=bad: self.equity(hand, S.SEED_K, bad),
                "equity with a sample count that is not a positive integer (%r)" % (bad,),
                ("sample", "positive", "integer", "int"),
            )
        self.assertTrue(S.is_number(self.equity(hand, S.SEED_K, 1)),
                        "one sample is a positive integer, so it is a legal call")

    def test_equity_09_a_malformed_decision_is_refused_rather_than_sampled(self):
        """§11 a mapping that is not a decision is refused rather than sampled."""
        readout = self.readout(self.new_hand(S.SEED_L))
        hole = S.card_list(readout["hole"], "the readout's hole fact")
        board = S.card_list(readout["board"], "the readout's board fact")
        third = None
        for seed in (S.SEED_M, S.SEED_N, S.SEED_O):
            for card in S.card_list(self.readout(self.new_hand(seed))["hole"], "hole"):
                if all(S.canon(card) != S.canon(known) for known in hole):
                    third = card
                    break
            if third is not None:
                break
        self.assertIsNotNone(third, "the battery needs a card the decision does not hold")
        malformed = {
            "an empty mapping": {},
            "a mapping with no board": {"hole": hole},
            "a one-card hole": {"hole": [hole[0]], "board": board},
            "a three-card hole": {"hole": hole + [third], "board": board},
            "a one-card board": {"hole": hole, "board": [hole[0]]},
            "a two-card board": {"hole": hole, "board": hole},
            "a duplicate card under hole": {"hole": [hole[0], hole[0]], "board": board},
            "a board repeating a hole card": {"hole": hole, "board": [hole[0], hole[1], third]},
        }
        for what, decision in malformed.items():
            self.assert_refused(
                lambda decision=decision: self.equity(decision, S.SEED_P, S.SAMPLES_COARSE),
                "equity with %s" % (what,),
                ("hole", "board", "card", "decision", "mapping", "sampl"),
            )


if __name__ == "__main__":
    unittest.main()
