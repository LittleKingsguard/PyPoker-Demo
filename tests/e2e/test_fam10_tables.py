"""FAM-10 — the two table budgets, the live table's arithmetic, and the cost record.

`docs/L1/battery.md` §3 FAM-10, `docs/L1/league.md` §6–§7 (D-8, D-16, ASM-14,
ASM-15).  ``live`` and ``full`` are the two table budgets: one membership, two hand
counts per cell.  The live table's hands played are cells × hands per cell for the
membership; the cell count follows from K arithmetically; and the cost record carries
hands and seconds per hand.  No case below requires a wall clock to be beaten: the
bound sizes the table, and the timings are evidence that the measurement exists
(``battery.md`` §3, ASM-15).
"""

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


class FAM10Tables(S.SurfaceCase):
    """The two budgets, the live table's arithmetic and the cost record."""

    # -- helpers -----------------------------------------------------------
    def league(self):
        return self.ep("evaluation", "league")()

    def table(self):
        return S.shared_league(self)

    def driven(self, case_id="fam10-clock", seed=S.SEED_C):
        """One case through ``harness.drive``, which is what collects the timing."""
        case = {
            "id": case_id,
            "steps": [lambda: self.play(seed)],
            # A kind the fixture lists: the expectation vocabulary is the harness's own
            # (e2e-surface §3.6, records.md §14).
            "expect": [self.an_expectation_kind()],
        }
        return self.ep("harness", "drive")(case)

    # -- the two budgets ---------------------------------------------------
    def test_fam10_1_both_table_budgets_are_declared_with_their_cell_sizes(self):
        """FAM-10.1 evaluation.league declares live and full with their cell sizes."""
        league = self.league()
        live = R.table_numbers(league, "live")
        full = R.table_numbers(league, "full")
        self.assertIn(
            S.LIVE_CELL_HANDS,
            live,
            "the live table's cell is 120 hands (league.md §6, ASM-14): %r" % (league,),
        )
        self.assertIn(
            S.FULL_CELL_HANDS,
            full,
            "the full table's cell is 1,500 hands (league.md §6, ASM-14): %r" % (league,),
        )
        self.assertEqual(
            R.league_m(league),
            S.LEAGUE_BOUND,
            "both tables share one membership, so both are built at the league's bound M "
            "(league.md §6, D-16): %r" % (league,),
        )

    def test_fam10_2_the_live_table_plays_cells_times_hands_per_cell(self):
        """FAM-10.2 the live table's hands played are cells × hands per cell."""
        matrix = self.table()["matrix"]
        cells = R.matrix_cells(matrix)
        hands = R.matrix_hands_per_cell(matrix)
        k = len(R.matrix_members(matrix))
        played = sum(R.cell_hands(cell) for cell in cells)
        self.assertEqual(
            played,
            len(cells) * hands,
            "the live table plays its cells × its hands per cell, and nothing else: %d "
            "hands over %d cells at %d hands each (league.md §6, ASM-14): %r"
            % (played, len(cells), hands, matrix),
        )
        self.assertEqual(
            played,
            k * (k - 1) // 2 * hands,
            "the same total follows from the membership: K(K-1)/2 cells at %d hands for "
            "K = %d (league.md §4, §6): %d" % (hands, k, played),
        )

    def test_fam10_3_the_cell_count_for_a_membership_is_the_pair_count(self):
        """FAM-10.3 the league's cell count for K members is K(K−1)/2."""
        league = self.league()
        for k, expected in ((9, 36), (10, 45)):
            declared = R.cells_for(league, k)
            self.assertIsNotNone(
                declared,
                "the league declares the cell count for a given membership (e2e-surface "
                "§3.4), so a talk can size its table before it plays one: %r" % (league,),
            )
            self.assertEqual(
                declared,
                k * (k - 1) // 2,
                "a membership of K = %d members has K(K-1)/2 = %d unordered pairs "
                "(league.md §4, ASM-14): %r" % (k, k * (k - 1) // 2, declared),
            )

    # -- the cost record ---------------------------------------------------
    def test_fam10_4_the_driver_s_cost_record_carries_hands_and_seconds_per_hand(self):
        """FAM-10.4 harness.timings reports the hands counted and a duration per hand."""
        self.driven()
        timings = self.ep("harness", "timings")()
        facts = R.timing_facts(timings)
        self.assertTrue(
            facts["hands"],
            "the cost record carries the hands the driver counted (e2e-surface §3.6): %r"
            % (timings,),
        )
        self.assertTrue(
            all(number >= 0 for number in facts["hands"]),
            "the hands the driver counted are a non-negative count: %r" % (timings,),
        )
        per_hand = facts["per_hand"] or facts["throughput"]
        self.assertTrue(
            per_hand,
            "the cost record carries the seconds per hand, or the throughput that is their "
            "reciprocal, under whatever key the record spells it (seconds_per_hand, "
            "hands_per_second, ...): the per-hand cost of ASM-15 is measured, not asserted: %r"
            % (timings,),
        )
        self.assertTrue(
            any(number > 0 for number in per_hand),
            "a per-hand cost or a throughput is a positive measurement: %r" % (timings,),
        )
        # No case asserts that a wall clock was beaten: the bound sizes the table and the
        # record shows that the measurement exists (battery.md §2, ASM-15).

    def test_fam10_5_the_run_record_carries_its_own_cost_record(self):
        """FAM-10.5 a run record carries the cost its rung was measured at."""
        record = self.run_record("R1", (S.SEED_A,), S.BUDGET_TINY)
        timings = R.run_timings(record)
        self.assertTrue(
            timings,
            "the run record carries the cost record of harness.timings, so the D-7 speed "
            "evidence and ASM-15's per-hand bound have a measurement (records.md §12): %r"
            % (sorted(str(key) for key in record) if S.is_mapping(record) else record,),
        )
        facts = R.timing_facts(timings)
        self.assertTrue(
            facts["hands"],
            "the run's cost record carries the hands it counted: %r" % (timings,),
        )
        self.assertTrue(
            facts["per_hand"] or facts["throughput"],
            "the run's cost record carries seconds per hand or a throughput, read by what "
            "its keys name and not by a literal spelling (records.md §12, ASM-15): %r"
            % (timings,),
        )
        self.assertTrue(
            any(number > 0
                for number in facts["per_hand"] + facts["throughput"] + facts["clock"]),
            "the run's cost record carries a positive measured cost: %r" % (timings,),
        )


if __name__ == "__main__":
    unittest.main()
