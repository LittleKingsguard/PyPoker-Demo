"""FEA-5 -- `card-tokens`: the nine token blocks, the card map, the pad and the buckets.

``docs/L3/features/card-tokens.md`` §2-§6; ``docs/L2/features/encodings.md`` §4;
``docs/L3/features/encoder.md`` §3.1, §4; ``docs/L3/features/guardrails.md`` G3, G10;
``docs/L1/shapes.md`` §8 and ``docs/L1/assumptions.md`` ASM-42, ASM-44 (the history
block's capacity is the shape's, and the vocabulary does not grow with it).

Every case walks a ladder through the public `encode` only: no bucket edge is read
from a private table, and every id asserted is the id `card-tokens.md` fixes.
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


class FEA5Tokens(S.FeaturesCase):
    """The token encoding's block table, its id map and its five bucket ladders."""

    # -- the table ---------------------------------------------------------
    def test_fea5_1_the_nine_counts_sum_to_the_declared_width_and_the_blocks_land_there(self):
        """FEA-5.1 the nine token counts sum to the width the spec declares, and one worked
        readout's nine token blocks occupy the running-sum offsets of the array `encode`
        returns, with the history block last (card-tokens.md §2, §5, encoder.md §4,
        guardrails.md G3).

        The offsets are read back from the observation and never compared with this
        battery's own offset column: a table copied faithfully into the support module
        would otherwise pass against a block written one token off.
        """
        F = self.surface()
        spec = F.spec(S.TOKENS)
        counts = [count for _field, _offset, count in S.TOKEN_BLOCKS]
        declared = tuple(int(value) for value in spec["shape"])
        self.assertEqual(
            declared, (sum(counts),),
            "1 + 2 + 2 + 5 + 2 + 1 + 1 + 2 + 24 = 40 must be the width the spec declares "
            "(card-tokens.md §2, encoder.md §4): %r against a sum of %d"
            % (declared, sum(counts)),
        )
        record = S.readout(street="river", seat=(1, False), hole=("2c", "Td"),
                           stacks=(13, 12), pot=15, to_call=4, limit=(2, 0),
                           history=["preflop seat 0 folds"])
        values = S.ints(F.encode(F.build_encoder(S.TOKENS), record))
        self.assertEqual(
            len(values), sum(counts),
            "one token observation is as long as the nine counts together "
            "(card-tokens.md §2, §6): %d tokens" % (len(values),),
        )
        expected_of = {
            "street": [S.STREET_IDS["river"]],
            "seat": [S.SEAT_INDEX_BASE + 1, S.SEAT_FLAG_BASE],
            "hole": [S.card_id("2c"), S.card_id("Td")],
            "board": [S.card_id(card) for card in record["board"]],
            "stacks": [S.bucket("stacks", 13), S.bucket("stacks", 12)],
            "pot": [S.bucket("pot", 15)],
            "to_call": [S.bucket("to_call", 4)],
            "limit": [S.bucket("bet", 2), S.bucket("raises", 0)],
            "history": S.history_tokens(record["history"]),
        }
        fields = tuple(F.spec(S.TOKENS)["fields"])
        self.assertEqual(
            list(fields), [field for field, _offset, _count in S.TOKEN_BLOCKS],
            "the blocks are in the spec's field order, so the running sum of the counts "
            "is the order the observation was built in (encoder.md §3.1, §4, README.md §5 "
            "rule 3): %r" % (fields,),
        )
        offset = 0
        for field, count in zip(fields, counts):
            expected = expected_of[field]
            with self.subTest(field=field):
                self.assertEqual(
                    len(expected), count,
                    "the %r block's own token count is %d (card-tokens.md §2)"
                    % (field, count),
                )
                self.assert_ints(
                    values[offset:offset + count], expected,
                    "the %r block occupies tokens %d-%d: the running sum of the counts "
                    "before it (card-tokens.md §2-§5, encoder.md §4, guardrails.md G3)"
                    % (field, offset, offset + count),
                )
                if offset:
                    self.assertNotEqual(
                        list(values[offset - 1:offset - 1 + count]), list(expected),
                        "the %r block does not start one token earlier: a block an offset "
                        "off lands here instead (card-tokens.md §2, guardrails.md G3): %r"
                        % (field, list(values[offset - 1:offset - 1 + count])),
                    )
            offset += count
        self.assertEqual(
            offset, len(values),
            "the count sum ends exactly where the observation ends, so the last block is "
            "the history (card-tokens.md §2, guardrails.md G3): %d of %d tokens"
            % (offset, len(values)),
        )
        self.assert_ints(
            values[len(values) - counts[-1]:], S.history_tokens(record["history"]),
            "the history block is the observation's last %d tokens, read from the array's "
            "own length (card-tokens.md §2, §5)" % (counts[-1],),
        )

    def test_fea5_2_every_emitted_id_is_an_integer_inside_the_vocabulary(self):
        """FEA-5.2 every id an observation carries is an integer in 0-95, over a survey of
        readouts (card-tokens.md §1, §6, guardrails.md G10)."""
        F = self.surface()
        encoder = F.build_encoder(S.TOKENS)
        survey = [
            S.readout(),
            S.readout(street="flop", history=S.history_entries(2)),
            S.readout(street="river", seat=(1, False), hole=("As", "Ah"),
                      history=S.history_entries(23)),
            S.readout(stacks=(500, 0), pot=1000, to_call=999, limit=(9, 7)),
            S.readout(board=("Jh",)),
        ]
        for position, record in enumerate(survey):
            with self.subTest(readout=position):
                values = S.ints(F.encode(encoder, record))
                self.assertEqual(len(values), 40,
                                 "one token observation is 40 ids (card-tokens.md §2)")
                for slot, value in enumerate(values):
                    with self.subTest(readout=position, slot=slot):
                        self.assertTrue(
                            S.is_integer(value),
                            "a token id is an integer (card-tokens.md §1): %r at slot %d"
                            % (value, slot),
                        )
                        self.assertGreaterEqual(
                            value, 0,
                            "no id is below the vocabulary's first id 0 (card-tokens.md §6): "
                            "%r at slot %d" % (value, slot),
                        )
                        self.assertLess(
                            value, S.VOCABULARY,
                            "every id an observation can carry is in 0-95 (card-tokens.md "
                            "§6): %r at slot %d" % (value, slot),
                        )

    def test_fea5_3_each_block_emits_only_its_own_ids(self):
        """FEA-5.3 each of the nine blocks emits only the ids its range declares, and the
        ten id ranges tile 0-95 (card-tokens.md §2, §3, §4, §6)."""
        encoder = self.ep("build_encoder")(S.TOKENS)
        encode = self.ep("encode")
        record = S.readout(street="turn", seat=(1, False), hole=("As", "Ah"),
                           history=S.history_entries(4))
        values = S.ints(encode(encoder, record))
        ranges = {
            "street": (53, 56),
            "seat": (57, 60),
            "hole": (1, 52),
            "board": (0, 52),
            "stacks": (77, 84),
            "pot": (69, 76),
            "to_call": (61, 68),
            "limit": (85, 92),
            "history": (0, 95),
        }
        for field, offset, count in S.TOKEN_BLOCKS:
            low, high = ranges[field]
            with self.subTest(field=field):
                for slot in range(offset, offset + count):
                    self.assertTrue(
                        low <= values[slot] <= high,
                        "the %r block emits ids in %d-%d (card-tokens.md §2-§4): %r at "
                        "slot %d" % (field, low, high, values[slot], slot),
                    )
        self.assertEqual(
            values[0], S.STREET_IDS["turn"],
            "the street token of a turn readout is 55 (card-tokens.md §3): %r"
            % (values[0],),
        )
        self.assertEqual(values[1:3], [58, 59],
                         "seat 1 without the button is (58, 59) (card-tokens.md §3): %r"
                         % (values[1:3],))

    # -- the card map ------------------------------------------------------
    def test_fea5_4_the_card_ids_are_one_plus_four_ranks_plus_the_suit(self):
        """FEA-5.4 all 52 cards encode to the 52 distinct ids 1-52, rank-major and
        suit-minor, so "2c" is 1 and "As" is 52 (card-tokens.md §3, README.md §4)."""
        F = self.surface()
        encoder = F.build_encoder(S.TOKENS)
        seen = {}
        for card in S.all_cards():
            with self.subTest(card=card):
                values = S.ints(F.encode(encoder, S.readout(hole=(card, "2c"))))
                self.assertEqual(
                    values[3], S.card_id(card),
                    "card %r is id 1 + 4 * rank_index + suit_index (card-tokens.md §3): "
                    "%r, expected %r" % (card, values[3], S.card_id(card)),
                )
                self.assertEqual(
                    values[4], 1,
                    "the second hole card is the other slot, whatever the first was "
                    "(card-tokens.md §2): %r" % (values[4],),
                )
                seen[card] = values[3]
        self.assertEqual(len(set(seen.values())), 52,
                         "the 52 cards are 52 distinct ids (card-tokens.md §3): %r"
                         % (sorted(seen.values())[:8],))
        self.assertEqual(min(seen.values()), 1, "'2c' is id 1 (card-tokens.md §3)")
        self.assertEqual(max(seen.values()), 52, "'As' is id 52 (card-tokens.md §3)")
        self.assertEqual(
            seen["Td"], 34,
            "the canonical readout's 'Td' is id 1 + 4 * 8 + 1 = 34 (card-tokens.md §3)",
        )

    # -- the pad -----------------------------------------------------------
    def test_fea5_5_a_board_slot_past_the_deal_is_the_pad_zero(self):
        """FEA-5.5 the board block is five tokens and every token at or past len(board) is
        the pad 0 (card-tokens.md §3, §7, guardrails.md G10)."""
        F = self.surface()
        encoder = F.build_encoder(S.TOKENS)
        for position, street in enumerate(S.STREETS):
            with self.subTest(street=street):
                record = S.readout(street=street)
                dealt = len(record["board"])
                self.assertEqual(dealt, S.BOARD_SIZES[position],
                                 "the invented %s readout's board" % (street,))
                values = S.ints(F.encode(encoder, record))
                self.assert_ints(
                    values[5:10],
                    [S.card_id(card) for card in record["board"]]
                    + [S.PAD] * (5 - dealt),
                    "the board tokens of a %s readout" % (street,),
                )

    def test_fea5_6_the_history_block_is_the_last_24_tokens(self):
        """FEA-5.6 the history block is the last 24 tokens, one per applied action, and a
        token past the history's end is the pad 0 (card-tokens.md §2, §5)."""
        field, offset, count = S.TOKEN_BLOCKS[-1]
        self.assertEqual(
            (field, offset, count), ("history", 16, 24),
            "the history is the last block: 16 + 24 = 40 (card-tokens.md §2)",
        )
        self.assertEqual(offset + count, 40, "the history block ends the observation")
        history = ["preflop seat 0 calls 1", "flop seat 1 raises to 4"]
        values = S.ints(self.tokens(S.readout(street="flop", history=history)))
        self.assert_ints(values[16:40], S.history_tokens(history),
                         "the history tokens of a two-entry history")

    def test_fea5_7_a_to_call_of_zero_is_id_61_and_never_the_pad(self):
        """FEA-5.7 a to_call of 0 is its own id 61, never the pad 0: the boundary between
        checking and folding is a value, not an absence (card-tokens.md §3, §4,
        guardrails.md G10)."""
        F = self.surface()
        encoder = F.build_encoder(S.TOKENS)
        values = S.ints(F.encode(encoder, S.readout(street="flop", to_call=0)))
        self.assertEqual(
            values[13], 61,
            "to_call 0 is id 61 (card-tokens.md §4): %r" % (values[13],),
        )
        self.assertNotEqual(
            values[13], S.PAD,
            "the pad is not a bucket: 'nothing to call' is not 'no fact' "
            "(guardrails.md G10): %r" % (values[13],),
        )
        values = S.ints(F.encode(encoder, S.readout(to_call=1)))
        self.assertEqual(values[13], 62, "to_call 1 is id 62 (card-tokens.md §4)")

    # -- ids that are not buckets -----------------------------------------
    def test_fea5_8_a_street_is_53_plus_its_index(self):
        """FEA-5.8 the street token is 53 preflop, 54 flop, 55 turn, 56 river
        (card-tokens.md §3)."""
        encoder = self.ep("build_encoder")(S.TOKENS)
        encode = self.ep("encode")
        for street in S.STREETS:
            with self.subTest(street=street):
                values = S.ints(encode(encoder, S.readout(street=street)))
                self.assertEqual(
                    values[0], S.STREET_IDS[street],
                    "the %s street is id %d (card-tokens.md §3): %r"
                    % (street, S.STREET_IDS[street], values[0]),
                )

    def test_fea5_9_a_seat_is_57_plus_the_index_and_59_plus_the_button(self):
        """FEA-5.9 the two seat tokens are 57 + index and 59 + flag, so seat 0 with the
        button is (57, 60) (card-tokens.md §3)."""
        encoder = self.ep("build_encoder")(S.TOKENS)
        encode = self.ep("encode")
        for seat, expected in (
            ((0, True), [57, 60]),
            ((0, False), [57, 59]),
            ((1, True), [58, 60]),
            ((1, False), [58, 59]),
        ):
            with self.subTest(seat=seat):
                values = S.ints(encode(encoder, S.readout(seat=seat)))
                self.assert_ints(
                    values[1:3], expected,
                    "the seat tokens of seat %r (card-tokens.md §3)" % (seat,),
                )

    # -- the five bucket ladders ------------------------------------------
    def test_fea5_10_the_to_call_ladder_is_total_and_inside_61_to_68(self):
        """FEA-5.10 to_call's ladder -- 61:0, 62:1, 63:2, 64:3, 65:4, 66:5-6, 67:7-10,
        68:11+ -- is total and monotone over the non-negative integers (card-tokens.md §4,
        §8)."""
        F = self.surface()
        encoder = F.build_encoder(S.TOKENS)
        walked = []
        for amount in range(0, 25):
            with self.subTest(to_call=amount):
                values = S.ints(F.encode(encoder, S.readout(to_call=amount)))
                self.assertEqual(
                    values[13], S.bucket("to_call", amount),
                    "to_call %r is the id the ladder fixes (card-tokens.md §4): %r, "
                    "expected %r" % (amount, values[13], S.bucket("to_call", amount)),
                )
                self.assertIn(values[13], S.ladder_ids("to_call"),
                              "to_call's ids are 61-68 (card-tokens.md §4): %r"
                              % (values[13],))
                walked.append(values[13])
        self.assertEqual(walked, sorted(walked),
                         "the to_call ladder is monotone (card-tokens.md §4, §8): %r"
                         % (walked,))

    def test_fea5_11_the_pot_ladder_is_total_and_inside_69_to_76(self):
        """FEA-5.11 pot's ladder -- 69:0-3, 70:4-5, 71:6-8, 72:9-12, 73:13-16, 74:17-24,
        75:25-32, 76:33+ -- is total and monotone (card-tokens.md §4, §8)."""
        F = self.surface()
        encoder = F.build_encoder(S.TOKENS)
        walked = []
        for amount in range(0, 41):
            with self.subTest(pot=amount):
                values = S.ints(F.encode(encoder, S.readout(pot=amount)))
                self.assertEqual(
                    values[12], S.bucket("pot", amount),
                    "a pot of %r is the id the ladder fixes (card-tokens.md §4): %r, "
                    "expected %r" % (amount, values[12], S.bucket("pot", amount)),
                )
                self.assertIn(values[12], S.ladder_ids("pot"),
                              "pot's ids are 69-76 (card-tokens.md §4): %r"
                              % (values[12],))
                walked.append(values[12])
        self.assertEqual(walked, sorted(walked),
                         "the pot ladder is monotone (card-tokens.md §4, §8): %r"
                         % (walked,))

    def test_fea5_12_the_stacks_ladder_is_total_and_read_in_seat_order(self):
        """FEA-5.12 each stack is bucketed -- 77:0-1 ... 84:18+ -- and the two tokens are
        `stacks[0]` then `stacks[1]`, the readout's seat order, never the acting seat's
        (card-tokens.md §4, §8)."""
        F = self.surface()
        encoder = F.build_encoder(S.TOKENS)
        walked = []
        for amount in range(0, 26):
            with self.subTest(stack=amount):
                values = S.ints(F.encode(encoder, S.readout(stacks=(amount, amount))))
                self.assertEqual(
                    values[10:12], [S.bucket("stacks", amount)] * 2,
                    "a stack of %r is the id the ladder fixes (card-tokens.md §4): %r, "
                    "expected %r" % (amount, values[10:12], S.bucket("stacks", amount)),
                )
                self.assertIn(values[10], S.ladder_ids("stacks"),
                              "stacks' ids are 77-84 (card-tokens.md §4): %r"
                              % (values[10],))
                walked.append(values[10])
        self.assertEqual(walked, sorted(walked),
                         "the stacks ladder is monotone (card-tokens.md §4, §8): %r"
                         % (walked,))
        record = S.readout(seat=(1, False), stacks=(3, 10))
        values = S.ints(F.encode(encoder, record))
        self.assert_ints(
            values[10:12], [78, 81],
            "the stacks tokens are stacks[0] then stacks[1] -- 3 then 10, even though "
            "seat 1 is acting (card-tokens.md §4)",
        )

    def test_fea5_13_the_bet_size_and_raise_ladders_are_total(self):
        """FEA-5.13 the bet size in force buckets to 85:/86:/87:/88: and the raises this
        street to 89:/90:/91:/92:, both total and monotone (card-tokens.md §4, §8)."""
        F = self.surface()
        encoder = F.build_encoder(S.TOKENS)
        bets = []
        for size in range(0, 9):
            with self.subTest(bet_size=size):
                values = S.ints(F.encode(encoder, S.readout(limit=(size, 0))))
                self.assertEqual(
                    values[14], S.bucket("bet", size),
                    "a bet size of %r is the id the ladder fixes (card-tokens.md §4): %r, "
                    "expected %r" % (size, values[14], S.bucket("bet", size)),
                )
                self.assertIn(values[14], S.ladder_ids("bet"),
                              "the bet size's ids are 85-88 (card-tokens.md §4): %r"
                              % (values[14],))
                bets.append(values[14])
        self.assertEqual(bets, sorted(bets),
                         "the bet-size ladder is monotone (card-tokens.md §4): %r" % (bets,))
        raises = []
        for count in range(0, 6):
            with self.subTest(raises=count):
                values = S.ints(F.encode(encoder, S.readout(limit=(2, count))))
                self.assertEqual(
                    values[15], S.bucket("raises", count),
                    "a raise count of %r is the id the ladder fixes (card-tokens.md §4): "
                    "%r, expected %r" % (count, values[15], S.bucket("raises", count)),
                )
                self.assertIn(values[15], S.ladder_ids("raises"),
                              "the raise count's ids are 89-92 (card-tokens.md §4): %r"
                              % (values[15],))
                raises.append(values[15])
        self.assertEqual(raises, sorted(raises),
                         "the raise ladder is monotone (card-tokens.md §4): %r" % (raises,))

    # -- the worked example and the pad's exclusivity ----------------------
    def test_fea5_14_the_canonical_readout_lands_at_the_declared_offsets(self):
        """FEA-5.14 one fully worked readout is [53, 57, 60, 34, 1, 0, 0, 0, 0, 0, 84, 84,
        69, 62, 86, 89, 0 x 24] (card-tokens.md §2-§5)."""
        values = S.ints(self.tokens(S.readout()))
        self.assertEqual(len(values), 40, "one token observation is 40 ids")
        expected = (
            [53, 57, 60]
            + [34, 1]
            + [0, 0, 0, 0, 0]
            + [84, 84]
            + [69]
            + [62]
            + [86, 89]
            + [0] * 24
        )
        self.assert_ints(values, expected, "the canonical readout's token vector")
        for slot, wanted, where in (
            (0, 53, "slot 0: the preflop street"),
            (1, 57, "slot 1: seat 0"),
            (2, 60, "slot 2: the button"),
            (3, 34, "slot 3: 'Td'"),
            (4, 1, "slot 4: '2c'"),
            (5, 0, "slot 5: the first board token is not yet dealt"),
            (9, 0, "slot 9: the last board token is not yet dealt"),
            (10, 84, "slot 10: the first seat's 19 chips"),
            (11, 84, "slot 11: the other seat's 18 chips"),
            (12, 69, "slot 12: the pot of 3"),
            (13, 62, "slot 13: the 1 chip to call"),
            (14, 86, "slot 14: the small bet of 2"),
            (15, 89, "slot 15: no raise this street"),
            (16, 0, "slot 16: the history is empty"),
            (39, 0, "slot 39: the last token of the observation"),
        ):
            with self.subTest(slot=slot):
                self.assertEqual(values[slot], wanted, where)

    def test_fea5_15_only_the_board_and_the_history_emit_the_pad(self):

        """FEA-5.15 no block but the board and the history may emit 0: the pad is an
        absence, and a zero amount is a value with its own id (card-tokens.md §3, §6,
        guardrails.md G10)."""
        F = self.surface()
        encoder = F.build_encoder(S.TOKENS)
        record = S.readout(street="flop", seat=(1, False), hole=("As", "Kh"),
                           stacks=(0, 0), pot=0, to_call=0, limit=(2, 0))
        values = S.ints(F.encode(encoder, record))
        for field, offset, count in S.TOKEN_BLOCKS:
            if field in ("board", "history"):
                continue
            with self.subTest(field=field):
                for slot in range(offset, offset + count):
                    self.assertNotEqual(
                        values[slot], S.PAD,
                        "the %r block never emits the pad 0 (card-tokens.md §3, "
                        "guardrails.md G10): slot %d of %r is 0"
                        % (field, slot, record),
                    )
        self.assertEqual(values[3:5], [52, 47],
                         "hole never pads: 'As' is 52 and 'Kh' is 47 (card-tokens.md §3)")
        self.assertEqual(values[10:12], [77, 77],
                         "a stack of 0 is id 77, never the pad (guardrails.md G10)")


class FEA5ShapedCapacity(S.FeaturesCase):
    """The history block's capacity is the shape's, so the token width follows it."""

    def test_fea5_16_the_token_width_is_the_shapes_and_the_vocabulary_is_not(self):
        """FEA-5.16 the history block is one token per applied action over the shape's own
        capacity and the sixteen tokens before it do not move: `no-limit-100` declares 82
        tokens -- 16 + 66 = 82 -- while the default shape keeps 40 -- 16 + 24 -- and both
        declare the vocabulary of 96 ids, the history block's three ids 93-95 unmoved; the
        tokens before the history carry the shape's own ladder ids, so this case reads the
        two lengths and the history block itself, which no ladder reaches, and the shape
        declares its own capacity as the block's refusal threshold (shapes.md §8, ASM-42,
        ASM-44, card-tokens.md §2, §5, §6).
        """
        F = self.surface()
        record = S.readout(street="turn", seat=(1, False), hole=("As", "Ah"),
                           stacks=(96, 5), pot=151, to_call=11, limit=(26, 6),
                           history=S.history_entries(4))
        lengths = {}
        for shape in S.SHAPES:
            capacity = S.CAPACITY[shape]
            encoder = F.build_encoder(S.TOKENS, shape=shape)
            spec = F.observation_spec(encoder)
            values = S.ints(F.encode(encoder, record))
            with self.subTest(shape=shape):
                self.assertEqual(
                    tuple(spec["shape"]), S.DECLARED_BY_SHAPE[shape][S.TOKENS],
                    "the token width of %r is %d: 16 + %d = %d (shapes.md §8, ASM-42, "
                    "ASM-44): %r"
                    % (shape, S.DECLARED_BY_SHAPE[shape][S.TOKENS][0], capacity,
                       16 + capacity, spec["shape"]),
                )
                self.assertEqual(
                    len(values), S.FIXED_TOKEN_SLOTS + capacity,
                    "one token observation of %r is the sixteen tokens before the history "
                    "plus its %d-token history block (card-tokens.md §2, shapes.md §8): %d "
                    "tokens" % (shape, capacity, len(values)),
                )
                self.assertEqual(
                    len(values) - capacity, S.FIXED_TOKEN_SLOTS,
                    "the tokens before the history are 16 on every shape: the shape moves "
                    "the capacity and no other block (shapes.md §8, ASM-44): %d"
                    % (len(values) - capacity,),
                )
                self.assertEqual(
                    int(spec["vocabulary"]), S.VOCABULARY,
                    "the token vocabulary stays 96 ids on %r: a history token emits one of "
                    "the three action-kind ids and adds no id (card-tokens.md §6, "
                    "shapes.md §8): %r" % (shape, spec["vocabulary"]),
                )
                self.assert_ints(
                    values[S.FIXED_TOKEN_SLOTS:],
                    S.history_tokens(record["history"], capacity),
                    "the history block of %r is the last %d tokens, one per applied "
                    "action, the pad past the end (card-tokens.md §5, shapes.md §8)"
                    % (shape, capacity),
                )
                self.assertTrue(
                    set(values[S.FIXED_TOKEN_SLOTS:])
                    <= set(S.HISTORY_IDS.values()) | {S.PAD},
                    "the wider block emits the same three ids and the pad, and no fourth "
                    "id: the vocabulary does not grow with the capacity "
                    "(card-tokens.md §5, §6, ASM-44): %r"
                    % (sorted(set(values[S.FIXED_TOKEN_SLOTS:])),),
                )
                lengths[shape] = len(values)
        self.assertEqual(
            (lengths[S.DEFAULT_SHAPE], lengths[S.SECOND_SHAPE]), (40, 82),
            "the default shape's token width does not move and the no-cap shape's is its "
            "own: 40 and 82 (shapes.md §5, §8): %r" % (lengths,),
        )



class FEA5ThirdSeatCount(S.FeaturesCase):
    """The third row's token table, its six own seat ids and its vocabulary of 102."""

    def test_fea5_17_the_six_seat_token_table_is_122_tokens_at_its_own_offsets(self):
        """FEA-5.17 on `six-seat-no-limit-100` the token table is
        `0/1, 1/6, 7/2, 9/5, 14/6, 20/1, 21/1, 22/2, 24/98` -- the eight blocks before the
        history reaching `12 + 2 x 6 = 24` and `24 + 98 = 122` -- and one six-seat
        readout's nine token blocks land at exactly those offsets: street 56, the acting
        seat's own id in the six-token seat block, two card ids, five board ids, six
        stack buckets in seat order, the pot's and to_call's ids over the row's ladders,
        the limit pair, and 98 history tokens with the pad past the end (capacity.md §2,
        card-tokens.md §2-§5, seats.md §3, ASM-42, ASM-44)."""
        F = self.surface()
        expected = (
            ("street", 0, 1),
            ("seat", 1, 6),
            ("hole", 7, 2),
            ("board", 9, 5),
            ("stacks", 14, 6),
            ("pot", 20, 1),
            ("to_call", 21, 1),
            ("limit", 22, 2),
            ("history", 24, 98),
        )
        self.assertEqual(
            S.THIRD_TOKEN_BLOCKS, expected,
            "the six-seat row's token table is the design's, field for field, offset for "
            "offset and count for count (capacity.md §2, card-tokens.md §2, seats.md §3): "
            "%r" % (S.THIRD_TOKEN_BLOCKS,),
        )
        counts = [count for _field, _offset, count in S.THIRD_TOKEN_BLOCKS]
        self.assertEqual(
            (sum(counts), 24 + 98, 12 + 2 * 6 + 98),
            (122, 122, 122),
            "1 + 6 + 2 + 5 + 6 + 1 + 1 + 2 + 98 = 122: the nine counts, the pre-history "
            "sum plus the history, and the row's arithmetic are one number (capacity.md "
            "§2, encoder.md §4): %r" % (sum(counts),),
        )
        record = S.six_seat_readout(street="river", seat=(2, True), hole=("As", "Ah"),
                                    stacks=(100, 76, 40, 20, 10, 5), pot=96,
                                    to_call=25, limit=(100, 3),
                                    history=S.history_entries(3))
        values = S.ints(F.encode(F.build_encoder(S.TOKENS, shape=S.THIRD_SHAPE), record))
        self.assertEqual(
            len(values), S.DECLARED_BY_SHAPE[S.THIRD_SHAPE][S.TOKENS][0],
            "one token observation of the third row is the declared 122 ids "
            "(capacity.md §2, surface.md §5): %d" % (len(values),),
        )
        expected_of = {
            "street": [S.STREET_IDS["river"]],
            "seat": [S.SEAT_TOKEN_BASE + 2 if slot == 2 else S.PAD for slot in range(6)],
            "hole": [S.card_id("As"), S.card_id("Ah")],
            "board": [S.card_id(card) for card in record["board"]],
            "stacks": [S.bucket_on(S.THIRD_SHAPE, "stacks", amount)
                       for amount in record["stacks"]],
            "pot": [S.bucket_on(S.THIRD_SHAPE, "pot", 96)],
            "to_call": [S.bucket_on(S.THIRD_SHAPE, "to_call", 25)],
            "limit": [S.bucket_on(S.THIRD_SHAPE, "bet", 100),
                      S.bucket_on(S.THIRD_SHAPE, "raises", 3)],
            "history": S.history_tokens(record["history"],
                                        S.CAPACITY[S.THIRD_SHAPE]),
        }
        for field, offset, count in expected:
            with self.subTest(field=field):
                self.assertEqual(
                    len(expected_of[field]), count,
                    "the %r block is %d tokens on the six-seat row (capacity.md §2, "
                    "card-tokens.md §2, seats.md §3): %d"
                    % (field, count, len(expected_of[field])),
                )
                self.assert_ints(
                    values[offset:offset + count], expected_of[field],
                    "the %r block of a six-seat readout occupies tokens %d-%d with the "
                    "design's ids (card-tokens.md §3-§5, seats.md §3)"
                    % (field, offset, offset + count),
                )
                if offset:
                    self.assertNotEqual(
                        list(values[offset - 1:offset - 1 + count]),
                        list(expected_of[field]),
                        "the %r block does not start one token earlier: a block an offset "
                        "off lands here instead (card-tokens.md §2, guardrails.md G3): %r"
                        % (field, list(values[offset - 1:offset - 1 + count])),
                    )
        self.assert_ints(
            values[24:], S.history_tokens(record["history"], S.CAPACITY[S.THIRD_SHAPE]),
            "the history block is the last 98 tokens, oldest first, the pad past the "
            "history's end (card-tokens.md §5, capacity.md §2)",
        )
        self.assert_ints(
            values[24 + len(record["history"]):],
            [S.PAD] * (S.CAPACITY[S.THIRD_SHAPE] - len(record["history"])),
            "the tokens past the three applied actions are the pad 0, and the capacity's "
            "98 tokens are all declared (card-tokens.md §5, ASM-42): %r"
            % (values[27:33],),
        )

    def test_fea5_18_the_six_seat_seat_tokens_are_96_plus_the_seat_and_the_pad_elsewhere(self):
        """FEA-5.18 on `six-seat-no-limit-100` the six-token seat block holds `96 + i` at
        the acting seat's slot and the pad `0` in the other five, so ids 96-101 are the
        row's own and every one is reachable, while a two-seat row still writes
        `[57 + index, 59 + flag]` and its 96-id vocabulary is unmoved (seats.md §3,
        card-tokens.md §3, §6, capacity.md §4, ASM-44)."""
        F = self.surface()
        offset = {field: position for field, position, _count
                  in S.THIRD_TOKEN_BLOCKS}["seat"]
        self.assertEqual(offset, 1, "the six-token seat block starts at token 1")
        seen = set()
        for index in range(S.SEATS[S.THIRD_SHAPE]):
            for flag in (True, False):
                with self.subTest(seat=(index, flag)):
                    values = S.ints(F.encode(
                        F.build_encoder(S.TOKENS, shape=S.THIRD_SHAPE),
                        S.six_seat_readout(seat=(index, flag))))
                    block = values[offset:offset + 6]
                    self.assertEqual(
                        block,
                        [S.SEAT_TOKEN_BASE + index if slot == index else S.PAD
                         for slot in range(6)],
                        "the seat block of seat index %d: 96 + the slot, the pad in the "
                        "other five (card-tokens.md §3, seats.md §3): %r"
                        % (index, block),
                    )
                    self.assertEqual(
                        [ident for ident in block if ident != S.PAD],
                        [S.SEAT_TOKEN_BASE + index],
                        "exactly one non-pad id, and it is the acting seat's own "
                        "(card-tokens.md §3, ASM-44): %r" % (block,),
                    )
                    self.assertIn(
                        S.SEAT_TOKEN_BASE + index, S.SIX_SEAT_SEAT_IDS,
                        "the id is one of the row's six, 96-101 (seats.md §3, ASM-44): "
                        "%r" % (S.SEAT_TOKEN_BASE + index,),
                    )
                    seen.add(block[index])
        self.assertEqual(
            tuple(sorted(seen)), S.SIX_SEAT_SEAT_IDS,
            "all six of 96-101 were emitted, one per seat slot (seats.md §3, "
            "ASM-44): %r" % (tuple(sorted(seen)),),
        )
        self.assertEqual(
            S.SIX_SEAT_SEAT_IDS, (96, 97, 98, 99, 100, 101),
            "the row's six ids are 96 to 101, above every id the two-seat rows use "
            "(seats.md §3, card-tokens.md §6, ASM-44): %r"
            % (S.SIX_SEAT_SEAT_IDS,),
        )
        for shape in S.SHAPES:
            for seat in ((0, True), (0, False), (1, True), (1, False)):
                with self.subTest(shape=shape, seat=seat):
                    values = S.ints(F.encode(
                        F.build_encoder(S.TOKENS, shape=shape),
                        S.readout(seat=seat)))
                    position = {field: start for field, start, _count
                                in S.TOKEN_BLOCKS_BY_SHAPE[shape]}["seat"]
                    self.assert_ints(
                        values[position:position + 2],
                        [S.SEAT_INDEX_BASE + seat[0],
                         S.SEAT_FLAG_BASE + (1 if seat[1] else 0)],
                        "a two-seat row still writes 57 + index and 59 + flag: the six "
                        "seat ids rename nothing (card-tokens.md §3, seats.md §3, "
                        "ASM-44): %r" % (values[position:position + 2],),
                    )
        self.assertEqual(
            S.VOCABULARY_BY_SHAPE[S.THIRD_SHAPE],
            max(S.SIX_SEAT_SEAT_IDS) + 1,
            "the 102-id vocabulary is the row's top seat id plus one, so no emitted id "
            "leaves it (card-tokens.md §6, capacity.md §4): %r against %r"
            % (S.VOCABULARY_BY_SHAPE[S.THIRD_SHAPE], max(S.SIX_SEAT_SEAT_IDS) + 1),
        )

    def test_fea5_19_the_six_seat_stacks_are_bucketed_one_per_seat_in_seat_order(self):
        """FEA-5.19 the six-seat stacks block is six buckets, one per seat in the
        readout's seat order, over the same ladder `no-limit-100` declares -- 5, 10, 20,
        40, 60, 80, 95 and then unbounded -- and the acting seat never reorders them, so
        a six-stack readout reads the same tokens on any seat (seats.md §3, card-tokens.md
        §4, capacity.md §4, ASM-44)."""
        F = self.surface()
        self.assertEqual(
            S.SIX_SEAT_LADDERS["stacks"], S.SECOND_LADDERS["stacks"],
            "the six-seat stacks ladder is the two-seat uncapped row's: a stack is "
            "bounded by 100 on both, so the seat count re-edges no stack (capacity.md §2, "
            "seats.md §2, card-tokens.md §4): %r" % (S.SIX_SEAT_LADDERS["stacks"],),
        )
        offset = {field: position for field, position, _count
                  in S.THIRD_TOKEN_BLOCKS}["stacks"]
        self.assertEqual(offset, 14, "the six-token stacks block starts at token 14")
        stacks = (0, 6, 11, 21, 41, 61)
        for index in range(S.SEATS[S.THIRD_SHAPE]):
            with self.subTest(seat=index):
                values = S.ints(F.encode(
                    F.build_encoder(S.TOKENS, shape=S.THIRD_SHAPE),
                    S.six_seat_readout(seat=(index, index == 0), stacks=stacks)))
                block = values[offset:offset + 6]
                self.assertEqual(
                    block,
                    [S.bucket_on(S.THIRD_SHAPE, "stacks", amount)
                     for amount in stacks],
                    "the stacks block of seat %d is the six buckets in seat order: the "
                    "acting seat does not move them (card-tokens.md §4, seats.md §3)"
                    % (index,),
                )
                self.assertEqual(
                    block,
                    S.ints(F.encode(
                        F.build_encoder(S.TOKENS, shape=S.THIRD_SHAPE),
                        S.six_seat_readout(seat=(0, True), stacks=stacks)))[
                            offset:offset + 6],
                    "one stacks tuple reads the same six buckets on every seat "
                    "(card-tokens.md §4, ASM-44): %r" % (block,),
                )
                for slot, amount in enumerate(stacks):
                    with self.subTest(seat=index, slot=slot, stack=amount):
                        self.assertIn(
                            block[slot], S.ladder_ids("stacks"),
                            "a six-seat stack id is one of 77-84, the same ids every row "
                            "emits (card-tokens.md §4, §6): %r" % (block[slot],),
                        )
                        self.assertEqual(
                            block[slot],
                            S.bucket_on(S.SECOND_SHAPE, "stacks", amount),
                            "and it is the id the uncapped row's ladder gives the same "
                            "stack (card-tokens.md §4, capacity.md §2): %r"
                            % (block[slot],),
                        )
        walked = []
        for amount in (0, 5, 6, 10, 11, 20, 21, 40, 41, 60, 61, 80, 81, 95, 96, 100):
            with self.subTest(stack=amount):
                values = S.ints(F.encode(
                    F.build_encoder(S.TOKENS, shape=S.THIRD_SHAPE),
                    S.six_seat_readout(stacks=(amount,) * 6)))
                self.assertEqual(
                    values[offset:offset + 6],
                    [S.bucket_on(S.THIRD_SHAPE, "stacks", amount)] * 6,
                    "a stack of %r is one id on all six seats (card-tokens.md §4, "
                    "seats.md §3): %r" % (amount, values[offset:offset + 6]),
                )
                walked.append(values[offset])
        self.assertEqual(
            walked, sorted(walked),
            "the six-seat stacks ladder is monotone, so a larger stack is never a lower "
            "bucket (card-tokens.md §4, §8): %r" % (walked,),
        )

    def test_fea5_20_every_six_seat_id_is_inside_the_vocabulary_of_102(self):
        """FEA-5.20 every id a six-seat observation carries is an integer in 0-101: no
        block leaves the row's vocabulary, whose six seat ids 96-101 sit above the 96
        the two-seat rows declare, and the two-seat rows' observations still stay inside
        their own 96 (card-tokens.md §1, §6, capacity.md §4, seats.md §3, ASM-44)."""
        F = self.surface()
        survey = [
            S.six_seat_readout(),
            S.six_seat_readout(seat=(5, False), hole=("As", "Ah"),
                               stacks=(100, 96, 80, 60, 40, 5), pot=600, to_call=99,
                               limit=(100, 50), history=S.history_entries(98)),
            S.six_seat_readout(seat=(3, True), stacks=(500, 0, 100, 1, 99, 2),
                               pot=1000, to_call=999, limit=(999, 999),
                               history=S.history_entries(1)),
            S.six_seat_readout(street="river", seat=(1, False),
                               stacks=(0, 0, 0, 0, 0, 0), pot=0, to_call=0,
                               limit=(0, 0)),
        ]
        for position, record in enumerate(survey):
            with self.subTest(readout=position):
                values = S.ints(F.encode(
                    F.build_encoder(S.TOKENS, shape=S.THIRD_SHAPE), record))
                self.assertEqual(
                    len(values), 122,
                    "one six-seat token observation is 122 ids (capacity.md §2): %d"
                    % (len(values),),
                )
                for slot, value in enumerate(values):
                    with self.subTest(readout=position, slot=slot):
                        self.assertTrue(
                            S.is_integer(value),
                            "a token id is an integer (card-tokens.md §1): %r at slot %d"
                            % (value, slot),
                        )
                        self.assertGreaterEqual(
                            value, 0,
                            "no id is below the vocabulary's first id 0 (card-tokens.md "
                            "§6): %r at slot %d" % (value, slot),
                        )
                        self.assertLess(
                            value, S.VOCABULARY_BY_SHAPE[S.THIRD_SHAPE],
                            "every id the six-seat row can carry is in 0-101, the "
                            "vocabulary its encoder declares (card-tokens.md §6, "
                            "capacity.md §4, ASM-44): %r at slot %d" % (value, slot),
                        )
        seat_ids = set()
        for index in range(6):
            values = S.ints(F.encode(
                F.build_encoder(S.TOKENS, shape=S.THIRD_SHAPE),
                S.six_seat_readout(seat=(index, True))))
            seat_ids.update(value for value in values[1:7] if value != S.PAD)
        self.assertEqual(
            sorted(seat_ids), [96, 97, 98, 99, 100, 101],
            "the ids at the top of the vocabulary are the six seat ids and no other "
            "block reaches them (card-tokens.md §6, seats.md §3, ASM-44): %r"
            % (sorted(seat_ids),),
        )
        for shape in S.SHAPES:
            with self.subTest(shape=shape, vocabulary=96):
                values = S.ints(F.encode(
                    F.build_encoder(S.TOKENS, shape=shape),
                    S.readout(seat=(1, True), stacks=(96, 5), pot=151, to_call=11,
                              limit=(26, 6), history=S.history_entries(2))))
                self.assertLess(
                    max(values), S.VOCABULARY_BY_SHAPE[shape],
                    "a two-seat row's ids stay inside its own 96, so the third row's "
                    "102 is an addition and not a renaming (card-tokens.md §6, "
                    "capacity.md §4, ASM-44): %r" % (max(values),),
                )
                self.assertNotIn(
                    min(S.SIX_SEAT_SEAT_IDS), values,
                    "no two-seat row emits one of the six seat ids 96-101: they are the "
                    "third row's own (seats.md §3, ASM-44): %r" % (values[1:3],),
                )


if __name__ == "__main__":
    unittest.main()
