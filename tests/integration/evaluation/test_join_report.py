"""JOIN-EVL-10 — report ⇄ matrix ⇄ rating: one membership, one record.

`docs/L2/evaluation/surface.md` §13 and `docs/L3/evaluation/report.md` §3: a
report refuses a matrix whose membership is not the pool family's members plus the
rung's variants, refuses a rating that does not name exactly the matrix's members,
and refuses a header missing one of `protocol.md` §1's nine items; a complete
record's report carries the seed set, the table seed and the device, so a third
party can re-run what it describes.  `report` plays no hand, reads no file and
moves no stream — it is assembled from records alone (`docs/L2/evaluation/
league.md` §6, `docs/L1/records.md` §13, D-6).
"""

import importlib.util
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


class ReportIdentity(J.JoinCase):
    """The report's membership rule, the rating's identity and its facts."""

    def renamed(self):
        """A real table with the pool's version renamed in membership and cells."""
        table = J.shared_matrix()
        renamed = J.renamed_matrix(table, J.VERSION_A, J.FOREIGN_MEMBER)
        fitted = J.rating(renamed)
        record = J.run_record(table, J.shared_rating())
        record["matrix"] = renamed
        record["rating"] = fitted
        return renamed, fitted, record

    def test_join_evl_10_1_a_membership_outside_the_pool_family_is_refused(self):
        """JOIN-EVL-10.1 a real table with the pool's member renamed is not the pool's.

        `docs/L2/evaluation/surface.md` §13 and `docs/L3/evaluation/report.md` §3
        item 3: every pool member must be in the matrix's membership, the three
        baselines must be present, and no more than two members may lie outside the
        pool.  The renamed table is still a *table* — same K, one cell per pair, the
        baselines present — but the pool family no longer names one of its members,
        so the refusal is the membership rule's and it names the missing member
        (`docs/L2/evaluation/league.md` §3, `docs/L1/protocol.md` §1).
        """
        renamed, fitted, record = self.renamed()
        message = self.assert_refusal(
            "report",
            [("pool",), (J.VERSION_A, J.FOREIGN_MEMBER)],
            lambda: J.report(J.RUNG, record, renamed, fitted),
            "a matrix whose membership is not the pool family's members plus the "
            "variants",
        )
        self.assertIn(
            J.VERSION_A.lower(),
            message.lower(),
            "the refusal names the missing pool member "
            "(docs/L3/evaluation/report.md §3 item 3): %r" % (message,),
        )

    def test_join_evl_10_2_a_rating_that_names_other_members_is_refused(self):
        """JOIN-EVL-10.2 the rating must name exactly the matrix's members.

        `docs/L2/evaluation/surface.md` §13 and `docs/L3/evaluation/report.md` §3
        item 4: `rating["values"]` must name exactly the matrix's members, no more
        and no fewer, and the difference is named (`records.md` §11).  A rating
        fitted to another table is the failure this rule exists to catch: the rating
        and the matrix travel together (`docs/L2/evaluation/league.md` §4, D-16).
        """
        table = J.shared_matrix()
        record = J.run_record(table, J.shared_rating())
        broken = J.clone(J.shared_rating())
        broken["values"].pop("variant-1")
        record["rating"] = broken
        message = self.assert_refusal(
            "report",
            [("rating",), ("variant-1",)],
            lambda: J.report(J.RUNG, record, table, broken),
            "a rating that does not name the matrix's variant member",
        )
        self.assertIn(
            "variant-1",
            message.lower(),
            "the refusal names the difference between the rating and the matrix "
            "(docs/L3/evaluation/report.md §3 item 4): %r" % (message,),
        )

    def test_join_evl_10_3_a_complete_report_carries_the_seeds_seed_and_device(self):
        """JOIN-EVL-10.3 the report carries the seed set, the table seed and the device.

        `docs/L2/evaluation/surface.md` §13 and `docs/L1/protocol.md` §2, §6: the
        report carries the rung, the seeds, the table budget, the table seed and the
        device beside the seven families, so a CPU run and a GPU run are never
        confused and a third party can re-play the same table
        (`docs/L3/evaluation/report.md` §2, D-6).
        """
        table = J.shared_matrix()
        record = J.run_record(table, J.shared_rating())
        assembled = J.report(J.RUNG, record, table, J.shared_rating())
        self.assertEqual(
            assembled["rung"],
            J.RUNG,
            "the report carries the rung name it was given, an unregistered "
            "configuration's label included (records.md §12, ladder.md §1)",
        )
        self.assertEqual(
            tuple(assembled["seeds"]),
            tuple(J.protocol()["seeds"]),
            "the report carries the seed set the run used (protocol.md §2, "
            "docs/L3/evaluation/report.md §2)",
        )
        self.assertEqual(
            int(assembled["table seed"]),
            int(table["table_seed"]),
            "the report carries its matrix's table seed, the league's one integer "
            "(docs/L3/evaluation/report.md §2, docs/L2/evaluation/league.md §3)",
        )
        self.assertEqual(
            str(assembled["table"]),
            str(table["table"]),
            "the report states the budget its table was measured at "
            "(records.md §10, §13)",
        )
        self.assertEqual(
            str(assembled["device"]),
            "cpu",
            "the report carries the device the header names, `cpu` inside the "
            "sandbox (protocol.md §6, D-8)",
        )

    def test_join_evl_10_4_a_report_plays_nothing_and_edits_nothing(self):
        """JOIN-EVL-10.4 `report` moves no stream and leaves the run record alone.

        `docs/L2/evaluation/surface.md` §13 and `docs/L3/evaluation/report.md` §4:
        a report is assembled from records alone — it plays no hand, reads no file
        and moves no stream — and it never edits the run record it is handed, so a
        caller keeps what `training` gave it (records.md §13, D-13, ASM-2).
        """
        table = J.shared_matrix()
        record = J.run_record(table, J.shared_rating())
        before = J.canonical(record)
        self.assert_stream_unchanged(
            lambda: J.report(J.RUNG, record, table, J.shared_rating()),
            "evaluation.report",
        )
        self.assertEqual(
            J.canonical(record),
            before,
            "report never edits the run record it is handed "
            "(docs/L3/evaluation/report.md §4, records.md §13)",
        )

    def test_join_evl_10_5_each_absent_family_is_refused_by_its_own_word(self):
        """JOIN-EVL-10.5 a missing family is refused by the name `protocol()` spells.

        `docs/L2/evaluation/surface.md` §13 and `docs/L1/protocol.md` §1: an absent
        family is refused by name — `axis row` included — and no family is invented
        or filled in.  The names are read from `protocol()` itself, because a
        report's families are judged against that declaration (`docs/L3/evaluation/
        declarations.md` §3, `docs/L3/evaluation/report.md` §3 item 1).
        """
        table = J.shared_matrix()
        fitted = J.shared_rating()
        record = J.run_record(table, fitted)
        declared = J.family_names()
        self.assertEqual(
            declared,
            ["curves", "pool", "matrix", "rating", "baselines", "axis row",
             "header"],
            "protocol() declares the seven families of protocol.md §1, in its "
            "order, `axis row` included (docs/L3/evaluation/declarations.md §3)",
        )
        for name in declared:
            with self.subTest(family=name):
                broken = J.clone(record)
                broken.pop(name)
                message = self.assert_refusal(
                    "report",
                    [(J.family_refusal(name),)],
                    lambda broken=broken: J.report(J.RUNG, broken, table, fitted),
                    "a record with the %r family absent" % (name,),
                )
                self.assertIn(
                    name.lower(),
                    message.lower(),
                    "the refusal names the family exactly as protocol() spells it "
                    "(docs/L3/evaluation/report.md §3 item 1): %r" % (message,),
                )

    def test_join_evl_10_6_a_header_missing_one_of_the_nine_items_is_refused(self):
        """JOIN-EVL-10.6 the header is judged by `protocol()`'s nine items.

        `docs/L2/evaluation/surface.md` §13 and `docs/L3/evaluation/declarations.md`
        §2.1: the header carries the game, the action space, every member's
        parameter counts, the sample budget, the cell size, the seed set, the table
        seed, the device and the checkpoint paths, and a header missing one is
        refused naming that item (`docs/L3/evaluation/report.md` §3 item 5).  The
        declaration's presence rule is tolerant by token — `seeds` is contained in
        `table seed`'s token — so the two seed items are removed together and the
        refusal is required to name one of them.
        """
        table = J.shared_matrix()
        fitted = J.shared_rating()
        record = J.run_record(table, fitted)
        items = [str(item) for item in J.protocol()["header"]]
        self.assertEqual(
            len(items),
            9,
            "protocol() declares nine header items (docs/L3/evaluation/"
            "declarations.md §2.1)",
        )
        tolerant = {J.token("seeds"), J.token("table seed")}
        for item in items:
            if J.token(item) in tolerant:
                continue
            with self.subTest(item=item):
                broken = J.clone(record)
                broken["header"] = {
                    key: value for key, value in broken["header"].items()
                    if J.token(key) != J.token(item)
                }
                message = self.assert_refusal(
                    "report",
                    [("header",)],
                    lambda broken=broken: J.report(J.RUNG, broken, table, fitted),
                    "a header missing the %r item" % (item,),
                )
                self.assertIn(
                    J.token(item),
                    J.token(message),
                    "the refusal names the missing header item "
                    "(docs/L3/evaluation/report.md §3 item 5): %r" % (message,),
                )
        both = J.clone(record)
        both["header"] = {
            key: value for key, value in both["header"].items()
            if J.token(key) not in tolerant
        }
        message = self.assert_refusal(
            "report",
            [("header",), ("seed",)],
            lambda: J.report(J.RUNG, both, table, fitted),
            "a header missing both seed items",
        )
        self.assertIn(
            "seed",
            J.token(message),
            "a header missing its seed items is refused naming one of them "
            "(docs/L3/evaluation/report.md §3 item 5): %r" % (message,),
        )


if __name__ == "__main__":
    unittest.main()
