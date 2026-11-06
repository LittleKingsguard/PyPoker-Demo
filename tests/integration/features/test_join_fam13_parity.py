"""FAM-13 — the D-7 parity join: one encoding serves both the NumPy and the Torch rung.

`docs/L1/battery.md` §3 FAM-13 (the D-7 speed evidence), `docs/L1/ladder.md` §5,
`docs/L2/features/encodings.md` §1 and §7, `docs/L2/features/surface.md` §4.  R1 and R2
declare the same encoding — `flat-numeric` — and differ only on the backend, so their
evidence is a speed comparison on identical work.  That is only true if one name, one
`build_encoder` and one `encode` serve both rungs: two separately built encoders must
declare equal specs and encode one readout to equal observations, and the mask and the
decoder must be the same functions at both rungs' decisions.

The battery plays the same invented deal twice — once as R1's run and once as R2's — and
compares the two runs decision by decision at this module's edge.  A rung is a variant
name and never a branch in `features` (``encodings.md`` §1, D-3), so nothing here may
differ between the two runs, and nothing here is a speed measurement: that belongs to
`harness.timings` and is not this module's to promise (``ladder.md`` §5).
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

# ladder.md §2, encodings.md §1: the one encoding R1's and R2's variants both declare.
R12_ENCODING = "flat-numeric"


class FAM13Parity(S.JoinCase):
    """The R1/R2 pair at the `features` edge: one encoding, one encode, one vocabulary."""

    def test_fam13_1_one_name_builds_two_encoders_of_one_spec_and_one_observation(self):
        """FAM-13.1 two encoders from one name declare one spec and encode one readout (D-7)."""
        readout = self.readout(self.new_hand(S.SEED_PARITY))
        first = self.encoder(R12_ENCODING)
        second = self.encoder(R12_ENCODING)
        self.assertIsNot(
            first,
            second,
            "each rung builds its own encoder from the one declared name (surface.md §4, "
            "ladder.md §2)",
        )
        self.assertEqual(
            S.canonical(self.observation_spec(first)),
            S.canonical(self.observation_spec(second)),
            "one name declares one spec, so the two rungs are sized identically and "
            "their comparison varies the backend alone (surface.md §4, ladder.md §5)",
        )
        left = self.encode(first, readout)
        right = self.encode(second, readout)
        self.assertEqual(
            self.declared_shape(self.observation_spec(first)),
            self.declared_shape(self.observation_spec(second)),
            "both rungs' one observation has the same shape (surface.md §5, "
            "encodings.md §1)",
        )
        self.assertTrue(
            S.same_observation(left, right),
            "one encode serves both rungs: one readout is one observation whichever "
            "encoder of the declared name encodes it (surface.md §4, §6, D-7)",
        )
        self.assertIsNot(
            left,
            right,
            "each call returns its own array, so one rung's observation cannot be the "
            "other's (surface.md §6)",
        )

    def test_fam13_2_the_two_rungs_runs_agree_at_every_decision(self):
        """FAM-13.2 the same deal played twice encodes identically at every decision (D-7)."""
        r1_steps, r1_hand = self.walk(S.SEED_PARITY, S.CHECK_CALL)
        r2_steps, r2_hand = self.walk(S.SEED_PARITY, S.CHECK_CALL)
        self.assertEqual(
            len(r1_steps),
            len(r2_steps),
            "the two runs play the same deal under the same policy, so they take the "
            "same number of decisions (engine/surface.md §4, ASM-2): %r against %r"
            % (len(r1_steps), len(r2_steps)),
        )
        self.assertEqual(
            self.is_terminal(r1_hand),
            self.is_terminal(r2_hand),
            "the two runs end the same way: %r against %r"
            % (self.is_terminal(r1_hand), self.is_terminal(r2_hand)),
        )
        r1_encoder = self.encoder(R12_ENCODING)
        r2_encoder = self.encoder(R12_ENCODING)
        for position, (left, right) in enumerate(zip(r1_steps, r2_steps)):
            with self.subTest(decision=position, street=left.readout["street"]):
                self.assertEqual(
                    S.canonical(left.readout),
                    S.canonical(right.readout),
                    "both rungs read the same information set at decision %d, because "
                    "the readout is a function of the hand alone (engine/"
                    "environment.md §2, D-3)" % (position,),
                )
                self.assertTrue(
                    S.same_observation(
                        self.encode(r1_encoder, left.readout),
                        self.encode(r2_encoder, right.readout),
                    ),
                    "the representation a run sees is rung-independent: decision %d of "
                    "one deal encodes identically in R1's run and in R2's run "
                    "(encodings.md §1, ladder.md §4, D-7)" % (position,),
                )
                self.assertEqual(
                    [int(index) for index in self.legal_indices(left.legal)],
                    [int(index) for index in self.legal_indices(right.legal)],
                    "the legal mask is the game's and not the rung's, so both runs read "
                    "the same mask at decision %d (surface.md §2, §8, D-2)" % (position,),
                )

    def test_fam13_3_the_mask_and_the_decoder_are_the_same_functions_for_both_rungs(self):
        """FAM-13.3 decode_action is hand-independent and the mask is one function (§2)."""
        r1_steps, _r1_hand = self.walk(S.SEED_PARITY, S.CHECK_CALL)
        r2_steps, _r2_hand = self.walk(S.SEED_PARITY, S.RAISE)
        self.assertGreaterEqual(
            len(r1_steps), 2, "the case needs more than one decision to compare"
        )
        baseline = tuple(self.decode_action(index) for index in S.ACTION_INDICES)
        self.assertEqual(
            baseline,
            S.ACTION_NAMES,
            "the decoder is the vocabulary and nothing else: index 0, 1 and 2 decode to "
            "fold, check/call and raise (surface.md §2, §9): %r" % (baseline,),
        )
        for label, steps in (("R1's run", r1_steps), ("R2's run", r2_steps)):
            for position, step in enumerate(steps):
                legal = S.descriptors(step.legal, "a decision's legal descriptors")
                indices = [int(value) for value in self.legal_indices(step.legal)]
                with self.subTest(run=label, decision=position):
                    self.assertEqual(
                        tuple(self.decode_action(index) for index in S.ACTION_INDICES),
                        baseline,
                        "%s decoded an index differently at decision %d: a descriptor is "
                        "hand-independent, so one index is one action at every decision "
                        "and in both rungs (surface.md §2, §9): %r"
                        % (label, position, step.readout["street"]),
                    )
                    self.assertEqual(
                        [int(index) for index in self.legal_indices(step.readout["legal"])],
                        indices,
                        "%s reads one mask at decision %d, from the readout's legal fact "
                        "or from legal_actions, because the engine makes them one "
                        "sequence (engine/surface.md §6, surface.md §8)"
                        % (label, position),
                    )
                    for slot, index in enumerate(indices):
                        self.assertEqual(
                            S.token(self.decode_action(index)),
                            S.token(legal[slot]),
                            "index %r is the %d-th legal index, so the decoder returns "
                            "the %d-th descriptor — the one function both rungs use "
                            "(surface.md §2, §8, §9): %r against %r"
                            % (index, slot, slot, self.decode_action(index), legal[slot]),
                        )


if __name__ == "__main__":
    unittest.main()
