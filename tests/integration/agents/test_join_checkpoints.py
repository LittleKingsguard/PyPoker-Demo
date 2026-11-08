"""JOIN-AGT-7 — checkpoints as league members.

`docs/L2/agents/surface.md` §8–§10 and `docs/L2/agents/learner.md` §4: `save`/`load`
is loss-free at the decision boundary, a checkpoint is loadable from its path alone,
and a policy built at the checkpoint's recorded seed decides as its learner did —
which is what lets a shipped version be a league member (`docs/L1/records.md` §7,
`docs/L1/protocol.md` §5, ASM-5).  The checkpoint is saved at a *learned* state and
the exploration schedule is annealed past the catalogue's `samples`, so the compared
decisions are taken on the greedy arm; otherwise a restore that dropped the
parameters would pass.  D-19's rule travels with the member: the container records
the catalogue member the learner was trained under and a restore reads the file under
it (`docs/L1/rules.md` §6, `docs/L3/agents/checkpoint.md` §1–§3).
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


class CheckpointsAsMembers(J.JoinCase):
    """A learned checkpoint, restored three ways, deciding on real readouts."""

    def spec(self):
        return J.learner_spec(
            "naive-stack", J.WIDTH_ONE, J.DEPTH_TWO, J.LEARNER_SEED
        )

    def learned(self):
        """The encoder, the spec and a learner trained far enough to act greedily.

        One real batch is learned first, then a batch at least as long as the
        exploration schedule's `samples`, so the schedule position is at its end and
        the greedy arm is the common case (`docs/L2/agents/surface.md` §3, §7).
        """
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        spec = self.spec()
        learner = J.build_learner(spec)
        episode = J.play_hand(J.DEAL_CHECKPOINT_A, J.caller, J.caller)
        batch = J.seat_transitions(episode, 0, encoder)
        first = J.learn(learner, batch)
        self.assertEqual(
            J.transitions_consumed(first),
            len(batch),
            "the first real batch is the one learn consumed",
        )
        self.assertTrue(J.finite(J.td_error(first)))
        samples = J.exploration_samples()
        annealed = J.learn(learner, J.tiled(batch, samples))
        self.assertEqual(
            J.transitions_consumed(annealed),
            samples,
            "the annealing batch must be at least as long as the catalogue's "
            "exploration samples (docs/L2/agents/surface.md §3)",
        )
        self.assertTrue(J.finite(J.td_error(annealed)))
        return encoder, spec, learner

    def decisions(self, encoder):
        """Observations and masks from two invented deals, driven by a caller policy."""
        out = []
        for deal in (J.DEAL_CHECKPOINT_B, J.DEAL_SEED_A):
            out.extend(J.observations(deal, J.caller, encoder))
        self.assertGreaterEqual(
            len(out),
            4,
            "the comparison must cover several decisions of two real hands",
        )
        return out

    def test_join_agt_7_1_save_then_load_with_the_spec_is_loss_free(self):
        """JOIN-AGT-7.1 a loaded learner makes the saved learner's decisions.

        `docs/L2/agents/surface.md` §9 and `docs/L1/protocol.md` §5: the restored
        learner carries the same parameter values and the same decision boundary, and
        `param_count` reports the saved count.  A fresh learner from the same spec is
        the control: it must differ somewhere, or the comparison would not show that
        the saved parameters are what decides.
        """
        encoder, spec, learner = self.learned()
        path = J.save(learner, self.checkpoint_path(J.CHECKPOINT_ALPHA))
        restored = J.load(spec, path)
        self.assertEqual(
            J.param_count(restored),
            J.param_count(learner),
            "a restored learner reports the saved capacity "
            "(docs/L2/agents/surface.md §5, §9)",
        )
        decisions = self.decisions(encoder)
        saved = [
            J.action_index(J.act(learner, observation, mask))
            for observation, mask in decisions
        ]
        loaded = [
            J.action_index(J.act(restored, observation, mask))
            for observation, mask in decisions
        ]
        self.assertEqual(
            loaded,
            saved,
            "save/load is loss-free at the decision boundary "
            "(docs/L1/protocol.md §5, ASM-5)",
        )
        fresh = J.build_learner(spec)
        control = [
            J.action_index(J.act(fresh, observation, mask))
            for observation, mask in decisions
        ]
        self.assertNotEqual(
            control,
            saved,
            "the saved learner must be past its initial state, or a restore that "
            "dropped the learned parameters would pass this comparison "
            "(docs/L2/agents/surface.md §7, §9)",
        )

    def test_join_agt_7_2_a_checkpoint_is_loadable_from_its_path_alone(self):
        """JOIN-AGT-7.2 `load(None, path)` restores the same decision boundary.

        `docs/L2/agents/surface.md` §9: a checkpoint recovers everything from the file
        itself, so a member is loadable from its path alone — which is how
        `evaluation.policy_from` loads a shipped version (`docs/L1/records.md` §7).
        """
        encoder, _spec, learner = self.learned()
        path = J.save(learner, self.checkpoint_path(J.CHECKPOINT_GAMMA))
        restored = J.load(None, path)
        self.assertEqual(
            J.param_count(restored),
            J.param_count(learner),
            "the path alone carries the learner's capacity "
            "(docs/L2/agents/surface.md §5, §9)",
        )
        decisions = self.decisions(encoder)
        for position, (observation, mask) in enumerate(decisions):
            self.assertEqual(
                J.action_index(J.act(restored, observation, mask)),
                J.action_index(J.act(learner, observation, mask)),
                "load(None, path) must restore the decision boundary "
                "(docs/L2/agents/surface.md §9), decision %d" % (position,),
            )

    def test_join_agt_7_3_a_loaded_member_becomes_a_policy_at_its_seed(self):
        """JOIN-AGT-7.3 a path-only checkpoint's policy at its seed decides as the learner.

        `docs/L2/agents/surface.md` §10: for a learner restored by §9 the seed to pass
        `as_policy` is the checkpoint's recorded seed, and at that seed the policy
        decides exactly as `act` does.  `docs/L1/records.md` §7 makes the seed and the
        path both required of a version record, and this equality is what lets a
        shipped version play in the league (`docs/L1/protocol.md` §5, D-16).
        """
        encoder, _spec, learner = self.learned()
        path = J.save(learner, self.checkpoint_path(J.CHECKPOINT_BETA))
        member = J.load(None, path)
        policy = J.as_policy(member, encoder, J.LEARNER_SEED)
        compared = 0
        for deal in (J.DEAL_SEED_A, J.DEAL_SEED_B):
            for _hand, facts, legal, _chosen, _index in J.walk(deal, J.caller):
                mask = J.legal_indices(legal)
                by_act = J.action_index(
                    J.act(learner, J.encode(encoder, facts), mask)
                )
                chosen = policy(facts, legal)
                self.assert_descriptor_in(legal, chosen, "member policy")
                self.assertEqual(
                    J.descriptor_index(legal, chosen),
                    by_act,
                    "a member's policy at the checkpoint's seed decides as its "
                    "learner does (docs/L2/agents/surface.md §10, "
                    "docs/L1/protocol.md §5)",
                )
                compared += 1
        self.assertGreaterEqual(
            compared,
            4,
            "the equality must be shown over several decisions of two real hands",
        )

    def test_join_agt_7_4_a_two_rule_pair_keeps_one_capacity_and_its_own_rule(self):
        """JOIN-AGT-7.4 a two-rule pair has one capacity, each policy names its own rule, and a double-Q member round-trips with its rule.

        `docs/L1/rules.md` §3 and §8: the rule is an axis a pair may differ on, and
        the two members hold one capacity (`docs/L2/agents/surface.md` §5, ASM-10,
        D-19) — so `param_count` cannot tell them apart while
        `as_policy(...).learning_rule` must (`docs/L1/e2e-surface.md` §2,
        `docs/L2/agents/surface.md` §10).  The double-Q member then goes through
        `save`/`load` from its path alone with its rule intact (`docs/L1/rules.md`
        §6, `docs/L2/agents/surface.md` §9), which is what lets a shipped version
        certify the population it belongs to (`docs/L1/records.md` §7).
        """
        catalogue = tuple(J.learners()["learning_rules"])
        self.assertGreaterEqual(
            len(catalogue),
            2,
            "the rule catalogue carries the two members this case pairs "
            "(docs/L1/rules.md §2, D-19)",
        )
        first, second = catalogue[0], catalogue[1]
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        spec = J.learner_spec(
            "naive-stack", J.WIDTH_ONE, J.DEPTH_ONE, J.LEARNER_SEED
        )
        named = dict(spec)
        named["learning_rule"] = second
        learners = []
        for rule, learner_spec in ((first, spec), (second, named)):
            with self.subTest(rule=rule):
                learner = J.build_learner(learner_spec)
                policy = J.as_policy(learner, encoder, J.LEARNER_SEED)
                self.assertEqual(
                    getattr(policy, "learning_rule", None),
                    rule,
                    "a policy carries the catalogue member its learner was built "
                    "under (docs/L1/e2e-surface.md §2, docs/L2/agents/surface.md §10, "
                    "D-19)",
                )
                learners.append(learner)
        self.assertEqual(
            J.param_count(learners[0]),
            J.param_count(learners[1]),
            "the two catalogue members hold one trainable capacity, so a pair may "
            "differ on the rule and still be matched (docs/L1/rules.md §3, ASM-10, "
            "D-19)",
        )

        # A tiny budget: one played hand's transitions at seat 0, so the member has
        # consumed something and its recorded position is not a fresh learner's.
        doubled = learners[1]
        episode = J.play_hand(J.DEAL_REWARD_A, J.caller, J.caller)
        batch = J.seat_transitions(episode, 0, encoder)
        consumed = J.learn(doubled, batch)
        self.assertEqual(J.transitions_consumed(consumed), len(batch))
        self.assertTrue(J.finite(J.td_error(consumed)))

        path = J.save(doubled, self.checkpoint_path(J.CHECKPOINT_BETA))
        restored = J.load(None, path)
        self.assertEqual(
            getattr(J.as_policy(restored, encoder, J.LEARNER_SEED), "learning_rule", None),
            second,
            "a member loaded from its path alone learns under the rule its container "
            "records (docs/L2/agents/surface.md §9, docs/L1/rules.md §6, D-19)",
        )
        self.assertEqual(
            J.param_count(restored),
            J.param_count(doubled),
            "a restore recovers the member's capacity as well as its rule "
            "(docs/L2/agents/surface.md §5, §9)",
        )
        # `learn` reads no exploration draw, so one probe batch on both learners is
        # an equality on the parameters and the target copy the file carries, at a
        # position where `act` would still be exploring (`docs/L2/agents/surface.md`
        # §7, §9, `docs/L1/protocol.md` §5, ASM-5).
        probe = J.tiled(batch, J.BATCH_LENGTH)
        saved = J.learn(doubled, probe)
        loaded = J.learn(restored, probe)
        self.assertEqual(
            J.transitions_consumed(loaded),
            J.transitions_consumed(saved),
            "the restored member consumes the batch its saved learner consumes "
            "(docs/L2/agents/surface.md §7, §9)",
        )
        self.assertEqual(
            J.td_error(loaded),
            J.td_error(saved),
            "the restored member's next update is not its saved learner's: the "
            "target copy, the counter and the position the file records did not "
            "travel (docs/L2/agents/surface.md §9, docs/L3/agents/checkpoint.md §1-§4)",
        )


if __name__ == "__main__":
    unittest.main()
