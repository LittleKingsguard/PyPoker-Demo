"""FAM-2, D-3 — the information set is exactly the ten declared facts.

`docs/L2/engine/environment.md` §2 and `surface.md` §5.  The readout is the closed
information set: exactly ten keys, no eleventh, the acting seat's own cards and never
the other seat's, 0/3/4/5 board cards as the street reveals them, `legal` the same
descriptors `legal_actions` returns, `history` the empty list before the first action
and one entry longer per action, `seat` the acting seat with its button flag, and
`pot` plus the two `stacks` conserving the forty chips the hand began with.
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


class FAM2InformationSet(S.EngineCase):
    """D-3's information set, through a whole hand."""

    def test_fam2_10_readout_carries_exactly_the_ten_facts(self):
        """FAM-2.10 the readout's keys are exactly environment.md §2's ten facts."""
        for seed in (S.SEED_A, S.SEED_B, S.SEED_C):
            steps, _ = self.walk(seed, limit=S.DECISION_BOUND)
            self.assertTrue(steps, "a hand has at least one decision; seed %r" % (seed,))
            for position, step in enumerate(steps):
                self.assertEqual(
                    set(step.readout),
                    set(S.READOUT_FACTS),
                    "the information set is closed: decision %d of seed %r must carry "
                    "exactly the ten facts and no eleventh (environment.md §2, D-3); it "
                    "carried %r" % (position, seed, sorted(str(key) for key in step.readout)),
                )

    def test_fam2_11_the_board_reveals_what_the_street_says(self):
        """FAM-2.11 the board holds 0, 3, 4 or 5 cards and never an unrevealed one."""
        for seed in (S.SEED_D, S.SEED_E):
            steps, _ = self.walk(seed, limit=S.DECISION_BOUND)
            self.assertTrue(
                steps, "the battery needs the decisions of seed %r to read the board: %r"
                % (seed, steps))
            seen = []
            for position, step in enumerate(steps):
                street = step.readout["street"]
                self.assertIn(
                    street, S.STREETS,
                    "the street is one of preflop, flop, turn and river (environment.md §2); "
                    "seed %r read %r at decision %d" % (seed, street, position),
                )
                board = S.card_list(step.readout["board"], "the readout's board fact")
                self.assertEqual(
                    len(board), S.BOARD_LENGTH[street],
                    "street %r reveals %d public cards (environment.md §2); seed %r read %r"
                    % (street, S.BOARD_LENGTH[street], seed, board),
                )
                for earlier in seen:
                    if len(board) >= len(earlier):
                        self.assertEqual(
                            S.canon(board[:len(earlier)]), S.canon(earlier),
                            "a revealed board card stays; the board only grows "
                            "(environment.md §1): %r then %r" % (earlier, board),
                        )
                seen.append(board)

    def test_fam2_12_history_is_the_empty_list_then_one_entry_per_action(self):
        """FAM-2.12 history is [] before the first action and one entry longer per action."""
        seed = S.SEED_F
        first = self.readout(self.new_hand(seed))
        self.assertIsInstance(
            first["history"], list,
            "history is a list of the hand's public actions (environment.md §2); got %r"
            % (first["history"],),
        )
        self.assertEqual(
            first["history"], [],
            "before the first action history is the empty list (environment.md §2)",
        )
        steps, _ = self.walk(seed, limit=S.DECISION_BOUND)
        for position, step in enumerate(steps):
            self.assertIsInstance(step.readout["history"], list, "history is a list (§2)")
            self.assertEqual(
                len(step.readout["history"]), position,
                "one applied action appends exactly one entry (surface.md §7): decision %d "
                "of seed %r read %d entries" % (position, seed, len(step.readout["history"])),
            )
        replay, _ = self.walk(seed, limit=S.DECISION_BOUND)
        self.assertEqual(len(steps), len(replay), "one seed replays one hand (surface.md §4)")
        for position, (left, right) in enumerate(zip(steps, replay)):
            self.assertEqual(
                [str(entry) for entry in left.readout["history"]],
                [str(entry) for entry in right.readout["history"]],
                "history prints stably so two records of one deal compare "
                "(environment.md §2): decision %d differed" % (position,),
            )

    def test_fam2_13_legal_is_legal_actions_in_value_and_order(self):
        """FAM-2.13 readout's `legal` is legal_actions for the same hand (§6, §5)."""
        steps, _ = self.walk(S.SEED_G, limit=S.DECISION_BOUND)
        self.assertTrue(steps, "the battery needs the hand's decisions to compare its legal sets")
        for position, step in enumerate(steps):
            legal = S.descriptor_list(
                self.legal_actions(step.hand), "legal_actions of the hand at its decision"
            )
            self.assertEqual(
                len(legal), len(step.readout["legal"]),
                "readout's legal fact holds the descriptors legal_actions returns "
                "(environment.md §2); decision %d returned %r against %r"
                % (position, legal, step.readout["legal"]),
            )
            self.assertTrue(
                S.descriptors_equal(legal, step.readout["legal"]),
                "readout's legal fact is legal_actions in value and order (surface.md §6); "
                "decision %d: %r against %r" % (position, legal, step.readout["legal"]),
            )

    def test_fam2_14_the_seat_fact_names_the_acting_seat_and_the_button(self):
        """FAM-2.14 seat is the acting seat's index and whether it holds the button."""
        steps, _ = self.walk(S.SEED_H, limit=S.DECISION_BOUND)
        self.assertGreaterEqual(len(steps), 4, "the battery needs several decisions")
        for step in steps:
            index, button = S.seat_fact(step.readout["seat"])
            self.assertIn(
                index, (0, 1),
                "the seat fact's first number is the acting seat, 0 or 1 "
                "(environment.md §2); got %r" % (step.readout["seat"],),
            )
            self.assertEqual(
                button, index == 0,
                "seat 0 holds the button, seat 1 does not (surface.md §4): the seat fact "
                "%r says otherwise" % (step.readout["seat"],),
            )
        first_index, _ = S.seat_fact(steps[0].readout["seat"])
        self.assertEqual(
            first_index, 0,
            "seat 0 acts first preflop (environment.md §1); the first decision named %r"
            % (first_index,),
        )
        flop = None
        for step in steps:
            if step.readout["street"] == "flop":
                flop = step
                break
        self.assertIsNotNone(flop, "the always-call walk reaches the flop")
        flop_index, _ = S.seat_fact(flop.readout["seat"])
        self.assertEqual(
            flop_index, 1,
            "seat 1 acts first on the flop (environment.md §1); the flop's first decision "
            "named %r" % (flop_index,),
        )

    def test_fam2_15_stacks_and_pot_conserve_the_forty_chips(self):
        """FAM-2.15 pot plus the two stacks is the 40 chips the hand began with."""
        for seed in (S.SEED_I, S.SEED_J, S.SEED_K):
            steps, _ = self.walk(seed, limit=S.DECISION_BOUND)
            self.assertTrue(steps, "the battery needs the hand's decisions: seed %r" % (seed,))
            for position, step in enumerate(steps):
                stacks = S.count_list(step.readout["stacks"], "the readout's stacks fact")
                pot = S.one_number(step.readout["pot"], "the readout's pot fact")
                self.assertEqual(
                    sum(stacks) + pot, 2 * S.STARTING_STACKS,
                    "committed chips sit in pot and never in a stack, so pot plus the two "
                    "stacks is 40 at every decision (environment.md §1); decision %d of "
                    "seed %r read pot %r and stacks %r"
                    % (position, seed, pot, stacks),
                )
                self.assertTrue(
                    all(value >= 0 for value in stacks),
                    "a stack holds chips behind and never a negative count: %r" % (stacks,),
                )

    def test_fam2_16_the_acting_seat_sees_only_its_own_cards(self):
        """FAM-2.16 hole is the acting seat's two cards; the other seat's are never exposed."""
        steps, _ = self.walk(S.SEED_L, limit=S.DECISION_BOUND)
        self.assertTrue(steps, "the battery needs the hand's decisions to compare its cards")
        holes = {}
        for step in steps:
            index, _ = S.seat_fact(step.readout["seat"])
            hole = S.card_list(step.readout["hole"], "the readout's hole fact")
            self.assertEqual(
                len(hole), 2,
                "the acting seat holds two cards (environment.md §2); seat %r read %r"
                % (index, hole),
            )
            self.assertNotEqual(
                S.canon(hole[0]), S.canon(hole[1]),
                "two distinct cards: %r" % (hole,),
            )
            if index in holes:
                self.assertEqual(
                    S.canon(hole), S.canon(holes[index]),
                    "the acting seat's hole does not change during a hand "
                    "(environment.md §2): seat %r read %r then %r"
                    % (index, holes[index], hole),
                )
            holes[index] = hole
        self.assertEqual(
            sorted(holes), [0, 1],
            "both seats act in a hand played to its end (environment.md §1); the readout "
            "named seats %r" % (sorted(holes),),
        )
        self.assertFalse(
            set(S.canon(card) for card in holes[0]) & set(S.canon(card) for card in holes[1]),
            "the two seats never hold one card: %r against %r" % (holes[0], holes[1]),
        )
        for step in steps:
            index, _ = S.seat_fact(step.readout["seat"])
            other = 1 - index
            text = S.flatten_text(step.readout)
            for card in holes[other]:
                self.assertNotIn(
                    S.flatten_text(card), text,
                    "the readout never carries the non-acting seat's hole cards "
                    "(environment.md §2, D-3): seat %r's readout names seat %r's card %r"
                    % (index, other, card),
                )

    def test_fam2_17_the_readout_is_deterministic_and_draws_nothing(self):
        """FAM-2.17 one hand at one state reads one mapping, and reading draws no randomness."""
        hand = self.new_hand(S.SEED_M)
        first = self.readout(hand)
        second = self.readout(hand)
        self.assertEqual(
            S.canon(first), S.canon(second),
            "one hand at one state reads one mapping (surface.md §5)",
        )
        self.assertEqual(
            S.canon(first), S.canon(self.readout(self.new_hand(S.SEED_M))),
            "one seed deals one hand, so its first readout is one mapping (surface.md §4)",
        )
        self.assert_stream_unchanged(lambda: self.readout(hand),
                                     "readout")
        self.assert_stream_unchanged(lambda: self.legal_actions(hand),
                                     "legal_actions")


if __name__ == "__main__":
    unittest.main()
