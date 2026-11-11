"""ENG-9 and ENG-10 -- the equity question, and the global `random` stream.

``docs/L2/engine/surface.md`` §1, §11; ``docs/L2/engine/environment.md`` §4, §5;
``docs/L3/engine/equity.md`` §1-§4; ``docs/L3/engine/stream.md`` §1;
``docs/L1/battery.md`` §3 FAM-4, FAM-16 (ASM-2, ASM-4).

`equity` is a query and not a step: it answers from the acting seat's cards and
the board, the same number from the hand and from that hand's readout, and it
hands the global stream back exactly as it found it.  Every other entry point
leaves the stream alone too, because `new_hand` is the project's single seeding
point.
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


class ENG9Equity(S.EngineCase):
    """`equity` answers one question about one decision, repeatably."""

    def test_eng9_1_the_first_decisions_estimate_is_a_probability_and_repeats(self):
        """ENG-9.1 equity at a first decision is a number in [0, 1], and the same
        arguments give the same value twice (surface.md §11, equity.md §4)."""
        first = self.equity(self.hand(S.SEED_A), S.SEED_A, S.SAMPLES_COARSE)
        self.assertTrue(S.is_number(first), "equity returns a number")
        self.assertGreaterEqual(first, 0.0, "a win share cannot be negative")
        self.assertLessEqual(first, 1.0, "a win share cannot exceed one")
        self.assertEqual(first, self.equity(self.hand(S.SEED_A), S.SEED_A, S.SAMPLES_COARSE),
                         "one decision, one seed and one sample count give one estimate")
        for seed in (S.SEED_C, S.SEED_F):
            with self.subTest(seed=seed):
                value = self.equity(self.hand(seed), seed, S.SAMPLES_COARSE)
                self.assertTrue(S.is_number(value), "equity returns a number")
                self.assertGreaterEqual(value, 0.0, "a win share cannot be negative")
                self.assertLessEqual(value, 1.0, "a win share cannot exceed one")
                self.assertEqual(
                    value, self.equity(self.hand(seed), seed, S.SAMPLES_COARSE),
                    "one decision, one seed and one sample count give one estimate "
                    "(surface.md §11)",
                )

    def test_eng9_2_the_hand_and_its_readout_answer_identically(self):
        """ENG-9.2 equity(hand, seed, samples) equals equity(readout(hand), seed, samples)
        to the bit, at the first decision and mid-hand (surface.md §11, equity.md §2)."""
        seed = S.SEED_B
        hand = self.hand(seed)
        for step in range(3):
            with self.subTest(decision=step):
                from_hand = self.equity(hand, seed, S.SAMPLES_MID)
                from_readout = self.equity(self.readout(hand), seed, S.SAMPLES_MID)
                self.assertEqual(
                    from_hand, from_readout,
                    "the readout already carries the acting seat's cards and the board, so both "
                    "argument shapes denote the same decision and return the same number "
                    "(surface.md §11, equity.md §2)",
                )
                self.assertGreaterEqual(from_hand, 0.0)
                self.assertLessEqual(from_hand, 1.0)
            hand = self.step(hand, "check-call")

    def test_eng9_3_a_coarse_count_and_a_small_count_are_legal_calls(self):
        """ENG-9.3 the battery's own coarse sample count (149) and its own small count (11)
        are accepted, in [0, 1] and bit-exactly repeatable: the count is the caller's
        accuracy knob, not a validity rule (surface.md §11, equity.md §1)."""
        hand = self.hand(S.SEED_D)
        for samples in (S.SAMPLES_COARSE, S.SAMPLES_TINY):
            value = self.equity(hand, S.SEED_D, samples)
            self.assertTrue(S.is_number(value),
                            "a sample count of %d is a legal call, not an error (surface.md §11)"
                            % samples)
            self.assertGreaterEqual(value, 0.0,
                                    "a coarse sample count is a legal call (surface.md §11)")
            self.assertLessEqual(value, 1.0,
                                 "a small sample count is a legal call (equity.md §1)")
            self.assertEqual(
                value, self.equity(hand, S.SEED_D, samples),
                "one decision, seed and sample count give one estimate, whatever the count is "
                "(surface.md §11, equity.md §1)",
            )

    def test_eng9_4_the_query_mutates_nothing_and_leaves_the_hand_playable(self):
        """ENG-9.4 equity leaves the hand, its readout and the global stream exactly as it
        found them, and the hand can still be advanced afterwards (surface.md §11,
        equity.md §4, environment.md §4)."""
        hand = self.hand(S.SEED_E)
        before = self.readout(hand)
        stream = random.getstate()
        self.equity(hand, S.SEED_E, S.SAMPLES_COARSE)
        self.equity(before, S.SEED_E, S.SAMPLES_TINY)
        self.assertEqual(random.getstate(), stream,
                         "equity hands the global stream back in the state it found it "
                         "(stream.md §1)")
        self.assertEqual(self.readout(hand), before,
                         "equity neither advances nor mutates the hand it is asked about")
        advanced = self.step(hand, "raise")
        after = self.readout(advanced)
        self.assertEqual(
            len(after["history"]), len(before["history"]) + 1,
            "the hand can still be advanced after an equity query: %r" % (after,),
        )
        self.assertGreater(
            after["pot"], before["pot"],
            "the raise the hand applied after the query moved chips into the pot: %r" % (after,),
        )
        self.assertEqual(after["pot"] + sum(S.numbers(after["stacks"])), 40,
                         "the advanced hand still conserves the table's chips")

    def test_eng9_5_equity_refuses_a_bad_decision_seed_or_sample_count(self):
        """ENG-9.5 a mapping is a decision only when `hole` is exactly two card strings of
        the declared spelling and `board` is 0, 3, 4 or 5 of them; a mapping missing either,
        or carrying a wrong count or a non-card, is refused, as are a non-mapping decision,
        a finished hand, a non-integer seed and a non-positive sample count, and no refusal
        moves anything (surface.md §11, equity.md §1, errors.md §4)."""
        running = self.hand(S.SEED_A)
        facts = self.readout(running)
        hole = list(facts["hole"])
        free = [rank + suit for rank in S.RANKS for suit in S.SUITS if rank + suit not in hole]
        malformed = (
            ("a mapping with no hole", {"board": []}),
            ("a mapping with no board", {"hole": hole}),
            ("a hole of one card", {"hole": hole[:1], "board": []}),
            ("a hole of three cards", {"hole": hole + free[:1], "board": []}),
            ("a non-card in the hole", {"hole": [hole[0], "Zz"], "board": []}),
            ("a board of one card", {"hole": hole, "board": free[:1]}),
            ("a board of two cards", {"hole": hole, "board": free[:2]}),
            ("a board of six cards", {"hole": hole, "board": free[:6]}),
            ("a non-card on the board", {"hole": hole, "board": free[:2] + ["Zz"]}),
        )
        finished = self.played_out(S.SEED_B)
        stream = random.getstate()
        for label, bad in (("None", None), ("an int", 5), ("a float", 3.5)) + malformed:
            with self.subTest(decision=label):
                exc = self.refusal(S.ep("equity"), bad, S.SEED_A, S.SAMPLES_MID)
                self.assert_mentions(exc, "decision", "hand", "readout")
        exc = self.refusal(S.ep("equity"), finished, S.SEED_B, S.SAMPLES_MID)
        self.assert_mentions(exc, "over", "hand", "decision")
        for bad_seed in ("20260101", 4242424.0, None):
            with self.subTest(seed=bad_seed):
                exc = self.refusal(S.ep("equity"), running, bad_seed, S.SAMPLES_MID)
                self.assert_mentions(exc, "seed")
        for bad_samples in (0, -5, 2.5, None, True):
            with self.subTest(samples=bad_samples):
                exc = self.refusal(S.ep("equity"), running, S.SEED_A, bad_samples)
                self.assert_mentions(exc, "sample")
        self.assertEqual(random.getstate(), stream,
                         "a refused equity call is refused before any sampling, so it cannot "
                         "move the stream (equity.md §1, stream.md §1)")
        self.assertEqual(self.readout(running), facts, "the refusals changed nothing")

    def test_eng9_6_a_well_formed_readout_with_extra_caller_keys_is_accepted(self):
        """ENG-9.6 the positive control beside the malformed-mapping refusals: a readout
        mapping that carries extra caller keys beside `hole` and `board` is accepted and
        answers the same number as the plain readout, and so is a mapping carrying only
        those two facts -- the other eight facts are not inspected, so refusing every
        mapping is a defect (errors.md §4, equity.md §1)."""
        seed = S.SEED_C
        hand = self.hand(seed)
        for _attempt in range(S.MAX_DECISIONS):
            facts = self.readout(hand)
            if facts["street"] != "preflop":
                break
            hand = self.step(hand, "check-call")
        else:  # pragma: no cover - the defect this case exists for
            self.fail("the hand did not reach the flop within %d applied actions"
                      % S.MAX_DECISIONS)
        self.assertIn(len(facts["board"]), S.BOARD_SIZES,
                      "a decision's board carries 0, 3, 4 or 5 cards (readout.md §2)")

        plain = self.equity(facts, seed, S.SAMPLES_MID)
        self.assertTrue(S.is_number(plain), "a readout mapping is an accepted decision")
        self.assertGreaterEqual(plain, 0.0, "a win share cannot be negative")
        self.assertLessEqual(plain, 1.0, "a win share cannot exceed one")

        augmented = dict(facts)
        augmented["caller_note"] = "not a fact of the readout"
        augmented["caller_budget"] = S.SAMPLES_MID
        augmented["caller_seat_hint"] = (0, True)
        self.assertEqual(
            self.equity(augmented, seed, S.SAMPLES_MID), plain,
            "extra caller keys beside the two facts are ignored: they neither change nor "
            "refuse the answer (errors.md §4)",
        )

        minimal = {"hole": list(facts["hole"]), "board": list(facts["board"])}
        self.assertEqual(
            self.equity(minimal, seed, S.SAMPLES_MID), plain,
            "the question needs only the acting seat's two cards and the board; the other "
            "eight facts are not inspected (errors.md §4, equity.md §1)",
        )


    def test_eng9_7_the_two_seat_answer_is_the_pre_change_enumeration(self):
        """ENG-9.7 on both two-seat shapes the answer is exactly the one this module has
        always given: the unseen deck's every two-card combination, enumerated in
        `Deck.STANDARD` order as the opponent range, through
        `pokerkit.analysis.calculate_equities` -- compared bit for bit at several
        decisions of both two-seat shapes (surface.md §11, equity.md §3, shapes.md §5)."""
        import itertools

        from pokerkit.analysis import calculate_equities
        from pokerkit.hands import StandardHighHand
        from pokerkit.utilities import Card, Deck

        def card(spelling):
            """The library's card a readout spelling names (readout.md §3)."""
            return Card(spelling[0], spelling[1])

        def pre_change_answer(hole, board, seed, samples):
            """The two-seat estimate computed the way this module computed it before D-33.

            The sample universe is the unseen deck's every two-card combination in
            `Deck.STANDARD` order -- never a set iteration -- so the estimate is the old
            algorithm's and not a second implementation of the new one (equity.md §3).
            """
            hole = [card(spelling) for spelling in hole]
            board = [card(spelling) for spelling in board]
            unseen = [value for value in Deck.STANDARD
                      if value not in set(hole + board)]
            ranges = (
                [list(hole)],
                [[first, second] for first, second in itertools.combinations(unseen, 2)],
            )
            saved = random.getstate()
            try:
                random.seed(seed)
                values = calculate_equities(
                    ranges,
                    list(board),
                    2,
                    5,
                    Deck.STANDARD,
                    (StandardHighHand,),
                    sample_count=samples,
                )
            finally:
                random.setstate(saved)
            return float(values[0])

        checked = 0
        for shape in (S.DEFAULT_SHAPE, S.NO_LIMIT_SHAPE):
            for seed in (S.SEED_A, S.SEED_F):
                hand = self.shaped_hand(seed, shape)
                for decision in range(3):
                    if self.terminal(hand):
                        break
                    facts = self.readout(hand)
                    expected = pre_change_answer(
                        facts["hole"], facts["board"], S.SEED_C, S.SAMPLES_MID
                    )
                    with self.subTest(shape=shape, seed=seed, decision=decision):
                        self.assertEqual(
                            self.equity(hand, S.SEED_C, S.SAMPLES_MID), expected,
                            "a two-seat hand's estimate is exactly the old enumeration's: "
                            "the unseen two-card combinations in Deck.STANDARD order as the "
                            "opponent range (equity.md §3, shapes.md §5): %r on %r at seed "
                            "%r, decision %d, against the reimplementation's %r"
                            % (self.equity(hand, S.SEED_C, S.SAMPLES_MID), shape, seed,
                               decision, expected),
                        )
                        self.assertEqual(
                            self.equity(facts, S.SEED_C, S.SAMPLES_MID), expected,
                            "and the readout form of that decision answers the same old "
                            "number, because both carry the same two cards and board "
                            "(surface.md §11, equity.md §3): %r against %r"
                            % (self.equity(facts, S.SEED_C, S.SAMPLES_MID), expected),
                        )
                    checked += 1
                    hand = self.step(hand, "check-call")
        self.assertGreaterEqual(
            checked, 6,
            "the cross-check reads several decisions of both two-seat shapes, or it says "
            "nothing about the unchanged path (shapes.md §5): it read %d" % (checked,),
        )

    def test_eng9_8_the_six_seat_question_is_six_way(self):
        """ENG-9.8 a decision whose readout carries six stacks is asked against the other
        five seats' uniformly random hands: the answer is a probability in [0, 1], 1.0 for
        the nuts the opponents cannot tie, near zero for a known-weak hand, the same number
        twice for one readout, and the global stream is handed back as it was found
        (surface.md §11, environment.md §4, seats.md §2, D-33)."""
        six_stacks = [100, 99, 98, 100, 100, 100]
        nuts = {"hole": ("As", "Ks"), "board": ("Qs", "Js", "Ts"), "stacks": six_stacks}
        weak = {"hole": ("2c", "7d"), "board": ("As", "Ks", "Qs"), "stacks": six_stacks}
        seed = S.SEED_C
        samples = S.SAMPLES_MID

        value = self.equity(nuts, seed, samples)
        self.assertTrue(S.is_number(value), "equity returns a number (surface.md §11)")
        self.assertGreaterEqual(value, 0.0, "a share of the pot is never negative")
        self.assertLessEqual(value, 1.0, "a share of the pot never exceeds one")
        self.assertEqual(
            value, 1.0,
            "As Ks over Qs Js Ts is a royal flush, and the opponents cannot tie it because "
            "As and Ks are the acting seat's own cards, so a six-way query answers 1.0 "
            "(surface.md §11, seats.md §2): got %r" % (value,),
        )

        weak_value = self.equity(weak, seed, samples)
        self.assertGreaterEqual(
            weak_value, 0.0,
            "a share of the pot is never negative (surface.md §11): got %r" % (weak_value,),
        )
        self.assertLessEqual(
            weak_value, 1.0,
            "a share of the pot never exceeds one (surface.md §11): got %r" % (weak_value,),
        )
        self.assertLess(
            weak_value, 0.1,
            "2c 7d over As Ks Qs is a known-weak hand against five random ones, so its "
            "six-way share is near zero (surface.md §11, seats.md §2): measured %r"
            % (weak_value,),
        )

        stream = random.getstate()
        self.assertEqual(
            self.equity(nuts, seed, samples), value,
            "one readout, one seed and one sample count give one estimate, so the six-way "
            "question repeats (surface.md §11): %r against %r"
            % (self.equity(nuts, seed, samples), value),
        )
        self.assertEqual(
            self.equity(weak, seed, samples), weak_value,
            "and a second query of the weak hand reads the same number (surface.md §11): "
            "%r against %r" % (self.equity(weak, seed, samples), weak_value),
        )
        self.assertEqual(
            random.getstate(), stream,
            "a six-way query saves and restores the global stream like a two-way one "
            "(surface.md §11, equity.md §4, stream.md §1)",
        )

        # The opponents are the other seats', so the same two cards are worth less six-way
        # than heads-up: the seat count is read from the readout's stacks fact (seats.md §2).
        middle = ("As", "Kd")
        six_way = self.equity(
            {"hole": middle, "board": (), "stacks": six_stacks}, seed, S.SAMPLES_COARSE
        )
        heads_up = self.equity(
            {"hole": middle, "board": (), "stacks": [100, 100]}, seed, S.SAMPLES_COARSE
        )
        self.assertLess(
            six_way, heads_up,
            "the same hole cards are worth less against five random hands than against one, "
            "so the seat count decides how many opponents the question holds (seats.md §2, "
            "surface.md §11): six-way %r against heads-up %r" % (six_way, heads_up),
        )


class ENG10Stream(S.EngineCase):
    """Only `new_hand` seeds; every other entry point hands the stream back."""

    def test_eng10_1_reading_the_game_and_the_facts_draws_nothing(self):
        """ENG-10.1 game_config, readout and legal_actions leave random.getstate()
        byte-identical (surface.md §1, stream.md §1, guardrails G4)."""
        random.seed(S.SEED_F)
        before = random.getstate()
        self.config()
        self.assertEqual(random.getstate(), before,
                         "game_config draws no randomness (stream.md §1)")
        hand = self.hand(S.SEED_A)
        self.assert_stream_untouched(self.readout, hand)
        self.assert_stream_untouched(self.legal, hand)

    def test_eng10_2_stepping_and_ending_draw_nothing(self):
        """ENG-10.2 apply_action, is_terminal and payoffs leave random.getstate()
        byte-identical (surface.md §1, §7, stream.md §1)."""
        hand = self.hand(S.SEED_C)
        self.assert_stream_untouched(self.terminal, hand)
        advanced = self.assert_stream_untouched(self.step, hand, "check-call")
        self.assert_stream_untouched(self.readout, advanced)
        finished = self.played_out(S.SEED_D)
        self.assert_stream_untouched(self.payoffs, finished)

        walk, _ = self.drive(S.SEED_B, S.always_raise)
        hand = self.hand(S.SEED_B)
        stream = random.getstate()
        for _facts, _legal, action in walk:
            hand = self.step(hand, action)
        self.assertEqual(
            random.getstate(), stream,
            "a whole played-out hand moves no stream: the deck was fixed when the hand was "
            "created (surface.md §4, hand.md §2)",
        )

    def test_eng10_3_an_equity_query_hands_the_stream_back(self):
        """ENG-10.3 equity leaves random.getstate() byte-identical, from a readout as well,
        and even when it refuses (surface.md §1, equity.md §4, stream.md §1)."""
        hand = self.hand(S.SEED_A)
        facts = self.readout(hand)
        random.seed(S.SEED_D)
        before = random.getstate()
        self.equity(hand, S.SEED_A, S.SAMPLES_COARSE)
        self.assertEqual(random.getstate(), before,
                         "equity saves the stream, seeds its own sample and restores it "
                         "(stream.md §1)")
        self.equity(facts, S.SEED_B, S.SAMPLES_TINY)
        self.assertEqual(random.getstate(), before,
                         "the readout form of the question restores the stream too")
        self.refusal(S.ep("equity"), hand, S.SEED_A, 0)
        self.assertEqual(random.getstate(), before,
                         "a refused sample count is refused before sampling, so the stream is "
                         "still the caller's (equity.md §1)")

    def test_eng10_4_the_deal_does_not_depend_on_the_stream_while_playing(self):
        """ENG-10.4 draws a caller makes between two steps do not change the hand: the
        deck was fixed when the hand was created (surface.md §4, advance.md §1,
        hand.md §2)."""
        clean, finished_clean = self.drive(S.SEED_E, S.always_call)
        hand = self.hand(S.SEED_E)
        injected = []
        while not self.terminal(hand):
            random.random()
            readout = self.readout(hand)
            injected.append(readout)
            hand = self.step(hand, "check-call")
        self.assertEqual(
            [entry[0] for entry in clean], injected,
            "the whole card order is fixed when the hand is created, so a caller's own draws "
            "between two steps cannot change the hand in flight (surface.md §4, advance.md §1)",
        )
        self.assertEqual(
            dict(self.payoffs(hand)), dict(self.payoffs(finished_clean)),
            "the hand played beside a caller's draws pays what the clean hand paid",
        )


if __name__ == "__main__":
    unittest.main()
