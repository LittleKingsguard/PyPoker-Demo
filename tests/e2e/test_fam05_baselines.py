"""FAM-5 — the three fixed baselines behave as their rules state.

`docs/L1/battery.md` §3 FAM-5, `docs/L1/protocol.md` §3 (D-6, ASM-4).  A baseline is a
policy of `e2e-surface.md` §2 and a rule a battery can check: `random` is uniform over
the legal indices and seeded, `always-call` never folds and raises only when it must,
and `oracle` is consistent with the pot odds against `engine.equity` — the same two
entry points the oracle itself uses.

Rev 2 gives the baselines a second job: they are pool members and matrix columns at the
same hand count as every league cell, and their three mutual cells anchor the rating
(protocol §3, `league.md` §4–§5).  That membership is a league fact and is asserted by
the matrix and pool families (FAM-6 and FAM-8 of `battery.md` §3); here it appears only
structurally, as "all three names are buildable policies".
"""

import os
import sys
import unittest

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _surface as S  # noqa: E402

# How far the oracle's own equity sample and the battery's estimate may disagree
# before a decision counts as decisive.  Both are estimates; the case asserts the
# pot-odds rule outside this band and does not pretend to see inside it.
EQUITY_BAND = 0.08


class FAM5Baselines(S.SurfaceCase):
    """The fixed baselines of D-6, asserted as rules."""

    def indices(self, walk):
        return [entry[4] for entry in walk]

    def test_fam5_1_baselines_are_exactly_the_three_of_d6(self):
        """FAM-5.1 agents.baselines names random, always-call and oracle (D-6)."""
        declared = self.ep("agents", "baselines")()
        names = set()
        for text in S.strings(declared):
            for baseline in S.BASELINES:
                if text.strip() == baseline:
                    names.add(baseline)
        self.assertEqual(
            names,
            set(S.BASELINES),
            "agents.baselines must name exactly %r; it declared %r"
            % (sorted(S.BASELINES), declared),
        )

    def test_fam5_2_every_baseline_builds_a_policy_of_section_2(self):
        """FAM-5.2 build_baseline returns a callable that chooses from legal_actions."""
        hand = self.hand(S.SEED_E)
        readout = self.readout(hand)
        legal = self.legal(hand)
        for name in S.BASELINES:
            policy = self.baseline(name, S.SEED_E)
            self.assertTrue(callable(policy), "the %r baseline is not a policy" % (name,))
            action = policy(readout, legal)
            self.assertTrue(
                any(_same(action, candidate) for candidate in legal),
                "the %r baseline chose a descriptor outside legal_actions: %r"
                % (name, action),
            )

    def test_fam5_3_random_never_returns_an_illegal_action(self):
        """FAM-5.3 the random baseline never leaves the legal set (protocol §3)."""
        for seed in (S.SEED_A, S.SEED_E):
            policy = self.baseline("random", S.SEED_G)
            for _hand, _readout, _legal, _action, index in self.decision_walk(seed, policy):
                self.assertIn(index, {0, 1, 2},
                              "the random baseline chose an index outside the vocabulary")

    def test_fam5_4_random_is_seeded(self):
        """FAM-5.4 one seed agrees twice and two seeds differ (protocol §3)."""
        first = self.indices(
            self.decision_walk(S.SEED_A, self.baseline("random", S.SEED_D))
        )
        same_seed = self.indices(
            self.decision_walk(S.SEED_A, self.baseline("random", S.SEED_D))
        )
        other_seed = self.indices(
            self.decision_walk(S.SEED_A, self.baseline("random", S.SEED_F))
        )
        self.assertEqual(first, same_seed,
                         "two random policies at one seed must agree")
        self.assertNotEqual(first, other_seed,
                            "two random policies at different seeds must differ")

    def test_fam5_5_always_call_never_folds(self):
        """FAM-5.5 always-call never folds in any decision of any hand (D-6)."""
        for seed in (S.SEED_A, S.SEED_E, S.SEED_F):
            policy = self.baseline("always-call", S.SEED_D)
            for _hand, _readout, _legal, _action, index in self.decision_walk(seed, policy):
                self.assertNotEqual(
                    index,
                    0,
                    "the always-call baseline folded at seed %r" % (seed,),
                )

    def test_fam5_6_always_call_calls_whenever_calling_is_legal(self):
        """FAM-5.6 always-call checks/calls when it can, and raises only when forced."""
        for seed in (S.SEED_A, S.SEED_E):
            policy = self.baseline("always-call", S.SEED_D)
            for _hand, _readout, legal, _action, index in self.decision_walk(seed, policy):
                indices = set(self.ep("features", "legal_indices")(legal))
                if 1 in indices:
                    self.assertEqual(
                        index,
                        1,
                        "always-call must check or call whenever that is legal",
                    )
                else:
                    self.assertEqual(
                        index,
                        2,
                        "with check/call unavailable always-call makes the minimum completion",
                    )

    def test_fam5_7_oracle_is_consistent_with_pot_odds_against_equity(self):
        """FAM-5.7 the oracle calls at or above the pot odds and folds below them."""
        decisive = 0
        for seed in (S.SEED_A, S.SEED_C, S.SEED_E):
            oracle = self.baseline("oracle", S.SEED_E)
            for hand, readout, legal, _action, index in self.decision_walk(seed, oracle):
                indices = set(self.ep("features", "legal_indices")(legal))
                if 0 not in indices:
                    self.assertNotEqual(index, 0,
                                        "the oracle folded where folding was not legal")
                    continue
                pot = readout["pot"]
                to_call = readout["to_call"]
                odds = to_call / float(pot + to_call) if (pot + to_call) else 0.0
                equity = self.ep("engine", "equity")(hand, S.SEED_E, S.EQUITY_SAMPLES)
                self.assertGreaterEqual(equity, 0.0)
                self.assertLessEqual(equity, 1.0)
                if abs(equity - odds) <= EQUITY_BAND:
                    continue
                decisive += 1
                if equity >= odds:
                    self.assertNotEqual(
                        index,
                        0,
                        "equity %.3f is at or above the pot odds %.3f, so the oracle "
                        "must not fold (protocol §3)" % (equity, odds),
                    )
                else:
                    self.assertEqual(
                        index,
                        0,
                        "equity %.3f is below the pot odds %.3f, so the oracle must fold "
                        "when folding is legal (protocol §3)" % (equity, odds),
                    )
        self.assertGreaterEqual(
            decisive,
            2,
            "the case saw no decision clear of the pot-odds boundary, so it proved nothing",
        )

    def test_fam5_8_a_rebuilt_baseline_repeats_its_decisions(self):
        """FAM-5.8 a baseline is a fixed rule: rebuilt at one seed, it decides the same."""
        policy = self.baseline("oracle", S.SEED_E)
        first = self.indices(self.decision_walk(S.SEED_A, policy))
        fresh = self.baseline("oracle", S.SEED_E)
        second = self.indices(self.decision_walk(S.SEED_A, fresh))
        self.assertEqual(first, second,
                         "a rebuilt baseline at the same seed must choose the same actions")


def _same(one, other):
    if one is other:
        return True
    try:
        return bool(one == other)
    except Exception:
        return False


if __name__ == "__main__":
    unittest.main()
