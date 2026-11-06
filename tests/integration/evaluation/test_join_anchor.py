"""JOIN-EVL-7 — the baselines sit inside the table, and the fit anchors on them.

D-16's table carries three cells no model influences: the three pinned baselines
are rows and columns at the same hand count as every league cell, and the
Bradley-Terry fit is anchored so their mean value is zero (`docs/L1/league.md`
§4–§5, `docs/L1/protocol.md` §3, ASM-17).  This family asserts both halves against
the battery's one real `live` table and the rating fitted to it: the baselines'
cells are played like any other, and the rating reads them as the fixed standard
(`docs/L2/evaluation/league.md` §4, `docs/L2/evaluation/rating.md` §2).
"""

import importlib.util
import itertools
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


class BaselinesInsideTheTable(J.JoinCase):
    """The three baseline rows and columns, and the fit that anchors on them."""

    def test_join_evl_7_1_each_baseline_is_a_row_and_a_column(self):
        """JOIN-EVL-7.1 a baseline plays every other member at the table's hand count.

        `docs/L2/evaluation/league.md` §3 and `docs/L1/protocol.md` §3: the three
        baselines are rows and columns at the same hand count as every league cell,
        so each plays K−1 cells, and every one of them is played at the table's one
        count — no member's row is measured more precisely than another's (D-16,
        ASM-14).
        """
        table = J.shared_matrix()
        members = J.matrix_members(table)
        names = [str(name) for name in J.protocol()["baselines"]]
        for name in names:
            cells = [cell for cell in table["cells"]
                     if name in J.cell_members(cell)]
            self.assertEqual(
                len(cells),
                len(members) - 1,
                "the baseline %r is a row and a column of the table, one cell "
                "against each other member (docs/L1/league.md §4, D-16)"
                % (name,),
            )
            for cell in cells:
                self.assertEqual(
                    int(cell["hands"]),
                    int(table["hands_per_cell"]),
                    "the baseline cell %r is played at the table's one hand "
                    "count (docs/L2/evaluation/league.md §3, ASM-14)"
                    % (J.cell_members(cell),),
                )
                direction = J.direction_for(cell, name)
                wins, ties, losses = J.counts_of(direction)
                self.assertEqual(
                    wins + ties + losses,
                    int(cell["hands"]),
                    "a baseline's direction accounts for every hand of its cell "
                    "(records.md §9)",
                )

    def test_join_evl_7_2_the_three_mutual_baseline_cells_are_in_the_table(self):
        """JOIN-EVL-7.2 the three baseline-vs-baseline cells exist and report both seats.

        `docs/L2/evaluation/league.md` §3: the three mutual cells are in the table,
        so the matrix carries cells no model influences; each reports both
        directions and a seat split summing to the hands played
        (`docs/L3/evaluation/scheduler.md` §4, `records.md` §9).
        """
        table = J.shared_matrix()
        names = [str(name) for name in J.protocol()["baselines"]]
        pairs = list(itertools.combinations(names, 2))
        self.assertEqual(len(pairs), 3, "three baselines have three mutual cells")
        for member_a, member_b in pairs:
            cell = J.cell_by_pair(table, member_a, member_b)
            hands = int(cell["hands"])
            left = J.direction_for(cell, member_a)
            right = J.direction_for(cell, member_b)
            left_counts = J.counts_of(left)
            right_counts = J.counts_of(right)
            self.assertEqual(
                right_counts,
                (left_counts[2], left_counts[1], left_counts[0]),
                "the two directions are the same hands seen from each seat "
                "(docs/L3/evaluation/scheduler.md §4, docs/L1/league.md §2)",
            )
            for direction in (left, right):
                self.assertEqual(
                    sum(J.seat_split_of(direction)),
                    hands,
                    "each direction's seat split covers the hands it played "
                    "(docs/L1/league.md §3, records.md §9)",
                )
            self.assertAlmostEqual(
                J.mean_delta_of(left) + J.mean_delta_of(right),
                0.0,
                places=12,
                msg="the mutual baseline cell is zero-sum, like every other cell "
                    "(ASM-12)",
            )

    def test_join_evl_7_3_the_fit_anchors_the_baselines_mean_at_zero(self):
        """JOIN-EVL-7.3 the three baselines' mean fitted value is 0.

        `docs/L2/evaluation/league.md` §4 and `docs/L2/evaluation/rating.md` §2:
        the fit is anchored by the three baselines, whose mean value is fixed at 0,
        so every value reads as a distance from the only fixed standard in the
        table (`docs/L1/league.md` §5, ASM-17).  The rating is the one fitted over
        this same real matrix, and its `anchor` names that rule so a reader is not
        left to infer it (`records.md` §11).
        """
        table = J.shared_matrix()
        fitted = J.shared_rating()
        names = [str(name) for name in J.protocol()["baselines"]]
        values = J.rating_values(fitted)
        for name in names:
            self.assertIn(
                name,
                values,
                "the rating names the baseline %r the anchor is computed from "
                "(records.md §11, docs/L2/evaluation/rating.md §2)" % (name,),
            )
        mean = sum(J.entry_value(values[name]) for name in names) / len(names)
        self.assertAlmostEqual(
            mean,
            0.0,
            places=9,
            msg="the three baselines' mean value is fixed at 0 by the fit's "
                "anchor (docs/L2/evaluation/league.md §4, ASM-17), got %r"
                % (mean,),
        )
        anchor = str(fitted["anchor"])
        for needle in ("baseline", "mean", "0"):
            self.assertIn(
                needle,
                anchor.lower(),
                "the rating carries an `anchor` naming the baselines' mean fixed "
                "at zero (records.md §11, docs/L3/evaluation/declarations.md §2.2): "
                "%r" % (anchor,),
            )

    def test_join_evl_7_4_the_rating_reads_the_table_it_was_fitted_over(self):
        """JOIN-EVL-7.4 the bootstrap seed is the table's, and the hands are the table's.

        `docs/L2/evaluation/rating.md` §4 and `docs/L2/evaluation/surface.md` §11:
        the bootstrap is seeded from the matrix's own table seed and records that
        seed, the method is `Bradley-Terry`, the anchor is the league's declared
        one, and each member's value carries `hands_per_cell × (K−1)` hands — so
        the rating and the matrix travel together (`docs/L1/league.md` §4, §5).
        """
        table = J.shared_matrix()
        fitted = J.shared_rating()
        self.assertEqual(
            str(fitted["method"]),
            str(J.protocol()["rating"]["method"]),
            "the fit's method is the one protocol() declares "
            "(docs/L3/evaluation/declarations.md §2.2, records.md §11)",
        )
        self.assertEqual(
            str(fitted["anchor"]),
            str(J.protocol()["rating"]["anchor"]),
            "the fit's anchor is the league's declared anchor, one value on both "
            "sides (docs/L3/evaluation/declarations.md §2.2)",
        )
        self.assertEqual(
            int(fitted["bootstrap_seed"]),
            J.bootstrap_seed(int(table["table_seed"])),
            "the bootstrap seed is derived from the matrix's own table seed and "
            "recorded, so the interval can be re-run "
            "(docs/L3/evaluation/rating.md §4, ASM-17)",
        )
        behind = int(table["hands_per_cell"]) * (len(J.matrix_members(table)) - 1)
        for member_id, entry in J.rating_values(fitted).items():
            self.assertEqual(
                J.entry_hands(entry),
                behind,
                "the %r value carries the hands_per_cell × (K−1) hands behind it "
                "(records.md §11, docs/L3/evaluation/rating.md §5)"
                % (member_id,),
            )


if __name__ == "__main__":
    unittest.main()
