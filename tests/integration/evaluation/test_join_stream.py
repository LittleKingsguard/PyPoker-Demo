"""JOIN-EVL-9 — one cell at a time, and the one stream (ASM-2).

`docs/L2/evaluation/surface.md` §1 and `docs/L1/protocol.md` §4: play is the only
thing that moves Python's global `random` stream, and it moves it only through
`engine.new_hand`, the project's single seeding point.  The nine entry points that
play nothing therefore leave the stream exactly where they found it — `rating`'s
bootstrap draws from its own generator seeded from the table seed — while `match`
and `matrix` move it, and a cell played twice at one seed is identical whatever
was played between the two runs (`docs/L2/evaluation/league.md` §2,
`docs/L2/evaluation/scheduler.md` §7, FAM-4, FAM-7).
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


class TheStream(J.JoinCase):
    """What moves the global stream, and what must not."""

    def hand_built_record(self):
        table = J.hand_built_matrix()
        fitted = J.rating(table)
        pool_record = J.hand_built_pool_record()
        return J.run_record(table, fitted, pool_record), table, fitted

    def test_join_evl_9_1_the_nine_that_play_nothing_leave_the_stream_alone(self):
        """JOIN-EVL-9.1 no non-playing entry point moves `random.getstate()`.

        `docs/L2/evaluation/surface.md` §1 lists the nine explicitly: `protocol`,
        `league`, `build_pool`, `pool_members`, `offer`, `opponent`, `rating`,
        `policy_from` and `report` play nothing and leave the stream where they
        found it; `rating`'s bootstrap draws from its own generator seeded from the
        table seed and records that seed (ASM-17, ASM-2).
        """
        record, table, fitted = self.hand_built_record()
        version = J.version(J.VERSION_A, J.START_LABEL)
        unfrozen = J.build_pool(
            {"members": [J.bare_version(J.VERSION_A, J.START_LABEL)],
             "m": J.league()["m"], "frozen": False}
        )
        names = J.names_of(J.pool_members(J.shared_pool()))
        baseline_seed = names.index("random") + len(names) * J.DRAW_MULTIPLE
        calls = (
            ("protocol", lambda: J.protocol()),
            ("league", lambda: J.league()),
            ("build_pool", lambda: J.build_pool(
                {"members": [version], "m": J.league()["m"], "frozen": True})),
            ("pool_members", lambda: J.pool_members(J.shared_pool())),
            ("offer", lambda: J.offer(
                unfrozen, J.bare_version(J.VERSION_B, J.VERSION_A))),
            ("opponent", lambda: J.opponent(J.shared_pool(), baseline_seed)),
            ("rating", lambda: J.rating(table)),
            ("policy_from", lambda: J.policy_from(version["path"])),
            ("report", lambda: J.report(J.RUNG, record, table, fitted)),
        )
        for name, call in calls:
            with self.subTest(entry=name):
                self.assert_stream_unchanged(call, "evaluation.%s" % (name,))
        self.assertEqual(
            len(calls),
            9,
            "the surface's non-playing entry points are nine "
            "(docs/L2/evaluation/surface.md §1)",
        )

    def test_join_evl_9_2_match_moves_the_stream_only_through_the_deal(self):
        """JOIN-EVL-9.2 after a cell the stream is where the last hand's deal left it.

        `docs/L2/evaluation/surface.md` §9 and `docs/L2/engine/surface.md` §4:
        `new_hand` seeds the stream and deals, and `play_hand` deals through it
        instead of seeding again, so a cell's only movement of the stream is its
        hands' deals — and because each deal reseeds, the state after the cell is
        the state after the last hand's deal (`docs/L3/evaluation/scheduler.md` §3,
        §7, ASM-2).
        """
        before = random.getstate()
        try:
            cell = J.match("random", "always-call", J.HANDS_DOZEN, J.MATCH_SEED)
            after = random.getstate()
        finally:
            random.setstate(before)
        self.assertNotEqual(
            after,
            before,
            "a cell plays hands, so it moves the global stream "
            "(docs/L2/evaluation/surface.md §1, FAM-7)",
        )
        self.assert_stream_at_last_deal(
            after,
            J.hand_seed(J.MATCH_SEED, J.HANDS_DOZEN - 1),
            "evaluation.match",
        )
        self.assertEqual(
            int(cell["seed"]),
            J.MATCH_SEED,
            "the cell records the seed its hands were derived from "
            "(records.md §9)",
        )

    def test_join_evl_9_3_the_table_moves_the_stream_through_its_last_deal(self):
        """JOIN-EVL-9.3 the shared table's stream state is its last hand's deal.

        `docs/L2/evaluation/surface.md` §10 and `docs/L3/evaluation/matrix.md` §2:
        the cells are played in the pair enumeration's order, each to completion,
        and every hand is dealt at the seed the scheduler derives — so the table's
        only movement of the stream is its hands' deals, and the final state is the
        last cell's last hand's deal (`docs/L2/evaluation/surface.md` §1, ASM-2).
        The observation was taken around the one real call in `_join_support`.
        """
        table = J.shared_matrix()
        observed = J.matrix_stream()
        self.assertTrue(
            observed["moved"],
            "a table plays hands, so it moves the global stream "
            "(docs/L2/evaluation/surface.md §1, FAM-8)",
        )
        last_seed = J.last_cell_hand_seed(
            table, int(table["table_seed"]), int(table["hands_per_cell"])
        )
        self.assert_stream_at_last_deal(
            observed["after"], last_seed, "evaluation.matrix"
        )

    def test_join_evl_9_4_a_cell_is_identical_whatever_was_played_between(self):
        """JOIN-EVL-9.4 two runs of one cell agree value for value.

        `docs/L2/evaluation/surface.md` §9 and `docs/L3/evaluation/scheduler.md` §7:
        one pair, one hand count and one seed give one cell whatever was played
        before it, because every hand's seed is a function of the cell's seed and
        the hand's index alone and a policy's answer is a function of the decision
        (FAM-7, ASM-2).  The cell between the two runs is another cell of another
        pair at another seed, so the stream is genuinely elsewhere.
        """
        first = J.match("random", "always-call", J.HANDS_NINE, J.MATCH_SEED)
        J.match("random", "oracle", J.HANDS_TWO, J.MATCH_SEED_OTHER)
        J.match("always-call", "random", J.HANDS_FOUR, J.REPLAY_SEED)
        second = J.match("random", "always-call", J.HANDS_NINE, J.MATCH_SEED)
        self.assertEqual(
            J.canonical(second),
            J.canonical(first),
            "one pair, one hand count and one seed give one cell whatever was "
            "played before it (docs/L2/evaluation/surface.md §9, "
            "docs/L3/evaluation/scheduler.md §7)",
        )


if __name__ == "__main__":
    unittest.main()
