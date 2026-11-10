"""FAM-14 — the harness is support, never a substitute for a real module.

`docs/L1/battery.md` §3 FAM-14, `docs/L1/module-map.md` §3 and §5, `docs/L1/records.md`
§14 and `docs/L1/e2e-surface.md` §3.6 (brief §5, D-13).  The six harness entry points
drive a case from pinned preconditions, build only the objects the map declares, and hand
back policies and expectations that still satisfy the shared contracts of
``e2e-surface.md`` §2 — they never re-implement the engine, the learner or the match.

The two vocabularies are read the way the design hands them down.  A **seam** takes any
label: its contract is the policy protocol and not the label, ``recording`` and
``synthetic`` are the documented behaviours, and any other label behaves as
``recording`` — so the battery may name its own seam.  An **expectation kind** is the
harness's own set, discovered from ``harness.fixtures()``: the battery invents an
*observed value* for a listed kind, never a kind, and an unlisted kind is a named failure
(``records.md`` §14, D-13, D-15, ``battery.md`` §4).

**The seam walk is on the shape in force.**  A seam is a policy of `e2e-surface.md` §2, so
what it must satisfy is the shape of the hands it is handed: today's three indices when no
shape is named (FAM-14.5, FAM-14.6, unchanged) and the named shape's six when it is
(FAM-14.12) — never an index outside the decision's legal set, and never a descriptor the
engine refuses (`shapes.md` §2, §5, D-29).
"""

import os
import sys
import unittest

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _records as R  # noqa: F401
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _records as R  # noqa: E402
    import _surface as S  # noqa: E402


class FAM14Harness(S.SurfaceCase):
    """Fixtures, factory, seam, expect, drive and timings, asserted as support."""

    # -- helpers -----------------------------------------------------------
    def case(self, case_id, steps, expected):
        return {"id": case_id, "steps": list(steps), "expect": list(expected)}

    def listed_expectations(self):
        """The driver's ``expect``: a kind the fixture lists, never one this battery made up."""
        return [self.an_expectation_kind()]

    def driven_case(self, case_id="FAM-14.9-seeded-episode", seed=S.SEED_G, ran=None):
        """A case over declared entry points, with an invented step and a listed kind."""

        def step():
            if ran is not None:
                ran.append(case_id)
            return self.play(seed)

        return self.case(case_id, [step], self.listed_expectations())

    def judged(self, kind, observation):
        """The verdict of one expectation, or the text of its named refusal.

        ``e2e-surface.md`` §3.6 contracts ``expect`` for a pass or a named failure, and §2
        lets an invalid argument be refused by raising and naming the contract it violated,
        so an observed value a kind does not accept is read as the named failure it is.
        """
        try:
            return self.ep("harness", "expect")(kind, observation)
        except S.SurfaceAbsent:
            raise
        except Exception as exc:
            return "%s: %s" % (type(exc).__name__, exc)

    def observations(self):
        """Observed values to judge: the invented ones first, then what the surface really returns."""
        return [
            {"seat 0": 12, "seat 1": -12},   # invented: a seat map that balances
            {"seat 0": 8, "seat 1": -5},     # invented: a seat map that does not
            [7, -7],                         # invented: the same fact as a sequence
            3,                               # invented: one bare observed number
            self.play(S.SEED_B),             # what engine.play_hand really returns
            self.ep("engine", "payoffs")(self.finished_hand(S.SEED_A)),
            self.match(hands=S.HANDS_TINY),  # what evaluation.match really returns
        ]

    def seam_plays_legally(self, kind, seed, shape=None):
        """A seam satisfies the policy protocol on the shape in force (`shapes.md` §2).

        ``shape`` is the shape the hands are dealt on and whose vocabulary the seam must
        answer in — today's three indices when no name is given, and the named shape's six
        otherwise (`e2e-surface.md` §2, §3.6, ``sizing.md`` §3).  It returns the decisions
        it observed so a case can assert what the walk reached.
        """
        policy = self.ep("harness", "seam")(kind)
        self.assertTrue(
            callable(policy),
            "harness.seam(%r) returns a policy in the sense of e2e-surface §2: %r"
            % (kind, policy),
        )
        vocabulary = set(self.vocabulary(shape))
        walk = self.decision_walk(seed, policy, limit=3, shape=shape)
        self.assertTrue(walk, "the %r seam answered no decision at all" % (kind,))
        for _hand, _readout, legal, action, index in walk:
            self.assertIn(
                index,
                vocabulary,
                "a %r seam chooses from the shape in force's vocabulary %r (e2e-surface "
                "§2, shapes.md §2): %r" % (kind, sorted(vocabulary), index),
            )
            self.assertIn(
                index,
                set(self.ep("features", "legal_indices")(legal)),
                "a %r seam chooses a legal index: %r against %r"
                % (kind, index, sorted(self.ep("features", "legal_indices")(legal))),
            )
            self.assertTrue(
                any(S.canon(action) == S.canon(candidate) for candidate in legal),
                "a %r seam returns a descriptor from legal_actions, never an illegal action "
                "(e2e-surface §2, D-2): %r" % (kind, action),
            )
        return walk

    # -- fixtures and factory ---------------------------------------------
    def test_fam14_1_fixtures_give_a_scratch_root_a_seed_and_a_device(self):
        """FAM-14.1 harness.fixtures pins a scratch root, a seed and a device."""
        fixtures = self.ep("harness", "fixtures")()
        roots = S.find_values(fixtures, "root")
        self.assertTrue(roots, "the fixture names its scratch root: %r" % (fixtures,))
        root = str(roots[0])
        os.makedirs(root, exist_ok=True)
        probe = os.path.join(root, "FAM-14.1.probe")
        with open(probe, "w", encoding="utf-8") as handle:
            handle.write("scratch")
        with open(probe, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "scratch", "the scratch root is writable")
        os.remove(probe)
        seeds = S.numbers(S.find_values(fixtures, "seed"))
        self.assertTrue(seeds, "the fixture pins a seed: %r" % (fixtures,))
        self.assertIn(
            "cpu",
            S.flatten_text(S.find_values(fixtures, "device")),
            "the fixture pins the device the sandbox actually has (D-8, protocol.md §6)",
        )

    def test_fam14_2_factory_builds_a_learner_through_build_learner(self):
        """FAM-14.2 the factory builds a learner through the owning module."""
        spec = self.learner_spec(width=S.VERSION_WIDTH, depth=S.VERSION_DEPTH, seed=S.SEED_I)
        built = self.ep("harness", "factory")("learner", spec)
        self.assertEqual(
            self.ep("agents", "param_count")(built),
            self.ep("agents", "param_count")(self.ep("agents", "build_learner")(spec)),
            "a factory builds through agents.build_learner rather than around it "
            "(module-map §3, records.md §14)",
        )

    def test_fam14_3_factory_builds_an_encoder_through_build_encoder(self):
        """FAM-14.3 the factory builds an encoder the encoder surface accepts."""
        encoder = self.ep("harness", "factory")("encoder", S.FLAT)
        readout = self.readout(self.hand(S.SEED_B))
        observation = self.ep("features", "encode")(encoder, readout)
        self.assertIsNotNone(
            observation,
            "the factory's encoder encodes a readout, because it is features.build_encoder's "
            "own object (records.md §14, module-map §3)",
        )

    def test_fam14_4_the_factory_refuses_an_object_the_map_does_not_declare(self):
        """FAM-14.4 the factory builds only declared objects and refuses the rest."""
        text = S.refusal_text(
            lambda: self.ep("harness", "factory")("deck-of-cards", {"suits": 7})
        )
        self.assertIsNotNone(
            text,
            "a factory that builds an undeclared object kind is substituting for a module, "
            "which the harness never does (module-map §3, brief §5)",
        )

    # -- the seams ---------------------------------------------------------
    def test_fam14_5_a_recording_seam_satisfies_the_policy_protocol(self):
        """FAM-14.5 a recording seam is a policy of e2e-surface §2."""
        self.seam_plays_legally("recording", S.SEED_J)

    def test_fam14_6_a_synthetic_seam_satisfies_the_policy_protocol(self):
        """FAM-14.6 a synthetic seam never returns an illegal action."""
        self.seam_plays_legally("synthetic", S.SEED_F)

    def test_fam14_7_a_seam_policy_produces_a_real_engine_episode(self):
        """FAM-14.7 the engine plays a seam, so the episode is the engine's."""
        policy = self.ep("harness", "seam")("recording")
        episode = self.play(S.SEED_I, policy, self.baseline("always-call", S.SEED_D))
        self.assertIsNotNone(episode, "the engine must be able to play a seam policy")
        payoffs = S.numbers(S.find_values(episode, "payoff"))
        self.assertTrue(payoffs, "a real episode record carries its payoffs: %r" % (episode,))
        self.assertEqual(
            sum(payoffs),
            0,
            "the episode the engine played through a seam is still zero-sum, because the "
            "engine and not the seam decided the hand (ASM-12, brief §5)",
        )

    # -- expectations and the driver --------------------------------------
    def test_fam14_8_expect_yields_a_verdict_for_every_kind_the_fixture_lists(self):
        """FAM-14.8 harness.expect judges the kinds fixtures() lists, and only those."""
        kinds = self.expectation_kinds()
        observations = self.observations()
        verdicts = []
        for kind in kinds:
            for observation in observations:
                verdict = S.verdict(self.judged(kind, observation))
                self.assertIsNotNone(
                    verdict,
                    "harness.expect(%r, ...) yields a verdict — a pass or a named failure — "
                    "for an observed value it is handed, and never nothing at all "
                    "(e2e-surface §3.6, records.md §14): %r" % (kind, observation),
                )
                verdicts.append(verdict)
        self.assertIn(
            True,
            verdicts,
            "at least one kind the harness lists passes an observed value, or `expect` could "
            "never report the pass the driver records (e2e-surface §3.6): %r" % (kinds,),
        )
        self.assertIn(
            False,
            verdicts,
            "at least one kind the harness lists fails one, so an expectation distinguishes "
            "two different observations and is never a silent pass; a list whose every kind "
            "passed every observation would judge nothing (e2e-surface §3.6, records.md "
            "§14): %r" % (kinds,),
        )
        # A kind the fixture does not list is not a kind: a named failure, never a pass.
        unknown = "fam14-8-no-such-expectation-kind"
        text = S.refusal_text(
            lambda: self.ep("harness", "expect")(unknown, observations[0])
        )
        self.assertIsNotNone(
            text,
            "harness.expect refuses a kind the fixture does not list, and never silently "
            "passes it (e2e-surface §3.6, records.md §14): %r" % (unknown,),
        )
        self.assertIn(
            S._family_token(unknown),
            S._family_token(text),
            "the named failure names the kind it was handed, so a layer can cite it: %r"
            % (text,),
        )

    def test_fam14_9_drive_runs_a_case_from_its_steps(self):
        """FAM-14.9 harness.drive steps over the declared surface and records the case."""
        ran = []
        case = self.driven_case("FAM-14.9-driver", S.SEED_G, ran)
        result = self.ep("harness", "drive")(case)
        self.assertEqual(
            ran,
            [case["id"]],
            "the driver steps over the case it was handed: a step it never calls is a case "
            "that never ran (records.md §14): %r" % (result,),
        )
        self.assertIsNotNone(
            S.verdict(result),
            "the driver records a verdict for the case — the pass, or the named failure its "
            "expectation reported — and never leaves the case unjudged (records.md §14, "
            "e2e-surface §3.6): %r" % (result,),
        )
        self.assertIn(
            S._family_token(case["id"]),
            S._family_token(S.flatten_text(result)),
            "the driver's record names the case it ran, so a layer return can cite it: %r"
            % (result,),
        )

    def test_fam14_10_drive_reports_a_case_it_cannot_judge_as_failed(self):
        """FAM-14.10 a case resting on an unlisted expectation kind is reported failed."""
        case = self.case(
            "FAM-14.10-unlisted-expectation",
            [lambda: {"seat 0": 4, "seat 1": -3}],
            ["fam14-10-no-such-expectation-kind"],
        )
        try:
            result = self.ep("harness", "drive")(case)
        except S.SurfaceAbsent:
            raise
        except Exception as exc:  # a named refusal is the other legal edge (e2e-surface §2)
            result = "%s: %s" % (type(exc).__name__, exc)
        self.assertIs(
            S.verdict(result),
            False,
            "an expectation kind that fixtures() does not list is a named failure, so a case "
            "resting on one is never reported passed (e2e-surface §3.6, records.md §14): %r"
            % (result,),
        )

    # -- the cost record ---------------------------------------------------
    def test_fam14_11_timings_reports_the_cost_the_driver_collected(self):
        """FAM-14.11 harness.timings reports the driver's clock, hands and per-hand cost."""
        result = self.ep("harness", "drive")(self.driven_case("FAM-14.11-cost"))
        self.assertIsNotNone(
            S.verdict(result),
            "the driven case the timings describe is judged by the driver, so the cost "
            "belongs to work that really ran (records.md §14): %r" % (result,),
        )
        timings = self.ep("harness", "timings")()
        facts = R.timing_facts(timings)
        self.assertTrue(
            facts["clock"],
            "harness.timings reports the wall clock the driver collected (e2e-surface §3.6): "
            "%r" % (timings,),
        )
        self.assertTrue(
            facts["hands"],
            "harness.timings reports the hands it counted beside the clock: %r" % (timings,),
        )
        self.assertTrue(
            facts["per_hand"] or facts["throughput"],
            "harness.timings reports the seconds per hand or the throughput — the per-hand "
            "cost of ASM-15, read by what the key names rather than by a literal spelling: "
            "%r" % (timings,),
        )
        self.assertTrue(
            any(number > 0 for number in facts["clock"]),
            "a wall clock is a positive number of seconds: %r" % (timings,),
        )
        # The harness reports the cost; the bound is what sizes the table, so no case
        # asserts that a wall clock was beaten (battery.md §2, ASM-15).


    # -- the shape in force (D-29) ----------------------------------------
    def test_fam14_12_a_seam_satisfies_the_protocol_on_the_named_shape(self):
        """FAM-14.12 a seam answers the second shape's decisions, in its six indices.

        The harness never substitutes for a module and never learns a game: a seam is a
        policy of `e2e-surface.md` §2 handed `(readout, legal_actions)`, so on a hand dealt
        on D-29's no-cap shape it must return one of **that** shape's legal descriptors —
        a seam that spoke only today's three indices would be a policy of one game and not
        of the surface (`shapes.md` §2, §5, ``sizing.md`` §3, D-29).

        The label is the battery's own, because a seam's contract is the protocol and not
        the label (`e2e-surface.md` §3.6, `records.md` §14, `battery.md` §4).
        """
        shape = self.second_shape()
        self.assertEqual(
            set(self.vocabulary(shape)),
            set(range(len(S.SIZED_ACTIONS))),
            "the named shape's vocabulary is its six declared descriptors (sizing.md §3)",
        )
        walk = self.seam_plays_legally("fam14-12-six-index-seam", S.SEED_I, shape=shape)
        self.assertTrue(walk, "the seam answered no decision of the named shape")
        # The episode the seam's decisions end in is still the engine's: zero-sum payoffs.
        episode = self.play(S.SEED_I, self.ep("harness", "seam")("fam14-12-six-index-seam"),
                            self.baseline("always-call", S.SEED_D), shape=shape)
        payoffs = S.numbers(S.find_values(episode, "payoff"))
        self.assertTrue(payoffs, "a real episode record carries its payoffs: %r" % (episode,))
        self.assertEqual(
            sum(payoffs),
            0,
            "the episode the engine played through a seam on the named shape is still "
            "zero-sum, because the engine and not the seam decided the hand (ASM-12)",
        )


if __name__ == "__main__":
    unittest.main()
