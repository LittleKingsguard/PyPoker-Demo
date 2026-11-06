"""FAM-4, ASM-2 — one seed deals one hand, and only the deal moves the stream.

`docs/L2/engine/surface.md` §4 and §1 rules 3–4, `environment.md` §1 (dealt, dealt
before), §5, `strata/platform.md` (`pokerkit` shuffles with Python's global `random`
and takes no seed).  One seed deals the same hand twice; different seeds deal
different hands; a deal depends on its seed and not on the hands dealt before it;
`new_hand` is the project's single seeding point; and every other call — the queries
and `play_hand`'s whole episode — hands the caller's stream back in the state it
found, `play_hand` included, since it deals through `new_hand` and never seeds again.
"""

import os
import random
import sys
import unittest

try:
    from . import _support as S
except ImportError:
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _support as S  # noqa: E402


class FAM4Seeding(S.EngineCase):
    """The seeding contract, observed at the package's edge."""

    def fingerprint(self, seed):
        """The deal visible at a hand's first decision."""
        readout = self.readout(self.new_hand(seed))
        return S.canon(
            [readout["street"], readout["hole"], readout["board"], readout["pot"],
             readout["stacks"], readout["to_call"]]
        )

    def test_fam4_01_one_seed_deals_the_same_hand_twice(self):
        """FAM-4.1 new_hand at one invented seed deals one hand (surface.md §4)."""
        self.assertEqual(
            self.fingerprint(S.SEED_A),
            self.fingerprint(S.SEED_A),
            "the same seed must deal the same hand (surface.md §4, ASM-2)",
        )

    def test_fam4_02_different_seeds_deal_different_hands(self):
        """FAM-4.2 different seeds deal different hands (surface.md §4)."""
        deals = [self.fingerprint(seed) for seed in S.SEED_DISTINCT]
        self.assertGreaterEqual(
            len(set(deals)), len(deals) - 1,
            "different seeds deal different hands (surface.md §4): %d of %d deals were "
            "distinct" % (len(set(deals)), len(deals)),
        )

    def test_fam4_03_a_deal_depends_on_its_seed_and_not_on_the_hands_before_it(self):
        """FAM-4.3 a deal ignores the hands dealt, played and read before it (§4)."""
        before = self.fingerprint(S.SEED_B)
        self.fingerprint(S.SEED_C)
        self.fingerprint(S.SEED_D)
        self.walk(S.SEED_E, limit=S.DECISION_BOUND)
        self.play_hand(S.SEED_F, S.PolicyProbe(name="seat 0"), S.PolicyProbe(name="seat 1"))
        self.assertEqual(
            before,
            self.fingerprint(S.SEED_B),
            "a deal depends on its seed and not on the hands dealt before it "
            "(surface.md §4, ASM-2)",
        )

    def test_fam4_04_new_hand_seeds_python_s_global_random(self):
        """FAM-4.4 new_hand is the project's single seeding point (surface.md §1 rule 3)."""
        self.new_hand(S.SEED_G)
        first = (random.random(), random.random(), random.random())
        self.new_hand(S.SEED_G)
        second = (random.random(), random.random(), random.random())
        self.assertEqual(
            first, second,
            "new_hand(seed) seeds the global random, which is what pokerkit shuffles "
            "with (surface.md §4, ASM-2): two deals at one seed must leave the same "
            "following draws",
        )
        self.new_hand(S.SEED_H)
        third = (random.random(), random.random(), random.random())
        self.assertNotEqual(
            first, third,
            "two different seeds seed the stream differently (ASM-2)",
        )

    def test_fam4_05_the_queries_hand_the_stream_back(self):
        """FAM-4.5 readout, legal_actions, is_terminal and payoffs leave the stream alone."""
        hand = self.new_hand(S.SEED_I)
        for what, call in (
            ("readout", lambda: self.readout(hand)),
            ("legal_actions", lambda: self.legal_actions(hand)),
            ("is_terminal", lambda: self.is_terminal(hand)),
        ):
            self.assert_stream_unchanged(call, what)
        finished = self.finished_hand(S.SEED_J)
        self.assert_stream_unchanged(lambda: self.payoffs(finished), "payoffs")
        before = self.stream()
        self.new_hand(S.SEED_K)
        self.assertNotEqual(
            S.canon(before), S.canon(self.stream()),
            "new_hand is the project's single seeding point, so the deal it makes is the "
            "one thing that moves the stream (surface.md §1 rule 3, ASM-2)",
        )

    def test_fam4_06_play_hand_leaves_the_stream_where_its_deal_left_it(self):
        """FAM-4.6 play_hand deals through new_hand and seeds the stream no second time."""
        seed = S.SEED_L
        self.new_hand(seed)
        after_deal = self.stream()
        self.play_hand(seed, S.PolicyProbe(name="seat 0"), S.PolicyProbe(name="seat 1"))
        self.assertEqual(
            S.canon(after_deal), S.canon(self.stream()),
            "play_hand deals through new_hand and hands the stream back where that deal "
            "left it (surface.md §1 rule 4, ASM-2): it neither seeds twice nor leaves a "
            "query's draw behind",
        )

    def test_fam4_07_one_seed_and_one_policy_pair_give_one_episode(self):
        """FAM-4.7 one seed and one pair of policies give one record; another seed differs."""
        left = S.PolicyProbe(S.choose_raise, name="seat 0")
        right = S.PolicyProbe(S.choose_call, name="seat 1")
        first = self.play_hand(S.SEED_M, left, right)
        again_left = S.PolicyProbe(S.choose_raise, name="seat 0")
        again_right = S.PolicyProbe(S.choose_call, name="seat 1")
        second = self.play_hand(S.SEED_M, again_left, again_right)
        self.assertEqual(
            S.canon(first), S.canon(second),
            "one seed and one pair of policies give one episode record (surface.md §10, "
            "ASM-2)",
        )
        other = self.play_hand(
            S.SEED_N, S.PolicyProbe(S.choose_raise, name="seat 0"),
            S.PolicyProbe(S.choose_call, name="seat 1"),
        )
        self.assertNotEqual(
            S.canon(S.decision_list(first)),
            S.canon(S.decision_list(other)),
            "a different seed gives a different episode: its decisions differ, since the "
            "deal differs (surface.md §10, ASM-2)",
        )


if __name__ == "__main__":
    unittest.main()
