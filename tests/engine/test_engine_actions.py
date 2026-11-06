"""ENG-5 -- what the acting seat may do.

``docs/L2/engine/surface.md`` §2, §6; ``docs/L3/engine/stepping.md`` §1;
``docs/L3/engine/actions.md`` §1; ``docs/L1/battery.md`` §3 FAM-1, FAM-2,
FAM-16 (D-2).

A descriptor is one of the three plain strings ``fold``, ``check-call`` and
``raise``, ordered as the vocabulary is, with at most one entry per action, and
``fold`` appears only when there is something to call.
"""

import os
import random
import sys
import unittest

try:  # discovered as part of a tests.engine package
    from . import _engine_support as S
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _engine_support as S  # noqa: E402


class ENG5Legality(S.EngineCase):
    """`legal_actions` is ordered, duplicate-free and bounded by the fixed game."""

    def test_eng5_1_the_first_decision_offers_the_three_actions_in_order(self):
        """ENG-5.1 facing the big blind all three descriptors are returned, in the order
        fold, check-call, raise, without duplicates, and two calls are equal
        (surface.md §2, §6, stepping.md §1)."""
        hand = self.hand(S.SEED_A)
        legal = self.legal(hand)
        self.assertEqual(
            list(legal), ["fold", "check-call", "raise"],
            "the first decision faces the big blind, so folding, continuing and raising are "
            "all legal, in the vocabulary's order (surface.md §2): %r" % (legal,),
        )
        self.assertEqual(len(set(legal)), len(legal),
                         "a decision's descriptors hold at most one entry per action")
        self.assertEqual(
            list(self.legal(hand)), list(legal),
            "two calls on one hand return equal sequences (surface.md §6)",
        )
        for seed in (S.SEED_D, S.SEED_F):
            with self.subTest(seed=seed):
                other = self.hand(seed)
                self.assertEqual(
                    list(self.legal(other)), ["fold", "check-call", "raise"],
                    "the first decision of any seed offers the three actions in order: %r"
                    % (list(self.legal(other)),),
                )

    def test_eng5_2_after_the_button_calls_folding_is_not_legal(self):
        """ENG-5.2 after seat 0 calls, the big blind's decision has to_call 0 and no
        fold, but check-call and raise (surface.md §2, stepping.md §1, FAM-16.10)."""
        hand = self.step(self.hand(S.SEED_B), "check-call")
        facts = self.readout(hand)
        self.assertEqual(facts["seat"][0], 1, "the big blind acts after the button calls")
        self.assertEqual(facts["to_call"], 0, "the big blind has nothing to call")
        legal = list(self.legal(hand))
        self.assertNotIn(
            "fold", legal,
            "fold appears only when to_call is non-zero, because folding where checking is "
            "free is not an action of that decision (surface.md §2): %r" % (legal,),
        )
        self.assertIn("check-call", legal, "the big blind may check")
        self.assertIn("raise", legal, "the big blind may raise")

    def test_eng5_3_raise_disappears_when_the_streets_four_bet_cap_is_reached(self):
        """ENG-5.3 at the decision whose raise count is 4 the tuple holds no raise
        (surface.md §2, stepping.md §1: the cap is 4 on a street)."""
        walk, _ = self.drive(S.SEED_C, S.always_raise)
        capped = [facts for facts, _legal, _action in walk if facts["limit"][1] == 4]
        self.assertTrue(
            capped,
            "a policy that always raises reaches the four-bet cap of a street (ASM-6): %r"
            % ([facts["limit"] for facts, _l, _a in walk],),
        )
        for facts in capped:
            self.assertNotIn(
                "raise", list(facts["legal"]),
                "the street's cap of four bets makes raising illegal (stepping.md §1): %r"
                % (facts,),
            )

    def test_eng5_4_legal_actions_refuses_a_finished_hand_and_a_non_hand(self):
        """ENG-5.4 legal_actions refuses a hand that is over and a value that is not a
        hand handle (surface.md §6, stepping.md §1, errors.md §3)."""
        finished = self.played_out(S.SEED_A)
        arguments = (None, 42, self.readout(self.hand(S.SEED_E)))
        before = random.getstate()
        exc = self.refusal(S.ep("legal_actions"), finished)
        self.assert_mentions(exc, "over", "hand", "acting")
        for bad in arguments:
            with self.subTest(argument=type(bad).__name__):
                exc = self.refusal(S.ep("legal_actions"), bad)
                self.assert_mentions(exc, "hand")
        self.assertEqual(
            random.getstate(), before,
            "a refusal draws no randomness and moves no stream (surface.md §1)",
        )


if __name__ == "__main__":
    unittest.main()
