"""ENG-11 -- refusals: what the module will not accept, and names when it refuses.

``docs/L2/engine/surface.md`` §1; ``docs/L3/engine/errors.md`` §1-§4;
``docs/L1/battery.md`` §2 (a refusal is an outcome, not a class).

A refusal raises an error that names the violated contract, coerces nothing,
substitutes no default, swallows nothing and returns no partial record; and a
refused call has no side effect -- it is refused before the first mutation, the
first copy and the first seed.  The battery asserts that the call raises, that
the message names the contract in words the design uses, and that nothing moved;
it never asserts an exception class, because the class is the module's freedom.
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


class ENG11Refusals(S.EngineCase):
    """One case per entry point that has a refusal in its contract."""

    def test_eng11_1_readout_refuses_a_value_that_is_not_a_hand(self):
        """ENG-11.1 readout refuses what is not a hand handle -- None, an int, and a
        readout mapping -- naming the hand contract (surface.md §5, readout.md §1,
        errors.md §3)."""
        arguments = (None, 42, self.readout(self.hand(S.SEED_A)), "hand", 3.5)
        for bad in arguments:
            with self.subTest(argument=type(bad).__name__):
                exc = self.refusal(S.ep("readout"), bad)
                self.assert_mentions(exc, "hand")

    def test_eng11_2_readout_refuses_a_hand_that_is_over(self):
        """ENG-11.2 readout refuses a hand that is over, because a hand with no acting
        seat has no readout, and the finished handle is unchanged (surface.md §5,
        readout.md §1)."""
        finished = self.played_out(S.SEED_A)
        paid = dict(self.payoffs(finished))
        exc = self.refusal(S.ep("readout"), finished)
        self.assert_mentions(exc, "over", "acting", "hand")
        self.assertTrue(self.terminal(finished), "the refused read did not re-open the hand")
        self.assertEqual(dict(self.payoffs(finished)), paid,
                         "a refused read leaves the finished hand exactly as it was")

    def test_eng11_3_is_terminal_refuses_only_a_non_hand(self):
        """ENG-11.3 is_terminal refuses a value that is not a hand handle and accepts
        every handle, a freshly dealt one included (surface.md §8, hand.md §5)."""
        for bad in (None, 0, self.readout(self.hand(S.SEED_B)), "hand", [S.SEED_A]):
            with self.subTest(argument=type(bad).__name__):
                exc = self.refusal(S.ep("is_terminal"), bad)
                self.assert_mentions(exc, "hand")
        self.assertIsInstance(self.terminal(self.hand(S.SEED_B)), bool,
                              "a freshly dealt handle states whether it is over (surface.md §8)")
        self.assertIsInstance(self.terminal(self.played_out(S.SEED_C)), bool,
                              "a completed handle states whether it is over")

    def test_eng11_4_payoffs_refuses_a_running_hand_and_a_non_hand(self):
        """ENG-11.4 payoffs refuses a hand that is still running and a value that is not a
        hand handle (surface.md §9, hand.md §5)."""
        running = self.hand(S.SEED_D)
        before = self.readout(running)
        exc = self.refusal(S.ep("payoffs"), running)
        self.assert_mentions(exc, "hand", "over", "running")
        self.assert_untouched(running, before)
        for bad in (None, 11, before, "hand"):
            with self.subTest(argument=type(bad).__name__):
                exc = self.refusal(S.ep("payoffs"), bad)
                self.assert_mentions(exc, "hand")

    def test_eng11_5_play_hand_refuses_a_bad_seed_and_a_non_callable_policy(self):
        """ENG-11.5 play_hand refuses a seed that is not an integer and a policy that is not
        callable, naming the contract and the seat, before the deal, and a refused call
        moves no stream (surface.md §10, episode.md §1, errors.md §3)."""
        policy = S.always_call
        stream = random.getstate()
        exc = self.refusal(S.ep("play_hand"), "20260101", policy, policy)
        self.assert_mentions(exc, "seed")
        for bad_seed in (4242424.0, None, True):
            with self.subTest(seed=bad_seed):
                exc = self.refusal(S.ep("play_hand"), bad_seed, policy, policy)
                self.assert_mentions(exc, "seed")
        self.assertEqual(
            random.getstate(), stream,
            "a refused seed is refused before the deal, so it cannot move the stream "
            "(episode.md §1)",
        )
        exc = self.refusal(S.ep("play_hand"), S.SEED_A, "always-call", policy)
        self.assert_mentions(exc, "policy")
        for seat, argument in (
            ("seat0_policy", "always-call"),
            ("seat1_policy", 7),
            ("seat0_policy", None),
            ("seat1_policy", []),
        ):
            with self.subTest(seat=seat, policy=type(argument).__name__):
                left, right = (argument, policy) if seat == "seat0_policy" else (policy, argument)
                exc = self.refusal(S.ep("play_hand"), S.SEED_A, left, right)
                self.assert_mentions(exc, "policy")
        self.assertEqual(
            random.getstate(), stream,
            "a refused policy is refused before the deal, so it cannot move the stream "
            "(episode.md §1)",
        )

    def test_eng11_6_play_hand_refuses_an_answer_outside_the_legal_descriptors(self):
        """ENG-11.6 a policy that answers outside legal_actions is refused -- an integer
        index is not a descriptor, even when it denotes a legal action -- and is never
        turned into a fold (surface.md §10, actions.md §3, D-2)."""
        exc = self.refusal(
            S.ep("play_hand"), S.SEED_B,
            lambda readout, legal: 1,
            S.always_call,
        )
        self.assert_mentions(exc, "policy", "legal", "action")
        for answer in (0, 2, "Fold", "call", None):
            with self.subTest(answer=answer):
                exc = self.refusal(
                    S.ep("play_hand"), S.SEED_B,
                    lambda readout, legal, answer=answer: answer,
                    S.always_call,
                )
                self.assert_mentions(exc, "policy", "legal", "action")
        for answer in (1, 2):
            with self.subTest(seat=1, answer=answer):
                exc = self.refusal(
                    S.ep("play_hand"), S.SEED_C,
                    S.always_call,
                    lambda readout, legal, answer=answer: answer,
                )
                self.assert_mentions(exc, "policy", "legal", "action")

    def test_eng11_7_a_policys_own_exception_propagates_unchanged(self):
        """ENG-11.7 play_hand does not catch a policy's own exception and turn it into an
        action: the exact type and message reach the caller (surface.md §10,
        episode.md §1, guardrails G8)."""

        class PolicyExploded(RuntimeError):
            pass

        def exploding(readout, legal):
            raise PolicyExploded("this policy refuses to play")

        try:
            S.ep("play_hand")(S.SEED_E, exploding, S.always_call)
        except PolicyExploded as exc:
            self.assertEqual(str(exc), "this policy refuses to play",
                             "the policy's own exception reaches the caller unchanged")
            self.assertIs(type(exc), PolicyExploded,
                          "the exception is not wrapped in a refusal of this module "
                          "(surface.md §10)")
        except S.SurfaceAbsent:
            raise
        except Exception as exc:  # pragma: no cover - the defect this case exists for
            self.fail(
                "play_hand converted the policy's own RuntimeError into %s(%s) instead of "
                "letting it propagate (surface.md §10, guardrails G8)"
                % (type(exc).__name__, exc)
            )
        else:  # pragma: no cover
            self.fail("play_hand swallowed the policy's exception and played on (surface.md §10)")

    def test_eng11_8_equity_refuses_a_non_hand_decision_and_a_bad_seed_or_sample_count(self):
        """ENG-11.8 equity refuses a mapping that is not a decision -- missing `hole` or
        `board`, a hole that is not exactly two cards, a board that is not 0, 3, 4 or 5
        cards, a non-card either side -- and a value that is no mapping at all, a finished
        hand, a non-integer seed and a non-positive sample count, and moves nothing
        (surface.md §11, equity.md §1, errors.md §4)."""
        hand = self.hand(S.SEED_F)
        before = self.readout(hand)
        hole = list(before["hole"])
        free = [rank + suit for rank in S.RANKS for suit in S.SUITS if rank + suit not in hole]
        malformed = (
            ("a mapping with no hole", {"board": []}),
            ("a mapping with no board", {"hole": hole}),
            ("a hole of one card", {"hole": hole[:1], "board": []}),
            ("a hole of three cards", {"hole": hole + free[:1], "board": []}),
            ("a non-card in the hole", {"hole": [hole[0], "Zz"], "board": []}),
            ("a board of one card", {"hole": hole, "board": free[:1]}),
            ("a board of two cards", {"hole": hole, "board": free[:2]}),
            ("a board of six cards", {"hole": hole, "board": free[:6]}),
            ("a non-card on the board", {"hole": hole, "board": free[:2] + ["Zz"]}),
        )
        finished = self.played_out(S.SEED_A)
        stream = random.getstate()
        for label, bad in (("None", None), ("an int", 5), ("a float", 3.5)) + malformed:
            with self.subTest(decision=label):
                exc = self.refusal(S.ep("equity"), bad, S.SEED_F, S.SAMPLES_MID)
                self.assert_mentions(exc, "decision", "hand", "readout")
        exc = self.refusal(S.ep("equity"), finished, S.SEED_A, S.SAMPLES_MID)
        self.assert_mentions(exc, "over", "hand", "decision")
        for bad_seed in ("seed", None, 1.5):
            with self.subTest(seed=bad_seed):
                exc = self.refusal(S.ep("equity"), hand, bad_seed, S.SAMPLES_MID)
                self.assert_mentions(exc, "seed")
        for bad_samples in (0, -1, 1.5, None):
            with self.subTest(samples=bad_samples):
                exc = self.refusal(S.ep("equity"), hand, S.SEED_F, bad_samples)
                self.assert_mentions(exc, "sample")
        self.assertEqual(random.getstate(), stream,
                         "every refusal happens before the sample, so the stream is untouched "
                         "(equity.md §1)")
        self.assertEqual(self.readout(hand), before, "the refusals changed nothing")


    def test_eng11_9_play_hand_refuses_a_seating_that_is_not_the_shapes(self):
        """ENG-11.9 play_hand refuses a `seats` sequence whose length is not the shape's
        seat count, a seating handed beside a positional policy, the two positional
        policies on a shape with more than two seats, and a policy that is not callable --
        positionally or inside the seating -- naming the violated contract, as an error of
        this module's own refusal tree, before the deal, so no refusal moves the global
        stream (surface.md §1, §10, episode.md §1, seats.md §4, errors.md §2,
        e2e-surface.md §3.1)."""
        six = self.seating(S.SIX_SEAT_SHAPE)
        two = self.seating(S.DEFAULT_SHAPE)
        self.assertEqual(
            [len(six), len(two)], [6, 2],
            "the premise: the two seatings are the two shapes' own seat counts "
            "(seats.md §2): %r and %r" % (len(six), len(two)),
        )
        refusals = (
            ("a seating of two policies on the six-seat shape",
             lambda: S.ep("play_hand")(S.SIX_SEED_A, seats=two, shape=S.SIX_SEAT_SHAPE),
             ("seat",)),
            ("a seating of six policies on a two-seat shape",
             lambda: S.ep("play_hand")(S.SIX_SEED_A, seats=six),
             ("seat",)),
            ("a seating beside the first positional policy",
             lambda: S.ep("play_hand")(S.SIX_SEED_A, S.always_call, None,
                                       S.SIX_SEAT_SHAPE, six),
             ("seat", "policy")),
            ("a seating beside the second positional policy",
             lambda: S.ep("play_hand")(S.SIX_SEED_A, None, S.always_call,
                                       S.SIX_SEAT_SHAPE, six),
             ("seat", "policy")),
            ("the two positional policies on the six-seat shape",
             lambda: S.ep("play_hand")(S.SIX_SEED_A, S.always_call, S.always_call,
                                       S.SIX_SEAT_SHAPE),
             ("seat", "policy")),
            ("a non-callable first positional policy",
             lambda: S.ep("play_hand")(S.SIX_SEED_A, "always-call", S.always_call),
             ("policy",)),
            ("a non-callable second positional policy",
             lambda: S.ep("play_hand")(S.SIX_SEED_C, S.always_call, 7),
             ("policy",)),
            ("a non-callable policy inside a six-seat seating",
             lambda: S.ep("play_hand")(S.SIX_SEED_C, seats=six[:5] + (None,),
                                       shape=S.SIX_SEAT_SHAPE),
             ("policy",)),
            ("a non-callable policy inside a two-seat seating",
             lambda: S.ep("play_hand")(S.SIX_SEED_C, seats=(S.always_call, "check-call")),
             ("policy",)),
        )
        stream = random.getstate()
        for label, call, words in refusals:
            with self.subTest(refusal=label):
                exc = self.refusal(call)
                self.assert_mentions(exc, *words)
                self.assertEqual(
                    type(exc).__module__.split(".")[0], "engine",
                    "the refusal is this module's own -- an error of the engine package's "
                    "refusal tree, never Python's TypeError from the call itself and never "
                    "a battery failure (errors.md §2, seats.md §4): %s(%s)"
                    % (type(exc).__name__, exc),
                )
                self.assertEqual(
                    random.getstate(), stream,
                    "the seating is checked before the deal, so a refused call cannot move "
                    "the global random stream (episode.md §1, seats.md §4): %r moved it"
                    % (label,),
                )
        self.assertEqual(
            random.getstate(), stream,
            "every one of the four refusals happened before a deal (episode.md §1)",
        )
        self.assertTrue(
            self.episode(S.SIX_SEED_D, S.always_call, S.always_call)["decisions"],
            "and the two-policy path is still accepted after the refusals: a refusal is an "
            "outcome and not a state the engine keeps (surface.md §1, seats.md §4)",
        )


if __name__ == "__main__":
    unittest.main()
