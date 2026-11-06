"""JOIN-AGT-7 — checkpoints as league members.

`docs/L2/agents/surface.md` §8–§10 and `docs/L2/agents/learner.md` §4: `save`/`load`
is loss-free at the decision boundary, a checkpoint is loadable from its path alone,
and a policy built at the checkpoint's recorded seed decides as its learner did —
which is what lets a shipped version be a league member (`docs/L1/records.md` §7,
`docs/L1/protocol.md` §5, ASM-5).  The checkpoint is saved at a *learned* state and
the exploration schedule is annealed past the catalogue's `samples`, so the compared
decisions are taken on the greedy arm; otherwise a restore that dropped the
parameters would pass.
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


if __name__ == "__main__":
    unittest.main()
