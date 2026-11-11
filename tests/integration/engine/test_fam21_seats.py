"""FAM-21 — the third seat count: six seats, 600 chips in play and a 98-slot history.

`docs/L2/engine/surface.md` §1, §3, §9, §10 and §11, `docs/L2/engine/environment.md` §1,
§2 and §4, `docs/L1/seats.md` §2–§4, `docs/L1/shapes.md` §2 and §8, `battery.md` §3
FAM-21, D-33.

`engine.game_shapes()` publishes a third row — the two-seat uncapped game over six
seats — and a six-seat hand is played through `play_hand`'s optional `seats`, its readout
carrying six stacks and its payoffs six numbers.  What changes at six seats is what a fact
is *worth*: the seat index runs over six seats, `stacks` holds one entry per seat, the pot
divides by the 600 chips in play and the history block is the shape's own 98 slots, while
the default row keeps its 24 and the two-seat uncapped one its 66.  This file asserts that
row, the six-seat hand it deals, the seat map seat 0 holds the button on across all three
shapes, the four refusals the `seats` edge states, and the equity question at six seats —
six-way, where the two-seat answer is still exactly the old enumeration's number.
"""

import os
import random
import sys
import unittest

try:  # collected as part of a package
    from . import _support as S
except ImportError:  # collected as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _support as S  # noqa: E402


# surface.md §12, shapes.md §2, seats.md §2: the declared shapes, in the catalogue's order
# — default first, the third row last.
DECLARED = S.SHAPE_NAMES

# surface.md §3, shapes.md §8: the fifteen keys of `game_config` and the five normalisers;
# the history capacity is the catalogue row's and never a key of the config (ASM-44).
CONFIG_FACTS = S.CONFIG_FACTS
NORMALISER_FACTS = S.NORMALISER_FACTS

# surface.md §2, sizing.md §2–§3, seats.md §2: the six-seat row's vocabulary — the two
# bases and the four raise bands, in the two-seat uncapped row's own index order, because a
# seat count adds no descriptor.
BASES = ("fold", "check-call")
SIX_ACTIONS = BASES + S.SIZED_RAISES

# seats.md §2–§3: the six-seat first decision's own numbers.  Seat 1 posts the small blind
# of 1 and seat 2 the big blind of 2, the button (seat 0) posts nothing, and no seat has
# committed anything else, so the stacks behind are 100, 99, 98, 100, 100 and 100 in seat
# order.
SIX_STACKS = (100, 99, 98, 100, 100, 100)


def try_edit(mapping, key, value):
    """Edit a returned mapping if a caller can; a read-only one is fresh by itself.

    surface.md §3 and §12 say the returned values are fresh, so a caller's edit cannot
    reach the catalogue or the declaration.  A mapping that refuses the edit satisfies the
    contract a fortiori, so the edit is attempted and its refusal is not a failure.
    """
    try:
        mapping[key] = value
    except (TypeError, AttributeError):
        pass


def row_of(case, shapes, name):
    """One declared row of the catalogue, or a failure naming what is missing."""
    if not S.is_mapping(shapes):
        case.fail(
            "game_shapes() must return the declared shapes as one ordered mapping, "
            "default first (surface.md §12); it returned %r" % (shapes,)
        )
    if name not in shapes:
        case.fail(
            "game_shapes() must declare the row %r (surface.md §12, seats.md §2); the "
            "catalogue keyed %r" % (name, [str(key) for key in shapes])
        )
    return shapes[name]


class FAM21Seats(S.EngineCase):
    """The six-seat row, the hand it seats, and the seat count the facts are worth."""

    # -- readers -----------------------------------------------------------
    def six_row(self):
        """The `six-seat-no-limit-100` row, or a failure naming what is absent."""
        return row_of(self, self.game_shapes(), S.SHAPE_SIX)

    def six_config(self):
        return self.game_config(S.SHAPE_SIX)

    def six_readout(self, seed):
        """One six-seat deal's first readout (surface.md §4, §5)."""
        return self.readout(self.new_hand(seed, S.SHAPE_SIX))

    def assert_chips_partitioned(self, readout, what, chips):
        """Assert this readout partitions the shape's chips: pot plus every stack."""
        pot = S.one_number(readout["pot"], "the readout's pot fact")
        stacks = S.count_list(
            readout["stacks"], "the readout's stacks fact",
            count=S.SHAPE_SEATS[S.SHAPE_SIX],
        )
        self.assertEqual(
            pot + sum(stacks),
            chips,
            "committed chips sit in the pot and never in a stack, so pot + sum(stacks) is "
            "the chips in play the shape declares at every decision — 600 on the six-seat "
            "row (environment.md §1, surface.md §12, seats.md §2): %s read pot %r and "
            "stacks %r" % (what, pot, stacks),
        )
        return pot, stacks

    # -- the third row -----------------------------------------------------
    def test_fam21_01_the_third_row_declares_six_seats_six_hundred_chips_and_98_slots(self):
        """FAM-21.1 the catalogue's third row is six seats, blinds 1/2, stacks 100, 600 chips in play, no bet and no cap, the same six descriptors, a head of 6, 98 history slots and a pot divisor of 600 (§12, shapes.md §8, seats.md §2)."""
        row = self.six_row()
        self.assertEqual(
            str(S.required(row, "the six-seat row", "name")),
            S.SHAPE_SIX,
            "the third row names the six-seat shape (surface.md §12, seats.md §2): %r"
            % (row["name"],),
        )
        self.assertIs(
            S.required(row, "the six-seat row", "default"),
            False,
            "the six-seat row is declared beside the default and is not it (surface.md "
            "§12, shapes.md §3): %r" % (row["default"],),
        )
        self.assertEqual(
            row["seats"], 6,
            "the six-seat row seats six, which is what makes its readout carry six stacks "
            "and its hand pay six numbers (seats.md §2–§3): %r" % (row["seats"],),
        )
        self.assertEqual(
            tuple(S.numbers_in(row["blinds"])),
            (1, 2),
            "the six-seat row keeps the same blinds, 1 and 2 (surface.md §12, seats.md §2): "
            "%r" % (row["blinds"],),
        )
        self.assertEqual(
            row["starting_stack"], 100,
            "the six-seat row starts each seat with 100 chips (surface.md §12, seats.md "
            "§2): %r" % (row["starting_stack"],),
        )
        self.assertEqual(
            row["chips_in_play"], 600,
            "six seats of 100 chips declare 600 chips in play (surface.md §12, seats.md "
            "§2): %r" % (row["chips_in_play"],),
        )
        self.assertEqual(
            row["chips_in_play"],
            row["seats"] * row["starting_stack"],
            "the chips in play are the row's own total, so pot + sum(stacks) is 600 at "
            "every decision (surface.md §12, environment.md §1, seats.md §2): the row said "
            "%r against a stack of %r at %r seats"
            % (row["chips_in_play"], row["starting_stack"], row["seats"]),
        )
        self.assertEqual(
            row["bet_structure"], "no-limit",
            "the six-seat row is the uncapped game at six seats (surface.md §12, seats.md "
            "§2): %r" % (row["bet_structure"],),
        )
        for name in ("small_bet", "big_bet", "raise_cap"):
            self.assertIsNone(
                row[name],
                "a row with no fixed bet and no cap declares None for %r on six seats as "
                "on two (surface.md §3, §12, seats.md §2): %r" % (name, row[name]),
            )
        self.assertEqual(
            tuple(S.descriptor_list(row["actions"], "the six-seat row's actions")),
            SIX_ACTIONS,
            "the six-seat row declares the two bases and the four raise bands in the "
            "two-seat uncapped row's own index order — worst-priced first — because a seat "
            "count adds no descriptor (surface.md §12, sizing.md §2–§3, seats.md §2): the "
            "row declared %r" % (row["actions"],),
        )
        self.assertEqual(
            row["head_width"], 6,
            "the six-seat row's head is six wide (sizing.md §6, shapes.md §2): %r"
            % (row["head_width"],),
        )
        self.assertEqual(
            row["head_width"],
            len(row["actions"]),
            "the head's width is the shape's descriptor count (sizing.md §6): the row "
            "said %r against %r descriptors"
            % (row["head_width"], len(row["actions"])),
        )
        self.assertEqual(
            row["history"], 98,
            "the six-seat row declares the 98-slot history block its own betting derives "
            "(shapes.md §8, ASM-42, ASM-44): %r" % (row["history"],),
        )
        self.assertEqual(
            row["history"], S.SHAPE_HISTORY[S.SHAPE_SIX],
            "and that 98 is the capacity the declaration states for it (shapes.md §8): %r"
            % (row["history"],),
        )
        normalisers = S.required(row, "the six-seat row", "normalisers")
        self.assertEqual(
            S.canon(normalisers),
            S.canon({"stack": 100, "pot": 600, "to_call": 100, "amount": 100,
                     "count": 50}),
            "the six-seat row's normalisers are the two-seat uncapped row's with the pot "
            "divided by its own 600 — stack ÷100, to_call ÷100, amount ÷100, count ÷50 "
            "(sizing.md §5, seats.md §2): the row said %r" % (row["normalisers"],),
        )
        self.assertEqual(
            set(normalisers), set(NORMALISER_FACTS),
            "the normalisers carry the five declared keys and nothing else (surface.md "
            "§12): the row said %r" % (sorted(str(key) for key in normalisers),),
        )
        self.assertEqual(
            normalisers["pot"], row["chips_in_play"],
            "the pot divisor is the row's own 600 chips in play: a divisor of 200 on a "
            "six-seat pot is a clip and not a normalisation (sizing.md §5, seats.md §2): "
            "%r" % (dict(normalisers),),
        )
        self.assertEqual(
            [normalisers["stack"], normalisers["to_call"], normalisers["amount"]],
            [row["starting_stack"], row["starting_stack"], row["starting_stack"]],
            "the stack, to_call and amount divisors are the row's own 100-chip stack "
            "(sizing.md §5, seats.md §2): %r" % (dict(normalisers),),
        )

        # The declaration realised: a six-seat deal opens on this row's own numbers.  The
        # seat map is the declaration's too — seat 1 posts 1, seat 2 posts 2 and seat 3
        # acts first behind the blinds (hand.md §3, seats.md §2–§3).
        for seed in (S.SEED_W, S.SEED_X):
            readout = self.six_readout(seed)
            self.assertEqual(
                readout["street"], "preflop",
                "the first decision of a six-seat hand is preflop (environment.md §1): "
                "seed %r read %r" % (seed, readout["street"]),
            )
            self.assertEqual(
                S.one_number(readout["pot"], "the readout's pot fact"), 3,
                "the pot holds the two blinds, 1 + 2, on six seats too (environment.md §1, "
                "seats.md §2): seed %r read %r" % (seed, readout["pot"]),
            )
            self.assertEqual(
                S.count_list(readout["stacks"], "the readout's stacks fact", count=6),
                list(SIX_STACKS),
                "the stacks behind are 100, 99, 98, 100, 100 and 100 in seat order, "
                "because seats 1 and 2 posted the blinds (hand.md §3, seats.md §2): seed "
                "%r read %r" % (seed, readout["stacks"]),
            )
            self.assertEqual(
                S.one_number(readout["to_call"], "the readout's to_call fact"), 2,
                "seat 3 acts first preflop behind the blinds and owes the big blind two "
                "chips (hand.md §4, seats.md §2): seed %r read %r"
                % (seed, readout["to_call"]),
            )
            self.assertEqual(
                S.seat_fact(readout["seat"]),
                (3, False),
                "seat 3, the seat after the big blind, acts first preflop, and the button "
                "is seat 0 (environment.md §1, seats.md §2–§3): seed %r read %r"
                % (seed, readout["seat"]),
            )
            self.assertEqual(
                tuple(S.numbers_in(readout["limit"])),
                (2, 0),
                "the bet size in force is the big blind of 2 and no bet-or-raise action "
                "has been made on the street (environment.md §2): seed %r read %r"
                % (seed, readout["limit"]),
            )

        # The seat map, the blinds and the stacks are the shape's and not the deal's: every
        # fact but the hole is the same at every one of the battery's six-seat seeds.
        readings = [self.six_readout(seed) for seed in S.SEEDS_SIX]
        self.assertEqual(
            len(readings), len(S.SEEDS_SIX),
            "the case reads the first decision at every one of its own six-seat seeds",
        )
        fixed = [{key: value for key, value in readout.items() if key != "hole"}
                 for readout in readings]
        for position, readout in enumerate(fixed[1:], start=1):
            self.assertEqual(
                S.canon(readout),
                S.canon(fixed[0]),
                "every fact but the dealt hole is the same at every seed: the seat order, "
                "the blinds, the stacks, the interval and the empty history are the "
                "shape's and not the deal's (seats.md §2–§3, shapes.md §5): seed %r read "
                "%r against %r" % (S.SEEDS_SIX[position], readout, fixed[0]),
            )

    def test_fam21_02_every_rows_history_capacity_is_the_declared_24_66_and_98(self):
        """FAM-21.2 each row's `history` is its own declared capacity — 24, 66 and 98 — and no `game_config` states one, because the capacity is the catalogue row's and the config's fifteen keys are a contract (§12, shapes.md §8, ASM-42, ASM-44)."""
        shapes = self.game_shapes()
        measured = {}
        for name in DECLARED:
            row = row_of(self, shapes, name)
            self.assertIn(
                "history", row,
                "every row declares its history-block capacity under `history` "
                "(shapes.md §8, ASM-44): the row %r carries %r"
                % (name, sorted(str(key) for key in row)),
            )
            measured[name] = row["history"]
        self.assertEqual(
            [measured[name] for name in DECLARED],
            [24, 66, 98],
            "the three rows' capacities are the declared 24, 66 and 98, each derived from "
            "its own betting rather than fixed by another row's cap (shapes.md §8, "
            "ASM-42, ASM-44): the catalogue stated %r" % (measured,),
        )
        self.assertEqual(
            measured,
            dict(S.SHAPE_HISTORY),
            "so the capacity every reader restates is the row's own number for that shape "
            "(shapes.md §8): the catalogue stated %r" % (measured,),
        )
        for shape in (S.SHAPE_DEFAULT, S.SHAPE_SIZED, S.SHAPE_SIX):
            with self.subTest(shape=shape):
                self.assertEqual(
                    shapes[shape]["history"], S.SHAPE_HISTORY[shape],
                    "row %r's capacity is %d (shapes.md §8): %r"
                    % (shape, S.SHAPE_HISTORY[shape], shapes[shape]["history"]),
                )
                config = self.game_config(shape)
                self.assertEqual(
                    set(config), set(CONFIG_FACTS),
                    "a shape's config states exactly the fifteen declared keys (surface.md "
                    "§3): %r stated %r"
                    % (shape, sorted(str(key) for key in config)),
                )
                self.assertNotIn(
                    "history", config,
                    "and never the history capacity, which is the catalogue row's key and "
                    "not the config's, on any shape (shapes.md §8, ASM-44): %r stated %r"
                    % (shape, sorted(str(key) for key in config)),
                )
        default = self.game_config()
        self.assertEqual(
            set(default), set(CONFIG_FACTS),
            "with no argument the config is the default row's, and its fifteen keys are "
            "unchanged (surface.md §3, shapes.md §5): it stated %r"
            % (sorted(str(key) for key in default),),
        )
        self.assertNotIn(
            "history", default,
            "the history capacity is absent from the default row's config too (shapes.md "
            "§8): it stated %r" % (sorted(str(key) for key in default),),
        )

    # -- the six-seat config ----------------------------------------------
    def test_fam21_03_the_six_seat_config_carries_the_fifteen_keys_with_its_own_values(self):
        """FAM-21.3 game_config('six-seat-no-limit-100') carries the same fifteen keys in the same order and states six seats, six starting stacks of 100, blinds 1/2, None for both bets, the limit and the cap, and a game name naming the six-seat no-limit game (§3, shapes.md §8, seats.md §2)."""
        default = self.game_config()
        six = self.six_config()
        self.assertTrue(
            S.is_mapping(six),
            "a named shape returns that shape's parameters as one mapping (surface.md §3); "
            "it returned %r" % (six,),
        )
        self.assertEqual(
            [str(key) for key in six],
            [str(key) for key in default],
            "the six-seat config carries the same fifteen keys in the same order as the "
            "default's, so one reader reads either row (surface.md §3, config.md §3): it "
            "stated %r against %r"
            % (sorted(str(key) for key in six), sorted(str(key) for key in default)),
        )
        self.assertEqual(
            set(six), set(CONFIG_FACTS),
            "and those fifteen keys are the declared ones (surface.md §3): it stated %r"
            % (sorted(str(key) for key in six),),
        )
        self.assertEqual(
            [six["seats"], six["player_count"]],
            [6, 6],
            "the six-seat row states six seats, and player_count repeats the row's own "
            "seat count (config.md §3, seats.md §2): %r"
            % ([six["seats"], six["player_count"]],),
        )
        self.assertNotEqual(
            six["seats"], default["seats"],
            "the seat count is one of the values the third row declares and the default "
            "row does not (surface.md §3, seats.md §2): both said %r" % (six["seats"],),
        )
        self.assertEqual(
            six["button_seat"], 0,
            "seat 0 holds the button on every shape, the six-seat one included (surface.md "
            "§4, seats.md §3): %r" % (six["button_seat"],),
        )
        self.assertEqual(
            tuple(S.numbers_in(six["blinds"])), (1, 2),
            "the blinds are 1 and 2 (surface.md §3, seats.md §2): %r" % (six["blinds"],),
        )
        self.assertEqual(
            (six["small_blind"], six["big_blind"]), (1, 2),
            "the two blinds are stated again as numbers (surface.md §3): %r"
            % ((six["small_blind"], six["big_blind"]),),
        )
        self.assertEqual(
            six["blind_levels"], 1,
            "one blind level, and it never rises (surface.md §3, ASM-6): %r"
            % (six["blind_levels"],),
        )
        self.assertEqual(
            six["starting_stack"], 100,
            "the six-seat row's starting stack is 100 chips (surface.md §3): %r"
            % (six["starting_stack"],),
        )
        self.assertEqual(
            tuple(S.numbers_in(six["starting_stacks"])),
            (100,) * 6,
            "the seat count is what makes six starting stacks: one 100-chip stack per "
            "seat, in seat order (config.md §3, seats.md §2): %r" % (six["starting_stacks"],),
        )
        for name in ("small_bet", "big_bet", "limit", "raise_cap"):
            self.assertIsNone(
                six[name],
                "the six-seat shape has no fixed bet and no cap, so it states None for %r "
                "— `limit` included, and never a pair of Nones (surface.md §3, config.md "
                "§3, seats.md §2): %r" % (name, six[name]),
            )
        self.assertEqual(
            tuple(six["streets"]), S.STREETS,
            "the four streets are the game's, in their declared order, on every shape "
            "(surface.md §3, environment.md §2): %r" % (six["streets"],),
        )
        game = six["game"]
        self.assertTrue(
            isinstance(game, str) and game.strip(),
            "the six-seat row's `game` name says which game it is (surface.md §3): %r"
            % (game,),
        )
        text = game.lower()
        self.assertIn(
            "six", text,
            "the game name names the six-seat table (surface.md §3, seats.md §2): %r"
            % (game,),
        )
        self.assertTrue(
            "no-limit" in text or "no limit" in text,
            "and it names the no-limit game the row declares (surface.md §3, seats.md §2): "
            "%r" % (game,),
        )
        self.assertNotIn(
            game,
            (default["game"], self.game_config(S.SHAPE_SIZED)["game"]),
            "the six-seat game's name is its own, so no reader mistakes one shape's "
            "config for another's (surface.md §3, shapes.md §2): %r" % (game,),
        )
        # The three rows share the table's own facts and differ in the seat count and in
        # what the seat count makes (surface.md §3, seats.md §2).
        for name in S.SHARED_TABLE_FACTS:
            self.assertEqual(
                S.canon(six[name]),
                S.canon(default[name]),
                "the three shapes share %r: the table's blinds, its one blind level, its "
                "button seat and its four streets (surface.md §3, shapes.md §2, seats.md "
                "§2): the six-seat config said %r against the default's %r"
                % (name, S.canon(six[name]), S.canon(default[name])),
            )
        before = S.canon(six)
        try_edit(six, "seats", 2)
        try_edit(six, "starting_stacks", (100, 100))
        try_edit(six, "game", "an invented game")
        self.assertEqual(
            S.canon(self.six_config()),
            before,
            "two calls with one argument return equal values and there is no per-call "
            "state, so a caller's edit of a returned config cannot reach the next call "
            "(surface.md §3, D-2)",
        )

    # -- the six-seat hand -------------------------------------------------
    def test_fam21_04_a_six_seat_hand_is_dealt_stepped_ended_and_paid(self):
        """FAM-21.4 a six-seat hand is dealt, stepped to its end and paid: every decision's readout holds the eleven facts with six stacks and 600 chips partitioned, the first decision reads preflop with a pot of 3, a call of 2, stacks (100, 99, 98, 100, 100, 100) and seat (3, False), and the payoffs are one net delta per seat, keyed by seats 0–5 and summing to zero (§8, §9, environment.md §1, seats.md §2–§3, ASM-12)."""
        steps, hand = self.walk(S.SEED_W, S.choose_call, shape=S.SHAPE_SIX)
        self.assertTrue(
            steps,
            "a six-seat hand takes decisions (records.md §5, surface.md §8): seed %r took "
            "none" % (S.SEED_W,),
        )
        self.assertLessEqual(
            len(steps), S.DECISION_BOUND,
            "a hand ends within %d applied actions on six seats too (surface.md §8, "
            "guardrails.md G5): this one took %d" % (S.DECISION_BOUND, len(steps)),
        )
        self.assertTrue(
            self.is_terminal(hand),
            "the six-seat hand reached its end (surface.md §8, seats.md §2)",
        )

        first = steps[0].readout
        self.assertEqual(
            first["street"], "preflop",
            "the first decision of a six-seat hand is preflop (environment.md §1): %r"
            % (first["street"],),
        )
        self.assertEqual(
            S.one_number(first["pot"], "the readout's pot fact"), 3,
            "the pot holds the two blinds, 1 + 2 (environment.md §1, seats.md §2): %r"
            % (first["pot"],),
        )
        self.assertEqual(
            S.one_number(first["to_call"], "the readout's to_call fact"), 2,
            "seat 3 acts first behind the blinds and owes the big blind two chips (hand.md "
            "§4, seats.md §2): %r" % (first["to_call"],),
        )
        self.assertEqual(
            S.count_list(first["stacks"], "the readout's stacks fact", count=6),
            list(SIX_STACKS),
            "the stacks behind are 100, 99, 98, 100, 100 and 100 in seat order (hand.md §3, "
            "seats.md §2): %r" % (first["stacks"],),
        )
        self.assertEqual(
            S.seat_fact(first["seat"]), (3, False),
            "seat 3 acts first preflop and the button is seat 0 (environment.md §1, "
            "seats.md §2–§3): %r" % (first["seat"],),
        )
        self.assertEqual(
            tuple(S.numbers_in(first["limit"])), (2, 0),
            "the bet size in force is the big blind and no bet-or-raise action has been "
            "made (environment.md §2): %r" % (first["limit"],),
        )
        self.assertEqual(
            S.descriptor_list(first["board"], "the readout's board fact"), [],
            "no public card is known at the first decision (environment.md §1)",
        )
        self.assertEqual(
            list(S.required(first, "the first decision's readout", "history")), [],
            "no action has been applied yet, so the public history is empty "
            "(environment.md §2)",
        )
        self.assertIsNone(
            S.required(first, "the first decision's readout", "hand_class"),
            "fewer than five cards are known, so no five-card hand exists (environment.md "
            "§2, ASM-30)",
        )
        self.assertTrue(
            S.descriptors_equal(
                S.required(first, "the first decision's readout", "legal"),
                S.required(self.six_row(), "the six-seat row", "actions"),
            ),
            "the six-seat first decision offers the row's own six descriptors in its "
            "declared index order, the same sequence the two-seat uncapped row declares "
            "(surface.md §6, §12, seats.md §2): it offered %r against %r"
            % (first["legal"], self.six_row()["actions"]),
        )

        seen = set()
        for position, step in enumerate(steps):
            with self.subTest(decision=position):
                readout = step.readout
                self.assertEqual(
                    set(readout), set(S.READOUT_FACTS),
                    "each decision's readout is the whole eleven-fact mapping, six seats "
                    "or two (environment.md §2, seats.md §3): got %r"
                    % (sorted(str(key) for key in readout),),
                )
                self.assert_chips_partitioned(
                    readout, "decision %d of seed %r" % (position, S.SEED_W), 600
                )
                index, button = S.seat_fact(readout["seat"])
                self.assertIn(
                    index, range(6),
                    "the acting seat's index runs over 0 .. seats - 1, so 0 to 5 (seats.md "
                    "§3): %r" % (readout["seat"],),
                )
                self.assertEqual(
                    button, index == 0,
                    "the seat fact's flag is True exactly for seat 0, the button (readout "
                    "§2, seats.md §3): %r" % (readout["seat"],),
                )
                seen.add(index)
        self.assertEqual(
            seen, set(range(6)),
            "a check-call walk of six seats is a whole table, so every seat acts and the "
            "seat map is read at all six indices (seats.md §2–§3): saw %r"
            % (sorted(seen),),
        )

        payoffs = self.payoffs(hand)
        deltas = S.seat_keyed(payoffs, "the six-seat hand's payoffs", seats=6)
        self.assertEqual(
            len(S.numbers_in(payoffs)), 6,
            "exactly one number per seat and nothing else numeric (surface.md §9): %r"
            % (payoffs,),
        )
        self.assertEqual(
            sum(S.numbers_in(payoffs)), 0,
            "the six net chip deltas are zero-sum (surface.md §9, ASM-12, seats.md §3): %r"
            % (payoffs,),
        )
        self.assertEqual(
            sorted(deltas), list(range(6)),
            "and the record is keyed by seats 0 to 5 (surface.md §9, hand.md §5): %r"
            % (payoffs,),
        )
        self.assertEqual(
            S.canon(self.payoffs(hand)), S.canon(payoffs),
            "the payoffs are a function of the completed hand alone (surface.md §9)",
        )
        self.assertEqual(
            S.canon(self.readout(self.new_hand(S.SEED_W, S.SHAPE_SIX))),
            S.canon(first),
            "and the first decision is the shape's, not the walk's: a second deal at that "
            "seed reads the same facts (surface.md §4, seats.md §2)",
        )

    def test_fam21_05_seat_zero_is_the_button_on_every_shape(self):
        """FAM-21.5 seat 0 holds the button on all three shapes: it acts preflop everywhere, the seat that acts first on the flop, the turn and the river is seat 1 — the small blind — on the two-seat shapes and on the six-seat one, and the button (seat 0) acts last post-flop on every shape (§4, environment.md §1, seats.md §2–§3)."""
        for shape in DECLARED:
            steps, _hand = self.walk(S.SEED_W, S.choose_call, shape=shape)
            with self.subTest(shape=shape):
                seats = S.SHAPE_SEATS[shape]
                by_street = {}
                for step in steps:
                    index, button = S.seat_fact(step.readout["seat"])
                    self.assertIn(
                        index, range(seats),
                        "the acting seat's index runs over 0 .. seats - 1 — 0 to %d on %r "
                        "(seats.md §3): %r" % (seats - 1, shape, step.readout["seat"]),
                    )
                    self.assertEqual(
                        button, index == 0,
                        "the flag is True exactly for the button, seat 0, on every shape "
                        "(readout §2, seats.md §3): %r" % (step.readout["seat"],),
                    )
                    by_street.setdefault(step.readout["street"], []).append(index)

                self.assertIn(
                    "preflop", by_street,
                    "a hand is dealt preflop on every shape (environment.md §1): %r"
                    % (sorted(by_street),),
                )
                self.assertIn(
                    0, by_street["preflop"],
                    "the button acts preflop on every shape — first on the two-seat shapes "
                    "and behind the blinds on the six-seat one (environment.md §1, seats.md "
                    "§2): the preflop seats were %r" % (by_street["preflop"],),
                )

                order = list(range(1, seats)) + [0]
                postflop = [street for street in S.STREETS[1:] if street in by_street]
                self.assertTrue(
                    postflop,
                    "the check-call walk reaches a post-flop street, so the order below is "
                    "asserted and not skipped (environment.md §1): reached %r"
                    % (sorted(by_street),),
                )
                for street in postflop:
                    seats_in_street = by_street[street]
                    self.assertEqual(
                        len(seats_in_street), seats,
                        "every seat acts on a post-flop street a check-call walk opens, so "
                        "the order is the shape's whole seating (seats.md §2–§3): the %s "
                        "of %r read %r" % (street, shape, seats_in_street),
                    )
                    self.assertEqual(
                        seats_in_street[0], 1,
                        "the seat that acts first on the %s is seat 1, the small blind, on "
                        "the two-seat shapes and on the six-seat one alike (environment.md "
                        "§1, seats.md §2): read %r" % (street, seats_in_street),
                    )
                    self.assertEqual(
                        seats_in_street[-1], 0,
                        "the button, seat 0, acts last on the %s of every shape "
                        "(environment.md §1, seats.md §3): read %r"
                        % (street, seats_in_street),
                    )
                    self.assertEqual(
                        seats_in_street, order,
                        "the post-flop order is the shape's seating — seat 1, then the "
                        "seats in order, then the button, %r on %r — so no seat map "
                        "inverts the button or stops at two seats (hand.md §3, seats.md "
                        "§2–§3): the %s read %r"
                        % (order, shape, street, seats_in_street),
                    )

    # -- the seating ------------------------------------------------------
    def test_fam21_06_a_six_seat_hand_seats_the_shapes_whole_seating(self):
        """FAM-21.6 play_hand with `seats` on the six-seat shape plays six policies, one per seat in seat order, each called only when its own seat acts; the decisions' seats are the readout's own seat facts; each seat's last decision carries its net chip delta; and the payoffs are six zero-sum numbers (§10, §9, episode.md §3, seats.md §4, ASM-12)."""
        probes = [S.PolicyProbe(S.choose_call, name="seat %d" % seat) for seat in range(6)]
        episode = self.seated_play_hand(S.SEED_X, probes, S.SHAPE_SIX)
        decisions = S.decision_list(episode)
        self.assertTrue(
            decisions,
            "an episode of a six-seat hand records its decisions (records.md §5): seed %r "
            "recorded none" % (S.SEED_X,),
        )
        self.assertEqual(
            S.canon(S.required(episode, "the episode record", "seed")),
            S.SEED_X,
            "the record carries the seed the call was made with, unchanged (records.md "
            "§5)",
        )

        last = {}
        seen = set()
        for position, decision in enumerate(decisions):
            with self.subTest(decision=position):
                readout = S.decision_fact(decision, "readout")
                self.assertEqual(
                    set(readout), set(S.READOUT_FACTS),
                    "the decision's readout is the whole eleven-fact mapping (environment.md "
                    "§3, seats.md §3): got %r" % (sorted(str(key) for key in readout),),
                )
                self.assertEqual(
                    S.canon(S.decision_fact(decision, "seat")),
                    S.canon(readout["seat"]),
                    "a decision's seat is its readout's own seat fact, so a seat index "
                    "means one thing in the record and in the facts (episode.md §3, seats.md "
                    "§3): %r against %r"
                    % (S.decision_fact(decision, "seat"), readout["seat"]),
                )
                index, button = S.seat_fact(readout["seat"])
                self.assertIn(
                    index, range(6),
                    "the deciding seat is one of the six (seats.md §3): %r"
                    % (readout["seat"],),
                )
                self.assertEqual(
                    button, index == 0,
                    "seat 0 is the button on six seats too (readout.md §2, seats.md §3): "
                    "%r" % (readout["seat"],),
                )
                self.assert_chips_partitioned(
                    readout, "decision %d of the six-seat episode" % position, 600
                )
                seen.add(index)
                last[index] = position
        self.assertEqual(
            seen, set(range(6)),
            "a check-call six-seat hand is a whole table, so all six seats act and all six "
            "policies are called (seats.md §4): the record seated %r" % (sorted(seen),),
        )

        for seat, probe in enumerate(probes):
            calls = list(probe.calls)
            self.assertTrue(
                calls,
                "seat %d's policy is called at least once in a check-call hand, or the "
                "seating did not reach it (seats.md §4)" % (seat,),
            )
            self.assertEqual(
                [S.seat_fact(call["readout"]["seat"])[0] for call in calls],
                [seat] * len(calls),
                "the sequence is the shape's whole seating in seat order, so seat %d's "
                "policy is called only when seat %d acts — never another seat's (seats.md "
                "§4): it saw %r"
                % (seat, seat, [S.seat_fact(call["readout"]["seat"])[0] for call in calls]),
            )
            self.assertEqual(
                len(calls),
                sum(1 for decision in decisions
                    if S.seat_fact(S.decision_fact(decision, "seat"))[0] == seat),
                "and it is called once per decision of its own seat (seats.md §4): seat %d "
                "was called %d times" % (seat, len(calls)),
            )

        payoffs = S.seat_keyed(
            S.required(episode, "the episode record", "payoffs"),
            "the six-seat episode's payoffs",
            seats=6,
        )
        self.assertEqual(
            len(S.numbers_in(payoffs)), 6,
            "the episode reports one payoff per seat and nothing else numeric (surface.md "
            "§9, seats.md §3): %r" % (payoffs,),
        )
        self.assertEqual(
            sum(S.numbers_in(payoffs)), 0,
            "the six net chip deltas are zero-sum (surface.md §9, ASM-12): %r"
            % (payoffs,),
        )
        rewarded = sorted(
            S.decision_fact(decision, "reward") for decision in decisions
            if S.decision_fact(decision, "reward") != 0
        )
        paid = sorted(value for value in S.numbers_in(payoffs) if value != 0)
        self.assertEqual(
            rewarded, paid,
            "the non-zero rewards are exactly the non-zero payoffs, one per paid seat "
            "(episode.md §3, ASM-12, guardrails G9): rewards %r against payoffs %r"
            % (rewarded, payoffs),
        )
        for seat, position in last.items():
            with self.subTest(seat=seat):
                self.assertEqual(
                    S.decision_fact(decisions[position], "reward"), payoffs[seat],
                    "each seat's last decision carries that seat's net chip delta, and no "
                    "shaped per-decision term (episode.md §3, ASM-12, guardrails G9): seat "
                    "%d was paid %r at decision %d, which carried %r"
                    % (seat, payoffs[seat], position,
                       S.decision_fact(decisions[position], "reward")),
                )

    def test_fam21_07_the_seating_on_two_seats_is_the_positional_pair_and_that_pair_is_unchanged(self):
        """FAM-21.7 play_hand with `seats` on a two-seat shape is legal and equals the two positional policies, and the two-policy path itself is unchanged: an absent shape and the named default are one record, its three keys are the record's, and its decisions and payoffs are the hand's the same two policies drive (§10, shapes.md §5, seats.md §4)."""
        seed = S.SEED_Y
        for shape in (S.SHAPE_DEFAULT, S.SHAPE_SIZED):
            with self.subTest(shape=shape):
                positional = self.play_hand(seed, S.choose_call, S.choose_raise, shape)
                seated = self.seated_play_hand(
                    seed, (S.choose_call, S.choose_raise), shape
                )
                self.assertEqual(
                    S.canon(seated),
                    S.canon(positional),
                    "with two seats the seating is the two positional policies, so the two "
                    "forms play one hand and record one episode (seats.md §4, "
                    "e2e-surface.md §3.1): on %r the seating recorded %r against the "
                    "positional call's %r" % (shape, seated, positional),
                )

        absent = self.play_hand(seed, S.choose_call, S.choose_raise)
        explicit_none = self.play_hand(seed, S.choose_call, S.choose_raise, None)
        named = self.play_hand(seed, S.choose_call, S.choose_raise, S.SHAPE_DEFAULT)
        self.assertEqual(
            S.canon(absent),
            S.canon(explicit_none),
            "an absent shape is today's game, so the two calls are one episode (surface.md "
            "§10, shapes.md §3)",
        )
        self.assertEqual(
            S.canon(named),
            S.canon(absent),
            "and naming the default shape is the same call as omitting it, so the "
            "fixed-limit path is unchanged (shapes.md §5, surface.md §10)",
        )
        self.assertEqual(
            set(absent), set(S.EPISODE_FACTS),
            "the record carries the three keys it has always carried — the seed, the "
            "decisions and the payoffs — and the shape is an argument, never a key "
            "(records.md §5, surface.md §10): got %r"
            % (sorted(str(key) for key in absent),),
        )
        self.assertEqual(
            S.canon(S.required(absent, "the episode record", "seed")), S.SEED_Y,
            "the record carries the seed the call was made with, unchanged (records.md §5)",
        )

        # The two policies play the hand they always played: the same seed and the same two
        # policy behaviours, dispatched seat by seat exactly as play_hand dispatches them,
        # reach the same decisions and pay the same chips (episode.md §5, surface.md §10).
        policies = (S.choose_call, S.choose_raise)
        hand = self.new_hand(seed)
        replayed = []
        while not self.is_terminal(hand):
            readout = self.readout(hand)
            legal = self.legal_actions(hand)
            index, _button = S.seat_fact(readout["seat"])
            action = policies[index](readout, legal)
            replayed.append(action)
            hand = self.apply_action(hand, action)
        decisions = S.decision_list(absent)
        self.assertEqual(
            [S.decision_fact(decision, "action") for decision in decisions],
            replayed,
            "the two-policy path is the hand new_hand deals at that seed and the two "
            "policies drive, decision for decision (episode.md §5, surface.md §10)",
        )
        self.assertEqual(
            len(decisions), len(replayed),
            "so its decision count is the hand's own (surface.md §8): %d against %d"
            % (len(decisions), len(replayed)),
        )
        self.assertEqual(
            S.canon(S.required(absent, "the episode record", "payoffs")),
            S.canon(self.payoffs(hand)),
            "and its payoffs are the completed hand's (episode.md §3, ASM-12): %r against "
            "%r" % (S.required(absent, "the episode record", "payoffs"), self.payoffs(hand)),
        )

    def test_fam21_08_the_seating_refusals_name_the_violated_contract(self):
        """FAM-21.8 play_hand refuses a seating whose length is not the shape's seat count, a seating handed beside a positional policy, the two positional policies on a shape with more than two seats, and a policy that is not callable — positionally or inside the seating — as an error of this module's own refusal tree, before the deal (§1, §10, seats.md §4, e2e-surface.md §3.1)."""
        six = S.seating(S.SHAPE_SIX)
        two = S.seating(S.SHAPE_DEFAULT)
        self.assertEqual(
            [len(six), len(two)], [6, 2],
            "the premise: the two seatings are the two shapes' own seat counts (seats.md "
            "§2): %r and %r" % (len(six), len(two)),
        )
        refusals = (
            ("a two-policy seating on the six-seat shape",
             lambda: self.seated_play_hand(S.SEED_Z, two, S.SHAPE_SIX),
             ("seat",)),
            ("a six-policy seating on a two-seat shape",
             lambda: self.seated_play_hand(S.SEED_Z, six),
             ("seat",)),
            ("a seating beside the first positional policy",
             lambda: self.seating_beside(S.SEED_Z, S.choose_call, six),
             ("seat", "policy")),
            ("a seating beside the second positional policy",
             lambda: self.seating_beside(S.SEED_Z, None, six, second=S.choose_call),
             ("seat", "policy")),
            ("the two positional policies on the six-seat shape",
             lambda: self.play_hand(S.SEED_Z, S.choose_call, S.choose_call, S.SHAPE_SIX),
             ("seat", "policy")),
            ("a non-callable first positional policy",
             lambda: self.play_hand(S.SEED_Z, "choose-call", S.choose_call),
             ("policy",)),
            ("a non-callable second positional policy",
             lambda: self.play_hand(S.SEED_Z, S.choose_call, 7),
             ("policy",)),
            ("a non-callable policy inside a six-seat seating",
             lambda: self.seated_play_hand(
                 S.SEED_Z, six[:5] + (None,), S.SHAPE_SIX
             ),
             ("policy",)),
            ("a non-callable policy inside a two-seat seating",
             lambda: self.seated_play_hand(S.SEED_Z, (S.choose_call, "fold")),
             ("policy",)),
        )
        for what, call, words in refusals:
            exc = self.assert_refused(call, what, words)
            self.assertEqual(
                type(exc).__module__.split(".")[0], "engine",
                "%s must be refused by this module's own refusal tree — never by Python's "
                "TypeError from the call itself and never by a battery failure (surface.md "
                "§1, seats.md §4): it raised %s(%s)"
                % (what, type(exc).__name__, exc),
            )
        self.assertTrue(
            S.decision_list(
                self.play_hand(S.SEED_Z, S.choose_call, S.choose_call)
            ),
            "and the two-policy path is still accepted after those refusals: a refusal is "
            "an outcome and not a state the engine keeps (surface.md §1)",
        )

    def seating_beside(self, seed, seat0, policies, second=None):
        """Call `play_hand` with one positional policy and a seating, the form it refuses."""
        return self.ep("play_hand")(seed, seat0, second, S.SHAPE_SIX, tuple(policies))

    # -- the equity question at six seats --------------------------------
    def test_fam21_09_the_six_seat_question_is_six_way(self):
        """FAM-21.9 a decision whose readout carries six stacks is asked against the other five seats' uniformly random hands: a probability in [0, 1], 1.0 for the nuts the opponents cannot tie, near zero for a known-weak hand, the same number twice for one readout, and the global stream handed back as it was found (§11, environment.md §4, seats.md §2)."""
        six_stacks = list(SIX_STACKS)
        nuts = {"hole": ("As", "Ks"), "board": ("Qs", "Js", "Ts"), "stacks": six_stacks}
        weak = {"hole": ("2c", "7d"), "board": ("As", "Ks", "Qs"), "stacks": six_stacks}
        seed = S.SEED_Y
        samples = S.SAMPLES_COARSE

        nuts_value = self.equity(nuts, seed, samples)
        self.assertTrue(
            S.is_number(nuts_value),
            "equity returns a number (surface.md §11); it returned %r" % (nuts_value,),
        )
        self.assertGreaterEqual(
            float(nuts_value), 0.0, "a share of the pot is never negative (surface.md §11)"
        )
        self.assertLessEqual(
            float(nuts_value), 1.0,
            "a share of the pot never exceeds one (surface.md §11): %r" % (nuts_value,),
        )
        self.assertEqual(
            float(nuts_value), 1.0,
            "As Ks over Qs Js Ts is a royal flush, and the opponents cannot tie it because "
            "As and Ks are the acting seat's own cards, so a six-way query answers 1.0 "
            "(surface.md §11, seats.md §2): got %r" % (nuts_value,),
        )

        weak_value = self.equity(weak, seed, samples)
        self.assertGreaterEqual(
            float(weak_value), 0.0,
            "a share of the pot is never negative (surface.md §11): got %r" % (weak_value,),
        )
        self.assertLessEqual(
            float(weak_value), 1.0,
            "a share of the pot never exceeds one (surface.md §11): got %r" % (weak_value,),
        )
        self.assertLess(
            float(weak_value), 0.1,
            "2c 7d over As Ks Qs is a known-weak hand against five random ones, so its "
            "six-way share is near zero (surface.md §11, seats.md §2): measured %r"
            % (weak_value,),
        )

        repeated = self.assert_stream_unchanged(
            lambda: self.equity(nuts, seed, samples),
            "a six-way equity query of one readout",
        )
        self.assertEqual(
            S.canon(repeated), S.canon(nuts_value),
            "one readout, one seed and one sample count give one estimate, so the six-way "
            "question repeats (surface.md §11): %r against %r" % (repeated, nuts_value),
        )
        self.assertEqual(
            S.canon(self.equity(weak, seed, samples)), S.canon(weak_value),
            "and a second query of the weak hand reads the same number (surface.md §11): "
            "%r against %r" % (self.equity(weak, seed, samples), weak_value),
        )

        # The opponents are the other seats', so the same two cards are worth less six-way
        # than heads-up: the seat count is read from the readout's stacks fact (seats.md §2).
        middle = ("As", "Kd")
        six_way = self.equity(
            {"hole": middle, "board": (), "stacks": six_stacks}, seed, samples
        )
        heads_up = self.equity(
            {"hole": middle, "board": (), "stacks": [100, 100]}, seed, samples
        )
        self.assertLess(
            float(six_way), float(heads_up),
            "the same hole cards are worth less against five random hands than against "
            "one, so the seat count decides how many opponents the question holds "
            "(seats.md §2, surface.md §11): six-way %r against heads-up %r"
            % (six_way, heads_up),
        )

    def test_fam21_10_the_two_seat_answer_is_still_the_old_enumeration(self):
        """FAM-21.10 on both two-seat shapes the answer is exactly the one this module has always given: the unseen deck's every two-card combination, enumerated in `Deck.STANDARD` order as the opponent range, through `pokerkit.analysis.calculate_equities` — compared bit for bit at several decisions of both two-seat shapes (§11, sizing.md §3, shapes.md §5)."""
        import itertools

        from pokerkit.analysis import calculate_equities
        from pokerkit.hands import StandardHighHand
        from pokerkit.utilities import Card, Deck

        def card(spelling):
            """The library's card a readout spelling names (environment.md §2)."""
            return Card(spelling[0], spelling[1])

        def pre_change_answer(hole, board, seed, samples):
            """The two-seat estimate computed the way this module computed it before D-33.

            The sample universe is the unseen deck's every two-card combination, in
            `Deck.STANDARD` order and never from a set iteration, so a six-way branch that
            reached the two-seat question would fail this comparison (sizing.md §3,
            shapes.md §5).
            """
            hole = [card(spelling) for spelling in hole]
            board = [card(spelling) for spelling in board]
            unseen = [value for value in Deck.STANDARD
                      if value not in set(hole + board)]
            ranges = (
                [list(hole)],
                [[first, second] for first, second in itertools.combinations(unseen, 2)],
            )
            saved = random.getstate()
            try:
                random.seed(seed)
                values = calculate_equities(
                    ranges,
                    list(board),
                    2,
                    5,
                    Deck.STANDARD,
                    (StandardHighHand,),
                    sample_count=samples,
                )
            finally:
                random.setstate(saved)
            return float(values[0])

        checked = 0
        for shape in (S.SHAPE_DEFAULT, S.SHAPE_SIZED):
            for seed in (S.SEED_W, S.SEED_Z):
                hand = self.new_hand(seed, shape)
                for decision in range(3):
                    if self.is_terminal(hand):
                        break
                    readout = self.readout(hand)
                    expected = pre_change_answer(
                        readout["hole"], readout["board"], S.SEED_X, S.SAMPLES_ODD
                    )
                    with self.subTest(shape=shape, seed=seed, decision=decision):
                        self.assertEqual(
                            float(self.equity(hand, S.SEED_X, S.SAMPLES_ODD)),
                            expected,
                            "a two-seat hand's estimate is exactly the old enumeration's "
                            "answer — the unseen two-card combinations in Deck.STANDARD "
                            "order as the opponent range (sizing.md §3, shapes.md §5): %r "
                            "on %r at seed %r, decision %d, against the reimplementation's "
                            "%r"
                            % (self.equity(hand, S.SEED_X, S.SAMPLES_ODD), shape, seed,
                               decision, expected),
                        )
                        self.assertEqual(
                            float(self.equity(readout, S.SEED_X, S.SAMPLES_ODD)),
                            expected,
                            "and the readout form of that decision answers the same old "
                            "number, because both carry the same two cards and board "
                            "(surface.md §11): %r against %r"
                            % (self.equity(readout, S.SEED_X, S.SAMPLES_ODD), expected),
                        )
                    checked += 1
                    hand = self.apply_action(hand, S.choose_call(self.readout(hand),
                                                                self.legal_actions(hand)))
        self.assertGreaterEqual(
            checked, 6,
            "the cross-check reads several decisions of both two-seat shapes, or it says "
            "nothing about the unchanged path (shapes.md §5): it read %d" % (checked,),
        )


if __name__ == "__main__":
    unittest.main()
