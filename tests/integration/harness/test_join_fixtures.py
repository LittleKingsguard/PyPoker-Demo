"""The fixture join -- HRNJ-6.

`docs/L2/harness/surface.md` §3: `fixtures()` pins four facts and takes no argument -- the
scratch root, "an absolute path this module owns, created on the first call and reused by
every later call in the process, empty at process start, and writable"; `seed`, "the
pinned seed: `0`, the protocol's first seed"; `device`, "`cpu`"; and `expectations`, "the
expectation kinds §6 accepts, as an ordered sequence of names, first kind first", where
"the first listed kind is the one a battery that takes the first listed kind gets, so it
is the kind that judges an episode record" (`surface.md` §3, §6, H-1, H-6).

Every one of those four facts is a join with something outside the harness: the seed is
`evaluation.protocol()`'s first seed (`protocol.md` §2), the device is the one
`training.devices()` reports for this platform (D-8, `protocol.md` §6), and the kind list
is the vocabulary `expect` judges.  The fixture is required to restate none of them,
because "a fixture that read either would make pinned preconditions depend on another
module's implementation" -- so the battery reads both sides and checks they agree
(`surface.md` §3, D-13, FAM-14.1, FAM-16.33).
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


class FixturesJoin(J.JoinCase):
    """HRNJ-6 -- the pinned preconditions a case starts from, read against their owners."""

    def fixture(self):
        record = J.fixtures()
        self.assert_required_keys(
            record, J.FIXTURE_KEYS, "the record `harness.fixtures` returns",
            "docs/L2/harness/surface.md §3",
        )
        return record

    def test_hrnj_6_1_the_scratch_root_is_one_writable_directory_per_process(self):
        """HRNJ-6.1 one root, created by the first call and readable by a later one.

        `docs/L2/harness/surface.md` §3: the root is "created on the first call and reused
        by every later call in the process", and "a case that writes a file into it and
        reads it back in a later call finds it".  The battery calls `fixtures()` twice,
        writes between the calls, and reads the file back through the second call's root
        -- the H-6 alternative, a fresh root per call, would make a case's own writes
        unfindable (FAM-14.1, FAM-16.33, `battery.md` §2).
        """
        first = self.fixture()
        root = str(first["root"])
        self.assertTrue(
            os.path.isabs(root),
            "the scratch root is an absolute path this module owns "
            "(docs/L2/harness/surface.md §3): %r" % (root,),
        )
        self.assertTrue(
            os.path.isdir(root),
            "the root is created, not computed: it exists the moment `fixtures()` returns "
            "(docs/L2/harness/surface.md §3, FAM-14.1): %r" % (root,),
        )
        probe_name = "hrnj-6-1-probe.txt"
        probe = os.path.join(root, probe_name)
        with open(probe, "w", encoding="utf-8") as handle:
            handle.write("hrnj-6-1")
        self.addCleanup(lambda: os.path.exists(probe) and os.remove(probe))
        later = self.fixture()
        self.assertEqual(
            str(later["root"]), root,
            "the root is the same directory on every call in one process -- one root per "
            "process, shared by every case (docs/L2/harness/surface.md §3, H-6): %r "
            "against %r" % (later["root"], root),
        )
        self.assertTrue(
            os.path.exists(os.path.join(str(later["root"]), probe_name)),
            "a file a case writes into the root is readable by a later call: the harness "
            "does not delete, rename or empty the root it made "
            "(docs/L2/harness/surface.md §3, FAM-16.33): %r" % (later["root"],),
        )
        with open(os.path.join(str(later["root"]), probe_name), encoding="utf-8") as handle:
            self.assertEqual(
                handle.read(), "hrnj-6-1",
                "the root is writable by a case, which is what makes it a scratch root "
                "(docs/L2/harness/surface.md §3, FAM-14.1): %r" % (later["root"],),
            )
        nested = os.path.join(root, "hrnj-6-1-nested")
        os.makedirs(nested, exist_ok=True)
        self.addCleanup(lambda: os.path.isdir(nested) and os.rmdir(nested))
        self.assertTrue(
            os.path.isdir(nested),
            "a caller that needs a fresh directory creates one inside the root, and the "
            "root the fixture returned is a directory that holds one "
            "(docs/L2/harness/surface.md §3, `battery.md` §2): %r" % (root,),
        )

    def test_hrnj_6_2_the_pinned_seed_is_the_protocols_first_and_the_device_is_cpu(self):
        """HRNJ-6.2 the fixture's seed and device are the ones their owners declare.

        `docs/L2/harness/surface.md` §3 pins `seed` to `0` -- "the protocol's first seed,
        so the fixture invents no value a design document owns" -- and `device` to `cpu`,
        "a workflow-started run is CPU-bound".  The seed set is `evaluation.protocol()`'s
        (`protocol.md` §2) and the device catalogue `training.devices()`' (`D-8`,
        `protocol.md` §6), so the battery reads both and requires the pinned facts to be
        the owners' -- the fixture restates no catalogue of its own
        (`surface.md` §3, H-6, FAM-14.1).
        """
        fixture = self.fixture()
        seeds = list(J.protocol()["seeds"])
        self.assertTrue(
            seeds,
            "evaluation.protocol() declares the seed set a run records, so there is a "
            "first seed for the fixture to pin (docs/L1/protocol.md §2, "
            "docs/L2/evaluation/surface.md §3): %r" % (seeds,),
        )
        self.assertEqual(
            fixture["seed"], seeds[0],
            "the pinned seed is the protocol's first seed, so the fixture invents no value "
            "a design document owns (docs/L2/harness/surface.md §3, protocol.md §2, "
            "FAM-4): %r against %r" % (fixture["seed"], seeds[0]),
        )
        self.assertEqual(
            fixture["device"], "cpu",
            "the pinned device is `cpu`, the device a workflow-started run is bound to "
            "because the file sandbox denies the GPU device nodes "
            "(docs/L2/harness/surface.md §3, D-8, protocol.md §6): %r" % (fixture["device"],),
        )
        catalogue = J.devices()
        available = [str(name) for name in catalogue.get("available", ())]
        self.assertIn(
            "cpu", available,
            "`training.devices()` reports the CPU this platform's runs use, so the pin "
            "names a device the owner really has (docs/L2/training/surface.md §6, D-8, "
            "protocol.md §6): %r" % (catalogue,),
        )
        self.assertEqual(
            str(catalogue.get("default")), "cpu",
            "the device a workflow-started run gets is the owner's declared default, and "
            "the fixture pins that one rather than inventing one "
            "(docs/L2/training/surface.md §6, D-8): %r" % (catalogue,),
        )

    def test_hrnj_6_3_the_kind_list_is_the_vocabulary_expect_judges(self):
        """HRNJ-6.3 `expectations` lists exactly the kinds `expect` accepts, first first.

        `docs/L2/harness/surface.md` §3 makes `expectations` "the expectation kinds §6
        accepts, as an ordered sequence of names, first kind first", and §6 fixes the set
        and its order -- `zero-sum`, `legal-choice`, `counted`, `refused` -- so that "the
        first listed kind is the one a battery that takes the first listed kind gets, so it
        is the kind that judges an episode record" (H-1, FAM-14.1, FAM-14.8).  The battery
        asserts the list, that every listed kind is a kind `expect` judges, that the first
        one judges an episode `engine.play_hand` really played, and that an unlisted name
        is not silently passed as one (FAM-16.36, D-13).
        """
        fixture = self.fixture()
        kinds = list(fixture["expectations"])
        self.assertEqual(
            kinds, list(J.DECLARED_KINDS),
            "`fixtures()` lists the four expectation kinds §6 accepts, in its order, so a "
            "battery that takes the first listed kind takes the kind that judges an "
            "episode record (docs/L2/harness/surface.md §3, §6, H-1): %r" % (kinds,),
        )
        self.assertTrue(
            kinds,
            "`expectations` is a non-empty sequence of names "
            "(docs/L2/harness/surface.md §3): %r" % (kinds,),
        )
        self.assertEqual(
            list(self.fixture()["expectations"]), kinds,
            "the kind list is equal on every call, in every process: a precondition that "
            "varied would make a red case unreproducible "
            "(docs/L2/harness/surface.md §3, protocol.md §2, D-6): %r" % (kinds,),
        )
        episode = J.shared_episode()
        verdict = J.expect(kinds[0], episode)
        self.assertEqual(
            J.verdict_of(verdict), "pass",
            "the first listed kind judges an episode record -- the value most cases drive "
            "-- and the episode the engine played is one "
            "(docs/L2/harness/surface.md §3, §6, H-1): %r" % (verdict,),
        )
        for kind in kinds:
            record = J.expect(kind, episode)
            self.assertEqual(
                record.get("kind"), kind,
                "every kind the fixture lists is a kind `expect` judges: it states the "
                "kind as handed and answers with a verdict "
                "(docs/L2/harness/surface.md §3, §6): %r" % (record,),
            )
            self.assertIn(
                J.verdict_of(record), ("pass", "fail"),
                "a listed kind yields a verdict for a real record rather than a silence "
                "(docs/L2/harness/surface.md §3, §6): %r" % (record,),
            )
        unlisted = J.expect(J.UNKNOWN_KIND, episode)
        self.assertEqual(
            J.verdict_of(unlisted), "fail",
            "a kind the fixture does not list is not a kind `expect` accepts: it is a "
            "named failure and never a silent pass, which is what makes the listed set "
            "the accepted one (docs/L2/harness/surface.md §6, FAM-14.8): %r" % (unlisted,),
        )


if __name__ == "__main__":
    unittest.main()
