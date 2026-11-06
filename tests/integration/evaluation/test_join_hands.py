"""JOIN-EVL-4 — a cell is a run of hands (engine's deal, at derived seeds).

`docs/L2/evaluation/league.md` §2 fixes the scheduler: one cell at a time, the
i-th hand dealt at a seed derived from the cell's seed and `i` alone, seats
alternating hand by hand, both directions read from one set of hands
(`docs/L3/evaluation/scheduler.md` §1, §3–§4).  This family re-derives each
hand's seed the way `docs/L3/evaluation/scheduler.md` §3 pins it, replays the
hands through `engine.play_hand`, and asserts that the cell really is those hands
and not a different deal; it also asserts the seat alternation against
`engine.readout`'s `seat` fact, because engine seat 0 holds the button in every
hand (`docs/L2/engine/surface.md` §4).
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


class CellAsHands(J.JoinCase):
    """One invented cell between two fixed baselines, replayed hand by hand."""

    def replay(self, left_name, right_name, hands, seed):
        """Replay a cell: the pinned derivation, `engine.play_hand`, the payoffs.

        Returns ``(episodes, left_counts, left_sum, button_hands)`` where each
        episode is ``(hand_seed, seat0_side, payoffs)`` and `seat0_side` is
        ``"left"`` or ``"right"``.
        """
        left = J.build_baseline(left_name, seed)
        right = J.build_baseline(right_name, seed)
        episodes = []
        wins = ties = losses = 0
        total = 0
        button_hands = 0
        for index in range(hands):
            hand_seed = J.hand_seed(seed, index)
            if index % 2 == 0:
                seat0, seat1, seat0_side, delta_seat = left, right, "left", 0
                button_hands += 1
            else:
                seat0, seat1, seat0_side, delta_seat = right, left, "right", 1
            episode = J.play_hand(hand_seed, seat0, seat1)
            self.assertEqual(
                J.episode_seed(episode),
                hand_seed,
                "engine.play_hand deals at the seed it was given "
                "(docs/L1/records.md §5, docs/L2/engine/surface.md §10)",
            )
            payoffs = J.episode_payoffs(episode)
            delta = payoffs[delta_seat]
            total += delta
            if delta > 0:
                wins += 1
            elif delta < 0:
                losses += 1
            else:
                ties += 1
            episodes.append((hand_seed, seat0_side, payoffs))
        return episodes, (wins, ties, losses), total, button_hands

    def cell(self):
        return J.match(
            "random", "always-call", J.HANDS_DOZEN, J.MATCH_SEED
        )

    def test_join_evl_4_1_the_cell_is_the_hands_the_derivation_deals(self):
        """JOIN-EVL-4.1 counts and mean chip deltas agree with the replayed hands.

        `docs/L3/evaluation/scheduler.md` §3–§4: the i-th hand of a cell at seed
        `s` is dealt at `_hand_seed(s, i)`, `engine.play_hand(seed, seat0, seat1)`
        drives it, and a win, loss or tie is read from the member's net chip delta
        (`docs/L1/protocol.md` §2, ASM-6).  The mean is chips per hand, so a cell
        of one hand count is comparable with any other (`scheduler.md` §4).  A cell
        whose counts agree but whose hands were dealt elsewhere would still be a
        different measurement, which is why the per-hand seeds are re-derived.
        """
        hands = J.HANDS_DOZEN
        cell = self.cell()
        self.assertEqual(
            J.cell_members(cell),
            ["random", "always-call"],
            "a cell names its two members in argument order (records.md §9)",
        )
        self.assertEqual(
            int(cell["hands"]),
            hands,
            "a cell plays the hand count it was given (records.md §9, "
            "docs/L1/league.md §3)",
        )
        self.assertEqual(
            int(cell["seed"]),
            J.MATCH_SEED,
            "the cell records the seed it was played at (records.md §9)",
        )
        _episodes, counts, total, _buttons = self.replay(
            "random", "always-call", hands, J.MATCH_SEED
        )
        for member_id, expected in (
            ("random", counts),
            ("always-call", (counts[2], counts[1], counts[0])),
        ):
            direction = J.direction_for(cell, member_id)
            self.assertEqual(
                J.counts_of(direction),
                tuple(int(value) for value in expected),
                "the cell's %r direction must be the replayed hands' win/tie/loss "
                "counts at the seeds docs/L3/evaluation/scheduler.md §3 pins: %r"
                % (member_id, expected),
            )
        left_mean = total / float(hands)
        left = J.direction_for(cell, "random")
        right = J.direction_for(cell, "always-call")
        self.assertAlmostEqual(
            J.mean_delta_of(left),
            left_mean,
            places=12,
            msg="the mean chip delta is the replayed sum over the hand count "
                "(docs/L3/evaluation/scheduler.md §4, ASM-12)",
        )
        self.assertAlmostEqual(
            J.mean_delta_of(right),
            -left_mean,
            places=12,
            msg="the two directions negate each other because every hand is "
                "zero-sum (docs/L3/evaluation/scheduler.md §4, ASM-12)",
        )

    def test_join_evl_4_2_the_seats_alternate_against_engines_seat_fact(self):
        """JOIN-EVL-4.2 seat alternation is engine seat 0 in the replayed hands.

        `docs/L2/engine/surface.md` §4: seat 0 holds the button and posts the small
        blind in every hand, so a caller alternates seats by swapping the two
        policies it hands to `play_hand`; `docs/L3/evaluation/scheduler.md` §2 then
        makes `left` seat 0 on `ceil(hands/2)` hands and `right` on
        `floor(hands/2)`, and each direction reports the split as two counts
        summing to `hands` (`docs/L1/league.md` §3, D-16).
        """
        hands = J.HANDS_NINE
        cell = J.match("random", "always-call", hands, J.MATCH_SEED)
        episodes, _counts, _total, buttons = self.replay(
            "random", "always-call", hands, J.MATCH_SEED
        )
        self.assertEqual(
            buttons,
            (hands + 1) // 2,
            "left is handed over as engine seat 0 on ceil(hands/2) hands "
            "(docs/L3/evaluation/scheduler.md §2)",
        )
        for position, (_hand_seed, seat0_side, _payoffs) in enumerate(episodes):
            hand = J.new_hand(J.hand_seed(J.MATCH_SEED, position))
            seat, is_button = J.seat_fact(J.readout(hand))
            self.assertEqual(
                seat,
                0,
                "a freshly dealt hand's acting seat is engine seat 0 "
                "(docs/L2/engine/surface.md §4), hand %d" % (position,),
            )
            self.assertTrue(
                is_button,
                "engine seat 0 is the button, so the first decision of every hand "
                "is the button's (docs/L2/engine/surface.md §4, "
                "docs/L1/protocol.md §1), hand %d" % (position,),
            )
            self.assertEqual(
                seat0_side,
                "left" if position % 2 == 0 else "right",
                "the scheduler swaps the two policies hand by hand "
                "(docs/L3/evaluation/scheduler.md §1–§2)",
            )
        left_split = J.seat_split_of(J.direction_for(cell, "random"))
        right_split = J.seat_split_of(J.direction_for(cell, "always-call"))
        self.assertEqual(
            left_split,
            (buttons, hands - buttons),
            "random's seat split is the hands it held engine seat 0 and seat 1 "
            "(docs/L3/evaluation/scheduler.md §2, records.md §9)",
        )
        self.assertEqual(
            right_split,
            (hands - buttons, buttons),
            "the two directions' splits are the mirror of one set of hands "
            "(docs/L3/evaluation/scheduler.md §2)",
        )
        for direction in (J.direction_for(cell, "random"),
                          J.direction_for(cell, "always-call")):
            self.assertEqual(
                sum(J.seat_split_of(direction)),
                hands,
                "each direction's seat split sums to the hands played "
                "(docs/L1/league.md §3, records.md §9)",
            )

    def test_join_evl_4_3_both_directions_are_the_same_hands_from_each_seat(self):
        """JOIN-EVL-4.3 one set of hands, reported from each seat.

        `docs/L2/evaluation/league.md` §2 and `docs/L3/evaluation/scheduler.md` §1,
        §4: a cell costs its hand count and not twice it, one direction's wins are
        the other's losses, a tied hand is a tie for both, and the two mean deltas
        negate because every hand's payoffs sum to zero (`records.md` §5, ASM-12).
        """
        hands = J.HANDS_DOZEN
        cell = self.cell()
        episodes, _counts, _total, _buttons = self.replay(
            "random", "always-call", hands, J.MATCH_SEED
        )
        self.assertEqual(
            len(episodes),
            hands,
            "a cell costs its hand count and not twice it "
            "(docs/L2/evaluation/league.md §2, ASM-14)",
        )
        left = J.direction_for(cell, "random")
        right = J.direction_for(cell, "always-call")
        left_wins, left_ties, left_losses = J.counts_of(left)
        right_wins, right_ties, right_losses = J.counts_of(right)
        self.assertEqual(
            (right_wins, right_ties, right_losses),
            (left_losses, left_ties, left_wins),
            "one direction's wins are the other's losses and a tie is a tie for "
            "both (docs/L3/evaluation/scheduler.md §4, docs/L1/league.md §2)",
        )
        self.assertAlmostEqual(
            J.mean_delta_of(left) + J.mean_delta_of(right),
            0.0,
            places=12,
            msg="the two mean chip deltas negate because the hand was zero-sum "
                "(docs/L3/evaluation/scheduler.md §4, ASM-12)",
        )
        for payoffs in (episode[2] for episode in episodes):
            self.assertEqual(
                sum(payoffs.values()),
                0.0,
                "every replayed hand's payoffs sum to zero "
                "(docs/L2/engine/surface.md §9, ASM-12)",
            )

    def test_join_evl_4_4_a_cell_accounts_for_every_hand(self):
        """JOIN-EVL-4.4 counts, splits and the seed account for the whole cell.

        `records.md` §9 and `docs/L2/evaluation/league.md` §2: each direction
        carries wins, ties and losses summing to the hands played, a seat split
        summing to them too, and the mean chip delta per hand; the record also
        carries the seed and one parameter count per member (`docs/L2/evaluation/
        surface.md` §9).
        """
        hands = J.HANDS_DOZEN
        cell = self.cell()
        self.assertEqual(
            len(cell["directions"]),
            2,
            "a cell reports both seats (records.md §9)",
        )
        for member_id in J.cell_members(cell):
            direction = J.direction_for(cell, member_id)
            wins, ties, losses = J.counts_of(direction)
            self.assertEqual(
                wins + ties + losses,
                hands,
                "the counts of the %r direction must account for every hand "
                "(records.md §9, docs/L1/league.md §3)" % (member_id,),
            )
            self.assertEqual(
                sum(J.seat_split_of(direction)),
                hands,
                "the seat split of the %r direction must account for every hand "
                "(records.md §9)" % (member_id,),
            )
            self.assertTrue(
                J.finite(J.mean_delta_of(direction)),
                "the mean chip delta per hand must be a finite number "
                "(records.md §9, docs/L3/evaluation/scheduler.md §4)",
            )
        self.assertEqual(
            len(cell["params"]),
            len(J.cell_members(cell)),
            "a cell carries one parameter count per member, position-aligned "
            "(records.md §9, docs/L2/evaluation/surface.md §2)",
        )

    def test_join_evl_4_5_a_different_seed_deals_different_hands(self):
        """JOIN-EVL-4.5 one seed gives one cell, and another deals other hands.

        `docs/L2/evaluation/surface.md` §9: one pair, one hand count and one seed
        give one cell whatever was played before it, while a different seed deals
        different hands (`docs/L3/evaluation/scheduler.md` §7, FAM-7, FAM-4).
        """
        hands = J.HANDS_SEVEN
        first = J.match("random", "always-call", hands, J.MATCH_SEED)
        again = J.match("random", "always-call", hands, J.MATCH_SEED)
        other = J.match("random", "always-call", hands, J.MATCH_SEED_OTHER)
        self.assertEqual(
            J.canonical(again),
            J.canonical(first),
            "one pair, one hand count and one seed give one cell "
            "(docs/L2/evaluation/surface.md §9)",
        )
        seeds = {J.hand_seed(J.MATCH_SEED, index) for index in range(hands)}
        other_seeds = {J.hand_seed(J.MATCH_SEED_OTHER, index)
                       for index in range(hands)}
        self.assertEqual(
            seeds & other_seeds,
            set(),
            "the pinned derivation gives different hands for different cell seeds "
            "(docs/L3/evaluation/scheduler.md §3)",
        )
        observed = {
            "counts": [J.counts_of(direction) for direction in first["directions"]],
            "means": [round(J.mean_delta_of(direction), 6)
                      for direction in first["directions"]],
        }
        observed_other = {
            "counts": [J.counts_of(direction) for direction in other["directions"]],
            "means": [round(J.mean_delta_of(direction), 6)
                      for direction in other["directions"]],
        }
        self.assertNotEqual(
            observed,
            observed_other,
            "a different seed deals different hands, so a different cell "
            "(docs/L2/evaluation/surface.md §9, ASM-2)",
        )


if __name__ == "__main__":
    unittest.main()
