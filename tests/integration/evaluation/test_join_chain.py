"""JOIN-EVL-1 — the evidence chain end to end (D-16).

This is the one join the module exists for: a real checkpoint becomes a pool
member, the frozen pool and one variant become a real `live` matrix, the matrix
becomes a rating, and the rating travels beside a run record's seven evidence
families into a report (`docs/L2/evaluation/league.md` §7–§8,
`docs/L1/protocol.md` §1, `docs/L1/records.md` §7–§13, D-16).  No single module
can check the chain — `evaluation` supplies the pool, the scheduler, the matrix
and the rating, while the checkpoint and the policy come from `agents` and the
encoding from `features` — so each link is asserted against the declared record
the next link consumes.

The one real `live` table of this battery is built once in `_join_support` and
shared (`docs/L2/evaluation/league.md` §5, ASM-15); every other case in this
family reads it or builds a hand-written record for `rating` and `report`.
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


class EvidenceChain(J.JoinCase):
    """A checkpoint, a pool, a table, a rating and a report, in that order."""

    def test_join_evl_1_1_a_real_checkpoint_becomes_a_pool_member(self):
        """JOIN-EVL-1.1 the declaration's version is the checkpoint `agents.save` wrote.

        `docs/L2/evaluation/surface.md` §5 and `docs/L2/agents/surface.md` §9: a
        version is a `records.md` §7 record whose `path` is a checkpoint, and the
        pool read-back carries that record untouched beside the three pinned
        baselines (`docs/L2/evaluation/surface.md` §6, `docs/L2/evaluation/pool.md`
        §2–§5).  A member is loadable from its path alone, so the pool names a
        player, not a file name: `agents.load(None, path)` restores it and
        `evaluation.policy_from` decides as the learner that was saved
        (`docs/L1/protocol.md` §5).
        """
        info = J.checkpoint(J.CHECKPOINT_A, J.CHECKPOINT_SEED)
        record = J.version(J.VERSION_A, J.START_LABEL)
        self.assertTrue(
            os.path.exists(record["path"]),
            "the version record must name the checkpoint agents.save wrote "
            "(docs/L1/records.md §7): %r" % (record["path"],),
        )
        pool = J.build_pool(
            {"members": [record], "m": J.league()["m"], "frozen": True}
        )
        readback = J.pool_members(pool)
        names = J.names_of(readback)
        self.assertEqual(
            names,
            [str(name) for name in J.protocol()["baselines"]] + [J.VERSION_A],
            "a pool is the three pinned baselines first, then its versions "
            "(docs/L2/evaluation/pool.md §2, §5)",
        )
        carried = J.member_record(readback, J.VERSION_A)
        self.assertEqual(
            (str(carried["id"]), str(carried["path"]), str(carried["lineage"])),
            (J.VERSION_A, record["path"], J.START_LABEL),
            "the read-back carries the declaration's own record, its id, path and "
            "lineage untouched (docs/L2/evaluation/pool.md §5, docs/L1/records.md "
            "§7)",
        )
        restored = J.load(None, record["path"])
        self.assertEqual(
            J.param_count(restored),
            info["params"],
            "a member is loadable from its path alone, and its capacity is the "
            "saved learner's (docs/L2/agents/surface.md §9, §5)",
        )
        readouts = J.decisions_of(J.MATCH_SEED, J.caller)[:4]
        member = J.policy_from(record["path"])
        for position, (facts, legal) in enumerate(readouts):
            expected = J.decision_as_act(
                info["learner"], info["encoder"], facts, legal
            )
            self.assertEqual(
                J.descriptor_index(legal, member(facts, legal)),
                expected,
                "policy_from must decide as the learner the checkpoint was saved "
                "from (docs/L2/evaluation/surface.md §12, docs/L1/protocol.md §5), "
                "decision %d" % (position,),
            )

    def test_join_evl_1_2_the_frozen_pool_and_one_variant_make_one_table(self):
        """JOIN-EVL-1.2 `matrix(pool, [variant], "live")` is K(K−1)/2 real cells.

        `docs/L2/evaluation/surface.md` §10: membership is the pool's members in
        `pool_members`'s order and then the variant as `variant-1`, the cells are
        exactly K(K−1)/2 `records.md` §9 records, and the record carries the one
        hand count, the league's table seed and the budget label.  The pool is
        frozen before the table is played (`docs/L2/evaluation/league.md` §1).
        """
        table = J.shared_matrix()
        pool_names = J.names_of(J.shared_pool_record())
        members = J.matrix_members(table)
        self.assertEqual(
            members,
            pool_names + ["variant-1"],
            "the table's ordered membership is the pool read-back plus the "
            "variant named by its slot (docs/L2/evaluation/matrix.md §1, "
            "docs/L2/evaluation/surface.md §10)",
        )
        self.assertEqual(
            J.matrix_cell_count(table),
            J.cell_count(members),
            "the table carries exactly K(K−1)/2 cells, one per unordered pair "
            "(docs/L1/league.md §4, records.md §10)",
        )
        self.assertEqual(
            table["hands_per_cell"],
            J.league()["tables"]["live"]["hands_per_cell"],
            "every cell of a live table is played at the league's live hand count "
            "(docs/L2/evaluation/league.md §5, ASM-14)",
        )
        self.assertEqual(
            table["table_seed"],
            J.league()["table_seed"],
            "a table is played from the league's one table seed "
            "(docs/L2/evaluation/declarations.md §6, surface.md §10)",
        )
        self.assertEqual(
            table["table"],
            "live",
            "the record carries the budget it was asked for, `live` "
            "(records.md §10, docs/L2/evaluation/surface.md §10)",
        )
        self.assertEqual(
            table["pool"],
            J.shared_pool_record()["id"],
            "the table names the frozen pool it measured, by the pool record's id "
            "(docs/L2/evaluation/matrix.md §5, league.md §3)",
        )

    def test_join_evl_1_3_the_rating_names_exactly_the_tables_members(self):
        """JOIN-EVL-1.3 one value and a 95% interval for each member of the table.

        `docs/L2/evaluation/surface.md` §11 and `records.md` §11: the rating names
        one value per matrix member, each with its interval and the hands behind
        it, and it is a Bradley-Terry fit anchored by the three baselines
        (`docs/L1/league.md` §5, ASM-17).  A rating that named a member outside
        the table, or missed one inside it, would not describe the table it
        travelled with.
        """
        table = J.shared_matrix()
        fitted = J.shared_rating()
        self.assertEqual(
            set(J.rating_names(fitted)),
            set(J.matrix_members(table)),
            "the rating names exactly the table's members, no more and no fewer "
            "(records.md §11, docs/L2/evaluation/surface.md §11)",
        )
        behind = table["hands_per_cell"] * (len(J.matrix_members(table)) - 1)
        for member_id in J.matrix_members(table):
            entry = J.rating_values(fitted)[member_id]
            value = J.entry_value(entry)
            lower, upper = J.entry_interval(entry)
            self.assertTrue(
                J.finite(value) and J.finite(lower) and J.finite(upper),
                "a rating value and its interval must be finite numbers "
                "(records.md §11, docs/L2/evaluation/rating.md §3): %r" % (entry,),
            )
            self.assertLessEqual(
                lower,
                value,
                "the interval is widened so the fitted value lies inside it "
                "(docs/L2/evaluation/rating.md §4): %r" % (entry,),
            )
            self.assertGreaterEqual(
                upper,
                value,
                "the interval is widened so the fitted value lies inside it "
                "(docs/L2/evaluation/rating.md §4): %r" % (entry,),
            )
            self.assertEqual(
                J.entry_hands(entry),
                behind,
                "each member's value carries hands_per_cell × (K−1) hands "
                "(records.md §11, docs/L2/evaluation/rating.md §5)",
            )

    def test_join_evl_1_4_the_run_record_and_its_families_make_a_report(self):
        """JOIN-EVL-1.4 a complete record's report carries all seven families.

        `docs/L2/evaluation/surface.md` §13 and `docs/L1/protocol.md` §1: the
        report is keyed by the seven family names `protocol()` declares, in its
        order, each carrying what that family must carry and never reduced to a
        blank; the matrix and the rating the report is about are its own arguments
        (`docs/L3/evaluation/report.md` §1–§2).  The record is hand-built — `training`
        produces one, and this module never writes it — but every family's value is
        a shape the protocol declares (`records.md` §13, D-6).
        """
        table = J.shared_matrix()
        fitted = J.shared_rating()
        record = J.run_record(table, fitted)
        assembled = J.report(J.RUNG, record, table, fitted)
        declared = J.family_names()
        self.assertEqual(
            [name for name in declared if name in assembled],
            declared,
            "the report carries the seven families by the names protocol() spells, "
            "`axis row` included (docs/L3/evaluation/report.md §1, "
            "docs/L2/evaluation/surface.md §13)",
        )
        for name in declared:
            self.assertIsNotNone(
                J.family_of(assembled, name),
                "no family is reduced to a blank (record.md §13, D-6): %r"
                % (name,),
            )
            self.assertEqual(
                J.canonical(J.family_of(assembled, name)),
                J.canonical(record[name]),
                "the report copies a family by value and never reshapes it "
                "(docs/L3/evaluation/report.md §2): %r" % (name,),
            )
        self.assertEqual(
            J.canonical(J.family_of(assembled, "matrix")),
            J.canonical(table),
            "the report's matrix family is the matrix the report is about "
            "(docs/L3/evaluation/report.md §2, surface.md §13)",
        )
        self.assertEqual(
            J.canonical(J.family_of(assembled, "rating")),
            J.canonical(fitted),
            "the report's rating family is the rating the report is about "
            "(docs/L3/evaluation/report.md §2, surface.md §13)",
        )
        self.assertEqual(
            J.canonical(J.family_of(assembled, "pool")),
            J.canonical(J.shared_pool_record()),
            "the pool family is records.md §8's pool record, the shape "
            "pool_members returns (protocol.md §1, surface.md §13)",
        )

    def test_join_evl_1_5_the_chain_closes_on_one_membership(self):
        """JOIN-EVL-1.5 the pool family, the matrix and the rating name one membership.

        `docs/L2/evaluation/league.md` §3 and §7: the membership is the frozen pool
        plus the rung's variants, the rating is fitted over that one table, and the
        pool the run trained against is the pool the table measures — the join no
        single module can check (`docs/L2/evaluation/league.md` §8, D-16,
        ASM-16).
        """
        table = J.shared_matrix()
        fitted = J.shared_rating()
        assembled = J.report(
            J.RUNG, J.run_record(table, fitted), table, fitted
        )
        pool_family = J.family_of(assembled, "pool")
        self.assertEqual(
            J.matrix_members(J.family_of(assembled, "matrix")),
            J.names_of(pool_family) + ["variant-1"],
            "the report's matrix membership is its pool's read-back plus the "
            "variant (docs/L2/evaluation/league.md §3, docs/L3/evaluation/report.md "
            "§3)",
        )
        self.assertEqual(
            J.rating_names(J.family_of(assembled, "rating")),
            J.matrix_members(J.family_of(assembled, "matrix")),
            "the rating inside the report names exactly the matrix's members "
            "(records.md §11, docs/L2/evaluation/surface.md §13)",
        )
        self.assertEqual(
            pool_family["id"],
            J.family_of(assembled, "matrix")["pool"],
            "the pool the report names and the pool the table names are one pool, "
            "read by its id (records.md §8, ASM-16)",
        )
        for name in J.protocol()["baselines"]:
            self.assertIn(
                str(name),
                J.names_of(pool_family),
                "the report's pool carries the three baselines it actually had "
                "(docs/L2/evaluation/league.md §1, protocol.md §1)",
            )


if __name__ == "__main__":
    unittest.main()
