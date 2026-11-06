"""FAM-1 — the declared surface exists and is callable.

One case per entry point of ``docs/L1/e2e-surface.md`` §3, in that document's order,
so that a missing name is one finding per name (``docs/L1/battery.md`` §3 FAM-1, D-11).
Rev 2 replaced the head-to-head opponent with the bounded round-robin league — the pool,
the scheduler, the matrix and the rating (D-16) — so ``evaluation`` declares eleven entry
points and the map forty-nine (``e2e-surface.md`` §3.4 and §4).

Each case asserts presence, that the name is callable, and that a minimal call returns a
value of the kind §3 declares.  A minimal call for a league entry goes through
``_surface.py``'s builders — a membership declaration, a pool, its members, one offer,
one opponent, one cell, the shared table — never through a private helper.  The
contracts behind the values are the business of the later families.
"""

import os
import sys
import unittest

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _surface as S  # noqa: E402


class FAM1Surface(S.SurfaceCase):
    """Every one of the 49 entry points, in the order of e2e-surface.md §3."""

    # -- 3.1 engine (9) ----------------------------------------------------
    def test_fam1_01_engine_game_config(self):
        """FAM-1.1 engine.game_config exists and returns the fixed game."""
        point = self.ep("engine", "game_config")
        self.assertTrue(callable(point), "engine.game_config is not callable")
        self.assertIsNotNone(point(), "engine.game_config() returned nothing")

    def test_fam1_02_engine_new_hand(self):
        """FAM-1.2 engine.new_hand exists and deals a hand from a seed."""
        point = self.ep("engine", "new_hand")
        self.assertTrue(callable(point), "engine.new_hand is not callable")
        self.assertIsNotNone(point(S.SEED_A), "engine.new_hand(seed) returned nothing")

    def test_fam1_03_engine_readout(self):
        """FAM-1.3 engine.readout exists and reads a hand's facts."""
        point = self.ep("engine", "readout")
        self.assertTrue(callable(point), "engine.readout is not callable")
        readout = point(self.hand(S.SEED_A))
        self.assertTrue(S.is_mapping(readout), "engine.readout must return a mapping of facts")

    def test_fam1_04_engine_legal_actions(self):
        """FAM-1.4 engine.legal_actions exists and returns ordered descriptors."""
        point = self.ep("engine", "legal_actions")
        self.assertTrue(callable(point), "engine.legal_actions is not callable")
        legal = point(self.hand(S.SEED_A))
        self.assertTrue(len(legal) >= 1, "engine.legal_actions returned no descriptor")

    def test_fam1_05_engine_apply_action(self):
        """FAM-1.5 engine.apply_action exists and advances a hand."""
        point = self.ep("engine", "apply_action")
        self.assertTrue(callable(point), "engine.apply_action is not callable")
        hand = self.hand(S.SEED_A)
        advanced = point(hand, self.legal(hand)[0])
        self.assertIsNotNone(advanced, "engine.apply_action returned nothing")

    def test_fam1_06_engine_is_terminal(self):
        """FAM-1.6 engine.is_terminal exists and reports a boolean."""
        point = self.ep("engine", "is_terminal")
        self.assertTrue(callable(point), "engine.is_terminal is not callable")
        self.assertIsInstance(point(self.hand(S.SEED_A)), bool)

    def test_fam1_07_engine_payoffs(self):
        """FAM-1.7 engine.payoffs exists and pays a completed hand."""
        point = self.ep("engine", "payoffs")
        self.assertTrue(callable(point), "engine.payoffs is not callable")
        self.assertIsNotNone(point(self.finished_hand(S.SEED_A)))

    def test_fam1_08_engine_play_hand(self):
        """FAM-1.8 engine.play_hand exists and returns an episode record."""
        point = self.ep("engine", "play_hand")
        self.assertTrue(callable(point), "engine.play_hand is not callable")
        episode = point(S.SEED_A, self.baseline("always-call", S.SEED_D),
                        self.baseline("always-call", S.SEED_D))
        self.assertIsNotNone(episode, "engine.play_hand returned nothing")

    def test_fam1_09_engine_equity(self):
        """FAM-1.9 engine.equity exists and returns a probability."""
        point = self.ep("engine", "equity")
        self.assertTrue(callable(point), "engine.equity is not callable")
        value = point(self.hand(S.SEED_C), S.SEED_C, S.EQUITY_SAMPLES)
        self.assertTrue(S.is_count(value) or isinstance(value, float),
                        "engine.equity must return a number")

    # -- 3.2 features (7) --------------------------------------------------
    def test_fam1_10_features_encodings(self):
        """FAM-1.10 features.encodings exists and declares the encodings."""
        point = self.ep("features", "encodings")
        self.assertTrue(callable(point), "features.encodings is not callable")
        self.assertIsNotNone(point())

    def test_fam1_11_features_build_encoder(self):
        """FAM-1.11 features.build_encoder exists and builds an encoder."""
        point = self.ep("features", "build_encoder")
        self.assertTrue(callable(point), "features.build_encoder is not callable")
        self.assertIsNotNone(point(S.FLAT))

    def test_fam1_12_features_observation_spec(self):
        """FAM-1.12 features.observation_spec exists and describes an encoding."""
        point = self.ep("features", "observation_spec")
        self.assertTrue(callable(point), "features.observation_spec is not callable")
        self.assertIsNotNone(point(self.encoder(S.TOKENS)))

    def test_fam1_13_features_encode(self):
        """FAM-1.13 features.encode exists and encodes a readout."""
        point = self.ep("features", "encode")
        self.assertTrue(callable(point), "features.encode is not callable")
        encoder = self.encoder()
        self.assertIsNotNone(point(encoder, self.readout(self.hand(S.SEED_A))))

    def test_fam1_14_features_action_space(self):
        """FAM-1.14 features.action_space exists and declares the vocabulary."""
        point = self.ep("features", "action_space")
        self.assertTrue(callable(point), "features.action_space is not callable")
        self.assertIsNotNone(point())

    def test_fam1_15_features_legal_indices(self):
        """FAM-1.15 features.legal_indices exists and maps legal actions to indices."""
        point = self.ep("features", "legal_indices")
        self.assertTrue(callable(point), "features.legal_indices is not callable")
        legal = self.legal(self.hand(S.SEED_A))
        self.assertTrue(len(list(point(legal))) >= 1)

    def test_fam1_16_features_decode_action(self):
        """FAM-1.16 features.decode_action exists and maps an index to a descriptor."""
        point = self.ep("features", "decode_action")
        self.assertTrue(callable(point), "features.decode_action is not callable")
        self.assertIsNotNone(point(1), "features.decode_action(1) returned nothing")

    # -- 3.3 agents (10) ---------------------------------------------------
    def test_fam1_17_agents_learners(self):
        """FAM-1.17 agents.learners exists and declares backends and kinds."""
        point = self.ep("agents", "learners")
        self.assertTrue(callable(point), "agents.learners is not callable")
        self.assertIsNotNone(point())

    def test_fam1_18_agents_build_learner(self):
        """FAM-1.18 agents.build_learner exists and builds a learner."""
        point = self.ep("agents", "build_learner")
        self.assertTrue(callable(point), "agents.build_learner is not callable")
        self.assertIsNotNone(point(self.learner_spec(width=61, depth=3, seed=S.SEED_A)))

    def test_fam1_19_agents_param_count(self):
        """FAM-1.19 agents.param_count exists and counts trainable parameters."""
        point = self.ep("agents", "param_count")
        self.assertTrue(callable(point), "agents.param_count is not callable")
        count = point(self.learner(width=61, depth=3, seed=S.SEED_A))
        self.assertTrue(S.is_count(count), "agents.param_count must return an integer")
        self.assertGreater(count, 0)

    def test_fam1_20_agents_act(self):
        """FAM-1.20 agents.act exists and chooses an index plus its record."""
        point = self.ep("agents", "act")
        self.assertTrue(callable(point), "agents.act is not callable")
        learner = self.learner(width=61, depth=3, seed=S.SEED_A)
        result = self.act(learner, self.encoder(), self.readout(self.hand(S.SEED_A)))
        self.assertTrue(S.is_count(self.action_index(result)))

    def test_fam1_21_agents_learn(self):
        """FAM-1.21 agents.learn exists and returns the update's statistics."""
        point = self.ep("agents", "learn")
        self.assertTrue(callable(point), "agents.learn is not callable")
        learner = self.learner(width=61, depth=3, seed=S.SEED_A)
        self.assertIsNotNone(point(learner, self.transitions(S.SEED_C)))

    def test_fam1_22_agents_save(self):
        """FAM-1.22 agents.save exists and writes a checkpoint."""
        point = self.ep("agents", "save")
        self.assertTrue(callable(point), "agents.save is not callable")
        learner = self.learner(width=61, depth=3, seed=S.SEED_A)
        path = point(learner, os.path.join(self.scratch(), "fam1-22.pth"))
        self.assertTrue(os.path.exists(str(path)), "agents.save did not write %r" % (path,))

    def test_fam1_23_agents_load(self):
        """FAM-1.23 agents.load exists and restores a learner from a checkpoint."""
        point = self.ep("agents", "load")
        self.assertTrue(callable(point), "agents.load is not callable")
        spec = self.learner_spec(width=61, depth=3, seed=S.SEED_A)
        path = self.ep("agents", "save")(
            self.ep("agents", "build_learner")(spec), os.path.join(self.scratch(), "fam1-23.pth")
        )
        self.assertIsNotNone(point(spec, path), "agents.load returned nothing")

    def test_fam1_24_agents_as_policy(self):
        """FAM-1.24 agents.as_policy exists and returns a policy of §2."""
        point = self.ep("agents", "as_policy")
        self.assertTrue(callable(point), "agents.as_policy is not callable")
        policy = point(self.learner(width=61, depth=3, seed=S.SEED_A), self.encoder(), S.SEED_H)
        self.assertTrue(callable(policy), "agents.as_policy must return a callable policy")

    def test_fam1_25_agents_baselines(self):
        """FAM-1.25 agents.baselines exists and names the three fixed baselines."""
        point = self.ep("agents", "baselines")
        self.assertTrue(callable(point), "agents.baselines is not callable")
        self.assertIsNotNone(point())

    def test_fam1_26_agents_build_baseline(self):
        """FAM-1.26 agents.build_baseline exists and returns a policy of §2."""
        point = self.ep("agents", "build_baseline")
        self.assertTrue(callable(point), "agents.build_baseline is not callable")
        self.assertTrue(callable(point("random", S.SEED_D)))

    # -- 3.4 evaluation (11) -----------------------------------------------
    def test_fam1_27_evaluation_protocol(self):
        """FAM-1.27 evaluation.protocol exists and declares the fixed protocol."""
        point = self.ep("evaluation", "protocol")
        self.assertTrue(callable(point), "evaluation.protocol is not callable")
        self.assertIsNotNone(point())

    def test_fam1_28_evaluation_league(self):
        """FAM-1.28 evaluation.league exists and declares the league's parameters."""
        point = self.ep("evaluation", "league")
        self.assertTrue(callable(point), "evaluation.league is not callable")
        self.assertIsNotNone(point())

    def test_fam1_29_evaluation_build_pool(self):
        """FAM-1.29 evaluation.build_pool exists and builds a pool from a membership."""
        point = self.ep("evaluation", "build_pool")
        self.assertTrue(callable(point), "evaluation.build_pool is not callable")
        pool = point(self.membership(("kestrel", "bramble")))
        self.assertIsNotNone(pool, "evaluation.build_pool returned nothing")

    def test_fam1_30_evaluation_pool_members(self):
        """FAM-1.30 evaluation.pool_members exists and reads a pool's members."""
        point = self.ep("evaluation", "pool_members")
        self.assertTrue(callable(point), "evaluation.pool_members is not callable")
        declared = point(self.pool(("kestrel",)))
        self.assertTrue(
            S.is_mapping(declared) or isinstance(declared, (list, tuple)),
            "evaluation.pool_members must return the members and the bound M",
        )
        self.assertTrue(S.strings(declared), "the member list carries no member at all")

    def test_fam1_31_evaluation_offer(self):
        """FAM-1.31 evaluation.offer exists and advances a pool by one version."""
        point = self.ep("evaluation", "offer")
        self.assertTrue(callable(point), "evaluation.offer is not callable")
        # A frozen pool's membership does not change while it is used (records.md §8), so
        # the pool this minimal call advances is declared unfrozen.
        advanced = point(self.pool(("kestrel",), frozen=False), self.version("bramble"))
        self.assertIsNotNone(advanced, "evaluation.offer returned nothing")

    def test_fam1_32_evaluation_opponent(self):
        """FAM-1.32 evaluation.opponent exists and draws a policy from the pool."""
        point = self.ep("evaluation", "opponent")
        self.assertTrue(callable(point), "evaluation.opponent is not callable")
        drawn = point(self.pool(("kestrel",)), S.SEED_G)
        self.assertTrue(callable(drawn), "evaluation.opponent must return a policy of §2")

    def test_fam1_33_evaluation_match(self):
        """FAM-1.33 evaluation.match exists and plays one cell."""
        point = self.ep("evaluation", "match")
        self.assertTrue(callable(point), "evaluation.match is not callable")
        cell = point(self.baseline("always-call", S.SEED_D),
                     self.baseline("random", S.SEED_F),
                     S.CELL_HANDS_SMALL, S.TABLE_SEED_A)
        self.assertTrue(
            S.is_mapping(cell) or isinstance(cell, (list, tuple)),
            "evaluation.match must return one cell with its two directions",
        )

    def test_fam1_34_evaluation_matrix(self):
        """FAM-1.34 evaluation.matrix exists and returns the pairwise matrix."""
        point = self.ep("evaluation", "matrix")
        self.assertTrue(callable(point), "evaluation.matrix is not callable")
        table = S.shared_league(self)["matrix"]
        self.assertTrue(
            S.is_mapping(table) or isinstance(table, (list, tuple)),
            "evaluation.matrix must return the members, the cells and the table seed",
        )

    def test_fam1_35_evaluation_rating(self):
        """FAM-1.35 evaluation.rating exists and fits one rating per member."""
        point = self.ep("evaluation", "rating")
        self.assertTrue(callable(point), "evaluation.rating is not callable")
        fitted = S.shared_league(self)["rating"]
        self.assertTrue(
            S.is_mapping(fitted) or isinstance(fitted, (list, tuple)),
            "evaluation.rating must return a value and an interval per member",
        )

    def test_fam1_36_evaluation_policy_from(self):
        """FAM-1.36 evaluation.policy_from exists and loads a checkpoint as a policy."""
        point = self.ep("evaluation", "policy_from")
        self.assertTrue(callable(point), "evaluation.policy_from is not callable")
        policy = point(self.version("quarry")["path"])
        self.assertTrue(callable(policy), "evaluation.policy_from must return a policy of §2")

    def test_fam1_37_evaluation_report(self):
        """FAM-1.37 evaluation.report exists and returns the complete rung report."""
        point = self.ep("evaluation", "report")
        self.assertTrue(callable(point), "evaluation.report is not callable")
        league = S.shared_league(self)
        record = self.evidence_record(
            self.run_record("R2", (S.SEED_A,), S.BUDGET_TINY),
            matrix=league["matrix"],
            rating=league["rating"],
            seeds=(S.SEED_A,),
            budget=S.BUDGET_TINY,
        )
        report = point("R2", record, league["matrix"], league["rating"])
        self.assertIsNotNone(report, "evaluation.report returned nothing")

    # -- 3.5 training (6) --------------------------------------------------
    def test_fam1_38_training_rungs(self):
        """FAM-1.38 training.rungs exists and declares the rungs."""
        point = self.ep("training", "rungs")
        self.assertTrue(callable(point), "training.rungs is not callable")
        self.assertIsNotNone(point())

    def test_fam1_39_training_rung(self):
        """FAM-1.39 training.rung exists and resolves a rung name."""
        point = self.ep("training", "rung")
        self.assertTrue(callable(point), "training.rung is not callable")
        self.assertIsNotNone(point("R1"), "training.rung('R1') resolved nothing")

    def test_fam1_40_training_run(self):
        """FAM-1.40 training.run exists and returns a run record."""
        point = self.ep("training", "run")
        self.assertTrue(callable(point), "training.run is not callable")
        self.assertIsNotNone(point("R1", [S.SEED_A], S.BUDGET_TINY, "cpu"))

    def test_fam1_41_training_fairness(self):
        """FAM-1.41 training.fairness exists and reports what a pair holds constant."""
        point = self.ep("training", "fairness")
        self.assertTrue(callable(point), "training.fairness is not callable")
        rung = self.ep("training", "rung")
        self.assertIsNotNone(point(rung("R1"), rung("R2")))

    def test_fam1_42_training_devices(self):
        """FAM-1.42 training.devices exists and reports the devices and the default."""
        point = self.ep("training", "devices")
        self.assertTrue(callable(point), "training.devices is not callable")
        declared = point()
        self.assertIsNotNone(declared)
        self.assertIn(
            "cpu",
            S.flatten_text(declared),
            "training.devices must report the CPU the sandbox runs on (D-8)",
        )

    def test_fam1_43_training_checkpoints(self):
        """FAM-1.43 training.checkpoints exists and returns the checkpoint index."""
        point = self.ep("training", "checkpoints")
        self.assertTrue(callable(point), "training.checkpoints is not callable")
        index = point()
        self.assertIsNotNone(index)
        self.assertTrue(S.is_mapping(index) or isinstance(index, (list, tuple, set)),
                        "the index must be a mapping or a sequence")

    # -- 3.6 harness (6) ---------------------------------------------------
    def test_fam1_44_harness_drive(self):
        """FAM-1.44 harness.drive exists and drives one case."""
        point = self.ep("harness", "drive")
        self.assertTrue(callable(point), "harness.drive is not callable")
        case = {
            "id": "FAM-1.44",
            "steps": [lambda: self.play(S.SEED_G)],
            # The expected outcome is one of the kinds the fixture lists; the battery
            # invents observed values and never a kind (e2e-surface §3.6, records.md §14).
            "expect": [self.an_expectation_kind()],
        }
        self.assertIsNotNone(point(case), "harness.drive returned nothing")

    def test_fam1_45_harness_fixtures(self):
        """FAM-1.45 harness.fixtures exists and returns the preconditions."""
        point = self.ep("harness", "fixtures")
        self.assertTrue(callable(point), "harness.fixtures is not callable")
        self.assertIsNotNone(point())

    def test_fam1_46_harness_factory(self):
        """FAM-1.46 harness.factory exists and builds a declared object."""
        point = self.ep("harness", "factory")
        self.assertTrue(callable(point), "harness.factory is not callable")
        spec = self.learner_spec(width=61, depth=3, seed=S.SEED_A)
        self.assertIsNotNone(point("learner", spec))

    def test_fam1_47_harness_seam(self):
        """FAM-1.47 harness.seam exists and returns a policy of §2."""
        point = self.ep("harness", "seam")
        self.assertTrue(callable(point), "harness.seam is not callable")
        self.assertTrue(callable(point("recording")))

    def test_fam1_48_harness_expect(self):
        """FAM-1.48 harness.expect exists and judges an observed value."""
        point = self.ep("harness", "expect")
        self.assertTrue(callable(point), "harness.expect is not callable")
        # The kind is one the fixture lists — the vocabulary is the harness's own — and the
        # observed value is this battery's (e2e-surface §3.6, records.md §14).
        kind = self.an_expectation_kind()
        try:
            answered = point(kind, {"seat 0": 3, "seat 1": -3})
        except S.SurfaceAbsent:
            raise
        except Exception:  # a named refusal of an observed value is still an answer
            answered = "refused"
        self.assertIsNotNone(answered, "harness.expect returned nothing at all")

    def test_fam1_49_harness_timings(self):
        """FAM-1.49 harness.timings exists and returns the collected timings."""
        point = self.ep("harness", "timings")
        self.assertTrue(callable(point), "harness.timings is not callable")
        self.assertIsNotNone(point())


if __name__ == "__main__":
    unittest.main()
