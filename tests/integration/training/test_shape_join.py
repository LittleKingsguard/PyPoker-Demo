"""The shape join -- TRNJ-11.

`training` holds two tables that are not the ladder's: the declared game shapes' names,
order and descriptor counts, and the greedy pass's two bounds.  It holds them because
`module-map.md` §2 grants it `engine.game_config` and no `game_shapes`, and
`features.decode_action` and no `features.action_space` — so the restatement is the module's
and the join is the battery's (`docs/L1/shapes.md` §4, D-13, D-29).

The join is the invariant a single module cannot check about itself:

* **TRNJ-11.1** the restated catalogue is the catalogue `engine` and `features` publish — the
  same names, in the same order, with the same descriptor count and the same descriptors
  (`shapes.md` §2, `sizing.md` §3);
* **TRNJ-11.2** a run's record names one shape, and its pool, its header and its variants
  are that shape's — the four carriers of `shapes.md` §3 as far as this module reaches
  (`records.md` §8, §12, `protocol.md` §1);
* **TRNJ-11.3** a second-shape run is the same record on another game, so a shape is data
  and never a second record layout (`shapes.md` §1, §5, FAM-15);
* **TRNJ-11.4** the retained decision stream decodes in that shape's vocabulary, so the
  indices a census reads are the ones `features.decode_action` answers for the run's game
  (`records.md` §15, `sizing.md` §6, D-29);
* **TRNJ-11.5** the pass's sample is the run's budget and its chip deltas are one per hand,
  on both shapes (`sizing.md` §4, `records.md` §15, ASM-38).

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

    def test_trnj_11_5_the_passes_sample_is_the_runs_budget_on_both_shapes(self):
        """TRNJ-11.5 `hands` is the budget, and the deltas are one per hand, on both.

        `sizing.md` §4 fixes the pass at the live budget's 1,000 hands and `records.md` §15
        bounds it at 2,000; the run's own sample budget is what it plays, so the block's
        `hands` and the run record's `budget` are one number and `net_chips` carries one
        delta per hand (`ladder.md` §6, ASM-38, D-29).
        """
        for record in (J.small_run(), J.no_limit_run()):
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


if __name__ == "__main__":
    unittest.main()
