"""FAM-2 — the game is one fixed declaration, and the dealt game agrees with it.

`docs/L2/engine/surface.md` §3–§4, `docs/L2/engine/environment.md` §1,
`battery.md` §3 FAM-2, ASM-6, D-2.  The game never varies: no entry point takes a
rung, an encoding or a game parameter, so `game_config` is one declaration and every
deal must open on that game — preflop, a pot of three chips, 37 chips behind and one
chip to call from the button.  The limits are ASM-6's fixed bets, and they follow the
street.
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


class FAM2Game(S.EngineCase):
    """ASM-6's fixed game, as declared and as dealt."""

    def test_fam2_01_game_config_is_one_fixed_declaration(self):
        """FAM-2.1 `game_config()` is equal twice and states ASM-6's numbers (§3)."""
        config = self.game_config()
        self.assertTrue(
            S.is_mapping(config),
            "game_config returns the game's parameters as one mapping (surface.md §3); "
            "got %r" % (config,),
        )
        self.assertEqual(
            S.canon(config),
            S.canon(self.game_config()),
            "two calls return equal values and there is no per-call state "
            "(surface.md §3): the ladder has one game object for its whole length",
        )
        values = S.numbers_in(config)

        def count(target):
            return sum(1 for value in values if float(value) == float(target))

        self.assertGreaterEqual(count(20), 1, "the starting stacks of ASM-6 are 20 chips; "
                                "game_config states them as a number: %r" % (config,))
        self.assertGreaterEqual(count(4), 2, "the big bet of 4 and the raise cap of 4 are "
                                "two of ASM-6's numbers; game_config states both: %r" % (config,))
        self.assertGreaterEqual(count(2), 2, "the big blind of 2, the small bet of 2 and "
                                "the two seats are ASM-6's numbers; game_config states them: %r"
                                % (config,))
        self.assertGreaterEqual(count(1), 1, "the small blind of 1 and the one blind level "
                                "are ASM-6's; game_config states them as numbers: %r" % (config,))

    def test_fam2_02_the_dealt_game_opens_with_the_blinds(self):
        """FAM-2.2 at the first decision of several seeds: preflop, pot 3, 37 behind, to_call 1."""
        for seed in (S.SEED_A, S.SEED_B, S.SEED_C, S.SEED_D, S.SEED_E):
            readout = self.readout(self.new_hand(seed))
            self.assertEqual(
                readout["street"], "preflop",
                "the first decision is preflop (environment.md §1); seed %r read %r"
                % (seed, readout["street"]),
            )
            self.assertEqual(
                S.one_number(readout["pot"], "the readout's pot fact"), 3,
                "the pot holds the two blinds, 1 + 2 (environment.md §1); seed %r"
                % (seed,),
            )
            stacks = S.count_list(readout["stacks"], "the readout's stacks fact")
            self.assertEqual(
                stacks, [S.STARTING_STACKS - S.SMALL_BLIND, S.STARTING_STACKS - S.BIG_BLIND],
                "the button posts 1 and the big blind 2, so the stacks behind are 19 and 18 "
                "in seat order (environment.md §1); seed %r read %r" % (seed, stacks),
            )
            self.assertEqual(
                sum(stacks), 37,
                "the two stacks hold 20 + 20 - 3 chips (environment.md §1); seed %r" % (seed,),
            )
            self.assertEqual(
                S.one_number(readout["to_call"], "the readout's to_call fact"), 1,
                "the button owes the big blind one chip (environment.md §1); seed %r"
                % (seed,),
            )

    def test_fam2_03_the_button_acts_first_and_holds_the_button(self):
        """FAM-2.3 seat 0 is the button and acts first preflop (§4, environment.md §1)."""
        for seed in (S.SEED_F, S.SEED_G, S.SEED_H):
            index, button = S.seat_fact(self.readout(self.new_hand(seed))["seat"])
            self.assertEqual(
                index, 0,
                "seat 0 acts first preflop (environment.md §1); seed %r named seat %r"
                % (seed, index),
            )
            self.assertTrue(
                button,
                "seat 0 holds the button (surface.md §4); seed %r said otherwise" % (seed,),
            )

    def test_fam2_04_game_config_does_not_move_while_hands_are_played(self):
        """FAM-2.4 the declaration carries no seed, hand or rung, and never moves (§3)."""
        before = self.game_config()
        hand = self.new_hand(S.SEED_I)
        self.readout(hand)
        self.play_hand(S.SEED_I, S.PolicyProbe(name="seat 0"), S.PolicyProbe(name="seat 1"))
        after = self.game_config()
        self.assertEqual(
            S.canon(before),
            S.canon(after),
            "game_config has no per-call state: playing hands does not move it "
            "(surface.md §3, D-2)",
        )

    def test_fam2_05_the_limit_is_the_fixed_bet_of_the_street(self):
        """FAM-2.5 the limit in force is the small bet of 2 preflop and the big bet of 4 later."""
        steps, _ = self.walk(S.SEED_J, limit=S.DECISION_BOUND)
        streets = {}
        for step in steps:
            streets.setdefault(step.readout["street"], step.readout)
        for street in ("preflop", "flop"):
            self.assertIn(street, streets, "the battery's always-call policy reaches the %s"
                            % (street,))
            self.assertTrue(
                S.contains_number(streets[street]["limit"], S.SMALL_BET),
                "the small bet of 2 is the %s bet (ASM-6); the limit fact was %r"
                % (street, streets[street]["limit"]),
            )
        for street in ("turn", "river"):
            self.assertIn(street, streets, "the battery's always-call policy reaches the %s"
                            % (street,))
            self.assertTrue(
                S.contains_number(streets[street]["limit"], S.BIG_BET),
                "the big bet of 4 is the %s bet (ASM-6); the limit fact was %r"
                % (street, streets[street]["limit"]),
            )


if __name__ == "__main__":
    unittest.main()
