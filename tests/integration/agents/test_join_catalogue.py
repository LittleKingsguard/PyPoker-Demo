"""JOIN-AGT-5 — the catalogue's `observation_size` cross-check (D-3).

`docs/L2/agents/surface.md` §3: `observation_size` is a contract, not a second source
of truth — each kind's scalar width must equal the width of the `shape` a dense
encoding's `observation_spec` declares, or the `vocabulary` a token encoding's
declares, and §4 refuses an encoder-bearing build whose kind and encoder disagree.
`features.observation_spec` is the authority (`docs/L2/features/surface.md` §5), so
the equality is a join neither module can check alone (`docs/L2/agents/learner.md`
§6).  The kinds' encodings are derived from the two catalogues, never from a document.
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


class CatalogueCrossCheck(J.JoinCase):
    """The declared sizes against the encodings' declared specs."""

    def test_join_agt_5_1_declared_size_equals_the_encoding_spec(self):
        """JOIN-AGT-5.1 every kind's declared size and family match its encoding.

        `docs/L2/agents/surface.md` §3's table makes the dense kind's
        `observation_size` the width of the one-element `shape` and a token kind's the
        `vocabulary`; `docs/L2/features/surface.md` §5 makes those two the spec's own
        keys.  The encoding is the one whose `kind` equals the catalogue's
        `observation`, so the pairing itself is read out of the two published
        catalogues.
        """
        declared = J.learners()["architectures"]
        self.assertTrue(declared, "learners() must declare its architecture kinds")
        for kind, entry in declared.items():
            with self.subTest(kind=kind):
                encoder = J.build_encoder(J.encoding_for(kind))
                spec = J.observation_spec(encoder)
                self.assertEqual(
                    entry["observation"],
                    spec["kind"],
                    "the kind %r consumes the representation family its encoding "
                    "declares (docs/L2/agents/surface.md §3, docs/L2/features/"
                    "surface.md §5)" % (kind,),
                )
                size = entry["observation_size"]
                self.assertIsInstance(
                    size,
                    int,
                    "observation_size is a scalar width "
                    "(docs/L2/agents/surface.md §3): %r" % (size,),
                )
                if spec["kind"] == "dense-numeric":
                    shape = tuple(spec["shape"])
                    self.assertEqual(
                        len(shape),
                        1,
                        "a dense encoding declares a one-element shape "
                        "(docs/L2/agents/surface.md §3): %r" % (shape,),
                    )
                    self.assertEqual(
                        int(size),
                        int(shape[0]),
                        "the %r kind's declared width must equal the dense encoding "
                        "%r's shape width (D-3, docs/L2/agents/surface.md §3)"
                        % (kind, spec["representation"]),
                    )
                else:
                    vocabulary = spec["vocabulary"]
                    self.assertIsNotNone(
                        vocabulary,
                        "a token encoding declares the vocabulary a token learner is "
                        "sized from (docs/L2/features/surface.md §5)",
                    )
                    self.assertEqual(
                        int(size),
                        int(vocabulary),
                        "the %r kind's declared size must equal the token encoding "
                        "%r's vocabulary (D-3, docs/L2/agents/surface.md §3)"
                        % (kind, spec["representation"]),
                    )

    def test_join_agt_5_2_a_learner_built_through_its_encoder_accepts_encode(self):
        """JOIN-AGT-5.2 the sizing contract holds in the other direction too.

        A learner of each declared kind is built *with* its encoding's encoder
        (`docs/L2/agents/surface.md` §4) and must accept the observation
        `features.encode` produces for a real readout, choosing a member of the mask
        `features.legal_indices` returns (`docs/L2/agents/surface.md` §6).  This is
        the arrow the L1 battery cannot reach while `training` does not exist.
        """
        declared = J.learners()["architectures"]
        hand = J.new_hand(J.DEAL_TOKEN_A)
        facts = J.readout(hand)
        legal = J.legal_actions(hand)
        mask = J.legal_indices(legal)
        for kind in declared:
            with self.subTest(kind=kind):
                encoder = J.build_encoder(J.encoding_for(kind))
                learner = J.learner(
                    kind, J.WIDTH_ONE, J.DEPTH_ONE, J.LEARNER_SEED
                )
                observation = J.encode(encoder, facts)
                spec = J.observation_spec(encoder)
                self.assertEqual(
                    tuple(observation.shape),
                    tuple(spec["shape"]),
                    "encode must produce the spec's declared shape "
                    "(docs/L2/features/surface.md §6)",
                )
                index = J.action_index(J.act(learner, observation, mask))
                self.assert_index_in(index, mask, "kind %r" % (kind,))

    def test_join_agt_5_3_a_contradicting_encoder_is_refused_naming_both_sides(self):
        """JOIN-AGT-5.3 a build whose encoder contradicts the kind names both sides.

        `docs/L2/agents/surface.md` §4 and `docs/L2/agents/learner.md` §6: an encoder
        whose `observation_spec` kind or size contradicts the kind's `observation` or
        `observation_size` is refused, naming both — the refusal is what keeps the
        two declarations equal instead of a comment.  Both directions are driven.
        """
        cases = (
            ("naive-stack", "card-tokens"),
            ("deep", "flat-numeric"),
        )
        for kind, encoding in cases:
            with self.subTest(kind=kind, encoding=encoding):
                spec = J.learner_spec(
                    kind,
                    J.WIDTH_ONE,
                    J.DEPTH_ONE,
                    J.LEARNER_SEED,
                    encoding=encoding,
                )
                groups = (
                    ("encoder", "encoding"),
                    (
                        ("card-tokens", "token-sequence")
                        if encoding == "card-tokens"
                        else ("flat-numeric", "dense-numeric")
                    ),
                    (
                        ("naive-stack", "dense-numeric")
                        if kind == "naive-stack"
                        else (kind, "token-sequence")
                    ),
                )
                self.assert_refusal(
                    "build_learner",
                    groups,
                    lambda: J.build_learner(spec),
                    note="JOIN-AGT-5.3 kind %r with the %r encoder" % (kind, encoding),
                )


if __name__ == "__main__":
    unittest.main()
