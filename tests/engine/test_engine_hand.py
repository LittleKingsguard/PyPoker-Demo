"""ENG-3 -- `new_hand` deals from its seed, and it is the project's only seeder.

``docs/L2/engine/surface.md`` §4; ``docs/L2/engine/environment.md`` §1, §5;
``docs/L3/engine/hand.md`` §2; ``docs/L3/engine/stream.md`` §1;
``docs/L1/battery.md`` §3 FAM-4 (ASM-2), D-15.

The seeds and the draw counts are the battery's own; no design document carries
them.  The *rule* they test is the contract's: one seed deals one hand, a deal
depends on its seed and not on the hands dealt before it, and `new_hand` is the
single point at which the global `random` stream is seeded.

One platform note, measured on this venv before the battery was written: a
`pokerkit` deal shuffles the deck inside `create_state`, so the three draws that
follow `new_hand(seed)` are the stream *after* that shuffle, not the stream a
bare `random.seed(seed)` would leave.  The cases below therefore assert what the
contract can state -- that the draws are a function of the seed alone, and that
two different seeds leave different draws -- rather than comparing them with a
bare `random.seed` sequence, which no conforming implementation can produce.
"""

import os
import random
import sys
import unittest

try:  # discovered as part of a tests.engine package
    from . import _engine_support as S
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _engine_support as S  # noqa: E402


class ENG3NewHand(S.EngineCase):
    """Dealing, reproducibility, and the single seeding point."""

    def first_readout(self, seed):
        """The facts of the first decision of the hand a seed deals."""
        return self.readout(self.hand(seed))

    def next_draws(self, seed, count=3, before=None):
        """The ``count`` draws the global stream yields straight after a deal."""
        if before is not None:
            random.seed(before)
        self.hand(seed)
        return tuple(random.random() for _ in range(count))

    def test_eng3_1_the_same_seed_deals_the_same_hand(self):
        """ENG-3.1 new_hand(seed) twice gives the same first-decision readout, and
        the whole hand replays identically (surface.md §4, ASM-2)."""
        first = self.first_readout(S.SEED_A)
        second = self.first_readout(S.SEED_A)
        self.assertEqual(first, second, "the same seed deals the same hand twice (surface.md §4)")

        walk_one, _ = self.drive(S.SEED_A, S.always_call)
        walk_two, _ = self.drive(S.SEED_A, S.always_call)
        self.assertEqual(
            [entry[0] for entry in walk_one],
            [entry[0] for entry in walk_two],
            "one seed and one policy sequence read the same facts at every decision (ASM-2)",
        )
        self.assertEqual(
            walk_one[-1][0]["history"], walk_two[-1][0]["history"],
            "the same seed and policy sequence give the same public history",
        )

    def test_eng3_2_a_different_seed_deals_a_different_hand(self):
        """ENG-3.2 different seeds deal different hands: twelve invented seeds give
        more than one deal (surface.md §4, protocol.md §4)."""
        deals = [self.first_readout(seed) for seed in S.SEEDS]
        distinct = {repr(facts["hole"]) + repr(facts["board"]) for facts in deals}
        self.assertGreaterEqual(
            len(distinct), 11,
            "a different seed deals a different hand: %d of %d invented seeds shared one "
            "deal, so the seed is not the deal (surface.md §4)" % (len(distinct), len(S.SEEDS)),
        )

    def test_eng3_3_a_deal_ignores_the_hands_dealt_before_it(self):
        """ENG-3.3 a deal depends on its seed and not on the hands dealt before it:
        deal A, deal B, deal other seeds, deal A again (surface.md §4, ASM-2)."""
        first_a = self.first_readout(S.SEED_A)
        first_b = self.first_readout(S.SEED_B)
        for seed in (S.SEED_C, S.SEED_D, S.SEED_E, S.SEED_F):
            self.hand(seed)
        self.assertEqual(
            self.first_readout(S.SEED_A), first_a,
            "a seed's deal must not depend on the hands dealt before it (surface.md §4)",
        )
        self.assertEqual(
            self.first_readout(S.SEED_B), first_b,
            "a seed's deal must not depend on the hands dealt before it (surface.md §4)",
        )

    def test_eng3_4_new_hand_seeds_the_global_random_stream(self):
        """ENG-3.4 the draws after new_hand(seed) are a function of the seed alone,
        whatever the stream held before the call (surface.md §4, stream.md §1)."""
        after_a = self.next_draws(S.SEED_A, before=123456789)
        again_a = self.next_draws(S.SEED_A, before=987654321)
        self.assertEqual(
            after_a, again_a,
            "engine.new_hand is the single point that seeds the global random (ASM-2), so the "
            "draws after it cannot depend on the stream state it was called in",
        )
        self.assertNotEqual(
            self.next_draws(S.SEED_B), self.next_draws(S.SEED_C),
            "the stream is seeded with the seed it was given, so two different seeds leave "
            "different draws (surface.md §4)",
        )

    def test_eng3_5_new_hand_moves_the_stream_at_all(self):
        """ENG-3.5 a deal moves the global stream: the state before the call differs
        from the state after it (surface.md §4, stream.md §1)."""
        random.seed(S.SEED_D)
        before = random.getstate()
        self.hand(S.SEED_D)
        self.assertNotEqual(
            random.getstate(), before,
            "new_hand seeds the global random and deals from it, so it must move the stream "
            "(surface.md §4, ASM-2)",
        )

    def test_eng3_6_new_hand_refuses_a_seed_that_is_not_an_integer(self):
        """ENG-3.6 new_hand refuses a str, a float, None and the booleans, naming the
        seed contract, and a refused call does not move the stream (surface.md §4,
        hand.md §2, errors.md §3)."""
        exc = self.refusal(S.ep("new_hand"), "20260101")
        self.assert_mentions(exc, "seed")
        for bad in (4242424.0, None, True, False):
            with self.subTest(seed=bad):
                random.seed(S.SEED_E)
                before = random.getstate()
                exc = self.refusal(S.ep("new_hand"), bad)
                self.assert_mentions(exc, "seed")
                self.assertEqual(
                    random.getstate(), before,
                    "a refused seed is refused before random.seed, so it cannot move the "
                    "stream (hand.md §2, errors.md §1): %r" % (bad,),
                )


if __name__ == "__main__":
    unittest.main()
