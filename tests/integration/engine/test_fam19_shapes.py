"""FAM-19 — the shape catalogue, the two configs, and the four refusals.

`docs/L2/engine/surface.md` §1, §3, §4, §10 and §12, `docs/L1/shapes.md` §2–§5,
`battery.md` §3 FAM-19, D-29, D-13.  The project declares a second game shape beside
the fixed-limit one, and it is reached as **data**: `game_shapes()` publishes the
catalogue as an ordered mapping, default first, and `game_config(shape)` returns one
row of it.  So this file asserts the declaration itself — the two names in the declared
order, each row's exact key set and declared values, the fifteen keys of both configs
and the values that differ — and the edge the widening lives on: absence and `None` are
the default shape, and a name outside the catalogue is refused naming it and the
declared names, before the deal, never defaulted.  The fixed-limit assertions of FAM-2
are untouched and stay where they are: an absent shape is today's game.
"""

import os
import sys
import unittest

try:  # collected as part of a package
    from . import _support as S
except ImportError:  # collected as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _support as S  # noqa: E402


# surface.md §12: the declared shapes, in the catalogue's order — default first.
DECLARED = ("fixed-limit-20", "no-limit-100")

# surface.md §12, shapes.md §2: the keys every row carries, and the five normalisers.
ROW_FACTS = (
    "name",
    "default",
    "seats",
    "blinds",
    "starting_stack",
    "chips_in_play",
    "bet_structure",
    "small_bet",
    "big_bet",
    "raise_cap",
    "actions",
    "head_width",
    "normalisers",
)
NORMALISER_FACTS = ("stack", "pot", "to_call", "amount", "count")

# surface.md §3: the fifteen keys of `game_config`, the same fifteen in every shape.
CONFIG_FACTS = (
    "game",
    "seats",
    "player_count",
    "button_seat",
    "blinds",
    "small_blind",
    "big_blind",
    "blind_levels",
    "starting_stack",
    "starting_stacks",
    "small_bet",
    "big_bet",
    "limit",
    "raise_cap",
    "streets",
)

# surface.md §12, §2: each shape's vocabulary, in the shape's own index order.  The
# fixed-limit row is ASM-6's three descriptors; the sized row declares the four raise
# bands of `sizing.md` §2 after the two every shape carries, worst-priced first.
DEFAULT_ACTIONS = ("fold", "check-call", "raise")
SIZED_ACTIONS = (
    "fold",
    "check-call",
    "raise-quarter",
    "raise-half",
    "raise-all-in",
    "raise-minimum",
)

# The values the two configs share, because the two shapes have the same table
# (shapes.md §2): two seats, blinds 1 and 2, one blind level and the same four streets.
SHARED_CONFIG_FACTS = (
    "seats",
    "player_count",
    "button_seat",
    "blinds",
    "small_blind",
    "big_blind",
    "blind_levels",
    "streets",
)


def row_of(case, shapes, name):
    """One declared row of the catalogue, or a failure naming what is missing."""
    if not S.is_mapping(shapes):
        case.fail(
            "game_shapes() must return the declared shapes as one ordered mapping, "
            "default first (surface.md §12); it returned %r" % (shapes,)
        )
    if name not in shapes:
        case.fail(
            "game_shapes() must declare the row %r (surface.md §12, shapes.md §2); the "
            "catalogue keyed %r" % (name, [str(key) for key in shapes])
        )
    return shapes[name]


def try_edit(mapping, key, value):
    """Edit a returned mapping if a caller can; a read-only one is fresh by itself.

    surface.md §12 and §3 say the returned values are fresh, so a caller's edit cannot
    reach the catalogue.  A mapping that refuses the edit satisfies the contract a
    fortiori, so the edit is attempted and its refusal is not a failure.
    """
    try:
        mapping[key] = value
    except (TypeError, AttributeError):
        pass


class FAM19Shapes(S.EngineCase):
    """The declared catalogue, the two configs, and the edge a name is refused at."""

    # -- readers -----------------------------------------------------------
    def assert_chips_conserved(self, shape, seed, chips):
        """Assert that a hand of `shape` partitions the table's `chips` at every decision.

        surface.md §12 and environment.md §1: committed chips sit in `pot` and never in a
        stack, so `pot + sum(stacks)` is the chips in play the hand's own shape declares —
        40 in the default shape and the shape's own total elsewhere.
        """
        episode = self.play_hand(
            seed,
            S.PolicyProbe(S.choose_call, name="seat 0"),
            S.PolicyProbe(S.choose_raise, name="seat 1"),
            shape,
        )
        decisions = S.decision_list(episode)
        self.assertTrue(
            decisions,
            "an episode of a hand records its decisions (records.md §5): shape %r seed %r "
            "recorded none" % (shape, seed),
        )
        for position, decision in enumerate(decisions):
            readout = S.decision_fact(decision, "readout")
            self.assertEqual(
                set(readout),
                set(S.READOUT_FACTS),
                "the readout is the same eleven facts in every shape, because what changes "
                "is what a fact means and never how many there are (surface.md §5, "
                "environment.md §3): %r decision %d of shape %r carried %r"
                % (seed, position, shape, sorted(str(key) for key in readout)),
            )
            pot = S.one_number(readout["pot"], "the readout's pot fact")
            stacks = S.count_list(readout["stacks"], "the readout's stacks fact")
            self.assertEqual(
                pot + sum(stacks),
                chips,
                "at every decision pot plus the two stacks is the chips in play the hand's "
                "own shape declares — 40 in the default shape and the shape's own total "
                "elsewhere (surface.md §12, environment.md §1): shape %r seed %r read a pot "
                "of %r and stacks of %r at decision %d"
                % (shape, seed, pot, stacks, position),
            )

    # -- the catalogue -----------------------------------------------------
    def test_fam19_01_the_catalogue_is_ordered_default_first(self):
        """FAM-19.1 game_shapes() declares exactly the two shapes, default first (§12)."""
        shapes = self.game_shapes()
        self.assertTrue(
            S.is_mapping(shapes),
            "game_shapes() takes no argument and returns the declared shapes as an "
            "ordered mapping (surface.md §12); it returned %r" % (shapes,),
        )
        names = [str(key) for key in shapes]
        self.assertEqual(
            names,
            list(DECLARED),
            "the catalogue declares exactly two shapes, `fixed-limit-20` then "
            "`no-limit-100`, in that order and default first (surface.md §12, "
            "shapes.md §2); it keyed %r" % (names,),
        )
        flags = [row_of(self, shapes, name)["default"] for name in DECLARED]
        self.assertEqual(
            flags,
            [True, False],
            "the first row is the default and the second is not (surface.md §12): the "
            "rows said %r" % (flags,),
        )
        self.assertEqual(
            sum(1 for flag in flags if flag is True),
            1,
            "exactly one declared shape is the default, because absence reads as one "
            "shape and never as two (shapes.md §3): the rows said %r" % (flags,),
        )

    def test_fam19_02_every_row_carries_exactly_the_declared_keys(self):
        """FAM-19.2 each row carries the thirteen declared keys and the five normalisers (§12)."""
        shapes = self.game_shapes()
        for name in DECLARED:
            row = row_of(self, shapes, name)
            self.assertEqual(
                set(row),
                set(ROW_FACTS),
                "a row is the shape's declaration and carries exactly the keys §12 "
                "names — name, default, seats, blinds, starting_stack, chips_in_play, "
                "bet_structure, small_bet/big_bet/raise_cap, actions, head_width and "
                "normalisers (surface.md §12, shapes.md §2); row %r carried %r"
                % (name, sorted(str(key) for key in row)),
            )
            normalisers = S.required(row, "the row %r" % (name,), "normalisers")
            self.assertTrue(
                S.is_mapping(normalisers),
                "the normalisers are one divisor per key (surface.md §12, sizing.md §5): "
                "row %r stated %r" % (name, normalisers),
            )
            self.assertEqual(
                set(normalisers),
                set(NORMALISER_FACTS),
                "the normalisers carry stack, pot, to_call, amount and count and nothing "
                "else (surface.md §12): row %r stated %r"
                % (name, sorted(str(key) for key in normalisers)),
            )

    def test_fam19_03_the_default_row_declares_the_fixed_limit_game(self):
        """FAM-19.3 the default row is ASM-6's game: stack 20, 40 in play, bets 2/4, cap 4, width 3 (§12)."""
        row = row_of(self, self.game_shapes(), S.SHAPE_DEFAULT)
        self.assertEqual(
            row["name"],
            S.SHAPE_DEFAULT,
            "the first row names the default shape (surface.md §12): %r" % (row["name"],),
        )
        self.assertIs(
            row["default"],
            True,
            "the default row says so, as a boolean (surface.md §12, shapes.md §2): %r"
            % (row["default"],),
        )
        self.assertEqual(
            row["seats"], 2, "the shape seats two (shapes.md §2): %r" % (row["seats"],)
        )
        self.assertEqual(
            tuple(S.numbers_in(row["blinds"])),
            (1, 2),
            "the blinds are 1 and 2, in seat order (surface.md §12, shapes.md §2): %r"
            % (row["blinds"],),
        )
        self.assertEqual(
            row["starting_stack"],
            20,
            "the default shape's starting stack is 20 chips (surface.md §12, ASM-6): %r"
            % (row["starting_stack"],),
        )
        self.assertEqual(
            row["chips_in_play"],
            40,
            "the default shape declares 40 chips in play (surface.md §12, shapes.md §2): "
            "%r" % (row["chips_in_play"],),
        )
        self.assertEqual(
            row["chips_in_play"],
            row["seats"] * row["starting_stack"],
            "the chips in play are the row's own total, so pot plus the two stacks is 40 "
            "at every decision (surface.md §12, environment.md §1): the row said %r "
            "against a stack of %r at %r seats"
            % (row["chips_in_play"], row["starting_stack"], row["seats"]),
        )
        self.assertEqual(
            row["bet_structure"],
            "fixed-limit",
            "the default row's bet structure is `fixed-limit` and a row's `game` name "
            "never carries it (surface.md §3, §12): %r" % (row["bet_structure"],),
        )
        self.assertEqual(
            (row["small_bet"], row["big_bet"], row["raise_cap"]),
            (2, 4, 4),
            "the default shape's fixed bets are 2 and 4 under a cap of four bet-or-raise "
            "actions a street (surface.md §12, ASM-6): the row said %r"
            % ((row["small_bet"], row["big_bet"], row["raise_cap"]),),
        )
        self.assertEqual(
            tuple(S.descriptor_list(row["actions"], "the default row's actions")),
            DEFAULT_ACTIONS,
            "the default shape's vocabulary is fold, check-call and raise, in that index "
            "order (surface.md §2, §12): the row declared %r" % (row["actions"],),
        )
        self.assertEqual(
            row["head_width"],
            3,
            "the default shape's head is three wide (sizing.md §6, shapes.md §2): %r"
            % (row["head_width"],),
        )
        self.assertEqual(
            row["head_width"],
            len(row["actions"]),
            "the head's width is the shape's descriptor count, so no caller branches on "
            "the shape (sizing.md §6): the row said %r against %r descriptors"
            % (row["head_width"], len(row["actions"])),
        )
        self.assertEqual(
            S.canon(S.required(row, "the default row", "normalisers")),
            S.canon({"stack": 20, "pot": 40, "to_call": 20, "amount": 4, "count": 4}),
            "the default shape's normalisers are stack ÷20, pot ÷40, to_call ÷20, amount "
            "÷4 and count ÷4 (surface.md §12, shapes.md §2): the row said %r"
            % (row["normalisers"],),
        )
        # The row is the declaration and the deal is that declaration realised: a hand of
        # this shape partitions the table's 40 chips at every decision (surface.md §12).
        for seed in (S.SEED_Q, S.SEED_T):
            self.assert_chips_conserved(S.SHAPE_DEFAULT, seed, row["chips_in_play"])

    def test_fam19_04_the_sized_row_declares_the_no_limit_game(self):
        """FAM-19.4 the sized row is stack 100, 200 in play, no bet and no cap, six descriptors, width 6 (§12)."""
        row = row_of(self, self.game_shapes(), S.SHAPE_SIZED)
        self.assertEqual(
            row["name"],
            S.SHAPE_SIZED,
            "the second row names the sized shape (surface.md §12): %r" % (row["name"],),
        )
        self.assertIs(
            row["default"],
            False,
            "the sized row is declared beside the default and is not it (surface.md §12, "
            "shapes.md §2): %r" % (row["default"],),
        )
        self.assertEqual(
            row["seats"], 2, "the shape seats two (shapes.md §2): %r" % (row["seats"],)
        )
        self.assertEqual(
            tuple(S.numbers_in(row["blinds"])),
            (1, 2),
            "the sized shape keeps the same blinds, 1 and 2 (surface.md §12, shapes.md §2): "
            "%r" % (row["blinds"],),
        )
        self.assertEqual(
            row["starting_stack"],
            100,
            "the sized shape's starting stack is 100 chips (surface.md §12, shapes.md §2): "
            "%r" % (row["starting_stack"],),
        )
        self.assertEqual(
            row["chips_in_play"],
            200,
            "the sized shape declares 200 chips in play (surface.md §12): %r"
            % (row["chips_in_play"],),
        )
        self.assertEqual(
            row["chips_in_play"],
            row["seats"] * row["starting_stack"],
            "the chips in play are the row's own total, so pot plus the two stacks is 200 "
            "at every decision (surface.md §12, environment.md §1): the row said %r "
            "against a stack of %r at %r seats"
            % (row["chips_in_play"], row["starting_stack"], row["seats"]),
        )
        self.assertEqual(
            row["bet_structure"],
            "no-limit",
            "the sized row's bet structure is `no-limit` (surface.md §12, sizing.md §2): %r"
            % (row["bet_structure"],),
        )
        for name in ("small_bet", "big_bet", "raise_cap"):
            self.assertIsNone(
                row[name],
                "a shape with no fixed bet and no cap declares None for %r, because it "
                "has neither (surface.md §3, §12, shapes.md §2): %r" % (name, row[name]),
            )
        self.assertEqual(
            tuple(S.descriptor_list(row["actions"], "the sized row's actions")),
            SIZED_ACTIONS,
            "the sized shape declares fold, check-call and the four raise bands in its own "
            "index order — the measured price order, worst first, so the order is not "
            "monotone in amount (surface.md §12, sizing.md §3): the row declared %r"
            % (row["actions"],),
        )
        self.assertEqual(
            row["head_width"],
            6,
            "the sized shape's head is six wide (sizing.md §6, shapes.md §2): %r"
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
            S.canon(S.required(row, "the sized row", "normalisers")),
            S.canon({"stack": 100, "pot": 200, "to_call": 100, "amount": 100, "count": 50}),
            "the sized shape's normalisers are stack ÷100, pot ÷200, to_call ÷100, amount "
            "÷100 and count ÷50 — a divisor of 40 on a 200-chip game is a clip and not a "
            "normalisation (surface.md §12, sizing.md §5): the row said %r"
            % (row["normalisers"],),
        )
        # The declaration realised: a sized deal opens on this row's own numbers and
        # partitions the table's 200 chips at every decision (surface.md §12,
        # environment.md §1, shapes.md §2).
        for seed in (S.SEED_Q, S.SEED_R):
            readout = self.readout(self.new_hand(seed, S.SHAPE_SIZED))
            self.assertEqual(
                readout["street"],
                "preflop",
                "the first decision of a no-limit hand is preflop (environment.md §1): "
                "seed %r read %r" % (seed, readout["street"]),
            )
            self.assertEqual(
                S.one_number(readout["pot"], "the readout's pot fact"),
                3,
                "the pot holds the two blinds, 1 + 2, in every declared shape "
                "(environment.md §1, shapes.md §2): seed %r read %r"
                % (seed, readout["pot"]),
            )
            self.assertEqual(
                S.count_list(readout["stacks"], "the readout's stacks fact"),
                [row["starting_stack"] - 1, row["starting_stack"] - 2],
                "the button posts 1 and the big blind 2 off a 100-chip stack, so the stacks "
                "behind are 99 and 98 in seat order (environment.md §1, shapes.md §2): "
                "seed %r read %r" % (seed, readout["stacks"]),
            )
            self.assertEqual(
                S.one_number(readout["to_call"], "the readout's to_call fact"),
                1,
                "the button owes the big blind one chip (environment.md §1): seed %r read "
                "%r" % (seed, readout["to_call"]),
            )
            index, button = S.seat_fact(readout["seat"])
            self.assertEqual(
                (index, button),
                (0, True),
                "seat 0 holds the button and acts first preflop in every declared shape "
                "(surface.md §4, environment.md §1): seed %r read %r"
                % (seed, readout["seat"]),
            )
            self.assertEqual(
                tuple(S.numbers_in(readout["limit"])),
                (2, 0),
                "a shape without a cap keeps the limit fact's two entries and its "
                "derivation: the bet size in force is the big blind of 2 and no "
                "bet-or-raise action has been made on this street yet (environment.md §2): "
                "seed %r read %r" % (seed, readout["limit"]),
            )
            self.assert_chips_conserved(S.SHAPE_SIZED, seed, row["chips_in_play"])

    def test_fam19_05_two_calls_are_equal_and_an_edit_does_not_reach_the_catalogue(self):
        """FAM-19.5 two calls return equal values, and a caller's edit of a row stays the caller's (§12)."""
        before = S.canon(self.game_shapes())
        first = self.game_shapes()
        row = row_of(self, first, S.SHAPE_DEFAULT)
        try_edit(row, "starting_stack", 9999)
        try_edit(row, "actions", ("fold",))
        try_edit(row, "head_width", 1)
        normalisers = S.required(row, "a returned row", "normalisers")
        try_edit(normalisers, "pot", 1)
        try_edit(normalisers, "stack", 1)
        sized = row_of(self, first, S.SHAPE_SIZED)
        try_edit(sized, "default", True)
        try_edit(first, S.SHAPE_DEFAULT, {"name": "an invented shape"})
        second = self.game_shapes()
        self.assertEqual(
            S.canon(second),
            before,
            "the returned mapping is fresh, so a caller's edit of a row cannot reach the "
            "catalogue (surface.md §12, D-13): the second call returned %r against %r"
            % (S.canon(second), before),
        )
        self.assertEqual(
            [str(key) for key in second],
            list(DECLARED),
            "a caller's edit of the mapping cannot remove or add a declared shape "
            "(surface.md §12): the catalogue keyed %r"
            % ([str(key) for key in second],),
        )
        self.assertEqual(
            S.canon(self.game_shapes()),
            S.canon(second),
            "two calls with no argument return equal values and there is no per-call "
            "state (surface.md §12, §3)",
        )

    # -- the two configs ---------------------------------------------------
    def test_fam19_06_game_config_with_no_argument_is_the_default_rows_config(self):
        """FAM-19.6 game_config() is game_config('fixed-limit-20'), with the fifteen declared keys (§3)."""
        config = self.game_config()
        self.assertTrue(
            S.is_mapping(config),
            "game_config() returns one shape's parameters as one mapping (surface.md §3); "
            "it returned %r" % (config,),
        )
        self.assertEqual(
            set(config),
            set(CONFIG_FACTS),
            "the config states exactly the fifteen declared keys and the bet structure is "
            "§12's row and never a key here (surface.md §3): it stated %r"
            % (sorted(str(key) for key in config),),
        )
        self.assertEqual(
            S.canon(config),
            S.canon(self.game_config(S.SHAPE_DEFAULT)),
            "with no argument game_config returns the default shape's row, byte for byte "
            "the mapping it has always returned, so it is equal to the named call "
            "(surface.md §3, shapes.md §2)",
        )
        self.assertEqual(
            config["game"],
            "fixed-limit texas hold'em",
            "the default row's `game` name says which game, and a shape's name is never "
            "carried here as a second spelling (surface.md §3): %r" % (config["game"],),
        )
        self.assertEqual(
            config["seats"],
            2,
            "the game seats two, and `player_count` repeats it (surface.md §3): %r"
            % (config["seats"],),
        )
        self.assertEqual(
            config["player_count"],
            config["seats"],
            "the two seat keys state one number (surface.md §3): %r against %r"
            % (config["player_count"], config["seats"]),
        )
        self.assertEqual(
            config["button_seat"],
            0,
            "seat 0 holds the button (surface.md §4, environment.md §1): %r"
            % (config["button_seat"],),
        )
        self.assertEqual(
            tuple(S.numbers_in(config["blinds"])),
            (1, 2),
            "the blinds are 1 and 2 (surface.md §3, ASM-6): %r" % (config["blinds"],),
        )
        self.assertEqual(
            (config["small_blind"], config["big_blind"]),
            (1, 2),
            "the two blinds are stated again as numbers, because the report reads them "
            "numerically (surface.md §3): %r" % ((config["small_blind"], config["big_blind"]),),
        )
        self.assertEqual(
            config["blind_levels"],
            1,
            "one blind level, and it never rises (surface.md §3, ASM-6): %r"
            % (config["blind_levels"],),
        )
        self.assertEqual(
            config["starting_stack"],
            20,
            "the default shape's starting stack is 20 chips (surface.md §3, ASM-6): %r"
            % (config["starting_stack"],),
        )
        self.assertEqual(
            tuple(S.numbers_in(config["starting_stacks"])),
            (20, 20),
            "one starting stack per seat, both 20 (surface.md §3): %r"
            % (config["starting_stacks"],),
        )
        self.assertEqual(
            (config["small_bet"], config["big_bet"], config["raise_cap"]),
            (2, 4, 4),
            "the default shape's small bet, big bet and raise cap are 2, 4 and 4 "
            "(surface.md §3, ASM-6): the config said %r"
            % ((config["small_bet"], config["big_bet"], config["raise_cap"]),),
        )
        self.assertEqual(
            tuple(S.numbers_in(config["limit"])),
            (2, 4),
            "the limit in force is the two fixed bets, as numbers (surface.md §3, ASM-6): "
            "%r" % (config["limit"],),
        )
        self.assertEqual(
            tuple(config["streets"]),
            ("preflop", "flop", "turn", "river"),
            "the four streets are the game's, in their declared order (surface.md §3, "
            "environment.md §2): %r" % (config["streets"],),
        )
        before = S.canon(config)
        try_edit(config, "starting_stack", 9999)
        try_edit(config, "game", "an invented game")
        try_edit(config, "streets", ())
        self.assertEqual(
            S.canon(self.game_config()),
            before,
            "two calls with one argument return equal values and there is no per-call "
            "state, so a caller's edit of a returned config cannot reach the next call "
            "(surface.md §3, D-2)",
        )

    def test_fam19_07_the_sized_config_carries_the_same_fifteen_keys(self):
        """FAM-19.7 game_config('no-limit-100') has the same fifteen keys, differing only in declared values (§3)."""
        default = self.game_config()
        sized = self.game_config(S.SHAPE_SIZED)
        self.assertTrue(
            S.is_mapping(sized),
            "a named shape returns that shape's parameters as one mapping (surface.md §3); "
            "it returned %r" % (sized,),
        )
        self.assertEqual(
            set(sized),
            set(default),
            "a named shape returns the same fifteen keys as the default, with the same "
            "value shapes (surface.md §3): the sized config stated %r against %r"
            % (sorted(str(key) for key in sized), sorted(str(key) for key in default)),
        )
        self.assertEqual(
            set(sized),
            set(CONFIG_FACTS),
            "the sized config states exactly the fifteen declared keys (surface.md §3): "
            "it stated %r" % (sorted(str(key) for key in sized),),
        )
        self.assertEqual(
            sized["game"],
            "no-limit texas hold'em",
            "the sized row states its own game name (surface.md §3, shapes.md §2): %r"
            % (sized["game"],),
        )
        self.assertEqual(
            sized["starting_stack"],
            100,
            "the sized shape's starting stack is 100 chips (surface.md §3): %r"
            % (sized["starting_stack"],),
        )
        self.assertEqual(
            tuple(S.numbers_in(sized["starting_stacks"])),
            (100, 100),
            "one starting stack per seat, both 100 (surface.md §3): %r"
            % (sized["starting_stacks"],),
        )
        for name in ("small_bet", "big_bet", "limit", "raise_cap"):
            self.assertIsNone(
                sized[name],
                "a shape with no fixed bet and no cap states None for %r, because it has "
                "neither (surface.md §3, shapes.md §2): %r" % (name, sized[name]),
            )
        for name in SHARED_CONFIG_FACTS:
            self.assertEqual(
                S.canon(sized[name]),
                S.canon(default[name]),
                "the two shapes share the seats, the blinds, the one blind level and the "
                "four streets, so %r must be equal in both configs (surface.md §3, "
                "shapes.md §2): the sized config said %r against the default's %r"
                % (name, S.canon(sized[name]), S.canon(default[name])),
            )
        self.assertNotEqual(
            S.canon(sized),
            S.canon(default),
            "the two configs differ in the values each shape declares — the game name, the "
            "stack and the bets (surface.md §3): both returned %r" % (S.canon(default),),
        )

    # -- the refusals ------------------------------------------------------
    def test_fam19_08_an_undeclared_name_is_refused_naming_it_and_the_declared_names(self):
        """FAM-19.8 an undeclared shape name is refused by all three entries, naming it and the declared names (§1, §3, §4, §10)."""
        declared = [str(key) for key in self.game_shapes()]
        policy = S.PolicyProbe(name="the battery's policy")
        for name in ("no-limit-200", "fixed-limit-40", "fixedlimit20", "no_limit_100"):
            calls = (
                ("game_config", lambda name=name: self.game_config(name)),
                ("new_hand", lambda name=name: self.new_hand(S.SEED_Q, name)),
                ("play_hand",
                 lambda name=name: self.play_hand(S.SEED_Q, policy, policy, name)),
            )
            for entry_point, call in calls:
                what = "%s with the undeclared shape name %r" % (entry_point, name)
                exc = self.assert_refused_without_moving_the_stream(
                    call, what, ("shape", "declared")
                )
                text = str(exc).lower()
                self.assertIn(
                    name.lower(),
                    text,
                    "%s must be refused naming the value it refused, never defaulted "
                    "(surface.md §1, shapes.md §3); it raised %s: %s"
                    % (what, type(exc).__name__, exc),
                )
                for declared_name in declared:
                    self.assertIn(
                        declared_name.lower(),
                        text,
                        "a shape name outside the catalogue is refused naming it and the "
                        "declared names, so that a caller reads what it may pass "
                        "(surface.md §1, shapes.md §3); %s raised %s: %s"
                        % (what, type(exc).__name__, exc),
                    )
        self.assertEqual(
            [str(key) for key in self.game_shapes()],
            list(DECLARED),
            "a refused name adds no shape and removes none: the catalogue is still the "
            "declaration it was (surface.md §12, D-13)",
        )

    def test_fam19_09_a_shape_that_is_not_a_string_is_refused(self):
        """FAM-19.9 a shape that is not a declared name is refused by every entry that takes one (§1, §4, §10)."""
        policy = S.PolicyProbe(name="the battery's policy")
        for bad in (5, 2.5, ("no-limit-100",), ["no-limit-100"], b"no-limit-100",
                    {"shape": "no-limit-100"}, True):
            calls = (
                ("game_config", lambda bad=bad: self.game_config(bad)),
                ("new_hand", lambda bad=bad: self.new_hand(S.SEED_R, bad)),
                ("play_hand", lambda bad=bad: self.play_hand(S.SEED_R, policy, policy, bad)),
            )
            for entry_point, call in calls:
                what = "%s with the shape %r, which names no declared shape" % (
                    entry_point, bad)
                self.assert_refused_without_moving_the_stream(
                    call, what, ("shape", "declared")
                )

    def test_fam19_10_absence_and_none_are_the_default_shape(self):
        """FAM-19.10 an absent shape and None both read as the default, and no shape moves the deal (§4, §10, §5)."""
        seed = S.SEED_R
        absent = self.readout(self.new_hand(seed))
        explicit_none = self.readout(self.new_hand(seed, None))
        named_default = self.readout(self.new_hand(seed, S.SHAPE_DEFAULT))
        self.assertEqual(
            S.canon(absent),
            S.canon(explicit_none),
            "an absent shape is today's game, so new_hand(seed) and new_hand(seed, None) "
            "deal one hand and read one mapping (surface.md §4, shapes.md §3)",
        )
        self.assertEqual(
            S.canon(explicit_none),
            S.canon(named_default),
            "None and the default shape's name denote the same shape, so the two calls "
            "read one mapping (surface.md §4, shapes.md §3)",
        )
        sized = self.readout(self.new_hand(seed, S.SHAPE_SIZED))
        self.assertNotEqual(
            S.canon(named_default),
            S.canon(sized),
            "a named shape deals that shape's state, so the sized row's deal is not the "
            "default's (surface.md §4, shapes.md §3): both read %r"
            % (S.canon(named_default),),
        )
        self.assertEqual(
            S.canon(named_default["hole"]),
            S.canon(sized["hole"]),
            "the shape does not move the deal stream: one seed deals one deck in every "
            "shape, so the hole cards are the same (environment.md §5, shapes.md §5): "
            "%r against %r" % (named_default["hole"], sized["hole"]),
        )
        episodes = [
            S.canon(self.play_hand(seed, S.PolicyProbe(S.choose_call, name="seat 0"),
                                   S.PolicyProbe(S.choose_call, name="seat 1"))),
            S.canon(self.play_hand(seed, S.PolicyProbe(S.choose_call, name="seat 0"),
                                   S.PolicyProbe(S.choose_call, name="seat 1"), None)),
            S.canon(self.play_hand(seed, S.PolicyProbe(S.choose_call, name="seat 0"),
                                   S.PolicyProbe(S.choose_call, name="seat 1"),
                                   S.SHAPE_DEFAULT)),
        ]
        self.assertEqual(
            episodes[0],
            episodes[1],
            "play_hand's absent shape and an explicit None are the same episode: it deals "
            "through new_hand at that seed and shape (surface.md §10, shapes.md §3)",
        )
        self.assertEqual(
            episodes[1],
            episodes[2],
            "None and the default shape's name play the same hand card for card "
            "(surface.md §10, shapes.md §3)",
        )

    # -- the stream --------------------------------------------------------
    def assert_refused_without_moving_the_stream(self, call, what, words=()):
        """Assert ``call`` is refused, and that it is refused before any deal moves the stream.

        surface.md §4 and §10: the shape is checked **before** the deal, so a refused
        name cannot leave the global `random` where a deal would have left it (ASM-2).
        """
        before = self.stream()
        exc = self.assert_refused(call, what, words)
        self.assertEqual(
            S.canon(before),
            S.canon(self.stream()),
            "%s: the refusal happens before the deal, so the global random stream is "
            "untouched (surface.md §4, §10, ASM-2)" % (what,),
        )
        return exc


if __name__ == "__main__":
    unittest.main()
