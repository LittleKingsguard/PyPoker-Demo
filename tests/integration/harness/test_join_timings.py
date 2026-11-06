"""The cost join -- HRNJ-5.

`docs/L2/harness/surface.md` §7: `timings()` is "the cost the driver collected" -- the
hands the driven cases' outcomes declared, the summed monotonic clock the driver measured,
`seconds_per_hand` as that clock over those hands and `hands_per_second` as its reciprocal,
beside the driver's own counts of what it ran.  The join is that every number here is a
measurement of work that really ran: the hands are the ones `engine.play_hand` and
`evaluation.match` reported, and the accumulators move only when a case is driven
(`surface.md` §7, H-5, `records.md` §12, FAM-10.4, FAM-13.6, FAM-14.11).

No case here asserts that a wall clock was beaten: ASM-15's per-hand bound sizes the table
and is not a test, and a beaten clock would be a flaky assertion rather than a contract
(`docs/L1/battery.md` §2, ASM-15).  What is asserted is the arithmetic the record declares
-- the hands counted, the per-hand cost, the throughput and the monotonicity of the
accumulators -- between two calls around work the battery drives itself, so the battery's
own cases are never a precondition of another case's reading.
"""

import importlib.util
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
if "harness_join_support" in sys.modules:
    J = sys.modules["harness_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "harness_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["harness_join_support"] = J
    _spec.loader.exec_module(J)


class TimingsJoin(J.JoinCase):
    """HRNJ-5 -- `timings()` is the cost of work the driver measured."""

    def played(self):
        return J.play_hand(
            J.DEAL_SEED,
            J.build_baseline("always-call", J.BASELINE_SEED),
            J.build_baseline("random", J.BASELINE_SEED_OTHER),
        )

    def cell(self):
        return J.match("always-call", "random", J.HANDS_SMALL, J.MATCH_SEED)

    def reading(self):
        """One `timings()` record with its declared keys checked."""
        record = J.timings()
        self.assert_required_keys(
            record, J.TIMING_KEYS, "the record `harness.timings` returns",
            "docs/L2/harness/surface.md §7, records.md §12",
        )
        for key in J.TIMING_KEYS:
            self.assert_finite(
                record[key], "timings()[%r]" % (key,),
                "docs/L2/harness/surface.md §7",
            )
        self.assertGreaterEqual(
            float(record["hands"]), 0.0,
            "`hands` is an integer never negative (docs/L2/harness/surface.md §7): %r"
            % (record,),
        )
        self.assertGreaterEqual(
            float(record["wall_clock_seconds"]), 0.0,
            "the summed monotonic clock the driver measured is never negative "
            "(docs/L2/harness/surface.md §7): %r" % (record,),
        )
        return record

    def test_hrnj_5_1_the_record_counts_the_hands_the_outcomes_declared(self):
        """HRNJ-5.1 hands are the outcomes' hands, exactly.

        `docs/L2/harness/surface.md` §7 counts `hands` "under §2's counting rule": one per
        episode record, the `hands` a cell record declares, none for anything else (H-5).
        The battery drives a case that returns an episode, a cell and a refusal
        observation, and requires the accumulators to grow by exactly one case, three
        steps and `1 + HANDS` hands -- the numbers the outcomes declared and not the
        number of steps (`surface.md` §2, §7, FAM-14.11).
        """
        before = self.reading()
        case = {
            "id": "hrnj-5-1-cost",
            "steps": [lambda: self.played(),
                      lambda: self.cell(),
                      lambda: J.factory("encoder", J.UNKNOWN_ENCODING)],
            "expect": [{"kind": "zero-sum", "step": 0},
                       {"kind": "counted", "step": 1},
                       {"kind": "refused", "step": 2}],
        }
        result = J.drive(case)
        self.assert_verdict(
            result, "pass", "the case whose cost the battery measures",
            "docs/L2/harness/surface.md §2",
        )
        after = self.reading()
        self.assertEqual(
            int(after["hands"]) - int(before["hands"]), 1 + J.HANDS_SMALL,
            "the record grows by the hands the outcomes declared -- one for the episode "
            "record and the cell's own %d, and nothing for the refusal observation "
            "(docs/L2/harness/surface.md §2, §7, H-5): %r against %r"
            % (J.HANDS_SMALL, before, after),
        )
        self.assertEqual(
            int(after["hands"]) - int(before["hands"]), int(result["hands"]),
            "`timings()` reports what the driven case declared, so the two records carry "
            "one number of hands (docs/L2/harness/surface.md §2, §7): %r against %r"
            % (result["hands"], after["hands"]),
        )
        self.assertEqual(
            int(after["cases"]) - int(before["cases"]), 1,
            "the driver counts the case it drove once (docs/L2/harness/surface.md §7): "
            "%r against %r" % (before, after),
        )
        self.assertEqual(
            int(after["steps"]) - int(before["steps"]), 3,
            "the driver counts the steps it called, which is what the case declared "
            "(docs/L2/harness/surface.md §7): %r against %r" % (before, after),
        )
        self.assertGreater(
            float(after["wall_clock_seconds"]), float(before["wall_clock_seconds"]),
            "the clock the driver measured grows by the work that ran, because it holds a "
            "monotonic clock around each case it drives "
            "(docs/L2/harness/surface.md §2, §7): %r against %r" % (before, after),
        )

    def test_hrnj_5_2_the_per_hand_cost_and_the_throughput_are_the_records_own(self):
        """HRNJ-5.2 `seconds_per_hand` and `hands_per_second` are the record's arithmetic.

        `docs/L2/harness/surface.md` §7 fixes the two derived facts: `seconds_per_hand` is
        "`wall_clock_seconds / hands`" and `hands_per_second` "`hands /
        wall_clock_seconds`", each with its zero case.  The battery drives work so both
        are defined, then requires the products to return the record's own numbers -- the
        per-hand cost times the hands is the clock, and the throughput times the clock is
        the hands (`surface.md` §7, FAM-10.4, FAM-13.6, ASM-15).
        """
        J.drive({
            "id": "hrnj-5-2-cost",
            "steps": [lambda: self.played(), lambda: self.cell()],
            "expect": [{"kind": "zero-sum", "step": 0},
                       {"kind": "counted", "step": 1}],
        })
        record = self.reading()
        hands = float(record["hands"])
        clock = float(record["wall_clock_seconds"])
        per_hand = float(record["seconds_per_hand"])
        throughput = float(record["hands_per_second"])
        self.assertGreater(
            hands, 0.0,
            "the battery drove work that played hands, so `hands` is not zero and the "
            "derived facts are defined (docs/L2/harness/surface.md §7): %r" % (record,),
        )
        self.assertGreater(
            clock, 0.0,
            "the driver measured a wall clock for that work, so the throughput is defined "
            "(docs/L2/harness/surface.md §7): %r" % (record,),
        )
        self.assertGreater(
            per_hand, 0.0,
            "the record carries a positive per-hand cost once hands have been counted, "
            "which is the ASM-15 figure FAM-10 asserts the record for "
            "(docs/L2/harness/surface.md §7, ASM-15): %r" % (record,),
        )
        self.assertGreater(
            throughput, 0.0,
            "the record carries a positive throughput once a clock has been measured, "
            "which is the D-7 speed evidence FAM-13.6 reads "
            "(docs/L2/harness/surface.md §7, D-7): %r" % (record,),
        )
        self.assertAlmostEqual(
            per_hand * hands, clock, delta=max(1e-9, 1e-9 * abs(clock)),
            msg="`seconds_per_hand` is the record's own `wall_clock_seconds / hands`, so "
            "the per-hand cost times the hands must return the clock the driver summed "
            "(docs/L2/harness/surface.md §7, FAM-10.4): %r" % (record,),
        )
        self.assertAlmostEqual(
            throughput * clock, hands, delta=max(1e-6, 1e-9 * hands),
            msg="`hands_per_second` is the reciprocal of `seconds_per_hand`, so the "
            "throughput times the clock must return the hands counted "
            "(docs/L2/harness/surface.md §7, FAM-13.6): %r" % (record,),
        )

    def test_hrnj_5_3_the_accumulators_never_decrease(self):
        """HRNJ-5.3 the record accumulates: no counter falls between two calls.

        `docs/L2/harness/surface.md` §7: "the record accumulates over everything the
        driver *collected* -- the plural of `e3e-surface.md` §3.6's Returns column -- so
        `hands`, `cases`, `steps` and the measured clock never decrease between two
        calls".  A second call with nothing driven between changes nothing at all, which
        is what tells a caller the record is the process's and not a window
        (`surface.md` §7, FAM-14.11).
        """
        first = self.reading()
        second = self.reading()
        self.assertEqual(
            {key: first[key] for key in J.TIMING_KEYS},
            {key: second[key] for key in J.TIMING_KEYS},
            "nothing was driven between two readings, so two calls report one cost: a "
            "call that reset or re-windowed the record would report less than the first "
            "(docs/L2/harness/surface.md §7): %r against %r" % (first, second),
        )
        J.drive({
            "id": "hrnj-5-3-cost",
            "steps": [lambda: self.played()],
            "expect": [{"kind": "zero-sum", "step": 0}],
        })
        third = self.reading()
        for key in ("hands", "wall_clock_seconds", "cases", "steps"):
            self.assertGreaterEqual(
                float(third[key]), float(second[key]),
                "`%s` never decreases between two calls: the record is what the driver "
                "collected over the whole process (docs/L2/harness/surface.md §7): %r "
                "against %r" % (key, second, third),
            )
        self.assertGreater(
            float(third["hands"]), float(second["hands"]),
            "the case that played a hand moved the hands the driver counted "
            "(docs/L2/harness/surface.md §7, H-5): %r against %r" % (second, third),
        )

    def test_hrnj_5_4_a_case_that_plays_no_hand_adds_no_hands(self):
        """HRNJ-5.4 work that plays no hand is measured, and counts no hand.

        `docs/L2/harness/surface.md` §7 makes `cases` and `steps` "this module's own
        counts of what the driver ran, so a caller can tell 'measured nothing yet' from
        'measured something cheap'".  A driven case whose steps call `evaluation` and
        `features` and play nothing therefore moves the case and step counters and leaves
        `hands` where it was (`surface.md` §2, §7, H-5).
        """
        pool = J.shared_pool()
        record, legal = J.readout_and_legal(J.DEAL_SEED)
        observation = J.encode(J.shared_encoder(), record)
        learner = J.build_learner(J.learner_spec())

        def read_pool():
            ids = J.member_ids(J.pool_members(pool))
            return {"chosen": ids[0], "legal": ids}

        def decide():
            index = J.chosen_index(J.act(learner, observation, J.legal_indices(legal)))
            return {"chosen": J.decode_action(index), "legal": list(legal)}

        before = self.reading()
        J.drive({
            "id": "hrnj-5-4-no-hands",
            "steps": [read_pool, decide],
            "expect": [{"kind": "legal-choice", "step": 0},
                       {"kind": "legal-choice", "step": 1}],
        })
        after = self.reading()
        self.assertEqual(
            int(after["hands"]), int(before["hands"]),
            "neither step played a hand, so the hands the driver counted do not move: the "
            "count is read off the outcomes and never off the driver's own work "
            "(docs/L2/harness/surface.md §2, §7, H-5): %r against %r" % (before, after),
        )
        self.assertEqual(
            int(after["cases"]) - int(before["cases"]), 1,
            "the cheap case is still counted as a case, so 'measured nothing yet' and "
            "'measured something cheap' are two different readings "
            "(docs/L2/harness/surface.md §7): %r against %r" % (before, after),
        )
        self.assertEqual(
            int(after["steps"]) - int(before["steps"]), 2,
            "both steps the case declared were called and counted "
            "(docs/L2/harness/surface.md §2, §7): %r against %r" % (before, after),
        )


if __name__ == "__main__":
    unittest.main()
