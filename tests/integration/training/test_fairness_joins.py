"""The lineage join -- TRNJ-5.

R2's declared pool is R1's retained window, and `fairness` is where the design
reads that inheritance back (`docs/L2/training/loop.md` §4, `docs/L3/training/
fairness.md` §5, `docs/L3/training/registry.md` §3): a rung's pool is the last M
versions of the rung it inherits plus the three baselines, so an *adjacent* pair's
two rungs cannot share one id -- R2's window contains R1's snapshots while R1's is
the baselines alone -- and `fairness` reports each arm's declared id, `same: None`,
and the membership the pair is compared *on*, which for R1-R2 is the three baselines
both windows hold (`docs/L1/league.md` §2, D-16, ASM-16, FAM-13).

Two rules are joined here that no single module can check: that the window R2
declares is literally the artefacts `training.checkpoints()` lists as R1's retained
snapshots, in lineage order and each a file the repository carries
(`docs/L3/training/checkpoints.md` §4-§5), and that the index is *declared* data
over `checkpoints/` and never a scan -- the battery's own run at an invented seed
writes checkpoints under the session's temporary write root (`tests/conftest.py`),
never there, and must not appear in the index (`docs/L2/training/surface.md` §7,
`docs/L2/training/write-root.md` §4, FAM-16.31).
"""

import importlib.util
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "training_join_support" in sys.modules:
    J = sys.modules["training_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "training_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["training_join_support"] = J
    _spec.loader.exec_module(J)


class LineageJoin(J.JoinCase):
    """TRNJ-5 -- R2's declared pool is R1's retained window."""

    def present_r1_snapshots(self):
        """R1's retained snapshots the repository actually carries, in index order.

        `docs/L3/training/registry.md` §3 step 1 drops every declared version whose
        `path` names no readable file, so a declared but absent lineage checkpoint
        leaves the window short and the record states the membership it used
        (`docs/L1/protocol.md` §5, `docs/L3/training/loop.md` §1 step 2).
        """
        return [
            entry for entry in J.entries()
            if str(entry["rung"]) == "R1" and str(entry["kind"]) == "snapshot"
            and os.path.exists(J.resolve(entry["path"]))
        ]

    def test_trnj_5_1_r1_and_r2_declare_different_pools(self):
        """TRNJ-5.1 the two rungs' declared pools differ in membership and in id.

        `docs/L3/training/loop.md` §4: "An *adjacent* pair's rungs cannot share one:
        a rung's pool is the previous rung's window, so R2's contains R1's snapshots
        while R1's is the baselines alone".  Both declare `m` = 5 and `frozen` =
        true, the league's M (`docs/L3/training/loop.md` §1, ASM-14), and R1 inherits
        no lineage at all (`docs/L1/league.md` §2, D-16).
        """
        r1_pool = J.pool_declaration_of(J.rung("R1"))
        r2_pool = J.pool_declaration_of(J.rung("R2"))
        self.assertEqual(
            J.pool_member_ids(r1_pool),
            [],
            "R1 inherits no lineage, so its declared window is empty and its pool is "
            "the three baselines alone (docs/L1/league.md §2, "
            "docs/L3/training/registry.md" " §3 step 1)",
        )
        self.assertEqual(
            int(r1_pool["m"]),
            int(J.league()["m"]),
            "every pool declares the league's M and no declaration exceeds it "
            "(docs/L3/training/loop.md §1, docs/L2/evaluation/league.md §1, "
            "ASM-14)",
        )
        for pool in (r1_pool, r2_pool):
            self.assertIs(
                bool(pool["frozen"]),
                True,
                "every rung's pool is frozen before its variants train "
                "(docs/L3/training/loop.md §1, ASM-16)",
            )
            self.assertEqual(int(pool["m"]), int(J.league()["m"]),
                             "M is the league's one bound (ASM-14)")
        self.assertNotEqual(
            str(r1_pool["id"]),
            str(r2_pool["id"]),
            "two different memberships yield two different ids, because the id is a "
            "function of the ordered member ids and of nothing else "
            "(docs/L2/evaluation/surface.md §5, docs/L1/records.md §8)",
        )
        if self.present_r1_snapshots():
            self.assertGreater(
                len(J.pool_member_ids(r2_pool)),
                0,
                "a rung whose predecessor's run ships inherits its retained window: "
                "R2's declared window is R1's last M snapshots "
                "(docs/L3/training/loop.md §1, "
                "docs/L3/training/registry.md §3)",
            )
        else:
            self.assertEqual(
                J.pool_member_ids(r2_pool),
                [],
                "a lineage checkpoint the repository does not carry leaves the "
                "window short, and an empty inherited window is stated and not "
                "invented (docs/L1/protocol.md §5, "
                "docs/L3/training/registry.md §3)",
            )
        self.assertNotEqual(
            set(J.pool_member_ids(r1_pool)),
            set(J.pool_member_ids(r2_pool)),
            "an adjacent pair's pools differ in membership, so the pair is compared "
            "on the membership both name and not on one pool "
            "(docs/L3/training/loop.md §4, D-16)",
        )

    def test_trnj_5_2_r2s_window_is_the_r1_snapshots_the_index_lists(self):
        """TRNJ-5.2 R2's declared version members are the index's R1 snapshots.

        `docs/L2/training/surface.md` §3: "The window is read from the shipped index
        §7 returns, and a lineage checkpoint the repository does not carry leaves the
        window short".  `docs/L3/training/checkpoints.md` §4 declares the index's
        order -- rung, variant, seed ascending, step ascending -- and §3 declares the
        window one chain in the recorded seed set's order, so the ids match and the
        members' lineages chain.  Where the shipped set is short the same case
        asserts the *rule* instead: the declaration is a subset of the index's R1
        snapshots, in lineage order, and each path is a file
        (`docs/L1/protocol.md` §5).
        """
        declared = J.pool_declaration_of(J.rung("R2"))["members"]
        present = self.present_r1_snapshots()
        index_ids = {str(entry["id"]) for entry in J.entries()}
        declared_ids = [str(member["id"]) for member in declared]
        self.assertEqual(
            len(set(declared_ids)),
            len(declared_ids),
            "a window names each version once (docs/L1/records.md" " §8, "
            "docs/L3/training/registry.md §3)",
        )
        self.assertTrue(
            set(declared_ids).issubset(index_ids),
            "every member of R2's declared window is an artefact the shipped index "
            "lists, because the window is read from the index and never from a "
            "directory (docs/L2/training/surface.md §3, §7, "
            "docs/L3/training/registry.md §3): %r"
            % (sorted(set(declared_ids) - index_ids),),
        )
        for member in declared:
            self.assertTrue(
                os.path.exists(J.resolve(member["path"])),
                "a declared window member names a readable checkpoint, which is what "
                "step 1's readability filter keeps "
                "(docs/L3/training/registry.md §3 step 1, "
                "docs/L1/protocol.md §5): %r" % (member["path"],),
            )
        if present:
            self.assertEqual(
                declared_ids,
                [str(entry["id"]) for entry in present],
                "R2's declared version members are exactly the artefacts the index "
                "lists as R1's retained snapshots, in lineage order, each a file the "
                "repository carries (docs/L2/training/surface.md §3, "
                "docs/L3/training/checkpoints.md §4-§5, FAM-12.5)",
            )
        else:
            self.assertEqual(
                declared_ids,
                [],
                "a declared window whose every path is absent leaves the pool at the "
                "baselines and whatever versions are present -- here, none "
                "(docs/L1/protocol.md §5, docs/L3/training/registry.md §3)",
            )
        for previous, following in zip(declared, declared[1:]):
            self.assertEqual(
                str(following["lineage"]),
                str(previous["id"]),
                "a window is ordered by lineage, each version descending from the one "
                "before it (docs/L1/records.md §7, "
                "docs/L3/training/checkpoints.md §3)",
            )
        if declared:
            self.assertNotIn(
                str(declared[0]["lineage"]),
                declared_ids,
                "the window's first version descends from its rung's own start and "
                "not from another member of the window "
                "(docs/L1/records.md §7, docs/L3/training/checkpoints.md §3)",
            )
        window = J.version_members(J.pool_of(J.window_run()))
        self.assertEqual(
            [str(member["id"]) for member in window],
            declared_ids[-int(J.league()["m"]):],
            "a declaration richer than the bound is windowed and not refused: the "
            "frozen pool holds the newest M of the declared chain, which is how a "
            "rung's retained versions become a five-version window "
            "(docs/L3/training/loop.md §7, docs/L2/evaluation/league.md §1, "
            "ASM-18, FAM-6)",
        )

    def test_trnj_5_3_fairness_reads_the_parity_pairs_one_pool(self):
        """TRNJ-5.3 `pool` reports `same: None`, both ids and the intersection.

        `docs/L2/training/surface.md` §5 and `docs/L3/training/fairness.md` §5: for
        an adjacent pair the two arms declare two ids, `same` is `None`, and
        `membership` is the intersection of the two windows in lineage order -- for
        R1-R2 the three baselines alone.  That intersection is what FAM-13's
        same-work check is played on, and `fairness` reports it and never labels the
        pair fair (D-3, D-6, `docs/L1/ladder.md` §5).
        """
        left = J.rung("R1")
        right = J.rung("R2")
        declared_pair = J.fairness(left, right)
        pool = declared_pair["pool"]
        self.assertIn(
            "pool",
            declared_pair,
            "a comparison reports the frozen pool it holds constant "
            "(docs/L2/training/surface.md §5)",
        )
        self.assertIsNone(
            pool["same"],
            "an adjacent pair declares no one pool id, because a rung's pool is its "
            "predecessor's window and R1's is the baselines alone "
            "(docs/L2/training/surface.md §5, docs/L3/training/fairness.md §5)",
        )
        self.assertEqual(
            sorted(str(value) for value in pool["ids"]),
            sorted([str(J.pool_declaration_of(left)["id"]),
                    str(J.pool_declaration_of(right)["id"])]),
            "the report names each arm's declared id, the id each run record will "
            "carry (docs/L2/training/surface.md §5, §3.1, "
            "docs/L3/training/fairness.md §5)",
        )
        self.assertEqual(
            [str(member) for member in pool["membership"]],
            J.baseline_names(),
            "the membership the pair is compared on is the intersection of the two "
            "windows -- R1's three baselines alone, which R2's window holds as well "
            "(docs/L3/training/fairness.md §5, docs/L1/league.md §2, FAM-13)",
        )
        self.assertEqual(
            int(pool["m"]),
            int(J.league()["m"]),
            "the reported bound is the league's M (ASM-14, "
            "docs/L3/training/fairness.md §5)",
        )
        self.assertIs(
            bool(pool["frozen"]),
            True,
            "both arms train against one frozen membership "
            "(docs/L2/training/surface.md §5, ASM-16)",
        )
        self.assertEqual(
            [str(name) for name in pool["baselines"]],
            J.baseline_names(),
            "the pool report names the three pinned baselines in the catalogue's "
            "order (docs/L3/training/fairness.md §5, "
            "docs/L2/agents/surface.md §11)",
        )
        self.assertEqual(
            [str(name) for name in declared_pair["pair"]],
            ["naive-numeric", "naive-numeric-torch"],
            "the pair is reported by its primary variants, because the primary is "
            "the lineage the next rung inherits "
            "(docs/L2/training/surface.md §5, docs/L3/training/fairness.md §1)",
        )

    def test_trnj_5_4_every_rungs_window_is_the_indexs_declared_data(self):
        """TRNJ-5.4 a window is index data, and the battery's run is not in it.

        `docs/L2/training/surface.md` §7 and `docs/L3/training/checkpoints.md` §4:
        the index is "declared data over `checkpoints/`, never a directory scan, so
        a scratch file the battery wrote is not a shipped artefact and is never
        listed".  Every rung's declared window is therefore a subset of the index's
        entries, chained by lineage, each path a file -- and the battery's own run at
        an invented seed, which writes under the session's write root (a temporary
        directory `tests/conftest.py` names through `PYPOKER_CHECKPOINT_ROOT`) and
        never under `<repo>/checkpoints/`, adds nothing to it
        (D-16, ASM-18, FAM-16.31).
        """
        index_ids = {str(entry["id"]) for entry in J.entries()}
        index_paths = {J.resolve(entry["path"]) for entry in J.entries()}
        for name in J.rung_order():
            declared = J.pool_declaration_of(J.rung(name))["members"]
            ids = [str(member["id"]) for member in declared]
            self.assertEqual(
                len(set(ids)),
                len(ids),
                "a rung's window names each version once "
                "(docs/L1/records.md §8, D-16): rung %r" % (name,),
            )
            self.assertTrue(
                set(ids).issubset(index_ids),
                "a rung's declared window is index data and never a directory "
                "listing (docs/L2/training/surface.md §7, "
                "docs/L3/training/checkpoints.md §4): rung %r names %r"
                % (name, sorted(set(ids) - index_ids)),
            )
            for member in declared:
                self.assertTrue(
                    os.path.exists(J.resolve(member["path"])),
                    "a window member names a readable checkpoint "
                    "(docs/L3/training/registry.md §3 step 1): %r"
                    % (member["path"],),
                )
            for previous, following in zip(declared, declared[1:]):
                self.assertEqual(
                    str(following["lineage"]),
                    str(previous["id"]),
                    "a window is one chain in lineage order "
                    "(docs/L3/training/checkpoints.md §3, docs/L1/records.md §7): "
                    "rung %r" % (name,),
                )
        record = J.small_run()
        own = []
        for variant, per_seed in record["checkpoints"].items():
            for seed, pair in per_seed.items():
                own.extend(str(path) for path in pair["snapshots"])
                own.append(str(pair["final"]))
        self.assertGreater(
            len(own),
            0,
            "a run writes ten snapshots and its final model per variant per seed "
            "(ASM-18, docs/L3/training/checkpoints.md §3)",
        )
        for path in own:
            self.assertNotIn(
                J.resolve(path),
                index_paths,
                "the battery's own run at seed %r writes under the session's write "
                "root, a temporary directory and not `<repo>/checkpoints/`, and the "
                "index lists no scratch path the design did not declare -- it is "
                "declared data and never a scan (docs/L2/training/surface.md §7, "
                "docs/L3/training/checkpoints.md §4, FAM-16.31)" % (J.RUN_SEED,),
            )


if __name__ == "__main__":
    unittest.main()
