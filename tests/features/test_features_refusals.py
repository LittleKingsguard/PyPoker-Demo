"""FEA-8 -- every refusal the contract has, each naming what it refused.

``docs/L2/features/surface.md`` §1, §4-§9; ``docs/L3/features/errors.md`` §1-§4;
``docs/L3/features/flat-numeric.md`` §6; ``docs/L3/features/card-tokens.md`` §7;
``docs/L3/features/vocabulary.md`` §3, §5; ``docs/L3/features/guardrails.md`` G8, G9.

No case asserts an exception *class*: the classes are this module's freedom and are
not surface (``errors.md`` §2).  Each case asserts that the call raises, that the
message names the entry point, the argument or field, and -- where ``errors.md`` §3
prints it -- the offending value.
"""

import os
import sys
import unittest

try:  # discovered as part of a tests.features package
    from . import _features_support as S
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _features_support as S  # noqa: E402


class FEA8BuildEncoder(S.FeaturesCase):
    """`build_encoder` refuses a name that is not one of the two declared encodings."""

    def test_fea8_1_an_unknown_name_is_refused_with_that_name(self):
        """FEA-8.1 build_encoder refuses a name that is not a declared encoding, with the
        name in the message (surface.md §4, encoder.md §2, errors.md §3)."""
        build = self.ep("build_encoder")
        for name in ("flat", "numeric", "card-token", "tokens", "R3", "raise"):
            with self.subTest(name=name):
                self.refuses(build, name, words=("build_encoder", name))

    def test_fea8_2_a_value_that_is_not_a_string_is_refused(self):
        """FEA-8.2 build_encoder refuses a name that is not a str: a representation is
        named by the ladder's own spelling (encoder.md §2, surface.md §1)."""
        build = self.ep("build_encoder")
        for value in (None, 0, ("flat-numeric",), b"flat-numeric", [S.FLAT]):
            with self.subTest(value=value):
                self.refuses(build, value, words=("build_encoder", "name"))

    def test_fea8_3_the_name_is_matched_exactly_case_sensitively_and_not_stripped(self):
        """FEA-8.3 a differently-cased, padded or underscored spelling is a different
        thing and is refused (encoder.md §2, guardrails.md G2)."""
        build = self.ep("build_encoder")
        for variant in (
            "Flat-Numeric",
            "FLAT-NUMERIC",
            "card-Tokens",
            " flat-numeric",
            "flat-numeric ",
            "flat_numeric",
            "card_tokens",
            "flatnumeric",
        ):
            with self.subTest(name=variant):
                self.refuses(build, variant, words=("build_encoder", variant))


class FEA8EncoderArgument(S.FeaturesCase):
    """`observation_spec` and `encode` refuse a value that is not an encoder."""

    def test_fea8_4_observation_spec_refuses_a_non_encoder(self):
        """FEA-8.4 observation_spec refuses anything that is not an encoder this module
        built, naming the argument (surface.md §5, encoder.md §3, guardrails.md G2)."""
        F = self.surface()
        spec = F.observation_spec(F.build_encoder(S.FLAT))
        for value in (None, spec, dict(spec), S.FLAT, S.TOKENS, 0, (S.FLAT,)):
            with self.subTest(value=value):
                self.refuses(
                    F.observation_spec, value,
                    words=("observation_spec", "encoder"),
                )

    def test_fea8_5_encode_refuses_a_non_encoder(self):
        """FEA-8.5 encode refuses anything that is not an encoder this module built: the
        encoder is opaque and exists only by a declared encoding (surface.md §4, §6;
        encoder.md §1, §5)."""
        F = self.surface()
        spec = F.observation_spec(F.build_encoder(S.TOKENS))
        record = S.readout()
        for value in (None, spec, S.FLAT, S.TOKENS, 0, record):
            with self.subTest(value=type(value).__name__):
                self.refuses(
                    F.encode, value, record,
                    words=("encode", "encoder"),
                )


class FEA8ReadoutShape(S.FeaturesCase):
    """`encode` refuses a value that is not a readout, and a readout missing a carried field."""

    def test_fea8_6_a_readout_that_is_not_a_mapping_is_refused(self):
        """FEA-8.6 encode refuses a readout that is not a mapping, naming the readout
        (surface.md §6, errors.md §3)."""
        F = self.surface()
        encoder = F.build_encoder(S.FLAT)
        for value in ([], [("street", "preflop")], (), "preflop", None, 0):
            with self.subTest(value=value):
                self.refuses(F.encode, encoder, value, words=("encode", "readout"))

    def test_fea8_7_a_missing_carried_field_is_refused_by_name(self):
        """FEA-8.7 a readout missing any one of the nine carried facts is refused with that
        field named, and none is defaulted (surface.md §6, encoder.md §5, guardrails.md G9,
        FAM-2.4)."""
        F = self.surface()
        record = S.readout(street="flop", history=S.history_entries(2))
        for name in S.ENCODINGS:
            encoder = F.build_encoder(name)
            for field in S.FIELDS:
                with self.subTest(encoding=name, missing=field):
                    self.refuses(
                        F.encode, encoder, S.without(record, field),
                        words=("encode", field),
                    )


class FEA8Unrepresentable(S.FeaturesCase):
    """`encode` refuses a carried value the declared encoding cannot spell."""

    def _refused(self, surface, field, value, words):
        """Encode a valid readout with one fact replaced, in both encodings.

        The caller fetches the surface before the loop, so an absent package is one
        clean failure of the case rather than one per subTest.
        """
        record = S.with_facts(S.readout(street="flop"), **{field: value})
        for name in S.ENCODINGS:
            with self.subTest(encoding=name, field=field, value=value):
                self.refuses(
                    surface.encode, surface.build_encoder(name), record,
                    words=("encode", field) + tuple(words),
                )

    def test_fea8_8_a_street_outside_the_four_is_refused(self):
        """FEA-8.8 a street outside preflop/flop/turn/river is refused with the street in
        the message (flat-numeric.md §6, card-tokens.md §7, errors.md §3)."""
        F = self.surface()
        for street in ("pre-flop", "Preflop", "showdown", "flop "):
            with self.subTest(street=street):
                self._refused(F, "street", street, ("street", street))

    def test_fea8_9_a_seat_with_another_index_or_a_non_bool_flag_is_refused(self):
        """FEA-8.9 a seat that is not (index in 0,1; a real bool flag) is refused: the
        readout's seat type admits exactly four values (flat-numeric.md §6,
        card-tokens.md §7)."""
        F = self.surface()
        for value in ((2, True), (-1, False), (0, 1), (0, 0), (0, "yes"), 0, (0,), (0, True, False)):
            with self.subTest(seat=value):
                self._refused(F, "seat", value, ("seat",))

    def test_fea8_10_a_hole_that_is_not_two_cards_is_refused(self):
        """FEA-8.10 a hole that is not exactly two cards is refused (flat-numeric.md §6,
        card-tokens.md §7, errors.md §3)."""
        F = self.surface()
        for value in (("Td",), ("Td", "2c", "As"), "Td2c", 5):
            with self.subTest(hole=value):
                self._refused(F, "hole", value, ("hole",))

    def test_fea8_11_a_card_spelled_badly_is_refused(self):
        """FEA-8.11 a card whose spelling is not a rank from '23456789TJQKA' followed by a
        suit from 'cdhs' is refused, naming the card (flat-numeric.md §3, §6;
        card-tokens.md §7; errors.md §3, guardrail G9)."""
        F = self.surface()
        for card in ("Tz", "tD", "10d", "dT", "A", "", 2):
            with self.subTest(card=card):
                record = S.with_facts(S.readout(), hole=(card, "2c"))
                for name in S.ENCODINGS:
                    with self.subTest(card=card, encoding=name):
                        words = ("encode", "card")
                        if isinstance(card, str) and card:
                            words = words + (card,)
                        self.refuses(
                            F.encode, F.build_encoder(name), record, words=words,
                        )

    def test_fea8_12_a_board_longer_than_five_cards_is_refused(self):
        """FEA-8.12 a board longer than five cards is refused, and a badly spelled card on
        the board is refused by the same card rule (flat-numeric.md §6,
        card-tokens.md §7, errors.md §3)."""
        F = self.surface()
        self._refused(
            F, "board", ("Jh", "7c", "2d", "Ks", "3h", "9s"), ("board",),
        )
        record = S.with_facts(S.readout(street="flop"), board=("Jh", "Tz", "2d"))
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                self.refuses(
                    F.encode, F.build_encoder(name), record,
                    words=("encode", "card", "Tz"),
                )

    def test_fea8_13_a_negative_or_non_integer_pot_is_refused(self):
        """FEA-8.13 a pot that is not a non-negative integer is refused, and a bool is not
        a chip count (errors.md §3, §4; flat-numeric.md §6)."""
        F = self.surface()
        for value in (-3, 3.5, 3.0, True, "3", None):
            with self.subTest(pot=value):
                self._refused(F, "pot", value, ("pot",))

    def test_fea8_14_a_negative_or_non_integer_to_call_is_refused(self):
        """FEA-8.14 a to_call that is not a non-negative integer is refused: no ladder has
        a bucket below zero (errors.md §4, card-tokens.md §7)."""
        F = self.surface()
        for value in (-1, 1.5, 1.0, True, "1"):
            with self.subTest(to_call=value):
                self._refused(F, "to_call", value, ("to_call",))

    def test_fea8_15_a_negative_or_non_integer_stack_is_refused(self):
        """FEA-8.15 a stacks entry that is not a non-negative integer is refused, and the
        message prints the pair it saw (flat-numeric.md §6, errors.md §3)."""
        F = self.surface()
        for value in ((19, -1), (19.0, 18), (True, 18), (19,), ("19", 18)):
            with self.subTest(stacks=value):
                self._refused(F, "stacks", value, ("stacks",))

    def test_fea8_16_a_limit_that_is_not_two_integers_is_refused(self):
        """FEA-8.16 a limit that is not two non-negative integers is refused (errors.md §3,
        flat-numeric.md §6)."""
        F = self.surface()
        for value in ((2,), (2, 0, 1), ("2", 0), (2.0, 0), (2, -1), (True, 0)):
            with self.subTest(limit=value):
                self._refused(F, "limit", value, ("limit",))


class FEA8LegalIndices(S.FeaturesCase):
    """`legal_indices` refuses an empty list, a non-sequence, and an unknown descriptor."""

    def test_fea8_17_an_empty_sequence_is_refused(self):
        """FEA-8.17 an empty sequence is refused: a live decision always has at least one
        legal action (surface.md §8, vocabulary.md §3, errors.md §3)."""
        legal_indices = self.ep("legal_indices")
        for value in ((), [], () + tuple()):
            with self.subTest(value=value):
                self.refuses(
                    legal_indices, value,
                    words=("legal_indices", "action"),
                )

    def test_fea8_18_a_value_that_is_not_a_sequence_of_descriptors_is_refused(self):
        """FEA-8.18 a str, a set, a mapping and a bare descriptor are not sequences of
        descriptors and are refused (vocabulary.md §3, guardrails.md G7)."""
        legal_indices = self.ep("legal_indices")
        for value in ("fold", "foldcheck-call", {"fold"}, frozenset({"raise"}),
                      {"fold": 0}, {"fold", "raise"}, None, 0, iter(("fold",))):
            with self.subTest(value=value):
                self.refuses(
                    legal_indices, value,
                    words=("legal_indices",),
                )

    def test_fea8_19_a_descriptor_outside_the_three_is_refused_with_it(self):
        """FEA-8.19 a descriptor outside the three-index vocabulary is refused with that
        descriptor named, and no fold is substituted for it (surface.md §8,
        vocabulary.md §3, guardrails.md G7)."""
        legal_indices = self.ep("legal_indices")
        for descriptor in ("call", "Fold", "check", "bet", "raise-to-4", "", 0, 1, 2):
            with self.subTest(descriptor=descriptor):
                words = ("legal_indices",)
                if isinstance(descriptor, str) and descriptor:
                    words = words + (descriptor,)
                self.refuses(
                    legal_indices, ("fold", descriptor), words=words,
                )


class FEA8DecodeAction(S.FeaturesCase):
    """`decode_action` refuses an index outside {0, 1, 2} and a value that is not an index."""

    def test_fea8_20_an_index_outside_the_three_is_refused(self):
        """FEA-8.20 decode_action refuses -1, 3 and everything beyond, naming the index
        (surface.md §9, vocabulary.md §4, guardrails.md G8)."""
        decode = self.ep("decode_action")
        for index in (3, -1, 4, 100, -100):
            with self.subTest(index=index):
                self.refuses(decode, index, words=("decode_action", str(index)))

    def test_fea8_21_a_value_that_is_not_an_integer_is_refused(self):
        """FEA-8.21 decode_action refuses a str, a float, None and a bool: it never
        coerces, and a flag is not an index (vocabulary.md §4, errors.md §4,
        guardrails.md G8)."""
        decode = self.ep("decode_action")
        for value in ("1", "0", 1.0, 0.0, None, True, False, (1,), [1]):
            with self.subTest(value=value):
                self.refuses(decode, value, words=("decode_action",))


class FEA8ThirdSeatCount(S.FeaturesCase):
    """The third row's seat count bounds both per-seat facts, and the two rows stay two."""

    def test_fea8_34_a_seat_index_outside_the_shapes_seat_count_is_refused(self):
        """FEA-8.34 the seat block's index is bounded by the **shape's** own seat count, which
        the block's params carry: a six-seat encoder accepts exactly the six indices 0-5
        with a real bool flag, refuses (6, True) and (-1, False) naming `seat`, while the
        two-seat rows refuse (2, True) -- the value the six-seat row accepts -- so no
        readout's seat is in one shape's range and another's by accident (seats.md §3,
        flat-numeric.md §4, §6, card-tokens.md §3, §7, ASM-44)."""
        F = self.surface()
        six = F.build_encoder(S.FLAT, shape=S.THIRD_SHAPE)
        for index in range(S.SEATS[S.THIRD_SHAPE]):
            for flag in (True, False):
                with self.subTest(shape=S.THIRD_SHAPE, seat=(index, flag), accepted=True):
                    record = S.six_seat_readout(seat=(index, flag))
                    for name in S.ENCODINGS:
                        with self.subTest(shape=S.THIRD_SHAPE, seat=(index, flag),
                                          encoding=name, accepted=True):
                            F.encode(F.build_encoder(name, shape=S.THIRD_SHAPE), record)
        for value in ((S.SEATS[S.THIRD_SHAPE], True), (-1, False),
                      (S.SEATS[S.THIRD_SHAPE], False), (99, True)):
            with self.subTest(shape=S.THIRD_SHAPE, seat=value, accepted=False):
                for name in S.ENCODINGS:
                    with self.subTest(shape=S.THIRD_SHAPE, seat=value, encoding=name):
                        self.refuses(
                            F.encode, F.build_encoder(name, shape=S.THIRD_SHAPE),
                            S.six_seat_readout(seat=value),
                            words=("encode", "seat"),
                        )
        for shape in S.SHAPES:
            with self.subTest(shape=shape, seat=(2, True), accepted=False):
                for name in S.ENCODINGS:
                    with self.subTest(shape=shape, seat=(2, True), encoding=name):
                        self.refuses(
                            F.encode, F.build_encoder(name, shape=shape),
                            S.readout(seat=(2, True)),
                            words=("encode", "seat"),
                        )
        self.assertEqual(
            S.SEATS[S.THIRD_SHAPE], 6,
            "the six-seat row's seat count is 6, so its index range is 0-5 and the "
            "two-seat rows' 0-1 is theirs alone (seats.md §2-§3, ASM-44): %r"
            % (S.SEATS[S.THIRD_SHAPE],),
        )
        self.assertEqual(
            (S.SEATS[S.DEFAULT_SHAPE], S.SEATS[S.SECOND_SHAPE]), (2, 2),
            "the two two-seat rows keep exactly the four seat values they always carried "
            "(seats.md §3, ASM-44): %r"
            % ((S.SEATS[S.DEFAULT_SHAPE], S.SEATS[S.SECOND_SHAPE]),),
        )
        self.assertIsNotNone(
            six,
            "an encoder built for the six-seat row is one of this module's encoders "
            "(surface.md §4): %r" % (six,),
        )

    def test_fea8_35_a_stacks_that_is_not_one_count_per_seat_is_refused(self):
        """FEA-8.35 the stacks block's length is the shape's seat count: the six-seat row
        refuses a two-entry stacks and the two-seat rows refuse a six-entry one, each
        naming `stacks` and the count it declares, so a readout's stacks are one per seat
        on every row and no block defaults a missing seat (seats.md §3, flat-numeric.md
        §4, §6, card-tokens.md §4, §7, errors.md §3, ASM-44)."""
        F = self.surface()
        short = tuple(S.SIX_SEAT_STACKS[:2])
        long = tuple(range(S.SEATS[S.THIRD_SHAPE]))
        self.assertEqual(
            (len(short), len(long)),
            (2, 6),
            "the battery holds one stacks shorter and one longer than the row's seat "
            "count (seats.md §3, ASM-44): %r, %r" % (short, long),
        )
        for name in S.ENCODINGS:
            with self.subTest(shape=S.THIRD_SHAPE, stacks=short):
                self.refuses(
                    F.encode, F.build_encoder(name, shape=S.THIRD_SHAPE),
                    S.six_seat_readout(stacks=short),
                    words=("encode", "stacks"),
                )
            with self.subTest(shape=S.THIRD_SHAPE, stacks=long, encoding=name):
                F.encode(F.build_encoder(name, shape=S.THIRD_SHAPE),
                         S.six_seat_readout(stacks=long))
        for shape in S.SHAPES:
            for name in S.ENCODINGS:
                with self.subTest(shape=shape, stacks=long, encoding=name):
                    self.refuses(
                        F.encode, F.build_encoder(name, shape=shape),
                        S.readout(stacks=long),
                        words=("encode", "stacks"),
                    )
                with self.subTest(shape=shape, stacks=long[:2], encoding=name):
                    F.encode(F.build_encoder(name, shape=shape),
                             S.readout(stacks=long[:2]))


if __name__ == "__main__":
    unittest.main()
