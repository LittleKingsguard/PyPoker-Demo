"""ENG-1 and ENG-2 -- the declared surface, and the fixed game it declares.

``docs/L2/engine/surface.md`` §1, §3; ``docs/L3/engine/layout.md`` §2;
``docs/L1/battery.md`` §3 FAM-1 and FAM-2; D-12.

Every case here is red against absent code, which is the expected state of a
design-stage battery (``docs/L1/battery.md`` §1): the plumbing in
``_engine_support`` turns "``src/engine/`` is not there yet" into one clear
failure per case and never into a collection error.
"""

import os
import sys
import unittest

try:  # discovered as part of a tests.engine package
    from . import _engine_support as S
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _engine_support as S  # noqa: E402


class ENG1Surface(S.EngineCase):
    """The nine names exist, are callable, and return their declared kinds."""

    def test_eng1_1_the_nine_names_exist_are_callable_and_return_their_kind(self):
        """ENG-1.1 the nine declared names exist, are callable, and a minimal call
        returns the declared kind (surface.md §1, environment.md §7 FAM-1)."""
        for name in S.NINE:
            with self.subTest(name=name):
                self.assertTrue(
                    callable(S.ep(name)),
                    "engine.%s must be a callable module-level name (surface.md §1)" % name,
                )

        self.assertTrue(S.is_mapping(self.config()), "game_config() returns a mapping")
        hand = self.hand(S.SEED_A)
        self.assertIsNotNone(hand, "new_hand(seed) returns a hand handle")
        self.assertTrue(S.is_mapping(self.readout(hand)), "readout(hand) returns a mapping")

        legal = self.legal(hand)
        self.assertGreaterEqual(len(legal), 1, "legal_actions(hand) returns at least one descriptor")
        self.assertIn(legal[0], S.ACTIONS, "legal_actions returns declared descriptors")

        kept = "check-call" if "check-call" in list(legal) else legal[0]
        stepped = self.step(hand, kept)
        self.assertIsNotNone(stepped, "apply_action(hand, descriptor) returns a handle")
        self.assertTrue(
            S.is_mapping(self.readout(stepped)),
            "the handle apply_action returns is a hand readout accepts",
        )

        self.assertIsInstance(self.terminal(hand), bool, "is_terminal(hand) returns a boolean")

        payoffs = self.payoffs(self.played_out(S.SEED_B))
        self.assertTrue(S.is_mapping(payoffs), "payoffs(finished hand) returns a mapping")

        record = self.episode(S.SEED_C)
        self.assertTrue(S.is_mapping(record), "play_hand(seed, p0, p1) returns a mapping")

        value = self.equity(hand, S.SEED_A, S.SAMPLES_MID)
        self.assertTrue(S.is_number(value), "equity(decision, seed, samples) returns a number")
        self.assertGreaterEqual(value, 0.0, "equity is a probability, so at least 0")
        self.assertLessEqual(value, 1.0, "equity is a probability, so at most 1")

    def test_eng1_2_the_nine_names_take_the_declared_argument_counts(self):
        """ENG-1.2 each entry point succeeds with exactly its declared arguments --
        game_config(), new_hand(seed), readout(hand), legal_actions(hand),
        apply_action(hand, action), is_terminal(hand), payoffs(hand),
        play_hand(seed, policy0, policy1), equity(decision, seed, samples) -- and a
        call that omits a declared argument raises TypeError from the call itself
        (e2e-surface.md §3.1 "Inputs", surface.md §3-§11)."""
        hand = self.hand(S.SEED_A)
        finished = self.played_out(S.SEED_B)
        policy = S.always_call
        # A descriptor that leaves the hand live, so that the advanced handle can be read:
        # check/call is legal at this first decision and does not end a heads-up hand
        # (surface.md §2, §6; advance.md §2).
        kept = "check-call"

        self.assertTrue(S.is_mapping(self.config()),
                        "game_config() takes no argument and returns the game's mapping")
        self.assertIsNotNone(self.hand(S.SEED_A), "new_hand(seed) takes its seed and returns a handle")
        self.assertTrue(S.is_mapping(self.readout(self.hand(S.SEED_A))),
                        "readout(hand) takes one hand handle")
        self.assertTrue(list(self.legal(self.hand(S.SEED_A))),
                        "legal_actions(hand) takes one hand handle")
        advanced = self.step(self.hand(S.SEED_A), kept)
        self.assertIsNotNone(
            advanced,
            "apply_action(hand, action) takes a handle and a descriptor and returns the "
            "advanced handle (surface.md §7)",
        )
        facts = self.readout(advanced)
        self.assertTrue(
            S.is_mapping(facts),
            "the handle apply_action returns is a live hand, and readout(hand) reads it as a "
            "mapping (surface.md §5, §7)",
        )
        self.assertEqual(
            set(facts), set(S.FACTS),
            "the mapping read from the advanced handle carries the ten facts, so both calls "
            "took their declared argument kinds (readout.md §2, surface.md §5)",
        )
        self.assertIsInstance(self.terminal(self.hand(S.SEED_A)), bool,
                              "is_terminal(hand) takes one hand handle")
        self.assertTrue(S.is_mapping(self.payoffs(finished)),
                        "payoffs(hand) takes one completed hand handle")
        self.assertTrue(
            S.is_mapping(self.episode(S.SEED_C, policy, policy)),
            "play_hand(seed, policy0, policy1) takes the seed and both policies",
        )
        value = self.equity(hand, S.SEED_A, S.SAMPLES_MID)
        self.assertTrue(S.is_number(value),
                        "equity(decision, seed, samples) takes all three declared arguments")

        # A missing declared argument is Python's own TypeError from the call, not one of
        # this module's refusals: assert only that it is a TypeError (e2e-surface.md §3.1).
        for name, supplied in (
            ("new_hand", ()),
            ("readout", ()),
            ("legal_actions", ()),
            ("apply_action", (hand,)),
            ("is_terminal", ()),
            ("payoffs", ()),
            ("play_hand", (S.SEED_A, policy)),
            ("equity", (hand, S.SEED_A)),
        ):
            with self.subTest(omitted_argument=name):
                with self.assertRaises(TypeError):
                    S.ep(name)(*supplied)


class ENG2Config(S.EngineCase):
    """`game_config` is one deterministic declaration of the fixed game."""

    def test_eng2_1_game_config_is_stable(self):
        """ENG-2.1 game_config() returns a non-empty mapping, and two calls are equal:
        there is no per-call state (surface.md §3, e2e-surface.md §3.1)."""
        first = self.config()
        self.assertTrue(S.is_mapping(first), "game_config() returns the game's parameters as one mapping")
        self.assertTrue(first, "game_config() declares the game, so it is not empty")
        self.assertEqual(
            first, self.config(),
            "two calls of game_config() return equal values: there is no per-call state "
            "(surface.md §3, D-2)",
        )

    def test_eng2_2_the_numbers_of_the_fixed_game_are_declared(self):
        """ENG-2.2 game_config's numbers include the blinds, the stacks, the two bet
        sizes and the raise cap (surface.md §3, battery.md §3 FAM-2)."""
        values = set(int(value) for value in S.numbers(self.config()))
        for declared, what in (
            (1, "the small blind"),
            (2, "the big blind and the small bet"),
            (4, "the big bet and the raise cap"),
            (20, "the starting stacks"),
        ):
            self.assertIn(
                declared, values,
                "the fixed game must declare %s as a number, not only as prose "
                "(surface.md §3): %r" % (what, self.config()),
            )

    def test_eng2_3_game_config_is_unchanged_by_dealing_and_playing(self):
        """ENG-2.3 a third call after hands have been dealt and played is still equal
        (surface.md §3: no seed, no hand, no rung in it)."""
        before = self.config()
        self.hand(S.SEED_A)
        self.played_out(S.SEED_B, S.always_raise)
        self.episode(S.SEED_C)
        self.assertEqual(
            self.config(), before,
            "game_config() must not depend on hands dealt or played before it (surface.md §3)",
        )


if __name__ == "__main__":
    unittest.main()
