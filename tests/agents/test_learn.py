"""AGT-6 — `learn(learner, transitions)`.

Drives `docs/L2/agents/surface.md` §7, `docs/L3/agents/rule.md` §2-§3,
`docs/L1/records.md` §4 and ASM-12: two plain statistics, a real learning
signal on one repeated transition, a terminal target that is the reward alone,
the caller's order as the sample order in both directions (the same three
transitions reversed report a different statistic), what the batch taught
deciding a later action, and the batch/transition refusals (D-2, ASM-7).
"""

import unittest
from collections.abc import Mapping

from _agents_support import (
    LEARNER_SEED,
    TEACH_REWARD,
    AgentsCase,
    batch,
    dense_observation,
    finite_float,
    plain_int,
    taught_batch,
    token_observation,
    transition,
)


class LearnTest(AgentsCase):
    def test_agt6_1_the_statistics_are_the_two_declared_keys(self):
        """AGT-6.1 the update returns exactly `td_error` and `transitions`, plain and finite (`surface.md` §7, G8, `rule.md` §3)."""
        package = self.agents()
        for length in (6, 11):
            with self.subTest(transitions=length):
                learner = self.build(kind="naive-stack", width=6, depth=1)
                records = batch(
                    [dense_observation(0.03 * index) for index in range(length)]
                )
                result = package.learn(learner, records)
                self.assertIsInstance(result, Mapping)
                self.assertEqual(set(result), {"td_error", "transitions"})
                error = finite_float(result["td_error"], "learn(...)['td_error']")
                self.assertGreaterEqual(error, 0.0)
                consumed = plain_int(
                    result["transitions"], "learn(...)['transitions']"
                )
                self.assertEqual(consumed, length)

    def test_agt6_2_the_signal_is_real(self):
        """AGT-6.2 learning one transition twice lowers the second `td_error` strictly (`rule.md` §3, `surface.md` §7)."""
        package = self.agents()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        record = transition(
            dense_observation(0.0),
            next_observation=dense_observation(0.5),
            action=1,
            reward=0.0,
            terminal=False,
        )
        first = finite_float(
            package.learn(learner, [record])["td_error"], "the first td_error"
        )
        second = finite_float(
            package.learn(learner, [record])["td_error"], "the second td_error"
        )
        self.assertGreater(first, 0.0)
        self.assertLess(
            second,
            first,
            "a second semi-gradient step on one transition did not lower the "
            "TD error: %r then %r" % (first, second),
        )

    def test_agt6_3_a_terminal_reward_is_the_target(self):
        """AGT-6.3 a terminal target is the reward alone: the successor is not read (`rule.md` §2, `surface.md` §7, ASM-12)."""
        package = self.agents()
        observation = dense_observation(0.0)
        successor = dense_observation(0.5)
        other_successor = dense_observation(-0.9)
        cheap = transition(observation, next_observation=successor,
                           action=1, reward=7.5, terminal=True)
        rich = transition(observation, next_observation=successor,
                          action=1, reward=11.25, terminal=True)
        same_reward_other_successor = transition(
            observation,
            next_observation=other_successor,
            action=1,
            reward=7.5,
            terminal=True,
            next_legal=(2,),
        )
        cheap_error = finite_float(
            package.learn(self.build(kind="naive-stack", width=6, depth=1), [cheap])[
                "td_error"
            ],
            "the 7.5 terminal td_error",
        )
        rich_error = finite_float(
            package.learn(self.build(kind="naive-stack", width=6, depth=1), [rich])[
                "td_error"
            ],
            "the 11.25 terminal td_error",
        )
        other_error = finite_float(
            package.learn(
                self.build(kind="naive-stack", width=6, depth=1),
                [same_reward_other_successor],
            )["td_error"],
            "the other-successor terminal td_error",
        )
        self.assertNotEqual(
            cheap_error,
            rich_error,
            "two terminal rewards moved the TD error identically",
        )
        self.assertEqual(
            cheap_error,
            other_error,
            "a terminal transition's TD error read its successor, which the "
            "reward-only target never does",
        )

    def test_agt6_4_the_batch_order_is_the_callers(self):
        """AGT-6.4 the batch is consumed as handed: no sampling, no shuffle (`surface.md` §7, `rule.md` §3, G7, ASM-7)."""
        package = self.agents()
        first = transition(
            dense_observation(0.0), next_observation=dense_observation(0.4),
            action=1, reward=0.0, terminal=False,
        )
        second = transition(
            dense_observation(0.8), next_observation=dense_observation(-0.2),
            action=2, reward=0.0, terminal=False,
        )
        forward = package.learn(
            self.build(kind="naive-stack", width=6, depth=1), [first, second]
        )
        backward = package.learn(
            self.build(kind="naive-stack", width=6, depth=1), [second, first]
        )
        for label, result in (("forward", forward), ("backward", backward)):
            with self.subTest(order=label):
                self.assertEqual(plain_int(result["transitions"], "transitions"), 2)
                finite_float(result["td_error"], "td_error")
        one_a = package.learn(
            self.build(kind="naive-stack", width=6, depth=1), [first]
        )
        one_b = package.learn(
            self.build(kind="naive-stack", width=6, depth=1), [first]
        )
        self.assertEqual(
            plain_int(one_a["transitions"], "transitions"),
            plain_int(one_b["transitions"], "transitions"),
        )
        self.assertEqual(
            finite_float(one_a["td_error"], "td_error"),
            finite_float(one_b["td_error"], "td_error"),
            "a single-transition batch was not consumed as handed (the two "
            "identical calls disagree), so the batch is sampled or shuffled",
        )

    def test_agt6_6_a_reordered_batch_is_a_different_update(self):
        """AGT-6.6 the same three transitions in another order report a different `td_error`, and both report three consumed (`rule.md` §3, `surface.md` §7, G7, ASM-7)."""
        package = self.agents()
        first = transition(
            dense_observation(0.1), action=1, reward=12.5, terminal=True
        )
        second = transition(
            dense_observation(0.6), action=2, reward=-7.0, terminal=True
        )
        third = transition(
            dense_observation(-0.35), action=0, reward=3.25, terminal=True
        )
        forward = package.learn(
            self.build(kind="naive-stack", width=6, depth=1), [first, second, third]
        )
        backward = package.learn(
            self.build(kind="naive-stack", width=6, depth=1), [third, second, first]
        )
        for label, result in (("forward", forward), ("backward", backward)):
            with self.subTest(order=label):
                self.assertEqual(plain_int(result["transitions"], "transitions"), 3)
                finite_float(result["td_error"], "td_error")
        self.assertNotEqual(
            finite_float(forward["td_error"], "td_error"),
            finite_float(backward["td_error"], "td_error"),
            "the same three transitions handed in two orders reported one "
            "statistic, so the batch was sorted, shuffled, deduplicated or "
            "replayed instead of consumed in the caller's order (rule.md §3)",
        )

    def test_agt6_7_the_parameters_decide_the_action(self):
        """AGT-6.7 two learners from one spec taught opposing rewards on one action decide differently on at least one of 20 greedy-dominated decisions: the update writes values `act` reads (`rule.md` §2-§5, `surface.md` §4, §6, ASM-5)."""
        package = self.agents()
        raised = self.annealed_learner(
            "taught-raised",
            {"kind": "naive-stack", "width": 6, "depth": 1, "seed": LEARNER_SEED},
            taught_batch("naive-stack", TEACH_REWARD),
        )
        lowered = self.annealed_learner(
            "taught-lowered",
            {"kind": "naive-stack", "width": 6, "depth": 1, "seed": LEARNER_SEED},
            taught_batch("naive-stack", -TEACH_REWARD),
        )
        observations, masks = self.pool_decisions("naive-stack")
        self.greedy_arm(LEARNER_SEED, "naive-stack", observations, masks, 16)
        differences = 0
        for observation, mask in zip(observations, masks):
            with self.subTest(mask=mask):
                up = package.act(raised, observation, mask)["action"]
                down = package.act(lowered, observation, mask)["action"]
                self.assertIn(up, mask)
                self.assertIn(down, mask)
                if up != down:
                    differences += 1
        self.assertGreater(
            differences,
            0,
            "two learners whose batches taught opposing rewards on the same "
            "action answered every greedy-dominated decision alike, so the values "
            "`act` reads do not come from the parameters `learn` wrote",
        )

    def test_agt6_5_the_refusals(self):
        """AGT-6.5 empty, malformed and mismatched batches are refused naming the key (`surface.md` §7, `errors.md` §3)."""
        package = self.agents()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        observation = dense_observation()
        good = transition(observation)

        def with_key(key, value):
            record = dict(good)
            if value is _ABSENT:
                del record[key]
            else:
                record[key] = value
            return record

        cases = [
            ("an empty list", package.learn, (learner, []), (("transitions", "batch"),)),
            ("an empty tuple", package.learn, (learner, ()), (("transitions", "batch"),)),
            ("a dict as the learner", package.learn, ({"learner": 1}, [good]), (("learner",),)),
            (
                "a baseline as the learner",
                package.learn,
                (package.build_baseline("oracle", 7314), [good]),
                (("learner",),),
            ),
            (
                "an action outside that transition's legal",
                package.learn,
                (learner, [dict(good, action=2, legal=(0, 1))]),
                (("action",), ("2",)),
            ),
            (
                "a legal mask holding an index outside the vocabulary",
                package.learn,
                (learner, [dict(good, legal=(0, 1, 3), action=1)]),
                (("legal", "mask"), ("3",)),
            ),
            (
                "a next_legal mask holding an index outside the vocabulary",
                package.learn,
                (learner, [dict(good, next_legal=(0, 4))]),
                (("next_legal", "legal", "mask"), ("4",)),
            ),
            (
                "an empty legal mask",
                package.learn,
                (learner, [dict(good, legal=(), action=1)]),
                (("legal", "mask"),),
            ),
            (
                "an empty next_legal mask",
                package.learn,
                (learner, [dict(good, next_legal=())]),
                (("next_legal", "mask"),),
            ),
            (
                "a token observation on a dense learner",
                package.learn,
                (learner, [dict(good, observation=token_observation())]),
                (("observation",), ("token",), ("dense",)),
            ),
            (
                "a token next_observation on a dense learner",
                package.learn,
                (learner, [dict(good, next_observation=token_observation())]),
                (("observation", "next_observation"), ("token",), ("dense",)),
            ),
        ]
        for key in (
            "observation",
            "next_observation",
            "action",
            "reward",
            "terminal",
            "legal",
            "next_legal",
        ):
            cases.append(
                (
                    "a transition missing %r" % key,
                    package.learn,
                    (learner, [with_key(key, _ABSENT)]),
                    ((key,),),
                )
            )
        for label, fn, args, groups in cases:
            with self.subTest(case=label):
                self.assert_refused(fn, *args, entry="learn", groups=groups, label=label)


_ABSENT = object()


if __name__ == "__main__":
    unittest.main()
