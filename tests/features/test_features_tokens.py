"""FEA-5 -- `card-tokens`: the nine token blocks, the card map, the pad and the buckets.

``docs/L3/features/card-tokens.md`` §2-§6; ``docs/L2/features/encodings.md`` §4;
``docs/L3/features/encoder.md`` §3.1, §4; ``docs/L3/features/guardrails.md`` G3, G10.

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


if __name__ == "__main__":
    unittest.main()
