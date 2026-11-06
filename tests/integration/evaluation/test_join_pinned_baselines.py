"""JOIN-EVL-3 — the three pinned baselines (D-6, ASM-4).

`agents.baselines()` names exactly `random`, `always-call` and `oracle`, and
`agents.build_baseline(name, seed)` returns each as a policy of the protocol
(`docs/L2/agents/surface.md` §11–§12, `docs/L1/protocol.md` §3).  `evaluation`'s
pool always holds those three, never evicts them, and draws a baseline at the
caller's seed, so a baseline column is the same rule at every call order and no
cell's opponent drifts while the table is played (`docs/L2/evaluation/league.md`
§1, §7, `docs/L1/league.md` §2).
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


class PinnedBaselines(J.JoinCase):
    """The catalogue's three names, present in every pool and never evicted."""

    def names(self):
        return [str(name) for name in J.baselines()]

    def test_join_evl_3_1_the_catalogues_three_are_every_pools_first_three(self):
        """JOIN-EVL-3.1 the pool's baseline ids are exactly `agents.baselines()`'s names.

        `docs/L2/evaluation/pool.md` §2 step 5 and `docs/L2/evaluation/surface.md`
        §6: the three baselines are added first, in `agents.baselines()`'s order,
        each marked pinned with the `params` of `0` the catalogue declares — in
        every pool, R1's baselines-only pool included (`docs/L2/evaluation/league.md`
        §1, `docs/L1/league.md` §2, D-16).
        """
        catalogue = self.names()
        self.assertEqual(
            catalogue,
            ["random", "always-call", "oracle"],
            "agents.baselines() declares the three names of D-6 "
            "(docs/L2/agents/surface.md §11)",
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
                    "%s must carry the catalogue's three baselines first, in its "
                    "order (docs/L2/evaluation/pool.md §2, surface.md §6)"
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
                        "(docs/L2/evaluation/pool.md §2 step 5, D-16)",
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
            "the pool before the offer carries the three baselines first",
        )
        self.assertEqual(
            J.names_of(after),
            self.names() + [J.VERSION_B, J.VERSION_C],
            "the window keeps its last m versions oldest to newest and the "
            "baselines are never evicted (docs/L2/evaluation/surface.md §7, "
            "docs/L2/evaluation/pool.md §6, ASM-16)",
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
