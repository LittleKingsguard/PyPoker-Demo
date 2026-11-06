"""FAM-9 — the rating: one value and a 95% interval per member, anchored on the baselines.

`docs/L1/battery.md` §3 FAM-9 and `docs/L1/league.md` §5 (D-16, ASM-17).  The fitted
rating is Bradley-Terry over the matrix's cells, it reports one value and a 95%
confidence interval per member with the hands behind each value, the three baselines'
mean is fixed at zero so every value reads as a distance from the only fixed standard in
the table, and a member that won or lost everything is bounded rather than infinite.
The rating travels with the raw matrix and is never a claim of poker skill (``league.md``
§5, ``battery.md`` §5); no case below requires one member to outrank another.
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


class FAM9Rating(S.SurfaceCase):
    """The fit: its values, its intervals, its anchor and its bound."""

    # -- helpers -----------------------------------------------------------
    def table(self):
        return S.shared_league(self)

    def entry_for(self, entries, member):
        """One member's rating entry, allowing for a prefixed or decorated key."""
        if member in entries:
            return entries[member]
        for key, entry in entries.items():
            if R.tok(key) == R.tok(member) or R.tok(member) in R.tok(key):
                return entry
        raise AssertionError(
            "the rating carries no entry for the matrix member %r (records.md §11): %r"
            % (member, sorted(entries)),
        )

    def finite(self, value):
        return value == value and value not in (float("inf"), float("-inf"))

    # -- what a rating must carry ------------------------------------------
    def test_fam9_1_there_is_one_value_per_matrix_member(self):
        """FAM-9.1 the rating names exactly the matrix's members, one value each."""
        league = self.table()
        members = R.matrix_members(league["matrix"])
        entries = R.rating_entries(league["rating"])
        # The listing is counted as well as the keyed entries: a member listed twice would
        # collapse in the reader and pass a count taken after it (battery.md §2).
        self.assertEqual(
            R.rating_entry_count(league["rating"]),
            len(members),
            "a rating is fitted over the matrix, so it lists one entry per member "
            "(records.md §11, league.md §5): %r entries for %r members: %r"
            % (R.rating_entry_count(league["rating"]), members, league["rating"]),
        )
        self.assertEqual(
            len(entries),
            len(members),
            "a rating is fitted over the matrix, so it reports one entry per member "
            "(records.md §11, league.md §5): %d entries for %d members: %r"
            % (len(entries), len(members), sorted(entries)),
        )
        for member in members:
            self.entry_for(entries, member)

    def test_fam9_2_each_value_carries_a_95_percent_interval_around_it(self):
        """FAM-9.2 every value has a finite 95% interval whose extent contains it."""
        league = self.table()
        entries = R.rating_entries(league["rating"])
        for member, entry in entries.items():
            value = R.rating_value(entry)
            first, second = R.rating_interval(entry)
            self.assertTrue(
                self.finite(value) and self.finite(first) and self.finite(second),
                "a rating's value and its 95%% interval are finite numbers (league.md §5): "
                "%r" % (entry,),
            )
            # records.md §11 fixes neither the bounds' key names nor their order, so the
            # interval is read as the pair whose extent is meant to hold the value: a
            # conforming record that states its bounds high-first is the same interval.
            self.assertGreaterEqual(
                value,
                first,
                "the fitted value lies inside its own 95%% interval, whichever order the "
                "record states its two bounds in: %r" % (entry,),
            )
            self.assertLessEqual(
                value,
                second,
                "the fitted value lies inside its own 95%% interval, whichever order the "
                "record states its two bounds in: %r" % (entry,),
            )

    def test_fam9_3_the_method_is_declared_bradley_terry(self):
        """FAM-9.3 the rating declares the fitted method (league.md §5)."""
        rating = self.table()["rating"]
        method = R.required(rating, "a rating record", "method")
        self.assertIn(
            "bradley",
            R.tok(S.flatten_text(method)) + R.tok(method),
            "the fitted method is Bradley-Terry and the record declares it (records.md §11, "
            "league.md §5): %r" % (method,),
        )

    def test_fam9_4_the_three_baselines_mean_is_anchored_at_zero(self):
        """FAM-9.4 the baselines' mean value is 0, the table's only fixed standard."""
        league = self.table()
        members = R.matrix_members(league["matrix"])
        entries = R.rating_entries(league["rating"])
        baseline_values = []
        for name in S.BASELINES:
            member = R.baseline_member(members, name)
            self.assertIsNotNone(
                member,
                "the %r baseline is a rated member of the table (protocol.md §3): %r"
                % (name, members),
            )
            baseline_values.append(R.rating_value(self.entry_for(entries, member)))
        self.assertAlmostEqual(
            sum(baseline_values) / len(baseline_values),
            0.0,
            places=3,
            msg="the fit is anchored so the three baselines' mean is 0, which is what makes "
                "two tables comparable on one scale (league.md §5, ASM-17): %r"
                % (baseline_values,),
        )

    def test_fam9_5_the_hands_behind_each_value_are_reported(self):
        """FAM-9.5 each rating carries the hands it was fitted from."""
        league = self.table()
        matrix = league["matrix"]
        hands = R.matrix_hands_per_cell(matrix)
        expected = hands * (len(R.matrix_members(matrix)) - 1)
        entries = R.rating_entries(league["rating"])
        for member, entry in entries.items():
            reported = R.rating_hands(entry)
            self.assertIsNotNone(
                reported,
                "a rating entry reports the hands behind its value (records.md §11): %r"
                % (entry,),
            )
            self.assertEqual(
                reported,
                expected,
                "a member plays one cell against each of the other K-1 members, so %d "
                "hands at %d per cell stand behind its value (%r): %r"
                % (expected, hands, member, reported),
            )

    def test_fam9_6_a_member_that_won_everything_is_bounded_not_infinite(self):
        """FAM-9.6 a member with no finite maximum-likelihood value is bounded."""
        matrix = R.bounded_matrix()
        rating = self.rating_of(matrix)
        entries = R.rating_entries(rating)
        champion = "version-nimbus"
        entry = self.entry_for(entries, champion)
        value = R.rating_value(entry)
        first, second = R.rating_interval(entry)
        for number in (value, first, second):
            self.assertTrue(
                self.finite(number),
                "a member that won every cell has no finite maximum-likelihood rating, so "
                "the fit bounds it rather than reporting infinity (league.md §5, ASM-17): "
                "%r" % (entry,),
            )
        self.assertGreaterEqual(
            value,
            first,
            "the bounded member's value lies inside the interval its bound is stated in, "
            "whichever order the record states the two bounds: %r" % (entry,),
        )
        self.assertLessEqual(
            value,
            second,
            "the bounded member's value lies inside the interval its bound is stated in, "
            "whichever order the record states the two bounds: %r" % (entry,),
        )
        flag = R.rating_flag(rating, "bound")
        if flag is None:
            flag = R.rating_flag(rating, "applied")
        self.assertIsNotNone(
            flag,
            "the fit reports whether it applied a bound to a member with no finite "
            "maximum-likelihood value — league.md §5 requires the record to report that the "
            "bound was applied, and battery.md §3 FAM-9 asserts it (records.md §11, "
            "ASM-17): %r" % (rating,),
        )
        self.assertTrue(
            flag is True or R.tok(flag) in ("true", "yes", "1", "applied"),
            "the record says a bound was applied to the member that won every cell "
            "(league.md §5, ASM-17): %r" % (flag,),
        )

    def test_fam9_7_the_fit_records_its_convergence_and_its_bootstrap_seed(self):
        """FAM-9.7 the interval's seed and the fit's convergence are recorded."""
        rating = self.table()["rating"]
        values = R.numbers_under(rating, "bootstrap_seed", "bootstrap seed", "bootstrap")
        self.assertTrue(
            values,
            "the hand-level bootstrap is seeded from the table seed and its seed is recorded "
            "so the interval can be re-run (league.md §5, ASM-17; battery.md §3 FAM-9 makes "
            "the battery assert it): %r" % (rating,),
        )
        converged = R.rating_flag(rating, "conver")
        self.assertIsNotNone(
            converged,
            "the rating records whether the fit converged — the fit's convergence is part of "
            "what evaluation.rating returns (e2e-surface §3.4) and battery.md §3 FAM-9 makes "
            "the battery assert it is recorded (records.md §11): %r" % (rating,),
        )
        self.assertTrue(
            converged is True or R.tok(converged) in ("true", "yes", "1", "converged"),
            "the shared table is a complete round robin, so its Bradley-Terry fit converges "
            "and the recorded flag says so (league.md §5, D-6): %r" % (converged,),
        )

    def test_fam9_8_the_anchor_is_declared_in_the_record(self):
        """FAM-9.8 the record names the anchor: the three baselines' mean at zero."""
        rating = self.table()["rating"]
        anchor = R.required(rating, "a rating record", "anchor")
        text = S.flatten_text(anchor) + " " + str(anchor).lower()
        named = (
            "baseline" in text
            or "zero" in text
            or "0" in text
            or any(name in text for name in S.BASELINES)
        )
        self.assertTrue(
            named,
            "the anchor is the three baselines' mean fixed at zero, and the record says so "
            "(records.md §11, ASM-17): %r" % (anchor,),
        )


if __name__ == "__main__":
    unittest.main()
