"""FAM-2 — the game, the action vocabulary and the information set never move.

`docs/L1/battery.md` §3 FAM-2, `docs/L1/e2e-surface.md` §2, D-2 and D-3.  The ladder
changes how the agent *represents* what it knows (D-3); it never changes what it knows
(the readout facts of `e2e-surface.md` §2), the vocabulary it chooses from, or the game
it plays (D-2).  Rev 2 did not move any of that: D-16 changed the opponent, and the
league's cells are played on the same game, from the same readout, over the same three
action indices.  These cases hold the invariance across every rung and every declared
encoding, and they are the invariants a single module cannot check about itself
(`battery.md` §5).
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


class FAM2Invariance(S.SurfaceCase):
    """The D-2 and D-3 invariants, held across the whole ladder."""

    def encoding_names(self):
        """The declared encoding names, read from ``features.encodings()``."""
        declared = self.ep("features", "encodings")()
        found = []
        for text in S.strings(declared):
            if text in (S.FLAT, S.TOKENS) and text not in found:
                found.append(text)
        self.assertEqual(
            sorted(found),
            sorted([S.FLAT, S.TOKENS]),
            "features.encodings() must declare %r and %r with their representation kind; got %r"
            % (S.FLAT, S.TOKENS, declared),
        )
        return found

    def spec(self, encoding):
        return self.ep("features", "observation_spec")(self.encoder(encoding))

    def test_fam2_1_game_config_is_one_fixed_declaration(self):
        """FAM-2.1 engine.game_config is deterministic and is ASM-6's fixed game (D-2)."""
        config = self.ep("engine", "game_config")()
        again = self.ep("engine", "game_config")()
        self.assertEqual(S.canon(config), S.canon(again), "game_config() changed between calls")
        values = set(S.numbers(config))
        for declared in (20, 4):
            self.assertIn(
                declared,
                values,
                "the fixed game of e2e-surface.md §3.1 must declare %d; got %r" % (declared, config),
            )
        self.assertIn(2, values, "the fixed game must declare its two seats or its blinds")

    def test_fam2_2_the_dealt_game_has_the_fixed_parameters(self):
        """FAM-2.2 a first decision shows blinds 1/2 and stacks 20 (ASM-6, D-2)."""
        readout = self.readout(self.hand(S.SEED_A))
        self.assertEqual(readout["street"], "preflop")
        self.assertEqual(readout["pot"], 3, "the blinds committed to the pot must be 1 + 2")
        self.assertEqual(sum(S.numbers(readout["stacks"])), 37,
                         "the two stacks must hold 20 + 20 - 3 chips")
        self.assertEqual(readout["to_call"], 1, "the button owes the big blind one chip")

    def test_fam2_3_readout_has_exactly_the_declared_facts(self):
        """FAM-2.3 readout returns exactly the ten facts of e2e-surface.md §2."""
        readout = self.readout(self.hand(S.SEED_A))
        self.assertEqual(
            set(readout),
            set(S.READOUT_FACTS),
            "readout's keys must be exactly the declared information set",
        )

    def test_fam2_4_every_encoding_carries_the_same_fields(self):
        """FAM-2.4 features.observation_spec fields are identical for every encoding."""
        fields = {}
        for encoding in self.encoding_names():
            spec = self.spec(encoding)
            carried = spec["fields"]
            fields[encoding] = set(str(field) for field in carried)
        first = next(iter(fields.values()))
        for encoding, carried in fields.items():
            self.assertEqual(
                carried,
                first,
                "the ladder must not change what the agent may know: %r carries %r, not %r"
                % (encoding, sorted(carried), sorted(first)),
            )

    def test_fam2_5_observation_fields_are_readout_facts(self):
        """FAM-2.5 the encoded fields are a subset of the readout facts (D-3)."""
        for encoding in self.encoding_names():
            spec = self.spec(encoding)
            carried = set(str(field) for field in spec["fields"])
            self.assertTrue(carried, "%r carries no observation at all" % (encoding,))
            self.assertTrue(
                carried <= set(S.READOUT_FACTS),
                "%r carries fields that are not readout facts: %r"
                % (encoding, sorted(carried - set(S.READOUT_FACTS))),
            )

    def test_fam2_6_representation_names_the_encoding(self):
        """FAM-2.6 observation_spec names the representation of §2."""
        for encoding in self.encoding_names():
            spec = self.spec(encoding)
            text = S.flatten_text(spec["representation"])
            self.assertIn(
                S._family_token(encoding),
                S._family_token(text),
                "the spec of %r must declare representation %r; got %r"
                % (encoding, encoding, spec["representation"]),
            )

    def test_fam2_7_spec_declares_shape_and_dtype(self):
        """FAM-2.7 observation_spec declares the shape and dtype of one observation."""
        for encoding in self.encoding_names():
            spec = self.spec(encoding)
            self.assertIn("shape", spec, "the spec of %r declares no shape" % (encoding,))
            self.assertIn("dtype", spec, "the spec of %r declares no dtype" % (encoding,))
            self.assertTrue(S.flatten_text(spec["dtype"]).strip(),
                            "the spec of %r declares an empty dtype" % (encoding,))

    def test_fam2_8_encoded_observation_matches_the_declared_shape(self):
        """FAM-2.8 encode returns one observation of the declared shape."""
        readout = self.readout(self.hand(S.SEED_B))
        for encoding in self.encoding_names():
            encoder = self.encoder(encoding)
            spec = self.ep("features", "observation_spec")(encoder)
            observation = self.ep("features", "encode")(encoder, readout)
            shape = tuple(int(value) for value in S.numbers(spec["shape"]))
            if hasattr(observation, "shape"):
                self.assertEqual(tuple(observation.shape), shape,
                                 "%r returned a %r observation, declared %r"
                                 % (encoding, tuple(observation.shape), shape))
            else:
                self.assertEqual(len(observation), _product(shape),
                                 "%r returned %d values, declared %r"
                                 % (encoding, len(observation), shape))

    def test_fam2_9_action_space_is_the_three_index_vocabulary(self):
        """FAM-2.9 features.action_space is the fixed 0/1/2 vocabulary (D-2)."""
        space = self.ep("features", "action_space")()
        vocabulary = S.action_vocabulary(space)
        self.assertEqual(
            vocabulary,
            {0, 1, 2},
            "the vocabulary is the game's three indices — fold 0, check/call 1, raise 2 — "
            "however the container keys them, a sequence or a mapping keyed by name or by "
            "the indices themselves (e2e-surface §2): %r" % (space,),
        )

    def test_fam2_10_decode_action_round_trips_into_the_engine(self):
        """FAM-2.10 decode_action gives a descriptor apply_action accepts (D-2)."""
        legal = self.legal(self.hand(S.SEED_C))
        indices = list(self.ep("features", "legal_indices")(legal))
        self.assertTrue(indices, "no legal index at the first decision")
        self.assertTrue(set(indices) <= {0, 1, 2},
                        "legal indices outside the declared vocabulary: %r" % (indices,))
        for index in indices:
            descriptor = self.ep("features", "decode_action")(index)
            fresh = self.hand(S.SEED_C)
            advanced = self.ep("engine", "apply_action")(fresh, descriptor)
            self.assertIsNotNone(advanced,
                                 "decode_action(%r) gave a descriptor the engine refused" % (index,))

    def test_fam2_11_every_legal_descriptor_has_one_index(self):
        """FAM-2.11 the legal descriptors and the legal indices correspond one to one."""
        legal = self.legal(self.hand(S.SEED_C))
        indices = list(self.ep("features", "legal_indices")(legal))
        self.assertEqual(
            len(indices),
            len(legal),
            "one index per legal descriptor: %r descriptors, %r indices"
            % (len(legal), len(indices)),
        )
        self.assertEqual(
            len(set(indices)),
            len(indices),
            "the indices of one decision are distinct: %r" % (indices,),
        )
        for index in indices:
            descriptor = self.ep("features", "decode_action")(index)
            advanced = self.ep("engine", "apply_action")(self.hand(S.SEED_C), descriptor)
            self.assertIsNotNone(
                advanced,
                "decode_action(%r) must give a descriptor the engine accepts at this "
                "decision" % (index,),
            )


def _product(values):
    total = 1
    for value in values:
        total *= int(value)
    return total


if __name__ == "__main__":
    unittest.main()
