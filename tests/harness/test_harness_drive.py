"""HRN-2 — `drive`: one case, one verdict, and a refusal that is an observation.

Drives `docs/L3/harness/driver.md` §1-§5 and §7 (`docs/L2/harness/surface.md` §2): every
step is called exactly once in declared order and never speculatively, the pass does not
stop at a step that raised, that step's outcome is the refusal observation
`{"refused": True, "error": "<Class>: <message>"}`, the five malformed case shapes and the
three expectation-entry failures are reported rather than raised, the seven-key result is
readable in its declared order, and hands are counted from the outcomes and from nowhere
else (`guardrails.md` G13-G18).

The steps are zero-argument callables, so a step composing a value is judged exactly as
one calling `engine.play_hand` is (`surface.md` §2, FAM-14.10) — and the values a case
composes are `records.md`'s records, never a stand-in for a module.
"""

import unittest

from _harness_support import (
    CASE_ID,
    CASE_ID_OTHER,
    HarnessCase,
    as_int,
    as_mapping,
    as_sequence,
    SEED_STRANGER,
    case,
    play,
    pure_case,
    pure_value,
    real_cell,
)


class DriveTest(HarnessCase):
    def drive(self, value):
        """`drive` once, through the surface, with the record's seven keys checked."""
        return as_mapping(self.ep("drive")(value), "the case-result record")

    def refusal_step(self, ran=None, index=1):
        """A step that raises the refusal a declared entry point would raise."""

        def step():
            if ran is not None:
                ran.append(index)
            raise RuntimeError("an invented refusal")

        return step

    def marker_step(self, ran, index, value=(7, -7)):
        def step():
            ran.append(index)
            return value

        return step

    # -- the step pass -------------------------------------------------------
    def test_hrn_2_1_each_step_is_called_exactly_once_in_order(self):
        """HRN-2.1 a case of three steps appends `[0, 1, 2]` after one `drive`: never twice, never retried, never reordered, never evaluated speculatively, never skipped (driver §2, surface §2, G13, FAM-14.9)."""
        ran = []
        steps = [self.marker_step(ran, index) for index in range(3)]
        entries = [{"kind": "zero-sum", "step": index} for index in range(3)]
        record = self.drive(case(CASE_ID, steps, entries))
        self.assertEqual(
            ran,
            [0, 1, 2],
            "every step is called exactly once, in declared order (driver §2, G13): %r"
            % (ran,),
        )
        self.assertEqual(
            len(ran),
            3,
            "no step is called twice and none is skipped (driver §2, G13): %r" % (ran,),
        )
        self.assertEqual(
            record["id"],
            CASE_ID,
            "the result repeats the case's id verbatim (driver §4, surface §2): %r"
            % (record["id"],),
        )
        self.assertEqual(
            [as_int(entry["index"], "a step index") for entry in record["steps"]],
            [0, 1, 2],
            "one entry per step, in declared order (driver §2.5, §4): %r"
            % (record["steps"],),
        )
        for entry in record["steps"]:
            self.assertEqual(
                list(entry),
                ["index", "outcome", "refused", "seconds"],
                "a step entry carries index, outcome, refused, seconds, in that key "
                "order (driver §2.5): %r" % (list(entry),),
            )
        self.assertEqual(
            record["verdict"],
            "pass",
            "three steps each judged by a passing kind is a passing case (driver §3, "
            "surface §2): %r" % (record,),
        )

    def test_hrn_2_2_the_pass_does_not_stop_at_a_step_that_raised(self):
        """HRN-2.2 a raising step is the refusal observation, the third step still runs, and each step's outcome is judged separately (driver §2, §3, G13, FAM-14.9, FAM-16.32)."""
        ran = []
        steps = [
            self.marker_step(ran, 0),
            self.refusal_step(ran, 1),
            self.marker_step(ran, 2),
        ]
        entries = [
            {"kind": "zero-sum", "step": 0},
            {"kind": "refused", "step": 1},
            {"kind": "zero-sum", "step": 2},
        ]
        record = self.drive(case(CASE_ID, steps, entries))
        self.assertEqual(
            ran,
            [0, 1, 2],
            "a step that raised does not prevent a later step from running (driver §2, "
            "G13, FAM-14.9): %r" % (ran,),
        )
        observed = [entry["refused"] for entry in record["steps"]]
        self.assertEqual(
            observed,
            [False, True, False],
            "each step entry carries its own refused flag (driver §2.3-§2.5): %r"
            % (observed,),
        )
        refusal = as_mapping(
            record["steps"][1]["outcome"], "the refusal observation of step 1"
        )
        self.assertEqual(
            dict(refusal),
            {"refused": True, "error": "RuntimeError: an invented refusal"},
            "a raised step is recorded as {'refused': True, 'error': '<Class>: "
            "<message>'} and never re-raised or retried (driver §2.3, README §7): %r"
            % (dict(refusal),),
        )
        self.assertEqual(
            record["verdict"],
            "pass",
            "a case that expected the refusal passes (driver §3, G14): %r" % (record,),
        )

    # -- a raised step is an observation, not a case failure -----------------
    def test_hrn_2_3_a_case_that_expected_the_refusal_passes(self):
        """HRN-2.3 a case whose step raises and whose entry is `refused` passes, and `drive` does not raise (driver §2, §3, expectations §2.4, G14, FAM-14.10)."""
        record = self.drive(case(CASE_ID, [self.refusal_step()], ["refused"]))
        verdict = record["verdict"]
        self.assertEqual(
            verdict,
            "pass",
            "a raised step judged by `refused` is a pass — the driver must not turn a "
            "refusal into a failure of its own (driver §2, §3, G14): %r" % (record,),
        )
        self.assertIsNone(
            record["reason"],
            "a passing result states its verdict once and its reason is None (driver "
            "§4, surface §2): %r" % (record["reason"],),
        )
        self.assertEqual(
            as_int(record["hands"], "hands"),
            0,
            "a refusal observation is not a hand (driver §5): %r" % (record["hands"],),
        )

    def test_hrn_2_4_the_same_raising_step_judged_zero_sum_fails_the_case(self):
        """HRN-2.4 the same case under `zero-sum` fails, is reported as step 0's failure, and still does not raise (driver §3, G14)."""
        record = self.drive(case(CASE_ID, [self.refusal_step()], ["zero-sum"]))
        self.assertEqual(
            record["verdict"],
            "fail",
            "a step that raised, judged by a kind that expects a value, fails the case "
            "(driver §3, G14): %r" % (record,),
        )
        reason = record["reason"]
        self.assertIsInstance(
            reason,
            str,
            "a failure states its reason as one sentence (driver §3, §4): %r" % (reason,),
        )
        self.assertTrue(
            reason.startswith("harness.drive failed step 0:"),
            "the first failure in declared order becomes the reason, naming the step "
            "(driver §3): %r" % (reason,),
        )
        self.assertIn(
            "zero-sum",
            reason,
            "the reason carries `expect`'s own sentence, so the kind is named (driver "
            "§3, expectations §1): %r" % (reason,),
        )

    # -- the five malformed shapes ------------------------------------------
    def test_hrn_2_5_the_malformed_shapes_are_full_failing_records_and_never_raise(self):
        """HRN-2.5 not a mapping, no `id`, an empty `id`, no `steps`, an empty `steps`, no `expect` and an empty `expect` each give the whole record with `verdict: fail`, the sentence of driver §1, and no step is called (driver §1, §4, G15, FAM-14.10)."""
        ran = []
        shapes = (
            (
                "not a mapping",
                ["a list, not a mapping"],
                "harness.drive refused the case: it is not a mapping",
            ),
            (
                "no 'id'",
                {"steps": [self.marker_step(ran, 0)], "expect": ["zero-sum"]},
                "harness.drive refused the case: it carries no non-empty 'id'",
            ),
            (
                "an empty 'id'",
                {"id": "", "steps": [self.marker_step(ran, 0)], "expect": ["zero-sum"]},
                "harness.drive refused the case: it carries no non-empty 'id'",
            ),
            (
                "no 'steps'",
                {"id": CASE_ID, "expect": ["zero-sum"]},
                "harness.drive refused the case: it carries no non-empty 'steps'",
            ),
            (
                "an empty 'steps'",
                {"id": CASE_ID, "steps": [], "expect": ["zero-sum"]},
                "harness.drive refused the case: it carries no non-empty 'steps'",
            ),
            (
                "no 'expect'",
                {"id": CASE_ID, "steps": [self.marker_step(ran, 0)]},
                "harness.drive refused the case: it carries no non-empty 'expect'",
            ),
            (
                "an empty 'expect'",
                {"id": CASE_ID, "steps": [self.marker_step(ran, 0)], "expect": []},
                "harness.drive refused the case: it carries no non-empty 'expect'",
            ),
        )
        for label, malformed, sentence in shapes:
            with self.subTest(shape=label):
                record = self.drive(malformed)
                self.assertEqual(
                    list(record),
                    [
                        "id",
                        "steps",
                        "expectations",
                        "hands",
                        "wall_clock_seconds",
                        "verdict",
                        "reason",
                    ],
                    "a malformed case still returns the whole seven-key record of "
                    "driver §4 (%s): %r" % (label, list(record)),
                )
                self.assertEqual(
                    record["verdict"],
                    "fail",
                    "a malformed case is a fail and never a raise (%s, driver §1, G15): "
                    "%r" % (label, record["verdict"]),
                )
                self.assertEqual(
                    record["reason"],
                    sentence,
                    "the first failing check's sentence is the reason (%s, driver §1): "
                    "%r" % (label, record["reason"]),
                )
                self.assertEqual(
                    as_sequence(record["steps"], "the steps list"),
                    [],
                    "it ran no step, so `steps` grows by zero (%s, driver §1): %r"
                    % (label, record["steps"]),
                )
                self.assertEqual(
                    as_int(record["hands"], "hands"),
                    0,
                    "and no hand is counted (%s, driver §1, §5): %r"
                    % (label, record["hands"]),
                )
        self.assertEqual(
            ran,
            [],
            "a malformed case calls no step at all (driver §1: 'it ran no step'): %r"
            % (ran,),
        )

    def test_hrn_2_6_a_step_that_is_not_callable_fails_the_case_and_calls_nothing(self):
        """HRN-2.6 a step that is not a zero-argument callable gives the whole record with `verdict: fail` and the sentence of driver §1, and no step runs (driver §1, §4, G15)."""
        ran = []
        record = self.drive(
            case(CASE_ID, [self.marker_step(ran, 0), 42], ["zero-sum"]),
        )
        self.assertEqual(
            record["verdict"],
            "fail",
            "a step that is not callable is a named failure inside the result (driver "
            "§1, surface §2, G15): %r" % (record,),
        )
        self.assertEqual(
            record["reason"],
            "harness.drive refused the case: a step is not a zero-argument callable",
            "the sentence is driver §1's: %r" % (record["reason"],),
        )
        self.assertEqual(
            as_sequence(record["steps"], "the steps list"),
            [],
            "the shape is checked before the pass, so no step ran (driver §1): %r"
            % (record["steps"],),
        )
        self.assertEqual(
            ran,
            [],
            "not even the callable step before it was called (driver §1, G15): %r"
            % (ran,),
        )

    def test_hrn_2_7_the_first_failing_shape_is_the_sentence(self):
        """HRN-2.7 the shape checks are explicit and ordered — `id`, then `steps`, then `expect`, then callability — and the first one that fails is the reason (driver §1)."""
        cases = (
            (
                {"steps": [], "expect": ["zero-sum"]},
                "it carries no non-empty 'id'",
            ),
            (
                {"id": CASE_ID, "steps": [], "expect": ["zero-sum"]},
                "it carries no non-empty 'steps'",
            ),
            (
                {"id": CASE_ID, "steps": [42], "expect": []},
                "it carries no non-empty 'expect'",
            ),
        )
        for malformed, sentence in cases:
            with self.subTest(case=malformed):
                record = self.drive(malformed)
                self.assertEqual(
                    record["verdict"],
                    "fail",
                    "each malformed case is a fail (driver §1): %r" % (record,),
                )
                self.assertEqual(
                    record["reason"],
                    "harness.drive refused the case: " + sentence,
                    "the first check that fails is the sentence, not a later one "
                    "(driver §1): %r" % (record["reason"],),
                )

    # -- the three expectation-entry failures --------------------------------
    def test_hrn_2_8_an_out_of_range_step_index_is_named_and_judges_no_step(self):
        """HRN-2.8 an out-of-range `step` index fails the case with a sentence naming it and the entry is not recorded as judging a step (driver §3, G16)."""
        record = self.drive(
            case(CASE_ID, [pure_value()], [{"kind": "zero-sum", "step": 5}]),
        )
        self.assertEqual(
            as_sequence(record["expectations"], "the judged expectations"),
            [],
            "an out-of-range entry is not recorded as judging a step (driver §3): %r"
            % (record["expectations"],),
        )
        self.assertEqual(
            record["verdict"],
            "fail",
            "an out-of-range index is a named failure inside the result (driver §3): %r"
            % (record,),
        )
        reason = record["reason"]
        self.assertIn(
            "harness.drive refused the expectation",
            reason,
            "the failure names the expectation that could not be judged (driver §3): %r"
            % (reason,),
        )
        self.assertIn(
            "zero-sum",
            reason,
            "the sentence names the kind it could not place (driver §3): %r" % (reason,),
        )
        self.assertIn(
            "it names no step of this case",
            reason,
            "driver §3's sentence for an index outside 0 … len(steps)-1: %r" % (reason,),
        )

    def test_hrn_2_9_a_non_integer_index_and_an_unreadable_entry_are_named(self):
        """HRN-2.9 a non-integer step index and an entry that is neither a kind name nor a mapping each fail the case, and every entry that did judge is still recorded (driver §3, G16)."""
        for label, entry_value in (
            ("a string index", {"kind": "zero-sum", "step": "0"}),
            ("a float index", {"kind": "zero-sum", "step": 0.5}),
        ):
            with self.subTest(entry=label):
                record = self.drive(case(CASE_ID, [pure_value()], [entry_value]))
                self.assertEqual(
                    record["verdict"],
                    "fail",
                    "an index that is not an integer names no step and fails the case "
                    "(%s, driver §3): %r" % (label, record),
                )
                self.assertIn(
                    "it names no step of this case",
                    record["reason"],
                    "driver §3's sentence for a non-integer index (%s): %r"
                    % (label, record["reason"]),
                )
        record = self.drive(case(CASE_ID, [pure_value()], [5]))
        self.assertEqual(
            record["verdict"],
            "fail",
            "an entry that is neither a string nor a mapping is a named failure (driver "
            "§3, G16): %r" % (record,),
        )
        self.assertIn(
            "an entry is a kind name or a",
            record["reason"],
            "driver §3's sentence for an unreadable entry: %r" % (record["reason"],),
        )
        judged = self.drive(
            case(CASE_ID, [pure_value()], [{"kind": "zero-sum", "step": 0}, 5]),
        )
        self.assertEqual(
            len(as_sequence(judged["expectations"], "the judged expectations")),
            1,
            "every entry that did judge is still recorded, whatever a later entry did "
            "(driver §3): %r" % (judged["expectations"],),
        )
        self.assertEqual(
            judged["expectations"][0]["kind"],
            "zero-sum",
            "the recorded entry is the one that judged (driver §3): %r"
            % (judged["expectations"][0],),
        )
        self.assertEqual(
            judged["verdict"],
            "fail",
            "and the case still fails, because an entry could not be judged (driver "
            "§3): %r" % (judged,),
        )

    def test_hrn_2_10_a_step_no_entry_judges_is_named_and_nothing_is_judged_silently(self):
        """HRN-2.10 a step no entry judges fails the case with a sentence naming it, while every entry that did judge is still recorded (driver §3, surface §2, G16)."""
        record = self.drive(
            case(CASE_ID, [pure_value(), pure_value((1, 2))], [{"kind": "zero-sum", "step": 0}]),
        )
        self.assertEqual(
            record["verdict"],
            "fail",
            "a verdict over a step nobody judged is not a verdict about the case as run "
            "(surface §2, driver §3, G16): %r" % (record,),
        )
        reason = record["reason"]
        self.assertIn(
            "harness.drive ran step 1",
            reason,
            "the sentence names the step nobody judged (driver §3): %r" % (reason,),
        )
        self.assertIn(
            "no expectation judges",
            reason,
            "driver §3's sentence for an unjudged step: %r" % (reason,),
        )
        self.assertEqual(
            len(as_sequence(record["expectations"], "the judged expectations")),
            1,
            "the entry that did judge is still recorded (driver §3, G16): %r"
            % (record["expectations"],),
        )

    # -- the result record ---------------------------------------------------
    def test_hrn_2_11_the_seven_keys_are_in_the_declared_order_and_verdict_is_readable(self):
        """HRN-2.11 the result carries `id`, `steps`, `expectations`, `hands`, `wall_clock_seconds`, `verdict`, `reason` in that order, the id verbatim, and no key before `verdict` contains `pass`/`ok`/`success`/`result`/`verdict`/`status` (driver §4, G17, FAM-14.9)."""
        case_id = "HRN-2.11-verbatim-id"
        record = self.drive(pure_case(case_id=case_id))
        self.assertEqual(
            list(record),
            [
                "id",
                "steps",
                "expectations",
                "hands",
                "wall_clock_seconds",
                "verdict",
                "reason",
            ],
            "the seven keys of driver §4 in the declared order — a tolerant pass/fail "
            "scan must meet `verdict` first: %r" % (list(record),),
        )
        for key in list(record)[:5]:
            for token in ("pass", "ok", "success", "result", "verdict", "status"):
                self.assertNotIn(
                    token,
                    key.lower(),
                    "no key before `verdict` contains %r, or a tolerant reader answers "
                    "with the wrong key (driver §4, G17): %r" % (token, key),
                )
        self.assertEqual(
            record["id"],
            case_id,
            "the id is repeated verbatim, because a layer return cites the case by it "
            "(driver §4, surface §2): %r" % (record["id"],),
        )
        self.assertEqual(
            record["verdict"],
            "pass",
            "a pure-value case under `zero-sum` passes (driver §3): %r" % (record,),
        )
        self.assertIsNone(
            record["reason"],
            "a pass's reason is None, never a sentence arguing for a failure (driver §4, "
            "surface §2): %r" % (record["reason"],),
        )
        expectations = as_sequence(
            record["expectations"], "the judged expectations"
        )
        self.assertEqual(
            len(expectations),
            1,
            "one entry per expectation entry, in declared order (driver §3, §4): %r"
            % (expectations,),
        )
        judged = as_mapping(expectations[0], "one expectation record")
        self.assertEqual(
            list(judged),
            ["kind", "step", "verdict", "reason"],
            "the expect record is appended with the step index folded in, under kind, "
            "step, verdict, reason, in that order (driver §3): %r" % (list(judged),),
        )
        self.assertEqual(
            as_int(judged["step"], "the judged step index"),
            0,
            "a bare kind-name entry judges the last step (driver §3): %r" % (judged,),
        )
        self.assertEqual(
            judged["kind"],
            "zero-sum",
            "the entry's kind is carried into the record (driver §3): %r" % (judged,),
        )
        self.assertEqual(
            judged["verdict"],
            "pass",
            "the driver adds no second judging rule: the same kind and value pass here "
            "as when a battery calls `expect` (driver §3, surface §2): %r" % (judged,),
        )
        self.assertIsNone(
            judged["reason"],
            "a passing expectation carries no reason (expectations §1, driver §3): %r"
            % (judged["reason"],),
        )

    def test_hrn_2_12_a_pass_carries_no_reason_and_a_failure_carries_one_sentence(self):
        """HRN-2.12 `verdict` is `pass` iff `reason` is `None`, and a failure's reason is one sentence (driver §3, §4, G17, FAM-14.9)."""
        passing = self.drive(pure_case())
        self.assertEqual(
            passing["verdict"],
            "pass",
            "the control case passes (driver §3): %r" % (passing,),
        )
        self.assertIsNone(
            passing["reason"],
            "a pass never argues for a failure (driver §4, surface §2): %r"
            % (passing["reason"],),
        )
        failing = self.drive(case(CASE_ID, [pure_value((1, 2))], ["zero-sum"]))
        self.assertEqual(
            failing["verdict"],
            "fail",
            "unbalanced deltas fail the case (driver §3, expectations §2.1): %r"
            % (failing,),
        )
        reason = failing["reason"]
        self.assertIsInstance(
            reason,
            str,
            "a failure's reason is one sentence, not None (driver §4, G17): %r"
            % (reason,),
        )
        self.assertTrue(
            reason.strip(),
            "the sentence is non-empty (driver §4): %r" % (reason,),
        )
        self.assertNotIn(
            "\n",
            reason.strip(),
            "the reason is one sentence and not a traceback (driver §4, errors §3): %r"
            % (reason,),
        )
        for record in (passing, failing):
            self.assertEqual(
                record["verdict"] == "pass",
                record["reason"] is None,
                "`verdict` is pass iff `reason` is None (driver §3): %r" % (record,),
            )

    # -- hands, from the outcomes only ---------------------------------------
    def test_hrn_2_13_hands_are_counted_from_the_outcomes_and_nowhere_else(self):
        """HRN-2.13 an episode record counts 1, a composed episode counts 1, a cell record counts the `hands` it declares, and a refusal observation and a bare number count 0 (driver §5, G18, FAM-10.4)."""
        composed = {
            "seed": SEED_STRANGER,
            "decisions": ({"seat": (0, True), "action": "check-call", "reward": 0},),
            "payoffs": {0: 1, 1: -1},
        }
        cell = real_cell(hands=4)
        declared_hands = as_int(cell["hands"], "the cell's own hands")
        steps = [
            lambda: play(),                       # a real engine.play_hand episode
            lambda: composed,                     # a step composing an episode
            lambda: cell,                         # a real evaluation.match cell
            self.refusal_step(),                  # a refusal observation
            lambda: 3,                            # a bare number
        ]
        entries = [
            {"kind": "zero-sum", "step": 0},
            {"kind": "zero-sum", "step": 1},
            {"kind": "counted", "step": 2},
            {"kind": "refused", "step": 3},
            {"kind": "zero-sum", "step": 4},
        ]
        record = self.drive(case(CASE_ID, steps, entries))
        self.assertEqual(
            as_int(record["hands"], "the case's hands"),
            1 + 1 + declared_hands,
            "one hand per episode record, the cell's own declared hands, and nothing for "
            "a refusal or a bare number (driver §5, G18, records.md §5, §9): %r"
            % (record["hands"],),
        )
        self.assertEqual(
            len(as_sequence(record["steps"], "the step entries")),
            5,
            "five steps ran, and the step count is not the hand count (driver §5): %r"
            % (record["steps"],),
        )

    def test_hrn_2_14_the_step_count_is_never_the_hand_count(self):
        """HRN-2.14 three steps that return no hand record declare zero hands, while two episode steps declare two (driver §5, G18, H-5, FAM-13.6)."""
        no_hands = self.drive(
            case(
                CASE_ID,
                [pure_value((7, -7)), pure_value((1, -1)), pure_value((0, 0))],
                [
                    {"kind": "zero-sum", "step": 0},
                    {"kind": "zero-sum", "step": 1},
                    {"kind": "zero-sum", "step": 2},
                ],
            )
        )
        self.assertEqual(
            as_int(no_hands["hands"], "hands from three non-hand steps"),
            0,
            "three pure-value steps declare no hand, so counting steps as hands breaks "
            "the FAM-10/FAM-13 cost evidence (driver §5, G18): %r" % (no_hands["hands"],),
        )
        two_episodes = self.drive(
            case(
                CASE_ID_OTHER,
                [lambda: play(), lambda: play()],
                [
                    {"kind": "zero-sum", "step": 0},
                    {"kind": "zero-sum", "step": 1},
                ],
            )
        )
        self.assertEqual(
            as_int(two_episodes["hands"], "hands from two episode steps"),
            2,
            "one hand per episode record played (driver §5, records.md §5): %r"
            % (two_episodes["hands"],),
        )
        for record, what in ((no_hands, "a non-episode"), (two_episodes, "an episode")):
            self.assertIsInstance(
                record["wall_clock_seconds"],
                (int, float),
                "the case's measured clock is a number, the driver's own measurement "
                "(%s; driver §2, §4): %r" % (what, record["wall_clock_seconds"]),
            )

    # -- determinism, and the outcome stored verbatim ------------------------
    def test_hrn_2_15_one_case_gives_one_result_twice_and_runs_its_steps_twice(self):
        """HRN-2.15 one case gives the same step outcomes, expectation verdicts and verdict on a second `drive`, and the second call runs the steps a second time (driver §7, surface §2, protocol §4)."""
        ran = []
        one = case(
            CASE_ID,
            [self.marker_step(ran, 0), self.refusal_step(ran, 1)],
            [{"kind": "zero-sum", "step": 0}, {"kind": "refused", "step": 1}],
        )
        first = self.drive(one)
        second = self.drive(one)
        self.assertEqual(
            ran,
            [0, 1, 0, 1],
            "one `drive` call is one run of the case; a second call runs the steps a "
            "second time and is not a replay (driver §7, surface §2): %r" % (ran,),
        )
        self.assertEqual(
            first["verdict"],
            second["verdict"],
            "the same steps and seeds give the same verdict (driver §7): %r vs %r"
            % (first["verdict"], second["verdict"]),
        )
        self.assertEqual(
            [entry["refused"] for entry in first["steps"]],
            [entry["refused"] for entry in second["steps"]],
            "the same step outcomes (driver §7): %r vs %r"
            % (first["steps"], second["steps"]),
        )
        self.assertEqual(
            [
                (entry["kind"], entry["step"], entry["verdict"])
                for entry in first["expectations"]
            ],
            [
                (entry["kind"], entry["step"], entry["verdict"])
                for entry in second["expectations"]
            ],
            "the same expectation verdicts (driver §7, protocol §4): %r vs %r"
            % (first["expectations"], second["expectations"]),
        )

    def test_hrn_2_16_the_outcome_is_stored_verbatim_and_never_normalised(self):
        """HRN-2.16 the step's returned value is stored verbatim as `outcome` — the driver copies, normalises and re-encodes nothing (driver §2.3, §2.5)."""
        returned = {"invented": [1, 2, 3], "nested": {"refused": False}}
        record = self.drive(
            case(CASE_ID, [lambda: returned], ["zero-sum"]),
        )
        self.assertIs(
            record["steps"][0]["outcome"],
            returned,
            "a returned value is stored verbatim, not copied or re-encoded (driver §2.3, "
            "§2.5): %r" % (record["steps"][0]["outcome"],),
        )
        self.assertIs(
            record["steps"][0]["refused"],
            False,
            "a returned value is stored with refused: False (driver §2.3): %r"
            % (record["steps"][0]["refused"],),
        )
        self.assertEqual(
            record["verdict"],
            "fail",
            "the invented value states no two chip deltas, so the case fails and is not "
            "silently repaired (driver §3, expectations §2.1): %r" % (record,),
        )

    def test_hrn_2_17_a_step_judged_twice_must_pass_both_judgements(self):
        """HRN-2.17 a step covered by two entries passes only when both judgements pass, and both are recorded (driver §3, surface §2)."""
        cell = real_cell(hands=4)
        both_pass = self.drive(
            case(
                CASE_ID,
                [lambda: cell],
                [{"kind": "zero-sum", "step": 0}, {"kind": "counted", "step": 0}],
            )
        )
        self.assertEqual(
            len(as_sequence(both_pass["expectations"], "the judged expectations")),
            2,
            "a step judged twice records both judgements (driver §3, surface §2): %r"
            % (both_pass["expectations"],),
        )
        self.assertEqual(
            both_pass["verdict"],
            "pass",
            "both judgements pass on a real cell record, so the case passes (driver §3, "
            "expectations §2.1, §2.3): %r" % (both_pass,),
        )
        one_fails = self.drive(
            case(
                CASE_ID_OTHER,
                [lambda: cell],
                [{"kind": "zero-sum", "step": 0}, {"kind": "refused", "step": 0}],
            )
        )
        self.assertEqual(
            one_fails["verdict"],
            "fail",
            "a step judged twice must pass both judgements (driver §3, surface §2): %r"
            % (one_fails,),
        )
        verdicts = [
            entry["verdict"] for entry in one_fails["expectations"]
        ]
        self.assertEqual(
            verdicts,
            ["pass", "fail"],
            "both judgements are recorded, in declared order (driver §3): %r"
            % (one_fails["expectations"],),
        )
        self.assertIsInstance(
            one_fails["wall_clock_seconds"],
            (int, float),
            "the cell's hands are counted whatever the verdict, and the case's clock is "
            "still measured (driver §5, §2): %r" % (one_fails,),
        )
        self.assertEqual(
            as_int(one_fails["hands"], "hands"),
            as_int(cell["hands"], "the cell's own hands"),
            "the cell declares its own hands and the driver counts them, pass or fail "
            "(driver §5): %r" % (one_fails["hands"],),
        )

    def test_hrn_2_18_a_count_is_counted_and_a_number_a_value_states_is_not(self):
        """HRN-2.18 `{"hands": -3}`, `{"hands": 2.5}`, `{"hands": "7"}`, `{"hands": True}` and `{"hands": 5}` with no `directions` each contribute 0 hands, so the case's hands is the one cell record's declared count — an integer ≥ 0 (driver §5, G18, surface §2)."""
        cell = {"hands": 4, "directions": ({"wins": 2, "ties": 0, "losses": 2},)}
        steps = [
            lambda: {"hands": -3},
            lambda: {"hands": 2.5},
            lambda: {"hands": "7"},
            lambda: {"hands": True},
            lambda: {"hands": 5},
            lambda: cell,
        ]
        entries = [{"kind": "counted", "step": index} for index in range(len(steps))]
        record = self.drive(case(CASE_ID, steps, entries))
        # `{"hands": -3}` used to be counted as hands and reached `timings()`, which then
        # reported a negative `seconds_per_hand`: a count is a non-negative integer and
        # not the number a value states (driver §5, G18).
        self.assertNotIsInstance(
            record["hands"],
            bool,
            "hands is a count of hands and never a boolean (driver §5, G18): %r"
            % (record["hands"],),
        )
        hands = as_int(record["hands"], "the case's hands")
        self.assertGreaterEqual(
            hands,
            0,
            "hands stays an integer ≥ 0, because the rule reads a count and not the "
            "number a value states (driver §5, G18): %r" % (record["hands"],),
        )
        self.assertEqual(
            hands,
            as_int(cell["hands"], "the cell's own declared hands"),
            "only the cell record's own hands are counted: the negative, fractional, "
            "string, boolean and handless values each contributed 0 (driver §5, G18): %r"
            % (record["hands"],),
        )


if __name__ == "__main__":
    unittest.main()
