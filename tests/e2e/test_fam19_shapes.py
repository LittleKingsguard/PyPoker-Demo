"""FAM-19 — the declared game shapes: the catalogue, the identity, and the four refusals.

`docs/L1/battery.md` §3 FAM-19, `docs/L1/e2e-surface.md` §2 "Game shape" and §3.1, §5,
`docs/L1/shapes.md` §2–§5, `docs/L1/sizing.md` §6, D-29, D-13.  The project declares a
**second** game shape beside D-2's fixed-limit one, and it is reached as data: one new
entry point publishes the catalogue, eight existing rows take the shape's name as an
optional argument or key, and every record that reports a result names the shape it is
about.

What this family asserts, case by case, is the declaration and the identity:

* the catalogue declares more than one shape, **default first**, each row carrying its
  seats, blinds, starting stack, chips in play, bet structure, vocabulary, head width and
  amount normalisers — the declaration is a `fixed` row, so its instances are the
  design's own and are spelled here (`shapes.md` §2, `e2e-surface.md` §5);
* `game_config()` with no argument is the default shape's row and `game_config(name)`
  that shape's, and a name outside the catalogue is refused **by name**, at every one of
  the widened names, never defaulted (`shapes.md` §2–§3);
* a configuration, a run record, a pool, a container and a report each **carry** the
  shape, and a record whose parts name two is refused naming both (`shapes.md` §3, §6);
* a version-4 container requires `game`, a default-shape container must not carry one and
  is read as the default, and the 18 shipped version-1 containers load as the default
  shape (`sizing.md` §6, `shapes.md` §5);
* a learner built in one shape's head is refused another shape's observation, and its
  `param_count` follows the shape's vocabulary (`sizing.md` §6, ASM-40);
* the width the learner is built from is the shape's too, because a kind's declared
  `observation_size` is the **default** shape's: the uncapped shape's dense observation is
  329 wide and its token observation 82 over the same vocabulary of 96, a history of 66
  entries encodes there and 67 is refused naming the field, the capacity and the count (24
  and 25 on the default shape), `param_count` is 14,766 at `W = 36`, `D = 2` against the
  default's unchanged 10,119, and an encoder-less spec naming the uncapped shape is refused
  by name (`shapes.md` §8, ASM-42, ASM-44, `flat-numeric.md` §5);
* with **no shape named** the fixed-limit assertions of FAM-2, FAM-5, FAM-7, FAM-14 and
  FAM-16 are unchanged, because absence is the default (`shapes.md` §5, D-29).

The two shapes' names, their rows and their vocabularies are the design's own and are not
invented here: the row is `fixed` (`e2e-surface.md` §5, `battery.md` §4).  The **instances**
this family drives are the battery's: its own configuration, its own seeds, its own
membership and its own invented shape name for the refusals (`battery.md` §4, D-15).
"""

import json
import os
import sys
import unittest
import zipfile

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _surface as S  # noqa: E402


# shapes.md §2 and seats.md §2: the three declared rows, default first, as the catalogue
# states them.  The values are the design's — the row is `fixed` — and each vocabulary is
# the shape's own index order, `sizing.md` §3's measured price order for the two no-cap
# shapes.  The third row is D-33's: six seats, 600 chips in play, and a capacity of 98 that
# `shapes.md` §8 derives from its own betting.
DECLARED_ROWS = (
    {
        "name": "fixed-limit-20",
        "default": True,
        "seats": 2,
        "blinds": (1, 2),
        "starting_stack": 20,
        "chips_in_play": 40,
        "history": 24,
        "bet_structure": "fixed-limit",
        "small_bet": 2,
        "big_bet": 4,
        "raise_cap": 4,
        "actions": S.FIXED_ACTIONS,
        "head_width": 3,
        "normalisers": {"stack": 20, "pot": 40, "to_call": 20, "amount": 4, "count": 4},
    },
    {
        "name": "no-limit-100",
        "default": False,
        "seats": 2,
        "blinds": (1, 2),
        "starting_stack": 100,
        "chips_in_play": 200,
        "history": 66,
        "bet_structure": "no-limit",
        "small_bet": None,
        "big_bet": None,
        "raise_cap": None,
        "actions": S.SIZED_ACTIONS,
        "head_width": 6,
        "normalisers": {"stack": 100, "pot": 200, "to_call": 100,
                        "amount": 100, "count": 50},
    },
    {
        "name": "six-seat-no-limit-100",
        "default": False,
        "seats": 6,
        "blinds": (1, 2),
        "starting_stack": 100,
        "chips_in_play": 600,
        "history": 98,
        "bet_structure": "no-limit",
        "small_bet": None,
        "big_bet": None,
        "raise_cap": None,
        "actions": S.SIZED_ACTIONS,
        "head_width": 6,
        "normalisers": {"stack": 100, "pot": 600, "to_call": 100,
                        "amount": 100, "count": 50},
    },
)

# e2e-surface.md §3.1: the fifteen keys `game_config` declares, the same fifteen on every
# shape — the no-cap row's fixed-bet and cap facts are `None`, and its `limit` with them.
CONFIG_KEYS = (
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

# The number of containers the repository ships, and the version they were written as
# (`shapes.md` §5: 18 version-1 containers, read as the default shape).
SHIPPED_CONTAINERS = 18
SHIPPED_VERSION = 1

# The invented cell count and table seed of the hand-built no-cap table FAM-19.11 reports
# over: the table is a record in `records.md` §10's shape, written by the battery because
# the cells' *values* are no case's subject here (FAM-8, FAM-9) — only the shape the
# report reads off it (`battery.md` §2, §5, D-15).
TABLED_HANDS = 13
TABLED_SEED = 61337

# One entry of the history grammar's documented forms (`flat-numeric.md` §5, ASM-E2): a
# `calls` entry, whose action kind is neither a fold nor a bet, so the entry is the
# grammar's and nothing about the amount is under test.  The battery's own spelling of a
# value the grammar declares (`battery.md` §4).
HISTORY_ENTRY = "preflop seat 0 calls 2"


class FAM19Shapes(S.SurfaceCase):
    """The second game shape: one declaration, five carriers, four refusals."""

    # -- helpers -----------------------------------------------------------
    def declared(self):
        """The catalogue as ``[(name, row)]``, default first (§3.1, ``shapes.md`` §2)."""
        catalogue = self.shapes()
        self.assertTrue(
            catalogue,
            "engine.game_shapes() declares the shapes of the catalogue and not nothing "
            "(e2e-surface.md §3.1, shapes.md §2)",
        )
        return catalogue

    def row_value(self, row, key):
        """One declared value of a row, under the row's own key or a tolerant spelling."""
        for name, value in row.items():
            if S._family_token(name) == S._family_token(key):
                return value
        raise AssertionError(
            "a shape row declares %r (shapes.md §2); the row carries %r"
            % (key, sorted(str(name) for name in row))
        )

    def container(self, path):
        """The metadata one checkpoint container carries, read from the file it wrote.

        ``agents.save`` writes a zip with ``metadata.json`` inside it
        (``docs/L3/agents/checkpoint.md`` §2), and the shape's **format version** is what
        says whether a ``game`` field is there (`sizing.md` §6, ASM-40).  The version and
        the field are facts about the artefact an entry point wrote, so the case reads the
        artefact rather than a second spelling of it; the entry points are still the only
        thing the battery *calls* (`e2e-surface.md` §3.3, `battery.md` §2).
        """
        with zipfile.ZipFile(str(path)) as container:
            return json.loads(container.read("metadata.json").decode("utf-8"))

    def saved(self, shape=None, name="fam19.ckpt"):
        """One learner written by ``agents.save`` — on ``shape``, or on the default."""
        learner = self.learner(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH,
                               seed=S.SEED_I, game=shape)
        return self.ep("agents", "save")(learner, os.path.join(self.scratch(), name))

    def declared_width(self, shape, representation):
        """One shape's declared observation width, off ``observation_spec`` (§2, §3.2)."""
        spec = self.ep("features", "observation_spec")(self.encoder(representation, shape))
        width = 1
        for value in S.numbers(
            S.declared_field(spec, "an observation spec (e2e-surface.md §2)", "shape")
        ):
            width *= int(value)
        return width

    def declared_vocabulary(self, shape, representation):
        """One shape's declared token vocabulary, off ``observation_spec`` (§2, §3.2)."""
        spec = self.ep("features", "observation_spec")(self.encoder(representation, shape))
        return S.declared_field(spec, "an observation spec (e2e-surface.md §2)", "vocabulary")

    def history_readout(self, shape, count):
        """One shaped readout carrying exactly ``count`` documented history entries.

        The readout is the shape's own — ``engine.readout`` of a hand dealt on it — and the
        entries are the history grammar's `calls` form repeated, because the block's
        contract is over the readout it is handed and a shaped hand need not reach its
        capacity in any walk this battery drives (`flat-numeric.md` §5,
        `docs/L2/features/capacity.md` §1, §3).  Nothing else about the readout is touched,
        so the only fact under test is the history's own length.
        """
        readout = dict(self.readout(self.hand(S.SEED_I, shape)))
        readout["history"] = [HISTORY_ENTRY] * count
        return readout

    def no_cap_table(self, shape):
        """A no-cap table in ``records.md`` §10's shape, and its fitted rating.

        The cells' values are the battery's own and no case's subject: what FAM-19.11
        reads off this record is the **shape** it names, so the table exists to carry the
        identity and the report's judgement and not to rank anybody (`battery.md` §5,
        D-16).  K = 4 — the three anchor baselines and one invented member — and six
        cells, each naming the shape it was played on.
        """
        members = list(S.ANCHOR_BASELINES) + ["version-nimbus"]
        hands = TABLED_HANDS
        button = hands // 2

        def direction(wins, losses, delta, held, other):
            return {
                "wins": wins,
                "ties": hands - wins - losses,
                "losses": losses,
                "mean_chip_delta": delta,
                "seat_split": {"button": held, "big blind": other},
            }

        cells = []

        def cell(left, right, left_wins, left_delta):
            cells.append({
                "members": [left, right],
                "hands": hands,
                "directions": [
                    direction(left_wins, hands - left_wins, left_delta, button,
                              hands - button),
                    direction(hands - left_wins, left_wins, -left_delta,
                              hands - button, button),
                ],
                "params": [0, 0],
                "rules": {left: None, right: None},
                "utilities": {left: None, right: None},
                "seed": TABLED_SEED,
                "game": shape,
            })

        cell("random", "always-call", 8, 0.25)
        cell("random", "oracle", 5, -0.75)
        cell("always-call", "oracle", 6, -0.5)
        cell("version-nimbus", "random", hands, 2.0)
        cell("version-nimbus", "always-call", hands, 2.0)
        cell("version-nimbus", "oracle", hands, 2.0)
        return {
            "members": members,
            "cells": cells,
            "hands_per_cell": hands,
            "table_seed": TABLED_SEED,
            "table": "live",
            "game": shape,
            "rules": {member: None for member in members},
            "population": (),
            "utilities": {member: None for member in members},
            "utility_population": (),
        }

    # -- the catalogue (§3.1, shapes.md §2) --------------------------------
    def test_fam19_1_the_catalogue_declares_every_shape_default_first(self):
        """FAM-19.1 engine.game_shapes declares every declared row, default first, in full.

        `shapes.md` §2 makes the catalogue one ordered declaration with `fixed-limit-20`
        first and the **default**, and `seats.md` §2 adds the third row, each carrying its
        seats, blinds, starting stack, chips in play, history capacity, bet structure,
        action vocabulary, head width and amount normalisers; `e2e-surface.md` §3.1 makes it
        the tenth `engine` entry point.  A catalogue that declared one shape, in another
        order, or with a fact missing is caught here, row by row — and a third row is
        asserted exactly as the second was, never in place of it (`e2e-surface.md` §4, §5,
        `shapes.md` §2, §8, D-29, D-33).
        """
        catalogue = self.declared()
        self.assertGreaterEqual(
            len(catalogue),
            len(DECLARED_ROWS),
            "the catalogue declares the default shape and the two shapes beside it — the "
            "second is the whole of D-29 and the third the whole of D-33 (shapes.md §2, "
            "seats.md §2): %r" % ([name for name, _row in catalogue],),
        )
        names = [name for name, _row in catalogue]
        self.assertEqual(
            names[:3],
            [row["name"] for row in DECLARED_ROWS],
            "the declared shapes are fixed-limit-20, no-limit-100 and "
            "six-seat-no-limit-100, in that order — the default first (shapes.md §2, "
            "seats.md §2, D-29, D-33): %r" % (names,),
        )
        self.assertEqual(
            names[0],
            "fixed-limit-20",
            "the catalogue's first row is the default shape (shapes.md §2): %r" % (names,),
        )
        rows = dict(catalogue)
        for declared in DECLARED_ROWS:
            row = rows[declared["name"]]
            present = {S._family_token(name) for name in row}
            missing = [key for key in declared if S._family_token(key) not in present]
            self.assertFalse(
                missing,
                "the row %r carries every fact the catalogue declares of it "
                "(e2e-surface.md §3.1, shapes.md §2); it is missing %r and carries %r"
                % (declared["name"], missing, sorted(str(key) for key in row)),
            )
            for key, wanted in declared.items():
                if key == "normalisers":
                    normalisers = S.normalisers_of(row)
                    for name, value in wanted.items():
                        self.assertEqual(
                            int(S.declared_field(
                                normalisers,
                                "a shape row's normalisers (shapes.md §2)",
                                name,
                            )),
                            value,
                            "%r's `%s` normaliser is %r (shapes.md §2, sizing.md §5): %r"
                            % (declared["name"], name, value, normalisers),
                        )
                    continue
                if key == "actions":
                    self.assertEqual(
                        tuple(S.vocabulary_of(row)),
                        wanted,
                        "%r declares its vocabulary in its own index order "
                        "(shapes.md §2, sizing.md §3): %r"
                        % (declared["name"], S.vocabulary_of(row)),
                    )
                    continue
                if key == "default":
                    self.assertIs(
                        bool(self.row_value(row, "default")),
                        wanted,
                        "%r %sthe default shape (shapes.md §2)"
                        % (declared["name"], "" if wanted else "is not "),
                    )
                    continue
                got = self.row_value(row, key)
                if isinstance(wanted, tuple):
                    self.assertEqual(
                        tuple(got), wanted,
                        "%r's %s is %r (shapes.md §2): %r"
                        % (declared["name"], key, wanted, got),
                    )
                else:
                    self.assertEqual(
                        got, wanted,
                        "%r's %s is %r (shapes.md §2): %r"
                        % (declared["name"], key, wanted, got),
                    )

    # -- game_config (§3.1, shapes.md §2–§3) ------------------------------
    def test_fam19_2_game_config_is_the_named_shape_s_row(self):
        """FAM-19.2 game_config() is the default row and game_config(name) every shape's.

        With no argument it returns the mapping it always returned — the default shape's
        row, byte for byte (ASM-6, `shapes.md` §2) — and named it returns the same fifteen
        keys with **that** shape's values: a 100-chip stack on both uncapped rows, no fixed
        bet, no cap and so no `limit`, the same blinds and the same streets, two seats on
        one and six on the other, whose `starting_stacks` is the six-tuple its seat count
        makes (`e2e-surface.md` §3.1, `shapes.md` §2, `seats.md` §2, D-29, D-33).
        """
        default = self.game_config()
        named_default = self.game_config(self.shape_names()[0])
        self.assertEqual(
            S.canon(default),
            S.canon(named_default),
            "game_config() with no argument is the default shape's row, and naming that "
            "row by name is the same mapping (shapes.md §2, §3)",
        )
        self.assertEqual(
            S.starting_stack(default), 20,
            "the default shape's starting stack is 20, unchanged (ASM-6, shapes.md §5)",
        )
        self.assertEqual(
            self.row_value(default, "raise_cap"), 4,
            "the fixed game's raise cap of four is unchanged, and is the default's own "
            "fact now rather than the game's (ASM-6, shapes.md §5)",
        )
        for shape in self.other_shapes():
            named = self.game_config(shape)
            self.assertEqual(
                {S._family_token(key) for key in default},
                {S._family_token(key) for key in named},
                "every declared shape's config carries the same fifteen keys with the same "
                "value shapes (e2e-surface.md §3.1, shapes.md §2): %r against %r on %r"
                % (sorted(str(key) for key in default),
                   sorted(str(key) for key in named), shape),
            )
            present = {S._family_token(name) for name in named}
            missing = [key for key in CONFIG_KEYS if S._family_token(key) not in present]
            self.assertFalse(
                missing,
                "%r's config carries the fifteen declared keys; it is missing %r and "
                "carries %r" % (shape, missing, sorted(str(key) for key in named)),
            )
            self.assertEqual(
                S.starting_stack(named), 100,
                "%r's starting stack is 100 (shapes.md §2, seats.md §2): %r"
                % (shape, named),
            )
            seats = self.seats_of(shape)
            self.assertEqual(
                seats, S.SHAPE_SEATS[shape],
                "%r declares the seat count the catalogue states (shapes.md §2, seats.md "
                "§2): %r" % (shape, seats),
            )
            stacks = S.numbers(self.row_value(named, "starting_stacks"))
            self.assertEqual(
                len(stacks), seats,
                "`starting_stacks` is one stack per seat — two on the two-seat rows and six "
                "on the six-seat one (e2e-surface.md §3.1, seats.md §2): %r" % (stacks,),
            )
            self.assertTrue(
                all(int(value) == 100 for value in stacks),
                "%r's stacks are 100 chips a seat (shapes.md §2, seats.md §2): %r"
                % (shape, stacks),
            )
            for key in ("seats", "blinds", "small_blind", "big_blind", "blind_levels"):
                if key == "seats" and seats != self.seats_of():
                    continue
                self.assertEqual(
                    S.canon(self.row_value(default, key)),
                    S.canon(self.row_value(named, key)),
                    "the shapes with one seat count share their table: %r differs between "
                    "the default shape and %r (shapes.md §2, seats.md §2)"
                    % (key, shape),
                )
            for key in ("small_bet", "big_bet", "raise_cap", "limit"):
                value = self.row_value(named, key)
                self.assertIsNone(
                    value,
                    "a shape with no fixed bet and no cap declares %r as None — a seat "
                    "count adds no betting fact (e2e-surface.md §3.1, shapes.md §2, "
                    "seats.md §2): %r on %r" % (key, value, shape),
                )

    def test_fam19_3_a_name_outside_the_catalogue_is_refused_by_name(self):
        """FAM-19.3 engine.game_config refuses an uncatalogued name, naming it and theirs.

        `shapes.md` §2–§3: a name the catalogue does not carry is refused **naming it and
        the declared names** — never defaulted, because a default on a name is the silent
        substitution `e2e-surface.md` §2 forbids (D-13).  The name is the battery's own
        and appears in no design document (`battery.md` §4).
        """
        offending = S.UNKNOWN_SHAPE
        self.assertNotIn(
            offending,
            self.shape_names(),
            "the name this case invents is outside the catalogue it names",
        )
        text = S.refusal_text(lambda: self.game_config(offending))
        self.assertIsNotNone(
            text,
            "engine.game_config(%r) is a contract violation and must be refused, not "
            "answered with a shape's row (shapes.md §2, D-13)" % (offending,),
        )
        self.assertIn(
            S._family_token(offending),
            S._family_token(text),
            "the refusal names the shape name it refused (shapes.md §2): %r" % (text,),
        )
        for declared in self.shape_names():
            self.assertIn(
                S._family_token(declared),
                S._family_token(text),
                "the refusal names the declared names beside the one it refused, so a "
                "caller can see what it should have passed (shapes.md §2): %r" % (text,),
            )

    def test_fam19_4_every_widened_name_refuses_the_same_uncatalogued_shape(self):
        """FAM-19.4 the eight widened names refuse an uncatalogued shape by name too.

        D-29 widens `engine.game_config`, `features.action_space`, `features.build_encoder`,
        `agents.build_learner`'s spec, `evaluation.build_pool`'s declaration and
        `training.run`'s configuration — every one of them takes the shape's name and
        every one of them refuses a name the catalogue does not carry, naming it
        (`shapes.md` §4, `e2e-surface.md` §2 "Game shape").  One refusal per entry point,
        so a name that reaches a hand through any of them is one finding per name.
        """
        offending = S.UNKNOWN_SHAPE
        spec = self.learner_spec(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH, seed=S.SEED_I)
        spec["game"] = offending
        configuration = self.shaped_rung(shape=offending, seeds=(S.SEED_A,))
        calls = (
            ("features.action_space", lambda: self.action_space(offending)),
            ("features.build_encoder",
             lambda: self.ep("features", "build_encoder")(S.FLAT, shape=offending)),
            ("agents.build_learner",
             lambda: self.ep("agents", "build_learner")(spec)),
            ("evaluation.build_pool",
             lambda: self.pool({"members": [], "m": S.LEAGUE_BOUND, "frozen": True,
                                "game": offending})),
            ("training.run",
             lambda: self.ep("training", "run")(configuration, [S.SEED_A],
                                                S.BUDGET_TINY, "cpu")),
        )
        for name, call in calls:
            text = S.refusal_text(call)
            self.assertIsNotNone(
                text,
                "%s takes the shape's name and refuses a name the catalogue does not "
                "carry, rather than defaulting it (shapes.md §2–§4, D-13): %r"
                % (name, offending),
            )
            self.assertIn(
                S._family_token(offending),
                S._family_token(text),
                "%s's refusal names the shape name it refused (shapes.md §2): %r"
                % (name, text),
            )

    # -- the five carriers (§3, §6) ---------------------------------------
    def test_fam19_5_a_configuration_and_a_run_record_carry_the_shape(self):
        """FAM-19.5 the configuration's `game` is the run record's, on every declared shape.

        `shapes.md` §3 makes the configuration the first carrier: it declares `game`, the
        run repeats it under `game`, the run's pool block repeats it, and the record's
        header family is built from that shape's `game_config` and vocabulary — so a run
        says which game its curves are about (`records.md` §12, `e2e-surface.md` §3.5,
        D-29).  The carrier is asserted for **each** shape the catalogue declares beside
        the default, the six-seat one included, whose pool holds enough members to seat its
        hands (`seats.md` §4, §6, D-33); a configuration that names none is trained on the
        default shape, and its record says **that** (`shapes.md` §3: absence is the
        default).
        """
        samples = S.BUDGET_MICRO
        for shape in self.other_shapes():
            configuration = self.seated_rung(shape=shape, seeds=(S.SEED_A,), samples=samples)
            record = self.ep("training", "run")(
                configuration, [S.SEED_A], samples, "cpu"
            )
            self.assertEqual(
                str(S.declared_field(record, "a run record (records.md §12)", "game")),
                shape,
                "a run record names the shape it played (records.md §12, shapes.md §3): %r "
                "on %r" % (record.get("game"), shape),
            )
            pool_block = S.declared_field(record, "a run record (records.md §12)", "pool")
            self.assertEqual(
                str(S.declared_field(
                    pool_block, "a run record's pool block (records.md §12)", "game")),
                shape,
                "the record's pool block names the same shape as the record (records.md §8, "
                "§12, shapes.md §3): %r on %r" % (pool_block, shape),
            )
            header = S.declared_field(record, "a run record (records.md §12)", "header")
            self.assertEqual(
                S.starting_stack(S.declared_field(
                    header, "a run record's header (§1)", "game")),
                100,
                "the header's game configuration is the run's shape's, not the default's "
                "(protocol.md §1, shapes.md §3): %r on %r"
                % (header.get("game"), shape),
            )
            self.assertEqual(
                S.action_vocabulary(S.declared_field(
                    header, "a run record's header (§1)", "action space")),
                set(range(len(S.SIZED_ACTIONS))),
                "the header's vocabulary is the named shape's six descriptors (protocol.md "
                "§1, shapes.md §3): %r on %r" % (header.get("action space"), shape),
            )
        # A configuration that names no shape runs on the default one, and says so.
        plain = self.ep("training", "run")("R1", [S.SEED_A], S.BUDGET_TINY, "cpu")
        self.assertEqual(
            str(S.declared_field(plain, "a run record (records.md §12)", "game")),
            self.shape_names()[0],
            "a run whose configuration names no shape records the default shape "
            "(shapes.md §3): %r" % (plain.get("game"),),
        )

    def test_fam19_6_a_pool_carries_the_shape_and_refuses_a_member_of_another(self):
        """FAM-19.6 a pool is one shape's, and a member of another is refused naming both.

        `records.md` §8 makes a pool record's `game` **required** — the shape every member
        of it plays — and `shapes.md` §3 makes a declaration naming one shape and a member
        of another a refusal **naming both**, because a frozen pool is a pool on one shape
        and its membership cannot mix two.  The case holds for every shape declared beside
        the default: the versions a six-seat pool carries are that shape's containers, and
        a default-shape version offered to it is refused `(D-29, D-33, D-16)`.
        """
        for shape in self.other_shapes():
            pool = self.shaped_pool(shape, tags=("kestrel",))
            row = self.members(pool)
            self.assertEqual(
                str(S.declared_field(row, "a pool record (records.md §8)", "game")),
                shape,
                "a pool record names the one shape its members play (records.md §8, "
                "shapes.md §3): %r on %r" % (row.get("game"), shape),
            )
            version_members = [member for member in row["members"]
                               if isinstance(member, dict) and not member.get("baseline")]
            self.assertTrue(
                version_members,
                "the pool holds the version this case declared: %r"
                % ([member.get("id") for member in row["members"]],),
            )
            for member in version_members:
                self.assertEqual(
                    str(S.declared_field(
                        member, "a version member (records.md §7)", "game")),
                    shape,
                    "a version member of %r's pool records that shape as **required** "
                    "(records.md §7, shapes.md §3): %r" % (shape, member),
                )
            # A default-shape member in this shape's pool: refused, naming the member and both.
            stray = self.version("bramble", game=None)
            text = S.refusal_text(lambda: self.pool({
                "members": [stray],
                "m": S.LEAGUE_BOUND,
                "frozen": True,
                "game": shape,
            }))
            self.assertIsNotNone(
                text,
                "a pool declaration naming %r and a member of another shape is refused, not "
                "windowed (shapes.md §3, records.md §8, D-29)" % (shape,),
            )
            self.assertIn(
                S._family_token(str(stray["id"])),
                S._family_token(text),
                "the refusal names the member it refused (shapes.md §3): %r" % (text,),
            )
            for named in (shape, self.shape_names()[0]):
                self.assertIn(
                    S._family_token(named),
                    S._family_token(text),
                    "the refusal names **both** shapes — the pool's and the member's "
                    "(shapes.md §3): %r" % (text,),
                )

    def test_fam19_7_the_container_answers_with_a_format_version(self):
        """FAM-19.7 a version-4 container carries `game` and a default one carries none.

        `sizing.md` §6 answers the shape with a format version, not a migration: a learner
        of the default shape writes version **3** with no field — so a fixed-limit save is
        today's bytes — and a learner of **any** other declared shape writes version **4**
        and a `game` field, the two-seat uncapped row and D-33's six-seat one alike
        (`shapes.md` §5, `seats.md` §6, ASM-40).  A `load` whose spec names a shape its
        container contradicts is refused naming both, as a contradictory rule already is.
        """
        default_path = self.saved()
        default_meta = self.container(default_path)
        self.assertEqual(
            int(default_meta["format_version"]), 3,
            "a container of the default shape keeps writing version 3 (sizing.md §6, "
            "ASM-40): %r" % (default_meta.get("format_version"),),
        )
        self.assertNotIn(
            "game", default_meta,
            "a container of the default shape carries **no** `game` field, so a "
            "fixed-limit save is byte-identical to today's (sizing.md §6): %r"
            % (sorted(default_meta),),
        )
        default = self.shape_names()[0]
        for shape in self.other_shapes():
            named_path = self.saved(shape=shape, name="fam19-%s.ckpt" % (shape,))
            named_meta = self.container(named_path)
            self.assertEqual(
                int(named_meta["format_version"]), 4,
                "a container of %r writes version 4 (sizing.md §6, ASM-40): %r"
                % (shape, named_meta.get("format_version")),
            )
            self.assertEqual(
                str(named_meta.get("game")), shape,
                "a version-4 container requires the `game` field, naming its shape "
                "(sizing.md §6): %r on %r" % (named_meta.get("game"), shape),
            )
            # The identity is load-bearing: a spec naming the other shape is refused by name.
            spec = self.learner_spec(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH,
                                     seed=S.SEED_I, game=default)
            text = S.refusal_text(lambda: self.ep("agents", "load")(spec, named_path))
            self.assertIsNotNone(
                text,
                "agents.load refuses a spec whose shape the container contradicts, naming "
                "both (e2e-surface.md §3.3, shapes.md §3, sizing.md §6): %r against %r"
                % (default, shape),
            )
            for named in (default, shape):
                self.assertIn(
                    S._family_token(named),
                    S._family_token(text),
                    "the refusal names both shapes (shapes.md §3): %r" % (text,),
                )
            # And the default's container is read as the default: a spec naming this shape
            # is refused.
            spec_named = self.learner_spec(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH,
                                           seed=S.SEED_I, game=shape)
            text = S.refusal_text(lambda: self.ep("agents", "load")(spec_named, default_path))
            self.assertIsNotNone(
                text,
                "a container of the default shape is read as the default shape, so a spec "
                "naming %r is refused (shapes.md §3, §5)" % (shape,),
            )
            self.assertIn(
                S._family_token(shape),
                S._family_token(text),
                "the refusal names the shape the spec asked for (shapes.md §3): %r"
                % (text,),
            )

    def test_fam19_8_the_eighteen_shipped_containers_load_as_the_default_shape(self):
        """FAM-19.8 the 18 shipped version-1 containers are read as the default shape.

        `shapes.md` §5 leaves the shipped set exactly as it is: 18 version-1 containers
        written before the field existed, read as the default shape — which is what the
        absence of `game` means (§3) — and never regenerated.  Every one of them loads
        through `evaluation.policy_from` and decides in the default vocabulary, and a
        `load` spec naming the second shape is refused naming both (`sizing.md` §6,
        D-8, ASM-40).
        """
        index = self.ep("training", "checkpoints")()
        entries = S.index_entries(index)
        self.assertEqual(
            len(entries), SHIPPED_CONTAINERS,
            "the shipped set is %d containers — five retained snapshots and one final per "
            "seed of the one shipped run (protocol.md §5, shapes.md §5): %d entries"
            % (SHIPPED_CONTAINERS, len(entries)),
        )
        default = self.shape_names()[0]
        for entry in entries:
            path = entry.get("path")
            self.assertTrue(path, "an index entry names the artefact: %r" % (entry,))
            meta = self.container(path)
            self.assertEqual(
                int(meta["format_version"]), SHIPPED_VERSION,
                "the shipped containers are version 1 and are not regenerated "
                "(shapes.md §5, sizing.md §6): %r records %r"
                % (entry.get("id"), meta.get("format_version")),
            )
            self.assertNotIn(
                "game", meta,
                "a shipped version-1 container carries no `game` and is read as the "
                "default shape (shapes.md §3, §5): %r" % (entry.get("id"),),
            )
            policy = self.ep("evaluation", "policy_from")(path)
            self.assertTrue(
                callable(policy),
                "every shipped container loads through policy_from (records.md §7, "
                "e2e-surface.md §3.4): %r" % (entry.get("id"),),
            )
        representative = entries[0]["path"]
        # The spec is built from the container's own recorded facts — backend, kind,
        # settings and seed — so the only thing it contradicts is the **shape**, which is
        # the fact this case is about (`records.md` §3, `sizing.md` §6).
        settings = self.container(representative)["settings"]
        spec = self.learner_spec(
            width=int(settings["width"]),
            depth=int(settings["depth"]),
            seed=int(self.container(representative)["seed"]),
            backend=str(self.container(representative)["backend"]),
            kind=str(self.container(representative)["kind"]),
            sparsity=float(settings.get("sparsity", 0.0)),
            residual=bool(settings.get("residual", False)),
            game=self.second_shape(),
        )
        text = S.refusal_text(lambda: self.ep("agents", "load")(spec, representative))
        self.assertIsNotNone(
            text,
            "a shipped version-1 container is the **default** shape's, so a spec naming "
            "the no-cap shape is refused rather than read (shapes.md §3, §5, D-29)",
        )
        self.assertIn(
            S._family_token(default),
            S._family_token(text),
            "the refusal names the shape the container is read as — the default "
            "(shapes.md §3): %r" % (text,),
        )

    # -- the head (§6) ----------------------------------------------------
    def test_fam19_9_a_learner_refuses_another_shape_s_decision(self):
        """FAM-19.9 a learner built in one shape's head refuses another shape's decision.

        The head is the shape's — three wide on the default shape and six on each uncapped
        one — and an index decodes to a descriptor `engine.apply_action` accepts only in
        the vocabulary that declared it, so a mask carrying a sixth index into a
        three-head learner is refused **naming the shape it decides in** rather than read
        as one of its own indices (`sizing.md` §6, `shapes.md` §3, D-29).

        D-33's widening is the second half of the case, and it is asserted for every shape
        declared beside the default.  A learner on a shape takes its input width from
        **that shape's** encoder (`shapes.md` §8, ASM-44), so the observation of the shaped
        readout is the shaped encoder's 329 values on `no-limit-100` and 433 on the
        six-seat row, and not the default encoder's 203: a three-head learner refuses it by
        name of both widths, and the six-head learner built on the shape answers the same
        decision with one of its own legal indices.

        An **encoder** is the shape's too, and never only the head: the default shape's
        encoder is 203 values over two seats and over the seat indices `0..1`, so on
        `no-limit-100` its 203-value observation still carries the named shape's mask and
        the default-head learner refuses **that mask**, while a six-seat readout is not the
        default encoder's to encode at all — its `seat` and `stacks` facts are six-wide, and
        it refuses the readout by name rather than truncate it (`seats.md` §3, ASM-44,
        `flat-numeric.md` §5).  Both sides of the same fact are asserted here, so the
        six-seat row loses no assertion the two-seat one makes.
        """
        learner = self.learner(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH, seed=S.SEED_I)
        default = self.shape_names()[0]
        default_encoder_width = int(S.numbers(
            S.declared_field(
                self.ep("features", "observation_spec")(self.encoder()),
                "an observation spec (e2e-surface.md §2)", "shape",
            )
        )[0])
        for shape in self.other_shapes():
            seats = self.seats_of(shape)
            readout = self.readout(self.hand(S.SEED_I, shape))
            mask = list(self.ep("features", "legal_indices")(readout["legal"]))
            self.assertIn(
                5, mask,
                "%r's first decision offers its sixth index, which is what makes the "
                "refusal observable (sizing.md §2–§3): %r" % (shape, mask),
            )
            # The shape's own observation: its encoder's width, not the default's 203.
            shaped_encoder = self.encoder(shape=shape)
            shaped = self.ep("features", "encode")(shaped_encoder, readout)
            shaped_width = int(S.numbers(
                S.declared_field(
                    self.ep("features", "observation_spec")(shaped_encoder),
                    "an observation spec (e2e-surface.md §2)", "shape",
                )
            )[0])
            self.assertEqual(
                shaped_width, S.SHAPE_LAYOUTS[shape]["dense"],
                "%r's shaped observation is its own declared width (shapes.md §8): declared "
                "%d" % (shape, shaped_width),
            )
            self.assertEqual(
                len(shaped), shaped_width,
                "the shaped encoder returns one observation of its declared width "
                "(e2e-surface.md §2, shapes.md §8): %d values, declared %d on %r"
                % (len(shaped), shaped_width, shape),
            )
            text = S.refusal_text(lambda: self.ep("agents", "act")(learner, shaped, mask))
            self.assertIsNotNone(
                text,
                "a learner built in the default shape's head refuses %r's observation, "
                "because the input width is the shape's (shapes.md §8, ASM-44): %r"
                % (shape, shaped),
            )
            for width_seen in (shaped_width, default_encoder_width):
                self.assertIn(
                    str(width_seen),
                    text,
                    "the refusal names both widths — the observation's and the learner's "
                    "(shapes.md §8, ASM-44): %r on %r" % (text, shape),
                )
            six_learner = self.learner(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH,
                                       seed=S.SEED_I, game=shape)
            result = self.ep("agents", "act")(six_learner, shaped, mask)
            self.assertIn(
                self.action_index(result), mask,
                "a learner built in %r's head answers that shape's decision with one of its "
                "legal indices (e2e-surface.md §3.3, sizing.md §6): %r" % (shape, result),
            )
            if seats <= 2:
                # The default encoder still encodes two seats' readout, and the six-index
                # mask of that readout is what the default-head learner refuses.
                observation = self.ep("features", "encode")(self.encoder(), readout)
                self.assertEqual(
                    len(observation), default_encoder_width,
                    "the default encoder's observation is the default shape's 203 values "
                    "(shapes.md §5, §8): %d" % (len(observation),),
                )
                text = S.refusal_text(
                    lambda: self.ep("agents", "act")(learner, observation, mask))
                self.assertIsNotNone(
                    text,
                    "a three-head learner refuses %r's six-index mask, naming the shape it "
                    "decides in (sizing.md §6, shapes.md §3): %r" % (shape, mask),
                )
                self.assertIn(
                    S._family_token(default), S._family_token(text),
                    "the refusal names the shape whose head refused the index (shapes.md §3, "
                    "sizing.md §6): %r" % (text,),
                )
            else:
                # A six-seat readout is not the default encoder's to encode: its seat index
                # and its six stacks are the shape's, and the block refuses rather than
                # truncate (`seats.md` §3, ASM-44).
                text = S.refusal_text(
                    lambda: self.ep("features", "encode")(self.encoder(), readout))
                self.assertIsNotNone(
                    text,
                    "the default shape's encoder — 203 values over two seats — refuses a "
                    "six-seat readout by name rather than truncating it (shapes.md §8, "
                    "seats.md §3, ASM-44): %r" % (readout,),
                )

    def test_fam19_10_param_count_follows_the_shape_s_vocabulary(self):
        """FAM-19.10 param_count's output term is the shape's: `A·W + A`.

        `sizing.md` §6 makes the output layer `W → A` with `A` the shape's descriptor
        count, so two learners of **one** architecture under one rule and one utility
        differ by `Δsize·W` from the input block and `ΔA·W + ΔA` from the head — three
        widths and three more at either uncapped shape — and the default shape keeps
        today's `3W + 3` (ASM-40, ASM-10).

        D-33 makes both terms the shape's: a kind's declared `observation_size` is the
        default shape's 203, while a learner on another shape is sized from that shape's
        encoder — 329 on the two-seat uncapped row and 433 on the six-seat one
        (`shapes.md` §8, ASM-44).  So the difference is pinned term by term for **each**
        shape declared beside the default, each width **read** off the declared surface
        rather than spelled, and the head's own `A·W + A` stays the second term, with the
        two declared head widths asserted beside it.  The design's absolute counts at
        `W = 36`, `D = 2` are FAM-19.15's (`shapes.md` §8).
        """
        width = S.SHAPE_WIDTH
        first = self.learner(width=width, depth=S.SHAPE_DEPTH, seed=S.SEED_J)
        first_count = int(self.ep("agents", "param_count")(first))
        delta_actions = len(S.SIZED_ACTIONS) - len(S.FIXED_ACTIONS)
        default_width = int(S.numbers(
            S.declared_field(
                self.ep("features", "observation_spec")(self.encoder()),
                "an observation spec (e2e-surface.md §2)", "shape",
            )
        )[0])
        for shape in self.other_shapes():
            second = self.learner(width=width, depth=S.SHAPE_DEPTH, seed=S.SEED_J,
                                  game=shape)
            second_count = int(self.ep("agents", "param_count")(second))
            named_width = int(S.numbers(
                S.declared_field(
                    self.ep("features", "observation_spec")(self.encoder(shape=shape)),
                    "an observation spec (e2e-surface.md §2)", "shape",
                )
            )[0])
            delta_size = named_width - default_width
            self.assertGreater(
                delta_size,
                0,
                "%r's history block is wider than the default's, so its observation is wider "
                "(shapes.md §8): %r against %r" % (shape, named_width, default_width),
            )
            self.assertEqual(
                second_count - first_count,
                delta_size * width + delta_actions * width + delta_actions,
                "one architecture, two shapes: the input term is `Δsize·W` and the head's is "
                "`ΔA·W + ΔA`, so six descriptors and %d more input slots on %r cost %d×%d + "
                "%d×%d + %d more parameters (shapes.md §8, sizing.md §6, ASM-40, ASM-44): "
                "%d against %d"
                % (delta_size, shape, delta_size, width, delta_actions, width,
                   delta_actions, first_count, second_count),
            )
        rows = {name: row for name, row in self.declared()}
        self.assertEqual(
            int(self.row_value(rows[self.shape_names()[0]], "head_width")),
            len(S.FIXED_ACTIONS),
            "the default shape's declared head width is its vocabulary's size "
            "(shapes.md §2, sizing.md §6)",
        )
        for shape in self.other_shapes():
            self.assertEqual(
                int(self.row_value(rows[shape], "head_width")),
                len(S.SIZED_ACTIONS),
                "%r's declared head width is its vocabulary's size — a seat count adds no "
                "descriptor (shapes.md §2, sizing.md §6, seats.md §2): %r"
                % (shape, self.row_value(rows[shape], "head_width")),
            )

    def test_fam19_11_a_report_states_the_shape_and_refuses_a_record_naming_two(self):
        """FAM-19.11 the report's header carries the shape, and two shapes are refused.

        `records.md` §13 and `shapes.md` §3 make the report's `header` family state the
        shape the run, the pool family and the matrix agree on, and `evaluation.report`
        refuse a record whose three do not name one shape — naming **all three** and the
        shape each names, so a reader is told which record to re-derive (`protocol.md` §1,
        `shapes.md` §6, D-29).

        The case is asserted of the catalogue's **second** row, the two-seat uncapped shape,
        because a report is a report of a table and D-33's six-seat row is a placement: a
        matrix, and therefore a report, cannot exist on it, and `evaluation.report`'s
        refusal of that row — naming the shape and its seat count — is FAM-21.9's subject
        (`docs/L1/seats.md` §5, D-22, D-33).
        """
        shape = self.second_shape()
        configuration = self.shaped_rung(shape=shape, seeds=(S.SEED_A,))
        run = self.ep("training", "run")(configuration, [S.SEED_A], S.BUDGET_TINY, "cpu")
        matrix = self.no_cap_table(shape)
        rating = self.ep("evaluation", "rating")(matrix)
        record = self.evidence_record(
            run, matrix=matrix, rating=rating, seeds=(S.SEED_A,),
            budget=S.BUDGET_TINY, shape=shape,
            pool_row=self.pool_row(shape=shape),
        )
        report = self.report_of(configuration["name"], record, matrix, rating)
        header = S.declared_field(report, "a report (protocol.md §1, §13)", "header")
        shape_facts = S.find_values(header, "shape")
        self.assertTrue(
            shape_facts,
            "the report's header family states the one shape the run, the pool and the "
            "matrix agree on (records.md §13, shapes.md §3): %r" % (sorted(header),),
        )
        self.assertIn(
            S._family_token(shape),
            S._family_token(shape_facts),
            "the report states the shape it reports on — the named one, not the default "
            "(records.md §13, shapes.md §3): %r" % (shape_facts,),
        )
        # The same report judged against the default shape: one shape's or none.
        stray = dict(record)
        stray["game"] = self.shape_names()[0]
        text = S.refusal_text(
            lambda: self.report_of(configuration["name"], stray, matrix, rating)
        )
        self.assertIsNotNone(
            text,
            "a run, a pool and a matrix that do not name one shape are refused, not "
            "reported (e2e-surface.md §3.4, shapes.md §6)",
        )
        for named in (self.shape_names()[0], shape):
            self.assertIn(
                S._family_token(named),
                S._family_token(text),
                "the refusal names the shapes its parts named (shapes.md §3, §6): %r"
                % (text,),
            )

    # -- and the default path is unchanged --------------------------------
    def test_fam19_12_with_no_shape_named_the_fixed_game_is_unchanged(self):
        """FAM-19.12 naming no shape reproduces today's game, vocabulary and encoding.

        `shapes.md` §5 is the constraint the whole declaration is written under, and this
        case asserts it at the entry points: `game_config()`, `features.action_space()`,
        `features.build_encoder`, `agents.build_learner`, `engine.new_hand`,
        `engine.play_hand` and `harness`'s own driver all reproduce the default shape's
        value when no shape is named — so FM-2, FAM-5, FAM-7, FAM-14 and FAM-16's
        fixed-limit assertions stand exactly where they stood (`shapes.md` §5, D-29).
        """
        default = self.shape_names()[0]
        self.assertEqual(
            S.canon(self.game_config()),
            S.canon(self.game_config(default)),
            "game_config() with no argument is the default shape's row (shapes.md §2, §5)",
        )
        self.assertEqual(
            S.canon(self.action_space()),
            S.canon(self.action_space(default)),
            "features.action_space() with no argument is the default shape's vocabulary "
            "(e2e-surface.md §3.2, shapes.md §5)",
        )
        self.assertEqual(
            S.action_vocabulary(self.action_space()),
            {0, 1, 2},
            "the default vocabulary is today's three indices (e2e-surface.md §2): %r"
            % (self.action_space(),),
        )
        for representation in (S.FLAT, S.TOKENS):
            self.assertEqual(
                S.canon(self.ep("features", "observation_spec")(self.encoder(representation))),
                S.canon(self.ep("features", "observation_spec")(
                    self.encoder(representation, default))),
                "%r's encoder is the same object on the default shape however it is "
                "built, so every shipped checkpoint's encoding is unchanged "
                "(shapes.md §5, sizing.md §5)" % (representation,),
            )
        self.assertEqual(
            int(self.ep("agents", "param_count")(self.learner(width=61, depth=3))),
            int(self.ep("agents", "param_count")(
                self.learner(width=61, depth=3, game=default))),
            "a learner built with no shape is the default shape's learner, so today's "
            "parameter count holds (sizing.md §6, shapes.md §5)",
        )
        self.assertEqual(
            S.canon(self.readout(self.hand(S.SEED_C))),
            S.canon(self.readout(self.hand(S.SEED_C, default))),
            "engine.new_hand(seed) deals the default shape's hand (shapes.md §3)",
        )
        self.assertEqual(
            S.canon(self.play(S.SEED_C)),
            S.canon(self.play(S.SEED_C, shape=default)),
            "engine.play_hand with no shape is the default shape's episode (shapes.md §5)",
        )

    # -- the widened history block (shapes.md §8, D-33) --------------------
    def test_fam19_13_each_shape_declares_its_own_widened_layout(self):
        """FAM-19.13 203/40/96 and 329/82/96 and 433/122/102, each row its own.

        `shapes.md` §8 makes the history block's capacity the shape's own data — 24 slots on
        `fixed-limit-20`, 66 on `no-limit-100` and 98 on `six-seat-no-limit-100` — so each
        layout follows it: the dense observation is `131 + 3 × capacity` and the token
        observation `16 + capacity`, 203 and 40 on the default shape, **329** and **82** on
        the two-seat uncapped one, and **433** and **122** on the six-seat one, over a
        vocabulary of 96 on the two-seat rows and **102** on the six-seat row, whose six
        seat ids sit above every id the others use (`flat-numeric.md` §5,
        `card-tokens.md` §2, §6, `seats.md` §3, ASM-42, ASM-44).  What
        `features.observation_spec` declares and what `features.encode` returns are two
        statements of one layout, so each is held to the other here, on **every** declared
        shape and both encodings (`e2e-surface.md` §2, §3.2).
        """
        shapes = self.shape_names()
        self.assertEqual(
            list(shapes[:3]),
            [S.SHAPE_DEFAULT, S.SHAPE_SECOND, S.SHAPE_THIRD],
            "the catalogue declares the default shape and two beside it, in that order "
            "(shapes.md §2, seats.md §2, D-29, D-33): %r" % (shapes,),
        )
        for shape in shapes[:3]:
            layout = S.SHAPE_LAYOUTS[shape]
            readout = self.readout(self.hand(S.SEED_B, shape))
            for representation, key in ((S.FLAT, "dense"), (S.TOKENS, "tokens")):
                width = self.declared_width(shape, representation)
                self.assertEqual(
                    width, layout[key],
                    "%r's %r observation is %d wide — the shape's own capacity of %d behind "
                    "it (shapes.md §2, §8, D-33): declared %d"
                    % (shape, representation, layout[key], layout["history"], width),
                )
                observation = self.ep("features", "encode")(
                    self.encoder(representation, shape), readout)
                self.assertEqual(
                    len(observation), width,
                    "%r's %r encoder returns one observation of its declared width "
                    "(e2e-surface.md §2): %d values, declared %d"
                    % (shape, representation, len(observation), width),
                )
            vocabulary = self.declared_vocabulary(shape, S.TOKENS)
            self.assertEqual(
                int(vocabulary), layout["vocabulary"],
                "%r's token vocabulary is its own — 96 on the two-seat rows, where a history "
                "slot is one id wide and the widening adds no id, and 102 on the six-seat "
                "row, whose six seat ids sit above them (card-tokens.md §6, shapes.md §8, "
                "seats.md §3): %r" % (shape, vocabulary),
            )

    def test_fam19_14_a_history_past_the_shapes_capacity_is_refused(self):
        """FAM-19.14 each shape's capacity encodes whole and one more is refused by name.

        `shapes.md` §8 derives the capacity of each row from that row's own betting and
        `flat-numeric.md` §5 makes it the block's refusal threshold as well as its length:
        a history of exactly the capacity encodes whole, one entry more is refused naming
        the field, the capacity and the count, and nothing is truncated
        (`docs/L2/features/capacity.md` §1, §3, ASM-42, D-33).  The case holds for every
        declared row — 24 and 25 on the default shape, 66 and 67 on the two-seat uncapped
        one, **98 and 99** on the six-seat one — and both encodings answer to the same
        number, because the dense block is `3 × capacity` wide and the token block one slot
        per action over it (`flat-numeric.md` §5, `card-tokens.md` §5), so a shape whose two
        blocks disagreed would be caught at either one.
        """
        for shape in self.shape_names()[:3]:
            layout = S.SHAPE_LAYOUTS[shape]
            capacity = layout["history"]
            self.assertEqual(
                S.history_capacity_of(self.shape_row(shape)), capacity,
                "%r declares the capacity its own betting gives it (shapes.md §8): %r"
                % (shape, S.history_capacity_of(self.shape_row(shape))),
            )
            fits = self.history_readout(shape, capacity)
            over = self.history_readout(shape, capacity + 1)
            for representation, key in ((S.FLAT, "dense"), (S.TOKENS, "tokens")):
                encoder = self.encoder(representation, shape)
                encoded = self.ep("features", "encode")(encoder, fits)
                self.assertEqual(
                    len(encoded), layout[key],
                    "a history of exactly %d entries — the whole of %r's capacity — encodes "
                    "in full on %r, and is never truncated (flat-numeric.md §5, shapes.md "
                    "§8, ASM-42): %d values"
                    % (capacity, shape, representation, len(encoded)),
                )
                text = S.refusal_text(
                    lambda: self.ep("features", "encode")(encoder, over)
                )
                self.assertIsNotNone(
                    text,
                    "a history longer than %r's capacity of %d is refused, not truncated "
                    "(shapes.md §8, ASM-42, D-33): %d entries"
                    % (shape, capacity, capacity + 1),
                )
                self.assertIn(
                    "history", S._family_token(text),
                    "the refusal names the field it refused — the history block "
                    "(flat-numeric.md §5): %r" % (text,),
                )
                for number in (capacity, capacity + 1):
                    self.assertIn(
                        str(number), text,
                        "the refusal names the capacity %d and the count that crossed it "
                        "(docs/L2/features/capacity.md §1, §3): %r" % (number, text),
                    )

    def test_fam19_15_param_count_is_each_shapes_own_at_the_declared_size(self):
        """FAM-19.15 14,766 and 18,510 at W = 36, D = 2; the default's 10,119 unchanged.

        `shapes.md` §8's table fixes the counts at **one** architecture: input + trunk +
        `A·W + A`, which is **14,766** on `no-limit-100` from its 329-wide input block and
        its six-wide head, **18,510** on `six-seat-no-limit-100` from its 433-wide block and
        the same six-wide head, and today's **10,119** on `fixed-limit-20`, unchanged
        (`shapes.md` §5, §8, ASM-40, ASM-44).  The default build carries no encoder and is
        sized from the kind's declared `observation_size`; every shaped build is handed that
        shape's own encoder, which is the declared way to build a learner on a non-default
        shape (`e2e-surface.md` §3.3) — and the widths the differences are made of are read
        off the encoders rather than spelled here, so the case states the design's counts
        and derives the design's arithmetic for each row.
        """
        kind = self.architecture_kind("naive")
        default = self.shape_names()[0]
        plain = int(self.ep("agents", "param_count")(
            self.learner(width=S.PARAM_WIDTH, depth=S.PARAM_DEPTH, seed=S.SEED_I, kind=kind)
        ))
        self.assertEqual(
            plain, S.PARAM_COUNTS[default],
            "the default shape's count at W = %d, D = %d is today's %d, unchanged "
            "(shapes.md §5, §8, ASM-40): %d"
            % (S.PARAM_WIDTH, S.PARAM_DEPTH, S.PARAM_COUNTS[default], plain),
        )
        delta_actions = len(S.SIZED_ACTIONS) - len(S.FIXED_ACTIONS)
        for shape in self.other_shapes():
            shaped = int(self.ep("agents", "param_count")(
                self.learner(width=S.PARAM_WIDTH, depth=S.PARAM_DEPTH, seed=S.SEED_I,
                             kind=kind, game=shape)
            ))
            self.assertEqual(
                shaped, S.PARAM_COUNTS[shape],
                "%r's count at the same architecture is %d, its own input block and its "
                "six-wide head (shapes.md §8, ASM-44): %d"
                % (shape, S.PARAM_COUNTS[shape], shaped),
            )
            delta_size = (
                self.declared_width(shape, S.FLAT) - self.declared_width(default, S.FLAT)
            )
            self.assertEqual(
                shaped - plain,
                delta_size * S.PARAM_WIDTH + delta_actions * S.PARAM_WIDTH + delta_actions,
                "the two counts differ by the two shape terms and nothing else — the input "
                "block's `Δsize·W` and the head's `ΔA·W + ΔA` on %r (shapes.md §8, "
                "sizing.md §6): %d more from %d, against %d"
                % (shape, shaped - plain, delta_size * S.PARAM_WIDTH
                   + delta_actions * S.PARAM_WIDTH + delta_actions, plain),
            )

    def test_fam19_16_an_encoder_less_spec_naming_another_shape_is_refused(self):
        """FAM-19.16 a spec naming a shape beside the default and carrying no encoder is refused.

        A kind's declared `observation_size` is the **default** shape's — `naive-stack`'s
        203 and the token kinds' 96 — so there is no width to build a learner on another
        shape at, and `agents.build_learner` refuses the spec by name instead of sizing it
        from a number that is not that shape's (`shapes.md` §8, ASM-44,
        `e2e-surface.md` §3.3).  The case holds for **each** shape declared beside the
        default, D-33's six-seat row included.  The refusal names the shape it was given,
        the missing `encoder` key, the default shape whose size it declined to use and the
        entry point that refused, so a reader is told both why and what to pass instead.

        The two controls are the builds that **are** legal: the same shaped spec beside that
        shape's encoder — which is what `learner_spec` hands a shaped build, and which
        differs from the refused spec in that one key alone — and the same spec on the
        default shape, which is today's encoder-less build and carries no `encoder` key at
        all (`shapes.md` §5).  No case asserts the private class of the refusal: L2 may
        refine error classes (`e2e-surface.md` §1) and a battery asserts the behaviour and
        never the class (`docs/L3/agents/errors.md` §2).
        """
        default = self.shape_names()[0]
        for shape in self.other_shapes():
            refused = self.learner_spec(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH,
                                        seed=S.SEED_I, game=shape, encoder=None)
            self.assertNotIn(
                "encoder", refused,
                "this spec is deliberately encoder-less, which is the only thing that makes "
                "the refusal observable (shapes.md §8, ASM-44): %r" % (sorted(refused),),
            )
            self.assertEqual(
                str(refused["game"]), shape,
                "the spec names %r (shapes.md §2, §3): %r" % (shape, refused["game"]),
            )
            text = S.refusal_text(lambda: self.ep("agents", "build_learner")(refused))
            self.assertIsNotNone(
                text,
                "an encoder-less spec naming %r is refused by name, never sized at the "
                "default shape's 203 (shapes.md §8, ASM-44): %r"
                % (shape, sorted(refused)),
            )
            for needle, why in (
                (S._family_token("build_learner"),
                 "the entry point that refused (docs/L3/agents/errors.md §3)"),
                (S._family_token(shape),
                 "the shape the spec named (shapes.md §8, ASM-44)"),
                ("encoder", "the key that is missing (shapes.md §8, ASM-44)"),
                (S._family_token(default),
                 "the default shape whose width it declined to use (shapes.md §8)"),
            ):
                self.assertIn(
                    needle, S._family_token(text),
                    "the refusal names %s on %r: %r" % (why, shape, text),
                )
            # The declared way to build it: the same spec beside that shape's encoder.
            accepted = self.learner_spec(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH,
                                         seed=S.SEED_I, game=shape)
            self.assertIn(
                "encoder", accepted,
                "a shaped learner spec carries the shape's encoder, which is the declared way "
                "to size one (shapes.md §8, e2e-surface.md §3.3): %r" % (sorted(accepted),),
            )
            beside = dict(accepted)
            del beside["encoder"]
            self.assertEqual(
                S.canon(beside), S.canon(refused),
                "the accepted spec and the refused one differ in the `encoder` key alone, so "
                "the refusal is that key's and nothing else's (shapes.md §8, ASM-44)",
            )
            learner = self.ep("agents", "build_learner")(accepted)
            self.assertGreater(
                int(self.ep("agents", "param_count")(learner)), 0,
                "the spec carrying %r's encoder builds a learner (e2e-surface.md §3.3)"
                % (shape,),
            )
        # ... and the default shape's encoder-less spec is today's, unchanged.
        plain = self.learner_spec(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH,
                                  seed=S.SEED_I, game=default, encoder=None)
        self.assertNotIn(
            "encoder", plain,
            "naming the default shape is today's encoder-less spec, so it carries no "
            "`encoder` key (shapes.md §5): %r" % (sorted(plain),),
        )
        self.assertIsNotNone(
            self.ep("agents", "build_learner")(plain),
            "an encoder-less spec on the default shape is sized from the kind's declared "
            "`observation_size` and still builds (shapes.md §5, §8)",
        )



if __name__ == "__main__":
    unittest.main()
