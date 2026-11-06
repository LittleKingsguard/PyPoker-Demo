"""FEA-1 -- the declared surface of `features`, and its one-design shape.

``docs/L2/features/surface.md`` §1, §3-§9; ``docs/L3/features/layout.md`` §2;
``docs/L3/features/README.md`` §3; ``docs/L3/features/guardrails.md`` G1, G14;
``docs/L1/battery.md`` §3 FAM-1; D-12, D-3.

Every case here is red against absent code, which is the expected state of a
design-stage battery (``docs/L1/battery.md`` §1): the plumbing in
``_features_support`` turns "``src/features/`` is not there yet" into one clear
failure per case and never into a collection error.
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


class FEA1Surface(S.FeaturesCase):
    """The seven names exist, are callable, and take their declared arguments."""

    def test_fea1_1_the_seven_names_exist_and_are_callable(self):
        """FEA-1.1 the seven declared names are module-level callables of `features`
        (surface.md §1, layout.md §2, battery.md §3 FAM-1, D-12)."""
        surface = self.surface()
        for name in S.NINE:
            with self.subTest(name=name):
                self.assertTrue(
                    callable(getattr(surface, name)),
                    "features.%s must be a callable module-level name (surface.md §1, "
                    "layout.md §2)" % (name,),
                )

    def test_fea1_2_all_declares_exactly_the_seven_names_in_order(self):
        """FEA-1.2 `features.__all__` is exactly the seven names, in the declared order,
        with no eighth name (layout.md §2, guardrails.md G14, D-12)."""
        declared = S.all_names()
        self.assertEqual(
            declared, S.NINE,
            "features.__all__ must be exactly the seven entry points, in the order "
            "layout.md §2 declares them (guardrail G14): %r" % (declared,),
        )
        self.assertEqual(
            len(declared), 7,
            "an eighth name in __all__ is a second surface no L2 document declares "
            "(guardrails.md G14, D-12): %r" % (declared,),
        )
        for name in declared:
            with self.subTest(name=name):
                self.assertTrue(
                    callable(self.ep(name)),
                    "every name __all__ declares is a callable entry point "
                    "(layout.md §2): %r" % (name,),
                )

    def test_fea1_3_decode_action_of_one_returns_a_descriptor(self):
        """FEA-1.3 decode_action(1) is not None and is one of the three declared
        descriptors (surface.md §9, battery.md §3 FAM-1 case FAM-1.16)."""
        descriptor = self.decode(1)
        self.assertIsNotNone(
            descriptor,
            "features.decode_action(1) returned nothing (battery.md §3 FAM-1.16)",
        )
        self.assertEqual(
            descriptor, S.ACTIONS[1],
            "decode_action(1) is the shared spelling's second descriptor, 'check-call' "
            "(vocabulary.md §1, §4): %r" % (descriptor,),
        )

    def test_fea1_4_each_name_accepts_its_declared_arguments(self):
        """FEA-1.4 each of the seven names succeeds when it is called with exactly its
        declared arguments, and returns the declared kind (surface.md §3-§9)."""
        F = self.surface()
        record = S.readout()
        declared = F.encodings()
        self.assertTrue(
            S.is_mapping(declared),
            "encodings() returns a mapping keyed by the two encoding names "
            "(surface.md §3): %r" % (declared,),
        )
        self.assertEqual(len(declared), 2, "encodings() declares two encodings")
        encoder = F.build_encoder(S.FLAT)
        self.assertIsNotNone(
            encoder,
            "build_encoder('flat-numeric') returns an encoder (surface.md §4)",
        )
        self.assertTrue(
            S.is_mapping(F.observation_spec(encoder)),
            "observation_spec(encoder) returns the six-key spec record (surface.md §5)",
        )
        observation = F.encode(encoder, record)
        self.assertIsNotNone(
            observation,
            "encode(encoder, readout) returns one observation (surface.md §6)",
        )
        space = F.action_space()
        self.assertTrue(
            S.is_mapping(space),
            "action_space() returns a mapping keyed 0, 1, 2 (surface.md §7): %r" % (space,),
        )
        indices = F.legal_indices(S.ACTIONS)
        self.assertEqual(
            tuple(indices), (0, 1, 2),
            "legal_indices(descriptors) returns the descriptors' indices (surface.md §8)",
        )
        self.assertIsInstance(
            F.decode_action(0), str,
            "decode_action(index) returns one descriptor, a plain str (surface.md §9)",
        )

    def test_fea1_5_a_missing_declared_argument_is_a_type_error(self):
        """FEA-1.5 a call that omits a declared argument is Python's own TypeError from
        the call and never a substituted default (surface.md §1, §4-§9)."""
        F = self.surface()
        record = S.readout()
        encoder = F.build_encoder(S.FLAT)
        for label, fn, args in (
            ("build_encoder(name)", F.build_encoder, ()),
            ("observation_spec(encoder)", F.observation_spec, ()),
            ("encode(encoder, readout)", F.encode, (encoder,)),
            ("encode(encoder, readout)", F.encode, (record,)),
            ("legal_indices(legal_actions)", F.legal_indices, ()),
            ("decode_action(index)", F.decode_action, ()),
        ):
            with self.subTest(call=label, supplied=args):
                with self.assertRaises(TypeError):
                    fn(*args)

    def test_fea1_6_an_extra_argument_is_a_type_error(self):
        """FEA-1.6 each of the five names that take arguments refuses a caller-supplied
        extra one with Python's TypeError: the arity is the declared one (surface.md
        §1, §4-§9)."""
        F = self.surface()
        encoder = F.build_encoder(S.FLAT)
        record = S.readout()
        for label, fn, args in (
            ("build_encoder(name)", F.build_encoder, (S.FLAT, S.TOKENS)),
            ("observation_spec(encoder)", F.observation_spec, (encoder, encoder)),
            ("encode(encoder, readout)", F.encode, (encoder, record, record)),
            ("legal_indices(legal_actions)", F.legal_indices, (S.ACTIONS, S.ACTIONS)),
            ("decode_action(index)", F.decode_action, (0, 1)),
        ):
            with self.subTest(call=label, supplied=args):
                with self.assertRaises(TypeError):
                    fn(*args)

    def test_fea1_7_the_two_encodings_agree_about_the_same_facts(self):
        """FEA-1.7 one worked readout, encoded by both encoders, gives two observations
        that agree about the same nine facts: the dense street's hot index is the street
        token minus 53; the dense seat's two slots are the two seat tokens minus 57 and
        59; the dense history's live slots correspond one to one with the non-pad history
        tokens, with hot index = token - 93; the pot read back out of the dense slot falls
        in the bucket the pot token names; and the dense to_call slot is 0.0 exactly when
        the to_call token is 61 (README.md §5 rule 2, guardrails.md G1, encodings.md §2,
        flat-numeric.md §4-§5, card-tokens.md §3-§5, D-3).

        This is the discriminating form of "one design, two encodings": an implementation
        that forked the two encodings and let them drift fails at least one of the five
        agreements, where a scan of ``__all__``'s names could never see it.
        """
        F = self.surface()
        flat_encoder = F.build_encoder(S.FLAT)
        token_encoder = F.build_encoder(S.TOKENS)
        flat_width = S.DECLARED[S.FLAT]["shape"][0]
        token_width = S.DECLARED[S.TOKENS]["shape"][0]
        # The history block is the observation's last block in both encodings, and the
        # arithmetic below reads its offset from the array's own length.
        flat_history = flat_width - S.HISTORY_SLOTS * S.HISTORY_SLOT_WIDTH
        token_history = token_width - S.HISTORY_SLOTS

        def offset_of(table, index):
            """A block's offset, summed from the design's own widths/counts."""
            return sum(entry[2] for entry in table[:index])

        # 1. the street: the one-hot's live slot and the street token name one street.
        for street in S.STREETS:
            with self.subTest(fact="street", street=street):
                flat = S.floats(F.encode(flat_encoder, S.readout(street=street)))
                tokens = S.ints(F.encode(token_encoder, S.readout(street=street)))
                hot = [index for index, value in enumerate(flat[0:4]) if value == 1.0]
                self.assertEqual(
                    len(hot), 1,
                    "the dense street block is a one-hot (flat-numeric.md §2): %r"
                    % (flat[0:4],),
                )
                self.assertEqual(
                    hot[0], tokens[0] - S.STREET_IDS["preflop"],
                    "the dense street's hot index is the street token minus 53: the two "
                    "encodings name the same street (encodings.md §2, card-tokens.md §3): "
                    "hot index %r, token %r" % (hot[0], tokens[0]),
                )

        # 2. the seat: the two slots are the two seat tokens, offset by their bases.
        for seat in ((0, True), (0, False), (1, True), (1, False)):
            with self.subTest(fact="seat", seat=seat):
                record = S.readout(seat=seat, to_call=0)
                flat = S.floats(F.encode(flat_encoder, record))
                tokens = S.ints(F.encode(token_encoder, record))
                self.assertEqual(
                    flat[4], tokens[1] - S.SEAT_INDEX_BASE,
                    "the dense seat block's first slot is the seat token minus 57: seat "
                    "%r is one seat in both encodings (flat-numeric.md §4, "
                    "card-tokens.md §3): %r vs %r" % (seat, flat[4], tokens[1]),
                )
                self.assertEqual(
                    flat[5], 1.0 if tokens[2] == S.SEAT_FLAG_BASE + 1 else 0.0,
                    "the dense seat block's second slot is 1.0 exactly when the button "
                    "token is 60: seat %r carries one button flag, spelled twice "
                    "(flat-numeric.md §4, card-tokens.md §3): %r vs %r"
                    % (seat, flat[5], tokens[2]),
                )

        # 3. the history: the same entries, live slot for live token.
        history = list(S.UNSORTED_HISTORY)
        record = S.readout(street="turn", to_call=0, history=history)
        flat = S.floats(F.encode(flat_encoder, record))
        tokens = S.ints(F.encode(token_encoder, record))
        live_dense = [
            position for position in range(S.HISTORY_SLOTS)
            if any(value != 0.0 for value in
                   flat[flat_history + S.HISTORY_SLOT_WIDTH * position:
                        flat_history + S.HISTORY_SLOT_WIDTH * (position + 1)])
        ]
        live_tokens = [
            position for position in range(S.HISTORY_SLOTS)
            if tokens[token_history + position] != S.PAD
        ]
        self.assertEqual(
            live_dense, live_tokens,
            "the dense history's live slots and the history's non-pad tokens are the same "
            "applied actions in the same order (flat-numeric.md §5, card-tokens.md §5): "
            "%r vs %r" % (live_dense, live_tokens),
        )
        self.assertEqual(
            len(live_dense), len(history),
            "one live slot per applied action, in both encodings (flat-numeric.md §5): %r "
            "entries, %r live slots" % (len(history), len(live_dense)),
        )
        for position in live_dense:
            with self.subTest(fact="history", position=position):
                slot = flat[flat_history + S.HISTORY_SLOT_WIDTH * position:
                            flat_history + S.HISTORY_SLOT_WIDTH * (position + 1)]
                hot = [index for index, value in enumerate(slot) if value != 0.0]
                self.assertEqual(
                    len(hot), 1,
                    "a live history slot is a one-hot over the action kinds "
                    "(flat-numeric.md §5): %r" % (slot,),
                )
                self.assertEqual(
                    hot[0], tokens[token_history + position] - S.HISTORY_IDS["fold"],
                    "the dense slot's hot index is the history token minus 93: the two "
                    "encodings read one entry as one action (flat-numeric.md §5, "
                    "card-tokens.md §5): hot index %r, token %r"
                    % (hot[0], tokens[token_history + position]),
                )

        # 4. the pot: the dense magnitude, read back through its own normaliser, names the
        # same bucket the pot token does -- over values that cross every ladder edge.
        flat_pot_slot = offset_of(S.FLAT_BLOCKS, 5)
        token_pot_slot = offset_of(S.TOKEN_BLOCKS, 5)
        pots = (0, 3, 4, 6, 9, 13, 17, 25, 33)
        flat_pots = [S.floats(F.encode(flat_encoder, S.readout(pot=pot)))[flat_pot_slot]
                     for pot in pots]
        token_pots = [S.ints(F.encode(token_encoder, S.readout(pot=pot)))[token_pot_slot]
                      for pot in pots]
        self.assertEqual(
            flat_pots, sorted(set(flat_pots)),
            "the dense pot slot increases with the pot, so it can be read back as a "
            "magnitude (flat-numeric.md §4): %r" % (flat_pots,),
        )
        self.assertEqual(
            token_pots, sorted(token_pots),
            "the pot token's id is monotone in the pot, as its ladder is "
            "(card-tokens.md §4): %r" % (token_pots,),
        )
        for position, pot in enumerate(pots):
            with self.subTest(fact="pot", pot=pot):
                self.assertEqual(
                    token_pots[position],
                    S.bucket("pot", round(flat_pots[position] * 40)),
                    "the pot the dense slot spells, read back through its own divisor of "
                    "40, falls in the bucket the pot token names: a dense slot and a token "
                    "that disagreed about the pot are two facts, not one "
                    "(flat-numeric.md §4, card-tokens.md §4): pot %r, dense %r, token %r"
                    % (pot, flat_pots[position], token_pots[position]),
                )
                if position:
                    if token_pots[position] > token_pots[position - 1]:
                        self.assertGreater(
                            flat_pots[position], flat_pots[position - 1],
                            "whenever the pot bucket id increases, the dense pot slot "
                            "increases too (flat-numeric.md §4, card-tokens.md §4): pot %r"
                            % (pot,),
                        )

        # 5. to_call: the dense zero and the zero amount's own id 61 are the same state, and
        # the amount the dense slot spells names the bucket the token carries.
        flat_to_call_slot = offset_of(S.FLAT_BLOCKS, 6)
        token_to_call_slot = offset_of(S.TOKEN_BLOCKS, 6)
        zero_id = S.bucket("to_call", 0)
        for to_call in (0, 1, 2, 5, 11):
            with self.subTest(fact="to_call", to_call=to_call):
                dense = S.floats(F.encode(flat_encoder, S.readout(to_call=to_call)))[
                    flat_to_call_slot]
                token = S.ints(F.encode(token_encoder, S.readout(to_call=to_call)))[
                    token_to_call_slot]
                self.assertEqual(
                    dense == 0.0, token == zero_id,
                    "the dense to_call slot is 0.0 exactly when the to_call token is 61: "
                    "'nothing to call' is one state in both encodings "
                    "(flat-numeric.md §4, card-tokens.md §4, guardrails.md G10): to_call "
                    "%r, dense %r, token %r" % (to_call, dense, token),
                )
                self.assertEqual(
                    token, S.bucket("to_call", round(dense * 20)),
                    "the amount to call the dense slot spells, read back through its own "
                    "divisor of 20, falls in the bucket the to_call token names: a dense "
                    "slot and a token that disagreed about the amount to call are two "
                    "facts, not one (flat-numeric.md §4, card-tokens.md §4): to_call %r, "
                    "dense %r, token %r" % (to_call, dense, token),
                )

    def test_fea1_8_one_encode_serves_both_encoders(self):
        """FEA-1.8 one encode, one legal_indices, one decode_action: the same single
        `features.encode` object is what the battery passes BOTH encoders to, and each
        encoding comes back as an observation of its own declared shape and dtype, with the
        same one `legal_indices` and one `decode_action` serving the vocabulary
        (README.md §5 rule 2, layout.md §2, guardrails.md G1).

        This case holds the arity claim only -- one entry point per step; the
        cross-encoding agreement of the same facts is FEA-1.7's case.
        """
        F = self.surface()
        record = S.readout()
        encode = F.encode
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                observation = encode(F.build_encoder(name), record)
                self.assertEqual(
                    self.shape_of(observation), S.DECLARED[name]["shape"],
                    "the one encode writes %r's declared shape (encodings.md §3-§4, "
                    "FAM-2.8): %r" % (name, self.shape_of(observation)),
                )
                self.assertEqual(
                    str(getattr(observation, "dtype", None)), S.DECLARED[name]["dtype"],
                    "the one encode writes %r's declared dtype, because the encoder's own "
                    "row of the declaration table drives it (encodings.md §3-§4): %r"
                    % (name, getattr(observation, "dtype", None)),
                )
        self.assertEqual(
            tuple(F.legal_indices(S.ACTIONS)), (0, 1, 2),
            "one legal_indices serves both encodings: the action vocabulary is not a "
            "representation (vocabulary.md §1, D-2)",
        )
        self.assertEqual(
            F.decode_action(2), S.ACTIONS[2],
            "one decode_action serves both encodings (vocabulary.md §4, D-2)",
        )


if __name__ == "__main__":
    unittest.main()
