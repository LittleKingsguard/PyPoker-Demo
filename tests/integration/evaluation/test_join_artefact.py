"""JOIN-EVL-11 — the shipped artefact is the module's own output.

`docs/L2/evaluation/league.md` §5 and `docs/L3/evaluation/tables.md` §3: what ships
is a data artefact under `tables/` holding the `records.md` §10 matrix record, the
§8 pool record it was measured over and the §11 rating fitted to it, and no entry
point reads it — a notebook reads it with the standard library, and this battery
asserts it is self-consistent *through the module*: `rating` of the file's matrix
reproduces the file's rating, `build_pool` of the membership it names reproduces
its pool id, and the file's own arithmetic agrees with the record it carries
(D-8, D-16, `module-map.md` §5).  The file's 9,000 hands are never replayed.
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
if "evaluation_join_support" in sys.modules:
    J = sys.modules["evaluation_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "evaluation_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["evaluation_join_support"] = J
    _spec.loader.exec_module(J)


class ShippedArtefact(J.JoinCase):
    """`tables/league-full.json`, read with the standard library and judged by the module."""

    def document(self):
        self.assertTrue(
            os.path.exists(J.SHIPPED_PATH),
            "the shipped table must exist under tables/ "
            "(docs/L3/evaluation/tables.md §3, module-map.md §5): %r"
            % (J.SHIPPED_PATH,),
        )
        with open(J.SHIPPED_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_join_evl_11_1_the_file_carries_the_schema_and_the_three_records(self):
        """JOIN-EVL-11.1 the artefact's keys and schema are the design's.

        `docs/L3/evaluation/tables.md` §3: one UTF-8 JSON object whose keys are
        `schema`, `table`, `pool`, `matrix`, `rating`, `provenance` and `cost`; the
        schema string is the format's name and version, `table` repeats the
        matrix's budget, and `pool`, `matrix` and `rating` are the three records
        unchanged (`records.md` §8, §10, §11).
        """
        document = self.document()
        self.assertIsInstance(
            document,
            dict,
            "the artefact is one JSON object (docs/L3/evaluation/tables.md §3)",
        )
        self.assertEqual(
            document.get("schema"),
            J.SHIPPED_SCHEMA,
            "the artefact's schema is the format's name and version "
            "(docs/L3/evaluation/tables.md §3)",
        )
        for key in ("schema", "table", "pool", "matrix", "rating", "provenance",
                    "cost"):
            self.assertIn(
                key,
                document,
                "the artefact carries the %r key (docs/L3/evaluation/tables.md §3)"
                % (key,),
            )
        matrix_record = document["matrix"]
        for key in ("members", "cells", "hands_per_cell", "table_seed", "table"):
            self.assertIn(
                key,
                matrix_record,
                "the file's matrix carries records.md §10's required key %r"
                % (key,),
            )
        for key in ("id", "m", "frozen", "members"):
            self.assertIn(
                key,
                document["pool"],
                "the file's pool carries records.md §8's required key %r" % (key,),
            )
        for key in ("values", "method", "anchor", "bound_applied",
                    "bootstrap_seed", "converged"):
            self.assertIn(
                key,
                document["rating"],
                "the file's rating carries records.md §11's required key %r"
                % (key,),
            )
        self.assertEqual(
            document["table"],
            document["matrix"]["table"],
            "the file's table label repeats the matrix's budget "
            "(docs/L3/evaluation/tables.md §3, records.md §10)",
        )

    def test_join_evl_11_2_rating_of_the_files_matrix_reproduces_the_files_rating(self):
        """JOIN-EVL-11.2 `rating(artefact["matrix"])` gives the artefact's own values.

        `docs/L2/evaluation/surface.md` §11 and `docs/L3/evaluation/tables.md` §3–§4:
        the file holds the §11 rating exactly as `rating` returned it, so re-fitting
        the file's matrix must reproduce each member's value and both interval
        bounds, the method, the anchor, the bound flag, the bootstrap seed and the
        convergence — a rating is a function of the table it was fitted over
        (D-8, ASM-17).
        """
        document = self.document()
        fitted = J.rating(document["matrix"])
        shipped = document["rating"]
        self.assertEqual(
            str(fitted["method"]),
            str(shipped["method"]),
            "the re-fitted rating's method is the file's "
            "(records.md §11, docs/L2/evaluation/rating.md §5)",
        )
        self.assertEqual(
            str(fitted["anchor"]),
            str(shipped["anchor"]),
            "the re-fitted rating's anchor is the file's (records.md §11)",
        )
        self.assertEqual(
            bool(fitted["bound_applied"]),
            bool(shipped["bound_applied"]),
            "the re-fitted rating's bound flag is the file's (records.md §11, "
            "ASM-17)",
        )
        self.assertEqual(
            int(fitted["bootstrap_seed"]),
            int(shipped["bootstrap_seed"]),
            "the re-fitted rating's bootstrap seed is the file's "
            "(docs/L3/evaluation/rating.md §4)",
        )
        self.assertEqual(
            bool(fitted["converged"]),
            bool(shipped["converged"]),
            "the re-fitted rating's convergence is the file's (records.md §11)",
        )
        mine = J.rating_values(fitted)
        theirs = J.rating_values(shipped)
        self.assertEqual(
            list(mine),
            list(theirs),
            "the two ratings name one membership in one order "
            "(records.md §11, docs/L3/evaluation/rating.md §5)",
        )
        for member_id in theirs:
            with self.subTest(member=member_id):
                self.assertAlmostEqual(
                    J.entry_value(mine[member_id]),
                    J.entry_value(theirs[member_id]),
                    places=12,
                    msg="rating(artefact['matrix']) must reproduce the artefact's "
                        "value for %r (docs/L3/evaluation/tables.md §3, §4)"
                        % (member_id,),
                )
                lower, upper = J.entry_interval(theirs[member_id])
                mine_lower, mine_upper = J.entry_interval(mine[member_id])
                self.assertAlmostEqual(
                    mine_lower,
                    lower,
                    places=12,
                    msg="the lower interval bound must be reproduced for %r "
                        "(records.md §11, docs/L3/evaluation/rating.md §4)"
                        % (member_id,),
                )
                self.assertAlmostEqual(
                    mine_upper,
                    upper,
                    places=12,
                    msg="the upper interval bound must be reproduced for %r "
                        "(records.md §11, docs/L3/evaluation/rating.md §4)"
                        % (member_id,),
                )
                self.assertEqual(
                    J.entry_hands(mine[member_id]),
                    J.entry_hands(theirs[member_id]),
                    "the hands behind a value are reproduced for %r "
                    "(records.md §11, FAM-9.5)" % (member_id,),
                )

    def test_join_evl_11_3_the_membership_it_names_reproduces_its_pool_id(self):
        """JOIN-EVL-11.3 `build_pool` of the file's membership gives the file's pool id.

        `docs/L3/evaluation/tables.md` §3 and `docs/L2/evaluation/pool.md` §4: the
        file's pool is `records.md` §8's pool record, and the pool's id is a
        function of the ordered member ids and of nothing else — so rebuilding the
        pool from the declaration the record names reproduces the id the file
        carries, and the file cannot name a membership it does not hold.
        """
        document = self.document()
        shipped = document["pool"]
        names = [str(name) for name in J.protocol()["baselines"]]
        declared = [member for member in shipped["members"]
                    if str(member["id"]) not in names]
        rebuilt = J.pool_members(
            J.build_pool(
                {"members": declared, "m": shipped["m"], "frozen": shipped["frozen"]}
            )
        )
        self.assertEqual(
            str(rebuilt["id"]),
            str(shipped["id"]),
            "the id is a function of the ordered member ids, so the file's "
            "membership reproduces its pool id (docs/L2/evaluation/pool.md §4, "
            "docs/L3/evaluation/tables.md §3)",
        )
        self.assertEqual(
            J.names_of(rebuilt),
            J.names_of(shipped),
            "the rebuilt pool reads back the file's ordered membership "
            "(docs/L2/evaluation/surface.md §6, records.md §8)",
        )
        for name in names:
            self.assertEqual(
                int(J.member_record(rebuilt, name)["params"]),
                0,
                "the file's baselines are the declared zeros the pool pins "
                "(docs/L2/evaluation/pool.md §2 step 5, ASM-10)",
            )

    def test_join_evl_11_4_the_files_arithmetic_agrees_with_the_record_it_carries(self):
        """JOIN-EVL-11.4 hands_per_cell × cell_count is the hands it records.

        `docs/L3/evaluation/tables.md` §1 and §5: a table plays
        `cell_count(K) × hands_per_cell` hands, so the file's own cells, its
        recorded provenance and its cost block must be one number — 1,500 × 6 =
        9,000 for the shipped K = 4 `full` table — and the budget and table seed it
        records are the league's (`docs/L2/evaluation/league.md` §5, ASM-14).
        """
        document = self.document()
        matrix_record = document["matrix"]
        provenance = document["provenance"]
        cost = document["cost"]
        hands = int(matrix_record["hands_per_cell"]) * J.matrix_cell_count(
            matrix_record
        )
        self.assertEqual(
            int(provenance["hands_per_cell"]) * int(provenance["cell_count"]),
            hands,
            "the provenance's cell size times its cell count is the hands the "
            "table played (docs/L3/evaluation/tables.md §1, §5)",
        )
        self.assertEqual(
            int(provenance["hands_played"]),
            hands,
            "the provenance records the hands the table played "
            "(docs/L3/evaluation/tables.md §5)",
        )
        self.assertEqual(
            int(cost["hands"]),
            hands,
            "the cost block records the hands it measured, not a second count "
            "(docs/L3/evaluation/tables.md §5)",
        )
        self.assertEqual(
            int(provenance["cell_count"]),
            J.matrix_cell_count(matrix_record),
            "the provenance's cell count is the matrix's cells "
            "(docs/L3/evaluation/tables.md §3)",
        )
        self.assertEqual(
            str(provenance["budget"]),
            str(matrix_record["table"]),
            "the provenance's budget is the matrix's label "
            "(docs/L3/evaluation/tables.md §5, records.md §10)",
        )
        self.assertEqual(
            int(matrix_record["table_seed"]),
            int(J.league()["table_seed"]),
            "the file's table seed is the league's one integer "
            "(docs/L2/evaluation/declarations.md §6)",
        )
        self.assertEqual(
            int(provenance["table_seed"]),
            int(matrix_record["table_seed"]),
            "the provenance repeats the matrix's table seed "
            "(docs/L3/evaluation/tables.md §5)",
        )
        self.assertEqual(
            int(matrix_record["hands_per_cell"]),
            int(J.league()["tables"]["full"]["hands_per_cell"]),
            "the shipped table is the full budget's cell size "
            "(docs/L2/evaluation/league.md §5, ASM-14)",
        )

    def test_join_evl_11_5_the_shipped_rating_reads_the_baselines_as_the_anchor(self):
        """JOIN-EVL-11.5 the shipped rating is anchored on the three baselines.

        `docs/L2/evaluation/league.md` §4 and `docs/L1/league.md` §5: the three
        baselines are in the table at the table's hand count and the fit fixes their
        mean value at 0, so every value in the file reads as a distance from the
        only fixed standard the table has (ASM-17, `records.md` §11).  A shipped
        rating whose baselines were not anchored would not be comparable with any
        other table.
        """
        document = self.document()
        matrix_record = document["matrix"]
        fitted = document["rating"]
        names = [str(name) for name in J.protocol()["baselines"]]
        for name in names:
            self.assertIn(
                name,
                J.matrix_members(matrix_record),
                "the shipped table carries the baseline %r as a row and a column "
                "(docs/L2/evaluation/league.md §3, D-16)" % (name,),
            )
            for cell in matrix_record["cells"]:
                if name in J.cell_members(cell):
                    self.assertEqual(
                        int(cell["hands"]),
                        int(matrix_record["hands_per_cell"]),
                        "the baseline %r's cells are played at the table's one "
                        "hand count (docs/L1/protocol.md §3, ASM-14)" % (name,),
                    )
        mean = sum(
            J.entry_value(J.rating_values(fitted)[name]) for name in names
        ) / len(names)
        self.assertAlmostEqual(
            mean,
            0.0,
            places=9,
            msg="the shipped rating's three baselines have mean value 0 "
                "(docs/L1/league.md §5, ASM-17), got %r" % (mean,),
        )
        behind = int(matrix_record["hands_per_cell"]) * (
            len(J.matrix_members(matrix_record)) - 1
        )
        for member_id, entry in J.rating_values(fitted).items():
            self.assertEqual(
                J.entry_hands(entry),
                behind,
                "the shipped rating gives %r the hands_per_cell × (K−1) hands "
                "behind its value (records.md §11, FAM-9.5)" % (member_id,),
            )

    def test_join_evl_11_6_the_membership_says_which_player_each_row_is(self):
        """JOIN-EVL-11.6 the artefact's membership, its status and its records name one table.

        `docs/L2/evaluation/league.md` §5 and `docs/L3/evaluation/tables.md` §2, §5:
        `provenance.member_status` is aligned one-for-one with the matrix's `members`;
        a pinned baseline's status is `baseline` and its capacity the `0` the pool
        declares; and a member's status comes from its own recipe, with the seed it was
        built at.  The matrix's `unlabelled` list is the complementary fact and not a
        training claim: it says only that `matrix` was handed a policy already built
        (`docs/L3/evaluation/matrix.md` §5, ASM-18) — so an **untrained** variant's
        capacity is the producer's measurement and the matrix reports the `0` of an
        unmeasured one, and the same member id in a live table is a trained final model.
        """
        document = self.document()
        matrix_record = document["matrix"]
        provenance = document["provenance"]
        members = J.matrix_members(matrix_record)
        status = list(provenance["member_status"])
        self.assertEqual(
            [str(row["id"]) for row in status],
            members,
            "the membership's status is one row per matrix member, in the matrix's "
            "order, so no member of the table is left unnamed "
            "(docs/L3/evaluation/tables.md §2, §5)",
        )
        by_id = {str(row["id"]): row for row in status}
        recipes = {str(recipe["id"]): recipe for recipe in provenance["variants"]}
        names = [str(name) for name in J.protocol()["baselines"]]
        for name in names:
            self.assertEqual(
                str(by_id[name]["status"]),
                "baseline",
                "a pinned baseline's status is `baseline` "
                "(docs/L3/evaluation/tables.md §5)",
            )
            self.assertEqual(
                int(J.member_record(document["pool"], name)["params"]),
                0,
                "a baseline's capacity is the zero the catalogue declares "
                "(ASM-10, docs/L2/evaluation/pool.md §2)",
            )
        unlabelled = [str(name) for name in matrix_record.get("unlabelled", ())]
        matrix_records = {
            str(record["id"]): record
            for record in matrix_record.get("member_records", ())
        }
        for name in [member for member in members if member not in names]:
            with self.subTest(member=name):
                row = by_id[name]
                recipe = recipes.get(name)
                self.assertIsNotNone(
                    recipe,
                    "a member outside the pool is one of the rung's variants and carries "
                    "its recipe, so its status has a source "
                    "(docs/L3/evaluation/tables.md §2, §5)",
                )
                self.assertEqual(
                    str(row["status"]),
                    str(recipe["status"]),
                    "a member's status is its own recipe's status and not a value the "
                    "provenance block invented (docs/L3/evaluation/tables.md §5)",
                )
                self.assertEqual(
                    int(row["seed"]),
                    int(recipe["seed"]),
                    "the row names the seed the variant was built at "
                    "(docs/L3/evaluation/tables.md §2, §5)",
                )
                if str(row["status"]) == "untrained":
                    self.assertIn(
                        name,
                        unlabelled,
                        "an untrained variant is a policy handed to `matrix` already "
                        "built, so the matrix records the `0` of an unmeasured capacity "
                        "and its id in `unlabelled` while the producer's measurement sits "
                        "in the recipe (docs/L3/evaluation/matrix.md §5, ASM-10)",
                    )
                    self.assertEqual(
                        int(matrix_records[name]["params"]),
                        0,
                        "the matrix's capacity for an unlabelled variant is the "
                        "unmeasured `0`, never the recipe's measurement "
                        "(docs/L3/evaluation/matrix.md §5)",
                    )


if __name__ == "__main__":
    unittest.main()
