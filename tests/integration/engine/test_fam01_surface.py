"""FAM-1 — the nine names exist, are callable, and a minimal call returns its kind.

`docs/L2/engine/surface.md` §1 and §3–§11, `e2e-surface.md` §3.1, `battery.md` §3
FAM-1.  One case per entry point, in the surface document's order, so that a missing
name is one finding per name.  Each case asserts presence, callability and the kind
the surface declares — never a contract a later family owns.
"""

import os
import sys
import unittest

try:  # collected as part of a package
    from . import _support as S
except ImportError:  # collected as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _support as S  # noqa: E402


class FAM1Surface(S.EngineCase):
    """The declared surface of the `engine` package, name by name."""

    def test_fam1_00_the_nine_names_are_module_level_and_callable(self):
        """FAM-1.0 the nine fixed names are module-level names of `engine` (§1)."""
        package = S.module()
        for name in S.ENTRY_POINTS:
            self.assertTrue(
                hasattr(package, name),
                "surface absent: engine.%s is not a module-level name (surface.md §1)"
                % (name,),
            )
            self.assertTrue(
                callable(getattr(package, name)),
                "engine.%s is not callable (surface.md §1)" % (name,),
            )

    def test_fam1_01_game_config_returns_a_mapping(self):
        """FAM-1.1 engine.game_config() returns the fixed game as one mapping (§3)."""
        config = self.game_config()
        self.assertTrue(
            S.is_mapping(config),
            "engine.game_config() must return the game's parameters as one mapping "
            "(surface.md §3); got %r" % (config,),
        )

    def test_fam1_02_new_hand_returns_a_handle_the_next_entry_point_accepts(self):
        """FAM-1.2 engine.new_hand(seed) returns a hand handle (§4)."""
        hand = self.new_hand(S.SEED_A)
        self.assertIsNotNone(hand, "engine.new_hand(seed) returned nothing (surface.md §4)")
        readout = self.readout(hand)
        self.assertTrue(
            S.is_mapping(readout),
            "the handle new_hand returns is a value readout accepts (surface.md §4); "
            "readout returned %r" % (readout,),
        )

    def test_fam1_03_readout_returns_a_mapping(self):
        """FAM-1.3 engine.readout(hand) returns the facts as a mapping (§5)."""
        readout = self.readout(self.new_hand(S.SEED_B))
        self.assertTrue(
            S.is_mapping(readout),
            "engine.readout(hand) must return a mapping of facts (surface.md §5); got %r"
            % (readout,),
        )

    def test_fam1_04_legal_actions_returns_an_ordered_non_empty_sequence(self):
        """FAM-1.4 engine.legal_actions(hand) returns an ordered sequence (§6)."""
        legal = self.legal_actions(self.new_hand(S.SEED_C))
        self.assertTrue(
            S.is_indexable(legal),
            "engine.legal_actions(hand) must return an ordered, indexable sequence "
            "(surface.md §6); got %r" % (legal,),
        )
        self.assertGreaterEqual(
            len(legal), 1, "a decision has at least one legal action (surface.md §6)"
        )
        self.assertIsNotNone(
            legal[0], "the sequence is indexable: legal[0] must be a descriptor (surface.md §6)"
        )

    def test_fam1_05_apply_action_returns_an_advanced_handle(self):
        """FAM-1.5 engine.apply_action(hand, descriptor) returns a handle (§7)."""
        hand = self.new_hand(S.SEED_D)
        action = S.choose_call(self.readout(hand), self.legal_actions(hand))
        advanced = self.apply_action(hand, action)
        self.assertIsNotNone(
            advanced, "engine.apply_action returned nothing (surface.md §7)"
        )
        self.assertIsInstance(
            self.is_terminal(advanced),
            bool,
            "the handle apply_action returns is a hand: is_terminal answers for it with a "
            "boolean (surface.md §7)",
        )

    def test_fam1_06_is_terminal_returns_a_real_bool(self):
        """FAM-1.6 engine.is_terminal(hand) returns a boolean, not a truthy object (§8)."""
        answer = self.is_terminal(self.new_hand(S.SEED_E))
        self.assertIsInstance(
            answer,
            bool,
            "engine.is_terminal must return a boolean, not a truthy object "
            "(surface.md §8); got %r" % (answer,),
        )

    def test_fam1_07_payoffs_returns_a_mapping(self):
        """FAM-1.7 engine.payoffs(hand) returns the per-seat deltas as a mapping (§9)."""
        payoffs = self.payoffs(self.finished_hand(S.SEED_F))
        self.assertTrue(
            S.is_mapping(payoffs),
            "engine.payoffs(completed hand) must return a mapping keyed by seat "
            "(surface.md §9); got %r" % (payoffs,),
        )

    def test_fam1_08_play_hand_returns_an_episode_mapping(self):
        """FAM-1.8 engine.play_hand(seed, policy0, policy1) returns a record (§10)."""
        episode = self.play_hand(
            S.SEED_G, S.PolicyProbe(name="seat 0"), S.PolicyProbe(name="seat 1")
        )
        self.assertTrue(
            S.is_mapping(episode),
            "engine.play_hand returns the episode record as one mapping "
            "(surface.md §10); got %r" % (episode,),
        )

    def test_fam1_09_equity_returns_a_number(self):
        """FAM-1.9 engine.equity(decision, seed, samples) returns a number (§11)."""
        hand = self.new_hand(S.SEED_H)
        value = self.equity(hand, S.SEED_H, S.SAMPLES_COARSE)
        self.assertTrue(
            S.is_number(value),
            "engine.equity must return a number in [0, 1] (surface.md §11); got %r"
            % (value,),
        )


if __name__ == "__main__":
    unittest.main()
