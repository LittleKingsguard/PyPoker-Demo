"""FEA-2 -- the declared encodings and the six-key observation spec.

``docs/L2/features/surface.md`` §3, §5; ``docs/L2/features/encodings.md`` §1-§4;
``docs/L3/features/encoder.md`` §3, §4, §6; ``docs/L3/features/guardrails.md``
G11; ``docs/L1/battery.md`` §3 FAM-2.
"""

import os
import sys
import unittest

import numpy

try:  # discovered as part of a tests.features package
    from . import _features_support as S
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _features_support as S  # noqa: E402


class FEA2Encodings(S.FeaturesCase):
    """`encodings` declares the two names, in the ladder's order, and equals the specs."""

    def test_fea2_1_encodings_declares_the_two_names_in_ladder_order(self):
        """FEA-2.1 encodings() declares exactly `flat-numeric` then `card-tokens`, in the
        ladder's order, and no third encoding (surface.md §3, encodings.md §1, ladder.md
        §2, D-3)."""
        declared = self.ep("encodings")()
        self.assertTrue(
            S.is_mapping(declared),
            "encodings() returns a mapping keyed by the encoding names (surface.md §3)",
        )
        self.assertEqual(
            list(declared), [S.FLAT, S.TOKENS],
            "the catalogue is written in the ladder's order, `flat-numeric` then "
            "`card-tokens` (surface.md §3, ladder.md §2): %r" % (list(declared),),
        )
        self.assertEqual(
            len(declared), 2,
            "there are two encodings and no third (encodings.md §1, D-3): %r"
            % (list(declared),),
        )
        for name in declared:
            with self.subTest(name=name):
                self.assertIsInstance(
                    name, str,
                    "an encoding's key is the name a variant entry declares, a plain str "
                    "(encodings.md §1): %r" % (name,),
                )

    def test_fea2_2_each_record_equals_the_spec_observation_spec_returns(self):
        """FEA-2.2 encodings()[name] equals observation_spec(build_encoder(name)): both are
        built from the one declaration table (surface.md §3, encoder.md §6)."""
        F = self.surface()
        declared = F.encodings()
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                spec = F.observation_spec(F.build_encoder(name))
                self.assertEqual(
                    declared[name], spec,
                    "encodings()[%r] must be the record observation_spec returns for that "
                    "encoding (surface.md §3, encoder.md §6): %r != %r"
                    % (name, declared[name], spec),
                )

    def test_fea2_3_two_calls_of_encodings_are_equal(self):
        """FEA-2.3 two calls of encodings() return equal records: the catalogue is plain
        data with no per-call state (surface.md §3)."""
        first = self.ep("encodings")()
        second = self.ep("encodings")()
        self.assertEqual(
            first, second,
            "two calls of encodings() return equal records (surface.md §3): %r != %r"
            % (first, second),
        )

    def test_fea2_4_a_spec_declares_exactly_the_six_keys(self):
        """FEA-2.4 observation_spec returns the six declared keys and no seventh
        (surface.md §5, encoder.md §3)."""
        F = self.surface()
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                spec = F.observation_spec(F.build_encoder(name))
                self.assertTrue(
                    S.is_mapping(spec),
                    "observation_spec returns one mapping (surface.md §5): %r" % (spec,),
                )
                self.assertEqual(
                    set(spec), set(S.SPEC_KEYS),
                    "the record is read under exactly representation, kind, fields, shape, "
                    "dtype and vocabulary, and there is no seventh key (encoder.md §3): %r"
                    % (sorted(spec),),
                )
                self.assertEqual(
                    len(spec), 6,
                    "six keys, not seven (encoder.md §3): %r" % (sorted(spec),),
                )

    def test_fea2_5_fields_are_the_same_nine_names_in_the_declared_order(self):
        """FEA-2.5 `fields` is identical for both encodings and is the nine names in the
        readout's order: that identity is the ladder's fairness condition (surface.md §5,
        encodings.md §2, encoder.md §3.1, FAM-2.4)."""
        F = self.surface()
        carried = {}
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                fields = F.observation_spec(F.build_encoder(name))["fields"]
                self.assertIsInstance(
                    fields, tuple,
                    "`fields` is a tuple of names in the one declared order (encoder.md "
                    "§3.1): %r" % (fields,),
                )
                self.assertEqual(
                    tuple(fields), S.FIELDS,
                    "`fields` is the readout's ten facts less `legal`, in the readout's own "
                    "order (encoder.md §3.1): %r" % (tuple(fields),),
                )
                carried[name] = tuple(fields)
        self.assertEqual(
            carried[S.FLAT], carried[S.TOKENS],
            "the same nine names for both encodings: a representation never changes what "
            "the agent may know (encodings.md §2, FAM-2.4, D-3)",
        )

    def test_fea2_6_the_carried_fields_are_readout_facts_and_never_legal(self):
        """FEA-2.6 every carried field is one of the readout's ten facts, the set is
        exactly nine, and `legal` is never carried (encodings.md §2, surface.md §5,
        FAM-2.5)."""
        F = self.surface()
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                fields = tuple(F.observation_spec(F.build_encoder(name))["fields"])
                self.assertEqual(
                    len(set(fields)), 9,
                    "the observation carries nine facts, not ten and not eight "
                    "(encodings.md §2): %r" % (fields,),
                )
                self.assertTrue(
                    set(fields) <= set(S.FACTS),
                    "every carried field is a readout fact (encodings.md §2, FAM-2.5): %r"
                    % (sorted(set(fields) - set(S.FACTS)),),
                )
                self.assertNotIn(
                    "legal", fields,
                    "`legal` is not carried: the legal set reaches a policy beside the "
                    "observation, as legal_indices' mask (encodings.md §2, D-3): %r"
                    % (fields,),
                )

    def test_fea2_7_representation_names_the_encoding(self):
        """FEA-2.7 `representation` is the encoding's own name, a plain str (surface.md §5,
        encoder.md §3, FAM-2.6)."""
        F = self.surface()
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                representation = F.observation_spec(F.build_encoder(name))["representation"]
                self.assertIsInstance(
                    representation, str,
                    "`representation` is a plain str (encoder.md §3): %r"
                    % (representation,),
                )
                self.assertEqual(
                    representation, name,
                    "the spec of %r must name its own encoding (surface.md §5, FAM-2.6): %r"
                    % (name, representation),
                )

    def test_fea2_8_kind_is_the_declared_representation_family(self):
        """FEA-2.8 `kind` is `dense-numeric` for flat-numeric and `token-sequence` for
        card-tokens (encodings.md §1, surface.md §5)."""
        F = self.surface()
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                kind = F.observation_spec(F.build_encoder(name))["kind"]
                self.assertEqual(
                    kind, S.DECLARED[name]["kind"],
                    "the representation family of %r is %r (encodings.md §1): %r"
                    % (name, S.DECLARED[name]["kind"], kind),
                )

    def test_fea2_9_shape_is_the_declared_tuple_of_ints(self):
        """FEA-2.9 `shape` is exactly (203,) or (40,), a tuple of plain integers
        (surface.md §5, encodings.md §3-§4, encoder.md §3, FAM-2.7)."""
        F = self.surface()
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                shape = F.observation_spec(F.build_encoder(name))["shape"]
                self.assertIsInstance(
                    shape, tuple,
                    "`shape` is a tuple of integers, not a list or a set (encoder.md §3): %r"
                    % (shape,),
                )
                self.assertEqual(
                    tuple(shape), S.DECLARED[name]["shape"],
                    "the declared shape of %r is %r (encodings.md §3-§4): %r"
                    % (name, S.DECLARED[name]["shape"], shape),
                )
                self.assertEqual(
                    len(shape), 1,
                    "one observation is one dimension of the declared width (encoder.md "
                    "§3): %r" % (shape,),
                )
                for value in shape:
                    self.assertTrue(
                        S.is_integer(value),
                        "every entry of `shape` is an integer (encoder.md §3): %r" % (value,),
                    )

    def test_fea2_10_dtype_is_plain_data_numpy_accepts(self):
        """FEA-2.10 `dtype` is a plain str that numpy.dtype() reads as float32 for
        flat-numeric and int32 for card-tokens (surface.md §5, encodings.md §3-§4,
        encoder.md §3, guardrails.md G11, FAM-2.7)."""
        F = self.surface()
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                dtype = F.observation_spec(F.build_encoder(name))["dtype"]
                self.assertIsInstance(
                    dtype, str,
                    "`dtype` is the plain str 'float32'/'int32', not a numpy dtype object "
                    "or a type (encoder.md §3, guardrails.md G11): %r" % (dtype,),
                )
                self.assertEqual(
                    numpy.dtype(dtype), numpy.dtype(S.DECLARED[name]["dtype"]),
                    "numpy.dtype(spec['dtype']) must read %r for %r (encodings.md §3-§4): %r"
                    % (S.DECLARED[name]["dtype"], name, dtype),
                )

    def test_fea2_11_vocabulary_is_none_or_ninety_six(self):
        """FEA-2.11 `vocabulary` is None for flat-numeric and 96 for card-tokens
        (surface.md §5, encodings.md §1, §4, encoder.md §3)."""
        F = self.surface()
        flat = F.observation_spec(F.build_encoder(S.FLAT))["vocabulary"]
        self.assertIsNone(
            flat,
            "a dense vector has no ids at all, so its vocabulary is None (surface.md §5, "
            "encoder.md §3): %r" % (flat,),
        )
        tokens = F.observation_spec(F.build_encoder(S.TOKENS))["vocabulary"]
        self.assertTrue(
            S.is_integer(tokens),
            "the token encoding's vocabulary is the integer count an embedding is sized "
            "from (encoder.md §3): %r" % (tokens,),
        )
        self.assertEqual(
            int(tokens), S.VOCABULARY,
            "the vocabulary is 96 ids, 0-95 (encodings.md §4, card-tokens.md §6): %r"
            % (tokens,),
        )

    def test_fea2_12_a_spec_is_plain_data(self):
        """FEA-2.12 every value in a spec record is a str, an int, a tuple of those or
        None: no numpy dtype object and no set (encoder.md §3, guardrails.md G11)."""
        F = self.surface()
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                spec = F.observation_spec(F.build_encoder(name))
                for key, value in spec.items():
                    with self.subTest(encoding=name, key=key):
                        self.assertIsInstance(
                            key, str,
                            "every key of the six-key record is a plain str (encoder.md §3): "
                            "%r" % (key,),
                        )
                        problem = S.plain_data_problem(value)
                        self.assertIsNone(
                            problem,
                            "spec[%r] of %r is %r: a spec is plain data a report's header "
                            "may quote (encoder.md §3, guardrails.md G11)"
                            % (key, name, problem),
                        )

    def test_fea2_13_two_calls_of_observation_spec_are_equal(self):
        """FEA-2.13 one encoder declares one spec: two calls are equal and the spec
        depends on no readout, hand or seed (surface.md §5, encoder.md §3)."""
        F = self.surface()
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                encoder = F.build_encoder(name)
                first = F.observation_spec(encoder)
                self.assertEqual(
                    first, F.observation_spec(encoder),
                    "one encoder declares one spec (surface.md §5): %r" % (name,),
                )
                F.encode(encoder, S.readout(street="river", history=S.history_entries(3)))
                self.assertEqual(
                    first, F.observation_spec(encoder),
                    "the spec depends on no readout (surface.md §5): encoding a river "
                    "readout must not change it",
                )

    def test_fea2_14_two_encoders_from_one_name_declare_equal_specs(self):
        """FEA-2.14 two encoders built from one name declare equal specs and encode one
        readout to equal observations: an encoder holds no state an observation could
        see (surface.md §4, encoder.md §1)."""
        F = self.surface()
        record = S.readout()
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                first = F.build_encoder(name)
                second = F.build_encoder(name)
                self.assertEqual(
                    F.observation_spec(first), F.observation_spec(second),
                    "two encoders built from one name declare equal specs (surface.md §4)",
                )
                self.assertEqual(
                    S.floats(F.encode(first, record)), S.floats(F.encode(second, record)),
                    "two encoders built from one name encode one readout to equal "
                    "observations (surface.md §4, encoder.md §1)",
                )

    def test_fea2_15_mutating_a_returned_spec_does_not_change_a_later_call(self):
        """FEA-2.15 the spec is a fresh dict every call: mutating what one call returned
        changes nothing a later call returns (encoder.md §3, guardrails.md G11)."""
        F = self.surface()
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                encoder = F.build_encoder(name)
                before = F.observation_spec(encoder)
                mutated = F.observation_spec(encoder)
                mutated["shape"] = (1, 2, 3)
                mutated["dtype"] = "int8"
                mutated["fields"] = ("legal",)
                mutated["representation"] = "mutated"
                mutated["vocabulary"] = -1
                mutated["extra"] = True
                del mutated["kind"]
                after = F.observation_spec(encoder)
                self.assertEqual(
                    after, before,
                    "a spec is built fresh on every call, so a caller's mutation cannot "
                    "reach the next caller (encoder.md §3, guardrails.md G11): %r != %r"
                    % (after, before),
                )
                self.assertNotIn(
                    "extra", after,
                    "no seventh key appears in a later call (encoder.md §3): %r" % (after,),
                )

    def test_fea2_16_mutating_the_catalogue_changes_nothing_later(self):
        """FEA-2.16 encodings() returns a fresh plain mapping: deleting or replacing one
        record does not change the next call (encoder.md §6, guardrails.md G11)."""
        declared = self.ep("encodings")()
        before = {name: dict(record) for name, record in declared.items()}
        declared[S.FLAT]["shape"] = (203, 203)
        declared[S.TOKENS]["vocabulary"] = 0
        del declared[S.TOKENS]
        declared["a-third-encoding"] = {"representation": "a-third-encoding"}
        again = self.ep("encodings")()
        self.assertEqual(
            again, before,
            "the catalogue is rebuilt from the declaration table on every call, so a "
            "mutated catalogue cannot be mistaken for the ladder's (encoder.md §6, "
            "guardrails.md G11): %r != %r" % (again, before),
        )


if __name__ == "__main__":
    unittest.main()
