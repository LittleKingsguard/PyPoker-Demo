"""The second declared game shape at `training`'s edge -- TRN-13.

D-29 declares a second game shape and `shapes.md` §3 names the four carriers that must
report it; this module is one of them.  What these cases assert is therefore the edge and
not a game's arithmetic: the record names the shape it played, an uncatalogued name is
refused naming it and the declared names, everything the loop derives from the game is
derived from the **run's own** shape, and a pair of two shapes is not a comparison.

| Case | What it reads |
|---|---|
| TRN-13.1 | the record's `game`, and the default shape when a configuration names none |
| TRN-13.2 | an uncatalogued `game` refused at the configuration and at an entry |
| TRN-13.3 | the run's own shape reaches the hand: 40 chips in play, or 200 |
| TRN-13.4 | a `no-limit-100` run trains end to end, six descriptors and all |
| TRN-13.5 | the learner's head is the shape's, so a six-index mask is that learner's |
| TRN-13.6 | `fairness` names the shape as a held constant and refuses a pair of two |
| TRN-13.7 | `game` reads at either level, and absence is the default and never a name |

Every case states the design section whose claim it reads (`docs/L1/battery.md` §5); none
asserts a value a document leaves to the run (`D-6`).
"""

from _training_support import (  # noqa: E402  - the battery's own support module
    INVENTED_SHAPE,
    PARAM_BUDGET,
    SHAPE_BUDGET,
    SHAPE_SEED,
    SNAPSHOTS,
    TrainingCase,
    agents,
    as_int,
    as_mapping,
    as_sequence,
    as_text,
    decisions_of,
    default_shape,
    engine,
    error_class,
    features,
    greedy_block,
    no_limit_configuration,
    no_limit_run,
    one_seed_run,
    second_shape,
    shaped_episode,
    shaped_game_config,
    shaped_vocabulary,
    training,
    with_entry_game,
    with_game,
)


class ShapeInTheRecordCase(TrainingCase):
    """TRN-13.1, TRN-13.2, TRN-13.7 -- the record's `game`, and a name refused."""

    def test_trn_13_1_the_record_names_the_shape_it_played(self):
        """TRN-13.1 a default-shape run's record carries `game`, naming the default.

        `records.md` §12 makes `game` a required key of a record this build writes, absent
        only for a record already on disk, and `shapes.md` §3 makes the configuration the
        first of the four carriers: the record **repeats** the name it played. A
        configuration that names no shape is on the catalogue's first row, and the record
        says so rather than leaving the key out (`shapes.md` §2-§3, D-29).
        """
        record = one_seed_run()
        self.assertIn(
            "game",
            record,
            "a run record carries `game`, the shape it played (records.md §12, "
            "shapes.md §3, D-29): %r" % (sorted(record),),
        )
        self.assertEqual(
            as_text(record["game"], "the record's game"),
            default_shape(),
            "a configuration naming no `game` is trained and evaluated on the catalogue's "
            "first shape, and the record names that shape instead of omitting the key "
            "(shapes.md §2-§3, D-29): %r" % (record["game"],),
        )
        pool = as_mapping(record["pool"], "'pool'")
        self.assertEqual(
            as_text(pool.get("game"), "the pool's game"),
            as_text(record["game"], "the record's game"),
            "the pool's record repeats the same shape, because a pool is one shape's and "
            "`records.md` §8 makes `game` a required field of it (records.md §8, "
            "shapes.md §3): %r vs %r" % (pool.get("game"), record["game"]),
        )
        header = as_mapping(record["header"], "'header'")
        self.assertEqual(
            header["game"],
            engine().game_config(default_shape()),
            "the header's game is the declared shape's row, read through "
            "engine.game_config for the shape the run played (surface.md §4.1, "
            "engine/surface.md §3, shapes.md §2)",
        )

    def test_trn_13_2_an_uncatalogued_game_is_refused_naming_it_and_the_declared_names(self):
        """TRN-13.2 a `game` outside the catalogue is refused, never defaulted.

        `shapes.md` §2: a name outside the catalogue is refused "naming it and the declared
        names -- never defaulted, because a default on a name is the silent substitution
        `e2e-surface.md` §2 forbids".  The declaration reads at the configuration
        (`records.md` §2) and at a variant entry, so both levels are refused, each naming
        the value it saw (`shapes.md` §3, D-13, D-29).
        """
        declared = (default_shape(), second_shape())
        configuration = with_game(no_limit_configuration(), INVENTED_SHAPE)
        self.refuse(
            lambda: training().run(configuration, seeds=(SHAPE_SEED,), budget=SHAPE_BUDGET),
            "UnknownShape",
            groups=((INVENTED_SHAPE,), declared, ("not one of the declared shapes",)),
            label="a configuration whose `game` is %r" % (INVENTED_SHAPE,),
        )
        entry_level = with_entry_game(no_limit_configuration(), INVENTED_SHAPE)
        # ... the entry's declaration is refused at the same place, and the configuration
        # it belongs to declares a catalogued one, so only the entry can be the source.
        entry_level.pop("game", None)
        self.refuse(
            lambda: training().run(
                entry_level, seeds=(SHAPE_SEED,), budget=SHAPE_BUDGET
            ),
            "UnknownShape",
            groups=((INVENTED_SHAPE,), declared),
            label="a variant entry whose `game` is %r" % (INVENTED_SHAPE,),
        )

    def test_trn_13_7_game_reads_at_either_level_and_absence_is_the_default(self):
        """TRN-13.7 `game` at the configuration and at its entry are one declaration.

        The shape is a declaration a configuration carries at either level, exactly as
        `learning_rule` and `utility` are (`docs/L2/training/declarations.md` §1,
        `records.md` §2): a configuration whose **entry** names the second shape reaches
        the same shape a configuration naming it at its own level does, and a configuration
        naming it nowhere is on the default (`shapes.md` §3, D-29).
        """
        entry_level = with_entry_game(
            with_game(no_limit_configuration(), default_shape()), second_shape()
        )
        entry_level.pop("game", None)
        self.assertEqual(
            as_text(
                entry_level["variants"][0]["game"], "the entry's declared game"
            ),
            second_shape(),
            "the invented fixture declares the shape on its entry, so the case reads the "
            "level it means to read (%r)" % (entry_level["variants"][0]["game"],),
        )
        # Resolving is not training: the same declaration read at the entry reaches the
        # same shape, which is what the record and the pool then repeat (shapes.md §3).
        run = training().run(
            entry_level, seeds=(SHAPE_SEED,), budget=SHAPE_BUDGET
        )
        self.assertEqual(
            as_text(run["game"], "the record's game"),
            second_shape(),
            "a shape declared at the variant entry is the shape the run played, because "
            "the key reads at either level and never only at the configuration "
            "(records.md §2, shapes.md §3, D-29): %r" % (run["game"],),
        )


class ShapeInTheHandCase(TrainingCase):
    """TRN-13.3, TRN-13.5 -- the shape reaches the hand and the head."""

    def test_trn_13_3_the_chips_in_play_are_the_runs_own_shapes(self):
        """TRN-13.3 the conservation guard is 40 chips, or the shape's own total.

        `shapes.md` §2: the chips in play are the shape's own total, `pot + sum(stacks)` at
        every decision, so 40 in the default shape and 200 on the second.  The transition
        step's guard therefore reads **the run's** shape and not the engine's default: a
        no-limit decision totals 200 and the default's guard refuses it naming both totals
        (`episode.md` §3, `reward.md` §4, `utilities.md` §4, ASM-28, D-29).
        """
        chips_in_play = self.internal("episode", "_chips_in_play")
        conserve = error_class("ChipConservationBroken")
        default_game = shaped_game_config(default_shape())
        second_game = shaped_game_config(second_shape())
        self.assertEqual(
            int(default_game["starting_stack"]),
            20,
            "the default shape deals twenty-chip stacks, which is ASM-6's game "
            "(shapes.md §2): %r" % (default_game["starting_stack"],),
        )
        self.assertEqual(
            int(second_game["starting_stack"]),
            100,
            "the second shape deals hundred-chip stacks, so its chips in play are 200 "
            "(shapes.md §2, sizing.md §5): %r" % (second_game["starting_stack"],),
        )
        for shape, expected in ((default_shape(), 40.0), (second_shape(), 200.0)):
            episode = shaped_episode(shape)
            decisions = decisions_of(episode)
            self.assertTrue(
                decisions,
                "a hand has at least one decision, so the guard has one to read "
                "(records.md §5): shape %r" % (shape,),
            )
            total, stack = chips_in_play(decisions[0], episode["seed"], 0, shape)
            self.assertEqual(
                float(total),
                expected,
                "the chips in play on the shape %r are that shape's total, and the guard "
                "reads the run's own shape rather than engine.game_config()'s default "
                "(shapes.md §2, utilities.md §4, D-29): %r" % (shape, total),
            )
            self.assertEqual(
                float(stack),
                float(shaped_game_config(shape)["starting_stack"]),
                "the starting stack the guard returns is that shape's, because it is the "
                "normaliser the shortfall utility divides by (utility.md §1, D-20): %r"
                % (stack,),
            )
        # The two shapes' readouts are not interchangeable, and the guard says so by name.
        no_limit_decision = decisions_of(shaped_episode(second_shape()))[0]
        with self.assertRaises(
            conserve,
            msg="a 200-chip readout read against the default shape's 40 is refused, "
                "naming the hand and both totals (utilities.md §4, ASM-28)",
        ):
            chips_in_play(
                no_limit_decision, shaped_episode(second_shape())["seed"], 0,
                default_shape(),
            )
        default_decision = decisions_of(shaped_episode(default_shape()))[0]
        with self.assertRaises(
            conserve,
            msg="and a 40-chip readout read against the second shape's 200 is refused "
                "the same way (utilities.md §4, ASM-28)",
        ):
            chips_in_play(
                default_decision, shaped_episode(default_shape())["seed"], 0,
                second_shape(),
            )

    def test_trn_13_5_the_head_is_as_wide_as_the_shapes_vocabulary(self):
        """TRN-13.5 a six-index mask is the second shape's learner's, not the first's.

        `sizing.md` §6: the head's width is the shape's descriptor count, so a learner of
        the six-descriptor shape takes indices `0..5` while the default shape's takes
        `0..2`.  The mask is the observable: `agents.act` refuses an index its shape's
        vocabulary does not declare, so the same six-index mask is one learner's legal
        decision set and the other's refusal — and the parameter count follows the head
        (`agents/surface.md` §4-§5, `shapes.md` §2, D-29).
        """
        vocabulary = shaped_vocabulary(second_shape())
        self.assertEqual(
            sorted(vocabulary),
            [0, 1, 2, 3, 4, 5],
            "the second shape declares six indices in its own order (shapes.md §2, "
            "sizing.md §3): %r" % (vocabulary,),
        )
        self.assertEqual(
            len(shaped_vocabulary(default_shape())),
            3,
            "and the default shape declares three, so the two heads are two widths "
            "(sizing.md §6): %r" % (shaped_vocabulary(default_shape()),),
        )
        encoder = features().build_encoder("flat-numeric", shape=second_shape())
        spec = {
            "backend": "numpy",
            "architecture": {
                "kind": "naive-stack",
                "width": 36,
                "depth": 2,
                "sparsity": 0.0,
                "residual": False,
            },
            "seed": SHAPE_SEED,
            "encoder": encoder,
            "game": second_shape(),
        }
        six = agents().build_learner(dict(spec))
        three = agents().build_learner(
            dict(spec, encoder=features().build_encoder("flat-numeric"),
                 game=default_shape())
        )
        observation = as_sequence(
            features().encode(encoder, decisions_of(shaped_episode(second_shape()))[0]["readout"]),
            "one observation",
        )
        mask = (0, 1, 2, 3, 4, 5)
        decision = as_mapping(
            agents().act(six, observation, mask), "a decision"
        )
        self.assertIn(
            int(decision["action"]),
            list(mask),
            "a six-descriptor learner decides from a six-index mask, so its head is the "
            "shape's width (sizing.md §6, agents/surface.md §4, D-29): %r" % (decision,),
        )
        with self.assertRaises(
            Exception,
            msg="the default shape's learner refuses the same six-index mask, because "
                "its vocabulary is three (sizing.md §6, agents/surface.md §6)",
        ):
            agents().act(three, observation, mask)
        self.assertGreater(
            int(agents().param_count(six)),
            int(agents().param_count(three)),
            "the six-wide head is more parameters than the three-wide one at one "
            "architecture, so the count follows the shape (sizing.md §6, ASM-10): %r vs %r"
            % (agents().param_count(six), agents().param_count(three)),
        )
        self.assertLess(
            abs(int(agents().param_count(six)) - PARAM_BUDGET),
            abs(int(agents().param_count(three)) - PARAM_BUDGET) + PARAM_BUDGET,
            "the second shape's head is a matched-capacity question and not a different "
            "model class, so its count stays inside the declared budget's own order of "
            "magnitude (ASM-10, sizing.md §6): %r" % (agents().param_count(six),),
        )


class NoLimitRunCase(TrainingCase):
    """TRN-13.4 -- a `no-limit-100` run trains end to end."""

    def test_trn_13_4_a_no_limit_run_trains_and_passes_end_to_end(self):
        """TRN-13.4 a six-descriptor run completes: curves, snapshots, a pass, six indices.

        `shapes.md` §1: the second shape is reached the way any configuration outside the
        registry is reached, as a value through `training.run`, so nothing about the loop is
        conditional on it.  The run therefore trains, snapshots, saves and passes exactly as
        a default-shape run does, and every artefact it produces is the shape's: the
        header's vocabulary is six descriptors, the pass's decisions are six-index ones with
        a raise resolved to an amount in the shape's own interval, and the curve closes at
        the declared interval (`sizing.md` §5-§6, `ladder.md` §1, FAM-15, D-29).
        """
        record = no_limit_run()
        self.assertEqual(
            as_text(record["game"], "the record's game"),
            second_shape(),
            "the run's record names the shape it played (records.md §12, shapes.md §3): %r"
            % (record["game"],),
        )
        vocabulary = shaped_vocabulary(second_shape())
        header = as_mapping(record["header"], "'header'")
        declared = as_mapping(header["action space"], "the header's action space")
        self.assertEqual(
            {int(index): str(name) for index, name in declared.items()},
            vocabulary,
            "the header's action space is the shape's six descriptors in its declared "
            "order, and not the default shape's three (surface.md §4.1, sizing.md §3, "
            "D-29): %r" % (declared,),
        )
        self.assertEqual(
            int(header["game"]["starting_stack"]),
            100,
            "the header's game is the second shape's row, so a reader of the record alone "
            "sees a 100-chip game (surface.md §4.1, shapes.md §2): %r"
            % (header["game"]["starting_stack"],),
        )
        variant = as_text(record["variants"][0]["name"], "the variant's name")
        curve = as_mapping(record["curves"], "'curves'")[variant]
        seed_key = str(SHAPE_SEED)
        points = as_mapping(curve[seed_key], "one seed's curve")
        self.assertEqual(
            len(as_sequence(points["td_error"], "the curve's signal")),
            SNAPSHOTS,
            "the curve closes at the ten snapshot intervals, one signal per point, on the "
            "second shape as on the first (curves.md §2, ASM-18): %r"
            % (len(points["td_error"]),),
        )
        self.assertEqual(
            [int(sample) for sample in as_sequence(points["samples"], "the sample axis")],
            [k * max(1, SHAPE_BUDGET // SNAPSHOTS) for k in range(1, SNAPSHOTS + 1)],
            "and its axis is `budget // 10` apart, which is the interval the run used and "
            "not the interval the configuration declared (curves.md §2, loop.md §2, "
            "ASM-18): %r" % (points["samples"],),
        )
        written = as_mapping(
            as_mapping(record["checkpoints"], "'checkpoints'")[variant][seed_key],
            "one pair's checkpoints",
        )
        self.assertTrue(
            as_sequence(written["snapshots"], "the retained snapshots"),
            "the pair retains its snapshot window, so the run wrote artefacts of the "
            "second shape (checkpoints.md §3, ASM-18): %r" % (written,),
        )
        block = greedy_block(record, variant, SHAPE_SEED)
        decisions = [
            as_mapping(decision, "one decision record")
            for decision in as_sequence(block["decisions"], "the pass's decisions")
        ]
        self.assertTrue(
            decisions,
            "the pass retains decisions on the second shape too, and a twelve-hand budget "
            "at two to four decisions a hand yields several (sizing.md §4, ASM-38)",
        )
        for decision in decisions:
            index = as_int(decision["index"], "a decision's index")
            self.assertIn(
                index,
                list(vocabulary),
                "every retained index is one of the shape's six, so the pass decodes in the "
                "run's vocabulary and not the default shape's three (records.md §15, "
                "sizing.md §3, D-29): %r" % (decision,),
            )
            self.assertEqual(
                as_text(decision["descriptor"], "a decision's descriptor"),
                vocabulary[index],
                "the descriptor is the shape's name for that index (records.md §15, "
                "features/surface.md §9): %r" % (decision,),
            )
            self.assertIn(
                index,
                [int(member) for member in as_sequence(decision["legal"], "a mask")],
                "and it is one of that decision's own legal indices, so the six-mask and "
                "the six-index decision are the same vocabulary (records.md §15, "
                "features/surface.md §8): %r" % (decision,),
            )
            amount = decision["amount"]
            bounds = (decision["minimum"], decision["maximum"])
            if amount is None:
                self.assertEqual(
                    amount,
                    None,
                    "a fold or a check/call resolves no amount, whatever the shape's "
                    "raise interval at that decision was (sizing.md §2, records.md §5): %r"
                    % (decision,),
                )
                continue
            self.assertIsNotNone(
                bounds[0],
                "a decision that resolved an amount also carries the interval it was "
                "resolved between, because the amount is attributable only beside its "
                "bounds (sizing.md §2, records.md §15): %r" % (decision,),
            )
            self.assertLessEqual(
                float(bounds[0]),
                float(amount),
                "a resolved raise-to lies inside the interval the engine resolved it "
                "between, which is the shape's own legal range (sizing.md §2, "
                "records.md §15): %r" % (decision,),
            )
            self.assertLessEqual(
                float(amount),
                float(bounds[1]),
                "and never above the all-in raise-to the shape allows (sizing.md §2, "
                "shapes.md §2): %r" % (decision,),
            )


class ShapeInFairnessCase(TrainingCase):
    """TRN-13.6 -- `fairness` names the shape, and refuses a pair of two."""

    def test_trn_13_6_fairness_names_the_shape_and_refuses_a_pair_of_two(self):
        """TRN-13.6 the shape is a held constant, and two shapes are not a pair.

        `ladder.md` §4 holds "the game configuration ... identical for every rung, because
        every rung is one shape" and adds that "a pair on two shapes is refused rather than
        reported"; `shapes.md` §1 adds that a shape is never a rung's axis.  So the report
        names the shape it held constant and its vocabulary and game rows are that shape's,
        while a pair naming two shapes is refused with both (`shapes.md` §6, D-3, D-29).
        """
        report = as_mapping(
            training().fairness(training().rung("R1"), training().rung("R2")),
            "a fairness record",
        )
        constants = as_mapping(report["constants"], "'constants'")
        self.assertEqual(
            as_text(constants.get("shape"), "the shape held constant"),
            default_shape(),
            "the report names the shape the pair is on, as one of the things it holds "
            "constant (ladder.md §4, shapes.md §6, D-29): %r" % (constants.get("shape"),),
        )
        self.assertEqual(
            constants["action vocabulary"],
            shaped_vocabulary(default_shape()),
            "and its vocabulary row is that shape's, three descriptors on the default "
            "shape (fairness.md §4, features/surface.md §7): %r"
            % (constants["action vocabulary"],),
        )
        self.assertEqual(
            constants["game"],
            engine().game_config(default_shape()),
            "and its game row is engine.game_config of that shape, so a fixed-limit pair "
            "reports the mapping it has always reported (fairness.md §4, "
            "engine/surface.md §3, shapes.md §6)",
        )
        left = with_game(training().rung("R1"), default_shape())
        right = with_game(training().rung("R2"), second_shape())
        self.refuse(
            lambda: training().fairness(left, right),
            "PairDeclarationsDiffer",
            groups=((default_shape(),), (second_shape(),)),
            label="a pair whose two sides name two shapes",
            entry="fairness",
        )
        both_second = as_mapping(
            training().fairness(
                with_game(training().rung("R4"), second_shape()),
                with_game(training().rung("R4"), second_shape()),
            ),
            "a fairness record of a pair on the second shape",
        )
        second_constants = as_mapping(both_second["constants"], "'constants'")
        self.assertEqual(
            as_text(second_constants.get("shape"), "the shape held constant"),
            second_shape(),
            "and a pair both of whose sides name the second shape reports that shape, so "
            "the row is read and not defaulted (ladder.md §4, shapes.md §6, D-29): %r"
            % (second_constants.get("shape"),),
        )
        self.assertEqual(
            second_constants["action vocabulary"],
            shaped_vocabulary(second_shape()),
            "with the second shape's six descriptors in its own order (shapes.md §2, "
            "sizing.md §3): %r" % (second_constants["action vocabulary"],),
        )
        self.assertEqual(
            len(as_sequence(second_constants["readout facts"], "the readout facts")),
            11,
            "and the same eleven readout facts, because the two shapes share every fact "
            "of the readout and differ only in what they mean (e2e-surface.md §2, "
            "shapes.md §2): %r" % (second_constants["readout facts"],),
        )

    def test_trn_13_8_a_pair_that_names_no_shape_is_one_declaration(self):
        """TRN-13.8 two sides naming no shape are one shape, not two declarations.

        `shapes.md` §3: an absent `game` reads as the default shape, in a configuration and
        in a record alike.  Two registry rows name none, so they are one shape and a
        comparison between them is reportable — absence is not a difference and never a
        "no claim" that could not be compared (`docs/L2/training/declarations.md` §4,
        `fairness.md` §7, D-29).
        """
        report = as_mapping(
            training().fairness(training().rung("R4"), training().rung("R4")),
            "a fairness record of one rung against itself",
        )
        self.assertEqual(
            as_text(
                as_mapping(report["constants"], "'constants'").get("shape"),
                "the shape held constant",
            ),
            default_shape(),
            "two configurations naming no shape are both on the default shape, so their "
            "pair is a pair on one shape (shapes.md §3, fairness.md §7, D-29)",
        )
        self.assertEqual(
            [
                as_text(field, "a differing field")
                for field in as_sequence(
                    as_mapping(report["axis"], "'axis'")["differs"], "the differing fields"
                )
            ],
            [],
            "and the pair differs on nothing, because the shape is a constant and never "
            "an axis (ladder.md §4, shapes.md §1, D-29): %r"
            % (as_mapping(report["axis"], "'axis'")["differs"],),
        )
