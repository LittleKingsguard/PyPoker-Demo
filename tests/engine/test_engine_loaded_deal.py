"""FAM-25 -- the loaded deal: a prescribed hand, the six refusals and its replay.

``docs/L1/loaded-deal.md`` §2-§7; ``docs/L1/battery.md`` §3 FAM-25; D-70, D-13, ASM-2.

The four proof obligations the design lists, and nothing else: **P1** is the capture that
ships beside this file as ``tests/engine/_loaded_deal_baseline.json``'s gate and is not a
case here (a battery cannot assert a tree against itself); **P2** is the loaded path and
the seeded path reaching one state encoding identically, at both encodings; **P3** is that
a refusal deals nothing and leaves the global stream where it was; **P4** is that the
record replays, at a five-card deal, a four-card one and a three-card one.

The deals below are this battery's own, invented from the declared spelling; the replay
deals are read off a seeded hand's own ``reveal``, so the case is not written around an
example of the design document (``docs/L1/battery.md`` §4, D-15).
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

#: The two declared encodings (``features/surface.md`` §3).
ENCODINGS = ("flat-numeric", "card-tokens")

#: The six rules of ``loaded-deal.md`` §3, each with one invented deal that breaks it and
#: the word its message must name.  Every deal is six seats over a three-card board, so
#: the shape's seat count is fixed and one rule alone is broken.
SIX_REFUSALS = (
    ("not-a-deal", 4242424, "deal"),
    (
        "not-a-deal",
        {"holes": [["As", "Ad"], ["Ks", "Kd"], ["2c", "2d"], ["3c", "3d"],
                   ["4c", "4d"], ["5c", "5d"]], "board": ["6c", "7c", "8c"], "extra": 1},
        "deal",
    ),
    (
        "seat-coverage",
        {"holes": [["As", "Ad"], ["Ks", "Kd"], ["2c", "2d"], ["3c", "3d"],
                   ["4c", "4d"]], "board": ["6c", "7c", "8c"]},
        "pairs",
    ),
    (
        "hole-size",
        {"holes": [["As"], ["Ks", "Kd"], ["2c", "2d"], ["3c", "3d"], ["4c", "4d"],
                   ["5c", "5d"]], "board": ["6c", "7c", "8c"]},
        "pair",
    ),
    (
        "board-length",
        {"holes": [["As", "Ad"], ["Ks", "Kd"], ["2c", "2d"], ["3c", "3d"], ["4c", "4d"],
                   ["5c", "5d"]], "board": ["6c", "7c"]},
        "3..5",
    ),
    (
        "card-outside-deck",
        {"holes": [["As", "Ad"], ["Ks", "Kd"], ["2c", "2d"], ["3c", "3d"], ["4c", "4d"],
                   ["5c", "5d"]], "board": ["6c", "7c", "1x"]},
        "card",
    ),
    (
        "duplicate-card",
        {"holes": [["As", "Ad"], ["As", "Kd"], ["2c", "2d"], ["3c", "3d"], ["4c", "4d"],
                   ["5c", "5d"]], "board": ["6c", "7c", "8c"]},
        "times",
    ),
)

#: One invented six-seat deal, in seat order, on the six-seat shape: two cards per seat
#: and a five-card board, seventeen distinct spellings (``loaded-deal.md`` §2).
SIX_SEAT_DEAL = {
    "holes": (
        ("3c", "4d"), ("Jc", "Td"), ("3h", "5h"),
        ("4s", "6c"), ("5d", "6s"), ("As", "Ad"),
    ),
    "board": ("3s", "6d", "9d", "4c", "Jh"),
}


def features_module():
    """The declared ``features`` package, after the engine surface put ``src`` on the path."""
    S.engine()
    import features  # noqa: E402 - imported once the engine surface is present

    return features


class FAM25LoadedDeal(S.EngineCase):
    """P2-P4: the loaded deal's identity, its refusals and its replay."""

    def shaped_deal(self, seed, shape, deal=None):
        """`new_hand(seed, shape, deal)`: one hand dealt from a prescribed deal.

        An absent deal is today's call: the whole deck comes from the stream
        (loaded-deal.md §1, §5).
        """
        if deal is None:
            return S.ep("new_hand")(seed, shape)
        return S.ep("new_hand")(seed, shape, deal)

    def seating(self, shape, policy=None):
        """The shape's whole seating, one policy per seat in seat order."""
        policy = S.always_call if policy is None else policy
        return tuple(policy for _ in range(S.SHAPE_SEATS[shape]))

    def played(self, seed, shape, deal, policy=None):
        """One episode on one deal: the positional pair on two seats, the seating on six."""
        policy = S.always_call if policy is None else policy
        seats = S.SHAPE_SEATS[shape]
        if seats == 2:
            return S.ep("play_hand")(seed, policy, policy, shape, deal=deal)
        return S.ep("play_hand")(
            seed, seats=tuple(policy for _ in range(seats)), shape=shape, deal=deal
        )

    def replay_deal(self, record):
        """A seeded record's own cards, as the deal the loaded path is asked to lay."""
        return {
            "holes": tuple(entry["hole"] for entry in record["reveal"]["seats"]),
            "board": tuple(record["reveal"]["board"]),
        }

    # -- P2 -----------------------------------------------------------------
    def test_fam25_1_a_loaded_hand_encodes_as_the_seeded_hand_it_replays(self):
        """FAM-25.1 a seeded hand's own deal, replayed through the loaded path, reads and
        encodes identically at every decision, at both encodings (loaded-deal.md §6 P2)."""
        features = features_module()
        compared = 0
        for shape in (S.DEFAULT_SHAPE, S.NO_LIMIT_SHAPE, S.SIX_SEAT_SHAPE):
            seeded_record = self.played(S.SEED_A, shape, None)
            deal = self.replay_deal(seeded_record)
            loaded_record = self.played(S.SEED_A, shape, deal)
            self.assertEqual(
                loaded_record["decisions"],
                seeded_record["decisions"],
                "a loaded hand that names the seeded hand's own cards takes the same "
                "decisions with the same facts, amounts and payoffs (loaded-deal.md §6 P2)",
            )
            self.assertEqual(loaded_record["payoffs"], seeded_record["payoffs"])
            self.assertEqual(loaded_record["reveal"], seeded_record["reveal"])
            for encoding in ENCODINGS:
                encoder = features.build_encoder(encoding, shape=shape)
                left = self.shaped_deal(S.SEED_A, shape, deal)
                right = self.shaped_deal(S.SEED_A, shape)
                while not self.terminal(left):
                    left_facts = self.readout(left)
                    right_facts = self.readout(right)
                    self.assertEqual(
                        left_facts, right_facts,
                        "at decision %d of %s the loaded hand's readout is the seeded "
                        "hand's (loaded-deal.md §6 P2)" % (compared, shape),
                    )
                    self.assertEqual(
                        features.encode(encoder, left_facts).tolist(),
                        features.encode(encoder, right_facts).tolist(),
                        "the loaded state's %s observation is the one the encoder would "
                        "produce for the seeded state (loaded-deal.md §6 P2, D-70)"
                        % (encoding,),
                    )
                    compared += 1
                    left = self.step(left, "check-call")
                    right = self.step(right, "check-call")
        self.assertGreaterEqual(
            compared, 30,
            "the comparison must cover several decisions of several hands, got %d"
            % (compared,),
        )

    # -- P3 -----------------------------------------------------------------
    def test_fam25_2_each_of_the_six_refusals_names_its_rule_and_deals_nothing(self):
        """FAM-25.2 the six rules are refused in their declared order, naming the fact,
        and the global stream is exactly where it was (loaded-deal.md §3, §6 P3)."""
        for rule, deal, word in SIX_REFUSALS:
            with self.subTest(rule=rule, deal=deal):
                random.seed(S.SEED_D)
                before = random.getstate()
                exc = self.refusal(
                    S.ep("new_hand"), S.SEED_D, S.SIX_SEAT_SHAPE, deal
                )
                self.assert_mentions(exc, word)
                self.assert_mentions(exc, "deal")
                self.assertEqual(
                    random.getstate(), before,
                    "a refused deal is refused before random.seed, so it deals nothing "
                    "and cannot move the stream (loaded-deal.md §3, hand.md §2)",
                )
        # the same six refusals are reached through `play_hand`, and one message each
        for rule, deal, word in SIX_REFUSALS:
            with self.subTest(rule=rule, from_play_hand=True):
                random.seed(S.SEED_D)
                before = random.getstate()
                exc = self.refusal(
                    lambda: S.ep("play_hand")(
                        S.SEED_D,
                        shape=S.SIX_SEAT_SHAPE,
                        seats=self.seating(S.SIX_SEAT_SHAPE),
                        deal=deal,
                    )
                )
                self.assert_mentions(exc, word)
                self.assertEqual(random.getstate(), before)

    # -- P4 -----------------------------------------------------------------
    def test_fam25_3_the_record_replays_at_three_four_and_five_board_cards(self):
        """FAM-25.3 the record carries its deal and replays it; a short deal's unnamed
        street moves with the seed while its named cards do not (loaded-deal.md §4, §6 P4)."""
        for length in (3, 4, 5):
            with self.subTest(board_cards=length):
                deal = {
                    "holes": (("As", "Ad"), ("Ks", "Kd")),
                    "board": ("2c", "7h", "9s", "Td", "3c")[:length],
                }
                first = self.played(S.SEED_B, S.NO_LIMIT_SHAPE, deal)
                self.assertEqual(
                    first["deal"],
                    {"holes": tuple(deal["holes"]), "board": tuple(deal["board"])},
                    "the record carries the deal as played, normalised and undropped "
                    "(loaded-deal.md §4)",
                )
                again = self.played(first["seed"], S.NO_LIMIT_SHAPE, first["deal"])
                self.assertEqual(
                    again, first,
                    "handing the record's own deal back at its own seed gives the record "
                    "again (loaded-deal.md §4, §6 P4)",
                )
                other = self.played(S.SEED_E, S.NO_LIMIT_SHAPE, deal)
                self.assertEqual(
                    tuple(other["reveal"]["seats"][0]["hole"]), deal["holes"][0],
                    "a different seed at one deal does not move the hole cards it names "
                    "(loaded-deal.md §5)",
                )
                self.assertEqual(
                    tuple(other["reveal"]["board"][:length]), tuple(deal["board"]),
                    "a different seed at one deal does not move the board cards it names "
                    "(loaded-deal.md §5)",
                )
                if length < 5:
                    self.assertNotEqual(
                        other["reveal"]["board"][length:],
                        first["reveal"]["board"][length:],
                        "the street a short deal leaves undealt comes from the stream, so "
                        "it moves with the seed (loaded-deal.md §5, §6 P4)",
                    )

    # -- the record, the reveal and the seats ---------------------------------
    def test_fam25_4_a_seeded_record_carries_no_deal_and_a_loaded_one_agrees_with_the_reveal(self):
        """FAM-25.4 the `deal` key is present exactly when a deal was supplied, and it
        agrees with the reveal on every seat, a folded one included (loaded-deal.md §4)."""
        seeded = self.played(S.SEED_C, S.NO_LIMIT_SHAPE, None)
        self.assertNotIn(
            "deal", seeded,
            "a seeded call's record is exactly today's record key for key (loaded-deal.md "
            "§4, D-43)",
        )
        deal = {
            "holes": (("7h", "2h"), ("8h", "7d")),
            "board": ("3s", "6d", "9d"),
        }
        loaded = self.played(S.SEED_C, S.NO_LIMIT_SHAPE, deal)
        self.assertIn("deal", loaded, "a loaded call's record carries the deal")
        for seat, entry in enumerate(loaded["reveal"]["seats"]):
            self.assertEqual(
                tuple(entry["hole"]), tuple(deal["holes"][seat]),
                "reveal's per-seat hole equals the deal's pair for that seat, whether the "
                "seat showed or not (loaded-deal.md §4)",
            )
        self.assertEqual(
            tuple(loaded["reveal"]["board"][:3]), tuple(deal["board"]),
            "the recorded board is what the hand laid down and the recorded deal is what "
            "was prescribed; both are recorded (loaded-deal.md §4)",
        )

    def test_fam25_5_a_loaded_hand_deals_the_named_cards_on_every_shape(self):
        """FAM-25.5 at each of the three shapes the acting seat's own hole is the deal's
        pair for that seat, and the board grows into the prescribed prefix
        (loaded-deal.md §2, §8)."""
        two_seat = {"holes": (("As", "Ad"), ("Ks", "Kd")), "board": ("2c", "7h", "9s")}
        for shape in (S.DEFAULT_SHAPE, S.NO_LIMIT_SHAPE, S.SIX_SEAT_SHAPE):
            deal = two_seat if S.SHAPE_SEATS[shape] == 2 else SIX_SEAT_DEAL
            with self.subTest(shape=shape):
                hand = self.shaped_deal(S.SEED_F, shape, deal)
                seen = 0
                while not self.terminal(hand):
                    facts = self.readout(hand)
                    seat = facts["seat"][0]
                    self.assertEqual(
                        tuple(facts["hole"]), tuple(deal["holes"][seat]),
                        "the acting seat's hole is the deal's pair for that seat, in seat "
                        "order (loaded-deal.md §2)",
                    )
                    # The board grows into the deal's own cards and only then from the
                    # stream, so a short deal's card count is the cap (loaded-deal.md §2).
                    dealt = min(len(facts["board"]), len(deal["board"]))
                    self.assertEqual(
                        tuple(facts["board"][:dealt]),
                        tuple(deal["board"][:dealt]),
                        "the board at a decision is the deal's own cards, in dealing "
                        "order, for the streets it names; a street it leaves undealt "
                        "follows from the stream (loaded-deal.md §2, §5)",
                    )
                    seen += 1
                    hand = self.step(hand, "check-call")
                self.assertGreaterEqual(seen, 5, "the walk must reach several decisions")


if __name__ == "__main__":
    unittest.main()
