"""JOIN-EVL-12 — the nine blind instances (`general` rows of `e2e-surface.md` §5).

Every instance in this family is the battery's own and appears in no design
document and in no case of `tests/e2e/`: the version ids `version-goshawk`,
`version-dunlin`, `version-plover`, `version-wigeon`, `version-snipe` and
`version-curlew`; the lineage start `R9/start`; the unregistered rung label `R9`;
the learner seeds `58391`, `52861`, `46103`, `33907`, `90733`, `27739` and the
variant seed `66413`; the cell seeds `62077`, `71549`, `80231`; the draw multiple
`7919`; the cell sizes `2`, `4`, `7`, `9`, `10` and `12`; and the hand-built
table's seed `84673` (`docs/L1/battery.md` §4, D-15, `docs/L1/e2e-surface.md`
§5).  A blind instance is driven through the declared entry point alone — no case
here reads a private name — and every learned object it plays is built by the
module that owns it.
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


class BlindInstances(J.JoinCase):
    """One invented instance for each of the nine `general` rows."""

    def decisions(self):
        return J.decisions_of(J.MATCH_SEED, J.caller)[:3]

    def two_version_pool(self):
        record_a = J.version(J.VERSION_A, J.START_LABEL)
        record_b = J.version(J.VERSION_B, J.VERSION_A,
                             J.CHECKPOINT_B, J.CHECKPOINT_SEED_B)
        return J.build_pool(
            {"members": [record_a, record_b], "m": J.league()["m"], "frozen": True}
        )

    def test_join_evl_12_1_build_pool_windows_an_invented_declaration(self):
        """JOIN-EVL-12.1 an invented four-link lineage is windowed to a tighter bound.

        `docs/L2/evaluation/surface.md` §5 and `docs/L2/evaluation/league.md` §1: a
        declaration may carry a tighter `m` than the league's M and a declaration
        richer than the bound is windowed to its newest versions, never refused
        (`docs/L2/evaluation/pool.md` §2, docs/L1/league.md §2).  The chain and the
        bound are the battery's own.
        """
        chain = [
            J.bare_version(J.VERSION_A, J.START_LABEL),
            J.bare_version(J.VERSION_B, J.VERSION_A),
            J.bare_version(J.VERSION_C, J.VERSION_B),
            J.bare_version(J.VERSION_D, J.VERSION_C),
        ]
        pool = J.build_pool({"members": chain, "m": 3, "frozen": True})
        readback = J.pool_members(pool)
        self.assertEqual(
            int(readback["m"]),
            3,
            "the read-back gives the bound the pool holds to "
            "(records.md §8, docs/L2/evaluation/surface.md §6)",
        )
        self.assertEqual(
            J.names_of(readback),
            [str(name) for name in J.protocol()["baselines"]]
            + [J.VERSION_B, J.VERSION_C, J.VERSION_D],
            "a declaration richer than the bound is windowed to its last m "
            "versions, oldest to newest (docs/L2/evaluation/pool.md §2, §3, "
            "docs/L2/evaluation/league.md §1)",
        )
        self.assertEqual(
            str(readback["id"]),
            J.pool_id(J.names_of(readback)),
            "the invented pool's id is the digest of its ordered ids "
            "(docs/L2/evaluation/pool.md §4)",
        )

    def test_join_evl_12_2_pool_members_reads_an_invented_membership_back(self):
        """JOIN-EVL-12.2 an invented two-version pool reads back in lineage order.

        `docs/L2/evaluation/surface.md` §6 and `records.md` §8: the read-back is the
        three baselines first, in `agents.baselines()`'s order, each marked pinned
        with the declared zero, then the version window oldest to newest, each the
        §7 record the declaration carried — the id, the lineage and the checkpoint
        path included (`docs/L2/evaluation/pool.md` §5).
        """
        record_a = J.version(J.VERSION_A, J.START_LABEL)
        record_b = J.version(J.VERSION_B, J.VERSION_A,
                             J.CHECKPOINT_C, J.CHECKPOINT_SEED_C)
        readback = J.pool_members(
            J.build_pool(
                {"members": [record_a, record_b], "m": J.league()["m"],
                 "frozen": True}
            )
        )
        self.assertTrue(
            bool(readback["frozen"]),
            "the read-back carries the frozen flag (records.md §8, ASM-16)",
        )
        self.assertEqual(
            J.names_of(readback),
            [str(name) for name in J.protocol()["baselines"]]
            + [J.VERSION_A, J.VERSION_B],
            "the versions read back in lineage order, oldest first "
            "(docs/L2/evaluation/pool.md §3, §5)",
        )
        for expected in (record_a, record_b):
            carried = J.member_record(readback, expected["id"])
            for key in ("id", "path", "lineage", "seed", "step", "samples"):
                self.assertEqual(
                    carried.get(key),
                    expected[key],
                    "a version reads back as the records.md §7 record the "
                    "declaration carried, key %r (docs/L2/evaluation/pool.md §5)"
                    % (key,),
                )
        for name in J.protocol()["baselines"]:
            record = J.member_record(readback, str(name))
            self.assertEqual(
                int(record["params"]),
                0,
                "a baseline's read-back params is the declared zero "
                "(docs/L2/evaluation/surface.md §6, ASM-10)",
            )

    def test_join_evl_12_3_offer_rolls_an_invented_window(self):
        """JOIN-EVL-12.3 an invented offer extends the window and evicts one version.

        `docs/L2/evaluation/surface.md` §7: a version joins the window at its head
        and the oldest leaves when the window holds `m`, the baselines are
        untouched, the id is recomputed and the argument pool is unchanged
        (`docs/L2/evaluation/pool.md` §6, ASM-18).  The offered version's lineage
        must be the window's newest member, or the offer is refused
        (`docs/L1/league.md` §2).
        """
        pool = J.build_pool(
            {
                "members": [J.bare_version(J.VERSION_A, J.START_LABEL),
                            J.bare_version(J.VERSION_B, J.VERSION_A)],
                "m": 2,
                "frozen": False,
            }
        )
        before = J.pool_members(pool)
        message = self.assert_refusal(
            "offer",
            [("lineage",), (J.VERSION_B,)],
            lambda: J.offer(pool, J.bare_version(J.VERSION_C, J.START_LABEL)),
            "an offer whose lineage is not the window's newest version",
        )
        self.assertIn(
            J.VERSION_B.lower(),
            message.lower(),
            "the refusal names the lineage it had to extend "
            "(docs/L2/evaluation/pool.md §6): %r" % (message,),
        )
        advanced = J.pool_members(J.offer(
            pool, J.bare_version(J.VERSION_D, J.VERSION_B)
        ))
        self.assertEqual(
            J.names_of(advanced),
            [str(name) for name in J.protocol()["baselines"]]
            + [J.VERSION_B, J.VERSION_D],
            "the offered version joins at the head and the oldest leaves "
            "(docs/L2/evaluation/surface.md §7, ASM-18)",
        )
        self.assertEqual(
            J.canonical(J.pool_members(pool)),
            J.canonical(before),
            "offer returns a new pool and leaves its argument unchanged "
            "(docs/L2/evaluation/surface.md §7)",
        )
        self.assertEqual(
            str(advanced["id"]),
            J.pool_id(J.names_of(advanced)),
            "the advanced pool's id is the digest of its new ordered membership "
            "(docs/L2/evaluation/pool.md §6)",
        )

    def test_join_evl_12_4_opponent_draws_each_invented_member_by_position(self):
        """JOIN-EVL-12.4 the invented draw seeds visit every member by `seed % n`.

        `docs/L2/evaluation/surface.md` §8 and `docs/L2/evaluation/pool.md` §7: the
        draw is the seed reduced modulo the membership's size, so `n` consecutive
        residues visit each member once and a spread of seeds samples the whole pool
        rather than one fixed policy (`docs/L3/evaluation/scheduler.md` §3, FAM-7).
        A baseline is `agents.build_baseline(name, seed)`; a version is its
        checkpoint's policy at the container's seed.
        """
        pool = self.two_version_pool()
        readback = J.pool_members(pool)
        names = J.names_of(readback)
        self.assertEqual(len(names), 5, "three baselines and two invented versions")
        decisions = self.decisions()
        baselines = [str(name) for name in J.protocol()["baselines"]]
        seen = set()
        for position, member_id in enumerate(names):
            with self.subTest(position=position, member=member_id):
                seed = position + len(names) * J.DRAW_MULTIPLE
                drawn = J.opponent(pool, seed)
                self.assertIn(
                    seed % len(names),
                    range(len(names)),
                    "the draw is the seed reduced modulo the membership's size "
                    "(docs/L2/evaluation/pool.md §7)",
                )
                if member_id in baselines:
                    expected = J.build_baseline(member_id, seed)
                    where = "agents.build_baseline at the caller's seed"
                else:
                    expected = J.policy_from(
                        J.member_record(readback, member_id)["path"]
                    )
                    where = "the checkpoint's own recorded seed"
                for facts, legal in decisions:
                    self.assertEqual(
                        J.descriptor_index(legal, drawn(facts, legal)),
                        J.descriptor_index(legal, expected(facts, legal)),
                        "the member at position %d must be the policy %r at %s "
                        "(docs/L2/evaluation/surface.md §8, "
                        "docs/L2/evaluation/pool.md §7)"
                        % (position, member_id, where),
                    )
                seen.add(J.decision_signature(drawn, decisions))
        self.assertGreater(
            len(seen),
            1,
            "a spread of seeds samples the whole pool and not one fixed policy "
            "(docs/L2/evaluation/surface.md §8, FAM-7)",
        )

    def test_join_evl_12_5_match_plays_an_invented_cell(self):
        """JOIN-EVL-12.5 an invented hand count and seed make one sound cell.

        `docs/L2/evaluation/surface.md` §9 and `records.md` §9: `match` returns the
        two ids in argument order, the hand count, two directions whose counts sum
        to it, the parameter counts and the seed it was played at — and a version
        member's count is measured (`docs/L2/evaluation/scheduler.md` §5).
        """
        cell = J.match("random", "always-call", J.HANDS_TEN, J.MATCH_SEED_OTHER)
        self.assertEqual(
            (J.cell_members(cell), int(cell["hands"]), int(cell["seed"])),
            (["random", "always-call"], J.HANDS_TEN, J.MATCH_SEED_OTHER),
            "a cell names its members by id, its hand count and its seed "
            "(records.md §9)",
        )
        for member_id in J.cell_members(cell):
            wins, ties, losses = J.counts_of(J.direction_for(cell, member_id))
            self.assertEqual(
                wins + ties + losses,
                J.HANDS_TEN,
                "each direction accounts for the invented hand count "
                "(records.md §9, docs/L1/league.md §3)",
            )
        version = J.version(J.VERSION_E, J.START_LABEL,
                            J.CHECKPOINT_E, J.CHECKPOINT_SEED_E)
        measured = J.match("always-call", version, J.HANDS_FOUR, J.MATCH_SEED)
        self.assertEqual(
            [int(count) for count in measured["params"]],
            [0, J.param_count(J.checkpoint(J.CHECKPOINT_E,
                                          J.CHECKPOINT_SEED_E)["learner"])],
            "the invented version's cell records agents.param_count of its "
            "learner (records.md §9, docs/L2/evaluation/surface.md §2, ASM-10)",
        )

    def test_join_evl_12_6_matrix_of_the_invented_membership(self):
        """JOIN-EVL-12.6 the shared real table is over the invented membership.

        `docs/L2/evaluation/surface.md` §10 and `docs/L2/evaluation/matrix.md` §1:
        a variant is named `variant-1` by the slot it was handed in whatever it
        carries, the pool is frozen, and the table plays one cell per pair at the
        league's live cell size.  The membership this table measures — one invented
        version against one invented variant, beside the pinned baselines — appears
        in no design document (`docs/L1/battery.md` §4, D-15).
        """
        table = J.shared_matrix()
        readback = J.shared_pool_record()
        members = J.matrix_members(table)
        self.assertIn(
            J.VERSION_A,
            members,
            "the invented version is a table member "
            "(docs/L2/evaluation/matrix.md §1)",
        )
        self.assertEqual(
            members[-1],
            "variant-1",
            "the variant is named by its slot, whatever the policy carries "
            "(docs/L2/evaluation/matrix.md §1, docs/L2/evaluation/surface.md §10)",
        )
        self.assertEqual(
            len(members),
            len(J.names_of(readback)) + 1,
            "K is the frozen pool's size plus the one variant "
            "(docs/L1/league.md §4, ASM-14)",
        )
        self.assertEqual(
            J.matrix_cell_count(table),
            J.cell_count(members),
            "the invented table carries K(K−1)/2 cells "
            "(docs/L2/evaluation/league.md §3)",
        )
        self.assertEqual(
            int(table["hands_per_cell"]),
            int(J.league()["tables"]["live"]["hands_per_cell"]),
            "a live table is played at the league's live cell size "
            "(docs/L2/evaluation/league.md §5, ASM-14)",
        )
        self.assertEqual(
            str(table["pool"]),
            str(readback["id"]),
            "the table names the invented pool it measured "
            "(docs/L2/evaluation/matrix.md §5)",
        )

    def test_join_evl_12_7_rating_of_an_invented_hand_built_table(self):
        """JOIN-EVL-12.7 an invented table is rated from its record alone.

        `docs/L2/evaluation/surface.md` §11 and `docs/L2/evaluation/rating.md` §1:
        what is checked is the record and not its provenance, so a hand-built table
        at an invented cell size and table seed is rated as readily as a played one
        — one value and a 95% interval per member, anchored so the baselines' mean
        is 0, the bootstrap seeded from that table's own seed (ASM-17).
        """
        table = J.hand_built_matrix()
        fitted = J.rating(table)
        self.assertEqual(
            int(table["hands_per_cell"]),
            J.HANDS_SEVEN,
            "the invented table's cell size differs from both league budgets",
        )
        self.assertEqual(
            int(table["table_seed"]),
            J.HAND_BUILT_TABLE_SEED,
            "the invented table carries its own table seed",
        )
        self.assertEqual(
            set(J.rating_names(fitted)),
            set(J.matrix_members(table)),
            "the rating names exactly the hand-built table's members "
            "(records.md §11, docs/L2/evaluation/surface.md §11)",
        )
        names = [str(name) for name in J.protocol()["baselines"]]
        mean = sum(
            J.entry_value(J.rating_values(fitted)[name]) for name in names
        ) / len(names)
        self.assertAlmostEqual(
            mean,
            0.0,
            places=9,
            msg="the baselines' mean is 0 on a hand-built table too "
                "(docs/L2/evaluation/league.md §4, ASM-17)",
        )
        behind = J.HANDS_SEVEN * (len(J.matrix_members(table)) - 1)
        for member_id, entry in J.rating_values(fitted).items():
            self.assertEqual(
                J.entry_hands(entry),
                behind,
                "each value carries hands_per_cell × (K−1) hands on the invented "
                "table (records.md §11, FAM-9.5)",
            )
        self.assertEqual(
            int(fitted["bootstrap_seed"]),
            J.bootstrap_seed(J.HAND_BUILT_TABLE_SEED),
            "the bootstrap is seeded from the invented table's own seed "
            "(docs/L3/evaluation/rating.md §4, ASM-17)",
        )
        self.assertIsInstance(
            bool(fitted["converged"]),
            bool,
            "the fit records its convergence (records.md §11)",
        )

    def test_join_evl_12_8_policy_from_an_invented_checkpoint(self):
        """JOIN-EVL-12.8 an invented checkpoint is a policy that decides as its learner.

        `docs/L2/evaluation/surface.md` §12 and `docs/L2/agents/surface.md` §10: the
        policy is `agents.as_policy` of the restored learner over the encoder the
        checkpoint's encoding name builds, at the seed the checkpoint records, so it
        answers what `agents.act` answers and answers one decision one way
        (`docs/L1/protocol.md` §5).
        """
        info = J.checkpoint(J.CHECKPOINT_F, J.CHECKPOINT_SEED_F)
        member = J.policy_from(info["path"])
        for position, (facts, legal) in enumerate(self.decisions()):
            expected = J.decision_as_act(
                info["learner"], info["encoder"], facts, legal
            )
            chosen = member(facts, legal)
            self.assertEqual(
                J.descriptor_index(legal, chosen),
                expected,
                "an invented checkpoint's policy decides as its learner does "
                "(docs/L2/evaluation/surface.md §12, docs/L1/protocol.md §5), "
                "decision %d" % (position,),
            )
            self.assertEqual(
                member(facts, legal),
                chosen,
                "a policy answers one decision one way, because only the deal uses "
                "the global stream (docs/L2/evaluation/surface.md §8, ASM-2)",
            )

    def test_join_evl_12_9_report_an_untitled_rung_over_an_invented_table(self):
        """JOIN-EVL-12.9 an unregistered label reports the invented table as data.

        `docs/L2/evaluation/surface.md` §13 and `docs/L1/ladder.md` §1: a rung is
        data and not a registry entry, so the report carries the label it was given;
        the seven families are the record's, the pool family names the hand-built
        membership, and the rating names the matrix's members
        (`docs/L3/evaluation/report.md` §2–§3).
        """
        table = J.hand_built_matrix()
        fitted = J.rating(table)
        pool_record = J.hand_built_pool_record()
        record = J.run_record(table, fitted, pool_record)
        label = "R9-narrow-invented"
        assembled = J.report(label, record, table, fitted)
        self.assertEqual(
            assembled["rung"],
            label,
            "the report carries an unregistered configuration's own label "
            "(docs/L3/evaluation/report.md §2, ladder.md §1)",
        )
        for name in J.family_names():
            self.assertIsNotNone(
                J.family_of(assembled, name),
                "the invented rung's report carries the %r family "
                "(docs/L1/protocol.md §1, D-6)" % (name,),
            )
        self.assertEqual(
            J.canonical(J.family_of(assembled, "pool")),
            J.canonical(pool_record),
            "the pool family is the hand-built membership the record names "
            "(docs/L2/evaluation/surface.md §13, records.md §8)",
        )
        self.assertEqual(
            int(assembled["table seed"]),
            J.HAND_BUILT_TABLE_SEED,
            "the report carries the invented table's seed "
            "(docs/L3/evaluation/report.md §2)",
        )

    def test_join_evl_12_10_the_joins_refusals_at_invented_instances(self):
        """JOIN-EVL-12.10 the joins' refusals name what they refused.

        `docs/L2/evaluation/surface.md` §5, §8, §9 and §11 and
        `docs/L3/evaluation/errors.md` §3: a bound above the league's M names the
        bound, a non-integer draw seed names the seed, a non-positive hand count
        names the count, and a table missing one of the three baselines names the
        missing anchor — each refused before anything is built and each naming the
        entry point, the argument and the offending value.
        """
        self.assert_refusal(
            "build_pool",
            [("m", "bound", "5")],
            lambda: J.build_pool(
                {"members": [], "m": J.league()["m"] + 1, "frozen": True}
            ),
            "a declaration above the league's M",
        )
        pool = J.shared_pool()
        self.assert_refusal(
            "opponent",
            [("seed",)],
            lambda: J.opponent(pool, "8086"),
            "a draw seed that is not an integer",
        )
        self.assert_refusal(
            "match",
            [("hand",)],
            lambda: J.match("random", "always-call", 0, J.MATCH_SEED),
            "a hand count of zero",
        )
        missing = J.hand_matrix(
            ["always-call", "oracle", J.VERSION_A, "variant-1"],
            [(2, 0, 5), (2, 0, 5), (2, 1, 4), (2, 0, 5), (2, 0, 5), (3, 0, 4)],
            J.HANDS_SEVEN,
            J.HAND_BUILT_TABLE_SEED,
        )
        message = self.assert_refusal(
            "rating",
            [("random", "baseline", "anchor")],
            lambda: J.rating(missing),
            "a table missing the random baseline",
        )
        self.assertIn(
            "random",
            message.lower(),
            "the refusal names the missing baseline it cannot anchor on "
            "(docs/L3/evaluation/rating.md §6, docs/L1/protocol.md §3): %r"
            % (message,),
        )


if __name__ == "__main__":
    unittest.main()
