"""JOIN-AGT-6 — the token path at the join.

`docs/L2/features/surface.md` §5–§6: a `card-tokens` encoder declares
`token-sequence`, an `int32` observation and the vocabulary an embedding table is
sized from; `docs/L2/agents/surface.md` §3–§4: a token kind is built for that
vocabulary and `act` takes the observation and the mask.  A token learner and a
dense learner consume two different families, and the refusal must name both — the
join R3–R6 depend on and no single module can check (`docs/L3/agents/errors.md` §3).
"""

import importlib.util
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "agents_join_support" in sys.modules:
    J = sys.modules["agents_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "agents_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["agents_join_support"] = J
    _spec.loader.exec_module(J)

TOKEN_KIND = "deep"


class TokenPath(J.JoinCase):
    """The token observation from `features.encode` to `agents.act`."""

    def token_learner(self):
        return J.learner(
            TOKEN_KIND, J.WIDTH_ONE, J.DEPTH_TWO, J.LEARNER_SEED
        )

    def test_join_agt_6_1_encode_produces_the_declared_token_observation(self):
        """JOIN-AGT-6.1 a real readout encodes to int32 token ids of the declared size.

        `docs/L2/features/surface.md` §5 declares the token encoding's `shape`,
        `dtype` and `vocabulary`; §6 makes `encode` return exactly that shape and
        dtype.  An id outside the vocabulary is not a token the embedding table can
        read, so the check is a join between the two modules' declarations.  The deal
        is invented.
        """
        encoder = J.build_encoder(J.encoding_for(TOKEN_KIND))
        spec = J.observation_spec(encoder)
        facts = J.readout(J.new_hand(J.DEAL_TOKEN_A))
        observation = J.encode(encoder, facts)
        shape = tuple(spec["shape"])
        self.assertEqual(
            tuple(observation.shape),
            shape,
            "encode must return the declared shape (docs/L2/features/surface.md §6)",
        )
        self.assertEqual(
            str(observation.dtype),
            spec["dtype"],
            "the token observation's declared dtype is %r "
            "(docs/L2/features/surface.md §5)" % (spec["dtype"],),
        )
        self.assertEqual(
            len(shape),
            1,
            "a token observation is one sequence (docs/L2/features/surface.md §5)",
        )
        self.assertEqual(
            int(observation.size),
            int(shape[0]),
            "the observation holds one id per position of the declared sequence",
        )
        vocabulary = int(spec["vocabulary"])
        self.assertGreater(
            vocabulary, 0, "a token encoding declares a positive vocabulary"
        )
        for value in list(observation):
            token = int(value)
            self.assertTrue(
                0 <= token < vocabulary,
                "a token id must be readable by the embedding table the vocabulary "
                "sizes (docs/L2/features/surface.md §5): %r not in [0, %d)"
                % (token, vocabulary),
            )

    def test_join_agt_6_2_the_token_decision_decodes_to_an_applied_action(self):
        """JOIN-AGT-6.2 act chooses from the real mask and decode_action's answer applies.

        `docs/L2/agents/surface.md` §2, §6 and `docs/L2/features/surface.md` §9: the
        chosen token-learner index is a member of `features.legal_indices`' mask and
        its decoded descriptor is the action `engine.apply_action` accepts.  Applying
        it appends exactly one public action and leaves the argument handle at its
        own state (`docs/L2/engine/surface.md` §7).
        """
        encoder = J.build_encoder(J.encoding_for(TOKEN_KIND))
        learner = self.token_learner()
        hand = J.new_hand(J.DEAL_TOKEN_B)
        facts = J.readout(hand)
        legal = J.legal_actions(hand)
        mask = J.legal_indices(legal)
        observation = J.encode(encoder, facts)
        index = J.action_index(J.act(learner, observation, mask))
        self.assert_index_in(index, mask, "token decision")
        descriptor = J.decode_action(index)
        self.assert_descriptor_in(legal, descriptor, "token decision")
        before = len(facts["history"])
        self.assertFalse(
            J.is_terminal(hand),
            "a readout exists only for a non-terminal hand "
            "(docs/L2/engine/surface.md §5)",
        )
        advanced = J.apply_action(hand, descriptor)
        ended = J.is_terminal(advanced)
        self.assertIsInstance(
            ended,
            bool,
            "is_terminal returns a boolean (docs/L2/engine/surface.md §8)",
        )
        self.assertTrue(
            ended or len(J.readout(advanced)["history"]) == before + 1,
            "applying one legal action either ends the hand or appends exactly one "
            "public action (docs/L2/engine/surface.md §7)",
        )
        self.assertEqual(
            len(J.readout(hand)["history"]),
            before,
            "apply_action leaves the hand it was given at its own state "
            "(docs/L2/engine/surface.md §1, §7)",
        )

    def test_join_agt_6_3_each_family_refuses_the_other_family_s_observation(self):
        """JOIN-AGT-6.3 a dense observation to a token learner is refused naming both.

        `docs/L2/agents/surface.md` §6 and `docs/L3/agents/errors.md` §3: an
        observation whose shape, dtype or representation family contradicts the
        learner's is refused, naming both.  Both directions are driven: the dense
        learner must refuse the token observation as the token learner refuses the
        dense one.
        """
        dense_encoder = J.build_encoder(J.encoding_for("naive-stack"))
        token_encoder = J.build_encoder(J.encoding_for(TOKEN_KIND))
        dense_learner = J.learner(
            "naive-stack", J.WIDTH_ONE, J.DEPTH_ONE, J.LEARNER_SEED
        )
        token_learner = self.token_learner()
        hand = J.new_hand(J.DEAL_TOKEN_A)
        facts = J.readout(hand)
        mask = J.legal_indices(J.legal_actions(hand))
        cases = (
            ("token learner, dense observation", token_learner, dense_encoder,
             "dense-numeric", "token-sequence"),
            ("dense learner, token observation", dense_learner, token_encoder,
             "token-sequence", "dense-numeric"),
        )
        for label, learner, encoder, offered, expected in cases:
            with self.subTest(case=label):
                observation = J.encode(encoder, facts)
                groups = (
                    ("observation",),
                    (offered,),
                    (expected,),
                )
                self.assert_refusal(
                    "act",
                    groups,
                    lambda: J.act(learner, observation, mask),
                    note="JOIN-AGT-6.3 %s" % (label,),
                )


if __name__ == "__main__":
    unittest.main()
