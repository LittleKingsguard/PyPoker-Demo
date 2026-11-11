"""FEA-6 -- the history: four grammars, one slot per applied action, oldest first.

``docs/L3/features/flat-numeric.md`` §5; ``docs/L3/features/card-tokens.md`` §5;
``docs/L3/features/README.md`` §4 (ASM-E2); ``docs/L3/features/errors.md`` §3-§4;
``docs/L3/features/guardrails.md`` G13; ``docs/L2/features/encodings.md`` §3;
``docs/L1/shapes.md`` §8 and ``docs/L1/assumptions.md`` ASM-42, ASM-44 (the block's
capacity is the shape's -- 24 on `fixed-limit-20`, 66 on `no-limit-100` -- and it is the
refusal threshold as well as the width).

A history entry is a plain str of exactly four grammars and its fourth token is the
verb.  The entry's street, seat and amount are other blocks -- or not facts at all --
so only the verb reaches the slot.
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


class FEA6History(S.FeaturesCase):
    """All four entry grammars, in both encodings, oldest first, and the bound on length."""

    def test_fea6_1_the_four_grammars_fill_the_right_dense_slot(self):
        """FEA-6.1 a history entry of any of the four documented forms sets slot
        `131 + 3 * j + action` and nothing else in the dense block (flat-numeric.md §5,
        ASM-E2)."""
        F = self.surface()
        encoder = F.build_encoder(S.FLAT)
        for entry, action in (
            ("preflop seat 0 folds", 0),
            ("flop seat 1 checks", 1),
            ("turn seat 0 calls 2", 1),
            ("river seat 1 raises to 4", 2),
        ):
            with self.subTest(entry=entry):
                self.assertEqual(
                    S.history_action(entry), action,
                    "the battery's own entry %r denotes action %d (flat-numeric.md §5)"
                    % (entry, action),
                )
                values = S.floats(F.encode(encoder, S.readout(history=[entry])))
                self.assert_floats(
                    values[131:203], S.history_block([entry]),
                    "the history block of %r" % (entry,),
                )
                self.assertEqual(
                    values[131:134],
                    [1.0 if position == action else 0.0 for position in range(3)],
                    "the first history slot is the one-hot of %r (flat-numeric.md §5): %r"
                    % (entry, values[131:134]),
                )

    def test_fea6_2_the_four_grammars_emit_the_right_token_id(self):
        """FEA-6.2 the four forms emit 93 fold, 94 check/call and 95 raise in the token
        encoding (card-tokens.md §5, flat-numeric.md §5)."""
        F = self.surface()
        encoder = F.build_encoder(S.TOKENS)
        for entry, ident in (
            ("preflop seat 0 folds", 93),
            ("flop seat 1 checks", 94),
            ("turn seat 0 calls 2", 94),
            ("river seat 1 raises to 4", 95),
        ):
            with self.subTest(entry=entry):
                values = S.ints(F.encode(encoder, S.readout(history=[entry])))
                self.assertEqual(
                    values[16], ident,
                    "the first history token of %r is %d (card-tokens.md §5): %r"
                    % (entry, ident, values[16]),
                )
                self.assert_ints(
                    values[16:40], S.history_tokens([entry]),
                    "the history tokens of %r" % (entry,),
                )

    def test_fea6_3_the_street_seat_and_amount_do_not_change_the_slot(self):
        """FEA-6.3 two entries of one verb fill one slot whatever their street, seat and
        amount: only the verb is carried (flat-numeric.md §5, guardrails.md G13)."""
        F = self.surface()
        dense = F.build_encoder(S.FLAT)
        tokens = F.build_encoder(S.TOKENS)
        for verb, action, pairs in (
            ("folds", 0, ("preflop seat 0 folds", "river seat 1 folds")),
            ("checks", 1, ("flop seat 0 checks", "turn seat 1 checks")),
            ("calls", 1, ("preflop seat 1 calls 1", "river seat 0 calls 8")),
            ("raises", 2, ("flop seat 0 raises to 4", "river seat 1 raises to 12")),
        ):
            with self.subTest(verb=verb):
                for entry in pairs:
                    with self.subTest(entry=entry):
                        self.assertEqual(
                            S.history_action(entry), action,
                            "every %r entry denotes action %d whatever it names "
                            "(flat-numeric.md §5)" % (verb, action),
                        )
                        values = S.floats(F.encode(dense, S.readout(history=[entry])))
                        self.assert_floats(
                            values[131:203], S.history_block([entry]),
                            "the dense history slot of %r" % (entry,),
                        )
                        ids = S.ints(F.encode(tokens, S.readout(history=[entry])))
                        self.assertEqual(
                            ids[16], S.HISTORY_IDS[S.ACTIONS[action]],
                            "the history token of %r is the verb's own id "
                            "(card-tokens.md §5): %r" % (entry, ids[16]),
                        )

    def test_fea6_4_the_history_is_oldest_first(self):
        """FEA-6.4 the history block is one slot per applied action, oldest first, in both
        encodings (flat-numeric.md §5, card-tokens.md §5, README.md §4)."""
        F = self.surface()
        history = ["preflop seat 0 folds", "flop seat 1 checks", "turn seat 0 raises to 6"]
        dense = S.floats(F.encode(F.build_encoder(S.FLAT), S.readout(history=history)))
        self.assert_floats(dense[131:203], S.history_block(history),
                           "the dense history block of a three-entry history")
        tokens = S.ints(F.encode(F.build_encoder(S.TOKENS), S.readout(history=history)))
        self.assert_ints(tokens[16:40], S.history_tokens(history),
                         "the token history block of a three-entry history")
        self.assertEqual(
            dense[131:134], [1.0, 0.0, 0.0],
            "the oldest entry is slot 0 (flat-numeric.md §5): %r" % (dense[131:134],),
        )
        self.assertEqual(
            dense[134:137], [0.0, 1.0, 0.0],
            "the second entry is slot 1 (flat-numeric.md §5): %r" % (dense[134:137],),
        )
        self.assertEqual(
            dense[137:140], [0.0, 0.0, 1.0],
            "the third entry is slot 2 (flat-numeric.md §5): %r" % (dense[137:140],),
        )

    def test_fea6_5_a_23_entry_history_fills_23_slots_and_leaves_the_last_slot_empty(self):
        """FEA-6.5 a 23-entry history -- the most a hand can hold under the raise cap --
        fills 23 slots and leaves the last slot zero in the dense encoding and the pad in
        the token encoding (flat-numeric.md §5, card-tokens.md §5, encodings.md §3)."""
        F = self.surface()
        history = S.history_entries(23)
        self.assertEqual(len(history), 23, "the battery builds a 23-entry history")
        dense = S.floats(F.encode(F.build_encoder(S.FLAT), S.readout(history=history)))
        self.assert_floats(dense[131:203], S.history_block(history),
                           "the dense history block of a 23-entry history")
        self.assertEqual(
            dense[200:203], [0.0, 0.0, 0.0],
            "the 24th slot is past the history's end, so it is all-zero "
            "(flat-numeric.md §5): %r" % (dense[200:203],),
        )
        self.assertEqual(
            sum(1 for value in dense[131:203] if value == 1.0), 23,
            "23 applied actions are 23 one-hots (flat-numeric.md §5)",
        )
        tokens = S.ints(F.encode(F.build_encoder(S.TOKENS), S.readout(history=history)))
        self.assert_ints(tokens[16:40], S.history_tokens(history),
                         "the token history block of a 23-entry history")
        self.assertEqual(
            tokens[39], S.PAD,
            "the 24th history token is the pad (card-tokens.md §5): %r" % (tokens[39],),
        )
        self.assertEqual(
            sum(1 for value in tokens[16:39] if value != S.PAD), 23,
            "23 applied actions are 23 non-pad tokens (card-tokens.md §5)",
        )

    def test_fea6_6_a_24_entry_history_is_the_declared_maximum_and_is_accepted(self):
        """FEA-6.6 the block holds 24 slots and a history of at most 24 entries is carried,
        not refused (flat-numeric.md §5, errors.md §3-§4)."""
        F = self.surface()
        history = S.history_entries(24)
        self.assertEqual(len(history), 24, "the battery builds a 24-entry history")
        dense = S.floats(F.encode(F.build_encoder(S.FLAT), S.readout(history=history)))
        self.assert_floats(dense[131:203], S.history_block(history),
                           "the dense history block of a 24-entry history")
        self.assertEqual(
            sum(1 for value in dense[131:203] if value == 1.0), 24,
            "24 applied actions are 24 one-hots, so the last slot is live "
            "(flat-numeric.md §5)",
        )
        tokens = S.ints(F.encode(F.build_encoder(S.TOKENS), S.readout(history=history)))
        self.assert_ints(tokens[16:40], S.history_tokens(history),
                         "the token history block of a 24-entry history")
        self.assertNotIn(
            S.PAD, tokens[16:40],
            "a full history leaves no pad token (card-tokens.md §5): %r" % (tokens[16:40],),
        )

    def test_fea6_7_a_25_entry_history_is_refused(self):
        """FEA-6.7 a history longer than the 24 slots is refused, never truncated, and the
        message names history and the length it saw (flat-numeric.md §5, errors.md §3)."""
        F = self.surface()
        history = S.history_entries(25)
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                encoder = F.build_encoder(name)
                record = S.readout(history=history)
                exc = self.refuses(
                    F.encode, encoder, record,
                    words=("encode", "history", "25"),
                )
                self.assertTrue(
                    str(exc).strip(),
                    "the refusal names what was violated (errors.md §3)",
                )

    def test_fea6_8_an_entry_of_a_fifth_form_is_refused(self):
        """FEA-6.8 an entry that is not one of the four documented forms is refused with
        the entry in the message: a fifth spelling is not guessed at (flat-numeric.md §5,
        errors.md §3, guardrails.md G13)."""
        F = self.surface()
        encoder = F.build_encoder(S.FLAT)
        for entry in (
            "preflop seat 0 bets 5",
            "preflop seat 0 raises 4",
            "preflop seat 0 calls",
            "preflop seat 0",
        ):
            with self.subTest(entry=entry):
                self.refuses(
                    F.encode, encoder, S.readout(history=[entry]),
                    words=("encode", "history", entry),
                )

    def test_fea6_9_a_non_string_entry_is_refused(self):
        """FEA-6.9 a history entry that is not a plain str of the grammar is refused, not
        coerced (encodings.md §5, errors.md §4)."""
        F = self.surface()
        encoder = F.build_encoder(S.TOKENS)
        for entry in (5, None, ("preflop", "seat", "0", "folds")):
            with self.subTest(entry=entry):
                self.refuses(
                    F.encode, encoder, S.readout(history=[entry]),
                    words=("encode", "history"),
                )

    def test_fea6_10_an_empty_history_leaves_the_block_empty(self):
        """FEA-6.10 the empty history -- a hand before its first action -- leaves the dense
        block all-zero and the token block all-pad (README.md §4, flat-numeric.md §5)."""
        F = self.surface()
        record = S.readout()
        self.assertEqual(record["history"], [],
                         "the battery's invented readout starts before the first action")
        dense = S.floats(F.encode(F.build_encoder(S.FLAT), record))
        self.assertEqual(
            dense[131:203], [0.0] * 72,
            "no applied action means no live history slot (flat-numeric.md §5): %r"
            % (dense[131:140],),
        )
        tokens = S.ints(F.encode(F.build_encoder(S.TOKENS), record))
        self.assertEqual(
            tokens[16:40], [S.PAD] * 24,
            "no applied action means 24 pad tokens (card-tokens.md §5): %r"
            % (tokens[16:24],),
        )


class FEA6ShapedCapacity(S.FeaturesCase):
    """The capacity is the shape's: it is the block's width and its refusal threshold."""

    def test_fea6_11_the_default_shape_carries_24_entries_and_refuses_a_25th(self):
        """FEA-6.11 on `fixed-limit-20` a history of exactly the shape's 24 entries encodes
        in both encodings, and a 25th is refused -- never truncated -- by a message naming
        the field, the capacity and the count it saw, because the capacity is the block's
        refusal threshold as well as its width (shapes.md §8, ASM-42, flat-numeric.md §5,
        card-tokens.md §5, errors.md §3)."""
        F = self.surface()
        capacity = S.CAPACITY[S.DEFAULT_SHAPE]
        self.assertEqual(
            capacity, S.HISTORY_SLOTS,
            "the default shape's capacity is the 24 slots the encoding has always "
            "declared: the fixed-limit path does not move (shapes.md §5, §8): %r"
            % (capacity,),
        )
        history = S.history_entries(capacity)
        self.assertEqual(len(history), 24, "the battery builds a 24-entry history")
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                encoder = F.build_encoder(name)
                observation = F.encode(encoder, S.readout(history=history))
                self.assertEqual(
                    len(observation), S.DECLARED[name]["shape"][0],
                    "a history of exactly the capacity encodes, and the observation is "
                    "still the declared width (shapes.md §8, ASM-42): %d"
                    % (len(observation),),
                )
                exc = self.refuses(
                    F.encode, encoder, S.readout(history=S.history_entries(capacity + 1)),
                    words=("encode", "history", str(capacity), str(capacity + 1)),
                )
                self.assertIn(
                    str(capacity), str(exc),
                    "the refusal names the capacity it was measured against, so a caller "
                    "learns how long this shape's history may be (shapes.md §8, ASM-42, "
                    "errors.md §3): %r" % (str(exc),),
                )

    def test_fea6_12_the_no_cap_shape_carries_66_entries_and_refuses_a_67th(self):
        """FEA-6.12 on `no-limit-100` a history of exactly its 66 entries encodes in both
        encodings -- 3 x 66 = 198 dense slots and 66 tokens, the last ones live -- and a
        67th is refused, never truncated, naming the field, the capacity and the count:
        the capacity is that shape's own derived bound (200 / 4 = 50 raises plus
        4 x 2 x 2 = 16 non-bet actions), not the fixed-limit cap's (shapes.md §8, ASM-42,
        ASM-44, flat-numeric.md §5, card-tokens.md §5)."""
        F = self.surface()
        capacity = S.CAPACITY[S.SECOND_SHAPE]
        self.assertEqual(
            capacity, 66,
            "the no-cap shape's capacity is 66: 200 / 4 = 50 raises plus 4 x 2 x 2 = 16 "
            "non-bet actions (shapes.md §8, ASM-42): %r" % (capacity,),
        )
        self.assertGreater(
            capacity, S.CAPACITY[S.DEFAULT_SHAPE],
            "the uncapped shape's capacity is wider than the fixed-limit cap's, which is "
            "what makes a pool holding a trained no-limit model encodable at 25 decisions "
            "(shapes.md §8, ASM-42): %r against %r"
            % (capacity, S.CAPACITY[S.DEFAULT_SHAPE]),
        )
        history = S.history_entries(capacity)
        self.assertEqual(len(history), 66, "the battery builds a 66-entry history")
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                encoder = F.build_encoder(name, shape=S.SECOND_SHAPE)
                values = F.encode(encoder, S.readout(history=history))
                self.assertEqual(
                    len(values), S.DECLARED_BY_SHAPE[S.SECOND_SHAPE][name][0],
                    "a history of exactly the capacity encodes, at that shape's declared "
                    "width (shapes.md §8, ASM-42): %d" % (len(values),),
                )
                if name == S.FLAT:
                    block = S.floats(values)[S.FIXED_FLAT_SLOTS:]
                    self.assertEqual(
                        len(block), 3 * capacity,
                        "the dense history block of the no-cap shape is 3 x 66 = 198 slots "
                        "(flat-numeric.md §5, shapes.md §8): %d" % (len(block),),
                    )
                    self.assertEqual(
                        sum(1 for value in block if value == 1.0), 66,
                        "66 applied actions are 66 one-hots, so the last slot is live and "
                        "nothing was truncated (flat-numeric.md §5, ASM-42)",
                    )
                else:
                    block = S.ints(values)[S.FIXED_TOKEN_SLOTS:]
                    self.assertEqual(
                        block, S.history_tokens(history, capacity),
                        "the token history block of the no-cap shape is 66 tokens, oldest "
                        "first, with no pad at all (card-tokens.md §5, shapes.md §8)",
                    )
                    self.assertNotIn(
                        S.PAD, block,
                        "a full 66-entry history leaves no pad token: the block's width "
                        "and its capacity are one number (card-tokens.md §5, ASM-42): %r"
                        % (block,),
                    )
                exc = self.refuses(
                    F.encode, encoder,
                    S.readout(history=S.history_entries(capacity + 1)),
                    words=("encode", "history", str(capacity), str(capacity + 1)),
                )
                self.assertIn(
                    str(capacity), str(exc),
                    "the refusal names this shape's capacity, not the default shape's "
                    "(shapes.md §8, ASM-42, errors.md §3): %r" % (str(exc),),
                )
        default_encoder = F.build_encoder(S.FLAT)
        self.refuses(
            F.encode, default_encoder, S.readout(history=S.history_entries(capacity)),
            words=("encode", "history", str(S.CAPACITY[S.DEFAULT_SHAPE]), str(capacity)),
        )



class FEA6ThirdSeatCapacity(S.FeaturesCase):
    """The six-seat row's capacity of 98 is the block's width and its threshold."""

    def test_fea6_13_the_six_seat_row_carries_98_entries_and_refuses_a_99th(self):
        """FEA-6.13 on `six-seat-no-limit-100` a history of exactly its 98 entries encodes
        in both encodings -- 3 x 98 = 294 dense slots and 98 tokens, every one live and no
        pad at all -- and a 99th is refused, never truncated, naming the field, the 98 and
        the 99, so the capacity is that row's own derived bound (600 / 12 = 50 raises plus
        4 x 6 x 2 = 48 non-bet actions) and not the 66 or 24 of the two-seat rows
        (capacity.md §1-§3, shapes.md §8, seats.md §2, flat-numeric.md §5,
        card-tokens.md §5, errors.md §3, ASM-42, ASM-44)."""
        F = self.surface()
        capacity = S.CAPACITY[S.THIRD_SHAPE]
        self.assertEqual(
            capacity, 98,
            "the six-seat row's capacity is 98: 600 / 12 = 50 raises plus 4 x 6 x 2 = 48 "
            "non-bet actions (capacity.md §1, seats.md §2): %r" % (capacity,),
        )
        self.assertGreater(
            capacity, S.CAPACITY[S.SECOND_SHAPE],
            "and it is wider than both two-seat rows' capacities, which is what makes a "
            "pool holding a six-seat hand encodable at 67 decisions (capacity.md §1, "
            "ASM-42): %r against %r"
            % (capacity, S.CAPACITY[S.SECOND_SHAPE]),
        )
        history = S.history_entries(capacity)
        self.assertEqual(
            len(history), 98,
            "the battery builds a 98-entry history of the documented forms (capacity.md "
            "§1): %d entries" % (len(history),),
        )
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                encoder = F.build_encoder(name, shape=S.THIRD_SHAPE)
                values = F.encode(encoder, S.six_seat_readout(history=history))
                self.assertEqual(
                    len(values), S.DECLARED_BY_SHAPE[S.THIRD_SHAPE][name][0],
                    "a history of exactly the capacity encodes, at the row's declared "
                    "width -- 433 dense and 122 tokens (capacity.md §2-§3): %d"
                    % (len(values),),
                )
                if name == S.FLAT:
                    block = S.floats(values)[S.flat_slots_before_history(S.THIRD_SHAPE):]
                    self.assertEqual(
                        len(block), 3 * capacity,
                        "the dense history block is 3 x 98 = 294 slots, from slot 139 to "
                        "432 (flat-numeric.md §5, capacity.md §2): %d" % (len(block),),
                    )
                    self.assert_floats(
                        block, S.history_block(history, capacity),
                        "and it is the 98 one-hots of 3, oldest first (flat-numeric.md "
                        "§5, ASM-42)",
                    )
                    self.assertEqual(
                        sum(1 for value in block if value == 1.0), 98,
                        "98 applied actions are 98 one-hots, so the last slot is live and "
                        "nothing was truncated (flat-numeric.md §5, ASM-42)",
                    )
                else:
                    block = S.ints(values)[S.token_slots_before_history(S.THIRD_SHAPE):]
                    self.assertEqual(
                        len(block), capacity,
                        "the token history block is 98 tokens, from token 24 to 121 "
                        "(card-tokens.md §5, capacity.md §2): %d" % (len(block),),
                    )
                    self.assert_ints(
                        block, S.history_tokens(history, capacity),
                        "and it is one id per applied action, oldest first "
                        "(card-tokens.md §5, ASM-42)",
                    )
                    self.assertNotIn(
                        S.PAD, block,
                        "a full 98-entry history leaves no pad token: the block's width "
                        "and its capacity are one number (card-tokens.md §5, ASM-42): %r"
                        % (block[:6],),
                    )
                exc = self.refuses(
                    F.encode, encoder,
                    S.six_seat_readout(history=S.history_entries(capacity + 1)),
                    words=("encode", "history", str(capacity), str(capacity + 1)),
                )
                self.assertIn(
                    str(capacity), str(exc),
                    "the refusal names this row's 98, not another row's capacity "
                    "(capacity.md §3, errors.md §3): %r" % (str(exc),),
                )
                self.assertIn(
                    str(capacity + 1), str(exc),
                    "and the 99 entries it saw, so the caller learns the count was one "
                    "past the bound (flat-numeric.md §6, errors.md §3): %r" % (str(exc),),
                )
        for shape in S.SHAPES:
            with self.subTest(shape=shape, entries=98, accepted=False):
                self.refuses(
                    F.encode, F.build_encoder(S.FLAT, shape=shape),
                    S.readout(history=history),
                    words=("encode", "history", str(S.CAPACITY[shape]), str(capacity)),
                )


if __name__ == "__main__":
    unittest.main()
