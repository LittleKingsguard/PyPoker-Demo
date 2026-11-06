"""JOIN-EVL-6 — matrix ⇄ pool: one membership, K(K−1)/2 cells, one hand count.

`docs/L2/evaluation/league.md` §3 and `docs/L2/evaluation/matrix.md` §1–§6: a
table's membership is the frozen pool's members in `pool_members`'s order and
then `variant-1` (and `variant-2`) in argument order; the cells are exactly
K(K−1)/2 unordered pairs, one per pair and no repeat; every cell is played at
the table's one hand count, the baseline cells included; and each cell's seed is
derived from the league's one table seed and the pair's positions
(`docs/L3/evaluation/matrix.md` §2–§3).  This family asserts those facts against
the battery's one real `live` table.
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


class MatrixOverPool(J.JoinCase):
    """The shared table read against the pool it was played over."""

    def test_join_evl_6_1_membership_is_the_pools_order_plus_the_variant(self):
        """JOIN-EVL-6.1 the table's ordered membership is the pool read-back plus `variant-1`.

        `docs/L2/evaluation/matrix.md` §1 and `docs/L2/evaluation/surface.md` §10:
        the pool's order is `records.md` §8's — the three baselines first, then the
        window oldest to newest — and a variant is named `variant-1` by its
        position in the argument list whatever it carries (`docs/L2/evaluation/
        league.md` §3, `docs/L1/league.md` §4).
        """
        table = J.shared_matrix()
        readback = J.shared_pool_record()
        self.assertTrue(
            bool(readback["frozen"]),
            "the pool the table was played over is frozen "
            "(docs/L2/evaluation/league.md §1, ASM-16)",
        )
        self.assertEqual(
            J.matrix_members(table),
            J.names_of(readback) + ["variant-1"],
            "the table's membership is the pool read-back's order, then "
            "variant-1 (docs/L2/evaluation/matrix.md §1, surface.md §10)",
        )
        self.assertEqual(
            len(J.matrix_members(table)),
            len(J.names_of(readback)) + 1,
            "K = |pool| + V with one variant (docs/L1/league.md §4, ASM-14)",
        )

    def test_join_evl_6_2_the_cells_are_exactly_one_per_unordered_pair(self):
        """JOIN-EVL-6.2 K(K−1)/2 cells, one per unordered pair and no repeat.

        `docs/L2/evaluation/league.md` §3 and `docs/L3/evaluation/matrix.md` §2:
        the pairs are enumerated lexicographically by membership position, every
        cell is played to completion before the next begins, and a pair is
        unordered — `(i, j)` and `(j, i)` are one cell whose two directions report
        both seats (`records.md` §9, D-16).
        """
        table = J.shared_matrix()
        members = J.matrix_members(table)
        cells = list(table["cells"])
        self.assertEqual(
            len(cells),
            J.cell_count(members),
            "the table carries exactly K(K−1)/2 cells "
            "(docs/L1/league.md §4, records.md §10)",
        )
        seen = [frozenset(J.cell_members(cell)) for cell in cells]
        self.assertEqual(
            len(set(seen)),
            len(seen),
            "no unordered pair appears in two cells "
            "(docs/L3/evaluation/rating.md §6, docs/L1/league.md §4)",
        )
        expected = [
            frozenset((members[i], members[j]))
            for i, j in itertools.combinations(range(len(members)), 2)
        ]
        self.assertEqual(
            seen,
            expected,
            "the cells are one per unordered pair, in the enumeration's order "
            "(docs/L3/evaluation/matrix.md §2)",
        )

    def test_join_evl_6_3_one_hand_count_one_seed_one_label(self):
        """JOIN-EVL-6.3 every cell plays the table's one count at the league's seed.

        `docs/L2/evaluation/league.md` §3 and `§5`: every cell of one table is
        played at one hand count, the three baseline cells included, so no member's
        row is measured more precisely than another's; the table seed is the
        league's one integer; and the label is the budget the table was asked for
        (`records.md` §10).
        """
        table = J.shared_matrix()
        declared = J.league()
        cell_size = declared["tables"]["live"]["hands_per_cell"]
        self.assertEqual(
            int(table["hands_per_cell"]),
            int(cell_size),
            "a live table's one hand count is the league's declared live cell size "
            "(docs/L2/evaluation/declarations.md §4.1, ASM-14)",
        )
        for index, cell in enumerate(table["cells"]):
            self.assertEqual(
                int(cell["hands"]),
                int(table["hands_per_cell"]),
                "every cell is played at the table's one hand count, cell %d "
                "(docs/L1/league.md §3, docs/L2/evaluation/matrix.md §6)"
                % (index,),
            )
        self.assertEqual(
            int(table["table_seed"]),
            int(declared["table_seed"]),
            "the table seed is the league's one integer "
            "(docs/L2/evaluation/matrix.md §3, declarations.md §6)",
        )
        self.assertEqual(
            str(table["table"]),
            "live",
            "the label is the budget the table was asked for "
            "(records.md §10, docs/L2/evaluation/matrix.md §6)",
        )
        self.assertEqual(
            len(table["cells"]),
            declared["cell_count"](len(J.matrix_members(table))),
            "the declared cell count and the played table agree "
            "(docs/L2/evaluation/surface.md §4, declarations.md §5)",
        )

    def test_join_evl_6_4_each_cells_seed_is_derived_from_the_table_seed(self):
        """JOIN-EVL-6.4 a cell's seed is the pinned derivation of the table seed and the pair.

        `docs/L3/evaluation/matrix.md` §3 and `docs/L3/evaluation/scheduler.md` §3:
        the cell seed is a SHA-256 digest of the table seed and the pair's
        membership positions, an integer in ``[0, 2**31)``, recorded as the cell's
        `seed` (`records.md` §9).  A table is therefore reproduced from its table
        seed, its membership and its budget and from nothing else (ASM-2).
        """
        table = J.shared_matrix()
        members = J.matrix_members(table)
        table_seed = int(table["table_seed"])
        for i, j in itertools.combinations(range(len(members)), 2):
            cell = J.cell_by_pair(table, members[i], members[j])
            seed = cell["seed"]
            self.assertIsInstance(
                seed,
                int,
                "a cell records its seed as a plain integer (records.md §9, "
                "docs/L3/evaluation/scheduler.md §3): %r" % (seed,),
            )
            self.assertEqual(
                int(seed),
                J.cell_seed(table_seed, i, j),
                "the cell (%r, %r) must be seeded from the table seed and the "
                "pair's positions (docs/L3/evaluation/matrix.md §3)"
                % (members[i], members[j]),
            )

    def test_join_evl_6_5_the_baseline_cells_are_in_the_table(self):
        """JOIN-EVL-6.5 the three mutual baseline cells exist at the table's hand count.

        `docs/L2/evaluation/league.md` §3 and `docs/L1/protocol.md` §3: the three
        baselines are rows and columns at the table's one hand count, and their
        three mutual cells are in the table, so the matrix carries cells no model
        influences — the only fixed standard a self-play league has (D-16).
        """
        table = J.shared_matrix()
        members = J.matrix_members(table)
        names = [str(name) for name in J.protocol()["baselines"]]
        for member_a, member_b in itertools.combinations(names, 2):
            cell = J.cell_by_pair(table, member_a, member_b)
            self.assertEqual(
                int(cell["hands"]),
                int(table["hands_per_cell"]),
                "the baseline cells are played at the table's one hand count "
                "(docs/L2/evaluation/league.md §3, D-16)",
            )
            for member_id in (member_a, member_b):
                direction = J.direction_for(cell, member_id)
                wins, ties, losses = J.counts_of(direction)
                self.assertEqual(
                    wins + ties + losses,
                    int(cell["hands"]),
                    "a baseline's own direction accounts for every hand of the "
                    "cell (records.md §9)",
                )
        for index, cell in enumerate(table["cells"]):
            pair = J.cell_members(cell)
            self.assertEqual(
                len(pair),
                2,
                "a cell pairs two members, cell %d (records.md §9)" % (index,),
            )
            self.assertNotEqual(
                pair[0],
                pair[1],
                "a cell pairs two distinct members, cell %d "
                "(docs/L2/evaluation/surface.md §9)" % (index,),
            )
            for member_id in pair:
                self.assertIn(
                    member_id,
                    members,
                    "a cell names a member of the table's membership "
                    "(records.md §10, docs/L1/league.md §4)",
                )
            self.assertEqual(
                len(cell["params"]),
                len(pair),
                "one parameter count per member, position-aligned with the "
                "cell's members (records.md §9, docs/L2/evaluation/surface.md §2)",
            )


if __name__ == "__main__":
    unittest.main()
