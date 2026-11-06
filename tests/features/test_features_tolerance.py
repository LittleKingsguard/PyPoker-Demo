"""FEA-9 -- what the contract does NOT refuse: over-refusing is a defect too.

``docs/L3/features/errors.md`` §4; ``docs/L3/features/flat-numeric.md`` §6;
``docs/L3/features/card-tokens.md`` §7; ``docs/L2/features/surface.md`` §6;
``docs/L1/battery.md`` §3 FAM-2 and §4 (a battery may pass any valid instance, D-15).

Each case here is a value a correct implementation must *accept*: a refusal where
the contract has none fails as loudly as an accepted value the contract refuses.
"""

import os
import sys
import unittest

import numpy

try:  # discovered as part of a tests.features package
    from . import _features_support as S
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _features_support as S  # noqa: E402


class FEA9Tolerance(S.FeaturesCase):
    """The readouts and values the contract deliberately accepts."""

    def test_fea9_1_the_same_card_twice_in_hole_is_carried(self):
        """FEA-9.1 a hole holding one card twice is encoded as two slots: the deal's
        business, not the encoding's (errors.md §4, flat-numeric.md §6,
        card-tokens.md §7)."""
        F = self.surface()
        record = S.readout(hole=("As", "As"))
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                encoder = F.build_encoder(name)
                if name == S.FLAT:
                    values = S.floats(F.encode(encoder, record))
                    self.assert_floats(
                        values[6:23], S.card_slot("As"),
                        "the first hole card slot marks 'As' (flat-numeric.md §3)",
                    )
                    self.assert_floats(
                        values[23:40], S.card_slot("As"),
                        "the second hole card slot marks the same card again: a slot "
                        "carries whatever the deal put there (errors.md §4)",
                    )
                else:
                    values = S.ints(F.encode(encoder, record))
                    self.assert_ints(
                        values[3:5], [52, 52],
                        "two hole tokens, the same id twice (card-tokens.md §7)",
                    )

    def test_fea9_2_the_same_card_twice_on_the_board_is_carried(self):
        """FEA-9.2 a board holding one card twice is encoded slot by slot (errors.md §4,
        flat-numeric.md §6)."""
        F = self.surface()
        record = S.readout(street="flop", board=("Jh", "Jh", "2d"))
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                encoder = F.build_encoder(name)
                if name == S.FLAT:
                    values = S.floats(F.encode(encoder, record))
                    expected = (S.card_slot("Jh") + S.card_slot("Jh") + S.card_slot("2d")
                                + [0.0] * 34)
                    self.assert_floats(values[40:125], expected,
                                       "the board block of a repeated card")
                else:
                    values = S.ints(F.encode(encoder, record))
                    self.assert_ints(
                        values[5:10], [39, 39, 2, 0, 0],
                        "the board tokens of a repeated card (card-tokens.md §3)",
                    )

    def test_fea9_3_a_board_of_one_or_two_cards_is_representable(self):
        """FEA-9.3 a board of one or of two cards is accepted and the slots past it are
        zero or pad: the deal does not produce one, so refusing it would be a refusal the
        contract does not have (errors.md §4, card-tokens.md §7)."""
        F = self.surface()
        for board in (("Jh",), ("Jh", "7c")):
            with self.subTest(board=board):
                record = S.readout(street="flop", board=board)
                flat = S.floats(F.encode(F.build_encoder(S.FLAT), record))
                expected = []
                for card in board:
                    expected.extend(S.card_slot(card))
                expected.extend([0.0] * 17 * (5 - len(board)))
                self.assert_floats(flat[40:125], expected,
                                   "the board block of a %d-card board" % (len(board),))
                tokens = S.ints(F.encode(F.build_encoder(S.TOKENS), record))
                self.assert_ints(
                    tokens[5:10],
                    [S.card_id(card) for card in board] + [S.PAD] * (5 - len(board)),
                    "the board tokens of a %d-card board (card-tokens.md §7)"
                    % (len(board),),
                )

    def test_fea9_4_an_extra_key_in_the_readout_is_ignored(self):
        """FEA-9.4 `legal` and an invented key are ignored and not refused: a key the
        encoding does not carry is not an error (surface.md §6, encoder.md §5,
        errors.md §4)."""
        F = self.surface()
        plain = S.readout(street="flop", history=S.history_entries(2))
        extended = S.with_facts(
            plain,
            extra={"a": 1},
            opponent_hole=("Ah", "Ad"),
            rung="R3",
            seed=7,
        )
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                encoder = F.build_encoder(name)
                if name == S.FLAT:
                    self.assertEqual(
                        S.floats(F.encode(encoder, extended)),
                        S.floats(F.encode(encoder, plain)),
                        "an extra key contributes no slot to a dense observation "
                        "(encoder.md §5 rule 4): %r" % (name,),
                    )
                else:
                    self.assertEqual(
                        S.ints(F.encode(encoder, extended)),
                        S.ints(F.encode(encoder, plain)),
                        "an extra key contributes no token (encoder.md §5 rule 4): %r"
                        % (name,),
                    )

    def test_fea9_5_a_readout_without_legal_is_still_a_readout(self):
        """FEA-9.5 `legal` is not carried, so a readout that lacks it encodes to the same
        observation: the legal set reaches a policy beside the observation (encodings.md
        §2, surface.md §6, errors.md §4)."""
        F = self.surface()
        record = S.readout(street="flop", history=S.history_entries(1))
        without_legal = S.without(record, "legal")
        self.assertNotIn("legal", without_legal,
                         "the battery's own readout really has no `legal` key")
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                encoder = F.build_encoder(name)
                if name == S.FLAT:
                    self.assertEqual(
                        S.floats(F.encode(encoder, without_legal)),
                        S.floats(F.encode(encoder, record)),
                        "a readout without `legal` encodes, and to the same observation "
                        "(encodings.md §2): %r" % (name,),
                    )
                else:
                    self.assertEqual(
                        S.ints(F.encode(encoder, without_legal)),
                        S.ints(F.encode(encoder, record)),
                        "a readout without `legal` encodes, and to the same observation "
                        "(encodings.md §2): %r" % (name,),
                    )

    def test_fea9_6_a_numpy_integer_is_a_chip_count(self):
        """FEA-9.6 a numpy integer where a chip count is expected is accepted and gives
        the same observation as the plain integer: numpy.int64 is an Integral (errors.md
        §4)."""
        F = self.surface()
        plain = S.readout(street="flop", stacks=(7, 13), pot=6, to_call=0, limit=(2, 1))
        numpy_typed = S.with_facts(
            plain,
            stacks=(numpy.int64(7), numpy.int32(13)),
            pot=numpy.int64(6),
            to_call=numpy.int32(0),
            limit=(numpy.int64(2), numpy.int32(1)),
        )
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                encoder = F.build_encoder(name)
                if name == S.FLAT:
                    self.assertEqual(
                        S.floats(F.encode(encoder, numpy_typed)),
                        S.floats(F.encode(encoder, plain)),
                        "a numpy integer is a chip count whatever its class (errors.md "
                        "§4): %r" % (name,),
                    )
                else:
                    self.assertEqual(
                        S.ints(F.encode(encoder, numpy_typed)),
                        S.ints(F.encode(encoder, plain)),
                        "a numpy integer is a chip count whatever its class (errors.md "
                        "§4): %r" % (name,),
                    )

    def test_fea9_7_a_numpy_integer_is_an_action_index(self):
        """FEA-9.7 a numpy integer where an action index is expected is accepted: an index
        is an index whatever its class, and a bool is still not one (errors.md §4,
        vocabulary.md §4)."""
        decode = self.ep("decode_action")
        for index, expected in ((numpy.int64(0), "fold"),
                                (numpy.int32(1), "check-call"),
                                (numpy.int64(2), "raise")):
            with self.subTest(index=index):
                self.assertEqual(
                    decode(index), expected,
                    "numpy.int64(1) is an Integral and decodes as index 1 (errors.md §4, "
                    "vocabulary.md §4): %r -> %r" % (index, decode(index)),
                )

    def test_fea9_8_a_pot_that_does_not_complete_40_is_not_rechecked(self):
        """FEA-9.8 a readout whose pot and stacks do not sum to 40 is still encoded: that
        invariant is the engine's and re-checking it would be a second source of truth
        (flat-numeric.md §6, errors.md §4)."""
        F = self.surface()
        record = S.with_facts(S.readout(), pot=11, stacks=(3, 4))
        self.assertNotEqual(
            record["pot"] + sum(record["stacks"]), 40,
            "the battery's own readout must break the engine's invariant, or this case "
            "cannot fail",
        )
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                observation = F.encode(F.build_encoder(name), record)
                self.assertEqual(
                    self.shape_of(observation), S.DECLARED[name]["shape"],
                    "a readout the engine would not have produced is still a readout this "
                    "module encodes (errors.md §4): %r" % (name,),
                )
                if name == S.FLAT:
                    values = S.floats(observation)
                    self.assert_floats(values[125:127], [3 / 20.0, 4 / 20.0],
                                       "the stacks block of (3, 4)")
                    self.assert_floats(values[127:128], [11 / 40.0], "the pot block of 11")

    def test_fea9_9_any_non_negative_magnitude_is_representable(self):
        """FEA-9.9 every ladder is total over the non-negative integers, so a large amount
        is accepted in both encodings and stays inside the vocabulary (errors.md §4,
        card-tokens.md §4, flat-numeric.md §4)."""
        F = self.surface()
        record = S.readout(street="river", stacks=(500, 0), pot=1000, to_call=999,
                           limit=(9, 7))
        tokens = S.ints(F.encode(F.build_encoder(S.TOKENS), record))
        self.assert_ints(
            tokens[10:12], [84, 77],
            "a stack of 500 is the top bucket and a stack of 0 is the bottom one "
            "(card-tokens.md §4)",
        )
        self.assert_ints(
            tokens[12:16], [76, 68, 88, 92],
            "a pot of 1000, a to_call of 999, a bet size of 9 and 7 raises all have ids "
            "(card-tokens.md §4)",
        )
        flat = S.floats(F.encode(F.build_encoder(S.FLAT), record))
        self.assert_floats(flat[125:131], [500 / 20.0, 0.0, 1000 / 40.0, 999 / 20.0,
                                           9 / 4.0, 7 / 3.0],
                           "the dense encoding divides by its fixed divisors and keeps the "
                           "magnitude (flat-numeric.md §4)")

    def test_fea9_10_one_readout_and_one_encoder_are_reusable(self):
        """FEA-9.10 a readout reused across calls and an encoder held across calls are
        still accepted, and give one observation each time: the module keeps no state and
        holds no cache (errors.md §4, guardrails.md G4).

        The two encodings spell the worked readout's 1 chip to call differently -- 0.05 in
        the dense slot, the id 62 in the token -- so a case that compared only the two
        arrays' lengths or shapes would not see the fact at all (flat-numeric.md §4,
        card-tokens.md §4).
        """
        F = self.surface()
        record = S.readout(street="turn", to_call=1, history=S.history_entries(4))
        encoders = {name: F.build_encoder(name) for name in S.ENCODINGS}
        first = {name: S.floats(F.encode(encoder, record))
                 for name, encoder in encoders.items()}
        for _repeat in range(3):
            for name, encoder in encoders.items():
                with self.subTest(encoding=name, repeat=_repeat):
                    self.assertEqual(
                        S.floats(F.encode(encoder, record)), first[name],
                        "an encoder held and a readout reused still give one observation "
                        "(errors.md §4): %r" % (name,),
                    )
        flat_values = first[S.FLAT]
        token_values = first[S.TOKENS]
        self.assertAlmostEqual(
            flat_values[128], 0.05, delta=1e-5,
            msg="the dense encoding carries the one chip to call as its amount over 20, "
                "0.05, and keeps the magnitude (flat-numeric.md §4): %r"
                % (flat_values[128],),
        )
        self.assertEqual(
            token_values[13], 62,
            "the token encoding carries the same one chip to call as the id 62, and no "
            "amount at all (card-tokens.md §4): %r" % (token_values[13],),
        )
        self.assertNotEqual(
            flat_values[128], token_values[13],
            "the two encodings spell the worked readout's to_call differently -- 0.05 in "
            "the dense slot, the id 62 in the token -- so one readout's two observations "
            "differ where the fact is, and a case that compared only their lengths would "
            "not see it (encodings.md §1, §3-§4): %r vs %r"
            % (flat_values[128], token_values[13]),
        )


if __name__ == "__main__":
    unittest.main()
