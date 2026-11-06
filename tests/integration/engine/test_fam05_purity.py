"""FAM-5 — a step advances by returning a handle, and leaves everything else alone.

`docs/L2/engine/surface.md` §1 rules 4 and 6, §7; `environment.md` §1 (stateless),
ASM-2, `strata/platform.md` (`pokerkit` draws from the global stream while it deals
a street).  The hand is a value: a step returns the advanced handle and leaves its
argument at its own state, two handles are independent, a step does not mutate the
readout it was taken from, and every call hands the caller's global `random` stream
back as it found it — `apply_action` included, even though the library draws when it
deals a street.
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


class FAM5Purity(S.EngineCase):
    """Stepping and purity at the module's edge."""

    def test_fam5_01_a_step_returns_an_advanced_handle_and_leaves_its_argument(self):
        """FAM-5.1 apply_action returns the advanced hand and leaves its argument alone."""
        hand = self.new_hand(S.SEED_A)
        before = self.readout(hand)
        action = S.choose_call(before, self.legal_actions(hand))
        advanced = self.apply_action(hand, action)
        after = self.readout(hand)
        self.assertEqual(
            S.canon(before), S.canon(after),
            "a step leaves its argument at its own state, because a caller keeps an "
            "earlier handle and queries it after the hand has moved on (surface.md §1 "
            "rule 6, §7)",
        )
        self.assertFalse(
            self.is_terminal(hand),
            "the argument is still the decision it was: it is not the advanced hand "
            "(surface.md §7)",
        )
        self.assertFalse(
            self.is_terminal(advanced),
            "a call preflop leaves the big blind to act (environment.md §1)",
        )
        advanced_readout = self.readout(advanced)
        self.assertEqual(
            len(advanced_readout["history"]), 1,
            "the advanced handle has applied one action (surface.md §7): %r"
            % (advanced_readout["history"],),
        )

    def test_fam5_02_two_handles_from_one_hand_are_independent(self):
        """FAM-5.2 two handles of one hand are independent (surface.md §1, environment §1)."""
        hand = self.new_hand(S.SEED_B)
        opening = self.readout(hand)
        legal = self.legal_actions(hand)
        call = S.choose_call(opening, legal)
        fold = self.fold_descriptor(legal)
        called = self.apply_action(hand, call)
        folded = self.apply_action(hand, fold)
        self.assertTrue(
            self.is_terminal(folded),
            "folding preflop ends the hand (environment.md §1): %r" % (fold,),
        )
        self.assertFalse(
            self.is_terminal(called),
            "calling preflop does not end the hand (environment.md §1)",
        )
        continued = self.apply_action(
            called, S.choose_call(self.readout(called), self.legal_actions(called))
        )
        self.assertIsNotNone(continued)
        self.assertEqual(
            len(self.readout(called)["history"]), 1,
            "stepping the called branch leaves it at its own state (environment.md §1)",
        )
        self.assertTrue(
            self.is_terminal(folded),
            "the folded branch is unchanged by the other branch's steps (surface.md §7)",
        )
        self.assertEqual(
            S.canon(self.readout(hand)), S.canon(opening),
            "the origin handle is unchanged by either branch (surface.md §1 rule 6)",
        )

    def test_fam5_03_a_step_does_not_mutate_the_readout_it_came_from(self):
        """FAM-5.3 the readout a step was taken from keeps its own facts (surface.md §7)."""
        hand = self.new_hand(S.SEED_C)
        readout = self.readout(hand)
        snapshot = S.canon(readout)
        action = S.choose_call(readout, self.legal_actions(hand))
        self.apply_action(hand, action)
        self.assertEqual(
            S.canon(readout), snapshot,
            "a step does not mutate the readout it was taken from (surface.md §1 rule 6)",
        )
        self.assertEqual(
            len(readout["history"]), 0,
            "the readout still reports the history it was taken at: %r"
            % (readout["history"],),
        )

    def test_fam5_04_a_step_hands_the_stream_back(self):
        """FAM-5.4 apply_action leaves the global stream as it found it (§1 rule 4, §7)."""
        hand = self.new_hand(S.SEED_D)
        action = S.choose_call(self.readout(hand), self.legal_actions(hand))
        self.assert_stream_unchanged(
            lambda: self.apply_action(hand, action), "apply_action"
        )

    def test_fam5_05_the_queries_draw_no_randomness(self):
        """FAM-5.5 readout, legal_actions, is_terminal and payoffs draw nothing (ASM-2)."""
        hand = self.new_hand(S.SEED_E)
        for what, call in (
            ("readout", lambda: self.readout(hand)),
            ("legal_actions", lambda: self.legal_actions(hand)),
            ("is_terminal of a running hand", lambda: self.is_terminal(hand)),
        ):
            self.assert_stream_unchanged(call, what)
        finished = self.finished_hand(S.SEED_E)
        self.assert_stream_unchanged(lambda: self.payoffs(finished), "payoffs")
        self.assert_stream_unchanged(
            lambda: self.is_terminal(finished), "is_terminal of a completed hand"
        )

    def test_fam5_06_a_whole_street_of_steps_hands_the_stream_back(self):
        """FAM-5.6 stepping through a street boundary deals cards and still restores the stream."""
        hand = self.new_hand(S.SEED_F)
        stepped = 0
        for _ in range(S.DECISION_BOUND):
            if self.is_terminal(hand):
                break
            readout = self.readout(hand)
            if readout["street"] != "preflop":
                break
            action = S.choose_call(readout, self.legal_actions(hand))
            before = self.stream()
            hand = self.apply_action(hand, action)
            stepped += 1
            self.assertEqual(
                S.canon(before), S.canon(self.stream()),
                "apply_action hands the global stream back as it found it, restoring "
                "whatever the library drew while the step dealt a street "
                "(surface.md §7, ASM-2): seed %r, step %d" % (S.SEED_F, stepped),
            )
        self.assertGreaterEqual(stepped, 2, "the preflop is more than one action long")
        self.assertEqual(
            self.readout(hand)["street"], "flop",
            "the battery's always-call policy walks out of the preflop and the flip of "
            "the board is where the library draws (strata/platform.md)",
        )


if __name__ == "__main__":
    unittest.main()
