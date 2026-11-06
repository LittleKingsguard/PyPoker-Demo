"""ENG-6 -- one applied action: the step, the history and the untouched handle.

``docs/L2/engine/surface.md`` §1 rule 6, §7; ``docs/L3/engine/advance.md`` §1-§3;
``docs/L3/engine/stepping.md`` §2; ``docs/L1/battery.md`` §3 FAM-5, FAM-16.

A step returns an advanced handle and leaves its argument at its own state,
because a caller keeps an earlier handle and queries it after the hand has moved
on.  Each applied action appends exactly one entry to the public history, and an
action that is not legal for that hand is refused rather than turned into a fold
or a call on the violator's behalf.
"""

import os
import random
import re
import sys
import unittest

try:  # discovered as part of a tests.engine package
    from . import _engine_support as S
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _engine_support as S  # noqa: E402

# advance.md §2's grammar: "<street> seat <index> folds|checks|calls N|raises to N".
ENTRY = re.compile(
    r"^(?P<street>preflop|flop|turn|river) seat (?P<seat>[01]) "
    r"(?P<verb>folds|checks|calls|raises)(?: to)?(?: (?P<amount>[0-9]+))?$"
)


class ENG6Stepping(S.EngineCase):
    """`apply_action` advances by copy, appends one history entry and refuses."""

    def test_eng6_1_every_legal_descriptor_is_accepted_on_a_fresh_hand(self):
        """ENG-6.1 each descriptor legal_actions returns is accepted by apply_action on a
        fresh hand of the same seed (stepping.md §3, surface.md §7)."""
        for seed in (S.SEED_A, S.SEED_E):
            descriptors = list(self.legal(self.hand(seed)))
            self.assertTrue(descriptors, "a live hand has at least one legal descriptor")
            with self.subTest(seed=seed):
                for descriptor in descriptors:
                    advanced = self.step(self.hand(seed), descriptor)
                    self.assertIsNotNone(
                        advanced, "apply_action accepts %r at seed %r" % (descriptor, seed))
                    if self.terminal(advanced):
                        self.assertEqual(
                            descriptor, "fold",
                            "the only action that ends a heads-up hand is a fold: %r ended it"
                            % (descriptor,),
                        )
                    else:
                        self.assertEqual(
                            len(self.readout(advanced)["history"]), 1,
                            "the accepted descriptor advanced the hand by exactly one action",
                        )

    def test_eng6_2_one_applied_action_is_one_history_entry_for_each_verb(self):
        """ENG-6.2 one applied action appends exactly one history entry; entries are plain
        strings naming the pre-step street and acting seat.  A check-call and a raise are
        read back through the advanced handle's readout; a fold ends a heads-up hand, so
        the fold's entry is asserted through the episode record instead (advance.md §2,
        surface.md §7, FAM-16.4)."""
        verbs = {"check-call": ("calls", "checks"), "raise": ("raises",)}
        for action in sorted(verbs):
            with self.subTest(action=action):
                hand = self.hand(S.SEED_C)
                before = self.readout(hand)
                after = self.readout(self.step(hand, action))
                self.assertEqual(
                    len(after["history"]), len(before["history"]) + 1,
                    "one applied action is one entry in the public history "
                    "(advance.md §2): %r" % (after["history"],),
                )
                entry = after["history"][-1]
                self.assertIsInstance(entry, str, "a history entry is a plain str: %r" % (entry,))
                matched = ENTRY.match(entry)
                self.assertIsNotNone(
                    matched, "a history entry follows advance.md §2's grammar: %r" % (entry,))
                self.assertEqual(
                    matched.group("street"), before["street"],
                    "the entry is built from the state before the step, so it names that "
                    "street (advance.md §2): %r" % (entry,),
                )
                self.assertEqual(
                    matched.group("seat"), str(before["seat"][0]),
                    "the entry names the engine seat that acted (hand.md §3): %r" % (entry,),
                )
                self.assertIn(
                    matched.group("verb"), verbs[action],
                    "the entry names the action applied (advance.md §2): %r" % (entry,),
                )
                if action == "check-call":
                    expected = "checks" if before["to_call"] == 0 else "calls"
                    self.assertEqual(
                        matched.group("verb"), expected,
                        "a check-call with nothing to call is written as a check, otherwise as "
                        "a call of the chips added (advance.md §2): %r" % (entry,),
                    )
                if matched.group("verb") in ("calls", "raises"):
                    self.assertIsNotNone(
                        matched.group("amount"),
                        "a call and a raise carry the amount the operation reported "
                        "(advance.md §2): %r" % (entry,),
                    )
                    self.assertGreater(int(matched.group("amount")), 0,
                                       "the amount of a call or a raise is positive: %r" % (entry,))

        checked = self.step(self.step(self.hand(S.SEED_C), "check-call"), "check-call")
        entries = self.readout(checked)["history"]
        self.assertTrue(
            any(" checks" in entry for entry in entries),
            "a check-call with nothing to call is written as a check (advance.md §2): %r"
            % (entries,),
        )

        # A fold ends a heads-up hand, so its entry can never be read back -- the
        # readout refuses a hand that is over (surface.md §5).  The battery asserts the
        # fold through the episode record, which is the hand (episode.md §5).
        folded = self.step(self.hand(S.SEED_C), "fold")
        self.assertTrue(self.terminal(folded), "a fold of the first decision ends the hand")
        self.refusal(S.ep("readout"), folded)
        record = self.episode(S.SEED_C, S.always_fold, S.always_call)
        self.assertEqual(
            [decision["action"] for decision in record["decisions"]], ["fold"],
            "the fold of the first decision is one applied action and no more "
            "(advance.md §2, episode.md §5)",
        )

    def test_eng6_3_one_seed_and_one_policy_sequence_give_one_history(self):
        """ENG-6.3 the same seed and the same policy sequence give identical history
        lists, so two records of one deal compare through history alone
        (advance.md §2, FAM-4)."""
        first, _ = self.drive(S.SEED_B, S.always_raise)
        second, _ = self.drive(S.SEED_B, S.always_raise)
        self.assertEqual(
            first[-1][0]["history"], second[-1][0]["history"],
            "two driven hands of one seed and one policy sequence produce identical history "
            "lists (advance.md §2)",
        )
        self.assertEqual(
            len(first[-1][0]["history"]), len(first) - 1,
            "the last decision's readout holds one entry per applied action before it, and no "
            "extras (advance.md §2)",
        )
        for entry in first[-1][0]["history"]:
            self.assertIsNotNone(ENTRY.match(entry), "every entry is a stable str: %r" % (entry,))

    def test_eng6_4_the_argument_handle_is_untouched(self):
        """ENG-6.4 a step leaves its argument at its own state: the same readout, the
        same terminal answer, and payoffs still refused (surface.md §1 rule 6, §7,
        advance.md §1)."""
        hand = self.hand(S.SEED_D)
        before = self.readout(hand)
        self.assertFalse(self.terminal(hand), "a freshly dealt hand is not over")
        advanced = self.step(hand, "raise")
        self.assertNotEqual(self.readout(advanced), before, "the step moved the returned handle")
        self.assertEqual(
            self.readout(hand), before,
            "apply_action leaves its argument at its own state, because a caller keeps an "
            "earlier handle and queries it after the hand has moved on (surface.md §1)",
        )
        self.assertFalse(self.terminal(hand), "the argument handle still reports itself live")
        self.refusal(S.ep("payoffs"), hand)  # still running, so it has paid nothing

    def test_eng6_5_two_actions_from_one_handle_fork(self):
        """ENG-6.5 two different actions from one handle both succeed and give handles
        whose readouts differ (advance.md §1, stepping.md §3)."""
        hand = self.hand(S.SEED_F)
        called = self.step(hand, "check-call")
        raised = self.step(hand, "raise")
        self.assertIsNotNone(called, "check-call from the shared handle succeeded")
        self.assertIsNotNone(raised, "raise from the shared handle succeeded")
        self.assertNotEqual(
            self.readout(called), self.readout(raised),
            "two different actions from one handle are two different hands (advance.md §1)",
        )
        self.assertEqual(
            self.readout(hand)["history"], [],
            "neither step rebound the handle they were both applied to (advance.md §1)",
        )

    def test_eng6_6_an_illegal_descriptor_is_refused_and_changes_nothing(self):
        """ENG-6.6 apply_action refuses a descriptor outside legal_actions for that hand
        -- fold where checking is free, raise at the cap -- leaving the handle and the
        stream unchanged (surface.md §7, stepping.md §2, errors.md §3)."""
        checked = self.step(self.hand(S.SEED_A), "check-call")
        self.assertNotIn("fold", list(self.legal(checked)),
                         "the premise: folding is not legal when to_call is 0")
        before = self.readout(checked)
        stream = random.getstate()
        exc = self.refusal(S.ep("apply_action"), checked, "fold")
        self.assert_mentions(exc, "legal", "action")
        self.assert_untouched(checked, before)
        self.assertEqual(random.getstate(), stream,
                         "a refused step draws no randomness (surface.md §7)")

        walk, _ = self.drive(S.SEED_B, S.always_raise)
        self.assertTrue(
            [facts for facts, _legal, _action in walk if facts["limit"][1] == 4],
            "an always-raise policy reaches the street's four-bet cap (ASM-6)",
        )
        hand = self.hand(S.SEED_B)
        for facts, _legal, action in walk:
            if facts["limit"][1] == 4 and "raise" not in list(facts["legal"]):
                before = self.readout(hand)
                self.assertEqual(before, facts, "the driven hand stands at the capped decision")
                exc = self.refusal(S.ep("apply_action"), hand, "raise")
                self.assert_mentions(exc, "legal", "action")
                self.assert_untouched(hand, before)
                break
            hand = self.step(hand, action)
        else:
            self.fail("the walk reached no decision at the four-bet cap")

    def test_eng6_7_a_non_descriptor_is_refused(self):
        """ENG-6.7 apply_action refuses an integer index, None and a differently spelled
        word: there is no coercion and no normalisation (actions.md §3, stepping.md §2)."""
        hand = self.hand(S.SEED_E)
        before = self.readout(hand)
        exc = self.refusal(S.ep("apply_action"), hand, 0)
        self.assert_mentions(exc, "action", "legal")
        self.assert_untouched(hand, before)
        for bad in (1, 2, None, "Fold", "call", "check", "raise to 8", ""):
            with self.subTest(action=bad):
                hand = self.hand(S.SEED_E)
                before = self.readout(hand)
                exc = self.refusal(S.ep("apply_action"), hand, bad)
                self.assert_mentions(exc, "action", "legal")
                self.assert_untouched(hand, before)

    def test_eng6_8_a_finished_hand_is_refused_and_unchanged(self):
        """ENG-6.8 apply_action refuses a hand that is over, leaving that handle and the
        global stream as they were (surface.md §7, advance.md §3)."""
        finished = self.played_out(S.SEED_C)
        stream = random.getstate()
        exc = self.refusal(S.ep("apply_action"), finished, "check-call")
        self.assert_mentions(exc, "over", "hand")
        self.assertEqual(
            random.getstate(), stream,
            "a refused step leaves the global stream as it found it (surface.md §1)",
        )
        self.assertTrue(self.terminal(finished), "the refused call did not re-open the hand")


if __name__ == "__main__":
    unittest.main()
