"""FAM-11 — the report: seven evidence families, explicit rows, named refusals.

`docs/L1/battery.md` §3 FAM-11 and `docs/L1/protocol.md` §1 (D-6, D-16).  Rev 2
replaced the head-to-head row with the league, so ``evaluation.report`` now takes
``(rung name, run record, matrix, rating)`` and judges the record against **seven**
evidence families: ``curves``, ``pool``, ``matrix``, ``rating``, ``baselines``,
``axis row`` and ``header``.  A complete record yields a report carrying all seven; a
record missing any one is refused with that family named and is never fabricated; and
the rows that must exist even when there is nothing to compare — R1's pool row, which
is the three baselines alone, and the single-variant axis row — are explicit values.
"""

import os
import sys
import unittest

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _surface as S  # noqa: E402

FAMILIES = S.FAMILIES


class FAM11Report(S.SurfaceCase):
    """The report, its seven families, its refusals, and its explicit rows."""

    # -- helpers -----------------------------------------------------------
    def assert_names_family(self, text, family):
        """The refusal's own words must name the evidence family that was missing."""
        self.assertIn(
            S._family_token(family),
            S._family_token(text),
            "the refusal must name the missing family %r: %r" % (family, text),
        )

    def league(self):
        return S.shared_league(self)

    def completed(self, rung_name="R2", seeds=(S.SEED_A,), budget=S.BUDGET_TINY,
                  axis_row="n/a, single variant"):
        """A complete record: the run's record plus every measured family."""
        league = self.league()
        record = self.evidence_record(
            self.run_record(rung_name, seeds, budget),
            matrix=league["matrix"],
            rating=league["rating"],
            pool_row=self.members(league["pool"]),
            seeds=seeds,
            budget=budget,
            axis_row=axis_row,
        )
        return record, league["matrix"], league["rating"]

    def incomplete(self, missing):
        """A record carrying every family of protocol.md §1 except ``missing``.

        ``matrix`` and ``rating`` are handed to ``report`` as its own arguments
        (``e2e-surface.md`` §3.4), so they are withheld from both the record and the
        call; the other five families are withheld from the record alone.
        """
        league = self.league()
        include = tuple(family for family in FAMILIES if family != missing)
        matrix = None if missing == "matrix" else league["matrix"]
        rating = None if missing == "rating" else league["rating"]
        record = self.evidence_record(
            {},
            matrix=matrix,
            rating=rating,
            pool_row=self.members(league["pool"]),
            include=include,
            seeds=(S.SEED_A,),
            budget=S.BUDGET_TINY,
        )
        return record, matrix, rating

    def refused(self, missing, rung_name="R2"):
        record, matrix, rating = self.incomplete(missing)
        text = S.refusal_text(lambda: self.report_of(rung_name, record, matrix, rating))
        self.assertIsNotNone(
            text,
            "a record with no %r family must not produce a report (protocol.md §1)"
            % (missing,),
        )
        self.assert_names_family(text, missing)
        return text

    # -- the complete report -----------------------------------------------
    def test_fam11_1_a_complete_record_yields_a_report_with_all_seven_families(self):
        """FAM-11.1 a record with every family yields a report carrying all seven."""
        record, matrix, rating = self.completed("R2")
        report = self.report_of("R2", record, matrix, rating)
        self.assertTrue(S.is_mapping(report), "evaluation.report must return a record")
        for family in FAMILIES:
            self.assertTrue(
                S.has_family(report, family),
                "the report of a complete record must carry the %r family (protocol.md §1): %r"
                % (family, sorted(str(key) for key in report)),
            )

    def test_fam11_2_a_record_without_curves_is_refused(self):
        """FAM-11.2 a record missing curves is refused, and the refusal names curves."""
        self.refused("curves")

    def test_fam11_3_a_record_without_a_pool_is_refused(self):
        """FAM-11.3 a record missing the frozen pool is refused, naming the pool."""
        self.refused("pool")

    def test_fam11_4_a_record_without_a_matrix_is_refused(self):
        """FAM-11.4 a record missing the matrix is refused, and the matrix is named."""
        self.refused("matrix")

    def test_fam11_5_a_record_without_a_rating_is_refused(self):
        """FAM-11.5 a record missing the fitted rating is refused, naming the rating."""
        self.refused("rating")

    def test_fam11_6_a_record_without_the_baseline_rows_is_refused(self):
        """FAM-11.6 a record missing the baseline rows is refused, naming them."""
        self.refused("baselines")

    def test_fam11_7_a_record_without_an_axis_row_is_refused(self):
        """FAM-11.7 a record missing the axis row is refused, and the axis row is named."""
        self.refused("axis row")

    def test_fam11_8_a_record_without_a_header_is_refused(self):
        """FAM-11.8 a record missing the header is refused, and the header is named."""
        self.refused("header")

    # -- the rows that are values, not blanks ------------------------------
    def test_fam11_9_r1_s_pool_row_is_the_three_baselines_alone(self):
        """FAM-11.9 R1's pool row is the three baselines, never an invented version."""
        league = self.league()
        record = self.evidence_record(
            self.run_record("R1", (S.SEED_A,), S.BUDGET_TINY),
            matrix=league["matrix"],
            rating=league["rating"],
            pool_row=self.members(league["pool"]),
            seeds=(S.SEED_A,),
            budget=S.BUDGET_TINY,
        )
        report = self.report_of("R1", record, league["matrix"], league["rating"])
        self.assertTrue(
            S.has_family(report, "pool"),
            "R1's report carries a pool row even though the window is empty: %r" % (report,),
        )
        text = S.flatten_text(report)
        for baseline in S.BASELINES:
            self.assertIn(
                baseline,
                text,
                "R1's pool is the three baselines alone, so the report must name the %r "
                "baseline (league.md §2): %r" % (baseline, report),
            )
        for tag in S.VERSION_TAGS:
            self.assertNotIn(
                tag,
                text,
                "R1 has no lineage and its pool is the baselines alone; the report must not "
                "invent the version %r (league.md §2, protocol.md §5): %r" % (tag, report),
            )

    def test_fam11_10_a_single_variant_rung_s_axis_row_is_an_explicit_value(self):
        """FAM-11.10 R1-R3 carry 'n/a, single variant' as an explicit axis row."""
        record, matrix, rating = self.completed("R3", axis_row="n/a, single variant")
        report = self.report_of("R3", record, matrix, rating)
        self.assertTrue(
            S.has_family(report, "axis row"),
            "the report carries an axis row even for a single-variant rung: %r" % (report,),
        )
        self.assertIn(
            S._family_token("n/a, single variant"),
            S._family_token(S.flatten_text(report)),
            "a single-variant rung's axis row is the explicit value 'n/a, single variant': %r"
            % (report,),
        )

    def test_fam11_11_the_report_carries_the_seeds_the_table_seed_and_the_device(self):
        """FAM-11.11 a report records the seeds, the table seed and the device."""
        record, matrix, rating = self.completed("R2", seeds=(S.SEED_A,))
        report = self.report_of("R2", record, matrix, rating)
        text = S.flatten_text(report)
        self.assertIn(
            str(S.SEED_A),
            text,
            "the report must carry the seed set that was run (protocol.md §2)",
        )
        self.assertIn(
            "cpu",
            text,
            "the report must carry the device the run used, so a GPU run and a CPU run are "
            "never confused (protocol.md §6, D-8)",
        )
        seeds = S.declared_numbers(matrix, "tableseed") or S.declared_numbers(matrix, "seed")
        self.assertTrue(
            seeds,
            "the matrix records the table seed it played at, so a third party can re-run it "
            "(league.md §4): %r" % (matrix,),
        )
        self.assertTrue(
            any(str(int(seed)) in text for seed in seeds),
            "the report must carry the table seed of its own matrix (%r): %r"
            % ([int(seed) for seed in seeds], report),
        )

    def test_fam11_12_the_protocol_declares_the_required_header(self):
        """FAM-11.12 the protocol names the header a third party needs to re-run."""
        declared = self.ep("evaluation", "protocol")()
        text = S.flatten_text(declared)
        for token in ("game", "action", "param", "budget", "cell", "seed", "device",
                      "checkpoint"):
            self.assertIn(
                token,
                text,
                "the protocol's header carries %r, which is what makes a table re-runnable "
                "(protocol.md §1, D-6): %r" % (token, declared),
            )


if __name__ == "__main__":
    unittest.main()
