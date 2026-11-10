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


# shapes.md §2: the two declared rows, default first, as the catalogue states them.  The
# values are the design's — the row is `fixed` — and the vocabulary is the shape's own
# index order, `sizing.md` §3's measured price order for the no-cap shape.
DECLARED_ROWS = (
    {
        "name": "fixed-limit-20",
        "default": True,
        "seats": 2,
        "blinds": (1, 2),
        "starting_stack": 20,
        "chips_in_play": 40,
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
        "bet_structure": "no-limit",
        "small_bet": None,
        "big_bet": None,
        "raise_cap": None,
        "actions": S.SIZED_ACTIONS,
        "head_width": 6,
        "normalisers": {"stack": 100, "pot": 200, "to_call": 100,
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
    def test_fam19_1_the_catalogue_declares_the_two_shapes_default_first(self):
        """FAM-19.1 engine.game_shapes declares the two rows, default first, in full.

        `shapes.md` §2 makes the catalogue one ordered declaration with `fixed-limit-20`
        first and the **default**, each row carrying its seats, blinds, starting stack,
        chips in play, bet structure, action vocabulary, head width and amount
        normalisers; `e2e-surface.md` §3.1 makes it the tenth `engine` entry point.  A
        catalogue that declared one shape, in another order, or with a fact missing is
        caught here, row by row (`e2e-surface.md` §4, D-29).
        """
        catalogue = self.declared()
        self.assertGreater(
            len(catalogue),
            1,
            "the catalogue declares **more than one** shape: the second is the whole of "
            "D-29 (shapes.md §2): %r" % ([name for name, _row in catalogue],),
        )
        names = [name for name, _row in catalogue]
        self.assertEqual(
            names[:2],
            [row["name"] for row in DECLARED_ROWS],
            "the declared shapes are fixed-limit-20 and no-limit-100, in that order — the "
            "default first (shapes.md §2, D-29): %r" % (names,),
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
        """FAM-19.2 game_config() is the default row and game_config(name) that shape's.

        With no argument it returns the mapping it always returned — the default shape's
        row, byte for byte (ASM-6, `shapes.md` §2) — and named it returns the same fifteen
        keys with that shape's values: a 100-chip stack, no fixed bet, no cap and so no
        `limit`, and the same seats, blinds and streets (`e2e-surface.md` §3.1).
        """
        default = self.game_config()
        named_default = self.game_config(self.shape_names()[0])
        self.assertEqual(
            S.canon(default),
            S.canon(named_default),
            "game_config() with no argument is the default shape's row, and naming that "
            "row by name is the same mapping (shapes.md §2, §3)",
        )
        second = self.game_config(self.second_shape())
        self.assertEqual(
            {S._family_token(key) for key in default},
            {S._family_token(key) for key in second},
            "both shapes declare the same fifteen keys with the same value shapes "
            "(e2e-surface.md §3.1, shapes.md §2): %r against %r"
            % (sorted(str(key) for key in default), sorted(str(key) for key in second)),
        )
        present = {S._family_token(name) for name in second}
        missing = [key for key in CONFIG_KEYS if S._family_token(key) not in present]
        self.assertFalse(
            missing,
            "the named shape's config carries the fifteen declared keys; it is missing %r "
            "and carries %r" % (missing, sorted(str(key) for key in second)),
        )
        self.assertEqual(
            S.starting_stack(second), 100,
            "the no-cap shape's starting stack is 100 (shapes.md §2): %r" % (second,),
        )
        self.assertEqual(
            S.starting_stack(default), 20,
            "the default shape's starting stack is 20, unchanged (ASM-6, shapes.md §5)",
        )
        for key in ("seats", "blinds", "small_blind", "big_blind", "blind_levels"):
            self.assertEqual(
                S.canon(self.row_value(default, key)),
                S.canon(self.row_value(second, key)),
                "the two shapes share their table: %r differs between them "
                "(shapes.md §2)" % (key,),
            )
        for key in ("small_bet", "big_bet", "raise_cap", "limit"):
            value = self.row_value(second, key)
            self.assertIsNone(
                value,
                "a shape with no fixed bet and no cap declares %r as None "
                "(e2e-surface.md §3.1, shapes.md §2): %r" % (key, value),
            )
        self.assertEqual(
            self.row_value(default, "raise_cap"), 4,
            "the fixed game's raise cap of four is unchanged, and is the default's own "
            "fact now rather than the game's (ASM-6, shapes.md §5)",
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
        """FAM-19.5 the configuration's `game` is the run record's, and the default's too.

        `shapes.md` §3 makes the configuration the first carrier: it declares `game`, the
        run repeats it under `game`, the run's pool block repeats it, and the record's
        header family is built from that shape's `game_config` and vocabulary — so a run
        says which game its curves are about (`records.md` §12, `e2e-surface.md` §3.5,
        D-29).  A configuration that names none is trained on the default shape, and its
        record says **that** (`shapes.md` §3: absence is the default).
        """
        shape = self.second_shape()
        configuration = self.shaped_rung(shape=shape, seeds=(S.SEED_A,))
        record = self.ep("training", "run")(
            configuration, [S.SEED_A], S.BUDGET_TINY, "cpu"
        )
        self.assertEqual(
            str(S.declared_field(record, "a run record (records.md §12)", "game")),
            shape,
            "a run record names the shape it played (records.md §12, shapes.md §3): %r"
            % (record.get("game"),),
        )
        pool_block = S.declared_field(record, "a run record (records.md §12)", "pool")
        self.assertEqual(
            str(S.declared_field(pool_block, "a run record's pool block (records.md §12)",
                                 "game")),
            shape,
            "the record's pool block names the same shape as the record (records.md §8, "
            "§12, shapes.md §3): %r" % (pool_block,),
        )
        header = S.declared_field(record, "a run record (records.md §12)", "header")
        self.assertEqual(
            S.starting_stack(S.declared_field(header, "a run record's header (§1)",
                                              "game")),
            100,
            "the header's game configuration is the run's shape's, not the default's "
            "(protocol.md §1, shapes.md §3): %r" % (header.get("game"),),
        )
        self.assertEqual(
            S.action_vocabulary(S.declared_field(header, "a run record's header (§1)",
                                                 "action space")),
            set(range(len(S.SIZED_ACTIONS))),
            "the header's vocabulary is the named shape's six descriptors (protocol.md "
            "§1, shapes.md §3): %r" % (header.get("action space"),),
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
        and its membership cannot mix two (D-29, D-16).
        """
        shape = self.second_shape()
        pool = self.shaped_pool(shape, tags=("kestrel",))
        row = self.members(pool)
        self.assertEqual(
            str(S.declared_field(row, "a pool record (records.md §8)", "game")),
            shape,
            "a pool record names the one shape its members play (records.md §8, "
            "shapes.md §3): %r" % (row.get("game"),),
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
                str(S.declared_field(member, "a version member (records.md §7)", "game")),
                shape,
                "a version member of a non-default shape's pool records that shape as "
                "**required** (records.md §7, shapes.md §3): %r" % (member,),
            )
        # A default-shape member in a no-cap pool: refused, naming the member and both.
        stray = self.version("bramble", game=None)
        text = S.refusal_text(lambda: self.pool({
            "members": [stray],
            "m": S.LEAGUE_BOUND,
            "frozen": True,
            "game": shape,
        }))
        self.assertIsNotNone(
            text,
            "a pool declaration naming one shape and a member of another is refused, not "
            "windowed (shapes.md §3, records.md §8, D-29)",
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
        today's bytes — and a learner of any other declared shape writes version **4** and
        a `game` field (`shapes.md` §5, ASM-40).  A `load` whose spec names a shape its
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
        shape = self.second_shape()
        named_path = self.saved(shape=shape, name="fam19-nocap.ckpt")
        named_meta = self.container(named_path)
        self.assertEqual(
            int(named_meta["format_version"]), 4,
            "a container of any other declared shape writes version 4 "
            "(sizing.md §6, ASM-40): %r" % (named_meta.get("format_version"),),
        )
        self.assertEqual(
            str(named_meta.get("game")), shape,
            "a version-4 container requires the `game` field, naming its shape "
            "(sizing.md §6): %r" % (named_meta.get("game"),),
        )
        # The identity is load-bearing: a spec naming the other shape is refused by name.
        spec = self.learner_spec(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH,
                                 seed=S.SEED_I, game=self.shape_names()[0])
        text = S.refusal_text(lambda: self.ep("agents", "load")(spec, named_path))
        self.assertIsNotNone(
            text,
            "agents.load refuses a spec whose shape the container contradicts, naming both "
            "(e2e-surface.md §3.3, shapes.md §3, sizing.md §6)",
        )
        for named in (self.shape_names()[0], shape):
            self.assertIn(
                S._family_token(named),
                S._family_token(text),
                "the refusal names both shapes (shapes.md §3): %r" % (text,),
            )
        # And the default's container is read as the default: a no-cap spec is refused.
        spec_named = self.learner_spec(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH,
                                       seed=S.SEED_I, game=shape)
        text = S.refusal_text(lambda: self.ep("agents", "load")(spec_named, default_path))
        self.assertIsNotNone(
            text,
            "a container of the default shape is read as the default shape, so a spec "
            "naming the other one is refused (shapes.md §3, §5)",
        )
        self.assertIn(
            S._family_token(shape),
            S._family_token(text),
            "the refusal names the shape the spec asked for (shapes.md §3): %r" % (text,),
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

        The head is the shape's — three wide on the default shape and six on the no-cap
        one — and an index decodes to a descriptor `engine.apply_action` accepts only in
        the vocabulary that declared it, so a mask carrying a sixth index into a
        three-head learner is refused **naming the shape it decides in** rather than read
        as one of its own indices (`sizing.md` §6, `shapes.md` §3, D-29).
        """
        shape = self.second_shape()
        learner = self.learner(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH, seed=S.SEED_I)
        readout = self.readout(self.hand(S.SEED_I, shape))
        observation = self.ep("features", "encode")(self.encoder(), readout)
        mask = list(self.ep("features", "legal_indices")(readout["legal"]))
        self.assertIn(
            5, mask,
            "the named shape's first decision offers its sixth index, which is what makes "
            "the refusal observable (sizing.md §2–§3): %r" % (mask,),
        )
        text = S.refusal_text(lambda: self.ep("agents", "act")(learner, observation, mask))
        self.assertIsNotNone(
            text,
            "a learner of one shape's head refuses another shape's observation and mask, "
            "naming the shape it decides in (sizing.md §6, shapes.md §3)",
        )
        self.assertIn(
            S._family_token(self.shape_names()[0]),
            S._family_token(text),
            "the refusal names the shape whose head refused the index (shapes.md §3, "
            "sizing.md §6): %r" % (text,),
        )
        six_learner = self.learner(width=S.SHAPE_WIDTH, depth=S.SHAPE_DEPTH,
                                   seed=S.SEED_I, game=shape)
        result = self.ep("agents", "act")(six_learner, observation, mask)
        self.assertIn(
            self.action_index(result), mask,
            "a learner built in the named shape's head answers that shape's decision with "
            "one of its legal indices (e2e-surface.md §3.3, sizing.md §6): %r" % (result,),
        )

    def test_fam19_10_param_count_follows_the_shape_s_vocabulary(self):
        """FAM-19.10 param_count's output term is the shape's: `A·W + A`.

        `sizing.md` §6 makes the output layer `W → A` with `A` the shape's descriptor
        count, so two learners of **one** architecture under one rule and one utility
        differ by exactly `ΔA·W + ΔA` — three widths and three more at the second shape —
        and the default shape keeps today's `3W + 3` (ASM-40, ASM-10).
        """
        width = S.SHAPE_WIDTH
        first = self.learner(width=width, depth=S.SHAPE_DEPTH, seed=S.SEED_J)
        second = self.learner(width=width, depth=S.SHAPE_DEPTH, seed=S.SEED_J,
                              game=self.second_shape())
        first_count = int(self.ep("agents", "param_count")(first))
        second_count = int(self.ep("agents", "param_count")(second))
        delta_actions = len(S.SIZED_ACTIONS) - len(S.FIXED_ACTIONS)
        self.assertEqual(
            second_count - first_count, delta_actions * width + delta_actions,
            "the head is the shape's: `A·W + A` at each, so six descriptors against three "
            "cost %d×%d + %d more parameters (sizing.md §6, ASM-40): %d against %d"
            % (delta_actions, width, delta_actions, first_count, second_count),
        )
        rows = {name: row for name, row in self.declared()}
        self.assertEqual(
            int(self.row_value(rows[self.shape_names()[0]], "head_width")),
            len(S.FIXED_ACTIONS),
            "the default shape's declared head width is its vocabulary's size "
            "(shapes.md §2, sizing.md §6)",
        )
        self.assertEqual(
            int(self.row_value(rows[self.second_shape()], "head_width")),
            len(S.SIZED_ACTIONS),
            "the named shape's declared head width is its vocabulary's size "
            "(shapes.md §2, sizing.md §6)",
        )

    # -- the report (§6, §13) ---------------------------------------------
    def test_fam19_11_a_report_states_the_shape_and_refuses_a_record_naming_two(self):
        """FAM-19.11 the report's header carries the shape, and two shapes are refused.

        `records.md` §13 and `shapes.md` §3 make the report's `header` family state the
        shape the run, the pool family and the matrix agree on, and `evaluation.report`
        refuse a record whose three do not name one shape — naming **all three** and the
        shape each names, so a reader is told which record to re-derive (`protocol.md` §1,
        `shapes.md` §6, D-29).
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


if __name__ == "__main__":
    unittest.main()
