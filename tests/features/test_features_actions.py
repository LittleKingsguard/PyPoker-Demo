"""FEA-7 -- the three-index action vocabulary: `action_space`, `legal_indices`,
`decode_action`.

``docs/L2/features/surface.md`` §2, §7-§9; ``docs/L3/features/vocabulary.md`` §1-§6;
``docs/L3/features/guardrails.md`` G6-G8; ``docs/L1/battery.md`` §3 FAM-2 cases
FAM-2.9-2.11 and FAM-16 cases FAM-16.10-16.11.

The vocabulary is the game's and not a rung's: three indices, no amount, and a
positional mask.
"""

import itertools
import os
import sys
import unittest

try:  # discovered as part of a tests.features package
    from . import _features_support as S
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _features_support as S  # noqa: E402


class FEA7ActionSpace(S.FeaturesCase):
    """`action_space` declares the three indices and no number beside them."""

    def test_fea7_1_the_keys_are_exactly_the_three_indices(self):
        """FEA-7.1 action_space() is keyed by 0, 1 and 2 as plain integers, in ascending
        order, and by nothing else (surface.md §7, vocabulary.md §2, FAM-2.9)."""
        space = self.action_space()
        self.assertTrue(
            S.is_mapping(space),
            "action_space() returns a mapping keyed by the three indices (surface.md §7)",
        )
        keys = list(space)
        self.assertEqual(
            keys, [0, 1, 2],
            "the three keys are 0, 1 and 2, in ascending index order (vocabulary.md §2, "
            "surface.md §7): %r" % (keys,),
        )
        for key in keys:
            with self.subTest(index=key):
                self.assertTrue(
                    S.is_integer(key),
                    "an index is a plain integer, not '0' or 0.0 (vocabulary.md §2): %r"
                    % (key,),
                )

    def test_fea7_2_the_only_integers_in_the_record_are_0_1_and_2(self):
        """FEA-7.2 the record carries no integer but the three indices, read from its keys
        as well as its values, and no string anywhere in it contains a digit: a stray 4, a
        'sizes': (2, 4) or a 'raise to 4' would each put an amount into the vocabulary
        (surface.md §7, vocabulary.md §2, guardrails.md G6, FAM-2.9).

        The two assertions are the rule together: the L1 reader folds integers and
        all-digit strings, so a digit inside prose escapes it and only the second assertion
        decides that case (vocabulary.md §2, guardrails.md G6).
        """
        space = self.action_space()
        vocabulary = S.action_vocabulary(space)
        self.assertEqual(
            vocabulary, {0, 1, 2},
            "the vocabulary the record declares is exactly {0, 1, 2}: no amount, no chip "
            "count, no size and no id beyond the three indices (surface.md §7, "
            "vocabulary.md §2, FAM-2.9): %r from %r" % (sorted(vocabulary), space),
        )
        for index, record in space.items():
            with self.subTest(index=index):
                self.assertEqual(
                    S.numbers(record), [],
                    "no record carries a number of its own: the three indices are the "
                    "only numbers in the record (surface.md §7, guardrails.md G6): %r"
                    % (record,),
                )
        with_digits = [text for text in S.strings(space) if any(c.isdigit() for c in text)]
        self.assertEqual(
            with_digits, [],
            "no string in the record -- in a key or in a value, at any depth -- contains a "
            "digit, so no prose can smuggle a chip count past the integers this case "
            "found (vocabulary.md §2, guardrails.md G6): %r" % (with_digits,),
        )

    def test_fea7_3_the_three_names_are_in_index_order(self):
        """FEA-7.3 the records name fold, check-call and raise at indices 0, 1 and 2
        (surface.md §2, §7; vocabulary.md §1, §2)."""
        space = self.action_space()
        for index, expected in enumerate(S.ACTIONS):
            with self.subTest(index=index):
                record = space[index]
                self.assertTrue(
                    S.is_mapping(record),
                    "each value is a plain record carrying the action's name "
                    "(surface.md §7): %r" % (record,),
                )
                self.assertEqual(
                    record["name"], expected,
                    "index %d is %r, the shared spelling of the descriptor "
                    "(vocabulary.md §1, §2): %r" % (index, expected, record.get("name")),
                )

    def test_fea7_4_the_raise_record_carries_the_minimum_completion_note(self):
        """FEA-7.4 the raise's record carries the resolution that it denotes the engine's
        minimum legal completion, as prose and not as an amount (surface.md §2, §7;
        vocabulary.md §2)."""
        space = self.action_space()
        record = space[2]
        self.assertEqual(record["name"], "raise", "index 2 is the raise (vocabulary.md §1)")
        self.assertGreater(
            len(record), 1,
            "the raise's record is not a bare name: it carries the resolution that one "
            "index denotes the engine's minimum legal completion (surface.md §7, "
            "vocabulary.md §2): %r" % (record,),
        )
        self.assertIn(
            "completion", S.flatten_text(record),
            "the raise's record says it denotes the engine's minimum legal completion "
            "(surface.md §2, vocabulary.md §2): %r" % (record,),
        )

    def test_fea7_5_two_calls_are_equal_and_a_mutation_does_not_persist(self):
        """FEA-7.5 two calls of action_space() are equal and each returns a fresh plain
        mapping: mutating one is invisible to the next (surface.md §7, guardrails.md G11)."""
        first = self.action_space()
        before = {index: dict(record) for index, record in first.items()}
        first[0]["name"] = "bet"
        first[2]["sizes"] = (2, 4)
        first[7] = {"name": "call-any"}
        del first[1]
        again = self.action_space()
        self.assertEqual(
            again, before,
            "the vocabulary is the game's fixed declaration, rebuilt on every call "
            "(surface.md §7, guardrails.md G11): %r != %r" % (again, before),
        )
        self.assertEqual(
            again, self.action_space(),
            "two calls return equal records (surface.md §7)",
        )

    def test_fea7_6_the_records_are_plain_data(self):
        """FEA-7.6 every value of the record is plain data a report's header may quote: no
        numpy dtype, no set, no numpy scalar (encoder.md §3, guardrails.md G11,
        surface.md §7)."""
        space = self.action_space()
        for index, record in space.items():
            with self.subTest(index=index):
                for key, value in record.items():
                    with self.subTest(index=index, key=key):
                        self.assertIsInstance(
                            key, str,
                            "a record's key is a plain str (surface.md §7): %r" % (key,),
                        )
                        problem = S.plain_data_problem(value)
                        self.assertIsNone(
                            problem,
                            "space[%r][%r] is %r: action_space is plain data because a "
                            "report's header quotes it (surface.md §7, guardrails.md G11)"
                            % (index, key, problem),
                        )


class FEA7LegalIndices(S.FeaturesCase):
    """`legal_indices` is positional, so one descriptor gives one index in place."""

    def test_fea7_7_all_three_descriptors_give_0_1_and_2(self):
        """FEA-7.7 legal_indices(('fold', 'check-call', 'raise')) is (0, 1, 2), a tuple of
        plain integers (surface.md §8, vocabulary.md §3, FAM-2.11)."""
        indices = self.legal_indices(S.ACTIONS)
        self.assertIsInstance(
            indices, tuple,
            "legal_indices returns a tuple of indices (surface.md §8, layout.md §4): %r"
            % (indices,),
        )
        self.assertEqual(
            indices, (0, 1, 2),
            "the three descriptors' indices are 0, 1 and 2 in their own order "
            "(surface.md §8, FAM-2.11): %r" % (indices,),
        )
        for index in indices:
            self.assertTrue(
                S.is_integer(index),
                "an index is a plain integer (vocabulary.md §3): %r" % (index,),
            )

    def test_fea7_8_two_descriptors_give_their_own_indices(self):
        """FEA-7.8 legal_indices(('check-call', 'raise')) is (1, 2): the mask a decision
        with nothing to call returns (surface.md §8, vocabulary.md §3, FAM-16.10)."""
        self.assertEqual(
            self.legal_indices(("check-call", "raise")), (1, 2),
            "with nothing to call the legal indices are {1, 2}, positionally "
            "(vocabulary.md §3, FAM-16.10)",
        )

    def test_fea7_9_the_result_is_position_aligned_and_not_sorted(self):
        """FEA-7.9 legal_indices(('raise', 'check-call', 'fold')) is (2, 1, 0): the i-th
        index is the i-th descriptor's, never a sorted or de-duplicated set (surface.md §8,
        vocabulary.md §3, guardrails.md G7)."""
        indices = self.legal_indices(("raise", "check-call", "fold"))
        self.assertEqual(
            indices, (2, 1, 0),
            "the mask is position-aligned with the argument: the engine's ascending order "
            "is a consequence of its input, never a step this function takes "
            "(vocabulary.md §3, guardrails.md G7): %r" % (indices,),
        )
        self.assertNotEqual(
            tuple(sorted(indices)), indices,
            "a sorted result would hide the defect: this argument's indices are "
            "descending (vocabulary.md §3)",
        )

    def test_fea7_10_every_ordering_of_every_subset_is_position_aligned(self):
        """FEA-7.10 for every non-empty subset of the vocabulary in every order, the result
        is the argument's descriptors' indices, one per descriptor (surface.md §8,
        vocabulary.md §3)."""
        legal_indices = self.ep("legal_indices")
        for size in (1, 2, 3):
            for chosen in itertools.permutations(S.ACTIONS, size):
                with self.subTest(descriptors=chosen):
                    expected = tuple(S.ACTIONS.index(name) for name in chosen)
                    self.assertEqual(
                        legal_indices(chosen), expected,
                        "one index per descriptor, in the argument's order (surface.md §8): "
                        "%r must give %r" % (chosen, expected),
                    )

    def test_fea7_11_a_list_of_descriptors_is_the_same_sequence(self):
        """FEA-7.11 a list of descriptors is a sequence of descriptors too: the same
        indices as the tuple (vocabulary.md §3)."""
        legal_indices = self.ep("legal_indices")
        self.assertEqual(
            legal_indices(["raise", "fold"]), (2, 0),
            "a list is a sequence of descriptors, and the mask is positional "
            "(vocabulary.md §3): %r" % (legal_indices(["raise", "fold"]),),
        )

    def test_fea7_12_one_index_per_descriptor_and_they_are_distinct(self):
        """FEA-7.12 a decision's descriptors and indices correspond one to one and the
        indices are distinct: three descriptors are three different indices
        (surface.md §8, vocabulary.md §3, FAM-2.11)."""
        indices = self.legal_indices(S.ACTIONS)
        self.assertEqual(
            len(indices), len(S.ACTIONS),
            "one index per legal descriptor (surface.md §8, FAM-2.11): %r descriptors, "
            "%r indices" % (S.ACTIONS, indices),
        )
        self.assertEqual(
            len(set(indices)), len(indices),
            "the indices of one decision are distinct (surface.md §8, FAM-2.11): %r"
            % (indices,),
        )
        for descriptor, index in zip(S.ACTIONS, indices):
            with self.subTest(descriptor=descriptor):
                self.assertEqual(
                    self.decode(index), descriptor,
                    "the descriptor at the i-th position is the i-th index's descriptor "
                    "(surface.md §2, FAM-2.10): %r -> %r" % (index, descriptor),
                )


class FEA7DecodeAction(S.FeaturesCase):
    """`decode_action` is one index in, one descriptor out, and nothing else."""

    def test_fea7_13_every_legal_index_round_trips_to_its_descriptor(self):
        """FEA-7.13 decode_action(legal_indices(legal)[i]) is legal[i] for every index the
        mask can return (surface.md §2, §9; vocabulary.md §4, FAM-2.10)."""
        F = self.surface()
        for legal in (S.ACTIONS, ("check-call", "raise"), ("fold", "check-call"),
                      ("raise",), ("fold", "raise")):
            with self.subTest(legal=legal):
                indices = F.legal_indices(legal)
                for position, index in enumerate(indices):
                    with self.subTest(legal=legal, index=index):
                        self.assertEqual(
                            F.decode_action(index), legal[position],
                            "decode_action is the reverse step of legal_indices "
                            "(surface.md §2, FAM-2.10): %r -> %r, expected %r"
                            % (index, F.decode_action(index), legal[position]),
                        )

    def test_fea7_14_the_descriptors_are_the_shared_spelling(self):
        """FEA-7.14 decode_action returns 'fold', 'check-call' and 'raise' for 0, 1 and 2,
        a plain str equal to the name action_space declares (surface.md §2, §9;
        vocabulary.md §1, §4)."""
        space = self.action_space()
        for index in (0, 1, 2):
            with self.subTest(index=index):
                descriptor = self.decode(index)
                self.assertIsInstance(
                    descriptor, str,
                    "decode_action returns a plain str (surface.md §9, vocabulary.md §4): %r"
                    % (descriptor,),
                )
                self.assertEqual(
                    descriptor, S.ACTIONS[index],
                    "the shared spelling at index %d (vocabulary.md §1, §4): %r"
                    % (index, descriptor),
                )
                self.assertEqual(
                    descriptor, space[index]["name"],
                    "decode_action and action_space are two directions of one vocabulary "
                    "(vocabulary.md §1, §2): %r != %r"
                    % (descriptor, space[index]["name"]),
                )

    def test_fea7_15_decode_action_is_a_function_of_the_index_alone(self):
        """FEA-7.15 decode_action sees no decision, no readout and no hand: the same index
        gives the same descriptor before and after other work (surface.md §9,
        vocabulary.md §4)."""
        F = self.surface()
        before = [F.decode_action(index) for index in (0, 1, 2)]
        F.encode(F.build_encoder(S.FLAT), S.readout(street="river",
                                                    history=S.history_entries(7)))
        F.legal_indices(("raise", "fold"))
        F.encodings()
        after = [F.decode_action(index) for index in (0, 1, 2)]
        self.assertEqual(
            before, after,
            "one index gives one descriptor, whatever was called before it "
            "(surface.md §9): %r != %r" % (after, before),
        )
        self.assertEqual(
            [F.decode_action(index) for index in (0, 1, 2)], list(S.ACTIONS),
            "the three indices decode to the three descriptors of the vocabulary "
            "(vocabulary.md §4): %r" % ([F.decode_action(index) for index in (0, 1, 2)],),
        )

    def test_fea7_16_the_three_indices_are_the_whole_argument(self):
        """FEA-7.16 decode_action claims no legality: it decodes every index of {0, 1, 2}
        and takes nothing but the index (surface.md §9, vocabulary.md §4)."""
        decode = self.ep("decode_action")
        record = S.readout()
        for index in (0, 1, 2):
            with self.subTest(index=index):
                descriptor = decode(index)
                self.assertIn(
                    descriptor, S.ACTIONS,
                    "every index of the vocabulary decodes to one of its descriptors "
                    "(vocabulary.md §4): %r" % (descriptor,),
                )
                with self.assertRaises(TypeError):
                    decode(index, record)


if __name__ == "__main__":
    unittest.main()
