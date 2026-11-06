"""JOIN-AGT-11 — the blind instances and the join's refusals.

`docs/L1/e2e-surface.md` §5 and `docs/L1/battery.md` §4 (D-15): for each `agents` row
marked `general` — `build_learner`, `param_count`, `act`, `learn`, `save`, `load` and
`as_policy` — the battery carries a case whose instance it invented from this surface
alone.  The instances below (seeds, a sparsity, widths, depths, a batch length, a
mask, checkpoint file names) appear in no design document.  Alongside them this family
asserts the joins' refusals: an observation of the other representation family, a mask
that is not `features.legal_indices`' shape, a checkpoint of one kind under a spec
naming another, and a value that is not a learner — each refused with a message that
names the entry point, the argument or field and the offending value
(`docs/L3/agents/errors.md` §3).
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


class BlindInstances(J.JoinCase):
    """Seven invented instances and the join's named refusals."""

    def dense_learner(self, seed=J.LEARNER_SEED_BLIND):
        return J.learner(
            "naive-stack", J.WIDTH_ONE, J.DEPTH_ONE, seed
        )

    def token_learner(self, seed=J.LEARNER_SEED_BLIND):
        return J.learner("sparse", J.WIDTH_THREE, J.DEPTH_THREE, seed,
                         sparsity=J.SPARSITY)

    def decision(self, deal=J.DEAL_DECISION_A):
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        hand = J.new_hand(deal)
        facts = J.readout(hand)
        legal = J.legal_actions(hand)
        return encoder, facts, legal, J.encode(encoder, facts), J.legal_indices(legal)

    def real_batch(self):
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        record = J.play_hand(J.DEAL_REWARD_B, J.caller, J.caller)
        return encoder, J.seat_transitions(record, 0, encoder)

    # -- the seven invented instances --------------------------------------
    def test_join_agt_11_1_build_learner_takes_an_invented_spec(self):
        """JOIN-AGT-11.1 an invented sparse spec and an invented bare-kind spec both build.

        `docs/L2/agents/surface.md` §4: three keys are required and the two optional
        ones are read when present, a bare kind name takes its width and depth from
        `sizes`, and a setting the kind does not read is ignored.  The sparsity, the
        width, the depth, the seed and the bare-kind `sizes` are the battery's own.
        """
        spec = J.learner_spec(
            "sparse",
            J.WIDTH_THREE,
            J.DEPTH_THREE,
            J.LEARNER_SEED_BLIND,
            sparsity=J.SPARSITY,
        )
        built = J.build_learner(spec)
        self.assertGreater(
            J.param_count(built),
            0,
            "the invented sparsity-bearing spec must build a measurable learner "
            "(docs/L2/agents/surface.md §4, §5)",
        )
        encoder = J.build_encoder(J.encoding_for("sparse"))
        hand = J.new_hand(J.DEAL_TOKEN_A)
        facts = J.readout(hand)
        mask = J.legal_indices(J.legal_actions(hand))
        index = J.action_index(J.act(built, J.encode(encoder, facts), mask))
        self.assert_index_in(index, mask, "invented sparse learner")
        bare = {
            "backend": "numpy",
            "architecture": "plain",
            "sizes": {"width": J.WIDTH_ONE + 2, "depth": J.DEPTH_TWO},
            "seed": J.LEARNER_SEED_BLIND,
            "encoder": J.build_encoder(J.encoding_for("plain")),
        }
        self.assertGreater(
            J.param_count(J.build_learner(bare)),
            0,
            "a bare kind name takes its width and depth from `sizes` "
            "(docs/L2/agents/surface.md §4, docs/L1/records.md §3)",
        )

    def test_join_agt_11_2_param_count_measures_an_invented_pair(self):
        """JOIN-AGT-11.2 two invented widths of one kind report two positive counts.

        `docs/L2/agents/surface.md` §5 and `docs/L2/agents/learner.md` §3: the count is
        a measurement of the model's trainable values, so one spec reports one count
        and a wider model reports another.  The widths are the battery's own.
        """
        narrow = J.learner(
            "wide", J.WIDTH_ONE, J.DEPTH_THREE, J.LEARNER_SEED_BLIND
        )
        broad = J.learner(
            "wide", J.WIDTH_THREE, J.DEPTH_THREE, J.LEARNER_SEED_BLIND
        )
        narrow_count = J.param_count(narrow)
        broad_count = J.param_count(broad)
        self.assertIsInstance(narrow_count, int)
        self.assertGreater(narrow_count, 0)
        self.assertGreater(broad_count, 0)
        self.assertNotEqual(
            narrow_count,
            broad_count,
            "the count is a function of the spec, not a constant "
            "(docs/L2/agents/learner.md §3, ASM-10)",
        )
        same = J.learner(
            "wide", J.WIDTH_ONE, J.DEPTH_THREE, J.LEARNER_SEED_BLIND
        )
        self.assertEqual(
            J.param_count(same),
            narrow_count,
            "one spec reports one count (docs/L2/agents/surface.md §5)",
        )

    def test_join_agt_11_3_act_takes_an_invented_mask(self):
        """JOIN-AGT-11.3 an invented mask confines the chosen index on a real readout.

        `docs/L2/agents/surface.md` §6: the index is a member of the mask, and one
        state and one decision give one index.  The masks are the battery's own; each
        is a shape a decision can produce (`docs/L2/features/surface.md` §2, §8).
        """
        learner = self.dense_learner()
        _encoder, _facts, _legal, observation, _mask = self.decision()
        for mask in (J.MASK_PAIR, J.MASK_ALL):
            with self.subTest(mask=mask):
                index = J.action_index(J.act(learner, observation, mask))
                self.assert_index_in(index, mask, "invented mask %r" % (mask,))
                self.assertEqual(
                    J.action_index(J.act(learner, observation, mask)),
                    index,
                    "one state and one decision give one answer "
                    "(docs/L2/agents/surface.md §6)",
                )
        confined = J.action_index(J.act(learner, observation, J.MASK_PAIR))
        self.assertNotEqual(
            confined,
            0,
            "a mask without 0 cannot return 0 "
            "(docs/L2/agents/surface.md §2)",
        )

    def test_join_agt_11_4_learn_takes_an_invented_batch_length(self):
        """JOIN-AGT-11.4 a real batch tiled to an invented length is consumed and counted.

        `docs/L2/agents/surface.md` §7: the batch is the caller's and `learn` reports
        the transitions it consumed; `docs/L3/agents/rule.md` §3: any non-empty batch
        is legal, its length being the caller's.  The length is the battery's own.
        """
        _encoder, batch = self.real_batch()
        self.assertTrue(batch)
        tiled = J.tiled(batch, J.BATCH_LENGTH)
        self.assertEqual(len(tiled), J.BATCH_LENGTH)
        learner = self.dense_learner()
        statistics = J.learn(learner, tiled)
        self.assertEqual(
            J.transitions_consumed(statistics),
            J.BATCH_LENGTH,
            "learn reports the transitions it consumed "
            "(docs/L2/agents/surface.md §7)",
        )
        self.assertTrue(J.finite(J.td_error(statistics)))

    def test_join_agt_11_5_learn_refuses_an_empty_batch_a_missing_key_and_an_illegal_action(self):
        """JOIN-AGT-11.5 learn's three batch refusals name the field and the value.

        `docs/L2/agents/surface.md` §7: an empty batch, a transition missing a required
        key of `docs/L1/records.md` §4, and an `action` outside that transition's
        `legal` are refused; `docs/L3/agents/errors.md` §3 fixes the message grammar.
        The malformed records are built by the battery.
        """
        _encoder, batch = self.real_batch()
        learner = self.dense_learner()
        self.assert_refusal(
            "learn",
            (("transitions", "batch"), ("()", "at least one")),
            lambda: J.learn(learner, ()),
            note="JOIN-AGT-11.5 empty batch",
        )
        missing = {key: value for key, value in batch[0].items() if key != "next_legal"}
        self.assert_refusal(
            "learn",
            (("transitions",), ("next_legal",)),
            lambda: J.learn(learner, [missing]),
            note="JOIN-AGT-11.5 missing key",
        )
        hand = J.new_hand(J.DEAL_DECISION_A)
        hand = J.apply_action(hand, J.decode_action(1))
        facts = J.readout(hand)
        mask = J.legal_indices(J.legal_actions(hand))
        self.assertNotIn(0, mask, "a check/call leaves a mask without fold")
        observation = J.encode(J.build_encoder(J.encoding_for("naive-stack")), facts)
        illegal = {
            "observation": observation,
            "next_observation": observation,
            "action": 0,
            "reward": 0.0,
            "terminal": True,
            "legal": list(mask),
            "next_legal": list(mask),
        }
        self.assert_refusal(
            "learn",
            (("transitions",), ("action",), ("legal", "mask")),
            lambda: J.learn(learner, [illegal]),
            note="JOIN-AGT-11.5 action outside legal",
        )

    def test_join_agt_11_6_save_takes_an_invented_file_name_and_refuses_a_bad_path(self):
        """JOIN-AGT-11.6 save writes exactly the invented name and refuses an unwritable one.

        `docs/L2/agents/surface.md` §8: `save` returns the path it wrote and refuses a
        path that is not a writable file location, naming it; `docs/L3/agents/
        checkpoint.md` §2: the caller's spelling lands where the caller said.
        """
        learner = self.dense_learner()
        path = self.checkpoint_path(J.CHECKPOINT_ALPHA)
        written = J.save(learner, path)
        self.assertTrue(
            os.path.exists(str(written)),
            "save must write the checkpoint it returns: %r" % (written,),
        )
        self.assertEqual(
            os.path.basename(str(written)),
            J.CHECKPOINT_ALPHA,
            "the checkpoint lands at the caller's spelling "
            "(docs/L3/agents/checkpoint.md §2): %r" % (written,),
        )
        unwritable = os.path.join(
            self.scratch(), "join-invented-absent", J.CHECKPOINT_MISSING
        )
        self.assert_refusal(
            "save",
            (("path",), (unwritable,)),
            lambda: J.save(learner, unwritable),
            note="JOIN-AGT-11.6 unwritable path",
        )

    def test_join_agt_11_7_load_restores_from_a_path_and_refuses_missing_and_mismatched(self):
        """JOIN-AGT-11.7 load reads a path alone and refuses a missing path and a wrong kind.

        `docs/L2/agents/surface.md` §9: a checkpoint recovers everything from the file
        itself, a missing path is refused naming it, and a spec that disagrees with the
        checkpoint on a key it carries is refused naming that key and both values.
        """
        learner = self.dense_learner()
        saved = J.save(learner, self.checkpoint_path(J.CHECKPOINT_BETA))
        restored = J.load(None, saved)
        self.assertEqual(
            J.param_count(restored),
            J.param_count(learner),
            "the path alone restores the saved capacity "
            "(docs/L2/agents/surface.md §9)",
        )
        missing = self.checkpoint_path(J.CHECKPOINT_MISSING)
        self.assert_refusal(
            "load",
            (("path",), (missing,)),
            lambda: J.load(None, missing),
            note="JOIN-AGT-11.7 missing path",
        )
        other_kind = J.learner_spec(
            "deep", J.WIDTH_ONE, J.DEPTH_ONE, J.LEARNER_SEED_BLIND
        )
        self.assert_refusal(
            "load",
            (("kind",), ("deep",), ("naive-stack",)),
            lambda: J.load(other_kind, saved),
            note="JOIN-AGT-11.7 a spec naming another kind",
        )

    def test_join_agt_11_8_as_policy_takes_an_invented_seed_and_refuses_bad_arguments(self):
        """JOIN-AGT-11.8 an invented policy seed decides, and three bad arguments refuse.

        `docs/L2/agents/surface.md` §10: the policy returns one of `legal_actions`; a
        value that is not a learner or not an encoder, a seed that is not an integer,
        and an encoder whose spec contradicts the learner's are refused, naming the
        contract and both sides.  The policy seed is the battery's own.
        """
        encoder, facts, legal, _observation, _mask = self.decision()
        learner = self.dense_learner()
        policy = J.as_policy(learner, encoder, J.POLICY_SEED)
        self.assert_descriptor_in(legal, policy(facts, legal), "invented policy seed")
        token_encoder = J.build_encoder(J.encoding_for("sparse"))
        self.assert_refusal(
            "as_policy",
            (("encoder",), ("card-tokens", "token-sequence"),
             ("dense-numeric", "203")),
            lambda: J.as_policy(learner, token_encoder, J.POLICY_SEED),
            note="JOIN-AGT-11.8 a contradicting encoder",
        )
        self.assert_refusal(
            "as_policy",
            (("seed",), (str(J.POLICY_SEED),)),
            lambda: J.as_policy(learner, encoder, str(J.POLICY_SEED)),
            note="JOIN-AGT-11.8 a seed that is not an integer",
        )
        self.assert_refusal(
            "as_policy",
            (("learner",), ("baseline",)),
            lambda: J.as_policy(
                J.build_baseline("random", J.BASELINE_SEED),
                encoder,
                J.POLICY_SEED,
            ),
            note="JOIN-AGT-11.8 a baseline is not a learner",
        )

    def test_join_agt_11_9_each_family_refuses_the_other_family_s_observation(self):
        """JOIN-AGT-11.9 a contradiction between the observation and the learner names both.

        `docs/L2/agents/surface.md` §6: an observation whose shape, dtype or
        representation family contradicts the learner's is refused, naming both; the
        encoding is the other module's declared spec
        (`docs/L2/features/surface.md` §5).  Both directions are driven with an
        invented learner seed.
        """
        dense_encoder = J.build_encoder(J.encoding_for("naive-stack"))
        token_encoder = J.build_encoder(J.encoding_for("sparse"))
        _encoder, facts, _legal, _observation, mask = self.decision()
        cases = (
            ("token learner, dense observation", self.token_learner(),
             dense_encoder, "dense-numeric", "token-sequence"),
            ("dense learner, token observation", self.dense_learner(),
             token_encoder, "token-sequence", "dense-numeric"),
        )
        for label, learner, encoder, offered, expected in cases:
            with self.subTest(case=label):
                observation = J.encode(encoder, facts)
                self.assert_refusal(
                    "act",
                    (("observation",), (offered,), (expected,)),
                    lambda: J.act(learner, observation, mask),
                    note="JOIN-AGT-11.9 %s" % (label,),
                )

    def test_join_agt_11_10_a_mask_outside_the_decision_s_shape_is_refused(self):
        """JOIN-AGT-11.10 an empty, repeating or out-of-vocabulary mask is refused.

        `docs/L2/agents/surface.md` §6 and §2: a mask is `features.legal_indices`'
        shape — non-empty, distinct, in `{0, 1, 2}` — so empty, repeating and a `3` are
        refused, naming the mask and the value.  The malformed masks are the battery's
        own.
        """
        learner = self.dense_learner()
        _encoder, _facts, _legal, observation, _mask = self.decision()
        groups = {
            (): (("mask",), ("()", "empty", "at least one")),
            (0, 1, 1): (("mask",), ("distinct", "(0, 1, 1)", "[0, 1, 1]")),
            (0, 3): (("mask",), ("(0, 3)", "[0, 3]", "3")),
        }
        for mask, expected in groups.items():
            with self.subTest(mask=mask):
                self.assert_refusal(
                    "act",
                    expected,
                    lambda: J.act(learner, observation, mask),
                    note="JOIN-AGT-11.10 mask %r" % (mask,),
                )

    def test_join_agt_11_11_a_value_that_is_not_a_learner_is_refused_where_one_is_required(self):
        """JOIN-AGT-11.11 a baseline policy and a raw callable are refused as not learners.

        `docs/L2/agents/surface.md` §5–§10: `param_count`, `act`, `learn`, `save` and
        `as_policy` each refuse a value that is not a learner, naming that contract;
        `docs/L2/agents/learner.md` §5: a baseline never learns, and its count is the
        zero `baselines()` declares.  The raw callable is the battery's own policy in
        the protocol of `e2e-surface.md` §2.
        """
        encoder, _facts, _legal, observation, mask = self.decision()
        _encoder, batch = self.real_batch()
        path = self.checkpoint_path(J.CHECKPOINT_GAMMA)
        not_learners = (
            ("baseline policy", J.build_baseline("random", J.BASELINE_SEED),
             (("learner",), ("baseline",))),
            ("raw callable", J.caller, (("learner",), ("function", "callable"))),
        )
        entries = {
            "param_count": lambda value: J.param_count(value),
            "act": lambda value: J.act(value, observation, mask),
            "learn": lambda value: J.learn(value, batch),
            "save": lambda value: J.save(value, path),
            "as_policy": lambda value: J.as_policy(value, encoder, J.POLICY_SEED),
        }
        for name, value, groups in not_learners:
            for entry, call in entries.items():
                with self.subTest(entry=entry, value=name):
                    self.assert_refusal(
                        entry,
                        groups,
                        lambda: call(value),
                        note="JOIN-AGT-11.11 %s(%r)" % (entry, name),
                    )


if __name__ == "__main__":
    unittest.main()
