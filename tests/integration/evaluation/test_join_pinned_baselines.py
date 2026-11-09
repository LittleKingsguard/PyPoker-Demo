"""JOIN-EVL-3 — the pinned baselines, and the folders a declaration may add (D-6, D-21).

`agents.baselines()` names six — D-6's three, which are the catalogue's `anchor: True`
members, and D-21's three folders.  `evaluation`'s pool always holds the flagged three,
never evicts them, and draws a baseline at the caller's seed, so a baseline column is the
same rule at every call order and no cell's opponent drifts while the table is played;
a folder joins pinned, after them and in the catalogue's order, when — and only when — the
membership declaration names it (`docs/L2/evaluation/league.md` §1, `docs/L2/evaluation/
pool.md` §1, `docs/L1/records.md` §8, `docs/L1/league.md` §2, ASM-32, D-21).
"""

import importlib.util
import json
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
    J = sys.modules["evaluation_join_support"]
    _spec.loader.exec_module(J)


class PinnedBaselines(J.JoinCase):
    """The catalogue's six names, its flagged three, and the declaration that admits one."""

    def catalogue(self):
        return J.baselines()

    def names(self):
        """The catalogue's `anchor: True` members, in its order (ASM-32, D-21)."""
        declared = self.catalogue()
        return [str(name) for name, record in declared.items() if record.get("anchor")]

    def folders(self):
        """The catalogue's folding baselines, in its order (D-21)."""
        declared = self.catalogue()
        return [
            str(name) for name, record in declared.items() if not record.get("anchor")
        ]

    def test_join_evl_3_1_the_catalogues_pinned_three_are_every_pools_first_three(self):
        """JOIN-EVL-3.1 the pool's first baseline ids are the catalogue's flagged three.

        `docs/L2/evaluation/pool.md` §1 and `docs/L2/evaluation/surface.md` §6:
        the three anchor baselines are added first, in `agents.baselines()`'s order,
        each marked pinned with the `params` of `0` the catalogue declares — in
        every pool, R1's baselines-only pool included (`docs/L2/evaluation/league.md`
        §1, `docs/L1/league.md` §2, ASM-16, ASM-32).
        """
        catalogue = self.names()
        self.assertEqual(
            catalogue,
            ["random", "always-call", "oracle"],
            "agents.baselines() flags the three names of D-6 and no other "
            "(docs/L2/agents/surface.md §11, ASM-32)",
        )
        self.assertEqual(
            [str(name) for name in self.catalogue()],
            catalogue + self.folders(),
            "the catalogue is the anchored three and then D-21's three folders, in its "
            "own order (docs/L1/protocol.md §3, D-21)",
        )
        empty = J.build_pool({"members": [], "m": J.league()["m"], "frozen": True})
        pools = {
            "the baselines-only pool": J.pool_members(empty),
            "the shared versioned pool": J.shared_pool_record(),
        }
        for where, readback in pools.items():
            with self.subTest(pool=where):
                self.assertEqual(
                    J.names_of(readback)[:3],
                    catalogue,
                    "%s must carry the catalogue's three pinned baselines first, in its "
                    "order (docs/L2/evaluation/pool.md §1, surface.md §6)"
                    % (where,),
                )
                for name in catalogue:
                    record = J.member_record(readback, name)
                    self.assertEqual(
                        int(J.declared_params(name)),
                        0,
                        "a baseline declares no trainable parameter "
                        "(docs/L2/agents/surface.md §11, ASM-10)",
                    )
                    self.assertEqual(
                        int(record["params"]),
                        J.declared_params(name),
                        "a baseline member's params is the zero the catalogue "
                        "declares (docs/L2/evaluation/surface.md §6, ASM-10)",
                    )
                    self.assertTrue(
                        bool(record.get("pinned")),
                        "the baselines are pinned in every pool "
                        "(docs/L2/evaluation/pool.md §1, D-16)",
                    )
                self.assertEqual(
                    J.names_of(readback)[:3],
                    [name for name in J.names_of(readback) if name in catalogue],
                    "a pool that declares no folder holds the three anchors and no "
                    "other baseline (docs/L1/records.md §8, ASM-32, D-21): %r"
                    % (J.names_of(readback),),
                )

    def test_join_evl_3_5_a_declaration_admits_a_folder_pinned_after_the_anchors(self):
        """JOIN-EVL-3.5 a declaration's `baselines` key pins the folders it names after
        the anchor three, and a declaration that names none keeps its membership, its
        order and its id — the id the two shipped artefacts record.

        `docs/L1/records.md` §8 makes `baselines` an optional key of the membership
        declaration, `docs/L2/evaluation/pool.md` §1 makes a declared folder join pinned
        in the catalogue's order, and `docs/L1/league.md` §2 / ASM-32 make a folder a
        member and never an anchor — so the shipped pools, which declare no folder, cannot
        move (D-21).
        """
        anchored = J.build_pool({"members": [], "m": J.league()["m"], "frozen": True})
        baseline_record = J.pool_members(anchored)
        declared = self.folders()
        self.assertGreaterEqual(
            len(declared), 3, "the catalogue carries D-21's three folders (D-21)"
        )
        self.assertEqual(
            J.names_of(baseline_record),
            self.names(),
            "a declaration naming no folder holds the three anchors alone "
            "(docs/L1/records.md §8, ASM-32): %r" % (J.names_of(baseline_record),),
        )
        named = J.build_pool(
            {
                "members": [],
                "m": J.league()["m"],
                "frozen": True,
                "baselines": [declared[-1], declared[0]],
            }
        )
        admitted = J.pool_members(named)
        self.assertEqual(
            J.names_of(admitted),
            self.names() + [declared[0], declared[-1]],
            "the declared folders join after the three anchors, in the catalogue's order "
            "and not the declaration's (docs/L2/evaluation/pool.md §1, ASM-32, D-21): %r"
            % (J.names_of(admitted),),
        )
        for name in (declared[0], declared[-1]):
            with self.subTest(folder=name):
                record = J.member_record(admitted, name)
                self.assertTrue(
                    bool(record.get("pinned")),
                    "a declared folder is pinned like any baseline: eviction is the "
                    "version window's (docs/L1/league.md §2, ASM-32, D-21): %r"
                    % (record,),
                )
                self.assertEqual(
                    int(record["params"]),
                    0,
                    "a folder declares no trainable parameter (records.md §9, ASM-10)",
                )
        self.assertNotIn(
            declared[1],
            J.names_of(admitted),
            "a folder the declaration does not name is not a member: the catalogue's "
            "names join by declaration and never silently (records.md §8, ASM-32, D-21): "
            "%r" % (J.names_of(admitted),),
        )
        self.assertNotEqual(
            str(admitted["id"]),
            str(baseline_record["id"]),
            "the id changes when and only when the membership does, so a pool that "
            "admits a folder wears a different one (records.md §8, ASM-27, D-21)",
        )

    def test_join_evl_3_6_a_declaration_naming_no_folder_keeps_the_shipped_pool_id(self):
        """JOIN-EVL-3.6 the anchors-only declaration digests to the id the shipped artefact records.

        `docs/L1/records.md` §8 and ASM-27: a baseline's line of the digest is its bare
        id, so a declaration that names no folder is the same payload it was before D-21 —
        which is why `tables/league-full.json` and `checkpoints/evidence/r1-live.json`
        keep the pool ids they record (`docs/L1/protocol.md` §5, D-21).
        """
        self.assertTrue(
            os.path.exists(J.SHIPPED_PATH),
            "the shipped `full` table is the file whose pool id this case reads "
            "(docs/L1/league.md` §9, D-8): %r" % (J.SHIPPED_PATH,),
        )
        with open(J.SHIPPED_PATH, "r", encoding="utf-8") as handle:
            shipped = json.load(handle)
        anchored = J.build_pool({"members": [], "m": J.league()["m"], "frozen": True})
        readback = J.pool_members(anchored)
        self.assertEqual(
            str(readback["id"]),
            str(shipped["pool"]["id"]),
            "a declaration that names no folder yields the id the shipped artefact "
            "records, so neither shipped pool id changed (docs/L1/records.md §8, "
            "docs/L1/protocol.md §5, ASM-27, D-21): %r against %r"
            % (readback["id"], shipped["pool"]["id"]),
        )
        self.assertEqual(
            J.names_of(readback),
            [str(member["id"]) for member in shipped["pool"]["members"]],
            "and the same ordered membership (docs/L1/records.md §8, ASM-32)",
        )

    def test_join_evl_3_7_an_unknown_declared_baseline_is_refused_by_name(self):
        """JOIN-EVL-3.7 a `baselines` name the catalogue does not carry is refused by name.

        `docs/L1/records.md` §8: the declaration admits the catalogue's names and nothing
        else, so a name outside it is a row this module could not build and the refusal
        names it (`docs/L2/evaluation/pool.md` §1, `docs/L3/evaluation/errors.md` §4,
        ASM-32, D-21).
        """
        for invented in ("fold-on-a-pair", "oracle-plus", "always-fold"):
            with self.subTest(name=invented):
                with self.assertRaises(Exception) as caught:
                    J.build_pool(
                        {
                            "members": [],
                            "m": J.league()["m"],
                            "frozen": True,
                            "baselines": [invented],
                        }
                    )
                message = str(caught.exception)
                self.assertIn(
                    invented,
                    message,
                    "the refusal names the baseline it could not admit "
                    "(docs/L3/evaluation/errors.md §3, D-21): %r" % (message,),
                )
                self.assertIn(
                    "build_pool",
                    message,
                    "the refusal names the entry point at fault "
                    "(docs/L3/evaluation/errors.md` §3): %r" % (message,),
                )

    def test_join_evl_3_2_offer_never_evicts_a_baseline(self):
        """JOIN-EVL-3.2 `offer` drops the oldest version and nothing else.

        `docs/L2/evaluation/surface.md` §7 and `docs/L2/evaluation/pool.md` §6: a
        version joins the window at its head, the oldest version leaves when the
        window already holds `m`, the baselines are untouched and the id is
        recomputed (`docs/L1/league.md` §2, ASM-18).  The invented window holds two
        versions at `m = 2`, so the third offer must evict exactly the first.
        """
        first = J.bare_version(J.VERSION_A, J.START_LABEL)
        second = J.bare_version(J.VERSION_B, J.VERSION_A)
        third = J.bare_version(J.VERSION_C, J.VERSION_B)
        pool = J.build_pool({"members": [first, second], "m": 2, "frozen": False})
        before = J.pool_members(pool)
        advanced = J.offer(pool, third)
        after = J.pool_members(advanced)
        self.assertEqual(
            J.names_of(before)[:3],
            self.names(),
            "the pool before the offer carries the three pinned baselines first",
        )
        self.assertEqual(
            J.names_of(after),
            self.names() + [J.VERSION_B, J.VERSION_C],
            "the window keeps its last m versions oldest to newest and the "
            "baselines are never evicted (docs/L2/evaluation/surface.md §7, "
            "docs/L2/evaluation/pool.md §3, ASM-16)",
        )
        self.assertEqual(
            J.names_of(J.pool_members(pool)),
            J.names_of(before),
            "offer returns a new pool and leaves its argument unchanged "
            "(docs/L2/evaluation/surface.md §7)",
        )
        self.assertNotEqual(
            after["id"],
            before["id"],
            "the id is recomputed from the new ordered membership "
            "(docs/L2/evaluation/pool.md §6, records.md §8)",
        )

    def test_join_evl_3_3_a_drawn_baseline_is_agents_build_baseline(self):
        """JOIN-EVL-3.3 the pool's baselines are `agents.build_baseline`'s policies.

        `docs/L2/evaluation/surface.md` §8 and `docs/L2/evaluation/pool.md` §7: a
        baseline member is drawn as `agents.build_baseline(name, seed)` at the
        caller's seed, so one seed draws one policy that answers one decision one
        way (`docs/L2/agents/surface.md` §12).  The oracle's answer is the one place
        the two modules must agree on a decision *and* on the seed, because its
        equity query is re-issued at that seed (`docs/L1/protocol.md` §3, ASM-4).
        """
        pool = J.shared_pool()
        names = J.names_of(J.pool_members(pool))
        size = len(names)
        decisions = J.decisions_of(J.MATCH_SEED, J.caller)[:3]
        self.assertEqual(len(decisions), 3, "three real decisions are compared")
        for name in self.names():
            with self.subTest(baseline=name):
                seed = names.index(name) + size * J.DRAW_MULTIPLE
                drawn = J.opponent(pool, seed)
                rebuilt = J.build_baseline(name, seed)
                for facts, legal in decisions:
                    self.assertEqual(
                        J.descriptor_index(legal, drawn(facts, legal)),
                        J.descriptor_index(legal, rebuilt(facts, legal)),
                        "a drawn baseline is agents.build_baseline at the caller's "
                        "seed (docs/L2/evaluation/pool.md §7, "
                        "docs/L2/agents/surface.md §12)",
                    )
        random_policy = J.build_baseline("random", J.CHECKPOINT_SEED)
        first = J.decision_signature(random_policy, decisions)
        self.assertEqual(
            first,
            J.decision_signature(random_policy, decisions),
            "one seed draws one policy that answers one decision one way "
            "(docs/L2/evaluation/surface.md §8, docs/L2/agents/surface.md §12)",
        )
        other = J.build_baseline("random", J.CHECKPOINT_SEED_B)
        self.assertNotEqual(
            first,
            J.decision_signature(other, decisions),
            "two seeds differ, which is the seed property protocol.md §3 states "
            "for the random baseline",
        )

    def test_join_evl_3_4_a_baseline_learns_nothing_from_the_cell_it_plays(self):
        """JOIN-EVL-3.4 a cell leaves the baseline policy it was handed unchanged.

        `docs/L1/protocol.md` §3 and `docs/L2/agents/learner.md` §5: a baseline
        never learns and its state advances nowhere, so a baseline's column is the
        same rule at every call order — which is why no cell's opponent drifts
        while the table is played (`docs/L2/evaluation/league.md` §7, D-6).
        """
        policy = J.build_baseline("random", J.CHECKPOINT_SEED_C)
        decisions = J.decisions_of(J.MATCH_SEED, J.caller)[:6]
        before = J.decision_signature(policy, decisions)
        cell = J.match(policy, J.caller, J.HANDS_FOUR, J.MATCH_SEED_OTHER)
        self.assertEqual(
            J.cell_members(cell),
            ["policy-1", "policy-2"],
            "a handed callable is named by its position (docs/L2/evaluation/"
            "surface.md §2)",
        )
        self.assertEqual(
            J.decision_signature(policy, decisions),
            before,
            "a baseline never learns from a match and its state advances nowhere "
            "(docs/L1/protocol.md §3, docs/L2/agents/learner.md §5, D-6)",
        )


if __name__ == "__main__":
    unittest.main()
