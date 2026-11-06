"""§1 rule 2 — an invalid argument is refused by an error naming the violated contract.

`docs/L2/engine/surface.md` §1 rule 2 and §3–§11, `e2e-surface.md` §2 (failure).  No
entry point coerces a value, substitutes a default, swallows an error or returns part
of a record.  This file covers the refusals the whole surface owns: a seed that is not
an integer (a `bool` included), a value that is not a hand handle, a hand that is over,
an illegal descriptor, a non-callable policy, a policy's own exception, and a bad
sample count.  The per-entry-point refusals are asserted beside the entry point that
owns them; this file is the shared rule.
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


class Refusals(S.EngineCase):
    """surface.md §1 rule 2, across the nine entry points."""

    def test_refusals_01_new_hand_refuses_a_seed_that_is_not_an_integer(self):
        """§4 new_hand refuses a seed that is not an integer, a `bool` included."""
        for bad in (1.5, "20251", None, True, False, [20251], (20251,), 20251 + 0j):
            self.assert_refused(
                lambda bad=bad: self.new_hand(bad),
                "new_hand with a seed that is not an integer (%r)" % (bad,),
                ("seed", "integer", "int"),
            )

    def test_refusals_02_play_hand_refuses_a_seed_that_is_not_an_integer(self):
        """§10 play_hand refuses a seed that is not an integer, a `bool` included."""
        good = S.PolicyProbe(name="the battery's policy")
        for bad in (7.25, "60617", None, True, [60617]):
            self.assert_refused(
                lambda bad=bad: self.play_hand(bad, good, good),
                "play_hand with a seed that is not an integer (%r)" % (bad,),
                ("seed", "integer", "int"),
            )

    def test_refusals_03_the_hand_queries_refuse_a_value_that_is_not_a_hand(self):
        """§5–§9 readout, legal_actions, apply_action, is_terminal and payoffs refuse non-hands."""
        descriptor = S.choose_call(
            self.readout(self.new_hand(S.SEED_A)), self.legal_actions(self.new_hand(S.SEED_A))
        )
        for bad in (None, 0, "a hand", object(), [S.SEED_A], {"seed": S.SEED_A}):
            for name in ("readout", "legal_actions", "is_terminal", "payoffs"):
                self.assert_refused(
                    lambda bad=bad, name=name: self.ep(name)(bad),
                    "%s with a value that is not a hand handle (%r)" % (name, bad),
                    ("hand", "handle"),
                )
            self.assert_refused(
                lambda bad=bad: self.apply_action(bad, descriptor),
                "apply_action with a value that is not a hand handle (%r)" % (bad,),
                ("hand", "handle"),
            )

    def test_refusals_04_a_finished_hand_is_refused_by_the_hand_queries(self):
        """§5–§8 and §11 a hand that is over has no readout, no legal action and no equity."""
        finished = self.finished_hand(S.SEED_B)
        fold = self.fold_descriptor(self.legal_actions(self.new_hand(S.SEED_B)))
        for name, call in (
            ("readout", lambda: self.readout(finished)),
            ("legal_actions", lambda: self.legal_actions(finished)),
            ("apply_action", lambda: self.apply_action(finished, fold)),
            ("equity", lambda: self.equity(finished, S.SEED_B, S.SAMPLES_COARSE)),
        ):
            self.assert_refused(
                call,
                "%s on a hand that is over" % (name,),
                ("over", "terminal", "finished", "ended", "acting"),
            )
        self.assertTrue(
            self.is_terminal(finished),
            "a completed handle still states that it is over, and is not refused "
            "(surface.md §8)",
        )

    def test_refusals_05_apply_action_refuses_an_illegal_descriptor(self):
        """§7 a descriptor that is not one of legal_actions is a contract violation."""
        hand = self.new_hand(S.SEED_C)
        for bad in ("fold please", 0, 2, None, object(), {}, ["fold"]):
            self.assert_refused(
                lambda bad=bad: self.apply_action(hand, bad),
                "apply_action with a descriptor outside legal_actions (%r)" % (bad,),
                ("action", "descriptor", "legal"),
            )
        self.assertEqual(
            len(self.readout(hand)["history"]), 0,
            "no refused action is applied on the caller's behalf (surface.md §7)",
        )

    def test_refusals_06_play_hand_refuses_a_non_callable_policy(self):
        """§10 a policy that is not callable is refused, in either seat."""
        good = S.PolicyProbe(name="the battery's policy")
        for bad in (None, 7, "a policy", {}, object()):
            self.assert_refused(
                lambda bad=bad: self.play_hand(S.SEED_D, bad, good),
                "play_hand with a seat-0 policy that is not callable (%r)" % (bad,),
                ("policy", "callable"),
            )
            self.assert_refused(
                lambda bad=bad: self.play_hand(S.SEED_D, good, bad),
                "play_hand with a seat-1 policy that is not callable (%r)" % (bad,),
                ("policy", "callable"),
            )

    def test_refusals_07_play_hand_propagates_a_policy_s_own_error(self):
        """§10 a policy's own exception is not caught and turned into an action."""
        try:
            self.play_hand(S.SEED_E, S.ExplodingPolicy(), S.PolicyProbe())
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

    def test_refusals_08_equity_refuses_a_bad_seed_and_a_bad_sample_count(self):
        """§11 equity refuses a non-integer seed and a sample count that is not positive."""
        hand = self.new_hand(S.SEED_F)
        for bad in (0.5, "20251", None, True):
            self.assert_refused(
                lambda bad=bad: self.equity(hand, bad, S.SAMPLES_COARSE),
                "equity with a seed that is not an integer (%r)" % (bad,),
                ("seed", "integer", "int"),
            )
            
        for bad in (0, -3, 7.5, "fine", None):
            self.assert_refused(
                lambda bad=bad: self.equity(hand, S.SEED_F, bad),
                "equity with a sample count that is not a positive integer (%r)" % (bad,),
                ("sample", "positive", "integer", "int"),
            )
        self.assertTrue(
            S.is_number(self.equity(hand, S.SEED_F, 1)),
            "one sample is a positive integer and is a legal call (surface.md §11)",
        )


if __name__ == "__main__":
    unittest.main()
