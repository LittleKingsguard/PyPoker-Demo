"""The driver join -- HRNJ-1.

`docs/L2/harness/surface.md` §2: one case, one verdict.  A case's `steps` are
zero-argument callables that call declared entry points of `e2e-surface.md` §3, so the
driver is the place where the harness and the five modules actually meet: every step is
called exactly once in declared order, a step that raised is recorded as
``{"refused": true, "error": ...}`` and judged by the `refused` kind, a step judged twice
must pass both judgements, a step nobody judged is a named failure, `drive` never raises
for the case it is handed, and the verdict it records is what `expect` says about the same
outcome -- the driver adds no second judging rule (`surface.md` §1, §2, §6, H-4, H-5, H-6,
`docs/L3/harness/driver.md` §2-§5, `docs/L1/battery.md` §5).

No case here restates what `tests/e2e/test_fam14_harness.py` already asserts about the
driver's own behaviour: every step is a real call on `engine`, `features`, `agents` or
`evaluation`, and what is judgeable is the join -- that the harness drove the modules and
read their records as `records.md` declares them.
"""

import importlib.util
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "harness_join_support" in sys.modules:
    J = sys.modules["harness_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "harness_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["harness_join_support"] = J
    _spec.loader.exec_module(J)


class DriveJoin(J.JoinCase):
    """HRNJ-1 -- a driven case's steps are the five modules' own work."""

    # -- the case builders -------------------------------------------------
    def played(self):
        """One real episode: two declared baselines playing one seeded hand."""
        return J.play_hand(
            J.DEAL_SEED,
            J.build_baseline("always-call", J.BASELINE_SEED),
            J.build_baseline("random", J.BASELINE_SEED_OTHER),
        )

    def cell(self):
        return J.match("always-call", "random", J.HANDS_SMALL, J.MATCH_SEED)

    def driven(self, case, what):
        """`harness.drive` a case, failing loudly if it raised for it.

        `docs/L2/harness/surface.md` §2: "`drive` **never raises**" for the case it is
        handed -- a malformed case is a named failure inside the result, so a raise here
        is a contract violation and not a case finding.
        """
        try:
            return J.drive(case)
        except J.SurfaceAbsent:
            raise
        except Exception as exc:  # noqa: BLE001 - a raise is the finding
            self.fail(
                "%s: `harness.drive` never raises for the case it is handed -- a case "
                "that is not a mapping, a missing or empty key, a step that is not "
                "callable, an unlisted kind and an out-of-range index are each a named "
                "failure inside the result (docs/L2/harness/surface.md §2, H-6, "
                "FAM-14.10); it raised %s: %s"
                % (what, type(exc).__name__, exc)
            )

    # -- the cases ---------------------------------------------------------
    def test_hrnj_1_1_a_case_over_the_five_modules_runs_each_step_once_in_order(self):
        """HRNJ-1.1 every step is called exactly once, in declared order.

        The case's four steps are real calls: `engine.play_hand`, `evaluation.match`,
        `agents.act` over `features.encode` of a real `engine.readout`, and
        `evaluation.pool_members` read back against `agents.baselines`.  The driver runs
        each exactly once, in the order declared, records the value each returned
        verbatim, and judges each with the entry that names its index
        (`docs/L2/harness/surface.md` §2, FAM-14.9).
        """
        log = []
        played = self.played()
        cell = self.cell()
        encoder = J.shared_encoder()
        pool = J.shared_pool()

        def play():
            log.append("play_hand")
            return played

        def play_cell():
            log.append("match")
            return cell

        def decide():
            log.append("act+encode")
            record, legal = J.readout_and_legal(J.DEAL_SEED_OTHER)
            observation = J.encode(encoder, record)
            decision = J.act(
                J.build_learner(J.learner_spec()), observation, J.legal_indices(legal)
            )
            return {"chosen": J.decode_action(J.chosen_index(decision)),
                    "legal": list(legal)}

        def read_pool():
            log.append("pool_members")
            record = J.pool_members(pool)
            ids = J.member_ids(record)
            # A real membership claim, not a tautology: the read-back names the three
            # pinned baselines among its members (`records.md` §8, ASM-16).
            for name in J.baseline_names():
                if name not in ids:
                    raise AssertionError(
                        "harness.factory's pool read back through evaluation.pool_members "
                        "must name the pinned baseline %r among its members (%r), because "
                        "a pool always holds the three baselines (records.md §8, "
                        "docs/L2/evaluation/surface.md §6): %r"
                        % (name, ids, record)
                    )
            return {"chosen": J.baseline_names()[-1], "legal": ids}

        case = {
            "id": "hrnj-1-1-five-modules",
            "steps": [play, play_cell, decide, read_pool],
            "expect": [
                {"kind": "zero-sum", "step": 0},
                {"kind": "counted", "step": 1},
                {"kind": "legal-choice", "step": 2},
                {"kind": "legal-choice", "step": 3},
            ],
        }
        result = self.driven(case, "HRNJ-1.1")
        self.assert_required_keys(
            result, J.DRIVER_KEYS, "the case-result record", "docs/L2/harness/surface.md §2"
        )
        self.assertEqual(
            result["id"], case["id"],
            "the case-result record repeats the case's own id verbatim, because a layer "
            "return cites the case by it (docs/L2/harness/surface.md §2, FAM-14.9): %r"
            % (result["id"],),
        )
        self.assertEqual(
            log,
            ["play_hand", "match", "act+encode", "pool_members"],
            "every step is called exactly once and in declared order -- never twice, "
            "never reordered, never skipped and never evaluated speculatively "
            "(docs/L2/harness/surface.md §2, FAM-14.9): %r" % (log,),
        )
        self.assertEqual(
            len(result["steps"]), 4,
            "the record carries one entry per step called (docs/L2/harness/surface.md "
            "§2): %r" % (result["steps"],),
        )
        for position, entry in enumerate(result["steps"]):
            self.assert_required_keys(
                entry, J.STEP_KEYS, "step entry %d" % (position,),
                "docs/L2/harness/surface.md §2",
            )
            self.assertEqual(
                entry["index"], position,
                "the step entries are in declared order, one `index` per step "
                "(docs/L2/harness/surface.md §2): %r" % (result["steps"],),
            )
            self.assertIs(
                entry["refused"], False,
                "no step of this case raised, so no entry states a refusal "
                "(docs/L2/harness/surface.md §2): %r" % (entry,),
            )
            self.assert_finite(
                entry["seconds"], "one step's measured seconds",
                "docs/L2/harness/surface.md §2",
            )
            self.assertGreaterEqual(
                float(entry["seconds"]), 0.0,
                "the driver holds a monotonic clock around each step, so its seconds are "
                "never negative (docs/L2/harness/surface.md §2): %r" % (entry,),
            )
        self.assertIs(
            result["steps"][0]["outcome"], played,
            "a returned value is stored verbatim as the step's `outcome` -- not copied, "
            "normalised or re-encoded (docs/L2/harness/surface.md §2): %r"
            % (result["steps"][0]["outcome"],),
        )
        self.assertEqual(
            [entry["kind"] for entry in result["expectations"]],
            ["zero-sum", "counted", "legal-choice", "legal-choice"],
            "one expectation entry per entry declared, in declared order "
            "(docs/L2/harness/surface.md §2): %r" % (result["expectations"],),
        )
        for position, entry in enumerate(result["expectations"]):
            self.assert_required_keys(
                entry, J.EXPECTATION_KEYS, "expectation entry %d" % (position,),
                "docs/L2/harness/surface.md §2, §6",
            )
            self.assertEqual(
                entry["step"], position,
                "each entry judges the step its index names (docs/L2/harness/surface.md "
                "§2): %r" % (entry,),
            )
            self.assertEqual(
                entry["verdict"], "pass",
                "the value each step returned satisfies the kind that judges it -- an "
                "episode balances, a cell accounts for its hands, and the two composed "
                "choices are members of the sets they name (docs/L2/harness/surface.md "
                "§2, §6): %r" % (result["expectations"],),
            )
        self.assert_verdict(
            result, "pass", "a case whose steps all ran and all passed",
            "docs/L2/harness/surface.md §2",
        )
        self.assertEqual(
            result["hands"], 1 + J.HANDS_SMALL,
            "the hands are counted from the outcomes: one for the episode record and the "
            "cell's own %d, and nothing for the two composed values "
            "(docs/L2/harness/surface.md §2, H-5, records.md §5, §9): %r"
            % (J.HANDS_SMALL, result["hands"]),
        )

    def test_hrnj_1_2_a_step_that_raised_is_an_observation_the_pass_continues(self):
        """HRNJ-1.2 a refusing step is recorded, judged, and does not stop the case.

        The first step calls `factory` for an encoding `features` does not declare, so
        the owner refuses inside the step.  `docs/L2/harness/surface.md` §2 makes that a
        refusal observation -- ``{"refused": true, "error": "<class and message>"}`` --
        judged by the `refused` kind, and the pass does not stop at it: the second step
        plays a real hand and passes its own judgement (`surface.md` §2, §6, FAM-14.10).
        """
        log = []

        def refused_step():
            log.append("refused")
            return J.factory("encoder", J.UNKNOWN_ENCODING)

        def playing_step():
            log.append("played")
            return self.played()

        case = {
            "id": "hrnj-1-2-refusing-step",
            "steps": [refused_step, playing_step],
            "expect": [{"kind": "refused", "step": 0}, {"kind": "zero-sum", "step": 1}],
        }
        result = self.driven(case, "HRNJ-1.2")
        self.assertEqual(
            log, ["refused", "played"],
            "the step pass does not stop at a step that refused -- a case's later steps "
            "may be independent, and each step's outcome is judged separately "
            "(docs/L2/harness/surface.md §2, FAM-14.9): %r" % (log,),
        )
        first = result["steps"][0]
        self.assertIs(
            first["refused"], True,
            "a step that raised is recorded as refused (docs/L2/harness/surface.md §2): "
            "%r" % (first,),
        )
        self.assertIsInstance(
            first["outcome"], dict,
            "a raised step's outcome is the refusal observation of §2, a mapping: %r"
            % (first["outcome"],),
        )
        self.assertIs(
            first["outcome"].get("refused"), True,
            "the refusal observation carries the declared flag `refused`, which is the "
            "fact the `refused` kind reads -- never a wording "
            "(docs/L2/harness/surface.md §2, §6): %r" % (first["outcome"],),
        )
        raised, owner_class, owner_message = J.refusal_of(
            lambda: J.build_encoder(J.UNKNOWN_ENCODING)
        )
        self.assertTrue(
            raised,
            "features.build_encoder must refuse the undeclared encoding %r, or there is "
            "no refusal for the driver to observe (docs/L2/features/surface.md §4): %r"
            % (J.UNKNOWN_ENCODING, owner_message),
        )
        error = str(first["outcome"].get("error", ""))
        self.assertIn(
            owner_class.lower(), error.lower(),
            "the refusal the driver recorded is the owner's own -- its class name appears "
            "in the observation, because the harness reports what the owning entry point "
            "raised and repairs nothing (docs/L2/harness/surface.md §2, §4): %r"
            % (first["outcome"],),
        )
        self.assertIn(
            owner_message.lower(), error.lower(),
            "the refusal the driver recorded carries the owner's own message unchanged "
            "(docs/L2/harness/surface.md §2, §4, D-13): %r against %r"
            % (first["outcome"], owner_message),
        )
        self.assertIs(
            result["steps"][1]["refused"], False,
            "the second step returned a value, so it is not a refusal "
            "(docs/L2/harness/surface.md §2): %r" % (result["steps"][1],),
        )
        self.assert_verdict(
            result, "pass",
            "a case that expected the refusal and a balanced episode",
            "docs/L2/harness/surface.md §2, §6",
        )
        self.assertEqual(
            result["hands"], 1,
            "a refusal observation is not a hand: only the episode's one hand is counted "
            "(docs/L2/harness/surface.md §2, H-5): %r" % (result["hands"],),
        )

    def test_hrnj_1_3_a_step_judged_twice_must_pass_both_judgements(self):
        """HRNJ-1.3 two entries over one step both decide the verdict.

        A cell record is both zero-sum in its chip deltas and counted in its outcomes, so
        two entries over the same step both pass and the case passes; the same step
        judged by `counted` and then by `refused` fails, because the second judgement
        does not hold -- "a step judged twice must pass both judgements"
        (`docs/L2/harness/surface.md` §2, §6, `records.md` §9).
        """
        cell = self.cell()
        both_pass = {
            "id": "hrnj-1-3-both-pass",
            "steps": [lambda: cell],
            "expect": [{"kind": "counted", "step": 0}, {"kind": "zero-sum", "step": 0}],
        }
        result = self.driven(both_pass, "HRNJ-1.3 (both pass)")
        self.assertEqual(
            len(result["expectations"]), 2,
            "one expectation entry per entry declared, even when two entries name one "
            "step (docs/L2/harness/surface.md §2): %r" % (result["expectations"],),
        )
        self.assertEqual(
            [entry["step"] for entry in result["expectations"]], [0, 0],
            "both entries judge the step their index names "
            "(docs/L2/harness/surface.md §2): %r" % (result["expectations"],),
        )
        self.assertEqual(
            [entry["verdict"] for entry in result["expectations"]], ["pass", "pass"],
            "the cell satisfies both kinds -- a cell's two directions are the same hands "
            "seen from each seat, so their mean chip deltas balance, and each direction's "
            "wins + ties + losses is the cell's own `hands` (docs/L2/harness/surface.md "
            "§6, records.md §9): %r" % (result["expectations"],),
        )
        self.assert_verdict(
            result, "pass", "a step judged twice, passing both judgements",
            "docs/L2/harness/surface.md §2",
        )
        one_fails = {
            "id": "hrnj-1-3-one-fails",
            "steps": [lambda: cell],
            "expect": [{"kind": "counted", "step": 0}, {"kind": "refused", "step": 0}],
        }
        failed = self.driven(one_fails, "HRNJ-1.3 (one fails)")
        self.assertEqual(
            [entry["verdict"] for entry in failed["expectations"]], ["pass", "fail"],
            "every entry over a step is judged: the cell accounts for its hands, and it "
            "did not refuse, so the second judgement fails "
            "(docs/L2/harness/surface.md §2, §6): %r" % (failed["expectations"],),
        )
        self.assert_verdict(
            failed, "fail", "a step that fails one of its two judgements",
            "docs/L2/harness/surface.md §2",
        )
        self.assertIn(
            "refused", str(failed["reason"]).lower(),
            "the case's `reason` names the kind that failed, so a layer return can cite "
            "what failed (docs/L2/harness/surface.md §2, §6): %r" % (failed["reason"],),
        )

    def test_hrnj_1_4_a_step_no_entry_judges_is_a_named_failure(self):
        """HRNJ-1.4 an unjudged step fails the case and is named.

        A kind name judges the case's **last** step, so a two-step case expecting one
        kind leaves its first step unjudged.  `docs/L2/harness/surface.md` §2 makes that
        a named failure: "a verdict over a step nobody judged is not a verdict about the
        case as run".
        """
        first = self.played()
        second = J.play_hand(
            J.DEAL_SEED_OTHER,
            J.build_baseline("always-call", J.BASELINE_SEED),
            J.build_baseline("random", J.BASELINE_SEED_OTHER),
        )
        case = {
            "id": "hrnj-1-4-unjudged-step",
            "steps": [lambda: first, lambda: second],
            "expect": ["zero-sum"],
        }
        result = self.driven(case, "HRNJ-1.4")
        self.assert_verdict(
            result, "fail", "a case with a step no expectation judges",
            "docs/L2/harness/surface.md §2",
        )
        self.assertIn(
            "step 0", str(result["reason"]).lower(),
            "the failure names the step nobody judged, because a verdict over a step "
            "nobody judged is not a verdict about the case as run "
            "(docs/L2/harness/surface.md §2, records.md §14): %r" % (result["reason"],),
        )
        self.assertEqual(
            len(result["steps"]), 2,
            "both steps still ran, one entry each: the judgement is about the case as "
            "run (docs/L2/harness/surface.md §2): %r" % (result["steps"],),
        )
        self.assertEqual(
            [entry["index"] for entry in result["steps"]], [0, 1],
            "both steps were called, so both have an entry in declared order: a kind "
            "name judges the last one and the earlier one is the unjudged step "
            "(docs/L2/harness/surface.md §2): %r" % (result["steps"],),
        )
        self.assertEqual(
            result["hands"], 2,
            "an unjudged step's hands are still counted, because `hands` is read off the "
            "outcomes and not off the verdict (docs/L2/harness/surface.md §2, H-5): %r"
            % (result["hands"],),
        )

    def test_hrnj_1_5_drive_never_raises_for_the_case_it_is_handed(self):
        """HRNJ-1.5 every malformed case is a named failure inside the result.

        `docs/L2/harness/surface.md` §2 (and `docs/L3/harness/driver.md` §1) contract
        `drive` for **no** refusals: a case that is not a mapping, a missing or empty
        `id`, `steps` or `expect`, a step that is not callable, an unlisted kind, an
        out-of-range step index and an unreadable entry are each a `fail` with a sentence
        in `reason`, because a broken case must fail rather than error in the caller's
        runner (FAM-14.10, H-6).
        """
        malformed = {
            "not a mapping": "hrnj-1-5-not-a-mapping",
            "no id": {"steps": [lambda: 1], "expect": ["zero-sum"]},
            "empty id": {"id": "", "steps": [lambda: 1], "expect": ["zero-sum"]},
            "no steps": {"id": "hrnj-1-5-no-steps", "expect": ["zero-sum"]},
            "empty steps": {"id": "hrnj-1-5-empty-steps", "steps": [],
                            "expect": ["zero-sum"]},
            "no expect": {"id": "hrnj-1-5-no-expect", "steps": [lambda: 1]},
            "a step not callable": {"id": "hrnj-1-5-step", "steps": [17],
                                    "expect": ["zero-sum"]},
            "unlisted kind": {"id": "hrnj-1-5-kind", "steps": [lambda: 1],
                              "expect": [J.UNKNOWN_KIND]},
            "an out-of-range step": {"id": "hrnj-1-5-index", "steps": [lambda: 1],
                                     "expect": [{"kind": "zero-sum", "step": 9}]},
            "an unreadable entry": {"id": "hrnj-1-5-entry", "steps": [lambda: 1],
                                    "expect": [{"no": "kind"}]},
        }
        for label, case in malformed.items():
            result = self.driven(case, "HRNJ-1.5 (%s)" % (label,))
            self.assertIsInstance(
                result, dict,
                "a malformed case (%s) is reported, and inside a mapping the caller can "
                "read (docs/L2/harness/surface.md §2, H-6): %r" % (label, result),
            )
            self.assert_verdict(
                result, "fail", "the malformed case %r" % (label,),
                "docs/L2/harness/surface.md §2",
            )
            self.assertTrue(
                str(result.get("reason", "")).strip(),
                "the malformed case %r fails with one sentence naming what was wrong, so "
                "the caller can cite it (docs/L2/harness/surface.md §2, §6): %r"
                % (label, result),
            )

    def test_hrnj_1_6_the_drivers_verdict_is_the_one_expect_gives_directly(self):
        """HRNJ-1.6 judging through the driver is judging through `expect`.

        `docs/L2/harness/surface.md` §2: "judging is `expect`: one kind and one observed
        value give the same verdict here as when a battery calls `expect` directly, so
        the driver adds no second judging rule".  The case hands the driver three real
        module records and two values that fail their kind, and compares each judged
        entry with the direct call -- verdict and reason both (`surface.md` §2, §6,
        FAM-14.8).
        """
        walk = J.shared_walk()
        outside = next(
            ((record, legal) for record, legal in walk
             if not any(J.same_descriptor("fold", candidate) for candidate in legal)),
            None,
        )
        self.assertIsNotNone(
            outside,
            "the battery's hand must offer a decision where folding is illegal, or the "
            "legal set it tests cannot be left: %r" % ([list(legal) for _r, legal in walk],),
        )
        outside_record, outside_legal = outside
        observations = [
            ("zero-sum", self.played(), "engine.play_hand's episode"),
            ("zero-sum", self.cell(), "evaluation.match's cell"),
            ("counted", self.cell(), "evaluation.match's cell"),
            ("zero-sum", {"seat 0": 5, "seat 1": -4}, "seat deltas that do not balance"),
            ("zero-sum", 7, "a bare number, which states no deltas"),
            ("legal-choice",
             {"chosen": list(outside_legal)[0], "legal": list(outside_legal)},
             "a choice inside a real decision's legal set"),
            ("legal-choice",
             {"chosen": "fold", "legal": list(outside_legal)},
             "a fold at a decision where folding is illegal"),
            ("refused", {"refused": True, "error": "UnknownEncoding: x"},
             "a refusal observation"),
            ("refused", outside_record,
             "an engine readout, which is a value and not a refusal"),
        ]
        for kind, observation, what in observations:
            case = {
                "id": "hrnj-1-6-%s" % (kind,),
                "steps": [lambda observation=observation: observation],
                "expect": [kind],
            }
            result = self.driven(case, "HRNJ-1.6 (%s)" % (what,))
            direct = J.expect(kind, observation)
            self.assertEqual(
                len(result["expectations"]), 1,
                "one entry judges the case's last step (docs/L2/harness/surface.md §2): "
                "%r" % (result["expectations"],),
            )
            judged = result["expectations"][0]
            self.assertEqual(
                judged["verdict"], J.verdict_of(direct),
                "the driver's verdict over %r under %r must be the verdict `expect` gives "
                "for the same value, because the driver adds no second judging rule "
                "(docs/L2/harness/surface.md §2, §6): %r against %r"
                % (what, kind, judged, direct),
            )
            self.assertEqual(
                judged["reason"], J.reason_of(direct),
                "the driver reports `expect`'s own reason verbatim, so a case that fails "
                "through the driver fails for the reason the expectation gave "
                "(docs/L2/harness/surface.md §2, §6): %r against %r" % (judged, direct),
            )
            self.assertEqual(
                J.verdict_of(result), judged["verdict"],
                "the case's verdict is its judgements': one passing entry passes the "
                "case, one failing entry fails it (docs/L2/harness/surface.md §2): %r"
                % (result,),
            )

    def test_hrnj_1_7_hands_are_counted_from_the_outcomes_the_steps_returned(self):
        """HRNJ-1.7 one hand per episode, a cell's own hands, and none for anything else.

        `docs/L2/harness/surface.md` §2 (H-5): `hands` is read off the outcomes -- one per
        episode record, the `hands` a cell record declares, and nothing for any other
        value, a refusal observation included.  The four steps return an episode, a cell,
        a composed choice and a refusal, so the case counts `1 + HANDS` and not four
        (`surface.md` §2, `records.md` §5, §9).
        """
        record, legal = J.readout_and_legal(J.DEAL_SEED)

        def refusing():
            return J.factory("pool", {"members": [], "m": 999, "frozen": True})

        case = {
            "id": "hrnj-1-7-hands",
            "steps": [
                lambda: self.played(),
                lambda: self.cell(),
                lambda: {"chosen": list(legal)[0], "legal": list(legal)},
                refusing,
            ],
            "expect": [
                {"kind": "zero-sum", "step": 0},
                {"kind": "counted", "step": 1},
                {"kind": "legal-choice", "step": 2},
                {"kind": "refused", "step": 3},
            ],
        }
        result = self.driven(case, "HRNJ-1.7")
        self.assert_verdict(
            result, "pass", "a case whose four steps each pass their judgement",
            "docs/L2/harness/surface.md §2",
        )
        self.assertEqual(
            result["hands"], 1 + J.HANDS_SMALL,
            "the hands are the outcomes' own: one for the episode record and the cell's "
            "declared %d, and nothing for the composed choice or the refusal "
            "(docs/L2/harness/surface.md §2, H-5): %r"
            % (J.HANDS_SMALL, result["hands"]),
        )
        self.assertIs(
            result["steps"][3]["refused"], True,
            "the fourth step's real `evaluation.build_pool` refusal is recorded as a "
            "refusal and contributes no hand (docs/L2/harness/surface.md §2, §6): %r"
            % (result["steps"][3],),
        )
        two_values = {
            "id": "hrnj-1-7-hands-without-the-two-extra-steps",
            "steps": [lambda: self.played(), lambda: self.cell()],
            "expect": [{"kind": "zero-sum", "step": 0},
                       {"kind": "counted", "step": 1}],
        }
        without = self.driven(two_values, "HRNJ-1.7 (the two hand-bearing steps alone)")
        self.assertEqual(
            without["hands"], result["hands"],
            "the composed choice and the refusal observation add no hand: the case that "
            "returns them counts what the case without them counts "
            "(docs/L2/harness/surface.md §2, H-5): %r against %r"
            % (without["hands"], result["hands"]),
        )
        self.assertEqual(
            int(result["steps"][1]["outcome"]["hands"]), J.HANDS_SMALL,
            "the cell the harness drove reports its own `hands`, which is the number the "
            "driver added (docs/L2/harness/surface.md §2, records.md §9): %r"
            % (result["steps"][1]["outcome"],),
        )


if __name__ == "__main__":
    unittest.main()
