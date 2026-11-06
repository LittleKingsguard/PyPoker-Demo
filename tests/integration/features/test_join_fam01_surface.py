"""FAM-1 — the seven names exist, are callable, and a minimal call returns its kind.

`docs/L2/features/surface.md` §1 and §3–§9, `docs/L1/e2e-surface.md` §3.2,
`docs/L1/battery.md` §3 FAM-1.  One case per entry point, in the surface document's
order, so that a missing name is one finding per name.  Each case asserts presence,
callability and the kind the surface declares — never a contract a later family owns.

Every call here is made at the module join: the readout is `engine.readout`'s own, the
descriptors are `engine.legal_actions`' own, and the descriptor a case decodes is handed
to `engine.apply_action`, so the kind a case asserts is the kind the other module can
use (`docs/L1/e2e-surface.md` §2, D-13).
"""

import os
import sys
import unittest

try:  # collected as part of a package
    from . import _join_support as S
except ImportError:  # collected as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _join_support as S  # noqa: E402


class FAM1Surface(S.JoinCase):
    """The declared surface of the `features` package, name by name."""

    def test_fam1_0_the_seven_names_are_module_level_and_callable(self):
        """FAM-1.0 the seven fixed names are module-level names of `features` (§1)."""
        package = S.module(S.FEATURES)
        for name in S.ENTRY_POINTS:
            with self.subTest(name=name):
                self.assertTrue(
                    hasattr(package, name),
                    "surface absent: features.%s is not a module-level name of the "
                    "package (surface.md §1, layout.md §2)" % (name,),
                )
                self.assertTrue(
                    callable(getattr(package, name)),
                    "features.%s is not callable (surface.md §1)" % (name,),
                )

    def test_fam1_1_encodings_returns_the_two_declared_records_in_ladder_order(self):
        """FAM-1.1 features.encodings() returns a mapping keyed by the two names (§3)."""
        declared = self.encodings()
        self.assertTrue(
            S.is_mapping(declared),
            "features.encodings() must return a mapping of encoding names to their spec "
            "records (surface.md §3); got %r" % (declared,),
        )
        self.assertEqual(
            list(declared),
            list(S.ENCODING_NAMES),
            "the catalogue holds the two declared encodings and no third, in the "
            "ladder's order — flat-numeric then card-tokens (surface.md §3, ladder.md "
            "§2); got %r" % (list(declared),),
        )
        for name in S.ENCODING_NAMES:
            with self.subTest(encoding=name):
                self.assertTrue(
                    S.is_mapping(declared[name]),
                    "%r must map to the record observation_spec returns for it "
                    "(surface.md §3); got %r" % (name, declared[name]),
                )

    def test_fam1_2_build_encoder_returns_an_opaque_value_observation_spec_accepts(self):
        """FAM-1.2 features.build_encoder(name) returns an encoder (§4)."""
        for name in S.ENCODING_NAMES:
            with self.subTest(encoding=name):
                encoder = self.build_encoder(name)
                self.assertFalse(
                    S.is_plain(encoder),
                    "an encoder is opaque: a caller only hands it back to "
                    "observation_spec and encode (surface.md §1, §4); build_encoder(%r) "
                    "returned plain data %r" % (name, encoder),
                )
                spec = self.observation_spec(encoder)
                self.assertTrue(
                    S.is_mapping(spec),
                    "the value build_encoder(%r) returns is a value observation_spec "
                    "accepts (surface.md §4); it returned %r" % (name, spec),
                )

    def test_fam1_3_observation_spec_returns_the_six_key_record(self):
        """FAM-1.3 features.observation_spec(encoder) returns one mapping (§5)."""
        for name in S.ENCODING_NAMES:
            with self.subTest(encoding=name):
                spec = self.spec(name)
                self.assertTrue(
                    S.is_mapping(spec),
                    "features.observation_spec must return one mapping (surface.md §5); "
                    "got %r" % (spec,),
                )
                self.assertEqual(
                    set(spec),
                    set(S.SPEC_KEYS),
                    "the spec record carries exactly the six declared keys "
                    "(surface.md §5); the spec of %r carries %r"
                    % (name, sorted(str(key) for key in spec)),
                )

    def test_fam1_4_encode_returns_one_array_of_the_declared_shape(self):
        """FAM-1.4 features.encode(encoder, readout) returns one observation (§6)."""
        readout = self.readout(self.new_hand(S.SEED_ENCODE))
        for name in S.ENCODING_NAMES:
            with self.subTest(encoding=name):
                spec = self.spec(name)
                observation = self.encode(self.encoder(name), readout)
                self.assert_observation(name, spec, observation)
                self.assertEqual(
                    len(observation),
                    self.declared_shape(spec)[0],
                    "the observation is the declared shape's one dimension long "
                    "(surface.md §5, §6): %r" % (tuple(observation.shape),),
                )

    def test_fam1_5_action_space_returns_the_three_index_mapping(self):
        """FAM-1.5 features.action_space() returns a mapping keyed 0, 1, 2 (§7)."""
        space = self.action_space()
        self.assertTrue(
            S.is_mapping(space),
            "features.action_space() must return one mapping (surface.md §7); got %r"
            % (space,),
        )
        self.assertEqual(
            set(space),
            set(S.ACTION_INDICES),
            "the vocabulary is keyed by the three indices 0, 1 and 2 (surface.md §7); "
            "got %r" % (sorted(str(key) for key in space),),
        )
        for index in S.ACTION_INDICES:
            with self.subTest(index=index):
                self.assertTrue(
                    S.is_plain(space[index]),
                    "each index's value is a plain record (surface.md §1, §7); index %r "
                    "carries %r" % (index, space[index]),
                )

    def test_fam1_6_legal_indices_returns_an_indexable_sequence_of_ints(self):
        """FAM-1.6 features.legal_indices(legal_actions) returns the indices (§8)."""
        hand = self.new_hand(S.SEED_MASK)
        indices = self.legal_indices(self.legal_actions(hand))
        self.assertTrue(
            S.is_indexable(indices),
            "features.legal_indices must return an ordered, indexable sequence "
            "(surface.md §8); got %r" % (indices,),
        )
        self.assertGreaterEqual(
            len(indices),
            1,
            "a decision has at least one legal action, so one index (surface.md §8): %r"
            % (indices,),
        )
        for position in range(len(indices)):
            with self.subTest(position=position):
                self.assertTrue(
                    S.is_count(indices[position]),
                    "the %d-th legal index must be an integer (surface.md §8); got %r"
                    % (position, indices[position]),
                )
                self.assertIn(
                    int(indices[position]),
                    S.ACTION_INDICES,
                    "a legal index is one of the three vocabulary indices "
                    "(surface.md §2, §8); got %r" % (indices[position],),
                )

    def test_fam1_7_decode_action_returns_a_descriptor_the_engine_accepts(self):
        """FAM-1.7 features.decode_action(1) returns the check/call descriptor (§9)."""
        descriptor = self.decode_action(1)
        self.assertIsInstance(
            descriptor,
            str,
            "a descriptor is plain data the engine accepts (surface.md §1, §9); "
            "decode_action(1) returned %r" % (descriptor,),
        )
        self.assertEqual(
            S.descriptor_kind(descriptor),
            "check-call",
            "index 1 is check/call, so its descriptor names that action "
            "(surface.md §2, §9); got %r" % (descriptor,),
        )
        hand = self.new_hand(S.SEED_DECODE)
        self.assertIn(
            1,
            [int(index) for index in self.legal_indices(self.legal_actions(hand))],
            "check/call is legal at a first decision, so index 1 is in the mask "
            "(surface.md §2, §8)",
        )
        advanced = self.apply_action(hand, descriptor)
        self.assertIsNotNone(
            advanced,
            "decode_action(1) must return a descriptor engine.apply_action accepts at "
            "the decision whose mask holds index 1 (surface.md §9): %r" % (descriptor,),
        )

    def test_fam1_8_no_entry_point_takes_an_argument_it_does_not_declare(self):
        """FAM-1.8 none of the seven takes a seed, a rung or any fourth argument (§1)."""
        encoder = self.encoder("flat-numeric")
        readout = self.readout(self.new_hand(S.SEED_ENCODE))
        calls = {
            "encodings(seed)": lambda: self.ep("encodings")(S.SEED_ENCODE),
            "action_space(seed)": lambda: self.ep("action_space")(S.SEED_ENCODE),
            "build_encoder(name, seed)": lambda: self.ep("build_encoder")(
                "flat-numeric", S.SEED_ENCODE
            ),
            "observation_spec(encoder, seed)": lambda: self.ep("observation_spec")(
                encoder, S.SEED_ENCODE
            ),
            "encode(encoder, readout, seed)": lambda: self.ep("encode")(
                encoder, readout, S.SEED_ENCODE
            ),
            "legal_indices(legal, seed)": lambda: self.ep("legal_indices")(
                ("fold",), S.SEED_ENCODE
            ),
            "decode_action(index, seed)": lambda: self.ep("decode_action")(
                1, S.SEED_ENCODE
            ),
        }
        for what, call in calls.items():
            with self.subTest(call=what):
                self.assert_refused(
                    call,
                    "%s must be refused, because no entry point takes a seed, a rung "
                    "or a game parameter (surface.md §1)" % (what,),
                )


if __name__ == "__main__":
    unittest.main()
