"""ENG-4 -- the ten facts of the readout.

``docs/L2/engine/environment.md`` §1, §2; ``docs/L3/engine/readout.md`` §2-§5;
``docs/L1/battery.md`` §3 FAM-2 and FAM-16 (D-3).

The readout is the information set: exactly ten keys, the acting seat's own
cards and nothing of the opponent's, and the facts the game's life fixes -- a
board of 0, 3, 4 or 5 cards and 40 chips conserved at every decision.
"""

import os
import sys
import unittest

try:  # discovered as part of a tests.engine package
    from . import _engine_support as S
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _engine_support as S  # noqa: E402


class ENG4Readout(S.EngineCase):
    """The ten facts, their values, and what the readout may never expose."""

    def walks(self):
        """The readouts of a few driven hands: always-call at three seeds and
        always-raise at two, so the facts are read at over forty decisions."""
        out = []
        for seed in (S.SEED_A, S.SEED_B, S.SEED_C):
            out.extend(entry[0] for entry in self.drive(seed, S.always_call)[0])
        for seed in (S.SEED_D, S.SEED_E):
            out.extend(entry[0] for entry in self.drive(seed, S.always_raise)[0])
        return out

    def test_eng4_1_the_key_set_is_exactly_the_ten_facts(self):
        """ENG-4.1 the key set is exactly street, seat, hole, board, stacks, pot,
        to_call, limit, history, legal -- at several seeds and several decisions
        (environment.md §2, readout.md §2, FAM-2)."""
        readings = [self.readout(self.hand(seed)) for seed in S.SEEDS[:6]]
        readings.extend(self.walks())
        self.assertTrue(len(readings) > 12, "the case reads the facts at many decisions")
        for facts in readings:
            self.assertEqual(
                set(facts), set(S.FACTS),
                "the readout is a closed information set of exactly ten facts "
                "(environment.md §2): %r" % (sorted(facts),),
            )

    def test_eng4_2_the_first_decision_of_any_seed_is_the_declared_one(self):
        """ENG-4.2 the first decision of any seed reads preflop, pot 3, stacks
        (19, 18) summing to 37, to_call 1, seat (0, True), two hole cards, no board
        and the empty history (environment.md §1, hand.md §4, readout.md §5)."""
        first = self.readout(self.hand(S.SEED_A))
        self.assertEqual(first["street"], "preflop", "a hand is dealt preflop")
        self.assertEqual(first["pot"], 3, "the two blinds are in the pot: 1 + 2")
        self.assertEqual(tuple(first["stacks"]), (19, 18),
                         "seat 0 posts the small blind and seat 1 the big one (hand.md §3)")
        for seed in S.SEEDS:
            with self.subTest(seed=seed):
                facts = self.readout(self.hand(seed))
                self.assertEqual(sum(S.numbers(facts["stacks"])), 37, "the stacks hold 20 + 20 - 3")
                self.assertEqual(facts["to_call"], 1, "the button owes the big blind one chip")
                self.assertEqual(
                    tuple(facts["seat"]), (0, True),
                    "seat 0 holds the button and acts first preflop (environment.md §1)",
                )
                self.assertEqual(len(facts["hole"]), 2, "the acting seat holds two cards")
                self.assertEqual(len(facts["board"]), 0, "no public card before the flop")
                self.assertEqual(
                    facts["history"], [],
                    "history is the empty list before the first applied action "
                    "(readout.md §2, FAM-16.2)",
                )
                self.assertEqual(
                    list(facts["legal"]), list(S.ACTIONS),
                    "facing the big blind, fold, check/call and raise are all legal, in the "
                    "vocabulary's order (surface.md §2, stepping.md §1)",
                )

    def test_eng4_3_the_facts_conserve_the_tables_chips_at_every_decision(self):
        """ENG-4.3 pot + sum(stacks) == 40 at every decision of several played hands
        (environment.md §1, hand.md §4)."""
        for facts in self.walks():
            self.assertEqual(
                facts["pot"] + sum(S.numbers(facts["stacks"])), 40,
                "committed chips sit in the pot and never in a stack, so the facts partition "
                "the 40 chips the hand began with (environment.md §1): %r" % (facts,),
            )

    def test_eng4_4_the_board_grows_by_street_and_the_two_facts_agree(self):
        """ENG-4.4 board lengths are only 0, 3, 4 or 5, street is one of the four
        declared names, and 0/3/4/5 mean preflop/flop/turn/river (readout.md §2,
        environment.md §2)."""
        for facts in self.walks():
            size = len(facts["board"])
            self.assertIn(
                size, S.BOARD_SIZES,
                "the board holds 0, 3, 4 or 5 public cards (environment.md §2): %r" % (facts,),
            )
            self.assertIn(facts["street"], S.STREETS,
                          "the street is one of the four declared strings: %r" % (facts,))
            self.assertEqual(
                facts["street"], S.STREET_OF_SIZE[size],
                "a board of %d cards is the %s, so street and board cannot disagree "
                "(readout.md §2)" % (size, S.STREET_OF_SIZE[size]),
            )

    def test_eng4_5_cards_are_the_declared_spelling_and_the_acting_seats_own(self):
        """ENG-4.5 every card is a two-character string of the declared alphabets and
        is distinct within the readout, and hole is the acting seat's two cards --
        the two seats hold four different cards (readout.md §3, §4)."""
        for facts in self.walks():
            seen = []
            for card in list(facts["hole"]) + list(facts["board"]):
                self.assertTrue(
                    S.card_spelling_ok(card),
                    "a card is a two-character str, rank from %r and suit from %r "
                    "(readout.md §3): %r" % (S.RANKS, S.SUITS, card),
                )
                seen.append(card)
            self.assertEqual(len(seen), len(set(seen)),
                             "no card appears twice in one readout (readout.md §3): %r" % (facts,))
            self.assertEqual(len(facts["hole"]), 2, "the acting seat holds exactly two cards")

        first = self.readout(self.hand(S.SEED_A))
        dealt = list(first["hole"])
        second = self.readout(self.step(self.hand(S.SEED_A), "check-call"))
        other = list(second["hole"])
        self.assertEqual(len(set(dealt + other)), 4,
                         "hole is the acting seat's own cards, so the button's two and the big "
                         "blind's two are four different cards (readout.md §4)")

    def test_eng4_6_the_seat_fact_is_the_index_then_the_button_flag(self):
        """ENG-4.6 seat[0] is the acting index 0 or 1 and seat[1] is True exactly when
        it is 0; the first decision is seat 0 and the flop's first decision is seat 1
        (environment.md §2, readout.md §2, FAM-16)."""
        for facts in self.walks():
            seat = facts["seat"]
            self.assertEqual(len(seat), 2, "the seat fact is an index and a flag (readout.md §2)")
            self.assertIn(seat[0], (0, 1), "the acting seat is seat 0 or seat 1: %r" % (seat,))
            self.assertIsInstance(seat[0], int, "the seat index is a number")
            self.assertIsInstance(seat[1], bool, "the button flag is a boolean: %r" % (seat,))
            self.assertEqual(
                seat[1], seat[0] == 0,
                "the flag says whether the seat holds the button, and the button is seat 0 "
                "(readout.md §2): %r" % (seat,),
            )

        walk, _ = self.drive(S.SEED_F, S.always_call)
        self.assertEqual(walk[0][0]["seat"][0], 0, "seat 0 acts first preflop (environment.md §1)")
        flop = [entry[0] for entry in walk if entry[0]["street"] == "flop"]
        self.assertTrue(flop, "the driven hand reaches the flop")
        self.assertEqual(
            flop[0]["seat"][0], 1,
            "seat 1 acts first on the flop, the turn and the river (environment.md §1)",
        )

    def test_eng4_7_the_limit_is_the_bet_size_and_the_raises_of_the_street(self):
        """ENG-4.7 limit is (bet size, raises so far): 2 preflop and flop, 4 on the
        turn and river, and 0 raises at the start of every street (readout.md §2,
        ASM-6)."""
        for facts in self.walks():
            limit = facts["limit"]
            self.assertEqual(len(limit), 2, "limit is a pair of numbers (readout.md §2)")
            expected = 2 if facts["street"] in ("preflop", "flop") else 4
            self.assertEqual(
                limit[0], expected,
                "the fixed bet in force is 2 on the pre-flop and flop and 4 on the turn and "
                "river (ASM-6): %r at the %s" % (limit, facts["street"]),
            )
            self.assertGreaterEqual(limit[1], 0, "a raise count cannot be negative: %r" % (limit,))

        walk, _ = self.drive(S.SEED_A, S.always_raise)
        starts = {}
        previous = None
        for facts, _legal, _action in walk:
            if facts["street"] != previous:
                starts.setdefault(facts["street"], facts["limit"])
            previous = facts["street"]
        for street in ("preflop", "flop", "turn", "river"):
            if street in starts:
                self.assertEqual(
                    starts[street][1], 0,
                    "no bet has been made when a street opens, so its raise count is 0 "
                    "(readout.md §2): %r at the %s" % (starts[street], street),
                )

    def test_eng4_8_to_call_is_bounded_by_the_acting_seat_its_own_stack(self):
        """ENG-4.8 to_call is never negative and never more than the acting seat's own
        stack, so a call for less is bounded (environment.md §2, readout.md §2)."""
        for facts in self.walks():
            to_call = facts["to_call"]
            self.assertIsInstance(S.numbers(to_call)[0], int, "to_call is one number")
            self.assertGreaterEqual(to_call, 0, "to_call is 0 or positive: %r" % (facts,))
            own = facts["stacks"][facts["seat"][0]]
            self.assertLessEqual(
                to_call, own,
                "to_call is never more than the acting seat's own stack (environment.md §2): "
                "%r" % (facts,),
            )

    def test_eng4_9_the_readout_never_exposes_the_opponent(self):
        """ENG-4.9 the non-acting seat's two cards are absent from every fact of a
        readout taken while it is not acting (readout.md §4, D-3, FAM-2)."""
        hand = self.hand(S.SEED_A)
        mine = self.readout(hand)
        self.assertEqual(mine["seat"][0], 0, "seat 0 acts first, so seat 1 is the opponent here")
        theirs = list(self.readout(self.step(hand, "check-call"))["hole"])
        self.assertEqual(len(theirs), 2, "the big blind holds two cards")
        text = S.leaves(mine)
        for card in theirs:
            self.assertNotIn(
                card, text,
                "the readout of one decision never carries the non-acting seat's hole cards, "
                "in any form (readout.md §4, D-3): %r appeared in %r" % (card, mine),
            )
        self.assertEqual(
            set(theirs) & set(mine["hole"]), set(),
            "the two seats hold four different cards, so the absence check is about the "
            "opponent's cards and not about a coincidence of tokens (readout.md §3)",
        )

    def test_eng4_10_legal_matches_the_entry_point_and_a_readout_is_fresh(self):
        """ENG-4.10 readout's legal equals legal_actions in value and order, readout is
        deterministic, and it hands back a fresh mapping whose lists are copies
        (readout.md §1, §5, surface.md §5, §6)."""
        hand = self.hand(S.SEED_B)
        before = self.readout(hand)
        self.assertEqual(
            list(before["legal"]), list(self.legal(hand)),
            "readout's legal fact is the same tuple legal_actions returns, in the same order "
            "(readout.md §2, surface.md §6)",
        )
        self.assertEqual(self.readout(hand), before, "two reads of one hand are equal")

        before["history"].append("tampered")
        before["hole"] = ()
        before["pot"] = -1
        before["legal"] = ()
        fresh = self.readout(hand)
        self.assertEqual(fresh["history"], [], "a caller's edit of the history cannot reach the hand")
        self.assertEqual(fresh["pot"], 3, "a caller's edit of the pot cannot reach the hand")
        self.assertEqual(len(fresh["hole"]), 2, "a caller's edit of the hole cannot reach the hand")
        self.assertEqual(list(fresh["legal"]), list(S.ACTIONS),
                         "a caller's edit of legal cannot reach the hand")


if __name__ == "__main__":
    unittest.main()
