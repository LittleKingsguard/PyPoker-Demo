"""FAM-7 — the match scheduler: one cell at a time, both directions from one set of hands.

`docs/L1/battery.md` §3 FAM-7 and `docs/L1/league.md` §3 (D-16, ASM-2, ASM-14).  A cell
is one unordered pair played at the cell's hand count, hand after hand from the one
global stream; seats alternate across the hands; the two directions are the same hands
seen from each seat, so a cell costs its hand count and not twice it; and no cell is
interleaved with another.  `evaluation.opponent` is how the training loop draws one
opponent from the same pool, and what it returns is a pool member.

The cell sizes and seeds below (14, 23, 11 and the battery's own seeds) are the
battery's inventions; the league's cells are 120 and 1,500 (``league.md`` §6).
"""

import os
import sys
import unittest

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _records as R  # noqa: F401
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _records as R  # noqa: E402
    import _surface as S  # noqa: E402


class FAM7Scheduler(S.SurfaceCase):
    """One cell at a time: accounting, seat alternation, both directions, opponent."""

    # -- helpers -----------------------------------------------------------
    def cell(self, hands=S.CELL_HANDS_SMALL, seed=S.TABLE_SEED_A):
        """One chess-free cheap cell between two fixed baselines."""
        return self.match(hands=hands, seed=seed)

    def directions(self, cell):
        rows = R.direction_rows(cell)
        self.assertEqual(
            len(rows),
            2,
            "a cell is reported in both directions, one per seat (league.md §3): %r" % (cell,),
        )
        return rows

    def indices(self, policy, seed, limit=4):
        """The action indices one policy chooses over the first decisions of one hand."""
        return [entry[4] for entry in self.decision_walk(seed, policy, limit=limit)]

    def test_fam7_1_a_cell_accounts_for_every_hand_it_played(self):
        """FAM-7.1 every direction accounts for all the cell's hands."""
        cell = self.cell()
        hands = R.cell_hands(cell)
        for row in self.directions(cell):
            wins, ties, losses = R.direction_counts(row)
            self.assertEqual(
                wins + ties + losses,
                hands,
                "wins, ties and losses must account for every hand the cell played (%d): %r"
                % (hands, row),
            )

    def test_fam7_2_seats_alternate_across_a_cell_s_hands(self):
        """FAM-7.2 the seat split is two non-empty halves of the cell's hands."""
        cell = self.cell(hands=S.CELL_HANDS)
        hands = R.cell_hands(cell)
        for row in self.directions(cell):
            split = R.seat_split(row)
            self.assertGreaterEqual(
                len(split),
                2,
                "each member holds the button for half the hands, so both seats appear in "
                "the split (league.md §3): %r" % (row,),
            )
            if len(split) == 2:
                self.assertEqual(
                    int(sum(split)),
                    hands,
                    "the two seats partition the cell's hands, because seats alternate "
                    "across them (league.md §3): %r" % (row,),
                )
                self.assertLessEqual(
                    abs(split[0] - split[1]),
                    1,
                    "with seats alternating hand by hand the two seats differ by at most "
                    "one hand (%d played): %r" % (hands, row),
                )

    def test_fam7_3_both_directions_are_the_same_hands(self):
        """FAM-7.3 the two directions mirror each other: one cell, not two matches."""
        cell = self.cell()
        first, second = self.directions(cell)
        first_counts = R.direction_counts(first)
        second_counts = R.direction_counts(second)
        self.assertEqual(
            (first_counts[0], first_counts[2]),
            (second_counts[2], second_counts[0]),
            "the two directions are the same hands seen from each seat, so one direction's "
            "wins are the other's losses (league.md §3, ASM-14): %r against %r"
            % (first_counts, second_counts),
        )
        self.assertEqual(
            first_counts[1],
            second_counts[1],
            "a tied hand is a tie for both directions: %r against %r"
            % (first_counts, second_counts),
        )

    def test_fam7_4_the_two_directions_chip_deltas_are_zero_sum(self):
        """FAM-7.4 the mean chip deltas of a cell's directions negate each other."""
        cell = self.cell()
        first, second = R.cell_deltas(cell)
        self.assertAlmostEqual(
            first + second,
            0.0,
            places=9,
            msg="a heads-up cell pays one member what it takes from the other, so its two "
                "directions' mean chip deltas are zero-sum (protocol.md §2, ASM-12): %r"
                % ([first, second],),
        )

    def test_fam7_5_a_cell_plays_the_hand_count_it_was_given(self):
        """FAM-7.5 evaluation.match plays the declared hand count and records it."""
        hands = S.HANDS_TINY
        cell = self.match(hands=hands, seed=S.TABLE_SEED_B)
        self.assertEqual(
            R.cell_hands(cell),
            hands,
            "the cell's hand count is the one the caller declared (%d): %r" % (hands, cell),
        )
        for row in self.directions(cell):
            wins, ties, losses = R.direction_counts(row)
            self.assertEqual(
                wins + ties + losses,
                hands,
                "a cell of %d hands reports %d hands, not more and not fewer (league.md §3)"
                % (hands, hands),
            )

    def test_fam7_6_a_cell_carries_both_members_parameter_counts_and_its_seed(self):
        """FAM-7.6 a cell names its two members, their parameter counts and its seed."""
        cell = self.match(seed=S.TABLE_SEED_B)
        members = R.cell_members(cell)
        self.assertEqual(len(members), 2, "a cell pairs exactly two members: %r" % (cell,))
        self.assertNotEqual(
            members[0],
            members[1],
            "a cell is a pairing of two distinct members: %r" % (members,),
        )
        params = R.cell_params(cell)
        self.assertEqual(
            len(params),
            2,
            "the cell reports each member's parameter count from agents.param_count "
            "(records.md §9, e2e-surface §3.4): %r" % (cell,),
        )
        for count in params:
            self.assertGreaterEqual(
                count,
                0,
                "a parameter count is a non-negative number of trainable parameters: %r"
                % (params,),
            )
        self.assertEqual(
            R.cell_seed(cell),
            S.TABLE_SEED_B,
            "the cell records the seed it was played at (records.md §9): %r" % (cell,),
        )

    def test_fam7_7_two_cells_are_never_interleaved(self):
        """FAM-7.7 a cell played after another cell is the same cell it was before."""
        first = self.match(hands=S.CELL_HANDS_SMALL, seed=S.TABLE_SEED_A)
        self.match(hands=S.HANDS_TINY, seed=S.TABLE_SEED_B)
        again = self.match(hands=S.CELL_HANDS_SMALL, seed=S.TABLE_SEED_A)
        self.assertEqual(
            S.canon(first),
            S.canon(again),
            "cells are played one at a time from one stream, so a cell does not depend on "
            "what was played between two of its own runs (league.md §3, ASM-2)",
        )

    def test_fam7_8_opponent_returns_a_policy_of_the_declared_protocol(self):
        """FAM-7.8 evaluation.opponent returns one policy drawn from the pool."""
        pool = self.pool(tags=("kestrel", "bramble"))
        policy = self.opponent(pool, S.SEED_G)
        self.assertTrue(callable(policy), "opponent must return a policy of §2: %r" % (policy,))
        walk = self.decision_walk(S.SEED_H, policy, limit=3)
        self.assertTrue(walk, "the drawn opponent answered no decision at all")
        for _hand, _readout, legal, action, index in walk:
            self.assertIn(
                index,
                {0, 1, 2},
                "a drawn opponent chooses from the three-index vocabulary (e2e-surface §2): %r"
                % (index,),
            )
            self.assertTrue(
                any(S.canon(action) == S.canon(candidate) for candidate in legal),
                "a drawn opponent returns a descriptor from legal_actions, never an illegal "
                "action (e2e-surface §2, D-2): %r in %r" % (action, legal),
            )

    def test_fam7_9_opponent_is_drawn_from_the_pool_and_not_from_a_fixed_rule(self):
        """FAM-7.9 one (pool, seed) draws one opponent; different seeds draw others."""
        pool = self.pool(tags=("kestrel", "bramble", "thistle"))
        seeds = (S.SEED_A, S.SEED_B, S.SEED_C, S.SEED_D, S.SEED_E, S.SEED_F,
                 S.TABLE_SEED_A, S.TABLE_SEED_B)
        drawn = []
        for seed in seeds:
            first = self.indices(self.opponent(pool, seed), S.SEED_H)
            second = self.indices(self.opponent(pool, seed), S.SEED_H)
            self.assertEqual(
                first,
                second,
                "one pool and one seed draw one opponent: the draw is deterministic "
                "(ASM-2, D-16): %r against %r" % (first, second),
            )
            drawn.append(tuple(first))
        self.assertGreaterEqual(
            len(set(drawn)),
            2,
            "a draw over a pool of six members must not answer with one fixed policy for "
            "every seed, or the training loop is not sampling the pool (D-16): %r"
            % (sorted(set(drawn)),),
        )

    def test_fam7_10_a_cell_names_the_rule_each_member_carried(self):
        """FAM-7.10 a cell's `rules` names each member's learning rule."""
        # Two learners of one architecture, built under the two catalogue rules: the
        # estimator is the only thing that differs between the cell's two members
        # (`rules.md` §3, D-19).  The cell is 11 invented hands (battery.md §2).
        masked = self.rule_policy(S.RULE_DEFAULT, seed=S.SEED_I)
        doubled = self.rule_policy(S.RULE_SECOND, seed=S.SEED_J)
        cell = self.match(
            left=masked, right=doubled, hands=S.HANDS_TINY, seed=S.TABLE_SEED_B
        )
        rules = R.cell_rules(cell)
        named = [rule for _member, rule in R.rules_of(rules) if rule]
        self.assertEqual(
            sorted(named),
            sorted(S.RULES),
            "records.md §9 makes a cell's `rules` each member's rule by its id — the "
            "catalogue name its policy carries — so a cell says which two estimators met "
            "(e2e-surface.md §2, league.md §3, D-19): %r" % (rules,),
        )


if __name__ == "__main__":
    unittest.main()
