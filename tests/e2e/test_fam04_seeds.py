"""FAM-4 — the seed contract, with one pool in the tuple.

`docs/L1/battery.md` §3 FAM-4, `docs/L1/protocol.md` §2 and §4 (ASM-2), D-16.  A run is
reproducible from ``(configuration, seed set, budget, pool membership)``: since Rev 2 the
opponent is the league, so the fourth element of that tuple is the frozen pool.  At the
observable edge: one seed, one configuration and one pool produce identical outcomes
twice; a different seed or a different pool membership produces a different one; the
seed set actually used appears in the run record, the seed a cell used appears in the
cell; and the protocol's fixed seed set ``0, 1, 2`` and the league's fixed cell sizes are
declared, not implied (``protocol.md`` §2, ``league.md`` §6).
"""

import os
import random
import sys
import unittest

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _surface as S  # noqa: E402


class FAM4Seeds(S.SurfaceCase):
    """Seeded dealing, seeded episodes, seeded runs, and the record of them."""

    def fingerprint(self, seed):
        """The deal visible at a hand's first decision."""
        readout = self.readout(self.hand(seed))
        return tuple(
            str(readout[key]) for key in ("street", "hole", "board", "pot", "to_call")
        )

    def reported_seeds(self, record):
        """The seeds a record reports, read by key rather than by nesting."""
        values = S.declared_numbers(record, "seeds", "seed", "seedset", "seedings")
        if not values:
            values = S.numbers(S.find_values(record, "seed"))
        return set(int(value) for value in values)

    def test_fam4_1_one_seed_gives_the_same_deal_twice(self):
        """FAM-4.1 engine.new_hand(seed) twice deals the same hand (ASM-2)."""
        self.assertEqual(
            self.fingerprint(S.SEED_A),
            self.fingerprint(S.SEED_A),
            "the same seed must produce the same deal",
        )

    def test_fam4_2_a_different_seed_deals_a_different_hand(self):
        """FAM-4.2 different seeds give different deals (protocol §4)."""
        seeds = (S.SEED_A, S.SEED_B, S.SEED_C, S.SEED_D, S.SEED_E, S.SEED_F, S.SEED_G, S.SEED_H)
        deals = [self.fingerprint(seed) for seed in seeds]
        self.assertGreaterEqual(
            len(set(deals)),
            6,
            "eight different seeds must not deal the same hand: %r" % (deals,),
        )

    def test_fam4_3_the_seed_is_the_deal_and_nothing_before_it(self):
        """FAM-4.3 a deal depends on its seed, not on the hands dealt before it (ASM-2)."""
        first_b = self.fingerprint(S.SEED_B)
        first_a = self.fingerprint(S.SEED_A)
        self.hand(S.SEED_C)
        self.hand(S.SEED_H)
        self.assertEqual(
            self.fingerprint(S.SEED_B),
            first_b,
            "a seed's deal must not depend on earlier hands",
        )
        self.assertEqual(
            self.fingerprint(S.SEED_A),
            first_a,
            "a seed's deal must not depend on earlier hands",
        )

    def test_fam4_4_new_hand_seeds_python_s_global_random(self):
        """FAM-4.4 engine.new_hand seeds the global random — the ASM-2 contract."""
        self.hand(S.SEED_A)
        first = (random.random(), random.random(), random.random())
        self.hand(S.SEED_A)
        second = (random.random(), random.random(), random.random())
        self.assertEqual(
            first,
            second,
            "engine.new_hand is the single point that seeds the global random, which is "
            "what pokerkit shuffles with (ASM-2)",
        )

    def test_fam4_5_one_seed_gives_the_same_episode_twice(self):
        """FAM-4.5 engine.play_hand(seed, two policies) twice gives one record."""
        left = self.baseline("random", S.SEED_D)
        right = self.baseline("always-call", S.SEED_D)
        first = self.play(S.SEED_A, left, right)
        left_again = self.baseline("random", S.SEED_D)
        second = self.play(S.SEED_A, left_again, right)
        self.assertEqual(
            S.canon(first),
            S.canon(second),
            "one seed and one pair of policies must give one episode record",
        )

    def test_fam4_6_a_different_seed_gives_a_different_episode(self):
        """FAM-4.6 a different seed gives a different episode record."""
        left = self.baseline("random", S.SEED_D)
        first = self.play(S.SEED_A, left, self.baseline("always-call", S.SEED_D))
        second = self.play(S.SEED_B, left, self.baseline("always-call", S.SEED_D))
        self.assertNotEqual(
            S.canon(first),
            S.canon(second),
            "a different seed must not reproduce the same episode",
        )

    def test_fam4_7_one_seed_one_configuration_and_one_pool_repeat(self):
        """FAM-4.7 training.run is reproducible from (config, seeds, budget, pool)."""
        run = self.ep("training", "run")
        first = run("R1", [S.SEED_A], S.BUDGET_TINY, "cpu")
        second = run("R1", [S.SEED_A], S.BUDGET_TINY, "cpu")
        self.assertEqual(
            S.canon(self.curves_of(first)),
            S.canon(self.curves_of(second)),
            "two runs of one configuration at one seed set and one pool must report the "
            "same curves (protocol.md §4)",
        )
        self.assertEqual(
            S.canon(S.pool_identity(first)),
            S.canon(S.pool_identity(second)),
            "two runs of one configuration must train against the same frozen pool id",
        )

    def test_fam4_8_a_different_seed_gives_different_curves(self):
        """FAM-4.8 a different seed changes the run's curves (protocol §4)."""
        run = self.ep("training", "run")
        first = run("R1", [S.SEED_A], S.BUDGET_TINY, "cpu")
        second = run("R1", [S.SEED_B], S.BUDGET_TINY, "cpu")
        self.assertNotEqual(
            S.canon(self.curves_of(first)),
            S.canon(self.curves_of(second)),
            "the deal stream is seeded, so a different seed must give different curves",
        )

    def test_fam4_9_a_different_pool_membership_differs(self):
        """FAM-4.9 a different pool membership changes the pool and the cell (D-16)."""
        pool_a = self.pool(("kestrel",))
        pool_b = self.pool(("bramble",), width=96)
        self.assertNotEqual(
            S.canon(S.strings(self.members(pool_a))),
            S.canon(S.strings(self.members(pool_b))),
            "two membership declarations with different versions must read back as "
            "different pools (league.md §2)",
        )
        narrow = self.ep("agents", "param_count")(
            self.learner(width=S.VERSION_WIDTH, depth=S.VERSION_DEPTH,
                         seed=S.VERSIONS["kestrel"]["seed"])
        )
        broad = self.ep("agents", "param_count")(
            self.learner(width=96, depth=S.VERSION_DEPTH, seed=S.VERSIONS["bramble"]["seed"])
        )
        self.assertNotEqual(
            narrow,
            broad,
            "the two versions differ in capacity, which is what makes their cells "
            "distinguishable by the parameter counts §3.4 says a cell reports",
        )
        baseline = self.baseline("always-call", S.SEED_D)
        cell_a = self.match(
            self.member_policy("kestrel"), baseline, S.CELL_HANDS_SMALL, S.TABLE_SEED_A
        )
        cell_b = self.match(
            self.member_policy("bramble", width=96), baseline, S.CELL_HANDS_SMALL, S.TABLE_SEED_A
        )
        self.assertNotEqual(
            S.canon(cell_a),
            S.canon(cell_b),
            "at one seed and one hand count, a cell over a member of a different pool must "
            "not reproduce the same cell: no cell is played against a policy that is not "
            "one of the table's named members (league.md §1)",
        )

    def test_fam4_10_the_run_record_names_the_seed_set_and_budget_used(self):
        """FAM-4.10 a run record records the seeds and the budget it actually used."""
        record = self.run_record("R1", (S.SEED_A,), S.BUDGET)
        seeds = self.reported_seeds(record)
        self.assertIn(
            S.SEED_A,
            seeds,
            "the run record must carry the seed set it used: %r" % (sorted(seeds),),
        )
        self.assertIn(
            str(S.BUDGET),
            S.flatten_text(record),
            "the run record must carry the sample budget it used (%d)" % (S.BUDGET,),
        )

    def test_fam4_11_the_seed_a_cell_used_appears_in_the_cell(self):
        """FAM-4.11 a cell records the seed it was played at (protocol §4, D-16)."""
        cell = self.match(hands=S.CELL_HANDS_SMALL, seed=S.TABLE_SEED_A)
        reported = [int(value) for value in S.declared_numbers(cell, "seed", "tableseed")]
        self.assertTrue(
            S.TABLE_SEED_A in reported or str(S.TABLE_SEED_A) in S.flatten_text(cell),
            "the cell must record the seed it used (%d): %r" % (S.TABLE_SEED_A, cell),
        )

    def test_fam4_12_the_protocol_declares_the_fixed_seed_set_and_the_families(self):
        """FAM-4.12 evaluation.protocol declares seeds 0, 1, 2 and the seven families."""
        declared = self.ep("evaluation", "protocol")()
        seeds = set(
            int(value) for value in S.numbers(S.find_values(declared, "seed"))
        ) or set(int(value) for value in S.numbers(declared))
        self.assertTrue(
            {0, 1, 2} <= seeds,
            "the protocol's seed set is fixed at 0, 1, 2 and is recorded in every report: %r"
            % (declared,),
        )
        for family in S.FAMILIES:
            self.assertTrue(
                S.has_family(declared, family),
                "evaluation.protocol is the contract a report is judged against, so it must "
                "name the %r family (protocol.md §1): %r" % (family, declared),
            )

    def test_fam4_13_the_league_declares_its_bound_the_cells_and_the_table_seed(self):
        """FAM-4.13 evaluation.league declares M, both cell sizes and the table seed."""
        declared = self.ep("evaluation", "league")()
        values = set(int(value) for value in S.numbers(declared))
        for cell_size in (S.LIVE_CELL_HANDS, S.FULL_CELL_HANDS):
            self.assertIn(
                cell_size,
                values,
                "the league declares both table budgets' hands per cell (%d live, %d full): %r"
                % (S.LIVE_CELL_HANDS, S.FULL_CELL_HANDS, declared),
            )
        bounds = [int(value) for value in S.bound_numbers(declared)]
        self.assertIn(
            S.LEAGUE_BOUND,
            bounds,
            "the pool's bound is the fixed M = %d (league.md §2, ASM-14): %r"
            % (S.LEAGUE_BOUND, declared),
        )
        self.assertTrue(
            S.declared_numbers(declared, "tableseed", "seed"),
            "the league declares the table seed every table is played at (league.md §4): %r"
            % (declared,),
        )


if __name__ == "__main__":
    unittest.main()
