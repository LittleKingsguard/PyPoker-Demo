"""HRN-4 — `fixtures`: one scratch root per process, and three pinned facts.

Drives `docs/L3/harness/support.md` §1 and `docs/L2/harness/surface.md` §3: an absolute,
created, writable, shared `root` that is never inside the repository, `seed` `0`,
`device` `"cpu"` and `expectations` the four kinds in their declared order — the three
pinned facts equal on every call in every process, because a precondition that varied
would make a red case unreproducible (`guardrails.md` G7-G8, FAM-14.1, FAM-16.33,
D-6, protocol.md §2).
"""

import inspect
import os
import unittest

from _harness_support import (
    EXPECTATION_KINDS,
    REPO_ROOT,
    HarnessCase,
    as_mapping,
    as_sequence,
    as_text,
)


class FixturesTest(HarnessCase):
    def fixtures(self):
        """The fixture record, with `surface.md` §3's one-mapping shape asserted."""
        record = self.ep("fixtures")()
        return as_mapping(record, "the fixture record")

    def root_of(self, record):
        return str(as_text(str(record["root"]), "the fixture's root"))

    def test_hrn_4_1_the_root_is_absolute_created_and_writable(self):
        """HRN-4.1 `root` is an absolute path that exists when it is returned, is a directory, and accepts a file a case writes and reads back (support §1, surface §3, G7, FAM-14.1, FAM-16.33)."""
        root = self.root_of(self.fixtures())
        self.assertTrue(
            os.path.isabs(root),
            "the scratch root is an absolute path (support §1, surface §3, G7): %r"
            % (root,),
        )
        self.assertTrue(
            os.path.exists(root),
            "the root is created, not computed: `mkdtemp` makes the directory, so a "
            "case need not create it (support §1, FAM-14.1): %r" % (root,),
        )
        self.assertTrue(
            os.path.isdir(root),
            "the root is a directory, not a file a case cannot write into (support §1): "
            "%r" % (root,),
        )
        probe_dir = os.path.join(root, "HRN-4.1-probe")
        os.makedirs(probe_dir, exist_ok=True)
        probe = os.path.join(probe_dir, "written.txt")
        with open(probe, "w", encoding="utf-8") as handle:
            handle.write("a case's artefact")
        with open(probe, encoding="utf-8") as handle:
            self.assertEqual(
                handle.read(),
                "a case's artefact",
                "the root is writable when it is returned (support §1, surface §3, "
                "FAM-14.1): %r" % (root,),
            )
        os.remove(probe)
        os.rmdir(probe_dir)

    def test_hrn_4_2_one_root_per_process_and_a_case_s_artefact_stays_readable(self):
        """HRN-4.2 a second call returns the same root, and a file written in the first call is found through the second call's record — the root is created once and never deleted (support §1, surface §3, G7, FAM-16.33)."""
        first = self.fixtures()
        first_root = self.root_of(first)
        probe_dir = os.path.join(first_root, "HRN-4.2-probe")
        os.makedirs(probe_dir, exist_ok=True)
        probe = os.path.join(probe_dir, "kept.txt")
        with open(probe, "w", encoding="utf-8") as handle:
            handle.write("kept for a later case")
        second = self.fixtures()
        second_root = self.root_of(second)
        self.assertEqual(
            second_root,
            first_root,
            "the root is created once and named once, so every later call returns it "
            "(support §1, surface §3, G7): %r vs %r" % (first_root, second_root),
        )
        with open(os.path.join(second_root, "HRN-4.2-probe", "kept.txt"), encoding="utf-8") as handle:
            self.assertEqual(
                handle.read(),
                "kept for a later case",
                "an artefact a case wrote may still be needed after the case ended, so "
                "the harness never deletes or empties the root (support §1, "
                "battery.md §2): %r" % (second_root,),
            )
        os.remove(probe)
        os.rmdir(probe_dir)

    def test_hrn_4_3_the_seed_is_zero(self):
        """HRN-4.3 `seed` is `0`, the protocol's first seed, so the fixture invents no value a design document owns (support §1, surface §3, protocol.md §2)."""
        record = self.fixtures()
        self.assertIn(
            "seed",
            record,
            "the fixture pins a seed (support §1, surface §3): %r" % (list(record),),
        )
        seed = record["seed"]
        self.assertEqual(
            seed,
            0,
            "the pinned seed is 0, the protocol's first seed (support §1, surface §3, "
            "protocol.md §2): %r" % (seed,),
        )
        self.assertIsInstance(
            seed,
            int,
            "and it is stated as a number and not as text (support §1): %r" % (seed,),
        )
        self.assertFalse(
            isinstance(seed, bool),
            "a bool is a flag and not a seed (expectations §2.5's `_quantity`): %r"
            % (seed,),
        )

    def test_hrn_4_4_the_device_is_cpu_and_the_kinds_are_the_four_in_order(self):
        """HRN-4.4 `device` is `"cpu"` and `expectations` is the four kinds of expectations §2 in their declared order, first kind first (support §1, surface §3, expectations §2, G7)."""
        record = self.fixtures()
        device = record["device"]
        self.assertEqual(
            as_text(device, "the fixture's device"),
            "cpu",
            "the pinned device is cpu: a workflow-started run is CPU-bound because the "
            "file sandbox denies the GPU device nodes (support §1, D-8, protocol.md §6): "
            "%r" % (device,),
        )
        listed = as_sequence(record["expectations"], "the listed expectation kinds")
        self.assertEqual(
            list(listed),
            list(EXPECTATION_KINDS),
            "the fixture lists the four kinds of expectations §2 in KINDS' order — the "
            "first listed kind is the one that judges an episode record (support §1, "
            "expectations §2, L2's H-1): %r" % (list(listed),),
        )
        self.assertEqual(
            as_text(list(listed)[0], "the first listed kind"),
            "zero-sum",
            "the first listed kind is zero-sum, the kind most cases drive (expectations "
            "§2, FAM-14.8): %r" % (list(listed),),
        )
        self.assertEqual(
            self.fixtures()["expectations"],
            record["expectations"],
            "the kind set is equal on every call (support §1, surface §3): %r vs %r"
            % (record["expectations"], self.fixtures()["expectations"]),
        )

    def test_hrn_4_5_the_record_is_four_pinned_facts_and_not_a_catalogue_from_another_module(self):
        """HRN-4.5 the record carries exactly `root`, `seed`, `device`, `expectations`, and the three pinned values are the design's literals — no device catalogue and no seed set is read from `training.devices()` or `evaluation.protocol()` (support §1, surface §3, G8, D-13)."""
        record = self.fixtures()
        self.assertEqual(
            set(record),
            {"root", "seed", "device", "expectations"},
            "the fixture returns one mapping with these four keys, and restates no "
            "catalogue another module owns (support §1, surface §3, G8): %r"
            % (sorted(record),),
        )
        self.assertIsInstance(
            record["device"],
            str,
            "`device` is a plain pinned name and not a copy of training.devices()' "
            "catalogue record: %r" % (record["device"],),
        )
        self.assertEqual(
            record["device"],
            "cpu",
            "the device is the literal `cpu`, so a probe in another module that changed "
            "its mind cannot move it (support §1, surface §3, G8): %r"
            % (record["device"],),
        )
        listed = list(as_sequence(record["expectations"], "the listed expectation kinds"))
        for kind in listed:
            self.assertIn(
                kind,
                EXPECTATION_KINDS,
                "every listed kind is one of expectations §2's four names, spelled as "
                "the design spells it (support §1, G8): %r" % (listed,),
            )
        self.assertEqual(
            len(listed),
            len(EXPECTATION_KINDS),
            "the listed set is the four kinds and no fifth (support §1, surface §3, "
            "G8): %r" % (listed,),
        )
        self.assertNotIn(
            "available",
            record,
            "the device catalogue belongs to training.devices(), and a fixture that read "
            "it would make a pinned precondition depend on another module's "
            "implementation (surface §3, G8, D-13): %r" % (sorted(record),),
        )
        self.assertNotIn(
            "gpu",
            record,
            "and neither does the GPU probe's record appear here (surface §3, G8): %r"
            % (sorted(record),),
        )
        second = self.fixtures()
        for key in ("seed", "device", "expectations"):
            self.assertEqual(
                second[key],
                record[key],
                "`%s` is equal on every call, in every process (support §1, surface §3, "
                "D-6, protocol.md §2): %r vs %r" % (key, record[key], second[key]),
            )

    def test_hrn_4_6_the_root_is_not_inside_the_repository(self):
        """HRN-4.6 the root is outside the repository, so a battery cannot write into a shipped tree and `training.checkpoints`' index cannot list it (support §1, surface §3, module-map.md §5, FAM-16.31)."""
        root = os.path.realpath(self.root_of(self.fixtures()))
        repository = os.path.realpath(REPO_ROOT)
        self.assertNotEqual(
            root,
            repository,
            "the root is a scratch directory of its own and not the repository "
            "(support §1, G7): %r" % (root,),
        )
        self.assertFalse(
            root == repository or root.startswith(repository + os.sep),
            "a root under src/, checkpoints/ or tables/ would let a battery write into "
            "a shipped tree (support §1, module-map.md §5, FAM-16.31): %r is inside %r"
            % (root, repository),
        )
        for shipped in ("src", "checkpoints", "tables"):
            self.assertFalse(
                root == os.path.join(repository, shipped)
                or root.startswith(os.path.join(repository, shipped) + os.sep),
                "the root is not under the shipped `%s/` tree (support §1, G7): %r"
                % (shipped, root),
            )

    def test_hrn_4_7_fixtures_takes_no_argument(self):
        """HRN-4.7 `fixtures()` declares no parameter: a precondition the caller could vary would not be pinned (surface §3, support §1)."""
        signature = inspect.signature(self.ep("fixtures"))
        varying = [
            name
            for name, parameter in signature.parameters.items()
            if parameter.kind
            in (
                parameter.POSITIONAL_ONLY,
                parameter.POSITIONAL_OR_KEYWORD,
                parameter.VAR_POSITIONAL,
                parameter.KEYWORD_ONLY,
                parameter.VAR_KEYWORD,
            )
        ]
        self.assertEqual(
            varying,
            [],
            "fixtures() takes no argument, because a precondition that the caller could "
            "vary is not pinned (surface §3, support §1, records.md §14): %r"
            % (signature,),
        )


if __name__ == "__main__":
    unittest.main()
