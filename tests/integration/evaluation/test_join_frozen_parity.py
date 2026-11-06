"""JOIN-EVL-8 — frozen-pool parity (ASM-16, D-3, D-16).

D-3 keeps a rung to one axis and D-16 makes both arms of a pair train against one
frozen pool, so ASM-16's reading is a *join* invariant: one declaration yields one
ordered membership, one pool id and one read-back, and two arms prove they held
one pool by comparing the id alone (`docs/L1/league.md` §2, `docs/L1/assumptions.md`
ASM-16, `docs/L1/records.md` §8).  A pair of arms that recorded two different pool
ids is exactly what this family must be able to catch.  The pool's id is a
function of the ordered member ids and of nothing else, `build_pool` freezes what
the declaration says to freeze, `offer` refuses a frozen pool and `matrix` refuses
one that is not frozen (`docs/L2/evaluation/surface.md` §5, §7, §10,
`docs/L2/evaluation/pool.md` §4, `docs/L2/evaluation/league.md` §1).
"""

import importlib.util
import os
import random
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


class FrozenPoolParity(J.JoinCase):
    """One declaration, two arms, one id — and the refusals that keep it so."""

    def declaration(self, versions=None, m=None, frozen=True):
        return {
            "members": versions
            if versions is not None
            else [J.bare_version(J.VERSION_A, J.START_LABEL),
                  J.bare_version(J.VERSION_B, J.VERSION_A)],
            "m": J.league()["m"] if m is None else m,
            "frozen": frozen,
        }

    def test_join_evl_8_1_one_declaration_yields_one_id_and_one_read_back(self):
        """JOIN-EVL-8.1 a declaration built twice reads back byte-identically.

        `docs/L2/evaluation/surface.md` §5–§6 and `docs/L2/evaluation/pool.md` §4:
        one declaration yields one ordered member list and one id, and a pool reads
        back one record; the frozen read-back does not change while it is used,
        which is how a pair's parity is read (`docs/L1/records.md` §8, ASM-16).
        """
        first = J.build_pool(self.declaration())
        second = J.build_pool(self.declaration())
        readback_a = J.pool_members(first)
        readback_b = J.pool_members(second)
        self.assertEqual(
            readback_a["id"],
            readback_b["id"],
            "one declaration yields one pool id, whichever arm built it "
            "(docs/L2/evaluation/surface.md §5, ASM-16)",
        )
        self.assertEqual(
            J.canonical(readback_a),
            J.canonical(readback_b),
            "one declaration yields one byte-identical read-back, which is what "
            "two arms compare (docs/L2/evaluation/pool.md §5, ASM-16)",
        )
        self.assertEqual(
            str(readback_a["id"]),
            J.pool_id(J.names_of(readback_a)),
            "the id is a function of the ordered member ids and of nothing else "
            "(docs/L2/evaluation/pool.md §4, records.md §8)",
        )
        self.assertEqual(
            J.canonical(J.pool_members(first)),
            J.canonical(readback_a),
            "the pool has not changed while it is used: a frozen pool's read-back "
            "does not drift (docs/L2/evaluation/surface.md §6, ASM-16)",
        )

    def test_join_evl_8_2_the_id_changes_when_and_only_when_membership_does(self):
        """JOIN-EVL-8.2 the same ordered ids give the same id, a different set does not.

        `docs/L2/evaluation/pool.md` §4 excludes `m`, `frozen` and every other
        member field from the digest deliberately: a corrected `seed` or `step`
        does not rename the pool, and neither does a re-declared bound — while the
        id does change when the membership does (`docs/L2/evaluation/surface.md`
        §5, `docs/L1/records.md` §8).
        """
        same_members = [
            J.bare_version(J.VERSION_A, J.START_LABEL, step=1, samples=10, seed=111),
            J.bare_version(J.VERSION_B, J.VERSION_A, step=2, samples=20, seed=222),
        ]
        other_fields = [
            J.bare_version(J.VERSION_A, J.START_LABEL, step=9, samples=90, seed=999),
            J.bare_version(J.VERSION_B, J.VERSION_A, step=8, samples=80, seed=888),
        ]
        a = J.pool_members(J.build_pool(self.declaration(same_members, m=3)))
        b = J.pool_members(J.build_pool(self.declaration(other_fields, m=5,
                                                         frozen=False)))
        self.assertEqual(
            J.names_of(a),
            J.names_of(b),
            "the two declarations window to one ordered membership",
        )
        self.assertEqual(
            a["id"],
            b["id"],
            "a corrected seed, step or samples does not rename the pool, and "
            "neither does a re-declared bound or the frozen flag "
            "(docs/L2/evaluation/pool.md §4)",
        )
        grown = same_members + [J.bare_version(J.VERSION_C, J.VERSION_B)]
        c = J.pool_members(J.build_pool(self.declaration(grown)))
        self.assertNotEqual(
            a["id"],
            c["id"],
            "the id changes when the membership does (docs/L1/records.md §8, "
            "docs/L2/evaluation/league.md §1)",
        )
        self.assertEqual(
            str(c["id"]),
            J.pool_id(J.names_of(c)),
            "the changed id is still the digest of the new ordered ids "
            "(docs/L2/evaluation/pool.md §4)",
        )

    def test_join_evl_8_3_a_pool_that_may_change_is_not_a_table(self):
        """JOIN-EVL-8.3 `matrix` refuses an unfrozen pool and `offer` a frozen one.

        `docs/L2/evaluation/surface.md` §7 and §10 and `docs/L3/evaluation/matrix.md`
        §7: a frozen membership does not change while it is used, so `offer`
        refuses it; a pool that may still change would not be a table, so `matrix`
        refuses it before a single checkpoint is touched or a single hand is played
        (`docs/L2/evaluation/league.md` §1, ASM-16).
        """
        unfrozen = J.build_pool(self.declaration(frozen=False))
        frozen = J.build_pool(self.declaration(frozen=True))
        message = self.assert_refusal(
            "offer",
            [("frozen",)],
            lambda: J.offer(frozen, J.bare_version(J.VERSION_C, J.VERSION_B)),
            "offer into a frozen pool",
        )
        self.assertIn(
            "frozen",
            message.lower(),
            "the refusal names the frozen flag (docs/L2/evaluation/surface.md §7)",
        )
        stream = random.getstate()
        try:
            self.assert_refusal(
                "matrix",
                [("frozen",)],
                lambda: J.matrix(unfrozen, [J.variant_policy()], "live"),
                "matrix over an unfrozen pool",
            )
        finally:
            moved = random.getstate()
            random.setstate(stream)
        self.assertEqual(
            moved,
            stream,
            "a table refused for an unfrozen pool plays no hand, so it moves no "
            "stream (docs/L3/evaluation/matrix.md §7, ASM-2)",
        )
        for label in ("medium", "", "LIVE"):
            with self.subTest(label=label):
                self.assert_refusal(
                    "matrix",
                    [("live", "full", "label", "table")],
                    lambda label=label: J.matrix(frozen, [J.variant_policy()], label),
                    "matrix with the label %r" % (label,),
                )
        for variants in ([], [J.variant_policy(), J.variant_policy(),
                              J.variant_policy()]):
            with self.subTest(variants=len(variants)):
                self.assert_refusal(
                    "matrix",
                    [("variant",)],
                    lambda variants=variants: J.matrix(frozen, variants, "live"),
                    "matrix with %d variants" % (len(variants),),
                )
        self.assert_refusal(
            "matrix",
            [("variant",)],
            lambda: J.matrix(frozen, [42], "live"),
            "matrix with a non-callable variant",
        )

    def test_join_evl_8_4_the_reports_pool_family_is_the_id_the_matrix_names(self):
        """JOIN-EVL-8.4 report's pool family, read back, is the pool the table names.

        `docs/L2/evaluation/surface.md` §13 and `docs/L3/evaluation/report.md` §1
        item 2: the pool family is `records.md` §8's pool record, the shape
        `pool_members` returns; the matrix names the same pool by its id, so the
        report carries the record the table's id names (`docs/L2/evaluation/
        matrix.md` §5, docs/L1/records.md §8).
        """
        table = J.shared_matrix()
        record = J.run_record()
        assembled = J.report(J.RUNG, record, table, J.shared_rating())
        pool_family = J.family_of(assembled, "pool")
        self.assertEqual(
            J.canonical(pool_family),
            J.canonical(J.shared_pool_record()),
            "the report's pool family is the record pool_members returns "
            "(docs/L3/evaluation/report.md §1, docs/L2/evaluation/surface.md §13)",
        )
        self.assertEqual(
            pool_family["id"],
            table["pool"],
            "the pool family's id is the id the matrix names, so one pool is "
            "described once and used twice (docs/L1/records.md §8, ASM-16)",
        )
        self.assertEqual(
            set(J.matrix_members(table)) - {"variant-1"},
            set(J.names_of(pool_family)),
            "the pool family's members are the table's members but for the "
            "rung's variants (docs/L2/evaluation/league.md §3, report.md §3)",
        )

    def test_join_evl_8_5_two_ids_would_be_two_pools_and_are_caught(self):
        """JOIN-EVL-8.5 a pair of arms with two pool ids is exactly what this catches.

        `docs/L1/assumptions.md` ASM-16 and `docs/L2/evaluation/league.md` §1: a
        rung's pool is frozen before either arm trains, both arms record one pool
        id, and a pair that recorded two ids held two different oppositions.  The
        two declarations below differ by one version, so their ids must differ —
        the comparison an arm makes is the id alone (`docs/L1/records.md` §8).
        """
        one = [J.bare_version(J.VERSION_A, J.START_LABEL)]
        two = one + [J.bare_version(J.VERSION_E, J.VERSION_A)]
        arm_a = J.pool_members(J.build_pool(self.declaration(one)))
        arm_b = J.pool_members(J.build_pool(self.declaration(two)))
        self.assertNotEqual(
            arm_a["id"],
            arm_b["id"],
            "two memberships with two different versions are two pools, and the "
            "ids must say so (docs/L1/assumptions.md ASM-16, "
            "docs/L2/evaluation/pool.md §4)",
        )
        self.assertNotEqual(
            J.names_of(arm_a),
            J.names_of(arm_b),
            "the read-back distinguishes the two memberships the ids distinguish",
        )
        twin = J.pool_members(J.build_pool(self.declaration(one)))
        self.assertEqual(
            twin["id"],
            arm_a["id"],
            "the same one-arm membership built independently is one pool, so a "
            "pair that recorded one id held one pool (ASM-16, D-16)",
        )


if __name__ == "__main__":
    unittest.main()
