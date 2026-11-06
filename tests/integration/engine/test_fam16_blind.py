"""FAM-16 — one blind instance for each of the eight `general` rows of `engine`.

`docs/L1/e2e-surface.md` §5, `battery.md` §4, D-15.  Each of the eight `general` rows
of `engine` — `new_hand`, `readout`, `legal_actions`, `apply_action`, `is_terminal`,
`payoffs`, `play_hand`, `equity` — is the subject of one case here, and the case's
instance (the seed, the sample count, the policy pair) appears in no design document:
it is invented from the declared surface alone, which is what keeps the walkthrough
blind.  `game_config` is a `fixed` row and is not blinded.
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


# The blind instances of this file: seeds, sample counts and behaviours invented by
# the test writer and named in no design document (D-15).
BLIND_NEW_HAND = (S.SEED_O, S.SEED_P)        # 96001 against 10501
BLIND_READOUT = S.SEED_N                      # 70571
BLIND_LEGAL = S.SEED_M                        # 55049
BLIND_APPLY = S.SEED_L                        # 48017
BLIND_TERMINAL = S.SEED_K                     # 22273
BLIND_PAYOFFS = S.SEED_J                      # 13337
BLIND_EPISODE = S.SEED_I                      # 90917
BLIND_EQUITY = S.SEED_H                       # 81233
BLIND_SAMPLES = 211


class BlindInstances(S.EngineCase):
    """One invented instance per `general` row, invented from the surface alone."""

    def test_fam16_01_engine_new_hand_blind_instance(self):
        """FAM-16.1 new_hand — instance: seed 96001, with 10501 as the contrast."""
        first = S.canon(self.readout(self.new_hand(BLIND_NEW_HAND[0])))
        second = S.canon(self.readout(self.new_hand(BLIND_NEW_HAND[0])))
        self.assertEqual(
            first, second,
            "seed %d deals the same hand twice (surface.md §4, ASM-2)"
            % (BLIND_NEW_HAND[0],),
        )
        self.assertNotEqual(
            first,
            S.canon(self.readout(self.new_hand(BLIND_NEW_HAND[1]))),
            "seed %d does not deal what seed %d deals (surface.md §4)"
            % (BLIND_NEW_HAND[1], BLIND_NEW_HAND[0]),
        )

    def test_fam16_02_engine_readout_blind_instance(self):
        """FAM-16.2 readout — instance: the first decision at seed 70571."""
        readout = self.readout(self.new_hand(BLIND_READOUT))
        self.assertEqual(
            set(readout), set(S.READOUT_FACTS),
            "the readout is exactly the ten declared facts (environment.md §2): %r"
            % (readout,),
        )
        self.assertEqual(
            len(S.card_list(readout["hole"], "the readout's hole fact")), 2,
            "the acting seat holds two cards (environment.md §2)",
        )
        self.assertEqual(
            len(S.card_list(readout["board"], "the readout's board fact")), 0,
            "no public card is revealed before the flop (environment.md §2)",
        )
        self.assertEqual(
            readout["history"], [],
            "nothing has happened yet at the first decision (environment.md §2)",
        )

    def test_fam16_03_engine_legal_actions_blind_instance(self):
        """FAM-16.3 legal_actions — instance: the first decision at seed 55049."""
        hand = self.new_hand(BLIND_LEGAL)
        descriptors = S.descriptor_list(self.legal_actions(hand), "legal_actions")
        kinds = [S.descriptor_kind(descriptor) for descriptor in descriptors]
        self.assertEqual(
            kinds, ["fold", "check-call", "raise"],
            "facing the big blind, folding, continuing and raising are legal, in the "
            "vocabulary's order (surface.md §2, §6): seed %d returned %r"
            % (BLIND_LEGAL, descriptors),
        )
        for descriptor in descriptors:
            self.assertIsNotNone(
                self.apply_action(self.new_hand(BLIND_LEGAL), descriptor),
                "every descriptor legal_actions returns is applicable at that decision "
                "(surface.md §6): %r was not" % (descriptor,),
            )

    def test_fam16_04_engine_apply_action_blind_instance(self):
        """FAM-16.4 apply_action — instance: the first action at seed 48017."""
        hand = self.new_hand(BLIND_APPLY)
        before = self.readout(hand)
        action = S.choose_call(before, self.legal_actions(hand))
        advanced = self.apply_action(hand, action)
        after = self.readout(advanced)
        self.assertEqual(
            len(after["history"]), len(before["history"]) + 1,
            "one applied action appends exactly one entry to the public history "
            "(surface.md §7): %r" % (after["history"],),
        )
        self.assertEqual(
            S.canon(self.readout(hand)), S.canon(before),
            "the hand it was given is unchanged (surface.md §7)",
        )

    def test_fam16_05_engine_is_terminal_blind_instance(self):
        """FAM-16.5 is_terminal — instance: a hand at seed 22273 played out."""
        hand = self.new_hand(BLIND_TERMINAL)
        self.assertIsInstance(
            self.is_terminal(hand), bool,
            "is_terminal returns a boolean (surface.md §8)",
        )
        self.assertFalse(
            self.is_terminal(hand), "a fresh hand is not over (surface.md §8)"
        )
        finished = self.finished_hand(BLIND_TERMINAL)
        self.assertTrue(
            self.is_terminal(finished),
            "a hand of this fixed game ends within %d decisions (surface.md §8, ASM-6)"
            % (S.DECISION_BOUND,),
        )

    def test_fam16_06_engine_payoffs_blind_instance(self):
        """FAM-16.6 payoffs — instance: seed 13337 played to the end."""
        payoffs = S.seat_keyed(
            self.payoffs(self.finished_hand(BLIND_PAYOFFS)),
            "the payoffs of seed %d" % (BLIND_PAYOFFS,),
        )
        self.assertEqual(
            len(S.numbers_in(self.payoffs(self.finished_hand(BLIND_PAYOFFS)))), 2,
            "exactly one number per seat and nothing else numeric (surface.md §9)",
        )
        self.assertAlmostEqual(
            float(sum(payoffs.values())), 0.0, places=9,
            msg="the payoffs of a completed hand sum to zero (surface.md §9, ASM-12): %r"
                % (payoffs,),
        )

    def test_fam16_07_engine_play_hand_blind_instance(self):
        """FAM-16.7 play_hand — instance: seed 90917 with an invented policy pair."""

        def seat0_policy(readout, legal):
            """Raises while it is legal, then calls: the battery's own behaviour."""
            return S.choose_raise(readout, legal)

        def seat1_policy(readout, legal):
            """Folds only when the call is three chips or more, otherwise calls."""
            to_call = S.one_number(readout["to_call"], "the readout's to_call fact")
            if to_call >= 3:
                for descriptor in S.descriptor_list(legal, "legal_actions"):
                    if S.descriptor_kind(descriptor) == "fold":
                        return descriptor
            return S.choose_call(readout, legal)

        probe0 = S.PolicyProbe(seat0_policy, name="the blind episode's seat 0")
        probe1 = S.PolicyProbe(seat1_policy, name="the blind episode's seat 1")
        episode = self.play_hand(BLIND_EPISODE, probe0, probe1)
        for fact in S.EPISODE_FACTS:
            S.required(episode, "the episode record of play_hand", fact)
        self.assertEqual(
            S.required(episode, "the episode record of play_hand", "seed"), BLIND_EPISODE,
            "the record carries the seed the call was made with (records.md §5)",
        )
        decisions = S.decision_list(episode)
        self.assertTrue(
            decisions, "the episode records the decisions it took (records.md §5)"
        )
        for position, decision in enumerate(decisions):
            self.assertEqual(
                set(S.decision_fact(decision, "readout")), set(S.READOUT_FACTS),
                "decision %d carries the whole ten-fact readout (environment.md §3)"
                % (position,),
            )
        payoffs = S.seat_keyed(
            S.required(episode, "the episode record of play_hand", "payoffs"),
            "the episode's payoffs",
        )
        self.assertAlmostEqual(
            float(sum(payoffs.values())), 0.0, places=9,
            msg="an episode's payoffs sum to zero (records.md §5, ASM-12): %r" % (payoffs,),
        )

    def test_fam16_08_engine_equity_blind_instance(self):
        """FAM-16.8 equity — instance: 211 samples at seed 81233."""
        hand = self.new_hand(BLIND_EQUITY)
        readout = self.readout(hand)
        value = self.equity(hand, BLIND_EQUITY, BLIND_SAMPLES)
        self.assertTrue(
            S.is_number(value),
            "equity returns a share of the pot (surface.md §11): %r" % (value,),
        )
        self.assertGreaterEqual(float(value), 0.0, "a win probability cannot be negative")
        self.assertLessEqual(float(value), 1.0, "a win probability cannot exceed one")
        self.assertEqual(
            float(value),
            float(self.equity(readout, BLIND_EQUITY, BLIND_SAMPLES)),
            "a hand and its own readout denote the same decision (surface.md §11)",
        )
        self.assertEqual(
            float(value),
            float(self.equity(hand, BLIND_EQUITY, BLIND_SAMPLES)),
            "one decision, seed and sample count give one estimate (surface.md §11)",
        )


if __name__ == "__main__":
    unittest.main()
