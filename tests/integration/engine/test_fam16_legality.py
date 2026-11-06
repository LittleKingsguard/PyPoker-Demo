"""FAM-1, FAM-16 — what a decision allows, and what applying it does.

`docs/L2/engine/surface.md` §2, §6, §7 and `environment.md` §2, D-2, D-16.  A
decision's descriptors are ordered fold, check/call, raise; fold appears only where
`to_call` is non-zero; every descriptor returned is one `apply_action` accepts on a
fresh hand of the same seed; a descriptor outside the list is refused and the hand is
left where it was; `to_call` is never more than the acting seat's stack; and
descriptors compare by value and print stably, because a descriptor is
hand-independent.
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


class FAM16Legality(S.EngineCase):
    """The decision's legal set, and the step's contract with it."""

    def test_fam16_20_descriptors_are_ordered_fold_check_call_raise(self):
        """FAM-16.20 a decision's descriptors are ordered as the vocabulary is (§2)."""
        order = ["fold", "check-call", "raise"]
        for seed in (S.SEED_A, S.SEED_B):
            steps, _ = self.walk(seed, limit=S.DECISION_BOUND)
            self.assertTrue(steps, "the battery needs the hand's decisions: seed %r" % (seed,))
            for position, step in enumerate(steps):
                descriptors = S.descriptor_list(
                    step.legal, "legal_actions of the decision"
                )
                kinds = [S.descriptor_kind(descriptor) for descriptor in descriptors]
                self.assertNotIn(
                    None, kinds,
                    "a descriptor names one of the three vocabulary actions, fold, "
                    "check/call and raise (e2e-surface.md §2): decision %d of seed %r "
                    "returned %r" % (position, seed, descriptors),
                )
                self.assertEqual(
                    kinds, [kind for kind in order if kind in kinds],
                    "the order is fold, then check/call, then raise (surface.md §2): "
                    "decision %d of seed %r returned %r" % (position, seed, descriptors),
                )
                self.assertEqual(
                    len(kinds), len(set(kinds)),
                    "a decision holds at most one descriptor per vocabulary index "
                    "(surface.md §2): %r" % (descriptors,),
                )

    def test_fam16_21_fold_appears_only_when_a_call_is_owed(self):
        """FAM-16.21 folding where checking is free is not an action of that decision (§2)."""
        steps, _ = self.walk(S.SEED_C, limit=S.DECISION_BOUND)
        owed = 0
        free = 0
        for position, step in enumerate(steps):
            to_call = S.one_number(step.readout["to_call"], "the readout's to_call fact")
            kinds = [
                S.descriptor_kind(descriptor)
                for descriptor in S.descriptor_list(step.legal, "legal_actions")
            ]
            if to_call > 0:
                owed += 1
                self.assertIn(
                    "fold", kinds,
                    "where to_call is %r, folding is legal (surface.md §2): decision %d "
                    "returned %r" % (to_call, position, step.legal),
                )
            else:
                free += 1
                self.assertNotIn(
                    "fold", kinds,
                    "where to_call is 0, folding is not an action of the decision "
                    "(surface.md §2): decision %d returned %r" % (position, step.legal),
                )
        self.assertGreaterEqual(
            owed, 1,
            "facing the big blind, the button owes a chip, so at least one decision has a "
            "call to make (environment.md §1)",
        )
        self.assertGreaterEqual(
            free, 1,
            "after the button calls, the big blind checks for nothing, so at least one "
            "decision is free (environment.md §1)",
        )

    def test_fam16_22_every_legal_descriptor_is_applied_on_a_fresh_hand(self):
        """FAM-16.22 every descriptor legal_actions returns is accepted by apply_action."""
        for seed in (S.SEED_D, S.SEED_E):
            descriptors = S.descriptor_list(
                self.legal_actions(self.new_hand(seed)), "legal_actions"
            )
            self.assertGreaterEqual(
                len(descriptors), 2,
                "facing the big blind, folding and continuing are both legal "
                "(e2e-surface.md §2): seed %r returned %r" % (seed, descriptors),
            )
            for descriptor in descriptors:
                advanced = self.apply_action(self.new_hand(seed), descriptor)
                self.assertIsNotNone(
                    advanced,
                    "every descriptor legal_actions returns is applied at the decision it "
                    "was returned for (surface.md §6): seed %r refused %r"
                    % (seed, descriptor),
                )
                self.assertIsInstance(
                    self.is_terminal(advanced), bool,
                    "the advanced value is a hand handle (surface.md §7): %r" % (advanced,),
                )

    def test_fam16_23_a_descriptor_outside_the_list_is_refused(self):
        """FAM-16.23 an illegal descriptor is refused, never a fold or a call for the caller."""
        hand = self.new_hand(S.SEED_F)
        before = self.readout(hand)
        self.assert_refused(
            lambda: self.apply_action(hand, "an action this game does not have"),
            "apply_action with a value that names no action of this decision",
            ("action", "descriptor", "legal"),
        )
        self.assert_refused(
            lambda: self.apply_action(hand, 2),
            "apply_action with an index instead of an action descriptor",
            ("action", "descriptor", "legal"),
        )
        self.assertEqual(
            S.canon(self.readout(hand)), S.canon(before),
            "a refused action neither advances the hand nor changes its facts "
            "(surface.md §7)",
        )

    def test_fam16_24_a_fold_where_checking_is_free_is_refused(self):
        """FAM-16.24 folding at a free decision is a descriptor outside legal_actions (§2)."""
        seed = S.SEED_G
        steps, _ = self.walk(seed, limit=S.DECISION_BOUND)
        free = self.free_decision(steps)
        fold = self.fold_descriptor(self.legal_actions(self.new_hand(seed)))
        before = S.canon(free.readout)
        self.assert_refused(
            lambda: self.apply_action(free.hand, fold),
            "apply_action with a fold at a decision whose to_call is 0",
            ("action", "descriptor", "legal"),
        )
        self.assertEqual(
            S.canon(self.readout(free.hand)), before,
            "a refused action leaves the hand where it was (surface.md §7): the caller "
            "keeps the handle and reads the same facts",
        )
        self.assertFalse(
            self.is_terminal(free.hand), "the hand is still running (surface.md §7)"
        )

    def test_fam16_25_to_call_never_exceeds_the_acting_stack(self):
        """FAM-16.25 to_call is never more than the acting seat's stack (environment.md §2)."""
        for seed in (S.SEED_H, S.SEED_I):
            steps, _ = self.walk(seed, chooser=S.choose_raise, limit=S.DECISION_BOUND)
            self.assertTrue(steps, "the battery needs the hand's decisions: seed %r" % (seed,))
            for position, step in enumerate(steps):
                to_call = S.one_number(
                    step.readout["to_call"], "the readout's to_call fact"
                )
                index, _ = S.seat_fact(step.readout["seat"])
                stacks = S.count_list(
                    step.readout["stacks"], "the readout's stacks fact"
                )
                self.assertGreaterEqual(
                    to_call, 0, "to_call is a count of chips, never negative: %r" % (to_call,),
                )
                self.assertLessEqual(
                    to_call, stacks[index],
                    "to_call is never more than the acting seat's stack, which bounds a "
                    "call for less (environment.md §2): decision %d of seed %r owed %r "
                    "from a stack of %r" % (position, seed, to_call, stacks[index]),
                )

    def test_fam16_26_descriptors_compare_by_value_and_print_stably(self):
        """FAM-16.26 two descriptors for one action at one decision are equal by value and text."""
        seed = S.SEED_J
        first = S.descriptor_list(self.legal_actions(self.new_hand(seed)), "legal_actions")
        second = S.descriptor_list(
            self.legal_actions(self.new_hand(seed)), "legal_actions of a fresh hand"
        )
        self.assertEqual(
            len(first), len(second), "one decision holds one legal set (surface.md §6)"
        )
        for left, right in zip(first, second):
            self.assertTrue(
                S.same_descriptor(left, right),
                "two descriptors for one action at one decision are equal by value "
                "(surface.md §2): %r against %r" % (left, right),
            )
            self.assertEqual(
                str(left), str(right),
                "a descriptor prints stably (surface.md §2): %r against %r"
                % (left, right),
            )
        for descriptor in second:
            self.assertIsNotNone(
                self.apply_action(self.new_hand(seed), descriptor),
                "a descriptor is hand-independent, so another hand of the same seed "
                "accepts it (surface.md §2): %r" % (descriptor,),
            )


if __name__ == "__main__":
    unittest.main()
