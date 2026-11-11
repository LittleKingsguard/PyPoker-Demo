"""The one decision stream a run retains -- TRN-14.

`records.md` §15 fixes the block key by key and `sizing.md` §4 fixes its sample, its mode
and its bound; `D-28` fixes the negative half — **no training decision is retained**.  These
cases read the block the loop writes and nothing else: its keys and its mode, that it is
reproducible from the record's own tuple, that the hand bound is refused by name with the
counts **on the pass's own request** while a run above it completes over its own sample, that
a request which is not a positive integer is refused by name before a hand is dealt, that the
sample is the run's prefix hand for hand, that a run's record holds no log of the behaviour
policy anywhere but `greedy`, and that a default-shape record gained exactly the two keys
D-29 adds.

| Case | What it reads |
|---|---|
| TRN-14.1 | the block's five keys and its `mode == "off"`, per variant per seed |
| TRN-14.2 | one decision record's seven keys, its index, descriptor and bounds |
| TRN-14.3 | the sample: `hands` is `min(budget, 2,000)`, one net chip delta per hand |
| TRN-14.4 | two runs of one tuple reproduce one block, seed and all |
| TRN-14.5 | both bounds refused by name with their counts, and a 2,001-hand run that completes |
| TRN-14.6 | no training decision log anywhere in the record but `greedy` (D-28) |
| TRN-14.7 | a default-shape record gained exactly `game` and `greedy` and nothing else |
| TRN-14.8 | the prefix: hand *j* of the pass is the run's hand *j*, measured hand for hand |
| TRN-14.9 | the request: 0, a negative, a float, a string and a bool refused by name before a hand is dealt |

Every case states the design section whose claim it reads (`docs/L1/battery.md` §5,
`docs/L3/training/greedy.md` §4, D-36); none asserts a value a document leaves to the run
(`D-6`).
"""

import random

from _training_support import (  # noqa: E402  - the battery's own support module
    BASELINE_SEED,
    BLOCK_KEYS,
    DECISION_KEYS,
    OVER_BOUND_BUDGET,
    PREFIX_HANDS,
    PREFIX_LONGER_HANDS,
    PREFIX_SEED,
    RECORD_KEYS_BEFORE_SHAPES,
    REPLAY_HANDS,
    SHAPE_KEYS,
    TINY_BUDGET,
    TrainingCase,
    as_int,
    as_mapping,
    as_sequence,
    as_text,
    baseline_policy,
    checkpoint_block,
    custom_configuration,
    decision_logs,
    declared_greedy_bound,
    default_shape,
    evaluation,
    greedy_block,
    greedy_blocks,
    greedy_pool,
    internal_module,
    one_seed_run,
    pair_run,
    repeated_run,
    resolved,
    second_shape,
    shaped_vocabulary,
    third_shape,
    training,
)


class GreedyBlockCase(TrainingCase):
    """TRN-14.1 - TRN-14.3 -- the block, one decision, and the sample."""

    def test_trn_14_1_the_block_carries_five_keys_and_the_mode_off(self):
        """TRN-14.1 every variant × seed carries one block: `off`, its seed, hands, chips, log.

        `records.md` §15: `mode` (required — `off`; a block carrying any other value is
        refused by name), `seed` (the run seed the pass was played at), `hands` (the hands
        played), `net_chips` (one delta per hand) and `decisions` (the ordered records).
        `sizing.md` §4 makes the mode the policy's and never the schedule's, so every block
        of every variant at every seed says `off` and there is no second value a run writes
        (`docs/L3/training/greedy.md` §1-§2, ASM-38, D-29).
        """
        for record in (one_seed_run(), pair_run()):
            self.assertIn(
                "greedy",
                record,
                "a run record carries the pass under `greedy` (records.md §12, §15, "
                "D-29): %r" % (sorted(record),),
            )
            blocks = greedy_blocks(record)
            self.assertTrue(
                blocks,
                "one block per variant per seed, and a run declares at least one variant "
                "and one seed (records.md §15, ASM-38): %r" % (record["greedy"],),
            )
            expected = {
                (as_text(declared["name"], "a variant name"), int(seed))
                for declared in record["variants"]
                for seed in record["seeds"]
            }
            self.assertEqual(
                {(variant, seed) for variant, seed, _ in blocks},
                expected,
                "the block is keyed by variant and seed exactly as `curves` and "
                "`checkpoints` are, so a census can name the pair it reads "
                "(records.md §12, §15, L2 `surface.md` §4): %r" % (sorted(expected),),
            )
            for variant, seed, block in blocks:
                label = "the block of the variant %r at seed %r" % (variant, seed)
                self.assertEqual(
                    tuple(sorted(block)),
                    tuple(sorted(BLOCK_KEYS)),
                    "%s carries records.md §15's five keys and no sixth: %r"
                    % (label, sorted(block)),
                )
                self.assertEqual(
                    as_text(block["mode"], "the block's mode"),
                    "off",
                    "%s carries `mode: off`, and the mode is the policy's — the masked "
                    "maximum and the tie-break alone, with no generator drawn from "
                    "(records.md §15, sizing.md §4, ASM-38): %r" % (label, block["mode"]),
                )
                self.assertEqual(
                    int(block["seed"]),
                    int(seed),
                    "%s carries the run seed the pass was played at, so the block is "
                    "reproducible from the record (records.md §15, ASM-2): %r"
                    % (label, block["seed"]),
                )

    def test_trn_14_2_one_decision_record_carries_seven_keys_and_its_own_bounds(self):
        """TRN-14.2 a decision carries `index`, `descriptor`, three amounts, `legal`, `tie`.

        `records.md` §15's table: the chosen index and the descriptor it decodes to in the
        shape's declared order, the raise-to the engine resolved with the two bounds it was
        resolved between — all three null where no raise was legal — the decision's legal
        index set, so a census re-derives no mask, and the tie flag (`sizing.md` §2-§3,
        `records.md` §5).
        """
        record = one_seed_run()
        vocabulary = shaped_vocabulary(default_shape())
        seen = 0
        for variant, seed, block in greedy_blocks(record):
            for decision in as_sequence(block["decisions"], "a block's decisions"):
                decision = as_mapping(decision, "one decision record")
                label = "a decision of %r at seed %r" % (variant, seed)
                self.assertEqual(
                    tuple(sorted(decision)),
                    tuple(sorted(DECISION_KEYS)),
                    "%s carries records.md §15's seven keys and no eighth: %r"
                    % (label, sorted(decision)),
                )
                index = as_int(decision["index"], "a decision's index")
                self.assertIn(
                    index,
                    list(vocabulary),
                    "%s's index is one of the shape's declared indices (records.md §15, "
                    "sizing.md §3): %r" % (label, decision),
                )
                self.assertEqual(
                    as_text(decision["descriptor"], "a decision's descriptor"),
                    vocabulary[index],
                    "%s's descriptor is the shape's name for its index, so the record "
                    "carries both readings of one decision (records.md §15, "
                    "features/surface.md §9): %r" % (label, decision),
                )
                legal = [int(member) for member in as_sequence(decision["legal"], "a mask")]
                self.assertIn(
                    index,
                    legal,
                    "%s's index is one of its own legal indices, and the mask is recorded "
                    "so a census re-derives nothing (records.md §15, sizing.md §7): %r"
                    % (label, decision),
                )
                self.assertIsInstance(
                    decision["tie"],
                    bool,
                    "%s's `tie` is the flag the tie-break reports, and a flag is a bool "
                    "(records.md §15, sizing.md §3, `docs/L3/training/greedy.md` §2): %r"
                    % (label, decision),
                )
                amounts = (decision["amount"], decision["minimum"], decision["maximum"])
                if all(value is None for value in amounts):
                    self.assertEqual(
                        [decision["minimum"], decision["maximum"]],
                        [None, None],
                        "%s's three amount facts are null together exactly where no raise "
                        "was legal at that decision (sizing.md §2, records.md §5, §15): %r"
                        % (label, decision),
                    )
                elif decision["amount"] is None:
                    self.assertIsNotNone(
                        decision["minimum"],
                        "%s carries the raise interval whenever a raise was legal, even "
                        "where the seat folded or called and resolved no amount "
                        "(sizing.md §2, records.md §5, §15): %r" % (label, decision),
                    )
                    self.assertIsNotNone(
                        decision["maximum"],
                        "%s's interval has both bounds, and a raise-to lies between them "
                        "(sizing.md §2, records.md §5, §15): %r" % (label, decision),
                    )
                else:
                    self.assertLessEqual(
                        float(decision["minimum"]),
                        float(decision["amount"]),
                        "%s's amount lies inside its own bounds (sizing.md §2, "
                        "records.md §15): %r" % (label, decision),
                    )
                    self.assertLessEqual(
                        float(decision["amount"]),
                        float(decision["maximum"]),
                        "%s's amount is at most the all-in raise-to (sizing.md §2, "
                        "records.md §15): %r" % (label, decision),
                    )
                seen += 1
        self.assertGreaterEqual(
            seen,
            1,
            "a ten-hand pass at two to four decisions a hand retains several decisions, so "
            "the block is a sample and not an empty list (sizing.md §4, ASM-38)",
        )

    def test_trn_14_3_the_pass_plays_the_runs_own_sample(self):
        """TRN-14.3 `hands` is the **sample's** count, `min(budget, 2,000)`, with one delta per hand.

        `greedy.md` §1 and §4 and `records.md` §15: the pass plays one **sample** of the
        run's own hands, `S = min(budget, 2,000)`, and `hands` reports that sample's count —
        the budget at or below the bound, and exactly the bound above it.  So a ten-hand
        run's pass is ten hands and a 20,000-hand run's pass is 2,000 hands, and the record
        states the count it actually played rather than clamping anything: `net_chips`
        carries one delta per hand of that sample, so the pass's price can be recomputed
        (`sizing.md` §4, `records.md` §15, ASM-38, D-36).
        """
        record = one_seed_run()
        hands_bound = as_int(
            self.internal("greedy", "HANDS_BOUND"), "greedy.HANDS_BOUND"
        )
        self.assertEqual(
            hands_bound,
            2000,
            "the module's own `HANDS_BOUND` is the declared 2,000 sampled hands -- the name "
            "`docs/L3/training/README.md` §4 makes contract -- so the sample's rule reads one "
            "number and not a literal of this battery's (greedy.md §4, sizing.md §4): %r"
            % (hands_bound,),
        )
        self.assertEqual(
            hands_bound,
            as_int(
                internal_module("declarations").GREEDY_HANDS,
                "declarations.GREEDY_HANDS",
            ),
            "and it is `declarations.GREEDY_HANDS`, which is the **one** declaration of the "
            "bound: the rule is read off the declaration and never written down a second "
            "time, so the module and the declaration cannot drift apart (greedy.md §4, "
            "sizing.md §4, D-36): %r against %r"
            % (hands_bound, internal_module("declarations").GREEDY_HANDS),
        )
        self.assertEqual(
            int(record["budget"]),
            TINY_BUDGET,
            "the invented fixture runs at the battery's tiny budget, which the pass samples "
            "(%r)" % (record["budget"],),
        )
        for variant, seed, block in greedy_blocks(record):
            label = "the block of %r at seed %r" % (variant, seed)
            self.assertEqual(
                int(block["hands"]),
                int(record["budget"]),
                "%s plays the run's own sample and records the count it played: at or below "
                "the bound the sample rule is the **identity**, so the pass and the training "
                "sample are one size (greedy.md §1, §4, sizing.md §4, records.md §15): %r vs "
                "%r" % (label, block["hands"], record["budget"]),
            )
            self.assertEqual(
                as_int(block["hands"], "a block's hands"),
                min(int(record["budget"]), hands_bound),
                "%s's hand count is the sample's rule `min(budget, HANDS_BOUND)` and not the "
                "budget: the budget when it is at most the bound and exactly the bound above "
                "it, so `hands` is the sample's count and no sixth key states it "
                "(greedy.md §1, §4, sizing.md §4, records.md §15, ASM-38, D-36): %r against "
                "min(%r, %r)"
                % (label, block["hands"], record["budget"], hands_bound),
            )
            net = as_sequence(block["net_chips"], "the pass's per-hand chips")
            self.assertEqual(
                len(net),
                int(block["hands"]),
                "%s carries one net chip delta per hand it played, so the pass's price can "
                "be recomputed and not only quoted (records.md §15, ASM-23): %r deltas for "
                "%r hands" % (label, len(net), block["hands"]),
            )
            for value in net:
                self.assertIsInstance(
                    float(value),
                    float,
                    "%s's deltas are the learner's seat's net chips, one number per hand "
                    "(records.md §15, records.md §5): %r" % (label, value),
                )


class GreedyReproductionCase(TrainingCase):
    """TRN-14.4 -- one tuple, one block."""

    def test_trn_14_4_two_runs_of_one_tuple_reproduce_one_block(self):
        """TRN-14.4 the block is a function of the tuple, the seed and the model.

        `docs/L2/training/surface.md` §4 and ASM-2: one `(configuration, seed set, budget,
        pool membership)` gives one record twice.  The pass adds nothing to that tuple's
        determinism and takes nothing from it: it is played at the run's own seed, over the
        same hands and the same frozen pool, with `exploration="off"` so no generator is
        drawn from — which is why the block, and not only the curves, is reproducible
        (`sizing.md` §4, `records.md` §15, `docs/L3/training/greedy.md` §3).
        """
        first = one_seed_run()
        second = repeated_run()
        self.assertEqual(
            first["greedy"],
            second["greedy"],
            "two runs of one tuple reproduce one `greedy` block — the same seed, hands, "
            "chip deltas and ordered decisions — so the block is a function of the model, "
            "the sample and the pool (sizing.md §4, ASM-2, ASM-38, records.md §15)",
        )
        self.assertEqual(
            first["curves"],
            second["curves"],
            "and the curves they were trained to are the same curves, so the block's "
            "reproduction is the run's and not a coincidence of one sub-record "
            "(surface.md §4, FAM-4.7)",
        )
        other = training().run(
            training().rung("R1"), seeds=[TINY_BUDGET + 9000], budget=TINY_BUDGET
        )
        self.assertNotEqual(
            first["greedy"],
            other["greedy"],
            "a different run seed is a different sample and a different model, so its "
            "block is a different block and the reproduction above is not trivial "
            "(records.md §15, ASM-2, FAM-4.8)",
        )


class GreedyBoundCase(TrainingCase):
    """TRN-14.5 -- the bound is refused and never truncated."""

    def test_trn_14_5_both_bounds_are_refused_by_name_with_the_counts(self):
        """TRN-14.5 2,000 hands and one record bound per shape, refused with both numbers.

        `sizing.md` §4: "at most 2,000 hands and 24,000 decision records per variant per
        seed -- ... a pass that would exceed either bound is **refused, never truncated**,
        because a truncated log silently reports a different sample".  Both are refused with
        the count and the bound, and neither is clamped: the hand bound is on the **pass's
        own request**, which is the number `_pass` is asked to play, and the record bound is
        known only as the pass accumulates (`records.md` §15, ASM-38).

        The run-side refusal that stood here is **gone by design** (D-36): a budget above the
        bound is no longer a run this module refuses, because the per-pair step asks for
        `greedy._sample(budget)` and never for the budget, so a 2,001-hand run trains its
        2,001 hands and passes over its first 2,000.  The pass-side refusal is still driven —
        directly, above, through `_check_hands` — and the last block of this case runs the
        over-bound budget and asserts the sample it produced instead of the refusal it no
        longer makes (`greedy.md` §1, §4, `loop.md` §1 steps 1 and 8, `sizing.md` §4,
        D-36).

        `shapes.md` §8 makes the record bound the **shape's**: 1,000 × its history capacity,
        so 24,000 at the default shape, 66,000 on the two-seat uncapped one and 98,000 on
        the six-seat one, "refused beyond and never truncated".  The check reads that
        capacity through `declarations.greedy_decisions(shape)`, so this case drives the
        third number beside the default shape's and shows that the default shape's own bound
        did not widen when the bound became a function of the shape (`shapes.md` §8,
        ASM-38, ASM-42, `docs/L2/training/surface.md` §4, D-29, D-33).
        """
        check_hands = self.internal("greedy", "_check_hands")
        check_decisions = self.internal("greedy", "_check_decisions")
        hands_bound = as_int(self.internal("greedy", "HANDS_BOUND"), "greedy.HANDS_BOUND")
        decisions_bound = as_int(
            self.internal("greedy", "DECISIONS_BOUND"), "greedy.DECISIONS_BOUND"
        )
        where = "training.run of a variant"
        self.assertEqual(
            decisions_bound,
            24000,
            "the module's own `DECISIONS_BOUND` is still the default shape's 24,000 -- the "
            "name `docs/L3/training/README.md` §4 makes contract -- so a shape took the "
            "bound's argument and not its spelling (shapes.md §8, greedy.md §4, ASM-42): %r"
            % (decisions_bound,),
        )
        self.assertEqual(
            declared_greedy_bound(default_shape()),
            decisions_bound,
            "and it is the declaration's bound for the default shape, so the name and the "
            "shape's own number are one number (shapes.md §8, ASM-38, ASM-42): %r against %r"
            % (declared_greedy_bound(default_shape()), decisions_bound),
        )
        self.assertIsNone(
            check_hands(2000, "training.run of a variant"),
            "a pass of exactly the 2,000-hand bound is inside it and is not refused "
            "(sizing.md §4, ASM-38)",
        )
        self.assertIsNone(
            check_decisions(24000, where),
            "and a pass of exactly the 24,000-record bound is inside it (sizing.md §4, "
            "ASM-38)",
        )
        self.refuse(
            lambda: check_hands(OVER_BOUND_BUDGET, "training.run of a variant"),
            "GreedyPassRefused",
            groups=(("2001",), ("2000",)),
            label="a pass one hand above the hand bound",
        )
        # ... and the **sample** `loop` asks the pass for is `min(budget, HANDS_BOUND)`:
        # at or below the bound it is the budget, and above it it is the bound itself, so a
        # run never asks for a count the check above would refuse (greedy.md §1, §4, D-36).
        sample = self.internal("greedy", "_sample")
        self.assertEqual(
            as_int(sample(10), "greedy._sample(10)"),
            10,
            "a ten-hand budget is inside the hand bound, so the rule `min(budget, "
            "HANDS_BOUND)` is the identity there: the sample is the run's ten hands "
            "(greedy.md §1, §4, D-36): %r" % (sample(10),),
        )
        self.assertEqual(
            as_int(sample(2000), "greedy._sample(2000)"),
            hands_bound,
            "`_sample(2000) == HANDS_BOUND` -- 2,000 is the bound itself, which is **inside** "
            "it: a pass of exactly a bound is never refused, so the sample rule returns it "
            "unnarrowed (greedy.md §4, sizing.md §4, ASM-38, D-36): %r against %r"
            % (sample(2000), hands_bound),
        )
        self.assertEqual(
            as_int(sample(2001), "greedy._sample(2001)"),
            hands_bound,
            "one hand above the bound the sample is the bound and not the budget, so the "
            "rule `min(budget, HANDS_BOUND)` stops the pass at 2,000 hands and the run keeps "
            "training (greedy.md §1, §4, sizing.md §4, D-36): %r against %r"
            % (sample(2001), hands_bound),
        )
        self.assertEqual(
            as_int(sample(200000), "greedy._sample(200000)"),
            hands_bound,
            "and the catalogue's live 200,000-hand budget samples to the same 2,000 hands, "
            "which is the whole point of the rule: no run is refused for its budget "
            "(greedy.md §4, sizing.md §4, ASM-38, D-36): %r against %r"
            % (sample(200000), hands_bound),
        )
        self.refuse(
            lambda: check_decisions(24001, where),
            "GreedyPassRefused",
            groups=(("24001",), ("24000",)),
            label="a pass one record above the record bound",
        )
        # ... a pass on the default shape, asked for with the shape named, is the same
        # 24,000: no bound widened for the shape that had one.
        self.assertIsNone(
            check_decisions(24000, where, default_shape()),
            "a default-shape pass of exactly 24,000 records is inside its own bound too, so "
            "naming the shape changed no number for it (shapes.md §5, §8, ASM-38, ASM-42)",
        )
        self.refuse(
            lambda: check_decisions(24001, where, default_shape()),
            "GreedyPassRefused",
            groups=(("24001",), ("24000",), ("capacity of 24", "24 slots")),
            label="a default-shape pass one record above its own bound",
        )
        # ... and each uncapped shape bounds at 1,000 x its own capacity.
        self.assertEqual(
            declared_greedy_bound(second_shape()),
            66000,
            "the two-seat uncapped shape's bound is 66,000 records -- 1,000 x its 66-slot "
            "history capacity (shapes.md §8, ASM-42): %r"
            % (declared_greedy_bound(second_shape()),),
        )
        self.assertIsNone(
            check_decisions(66000, where, second_shape()),
            "a pass of exactly 66,000 records on that shape is inside its bound "
            "(shapes.md §8, sizing.md §4, ASM-38)",
        )
        self.refuse(
            lambda: check_decisions(66001, where, second_shape()),
            "GreedyPassRefused",
            groups=(("66001",), ("66000",), ("capacity of 66", "66 slots")),
            label="a two-seat uncapped pass one record above its own bound",
        )
        self.assertEqual(
            declared_greedy_bound(third_shape()),
            98000,
            "and the six-seat shape's is 98,000 -- 1,000 x its own 98-slot capacity, which "
            "its betting and not the fixed-limit cap derives (shapes.md §8, ASM-42, "
            "ASM-44, D-33): %r" % (declared_greedy_bound(third_shape()),),
        )
        self.assertIsNone(
            check_decisions(98000, where, third_shape()),
            "a pass of exactly 98,000 records on the six-seat shape is inside its bound, so "
            "the bound is the uncapped shape's own and not the default's "
            "(shapes.md §8, ASM-38, ASM-42)",
        )
        refusal = self.refuse(
            lambda: check_decisions(98001, where, third_shape()),
            "GreedyPassRefused",
            groups=(("98001",), ("98000",), ("capacity of 98", "98 slots")),
            label="a six-seat pass one record above its own bound",
        )
        message = str(refusal)
        self.assertIn(
            third_shape(),
            message,
            "and the refusal names the shape whose capacity set the bound, so a caller reads "
            "which game's bound it crossed (shapes.md §8, records.md §15, ASM-38, "
            "ASM-42): %r" % (message,),
        )
        # ... and the run does **not** refuse an over-bound budget: the per-pair step asks
        # the pass for `_sample(budget)` and never for the budget, so 2,001 hands train and
        # the pass replays the run's first 2,000 of them.  The refusal this case used to
        # drive here is gone by design (D-36); the refusal that stays is the pass's own,
        # driven directly above, and what this block asserts is the sample the run produced
        # (greedy.md §1, §4, loop.md §1 steps 1 and 8, sizing.md §4, ASM-38, D-36).
        configuration = custom_configuration(samples=OVER_BOUND_BUDGET)
        record = training().run(
            configuration,
            seeds=[TINY_BUDGET + 9100],
            budget=OVER_BOUND_BUDGET,
        )
        self.assertEqual(
            int(record["budget"]),
            OVER_BOUND_BUDGET,
            "a budget one hand above the hand bound is a run this module accepts and "
            "records: `budget` is the hands it trained, 2,001, and no bound is checked at "
            "resolve (greedy.md §4, loop.md §1 step 1, sizing.md §4, D-36): %r"
            % (record["budget"],),
        )
        blocks = greedy_blocks(record)
        self.assertTrue(
            blocks,
            "and the run retains its pass for every variant and seed it trained "
            "(records.md §12, §15): %r" % (record.get("greedy"),),
        )
        for variant, seed, block in blocks:
            label = "the block of %r at the %r-hand run's seed %r" % (
                variant, OVER_BOUND_BUDGET, seed,
            )
            self.assertEqual(
                as_int(block["hands"], "a block's hands"),
                hands_bound,
                "%s is the **sample** and not the budget: `min(budget, HANDS_BOUND)` is "
                "2,000 above the bound, so the pass stops at the bound while the run trained "
                "2,001 hands (greedy.md §1, §4, sizing.md §4, records.md §15, D-36): %r "
                "against %r" % (label, block["hands"], hands_bound),
            )
            self.assertEqual(
                len(as_sequence(block["net_chips"], "the pass's per-hand chips")),
                hands_bound,
                "%s carries one net chip delta per hand of that sample and not per hand of "
                "the run, so `budget` and `hands` together state the share the block covers "
                "(records.md §15, ASM-23, greedy.md §4, D-36): %r deltas"
                % (label, len(as_sequence(block["net_chips"], "the chips"))),
            )
            self.assertEqual(
                as_text(block["mode"], "the block's mode"),
                "off",
                "%s is still the exploration-off pass -- the masked maximum and the "
                "tie-break alone, with no generator drawn from (records.md §15, sizing.md "
                "§4, ASM-38): %r" % (label, block["mode"]),
            )
            self.assertEqual(
                tuple(sorted(block)),
                tuple(sorted(BLOCK_KEYS)),
                "%s carries records.md §15's five keys and **no sixth**: the sample's count "
                "is `hands` and the record's `budget` is the run's, so nothing else states "
                "the sample (greedy.md §2, §4, D-36): %r" % (label, sorted(block)),
            )
            self.assertLessEqual(
                len(as_sequence(block["decisions"], "the pass's ordered decisions")),
                decisions_bound,
                "%s stays inside the default shape's record bound of 24,000 -- 1,000 x its "
                "24-slot history capacity -- as the pass accumulates (records.md §15, "
                "shapes.md §8, ASM-38, ASM-42): %r records"
                % (label, len(as_sequence(block["decisions"], "the decisions"))),
            )


class GreedyRequestCase(TrainingCase):
    """TRN-14.9 -- the request itself: a pass asked for anything but a positive integer."""

    def test_trn_14_9_a_request_that_is_not_a_positive_integer_is_refused(self):
        """TRN-14.9 0, a negative, a float, a string and a bool refused, naming the request.

        `errors.md` §4 records `GreedyPassRefused`'s **third shape**: a request that is not a
        positive integer — a `bool`, a float, a string, 0 or a negative — is refused naming
        the request as it was given and the contract it breaks, `a pass plays at least 1 hand
        and at most 2000`, and the refusal arrives **before the pass deals its first hand**,
        so no block is ever returned whose `hands` is not a positive integer equal to
        `len(net_chips)` (`greedy.md` §4, D-36).  That rule is the **lower** end of the same
        hand bound `TRN-14.5` drives at its upper end: 2,000 hands are inside it and 2,001 are
        refused with the same class, so the bound is a closed interval of hand counts and not
        a ceiling with a floor nobody checked (`sizing.md` §4, `records.md` §15, ASM-38,
        D-36).

        The guard is also what keeps `int()` from manufacturing a block.  Without it a
        `3.7`-hand request would truncate to a three-hand block whose `hands` says three while
        the caller asked for 3.7, and a `0` or a negative request would return a block whose
        `hands` is not a positive integer and whose `net_chips` is empty — a block
        contradicting the record it sits in (`greedy.md` §1, §4, `records.md` §15, D-36).

        Each refusal is measured twice: the class exactly and the message's three parts — the
        request as given, the lower end of the contract and the bound — through `self.refuse`,
        and `random`'s global stream unmoved through `self.assert_no_hand_dealt`, which is
        what makes "refused before the pass deals its first hand" a measurement and not a
        reading of the code (`errors.md` §3, `seeds.md` §1, ASM-2).  The same requests are
        then handed to `_check_hands` directly, so the seam `_pass` raises through is shown to
        refuse them itself (`docs/L3/training/README.md` §4).  The contract's other side is
        asserted beside them and is not narrowed: a **one-hand** `_pass` returns a block whose
        `hands` is a positive `int` equal to one with exactly one chip delta, and `_sample`'s
        rule still reads `_sample(1) == 1` and `_sample(HANDS_BOUND + 1) == HANDS_BOUND` —
        the ladder `TRN-14.5` asserts in full (`greedy.md` §1, §4, `records.md` §15, D-36).
        """
        greedy_pass = self.internal("greedy", "_pass")
        check_hands = self.internal("greedy", "_check_hands")
        sample = self.internal("greedy", "_sample")
        hands_bound = as_int(self.internal("greedy", "HANDS_BOUND"), "greedy.HANDS_BOUND")
        pool = greedy_pool()
        shape = default_shape()
        # The spelling `src/training/loop.py` gives `_pass`'s last argument, so every message
        # read below is the one a run would emit if it could ask the pass for such a count
        # (`errors.md` §4, D-36).
        where = "training.run at the variant 'naive-numeric' and seed %r" % PREFIX_SEED
        for request in (0, -3, 3.7, "12", True):
            label = "the pass asked for the request %r" % (request,)
            policy = baseline_policy("always-call", BASELINE_SEED)
            before = random.getstate()
            self.refuse(
                lambda request=request: greedy_pass(
                    pool, shape, PREFIX_SEED, request, policy, where
                ),
                "GreedyPassRefused",
                groups=(
                    (str(request),),
                    ("at least 1", "at least one"),
                    (str(hands_bound),),
                ),
                label=label,
            )
            self.assert_no_hand_dealt(before, label)
        # ... and the check the pass raises its own request through refuses them itself, so a
        # request the pass would truncate is no narrower than the seam's (`greedy.md` §4).
        for request in (0, -3):
            label = "greedy._check_hands asked for the request %r" % (request,)
            before = random.getstate()
            self.refuse(
                lambda request=request: check_hands(request, where),
                "GreedyPassRefused",
                groups=(
                    (str(request),),
                    ("at least 1", "at least one"),
                    (str(hands_bound),),
                ),
                label=label,
            )
            self.assert_no_hand_dealt(before, label)
        # ... while one hand is inside the bound, and the block it yields states the count it
        # played: the guard refuses a request and not a small sample (`greedy.md` §4, D-36).
        one_hand = greedy_pass(
            pool,
            shape,
            PREFIX_SEED,
            1,
            baseline_policy("always-call", BASELINE_SEED),
            where,
        )
        self.assertEqual(
            as_int(one_hand["hands"], "the one-hand pass's hands"),
            1,
            "a pass asked for **one** hand is the least request the contract admits, and it "
            "reports that hand as a positive integer -- so the refusal above is the request's "
            "and no sample smaller than the bound is refused with it (greedy.md §4, "
            "sizing.md §4, records.md §15, ASM-38, D-36): %r" % (one_hand["hands"],),
        )
        one_chips = as_sequence(one_hand["net_chips"], "the one-hand pass's per-hand chips")
        self.assertEqual(
            len(one_chips),
            1,
            "and it carries exactly one net chip delta, so `hands` and `len(net_chips)` are one "
            "number at the guard's own floor as they are at a ten-hand sample -- the invariant "
            "the refusal exists to keep (records.md §15, greedy.md §4, D-36): %r deltas"
            % (len(one_chips),),
        )
        # ... and the rule the loop feeds the pass never asks for a count the guard refuses:
        # `min(1, HANDS_BOUND)` is one hand and `min(HANDS_BOUND + 1, HANDS_BOUND)` is the
        # bound, so both ends of the sample rule land inside the closed interval `TRN-14.5`
        # walks hand by hand (`greedy.md` §1, §4, D-36).
        low = as_int(sample(1), "greedy._sample(1)")
        high = as_int(sample(hands_bound + 1), "greedy._sample(HANDS_BOUND + 1)")
        self.assertEqual(
            low,
            1,
            "`_sample(1) == 1`: the rule `min(budget, HANDS_BOUND)` is the identity below the "
            "bound, so the least sample a run can ask for is one hand and not zero "
            "(greedy.md §4, sizing.md §4, D-36): %r" % (low,),
        )
        self.assertEqual(
            high,
            hands_bound,
            "and `_sample(HANDS_BOUND + 1) == HANDS_BOUND`, the sample's rule at its other "
            "end -- the full ladder over 10, 2,000, 2,001 and 200,000 hands is `TRN-14.5`'s "
            "and is not repeated here (greedy.md §1, §4, sizing.md §4, ASM-38, D-36): %r "
            "against %r" % (high, hands_bound),
        )


class GreedyIsTheOnlyLogCase(TrainingCase):
    """TRN-14.6, TRN-14.7 -- no training log, and exactly two new keys."""

    def test_trn_14_6_the_record_holds_no_decision_log_but_the_greedy_block(self):
        """TRN-14.6 `greedy` is the **only** decision stream a run retains (D-28).

        `sizing.md` §4: "Training decisions are **not** retained: the loop keeps its batch
        aggregate and the curve, and a log of the behaviour policy would be a log of the
        exploration schedule -- the defect D-28 recorded as fatal, since at 1,000 hands per
        seed almost the whole sample sits on the epsilon ramp".  So a run record's tree
        holds an ordered decision log in exactly one place, and it is the pass
        (`records.md` §12, §15, ASM-38, D-28).
        """
        for record in (one_seed_run(), pair_run()):
            found = decision_logs(record)
            self.assertTrue(
                found,
                "the record does carry the one stream it retains, so the negative claim "
                "below is not vacuous (records.md §15, D-28): %r" % (found,),
            )
            for path in found:
                self.assertEqual(
                    path[0],
                    "greedy",
                    "the only decision log in a run record is the greedy pass, and this "
                    "one is at %r: a log of the behaviour policy is the defect D-28 records "
                    "as fatal (sizing.md §4, ASM-38, D-28)" % (path,),
                )
            self.assertEqual(
                len(found),
                len(greedy_blocks(record)),
                "one log per variant per seed and no second log: the record holds %r logs "
                "for %r blocks (records.md §15, D-28)"
                % (len(found), len(greedy_blocks(record))),
            )
            for key in record:
                self.assertNotIn(
                    "history",
                    str(key).lower(),
                    "no key of a run record holds a hand's history, because the training "
                    "loop discards the batch it learned from (sizing.md §4, D-28): %r"
                    % (key,),
                )

    def test_trn_14_7_a_default_shape_record_gained_exactly_two_keys(self):
        """TRN-14.7 a default-shape record is the sixteen keys plus `game` and `greedy`.

        `shapes.md` §5 is the constraint the whole design is written under: "every
        widening's absence reproduces today's value".  D-29 adds two keys to the run record
        and no third, so a default-shape run's record is the sixteen it carried before plus
        exactly those two — which is the whole of what `verify.py`'s `record_keys` exemption
        carries, and the reason a fixed-limit record stays readable
        (`records.md` §12, `shapes.md` §3, §5, D-29).
        """
        record = one_seed_run()
        keys = {str(key) for key in record}
        self.assertEqual(
            keys - set(RECORD_KEYS_BEFORE_SHAPES),
            set(SHAPE_KEYS),
            "a default-shape run's record gains exactly `game` and `greedy` and nothing "
            "else, so no key moved and no key was renamed (shapes.md §5, records.md §12, "
            "D-29): gained %r, lost %r"
            % (sorted(keys - set(RECORD_KEYS_BEFORE_SHAPES)),
               sorted(set(RECORD_KEYS_BEFORE_SHAPES) - keys)),
        )
        self.assertEqual(
            set(RECORD_KEYS_BEFORE_SHAPES) - keys,
            set(),
            "and it lost none: every key a fixed-limit record carried is still there "
            "(shapes.md §5, records.md §12, D-29): %r"
            % (sorted(set(RECORD_KEYS_BEFORE_SHAPES) - keys),),
        )
        # The sub-records the two keys touch are the two D-29 names, and the pool block
        # repeats the shape because `records.md` §8 makes it a required field of a pool.
        self.assertEqual(
            as_text(record["game"], "the record's game"),
            default_shape(),
            "the first of the two keys is the default shape's name, not an absent key "
            "(records.md §12, shapes.md §3, D-29): %r" % (record["game"],),
        )
        self.assertEqual(
            as_text(
                as_mapping(record["pool"], "'pool'").get("game"), "the pool's game"
            ),
            as_text(record["game"], "the record's game"),
            "and the pool record repeats it, so a run, a pool and a matrix can be held to "
            "one shape (records.md §8, protocol.md §1, D-29)",
        )


class GreedyPrefixCase(TrainingCase):
    """TRN-14.8 -- hand *j* of the pass is the run's hand *j*."""

    def test_trn_14_8_hand_j_of_the_pass_is_the_runs_hand_j(self):
        """TRN-14.8 a pass hand does not depend on how many hands were asked for.

        What the first half of this case measures is the pass's **hand-independence**: one
        `_pass` is driven twice at one seed and one pool, asked for `PREFIX_HANDS = 4` hands
        and then for `PREFIX_LONGER_HANDS = 7`, and every hand's deal seed, opponent draw seed
        and learner seat are derivations of `(seed, j)` and of the shape and of nothing else
        (`seeds.md` §2, `episode.md` §1, ASM-2) — so the seven-hand pass replays the four-hand
        one's hands *first* and *identically*.  The chip deltas agree hand for hand and the
        ordered decision log of the shorter pass is the leading slice of the longer one's,
        because decisions are appended hand by hand and a prefix of hands can only append the
        same records in the same order.  That is `greedy.md` §1's "hand *j* of the pass is the
        run's own hand *j*" made into a **necessary** condition and not the identity itself:
        it shows that asking for more hands does not move the hands already played, which is
        what lets the sample be a function of `(seed, j)` alone; the identity is measured
        below, against the run's own block (`records.md` §15, `greedy.md` §1, §4, ASM-2,
        D-36).

        Each `_pass` is handed a **freshly built** policy of one declaration —
        `baseline_policy("always-call", BASELINE_SEED)` — and never one shared instance: a
        pinned baseline is a policy object a pass walks hand by hand, so a `random` baseline
        would hand the longer pass a different draw sequence and the comparison below would
        measure the object rather than the sample (`e2e-surface.md` §3.3, `greedy.md` §1).
        """
        greedy_pass = self.internal("greedy", "_pass")
        pool = greedy_pool()
        shape = default_shape()
        where = "training.run of a variant"
        shorter = greedy_pass(
            pool,
            shape,
            PREFIX_SEED,
            PREFIX_HANDS,
            baseline_policy("always-call", BASELINE_SEED),
            where,
        )
        longer = greedy_pass(
            pool,
            shape,
            PREFIX_SEED,
            PREFIX_LONGER_HANDS,
            baseline_policy("always-call", BASELINE_SEED),
            where,
        )
        self.assertEqual(
            tuple(sorted(as_mapping(shorter, "the shorter pass's block"))),
            tuple(sorted(BLOCK_KEYS)),
            "the shorter pass returns records.md §15's block and no sixth key, so the two "
            "blocks compared here are the ones a run records (greedy.md §2, records.md §15): "
            "%r" % (sorted(shorter),),
        )
        self.assertEqual(
            tuple(sorted(as_mapping(longer, "the longer pass's block"))),
            tuple(sorted(BLOCK_KEYS)),
            "and so does the longer one, so neither block compared below is a container the "
            "design does not state (greedy.md §2, records.md §15): %r" % (sorted(longer),),
        )
        self.assertEqual(
            as_int(shorter["hands"], "the shorter pass's hands"),
            PREFIX_HANDS,
            "a pass asked for %r hands plays %r hands and reports that count, so the sample "
            "is the caller's request inside the bound (greedy.md §1, §4, ASM-38): %r"
            % (PREFIX_HANDS, PREFIX_HANDS, shorter["hands"]),
        )
        self.assertEqual(
            as_int(longer["hands"], "the longer pass's hands"),
            PREFIX_LONGER_HANDS,
            "and a pass asked for %r hands plays %r, so the two passes are one sample's two "
            "lengths and not one call repeated (greedy.md §1, §4, ASM-38): %r"
            % (PREFIX_LONGER_HANDS, PREFIX_LONGER_HANDS, longer["hands"]),
        )
        short_chips = as_sequence(shorter["net_chips"], "the shorter pass's per-hand chips")
        long_chips = as_sequence(longer["net_chips"], "the longer pass's per-hand chips")
        short_decisions = as_sequence(
            shorter["decisions"], "the shorter pass's ordered decisions"
        )
        long_decisions = as_sequence(
            longer["decisions"], "the longer pass's ordered decisions"
        )
        self.assertGreater(
            len(short_chips),
            0,
            "the case must read a sample with hands in it, or the prefix below would hold of "
            "two empty lists and measure nothing (battery.md §2, greedy.md §1): %r"
            % (short_chips,),
        )
        self.assertEqual(
            len(short_chips),
            PREFIX_HANDS,
            "one net chip delta per hand played: the shorter pass played %r hands, so it "
            "carries %r deltas and a missing hand would be a different sample "
            "(records.md §15, ASM-23): %r" % (PREFIX_HANDS, PREFIX_HANDS, len(short_chips)),
        )
        self.assertEqual(
            len(long_chips),
            PREFIX_LONGER_HANDS,
            "and the longer pass carries one delta per hand it played, %r of them "
            "(records.md §15, ASM-23): %r" % (PREFIX_LONGER_HANDS, len(long_chips)),
        )
        self.assertEqual(
            long_chips[:PREFIX_HANDS],
            short_chips,
            "hand *j* of the pass is the run's own hand *j*, so the longer pass's first %r "
            "chip deltas are the shorter pass's deltas exactly: a differing delta would mean "
            "the two passes were dealt different hands at one seed (greedy.md §1, §4, "
            "seeds.md §2, ASM-2, D-36): %r against %r"
            % (PREFIX_HANDS, long_chips[:PREFIX_HANDS], short_chips),
        )
        self.assertEqual(
            long_decisions[: len(short_decisions)],
            short_decisions,
            "and the decisions are appended hand by hand, so the shorter pass's ordered log "
            "is the **leading slice** of the longer one's: a differing decision would mean "
            "the pass decided one hand differently when it was asked for more hands "
            "(records.md §15, greedy.md §1, §4, ASM-2, D-36): %r against %r"
            % (long_decisions[: len(short_decisions)], short_decisions),
        )
        self.assertGreaterEqual(
            len(long_decisions),
            len(short_decisions),
            "the longer pass holds at least the decisions of the shorter one, because it "
            "plays those hands and then more -- a shorter log would mean a hand of the "
            "prefix appended nothing it appended before (records.md §15, greedy.md §1): %r "
            "against %r" % (len(long_decisions), len(short_decisions)),
        )
        # ... and here is the identity itself, measured against **the run**: a pass replayed
        # from the checkpoint the record names, at the run's own seed and over the run's own
        # pool, reproduces that run's block hand for hand.  Two hands are enough — a differing
        # delta names the hand the replay did not reproduce — and cost two hands rather than a
        # second run (greedy.md §1, §5, records.md §15, battery.md §2, §4, D-36).
        record = one_seed_run()
        blocks = greedy_blocks(record)
        self.assertTrue(
            blocks,
            "the run this replay starts from retains its pass, so the block compared below is "
            "records.md §15's block and not an absent key (records.md §12, §15): %r"
            % (record.get("greedy"),),
        )
        variant, seed, block = blocks[0]
        final = as_text(
            as_mapping(
                checkpoint_block(record, variant, seed), "a record's checkpoint block"
            )["final"],
            "the final checkpoint a record names",
        )
        replayed = greedy_pass(
            greedy_pool(),
            default_shape(),
            seed,
            REPLAY_HANDS,
            evaluation().policy_from(resolved(final), "off"),
            where,
        )
        self.assertEqual(
            as_int(replayed["hands"], "the replayed pass's hands"),
            REPLAY_HANDS,
            "a pass asked for %r hands plays %r and reports it, so the comparison below holds "
            "of a block of that length and not of a block of whatever length the run's own "
            "sample happened to have (greedy.md §1, §4, records.md §15, ASM-38): %r"
            % (REPLAY_HANDS, REPLAY_HANDS, replayed["hands"]),
        )
        replay_chips = as_sequence(
            replayed["net_chips"], "the replayed pass's per-hand chips"
        )
        self.assertEqual(
            len(replay_chips),
            REPLAY_HANDS,
            "and it carries one net chip delta per hand played, %r of them, so `net_chips` "
            "has one entry per hand of the replay and none invented (records.md §15, "
            "ASM-23): %r" % (REPLAY_HANDS, len(replay_chips)),
        )
        run_chips = as_sequence(block["net_chips"], "the run's own per-hand chips")
        self.assertEqual(
            replay_chips,
            run_chips[:REPLAY_HANDS],
            "hand *j* of the pass **is** the run's own hand *j*: replayed from the checkpoint "
            "the record names, at the run's seed, over the run's own pool, the pass gives the "
            "same %r chip deltas as the leading %r of the run's block -- a differing delta "
            "would mean the pass did not replay the run's own hand, and the sample would not "
            "be the prefix the record states (greedy.md §1, §5, records.md §15, "
            "episode.md §1, seeds.md §2, ASM-2, D-36): %r against %r"
            % (REPLAY_HANDS, REPLAY_HANDS, replay_chips, run_chips[:REPLAY_HANDS]),
        )
        replay_decisions = as_sequence(
            replayed["decisions"], "the replayed pass's ordered decisions"
        )
        run_decisions = as_sequence(block["decisions"], "the run's own ordered decisions")
        self.assertGreaterEqual(
            len(run_decisions),
            len(replay_decisions),
            "the run's block holds at least the decisions the %r-hand replay appended, "
            "because its own sample plays those hands first and then more -- a shorter run "
            "log would mean the replay recorded decisions on hands the run did not play "
            "(records.md §15, greedy.md §1, §4, D-36): %r against %r"
            % (REPLAY_HANDS, len(run_decisions), len(replay_decisions)),
        )
        self.assertEqual(
            replay_decisions,
            run_decisions[: len(replay_decisions)],
            "and the leading slice of the run's log is the replay's log record for record, "
            "because decisions are appended hand by hand and a prefix of hands can only append "
            "the same records in the same order: a differing decision would mean the replay "
            "decided one of the run's own hands differently (records.md §15, greedy.md §1, §5, "
            "episode.md §1, ASM-2, D-36): %r against %r"
            % (replay_decisions, run_decisions[: len(replay_decisions)]),
        )
        self.assertEqual(
            len(replay_chips),
            as_int(replayed["hands"], "the replayed pass's hands"),
            "and the replayed block is internally consistent -- one delta per hand it reports "
            "-- which is the property no block may contradict at any length (records.md §15, "
            "greedy.md §4, D-36): %r deltas for %r hands"
            % (len(replay_chips), replayed["hands"]),
        )
