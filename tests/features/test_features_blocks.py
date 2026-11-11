"""FEA-4 -- `flat-numeric`: the nine blocks, their offsets and the slot order inside them.

``docs/L3/features/flat-numeric.md`` §2-§5; ``docs/L2/features/encodings.md`` §3;
``docs/L3/features/encoder.md`` §3.1, §4; ``docs/L3/features/guardrails.md`` G3, G10;
``docs/L1/shapes.md`` §8 and ``docs/L1/assumptions.md`` ASM-42, ASM-44 (the history
block's capacity is the shape's).

The numbers asserted here are the design's, not a re-derivation: every case compares
one slice of `encode`'s array with the values `flat-numeric.md` fixes for it, and the
two shapes' widths -- 203 and 329 -- with the arithmetic `shapes.md` §8 states.
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


class FEA4FlatBlocks(S.FeaturesCase):
    """The dense encoding's block table, and the arithmetic that reaches 203."""

    def test_fea4_1_the_nine_widths_sum_to_the_declared_width_and_the_blocks_land_there(self):
        """FEA-4.1 the nine block widths sum to the width the spec declares, and one worked
        readout's nine blocks occupy the running-sum offsets of the array `encode` returns,
        with the history block last (flat-numeric.md §2-§5, encoder.md §4,
        guardrails.md G3).

        The offsets are read back from the observation and never compared with this
        battery's own offset column: a table copied faithfully into the support module
        would otherwise pass against a block written one slot off.
        """
        F = self.surface()
        spec = F.spec(S.FLAT)
        widths = [width for _field, _offset, width in S.FLAT_BLOCKS]
        declared = tuple(int(value) for value in spec["shape"])
        self.assertEqual(
            declared, (sum(widths),),
            "4 + 2 + 34 + 85 + 2 + 1 + 1 + 2 + 72 = 203 must be the width the spec "
            "declares (flat-numeric.md §2, encoder.md §4): %r against a sum of %d"
            % (declared, sum(widths)),
        )
        record = S.readout(street="river", seat=(1, False), hole=("2c", "Td"),
                           stacks=(13, 12), pot=15, to_call=4, limit=(2, 0),
                           history=["preflop seat 0 folds"])
        values = S.floats(F.encode(F.build_encoder(S.FLAT), record))
        self.assertEqual(
            len(values), sum(widths),
            "one dense observation is as long as the nine widths together "
            "(flat-numeric.md §2, §7): %d slots" % (len(values),),
        )
        expected_of = {
            "street": S.street_onehot("river"),
            "seat": [1.0, 0.0],
            "hole": S.card_slot("2c") + S.card_slot("Td"),
            "board": [value for card in record["board"] for value in S.card_slot(card)],
            # the acting seat is 1, so its 12 chips are the block's first slot
            # (flat-numeric.md §4): the one block that reads a second fact.
            "stacks": [record["stacks"][record["seat"][0]] / 20.0,
                       record["stacks"][1 - record["seat"][0]] / 20.0],
            "pot": [15 / 40.0],
            "to_call": [4 / 20.0],
            "limit": [2 / 4.0, 0.0],
            "history": S.history_block(record["history"]),
        }
        fields = tuple(F.spec(S.FLAT)["fields"])
        self.assertEqual(
            list(fields), [field for field, _offset, _width in S.FLAT_BLOCKS],
            "the blocks are in the spec's field order, so the running sum of the widths "
            "is the order the observation was built in (encoder.md §3.1, §4, README.md §5 "
            "rule 3): %r" % (fields,),
        )
        offset = 0
        for field, width in zip(fields, widths):
            expected = expected_of[field]
            with self.subTest(field=field):
                self.assertEqual(
                    len(expected), width,
                    "the %r block's own width is %d (flat-numeric.md §2)" % (field, width),
                )
                self.assert_floats(
                    values[offset:offset + width], expected,
                    "the %r block occupies slots %d-%d: the running sum of the widths "
                    "before it (flat-numeric.md §2-§5, encoder.md §4, guardrails.md G3)"
                    % (field, offset, offset + width),
                )
                if offset:
                    self.assertNotEqual(
                        values[offset - 1:offset - 1 + width], expected,
                        "the %r block does not start one slot earlier: a block an offset "
                        "off lands here instead (flat-numeric.md §2, guardrails.md G3): %r"
                        % (field, values[offset - 1:offset - 1 + width]),
                    )
            offset += width
        self.assertEqual(
            offset, len(values),
            "the width sum ends exactly where the observation ends, so the last block is "
            "the history (flat-numeric.md §2, guardrails.md G3): %d of %d slots"
            % (offset, len(values)),
        )
        self.assert_floats(
            values[len(values) - widths[-1]:], S.history_block(record["history"]),
            "the history block is the observation's last %d slots, read from the array's "
            "own length (flat-numeric.md §2, §5)" % (widths[-1],),
        )

    def test_fea4_2_the_history_block_is_the_last_72_slots(self):
        """FEA-4.2 the history block is 24 one-hots of 3 in the last 72 slots, and a slot
        past the history's end is all zeros (flat-numeric.md §2, §5, §7)."""
        field, offset, width = S.FLAT_BLOCKS[-1]
        self.assertEqual(
            (field, offset, width), ("history", 131, 72),
            "the history is the last block: 131 + 72 = 203 (flat-numeric.md §2)",
        )
        self.assertEqual(
            offset + width, 203,
            "the history block ends the observation (flat-numeric.md §2): %d" % (offset + width,),
        )
        self.assertEqual(width, S.HISTORY_SLOTS * S.HISTORY_SLOT_WIDTH,
                         "72 = 24 slots of 3 (flat-numeric.md §2)")
        values = S.floats(self.flat(S.readout(history=["preflop seat 0 folds"])))
        self.assertEqual(len(values), 203, "one dense observation is 203 slots")
        self.assertEqual(
            values[131:134], [1.0, 0.0, 0.0],
            "slot 0 of the history is the fold one-hot (flat-numeric.md §5): %r"
            % (values[131:134],),
        )
        self.assertEqual(
            values[134:203], [0.0] * 69,
            "the 23 slots past the history's end stay all-zero (flat-numeric.md §5): %r"
            % (values[134:139],),
        )

    def test_fea4_3_the_street_block_is_a_one_hot_over_the_four_streets(self):
        """FEA-4.3 the street block is a 4-wide one-hot whose live slot is the street's
        position in preflop, flop, turn, river (flat-numeric.md §2, encodings.md §3)."""
        F = self.surface()
        encoder = F.build_encoder(S.FLAT)
        for street in S.STREETS:
            with self.subTest(street=street):
                values = S.floats(F.encode(encoder, S.readout(street=street)))
                self.assert_floats(
                    values[0:4], S.street_onehot(street),
                    "the street block of a %s readout" % (street,),
                )

    def test_fea4_4_the_seat_block_carries_the_index_and_the_button_flag(self):
        """FEA-4.4 the seat block is [the acting seat's index, 1.0 if it holds the button
        else 0.0] (flat-numeric.md §4, encodings.md §3)."""
        F = self.surface()
        encoder = F.build_encoder(S.FLAT)
        for seat, expected in (
            ((0, True), [0.0, 1.0]),
            ((0, False), [0.0, 0.0]),
            ((1, True), [1.0, 1.0]),
            ((1, False), [1.0, 0.0]),
        ):
            with self.subTest(seat=seat):
                values = S.floats(F.encode(encoder, S.readout(seat=seat)))
                self.assert_floats(values[4:6], expected, "the seat block of seat %r" % (seat,))

    def test_fea4_5_each_hole_card_slot_marks_its_rank_and_its_suit_and_nothing_else(self):
        """FEA-4.5 the hole block is two 17-slot card slots in `hole`'s own order, each
        marking exactly one rank slot and exactly one suit slot (flat-numeric.md §3,
        encodings.md §3)."""
        F = self.surface()
        encoder = F.build_encoder(S.FLAT)
        for hole in (("Td", "2c"), ("As", "Kh"), ("9h", "9s"), ("2d", "Qc")):
            with self.subTest(hole=hole):
                values = S.floats(F.encode(encoder, S.readout(hole=hole)))
                expected = S.card_slot(hole[0]) + S.card_slot(hole[1])
                self.assert_floats(values[6:40], expected,
                                   "the two hole card slots of %r" % (hole,))
                for position, card in enumerate(hole):
                    block = values[6 + 17 * position: 6 + 17 * (position + 1)]
                    self.assertEqual(
                        sum(1 for value in block if value != 0.0), 2,
                        "a card slot marks exactly two slots -- one rank, one suit -- and "
                        "leaves the other fifteen at zero (flat-numeric.md §3): %r set %r"
                        % (card, block),
                    )

    def test_fea4_6_an_undealt_board_card_slot_is_all_zeros(self):
        """FEA-4.6 the board block is five card slots and every slot at or past the deal is
        all zeros (flat-numeric.md §3, encodings.md §3)."""
        F = self.surface()
        encoder = F.build_encoder(S.FLAT)
        for position, street in enumerate(S.STREETS):
            with self.subTest(street=street):
                record = S.readout(street=street)
                dealt = len(record["board"])
                self.assertEqual(dealt, S.BOARD_SIZES[position],
                                 "the invented %s readout's board" % (street,))
                values = S.floats(F.encode(encoder, record))
                for slot in range(dealt, 5):
                    block = values[40 + 17 * slot: 40 + 17 * (slot + 1)]
                    self.assertEqual(
                        block, [0.0] * 17,
                        "card slot %d of the board is not yet dealt, so it is all zeros "
                        "(flat-numeric.md §3): %r" % (slot, block),
                    )

    def test_fea4_7_a_dealt_board_card_fills_its_own_slot_only(self):
        """FEA-4.7 board card i fills card slot i with its rank and suit one-hots, in the
        board's own order (flat-numeric.md §3)."""
        F = self.surface()
        encoder = F.build_encoder(S.FLAT)
        for position, street in enumerate(S.STREETS):
            with self.subTest(street=street):
                record = S.readout(street=street)
                board = record["board"]
                self.assertEqual(len(board), S.BOARD_SIZES[position],
                                 "the invented %s readout's board" % (street,))
                values = S.floats(F.encode(encoder, record))
                expected = []
                for card in board:
                    expected.extend(S.card_slot(card))
                expected.extend([0.0] * 17 * (5 - len(board)))
                self.assert_floats(values[40:125], expected,
                                   "the board block of a %s readout" % (street,))
                for index, card in enumerate(board):
                    block = values[40 + 17 * index: 40 + 17 * (index + 1)]
                    self.assert_floats(
                        block, S.card_slot(card),
                        "board card %d (%r) fills card slot %d" % (index, card, index),
                    )

    def test_fea4_8_the_stacks_block_is_the_acting_seat_first_each_divided_by_20(self):
        """FEA-4.8 the stacks block is [the acting seat's stack, the other's], each divided
        by 20: the one dense block that reads a second fact (flat-numeric.md §4,
        encodings.md §3, encoder.md §4)."""
        F = self.surface()
        encoder = F.build_encoder(S.FLAT)
        for seat, stacks, expected in (
            ((0, True), (19, 18), [19 / 20.0, 18 / 20.0]),
            ((1, False), (19, 18), [18 / 20.0, 19 / 20.0]),
            ((0, False), (7, 13), [7 / 20.0, 13 / 20.0]),
            ((1, True), (7, 13), [13 / 20.0, 7 / 20.0]),
        ):
            with self.subTest(seat=seat, stacks=stacks):
                values = S.floats(F.encode(encoder, S.readout(seat=seat, stacks=stacks)))
                self.assert_floats(
                    values[125:127], expected,
                    "the stacks block for seat %r and stacks %r" % (seat, stacks),
                )

    def test_fea4_9_the_pot_is_divided_by_40(self):
        """FEA-4.9 the pot block is one slot, the pot divided by the 40 chips a hand begins
        with (flat-numeric.md §4, encodings.md §3)."""
        F = self.surface()
        encoder = F.build_encoder(S.FLAT)
        for pot in (0, 3, 6, 10, 14, 40):
            with self.subTest(pot=pot):
                values = S.floats(F.encode(encoder, S.readout(pot=pot)))
                self.assert_floats(values[127:128], [pot / 40.0], "the pot block of %r" % (pot,))

    def test_fea4_10_to_call_is_divided_by_20(self):
        """FEA-4.10 the to_call block is one slot, the amount to call divided by 20
        (flat-numeric.md §4, encodings.md §3)."""
        F = self.surface()
        encoder = F.build_encoder(S.FLAT)
        for to_call in (0, 1, 2, 4, 20):
            with self.subTest(to_call=to_call):
                values = S.floats(F.encode(encoder, S.readout(to_call=to_call)))
                self.assert_floats(
                    values[128:129], [to_call / 20.0], "the to_call block of %r" % (to_call,),
                )

    def test_fea4_11_the_limit_block_is_the_bet_size_over_4_and_the_bet_or_raise_count_over_4(self):
        """FEA-4.11 the limit block is [the bet size in force / 4, the bet-or-raise actions made
        this street / 4]: the count takes 0-4 under ASM-6's cap of four such actions a street,
        which is its own maximum, so the slot spans 0.0-1.0 and needs no clip
        (flat-numeric.md §4, encodings.md §3)."""
        F = self.surface()
        encoder = F.build_encoder(S.FLAT)
        for bet, count in ((2, 0), (2, 3), (2, 4), (4, 0), (4, 1), (4, 3), (4, 4)):
            with self.subTest(bet=bet, count=count):
                values = S.floats(
                    F.encode(encoder, S.readout(limit=(bet, count)))
                )
                self.assert_floats(
                    values[129:131], [bet / 4.0, count / 4.0],
                    "the limit block of (%r, %r)" % (bet, count),
                )

    def test_fea4_12_the_first_block_writes_the_street_and_the_last_the_history(self):
        """FEA-4.12 the block order is the `fields` order: the first block is the street and
        the last block is the history (encoder.md §3.1, §4, flat-numeric.md §2,
        README.md §5 rule 3)."""
        F = self.surface()
        encoder = F.build_encoder(S.FLAT)
        fields = tuple(F.spec(S.FLAT)["fields"])
        self.assertEqual(fields[0], "street", "the first field is the street: %r" % (fields,))
        self.assertEqual(fields[-1], "history", "the last field is the history: %r" % (fields,))
        history = ["preflop seat 0 calls 1", "flop seat 1 checks"]
        values = S.floats(F.encode(encoder, S.readout(street="river", history=history)))
        self.assert_floats(values[0:4], S.street_onehot("river"),
                           "the first block of the observation is the street block")
        self.assert_floats(values[131:203], S.history_block(history),
                           "the last 72 slots of the observation are the history block")

    def test_fea4_13_the_canonical_readout_lands_at_the_declared_offsets(self):
        """FEA-4.13 one fully worked readout lands every block at its declared offset:
        0 street, 4 seat, 6 hole, 40 board, 125 stacks, 127 pot, 128 to_call, 129 limit,
        131 history (flat-numeric.md §2-§5)."""
        record = S.readout()
        values = S.floats(self.flat(record))
        self.assertEqual(len(values), 203, "one dense observation is 203 slots")
        for position, expected, where in (
            (0, 1.0, "slot 0: the preflop one-hot"),
            (4, 0.0, "slot 4: the acting seat's index, seat 0"),
            (5, 1.0, "slot 5: the button flag"),
            (14, 1.0, "slot 14: 'Td' marks the ten, rank slot 8 of card slot 0"),
            (20, 1.0, "slot 20: 'Td' marks the diamond, suit slot 1 of card slot 0"),
            (23, 1.0, "slot 23: '2c' marks the deuce, rank slot 0 of card slot 1"),
            (36, 1.0, "slot 36: '2c' marks the club, suit slot 0 of card slot 1"),
            (39, 0.0, "slot 39: the last slot inside the hole block is unmarked"),
            (40, 0.0, "slot 40: the first board slot is not yet dealt at preflop"),
            (124, 0.0, "slot 124: the last board slot is not yet dealt at preflop"),
            (125, 0.95, "slot 125: the acting seat's 19 chips over 20"),
            (126, 0.9, "slot 126: the other seat's 18 chips over 20"),
            (127, 0.075, "slot 127: the pot of 3 over 40"),
            (128, 0.05, "slot 128: the 1 chip to call over 20"),
            (129, 0.5, "slot 129: the small bet of 2 over 4"),
            (130, 0.0, "slot 130: no raise has been made this street"),
            (131, 0.0, "slot 131: the history is empty"),
            (202, 0.0, "slot 202: the last slot of the observation is the history's end"),
        ):
            with self.subTest(slot=position):
                self.assertAlmostEqual(
                    values[position], expected, delta=1e-5,
                    msg="%s, got %r (flat-numeric.md §2-§5)" % (where, values[position]),
                )

    def test_fea4_14_the_dense_width_is_the_shapes_and_the_other_blocks_do_not_move(self):
        """FEA-4.14 the dense history block is `3 x the shape's capacity` and the eight
        blocks before it are one table on both shapes: `no-limit-100` declares 329 slots
        -- 131 + 3 x 66 = 329 -- with its history block at 131 over 198 slots, while the
        default shape keeps 203 -- 131 + 3 x 24 -- and `encode` returns each shape's
        declared width; the slots before the history that no normaliser touches (street,
        seat, hole and board, 0-124) are the same values on both shapes, and the shape
        declares its own capacity as the block's refusal threshold (shapes.md §8,
        ASM-42, ASM-44, flat-numeric.md §2, §5).
        """
        F = self.surface()
        record = S.readout(street="flop", seat=(1, False), hole=("2c", "Td"),
                           board=("Jh", "7c", "2d"), stacks=(17, 17), pot=6,
                           to_call=0, limit=(2, 0),
                           history=S.history_entries(3))
        widths = {}
        for shape in S.SHAPES:
            capacity = S.CAPACITY[shape]
            encoder = F.build_encoder(S.FLAT, shape=shape)
            spec = F.observation_spec(encoder)
            values = S.floats(F.encode(encoder, record))
            with self.subTest(shape=shape):
                self.assertEqual(
                    tuple(spec["shape"]), S.DECLARED_BY_SHAPE[shape][S.FLAT],
                    "the dense width of %r is %d: 131 + 3 x %d = %d (shapes.md §8, "
                    "ASM-42, ASM-44): %r"
                    % (shape, S.DECLARED_BY_SHAPE[shape][S.FLAT][0], capacity,
                       131 + 3 * capacity, spec["shape"]),
                )
                self.assertEqual(
                    len(values), S.FIXED_FLAT_SLOTS + 3 * capacity,
                    "one dense observation of %r is the 131 slots before the history "
                    "plus 3 x its %d-slot history block (flat-numeric.md §2, §5, "
                    "shapes.md §8): %d slots" % (shape, capacity, len(values)),
                )
                self.assertEqual(
                    len(values) - 3 * capacity, S.FIXED_FLAT_SLOTS,
                    "the slots before the history are 131 on every shape: the shape "
                    "moves the capacity and no other block (shapes.md §8, ASM-44): %d"
                    % (len(values) - 3 * capacity,),
                )
                self.assert_floats(
                    values[S.FIXED_FLAT_SLOTS:],
                    S.history_block(record["history"], capacity),
                    "the history block of %r is the last %d slots, three per action "
                    "oldest first (flat-numeric.md §5, shapes.md §8)"
                    % (shape, 3 * capacity),
                )
                self.assertEqual(
                    values[S.FIXED_FLAT_SLOTS + 3 * len(record["history"]):
                           S.FIXED_FLAT_SLOTS + 3 * capacity],
                    [0.0] * (3 * (capacity - len(record["history"]))),
                    "the slots past the history's end stay all-zero on either capacity "
                    "(flat-numeric.md §5): %r"
                    % (values[S.FIXED_FLAT_SLOTS + 3 * len(record["history"]):][:6],),
                )
                widths[shape] = len(values)
        self.assertEqual(
            (widths[S.DEFAULT_SHAPE], widths[S.SECOND_SHAPE]), (203, 329),
            "the default shape's width does not move and the no-cap shape's is its own: "
            "203 and 329 (shapes.md §5, §8): %r" % (widths,),
        )
        default_values = S.floats(
            F.encode(F.build_encoder(S.FLAT, shape=S.DEFAULT_SHAPE), record))
        second_values = S.floats(
            F.encode(F.build_encoder(S.FLAT, shape=S.SECOND_SHAPE), record))
        self.assert_floats(
            second_values[0:125], default_values[0:125],
            "the street, seat, hole and board slots -- the ones no normaliser reaches -- "
            "are byte for byte the same on both shapes: the shape adds history slots and "
            "moves no earlier block (shapes.md §8, ASM-44)",
        )



class FEA4ThirdSeatCount(S.FeaturesCase):
    """The third row's dense table: six-wide seat and stacks blocks, 433 slots."""

    def test_fea4_15_the_six_seat_dense_table_is_433_slots_at_its_own_offsets(self):
        """FEA-4.15 on `six-seat-no-limit-100` the dense block table is
        `0/4, 4/6, 10/34, 44/85, 129/6, 135/1, 136/1, 137/2, 139/294` -- the eight blocks
        before the history reaching `127 + 2 x 6 = 139` and `139 + 3 x 98 = 433` -- and one
        six-seat readout's nine blocks land at exactly those offsets with the values the
        design fixes: the acting seat's one-hot over six seats, six stacks in seat order
        each over 100, the pot over 600, to_call over 100, the limit pair over 100 and
        50, and 98 slots of 3 for the history (capacity.md §2, flat-numeric.md §2, §4,
        §5, seats.md §3, ASM-42, ASM-44)."""
        F = self.surface()
        expected = (
            ("street", 0, 4),
            ("seat", 4, 6),
            ("hole", 10, 34),
            ("board", 44, 85),
            ("stacks", 129, 6),
            ("pot", 135, 1),
            ("to_call", 136, 1),
            ("limit", 137, 2),
            ("history", 139, 294),
        )
        self.assertEqual(
            S.THIRD_FLAT_BLOCKS, expected,
            "the six-seat row's dense block table is the design's, field for field, "
            "offset for offset and width for width (capacity.md §2, flat-numeric.md §2, "
            "seats.md §3): %r" % (S.THIRD_FLAT_BLOCKS,),
        )
        widths = [width for _field, _offset, width in S.THIRD_FLAT_BLOCKS]
        self.assertEqual(
            (sum(widths), 139 + 3 * 98, 127 + 2 * 6 + 3 * 98),
            (433, 433, 433),
            "4 + 6 + 34 + 85 + 6 + 1 + 1 + 2 + 294 = 433: the nine widths, the "
            "pre-history sum plus the history, and the row's arithmetic are one number "
            "(capacity.md §2, encoder.md §4): %r" % (sum(widths),),
        )
        record = S.six_seat_readout(street="river", seat=(2, True), hole=("As", "Ah"),
                                    stacks=(100, 76, 40, 20, 10, 5), pot=96,
                                    to_call=25, limit=(100, 3),
                                    history=S.history_entries(3))
        self.assertEqual(
            len(record["stacks"]), 6,
            "the readout handed to the six-seat encoder carries six stacks in seat "
            "order (seats.md §3, ASM-44): %r" % (record["stacks"],),
        )
        values = S.floats(F.encode(F.build_encoder(S.FLAT, shape=S.THIRD_SHAPE), record))
        self.assertEqual(
            len(values), S.DECLARED_BY_SHAPE[S.THIRD_SHAPE][S.FLAT][0],
            "one dense observation of the third row is the declared 433 slots "
            "(capacity.md §2, surface.md §5): %d" % (len(values),),
        )
        expected_of = {
            "street": S.street_onehot("river"),
            "seat": [1.0 if slot == 2 else 0.0 for slot in range(6)],
            "hole": S.card_slot("As") + S.card_slot("Ah"),
            "board": [value for card in record["board"] for value in S.card_slot(card)],
            "stacks": [amount / 100.0 for amount in record["stacks"]],
            "pot": [96 / 600.0],
            "to_call": [25 / 100.0],
            "limit": [100 / 100.0, 3 / 50.0],
            "history": S.history_block(record["history"], S.CAPACITY[S.THIRD_SHAPE]),
        }
        for field, offset, width in expected:
            with self.subTest(field=field):
                self.assertEqual(
                    len(expected_of[field]), width,
                    "the %r block is %d slots on the six-seat row (capacity.md §2, "
                    "flat-numeric.md §2, seats.md §3): %d"
                    % (field, width, len(expected_of[field])),
                )
                self.assert_floats(
                    values[offset:offset + width], expected_of[field],
                    "the %r block of a six-seat readout occupies slots %d-%d with the "
                    "design's values (flat-numeric.md §4, §5, seats.md §3)"
                    % (field, offset, offset + width),
                )
                if offset:
                    self.assertNotEqual(
                        values[offset - 1:offset - 1 + width], expected_of[field],
                        "the %r block does not start one slot earlier: a block an offset "
                        "off lands here instead (flat-numeric.md §2, guardrails.md G3): %r"
                        % (field, values[offset - 1:offset - 1 + width]),
                    )
        self.assert_floats(
            values[139:], expected_of["history"],
            "the history block is the last 294 slots, 98 slots of 3, oldest first "
            "(flat-numeric.md §5, capacity.md §2): %r" % (values[139:145],),
        )
        self.assert_floats(
            values[10:10 + 34 + 85],
            expected_of["hole"] + expected_of["board"],
            "the hole and board slots are still one table: 4 + 6 = 10 for the seat block "
            "and then the same 34 + 85 card slots the two-seat rows carry (flat-numeric.md "
            "§3, capacity.md §4)",
        )

    def test_fea4_16_the_three_rows_arithmetic_is_127_plus_2_seats_plus_3_capacity(self):
        """FEA-4.16 all three rows' dense tables are their own and the arithmetic is
        `127 + 2 x seats + 3 x capacity`: the 127 slots no seat count touches are the
        same on all three, the two per-seat blocks are one slot per seat, the slots
        before the history are 131/131/139, the history block is 3 x 24/66/98, and the
        widths are 203/329/433 -- while a six-seat readout's street, hole and board slots
        are the same values the two-seat rows write at their own offsets (capacity.md §2,
        §4, flat-numeric.md §2, §5, shapes.md §8, seats.md §3, ASM-42, ASM-44)."""
        F = self.surface()
        tables = {
            S.DEFAULT_SHAPE: (
                ("street", 0, 4), ("seat", 4, 2), ("hole", 6, 34),
                ("board", 40, 85), ("stacks", 125, 2), ("pot", 127, 1),
                ("to_call", 128, 1), ("limit", 129, 2), ("history", 131, 72),
            ),
            S.SECOND_SHAPE: (
                ("street", 0, 4), ("seat", 4, 2), ("hole", 6, 34),
                ("board", 40, 85), ("stacks", 125, 2), ("pot", 127, 1),
                ("to_call", 128, 1), ("limit", 129, 2), ("history", 131, 198),
            ),
            S.THIRD_SHAPE: S.THIRD_FLAT_BLOCKS,
        }
        widths = {}
        for shape, table in tables.items():
            seats, capacity = S.SEATS[shape], S.CAPACITY[shape]
            blocks = S.FLAT_BLOCKS_BY_SHAPE[shape]
            with self.subTest(shape=shape):
                self.assertEqual(
                    blocks, table,
                    "the %r dense block table is the design's (capacity.md §2, "
                    "flat-numeric.md §2, seats.md §3): %r" % (shape, blocks),
                )
                self.assertEqual(
                    (blocks[1][2], blocks[4][2]), (seats, seats),
                    "the seat and the stacks blocks are %d slots each, one per seat "
                    "(seats.md §3, ASM-44): %r" % (seats, blocks),
                )
                pre = blocks[-1][1]
                self.assertEqual(
                    (pre, S.SEAT_INVARIANT_FLAT_SLOTS + 2 * seats),
                    (S.SEAT_INVARIANT_FLAT_SLOTS + 2 * seats, pre),
                    "127 + 2 x %d = %d slots before the history: the 127 no seat count "
                    "touches plus the two per-seat blocks (capacity.md §2, ASM-44): %d"
                    % (seats, S.SEAT_INVARIANT_FLAT_SLOTS + 2 * seats, pre),
                )
                self.assertEqual(
                    blocks[-1][2], 3 * capacity,
                    "the history block is 3 x %d = %d slots (capacity.md §2, "
                    "flat-numeric.md §5, ASM-42): %d"
                    % (capacity, 3 * capacity, blocks[-1][2]),
                )
                self.assertEqual(
                    sum(width for _field, _offset, width in blocks), 3 * capacity + pre,
                    "and the widths sum to the pre-history slots plus the block "
                    "(encoder.md §4): %d" % (sum(w for _f, _o, w in blocks),),
                )
                spec = F.observation_spec(F.build_encoder(S.FLAT, shape=shape))
                self.assertEqual(
                    tuple(spec["shape"]),
                    (pre + 3 * capacity,),
                    "the row declares that width and no other (surface.md §5, "
                    "capacity.md §2): %r" % (spec["shape"],),
                )
                widths[shape] = pre + 3 * capacity
        self.assertEqual(
            (widths[S.DEFAULT_SHAPE], widths[S.SECOND_SHAPE], widths[S.THIRD_SHAPE]),
            (203, 329, 433),
            "the three rows' dense widths are 203, 329 and 433, each its own arithmetic "
            "(capacity.md §2, shapes.md §8): %r" % (widths,),
        )
        for shape, wanted in (
            (S.DEFAULT_SHAPE, 131), (S.SECOND_SHAPE, 131), (S.THIRD_SHAPE, 139),
        ):
            with self.subTest(shape=shape, before_history=wanted):
                blocks = S.FLAT_BLOCKS_BY_SHAPE[shape]
                self.assertEqual(
                    blocks[-1][1], wanted,
                    "the history block starts at slot %d on %r -- 131 on the two-seat "
                    "rows and 139 on the six-seat one, because the two per-seat blocks "
                    "are seats wide (capacity.md §2, seats.md §3): %d"
                    % (wanted, shape, blocks[-1][1]),
                )
                self.assertEqual(
                    blocks[-1][1] + blocks[-1][2],
                    widths[shape],
                    "and it ends the observation (flat-numeric.md §2): %d"
                    % (blocks[-1][1] + blocks[-1][2],),
                )
        fixed = S.readout(street="flop", seat=(1, False), hole=("2c", "Td"),
                          board=("Jh", "7c", "2d"), stacks=(17, 17), pot=6,
                          to_call=0, limit=(2, 0))
        six = S.six_seat_readout(street="flop", seat=(1, False), hole=("2c", "Td"),
                                 board=("Jh", "7c", "2d"), pot=6, to_call=0,
                                 limit=(2, 0))
        offsets = {shape: S.FLAT_BLOCKS_BY_SHAPE[shape] for shape in tables}
        default_values = S.floats(F.encode(F.build_encoder(S.FLAT, shape=S.DEFAULT_SHAPE),
                                           fixed))
        six_values = S.floats(F.encode(F.build_encoder(S.FLAT, shape=S.THIRD_SHAPE), six))
        for field, start, width in (("street", 0, 4), ("hole", None, 34),
                                    ("board", None, 85)):
            with self.subTest(field=field, shapes="two-seat against six-seat"):
                default_offset = dict(
                    (name, offset) for name, offset, _w in offsets[S.DEFAULT_SHAPE]
                )[field]
                six_offset = dict(
                    (name, offset) for name, offset, _w in offsets[S.THIRD_SHAPE]
                )[field]
                self.assert_floats(
                    six_values[six_offset:six_offset + width],
                    default_values[default_offset:default_offset + width],
                    "the %r block carries the same values on the six-seat row as on the "
                    "default: a seat count moves the block's offset and never its "
                    "contents (capacity.md §4, flat-numeric.md §3, ASM-44)"
                    % (field,),
                )


if __name__ == "__main__":
    unittest.main()
