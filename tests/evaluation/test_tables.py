"""EVL-6 — the two table budgets and the shipped artefact.

Drives `docs/L3/evaluation/tables.md` §1-§7, `docs/L3/evaluation/declarations.md`
§4.1 and `docs/L2/evaluation/league.md` §5-§6: the two budgets differ in
`hands_per_cell` and nothing else, a table plays `cell_count(K) x hands_per_cell`
hands, `league()` keeps carrying ASM-15's `0.04` bound and never a measurement, and
no entry point reads (or writes) the shipped artefact (`tables.md` §4, `guardrails.md`
G19).

EVL-6.3 is the battery's **one** case about `tables/league-full.json`: it exists, it
parses, it carries `tables.md` §3's seven keys in its order and §5's provenance and
cost blocks, and its `hands_played` is `cell_count x hands_per_cell` for the
membership it names (the K = 4 baselines-plus-variant table is the only membership
this repository can build today, `tables.md` §2 -- an artefact regenerated over a
frozen pool's window is read by the same arithmetic, `tables.md` §6).
"""

import json
import os
import unittest

from _evaluation_support import (
    BASELINES,
    BUDGETS,
    REPO_ROOT,
    EvaluationCase,
    declared_internal,
    hand_matrix,
    balanced,
    matrix_cells,
    matrix_member_ids,
    no_file_reads,
    report_inputs,
)

#: The artefact's declared schema name (`tables.md` §3).
SCHEMA = "pypoker-evaluation-league-table/1"

#: The artefact's seven top-level keys, in `tables.md` §3's order.
DOCUMENT_KEYS = ("schema", "table", "pool", "matrix", "rating", "provenance", "cost")


class TablesTest(EvaluationCase):
    def test_evl_6_1_the_two_budgets_are_arithmetic_on_k(self):
        """EVL-6.1 each budget row's `hands_per_cell` and `hands_played` are `declarations.md` §4.1's numbers, and every `hands_played` is `cell_count(K) x hands_per_cell` (`tables.md` §1, `league.md` §5-§6, FAM-10.1)."""
        package = self.evaluation()
        league = package.league()
        expected = {
            "live": {4: 720, 9: 4320, 10: 5400},
            "full": {4: 9000, 9: 54000, 10: 67500},
        }
        self.assertEqual(
            tuple(league["tables"]),
            BUDGETS,
            "the league declares both budgets, `live` then `full` "
            "(declarations.md §4.1, records.md §10): %r" % (tuple(league["tables"]),),
        )
        for budget in BUDGETS:
            row = league["tables"][budget]
            with self.subTest(budget=budget):
                hands_per_cell = int(row["hands_per_cell"])
                self.assertEqual(
                    hands_per_cell,
                    120 if budget == "live" else 1500,
                    "a live cell is 120 hands and a full cell 1,500 "
                    "(league.md §6, ASM-14): %r" % (hands_per_cell,),
                )
                for size, hands in expected[budget].items():
                    with self.subTest(budget=budget, k=size):
                        self.assertEqual(
                            int(row["hands_played"][size]),
                            hands,
                            "a K = %d %s table plays %d hands (tables.md §1, ASM-14): %r"
                            % (size, budget, hands, row["hands_played"].get(size)),
                        )
                        self.assertEqual(
                            int(row["hands_played"][size]),
                            league["cell_count"](size) * hands_per_cell,
                            "the hands a table plays are cell_count(K) x hands_per_cell, "
                            "so the budget is arithmetic on K and not a wall clock "
                            "(tables.md §1, ASM-15): %r"
                            % (row["hands_played"][size],),
                        )

    def test_evl_6_2_the_live_table_s_hands_played_are_its_cells_times_its_cell_size(self):
        """EVL-6.2 the shared `k4` live table's hand count is `len(cells) x hands_per_cell` and equals the league's declared `hands_played` for its K, so a talk sizes its table before it plays one (`tables.md` §1, `matrix.md` §6, FAM-10.2)."""
        package = self.evaluation()
        matrix = self.shared_matrix("k4")
        members = matrix_member_ids(matrix)
        cells = matrix_cells(matrix)
        hands_per_cell = int(matrix["hands_per_cell"])
        played = len(cells) * hands_per_cell
        self.assertEqual(
            len(cells),
            package.league()["cell_count"](len(members)),
            "a cell is played for every unordered pair of the membership, so the cell "
            "count follows from K (matrix.md §2, declarations.md §5, FAM-10.2): %r"
            % (len(cells),),
        )
        self.assertEqual(
            played,
            int(package.league()["tables"][matrix["table"]]["hands_played"][len(members)]),
            "a table of K = %d members at %d hands per cell plays %d hands, which is the "
            "league's declared hands_played for that K (tables.md §1, FAM-10.2): %r"
            % (len(members), hands_per_cell, played, played),
        )

    def test_evl_6_3_the_shipped_artefact_exists_and_carries_the_declared_schema(self):
        """EVL-6.3 `tables/league-full.json` exists at the module's `SHIPPED_PATH`, parses, carries `tables.md` §3's seven keys in order with its schema name, its pool, matrix and rating records, §5's provenance and measured cost, and `hands_played = cell_count x hands_per_cell` for the membership it names (`tables.md` §2-§5, G19)."""
        package = self.evaluation()
        league = package.league()
        shipped = declared_internal("tables", "SHIPPED_PATH")
        self.assertEqual(
            str(shipped),
            os.path.join("tables", "league-full.json"),
            "the artefact's path has one home, the module constant SHIPPED_PATH = "
            "'tables/league-full.json' (tables.md §3-§4, module-map.md §5): %r"
            % (shipped,),
        )
        path = os.path.join(REPO_ROOT, str(shipped))
        self.assertTrue(
            os.path.isfile(path),
            "the full table ships as one committed data artefact under tables/, and "
            "nothing loads it (tables.md §3-§4, §7, D-8, G19): %r is absent"
            % (path,),
        )
        with open(path, "r", encoding="utf-8") as handle:
            document = json.load(handle)
        self.assertIsInstance(
            document, dict, "the artefact is one JSON object (tables.md §3): %r" % (type(document),)
        )
        self.assertEqual(
            tuple(document),
            DOCUMENT_KEYS,
            "the artefact's keys are tables.md §3's seven, in its order (schema, table, "
            "pool, matrix, rating, provenance, cost): %r" % (tuple(document),),
        )
        self.assertEqual(
            document["schema"],
            SCHEMA,
            "the artefact names its format and version, so a reader can refuse a "
            "different one (tables.md §3): %r" % (document["schema"],),
        )
        self.assertEqual(
            document["table"],
            "full",
            "the artefact records the budget it was measured at (tables.md §3, "
            "records.md §10): %r" % (document["table"],),
        )
        pool = document["pool"]
        for key in ("id", "m", "frozen", "members"):
            with self.subTest(pool_key=key):
                self.assertIn(
                    key,
                    pool,
                    "the artefact carries records.md §8's pool record the table was "
                    "measured over (tables.md §3): %r" % (pool,),
                )
        matrix = document["matrix"]
        for key in ("members", "cells", "hands_per_cell", "table_seed", "table"):
            with self.subTest(matrix_key=key):
                self.assertIn(
                    key,
                    matrix,
                    "the artefact carries records.md §10's matrix record exactly as "
                    "matrix returned it (tables.md §3): %r" % (tuple(matrix),),
                )
        rating = document["rating"]
        for key in ("values", "method", "anchor", "bound_applied", "bootstrap_seed", "converged"):
            with self.subTest(rating_key=key):
                self.assertIn(
                    key,
                    rating,
                    "the artefact carries records.md §11's rating record exactly as "
                    "rating returned it (tables.md §3): %r" % (tuple(rating),),
                )
        self.assertEqual(
            int(matrix["table_seed"]),
            int(league["table_seed"]),
            "the artefact records the league's one table seed beside its membership "
            "(tables.md §3, §5, declarations.md §6): %r" % (matrix["table_seed"],),
        )
        provenance = document["provenance"]
        self.assertEqual(
            provenance.get("module"),
            "evaluation",
            "the provenance names what produced the file (tables.md §5): %r" % (provenance,),
        )
        self.assertEqual(
            tuple(provenance.get("entry_points", ())),
            ("build_pool", "matrix", "rating"),
            "the provenance names the three entry points that produced it "
            "(tables.md §4-§5): %r" % (provenance.get("entry_points"),),
        )
        self.assertEqual(
            provenance.get("schema"),
            SCHEMA,
            "the provenance repeats the document's schema name (tables.md §5): %r"
            % (provenance.get("schema"),),
        )
        self.assertEqual(
            provenance.get("budget"),
            "full",
            "the artefact is the full table (tables.md §2-§3): %r" % (provenance.get("budget"),),
        )
        self.assertEqual(
            int(provenance.get("hands_per_cell", -1)),
            int(matrix["hands_per_cell"]),
            "provenance records the one hand count of the table (tables.md §5): %r"
            % (provenance.get("hands_per_cell"),),
        )
        cells = len(matrix_cells(matrix))
        members = matrix_member_ids(matrix)
        self.assertEqual(
            int(provenance.get("cell_count", -1)),
            cells,
            "provenance records the cells the run played (tables.md §5): %r"
            % (provenance.get("cell_count"),),
        )
        self.assertEqual(
            cells,
            len(members) * (len(members) - 1) // 2,
            "the artefact's matrix is a table: K(K-1)/2 cells for its K members "
            "(tables.md §1, matrix.md §2): %r" % (cells,),
        )
        hands_played = int(provenance.get("hands_played", -1))
        self.assertEqual(
            hands_played,
            cells * int(matrix["hands_per_cell"]),
            "the artefact's hands_played is the cell count times the cell size for the "
            "membership it names (tables.md §5, FAM-10.2): %r for %d cells at %d hands"
            % (hands_played, cells, int(matrix["hands_per_cell"])),
        )
        self.assertEqual(
            tuple(provenance.get("members", ())),
            members,
            "provenance names the membership the table measured, in the matrix's order "
            "(tables.md §5): %r vs %r" % (provenance.get("members"), members),
        )
        self.assertIn(
            provenance.get("membership_kind"),
            ("baselines+variant", "pool+variant"),
            "provenance says which membership kind the file names (tables.md §2, §5-§6): "
            "%r" % (provenance.get("membership_kind"),),
        )
        variants = list(provenance.get("variants", ()))
        outside = [name for name in members if name not in BASELINES]
        self.assertEqual(
            len(variants),
            len(outside),
            "the provenance's variants are the members outside the pool, and the file "
            "adds no member (tables.md §5-§6): %r vs %r" % (variants, outside),
        )
        for variant in variants:
            with self.subTest(variant=variant.get("id")):
                for key in ("id", "backend", "encoding", "architecture", "seed", "params"):
                    self.assertIn(
                        key,
                        variant,
                        "a variant's provenance is the recipe a third party needs to "
                        "rebuild it (tables.md §5): %r" % (variant,),
                    )
                self.assertEqual(
                    int(variant["seed"]),
                    int(declared_internal("tables", "VARIANT_SEED")),
                    "the variant was built at the module's own VARIANT_SEED and never at "
                    "a table-derived seed (tables.md §2, §5, matrix.md §4): %r"
                    % (variant["seed"],),
                )
        self.assertEqual(
            int(declared_internal("tables", "VARIANT_SEED")),
            31415,
            "VARIANT_SEED is the module's own constant, 31415 (tables.md §2, §5): %r"
            % (declared_internal("tables", "VARIANT_SEED"),),
        )
        cost = document["cost"]
        for key in (
            "hands",
            "seconds_per_hand",
            "hands_per_second",
            "wall_clock_seconds",
            "device",
            "per_hand_ceiling_seconds",
            "measured",
        ):
            with self.subTest(cost_key=key):
                self.assertIn(
                    key,
                    cost,
                    "the cost block records the measured cost of the run alongside "
                    "ASM-15's bound (tables.md §5): %r" % (cost,),
                )
        self.assertEqual(
            cost.get("device"),
            "cpu",
            "the artefact was measured on the CPU the sandbox runs (tables.md §5, "
            "strata/platform.md, D-8): %r" % (cost.get("device"),),
        )
        self.assertTrue(
            bool(cost.get("measured")),
            "`measured: true` says these numbers were observed (tables.md §5): %r"
            % (cost.get("measured"),),
        )
        self.assertEqual(
            int(cost.get("hands", -1)),
            hands_played,
            "the cost block reports the hands the run played (tables.md §5): %r"
            % (cost.get("hands"),),
        )
        self.assertGreater(
            float(cost.get("seconds_per_hand", 0.0)),
            0.0,
            "the cost block reports a measured seconds per hand (tables.md §5, "
            "FAM-10.4): %r" % (cost.get("seconds_per_hand"),),
        )
        self.assertAlmostEqual(
            float(cost.get("per_hand_ceiling_seconds", 0.0)),
            0.04,
            msg="the cost block carries ASM-15's bound beside the measurement, so the two "
            "are never confused (tables.md §5, declarations.md §4.1): %r"
            % (cost.get("per_hand_ceiling_seconds"),),
        )

    def test_evl_6_4_league_carries_the_bound_and_never_a_measurement(self):
        """EVL-6.4 `league()` keeps carrying ASM-15's `0.04` per-hand bound with no measured seconds, hands, wall clock or device in it -- a measured figure lives in a run record's `timings` and in the artefact's cost block (`declarations.md` §4.1, `tables.md` §5, G19)."""
        package = self.evaluation()
        league = package.league()
        for budget in BUDGETS:
            row = league["tables"][budget]
            with self.subTest(budget=budget):
                self.assertEqual(
                    set(row),
                    {"hands_per_cell", "hands_played", "produced_by", "per_hand_ceiling_seconds"},
                    "a budget row carries four keys and no measured figure "
                    "(declarations.md §4.1, tables.md §5): %r" % (row,),
                )
                self.assertAlmostEqual(
                    float(row["per_hand_ceiling_seconds"]),
                    0.04,
                    msg="the per-hand figure the league carries is ASM-15's bound of "
                    "0.04 seconds, never a measurement (declarations.md §4.1, "
                    "tables.md §5, G19): %r" % (row["per_hand_ceiling_seconds"],),
                )
        flat = json.dumps(league, default=str).lower()
        for forbidden in ("seconds_per_hand", "wall_clock", "measured"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(
                    forbidden,
                    flat,
                    "no entry point returns a measured cost, and league() carries the "
                    "bound and never a measurement (tables.md §5, declarations.md §4.1, "
                    "G19): %r appears in the declaration" % (forbidden,),
                )

    def test_evl_6_5_no_entry_point_reads_the_shipped_artefact(self):
        """EVL-6.5 `league()`, `protocol()`, `pool_members`, `rating` and `report` all work with every file open refused, so nothing loads the artefact and `matrix` never consults it (`tables.md` §4, §7, `guardrails.md` G19)."""
        package = self.evaluation()
        rung, record, matrix, rating = report_inputs(hand_matrix(balanced))
        before = self.stream_state()
        with no_file_reads("the league's declarations and records"):
            league = package.league()
            protocol = package.protocol()
            pool = package.build_pool({"members": [], "m": 5, "frozen": True})
            members = package.pool_members(pool)
            fitted = package.rating(matrix)
            report = package.report(rung, record, matrix, rating)
        self.assert_stream_unchanged(before, "the non-playing entry points")
        for label, value in (
            ("league()", league),
            ("protocol()", protocol),
            ("pool_members()", members),
            ("rating()", fitted),
            ("report()", report),
        ):
            with self.subTest(record=label):
                self.assertTrue(
                    bool(value),
                    "%s is assembled from records alone and consults no file -- the "
                    "shipped table is evidence and never an interface (tables.md §4, §7, "
                    "G19): %r" % (label, value),
                )


if __name__ == "__main__":
    unittest.main()
