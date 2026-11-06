"""FAM-16 — the three blind instances, one per ``general`` row of ``features``.

`docs/L1/battery.md` §4 (D-15) and `docs/L1/e2e-surface.md` §5: three of this module's
seven rows are ``general`` — `encode`, `legal_indices` and `decode_action` — so each
carries one case whose **instance appears in no design document**.  The seeds below are
the writer's own and are none of the seeds `tests/e2e/_surface.py` uses; the readouts,
the actions and the descriptor round trip are the engine's own at those seeds.

Each case drives the full trip a caller performs in the policy protocol
(`docs/L1/e2e-surface.md` §2): a readout becomes an observation through `encode`, the
decision's mask comes from `legal_indices`, a chosen index becomes a descriptor through
`decode_action`, and `engine.apply_action` accepts it and advances the hand.  A case's
*subject* is one row; the other two are its path, which is what makes it a blind
instance of that row (`docs/L1/battery.md` §4).
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


class FAM16Blind(S.JoinCase):
    """Blind instances of the three ``general`` rows of this module's surface."""

    def test_fam16_9_encode_the_invented_seed_20483(self):
        """FAM-16.9 features.encode — instance: seed 20483, decisions of one hand."""
        encoders = {}
        specs = {}
        for name in S.ENCODING_NAMES:
            encoders[name] = self.encoder(name)
            specs[name] = self.observation_spec(encoders[name])
        hand = self.new_hand(S.SEED_ENCODE)
        decisions = []
        while len(decisions) < 20 and not self.is_terminal(hand):
            readout = self.readout(hand)
            for name in S.ENCODING_NAMES:
                with self.subTest(decision=len(decisions), encoding=name):
                    observation = self.encode(encoders[name], readout)
                    self.assert_observation(name, specs[name], observation)
                    again = self.encode(encoders[name], readout)
                    self.assertTrue(
                        S.same_observation(observation, again),
                        "one readout encodes to one observation value for value "
                        "(surface.md §6): %r encoded twice differently at %r"
                        % (name, readout["street"]),
                    )
                    self.assertIsNot(
                        observation,
                        again,
                        "each call returns its own observation array, so a caller's "
                        "mutation of one cannot reach the other (surface.md §6)",
                    )
            indices = [int(value) for value in self.legal_indices(readout["legal"])]
            self.assertTrue(
                indices,
                "a decision has at least one legal action, so one index "
                "(surface.md §8): %r" % (list(readout["legal"]),),
            )
            descriptor = self.decode_action(indices[-1])
            self.assertIn(
                S.token(descriptor),
                [S.token(item) for item in S.descriptors(readout["legal"], "legal")],
                "the decoded descriptor is one of the decision's legal descriptors "
                "(surface.md §8, §9): %r against %r"
                % (descriptor, list(readout["legal"])),
            )
            hand = self.apply_action(hand, descriptor)
            decisions.append(readout)
        self.assertGreaterEqual(
            len(decisions),
            3,
            "the invented seed's hand takes several decisions, and every one of them "
            "encoded (surface.md §6): %r" % (len(decisions),),
        )
        self.assertTrue(
            self.is_terminal(hand),
            "the round trip plays the invented hand to its end: seed %r"
            % (S.SEED_ENCODE,),
        )
        self.assertEqual(
            [readout["street"] for readout in decisions][0],
            "preflop",
            "the first decision the battery encoded is the preflop one "
            "(engine/environment.md §1)",
        )
        self.assertEqual(
            [len(readout["history"]) for readout in decisions],
            list(range(len(decisions))),
            "each decision of the invented hand carries one more public action than the "
            "last, so every decision the round trip visited is its own information set "
            "(engine/environment.md §2): %r"
            % ([len(readout["history"]) for readout in decisions],),
        )

    def test_fam16_10_legal_indices_the_invented_seed_61879(self):
        """FAM-16.10 features.legal_indices — instance: seed 61879, decisions of one hand."""
        steps, hand = self.walk(S.SEED_MASK, S.CHECK_CALL)
        self.assertGreaterEqual(
            len(steps), 3, "the invented seed's hand takes several decisions"
        )
        facing = 0
        free = 0
        for position, step in enumerate(steps):
            legal = S.descriptors(step.legal, "a decision's legal descriptors")
            indices = [int(value) for value in self.legal_indices(step.readout["legal"])]
            to_call = int(step.readout["to_call"])
            with self.subTest(decision=position, to_call=to_call, indices=indices):
                self.assertEqual(
                    len(indices),
                    len(legal),
                    "one index per legal descriptor, position by position "
                    "(surface.md §8): %r descriptors, %r indices" % (len(legal), indices),
                )
                self.assertEqual(
                    len(set(indices)),
                    len(indices),
                    "a decision's indices are distinct (surface.md §8): %r" % (indices,),
                )
                self.assertEqual(
                    indices,
                    sorted(indices),
                    "the indices ascend, because the engine hands the descriptors in the "
                    "vocabulary's order (surface.md §2, §8): %r" % (indices,),
                )
                self.assertEqual(
                    [int(value) for value in self.legal_indices(step.legal)],
                    indices,
                    "the readout's legal fact and legal_actions give one mask "
                    "(engine/surface.md §6, surface.md §8)",
                )
                self.assertIn(
                    1,
                    indices,
                    "check/call is the action that always continues, so index 1 is legal "
                    "at every decision of a hand that is not over (surface.md §2): %r"
                    % (indices,),
                )
                self.assertEqual(
                    0 in indices,
                    to_call > 0,
                    "folding is legal exactly where there is something to call, because "
                    "folding where checking is free is not an action of that decision "
                    "(engine/surface.md §2, surface.md §2): to_call %r, indices %r"
                    % (to_call, indices),
                )
            if to_call > 0:
                facing += 1
            else:
                free += 1
        self.assertGreaterEqual(
            facing,
            1,
            "the invented seed's hand holds at least one decision facing a bet "
            "(engine/environment.md §1)",
        )
        self.assertGreaterEqual(
            free,
            1,
            "the invented seed's hand holds at least one decision with nothing to call "
            "(engine/environment.md §1)",
        )
        self.assertTrue(
            self.is_terminal(hand),
            "the battery's always-continue policy plays the invented hand to its end "
            "(engine/surface.md §8)",
        )

    def test_fam16_11_decode_action_the_invented_seed_73391(self):
        """FAM-16.11 features.decode_action — instance: seed 73391, decisions of one hand."""
        steps, _hand = self.walk(S.SEED_DECODE, S.RAISE)
        self.assertGreaterEqual(
            len(steps), 3, "the invented seed's hand takes several decisions"
        )
        vocabulary = tuple(self.decode_action(index) for index in S.ACTION_INDICES)
        self.assertEqual(
            vocabulary,
            S.ACTION_NAMES,
            "the decoder is the three-index vocabulary: fold, check/call, raise "
            "(surface.md §2, §9): %r" % (vocabulary,),
        )
        free_decision = None
        for position, step in enumerate(steps):
            legal = S.descriptors(step.legal, "a decision's legal descriptors")
            indices = [int(value) for value in self.legal_indices(step.legal)]
            with self.subTest(decision=position, street=step.readout["street"]):
                self.assertEqual(
                    tuple(self.decode_action(index) for index in S.ACTION_INDICES),
                    vocabulary,
                    "one index decodes to one descriptor at every decision, because a "
                    "descriptor is hand-independent and sees no decision "
                    "(surface.md §2, §9)",
                )
                for slot, index in enumerate(indices):
                    descriptor = self.decode_action(index)
                    self.assertEqual(
                        S.token(descriptor),
                        S.token(legal[slot]),
                        "index %r stands at position %d of the decision's descriptors, so "
                        "it decodes to that descriptor (surface.md §8, §9): %r against %r"
                        % (index, slot, descriptor, legal[slot]),
                    )
                    self.assertIsNotNone(
                        self.apply_action(step.hand, descriptor),
                        "the engine accepts every decoded legal descriptor at the decision "
                        "it was decoded from (surface.md §2, §9): index %r at %r"
                        % (index, step.readout["street"]),
                    )
            if int(step.readout["to_call"]) == 0 and free_decision is None:
                free_decision = (position, step)
        self.assertIsNotNone(
            free_decision,
            "the invented seed's hand holds a decision with nothing to call "
            "(engine/environment.md §1)",
        )
        position, step = free_decision
        self.assertNotIn(
            0,
            [int(value) for value in self.legal_indices(step.legal)],
            "folding is not an action of decision %d, where checking is free "
            "(engine/surface.md §2, surface.md §2)" % (position,),
        )
        self.assertEqual(
            self.decode_action(0),
            S.ACTION_NAMES[0],
            "decode_action never claims legality: it sees no decision, so it returns the "
            "fold descriptor even at a decision where folding is not legal "
            "(surface.md §2, §9): %r"
            % (self.decode_action(0),),
        )


if __name__ == "__main__":
    unittest.main()
