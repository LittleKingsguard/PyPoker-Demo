"""FAM-8 — the matrix: membership, one cell per pair, one hand count, refusals.

`docs/L1/battery.md` §3 FAM-8 and `docs/L1/league.md` §4 (D-16, ASM-14).  The
membership of a table is the frozen pool plus the rung's variants; the cells are
exactly K(K−1)/2 unordered pairs; every cell — the three baseline cells included — is
played at the one hand count the table budget declares; and a matrix whose cells differ
in hand count, whose membership is not the pool's, or which is missing a baseline is a
contract violation and not a table.  No case asserts a table's values: a member that
outranks a baseline is what a run measures, not what the surface promises
(``battery.md`` §5).
"""

import copy
import os
import sys
import unittest

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _records as R  # noqa: F401
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _records as R  # noqa: E402
    import _surface as S  # noqa: E402


class FAM8Matrix(S.SurfaceCase):
    """The table's membership, its cell arithmetic, and the tables it must refuse."""

    # -- helpers -----------------------------------------------------------
    def table(self):
        return S.shared_league(self)

    def pair_key(self, cell):
        return tuple(sorted(R.tok(member) for member in R.cell_members(cell)))

    def doctored(self):
        """A copy of the shared table, safe for a case to damage."""
        return copy.deepcopy(self.table()["matrix"])

    def refused(self, matrix, why):
        """The refusal ``evaluation.rating`` gives for a matrix that is not a table."""
        text = S.refusal_text(lambda: self.rating_of(matrix))
        self.assertIsNotNone(
            text,
            "%s must be refused and not fitted as a table (league.md §4, D-16)" % (why,),
        )
        return text

    # -- the membership and the cell arithmetic ----------------------------
    def test_fam8_1_membership_is_the_pool_plus_the_rung_s_variants(self):
        """FAM-8.1 K is the frozen pool's members plus the rung's variants."""
        league = self.table()
        pool_members = R.member_ids(self.members(league["pool"]))
        members = R.matrix_members(league["matrix"])
        self.assertEqual(
            len(members),
            len(pool_members) + 1,
            "the membership is the frozen pool (%d members) plus the rung's one variant "
            "here (league.md §4): %r" % (len(pool_members), members),
        )
        for member in pool_members:
            self.assertIn(
                member,
                members,
                "every pool member is a row and a column of the table (league.md §4): %r"
                % (members,),
            )

    def test_fam8_2_the_cells_are_exactly_k_times_k_minus_one_over_two(self):
        """FAM-8.2 one cell per unordered pair: K(K−1)/2 cells and no repeat."""
        matrix = self.table()["matrix"]
        members = R.matrix_members(matrix)
        cells = R.matrix_cells(matrix)
        k = len(members)
        self.assertEqual(
            len(cells),
            k * (k - 1) // 2,
            "a table of K = %d members carries K(K-1)/2 = %d unordered pairs, not %d "
            "(league.md §4, ASM-14): %r" % (k, k * (k - 1) // 2, len(cells), members),
        )
        pairs = [self.pair_key(cell) for cell in cells]
        self.assertEqual(
            len(set(pairs)),
            len(pairs),
            "each unordered pair appears once: %r" % (sorted(pairs),),
        )
        self.assertEqual(
            sorted(set(pairs)),
            sorted({tuple(sorted((R.tok(left), R.tok(right))))
                    for index, left in enumerate(members)
                    for right in members[index + 1:]}),
            "the cells present are exactly the pairs of the membership (league.md §4)",
        )

    def test_fam8_3_every_cell_carries_the_table_s_one_hand_count(self):
        """FAM-8.3 one hand count across every cell, the baseline cells included."""
        matrix = self.table()["matrix"]
        hands = R.matrix_hands_per_cell(matrix)
        self.assertEqual(
            hands,
            S.LIVE_CELL_HANDS,
            "a live table's cells are 120 hands (league.md §6): %r" % (matrix,),
        )
        for cell in R.matrix_cells(matrix):
            self.assertEqual(
                R.cell_hands(cell),
                hands,
                "no member's row is measured more precisely than another's, so every cell — "
                "the three baseline cells included — plays %d hands (league.md §3, D-16): %r"
                % (hands, cell),
            )

    def test_fam8_4_the_three_baseline_cells_exist(self):
        """FAM-8.4 the baselines play each other: three cells no model influences."""
        matrix = self.table()["matrix"]
        members = R.matrix_members(matrix)
        baseline_ids = [R.baseline_member(members, name) for name in S.BASELINES]
        for member in baseline_ids:
            self.assertIsNotNone(
                member,
                "each of the three fixed baselines is a row and a column of the table "
                "(protocol.md §3, D-16): %r" % (members,),
            )
        present = {self.pair_key(cell) for cell in R.matrix_cells(matrix)}
        for index, left in enumerate(baseline_ids):
            for right in baseline_ids[index + 1:]:
                key = tuple(sorted((R.tok(left), R.tok(right))))
                self.assertIn(
                    key,
                    present,
                    "the three baselines play each other in the table, so the matrix carries "
                    "cells whose result no model can influence (D-16): %r" % (present,),
                )

    def test_fam8_5_the_matrix_carries_its_table_seed_and_budget(self):
        """FAM-8.5 a table records the table seed and the budget it was played at."""
        matrix = self.table()["matrix"]
        seed = R.matrix_table_seed(matrix)
        self.assertTrue(
            S.is_count(seed),
            "the table seed is a recorded integer, so a third party can re-run the table "
            "(league.md §4, ASM-2): %r" % (seed,),
        )
        # records.md §10 marks the matrix's `table` label **required**, and its value is
        # `live` or `full`; the label is read as a value, never as a substring of one.
        label = R.matrix_table(matrix)
        self.assertIsInstance(
            label,
            str,
            "records.md §10 makes a matrix's `table` label a required value, one of the two "
            "table budgets; the record gives %r" % (label,),
        )
        self.assertIn(
            R.tok(label),
            ("live", "full"),
            "the required `table` label is `live` or `full` (records.md §10): %r" % (label,),
        )
        self.assertEqual(
            R.tok(label),
            "live",
            "this matrix was asked for the live budget, so its required label reads live "
            "(records.md §10, league.md §6): %r" % (label,),
        )

    def test_fam8_6_no_cell_names_a_member_outside_the_table(self):
        """FAM-8.6 every cell pairs members of the table's own membership."""
        matrix = self.table()["matrix"]
        members = {R.tok(member) for member in R.matrix_members(matrix)}
        for cell in R.matrix_cells(matrix):
            for member in R.cell_members(cell):
                self.assertIn(
                    R.tok(member),
                    members,
                    "a matrix names its own membership and no foreign member (records.md "
                    "§10, league.md §4): %r not in %r" % (member, sorted(members)),
                )

    # -- what a table must refuse ------------------------------------------
    def test_fam8_7_a_matrix_with_an_unequal_cell_is_refused(self):
        """FAM-8.7 a table whose cells differ in hand count is refused."""
        matrix = self.doctored()
        hands = R.matrix_hands_per_cell(matrix)
        cells = R.matrix_cells(matrix)
        self.assertTrue(cells, "the table carries cells to compare: %r" % (matrix,))
        cell = cells[0]
        rewritten = R.set_declared(cell, hands - 1, "hands", "hands_played", "hands played")
        self.assertTrue(
            rewritten,
            "a cell record reports the hands it played under a key naming them, so the case "
            "can give one cell another hand count (records.md §9): %r" % (cell,),
        )
        self.refused(
            matrix,
            "a matrix whose cells differ in hand count",
        )

    def test_fam8_8_a_matrix_missing_a_baseline_is_refused(self):
        """FAM-8.8 a matrix that drops one of the three baselines is refused."""
        matrix = self.doctored()
        oracle = R.baseline_member(R.matrix_members(matrix), "oracle")
        self.assertIsNotNone(oracle, "the shared table carries the oracle baseline: %r" % (matrix,))
        R.drop_matrix_member(matrix, oracle)
        self.assertNotIn(
            R.tok(oracle),
            {R.tok(member) for member in R.matrix_members(matrix)},
            "the doctored table no longer names the oracle, in its membership or in its "
            "cells, whichever container holds them (records.md §10)",
        )
        self.refused(
            matrix,
            "a matrix missing one of the three pinned baselines",
        )

    def test_fam8_9_a_matrix_naming_a_member_outside_the_pool_is_refused(self):
        """FAM-8.9 the report refuses a matrix whose membership is not the pool's."""
        outsider = "version-outsider-9901"
        matrix = self.doctored()
        random_member = R.baseline_member(R.matrix_members(matrix), "random")
        self.assertIsNotNone(random_member, "the shared table carries the random baseline")
        R.rename_matrix_member(matrix, random_member, outsider)
        self.assertIn(
            R.tok(outsider),
            {R.tok(member) for member in R.matrix_members(matrix)},
            "the doctored membership names a member the pool does not hold, whichever "
            "container the membership is (records.md §10)",
        )
        league = self.table()
        record = self.evidence_record(
            self.run_record("R2", (S.SEED_A,), S.BUDGET_TINY),
            matrix=matrix,
            rating=league["rating"],
            pool_row=self.members(league["pool"]),
            seeds=(S.SEED_A,),
            budget=S.BUDGET_TINY,
        )
        text = S.refusal_text(
            lambda: self.report_of("R2", record, matrix, league["rating"])
        )
        self.assertIsNotNone(
            text,
            "a matrix whose membership is not the pool's plus its variants is not a table "
            "and must not be reported (league.md §4, D-16)",
        )
        body = R.tok(text)
        named = (
            R.tok(outsider) in body
            or "member" in body
            or "pool" in body
            or "baseline" in body
        )
        self.assertTrue(
            named,
            "the refusal says what the matrix violated — the foreign member, the pool's "
            "membership or the missing baseline (e2e-surface §2): %r" % (text,),
        )
    # -- the rules the table met, and the population they make up (D-19) ---
    def test_fam8_10_a_matrix_names_each_member_s_rule_and_its_population(self):
        """FAM-8.10 a matrix states each member's rule and the `population` it measured."""
        matrix = S.shared_rule_league(self)["matrix"]
        members = R.matrix_members(matrix)
        rules = {
            R.tok(member): rule for member, rule in R.rules_of(R.matrix_rules(matrix))
        }
        for member in members:
            self.assertIn(
                R.tok(member),
                rules,
                "records.md §10 makes the matrix's `rules` each member's rule by its id — "
                "`None` for a baseline, which carries none — so a table says which "
                "estimators its members are (e2e-surface.md §2, D-19): %r is missing from %r"
                % (member, R.matrix_rules(matrix)),
            )
        trained = sorted(rule for rule in rules.values() if rule)
        self.assertEqual(
            trained,
            sorted(S.RULES),
            "the table's trained members carry the two rules their policies carry, so the "
            "same architecture under two rules is what the matrix names (league.md §4, "
            "rules.md §7, D-19): %r" % (R.matrix_rules(matrix),),
        )
        population = R.rule_names_of(R.matrix_population(matrix))
        self.assertEqual(
            sorted(population),
            sorted(S.RULES),
            "a matrix states its `population`: the distinct rules its members declared, "
            "sorted, so a table says which estimators it was fitted over (records.md §10, "
            "league.md §4, D-19): %r" % (R.matrix_population(matrix),),
        )


if __name__ == "__main__":
    unittest.main()
