"""JOIN-AGT-12 — the utility axis at the join.

`docs/L3/agents/utility.md` §4, §7, `docs/L3/agents/checkpoint.md` §4,
`docs/L1/utilities.md` §3, §5, §6, §7 and D-20: a learner spec selects the terminal
reward it is trained on, the two catalogue members are **one capacity**, and a version
carries the member it was trained under so a table can name the objective it measured.
Every one of those is a join and not a module's own statement — the member is selected
through `agents.build_learner`, the model is driven by observations `features.encode`
makes of readouts `engine.readout` dealt, the reward the terminal transition carries is
`engine.play_hand`'s payoff transformed by `training`'s transition record, and the
objective travels with a checkpoint through `agents.save`/`agents.load` into the policy
`agents.as_policy` returns, whose restore is loss-free in `utility` as in everything else
(`checkpoint.md` §4, `docs/L1/e2e-surface.md` §2, §3.3).  This file walks that path under
**each** catalogue member: it builds one learner per member, encodes real decisions
through the granted `features` calls, learns from a real episode's transitions, saves,
loads, and compares the restored learner's decisions and reported `utility` with the
saved one's — and then states the capacity claim the axis rests on, because a pair whose
arms declare two utilities still has to be matched (`utility.md` §4, ASM-10, D-20).

Nothing here re-asserts what `tests/e2e/test_fam18_utilities.py` already drives one layer
up (the catalogue's own shape, the variant entry's refusals, the run record's utility set,
the pool id, the matrix's `utility_population`), and nothing here asserts the utility's
arithmetic: that lives where the transition record is built (`docs/L1/battery.md` §5,
`utility.md` §5, §6).  The instances — the widths, depths, deals and container names —
are the support module's invented ones (`docs/L1/battery.md` §4, D-15).
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


class UtilityAtTheJoin(J.JoinCase):
    """One learner per catalogue utility, driven through the join and restored."""

    def catalogue(self):
        """The utility catalogue `agents.learners()` publishes, in its declared order.

        `docs/L1/utilities.md` §2 makes `learners()` publish it and §5 makes its first
        member the declared default, so the order is read rather than assumed; a
        catalogue of fewer than two members cannot state this file's claim at all.
        """
        declared = J.learners()["utilities"]
        names = list(declared)
        self.assertGreaterEqual(
            len(names),
            2,
            "agents.learners()['utilities'] must publish the two members "
            "docs/L1/utilities.md §2 declares, and it published %r" % (names,),
        )
        return names

    def spec(self, utility):
        """One invented learner spec (`docs/L1/records.md` §3) naming `utility`."""
        spec = dict(
            J.learner_spec("naive-stack", J.WIDTH_ONE, J.DEPTH_ONE, J.LEARNER_SEED)
        )
        spec["utility"] = utility
        return spec

    def trained(self, utility, path):
        """`(encoder, learned learner)` for one utility, saved at `path`.

        The batch is built from a real episode of an invented deal — the observation of
        each decision is `features.encode` of `engine.readout`'s facts, the action is the
        index `features.legal_indices` aligns to the descriptor the caller played, and the
        terminal record carries `engine.play_hand`'s payoff, which is what the utility
        re-expresses (`docs/L1/records.md` §4, §5, `docs/L1/utilities.md` §4).  It is then
        tiled past the catalogue's exploration `samples`, so the compared decisions are
        the greedy arm's and a restore that dropped the parameters would fail below.
        """
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        learner = J.build_learner(self.spec(utility))
        episode = J.play_hand(J.DEAL_CHECKPOINT_B, J.caller, J.caller)
        batch = J.seat_transitions(episode, 0, encoder)
        self.assertTrue(
            batch,
            "the episode must report a decision for the seat, or no batch is built "
            "(docs/L1/records.md §5)",
        )
        first = J.learn(learner, batch)
        self.assertEqual(
            J.transitions_consumed(first),
            len(batch),
            "learn consumes the real batch it is handed (docs/L2/agents/surface.md §7)",
        )
        annealed = J.learn(learner, J.tiled(batch, J.exploration_samples()))
        self.assertTrue(
            J.finite(J.td_error(annealed)),
            "learn must report a finite td_error under either utility "
            "(docs/L2/agents/surface.md §7, docs/L1/utilities.md §3)",
        )
        J.save(learner, path)
        return encoder, learner

    def decisions(self, encoder):
        """Observations and masks from two invented deals, driven by a caller policy."""
        out = []
        for deal in (J.DEAL_DECISION_A, J.DEAL_TOKEN_B):
            out.extend(J.observations(deal, J.caller, encoder))
        self.assertGreaterEqual(
            len(out),
            4,
            "the comparison must cover several decisions of two real hands",
        )
        return out

    def test_join_agt_12_1_each_utility_survives_save_load_and_as_policy(self):
        """JOIN-AGT-12.1 under each catalogue utility a learner round-trips and reports its own member.

        `docs/L1/utilities.md` §6 and `docs/L1/e2e-surface.md` §2: the container records
        the utility its learner was trained under, a restore recovers the learner under
        it, and the policy `agents.as_policy` builds carries it — so a table can name each
        member's objective even when no record of the run exists yet
        (`docs/L1/records.md` §7).  The restored learner must also **decide as the saved
        one does** on real encoded decisions, and its policy at the recorded seed must
        choose the same descriptor as `act` reads off its own parameters: a restore that
        carried the label and not the state would otherwise pass
        (`docs/L1/protocol.md` §5, ASM-5).
        """
        for utility in self.catalogue():
            with self.subTest(utility=utility):
                path = self.checkpoint_path("%s-%s" % (utility, J.CHECKPOINT_ALPHA))
                encoder, learner = self.trained(utility, path)
                saved_policy = J.as_policy(learner, encoder, J.LEARNER_SEED)
                self.assertEqual(
                    getattr(saved_policy, "utility", None),
                    utility,
                    "a policy carries the catalogue member whose reward its learner was "
                    "trained on (docs/L1/e2e-surface.md §2, docs/L1/utilities.md §7, D-20)",
                )
                restored = J.load(None, path)
                self.assertEqual(
                    J.param_count(restored),
                    J.param_count(learner),
                    "a restored member reports the saved capacity, which no utility "
                    "changes (docs/L1/utilities.md §3, docs/L2/agents/surface.md §5)",
                )
                self.assertEqual(
                    getattr(
                        J.as_policy(restored, encoder, J.LEARNER_SEED), "utility", None
                    ),
                    utility,
                    "a member loaded from its path alone is trained on the member its "
                    "container records (docs/L1/utilities.md §6, D-20)",
                )
                by_spec = J.load(self.spec(utility), path)
                self.assertEqual(
                    getattr(
                        J.as_policy(by_spec, encoder, J.LEARNER_SEED), "utility", None
                    ),
                    utility,
                    "a spec naming the file's own utility agrees on that compared key and "
                    "loads under it (docs/L1/utilities.md §6)",
                )
                for position, (observation, mask) in enumerate(self.decisions(encoder)):
                    chosen = J.action_index(J.act(learner, observation, mask))
                    self.assertEqual(
                        J.action_index(J.act(restored, observation, mask)),
                        chosen,
                        "save/load is loss-free at the decision boundary under %r "
                        "(docs/L1/protocol.md §5, ASM-5), decision %d"
                        % (utility, position),
                    )
                fresh = J.build_learner(self.spec(utility))
                self.assertNotEqual(
                    [
                        J.action_index(J.act(fresh, observation, mask))
                        for observation, mask in self.decisions(encoder)
                    ],
                    [
                        J.action_index(J.act(learner, observation, mask))
                        for observation, mask in self.decisions(encoder)
                    ],
                    "a learner only at its initial draw decides as the saved one on every "
                    "compared decision, so a restore that dropped the learned parameters "
                    "would pass the equality above (docs/L2/agents/surface.md §7, §9)",
                )
                policy = J.as_policy(restored, encoder, J.LEARNER_SEED)
                for deal in (J.DEAL_DECISION_A, J.DEAL_DECISION_B):
                    for _hand, facts, legal, _chosen, _index in J.walk(deal, J.caller):
                        mask = J.legal_indices(legal)
                        by_act = J.action_index(
                            J.act(learner, J.encode(encoder, facts), mask)
                        )
                        descriptor = policy(facts, legal)
                        self.assert_descriptor_in(legal, descriptor, "restored policy")
                        self.assertEqual(
                            J.descriptor_index(legal, descriptor),
                            by_act,
                            "the restored member's policy at the checkpoint's seed "
                            "decides as its saved learner does (docs/L2/agents/"
                            "surface.md §10, docs/L1/protocol.md §5), deal %r" % (deal,),
                        )

    def test_join_agt_12_2_the_two_utilities_learners_are_one_capacity(self):
        """JOIN-AGT-12.2 the two catalogue members' learners report one `param_count`.

        `docs/L1/utilities.md` §3, ASM-10 and D-20: a utility changes the number a
        terminal transition carries and nothing of the state layout, so `param_count` — the
        matched-budget measurement — is identical under either member.  That is what lets
        two arms of a pair differ on the `utility` axis alone and still be comparable
        (`docs/L1/utilities.md` §8, D-3); the member each reports then differs, so the
        equality is a claim about capacity and not about the two learners being one.
        """
        names = self.catalogue()
        first, second = names[0], names[1]
        encoder = J.build_encoder(J.encoding_for("naive-stack"))
        learners = {}
        for utility in (first, second):
            with self.subTest(utility=utility):
                learner = J.build_learner(self.spec(utility))
                self.assertGreater(
                    J.param_count(learner),
                    0,
                    "a learner built under %r is sized like a learner, or there is no "
                    "capacity to match (docs/L2/agents/surface.md §5, "
                    "docs/L1/utilities.md §3)" % (utility,),
                )
                learners[utility] = learner
        self.assertEqual(
            J.param_count(learners[first]),
            J.param_count(learners[second]),
            "the two utilities are one capacity: a pair may differ on the utility axis "
            "and be matched on parameters (docs/L1/utilities.md §3, §8, ASM-10, D-20)",
        )
        policies = [
            J.as_policy(learners[utility], encoder, J.LEARNER_SEED)
            for utility in (first, second)
        ]
        self.assertEqual(
            [getattr(policy, "utility", None) for policy in policies],
            [first, second],
            "each policy names its own catalogue member, so one capacity under two "
            "utilities is still two named objectives (docs/L1/e2e-surface.md §2, "
            "docs/L1/utilities.md §7, D-20)",
        )


if __name__ == "__main__":
    unittest.main()
