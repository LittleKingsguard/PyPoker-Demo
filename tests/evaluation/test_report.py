"""EVL-7 — the per-rung report: `report`.

Drives `docs/L3/evaluation/report.md` §1-§5, `docs/L2/evaluation/surface.md` §13 and
`docs/L1/protocol.md` §1-§2: the seven evidence families in `protocol.md` §1's order
under `protocol()`'s own spellings (`axis row`'s space included), copied by value from
the run record and never invented or filled in; the five facts beside them -- the
rung, the seeds, the budget, the table seed and the device -- so a third party can
re-run what the report describes; R1's pool row being the three baselines it had and
no invented version; and a single-variant rung's axis row staying the explicit string
`n/a, single variant`.

The refusals are `report.md` §3's, in its order: an absent family by its own name, a
matrix that is not a table (`rating.md` §6's checks reused verbatim), the membership
rule (a foreign member, a missing pool member, a missing baseline), a rating that does
not name exactly the matrix's members, and a header missing one of the nine items.
`report` plays no hand, moves no stream and reads no file, so every case here works on
records built in `_evaluation_support` and the record it is handed is never edited.
"""

import copy
import unittest

from _evaluation_support import (
    AXIS_ROW,
    BASELINES,
    FAMILIES,
    HEADER_ITEMS,
    RUNG_NAME,
    SEED_SET,
    START_LABEL,
    VERSION_IDS,
    EvaluationCase,
    balanced,
    family_value,
    hand_matrix,
    header_record,
    matrix_cells,
    no_file_reads,
    pool_member_ids,
    pool_record,
    rating_entry_record,
    rating_record,
    report_inputs,
    run_record,
    token,
    version_record,
)


class ReportTest(EvaluationCase):
    def test_evl_7_1_a_complete_record_yields_the_seven_families_in_order(self):
        """EVL-7.1 one record carrying the seven families yields a report with exactly those seven under `protocol()`'s spellings, in `protocol.md` §1's order, each copied by value, and a matrix/rating that are the arguments (`report.md` §1-§2, `surface.md` §13, FAM-11.1)."""
        package = self.evaluation()
        rung, record, matrix, rating = report_inputs()
        report = package.report(rung, record, matrix, rating)
        self.assertIsInstance(
            report, dict, "report returns one mapping (report.md §2, records.md §13)"
        )
        self.assertEqual(
            tuple(package.protocol()["families"]),
            FAMILIES,
            "the family names a report is judged against are protocol()'s own, in its "
            "order (report.md §1, declarations.md §3 FAM-4, FAM-11)",
        )
        for family in FAMILIES:
            with self.subTest(family=family):
                self.assertIn(
                    family,
                    report,
                    "a complete record yields a report carrying the family under the "
                    "name protocol.md §1 spells, `axis row`'s space included "
                    "(report.md §1, surface.md §13, FAM-11.1): %r" % (tuple(report),),
                )
                self.assertEqual(
                    report[family],
                    record[family],
                    "every other family is a copy of the record's value, unchanged -- "
                    "the report copies and never reshapes (report.md §2, FAM-11.10): %r"
                    % (report[family],),
                )
        self.assertEqual(
            [key for key in report if key in FAMILIES],
            list(FAMILIES),
            "the seven families appear in protocol.md §1's order (report.md §1-§2): %r"
            % ([key for key in report if key in FAMILIES],),
        )
        self.assertEqual(
            report["rung"],
            rung,
            "the report carries the rung name as it was given (report.md §2, "
            "records.md §12): %r" % (report.get("rung"),),
        )
        self.assertEqual(
            report["matrix"],
            matrix,
            "the report is about the matrix it is handed, and carries it raw "
            "(report.md §2, §4): %r" % (report.get("matrix"),),
        )
        self.assertEqual(
            report["rating"],
            rating,
            "the rating travels beside the matrix it was fitted to (report.md §2): %r"
            % (report.get("rating"),),
        )

    def test_evl_7_2_each_absent_family_is_refused_by_its_own_name(self):
        """EVL-7.2 a record missing one of the seven families is refused with `MissingFamily` naming it exactly as `protocol()` spells it -- `axis row` included -- and never filled in (`report.md` §3 item 1, §4, D-6, FAM-11.2)."""
        package = self.evaluation()
        rung, record, matrix, rating = report_inputs()
        for family in FAMILIES:
            with self.subTest(family=family):
                incomplete = copy.deepcopy(record)
                incomplete.pop(family)
                self.assert_evaluation_refusal(
                    package.report,
                    rung,
                    incomplete,
                    matrix,
                    rating,
                    entry="report",
                    groups=((family,),),
                    label="a record with no %r family" % family,
                )

    def test_evl_7_3_r1_s_pool_row_is_the_baselines_it_had_and_the_axis_row_is_explicit(self):
        """EVL-7.3 a rung with no lineage reports the three baselines and no invented version, and a single-variant rung's axis row stays the explicit string `n/a, single variant`, copied verbatim and not wrapped into a record (`report.md` §1, §4, `league.md` §2, `protocol.md` §1, FAM-11.9)."""
        package = self.evaluation()
        rung, record, matrix, rating = report_inputs()
        report = package.report(rung, record, matrix, rating)
        pool_family = report["pool"]
        self.assertEqual(
            pool_member_ids(pool_family),
            BASELINES,
            "R1's pool row is the three baselines it actually had, and the report "
            "invents no version (report.md §4, league.md §2, FAM-11.9): %r"
            % (pool_member_ids(pool_family),),
        )
        self.assertEqual(
            len(pool_member_ids(pool_family)),
            3,
            "a pool record carries the three pinned baselines and no invented member "
            "(report.md §4, records.md §8): %r" % (pool_member_ids(pool_family),),
        )
        self.assertEqual(
            report["axis row"],
            AXIS_ROW,
            "a single-variant rung's axis row is the explicit value `n/a, single "
            "variant`, copied through verbatim and never wrapped into a record to "
            "satisfy a key name (report.md §1, §2, §4, declarations.md §3, "
            "protocol.md §1): %r" % (report["axis row"],),
        )
        self.assertIsInstance(
            report["axis row"],
            str,
            "the axis row of R1-R3 is a string value, not a record (report.md §1, "
            "declarations.md §3): %r" % (report["axis row"],),
        )

    def test_evl_7_4_the_membership_rule_the_rating_identity_and_the_header_are_enforced(self):
        """EVL-7.4 `report` refuses a foreign member, a missing pool member, a missing baseline, a rating that does not name exactly the matrix's members, and a header missing one of the nine items -- each naming what it found (`report.md` §3 items 2-5, `surface.md` §13, FAM-11.2)."""
        package = self.evaluation()
        base = hand_matrix(balanced)
        base_rating = rating_record(base)
        # (a) a matrix with three members outside the pool: at most two are the rung's
        #     variants, so the third is foreign and is named.
        wide = hand_matrix(
            balanced,
            members=BASELINES + ("variant-1", "variant-2", "version-outsider-9901"),
        )
        wide_rating = rating_record(wide)
        record = run_record(wide, wide_rating)
        self.assert_evaluation_refusal(
            package.report,
            RUNG_NAME,
            record,
            wide,
            wide_rating,
            entry="report",
            groups=(("version-outsider-9901",),),
            label="a member outside the pool that is no variant",
        )
        # (b) the pool names a version the matrix does not hold.
        held = pool_record(members=[version_record(VERSION_IDS[0], START_LABEL, step=7)])
        record = run_record(base, base_rating, pool=held)
        self.assert_evaluation_refusal(
            package.report,
            RUNG_NAME,
            record,
            base,
            base_rating,
            entry="report",
            groups=((VERSION_IDS[0],),),
            label="a missing pool member",
        )
        # (c) the matrix names no oracle: the table's anchor needs all three. This check
        #     is rating.md §6's, reused verbatim (report.md §3 item 2), so the case asks
        #     for the missing baseline and the rule, not for the entry point's word.
        three = hand_matrix(balanced, members=("random", "always-call", "variant-1"))
        three_rating = rating_record(three)
        record = run_record(three, three_rating)
        self.assert_evaluation_refusal(
            package.report,
            RUNG_NAME,
            record,
            three,
            three_rating,
            entry="oracle",
            groups=(("baseline",),),
            label="a missing baseline",
        )
        # (d) the rating names a member the matrix does not, and lacks one it does.
        extra = dict(
            base_rating,
            values=dict(base_rating["values"], **{"variant-2": rating_entry_record()}),
        )
        record = run_record(base, extra)
        self.assert_evaluation_refusal(
            package.report,
            RUNG_NAME,
            record,
            base,
            extra,
            entry="report",
            groups=(("variant-2",),),
            label="a rating naming a foreign member",
        )
        short = rating_record(base)
        short_values = dict(short["values"])
        short_values.pop("variant-1")
        short = dict(short, values=short_values)
        record = run_record(base, short)
        self.assert_evaluation_refusal(
            package.report,
            RUNG_NAME,
            record,
            base,
            short,
            entry="report",
            groups=(("variant-1",),),
            label="a rating missing a matrix member",
        )
        # (e) a header missing one of the nine items, naming it.
        for item in ("table seed", "game", "checkpoints"):
            with self.subTest(item=item):
                header = header_record()
                header.pop(item)
                record = run_record(base, base_rating, families={"header": header})
                self.assert_evaluation_refusal(
                    package.report,
                    RUNG_NAME,
                    record,
                    base,
                    base_rating,
                    entry="report",
                    groups=((item,),),
                    label="a header missing %r" % item,
                )

    def test_evl_7_5_a_matrix_that_is_not_a_table_is_refused(self):
        """EVL-7.5 `report` reuses `rating.md` §6's seven checks verbatim, so an uneven cell, a wrong cell count and a repeated pair are refused by the report too and nothing is assembled (`report.md` §3 item 2, `surface.md` §13, `league.md` §4)."""
        package = self.evaluation()
        matrix = hand_matrix(balanced)
        rating = rating_record(matrix)
        record = run_record(matrix, rating)
        cells = list(matrix_cells(matrix))
        uneven = list(cells)
        uneven[0] = dict(cells[0], hands=1)
        repeated = list(cells)
        repeated[-1] = cells[0]
        # These are rating.md §6's checks reused verbatim (report.md §3 item 2), so each
        # case asks for the violated rule's own word and not necessarily `report`.
        cases = (
            ("an uneven cell", dict(matrix, cells=tuple(uneven)), "hands"),
            ("a wrong cell count", dict(matrix, cells=tuple(cells[:5])), "cells"),
            ("a repeated pair", dict(matrix, cells=tuple(repeated)), "pair"),
        )
        for label, broken, rule in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.report,
                    RUNG_NAME,
                    record,
                    broken,
                    rating,
                    entry=rule,
                    label=label,
                )

    def test_evl_7_6_the_report_carries_the_seeds_the_table_and_the_device(self):
        """EVL-7.6 the report carries the seed set, the budget, the table seed and the device -- read from the record, never defaulted -- so a GPU run and a CPU run are never confused (`report.md` §2, `protocol.md` §2, §6, D-6, FAM-11.11)."""
        package = self.evaluation()
        rung, record, matrix, rating = report_inputs()
        report = package.report(rung, record, matrix, rating)
        self.assertEqual(
            tuple(report["seeds"]),
            SEED_SET,
            "the report carries the seed set the run used, so a third party can re-run "
            "it (report.md §2, protocol.md §2): %r" % (report.get("seeds"),),
        )
        self.assertEqual(
            report["table"],
            matrix["table"],
            "the report carries the budget its table was measured at "
            "(report.md §2, records.md §10): %r" % (report.get("table"),),
        )
        self.assertEqual(
            int(report["table seed"]),
            int(matrix["table_seed"]),
            "the report carries its table's table seed, the league's one integer "
            "(report.md §2, league.md §3): %r" % (report.get("table seed"),),
        )
        self.assertEqual(
            report["device"],
            "cpu",
            "the report carries the device the run used, read from the header "
            "(report.md §2, protocol.md §6): %r" % (report.get("device"),),
        )
        header_keys = {token(key) for key in report["header"]}
        for item in HEADER_ITEMS:
            with self.subTest(header_item=item):
                wanted = token(item)
                self.assertTrue(
                    any(
                        wanted == key or wanted in key or key in wanted
                        for key in header_keys
                    ),
                    "the report's header family carries protocol.md §1's nine items, and "
                    "%r is one of them (declarations.md §2.1, report.md §2): %r"
                    % (item, tuple(report["header"])),
                )
        other = header_record(device="cuda:0")
        record = run_record(matrix, rating, families={"header": other})
        report = package.report(rung, record, matrix, rating)
        self.assertEqual(
            report["device"],
            "cuda:0",
            "the device is read from the header and never defaulted, so a GPU run's "
            "report says so (report.md §2, protocol.md §6, D-8): %r"
            % (report.get("device"),),
        )
        with self.subTest(seeds="from the header when the record states none"):
            without = run_record(matrix, rating)
            without.pop("seeds")
            report = package.report(rung, without, matrix, rating)
            self.assertEqual(
                tuple(report["seeds"]),
                SEED_SET,
                "the seed set is read from the record's own `seeds`, else from its header "
                "family's seed item (report.md §2, protocol.md §2): %r"
                % (report.get("seeds"),),
            )

    def test_evl_7_7_report_plays_no_hand_moves_no_stream_and_reads_no_file(self):
        """EVL-7.7 `report` is assembled from records alone: it plays no hand, leaves Python's global `random` stream where it found it and reads no file (`report.md` §4, `surface.md` §13, module-map.md §3, D-13)."""
        package = self.evaluation()
        rung, record, matrix, rating = report_inputs()
        before = self.stream_state()
        with no_file_reads("report()"):
            report = package.report(rung, record, matrix, rating)
        self.assert_stream_unchanged(before, "report()")
        self.assertIn(
            "header",
            report,
            "report returned a report carrying the seven families (surface.md §13): %r"
            % (tuple(report),),
        )

    def test_evl_7_8_report_never_edits_the_run_record_it_is_handed(self):
        """EVL-7.8 the run record is read, not mutated: a caller keeps what `training` gave it, so the record is unchanged after a report (`report.md` §4, `surface.md` §13, records.md §13)."""
        package = self.evaluation()
        rung, record, matrix, rating = report_inputs()
        snapshot = copy.deepcopy(record)
        package.report(rung, record, matrix, rating)
        self.assertEqual(
            record,
            snapshot,
            "the report reads its argument and never edits the run record it is handed "
            "(report.md §4, module-map.md §3): %r" % (record,),
        )

    def test_evl_7_9_an_explicit_value_and_an_underscore_spelling_satisfy_a_family(self):
        """EVL-7.9 a family is present when the record carries a key whose letters-and-digits token equals the family's, and an explicit `n/a` value -- a string or an empty container -- satisfies one; over-refusal is a defect (`report.md` §3 item 1, `errors.md` §5)."""
        package = self.evaluation()
        rung, record, matrix, rating = report_inputs()
        spelled = copy.deepcopy(record)
        spelled["axis_row"] = spelled.pop("axis row")
        report = package.report(rung, spelled, matrix, rating)
        self.assertEqual(
            family_value(report, "axis row"),
            AXIS_ROW,
            "`axis_row` and `axisrow` are the same family name as `axis row` "
            "(report.md §3 item 1's token rule): %r" % (family_value(report, "axis row"),),
        )
        explicit = copy.deepcopy(record)
        explicit["curves"] = ()
        report = package.report(rung, explicit, matrix, rating)
        self.assertEqual(
            family_value(report, "curves"),
            (),
            "an explicit empty container is a value that satisfies a family, and a "
            "blank is only `None` or a missing key (report.md §3 item 1, "
            "errors.md §5): %r" % (family_value(report, "curves"),),
        )
        n_a = copy.deepcopy(record)
        n_a["baselines"] = "n/a"
        report = package.report(rung, n_a, matrix, rating)
        self.assertEqual(
            family_value(report, "baselines"),
            "n/a",
            "an explicit `n/a` string is a value, never a blank "
            "(report.md §3 item 1, records.md §13): %r" % (family_value(report, "baselines"),),
        )

    def test_evl_7_10_a_rung_name_that_is_not_a_str_and_a_record_that_is_not_a_mapping_are_refused(self):
        """EVL-7.10 a `rung_name` that is not a `str` and a `record` that is not a mapping are `InvalidArgument` refusals, raised the same way rather than returning a partial report (`report.md` §3, `errors.md` §2, `surface.md` §13)."""
        package = self.evaluation()
        rung, record, matrix, rating = report_inputs()
        cases = (
            ("a number as the rung name", (42, record, matrix, rating), (("rung", "report"),)),
            ("a None rung name", (None, record, matrix, rating), (("rung", "report"),)),
            ("a list as the record", (rung, [], matrix, rating), (("record", "report"),)),
            ("a string as the record", (rung, "record", matrix, rating), (("record", "report"),)),
        )
        for label, args, groups in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.report, *args, entry="report", groups=groups, label=label
                )


if __name__ == "__main__":
    unittest.main()
