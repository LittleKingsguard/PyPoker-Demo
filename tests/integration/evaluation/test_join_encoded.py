"""JOIN-EVL-5 — a member policy acts on encoded observations (features' edge).

`docs/L2/evaluation/league.md` §7 and `docs/L2/agents/learner.md` §6: a member's
policy is built from a learner, an encoder and a seed, so the decision it makes
is ``agents.act`` over ``features.encode``'s observation and
``features.legal_indices``' mask, and the descriptor it returns is the one
``features.decode_action`` builds from the chosen index — the shared three-index
vocabulary of `docs/L2/features/surface.md` §2.  That equality is why a checkpoint
becomes a policy at all (`docs/L1/protocol.md` §5, `docs/L2/evaluation/surface.md`
§12), and it is checked here for both ways `evaluation` builds a member policy:
`policy_from` of a bare path and `opponent` of a pool member.
"""

import importlib.util
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "evaluation_join_support" in sys.modules:
    J = sys.modules["evaluation_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "evaluation_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["evaluation_join_support"] = J
    _spec.loader.exec_module(J)


class EncodedDecisions(J.JoinCase):
    """A loaded member and a drawn member, both deciding on encoded observations."""

    def decisions(self):
        out = J.decisions_of(J.MATCH_SEED, J.caller)[:5]
        out += J.decisions_of(J.MATCH_SEED_OTHER, J.caller)[:3]
        self.assertGreaterEqual(len(out), 6, "the comparison covers two real hands")
        return out

    def test_join_evl_5_1_policy_from_decides_as_act_over_encode(self):
        """JOIN-EVL-5.1 a loaded member's decision is `agents.act` on the encoding.

        `docs/L2/evaluation/surface.md` §12 and `docs/L2/agents/surface.md` §9–§10:
        `policy_from` builds `agents.as_policy` of `agents.load(None, path)` over
        the encoder the checkpoint's encoding name builds, at the seed the
        checkpoint records, so at that seed it decides exactly as `act` does on
        ``features.encode``'s observation and ``features.legal_indices``' mask.
        """
        info = J.checkpoint(J.CHECKPOINT_B, J.CHECKPOINT_SEED_B)
        member = J.policy_from(info["path"])
        for position, (facts, legal) in enumerate(self.decisions()):
            mask = J.legal_indices(legal)
            observation = J.encode(info["encoder"], facts)
            expected = J.action_index(J.act(info["learner"], observation, mask))
            chosen = member(facts, legal)
            self.assert_descriptor_in(legal, chosen, "policy_from")
            self.assertEqual(
                J.descriptor_index(legal, chosen),
                expected,
                "a loaded member chooses the action its learner chooses on the "
                "same readout's observation and mask (docs/L2/agents/surface.md "
                "§10, docs/L1/protocol.md §5), decision %d" % (position,),
            )

    def test_join_evl_5_2_the_descriptor_is_decode_actions_descriptor(self):
        """JOIN-EVL-5.2 index → `features.decode_action` → the policy's descriptor.

        `docs/L2/features/surface.md` §2, §8–§9 and `docs/L2/engine/surface.md` §2:
        a descriptor is hand-independent and compares by value, the legal indices
        are position-aligned with the descriptors, and `decode_action` maps an
        index back to the descriptor the engine applies.  A member policy's answer
        must therefore be exactly that descriptor, and its index must be in the
        decision's mask.
        """
        info = J.checkpoint(J.CHECKPOINT_C, J.CHECKPOINT_SEED_C)
        member = J.policy_from(info["path"])
        for position, (facts, legal) in enumerate(self.decisions()):
            mask = J.legal_indices(legal)
            chosen = member(facts, legal)
            index = self.assert_descriptor_made_by_features(
                legal, chosen, "policy_from at decision %d" % (position,)
            )
            self.assertIn(
                index,
                set(mask),
                "a policy's answer must be one of the decision's legal indices "
                "(docs/L2/features/surface.md §8, D-2)",
            )
            self.assertEqual(
                list(J.legal_indices(facts["legal"])),
                list(mask),
                "the readout's own legal fact is the engine's descriptor order, "
                "so the mask the policy acts on is the one the decision carries "
                "(docs/L2/engine/surface.md §6, docs/L2/features/surface.md §8)",
            )

    def test_join_evl_5_3_a_drawn_member_decides_on_encoded_observations(self):
        """JOIN-EVL-5.3 `opponent`'s version member acts on the same encoding.

        `docs/L2/evaluation/pool.md` §7 and `docs/L2/agents/surface.md` §10: a
        drawn version is the same member-policy builder, so it too must answer
        `agents.act`'s index on the encoded observation — carried through the
        pool rather than only through the loader (`docs/L2/evaluation/surface.md`
        §8, `docs/L1/protocol.md` §5).
        """
        info = J.checkpoint(J.CHECKPOINT_D, J.CHECKPOINT_SEED_D)
        record = J.version(J.VERSION_D, J.START_LABEL,
                           J.CHECKPOINT_D, J.CHECKPOINT_SEED_D)
        pool = J.build_pool(
            {"members": [record], "m": J.league()["m"], "frozen": True}
        )
        names = J.names_of(J.pool_members(pool))
        size = len(names)
        drawn = J.opponent(pool, names.index(J.VERSION_D) + size * J.DRAW_MULTIPLE)
        for position, (facts, legal) in enumerate(self.decisions()):
            expected = J.decision_as_act(
                info["learner"], info["encoder"], facts, legal
            )
            chosen = drawn(facts, legal)
            index = self.assert_descriptor_made_by_features(
                legal, chosen, "opponent at decision %d" % (position,)
            )
            self.assertEqual(
                index,
                expected,
                "a drawn member's decisions are the ones the encoding and the "
                "vocabulary define (docs/L2/evaluation/pool.md §7, "
                "docs/L2/agents/surface.md §10)",
            )

    def test_join_evl_5_4_the_encoding_name_is_one_features_declares(self):
        """JOIN-EVL-5.4 the checkpoint's encoding is a declared encoding.

        `docs/L2/evaluation/surface.md` §12 and `docs/L2/features/surface.md` §3–§5:
        the encoding name a checkpoint records must be one of the two
        `features.encodings()` declares, and the encoder that name builds declares
        the representation the policy encodes with.  Two encoders of one name
        encode one readout to equal observations, so the decisions a member makes
        are the encoding's and not a private second encoding's.
        """
        info = J.checkpoint(J.CHECKPOINT_E, J.CHECKPOINT_SEED_E)
        declared = J.encodings()
        self.assertIn(
            J.DEFAULT_ENCODING,
            declared,
            "the checkpoint's encoding name must be one of the two features "
            "declares (docs/L2/features/surface.md §3, "
            "docs/L2/evaluation/surface.md §12)",
        )
        encoder = J.build_encoder(J.DEFAULT_ENCODING)
        spec = J.observation_spec(encoder)
        self.assertEqual(
            spec["representation"],
            J.DEFAULT_ENCODING,
            "an encoder declares its own encoding's name as its representation "
            "(docs/L2/features/surface.md §5)",
        )
        second = J.build_encoder(J.DEFAULT_ENCODING)
        member = J.policy_from(info["path"])
        for facts, legal in self.decisions()[:4]:
            first = J.encode(encoder, facts)
            again = J.encode(second, facts)
            self.assertEqual(
                first.shape,
                again.shape,
                "two encoders of one name declare equal specs "
                "(docs/L2/features/surface.md §4, §5)",
            )
            self.assertEqual(
                first.tolist(),
                again.tolist(),
                "one readout encodes to one observation, so a policy's decisions "
                "are a function of the encoding (docs/L2/features/surface.md §6)",
            )
            self.assertEqual(
                J.descriptor_index(legal, member(facts, legal)),
                J.action_index(
                    J.act(info["learner"], again, J.legal_indices(legal))
                ),
                "the member acts on the observation the encoding defines "
                "(docs/L2/agents/surface.md §10, docs/L2/features/surface.md §6)",
            )


if __name__ == "__main__":
    unittest.main()
