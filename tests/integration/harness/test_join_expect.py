"""The expectation join -- HRNJ-4.

`docs/L2/harness/surface.md` §6: one kind and one observed value give one verdict, and
the four kinds "read, in this order" the shapes the modules really return -- an episode
record's `payoffs`, a cell's two directions' `mean_chip_delta`, a cell's `hands`, a
decision's `legal` set, and the refusal observation the driver builds for a step that
raised (`records.md` §5, §9, §14).  Three properties are the join: every listed kind is
**total** (a value it cannot read is a named failure, never a raise and never a silence),
**deterministic** (one value and one kind give one verdict in a process and across
processes, because a verdict reads only the value it was handed), and a refusal is read
from a declared flag and never from the words a record chose (`surface.md` §6, H-1,
`docs/L3/harness/expectations.md` §2-§4, `docs/L1/battery.md` §5).  So the totality sweep
carries both families of value §6's reader branches on -- the flat values and the
cell-shaped records a league layer hands a case -- because a sweep of flat values alone
never enters the branch that reads a cell's two means (FAM-14.8, FAM-14.10).

The observed values are the modules', not the battery's: an episode `engine.play_hand`
played, a cell `evaluation.match` played, a choice an agent made at a real `readout`, and
a refusal `features` really produced through `harness.factory`.  What the battery invents
is the *value*, never the kind -- the four kinds are this module's own set, discovered
from `fixtures()` (`records.md` §14, D-13, D-15, FAM-14.8, FAM-16.36).
"""

import copy
import importlib.util
import json
import os
import subprocess
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


class ExpectJoin(J.JoinCase):
    """HRNJ-4 -- the four kinds read what the five modules really return."""

    def judged(self, kind, observation, what):
        """One verdict, with the record's declared keys checked on the way."""
        return self.checked(J.expect(kind, observation), kind, what)

    def checked(self, verdict, kind, what):
        """The record checks HRNJ-4 makes of every verdict `expect` returned."""
        self.assert_required_keys(
            verdict, J.VERDICT_KEYS, "the verdict for %r under %r" % (what, kind),
            "docs/L2/harness/surface.md §6",
        )
        self.assertEqual(
            verdict["kind"], kind,
            "the verdict states the kind as handed, verbatim, because a layer return "
            "cites it (docs/L2/harness/surface.md §6, FAM-16.36): %r" % (verdict,),
        )
        self.assertIn(
            verdict["verdict"], ("pass", "fail"),
            "a verdict is `pass` or `fail` and never a third value: %r" % (verdict,),
        )
        if verdict["verdict"] == "fail":
            self.assertIn(
                J.token(kind), J.token(verdict["reason"]),
                "a failure's sentence names the kind verbatim, so a reader can find it by "
                "its token (docs/L2/harness/surface.md §6, FAM-16.36): %r" % (verdict,),
            )
        else:
            self.assertIsNone(
                verdict["reason"],
                "a passing verdict states it once, in `verdict`, and its `reason` is "
                "None (docs/L2/harness/surface.md §6): %r" % (verdict,),
            )
        return verdict

    def not_raised(self, kind, observation, what):
        """One checked verdict, with §6's Total rule asserted at the call itself.

        `docs/L2/harness/surface.md` §6: "every listed kind yields a verdict for *any*
        observed value; a value a kind cannot read is a named failure and never a pass and
        never a silence".  A raise from `expect` is not a verdict, so the call is made
        inside this control: the failure it produces says "must not raise" rather than
        surfacing as an opaque error in the runner (FAM-14.8, FAM-16.36).
        """
        try:
            record = J.expect(kind, observation)
        except J.SurfaceAbsent:
            raise
        except Exception as exc:  # noqa: BLE001 - the raise is the finding
            self.fail(
                "%s: `harness.expect(%r, ...)` must return one verdict record for *any* "
                "observed value and must never raise, because a value a kind cannot read "
                "is a named failure and never a silence (docs/L2/harness/surface.md §6, "
                "FAM-14.8); it raised %s: %s"
                % (what, kind, type(exc).__name__, exc)
            )
        return self.checked(record, kind, what)

    def driven(self, case, what):
        """`harness.drive` a case, failing loudly if it raised for that case.

        `docs/L2/harness/surface.md` §2: "`drive` **never raises**" -- a case it cannot run
        is a named failure inside the result, so a raise out of the driver is a contract
        violation in the harness and not a finding about the case (H-6, FAM-14.10).
        """
        try:
            return J.drive(case)
        except J.SurfaceAbsent:
            raise
        except Exception as exc:  # noqa: BLE001 - the raise is the finding
            self.fail(
                "%s: `harness.drive` never raises for the case it is handed, and it "
                "judges what a step returned rather than catching around it, so a kind "
                "that raised on a real record would escape as an error in the caller's "
                "runner (docs/L2/harness/surface.md §2, §6, FAM-14.10); it raised %s: %s"
                % (what, type(exc).__name__, exc)
            )

    def unread_by(self, kind):
        """Values no reader of any kind can take for a pass."""
        return [None, 7, 3.5, "a sentence", (), [], {}, {"x": 1}]

    def test_hrnj_4_1_zero_sum_reads_an_episode_and_a_cell(self):
        """HRNJ-4.1 `zero-sum` reads `engine.play_hand`'s and `evaluation.match`'s own.

        `docs/L2/harness/surface.md` §6: the deltas are read "from an episode record's
        `payoffs`, a cell record's two directions' `mean_chip_delta`", and the kind fails
        when "the deltas do not sum to zero, or the value states no per-seat deltas".  The
        episode and the cell are the modules' own, so the passing verdicts are statements
        about the engine's and the league's arithmetic -- never about a value the battery
        composed (`records.md` §5, §9, ASM-12, FAM-7).
        """
        episode = J.shared_episode()
        cell = J.shared_cell()
        passing = [
            ("engine.play_hand's episode", episode),
            ("evaluation.match's cell", cell),
            ("engine.payoffs of a completed hand", J.shared_payoffs()),
            ("a two-seat map of the battery's own", {"seat 0": 12, "seat 1": -12}),
        ]
        for what, observation in passing:
            verdict = self.judged("zero-sum", observation, what)
            self.assertEqual(
                verdict["verdict"], "pass",
                "the %s balances: the engine's payoffs sum to zero and a cell's two "
                "directions are the same hands seen from each seat "
                "(docs/L2/harness/surface.md §6, records.md §5, §9, ASM-12, FAM-7): %r"
                % (what, verdict),
            )
        self.assertEqual(
            sum(float(delta) for delta in episode["payoffs"].values()), 0.0,
            "the episode the kind passed really is the engine's zero-sum record "
            "(records.md §5, protocol.md §2): %r" % (episode["payoffs"],),
        )
        self.assertEqual(
            len(cell["directions"]), 2,
            "the cell the kind read really is a two-direction cell record "
            "(records.md §9): %r" % (cell,),
        )
        failing = [
            ({"seat 0": 5, "seat 1": -4}, "seat deltas that do not balance"),
            (7, "a bare number, which states no per-seat deltas"),
            (J.pool_members(J.shared_pool()), "a pool record, which states none"),
        ]
        for observation, what in failing:
            verdict = self.judged("zero-sum", observation, what)
            self.assertEqual(
                verdict["verdict"], "fail",
                "`zero-sum` fails %s rather than passing a value it cannot read "
                "(docs/L2/harness/surface.md §6): %r" % (what, verdict),
            )

    def test_hrnj_4_2_counted_reads_a_real_cells_arithmetic(self):
        """HRNJ-4.2 `counted` closes a cell's outcomes against its own `hands`.

        `docs/L2/harness/surface.md` §6: the kind passes when "each direction's
        wins + ties + losses equals the `hands` it reports", which is the arithmetic
        `protocol.md` §2 requires of every cell ("Every cell reports wins, ties and
        losses ... and the hands played").  The battery reads the arithmetic out of the
        cell `evaluation.match` played, then breaks one direction of a copy: the kind must
        notice, or it is not counting anything (`records.md` §9, FAM-7).
        """
        cell = J.shared_cell()
        self.assert_required_keys(
            cell, J.CELL_KEYS, "the cell record `evaluation.match` returns",
            "docs/L1/records.md §9",
        )
        verdict = self.judged("counted", cell, "evaluation.match's cell")
        self.assertEqual(
            verdict["verdict"], "pass",
            "a cell accounts for every hand it reports, and the cell the league played is "
            "one (docs/L2/harness/surface.md §6, records.md §9, protocol.md §2): %r"
            % (verdict,),
        )
        for position, direction in enumerate(cell["directions"]):
            self.assert_required_keys(
                direction, J.DIRECTION_KEYS, "direction %d of the cell" % (position,),
                "docs/L1/records.md §9",
            )
            self.assertEqual(
                int(direction["wins"]) + int(direction["ties"]) + int(direction["losses"]),
                int(cell["hands"]),
                "the cell the kind passed accounts for its hands direction by direction "
                "(docs/L1/records.md §9, protocol.md §2): %r over %r hands"
                % (direction, cell["hands"]),
            )
        broken = json.loads(json.dumps(cell, default=list))
        broken["directions"][0]["wins"] = int(broken["directions"][0]["wins"]) + 1
        verdict = self.judged("counted", broken, "a cell whose first direction counts one hand more")
        self.assertEqual(
            verdict["verdict"], "fail",
            "a cell whose counts do not add up to its `hands` is named a failure: the "
            "kind judges the arithmetic and not the provenance "
            "(docs/L2/harness/surface.md §6): %r" % (verdict,),
        )
        for what, observation in [("a mapping with hands and no directions", {"hands": 5}),
                                  ("an episode record", J.shared_episode())]:
            verdict = self.judged("counted", observation, what)
            self.assertEqual(
                verdict["verdict"], "fail",
                "`counted` fails %s: the value is not a cell record carrying its "
                "directions and hands (docs/L2/harness/surface.md §6): %r"
                % (what, verdict),
            )

    def test_hrnj_4_3_legal_choice_reads_a_real_decisions_legal_set(self):
        """HRNJ-4.3 `legal-choice` decides membership, never legality.

        `docs/L2/harness/surface.md` §6: the kind "judges the chosen descriptor is one of
        the legal descriptors" and "the harness decides **no** legality: it asks whether
        the descriptor the work returned is one of the descriptors it was handed".  The
        set is `engine.legal_actions`' own at a real decision, and the chosen descriptor is
        what an agent chose there through `features.decode_action` (`e2e-surface.md` §2,
        D-2).
        """
        record, legal = J.readout_and_legal(J.DEAL_SEED)
        observation = J.encode(J.shared_encoder(), record)
        decision = J.act(J.build_learner(J.learner_spec()), observation, J.legal_indices(legal))
        chosen = J.decode_action(J.chosen_index(decision))
        value = {"chosen": chosen, "legal": list(legal)}
        verdict = self.judged("legal-choice", value, "a decision at a real readout")
        self.assertEqual(
            verdict["verdict"], "pass",
            "the descriptor an agent chose at a real decision is one of the descriptors "
            "the engine declared legal there, so the value satisfies the kind "
            "(docs/L2/harness/surface.md §6, e2e-surface.md §2): %r against %r"
            % (chosen, list(legal)),
        )
        seam_policy = J.seam(J.SEAM_LABEL)
        seam_choice = seam_policy(record, legal)
        verdict = self.judged(
            "legal-choice", {"chosen": seam_choice, "legal": list(legal)},
            "what a seam returned for that decision",
        )
        self.assertEqual(
            verdict["verdict"], "pass",
            "a seam's descriptor is a legal choice under the same kind, because a seam "
            "returns a member of `legal_actions` and nothing else "
            "(docs/L2/harness/surface.md §5, §6, D-2): %r" % (verdict,),
        )
        walk = J.shared_walk()
        closed = next(
            ((record_, legal_) for record_, legal_ in walk
             if not any(J.same_descriptor("fold", candidate) for candidate in legal_)),
            None,
        )
        self.assertIsNotNone(
            closed,
            "the battery's hand offers a decision where folding is illegal, which is the "
            "decision a fold can be outside of (docs/L2/engine/surface.md §2): %r"
            % ([list(legal_) for _r, legal_ in walk],),
        )
        _closed_record, closed_legal = closed
        verdict = self.judged(
            "legal-choice", {"chosen": "fold", "legal": list(closed_legal)},
            "a fold at a decision where folding is not legal",
        )
        self.assertEqual(
            verdict["verdict"], "fail",
            "a chosen descriptor outside the legal set is a named failure, because a "
            "policy that returns an illegal action is a contract violation and not a "
            "fold (docs/L2/harness/surface.md §6, e2e-surface.md §2, D-2): %r"
            % (verdict,),
        )
        for what, observation in [("a value with no legal descriptors", {"chosen": "fold"}),
                                  ("a value with no chosen descriptor", {"legal": ["fold"]})]:
            verdict = self.judged("legal-choice", observation, what)
            self.assertEqual(
                verdict["verdict"], "fail",
                "`legal-choice` fails %s (docs/L2/harness/surface.md §6): %r"
                % (what, verdict),
            )

    def test_hrnj_4_4_refused_reads_the_flag_the_driver_and_the_owners_declare(self):
        """HRNJ-4.4 a refusal is a declared flag, never a word.

        `docs/L2/harness/surface.md` §6: the kind passes when "the value is a refusal
        observation: a mapping whose `refused` flag is true -- the shape §2's driver builds
        for a step that raised", and "a refusal is never inferred from wording".  The
        observation is one the surface really produced: a `factory` call the owning module
        refused, driven through `harness.drive`, whose step outcome is that mapping
        (`surface.md` §2, §6, `records.md` §14, D-13).
        """
        def refusing():
            return J.factory("pool", {"members": [], "m": 999, "frozen": True})

        case = {"id": "hrnj-4-4-refusal", "steps": [refusing], "expect": ["refused"]}
        result = J.drive(case)
        self.assertEqual(
            J.verdict_of(result), "pass",
            "a case that expected a refusal passes, because the step is judged by the "
            "`refused` kind and not by the exception it raised "
            "(docs/L2/harness/surface.md §2, §6): %r" % (result,),
        )
        observation = result["steps"][0]["outcome"]
        verdict = self.judged("refused", observation, "a driven refusal observation")
        self.assertEqual(
            verdict["verdict"], "pass",
            "the value the driver built for the step that raised satisfies the kind the "
            "case declared (docs/L2/harness/surface.md §2, §6): %r" % (verdict,),
        )
        self.assertEqual(
            verdict["verdict"], result["expectations"][0]["verdict"],
            "the driver's judgement is `expect`'s: the same observation under the same "
            "kind gives the same verdict here as in the case "
            "(docs/L2/harness/surface.md §2): %r against %r"
            % (verdict, result["expectations"][0]),
        )
        self.assertIs(
            observation.get("refused"), True,
            "the flag the kind read is the one the driver declared, and it is in the "
            "value and not in its text (docs/L2/harness/surface.md §2, §6): %r"
            % (observation,),
        )
        for what, value in [
            ("an episode the engine really played", J.shared_episode()),
            ("a mapping that carries the word and no flag", {"error": "refused"}),
            ("a mapping whose flag is false", {"refused": False, "error": "refused"}),
        ]:
            verdict = self.judged("refused", value, what)
            self.assertEqual(
                verdict["verdict"], "fail",
                "`refused` fails %s: the observed work returned a value rather than "
                "refusing, and a refusal is never inferred from wording "
                "(docs/L2/harness/surface.md §6, D-13): %r" % (what, verdict),
            )

    def test_hrnj_4_5_every_listed_kind_is_total(self):
        """HRNJ-4.5 a kind yields a verdict for any value, never a raise and never silence.

        `docs/L2/harness/surface.md` §6: "every listed kind yields a verdict for *any*
        observed value; a value a kind cannot read is a named failure and never a pass and
        never a silence".  The battery hands each listed kind values no reader can take for
        a pass and requires a `fail` -- a raise here would be the kind raising for a shape
        it did not expect, which `expectations.md` §3 forbids (FAM-14.8).

        Two families of value, because §6's reader has two branches.  A flat value only
        reaches the reader's last branch; a mapping that declares `directions` takes the
        cell branch, which is the shape a league record hands a case, so the sweep carries
        cell-shaped values whose means are a string, a `None` and a boolean beside a number
        -- composed from `evaluation.match`'s own cell, whose keys, counts and `hands` stay
        the league's (`records.md` §9, `surface.md` §2, FAM-14.10).
        """
        for kind in J.DECLARED_KINDS:
            for value in self.unread_by(kind):
                verdict = self.not_raised(kind, value, "the value %r" % (value,))
                self.assertEqual(
                    verdict["verdict"], "fail",
                    "`%s` fails the value %r: a kind that cannot read a value names a "
                    "failure and never passes it (docs/L2/harness/surface.md §6): %r"
                    % (kind, value, verdict),
                )
        for label, first, second in J.UNREADABLE_MEANS:
            value = J.cell_shaped_like(first, second)
            what = "a cell-shaped value whose first direction carries %s" % (label,)
            judged = {}
            for kind in J.DECLARED_KINDS:
                judged[kind] = self.not_raised(kind, value, "%s, under %r" % (what, kind))
            self.assertEqual(
                judged["counted"]["verdict"], "pass",
                "%s is still a real cell record -- the league's counts close against its "
                "own `hands` -- so the sweep reached the cell-shaped branch and not a "
                "flat one, and only the mean the kind cannot read is at issue "
                "(docs/L2/harness/surface.md §6, records.md §9): %r"
                % (what, judged["counted"]),
            )
            verdict = judged["zero-sum"]
            self.assertEqual(
                verdict["verdict"], "fail",
                "%s states no two per-seat chip deltas, because a mean that is not a "
                "quantity is one the kind cannot read: `zero-sum` names that failure for "
                "the cell branch instead of raising on it or passing it "
                "(docs/L2/harness/surface.md §6, records.md §9, FAM-14.8): %r"
                % (what, verdict),
            )
            self.assertIn(
                "per-seat", verdict["reason"],
                "and the fact it names is the one §6 gives for a value that states no two "
                "per-seat chip deltas (docs/L2/harness/surface.md §6): %r"
                % (verdict["reason"],),
            )
        for kind in J.DECLARED_KINDS:
            verdict = J.expect(kind, J.shared_cell())
            self.assertIn(
                J.verdict_of(verdict), ("pass", "fail"),
                "`%s` gives a verdict for a real record too, so the battery knows the kind "
                "is judging rather than defaulting (docs/L2/harness/surface.md §6): %r"
                % (kind, verdict),
            )

    def test_hrnj_4_6_one_kind_and_one_value_give_one_verdict(self):
        """HRNJ-4.6 a verdict is deterministic and reads only the value it was handed.

        `docs/L2/harness/surface.md` §6: "one kind and one observed value give one
        verdict, in one process and across processes: an expectation reads only the value
        it was handed -- never a clock, a stream, a file, an ambient fixture or a second
        observation -- and never mutates it" (FAM-16.36, ASM-2).
        """
        walk = J.shared_walk()
        observations = [
            ("zero-sum", J.shared_episode()),
            ("zero-sum", J.shared_cell()),
            ("zero-sum", {"seat 0": 5, "seat 1": -4}),
            ("counted", J.shared_cell()),
            ("counted", {"hands": 3, "directions": [{"wins": 1, "ties": 0, "losses": 1}]}),
            ("legal-choice", {"chosen": list(walk[0][1])[0], "legal": list(walk[0][1])}),
            ("refused", {"refused": True, "error": "UnknownEncoding: x"}),
            ("refused", J.shared_cell()),
        ]
        for kind, observation in observations:
            before = J.canon(observation)
            first = J.expect(kind, observation)
            second = J.expect(kind, observation)
            self.assertEqual(
                (first["verdict"], first["reason"]), (second["verdict"], second["reason"]),
                "one kind and one observed value give one verdict twice: the verdict is a "
                "function of the value and of nothing else (docs/L2/harness/surface.md §6, "
                "FAM-16.36): %r against %r" % (first, second),
            )
            self.assertEqual(
                J.canon(observation), before,
                "judging a value never mutates it, so a case may hand the same record to "
                "two kinds in either order (docs/L2/harness/surface.md §6): %r" % (kind,),
            )
            copied = J.expect(kind, copy.deepcopy(observation))
            self.assertEqual(
                (copied["verdict"], copied["reason"]), (first["verdict"], first["reason"]),
                "two equal values give two equal verdicts, so the verdict depends on the "
                "value and not on the identity it was handed "
                "(docs/L2/harness/surface.md §6, FAM-16.36): %r against %r"
                % (copied, first),
            )

    def test_hrnj_4_7_the_verdict_is_the_same_in_a_second_process(self):
        """HRNJ-4.7 `expect` gives the same verdict in a second process.

        `docs/L2/harness/surface.md` §6 makes determinism cross-process: a verdict "reads
        only the value it was handed".  The battery therefore runs the same judgements in
        a second interpreter over the same JSON round-tripped values and compares verdict
        and reason with this process's (`surface.md` §6, FAM-16.36, D-6).
        """
        values = [
            json.loads(json.dumps(J.shared_cell(), default=list)),
            {"seat 0": 5, "seat 1": -4},
            {"refused": True, "error": "UnknownEncoding: x"},
            {"chosen": "fold", "legal": ["check-call", "raise"]},
        ]
        kinds = list(J.DECLARED_KINDS)
        here = [[J.expect(kind, value) for kind in kinds] for value in values]
        script = (
            "import json, sys\n"
            "sys.path.insert(0, %r)\n"
            "import harness\n"
            "payload = json.load(sys.stdin)\n"
            "print(json.dumps([[harness.expect(kind, value) for kind in payload['kinds']]"
            " for value in payload['values']]))\n" % (J.SRC,)
        )
        completed = subprocess.run(
            [sys.executable, "-c", script],
            input=json.dumps({"kinds": kinds, "values": values}),
            capture_output=True, text=True, cwd=J.ROOT, timeout=300,
        )
        self.assertEqual(
            completed.returncode, 0,
            "the second process must run the same judgements, so a verdict can be read "
            "outside the process that produced it (docs/L2/harness/surface.md §6, D-6): "
            "%r" % (completed.stderr,),
        )
        there = json.loads(completed.stdout)
        for position, value in enumerate(values):
            for index, kind in enumerate(kinds):
                self.assertEqual(
                    (there[position][index].get("verdict"),
                     there[position][index].get("reason")),
                    (here[position][index]["verdict"], here[position][index]["reason"]),
                    "one kind and one value give one verdict in a second process too, "
                    "because the judgement reads the value and no ambient state "
                    "(docs/L2/harness/surface.md §6, FAM-16.36): %r under %r gave %r here "
                    "and %r there"
                    % (value, kind, here[position][index], there[position][index]),
                )

    def test_hrnj_4_8_a_kind_the_fixture_does_not_list_is_a_named_failure(self):
        """HRNJ-4.8 an unlisted kind fails by name; a non-name is refused.

        `docs/L2/harness/surface.md` §6 draws the asymmetry: "a string kind `fixtures()`
        does not list is **not** raised: it is a `fail` whose `reason` names the kind
        verbatim", while "a `kind` that is not a string" is an invalid argument under §1's
        rule and is refused by raising.  The battery invents the unlisted name, because an
        expectation kind is the harness's own set and never the battery's
        (`records.md` §14, FAM-14.8, FAM-16.36, D-15).
        """
        cell = J.shared_cell()
        for kind in (J.UNKNOWN_KIND, "zero_sum", "Zero-Sum", " counted"):
            verdict = self.judged(kind, cell, "an observed value under an unlisted kind")
            self.assertEqual(
                verdict["verdict"], "fail",
                "a string kind the fixture does not list is a named failure and never a "
                "silent pass (docs/L2/harness/surface.md §6): %r under %r"
                % (verdict, kind),
            )
            self.assertEqual(
                verdict["kind"], kind,
                "the named failure names the kind as handed, verbatim, so the case that "
                "rested on it can be cited (docs/L2/harness/surface.md §6, FAM-14.10): %r"
                % (verdict,),
            )
        for not_a_name in (17, None, ("zero-sum",), {"kind": "zero-sum"}):
            self.assert_refusal(
                lambda not_a_name=not_a_name: J.expect(not_a_name, cell),
                ("kind",),
                "a kind that is not a string is not a kind at all: %r"
                % (not_a_name,),
                "docs/L2/harness/surface.md §1, §6",
            )

    def test_hrnj_4_9_the_cell_shaped_branch_keeps_what_a_cell_really_states(self):
        """HRNJ-4.9 a cell branch that drops unreadable means still passes a real cell.

        `docs/L2/harness/surface.md` §6 reads a cell's deltas "from ... a cell record's two
        directions' `mean_chip_delta`", so a branch that keeps only quantities must keep the
        two means `evaluation.match` really writes: the real cell still passes, a composed
        cell whose two means are a finite pair summing to zero still passes, and a value
        with one readable mean and one unreadable one is a *named failure* rather than a
        raise or a pass -- the branch needs a pair of quantities and not two slots
        (`records.md` §9, §14, FAM-14.8, FAM-14.10).
        """
        cell = J.shared_cell()
        means = [row["mean_chip_delta"] for row in cell["directions"]]
        self.assertEqual(
            len(means), 2,
            "the cell `evaluation.match` returns carries one direction per seat, so two "
            "means are on offer for the kind to read (records.md §9, "
            "docs/L2/harness/surface.md §6): %r" % (cell["directions"],),
        )
        for mean in means:
            self.assertTrue(
                J.finite(mean),
                "both means of a real cell are quantities, which is why a reader that "
                "keeps quantities only keeps both of them (records.md §9, protocol.md §2): "
                "%r" % (means,),
            )
        self.assertLessEqual(
            abs(sum(float(mean) for mean in means)), 1e-9,
            "and they are each other's negative -- the same hands seen from each seat -- "
            "which is why the cell balances at all (records.md §9, ASM-12): %r" % (means,),
        )
        verdict = self.judged("zero-sum", cell, "evaluation.match's cell")
        self.assertEqual(
            verdict["verdict"], "pass",
            "a real cell still passes `zero-sum`: the reader drops nothing the league "
            "states as a quantity, so the branch is not narrowed past the record a case is "
            "really handed (docs/L2/harness/surface.md §6, FAM-14.8): %r" % (verdict,),
        )
        balanced = J.cell_shaped_like(2.5, -2.5)
        verdict = self.judged(
            "zero-sum", balanced,
            "a composed cell whose two means are a finite pair summing to zero",
        )
        self.assertEqual(
            verdict["verdict"], "pass",
            "a cell-shaped value whose two means are quantities summing to zero passes, so "
            "the branch judges the pair it reads rather than only the values the battery "
            "has already seen (docs/L2/harness/surface.md §6, §2, FAM-14.10): %r"
            % (verdict,),
        )
        half = J.cell_shaped_like(float(means[0]), "join-probe-half-readable")
        verdict = self.not_raised(
            "zero-sum", half,
            "a cell-shaped value whose first mean is a quantity and whose second is not",
        )
        self.assertEqual(
            verdict["verdict"], "fail",
            "one readable mean and one unreadable one is one delta and not a pair, so the "
            "value is a named failure: neither a raise out of the reader nor a pass on a "
            "mean it never read (docs/L2/harness/surface.md §6, FAM-14.8): %r"
            % (verdict,),
        )
        self.assertIn(
            "per-seat", verdict["reason"],
            "and the fact it names is the one §6 gives for a value that states no two "
            "per-seat chip deltas (docs/L2/harness/surface.md §6): %r"
            % (verdict["reason"],),
        )

    def test_hrnj_4_10_an_unreadable_mean_reaches_the_driver_as_a_named_failure(self):
        """HRNJ-4.10 `drive` reports the cell-shaped failure at its step and never raises.

        `docs/L2/harness/surface.md` §2: "`drive` **never raises**", and the outcome a kind
        is handed is "the value the step returned".  §6's Total rule is only observable
        where a real record is driven, and a cell-shaped value is what the league layer
        hands around: here a step plays `evaluation.match` itself and composes on that
        record a mean the kind cannot read, so the failure the case records cites the step
        and the kind, one expectation entry carries `fail`, and `drive` returns a record
        rather than raising out of its judging pass (FAM-14.8, FAM-14.10, `records.md` §9).
        """
        for label, first, second in J.UNREADABLE_MEANS:
            def step(first=first, second=second):
                played = J.match("always-call", "random", J.HANDS_SMALL, J.MATCH_SEED)
                return J.cell_shaped_like(first, second, played)

            case = {
                "id": "hrnj-4-10-cell-shaped-" + J.token(label),
                "steps": [step],
                "expect": ["zero-sum"],
            }
            result = self.driven(case, "%s through drive" % (label,))
            self.assert_required_keys(
                result, J.DRIVER_KEYS, "the case-result record for %r" % (label,),
                "docs/L2/harness/surface.md §2",
            )
            self.assertEqual(
                result["id"], case["id"],
                "the result repeats the case's own id verbatim, so the failure can be "
                "cited (docs/L2/harness/surface.md §2, FAM-14.9): %r" % (result["id"],),
            )
            self.assertEqual(
                len(result["expectations"]), 1,
                "exactly one expectation entry is recorded, so the failure is attributed "
                "to the expectation and not to a malformed case "
                "(docs/L2/harness/surface.md §2): %r" % (result,),
            )
            entry = result["expectations"][0]
            self.assertEqual(
                (entry["kind"], entry["step"], entry["verdict"]),
                ("zero-sum", 0, "fail"),
                "one entry is recorded for the step the expectation names, and its verdict "
                "is `fail`: the kind judged the cell-shaped outcome and could not read two "
                "per-seat deltas from it (docs/L2/harness/surface.md §2, §6): %r"
                % (entry,),
            )
            self.assertEqual(
                result["verdict"], "fail",
                "the case fails, because the expectation it rests on failed "
                "(docs/L2/harness/surface.md §2): %r" % (result,),
            )
            reason = result["reason"]
            self.assertIsInstance(
                reason, str,
                "a failed case states one sentence naming the step or the kind that "
                "failed (docs/L2/harness/surface.md §2): %r" % (reason,),
            )
            self.assertIn(
                "step 0", reason.lower(),
                "and the sentence names the step whose outcome was judged "
                "(docs/L2/harness/surface.md §2): %r" % (reason,),
            )
            self.assertIn(
                J.token("zero-sum"), J.token(reason),
                "and the kind that failed (docs/L2/harness/surface.md §2, §6): %r"
                % (reason,),
            )
            self.assertIn(
                "per-seat", reason.lower(),
                "and the fact the kind could not read, so an unreadable mean reaches a "
                "named failure and never a raise out of the driver's judging pass "
                "(docs/L2/harness/surface.md §6, FAM-14.8): %r" % (reason,),
            )
            observation = result["steps"][0]["outcome"]
            self.assertIs(
                result["steps"][0]["refused"], False,
                "the step returned the cell-shaped value rather than raising, so its "
                "outcome is that value and not a refusal observation "
                "(docs/L2/harness/surface.md §2): %r" % (result["steps"][0],),
            )
            self.assertEqual(
                (observation["directions"][0]["mean_chip_delta"],
                 observation["hands"]),
                (first, J.HANDS_SMALL),
                "the observed value is the cell the step played with the battery's mean "
                "where the case put it, judged as `records.md` §9 declares it "
                "(docs/L2/harness/surface.md §2, FAM-14.10): %r" % (observation,),
            )
            self.assertEqual(
                entry["verdict"],
                J.expect("zero-sum", observation)["verdict"],
                "the driver's judgement is `expect`'s and not a second rule: the same "
                "observation under the same kind gives the same verdict directly "
                "(docs/L2/harness/surface.md §2): %r" % (entry,),
            )


if __name__ == "__main__":
    unittest.main()
