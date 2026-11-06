"""The shipped evidence file -- TRNJ-9.

`docs/L2/training/evidence.md` §1-§4 and `docs/L3/training/evidence.md` §1-§7:
`checkpoints/evidence/r1-live.json` is the R1 live run's evidence, it is not an
interface, its run block is the record `training.run` returns, and every path in it is
a repository-relative spelling that resolves inside the repository.

Nothing here drives the producer: the file is evidence, no entry point reads or writes it, and
a case that regenerated it would pay the 3,000-hand run to compare a measurement with itself
(`docs/L3/training/evidence.md` §6, `docs/L1/protocol.md` §5).  What a case can check is the file
the repository ships -- its keys, the shape its curves take, the spelling of its paths, the
arithmetic that keeps its header and its matrix from contradicting each other, and the index
summary it records -- plus, at the battery's own budget, that a run record's curve block carries
the one spread array the bundle's layout hoists (`docs/L3/training/curves.md` §4).  The bundle's
*hoisting* is the job's prose recipe (step 7 of that §6) and not shipped code, so no case can
drive it; and the shipped array itself is stale, so no case compares against it
(`docs/L3/training/evidence.md` §3).
"""

import importlib.util
import json
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "training_join_support" in sys.modules:
    J = sys.modules["training_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "training_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["training_join_support"] = J
    _spec.loader.exec_module(J)

#: The sixteen top-level keys `docs/L3/training/evidence.md` §2 declares.
TOP_LEVEL = (
    "stages", "errors", "rungs", "devices", "run",
    "run_wall_clock_seconds", "run_hands", "pool_versions", "pool_record",
    "r2_pool", "matrix", "rating", "report_families", "report",
    "index_summary", "index_missing",
)

#: `records.md` §12's ten required keys plus this module's own four (`loop.md` §3-§4).
RUN_KEYS = (
    "rung", "curves", "pool", "checkpoints", "seeds", "budget", "device", "params",
    "table", "timings", "variants", "header", "baselines", "axis row",
)


class EvidenceFileJoin(J.JoinCase):
    """TRNJ-9 -- the shipped evidence bundle, read as the artefact it is."""

    def document(self):
        path = os.path.join(J.ROOT, "checkpoints", "evidence", "r1-live.json")
        self.assertTrue(
            os.path.isfile(path),
            "the R1 live run's evidence ships at checkpoints/evidence/r1-live.json "
            "(docs/L1/protocol.md §5, docs/L2/training/evidence.md §1): %r" % (path,),
        )
        with open(path, encoding="utf-8") as handle:
            document = json.load(handle)
        self.assertIsInstance(
            document, dict,
            "the file is one JSON object (docs/L3/training/evidence.md §1)",
        )
        return document

    def paths_in(self, value, found=None):
        """Every string in `value` that ends in `.ckpt`, repeats kept."""
        found = [] if found is None else found
        if isinstance(value, str):
            if value.endswith(".ckpt"):
                found.append(value)
        elif isinstance(value, dict):
            for inner in value.values():
                self.paths_in(inner, found)
        elif isinstance(value, (list, tuple)):
            for inner in value:
                self.paths_in(inner, found)
        return found

    def test_trnj_9_1_the_file_holds_the_sixteen_documented_keys(self):
        """TRNJ-9.1 the bundle is one object of the sixteen top-level keys §2 lists, and none beside them (evidence.md §2 of L3)."""
        document = self.document()
        self.assertEqual(
            set(document),
            set(TOP_LEVEL),
            "the bundle's sixteen keys are the ones docs/L3/training/evidence.md §2 "
            "declares, and a seventeenth is a different format: %r"
            % (sorted(document),),
        )

    def test_trnj_9_2_the_run_block_is_the_run_record_with_the_hoisted_curve_layout(self):
        """TRNJ-9.2 `run` is `records.md` §12's record plus this module's own keys, its curves take the bundle's variant-level layout, and the one spread array a run record repeats per seed is that same array (evidence.md §2, §4 of L3, curves.md §4, loop.md §3-§4).

        The bundle's *structure* is asserted here and its *values* are not: the shipped
        array is stale (`docs/L3/training/evidence.md` §3), so the numbers are checked on a
        run this battery makes, where both layouts are views of one array.
        """
        run = self.document()["run"]
        for key in RUN_KEYS:
            self.assertIn(
                key,
                run,
                "the bundle's run block is the record `training.run` returns, so it "
                "carries %r (docs/L3/training/loop.md §3-§4, records.md §12): %r"
                % (key, sorted(run)),
            )
        curves = run["curves"]
        self.assertTrue(curves, "a run reports one curve block per variant")
        for variant, block in curves.items():
            with self.subTest(variant=variant):
                self.assertEqual(
                    set(block),
                    {"samples", "seeds", "spread"},
                    "the bundle hoists the variant's axis and its one spread and keys "
                    "the per-seed signals under `seeds` (docs/L3/training/evidence.md "
                    "§4): %r" % (sorted(block),),
                )
                seeds = block["seeds"]
                self.assertTrue(
                    seeds,
                    "a variant's block carries its seeds' signals (records.md §12)",
                )
                for seed, entry in seeds.items():
                    self.assertNotIn(
                        "spread",
                        entry,
                        "the spread is a property of the variant and the point, "
                        "stored once per variant here and never per seed "
                        "(docs/L3/training/curves.md §4, FAM-4.8): seed %r" % (seed,),
                    )
                    self.assertIn(
                        "td_error",
                        entry,
                        "one seed's entry is that seed's signal on the axis "
                        "(docs/L3/training/curves.md §3, §5): %r" % (sorted(entry),),
                    )
                self.assertEqual(
                    len(block["spread"]),
                    len(list(block["samples"])),
                    "one spread value per point of the shared axis, so the axis and "
                    "the spread are one length (docs/L3/training/curves.md §4): %r"
                    % (block["spread"],),
                )
        self.assert_hoisted_layout_of_a_live_run()

    def assert_hoisted_layout_of_a_live_run(self):
        """A live two-seed record, reshaped to the bundle's layout, carries one array.

        `docs/L3/training/curves.md` §4: the run record repeats the variant's one
        spread at each seed, and the bundle stores it once — the two layouts are one
        set of numbers, and neither makes the spread a per-seed measurement
        (`docs/L3/training/evidence.md` §4, FAM-4.8).
        """
        record = J.run(
            "R1", seeds=[J.RUN_SEED, J.RUN_SEED_OTHER], budget=J.PAIR_BUDGET
        )
        variant = str(record["variants"][0]["name"])
        entries = [
            J.curve_of(record, variant, seed)
            for seed in (J.RUN_SEED, J.RUN_SEED_OTHER)
        ]
        arrays = [[float(point) for point in entry["spread"]] for entry in entries]
        self.assertEqual(
            arrays[0],
            arrays[1],
            "the run record repeats one array at each of the variant's seeds, and the "
            "bundle's single `spread` key is that same array hoisted "
            "(docs/L3/training/curves.md §4, evidence.md §4): %r against %r"
            % (arrays[0], arrays[1]),
        )
        signals = [
            [float(point) for point in entry["td_error"]] for entry in entries
        ]
        for index, recorded in enumerate(arrays[0]):
            wanted = max(signal[index] for signal in signals) - min(
                signal[index] for signal in signals
            )
            self.assertAlmostEqual(
                recorded,
                wanted,
                places=12,
                msg="the array is the max minus the min of the seeds' signals at "
                "point %d, in either layout (docs/L3/training/curves.md §4): %r "
                "against %r" % (index, recorded, wanted),
            )

    def test_trnj_9_3_every_path_is_relative_and_resolves_inside_the_repository(self):
        """TRNJ-9.3 the three path-bearing blocks spell every path repository-relative, resolve it under the root, and name artefacts the index also names (docs/L2/training/evidence.md §3, checkpoints.md §2, protocol.md §5)."""
        document = self.document()
        run = document["run"]
        blocks = (
            ("run.checkpoints", run["checkpoints"]),
            ("run.header.checkpoints", run["header"]["checkpoints"]),
            ("report.header.checkpoints", document["report"]["header"]["checkpoints"]),
        )
        root = os.path.realpath(J.ROOT)
        from_index = {str(entry["path"]).replace(os.sep, "/") for entry in J.entries()}
        for label, block in blocks:
            paths = self.paths_in(block)
            self.assertTrue(paths, "the block names artefacts: %r" % (label,))
            self.assertEqual(
                len(paths),
                len(set(paths)),
                "no artefact is listed twice in one block, so a reader counting "
                "listings counts artefacts (checkpoints.md §4, FAM-12.6): %r" % (label,),
            )
            for path in paths:
                with self.subTest(block=label, path=path):
                    self.assertFalse(
                        os.path.isabs(path),
                        "the record is portable: a path naming one machine's home "
                        "directory cannot travel with the tree (docs/L2/training/"
                        "evidence.md §3, protocol.md §5): %r" % (path,),
                    )
                    self.assertNotIn(
                        "..",
                        path.split("/"),
                        "a recorded path never climbs out of the repository "
                        "(checkpoints.md §2): %r" % (path,),
                    )
                    resolved = os.path.realpath(J.resolve(path))
                    self.assertTrue(
                        os.path.isfile(resolved),
                        "every path the evidence names is a file the repository "
                        "carries (protocol.md §5, FAM-12.5): %r" % (path,),
                    )
                    self.assertTrue(
                        resolved == root or resolved.startswith(root + os.sep),
                        "every path the evidence names is inside the repository "
                        "(module-map.md §5): %r" % (path,),
                    )
                    self.assertIn(
                        path.replace(os.sep, "/"),
                        from_index,
                        "one artefact has one spelling: a path the run record names "
                        "is the path the index names for the same artefact, or the "
                        "run wrote something that does not ship (checkpoints.md §2, "
                        "§5): %r" % (path,),
                    )

    def test_trnj_9_4_the_header_declares_a_budget_and_a_cell_records_a_count(self):
        """TRNJ-9.4 the header's parameter count is the declared budget and a matrix cell's `params` is a measured count inside that band — the two differ without contradicting (evidence.md §5 of L3, records.md §9, ASM-10)."""
        document = self.document()
        counts = document["run"]["header"]["parameter counts"]
        declared = int(counts["naive-numeric"])
        self.assertEqual(
            declared,
            int(counts["variant-1"]),
            "the header states one declared budget for the variant, under its name "
            "and under the slot label a table reports it by (docs/L2/training/"
            "surface.md §4.1, loop.md §3): %r" % (counts,),
        )
        self.assertEqual(
            int(counts["random"]),
            0,
            "a baseline declares the zero `agents.baselines()` declares (ASM-10, "
            "records.md §9)",
        )
        measured = None
        for record in document["matrix"]["member_records"]:
            if str(record.get("id")) == "variant-1":
                measured = int(record["params"])
        self.assertIsNotNone(
            measured,
            "the matrix records the parameter count it measured for its variant "
            "member, because a cell's `params` is `agents.param_count` and not a "
            "declaration (records.md §9): %r" % (document["matrix"]["member_records"],),
        )
        lower, upper = J.band(declared)
        self.assertGreaterEqual(
            float(measured),
            float(lower),
            "the measured count sits inside the declared ±2 percent band the ladder "
            "matches a pair on, so the header's declaration is the band's centre and "
            "not a claim a cell contradicts (ASM-10, docs/L3/training/evidence.md §5): "
            "%r < %r" % (measured, lower),
        )
        self.assertLessEqual(
            float(measured),
            float(upper),
            "the measured count sits inside the declared ±2 percent band (ASM-10, "
            "docs/L3/training/evidence.md §5): %r > %r" % (measured, upper),
        )

    def test_trnj_9_5_the_report_families_and_the_index_summary_are_the_files_own(self):
        """TRNJ-9.5 `report_families` is the report's own key set and `index_summary`/`index_missing` are `training.checkpoints()` read once, so the evidence and the shipped index cannot drift apart (evidence.md §2, §6 of L3, protocol.md §1, checkpoints.md §4-§5)."""
        document = self.document()
        report = document["report"]
        self.assertEqual(
            list(document["report_families"]),
            sorted(report),
            "the families the report carries are the names the job recorded, sorted "
            "and with none added (records.md §13, protocol.md §1): %r"
            % (document["report_families"],),
        )
        self.assertEqual(
            len(document["report_families"]),
            12,
            "a report is twelve families, the count protocol.md §1 fixes: %r"
            % (document["report_families"],),
        )
        entries = J.entries()
        declared = J.checkpoints()
        summary = {
            "shipped": list(declared["shipped"]),
            "pending": list(declared["pending"]),
            "entries": len(entries),
            "all_exist": all(
                os.path.isfile(J.resolve(entry["path"])) for entry in entries
            ),
        }
        self.assertEqual(
            summary,
            document["index_summary"],
            "the bundle records the index the repository carries today, so a "
            "checkpoint that ships without being counted here is a shipped set the "
            "evidence does not know about (checkpoints.md §4-§5, FAM-12.5): %r"
            % (summary,),
        )
        missing = [
            str(entry["id"])
            for entry in entries
            if not os.path.isfile(J.resolve(entry["path"]))
        ]
        self.assertEqual(
            document["index_missing"],
            missing,
            "`index_missing` is the entries the repository does not carry — empty is "
            "the shipped set being complete (checkpoints.md §5): %r" % (missing,),
        )
        self.assertNotIn(
            "evidence",
            " ".join(str(entry["path"]) for entry in entries),
            "the evidence file is not a checkpoint, and the index never names it "
            "(docs/L2/training/evidence.md §1, checkpoints.md §5)",
        )


if __name__ == "__main__":
    unittest.main()
