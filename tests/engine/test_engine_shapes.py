"""ENG-12 and ENG-13 -- the two declared shapes, and the four raise bands.

``docs/L2/engine/surface.md`` §2, §3, §6, §7, §10, §12;
``docs/L2/engine/environment.md`` §1, §3; ``docs/L3/engine/config.md`` §1-§6;
``docs/L3/engine/actions.md`` §1-§3; ``docs/L3/engine/episode.md`` §3;
``docs/L3/engine/hand.md`` §2, §4; ``docs/L1/shapes.md`` §2-§5;
``docs/L1/sizing.md`` §2-§3 (D-29, D-30).

The game is no longer one declaration for the whole project.  ``game_shapes()``
publishes two rows, default first, and every entry point that names a game takes the
shape as an **optional argument whose absence is today's value**, so the fixed-limit
path is unchanged card for card: the same stacks, the same three descriptors, the
same ``raise`` resolving to the minimum legal completion.

What the second row adds is a vocabulary of sizes.  Its four raise descriptors
partition the decision's legal raise interval ``[m, A]``, each resolving to its own
band's maximum, so two descriptors never resolve to one amount and a band holding no
legal amount is **masked out of ``legal_actions``, never collapsed onto its
neighbour** (``sizing.md`` §2).  ENG-13 pins that arithmetic against each decision's
own ``minimum``/``maximum``, including the decisions where a band is empty.
"""

import os
import random
import sys
import unittest

try:  # discovered as part of a tests.engine package
    from . import _engine_support as S
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _engine_support as S  # noqa: E402

#: The three amount facts a decision carries beside its five (episode.md §3).
AMOUNT_FACTS = ("minimum", "maximum", "amount")

#: The eight facts one decision record holds -- the five of ``records.md`` §5 and the
#: three amounts above (environment.md §3, episode.md §3).
DECISION_FACTS = ("seat", "readout", "legal", "action", "reward") + AMOUNT_FACTS

#: The four raise descriptors of the no-cap row, in an order this file reads from the
#: cheapest band to the widest -- *not* the declared index order, which is the point
#: of ENG-13.1 (config.md §6, sizing.md §3).
BY_BAND = ("raise-minimum", "raise-quarter", "raise-half", "raise-all-in")

#: What each band resolves to at the no-cap row's first decision, where the interval is
#: ``[4, 100]``: ``minimum`` 4, ``quarter`` 4 + 96//4, ``half`` 4 + 96//2, ``all-in`` 100
#: (config.md §5, §6; sizing.md §2).  Spelled out as literals because it is the one
#: decision every no-cap hand shares and the numbers are the declaration's.
FIRST_DECISION_AMOUNTS = {
    "raise-minimum": 4,
    "raise-quarter": 28,
    "raise-half": 52,
    "raise-all-in": 100,
}

#: The raise descriptors legal at a decision whose raise interval has span ``L`` -- the
#: declaration's own answer, in the row's index order (config.md §5, sizing.md §2): at
#: ``L = 0`` only the minimum; at ``L = 1`` only it and the all-in; at ``L = 2`` and
#: ``L = 3`` it, the half and the all-in; from ``L = 4`` all four.
LEGAL_RAISES_BY_SPAN = {
    0: ("raise-minimum",),
    1: ("raise-all-in", "raise-minimum"),
    2: ("raise-half", "raise-all-in", "raise-minimum"),
    3: ("raise-half", "raise-all-in", "raise-minimum"),
    4: S.SIZED_RAISES,
}


class ENG12Catalogue(S.EngineCase):
    """The catalogue, its two rows, and the shape argument every entry point takes."""

    def test_eng12_1_the_catalogue_is_one_ordered_mapping_default_first(self):
        """ENG-12.1 game_shapes() takes no argument and returns an ordered mapping of
        exactly two rows, `fixed-limit-20` then `no-limit-100`, each row naming the key
        it is filed under and exactly one of them flagged `default`; the package exports
        those ten names and no other (surface.md §1, §12, shapes.md §2, D-29)."""
        catalogue = self.catalogue()
        self.assertTrue(
            S.is_mapping(catalogue),
            "game_shapes() returns the declared shapes as one mapping (surface.md §12)",
        )
        self.assertEqual(
            list(catalogue), list(S.SHAPE_NAMES),
            "the catalogue is ordered, default first: %r then %r, and nothing else "
            "(surface.md §12, shapes.md §2): got %r"
            % (S.DEFAULT_SHAPE, S.NO_LIMIT_SHAPE, list(catalogue)),
        )
        for name, row in catalogue.items():
            with self.subTest(shape=name):
                self.assertTrue(
                    S.is_mapping(row),
                    "a catalogue row is one mapping of declared values (surface.md §12)",
                )
                self.assertEqual(
                    row["name"], name,
                    "a row's own `name` is the key it is filed under, so no caller can read "
                    "two names for one row (surface.md §12)",
                )
        defaults = [name for name, row in catalogue.items() if row["default"]]
        self.assertEqual(
            defaults, [S.DEFAULT_SHAPE],
            "exactly one row is the default, and it is the catalogue's first: an absent "
            "shape reads as it (surface.md §12, config.md §1): got %r" % (defaults,),
        )

        with self.assertRaises(
            TypeError,
            msg="game_shapes() takes no argument and refuses nothing, because the "
                "instance set is the declaration itself (surface.md §12)",
        ):
            S.ep("game_shapes")(S.NO_LIMIT_SHAPE)

        self.assertEqual(
            tuple(S.engine().__all__), S.NINE,
            "the package declares the ten entry points of surface.md §1 and no other "
            "public name, `game_shapes` included (surface.md §12, layout.md §2)",
        )

    def test_eng12_2_each_row_declares_its_own_width_seats_and_chips_in_play(self):
        """ENG-12.2 every row carries exactly the thirteen declared keys, two seats, the
        same blinds 1 and 2, a head width equal to its descriptor count, and a chips-in-
        play total equal to the seats' stacks (surface.md §12, config.md §2, §4)."""
        catalogue = self.catalogue()
        for name in S.SHAPE_NAMES:
            row = catalogue[name]
            with self.subTest(shape=name):
                self.assertEqual(
                    set(row), set(S.ROW_KEYS),
                    "a row carries exactly the thirteen declared keys and nothing else "
                    "(surface.md §12): got %r for %r" % (sorted(row), name),
                )
                self.assertEqual(
                    row["seats"], 2,
                    "both shapes declare two seats, so no row re-seats a hand "
                    "(config.md §2, shapes.md §2)",
                )
                self.assertEqual(
                    tuple(row["blinds"]), (1, 2),
                    "both shapes declare blinds 1 and 2: %r" % (tuple(row["blinds"]),),
                )
                self.assertEqual(
                    tuple(row["actions"]), S.SHAPE_ACTIONS[name],
                    "the row declares its vocabulary in its own index order "
                    "(config.md §2, §6): got %r for %r" % (tuple(row["actions"]), name),
                )
                self.assertEqual(
                    row["head_width"], len(row["actions"]),
                    "the head width is the shape's descriptor count -- %d for %r -- so the "
                    "head is the vocabulary's size (surface.md §12, sizing.md §6): got %r"
                    % (len(row["actions"]), name, row["head_width"]),
                )
                self.assertEqual(
                    row["chips_in_play"], row["seats"] * row["starting_stack"],
                    "the chips in play are the row's own total, both seats' starting "
                    "stacks (config.md §4, shapes.md §2): %r for %r"
                    % (row["chips_in_play"], name),
                )
                self.assertEqual(
                    [row["starting_stack"], row["chips_in_play"]],
                    [S.SHAPE_STARTING_STACK[name], S.SHAPE_CHIPS_IN_PLAY[name]],
                    "the row starts each seat with %d chips and puts %d in play (config.md "
                    "§2): got %r" % (S.SHAPE_STARTING_STACK[name],
                                     S.SHAPE_CHIPS_IN_PLAY[name],
                                     [row["starting_stack"], row["chips_in_play"]]),
                )
        self.assertEqual(
            {name: catalogue[name]["bet_structure"] for name in S.SHAPE_NAMES},
            {S.DEFAULT_SHAPE: "fixed-limit", S.NO_LIMIT_SHAPE: "no-limit"},
            "each row states its bet structure, and it is what the state's class is "
            "picked from (config.md §2, D-29)",
        )
        self.assertEqual(
            {name: catalogue[name]["head_width"] for name in S.SHAPE_NAMES},
            {S.DEFAULT_SHAPE: 3, S.NO_LIMIT_SHAPE: 6},
            "the default row's head is three wide and the no-cap row's six (surface.md "
            "§12, sizing.md §6)",
        )

    def test_eng12_3_the_divisors_are_five_numbers_and_the_no_cap_row_declares_none(self):
        """ENG-12.3 every row declares the five normalisers, with the exact numbers
        config.md §4 fixes for it; the default row states its small bet, big bet and cap
        as numbers and the no-cap row declares `None` for all three (surface.md §12,
        config.md §4, sizing.md §5)."""
        catalogue = self.catalogue()
        declared = {
            S.DEFAULT_SHAPE: {"stack": 20, "pot": 40, "to_call": 20, "amount": 4, "count": 4},
            S.NO_LIMIT_SHAPE: {"stack": 100, "pot": 200, "to_call": 100, "amount": 100,
                               "count": 50},
        }
        for name in S.SHAPE_NAMES:
            row = catalogue[name]
            normalisers = row["normalisers"]
            with self.subTest(shape=name):
                self.assertEqual(
                    set(normalisers), set(S.NORMALISER_KEYS),
                    "a row declares one divisor per declared key, five in all "
                    "(surface.md §12, config.md §4): got %r" % (sorted(normalisers),),
                )
                self.assertEqual(
                    dict(normalisers), declared[name],
                    "the row's divisors are the numbers config.md §4 states for %r, so a "
                    "divisor never travels between rows (sizing.md §5, D-25): got %r"
                    % (name, dict(normalisers)),
                )
                self.assertEqual(
                    [normalisers["stack"], normalisers["pot"]],
                    [row["starting_stack"], row["chips_in_play"]],
                    "the stack divisor is a starting stack and the pot divisor the chips "
                    "in play (config.md §4): %r" % (dict(normalisers),),
                )

        default = catalogue[S.DEFAULT_SHAPE]
        no_limit = catalogue[S.NO_LIMIT_SHAPE]
        for key, number in (("small_bet", 2), ("big_bet", 4), ("raise_cap", 4)):
            with self.subTest(key=key):
                self.assertEqual(
                    default[key], number,
                    "the default row declares its %r as the number %d, because its bets "
                    "are fixed and its street is capped (config.md §2, ASM-6)" % (key, number),
                )
                self.assertIsNone(
                    no_limit[key],
                    "a shape with no fixed bet and no cap declares None for %r, never a "
                    "number borrowed from the default row (surface.md §12, config.md §2, "
                    "D-29)" % (key,),
                )
        self.assertEqual(
            [default["normalisers"]["amount"], default["normalisers"]["count"]],
            [default["big_bet"], default["raise_cap"]],
            "the default row's amount divisor is its big bet and its count divisor its cap "
            "(config.md §4)",
        )
        self.assertEqual(
            [no_limit["normalisers"]["amount"], no_limit["normalisers"]["count"]],
            [no_limit["starting_stack"], no_limit["starting_stack"] // 2],
            "the no-cap row's amount divisor is a stack and its count divisor 100 // 2, the "
            "most bet-or-raise actions its stack admits (config.md §4, sizing.md §5)",
        )

    def test_eng12_4_a_callers_edit_of_a_returned_row_cannot_reach_the_catalogue(self):
        """ENG-12.4 two calls return equal values, and a caller's edit of a returned row --
        its normalisers, its actions, its name, a row it adds -- reaches neither the next
        call nor the mapping another caller already holds (surface.md §12, D-2)."""
        snapshot = self.catalogue()
        self.assertEqual(
            self.catalogue(), snapshot,
            "two calls of game_shapes() return equal values: the catalogue is the "
            "declaration and not per-call state (surface.md §12, D-2)",
        )

        edited = self.catalogue()
        edited[S.NO_LIMIT_SHAPE]["normalisers"]["pot"] = 1
        edited[S.NO_LIMIT_SHAPE]["actions"] = ()
        edited[S.NO_LIMIT_SHAPE]["name"] = "invented"
        edited[S.NO_LIMIT_SHAPE]["head_width"] = 99
        edited[S.DEFAULT_SHAPE]["default"] = False
        edited["no-limit-50"] = {}
        self.assertEqual(
            self.catalogue(), snapshot,
            "the returned mapping is fresh: a caller's edit of a row cannot reach the "
            "catalogue, and no caller can invent a shape through it (surface.md §12, D-29)",
        )
        self.assertEqual(
            list(self.catalogue()), list(S.SHAPE_NAMES),
            "nor can an added key survive into the next call: the catalogue is fixed "
            "(surface.md §12, shapes.md §2)",
        )
        self.assertEqual(
            self.catalogue()[S.NO_LIMIT_SHAPE]["normalisers"]["pot"],
            S.SHAPE_CHIPS_IN_PLAY[S.NO_LIMIT_SHAPE],
            "the no-cap row's pot divisor is still its chips in play after that edit "
            "(config.md §4)",
        )

    def test_eng12_5_game_config_returns_the_default_rows_fifteen_keys(self):
        """ENG-12.5 game_config() is equal to game_config('fixed-limit-20'), carries
        exactly the fifteen declared keys in the declared order, and states the default
        row's numbers: stacks 20, blinds 1 and 2, bets 2 and 4, cap 4, four streets
        (surface.md §3, config.md §3, ASM-6)."""
        config = self.config()
        self.assertEqual(
            tuple(config), S.CONFIG_KEYS,
            "game_config carries exactly the fifteen declared keys, in the declared order "
            "(config.md §3): got %r" % (list(config),),
        )
        self.assertEqual(
            config, S.ep("game_config")(S.DEFAULT_SHAPE),
            "called with no argument it returns the default shape's row, so the two calls "
            "are equal (surface.md §3, shapes.md §2)",
        )
        self.assertTrue(
            S.is_mapping(config) and config,
            "game_config() returns the game's parameters as one non-empty mapping "
            "(surface.md §3)",
        )
        self.assertIsInstance(
            config["game"], str,
            "its `game` name says which game it is (surface.md §3, config.md §3)",
        )
        self.assertTrue(config["game"],
                        "the game name is not empty (config.md §3)")
        self.assertEqual(
            [config["seats"], config["player_count"]], [2, 2],
            "player_count is the row's seats, and both are two (config.md §3)",
        )
        self.assertEqual(
            config["button_seat"], 0,
            "seat 0 holds the button, and a posted blind alternates nothing here "
            "(hand.md §3, config.md §3)",
        )
        self.assertEqual(
            [tuple(config["blinds"]), config["small_blind"], config["big_blind"]],
            [(1, 2), 1, 2],
            "the blinds are 1 and 2, stated as the pair and as the two numbers "
            "(config.md §3)",
        )
        self.assertEqual(
            config["blind_levels"], 1,
            "one blind level, and it never rises (config.md §3, ASM-6)",
        )
        self.assertEqual(
            [config["starting_stack"], tuple(config["starting_stacks"])],
            [S.SHAPE_STARTING_STACK[S.DEFAULT_SHAPE],
             (S.SHAPE_STARTING_STACK[S.DEFAULT_SHAPE],) * 2],
            "the default row starts each of the two seats with 20 chips (surface.md §3, "
            "config.md §3)",
        )
        self.assertEqual(
            [config["small_bet"], config["big_bet"], tuple(config["limit"])],
            [2, 4, (2, 4)],
            "the fixed bets are 2 and 4, and `limit` is that pair (config.md §3, ASM-6)",
        )
        self.assertEqual(
            config["raise_cap"], 4,
            "the cap is four bet-or-raise actions a street (config.md §3, ASM-6)",
        )
        self.assertEqual(
            tuple(config["streets"]), S.STREETS,
            "the four streets of the declared order (config.md §3, readout.md §2)",
        )

    def test_eng12_6_game_config_of_the_no_cap_row_differs_only_in_its_declared_values(self):
        """ENG-12.6 game_config('no-limit-100') carries the same fifteen keys in the same
        order and differs only where the row differs: its game name, stacks 100, and
        `None` for `small_bet`, `big_bet`, `limit` and `raise_cap`, which the default row
        states as numbers (surface.md §3, config.md §3, D-29)."""
        default = self.config()
        no_limit = S.ep("game_config")(S.NO_LIMIT_SHAPE)
        self.assertEqual(
            tuple(no_limit), tuple(default),
            "a named shape returns the same fifteen keys in the same order, so one reader "
            "reads either row (surface.md §3, config.md §3): got %r" % (list(no_limit),),
        )
        self.assertEqual(
            tuple(no_limit), S.CONFIG_KEYS,
            "and those fifteen keys are the declared ones (config.md §3)",
        )
        for key in ("seats", "player_count", "button_seat", "blinds", "small_blind",
                    "big_blind", "blind_levels", "streets"):
            with self.subTest(key=key):
                self.assertEqual(
                    no_limit[key], default[key],
                    "the two rows share %r: the shapes differ in the game's numbers and "
                    "not in its seating or its streets (shapes.md §2, hand.md §4)" % (key,),
                )
        self.assertEqual(
            no_limit["game"], "no-limit texas hold'em",
            "the no-cap row's game name is the words config.md §3 declares (surface.md §3)",
        )
        self.assertNotEqual(
            no_limit["game"], default["game"],
            "each row's game name says which game it is, so the two names differ "
            "(config.md §3)",
        )
        self.assertEqual(
            no_limit["starting_stack"], S.SHAPE_STARTING_STACK[S.NO_LIMIT_SHAPE],
            "the no-cap row's stacks are 100 chips (surface.md §3, config.md §3)",
        )
        self.assertEqual(
            tuple(no_limit["starting_stacks"]),
            (S.SHAPE_STARTING_STACK[S.NO_LIMIT_SHAPE],) * 2,
            "both seats start with 100 chips, so the pair is the stack twice "
            "(config.md §3)",
        )
        for key in ("small_bet", "big_bet", "raise_cap"):
            with self.subTest(key=key):
                self.assertIsNone(
                    no_limit[key],
                    "a row with no fixed bet and no cap declares None for %r, because it "
                    "has neither (surface.md §3, config.md §3, D-29)" % (key,),
                )
                self.assertTrue(
                    S.is_number(default[key]),
                    "while the default row states %r as a number, not as prose "
                    "(surface.md §3): got %r" % (key, default[key]),
                )
        self.assertIsNone(
            no_limit["limit"],
            "`limit` is the (small_bet, big_bet) pair, so a row without either declares "
            "None and never a pair of Nones (config.md §3, D-29)",
        )
        self.assertEqual(
            [S.is_number(default["limit"][0]), S.is_number(default["limit"][1])], [True, True],
            "while the default row's `limit` is the pair of its two fixed bets "
            "(config.md §3)",
        )

    def test_eng12_7_the_no_cap_deals_first_decision_reads_its_own_numbers(self):
        """ENG-12.7 at any seed a no-limit-100 deal's first decision reads street
        `preflop`, pot 3, stacks (99, 98), to_call 1, seat (0, True), limit (2, 0), an
        empty board and history, two hole cards, and the same eleven facts (config.md §6,
        hand.md §4, environment.md §2)."""
        for seed in (S.SHAPE_SEED_A, S.SHAPE_SEED_B, S.SHAPE_SEED_C):
            with self.subTest(seed=seed):
                facts = self.readout(self.shaped_hand(seed, S.NO_LIMIT_SHAPE))
                self.assertEqual(
                    set(facts), set(S.FACTS),
                    "the readout carries exactly the eleven facts in both shapes, so the "
                    "second shape widens no information set (surface.md §5, environment.md "
                    "§2, D-3): got %r" % (sorted(facts),),
                )
                self.assertEqual(
                    facts["street"], "preflop",
                    "the first decision is pre-flop, where the button owes the big blind "
                    "(hand.md §4): %r" % (facts["street"],),
                )
                self.assertEqual(
                    facts["pot"], 3,
                    "the pot holds the two blinds, 1 and 2 (config.md §6, environment.md §1)",
                )
                self.assertEqual(
                    tuple(facts["stacks"]), (99, 98),
                    "the stacks behind are 99 and 98 out of the row's 100, in seat order -- "
                    "seat 0 posted the small blind -- and it is the seat map of hand.md §3 "
                    "at the no-cap row's own stacks (hand.md §4): got %r"
                    % (tuple(facts["stacks"]),),
                )
                self.assertEqual(
                    facts["to_call"], 1,
                    "the button owes the big blind one chip (hand.md §4)",
                )
                self.assertEqual(
                    tuple(facts["seat"]), (0, True),
                    "seat 0 holds the button and acts first pre-flop in every shape "
                    "(hand.md §4, shapes.md §2): got %r" % (tuple(facts["seat"]),),
                )
                self.assertEqual(
                    tuple(facts["limit"]), (2, 0),
                    "the bet size in force is the big blind and no bet-or-raise action has "
                    "been made on the street, so the posted blind is not one of them "
                    "(config.md §6, environment.md §2): got %r" % (tuple(facts["limit"]),),
                )
                self.assertEqual(
                    tuple(facts["board"]), (),
                    "no public card is known at the first decision (environment.md §1)",
                )
                self.assertEqual(
                    len(facts["hole"]), 2,
                    "the acting seat holds two cards from the first decision on "
                    "(environment.md §2)",
                )
                self.assertEqual(
                    list(facts["history"]), [],
                    "no action has been applied yet, so the public history is the empty "
                    "list (environment.md §2)",
                )

    def test_eng12_8_the_hand_conserves_the_chips_its_own_shape_declares(self):
        """ENG-12.8 at every decision of every played hand, `pot + sum(stacks)` is the
        chips in play the hand's own shape declares -- 40 in the default shape and 200 in
        the no-cap one -- because committed chips sit in the pot and never in a stack
        (environment.md §1, config.md §4, surface.md §12)."""
        catalogue = self.catalogue()
        for shape in S.SHAPE_NAMES:
            declared = catalogue[shape]["chips_in_play"]
            raising = S.always_raise if shape == S.DEFAULT_SHAPE else S.last_legal
            self.assertEqual(
                declared, S.SHAPE_CHIPS_IN_PLAY[shape],
                "the row's own total is the number the invariant is asserted against: "
                "%r declares %d (config.md §4)" % (shape, S.SHAPE_CHIPS_IN_PLAY[shape]),
            )
            for seed in (S.SHAPE_SEED_A, S.SHAPE_SEED_D):
                for label, policy in (("calling", S.always_call), ("raising", raising)):
                    with self.subTest(shape=shape, seed=seed, policy=label):
                        record = self.shaped_episode(seed, policy, policy, shape)
                        self.assertGreaterEqual(
                            len(record["decisions"]), 2,
                            "the walk takes more than one decision, so the invariant is "
                            "asserted where chips have been committed: %r"
                            % (record["decisions"],),
                        )
                        for position, decision in enumerate(record["decisions"]):
                            facts = decision["readout"]
                            self.assertEqual(
                                facts["pot"] + sum(facts["stacks"]), declared,
                                "pot + sum(stacks) is the chips in play of the hand's own "
                                "shape at every decision -- %d in %r -- because committed "
                                "chips sit in the pot and never in a stack "
                                "(environment.md §1, config.md §4): decision %d read pot %r "
                                "and stacks %r"
                                % (declared, shape, position, facts["pot"], facts["stacks"]),
                            )

    def test_eng12_9_an_unknown_or_non_str_shape_is_refused_naming_it(self):
        """ENG-12.9 a shape name outside the catalogue is refused by game_config, new_hand
        and play_hand alike, naming the value and both declared names, and a non-str value
        is refused too -- both before the deal, so the global stream does not move
        (surface.md §1, §3, §4, §10, config.md §1, shapes.md §3, D-13)."""
        rejected = "no-limit-50"
        for entry_point, arguments in (
            ("game_config", (rejected,)),
            ("new_hand", (S.SHAPE_SEED_A, rejected)),
            ("play_hand", (S.SHAPE_SEED_A, S.always_call, S.always_call, rejected)),
        ):
            with self.subTest(entry_point=entry_point):
                saved = random.getstate()
                exc = self.refusal(S.ep(entry_point), *arguments)
                self.assert_mentions(exc, rejected)
                self.assert_mentions(exc, S.DEFAULT_SHAPE)
                self.assert_mentions(exc, S.NO_LIMIT_SHAPE)
                self.assertEqual(
                    random.getstate(), saved,
                    "%s refused the name before the deal, so the global random stream is "
                    "untouched: a shape name is refused and never defaulted "
                    "(surface.md §4, hand.md §2, D-13)" % (entry_point,),
                )

        for value in (7, 100.0, True, ("no-limit-100",), b"no-limit-100"):
            for entry_point, arguments in (
                ("game_config", (value,)),
                ("new_hand", (S.SHAPE_SEED_B, value)),
            ):
                with self.subTest(entry_point=entry_point, value=repr(value)):
                    saved = random.getstate()
                    exc = self.refusal(S.ep(entry_point), *arguments)
                    self.assert_mentions(exc, S.DEFAULT_SHAPE, S.NO_LIMIT_SHAPE)
                    self.assertEqual(
                        random.getstate(), saved,
                        "a non-str shape is refused before the deal and moves no stream: "
                        "there is no coercion of a shape value (surface.md §1, config.md §1)",
                    )

    def test_eng12_10_an_absent_shape_and_a_none_shape_are_the_default(self):
        """ENG-12.10 new_hand and play_hand treat an absent shape and an explicit None as
        the default shape, equal to naming it, because absence is today's value and
        `None` is absence rather than a defaulted name (surface.md §4, §10, config.md §1,
        shapes.md §3)."""
        absent = S.ep("new_hand")(S.SHAPE_SEED_E)
        none_shape = S.ep("new_hand")(S.SHAPE_SEED_E, None)
        named = S.ep("new_hand")(S.SHAPE_SEED_E, S.DEFAULT_SHAPE)
        self.assertEqual(
            self.readout(none_shape), self.readout(absent),
            "new_hand(seed, None) deals the default shape's hand, card for card "
            "(surface.md §4, shapes.md §3)",
        )
        self.assertEqual(
            self.readout(named), self.readout(absent),
            "and naming the default shape is the same call as omitting it, so today's "
            "call deals today's hand (shapes.md §5)",
        )

        first = self.episode(S.SHAPE_SEED_E)
        second = S.ep("play_hand")(S.SHAPE_SEED_E, S.always_call, S.always_call, None)
        third = S.ep("play_hand")(S.SHAPE_SEED_E, S.always_call, S.always_call,
                                  S.DEFAULT_SHAPE)
        self.assertEqual(
            second, first,
            "play_hand(seed, p0, p1, None) is play_hand(seed, p0, p1): an absent shape is "
            "the default (surface.md §10, episode.md §1)",
        )
        self.assertEqual(
            third, first,
            "and naming it is the same episode, decision for decision (surface.md §10)",
        )


class ENG13Sized(S.EngineCase):
    """The sized vocabulary, the four bands, and the bands that are masked out."""

    def test_eng13_1_the_no_cap_vocabulary_is_six_descriptors_in_index_order(self):
        """ENG-13.1 legal_actions on a no-cap hand returns the row's six descriptors as a
        tuple in the shape's declared index order -- `fold` and `check-call` first, then
        the four raises worst-priced first -- and that order is not monotone in amount
        (surface.md §2, §6, config.md §6, sizing.md §3)."""
        hand = self.shaped_hand(S.SHAPE_SEED_A, S.NO_LIMIT_SHAPE)
        legal = self.legal(hand)
        self.assertIsInstance(
            legal, tuple,
            "legal_actions returns a tuple of descriptors, never a list a caller may edit "
            "(actions.md §1): got %r" % (type(legal).__name__,),
        )
        self.assertEqual(
            tuple(legal), S.SIZED_ACTIONS,
            "the first decision offers every descriptor of the row, in the shape's own "
            "index order: the two bases, then quarter, half, all-in, minimum "
            "(surface.md §2, §6, config.md §6): got %r" % (tuple(legal),),
        )
        self.assertEqual(
            tuple(self.readout(hand)["legal"]), tuple(legal),
            "the readout's `legal` fact is the same tuple in the same order (surface.md §2)",
        )
        self.assertEqual(
            tuple(self.catalogue()[S.NO_LIMIT_SHAPE]["actions"]), tuple(legal),
            "the tuple is the row's own declared vocabulary, so one declaration serves the "
            "catalogue, legal_actions and the encoder's index order (surface.md §12, "
            "config.md §6)",
        )

        amounts = tuple(S.band_amount(descriptor, 4, 100) for descriptor in S.SIZED_RAISES)
        self.assertEqual(
            amounts, (28, 52, 100, 4),
            "at the first decision the interval is [4, 100], so the four bands resolve to "
            "28, 52, 100 and 4 in that index order (config.md §5, §6)",
        )
        self.assertNotEqual(
            list(amounts), sorted(amounts),
            "the index order is not monotone in amount -- the all-in sits before the "
            "minimum -- so no reader and no test can read an index as a size "
            "(sizing.md §3, D-29): got %r" % (amounts,),
        )
        self.assertLess(
            amounts[-1], amounts[0],
            "the last index is the cheapest band and the first raise index is not: a tie "
            "break toward the smallest index resolves toward a worse-priced band "
            "(sizing.md §3): got %r" % (amounts,),
        )

    def test_eng13_2_the_first_decisions_four_bands_resolve_to_their_own_maximum(self):
        """ENG-13.2 at the no-cap row's first decision the interval is [4, 100] and the
        four raise descriptors resolve to 4, 28, 52 and 100 -- pairwise distinct, each its
        own band's maximum (config.md §5, §6, actions.md §2)."""
        resolved = {}
        for descriptor in BY_BAND:
            with self.subTest(descriptor=descriptor):
                record = self.shaped_episode(
                    S.SHAPE_SEED_A,
                    S.band_walk((descriptor,)),
                    S.band_walk((descriptor,)),
                    S.NO_LIMIT_SHAPE,
                )
                first = record["decisions"][0]
                self.assertEqual(
                    first["action"], descriptor,
                    "the policy returned %r and the engine applied it (surface.md §10)"
                    % (descriptor,),
                )
                self.assertEqual(
                    (first["minimum"], first["maximum"]), (4, 100),
                    "the first decision's raise interval is [4, 100], so the minimum legal "
                    "raise-to is 4 and the all-in raise-to 100 (config.md §6): got %r"
                    % ((first["minimum"], first["maximum"]),),
                )
                self.assertEqual(
                    first["amount"], FIRST_DECISION_AMOUNTS[descriptor],
                    "%r resolves to %d -- its own band's maximum -- and the record carries "
                    "the amount the engine resolved (config.md §5, episode.md §3)"
                    % (descriptor, FIRST_DECISION_AMOUNTS[descriptor]),
                )
                resolved[descriptor] = first["amount"]
        self.assertEqual(
            len(set(resolved.values())), len(BY_BAND),
            "four disjoint bands give four distinct resolutions, so two descriptors never "
            "bet one amount (sizing.md §2): got %r" % (resolved,),
        )

    def test_eng13_3_every_legal_band_resolves_to_the_arithmetic_of_its_bounds(self):
        """ENG-13.3 for every decision of several no-cap hands each legal raise descriptor
        resolves to the maximum of its own band, computed from that decision's own
        `minimum` and `maximum`, each illegal one is absent from legal_actions, and four
        legal bands give four distinct amounts (surface.md §6, config.md §5, sizing.md §2)."""
        patterns = (
            ("all calls", ("check-call",)),
            ("quarter then half", ("raise-quarter", "raise-quarter", "raise-half")),
            ("minimum ladder", ("raise-minimum",)),
        )
        seen_spans = set()
        for seed in (S.SHAPE_SEED_A, S.SHAPE_SEED_B, S.SHAPE_SEED_D):
            for label, pattern in patterns:
                with self.subTest(seed=seed, walk=label):
                    checked = 0
                    walk = self.replay(seed, S.NO_LIMIT_SHAPE,
                                       S.band_walk(pattern), S.band_walk(pattern))
                    for hand, decision in walk:
                        self.assertEqual(
                            self.readout(hand), decision["readout"],
                            "the replayed handle stands at the recorded decision: one seed "
                            "and one action sequence reach one state (episode.md §5)",
                        )
                        legal = tuple(decision["legal"])
                        bounds = (decision["minimum"], decision["maximum"])
                        if bounds == (None, None):
                            for descriptor in S.SIZED_RAISES:
                                self.assertNotIn(
                                    descriptor, legal,
                                    "no raise is legal at this decision -- both bounds are "
                                    "None -- so no raise descriptor appears in legal_actions "
                                    "(environment.md §3, config.md §5): got %r" % (legal,),
                                )
                            continue
                        minimum, maximum = bounds
                        span = maximum - minimum
                        seen_spans.add(span)
                        for descriptor in S.SIZED_RAISES:
                            expected = S.band_amount(descriptor, minimum, maximum)
                            if expected is None:
                                self.assertNotIn(
                                    descriptor, legal,
                                    "%r's band holds no legal amount in [%d, %d], so it is "
                                    "masked out of legal_actions and never collapsed onto a "
                                    "neighbouring band (surface.md §6, config.md §5, "
                                    "sizing.md §2): got %r"
                                    % (descriptor, minimum, maximum, legal),
                                )
                                continue
                            self.assertIn(
                                descriptor, legal,
                                "%r's band holds %d in [%d, %d], so it must appear in "
                                "legal_actions (config.md §5): got %r"
                                % (descriptor, expected, minimum, maximum, legal),
                            )
                            advanced = self.step(hand, descriptor)
                            self.assertFalse(
                                self.terminal(advanced),
                                "a legal raise leaves the other seat to answer, so the "
                                "advanced handle is live and its history readable "
                                "(surface.md §7): %r at [%d, %d] ended the hand"
                                % (descriptor, minimum, maximum),
                            )
                            self.assertEqual(
                                S.raise_to(self.readout(advanced)["history"][-1]), expected,
                                "%r resolves to %d, the maximum of its own band, from the "
                                "bounds [%d, %d] this decision reports (config.md §5, "
                                "actions.md §2)" % (descriptor, expected, minimum, maximum),
                            )
                            if decision["action"] == descriptor:
                                self.assertEqual(
                                    decision["amount"], expected,
                                    "the amount the record carries for the descriptor it "
                                    "applied is the same resolution the step made "
                                    "(episode.md §3): %r recorded %r of %d"
                                    % (descriptor, decision["amount"], expected),
                                )
                            checked += 1
                        if span >= 4:
                            resolutions = [S.band_amount(descriptor, minimum, maximum)
                                           for descriptor in S.SIZED_RAISES]
                            self.assertEqual(
                                len(set(resolutions)), len(S.SIZED_RAISES),
                                "a span of at least 4 admits all four bands, so their four "
                                "resolutions are pairwise distinct (sizing.md §2): [%d, %d] "
                                "gave %r" % (minimum, maximum, resolutions),
                            )
                    self.assertGreater(
                        checked, 0,
                        "the walk at seed %r measures at least one raise resolution, so the "
                        "arithmetic above is asserted and not skipped (config.md §5)"
                        % (seed,),
                    )
        self.assertTrue(
            seen_spans,
            "the sweep met at least one decision with a raise interval to partition "
            "(config.md §6)",
        )

    def test_eng13_4_an_empty_band_is_masked_out_never_collapsed_on_a_neighbour(self):
        """ENG-13.4 walking the no-cap row to raise intervals of span 4, 3, 2, 1 and 0, the
        raise descriptors legal at each are exactly the row's own answer for that span --
        at 0 only `raise-minimum`, at 1 only it and `raise-all-in` -- so an empty band is
        masked out of legal_actions and never collapsed onto its neighbour (surface.md §6,
        config.md §5, sizing.md §2)."""
        walks = (
            ("quarter walk", S.SHAPE_SEED_C, ("raise-quarter", "raise-quarter")),
            ("quarter-half walk", S.SHAPE_SEED_A,
             ("raise-quarter", "raise-quarter", "raise-half")),
        )
        by_span = {}
        for label, seed, pattern in walks:
            walk = self.replay(seed, S.NO_LIMIT_SHAPE,
                               S.band_walk(pattern), S.band_walk(pattern))
            for hand, decision in walk:
                minimum, maximum = decision["minimum"], decision["maximum"]
                if minimum is None:
                    continue
                span = maximum - minimum
                if span > 4:
                    continue
                self.assertEqual(
                    self.readout(hand)["legal"], decision["legal"],
                    "the handle stands at the recorded decision, so the two readings of "
                    "one decision agree (surface.md §2)",
                )
                by_span.setdefault(span, []).append(
                    (label, minimum, maximum, S.raises_in(decision["legal"]))
                )

        self.assertEqual(
            sorted(by_span), sorted(LEGAL_RAISES_BY_SPAN),
            "the walk is the battery's route to every empty band: it must reach a decision "
            "whose raise interval has span 0, 1, 2, 3 and 4, or the masking below is "
            "asserted about nothing (config.md §5): reached %r" % (sorted(by_span),),
        )
        for span, expected in LEGAL_RAISES_BY_SPAN.items():
            for label, minimum, maximum, observed in by_span[span]:
                with self.subTest(span=span, walk=label, bounds=(minimum, maximum)):
                    self.assertEqual(
                        len(observed), len(set(observed)),
                        "a decision holds at most one entry per vocabulary index "
                        "(stepping.md §1): got %r" % (observed,),
                    )
                    self.assertEqual(
                        observed, expected,
                        "with L = %d in [%d, %d] the legal raise descriptors are exactly %r, "
                        "in the row's index order: an empty band is masked out of "
                        "legal_actions and never collapsed onto a neighbour, so no size is "
                        "offered twice and no band bets its neighbour's amount "
                        "(surface.md §6, config.md §5, sizing.md §2): got %r"
                        % (span, minimum, maximum, expected, observed),
                    )
                    if span == 0:
                        self.assertEqual(
                            minimum, maximum,
                            "at L = 0 the interval is the single amount the minimum band "
                            "owns, so both bounds are that one number (config.md §5)",
                        )
                    if span < 4:
                        self.assertNotIn(
                            "raise-quarter", observed,
                            "at L = %d the quarter band is empty and must be masked, never "
                            "collapsed onto the minimum band it would otherwise repeat "
                            "(sizing.md §2)" % (span,),
                        )

    def test_eng13_5_the_fixed_row_keeps_its_single_raise_and_its_point_interval(self):
        """ENG-13.5 the default shape declares the three descriptors it always did, its
        `raise` resolves to the minimum legal completion with minimum == maximum == amount,
        its interval is a point at every decision, and a sized descriptor of the other row
        is refused on its hands (surface.md §2, §7, actions.md §2, config.md §5)."""
        hand = self.hand(S.SHAPE_SEED_A)
        self.assertEqual(
            tuple(self.legal(hand)), S.FIXED_ACTIONS,
            "the default row declares fold, check-call and raise, and only those "
            "(surface.md §2, config.md §2): got %r" % (tuple(self.legal(hand)),),
        )

        record = self.episode(S.SHAPE_SEED_A, S.always_raise, S.always_raise)
        first = record["decisions"][0]
        self.assertEqual(first["action"], "raise", "the policy raised the first decision")
        self.assertEqual(
            (first["minimum"], first["maximum"], first["amount"]), (4, 4, 4),
            "the fixed `raise` resolves to the minimum legal completion, which for a 2/4 "
            "game with blinds 1 and 2 is a raise to 4 -- and that one amount is both "
            "bounds (actions.md §2, config.md §5, §6): got %r"
            % ((first["minimum"], first["maximum"], first["amount"]),),
        )
        for position, decision in enumerate(record["decisions"]):
            legal = tuple(decision["legal"])
            observed = S.raises_in(legal)
            self.assertIn(
                observed, [(), ("raise",)],
                "the fixed row declares no band, so its only raise descriptor is `raise` "
                "and it appears only when a completion is legal (config.md §5, "
                "stepping.md §1): decision %d offered %r" % (position, observed),
            )
            if "raise" in legal:
                self.assertEqual(
                    decision["minimum"], decision["maximum"],
                    "the fixed row's interval is a point -- minimum == maximum -- because "
                    "its completion is unique (config.md §5, actions.md §2): decision %d "
                    "read [%r, %r]" % (position, decision["minimum"], decision["maximum"]),
                )
                self.assertEqual(
                    decision["amount"], decision["minimum"],
                    "the fixed raise resolves to that one amount (actions.md §2): decision "
                    "%d resolved to %r of [%r, %r]"
                    % (position, decision["amount"], decision["minimum"],
                       decision["maximum"]),
                )
            else:
                self.assertIsNone(
                    decision["minimum"],
                    "no completion is legal at this decision, so both bounds are None "
                    "(environment.md §3): decision %d read %r"
                    % (position, decision["minimum"]),
                )

        before = self.readout(hand)
        for foreign in S.SIZED_RAISES:
            with self.subTest(foreign=foreign):
                exc = self.refusal(S.ep("apply_action"), hand, foreign)
                self.assert_mentions(exc, "action", "legal")
                self.assert_untouched(hand, before)
        self.assertEqual(
            tuple(self.legal(hand)), S.FIXED_ACTIONS,
            "a refused descriptor names another shape's vocabulary and leaves the hand at "
            "its own decision, with the three descriptors it declares (actions.md §3, "
            "stepping.md §2)",
        )

    def test_eng13_6_the_three_amount_facts_are_none_exactly_where_declared(self):
        """ENG-13.6 every decision carries `minimum`, `maximum` and `amount`; the bounds
        are None exactly when no raise is legal, `amount` is None exactly when the chosen
        descriptor is not a raise, and the decision's readout keeps its eleven facts in
        both shapes (environment.md §3, episode.md §3, config.md §5)."""
        folded = self.shaped_episode(S.SHAPE_SEED_B, S.always_fold, S.always_fold,
                                     S.NO_LIMIT_SHAPE)["decisions"][0]
        self.assertEqual(
            folded["action"], "fold",
            "the premise: the button folded the first decision, where a raise was legal",
        )
        self.assertIsNone(
            folded["amount"],
            "`amount` is None whenever the chosen descriptor is not a raise, so a fold "
            "carries no amount even where a raise was legal (episode.md §3): got %r"
            % (folded["amount"],),
        )
        self.assertEqual(
            (folded["minimum"], folded["maximum"]), (4, 100),
            "while the bounds are that decision's raise interval, not the action's "
            "(environment.md §3): got %r" % ((folded["minimum"], folded["maximum"]),),
        )

        for shape, seed, policy in (
            (S.DEFAULT_SHAPE, S.SHAPE_SEED_A, S.always_raise),
            (S.NO_LIMIT_SHAPE, S.SHAPE_SEED_D, S.last_legal),
            (S.NO_LIMIT_SHAPE, S.SHAPE_SEED_E, S.always_call),
        ):
            record = self.shaped_episode(seed, policy, policy, shape)
            for position, decision in enumerate(record["decisions"]):
                with self.subTest(shape=shape, seed=seed, decision=position):
                    for key in DECISION_FACTS:
                        self.assertIn(
                            key, decision,
                            "a decision carries its eight facts -- the five of records.md "
                            "§5 and the three amounts -- in both shapes (environment.md §3, "
                            "episode.md §3): missing %r" % (key,),
                        )
                    self.assertEqual(
                        set(decision["readout"]), set(S.FACTS),
                        "the decision's readout is the whole eleven-fact mapping, so the "
                        "amounts are the record's and never a twelfth fact (environment.md "
                        "§3, D-3): got %r" % (sorted(decision["readout"]),),
                    )
                    legal = tuple(decision["legal"])
                    has_raise = bool(S.raises_in(legal))
                    self.assertEqual(
                        decision["minimum"] is None, not has_raise,
                        "`minimum` is None exactly when no raise is legal, so one reading "
                        "of the record tells whether a size was available (environment.md "
                        "§3, config.md §5): got %r with legal %r"
                        % (decision["minimum"], legal),
                    )
                    self.assertEqual(
                        decision["maximum"] is None, decision["minimum"] is None,
                        "the two bounds are absent together: they are the ends of one "
                        "interval (config.md §5): got [%r, %r]"
                        % (decision["minimum"], decision["maximum"]),
                    )
                    if has_raise:
                        self.assertLessEqual(
                            decision["minimum"], decision["maximum"],
                            "the interval's minimum is no more than its maximum "
                            "(config.md §5): got [%r, %r]"
                            % (decision["minimum"], decision["maximum"]),
                        )
                    if decision["action"] in S.BASES:
                        self.assertIsNone(
                            decision["amount"],
                            "`amount` is None whenever the chosen descriptor is not a "
                            "raise -- a fold and a check/call included (episode.md §3): "
                            "%r carried %r" % (decision["action"], decision["amount"]),
                        )
                    else:
                        self.assertIsNotNone(
                            decision["amount"],
                            "a raise descriptor carries the raise-to the engine resolved "
                            "(episode.md §3): %r carried %r"
                            % (decision["action"], decision["amount"]),
                        )
                        self.assertTrue(
                            decision["minimum"] <= decision["amount"] <= decision["maximum"],
                            "a resolved raise-to lies inside that decision's own interval "
                            "(config.md §5): %r of [%r, %r]"
                            % (decision["amount"], decision["minimum"],
                               decision["maximum"]),
                        )

    def test_eng13_7_apply_action_takes_every_legal_size_and_refuses_a_masked_one(self):
        """ENG-13.7 apply_action accepts every descriptor legal_actions offers on a no-cap
        hand, leaves the argument handle at its own state, refuses `raise` -- a descriptor
        of the other shape -- and refuses a sized descriptor whose band is empty at that
        decision (surface.md §6, §7, stepping.md §2, actions.md §3)."""
        hand = self.shaped_hand(S.SHAPE_SEED_E, S.NO_LIMIT_SHAPE)
        before = self.readout(hand)
        legal = tuple(self.legal(hand))
        self.assertEqual(
            legal, S.SIZED_ACTIONS,
            "the premise: every descriptor of the row is legal at the first decision "
            "(config.md §6): got %r" % (legal,),
        )
        for descriptor in legal:
            with self.subTest(descriptor=descriptor):
                advanced = self.step(hand, descriptor)
                self.assertIsNotNone(
                    advanced,
                    "apply_action accepts %r, because legal_actions offers it "
                    "(surface.md §7)" % (descriptor,),
                )
                if not self.terminal(advanced):
                    self.assertEqual(
                        len(self.readout(advanced)["history"]), 1,
                        "one applied action is one history entry, a raise included "
                        "(surface.md §7, advance.md §2)",
                    )
        self.assertEqual(
            self.readout(hand), before,
            "no step touched the handle it was given: a caller keeps an earlier handle "
            "and queries it after the hand has moved on (surface.md §1 rule 6)",
        )

        exc = self.refusal(S.ep("apply_action"), hand, "raise")
        self.assert_mentions(exc, "action", "legal")
        self.assert_untouched(hand, before)

        # A masked band: walk to a decision whose raise interval has span 1, where the
        # quarter and half bands are empty (config.md §5).
        pattern = ("raise-quarter", "raise-quarter")
        masked = None
        for replayed, decision in self.replay(S.SHAPE_SEED_C, S.NO_LIMIT_SHAPE,
                                              S.band_walk(pattern), S.band_walk(pattern)):
            if decision["minimum"] is None:
                continue
            if decision["maximum"] - decision["minimum"] == 1:
                masked = (replayed, decision)
                break
        self.assertIsNotNone(
            masked,
            "the walk reaches a decision whose raise interval has span 1, where two of the "
            "four bands are empty (config.md §5)",
        )
        masked_hand, masked_decision = masked
        masked_before = self.readout(masked_hand)
        self.assertEqual(
            S.raises_in(masked_decision["legal"]), LEGAL_RAISES_BY_SPAN[1],
            "the premise: at span 1 only the minimum and all-in bands hold a legal amount "
            "(config.md §5): got %r" % (S.raises_in(masked_decision["legal"]),),
        )
        for descriptor in ("raise-quarter", "raise-half"):
            with self.subTest(masked=descriptor):
                exc = self.refusal(S.ep("apply_action"), masked_hand, descriptor)
                self.assert_mentions(exc, "action", "legal")
                self.assert_untouched(masked_hand, masked_before)
        for descriptor in LEGAL_RAISES_BY_SPAN[1]:
            with self.subTest(accepted=descriptor):
                self.assertIsNotNone(
                    self.step(masked_hand, descriptor),
                    "the two bands that do hold a legal amount are still applicable: %r"
                    % (descriptor,),
                )

    def test_eng13_8_one_seed_and_one_pair_give_one_episode_on_either_shape(self):
        """ENG-13.8 two identical play_hand calls on the no-cap row give equal records, and
        the same seed on the other shape gives a different one -- a shape is a declared
        argument and never a state the engine remembers (surface.md §10, episode.md §4,
        shapes.md §3)."""
        pattern = ("raise-quarter", "raise-quarter", "raise-half")
        first = self.shaped_episode(S.SHAPE_SEED_B, S.band_walk(pattern),
                                    S.band_walk(pattern), S.NO_LIMIT_SHAPE)
        second = self.shaped_episode(S.SHAPE_SEED_B, S.band_walk(pattern),
                                     S.band_walk(pattern), S.NO_LIMIT_SHAPE)
        self.assertEqual(
            first, second,
            "one seed, one pair of policies and one shape give one record, so a run on the "
            "second shape repeats from its own seed (surface.md §10, episode.md §4)",
        )
        self.assertEqual(
            first["seed"], S.SHAPE_SEED_B,
            "the record carries the seed the call was made with, unchanged "
            "(environment.md §3)",
        )
        self.assertGreaterEqual(
            len(first["decisions"]), 5,
            "the walk is a whole hand and takes several decisions: %r"
            % (first["decisions"],),
        )
        self.assertEqual(
            sum(S.numbers(first["payoffs"])), 0,
            "a no-cap hand's payoffs are net chip deltas summing to zero (surface.md §9, "
            "ASM-12): got %r" % (first["payoffs"],),
        )

        call_only = self.shaped_episode(S.SHAPE_SEED_B, S.always_call, S.always_call,
                                        S.NO_LIMIT_SHAPE)
        fixed = self.episode(S.SHAPE_SEED_B)
        self.assertNotEqual(
            fixed["decisions"], call_only["decisions"],
            "the same seed on the other shape is a different record: the stacks, the "
            "interval and the vocabulary differ, so no reader mistakes one shape's hand "
            "for the other's (surface.md §10, shapes.md §6)",
        )
        self.assertEqual(
            set(fixed), set(call_only),
            "both records carry the same keys, because the shape is an argument and never "
            "a key a caller reads back (surface.md §10, episode.md §3)",
        )
        self.assertEqual(
            sum(S.numbers(call_only["payoffs"])), 0,
            "and the same zero-sum rule holds on the other shape (surface.md §9, ASM-12)",
        )


if __name__ == "__main__":
    unittest.main()
