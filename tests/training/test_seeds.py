"""TRN-3 — the derivations: `_derive`, `_deal_seed`, `_opponent_seed`.

Drives `docs/L3/training/seeds.md` §2-§5: the `sha256` payload for the deal and the
opponent seed, the two domains, the modulo, and the property that makes a run
reproducible from `(configuration, seed set, budget, pool membership)` — the derivation is
a function of `(seed, index)` and never a draw, so no call here touches the global stream
(ASM-2, `protocol.md` §4). The battery recomputes §2's payload byte for byte instead of
trusting the call: a `seed + i`, a `hash()`, a missing separator or a one-domain digest
each changes the number and fails TRN-3.5, TRN-3.6 or TRN-3.2.
"""

import hashlib
import random
import unittest

from _training_support import (
    RUN_SEED,
    SIXTY_BUDGET,
    TrainingCase,
    as_int,
    internal,
)

#: seeds.md §2's payload, recomputed here: the five parts, their order, the separator.
PREFIX = b"pypoker-training/"
VERSION = b"/v1"
SEPARATOR = b"\x1f"
CEILING = 2 ** 63

#: A small budget's worth of indices, and the seed set it is trained at.
INDICES = tuple(range(0, SIXTY_BUDGET))
SEEDS = (RUN_SEED, RUN_SEED + 1, RUN_SEED + 2)


def expected(domain, seed, index):
    """seeds.md §2's derivation, computed from the document and nothing else."""
    payload = (
        PREFIX
        + domain.encode("ascii")
        + VERSION
        + SEPARATOR
        + str(int(seed)).encode("ascii")
        + SEPARATOR
        + str(int(index)).encode("ascii")
    )
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % CEILING


class SeedsTest(TrainingCase):
    def deal(self, seed, index):
        return internal("seeds", "_deal_seed")(seed, index)

    def opponent(self, seed, index):
        return internal("seeds", "_opponent_seed")(seed, index)

    def derive(self, domain, seed, index):
        return internal("seeds", "_derive")(domain, seed, index)

    def test_trn_3_1_one_seed_and_one_index_derive_one_pair(self):
        """TRN-3.1 the same `(seed, index)` derives the same deal and opponent seed twice, and each is `_derive`'s for its own domain (seeds.md §2, §5, ASM-2)."""
        seed, index = RUN_SEED, 7
        first = (self.deal(seed, index), self.opponent(seed, index))
        second = (self.deal(seed, index), self.opponent(seed, index))
        self.assertEqual(
            second,
            first,
            "a derivation is a function of (seed, index), so two calls give one pair "
            "(seeds.md §2, §5, FAM-4.3): %r again %r" % (first, second),
        )
        self.assertEqual(
            self.deal(seed, index),
            self.derive("deal", seed, index),
            "`_deal_seed` is `_derive` for the deal domain (seeds.md §2)",
        )
        self.assertEqual(
            self.opponent(seed, index),
            self.derive("opponent", seed, index),
            "`_opponent_seed` is `_derive` for the opponent domain (seeds.md §2)",
        )

    def test_trn_3_2_a_different_index_derives_a_different_pair(self):
        """TRN-3.2 hand *i* and hand *i+1* derive different seeds, which is why adjacent hands are not a shifted copy of one stream (seeds.md §2, §5, FAM-4.8)."""
        seed = RUN_SEED
        for index in range(12):
            with self.subTest(index=index):
                self.assertNotEqual(
                    self.deal(seed, index),
                    self.deal(seed, index + 1),
                    "hand i and hand i+1 are dealt at different seeds (seeds.md §2)",
                )
                self.assertNotEqual(
                    self.opponent(seed, index),
                    self.opponent(seed, index + 1),
                    "hand i and hand i+1 draw from different opponent seeds "
                    "(seeds.md §2)",
                )

    def test_trn_3_3_a_different_seed_derives_a_different_pair(self):
        """TRN-3.3 two seeds one apart do not swap, shift or repeat their hands: every index derives a different pair (seeds.md §2, §5, FAM-4.8)."""
        index = 5
        base = (self.deal(RUN_SEED, index), self.opponent(RUN_SEED, index))
        for seed in (RUN_SEED + 1, RUN_SEED + 2):
            with self.subTest(seed=seed):
                other = (self.deal(seed, index), self.opponent(seed, index))
                self.assertNotEqual(
                    other,
                    base,
                    "a different seed derives a different pair, so a battery that "
                    "changes one seed sees a different sample and not a shifted copy "
                    "(seeds.md §2): %r against %r" % (other, base),
                )

    def test_trn_3_4_no_derivation_touches_the_global_random_stream(self):
        """TRN-3.4 sampling `random.getstate()`, calling every private name and comparing shows the stream where it was found (seeds.md §5, ASM-2, FAM-4.4)."""
        before = random.getstate()
        for index in range(8):
            self.deal(RUN_SEED, index)
            self.opponent(RUN_SEED, index)
            self.derive("deal", RUN_SEED, index)
            self.derive("opponent", RUN_SEED, index)
        self.assertEqual(
            random.getstate(),
            before,
            "no call here seeds, reads or advances the global stream; only dealing "
            "moves it, and dealing goes through engine.new_hand (seeds.md §1, §5, "
            "ASM-2)",
        )

    def test_trn_3_5_the_payload_is_the_documented_sha256_byte_for_byte(self):
        """TRN-3.5 the derived value is seeds.md §2's payload — the five parts in order, the `\\x1f` separator, the first eight bytes big-endian, modulo `2**63` (seeds.md §2, §5, §6, guardrails G9)."""
        for domain, function in (("deal", self.deal), ("opponent", self.opponent)):
            for seed, index in ((RUN_SEED, 0), (RUN_SEED, 23), (RUN_SEED + 1, 3)):
                with self.subTest(domain=domain, seed=seed, index=index):
                    self.assertEqual(
                        function(seed, index),
                        expected(domain, seed, index),
                        "the payload is b\"pypoker-training/\" + domain + b\"/v1\" + "
                        "b\"\\x1f\" + seed + b\"\\x1f\" + index, sha256'd, the first "
                        "eight bytes big-endian, reduced modulo 2**63 (seeds.md §2, "
                        "guardrails G9)",
                    )
        self.assertNotEqual(
            expected("deal", RUN_SEED, 23),
            expected("deal", RUN_SEED + 11, 3),
            "the separator is what keeps (seed, index) = (1, 23) from colliding with "
            "(12, 3) (seeds.md §2)",
        )
        self.assertEqual(
            self.deal(RUN_SEED + 11, 3),
            expected("deal", RUN_SEED + 11, 3),
            "a payload assembled without the separator would collide those two and "
            "fail here (seeds.md §2, guardrails G9)",
        )

    def test_trn_3_6_the_two_domains_do_not_coincide(self):
        """TRN-3.6 for one `(seed, index)` the deal seed and the opponent seed differ, because the opponent draw must not be a function of the deal (seeds.md §2)."""
        for index in range(16):
            with self.subTest(index=index):
                self.assertNotEqual(
                    self.deal(RUN_SEED, index),
                    self.opponent(RUN_SEED, index),
                    "one digest per question keeps hand i's opponent seed from being "
                    "its deal seed (seeds.md §2, evaluation/surface.md §8)",
                )

    def test_trn_3_7_the_derived_value_is_a_non_negative_int_below_the_ceiling(self):
        """TRN-3.7 every derivation is a plain non-negative `int` below `2**63`, so `engine.new_hand` and `evaluation.opponent` receive an integer seed (seeds.md §2, engine/surface.md §4, evaluation/surface.md §8)."""
        for index in range(24):
            for value in (self.deal(RUN_SEED, index), self.opponent(RUN_SEED, index)):
                with self.subTest(index=index):
                    number = as_int(value, "a derived seed")
                    self.assertGreaterEqual(number, 0, "the modulo keeps it non-negative")
                    self.assertLess(
                        number,
                        CEILING,
                        "the derivation reduces modulo 2**63 (seeds.md §2): %r" % (number,),
                    )

    def test_trn_3_8_no_two_hands_of_a_small_budget_share_a_seed(self):
        """TRN-3.8 over the indices a 60-hand budget uses, across the seed set, every deal seed and every opponent seed is distinct (seeds.md §2, §3, FAM-4.3)."""
        deals = []
        opponents = []
        for seed in SEEDS:
            for index in INDICES:
                deals.append(self.deal(seed, index))
                opponents.append(self.opponent(seed, index))
        self.assertEqual(
            len(set(deals)),
            len(deals),
            "two hands of one budget must not be dealt at one seed, or two rungs' "
            "hands would coincide (seeds.md §2): %d distinct of %d"
            % (len(set(deals)), len(deals)),
        )
        self.assertEqual(
            len(set(opponents)),
            len(opponents),
            "two hands of one budget must not draw the same opponent seed "
            "(seeds.md §2): %d distinct of %d"
            % (len(set(opponents)), len(opponents)),
        )
        self.assertEqual(
            len(set(deals) & set(opponents)),
            0,
            "a deal seed and an opponent seed are two questions about one hand and "
            "never one value (seeds.md §2)",
        )


if __name__ == "__main__":
    unittest.main()
