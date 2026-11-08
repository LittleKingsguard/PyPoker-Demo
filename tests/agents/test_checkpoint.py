"""AGT-7 — `save` / `load`.

Drives `docs/L3/agents/checkpoint.md` §1-§5, `docs/L2/agents/surface.md`
§8-§9, `docs/L1/rules.md` §6 and ASM-5: the caller's path is written byte for
byte and nowhere else, the pair is loss-free at the decision boundary **on a
learner a `learn` has moved**, a member loads from its path alone, a spec that
agrees loads while one that disagrees is refused naming the key — the
`learning_rule` among the compared keys (D-19) — a container carrying a value
§2.1 does not declare is refused naming the field and the value, and the
recorded state a restore must recover — parameters, seed, schedule position, the
target copy, and the rule the container names, a version-1 file being read as
`masked-q-learning` — is observed where it decides: in `act`, in the next
`learn`, in the metadata and in the policy — on a synthetic copy of the
container and on the version-1 set the repository actually ships, discovered by
walking `checkpoints/` and opened read-only (D-16, D-19).
"""

import json
import os
import subprocess
import sys
import unittest
import zipfile

from _agents_support import (
    ANNEAL_SEED,
    CHECKPOINT_NAMES,
    LEARNER_SEED,
    OTHER_SEED,
    REPO_ROOT,
    SRC_ROOT,
    AgentsCase,
    anneal_batch,
    declared_internal,
    features,
    finite_float,
    flat_encoder,
    learner_spec,
    plain_int,
    token_encoder,
)

#: The tree the repository ships its version-1 containers under, read **read-only**
#: (`checkpoint.md` §3, `rules.md` §6).  It belongs to `training` (`module-map.md` §5,
#: `surface.md` §8), so this battery opens it and writes nothing under it.
SHIPPED_ROOT = os.path.join(REPO_ROOT, "checkpoints")

#: G6's witness for the container's *value* checks, run in a clean interpreter so
#: "a numpy checkpoint imports no torch" is asserted and not inherited from what an
#: earlier case already imported (`checkpoint.md` §3, `backends.md` §1, §4, G6).
DOCTORED_SCRIPT = """
import json
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, SRC)

import agents

print("imported", "torch" in sys.modules)
learner = agents.build_learner(
    {"backend": "numpy",
     "architecture": {"kind": "naive-stack", "width": 6, "depth": 1},
     "seed": 8127}
)
folder = tempfile.mkdtemp()
path = agents.save(learner, os.path.join(folder, "v-8127-numpy.pt"))
agents.load(None, path)
print("loaded", "torch" in sys.modules)
with zipfile.ZipFile(path) as container:
    metadata = json.loads(container.read("metadata.json").decode("utf-8"))
    parameters = container.read("parameters.npy")
metadata["backend"] = "jax"
doctored = os.path.join(folder, "doctored-a.pt")
with open(doctored, "wb") as handle:
    with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_STORED) as container:
        container.writestr("metadata.json", json.dumps(metadata).encode("utf-8"))
        container.writestr("parameters.npy", parameters)
try:
    agents.load(None, doctored)
except Exception as error:
    print("refused", "jax" in str(error))
else:
    print("refused", False)
print("doctored", "torch" in sys.modules)
"""


def rewrite_metadata(source, target, field, value):
    """Copy one container to `target`, with one dotted field of §2.1 doctored.

    Both members are the file's own bytes; only the metadata value the caller
    names is replaced, which is how a case builds a file this module did not write
    — the doctored instance a value check must refuse (`checkpoint.md` §2, §3).
    """
    with zipfile.ZipFile(source) as container:
        metadata = json.loads(container.read("metadata.json").decode("utf-8"))
        parameters = container.read("parameters.npy")
    record = metadata
    keys = field.split(".")
    for key in keys[:-1]:
        record = record[key]
    record[keys[-1]] = value
    with open(target, "wb") as handle:
        with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_STORED) as container:
            container.writestr("metadata.json", json.dumps(metadata).encode("utf-8"))
            container.writestr("parameters.npy", parameters)
    return target


def version_one_metadata(source, target):
    """Copy one container to `target` in the **version-1** form of `checkpoint.md` §3.

    Both members are the file's own bytes and every metadata field `save` wrote is
    kept, except that `format_version` reads `1` and `learning_rule` — a field no
    version-1 writer wrote — is gone.  That is the reading rule D-19 requires of
    the 18 shipped containers, built here from a file this module wrote so the
    version-1 path is driven without touching `checkpoints/`.
    """
    with zipfile.ZipFile(source) as container:
        metadata = json.loads(container.read("metadata.json").decode("utf-8"))
        parameters = container.read("parameters.npy")
    metadata["format_version"] = 1
    metadata.pop("learning_rule", None)
    with open(target, "wb") as handle:
        with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_STORED) as container:
            container.writestr("metadata.json", json.dumps(metadata).encode("utf-8"))
            container.writestr("parameters.npy", parameters)
    return target


def files_under(root):
    """Every file under `root`, walked and sorted: the shipped set exactly as it is.

    A version is discovered by the tree's contents and never by a name pattern
    (`checkpoint.md` §1, §3): the walk finds whatever rung, variant and seed
    directories a checkout holds.  The R1 run's evidence record ships beside the
    containers, which is why `shipped_containers` filters by content and not by name.
    """
    found = []
    for directory, _subdirectories, filenames in os.walk(root):
        for name in filenames:
            found.append(os.path.join(directory, name))
    return sorted(found)


def shipped_containers(root):
    """The files under `root` that open as a zip container, sorted.

    `zipfile.is_zipfile` is the one filter, and it is a content test: a file that is a
    zip and not one of this module's containers is left to `load` to refuse, so no name
    and no member is consulted here (`checkpoint.md` §2, §3).
    """
    return [path for path in files_under(root) if zipfile.is_zipfile(path)]


def tree_fingerprint(root):
    """`{path: (size, mtime_ns)}` for every file under `root`: what a read must not move.

    Read-only is a claim about the tree (`surface.md` §8): a battery that opened one of
    `training`'s shipped containers for writing, appended a member or rewrote a byte
    shows here, and nothing else in this case may change the tree.
    """
    fingerprint = {}
    for path in files_under(root):
        status = os.stat(path)
        fingerprint[path] = (status.st_size, status.st_mtime_ns)
    return fingerprint


class CheckpointTest(AgentsCase):
    def test_agt7_1_save_writes_exactly_the_path_it_was_handed(self):
        """AGT-7.1 `.pt`, `.pth` and `.ckpt` land at the caller's spelling and no `.npz` sibling appears (`checkpoint.md` §2, G11, `surface.md` §8)."""
        package = self.agents()
        folder = self.tempdir()
        for name in CHECKPOINT_NAMES:
            with self.subTest(name=name):
                learner = self.build(kind="naive-stack")
                path = os.path.join(folder, name)
                written = package.save(learner, path)
                self.assertIsInstance(written, str)
                self.assertEqual(written, path)
                self.assertTrue(os.path.isfile(path), "save wrote no file at %r" % path)
                self.assertGreater(os.path.getsize(path), 0)
                self.assertFalse(
                    os.path.exists(path + ".npz"),
                    "save appended .npz to the caller's path",
                )
                self.assertFalse(
                    os.path.exists(os.path.splitext(path)[0] + ".npz"),
                    "save substituted a .npz spelling",
                )

    def test_agt7_2_the_round_trip_keeps_the_decision_of_a_learned_learner(self):
        """AGT-7.2 a checkpoint of a learned learner restores its parameters and its schedule position: `act`'s index agrees over 20 decisions, at least 16 of them greedy-expected, while a checkpoint written before that learning decides differently on at least one of them (`checkpoint.md` §1-§4, `rule.md` §1, §4, `surface.md` §9, G12, ASM-5)."""
        package = self.agents()
        learner = self.annealed_learner(
            "round-trip", {"kind": "naive-stack", "width": 8, "depth": 1}
        )
        rows = self.decisions(20)
        observations, masks = map(list, zip(*self.decision_observations(rows, "naive-stack")))
        self.greedy_arm(LEARNER_SEED, "naive-stack", observations, masks, 16)
        folder = self.tempdir()
        learned_path = package.save(learner, os.path.join(folder, "learned-8127.pt"))
        fresh = self.build(kind="naive-stack", width=8, depth=1)
        fresh_path = package.save(fresh, os.path.join(folder, "fresh-8127.pt"))
        restored = package.load(None, learned_path)
        before_learning = package.load(None, fresh_path)
        differences = 0
        for row in rows:
            saved = package.act(learner, row["dense"], row["mask"])["action"]
            loaded = package.act(restored, row["dense"], row["mask"])["action"]
            with self.subTest(hand=row["readout"]["hole"]):
                self.assertEqual(
                    saved,
                    loaded,
                    "the restored learner did not decide as the saved one",
                )
            if package.act(before_learning, row["dense"], row["mask"])["action"] != loaded:
                differences += 1
        self.assertGreater(
            differences,
            0,
            "a checkpoint written before the learning and one written after it "
            "restored learners that decide alike on every one of 20 decisions, so "
            "the saved parameter values did not travel (the two learners share a "
            "seed and differ only in what the batch taught them)",
        )

    def test_agt7_3_a_restored_learner_reports_the_saved_count(self):
        """AGT-7.3 the restored learner reports the saved `param_count` (`checkpoint.md` §4, `surface.md` §9)."""
        package = self.agents()
        learner = self.build(kind="deep", width=12, depth=2)
        kept = package.param_count(learner)
        restored = package.load(
            None, package.save(learner, os.path.join(self.tempdir(), CHECKPOINT_NAMES[2]))
        )
        self.assertEqual(package.param_count(restored), kept)

    def test_agt7_4_a_spec_that_agrees_loads(self):
        """AGT-7.4 a spec agreeing on backend, kind and seed loads (`surface.md` §9, `checkpoint.md` §3, G13)."""
        package = self.agents()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        path = package.save(learner, os.path.join(self.tempdir(), CHECKPOINT_NAMES[1]))
        spec = learner_spec(kind="naive-stack", width=6, depth=1, seed=LEARNER_SEED)
        restored = package.load(spec, path)
        self.assertEqual(package.param_count(restored), package.param_count(learner))

    def test_agt7_5_a_disagreeing_spec_is_refused_naming_the_key(self):
        """AGT-7.5 a spec disagreeing on seed, backend or kind is refused naming that key (`checkpoint.md` §3, `surface.md` §9)."""
        package = self.agents()
        folder = self.tempdir()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        path = package.save(learner, os.path.join(folder, CHECKPOINT_NAMES[0]))
        cases = (
            (
                "a seed that disagrees",
                learner_spec(kind="naive-stack", seed=OTHER_SEED),
                (("seed",), (str(OTHER_SEED),), (str(LEARNER_SEED),)),
            ),
            (
                "a backend that disagrees",
                learner_spec(backend="torch", kind="naive-stack"),
                (("backend",), ("torch",), ("numpy",)),
            ),
            (
                "a kind that disagrees",
                learner_spec(kind="deep", width=6, depth=1),
                (("kind",), ("deep",), ("naive-stack",)),
            ),
        )
        for label, spec, groups in cases:
            with self.subTest(case=label):
                self.assert_refused(
                    package.load, spec, path, entry="load", groups=groups, label=label
                )

    def test_agt7_6_a_path_that_does_not_exist_is_refused(self):
        """AGT-7.6 a missing path is refused naming the path (`checkpoint.md` §3, `surface.md` §9)."""
        package = self.agents()
        path = os.path.join(self.tempdir(), "absent-8127.pt")
        self.assert_refused(
            package.load,
            None,
            path,
            entry="load",
            groups=(("path",), (path,)),
            label="a missing checkpoint path",
        )

    def test_agt7_7_a_non_checkpoint_is_refused(self):
        """AGT-7.7 a file that is not this container is refused naming the path (`checkpoint.md` §3, `surface.md` §9)."""
        package = self.agents()
        path = os.path.join(self.tempdir(), "not-a-checkpoint-8127.pt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("this file is not a pypoker-agents-checkpoint\n")
        self.assert_refused(
            package.load,
            None,
            path,
            entry="load",
            groups=(("path",), (path,), ("checkpoint", "format")),
            label="a text file as a checkpoint",
        )

    def test_agt7_8_the_loaded_learner_is_independent_of_its_source(self):
        """AGT-7.8 a `learn` on the restored learner leaves the saved learner's decisions alone, over 20 decisions of a learned learner (`checkpoint.md` §2, §4, ASM-5)."""
        package = self.agents()
        learner = self.annealed_learner(
            "round-trip", {"kind": "naive-stack", "width": 8, "depth": 1}
        )
        path = package.save(learner, os.path.join(self.tempdir(), CHECKPOINT_NAMES[0]))
        restored = package.load(None, path)
        rows = self.decisions(20)
        observations, masks = map(list, zip(*self.decision_observations(rows, "naive-stack")))
        self.greedy_arm(LEARNER_SEED, "naive-stack", observations, masks, 16)
        before = [package.act(learner, row["dense"], row["mask"])["action"] for row in rows]
        package.learn(restored, anneal_batch("naive-stack", seed=ANNEAL_SEED + 3))
        after = [package.act(learner, row["dense"], row["mask"])["action"] for row in rows]
        self.assertEqual(before, after, "learning on the restored learner moved its source")
        self.assertEqual(package.param_count(restored), package.param_count(learner))

    def test_agt7_9_save_refuses_a_non_learner_and_an_unwritable_path(self):
        """AGT-7.9 `save` refuses a value that is not a learner naming the learner, and a path that is not a writable file location naming the path, leaving no partial file and inventing no directory (`surface.md` §8, `checkpoint.md` §3, `errors.md` §3, G14)."""
        package = self.agents()
        folder = self.tempdir()
        learner = self.build(kind="naive-stack", width=6, depth=1)

        refused_path = os.path.join(folder, "not-a-learner-8127.pt")
        self.assert_refused(
            package.save,
            {"learner": 1},
            refused_path,
            entry="save",
            groups=(("learner",),),
            label="save of a dict",
        )
        self.assertFalse(
            os.path.exists(refused_path),
            "save wrote at the caller's path before refusing a non-learner",
        )

        missing_parent = os.path.join(folder, "absent-directory", "v-8127.pt")
        self.assert_refused(
            package.save,
            learner,
            missing_parent,
            entry="save",
            groups=(("path",), (missing_parent,)),
            label="a path inside a directory that does not exist",
        )
        self.assertFalse(
            os.path.exists(missing_parent),
            "save wrote a partial checkpoint at a path it refused",
        )
        self.assertFalse(
            os.path.exists(os.path.dirname(missing_parent)),
            "save invented a directory, and it invents none (checkpoint.md §3)",
        )

        existing_directory = os.path.join(folder, "a-directory.pt")
        os.mkdir(existing_directory)
        self.assert_refused(
            package.save,
            learner,
            existing_directory,
            entry="save",
            groups=(("path",), (existing_directory,)),
            label="a path that is a directory",
        )
        self.assertTrue(os.path.isdir(existing_directory))
        self.assertEqual(
            os.listdir(existing_directory),
            [],
            "save left a partial checkpoint inside the directory it refused",
        )

    def test_agt7_10_a_specs_encoder_must_agree_with_the_checkpoint(self):
        """AGT-7.10 `load` with a spec carrying an encoder whose representation contradicts the checkpoint is refused naming both sides (`checkpoint.md` §3, `surface.md` §9, `architecture.md` §6, G13)."""
        package = self.agents()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        path = package.save(learner, os.path.join(self.tempdir(), CHECKPOINT_NAMES[1]))
        spec = learner_spec(
            kind="naive-stack", width=6, depth=1, encoder=token_encoder()
        )
        self.assert_refused(
            package.load,
            spec,
            path,
            entry="load",
            groups=(
                ("encoder", "representation"),
                ("card-tokens", "token-sequence", "96"),
                ("naive-stack", "dense-numeric", "203"),
            ),
            label="a card-tokens encoder against a dense checkpoint",
        )

    def test_agt7_11_one_checkpoint_restored_twice_decides_alike(self):
        """AGT-7.11 one checkpoint restored twice gives two learners that decide alike, because a decision is a function of state and decision and not of call order (`surface.md` §9, `checkpoint.md` §4, ASM-5)."""
        package = self.agents()
        learner = self.annealed_learner(
            "round-trip", {"kind": "naive-stack", "width": 8, "depth": 1}
        )
        path = package.save(learner, os.path.join(self.tempdir(), CHECKPOINT_NAMES[2]))
        first = package.load(None, path)
        second = package.load(None, path)
        rows = self.decisions(20)
        observations, masks = map(list, zip(*self.decision_observations(rows, "naive-stack")))
        self.greedy_arm(LEARNER_SEED, "naive-stack", observations, masks, 16)
        for row in rows:
            with self.subTest(hand=row["readout"]["hole"]):
                self.assertEqual(
                    package.act(first, row["dense"], row["mask"])["action"],
                    package.act(second, row["dense"], row["mask"])["action"],
                    "one checkpoint restored twice gave two learners that disagree",
                )
        self.assertEqual(package.param_count(first), package.param_count(second))

    def test_agt7_12_the_target_copy_and_its_counter_travel(self):
        """AGT-7.12 the target copy and its consumed-transition counter are part of the file: after a restore the next `learn` reports the saved learner's own `td_error`, before and after a refresh boundary (`checkpoint.md` §1-§2.1, `rule.md` §3, G9, G12, ASM-5)."""
        package = self.agents()
        learner = self.annealed_learner(
            "target-copy", {"kind": "naive-stack", "width": 8, "depth": 1}
        )
        # 37 transitions leave the target copy stale and the counter off a refresh
        # boundary (the anneal's own 2,000 did land on one).
        package.learn(learner, anneal_batch("naive-stack", seed=ANNEAL_SEED + 5)[:37])
        path = package.save(learner, os.path.join(self.tempdir(), CHECKPOINT_NAMES[0]))
        restored = package.load(None, path)

        probe = anneal_batch("naive-stack", seed=ANNEAL_SEED + 9)[:12]
        saved = package.learn(learner, probe)
        loaded = package.learn(restored, probe)
        self.assertEqual(
            plain_int(loaded["transitions"], "transitions"),
            plain_int(saved["transitions"], "transitions"),
        )
        self.assertEqual(
            finite_float(loaded["td_error"], "td_error"),
            finite_float(saved["td_error"], "td_error"),
            "the restored learner's first update did not report the saved "
            "learner's td_error, so the target copy the bootstrap reads did not "
            "travel (checkpoint.md §1)",
        )

        # 12 + 163 = 175 consumed, so 37 + 175 crosses the refresh interval: a
        # learner whose counter was not restored crosses it at another transition.
        drift = anneal_batch("naive-stack", seed=ANNEAL_SEED + 11)[:163]
        package.learn(learner, drift)
        package.learn(restored, drift)
        after = anneal_batch("naive-stack", seed=ANNEAL_SEED + 13)[:12]
        saved_after = package.learn(learner, after)
        loaded_after = package.learn(restored, after)
        self.assertEqual(
            finite_float(loaded_after["td_error"], "td_error"),
            finite_float(saved_after["td_error"], "td_error"),
            "the two learners refreshed the target copy at different transitions, "
            "so the consumed-transition counter did not travel (rule.md §3, "
            "checkpoint.md §2.1)",
        )

    def test_agt7_13_a_doctored_checkpoint_is_refused(self):
        """AGT-7.13 `load` refuses a `metadata.json` carrying a value §2.1 does not declare — an undeclared `backend` (`checkpoint.md` §3, first row of its *Values are checked* paragraph), a `format_version` this module does not know (§3's format paragraph) and a `settings` value outside its declared range (§2.1-§3) — naming the field and the value with this module's own error, so no name is coerced to `torch`; and a clean interpreter's `import agents` plus a numpy checkpoint's `load` leave `torch` out of `sys.modules` (§3, `errors.md` §3, `backends.md` §1, §4, G6)."""
        package = self.agents()
        folder = self.tempdir()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        source = package.save(learner, os.path.join(folder, "source-8127.pt"))
        cases = (
            (
                "an undeclared backend",
                "doctored-a.pt",
                "backend",
                "jax",
                "checkpoint.md §3 (a backend outside backends.md §1's two)",
                (("backend",), ("jax",)),
            ),
            (
                "a format version this module does not know",
                "doctored-b.pt",
                "format_version",
                4242,
                "checkpoint.md §3 (format_version is 1, never guessed)",
                (("format_version", "format version"), ("4242",)),
            ),
            (
                "a settings value outside its declared range",
                "doctored-c.pt",
                "settings.sparsity",
                1.5,
                "checkpoint.md §2.1-§3 (sparsity in [0, 1])",
                (("sparsity",), ("1.5",)),
            ),
        )
        for label, name, field, value, section, groups in cases:
            doctored = rewrite_metadata(source, os.path.join(folder, name), field, value)
            with self.subTest(case=label, holds=section):
                self.assert_agents_refusal(
                    package.load,
                    None,
                    doctored,
                    entry="load",
                    groups=groups,
                    label="%s: %s = %r" % (label, field, value),
                )
        self.assertEqual(
            package.param_count(package.load(None, source)),
            package.param_count(learner),
            "the container the doctored copies came from must still load, so the "
            "refusals above are the doctored values' and not the file's",
        )

        script = DOCTORED_SCRIPT.replace("SRC", repr(SRC_ROOT), 1)
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
        self.assertIn(
            "imported False",
            completed.stdout,
            "`import agents` imported torch, which no module-level import may "
            "(backends.md §4, G6):\n%s" % completed.stdout,
        )
        self.assertIn(
            "loaded False",
            completed.stdout,
            "loading a numpy checkpoint imported torch, so the recorded backend was "
            "not checked before a backend module was (checkpoint.md §3, G6):\n%s"
            % completed.stdout,
        )
        self.assertIn(
            "refused True",
            completed.stdout,
            "a clean interpreter's `load` accepted an undeclared backend:\n%s"
            % completed.stdout,
        )
        self.assertIn(
            "doctored False",
            completed.stdout,
            "refusing an undeclared backend imported torch, so the value was "
            "coerced to a backend instead of being refused (checkpoint.md §3):\n%s"
            % completed.stdout,
        )


    def test_agt7_14_the_container_records_the_rule(self):
        """AGT-7.14 `save` writes format version 2 and records the learner's `learning_rule`, and a double-Q member round-trips and loads under a spec naming that rule (`checkpoint.md` §2.1, §3, `surface.md` §8-§9, `rules.md` §6, `rule.md` §8, D-19).

        The field is required of a version-2 container and is read back through
        `checkpoint._read_metadata(path)`, the sixth internal `rule.md` §8 declares
        for exactly this, and through the public attribute
        `as_policy(...).learning_rule` (`e2e-surface.md` §2).  A spec naming the
        file's own rule is a compared key that agrees, so it loads.  The container
        side is the half `guardrails.md` G12 names beside the version-1 reading,
        which is AGT-7.15.
        """
        package = self.agents()
        read_metadata = declared_internal("checkpoint", "_read_metadata")
        folder = self.tempdir()
        catalogue = tuple(package.learners()["learning_rules"])
        self.assertGreaterEqual(len(catalogue), 2, "the catalogue carries two members")
        default_rule, double_rule = catalogue[0], "double-q-learning"
        self.assertIn(double_rule, catalogue)
        learners = (
            (default_rule, self.build(kind="naive-stack", width=6, depth=1)),
            (
                double_rule,
                package.build_learner(
                    learner_spec(
                        kind="naive-stack",
                        width=6,
                        depth=1,
                        extra={"learning_rule": double_rule},
                    )
                ),
            ),
        )
        paths = {}
        for rule, learner in learners:
            with self.subTest(rule=rule):
                path = package.save(
                    learner, os.path.join(folder, "v2-%s.pt" % (rule,))
                )
                metadata = read_metadata(path)
                self.assertEqual(
                    plain_int(metadata["format_version"], "format_version"),
                    2,
                    "a container this module writes is format version 2 "
                    "(checkpoint.md §2.1, §3, D-19)",
                )
                self.assertEqual(
                    metadata["learning_rule"],
                    rule,
                    "a version 2 container records, in `learning_rule`, the catalogue "
                    "member its learner was trained under (checkpoint.md §2.1, §3)",
                )
                paths[rule] = path

        double_path = paths[double_rule]
        restored = package.load(None, double_path)
        self.assertEqual(
            getattr(
                package.as_policy(restored, flat_encoder(), LEARNER_SEED),
                "learning_rule",
                None,
            ),
            double_rule,
            "a restored learner learns under the rule its container records "
            "(surface.md §9, rules.md §6, D-19)",
        )
        via_spec = package.load(
            learner_spec(
                kind="naive-stack",
                width=6,
                depth=1,
                extra={"learning_rule": double_rule},
            ),
            double_path,
        )
        self.assertEqual(
            package.param_count(via_spec),
            package.param_count(restored),
            "a spec naming the file's own rule agrees on that compared key and loads "
            "(surface.md §9, checkpoint.md §3)",
        )

    def test_agt7_15_a_version_one_container_is_read_as_masked_q_learning(self):
        """AGT-7.15 a version-1 container carries no rule and is read as `masked-q-learning`, decides as its learner did, while a version-1 container carrying the field and a version-2 one naming an uncarried rule are refused (`checkpoint.md` §3, `surface.md` §9, `rules.md` §6, D-19).

        The 18 containers the repository ships were written before the catalogue
        existed and none is regenerated, so the version-1 reading is contract: the
        only rule such a writer could have used is the catalogue's first member.  The
        file is built from one this module wrote — both members the file's own bytes,
        `format_version` rewritten and `learning_rule` dropped — so `checkpoints/`
        is never touched.  A version-1 container that *carries* the field was edited
        and is refused by name, and a rule outside the catalogue is refused naming
        the field and the value.
        """
        package = self.agents()
        folder = self.tempdir()
        catalogue = tuple(package.learners()["learning_rules"])
        default_rule = catalogue[0]
        learner = self.annealed_learner(
            "rule-v1", {"kind": "naive-stack", "width": 8, "depth": 1}
        )
        source = package.save(learner, os.path.join(folder, "v2-source-8127.pt"))
        older = version_one_metadata(
            source, os.path.join(folder, "v1-8127.pt")
        )
        restored = package.load(None, older)
        self.assertEqual(
            getattr(
                package.as_policy(restored, flat_encoder(), LEARNER_SEED),
                "learning_rule",
                None,
            ),
            default_rule,
            "a version 1 container carries no `learning_rule` and is read as %r, the "
            "only rule its writer could have used (checkpoint.md §3, rules.md §6)"
            % (default_rule,),
        )
        rows = self.decisions(20)
        observations, masks = map(
            list, zip(*self.decision_observations(rows, "naive-stack"))
        )
        self.greedy_arm(LEARNER_SEED, "naive-stack", observations, masks, 16)
        for row in rows:
            with self.subTest(hand=row["readout"]["hole"]):
                self.assertEqual(
                    package.act(restored, row["dense"], row["mask"])["action"],
                    package.act(learner, row["dense"], row["mask"])["action"],
                    "the version-1 reading changes the rule alone: the restored "
                    "learner makes the saved learner's decisions (surface.md §9, "
                    "checkpoint.md §4, ASM-5)",
                )

        carrying = rewrite_metadata(
            source,
            os.path.join(folder, "v1-carrying-8127.pt"),
            "format_version",
            1,
        )
        self.assert_agents_refusal(
            package.load,
            None,
            carrying,
            entry="load",
            groups=(("learning_rule",),),
            label="a version 1 container carrying a learning_rule",
        )
        uncarried = rewrite_metadata(
            source,
            os.path.join(folder, "uncarried-8127.pt"),
            "learning_rule",
            "monte-carlo",
        )
        self.assert_agents_refusal(
            package.load,
            None,
            uncarried,
            entry="load",
            groups=(("learning_rule",), ("monte-carlo",)),
            label="a version 2 container naming a rule outside the catalogue",
        )

    def test_agt7_16_load_compares_the_specs_rule_with_the_files(self):
        """AGT-7.16 a spec whose `learning_rule` disagrees with the file's is refused naming both values, and a spec naming a rule outside the catalogue is refused naming it (`checkpoint.md` §3, `surface.md` §9, `errors.md` §3, `rules.md` §6, D-19).

        `learning_rule` is a compared key exactly as `seed`, `backend` and the kind
        are: a disagreement names both values, and a value the catalogue does not
        carry is validated before it is compared and refused as this module's own
        error, never coerced onto the file's rule (`errors.md` §4).
        """
        package = self.agents()
        catalogue = tuple(package.learners()["learning_rules"])
        self.assertGreaterEqual(len(catalogue), 2)
        default_rule, other_rule = catalogue[0], catalogue[1]
        learner = self.build(kind="naive-stack", width=6, depth=1)
        path = package.save(
            learner, os.path.join(self.tempdir(), CHECKPOINT_NAMES[1])
        )
        self.assert_refused(
            package.load,
            learner_spec(
                kind="naive-stack",
                width=6,
                depth=1,
                extra={"learning_rule": other_rule},
            ),
            path,
            entry="load",
            groups=(("learning_rule",), (other_rule,), (default_rule,)),
            label="a spec naming another catalogue member than the file records",
        )
        self.assert_agents_refusal(
            package.load,
            learner_spec(
                kind="naive-stack",
                width=6,
                depth=1,
                extra={"learning_rule": "monte-carlo"},
            ),
            path,
            entry="load",
            groups=(("learning_rule",), ("monte-carlo",)),
            label="a spec naming a rule outside the catalogue",
        )
        agreed = package.load(
            learner_spec(
                kind="naive-stack",
                width=6,
                depth=1,
                extra={"learning_rule": default_rule},
            ),
            path,
        )
        self.assertEqual(package.param_count(agreed), package.param_count(learner))

    def test_agt7_17_the_shipped_version_one_set_loads_unchanged(self):
        """AGT-7.17 every container the repository ships is read, from its path alone, as `masked-q-learning` — format version 1, no `learning_rule` field, one positive `param_count` and a policy naming the catalogue's first member (`checkpoint.md` §3, `surface.md` §9, `rules.md` §4, §6, D-19, ASM-5).

        D-19 leaves the shipped set alone: the containers were written before the
        catalogue existed, so a version-1 container carries no rule and is read as
        `masked-q-learning`, the only rule its writer could have used, and it loads
        unchanged (`rules.md` §6, `checkpoint.md` §3).  AGT-7.15 drives that reading on
        a synthetic copy; this case drives it on what is actually shipped, so the
        artefact a restore recovers is the artefact the repository holds.  The set is
        discovered by walking `checkpoints/` — nothing is assumed about a name, a rung
        or a seed — and every container is opened read-only.  A checkout that does not
        hold the set skips rather than fails: the case is evidence about the shipped
        containers, never a precondition of the battery.  The encoder is the one the
        container's own `representation.encoding` names, since the set may hold both
        families (`encodings.md` §1), and the policy's seed is the recorded one
        (`surface.md` §10).
        """
        package = self.agents()
        if not os.path.isdir(SHIPPED_ROOT) or not os.listdir(SHIPPED_ROOT):
            self.skipTest(
                "the shipped version-1 set is not in this checkout: there is no "
                "checkpoints/ tree (or it holds no file) under %r, so the containers "
                "checkpoint.md §3 reads as masked-q-learning cannot be opened"
                % (REPO_ROOT,)
            )
        containers = shipped_containers(SHIPPED_ROOT)
        if not containers:
            self.skipTest(
                "the shipped version-1 set is not in this checkout: %r holds no file "
                "that opens as a zip container, so checkpoint.md §3's reading of the "
                "shipped versions cannot be exercised" % (SHIPPED_ROOT,)
            )
        catalogue = tuple(package.learners()["learning_rules"])
        self.assertGreaterEqual(
            len(catalogue),
            2,
            "the catalogue carries the two members rules.md §2 declares, and a "
            "version-1 container is read as its first",
        )
        first_member = catalogue[0]
        self.assertEqual(
            first_member,
            "masked-q-learning",
            "the catalogue's declared first member — the default a spec naming no rule "
            "is built under, and the rule a version-1 container is read as — is "
            "masked-q-learning (rules.md §2, §4, surface.md §3, D-19)",
        )
        # The set is read as the checkout holds it: `rules.md` §6 and `checkpoint.md` §3
        # count 18 containers, and this case reads every one the walk finds rather than
        # pinning a number a checkout may not hold.
        before = tree_fingerprint(SHIPPED_ROOT)
        for path in containers:
            name = os.path.relpath(path, REPO_ROOT)
            with self.subTest(container=name):
                with zipfile.ZipFile(path, "r") as container:  # read-only, always
                    metadata = json.loads(
                        container.read("metadata.json").decode("utf-8")
                    )
                self.assertEqual(
                    plain_int(metadata["format_version"], "metadata['format_version']"),
                    1,
                    "the shipped container %r is not format version 1, and a version-1 "
                    "container is what carries no rule (checkpoint.md §3, rules.md §6)"
                    % (name,),
                )
                self.assertNotIn(
                    "learning_rule",
                    metadata,
                    "the shipped container %r carries a `learning_rule` field: a "
                    "version-1 container has none, and one that carries it was edited "
                    "and is refused by name (checkpoint.md §2.1, §3, D-19)" % (name,),
                )
                restored = package.load(None, path)
                count = plain_int(
                    package.param_count(restored), "param_count(load(None, path))"
                )
                self.assertGreater(
                    count,
                    0,
                    "the shipped container %r restored a learner with no trainable "
                    "parameter (surface.md §5, checkpoint.md §4)" % (name,),
                )
                self.assertEqual(
                    count,
                    plain_int(
                        metadata["params"]["count"], "metadata['params']['count']"
                    ),
                    "the restored learner's count is not the count the container "
                    "records, which `params.count` is by definition and which a load "
                    "checks against the rebuilt layout (checkpoint.md §2.1, §3)",
                )
                encoding = metadata["representation"]["encoding"]
                policy = package.as_policy(
                    restored,
                    features().build_encoder(encoding),
                    plain_int(metadata["seed"], "metadata['seed']"),
                )
                self.assertEqual(
                    getattr(policy, "learning_rule", None),
                    first_member,
                    "the shipped container %r is not read as %r: a version-1 container "
                    "carries no rule and is read as the catalogue's first member, and "
                    "the policy it yields at its recorded seed names that rule "
                    "(checkpoint.md §3, surface.md §9-§10, rules.md §4, §6, D-19)"
                    % (name, first_member),
                )
        self.assertEqual(
            tree_fingerprint(SHIPPED_ROOT),
            before,
            "reading the shipped set moved its tree: checkpoints/ belongs to "
            "`training` and this module reads it read-only, writing only where it is "
            "told (surface.md §8, module-map.md §5)",
        )


if __name__ == "__main__":
    unittest.main()
