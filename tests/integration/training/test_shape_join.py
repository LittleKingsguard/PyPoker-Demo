"""The shape join -- TRNJ-11.

`training` holds two tables that are not the ladder's: the declared game shapes' names,
order, descriptor counts and history capacities, and the greedy pass's bounds.  It holds
them because `module-map.md` §2 grants it `engine.game_config` and no `game_shapes`, and
`features.decode_action` and no `features.action_space` — so the restatement is the module's
and the join is the battery's (`docs/L1/shapes.md` §4, §8, D-13, D-29, D-33).

The join is the invariant a single module cannot check about itself:

* **TRNJ-11.1** the restated catalogue is the catalogue `engine` and `features` publish — the
  same names, in the same order, with the same descriptor count, the same descriptors and
  the same history capacities (`shapes.md` §2, §8, `sizing.md` §3, ASM-42);
* **TRNJ-11.2** a run's record names one shape, and its pool, its header and its variants
  are that shape's — the four carriers of `shapes.md` §3 as far as this module reaches
  (`records.md` §8, §12, `protocol.md` §1);
* **TRNJ-11.3** a second- or third-shape run is the same record on another game, so a shape
  is data and never a second record layout (`shapes.md` §1, §5, FAM-15);
* **TRNJ-11.4** the retained decision stream decodes in that shape's vocabulary, so the
  indices a census reads are the ones `features.decode_action` answers for the run's game
  (`records.md` §15, `sizing.md` §6, D-29);
* **TRNJ-11.5** the pass's sample is the run's budget and its chip deltas are one per hand,
  on every shape (`sizing.md` §4, `records.md` §15, ASM-38);
* **TRNJ-11.6** a six-seat run trains end to end: ten points, ASM-18's retained window, the
  six-seat header and a pass whose every decision is the learner's own (`shapes.md` §1, §2,
  `seats.md` §4, ASM-18, ASM-38, ASM-42, D-33);
* **TRNJ-11.7** the learner takes each of the six seats once, and the default shape's
  alternation did not move (`seats.md` §4, `episode.md` §1, ASM-43, ASM-44, `shapes.md` §5);
* **TRNJ-11.8** five distinct opponents are drawn from a pool of five, and a pool that
  cannot supply the draw is refused naming both counts in `evaluation`'s own class
  (`seats.md` §4, `records.md` §8, ASM-43, `module-map.md` §2);
* **TRNJ-11.9** a six-seat run writes no matrix, because this module never measures a cell
  and `evaluation`'s pairwise instrument refuses a shape of more than two seats
  (`seats.md` §5, `module-map.md` §3, D-22, D-33).

Every case states the design section whose claim it reads; none asserts a value a document
leaves to the run (`docs/L1/battery.md` §5, D-6).
"""

import importlib.util
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "training_join_support" in sys.modules:
    J = sys.modules["training_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "training_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["training_join_support"] = J
    _spec.loader.exec_module(J)


class ShapeCatalogueJoin(J.JoinCase):
    """TRNJ-11.1 -- the restated catalogue is the published one."""

    def test_trnj_11_1_the_restated_shapes_are_the_published_ones(self):
        """TRNJ-11.1 `training`'s shape table equals `engine.game_shapes()` and `features`.

        `docs/L1/shapes.md` §2: `engine.game_shapes()` "publishes the declared shapes,
        default first: its instance set is the declaration itself", and the row's
        vocabulary is the shape's — three indices on the fixed-limit shape and six on the
        no-cap one, in the shape's own declared order (`sizing.md` §3).  `training` restates
        the names, their order and each shape's descriptor count, because the map grants it
        neither call; the join is what keeps the restatement the catalogue's rather than a
        copy that can drift (`shapes.md` §4, D-13, D-29).
        """
        published = J.shape_names()
        names, actions = J.declared_shapes()
        self.assertEqual(
            tuple(str(name) for name in names),
            published,
            "the restated shape names are the catalogue's, in its order -- default first "
            "(shapes.md §2, D-29): module %r against engine %r"
            % (tuple(names), published),
        )
        self.assertEqual(
            dict(actions),
            {name: len(J.action_space(shape=name)) for name in published},
            "and each restated descriptor count is the length of the vocabulary "
            "features.action_space publishes for that shape, so no count is a `3` or a "
            "`6` this module invented (shapes.md §2, sizing.md §3, §6): module %r"
            % (dict(actions),),
        )
        for name in published:
            space = J.action_space(shape=name)
            declared = {
                int(index): str(record["name"]) if isinstance(record, dict) else str(record)
                for index, record in dict(space).items()
            }
            self.assertEqual(
                sorted(declared),
                list(range(int(actions[name]))),
                "the shape %r's indices are exactly the restated count, contiguous from "
                "zero, so a mask of that width is that shape's (sizing.md §3, "
                "shapes.md §2): %r" % (name, sorted(declared)),
            )
            for index, descriptor in declared.items():
                self.assertEqual(
                    J.shaped_decode_action(index, shape=name),
                    descriptor,
                    "and the two directions are one vocabulary: decode_action of an index "
                    "is the descriptor action_space names there (features/surface.md "
                    "§7, §9, shapes.md §2): shape %r, index %r" % (name, index),
                )
        self.assertEqual(
            J.shaped_game_config(published[0]),
            J.game_config(),
            "the first published shape is the default, and its row is the mapping "
            "engine.game_config() returns with no argument -- byte for byte, which is "
            "what keeps every fixed-limit record readable (shapes.md §2-§3, ASM-6, D-29)",
        )
        self.assertEqual(
            dict(J.declared_history()),
            {name: J.game_shapes()[name]["history"] for name in published},
            "and each restated history capacity is the published catalogue row's own, so a "
            "pass's record bound is a multiple of the shape's capacity and never a number "
            "this module invented -- 24 slots on the default shape, 66 and 98 on the two "
            "uncapped ones (shapes.md §8, ASM-42, D-13, D-33): module %r"
            % (dict(J.declared_history()),),
        )


class ShapeInTheRecordJoin(J.JoinCase):
    """TRNJ-11.2, TRNJ-11.3 -- one shape per record, on both declared shapes."""

    def test_trnj_11_2_a_records_shape_is_its_pools_and_its_headers(self):
        """TRNJ-11.2 a run record names one shape, and the pool and the header agree.

        `shapes.md` §3 names four carriers: the configuration, the checkpoint, the pool and
        the report.  A run reaches three of them — its own `game`, its pool's, and the
        header's `game` and `action space` — and `evaluation.report` refuses a run, a pool
        and a matrix that do not name one shape, so the three must agree before a record
        leaves this module (`records.md` §8, §12, `protocol.md` §1, D-29).
        """
        for record, shape in (
            (J.small_run(), J.shape_names()[0]),
            (J.no_limit_run(), J.shape_names()[1]),
            (J.six_seat_run(), J.third_shape()),
        ):
            self.assertEqual(
                str(record.get("game")),
                shape,
                "a run's record names the shape it played, and it is the shape the "
                "configuration declared (records.md §12, shapes.md §3, D-29): %r against "
                "%r" % (record.get("game"), shape),
            )
            pool = J.pool_of(record)
            self.assertEqual(
                str(pool.get("game")),
                shape,
                "the pool's record repeats it, because a pool is one shape's and "
                "`game` is a required field of a pool record (records.md §8, "
                "shapes.md §3): %r against %r" % (pool.get("game"), shape),
            )
            header = J.header_of(record)
            self.assertEqual(
                J.canonical(header["game"]),
                J.canonical(J.shaped_game_config(shape)),
                "the header's game is that shape's row, so a reader of the record alone "
                "sees the stack and the bet structure it was measured in "
                "(surface.md §4.1, engine/surface.md §3, D-29)",
            )
            published = {
                int(index): str(value["name"]) if isinstance(value, dict) else str(value)
                for index, value in dict(J.action_space(shape=shape)).items()
            }
            self.assertEqual(
                {
                    int(index): str(value)
                    for index, value in dict(header["action space"]).items()
                },
                published,
                "and the header's action space is the same shape's vocabulary, so the "
                "record's game and its mask are one game (surface.md §4.1, "
                "features/surface.md §7, D-29): %r" % (header["action space"],),
            )

    def test_trnj_11_3_the_second_shape_is_the_same_record_on_another_game(self):
        """TRNJ-11.3 a second-shape run is one record shape, on another vocabulary.

        `shapes.md` §1: the second shape "is reached the way any configuration outside the
        registry is reached: as a value through `training.run`", so nothing about the record
        is conditional on the game — the same keys, the same sub-records, the same pool
        structure — and the only difference is the vocabulary, the stack and the amount
        normalisers the shape declares (`shapes.md` §2, §5, FAM-15, D-29).
        """
        default = J.small_run()
        second = J.no_limit_run()
        self.assertEqual(
            sorted(str(key) for key in second),
            sorted(str(key) for key in default),
            "the two shapes' records carry the same keys, because the shape is data and "
            "never a second record layout (shapes.md §1, §5, D-29): %r against %r"
            % (sorted(second), sorted(default)),
        )
        self.assertEqual(
            sorted(str(key) for key in J.pool_of(second)),
            sorted(str(key) for key in J.pool_of(default)),
            "and the same pool block's keys, so a pool on either shape is read one way "
            "(records.md §8, shapes.md §3): %r against %r"
            % (sorted(J.pool_of(second)), sorted(J.pool_of(default))),
        )
        third = J.six_seat_run()
        self.assertEqual(
            sorted(str(key) for key in third),
            sorted(str(key) for key in default),
            "and a run on the catalogue's third shape carries the same keys, because a seat "
            "count adds no key to the record: a shape is data and never a third record "
            "layout (shapes.md §1, §5, seats.md §2, D-29, D-33): %r against %r"
            % (sorted(third), sorted(default)),
        )
        self.assertEqual(
            sorted(str(key) for key in J.pool_of(third)),
            sorted(str(key) for key in J.pool_of(default)),
            "and the pool block's keys are the same three shapes', so a five-member pool on "
            "six seats is read exactly as the three-member pool of a fixed-limit run "
            "(records.md §8, shapes.md §3, ASM-43, D-33): %r against %r"
            % (sorted(J.pool_of(third)), sorted(J.pool_of(default))),
        )
        shape = J.shape_names()[1]
        self.assertNotEqual(
            J.canonical(J.shaped_game_config(shape)),
            J.canonical(J.shaped_game_config(J.shape_names()[0])),
            "the two shapes are two games — another stack, another bet structure and, on "
            "the sized shape, no cap at all — so a figure on one is never read as a figure "
            "on the other (shapes.md §2, §6, D-29)",
        )
        self.assertEqual(
            len(dict(J.action_space(shape=shape))),
            6,
            "the second shape's vocabulary is six descriptors in an order the measurement "
            "sets, so a census reads indices 0 to 5 and never the default three "
            "(sizing.md §3, shapes.md §2, D-29)",
        )


class ShapeInThePassJoin(J.JoinCase):
    """TRNJ-11.4, TRNJ-11.5 -- the retained decisions decode in the run's vocabulary."""

    def test_trnj_11_4_the_retained_decisions_decode_in_the_runs_own_vocabulary(self):
        """TRNJ-11.4 every retained index is one `features.decode_action` answers for it.

        `records.md` §15 makes a decision's `index` and `descriptor` two readings of one
        choice "in the shape's declared order", and `sizing.md` §6 makes the head the
        shape's width.  So the pass's log is the place where the run's shape, its learner's
        head and `features`' vocabulary meet: an index outside the run's shape, or a
        descriptor that is another shape's spelling of it, is a record no census can
        attribute (`sizing.md` §2, §7, D-29).
        """
        for record, shape in (
            (J.small_run(), J.shape_names()[0]),
            (J.no_limit_run(), J.shape_names()[1]),
            (J.six_seat_run(), J.third_shape()),
        ):
            width = len(dict(J.action_space(shape=shape)))
            for declared in record["variants"]:
                variant = str(declared["name"])
                for seed in record["seeds"]:
                    block = J.greedy_block(record, variant, int(seed))
                    self.assertEqual(
                        str(block.get("mode")),
                        "off",
                        "the pass of %r at seed %r carries `mode: off`, the only mode a "
                        "retained decision reports (records.md §15, sizing.md §4, "
                        "ASM-38): %r" % (variant, seed, block.get("mode")),
                    )
                    decisions = J.decisions_of_block(block)
                    for decision in decisions:
                        index = int(decision["index"])
                        self.assertTrue(
                            0 <= index < width,
                            "an index of the pass of %r on the shape %r is one of that "
                            "shape's %r indices, because the learner's head is the shape's "
                            "width (sizing.md §6, records.md §15, D-29): %r"
                            % (variant, shape, width, decision),
                        )
                        self.assertEqual(
                            str(decision["descriptor"]),
                            str(J.shaped_decode_action(index, shape=shape)),
                            "and the descriptor is the one that shape's vocabulary gives "
                            "that index, so a census maps the record back to one band "
                            "(sizing.md §2-§3, records.md §15, D-29): %r" % (decision,),
                        )
                        self.assertIn(
                            index,
                            [int(member) for member in decision["legal"]],
                            "and it is one of the decision's own legal indices, which is "
                            "the mask the census is computed over (records.md §15, "
                            "sizing.md §7): %r" % (decision,),
                        )

    def test_trnj_11_5_the_passes_sample_is_the_runs_budget_on_every_shape(self):
        """TRNJ-11.5 `hands` is the budget, and the deltas are one per hand, on every shape.

        `sizing.md` §4 fixes the pass at the live budget's 1,000 hands and `records.md` §15
        bounds it at 2,000; the run's own sample budget is what it plays, so the block's
        `hands` and the run record's `budget` are one number and `net_chips` carries one
        delta per hand — on a six-seat shape as on the two two-seat ones, because the pass
        replays the sample the run trained rather than a sample of another size
        (`ladder.md` §6, `seats.md` §4, ASM-38, D-29, D-33).
        """
        for record in (J.small_run(), J.no_limit_run(), J.six_seat_run()):
            budget = int(record["budget"])
            for declared in record["variants"]:
                variant = str(declared["name"])
                for seed in record["seeds"]:
                    block = J.greedy_block(record, variant, int(seed))
                    self.assertEqual(
                        int(block.get("hands")),
                        budget,
                        "the pass of %r at seed %r plays the run's own sample budget, "
                        "which is what makes it cheap for the budgets a talk and a "
                        "battery use (sizing.md §4, records.md §15, ASM-38): %r against %r"
                        % (variant, seed, block.get("hands"), budget),
                    )
                    self.assertEqual(
                        len(list(block.get("net_chips") or ())),
                        budget,
                        "and it records one net chip delta per hand it played, so the "
                        "pass's price can be recomputed and not only quoted "
                        "(records.md §15, ASM-23): %r"
                        % (len(list(block.get("net_chips") or ())),),
                    )


class SixSeatRunJoin(J.JoinCase):
    """TRNJ-11.6, TRNJ-11.7 -- a six-seat run trains end to end, and takes six seats."""

    def test_trnj_11_6_a_six_seat_run_trains_end_to_end(self):
        """TRNJ-11.6 a six-seat run completes: ten points, a window, and its own decisions.

        `shapes.md` §1 makes a shape a value a configuration declares and not a fork of the
        loop, and `seats.md` §5 states that everything a run does — hands, readout, encoder,
        learner, pool, greedy pass — works at six seats.  So a six-seat run trains,
        snapshots, saves and passes as a default-shape run does: the curve closes at
        `budget // 10` with ten points, the record retains ASM-18's five snapshots plus the
        final model and each is a file, the four cost facts are measured, the header is the
        six-seat row, and the pass's decisions are **the learner's own** — each an index of
        its own legal mask that decodes in the six-seat vocabulary, which is what makes the
        block a sample `sizing.md` §4 allows this module to write (`records.md` §12, §15,
        `sizing.md` §4, ASM-18, ASM-38, ASM-42, D-33).
        """
        record = J.six_seat_run()
        six = J.third_shape()
        self.assertEqual(
            str(record.get("game")),
            six,
            "the run's record names the shape it played, and it is the catalogue's third "
            "row (records.md §12, shapes.md §3, D-33): %r against %r"
            % (record.get("game"), six),
        )
        pool = J.pool_of(record)
        self.assertEqual(
            str(pool.get("game")),
            six,
            "the pool's record repeats it, because a pool is one shape's and `game` is a "
            "required field of a pool record (records.md §8, shapes.md §3, D-33): %r"
            % (pool.get("game"),),
        )
        for member in list(pool.get("members") or ()):
            declared = member.get("game") if hasattr(member, "get") else None
            self.assertIn(
                declared,
                (None, six),
                "every member the pool carries names the pool's shape where it names one, "
                "so no member of another shape was seated: a member of another shape is the "
                "pool's ShapeMismatch, refused before a hand (records.md §8, shapes.md §3, "
                "seats.md §4, D-13, D-33): %r" % (member,),
            )
        budget = int(record["budget"])
        for declared in record["variants"]:
            variant = str(declared["name"])
            for seed in record["seeds"]:
                curve = J.curve_of(record, variant, int(seed))
                self.assertEqual(
                    [int(sample) for sample in list(curve.get("samples") or ())],
                    [k * max(1, J.RUN_BUDGET // 10) for k in range(1, 11)],
                    "every curve of %r at seed %r closes at the ten snapshot intervals, one "
                    "hand apart at this budget, so no interval was skipped at six seats "
                    "(curves.md §2, loop.md §2, ASM-18): %r" % (variant, seed, curve),
                )
                self.assertEqual(
                    len(list(curve.get("td_error") or ())),
                    10,
                    "and it carries ten signals, one per point, on the third shape as on the "
                    "other two (curves.md §2, §5, ASM-18): %r"
                    % (list(curve.get("td_error") or ()),),
                )
                written = J.checkpoints_of(record, variant, int(seed))
                snapshots = list(written.get("snapshots") or ())
                self.assertEqual(
                    len(snapshots),
                    J.retained(),
                    "the pair retains ASM-18's five snapshots — ten written and the last "
                    "five kept — beside the final model, so the retained window is the same "
                    "window on a six-seat run (checkpoints.md §3, ASM-18, D-33): %r"
                    % (snapshots,),
                )
                for path in snapshots + [written.get("final")]:
                    self.assertTrue(
                        os.path.isfile(J.resolve(path)),
                        "and each retained snapshot and the final model is a file this run "
                        "wrote, because an episode no one can load is three episodes "
                        "(checkpoints.md §1-§3, write-root.md §3): %r" % (path,),
                    )
                timings = J.timings_of(record, variant, int(seed))
                for key in ("hands", "wall_clock_seconds", "seconds_per_hand",
                            "hands_per_second"):
                    self.assertIn(
                        key,
                        timings,
                        "the pair's cost is the four facts records.md §12 declares — the "
                        "hands, the clock, the seconds a hand and the hands a second "
                        "(records.md §12, ASM-15): %r" % (sorted(timings),),
                    )
                self.assertEqual(
                    int(timings["hands"]),
                    budget,
                    "the hands it counts are the hands it played (records.md §12, ASM-23)",
                )
                for key in ("wall_clock_seconds", "seconds_per_hand", "hands_per_second"):
                    self.assert_finite(
                        timings[key],
                        "the pair's %r at six seats" % (key,),
                        "records.md §12, ASM-15",
                    )
                block = J.greedy_block(record, variant, int(seed))
                self.assertEqual(
                    str(block.get("mode")),
                    "off",
                    "the six-seat pass carries `mode: off`, the masked maximum and the "
                    "tie-break alone with no generator drawn from (records.md §15, "
                    "sizing.md §4, ASM-38): %r" % (block.get("mode"),),
                )
                self.assertEqual(
                    int(block.get("hands")),
                    budget,
                    "and it plays the run's own sample budget, so training and the pass "
                    "replay one sample at six seats as at two (sizing.md §4, records.md "
                    "§15, ASM-38): %r against %r" % (block.get("hands"), budget),
                )
                net = list(block.get("net_chips") or ())
                self.assertEqual(
                    len(net),
                    int(block["hands"]),
                    "with one net chip delta per hand it played, so the five-opponent "
                    "pass's price is recomputable and not only quoted (records.md §15, "
                    "ASM-23): %r deltas for %r hands" % (len(net), block.get("hands")),
                )
                decisions = J.decisions_of_block(block)
                self.assertTrue(
                    decisions,
                    "and it retains decisions, so the block is a sample and not an empty "
                    "list (sizing.md §4, ASM-38): %r" % (block,),
                )
                for decision in decisions:
                    index = int(decision["index"])
                    self.assertIn(
                        index,
                        [int(member) for member in list(decision["legal"])],
                        "every retained index is one of its own decision's legal indices, so "
                        "the decision is the learner's own and the census re-derives no mask "
                        "(records.md §15, sizing.md §7, ASM-38): %r" % (decision,),
                    )
                    self.assertEqual(
                        str(decision["descriptor"]),
                        str(J.shaped_decode_action(index, shape=six)),
                        "and its descriptor is the six-seat vocabulary's reading of that "
                        "index, so the record maps back to one band of the run's own game "
                        "(records.md §15, sizing.md §2-§3, features/surface.md §9, D-33): %r"
                        % (decision,),
                    )
            encoder = J.build_encoder(str(declared["encoding"]), shape=six)
            learner = J.build_learner(
                {
                    "backend": declared["backend"],
                    "architecture": dict(declared["architecture"]),
                    "seed": int(record["seeds"][0]),
                    "encoder": encoder,
                    "game": six,
                }
            )
            self.assertEqual(
                int(J.param_count(learner)),
                18510,
                "the learner the run's own variant row describes is 18,510 parameters at "
                "W = 36, D = 2 on the six-seat encoder — the third row's arithmetic, which "
                "rises by the input term alone from the default shape's 10,119, so the count "
                "follows the shape's encoder and not the kind's declared observation size "
                "(shapes.md §8, ASM-42, ASM-44, docs/L3/training/loop.md §1 step 3): %r"
                % (J.param_count(learner),),
            )

    def test_trnj_11_7_the_learner_takes_each_of_the_six_seats(self):
        """TRNJ-11.7 the learner holds each of the six seats for one hand in six.

        `seats.md` §4 and ASM-43 seat the learner at `hand index mod seats`, reading the seat
        count from `engine.game_config` and never from a literal, because position is a real
        and unequal advantage in a multi-way pot and a fixed seat would make a seed's chips a
        measurement of the seat it drew.  The private name that expresses it, `_seat`, is
        contract for the unit battery (`docs/L3/training/README.md` §4, `episode.md` §1), and
        on a two-seat shape it is the `index % 2` every run has always had — so this case
        measures both halves of the claim: the rotation generalises to six seats and the
        default shape's alternation did not move (`seats.md` §2, §4, `shapes.md` §5,
        ASM-43, ASM-44, D-33).
        """
        six = J.third_shape()
        self.assertEqual(
            int(J.shaped_game_config(six)["seats"]),
            6,
            "the third row declares six seats, which is the modulus the rotation reads "
            "(shapes.md §2, seats.md §2, engine/surface.md §3, ASM-44): %r"
            % (J.shaped_game_config(six)["seats"],),
        )
        self.assertEqual(
            [J.seat_of_hand(index, six) for index in range(6)],
            [0, 1, 2, 3, 4, 5],
            "so the first six hands of a six-seat run put the learner in each seat once, in "
            "seat order, and no seat is held twice (seats.md §4, ASM-43, D-33): %r"
            % ([J.seat_of_hand(index, six) for index in range(6)],),
        )
        default = J.shape_names()[0]
        self.assertEqual(
            [J.seat_of_hand(index, default) for index in range(6)],
            [0, 1, 0, 1, 0, 1],
            "and on the default shape the same rule is the alternation a run has always "
            "had, so no fixed-limit hand moved when the seat became a function of the "
            "shape (shapes.md §5, episode.md §1, ASM-43): %r"
            % ([J.seat_of_hand(index, default) for index in range(6)],),
        )


class SixSeatDrawJoin(J.JoinCase):
    """TRNJ-11.8 -- five distinct opponents, and a pool that cannot supply them."""

    def test_trnj_11_8_five_distinct_opponents_and_a_pool_that_cannot_supply_them(self):
        """TRNJ-11.8 a pool of five satisfies the draw; a pool of four is refused, naming both.

        `seats.md` §4 and ASM-43 make `evaluation.opponent(pool, seed, count)` a draw
        **without replacement**, so a six-seat hand seats `seats - 1` distinct members and no
        seat faces itself; a pool holding fewer than the draw is that entry point's own
        refusal, naming both counts, because "a substitute seat would be an opponent the
        membership does not carry".  The join is therefore three measurements: the run whose
        pool names two folders holds five members and trains, so the draw was satisfied hand
        after hand; the same configuration with one folder holds four and is refused with 5
        and 4 in `evaluation`'s class, which is the class a re-wrapping here would hide; and
        the draw itself returns five distinct policies and refuses six from a five-member
        pool (`records.md` §8, `league.md` §2, `module-map.md` §2, D-21, D-33).
        """
        six = J.third_shape()
        record = J.six_seat_run()
        members = list(J.pool_of(record).get("members") or ())
        self.assertEqual(
            len(members),
            5,
            "the run's frozen pool holds D-6's three anchors plus the two folders its "
            "declaration names — five members, the least a five-opponent draw can be "
            "satisfied from (records.md §8, seats.md §4, ASM-32, ASM-43, D-21): %r"
            % ([member.get("id") for member in members],),
        )
        budget = int(record["budget"])
        played = 0
        for declared in record["variants"]:
            variant = str(declared["name"])
            for seed in record["seeds"]:
                block = J.greedy_block(record, variant, int(seed))
                net = list(block.get("net_chips") or ())
                self.assertEqual(
                    len(net),
                    budget,
                    "the run played every hand of its budget against those five opponents, "
                    "so the draw was satisfied hand after hand and no seat was left empty "
                    "(seats.md §4, sizing.md §4, ASM-43, ASM-38): %r deltas for %r hands"
                    % (len(net), budget),
                )
                played += len(J.decisions_of_block(block))
        self.assertGreater(
            played,
            0,
            "and it trained against them, so the five members are opposition and not a "
            "listing (records.md §15, sizing.md §4, ASM-38)",
        )
        # ... the same configuration with one folder holds four members, and the draw of
        # five is refused by the module that owns the membership.
        four = J.six_seat_configuration_with(J.folders()[:1])
        captured = {}

        def attempt():
            try:
                return J.run(four, seeds=[J.RUN_SEED], budget=J.RUN_BUDGET)
            except Exception as exc:  # noqa: BLE001 - the class is asserted below
                captured["exc"] = exc
                raise

        message = self.assert_refusal(
            "opponent",
            groups=(("asks for 5",), ("holds 4",)),
            call=attempt,
            note="a six-seat run whose pool holds four members",
        )
        self.assertEqual(
            type(captured["exc"]).__module__.split(".")[0],
            "evaluation",
            "the refusal propagates in its owner's class — evaluation's, not training's — "
            "because a refusal re-wrapped here would hide which module owns the membership "
            "(module-map.md §2, records.md §8, seats.md §4, errors.md §2): %r"
            % (captured.get("exc"),),
        )
        self.assertIn(
            "5",
            message,
            "and it names the five distinct opponents the hand asked for (seats.md §4, "
            "ASM-43): %r" % (message,),
        )
        self.assertIn(
            "4",
            message,
            "beside the four members the pool holds, both counts being the whole of the "
            "finding (records.md §8, seats.md §4): %r" % (message,),
        )
        # ... and the draw itself: five distinct members, in the draw's order, without
        # replacement; six from a five-member pool is refused.
        declaration = dict(J.six_seat_configuration()["pool"], game=six)
        pool = J.build_pool(declaration)
        self.assertEqual(
            len(list(J.pool_members(pool)["members"])),
            5,
            "the pool `build_pool` reads back from that frozen declaration holds five "
            "members, so the drawn set below is drawn from the membership the run used "
            "(records.md §8, surface.md §5, ASM-32): %r"
            % (list(J.pool_members(pool)["members"]),),
        )
        drawn = J.draw(pool, J.RUN_SEED, 5)
        self.assertEqual(
            len(drawn),
            5,
            "a draw of five returns five policies (seats.md §4, ASM-43): %r" % (drawn,),
        )
        self.assertEqual(
            len({id(policy) for policy in drawn}),
            5,
            "and five **distinct** ones, because the draw is without replacement and a seat "
            "never faces itself (seats.md §4, league.md §2, ASM-43): %r" % (drawn,),
        )
        self.assert_refusal(
            "opponent",
            groups=(("asks for 6",), ("holds 5",)),
            call=lambda: J.draw(pool, J.RUN_SEED, 6),
            note="a draw of six from a five-member pool",
        )


class SixSeatNoMatrixJoin(J.JoinCase):
    """TRNJ-11.9 -- a six-seat run writes no matrix, and writes nothing it cannot measure."""

    def test_trnj_11_9_a_six_seat_run_writes_no_matrix(self):
        """TRNJ-11.9 the six-seat record is one record layout and carries no matrix.

        `shapes.md` §1 and §5 make a shape data, so the record's keys are the default
        shape's keys and no sixth key appears for six seats.  What a six-seat run cannot
        write is a **matrix**: `seats.md` §5 makes a cell a pair and a rating a fit over
        pairs, and `evaluation.match`, `matrix`, `rating` and `report` refuse a shape whose
        seat count is not two — a six-way hand is a placement and no permutation model is
        designed here (`module-map.md` §3, D-22, D-33).  So this case reads the record and
        the catalogue and calls none of the four.
        """
        record = J.six_seat_run()
        default = J.small_run()
        self.assertEqual(
            sorted(str(key) for key in record),
            sorted(str(key) for key in default),
            "a six-seat run's record carries the default shape's keys and no seventh, "
            "because a shape is data and never a second layout (shapes.md §1, §5, "
            "records.md §12, D-33): %r against %r"
            % (sorted(record), sorted(default)),
        )
        self.assertNotIn(
            "matrix",
            record,
            "and it carries no `matrix`: this module measures no cell, and the pairwise "
            "instrument refuses a shape of more than two seats (records.md §12-§13, "
            "seats.md §5, D-22, D-33): %r" % (sorted(record),),
        )
        self.assertNotIn(
            "rating",
            record,
            "and no `rating`, which is fitted over one shape's cells and reads as a "
            "distance from the baselines in that game (records.md §13, seats.md §5, "
            "D-16, D-22): %r" % (sorted(record),),
        )
        six = J.third_shape()
        self.assertEqual(
            str(record.get("game")),
            six,
            "the shape the record does name is the one whose `seats` is six "
            "(records.md §12, shapes.md §3, seats.md §2): %r" % (record.get("game"),),
        )
        self.assertEqual(
            int(J.shaped_game_config(six)["seats"]),
            6,
            "read off the catalogue: the third row declares six seats "
            "(engine/surface.md §3, seats.md §2, ASM-44): %r"
            % (J.shaped_game_config(six)["seats"],),
        )
        for name in (J.shape_names()[0], J.shape_names()[1]):
            self.assertEqual(
                int(J.shaped_game_config(name)["seats"]),
                2,
                "and the two shapes the instrument still measures are two-seat ones, which "
                "is the line seats.md §5 draws (league.md §4, ASM-43, D-22): %r on %r"
                % (J.shaped_game_config(name)["seats"], name),
            )


if __name__ == "__main__":
    unittest.main()
