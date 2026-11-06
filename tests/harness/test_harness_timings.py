"""HRN-7 — `timings`: what the driver collected, and nothing it did not.

Drives `docs/L3/harness/driver.md` §6 and `docs/L2/harness/surface.md` §7: the four
accumulators are monotone over the process, so every case is measured as a **delta between
two `timings()` calls**; the two derived facts are consistent with the hands counted; a
case that counted no hand adds none; the record is a fresh copy; and the four cost keys
are spelled by what they name, because the D-7 and ASM-15 readers classify a key by the
words in it (`guardrails.md` G19-G20, FAM-10.4, FAM-13.6, FAM-14.11, FAM-16.37).
"""

import json
import subprocess
import sys
import unittest

from _harness_support import (
    CASE_ID,
    REPO_ROOT,
    SRC_ROOT,
    HarnessCase,
    as_int,
    as_mapping,
    as_number,
    case,
    episode_case,
    pure_case,
    real_cell,
)

#: `driver.md` §6's six keys in the declared order.
COST_KEYS = (
    "hands",
    "wall_clock_seconds",
    "cases",
    "steps",
    "seconds_per_hand",
    "hands_per_second",
)

#: The four keys a run record quotes (`records.md` §12, G20).
COST_FACTS = ("hands", "wall_clock_seconds", "seconds_per_hand", "hands_per_second")


class TimingsTest(HarnessCase):
    def timings(self):
        record = as_mapping(self.ep("timings")(), "the timings record")
        return record

    def snapshot(self):
        record = self.timings()
        for key in COST_KEYS:
            self.assertIn(
                key,
                record,
                "the record carries %r (driver §6, surface §7, G19-G20): %r"
                % (key, sorted(record),),
            )
        return {key: record[key] for key in COST_KEYS}

    def delta(self, before, after):
        return {
            key: as_number(after[key], key) - as_number(before[key], key)
            for key in COST_KEYS
        }

    def test_hrn_7_1_a_driven_episode_case_adds_exactly_its_hands_and_steps(self):
        """HRN-7.1 measured as deltas between two calls, a driven episode case adds one case, its hands and its steps to the accumulators, and nothing ever decreases (driver §6, G19, surface §7)."""
        before = self.snapshot()
        record = self.ep("drive")(episode_case(case_id="HRN-7.1-invented-episode"))
        self.assertEqual(
            record["verdict"],
            "pass",
            "the control: the driven episode case passes (driver §3): %r" % (record,),
        )
        after = self.snapshot()
        for key in ("hands", "wall_clock_seconds", "cases", "steps"):
            self.assertGreaterEqual(
                as_number(after[key], key),
                as_number(before[key], key),
                "the accumulators never decrease between two calls (%r, driver §6, "
                "G19): %r then %r" % (key, before[key], after[key]),
            )
        grown = self.delta(before, after)
        self.assertEqual(
            as_int(grown["cases"], "cases grown by"),
            1,
            "one drive call adds one case (driver §6, G19): %r" % (grown,),
        )
        self.assertEqual(
            as_int(grown["steps"], "steps grown by"),
            1,
            "and the number of steps it called (driver §6, G19): %r" % (grown,),
        )
        self.assertEqual(
            as_int(grown["hands"], "hands grown by"),
            as_int(record["hands"], "the case's own hands"),
            "the hands the case's outcomes declared are the hands added (driver §6, "
            "§5, G19): %r vs %r" % (grown["hands"], record["hands"]),
        )
        self.assertEqual(
            as_int(grown["hands"], "hands grown by"),
            1,
            "one episode record is one hand (driver §5, records.md §5, G19): %r"
            % (grown["hands"],),
        )
        self.assertGreater(
            as_number(record["wall_clock_seconds"], "the case's clock"),
            0,
            "the case's clock is measured around the whole case, so it is positive "
            "with the standard library's monotonic clock (driver §2, §4, surface §7): "
            "%r" % (record["wall_clock_seconds"],),
        )
        self.assertAlmostEqual(
            as_number(grown["wall_clock_seconds"], "the clock grown by"),
            as_number(record["wall_clock_seconds"], "the case's clock"),
            places=9,
            msg="the summed clock grows by the record's own measurement (driver §6): "
            "%r vs %r" % (grown["wall_clock_seconds"], record["wall_clock_seconds"]),
        )

    def test_hrn_7_2_the_two_derived_facts_agree_with_the_hands_counted(self):
        """HRN-7.2 `seconds_per_hand × hands` equals the summed clock and `hands_per_second × clock` equals the hands, over the accumulated record a real cell case grows (driver §6, surface §7, G19, FAM-10.4, FAM-13.6)."""
        self.ep("drive")(
            case(
                CASE_ID,
                [lambda: real_cell(hands=4)],
                ["counted"],
            )
        )
        record = self.timings()
        hands = as_int(record["hands"], "the accumulated hands")
        clock = as_number(record["wall_clock_seconds"], "the accumulated clock")
        per_hand = as_number(record["seconds_per_hand"], "seconds_per_hand")
        throughput = as_number(record["hands_per_second"], "hands_per_second")
        self.assertGreaterEqual(
            hands,
            4,
            "the cell case declared four hands, so at least four hands are accumulated "
            "(driver §5, §6, G19): %r" % (hands,),
        )
        self.assertGreaterEqual(
            clock,
            0,
            "a summed elapsed time is never negative (driver §6, surface §7): %r"
            % (clock,),
        )
        self.assertLessEqual(
            abs(per_hand * hands - clock),
            1e-9 * max(1.0, abs(clock)),
            "seconds_per_hand is the per-hand duration the name states, so it times "
            "the hands gives the clock (driver §6, G19, records.md §12): %r × %r vs %r"
            % (per_hand, hands, clock),
        )
        if clock > 0:
            self.assertLessEqual(
                abs(throughput * clock - hands),
                1e-9 * max(1.0, abs(hands)),
                "hands_per_second is the throughput the name states, so it times the "
                "clock gives the hands (driver §6, G19, ASM-15): %r × %r vs %r"
                % (throughput, clock, hands),
            )
        else:
            self.assertEqual(
                throughput,
                0.0,
                "hands_per_second is 0.0 when no time was measured (driver §6, "
                "surface §7): %r" % (throughput,),
            )

    def test_hrn_7_3_a_case_that_counted_no_hand_adds_no_hand(self):
        """HRN-7.3 a pure-value case adds a case and a step and no hand, because hands come from the outcomes and not from the driver's own work (driver §5, §6, G19, FAM-10.4)."""
        before = self.snapshot()
        record = self.ep("drive")(pure_case(case_id="HRN-7.3-invented-pure"))
        self.assertEqual(
            record["verdict"],
            "pass",
            "the control: the pure-value case passes (driver §3): %r" % (record,),
        )
        grown = self.delta(before, self.snapshot())
        self.assertEqual(
            as_int(grown["hands"], "hands grown by"),
            0,
            "a case that counted no hand adds nothing to hands (driver §6, G19): %r"
            % (grown,),
        )
        self.assertEqual(
            as_int(grown["cases"], "cases grown by"),
            1,
            "but it is still a case the driver ran (driver §6, G19): %r" % (grown,),
        )
        self.assertEqual(
            as_int(grown["steps"], "steps grown by"),
            1,
            "and its step is still a step (driver §6, G19): %r" % (grown,),
        )

    def test_hrn_7_4_the_record_is_a_fresh_copy_a_caller_cannot_corrupt(self):
        """HRN-7.4 editing the record a call returned changes nothing the next call reports: `timings()` returns a fresh copy of the accumulators plus the two derived facts (driver §6, README §7 decision 8, G19)."""
        first = self.timings()
        second = self.timings()
        self.assertEqual(
            dict(first),
            dict(second),
            "two calls with no work between them report one record (driver §6, surface "
            "§7): %r vs %r" % (dict(first), dict(second)),
        )
        for key in COST_KEYS:
            self.assertIn(
                key,
                first,
                "the record carries %r (driver §6, G20): %r" % (key, sorted(first),),
            )
        pristine = dict(second)
        first["hands"] = 10 ** 6
        first["wall_clock_seconds"] = 0.0
        first["rate"] = 12.5
        first.pop("cases", None)
        third = self.timings()
        self.assertEqual(
            dict(third),
            pristine,
            "a caller's edit of the returned record cannot corrupt the accumulators, "
            "because the record is a fresh copy of them (driver §6, README §7 decision "
            "8): %r vs %r" % (dict(third), pristine),
        )
        self.assertNotIn(
            "rate",
            third,
            "an invented key a caller wrote into its copy does not appear in a later "
            "record (driver §6, G19): %r" % (sorted(third),),
        )
        self.assertIn(
            "cases",
            third,
            "and a key a caller removed from its copy is still reported (driver §6, "
            "G19): %r" % (sorted(third),),
        )

    def test_hrn_7_5_the_four_cost_keys_are_spelled_by_what_they_name(self):
        """HRN-7.5 the record is `hands`, `wall_clock_seconds`, `cases`, `steps`, `seconds_per_hand`, `hands_per_second` in that order, with no `rate`, `perf` or `t` alias, and each derived name states its own fact (driver §6, G20, records.md §12, FAM-10.4)."""
        record = self.timings()
        self.assertEqual(
            list(record),
            list(COST_KEYS),
            "the six keys are appended in driver §6's order, the four cost keys first "
            "(driver §6, surface §7, G20): %r" % (list(record),),
        )
        for key in ("hands", "cases", "steps"):
            as_int(record[key], key)
        for key in COST_FACTS:
            as_number(record[key], key)
        for alias in ("rate", "perf", "t", "duration", "throughput", "seconds", "clock"):
            self.assertNotIn(
                alias,
                record,
                "the keys are named by what they name, and neither `seconds_per_hand` "
                "nor `hands_per_second` may be renamed to %r, or the D-7 and ASM-15 "
                "evidence readers lose the number (driver §6, G20): %r"
                % (alias, sorted(record)),
            )
        hands = as_int(record["hands"], "hands")
        clock = as_number(record["wall_clock_seconds"], "wall_clock_seconds")
        per_hand = as_number(record["seconds_per_hand"], "seconds_per_hand")
        throughput = as_number(record["hands_per_second"], "hands_per_second")
        self.assertGreaterEqual(hands, 0, "hands is never negative (driver §6): %r" % (hands,))
        if hands:
            self.assertAlmostEqual(
                per_hand,
                clock / hands,
                places=12,
                msg="seconds_per_hand is a per-hand duration, `wall_clock_seconds / "
                "hands` (driver §6, G20): %r vs %r" % (per_hand, clock / hands),
            )
        else:
            self.assertEqual(
                per_hand,
                0.0,
                "and 0.0 when no hand was counted (driver §6, surface §7): %r"
                % (per_hand,),
            )
        if clock:
            self.assertAlmostEqual(
                throughput,
                hands / clock,
                places=12,
                msg="hands_per_second is a throughput, `hands / wall_clock_seconds` "
                "(driver §6, G20): %r vs %r" % (throughput, hands / clock),
            )
        else:
            self.assertEqual(
                throughput,
                0.0,
                "and 0.0 when no time was measured (driver §6, surface §7): %r"
                % (throughput,),
            )

    def test_hrn_7_6_a_malformed_case_still_counts_as_a_case(self):
        """HRN-7.6 a case the driver refused counts once in `cases` and grows `steps` and `hands` by zero, so a caller can tell that the driver refused a case (driver §1, §6, README §7 decision 3, G19)."""
        before = self.snapshot()
        record = self.ep("drive")({"id": CASE_ID, "steps": [], "expect": []})
        self.assertEqual(
            record["verdict"],
            "fail",
            "the control: an empty-steps case is refused (driver §1): %r" % (record,),
        )
        grown = self.delta(before, self.timings())
        self.assertEqual(
            as_int(grown["cases"], "cases grown by"),
            1,
            "a malformed case is counted in cases, because not counting it would hide "
            "that the driver refused a case (driver §1, README §7 decision 3, G19): %r"
            % (grown,),
        )
        self.assertEqual(
            as_int(grown["steps"], "steps grown by"),
            0,
            "it ran no step, so the step count does not grow (driver §1, §6, G19): %r"
            % (grown,),
        )
        self.assertEqual(
            as_int(grown["hands"], "hands grown by"),
            0,
            "and `hands` stays as it was (driver §1, G19): %r" % (grown,),
        )

    def test_hrn_7_7_a_fresh_process_reports_the_documented_zero_record(self):
        """HRN-7.7 in a fresh process, before any case has been driven, the record is `hands` 0, `wall_clock_seconds` 0.0, `cases` 0, `steps` 0, `seconds_per_hand` 0.0, `hands_per_second` 0.0, in that order (driver §6, surface §7, FAM-1.49)."""
        script = (
            "import json, sys\n"
            "sys.path.insert(0, %r)\n"
            "import harness\n"
            "print(json.dumps(harness.timings()))\n" % (SRC_ROOT,)
        )
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            completed.returncode,
            0,
            "a fresh process can import the harness and read its cost record; stderr: "
            "%r" % (completed.stderr.strip(),),
        )
        pairs = json.loads(completed.stdout.strip(), object_pairs_hook=list)
        self.assertEqual(
            pairs,
            [
                ("hands", 0),
                ("wall_clock_seconds", 0.0),
                ("cases", 0),
                ("steps", 0),
                ("seconds_per_hand", 0.0),
                ("hands_per_second", 0.0),
            ],
            "before any case has been driven the record is the documented zero record, "
            "so a caller can tell 'measured nothing yet' from 'measured something "
            "cheap' (driver §6, surface §7, FAM-1.49): %r" % (pairs,),
        )

    def test_hrn_7_8_no_negative_count_reaches_the_accumulators_or_a_rate(self):
        """HRN-7.8 a case whose steps declare `{"hands": -3}`, `{"hands": 2.5}` and `{"hands": "7"}` grows `hands` by 0 and leaves both rates ≥ 0.0, while a real cell grows it by exactly the hands it declares (driver §6, surface §7, G18, G19)."""
        before = self.snapshot()
        record = self.ep("drive")(
            case(
                "HRN-7.8-invented-counts",
                [
                    lambda: {"hands": -3},
                    lambda: {"hands": 2.5},
                    lambda: {"hands": "7"},
                ],
                [
                    {"kind": "counted", "step": 0},
                    {"kind": "counted", "step": 1},
                    {"kind": "counted", "step": 2},
                ],
            )
        )
        self.assertEqual(
            record["verdict"],
            "fail",
            "the control: none of the three values is a cell record carrying its "
            "directions, so the case fails (driver §3, expectations §2.3): %r"
            % (record,),
        )
        grown = self.delta(before, self.snapshot())
        self.assertEqual(
            as_int(grown["hands"], "hands grown by"),
            0,
            "a negative, a fractional and a string count are not hands, so the case adds "
            "none (driver §5, §6, G18): %r" % (grown,),
        )
        accumulated = self.timings()
        hands = as_int(accumulated["hands"], "the accumulated hands")
        self.assertGreaterEqual(
            hands,
            0,
            "hands is an integer ≥ 0, so no driven case can make it negative (driver "
            "§5, §6, G18): %r" % (accumulated["hands"],),
        )
        self.assertGreaterEqual(
            as_number(accumulated["seconds_per_hand"], "seconds_per_hand"),
            0.0,
            "seconds_per_hand is a per-hand duration and never negative, because no "
            "negative count can reach the accumulators (driver §6, surface §7, G18): %r"
            % (accumulated["seconds_per_hand"],),
        )
        self.assertGreaterEqual(
            as_number(accumulated["hands_per_second"], "hands_per_second"),
            0.0,
            "and hands_per_second is a throughput and never negative (driver §6, "
            "surface §7, G18, G19): %r" % (accumulated["hands_per_second"],),
        )
        measured = self.snapshot()
        cell = real_cell(hands=4)
        declared = as_int(cell["hands"], "the cell's own declared hands")
        driven = self.ep("drive")(case(CASE_ID, [lambda: cell], ["counted"]))
        self.assertEqual(
            driven["verdict"],
            "pass",
            "the control: a real cell record accounts for its hands (driver §3, "
            "expectations §2.3): %r" % (driven,),
        )
        after_cell = self.snapshot()
        counted = as_int(
            self.delta(measured, after_cell)["hands"], "hands grown by"
        )
        self.assertEqual(
            counted,
            declared,
            "a cell record contributes exactly the hands it declares (driver §5, §6, "
            "G18, records.md §9): %r vs %r" % (counted, declared),
        )
        self.assertGreater(
            counted,
            0,
            "so the hands a real cell declares are a positive integer and reach the "
            "accumulators (driver §6, G19): %r" % (counted,),
        )


if __name__ == "__main__":
    unittest.main()
