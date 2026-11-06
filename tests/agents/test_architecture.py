"""AGT-13 — the rung axes, each made observable through an entry point.

Drives `docs/L3/agents/architecture.md` §2-§5 at the one place the rest of this
battery could not see them: `residual` against `plain`, and `sparse` against a
dense trunk, built from one spec at one shape and one seed, then driven through
`learn` and `act`. The axis is invisible to `param_count` alone — §2's residual
connection adds no parameter, so a trunk shared between `residual` and `plain`
would pass every count in the battery — and it is invisible to `act` on a fresh
learner, because a learner at position 0 explores at the schedule's `start`
(1.0) and the kind's keyed draw decides which index comes back (`rule.md` §4).
So each case reads the axis where the forward pass is the only difference left:
`learn`'s mean absolute TD error on one identical batch (`rule.md` §3), and the
indices 20 real decisions come back with on two learners the same batch has
moved. `sparse` is asserted twice — as the count difference §5's `D·(k + W)`
states for `s = 0.5`, and as a signal no dense trunk produces. R5 and R6 are the
axes those kinds exist for (`docs/L1/ladder.md` §2, D-3); guardrails G4 and G10
are the notes naming the gap these cases close (`guardrails.md`).
"""

import unittest

import numpy as np

from _agents_support import (
    LEARNER_SEED,
    AgentsCase,
    anneal_batch,
    declared_internal,
    finite_float,
    invented_observations,
    learner_spec,
    plain_int,
    quiet_batch,
    schedule,
    target_interval,
    transition,
)

#: The invented observations and the invented rewards `mixed_batch` hands one pair
#: of learners: no number here is a design number, and every reward is paid on a
#: terminal record only, which is where ASM-12 delivers it (`rule.md` §2).
MIXED_SEED = 1777
MIXED_REWARDS = (6.5, -3.25, 11.0, -1.75)


def mixed_batch(count=8, seed=MIXED_SEED):
    """`count` invented token transitions, non-degenerate by construction.

    Several distinct observations, a non-terminal and a terminal record, and a
    non-zero reward on each of the latter, so a mean absolute TD error over this
    batch (`rule.md` §3) is a statistic over a varied batch and not the
    coincidence of one record. The family is the six token kinds' own
    (`architecture.md` §1), read from `features.observation_spec` by the support
    helper and never copied.
    """
    values = invented_observations("deep", count + 1, seed)
    records = []
    paid = 0
    for step in range(count):
        terminal = step % 3 == 0
        reward = 0.0
        if terminal:
            reward = MIXED_REWARDS[paid % len(MIXED_REWARDS)]
            paid += 1
        records.append(
            transition(
                values[step],
                action=step % 3,
                reward=reward,
                terminal=terminal,
                next_observation=values[step + 1],
            )
        )
    return records


class ArchitectureAxisTest(AgentsCase):
    def test_agt13_1_residual_and_plain_share_a_count_but_not_a_forward_pass(self):
        """AGT-13.1 `residual` and `plain` at one width, depth and seed hold **the same parameters** — the residual connection adds none (`architecture.md` §2, §5) — and yet report different mean absolute TD errors on one identical batch, so the kind decides the trunk connection and the two kinds do not share one code path (`architecture.md` §2-§4, `rule.md` §2-§3, §8, `ladder.md` §2, D-3)."""
        package = self.agents()
        width, depth = 6, 2
        records = mixed_batch()
        self.assert_mixed(records)
        residual = self.build(kind="residual", width=width, depth=depth)
        plain = self.build(kind="plain", width=width, depth=depth)
        count = declared_internal("model", "_param_count_for")
        self.assertEqual(
            package.param_count(residual),
            package.param_count(plain),
            "architecture.md §2 gives `residual` the same D trunk layers of shape "
            "W x W as `plain` — it adds the delta, it does not add a weight — so "
            "the two kinds must hold one number of parameters at one shape: %r "
            "against %r"
            % (package.param_count(residual), package.param_count(plain)),
        )
        for kind, learner in (("residual", residual), ("plain", plain)):
            with self.subTest(kind=kind):
                self.assertEqual(
                    package.param_count(learner),
                    int(count(kind, width, depth, 0.0)),
                    "the count is not architecture.md §5's formula for that kind",
                )
        initial = declared_internal("model", "_initial_parameters")
        self.assertTrue(
            np.array_equal(
                np.asarray(initial("residual", width, depth, 0.0, LEARNER_SEED)),
                np.asarray(initial("plain", width, depth, 0.0, LEARNER_SEED)),
            ),
            "one seed drew two different parameter vectors for the two kinds "
            "(architecture.md §4), so a differing statistic would not be the "
            "trunk's",
        )
        residual_result = package.learn(residual, records)
        plain_result = package.learn(plain, records)
        for label, result in (("residual", residual_result), ("plain", plain_result)):
            with self.subTest(kind=label):
                self.assertEqual(
                    plain_int(result["transitions"], "transitions"), len(records)
                )
        residual_error = finite_float(residual_result["td_error"], "td_error")
        plain_error = finite_float(plain_result["td_error"], "td_error")
        self.assertNotEqual(
            residual_error,
            plain_error,
            "`residual` and `plain` reported one mean absolute TD error (%r) for "
            "one batch from one seed: h + relu(z) and relu(z) are one forward "
            "pass, so the kind does not decide the trunk connection "
            "(architecture.md §2-§3)" % (residual_error,),
        )

    def test_agt13_2_sparse_masks_its_trunk_so_its_signal_differs_from_a_dense_trunk(self):
        """AGT-13.2 a `sparse` learner and a `deep` one at one width and depth differ in `param_count` exactly as `architecture.md` §5's `D·(k + W)` at `s = 0.5` says, and report different mean absolute TD errors on one identical batch: the mask is real, so this is not a dense trunk with a smaller count (`architecture.md` §2-§3, §5, `rule.md` §2-§3, §8, `ladder.md` §2, R5)."""
        package = self.agents()
        width, depth, sparsity = 6, 2, 0.5
        records = mixed_batch()
        self.assert_mixed(records)
        dense = self.build(kind="deep", width=width, depth=depth)
        sparse = package.build_learner(
            learner_spec(
                architecture={
                    "kind": "sparse",
                    "width": width,
                    "depth": depth,
                    "sparsity": sparsity,
                }
            )
        )
        count = declared_internal("model", "_param_count_for")
        self.assertEqual(
            package.param_count(dense),
            int(count("deep", width, depth, 0.0)),
            "the dense trunk's count is not architecture.md §5's formula",
        )
        self.assertEqual(
            package.param_count(sparse),
            int(count("sparse", width, depth, sparsity)),
            "the sparse count is not the input block, the output layer and "
            "D·(k + W) at s = 0.5 with k = round((1 - s)·W²) "
            "(architecture.md §5)",
        )
        self.assertNotEqual(
            package.param_count(sparse),
            package.param_count(dense),
            "the sparse learner holds as many parameters as the dense one at "
            "s = 0.5, so no slot of a trunk layer was pinned to zero "
            "(architecture.md §3)",
        )
        dense_error = finite_float(
            package.learn(dense, records)["td_error"], "the dense td_error"
        )
        sparse_error = finite_float(
            package.learn(sparse, records)["td_error"], "the sparse td_error"
        )
        self.assertNotEqual(
            dense_error,
            sparse_error,
            "a masked trunk and a dense one reported one mean absolute TD error "
            "(%r) for one batch from one seed: the mask is not materialised "
            "before the matmul, so `sparse` is a dense trunk with a smaller "
            "count (architecture.md §2-§3)" % (dense_error,),
        )

    def test_agt13_3_the_residual_axis_survives_learning(self):
        """AGT-13.3 one identical batch — the schedule's own length at the annealed rate, then `target_update_interval` real transitions — leaves `residual` and `plain` at one position, one seed and one schedule, so the keyed draw is one draw (`rule.md` §4); over 20 real decisions, at least 16 greedy-expected, at least one `act` index differs, and only the trunk connection of `architecture.md` §2 can make it differ (`architecture.md` §2-§3, `rule.md` §3-§5, D-3, R6)."""
        package = self.agents()
        width, depth = 8, 2
        # `quiet_batch` reaches the annealed rate without moving a parameter
        # (`_agents_support.quiet_batch`), and the `target_update_interval`
        # transitions after it are the batch this case is about: on a fresh pair
        # the exploring arm, whose draw is one draw for both kinds, would decide
        # nine decisions in ten and the case could not tell the two forward
        # passes apart (`rule.md` §4).
        samples = int(schedule()["samples"])
        records = quiet_batch("residual") + anneal_batch("residual")[
            : target_interval()
        ]
        self.assertEqual(
            len(records),
            samples + target_interval(),
            "the batch does not start from the annealed position and then hand "
            "this many real transitions",
        )
        residual = self.annealed_learner(
            "axis-residual",
            {"kind": "residual", "width": width, "depth": depth},
            records,
        )
        plain = self.annealed_learner(
            "axis-plain", {"kind": "plain", "width": width, "depth": depth}, records
        )
        self.assertEqual(
            package.param_count(residual),
            package.param_count(plain),
            "the pair this case moves does not hold one parameter vector, so a "
            "differing decision would not be the trunk's (architecture.md §2)",
        )
        rows = self.decisions(20)
        self.assertGreaterEqual(len(rows), 12, "fewer than twelve decisions")
        observations, masks = map(
            list, zip(*self.decision_observations(rows, "residual"))
        )
        self.greedy_arm(LEARNER_SEED, "residual", observations, masks, 16)
        answers = [
            (
                package.act(residual, observation, mask)["action"],
                package.act(plain, observation, mask)["action"],
            )
            for observation, mask in zip(observations, masks)
        ]
        differing = [
            index for index, (left, right) in enumerate(answers) if left != right
        ]
        self.assertGreaterEqual(
            len(differing),
            1,
            "`residual` and `plain` decided all %d decisions identically after "
            "one batch from one seed, so one forward pass answered both kinds "
            "(architecture.md §2-§3)" % (len(answers),),
        )

    def assert_mixed(self, records):
        """Guard the non-degeneracy the two `td_error` inequalities rest on.

        Each inequality is a statement about two forward passes, and it holds for
        any correct implementation **only** while the statistic is not one
        record's: so the batch holds distinct observations, both terminal flags,
        and at least one non-zero reward (`rule.md` §2-§3, ASM-12).
        """
        self.assertGreaterEqual(len(records), 4)
        self.assertEqual(
            len({record["observation"].tobytes() for record in records}),
            len(records),
            "the batch repeats an observation, so its mean absolute TD error is "
            "one record's and the inequality could be a coincidence",
        )
        self.assertTrue(
            any(not record["terminal"] for record in records),
            "the batch holds no non-terminal transition, so no target bootstraps "
            "and the successor is never read",
        )
        self.assertTrue(
            any(record["terminal"] for record in records),
            "the batch holds no terminal transition, so no target is a reward",
        )
        self.assertTrue(
            any(record["reward"] != 0.0 for record in records),
            "every reward is zero, so the two targets are both pure bootstraps",
        )


if __name__ == "__main__":
    unittest.main()
