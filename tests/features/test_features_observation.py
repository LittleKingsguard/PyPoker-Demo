"""FEA-3 -- one readout, one observation: the array contract of `encode`.

``docs/L2/features/surface.md`` §6; ``docs/L2/features/encodings.md`` §3-§4;
``docs/L3/features/encoder.md`` §5; ``docs/L3/features/guardrails.md`` G4;
``docs/L1/battery.md`` §3 FAM-2 case FAM-2.8 and FAM-16 case FAM-16.9.
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


class FEA3Observation(S.FeaturesCase):
    """`encode` returns a fresh array of the declared shape and dtype, and mutates nothing."""

    def test_fea3_1_the_observation_has_the_declared_shape(self):
        """FEA-3.1 encode returns a numpy array of the shape the spec declares, for both
        encoders (surface.md §6, encodings.md §3-§4, FAM-2.8)."""
        F = self.surface()
        record = S.readout()
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                observation = F.encode(F.build_encoder(name), record)
                self.assertIsInstance(
                    observation, numpy.ndarray,
                    "encode returns one numpy array (encodings.md §3-§4, FAM-2.8): %r"
                    % (type(observation).__name__,),
                )
                self.assertEqual(
                    self.shape_of(observation), S.DECLARED[name]["shape"],
                    "the observation of %r is one dimension of %r (surface.md §6): %r"
                    % (name, S.DECLARED[name]["shape"], self.shape_of(observation)),
                )
                self.assertEqual(
                    len(observation), S.DECLARED[name]["shape"][0],
                    "the array holds exactly the declared number of values (encodings.md "
                    "§3-§4): %d slots" % (len(observation),),
                )

    def test_fea3_2_the_observation_has_the_declared_dtype(self):
        """FEA-3.2 the observation's element type is the declared dtype, for both encoders
        (surface.md §6, encodings.md §3-§4)."""
        F = self.surface()
        record = S.readout()
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                observation = F.encode(F.build_encoder(name), record)
                actual = numpy.asarray(observation).dtype.name
                self.assertEqual(
                    actual, S.DECLARED[name]["dtype"],
                    "an observation of %r is a %r array (encodings.md §3-§4): %r"
                    % (name, S.DECLARED[name]["dtype"], actual),
                )

    def test_fea3_3_the_declared_shape_holds_at_every_board_length(self):
        """FEA-3.3 the declared shape holds for a readout at each of the four board
        lengths 0, 3, 4 and 5, for both encoders (encodings.md §2, §5; surface.md §6)."""
        F = self.surface()
        for name in S.ENCODINGS:
            for position, street in enumerate(S.STREETS):
                with self.subTest(encoding=name, street=street):
                    record = S.readout(street=street)
                    self.assertEqual(
                        len(record["board"]), S.BOARD_SIZES[position],
                        "the battery's own invented readout is a %s readout with a "
                        "%d-card board" % (street, S.BOARD_SIZES[position]),
                    )
                    observation = F.encode(F.build_encoder(name), record)
                    self.assertEqual(
                        self.shape_of(observation), S.DECLARED[name]["shape"],
                        "the shape does not depend on how much of the board is dealt "
                        "(surface.md §6): %s readout, %r"
                        % (street, self.shape_of(observation)),
                    )

    def test_fea3_4_a_non_empty_history_does_not_change_the_shape(self):
        """FEA-3.4 a readout whose history is not empty encodes to one observation of the
        declared shape, for both encoders (flat-numeric.md §5, card-tokens.md §5,
        surface.md §6)."""
        F = self.surface()
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                record = S.readout(street="flop", history=S.history_entries(5))
                self.assertEqual(len(record["history"]), 5, "five applied actions")
                observation = F.encode(F.build_encoder(name), record)
                self.assertEqual(
                    self.shape_of(observation), S.DECLARED[name]["shape"],
                    "a history is a fixed-width block, so five entries do not widen the "
                    "observation (encodings.md §3-§4): %r" % (self.shape_of(observation),),
                )

    def test_fea3_5_two_encodes_are_equal_but_not_the_same_object(self):
        """FEA-3.5 two encodes of one readout give equal observations that are not the
        same object: a fresh array every call (encoder.md §5 rule 4, guardrails.md G4,
        FAM-16.9)."""
        F = self.surface()
        record = S.readout(street="turn", history=S.history_entries(2))
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                encoder = F.build_encoder(name)
                first = F.encode(encoder, record)
                second = F.encode(encoder, record)
                self.assertIsNot(
                    first, second,
                    "encode builds its array inside the call, so two calls are two arrays "
                    "(encoder.md §5 rule 4, guardrails.md G4)",
                )
                if name == S.FLAT:
                    self.assertEqual(
                        S.floats(first), S.floats(second),
                        "one encoder and one readout give one observation value for value "
                        "(surface.md §6, FAM-16.9)",
                    )
                else:
                    self.assertEqual(
                        S.ints(first), S.ints(second),
                        "one encoder and one readout give one observation value for value "
                        "(surface.md §6, FAM-16.9)",
                    )

    def test_fea3_6_encoding_other_readouts_does_not_change_the_observation(self):
        """FEA-3.6 the module holds no observation cache and no module-level buffer: the
        same readout encodes to the same observation after other work (encoder.md §5 rule
        4, guardrails.md G4)."""
        F = self.surface()
        record = S.readout(street="flop", history=S.history_entries(3))
        other = S.readout(street="river", seat=(1, False), hole=("Kh", "9s"),
                          history=S.history_entries(11))
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                encoder = F.build_encoder(name)
                before = F.encode(encoder, record)
                F.encode(encoder, other)
                F.encode(F.build_encoder(S.TOKENS if name == S.FLAT else S.FLAT), other)
                after = F.encode(encoder, record)
                self.assertEqual(
                    S.floats(before), S.floats(after),
                    "a second encode of one readout is the same observation, whatever was "
                    "encoded in between (guardrails.md G4): %r" % (name,),
                )

    def test_fea3_7_the_readout_is_unchanged_after_encoding(self):
        """FEA-3.7 encode neither mutates nor reorders its argument: the readout is
        deep-equal after the call (surface.md §6, guardrails.md G4)."""
        F = self.surface()
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                record = S.readout(street="flop", history=S.history_entries(2))
                before = S.deep(record)
                F.encode(F.build_encoder(name), record)
                self.assertEqual(
                    record, before,
                    "an encode leaves the readout it was handed untouched (surface.md §6, "
                    "guardrails.md G4): %r" % (name,),
                )
                self.assertIsInstance(
                    record["history"], list,
                    "the history stays the ordered list the readout carried (README.md §4)",
                )

    def test_fea3_8_the_history_list_is_not_sorted_or_reordered(self):
        """FEA-3.8 the history is laid out in the order the argument carries it: slot j of
        the dense history block is the one-hot of the j-th entry, never of the entry a sort
        would put there, and the readout's `history` list comes back unchanged and in its
        own order (flat-numeric.md §5, card-tokens.md §5, guardrails.md G4)."""
        F = self.surface()
        history = [
            "preflop seat 0 raises to 4",
            "preflop seat 1 calls 2",
            "flop seat 0 checks",
        ]
        actions = [S.history_action(entry) for entry in history]
        self.assertEqual(
            actions, [2, 1, 1],
            "the battery's own history denotes raise, check-call, check-call in that "
            "order (flat-numeric.md §5): %r" % (actions,),
        )
        self.assertNotEqual(
            actions,
            [S.history_action(entry) for entry in sorted(history)],
            "the battery's own history must be one a sort would re-order in the block, or "
            "this case cannot fail: %r" % (history,),
        )
        record = S.readout(street="preflop", history=history)
        before = S.deep(record)
        # The history block is the observation's last block, so its offset is the declared
        # width less its own width (flat-numeric.md §2, §5).
        offset = S.FLAT_WIDTH - S.HISTORY_SLOTS * S.HISTORY_SLOT_WIDTH
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                F.encode(F.build_encoder(name), record)
                self.assertEqual(
                    list(record["history"]), history,
                    "the history list comes back in its own order, unsorted and "
                    "unreordered (guardrails.md G4): %r" % (record["history"],),
                )
                self.assertEqual(
                    record, before,
                    "encoding a readout leaves the readout equal to what was passed "
                    "(surface.md §6)",
                )
        values = S.floats(F.encode(F.build_encoder(S.FLAT), record))
        for position, action in enumerate(actions):
            with self.subTest(slot=position):
                slot = values[offset + S.HISTORY_SLOT_WIDTH * position:
                              offset + S.HISTORY_SLOT_WIDTH * (position + 1)]
                self.assertEqual(
                    slot,
                    [1.0 if index == action else 0.0
                     for index in range(S.HISTORY_SLOT_WIDTH)],
                    "history slot %d is the one-hot of the argument's own entry %d, %r: "
                    "the entries are laid out oldest first and never sorted "
                    "(flat-numeric.md §5): %r"
                    % (position, position, history[position], slot),
                )

    def test_fea3_9_a_refused_encode_leaves_no_half_written_observation(self):
        """FEA-3.9 a refusal before the first write leaves nothing behind: the next encode
        returns the same observation (errors.md §1, guardrails.md G4, G9)."""
        F = self.surface()
        record = S.readout(street="turn", history=S.history_entries(1))
        broken = S.without(record, "hole")
        for name in S.ENCODINGS:
            with self.subTest(encoding=name):
                encoder = F.build_encoder(name)
                before = S.floats(F.encode(encoder, record))
                self.refusal(F.encode, encoder, broken)
                self.assertEqual(
                    S.floats(F.encode(encoder, record)), before,
                    "a refused encode must not leave a half-written buffer for the next "
                    "call to return (errors.md §1, guardrails.md G4): %r" % (name,),
                )


if __name__ == "__main__":
    unittest.main()
