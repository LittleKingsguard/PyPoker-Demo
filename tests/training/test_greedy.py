"""The one decision stream a run retains -- TRN-14.

`records.md` §15 fixes the block key by key and `sizing.md` §4 fixes its sample, its mode
and its bound; `D-28` fixes the negative half — **no training decision is retained**.  These
cases read the block the loop writes and nothing else: its keys and its mode, that it is
reproducible from the record's own tuple, that both bounds are refused by name with the
counts, that a run's record holds no log of the behaviour policy anywhere but `greedy`, and
that a default-shape record gained exactly the two keys D-29 adds.

| Case | What it reads |
|---|---|
| TRN-14.1 | the block's five keys and its `mode == "off"`, per variant per seed |
| TRN-14.2 | one decision record's seven keys, its index, descriptor and bounds |
| TRN-14.3 | the sample: `hands` is the run's budget, one net chip delta per hand |
| TRN-14.4 | two runs of one tuple reproduce one block, seed and all |
| TRN-14.5 | the 2,000-hand and 24,000-record bounds refused by name with the counts |
| TRN-14.6 | no training decision log anywhere in the record but `greedy` (D-28) |
| TRN-14.7 | a default-shape record gained exactly `game` and `greedy` and nothing else |

Every case states the design section whose claim it reads (`docs/L1/battery.md` §5); none
asserts a value a document leaves to the run (`D-6`).
"""

from _training_support import (  # noqa: E402  - the battery's own support module
    BLOCK_KEYS,
    DECISION_KEYS,
    OVER_BOUND_BUDGET,
    RECORD_KEYS_BEFORE_SHAPES,
    SHAPE_KEYS,
    TINY_BUDGET,
    TrainingCase,
    as_int,
    as_mapping,
    as_sequence,
    as_text,
    custom_configuration,
    decision_logs,
    default_shape,
    greedy_block,
    greedy_blocks,
    one_seed_run,
    pair_run,
    repeated_run,
    shaped_vocabulary,
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

    def test_trn_14_3_the_pass_plays_the_runs_own_sample_budget(self):
        """TRN-14.3 `hands` is the run's budget, and `net_chips` holds one delta per hand.

        `sizing.md` §4: the pass is played "of 1,000 hands" at the live budget, and
        `records.md` §15 makes `hands` "the hands played, at most 2,000".  The run's budget
        *is* the pass's hand count — sample-matched — so a ten-hand run yields a ten-hand
        pass and a live-budget run a 1,000-hand one, and the record states the count it
        actually played rather than clamping (`sizing.md` §4, `ladder.md` §6, ASM-38).
        """
        record = one_seed_run()
        self.assertEqual(
            int(record["budget"]),
            TINY_BUDGET,
            "the invented fixture runs at the battery's tiny budget, which the pass is "
            "sample-matched to (%r)" % (record["budget"],),
        )
        for variant, seed, block in greedy_blocks(record):
            label = "the block of %r at seed %r" % (variant, seed)
            self.assertEqual(
                int(block["hands"]),
                int(record["budget"]),
                "%s plays the run's own sample budget and records the count it played, so "
                "the pass and the training sample are one size (sizing.md §4, "
                "records.md §15): %r vs %r" % (label, block["hands"], record["budget"]),
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
        """TRN-14.5 2,000 hands and 24,000 records, refused with both numbers.

        `sizing.md` §4: "at most 2,000 hands and 24,000 decision records per variant per
        seed -- ... a pass that would exceed either bound is **refused, never truncated**,
        because a truncated log silently reports a different sample".  The hand bound is
        known before the run trains, because the pass's hand count is the budget; the record
        bound is known only as the pass accumulates.  Both are refused with the count and
        the bound, and neither is clamped (`records.md` §15, ASM-38).
        """
        check_hands = self.internal("greedy", "_check_hands")
        check_decisions = self.internal("greedy", "_check_decisions")
        self.assertIsNone(
            check_hands(2000, "training.run of a variant"),
            "a pass of exactly the 2,000-hand bound is inside it and is not refused "
            "(sizing.md §4, ASM-38)",
        )
        self.assertIsNone(
            check_decisions(24000, "training.run of a variant"),
            "and a pass of exactly the 24,000-record bound is inside it (sizing.md §4, "
            "ASM-38)",
        )
        self.refuse(
            lambda: check_hands(OVER_BOUND_BUDGET, "training.run of a variant"),
            "GreedyPassRefused",
            groups=(("2001",), ("2000",)),
            label="a pass one hand above the hand bound",
        )
        self.refuse(
            lambda: check_decisions(24001, "training.run of a variant"),
            "GreedyPassRefused",
            groups=(("24001",), ("24000",)),
            label="a pass one record above the record bound",
        )
        # ... and the run refuses a budget it could not pass at, before it trains: the
        # pass's hand count IS the budget, so nothing is written for a record this module
        # is not allowed to produce (sizing.md §4, e2e-surface.md §2, ASM-38).
        configuration = custom_configuration()
        self.refuse(
            lambda: training().run(
                configuration,
                seeds=[TINY_BUDGET + 9100],
                budget=OVER_BOUND_BUDGET,
            ),
            "GreedyPassRefused",
            groups=(("2001",), ("2000",)),
            label="a run whose budget is one hand above the pass's bound",
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
