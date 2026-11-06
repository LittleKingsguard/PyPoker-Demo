"""JOIN-EVL-2 — a pool member is the player its checkpoint is.

`docs/L1/protocol.md` §5 makes `save`/`load` loss-free at the decision boundary,
and D-16 turns that equality into a league member: the member a pool draws must
decide as the learner the checkpoint was saved from, its capacity must be the
count `agents.param_count` measured, and a baseline's capacity must be the zero
`agents.baselines()` declares (`docs/L2/evaluation/surface.md` §2, §8, §9;
`docs/L2/evaluation/league.md` §7).  This family drives that boundary *through the
pool* — through `opponent`, through `match`'s cells and through `policy_from` —
rather than only through `agents.as_policy`.
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


class MembersAsPlayers(J.JoinCase):
    """The drawn member, the cell's parameter counts and the one checkpoint."""

    def decisions(self):
        """A fixed set of real decisions over two invented deals."""
        out = J.decisions_of(J.MATCH_SEED, J.caller)
        out += J.decisions_of(J.MATCH_SEED_OTHER, J.caller)
        self.assertGreaterEqual(
            len(out),
            8,
            "the compared decisions must cover more than one real hand",
        )
        return out

    def test_join_evl_2_1_the_drawn_version_decides_as_its_learner(self):
        """JOIN-EVL-2.1 `opponent` draws the checkpoint's player at its own seed.

        `docs/L2/evaluation/surface.md` §8 and `docs/L2/evaluation/pool.md` §7: a
        drawn version is `policy_from` of its checkpoint, built at the seed the
        container records, so it answers what `agents.act` answers on the same
        readout — the loss-free boundary of `docs/L1/protocol.md` §5 carried
        through the pool rather than only through `agents.as_policy`.
        """
        info = J.checkpoint(J.CHECKPOINT_A, J.CHECKPOINT_SEED)
        pool = J.shared_pool()
        names = J.names_of(J.pool_members(pool))
        position = names.index(J.VERSION_A)
        size = len(names)
        draw_seed = position + size * J.DRAW_MULTIPLE
        self.assertEqual(
            draw_seed % size,
            position,
            "the draw is the seed reduced modulo the membership's size "
            "(docs/L2/evaluation/pool.md §7)",
        )
        drawn = J.opponent(pool, draw_seed)
        for index, (facts, legal) in enumerate(self.decisions()):
            expected = J.decision_as_act(
                info["learner"], info["encoder"], facts, legal
            )
            chosen = drawn(facts, legal)
            self.assert_descriptor_in(legal, chosen, "a drawn version member")
            self.assertEqual(
                J.descriptor_index(legal, chosen),
                expected,
                "a member drawn from the pool decides as the learner its "
                "checkpoint was saved from (docs/L1/protocol.md §5, "
                "docs/L2/evaluation/pool.md §7), decision %d" % (index,),
            )

    def test_join_evl_2_2_a_cells_params_are_the_measured_counts(self):
        """JOIN-EVL-2.2 a baseline's cell count is the declared zero, a version's is measured.

        `records.md` §9 makes `params` a cell's required key, and
        `docs/L2/evaluation/surface.md` §2 says it carries one integer per member:
        `agents.param_count` of the learner behind a version, and the zero
        `agents.baselines()` declares for a baseline (ASM-10).  A baseline has no
        trainable parameter and `param_count` refuses it (`docs/L2/agents/surface.md`
        §5), so the zero must be the catalogue's, not a number this module invented.
        """
        info = J.checkpoint(J.CHECKPOINT_A, J.CHECKPOINT_SEED)
        record = J.version(J.VERSION_A, J.START_LABEL)
        cell = J.match("always-call", record, J.HANDS_FOUR, J.MATCH_SEED)
        self.assertEqual(
            J.cell_members(cell),
            ["always-call", J.VERSION_A],
            "a cell names its two members by the record's id, in argument order "
            "(records.md §9, surface.md §9)",
        )
        self.assertEqual(
            [int(count) for count in cell["params"]],
            [J.declared_params("always-call"), info["params"]],
            "a cell's params are the zero agents.baselines() declares and "
            "agents.param_count of the version's learner (records.md §9, "
            "docs/L2/evaluation/surface.md §2, ASM-10)",
        )
        self.assertEqual(
            J.unlabelled_of(cell),
            set(),
            "a measured count is never listed as unlabelled "
            "(docs/L2/evaluation/scheduler.md §4, ASM-10)",
        )
        baseline_cell = J.match("random", "always-call", J.HANDS_FOUR, J.MATCH_SEED)
        self.assertEqual(
            [int(count) for count in baseline_cell["params"]],
            [J.declared_params("random"), J.declared_params("always-call")],
            "two baselines are two declared zeros in one cell "
            "(records.md §9, ASM-10)",
        )

    def test_join_evl_2_3_one_checkpoint_is_one_player_across_pool_and_loader(self):
        """JOIN-EVL-2.3 the drawn member and `policy_from` are one player.

        `docs/L2/evaluation/surface.md` §8 and §12: a version member is
        `policy_from` of its checkpoint beside its member record, so the pool and
        the bare path name one player at the checkpoint's recorded seed
        (`docs/L2/evaluation/scheduler.md` §5, §5.1, `docs/L1/protocol.md` §5).
        """
        record = J.version(J.VERSION_A, J.START_LABEL)
        pool = J.build_pool(
            {"members": [record], "m": J.league()["m"], "frozen": True}
        )
        names = J.names_of(J.pool_members(pool))
        size = len(names)
        drawn = J.opponent(pool, names.index(J.VERSION_A) + size * J.DRAW_MULTIPLE)
        loaded = J.policy_from(record["path"])
        compared = 0
        for facts, legal in self.decisions():
            self.assertEqual(
                J.descriptor_index(legal, drawn(facts, legal)),
                J.descriptor_index(legal, loaded(facts, legal)),
                "one checkpoint is one player, whether the pool drew it or the "
                "bare path loaded it (docs/L2/evaluation/pool.md §7, "
                "docs/L2/evaluation/surface.md §12)",
            )
            compared += 1
        self.assertGreaterEqual(compared, 8, "the equality must be shown over a set "
                                              "of real decisions")

    def test_join_evl_2_4_the_container_decides_the_seed_not_the_record(self):
        """JOIN-EVL-2.4 a version record whose `seed` disagrees is not refused.

        `docs/L2/evaluation/scheduler.md` §5 and `docs/L3/evaluation/errors.md` §5:
        a version is built at the seed its checkpoint records, read from the
        container, and a record whose own `seed` disagrees is carried — not
        refused, because over-refusal is a defect.  So one checkpoint is one cell
        whatever the record's `seed` field says.
        """
        record = J.version(J.VERSION_A, J.START_LABEL)
        wrong = dict(record)
        wrong["seed"] = 111
        self.assertNotEqual(
            int(wrong["seed"]),
            J.checkpoint(J.CHECKPOINT_A, J.CHECKPOINT_SEED)["seed"],
            "the disagreeing record must genuinely disagree with the container",
        )
        honest = J.match("always-call", record, J.HANDS_FOUR, J.MATCH_SEED)
        disagreeing = J.match("always-call", wrong, J.HANDS_FOUR, J.MATCH_SEED)
        self.assertEqual(
            J.canonical(disagreeing),
            J.canonical(honest),
            "the checkpoint's container decides the member's seed, and a record "
            "whose `seed` disagrees is not refused (docs/L2/evaluation/scheduler.md "
            "§5, docs/L3/evaluation/errors.md §5)",
        )

    def test_join_evl_2_5_an_opaque_side_is_named_by_its_position(self):
        """JOIN-EVL-2.5 a callable from outside is `policy-1`/`policy-2`, unmeasured.

        `docs/L2/evaluation/surface.md` §2: a callable handed in from outside
        carries no member record, so it is named for its position in the call and
        its capacity is recorded as unmeasured, which the cell states in
        `unlabelled` — an opaque policy cannot be asked for a parameter count and
        this module invents no number it did not measure (ASM-10).  A baseline
        *policy object* handed in is exactly such a callable: the three names are
        strings in the call, not policy objects (`docs/L3/evaluation/scheduler.md`
        §5).
        """
        left = J.caller
        right = J.build_baseline("always-call", J.CHECKPOINT_SEED)
        cell = J.match(left, right, J.HANDS_FOUR, J.MATCH_SEED)
        self.assertEqual(
            J.cell_members(cell),
            ["policy-1", "policy-2"],
            "a callable handed in is named for its position in the call "
            "(docs/L2/evaluation/surface.md §2, docs/L3/evaluation/scheduler.md §5)",
        )
        self.assertEqual(
            [int(count) for count in cell["params"]],
            [0, 0],
            "an unlabelled policy's params is zero because nothing was measured "
            "(records.md §9, docs/L2/evaluation/surface.md §2)",
        )
        self.assertEqual(
            J.unlabelled_of(cell),
            {"policy-1", "policy-2"},
            "the cell states which zeros are unmeasured "
            "(docs/L2/evaluation/scheduler.md §4, ASM-10)",
        )


if __name__ == "__main__":
    unittest.main()
