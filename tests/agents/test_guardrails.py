"""AGT-11 — the L4 guardrails, one case per risk observable through an entry point.

Drives `docs/L3/agents/guardrails.md` G1-G16 where a learner, a policy or a
checkpoint exposes the risk: the export list, the plain-int action, the keyed
draw, the one initialisation order and the backend axis after a real batch, the
lazy import, the batch order, the two plain statistics, the target copy inside
one step and across a full refresh interval, and the refresh itself at
`target_update_interval` read as the recorded `target.counter` through
`checkpoint._read_metadata(path)` — `rule.md` §8's sixth declared internal, which
closes G9's Unverified clause — the one parameter formula, the
caller's path, the checkpoint's contents on a learned learner, `load`'s
compared keys, the accepted valid instances, the oracle's count and the policy's
snapshot (D-3, D-7, D-12, D-16, ASM-2, ASM-10).
"""

import io
import os
import subprocess
import sys
import unittest
import zipfile

import numpy as np

from _agents_support import (
    ALL_MASK,
    ANNEAL_SEED,
    CHECKPOINT_NAMES,
    LEARNER_SEED,
    REPO_ROOT,
    SRC_ROOT,
    AgentsCase,
    anneal_batch,
    batch,
    chosen_index,
    declared_internal,
    dense_observation,
    features,
    finite_float,
    flat_encoder,
    learner_spec,
    plain_int,
    target_interval,
    token_encoder,
    transition,
)

#: G6's witness, run in a clean interpreter so the assertion cannot depend on
#: what an earlier case already imported.
G6_SCRIPT = """
import os
import sys
import tempfile

sys.path.insert(0, SRC)

import numpy as np
import agents

spec = {"backend": "numpy",
        "architecture": {"kind": "naive-stack", "width": 6, "depth": 1},
        "seed": 8127}
learner = agents.build_learner(spec)
record = agents.act(learner, np.zeros(203, dtype=np.float32), (0, 1, 2))
assert isinstance(record["action"], int)
folder = tempfile.mkdtemp()
path = agents.save(learner, os.path.join(folder, "v-8127-a.pt"))
agents.load(None, path)
print("torch", "torch" in sys.modules)
print("pokerkit", "pokerkit" in sys.modules)
"""


class GuardrailTest(AgentsCase):
    def test_agt11_g1_all_is_the_ten_names_in_order(self):
        """G1 `__all__` is the ten entry points in the L1 order, no eleventh (`README.md` §3, D-12)."""
        package = self.agents()
        self.assertEqual(
            tuple(package.__all__),
            (
                "learners",
                "build_learner",
                "param_count",
                "act",
                "learn",
                "save",
                "load",
                "as_policy",
                "baselines",
                "build_baseline",
            ),
        )

    def test_agt11_g2_the_action_is_a_plain_int(self):
        """G2 `act` returns a plain Python `int` under `action` in a mapping (`surface.md` §6, G2, `records.md` §6)."""
        package = self.agents()
        learner = self.build(kind="naive-stack")
        action = plain_int(
            package.act(learner, dense_observation(), ALL_MASK)["action"],
            "act(...)['action']",
        )
        self.assertIn(action, ALL_MASK)

    def test_agt11_g3_two_calls_at_one_decision_agree(self):
        """G3 the exploration is keyed by the decision, so a second call cannot advance a stream (`surface.md` §6, `rule.md` §4, G3)."""
        package = self.agents()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        observation = dense_observation(0.2)
        first = package.act(learner, observation, ALL_MASK)["action"]
        second = package.act(learner, observation, ALL_MASK)["action"]
        self.assertEqual(first, second)

    def test_agt11_g4_both_backends_answer_one_decision_alike(self):
        """G4 two learners from one spec, handed one batch and learned on both, answer one index per decision over 20 decisions at least 16 of them greedy-expected: one initialisation, one keyed draw and one tie-break in either backend (`rule.md` §4-§5, `architecture.md` §4, `backends.md` §2-§3, G4, ASM-10)."""
        package = self.agents()
        records = anneal_batch("naive-stack")
        numpy_learner = self.annealed_learner(
            "parity-numpy",
            {"backend": "numpy", "kind": "naive-stack", "width": 6, "depth": 1},
            records,
        )
        torch_learner = self.annealed_learner(
            "parity-torch",
            {"backend": "torch", "kind": "naive-stack", "width": 6, "depth": 1},
            records,
        )
        rows = self.decisions(20)
        observations, masks = map(list, zip(*self.decision_observations(rows, "naive-stack")))
        self.greedy_arm(LEARNER_SEED, "naive-stack", observations, masks, 16)
        for row in rows:
            with self.subTest(hand=row["readout"]["hole"]):
                self.assertEqual(
                    package.act(numpy_learner, row["dense"], row["mask"])["action"],
                    package.act(torch_learner, row["dense"], row["mask"])["action"],
                    "the two backends disagree on one decision after one batch, so "
                    "the initialisation, the keyed draw or the tie-break is not the "
                    "design's one (backends.md §3)",
                )

    def test_agt11_g4b_both_backends_start_from_one_draw(self):
        """G4 the torch backend copies `architecture.md` §4's NumPy draw and never redraws its own: both backends' checkpointed online parameters, the array's `[0, P)`, are `_initial_parameters` at that seed (`architecture.md` §4-§5, `backends.md` §2, `checkpoint.md` §2, `rule.md` §8, G4)."""
        package = self.agents()
        count = declared_internal("model", "_param_count_for")
        initial = declared_internal("model", "_initial_parameters")
        width, depth = 6, 2
        for kind in ("naive-stack", "deep"):
            expected = np.asarray(initial(kind, width, depth, 0.0, LEARNER_SEED))
            parameter_count = int(count(kind, width, depth, 0.0))
            saved = {}
            for backend in ("numpy", "torch"):
                learner = package.build_learner(
                    learner_spec(backend=backend, kind=kind, width=width, depth=depth)
                )
                path = os.path.join(
                    self.tempdir(), "%s-%s-8127.pt" % (backend, kind)
                )
                package.save(learner, path)
                self.assertEqual(package.param_count(learner), parameter_count)
                array = self.parameters_array(path)
                with self.subTest(kind=kind, backend=backend):
                    self.assertGreaterEqual(
                        int(array.shape[0]),
                        2 * parameter_count,
                        "the container's array is shorter than the two copies of P",
                    )
                    saved[backend] = np.asarray(array[:parameter_count], dtype="float64")
                    self.assertTrue(
                        np.array_equal(saved[backend], expected),
                        "the saved online parameters are not the one draw "
                        "_initial_parameters returns at this seed",
                    )
            self.assertTrue(
                np.array_equal(saved["numpy"], saved["torch"]),
                "the two backends started from different values, so one of them "
                "drew its own rather than copying (architecture.md §4)",
            )

    def test_agt11_g6_the_numpy_path_never_imports_torch_or_pokerkit(self):
        """G6 `import agents` and a numpy build/act/save/load leave `torch` and `pokerkit` out of `sys.modules` (`backends.md` §4, `README.md` §6, G6)."""
        self.agents()
        script = G6_SCRIPT.replace("SRC", repr(SRC_ROOT), 1)
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
        self.assertEqual(
            completed.returncode,
            0,
            "the clean-interpreter witness failed:\n%s\n%s"
            % (completed.stdout, completed.stderr),
        )
        self.assertIn("torch False", completed.stdout)
        self.assertIn("pokerkit False", completed.stdout)

    def test_agt11_g6b_a_torch_learner_runs_on_the_cpu_without_a_device(self):
        """G6 a torch learner builds and decides on CPU, and no CUDA device is initialised (`backends.md` §4, `strata/platform.md`, G6)."""
        package = self.agents()
        learner = self.build(backend="torch", kind="naive-stack", width=4, depth=1)
        action = plain_int(
            package.act(learner, dense_observation(), ALL_MASK)["action"], "action"
        )
        self.assertIn(action, ALL_MASK)
        import torch

        self.assertFalse(
            torch.cuda.is_initialized(),
            "a torch learner touched a CUDA device; the design promises CPU only",
        )

    def test_agt11_g7_a_six_transition_batch_is_consumed(self):
        """G7 a six-record batch is accepted and consumed, `batch_size` being no precondition (`rule.md` §3, `surface.md` §7, G7)."""
        package = self.agents()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        records = batch([dense_observation(0.05 * step) for step in range(6)])
        result = package.learn(learner, records)
        self.assertEqual(plain_int(result["transitions"], "transitions"), 6)

    def test_agt11_g8_the_statistics_are_plain_and_finite(self):
        """G8 `td_error` is a finite float and `transitions` a plain int, and nothing else is returned (`rule.md` §3, G8)."""
        package = self.agents()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        result = package.learn(learner, batch([dense_observation(0.3)]))
        self.assertEqual(set(result), {"td_error", "transitions"})
        self.assertGreaterEqual(finite_float(result["td_error"], "td_error"), 0.0)
        self.assertEqual(plain_int(result["transitions"], "transitions"), 1)

    def test_agt11_g9_the_target_is_unmoved_within_one_step(self):
        """G9 a terminal target is the reward and a repeated transition's TD error shrinks, so `q'` is held constant (`rule.md` §2-§3, G9)."""
        package = self.agents()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        record = transition(
            dense_observation(0.0),
            next_observation=dense_observation(0.5),
            action=1,
            reward=0.0,
            terminal=False,
        )
        first = finite_float(package.learn(learner, [record])["td_error"], "td_error")
        second = finite_float(package.learn(learner, [record])["td_error"], "td_error")
        self.assertLess(second, first)
        terminal = transition(
            dense_observation(0.0), action=1, reward=9.5, terminal=True
        )
        one = finite_float(
            package.learn(self.build(kind="naive-stack", width=6, depth=1), [terminal])[
                "td_error"
            ],
            "td_error",
        )
        other = finite_float(
            package.learn(
                self.build(kind="naive-stack", width=6, depth=1),
                [dict(terminal, next_observation=dense_observation(-0.9), next_legal=(2,))],
            )["td_error"],
            "td_error",
        )
        self.assertEqual(one, other)

    def test_agt11_g9b_a_full_refresh_interval_stays_finite(self):
        """G9 consuming `target_update_interval` transitions in one call leaves the statistics plain and finite and reports every record consumed; the refresh itself is observable only through the recorded `target.counter`, which the design's G9 marks a known gap, so no private name is invented for it (`rule.md` §3, §6, `checkpoint.md` §2.1, G9)."""
        package = self.agents()
        interval = target_interval()
        self.assertGreater(interval, 0)
        learner = self.build(kind="naive-stack", width=6, depth=1)
        records = anneal_batch("naive-stack", seed=ANNEAL_SEED + 21)[:interval]
        self.assertEqual(len(records), interval)
        result = package.learn(learner, records)
        self.assertEqual(set(result), {"td_error", "transitions"})
        self.assertGreaterEqual(finite_float(result["td_error"], "td_error"), 0.0)
        self.assertEqual(
            plain_int(result["transitions"], "transitions"),
            interval,
            "the batch that crosses the refresh interval did not report every "
            "record consumed",
        )

    def test_agt11_g9c_the_target_copy_is_refreshed_exactly_at_the_interval(self):
        """G9 the recorded `target.counter` is the transitions consumed since the last refresh — `0` on a learner that has consumed nothing, the batch's own length after a batch shorter than `target_update_interval`, and `0` again exactly when the interval has been consumed, the two copies in the container then being equal — which is G9's Unverified clause read through `checkpoint._read_metadata(path)`, the sixth internal `rule.md` §8 declares for exactly this (`rule.md` §3, §6, §8, `checkpoint.md` §1, §2.1, §3, G9, G12, ASM-5)."""
        package = self.agents()
        read_metadata = declared_internal("checkpoint", "_read_metadata")
        interval = target_interval()
        self.assertGreater(interval, 1, "a refresh interval must hold more than one transition")
        folder = self.tempdir()
        learner = self.build(kind="naive-stack", width=6, depth=1)

        before = read_metadata(
            package.save(learner, os.path.join(folder, CHECKPOINT_NAMES[0]))
        )
        start = plain_int(before["target"]["counter"], "target.counter")
        self.assertEqual(
            start,
            0,
            "a learner that has consumed no transition records a target counter of "
            "0, the count consumed since the last refresh (rule.md §3, "
            "checkpoint.md §2.1)",
        )
        self.assertEqual(
            plain_int(before["target"]["interval"], "target.interval"),
            interval,
            "the counter's interval is not the declared target_update_interval, so "
            "the count has no fixed scale (rule.md §6)",
        )
        count = plain_int(before["params"]["count"], "params.count")

        records = anneal_batch("naive-stack", seed=ANNEAL_SEED + 41)[:interval]
        shorter = interval // 2
        package.learn(learner, records[:shorter])
        second_path = package.save(learner, os.path.join(folder, CHECKPOINT_NAMES[1]))
        second = read_metadata(second_path)
        consumed = plain_int(second["target"]["counter"], "target.counter")
        self.assertNotEqual(
            consumed,
            start,
            "%d transitions were consumed and the recorded target counter is still "
            "its starting value: no count of the transitions consumed is kept, so a "
            "refresh is either due every step or never (rule.md §3)" % (shorter,),
        )
        self.assertEqual(
            consumed,
            shorter,
            "the recorded target counter is not the number of transitions consumed "
            "since the last refresh, so the refresh lands at another transition "
            "(rule.md §3, G9)",
        )
        online, target = self.parameter_copies(second_path, count)
        self.assertFalse(
            np.array_equal(online, target),
            "after %d consumed transitions the target copy equals the online "
            "parameters, so it was refreshed before the interval was reached "
            "(rule.md §3, G9)" % (shorter,),
        )

        package.learn(learner, records[shorter:])
        third_path = package.save(learner, os.path.join(folder, CHECKPOINT_NAMES[2]))
        third = read_metadata(third_path)
        self.assertEqual(
            plain_int(third["exploration"]["position"], "exploration.position"),
            interval,
            "the learner consumed %d transitions and its recorded schedule position "
            "is not that count (rule.md §3-§4)" % (interval,),
        )
        refreshed = plain_int(third["target"]["counter"], "target.counter")
        self.assertNotEqual(
            refreshed,
            consumed,
            "the target counter did not reset at target_update_interval: it reads "
            "%d after %d consumed transitions, so no refresh is counted and one "
            "every step or never passes (rule.md §3, G9)"
            % (refreshed, interval),
        )
        self.assertEqual(
            refreshed,
            start,
            "the counter is not back at its starting value once the interval has "
            "been consumed, so the refresh is one transition early or late "
            "(rule.md §3, G9)",
        )
        online, target = self.parameter_copies(third_path, count)
        self.assertTrue(
            np.array_equal(online, target),
            "at the refresh boundary the target copy is not a copy of the online "
            "parameters, so nothing was copied into it (rule.md §3, G9)",
        )

    def test_agt11_g10_param_count_is_one_formula(self):
        """G10 the one formula of `architecture.md` §5, masks and buffers excluded (`architecture.md` §5, G10, ASM-10)."""
        package = self.agents()
        feats = features()
        dense_width = feats.observation_spec(flat_encoder())["shape"][0]
        vocabulary = feats.observation_spec(token_encoder())["vocabulary"]
        width, depth = 6, 2
        kept = round((1.0 - 0.5) * width * width)
        expected = {
            ("naive-stack", "dense"): dense_width * width
            + width
            + depth * (width * width + width)
            + 3 * width
            + 3,
            ("deep", "token"): vocabulary * width
            + depth * (width * width + width)
            + 3 * width
            + 3,
            ("sparse", "sparse"): vocabulary * width
            + depth * (kept + width)
            + 3 * width
            + 3,
        }
        cases = (
            ("naive-stack", "dense", {}),
            ("deep", "token", {}),
            ("sparse", "sparse", {"sparsity": 0.5}),
        )
        for kind, shape, settings in cases:
            with self.subTest(kind=kind):
                architecture = {"kind": kind, "width": width, "depth": depth}
                architecture.update(settings)
                learner = package.build_learner(
                    learner_spec(architecture=architecture)
                )
                self.assertEqual(package.param_count(learner), expected[(kind, shape)])
        dense_at_zero = package.build_learner(
            learner_spec(
                architecture={
                    "kind": "sparse",
                    "width": width,
                    "depth": depth,
                    "sparsity": 0.0,
                }
            )
        )
        token_at_zero = package.build_learner(
            learner_spec(architecture={"kind": "deep", "width": width, "depth": depth})
        )
        self.assertEqual(
            package.param_count(dense_at_zero), package.param_count(token_at_zero)
        )

    def test_agt11_g11_save_writes_exactly_the_callers_path(self):
        """G11 the container is written through an open handle at the caller's spelling (`checkpoint.md` §2, `surface.md` §8, G11)."""
        package = self.agents()
        folder = self.tempdir()
        path = os.path.join(folder, CHECKPOINT_NAMES[2])
        written = package.save(self.build(kind="naive-stack"), path)
        self.assertEqual(written, path)
        self.assertTrue(os.path.isfile(path))
        self.assertFalse(os.path.exists(path + ".npz"))

    def test_agt11_g12_a_checkpoint_carries_the_seed_and_the_position(self):
        """G12 a learned learner's checkpoint carries the seed and the schedule position: the restored learner answers as its source did over 20 decisions (at least 16 greedy-expected), and a policy at the recorded seed decides as `act` (`checkpoint.md` §1-§2.1, `surface.md` §9-§10, `rule.md` §4, G12, ASM-5)."""
        package = self.agents()
        learner = self.annealed_learner(
            "g12", {"kind": "naive-stack", "width": 8, "depth": 1}
        )
        rows = self.decisions(20)
        observations, masks = map(list, zip(*self.decision_observations(rows, "naive-stack")))
        self.greedy_arm(LEARNER_SEED, "naive-stack", observations, masks, 16)
        path = package.save(learner, os.path.join(self.tempdir(), CHECKPOINT_NAMES[0]))
        restored = package.load(None, path)
        policy = package.as_policy(restored, flat_encoder(), LEARNER_SEED)
        for row in rows:
            with self.subTest(hand=row["readout"]["hole"]):
                acted = package.act(learner, row["dense"], row["mask"])["action"]
                self.assertEqual(
                    package.act(restored, row["dense"], row["mask"])["action"],
                    acted,
                    "the restored learner did not answer at the recorded seed and "
                    "position",
                )
                self.assertEqual(
                    chosen_index(policy(row["readout"], row["legal"]), row["legal"]),
                    acted,
                    "the policy at the recorded seed did not decide as act",
                )

    def test_agt11_g13_load_compares_only_the_enumerated_keys(self):
        """G13 width, depth, `sizes` and extra keys are not compared while `learning_rule` is; the file's geometry is the authority (`checkpoint.md` §3, `surface.md` §9, G13, D-19).

        The compared keys are `backend`, the kind, `seed`, `learning_rule` whenever
        the spec names one, and the encoder's representation and size; a bare kind
        leaves width and depth uncompared and `sizes` never disagrees
        (`checkpoint.md` §3).  Both sides are driven: a spec naming the file's own
        rule beside the uncompared keys loads, and the same spec with the other
        catalogue member is refused naming the key and both values — so "extra keys
        are ignored" is kept for the keys that are still ignored, and `learning_rule`
        is not one of them any more.
        """
        package = self.agents()
        catalogue = tuple(package.learners()["learning_rules"])
        self.assertGreaterEqual(len(catalogue), 2)
        default_rule, other_rule = catalogue[0], catalogue[1]
        learner = self.build(kind="naive-stack", width=6, depth=1)
        kept = package.param_count(learner)
        path = package.save(learner, os.path.join(self.tempdir(), CHECKPOINT_NAMES[1]))
        spec = learner_spec(
            kind="naive-stack",
            width=24,
            depth=3,
            sizes={"width": 24, "depth": 3},
            extra={"name": "invented-version", "device": "cpu"},
        )
        restored = package.load(spec, path)
        self.assertEqual(package.param_count(restored), kept)
        agreed = package.load(dict(spec, learning_rule=default_rule), path)
        self.assertEqual(
            package.param_count(agreed),
            kept,
            "a spec naming the file's own `learning_rule` is a compared key that "
            "agrees, and width, depth, `sizes` and the extra keys beside it are still "
            "not compared (checkpoint.md §3, surface.md §9)",
        )
        self.assert_refused(
            package.load,
            dict(spec, learning_rule=other_rule),
            path,
            entry="load",
            groups=(("learning_rule",), (other_rule,), (default_rule,)),
            label="a spec naming the other catalogue member than the file records",
        )

    def test_agt11_g14_valid_instances_are_not_refused(self):
        """G14 an extra key, `sizes` beside `architecture`, an unread `sparsity`, a numpy seed, either catalogue member as `learning_rule` and the extreme settings are accepted (`errors.md` §4, `architecture.md` §3, `rules.md` §2, §4, G14, D-19)."""
        package = self.agents()
        catalogue = tuple(package.learners()["learning_rules"])
        self.assertGreaterEqual(len(catalogue), 2)
        cases = (
            (
                "sizes beside architecture",
                learner_spec(sizes={"width": 13, "depth": 2}),
            ),
            (
                "an unread sparsity",
                learner_spec(
                    architecture={"kind": "deep", "width": 6, "depth": 1, "sparsity": 0.5}
                ),
            ),
            ("a numpy integer seed", learner_spec(seed=np.int64(LEARNER_SEED))),
            (
                "the declared default named as the rule",
                learner_spec(extra={"learning_rule": catalogue[0]}),
            ),
            (
                "the other catalogue member named as the rule",
                learner_spec(extra={"learning_rule": catalogue[1]}),
            ),
            ("an extra run-record key", learner_spec(extra={"hyper": {}})),
            (
                "a width and depth of one",
                learner_spec(architecture={"kind": "deep", "width": 1, "depth": 1}),
            ),
            (
                "a sparsity of zero",
                learner_spec(
                    architecture={"kind": "sparse", "width": 6, "depth": 1, "sparsity": 0.0}
                ),
            ),
            (
                "a sparsity of one",
                learner_spec(
                    architecture={"kind": "sparse", "width": 6, "depth": 1, "sparsity": 1.0}
                ),
            ),
        )
        for label, spec in cases:
            with self.subTest(case=label):
                self.assertGreater(package.param_count(package.build_learner(spec)), 0)

    def test_agt11_g14b_a_refused_batch_leaves_the_learner_as_it_was(self):
        """G14 a refused `learn` has no observable effect: the learner's next `act` answers as it did before, because validation precedes the first step (`errors.md` §1, §4, `rule.md` §3, `surface.md` §1, §7, G14)."""
        package = self.agents()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        probes = [
            (dense_observation(0.0), ALL_MASK),
            (dense_observation(0.45), (1, 2)),
            (dense_observation(-0.8), (0, 2)),
        ]
        before = [
            package.act(learner, observation, mask)["action"]
            for observation, mask in probes
        ]
        good = transition(dense_observation(0.2))
        self.assert_refused(
            package.learn,
            learner,
            [good, dict(good, next_legal=(0, 7))],
            entry="learn",
            groups=(("next_legal", "legal", "mask"), ("7",)),
            label="a refused batch with one malformed transition",
        )
        after = [
            package.act(learner, observation, mask)["action"]
            for observation, mask in probes
        ]
        self.assertEqual(
            before,
            after,
            "a refused batch moved the learner: validation must precede the first "
            "step, and the position advances nowhere else (rule.md §3)",
        )

    def test_agt11_g15_the_oracle_declares_257_samples(self):
        """G15 `baselines()`'s oracle declares the pinned equity sample count, 257 (`baselines.md` §5, `surface.md` §11, G15, ASM-4)."""
        package = self.agents()
        declared = package.baselines()["oracle"]["equity_samples"]
        self.assertEqual(plain_int(declared, "equity_samples"), 257)

    def test_agt11_g16_a_policy_is_a_snapshot_and_stays_legal(self):
        """G16 a policy keeps its snapshot and never leaves `legal_actions` (`surface.md` §10, `rule.md` §7, G16)."""
        package = self.agents()
        learner = self.build(kind="naive-stack", width=8, depth=1)
        policy = package.as_policy(learner, flat_encoder(), LEARNER_SEED)
        rows = self.decisions(3)
        before = [policy(row["readout"], row["legal"]) for row in rows]
        package.learn(learner, batch([dense_observation(0.2 * step) for step in range(6)]))
        after = [policy(row["readout"], row["legal"]) for row in rows]
        self.assertEqual(before, after)
        for row, answer in zip(rows, after):
            with self.subTest(hand=row["readout"]["hole"]):
                self.assertIn(answer, tuple(row["legal"]))


    def parameters_array(self, path):
        """The one array member of the container `save` wrote (`checkpoint.md` §2)."""
        with zipfile.ZipFile(path) as container:
            names = container.namelist()
            self.assertIn(
                "parameters.npy",
                names,
                "the checkpoint carries no 'parameters.npy' member: %r" % (names,),
            )
            data = container.read("parameters.npy")
        return np.load(io.BytesIO(data))

    def parameter_copies(self, path, count):
        """The container's two copies of the parameters, `[0, P)` and `[P, 2P)` (`checkpoint.md` §2)."""
        array = self.parameters_array(path)
        self.assertGreaterEqual(
            int(array.shape[0]),
            2 * count,
            "the container's array is shorter than the two copies of P (%d values "
            "for P = %d)" % (int(array.shape[0]), count),
        )
        return array[:count], array[count : 2 * count]


if __name__ == "__main__":
    unittest.main()
