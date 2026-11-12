"""AGT-6 — `learn(learner, transitions)`.

Drives `docs/L2/agents/surface.md` §7, `docs/L3/agents/rule.md` §2-§3,
`docs/L1/records.md` §4 and ASM-12: two plain statistics, a real learning
signal on one repeated transition, a terminal target that is the reward alone,
the caller's order as the sample order in both directions (the same three
transitions reversed report a different statistic), what the batch taught
deciding a later action, the batch/transition refusals, and D-19's two target
arithmetics — the masked maximum of the target copy and the target copy's value
at the index the online parameters choose — with the one path they share, and
the mask every maximum and every index of either rule runs over, observed on a
`next_legal` that excludes the whole vocabulary's argmax (D-2, ASM-7, D-19,
ASM-25).  The last two cases are the third catalogue's own path: **every** transition that
carries a complete resolution — a **terminal** one included, the seat's last decision of a hand
being where the outcome is known and not an exemption — takes `A = len(legal)` semi-gradient
steps whose movement is the **mean** over those steps, each step applying its raw residual
`v_i − q[i]` over the number of steps that transition takes, and both read off one shared
forward pass.  Only a transition whose `counterfactual` is `None` and one whose sequence is
`None` at an index of its own `legal` mask fall back to the single ordinary step — a partial
resolution is not a resolution.  The batch still reports one consumed record and one schedule
position whatever its step count, and its `td_error` is the mean of the **raw** residual
magnitudes over its steps (D-43, `docs/L1/counterfactual.md` §4, §6).
"""

import io
import os
import unittest
from collections.abc import Mapping

import numpy as np

from _agents_support import (
    ALL_MASK,
    LEARNER_SEED,
    NONEMPTY_MASKS,
    TEACH_REWARD,
    AgentsCase,
    batch,
    container_document,
    declared_internal,
    dense_observation,
    finite_float,
    greedy_expectation,
    hyper,
    learner_spec,
    observation_template,
    plain_int,
    taught_batch,
    taught_observations,
    target_interval,
    token_observation,
    transition,
)

#: The reward the prefix teaches the second index after teaching the first one: larger
#: than `TEACH_REWARD`, so the online parameters' masked order and the target copy's
#: diverge over the extra transitions and the two rules are observable apart
#: (`rule.md` §2-§3, D-19).  An invented number, like every fixture here.
REVERSE_REWARD = 60.0

#: The masks a constructed transition is searched over: every mask of more than one
#: index, since a singleton mask cannot tell the two arithmetics apart (`rule.md` §2).
WIDER_MASKS = tuple(mask for mask in NONEMPTY_MASKS if len(mask) > 1)

#: One resolved hand's whole-hand net chip deltas, one per descriptor of `ALL_MASK`'s
#: order: the three numbers such a hand's last decision carries, `fold`,
#: `check-call` and the fixed row's one raise band (`counterfactual.md` §4, §5).
#: The second is the realised action's, so it is that transition's `reward` by §4's
#: identity.  Invented numbers, like every fixture here.
RESOLVED_VALUES = (11.0, -7.0, 23.0)


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

    def _rule_learner(self, rule=None, kind="naive-stack", width=6, depth=1):
        """One learner of this case's spec, under `rule` or the declared default."""
        package = self.agents()
        extra = {} if rule is None else {"learning_rule": rule}
        return package.build_learner(
            learner_spec(kind=kind, width=width, depth=depth, extra=extra)
        )

    def _taught_prefix(self, learner, kind="naive-stack"):
        """The terminal-only prefix both rules consume into identical parameters.

        Every record is terminal, so its target is the reward alone under either
        rule (`rule.md` §2), and two learners built from one spec therefore hold
        identical parameters after it.  The first batch is the schedule's own length,
        so the target copy is refreshed on its last transition; the second teaches a
        larger reward on another index for `target_update_interval - 2` transitions,
        so the online parameters move away from that copy without reaching the next
        refresh (`rule.md` §2-§3, `rule.md` §6).
        """
        package = self.agents()
        package.learn(learner, taught_batch(kind, TEACH_REWARD))
        values = taught_observations(kind)
        package.learn(
            learner,
            [
                transition(
                    values[step % len(values)],
                    action=2,
                    reward=REVERSE_REWARD,
                    terminal=True,
                )
                for step in range(target_interval() - 2)
            ],
        )

    def test_agt6_8_the_two_targets_on_one_transition(self):
        """AGT-6.8 double-Q aims at the target copy's value at the online masked argmax, and the two rules report different updates on at least one constructed transition (`rule.md` §2, §3, `rules.md` §2, ASM-25, D-19).

        The identity needs no private forward pass.  Two learners from one spec —
        one built under `double-q-learning`, one under the declared default — consume
        the same terminal-only prefix, so they hold the same parameters.  At the
        annealed position the index `act` answers is the tie-break over the **online**
        values at the successor (`rule.md` §4-§5), and the masked rule on the
        singleton mask `(index,)` aims at exactly `reward + discount ×
        Q_target(s', index)`; double-Q aims at the target copy's value at the index
        the online parameters chose.  The two `td_error`s being equal is therefore
        the formula stated by hand.  The third clause is the other direction: a third
        masked learner, from the same spec and the same prefix, differs from double-Q
        on at least one constructed transition, so the two rules are not one rule.
        """
        package = self.agents()
        kind = "naive-stack"
        catalogue = tuple(package.learners()["learning_rules"])
        self.assertIn("double-q-learning", catalogue, "the declared second member exists")
        double = self._rule_learner("double-q-learning")
        masked = self._rule_learner()
        third = self._rule_learner()
        folder = self.tempdir()
        for learner in (double, masked, third):
            self._taught_prefix(learner)
        # The two prefix checkpoints are taken before anything learns on the learners
        # above, so every search candidate starts from the documented prefix state
        # (`checkpoint.md` §1, §4): a restore recovers the parameters, the target copy,
        # the counter and the position.
        double_path = package.save(double, os.path.join(folder, "double-8127.pt"))
        masked_path = package.save(third, os.path.join(folder, "masked-8127.pt"))

        observation = dense_observation(0.0)
        successor = dense_observation(-0.3)
        self.greedy_arm(LEARNER_SEED, kind, [successor], [ALL_MASK], 1)
        index = package.act(double, successor, ALL_MASK)["action"]
        self.assertIn(index, ALL_MASK)
        record = transition(
            observation,
            action=1,
            reward=0.0,
            terminal=False,
            next_observation=successor,
            next_legal=ALL_MASK,
        )
        by_double = finite_float(
            package.learn(double, [record])["td_error"], "the double-Q td_error"
        )
        by_singleton = finite_float(
            package.learn(masked, [dict(record, next_legal=(index,))])["td_error"],
            "the masked singleton-mask td_error",
        )
        self.assertEqual(
            by_double,
            by_singleton,
            "double-Q's target is not reward + discount × Q_target(s', index) for the "
            "index %r the online parameters chose over %r: the masked rule on the "
            "singleton mask (index,) is that expression by definition, and the two "
            "reported %r and %r (rule.md §2, rules.md §2)"
            % (index, ALL_MASK, by_double, by_singleton),
        )

        differing = []
        searched = 0
        for successor in taught_observations(kind):
            for mask in WIDER_MASKS:
                searched += 1
                record = transition(
                    observation,
                    action=1,
                    reward=0.0,
                    terminal=False,
                    next_observation=successor,
                    next_legal=mask,
                )
                double_error = finite_float(
                    package.learn(package.load(None, double_path), [record])["td_error"],
                    "the double-Q td_error",
                )
                masked_error = finite_float(
                    package.learn(package.load(None, masked_path), [record])["td_error"],
                    "the masked td_error",
                )
                if double_error != masked_error:
                    differing.append((mask, double_error, masked_error))
        self.assertGreater(
            len(differing),
            0,
            "none of %d constructed transitions told the two arithmetics apart: the "
            "masked rule must aim at the masked maximum of the target copy while "
            "double-Q aims at the copy's value at the index the online parameters "
            "choose, and after a prefix that taught two indices different rewards "
            "over a stale target copy those two targets differ somewhere (rule.md "
            "§2, rules.md §2, ASM-25, D-19)" % (searched,),
        )

    def test_agt6_9_a_terminal_target_is_the_reward_under_both_rules(self):
        """AGT-6.9 at a terminal transition both rules aim at the reward alone, so no successor value is read (`rule.md` §2, `surface.md` §7, ASM-12, D-19).

        The record's `next_observation` and `next_legal` are the ones the two rules
        would read if they bootstrapped, so a rule that read them at a terminal
        transition would report another number; the same reward with another
        successor reports the same one under both members.
        """
        package = self.agents()
        catalogue = tuple(package.learners()["learning_rules"])
        self.assertGreaterEqual(len(catalogue), 2)
        observation = dense_observation(0.0)
        record = transition(
            observation,
            action=1,
            reward=7.5,
            terminal=True,
            next_observation=dense_observation(0.5),
            next_legal=ALL_MASK,
        )
        other = dict(
            record,
            next_observation=dense_observation(-0.9),
            next_legal=(0, 2),
        )
        reported = {}
        for rule in catalogue:
            with self.subTest(rule=rule):
                first = finite_float(
                    package.learn(self._rule_learner(rule), [record])["td_error"],
                    "the terminal td_error",
                )
                second = finite_float(
                    package.learn(self._rule_learner(rule), [other])["td_error"],
                    "the terminal td_error with another successor",
                )
                self.assertEqual(
                    first,
                    second,
                    "a terminal transition's td_error read its successor under %r, "
                    "which the reward-only target never does (rule.md §2, ASM-12)"
                    % (rule,),
                )
                reported[rule] = first
        self.assertEqual(
            len(set(reported.values())),
            1,
            "the two catalogue members report %r at one terminal transition: the "
            "terminal target is the reward under both (rule.md §2, D-19)" % (reported,),
        )

    def test_agt6_10_the_shared_path_is_shared(self):
        """AGT-6.10 one non-terminal batch reports one shape and moves one schedule position under both rules (`surface.md` §7, `rule.md` §3, §8, `checkpoint.md` §2.1, D-19).

        The rule fixes the target and nothing else: validation, the per-transition
        loop, the statistics, the step, the refresh counter and the schedule position
        are one path, so both members report the two declared keys, consume the whole
        batch and land on the same position — the position read where the design
        makes it observable, `checkpoint._read_metadata(path)`'s
        `exploration.position` (`rule.md` §8).
        """
        package = self.agents()
        read_metadata = declared_internal("checkpoint", "_read_metadata")
        catalogue = tuple(package.learners()["learning_rules"])
        self.assertGreaterEqual(len(catalogue), 2)
        folder = self.tempdir()
        records = batch(
            [dense_observation(0.13 * step) for step in range(6)],
            next_observation=dense_observation(-0.4),
        )
        self.assertFalse(any(record["terminal"] for record in records))
        positions = {}
        for rule in catalogue:
            with self.subTest(rule=rule):
                learner = self._rule_learner(rule)
                result = package.learn(learner, records)
                self.assertIsInstance(result, Mapping)
                self.assertEqual(
                    set(result),
                    {"td_error", "transitions"},
                    "the rule fixes the target, not the return's keys (rule.md §3)",
                )
                self.assertGreaterEqual(
                    finite_float(result["td_error"], "learn(...)['td_error']"), 0.0
                )
                self.assertEqual(
                    plain_int(result["transitions"], "learn(...)['transitions']"),
                    len(records),
                    "one batch is consumed whole under %r (rule.md §3)" % (rule,),
                )
                path = package.save(
                    learner, os.path.join(folder, "shared-%s.pt" % (rule,))
                )
                metadata = read_metadata(path)
                positions[rule] = plain_int(
                    metadata["exploration"]["position"], "exploration.position"
                )
        self.assertEqual(
            sorted(positions.values()),
            [len(records)] * len(catalogue),
            "the catalogue's members advanced the schedule position to %r for a batch "
            "of %d transitions: the position advances in learn and nowhere else, "
            "whatever the rule (rule.md §3, surface.md §7, D-19)"
            % (positions, len(records)),
        )

    def test_agt6_11_the_bootstrap_index_is_masked_to_next_legal(self):
        """AGT-6.11 over a `next_legal` that excludes the whole vocabulary's argmax, double-Q bootstraps at the masked tie-break's index and never at the excluded one (`rule.md` §2, §3, §5, `rules.md` §2, `surface.md` §7, D-2, ASM-25, D-19).

        Both targets run **every maximum and every index over `next_legal` only**, so
        an index outside it is never a candidate (`rule.md` §2, §3, `rules.md` §2,
        D-2, ASM-25).  One learner is built under `double-q-learning` and one under
        the declared default as the control; both take the same terminal-only prefix,
        so they hold bit-identical parameters and target copies (AGT-6.8's pattern),
        and every figure below is read from a fresh `load` of that prefix checkpoint,
        so one `learn` call's step never leaks into the next.  In the greedy arm
        `act` answers §5's tie-break over the mask it is handed, and the declared key
        and the annealed rate say that arm is taken (`rule.md` §4-§5, §8), so
        `act(..., mask)` is the tie-break over `next_legal` and `act(..., ALL_MASK)`
        is the argmax over `(0, 1, 2)`; §5's tie-break returns a member of its mask,
        so an excluded argmax is an index the two choices cannot share.  The masked
        rule on a singleton mask aims at exactly `reward + discount ×
        Q_target(s', that index)` (AGT-6.8's identity, the formula stated by hand),
        so the equality names double-Q's index and the inequality rules the excluded
        one out.  The last two clauses prove the case bites: `next_legal` widened to
        the whole vocabulary reports the excluded index's figure and not the masked
        one — the figure a bootstrap over `(0, 1, 2)` reports for the mask under test.
        """
        package = self.agents()
        kind = "naive-stack"
        catalogue = tuple(package.learners()["learning_rules"])
        self.assertGreaterEqual(
            len(catalogue),
            2,
            "the catalogue carries the two members this case pairs (rules.md §2, D-19)",
        )
        double = self._rule_learner("double-q-learning")
        control = self._rule_learner()
        for learner in (double, control):
            self._taught_prefix(learner)
        # The prefix checkpoint of each learner: every figure below comes from a fresh
        # restore of it, so no earlier `learn` call's step is in any of them (AGT-6.8).
        folder = self.tempdir()
        double_path = package.save(double, os.path.join(folder, "double-mask-8127.pt"))
        control_path = package.save(control, os.path.join(folder, "control-mask-8127.pt"))

        # The premise: the terminal-only prefix left the two learners one state.  A
        # terminal batch reads no rule at all (`rule.md` §2), so one figure twice is one
        # set of parameters and one target copy, which is what the identity needs.
        probe = [transition(dense_observation(0.0), action=1, reward=5.0, terminal=True)]
        self.assertEqual(
            finite_float(
                package.learn(package.load(None, double_path), probe)["td_error"],
                "the double-Q prefix probe",
            ),
            finite_float(
                package.learn(package.load(None, control_path), probe)["td_error"],
                "the masked prefix probe",
            ),
            "the two learners did not come out of one terminal-only prefix holding one "
            "state, so the figures compared below are two learners' and not one "
            "(rule.md §2, AGT-6.8)",
        )

        observation = dense_observation(0.0)
        chosen = None
        for successor in taught_observations(kind):
            for mask in WIDER_MASKS:
                # Both decisions must be the greedy arm's, or `act` would answer §4's
                # exploring arm instead of §5's tie-break (`rule.md` §4, §5, §8).
                if greedy_expectation(
                    LEARNER_SEED, kind, [successor, successor], [mask, ALL_MASK]
                ) < 2:
                    continue
                by_mask = package.act(package.load(None, double_path), successor, mask)
                by_whole = package.act(
                    package.load(None, double_path), successor, ALL_MASK
                )
                if by_mask["action"] in mask and by_whole["action"] not in mask:
                    chosen = (successor, mask, by_mask["action"], by_whole["action"])
                    break
            if chosen is not None:
                break
        self.assertIsNotNone(
            chosen,
            "no constructed successor let the masked tie-break and the whole "
            "vocabulary's argmax differ, so this case cannot show that double-Q's "
            "index runs over next_legal alone (rule.md §2, §5, D-2, ASM-25)",
        )
        successor, mask, masked_index, whole_index = chosen
        self.greedy_arm(
            LEARNER_SEED, kind, [successor, successor], [mask, ALL_MASK], 2
        )
        self.assertIn(masked_index, mask)
        self.assertNotIn(
            whole_index,
            mask,
            "the index the online values' argmax takes over the whole vocabulary %r is "
            "a member of next_legal=%r, so this mask does not exclude it (rule.md §2, §5)"
            % (whole_index, mask),
        )
        record = transition(
            observation,
            action=1,
            reward=0.0,
            terminal=False,
            next_observation=successor,
            next_legal=mask,
        )

        def figure(path, next_legal):
            """One prefix learner's `td_error` for `record` under one `next_legal`."""
            restored = package.load(None, path)
            return finite_float(
                package.learn(restored, [dict(record, next_legal=next_legal)])[
                    "td_error"
                ],
                "the td_error over next_legal=%r" % (next_legal,),
            )

        by_double = figure(double_path, mask)
        at_masked = figure(control_path, (masked_index,))
        at_excluded = figure(control_path, (whole_index,))
        whole_vocabulary = figure(double_path, ALL_MASK)

        self.assertNotEqual(
            at_masked,
            at_excluded,
            "the masked rule reports one figure at the singleton mask (%r,) and the "
            "other at (%r,), so the index double-Q reads is observable in td_error; "
            "without that the assertions below would hold for either index "
            "(rule.md §2, §3)" % (masked_index, whole_index),
        )
        self.assertEqual(
            by_double,
            at_masked,
            "double-Q's target is not reward + discount × Q_target(s', %r) for the "
            "index %r its online values' tie-break chooses over next_legal=%r: the "
            "masked rule on the singleton mask (%r,) is that expression by definition "
            "(AGT-6.8), and the two reported %r and %r (rule.md §2, §3, §5, "
            "rules.md §2, ASM-25, D-19)"
            % (masked_index, masked_index, mask, masked_index, by_double, at_masked),
        )
        self.assertNotEqual(
            by_double,
            at_excluded,
            "double-Q bootstrapped at index %r, which is outside next_legal=%r: the "
            "index the online argmax takes over the whole vocabulary (0, 1, 2) is never "
            "a candidate, so double-Q must not report the masked rule's singleton "
            "figure for (%r,), and it reported %r against %r (rule.md §2, §3, §5, "
            "rules.md §2, D-2, ASM-25)"
            % (whole_index, mask, whole_index, by_double, at_excluded),
        )
        self.assertEqual(
            whole_vocabulary,
            at_excluded,
            "widened to next_legal=(0, 1, 2), double-Q reported %r, which is not the "
            "masked rule's singleton figure for the whole vocabulary's argmax (%r,): "
            "the mask is what decides the index, so widening it must land there "
            "(rule.md §2, §5, D-2)" % (whole_vocabulary, whole_index),
        )
        self.assertNotEqual(
            whole_vocabulary,
            at_masked,
            "double-Q reports %r over next_legal=%r and %r over the whole vocabulary: "
            "the excluded index %r is not a candidate under the mask, so widening the "
            "mask must move the figure off the masked tie-break's index — a bootstrap "
            "over (0, 1, 2) under the mask would have reported the second figure "
            "(rule.md §2, §5, D-2, ASM-25)"
            % (by_double, mask, whole_vocabulary, whole_index),
        )

    def test_agt6_12_the_terminal_is_not_exempt_and_the_resolved_path_takes_a_steps(self):
        """AGT-6.12 a **terminal** transition carrying a complete resolution takes the same `A` semi-gradient steps a resolved non-terminal one takes — it is not exempt — while a `None` resolution and a partial one each take the **single** ordinary step, and the batch still reports one consumed record and one schedule position (`docs/L3/agents/rule.md` §2-§3, `docs/L1/counterfactual.md` §4, §6, `docs/L1/records.md` §4, D-43).

        The terminal transition is where the outcome is known: the seat's last decision of a
        hand carries the whole-hand value of every legal action and the realised one **equals
        that transition's `reward`**, so `counterfactual.md` §6 takes its `A` steps there
        exactly as at any other transition, and the exemption an earlier reading gave it is
        removed.  That is measured twice, and neither figure is derived: one `learn` call on
        one terminal record with `legal == ALL_MASK` leaves the target copy's **step** counter
        a container records at `A` where the record count is `1`, and it leaves exactly the
        online block a resolved **non-terminal** record of the same observation, the same mask
        and the same resolution leaves (`np.array_equal`, never "nearly") — while the `none`
        learner's single ordinary step on the same record with no `counterfactual` key at all
        lands somewhere else, which is what "not exempt" rules out.

        The two fallbacks that remain are the other case and are measured the same way: a
        transition whose `counterfactual` is `None` carries no resolution at all, and one whose
        sequence is `None` at an index of its own `legal` mask carries only part of one, which
        is not a resolution.  Each takes exactly one step, leaves the step counter at `1`, and
        ends in exactly the state the `none` control ends in on the same record without the key.

        The statistics separate with the step count: `transitions` is the record count, `1`,
        the schedule position advances by the records consumed and never by the steps taken,
        and `td_error` is the batch's mean of the **raw** residual magnitudes over its **steps**
        — here the mean of the `A` residuals, each measured as the `none` learner's own
        one-step figure on a terminal record whose `reward` is that index's value.
        """
        package = self.agents()
        catalogue = tuple(package.learners()["counterfactuals"])
        self.assertGreaterEqual(
            len(catalogue),
            2,
            "the counterfactual catalogue declares the two members this case pairs "
            "(counterfactual.md §6, D-43): %r" % (catalogue,),
        )
        # `none` first and the declared default, and the member that takes its residuals from
        # the record second.  The member's name is read here and never spelled, and `A` is the
        # shape's descriptor count: `ALL_MASK == (0, 1, 2)` on the default shape
        # (`counterfactual.md` §6, §8, D-43).
        self.assertEqual(
            catalogue[0],
            "none",
            "the catalogue's first member is the declared default, `none`, the rule's own "
            "target and one step per transition (counterfactual.md §6, D-43): %r"
            % (catalogue,),
        )
        member = catalogue[1]
        A = len(ALL_MASK)
        folder = self.tempdir()
        read_metadata = declared_internal("checkpoint", "_read_metadata")

        def learner(under=None):
            """One learner of this spec and seed, under `under` or the declared default."""
            extra = {"counterfactual": under} if under is not None else None
            return package.build_learner(
                learner_spec(kind="naive-stack", width=6, depth=1, extra=extra)
            )

        # One container is one zip of `metadata.json` and `parameters.npy`
        # (`checkpoint.md` §2), and the array holds the online block first, so the whole
        # online block is the first `param_count` values it carries (`backends.md` §2).
        total = plain_int(package.param_count(learner()), "param_count(learner)")

        def online(path):
            """One container's whole online parameter block."""
            _metadata, blob = container_document(path)
            return np.load(io.BytesIO(blob), allow_pickle=False)[:total]

        def steps_taken(path):
            """The target copy's consumed-**step** counter one container records.

            `counterfactual.md` §6's other half is a step count and not a record count, and
            the counter `checkpoint.md` §2.1 writes under `target` is where it is observable
            from outside: it advances once per semi-gradient step and is reset by the
            refresh, which no batch here reaches.
            """
            metadata, _blob = container_document(path)
            return plain_int(metadata["target"]["counter"], "metadata['target']['counter']")

        def state(held, record, tag):
            """One fresh learner's whole online block either side of one `learn` call."""
            before = package.save(held, os.path.join(folder, "%s-before.pt" % (tag,)))
            result = package.learn(held, [record])
            after = package.save(held, os.path.join(folder, "%s-after.pt" % (tag,)))
            return online(before), online(after), result, after

        def moved(before, after):
            """The parameter indices one `learn` call moved, exactly and not nearly."""
            return {int(index) for index in np.nonzero(before != after)[0]}

        observation = dense_observation(0.0)

        # The terminal transition, which is **not** exempt.  One terminal record carrying that
        # hand's whole-hand values, one per legal descriptor, with the realised one at action
        # 1: `reward` **is** `RESOLVED_VALUES[1]` (`counterfactual.md` §4, §5, `records.md` §4).
        resolved = transition(
            observation,
            action=1,
            reward=RESOLVED_VALUES[1],
            terminal=True,
            legal=ALL_MASK,
            next_legal=ALL_MASK,
            counterfactual=RESOLVED_VALUES,
        )
        ordinary = dict(resolved)
        del ordinary["counterfactual"]
        member_before, member_after, by_member, member_path = state(
            learner(member), resolved, "terminal-member"
        )
        control_before, control_after, by_control, control_path = state(
            learner(), ordinary, "terminal-none"
        )
        self.assertEqual(
            plain_int(by_member["transitions"], "learn(...)['transitions']"),
            1,
            "a batch of one transition reports one consumed whatever its step count: "
            "`transitions` is the record count and never the step count (rule.md §3, "
            "counterfactual.md §6)",
        )
        self.assertEqual(
            plain_int(by_control["transitions"], "learn(...)['transitions']"),
            1,
            "the `none` control consumed %r records where it was handed one (rule.md §3)"
            % (by_control["transitions"],),
        )
        self.assertTrue(
            np.array_equal(control_before, member_before),
            "the two learners of one spec and one seed did not come out holding one initial "
            "parameter array, so the comparisons below would be two learners' and not one "
            "(architecture.md §4's seeded draw)",
        )
        self.assertEqual(
            steps_taken(member_path),
            A,
            "the member's one **terminal** record carrying a complete resolution over "
            "%r left the target copy's step counter at %r instead of %d: the seat's last "
            "decision of a hand carries the whole-hand value of every legal action and the "
            "realised one equals that transition's `reward`, so the terminal transition is "
            "where the outcome is known and takes `A` steps like any other — it is not "
            "exempt (counterfactual.md §4, §6, rule.md §2-§3, D-43)"
            % (ALL_MASK, steps_taken(member_path), A),
        )
        self.assertEqual(
            steps_taken(control_path),
            1,
            "the `none` control's one record left the step counter at %r instead of one: "
            "under `none` one record is one step (rule.md §3)" % (steps_taken(control_path),),
        )
        self.assertFalse(
            np.array_equal(member_after, control_after),
            "a member learner handed one **terminal** record carrying a complete resolution "
            "ended in exactly the state a `none` learner of the same spec and seed ends in on "
            "the same record with no `counterfactual` key at all — the ordinary path's single "
            "step at the applied action.  A terminal transition's resolution **is** read: the "
            "member takes `A` steps there, one per legal index, on the cache of one forward "
            "pass, and the exemption an earlier reading gave the terminal transition is "
            "removed (counterfactual.md §4, §6, rule.md §2-§3, D-43)",
        )
        moved_at_terminal = moved(member_before, member_after)
        for index in ALL_MASK:
            slot = total - A + index
            self.assertIn(
                slot,
                moved_at_terminal,
                "the output bias of action index %d sits at parameter index `param_count − A "
                "+ i` = %d − %d + %d and the member's terminal step set left it where it "
                "was: the terminal transition takes one step per index of its legal mask and "
                "each writes its own action's bias (rule.md §3, counterfactual.md §6, "
                "backends.md §2)" % (index, total, A, index),
            )

        # The same resolution on a **non-terminal** record: the member reads no successor and
        # no discount at all, so `terminal` cannot separate the two blocks it leaves
        # (`counterfactual.md` §6).  The equality is what makes "the terminal one is not
        # exempt" a measurement rather than a claim about the file's branch.
        open_record = transition(
            observation,
            action=1,
            reward=RESOLVED_VALUES[1],
            terminal=False,
            legal=ALL_MASK,
            next_legal=ALL_MASK,
            counterfactual=RESOLVED_VALUES,
        )
        open_control = dict(open_record)
        del open_control["counterfactual"]
        open_before, open_after, open_result, open_path = state(
            learner(member), open_record, "resolved-member"
        )
        fallback_before, fallback_after, fallback_result, _path = state(
            learner(), open_control, "resolved-none"
        )
        self.assertTrue(
            np.array_equal(fallback_before, open_before),
            "the two learners of one spec and one seed did not come out holding one initial "
            "parameter array, so the inequality below would be two learners' and not one "
            "(architecture.md §4's seeded draw)",
        )
        self.assertEqual(
            plain_int(open_result["transitions"], "learn(...)['transitions']"),
            1,
            "the member's one-transition batch reports one consumed record whatever its step "
            "count (rule.md §3, counterfactual.md §6)",
        )
        self.assertEqual(
            plain_int(fallback_result["transitions"], "learn(...)['transitions']"),
            1,
            "the `none` control consumed %r records where it was handed one (rule.md §3)"
            % (fallback_result["transitions"],),
        )
        self.assertEqual(
            steps_taken(open_path),
            A,
            "the member's one non-terminal transition carrying a complete resolution left the "
            "target copy's step counter at %r instead of %d: `A` steps, one per legal index "
            "(rule.md §3, counterfactual.md §6)" % (steps_taken(open_path), A),
        )
        self.assertTrue(
            np.array_equal(member_after, open_after),
            "the member's one **terminal** record carrying a complete resolution did not end "
            "in the state the same observation, mask and resolution leave on a "
            "**non-terminal** record: the member reads no successor and no discount, so the "
            "terminal transition takes exactly the `A` steps the other one takes and is not "
            "exempt (counterfactual.md §4, §6, rule.md §2-§3, D-43)",
        )
        self.assertFalse(
            np.array_equal(open_after, fallback_after),
            "the member's one non-terminal transition carrying a complete resolution left the "
            "online parameter block where the ordinary path leaves it: its %d steps at %d "
            "distinct residuals cannot write the single step's array, so a member that agrees "
            "with the ordinary path here took that path on a resolved transition (rule.md §3, "
            "counterfactual.md §6, D-43)" % (A, A),
        )

        by_member_moved = moved(open_before, open_after)
        by_fallback_moved = moved(fallback_before, fallback_after)
        applied = open_record["action"]
        for index in ALL_MASK:
            slot = total - A + index
            self.assertIn(
                slot,
                by_member_moved,
                "the output bias of action index %d sits at parameter index `param_count − A "
                "+ i` = %d − %d + %d and the member's step set left it where it was: the "
                "member takes one step per index of its legal mask and each writes its own "
                "action's bias (rule.md §3, counterfactual.md §6, backends.md §2)"
                % (index, total, A, index),
            )
        for index in ALL_MASK:
            slot = total - A + index
            if index == applied:
                self.assertIn(
                    slot,
                    by_fallback_moved,
                    "the ordinary path's one step moved no parameter at %d, the output bias "
                    "of the action %r it applied, and that step writes the applied index's own "
                    "bias (rule.md §3, backends.md §2)" % (slot, applied),
                )
                continue
            self.assertEqual(
                float(fallback_after[slot]),
                float(fallback_before[slot]),
                "the ordinary path's single step moved parameter %d, the output bias of action "
                "index %d, and that step writes no index but the applied %r's: a parameter "
                "whose gradient belongs to another action index is a step the ordinary path "
                "cannot take, and the member's move at %d is exactly what its %d steps buy "
                "(rule.md §3, counterfactual.md §6, backends.md §2)"
                % (slot, index, applied, slot, A),
            )

        # The measured mean.  Each reference is a fresh learner of one spec and one seed, so
        # it holds the same initial parameters; its one terminal transition is the fallback's
        # — the singleton mask `(i,)` and no `counterfactual` key — so it takes exactly one
        # step and reports `|V[i] − q[i]|` (`rule.md` §2-§3).
        references = {}
        for index in ALL_MASK:
            _before, _after, result, _path = state(
                learner(),
                transition(
                    observation,
                    action=index,
                    reward=RESOLVED_VALUES[index],
                    terminal=True,
                    legal=(index,),
                    next_legal=(index,),
                ),
                "reference-%d" % (index,),
            )
            references[index] = finite_float(
                result["td_error"],
                "the one-step fallback's td_error at action index %d" % (index,),
            )
        by_member_error = finite_float(by_member["td_error"], "learn(...)['td_error']")
        by_open_error = finite_float(open_result["td_error"], "learn(...)['td_error']")
        mean_over_steps = sum(references[index] for index in ALL_MASK) / A
        self.assertGreater(
            references[applied],
            0.0,
            "the one-step reference at the applied index %r reported a zero td_error, so the "
            "mean below would be measured over a residual that is zero (rule.md §3)"
            % (applied,),
        )
        for label, figure in (
            ("the terminal record's", by_member_error),
            ("the non-terminal record's", by_open_error),
        ):
            with self.subTest(statistic=label):
                self.assertAlmostEqual(
                    figure,
                    mean_over_steps,
                    places=12,
                    msg="%s member batch reported %r and the mean of its %d raw residual "
                        "magnitudes is %r: a resolved transition takes `A` steps, one per legal "
                        "index — at a terminal transition too — and the batch's statistic is "
                        "its mean over those steps, accumulated **before** the divisor, so the "
                        "member's figure is the mean of %r and not the applied action's alone, "
                        "which is %r (rule.md §3, counterfactual.md §4, §6, D-43)"
                        % (
                            label,
                            figure,
                            A,
                            mean_over_steps,
                            [references[index] for index in ALL_MASK],
                            references[applied],
                        ),
                )
        position = plain_int(
            read_metadata(open_path)["exploration"]["position"], "exploration.position"
        )
        self.assertEqual(
            position,
            1,
            "the member's one-transition batch left the schedule position at %r: the position "
            "advances by the records consumed and never by the steps they took "
            "(counterfactual.md §6, rule.md §3, §4)" % (position,),
        )

        # The two fallbacks: a resolution the record does not carry at all, and one it carries
        # only in part — both on non-terminal records, since a terminal one is no longer a
        # fallback.  Each is the ordinary path, so each must take one step and end in exactly
        # the state the `none` control ends in on the same record without the key — whole-block
        # equality, because both take one step with one delta (`counterfactual.md` §4, §6,
        # D-43).
        def falls_back(record, tag, what):
            """One fallback's whole online block and step count, and the control's."""
            member_before_row, member_after_row, result, member_path_row = state(
                learner(member), record, tag + "-member"
            )
            control_record = dict(record)
            del control_record["counterfactual"]
            control_before_row, control_after_row, _result, _path = state(
                learner(), control_record, tag + "-none"
            )
            self.assertEqual(
                plain_int(result["transitions"], "learn(...)['transitions']"),
                1,
                "a record that is not a complete resolution reports one consumed transition "
                "(rule.md §3, counterfactual.md §6)",
            )
            self.assertEqual(
                steps_taken(member_path_row),
                1,
                "a %s took %r steps where it is not a resolution at all: a transition whose "
                "`counterfactual` is `None` and one whose sequence carries `None` at an index "
                "of its own `legal` mask take the **single** ordinary step, and a fraction of a "
                "step is never taken (counterfactual.md §4, §6, rule.md §2-§3, D-43)"
                % (what, steps_taken(member_path_row)),
            )
            self.assertTrue(
                np.array_equal(control_before_row, member_before_row),
                "the two learners of one spec and one seed did not come out holding one "
                "initial parameter array, so the equality below would be two learners' and "
                "not one (architecture.md §4's seeded draw)",
            )
            self.assertTrue(
                np.array_equal(member_after_row, control_after_row),
                "a %s did not end in exactly the state the ordinary path ends in on the same "
                "record with no `counterfactual` key: a transition whose resolution is `None` "
                "and one whose resolution is partial both fall back to the single ordinary "
                "step — a partial resolution is not a resolution, so no fraction of a step and "
                "no second step is taken (counterfactual.md §4, §6, rule.md §2-§3, D-43)"
                % (what,),
            )

        fallbacks = (
            (
                "unresolved",
                "transition whose `counterfactual` is `None`",
                None,
            ),
            (
                "partial",
                "transition whose sequence carries `None` at an index of its own `legal` mask",
                (RESOLVED_VALUES[0], None, RESOLVED_VALUES[2]),
            ),
        )
        for tag, what, resolution in fallbacks:
            with self.subTest(resolution=tag):
                falls_back(
                    transition(
                        observation,
                        action=1,
                        reward=RESOLVED_VALUES[1],
                        terminal=False,
                        legal=ALL_MASK,
                        next_legal=ALL_MASK,
                        counterfactual=resolution,
                    ),
                    tag,
                    what,
                )

        # A batch of several resolved records: the record count is the transition count and
        # the schedule position, whatever the step count (`counterfactual.md` §6).
        several = [
            transition(
                dense_observation(0.11 * step),
                action=1,
                reward=0.5,
                terminal=False,
                legal=ALL_MASK,
                next_legal=ALL_MASK,
                counterfactual=RESOLVED_VALUES,
            )
            for step in range(5)
        ]
        batch_learner = learner(member)
        batch_result = package.learn(batch_learner, several)
        batch_path = package.save(batch_learner, os.path.join(folder, "several-8127.pt"))
        self.assertEqual(
            plain_int(batch_result["transitions"], "learn(...)['transitions']"),
            len(several),
            "a member batch reports the records it consumed and not the %d steps they took "
            "(rule.md §3, counterfactual.md §6)" % (len(several) * A,),
        )
        batch_position = plain_int(
            read_metadata(batch_path)["exploration"]["position"], "exploration.position"
        )
        self.assertEqual(
            batch_position,
            len(several),
            "the member's batch of %d resolved records left the schedule position at %r: the "
            "position counts transitions and never steps, so it is %d and not %d "
            "(counterfactual.md §6, rule.md §3, §4)"
            % (len(several), batch_position, len(several), len(several) * A),
        )

    def test_agt6_13_the_member_s_step_is_the_raw_residual_over_the_legal_count(self):
        """AGT-6.13 the member's step at one index applies `(V[i] − q[i]) / A`, `A` being **the number of steps that transition takes** — `len(legal)`, and not the shape's descriptor count — so one transition's movement is the mean over its steps (`docs/L3/agents/rule.md` §2-§3, `docs/L1/counterfactual.md` §4, §6, D-43).

        Measured, never derived, at a **zero observation**: `architecture.md` §4's
        initialisation has zero biases and a zero input zeroes every pre-activation, so every
        masked value is exactly `0.0`, the residual at index `i` is `V[i]` itself, and only the
        `A` output **biases** can move — the output weights' gradient is the zero carried
        vector.  The step at index `i` therefore writes `α · V[i] / A` into that index's bias,
        which is the number asserted here **by hand** from `learners()['hyper']`'s declared
        `learning_rate`; the whole residual would write `α · V[i]`, `A` times as far.

        Three clauses make the divisor the transition's own step count and not the shape's.  A
        complete resolution over `ALL_MASK` divides by `A`; the same values over the two-index
        mask `(0, 1)` of a three-descriptor shape divide by **two**, because that transition
        takes two steps — dividing by the shape's three would be a fraction of a step and not
        a mean over the steps taken; and the ordinary path's single step at the same residual,
        taken by a `none` learner on a terminal record whose `reward` is `V[i]`, moves that
        bias exactly `A` times as far as the member's step there, so the divisor is read off
        two learners and not off one.

        The statistic is asserted beside the step, on its own scale: `td_error` is the mean of
        the **raw** residual magnitudes over the steps, so a one-transition batch of `A` steps
        reports `(|V[0]| + |V[1]| + |V[2]|) / A` and not an `A`th of that number — a statistic
        accumulating the **divided** residual would report the mean divided by `A` a second
        time (`counterfactual.md` §6).  The last control proves the case bites: a complete
        resolution of zero values at that same zero observation moves nothing while still
        taking its `A` steps, so a movement there would be a step not driven by the residual
        the same transition reports.
        """
        package = self.agents()
        catalogue = tuple(package.learners()["counterfactuals"])
        self.assertGreaterEqual(
            len(catalogue),
            2,
            "the counterfactual catalogue declares the member this case measures second, after "
            "`none` (counterfactual.md §6, D-43): %r" % (catalogue,),
        )
        self.assertEqual(
            catalogue[0],
            "none",
            "the catalogue's first member is the declared default, `none`, the rule's own "
            "target (counterfactual.md §6, D-43): %r" % (catalogue,),
        )
        member = catalogue[1]
        A = len(ALL_MASK)
        applied = 1
        rate = float(hyper()["learning_rate"])
        folder = self.tempdir()

        def learner(under=None):
            """One learner of this spec and seed, under `under` or the declared default."""
            extra = {"counterfactual": under} if under is not None else None
            return package.build_learner(
                learner_spec(kind="naive-stack", width=6, depth=1, extra=extra)
            )

        # One container is one zip of `metadata.json` and `parameters.npy`
        # (`checkpoint.md` §2), the array holds the online block first, and the output layer's
        # `A` biases are that block's last `A` values, so the bias of action index `i` is
        # `param_count − A + i` (`backends.md` §2).
        total = plain_int(package.param_count(learner()), "param_count(learner)")

        def online(path):
            """One container's whole online parameter block."""
            _metadata, blob = container_document(path)
            return np.load(io.BytesIO(blob), allow_pickle=False)[:total]

        def run(tag, record, under=None):
            """One fresh learner, one `learn`, and its online block either side of that call."""
            held = learner(under)
            before = online(package.save(held, os.path.join(folder, "%s-before.pt" % (tag,))))
            result = package.learn(held, [record])
            after_path = package.save(held, os.path.join(folder, "%s-after.pt" % (tag,)))
            metadata_container, _blob = container_document(after_path)
            return {
                "before": before,
                "after": online(after_path),
                "moved": online(after_path) - before,
                "td_error": finite_float(result["td_error"], "learn(...)['td_error']"),
                "transitions": plain_int(result["transitions"], "learn(...)['transitions']"),
                "steps": plain_int(
                    metadata_container["target"]["counter"], "metadata['target']['counter']"
                ),
            }

        # The zero observation and the rule's own single step on it: a terminal record whose
        # target is the reward alone (`rule.md` §2) applies `α · V[i] · ∂q[i]/∂θ` and reports
        # `|V[i]|`, every masked value being `0.0` (`architecture.md` §4).
        zero, _spec = observation_template("dense-numeric")
        reference = run(
            "none-applied",
            transition(
                zero,
                action=applied,
                reward=RESOLVED_VALUES[applied],
                terminal=True,
                legal=(applied,),
                next_legal=(applied,),
            ),
        )
        self.assertEqual(
            reference["steps"],
            1,
            "the ordinary path's one terminal record left the target copy's step counter at %r "
            "instead of one: under `none` one record is one step (rule.md §3)"
            % (reference["steps"],),
        )
        self.assertGreater(
            reference["td_error"],
            0.0,
            "the ordinary path's one step at index %d reported a zero td_error, so the "
            "residual this case compares is zero and every equality below would decide "
            "nothing (rule.md §3)" % (applied,),
        )
        applied_slot = total - A + applied
        self.assertNotEqual(
            float(reference["moved"][applied_slot]),
            0.0,
            "the ordinary path's step at a zero observation moved the applied index's output "
            "bias by nothing, so the divisor below cannot be read off it (rule.md §3)",
        )

        # A complete resolution over `ALL_MASK`, on the same zero observation: `A` steps, each
        # applying its raw residual over `A`, and nothing but the `A` biases may move.
        whole = run(
            "zero-whole",
            transition(
                zero,
                action=applied,
                reward=RESOLVED_VALUES[applied],
                terminal=False,
                legal=ALL_MASK,
                next_legal=ALL_MASK,
                counterfactual=RESOLVED_VALUES,
            ),
            under=member,
        )
        self.assertEqual(
            whole["transitions"],
            1,
            "the member's one-transition batch reports one consumed record (rule.md §3, "
            "counterfactual.md §6)",
        )
        self.assertEqual(
            whole["steps"],
            A,
            "the member's one resolved transition over %r left the target copy's step counter "
            "at %r instead of %d, one per legal action (rule.md §3, counterfactual.md §6)"
            % (ALL_MASK, whole["steps"], A),
        )
        for index in ALL_MASK:
            with self.subTest(action=index):
                self.assertAlmostEqual(
                    float(whole["moved"][total - A + index]),
                    rate * (RESOLVED_VALUES[index] / A),
                    places=15,
                    msg="the member's step at action index %d moved the output bias at "
                        "parameter %d by %r and the raw residual `V[%d] − q[%d]` = %r over the "
                        "%d steps that transition takes is %r: `θ ← θ + α · ((V[i] − q[i]) / A) "
                        "· ∂q[i]/∂θ`, and the whole residual — with no divisor at all — would "
                        "have written %r (rule.md §2-§3, counterfactual.md §6, D-43)"
                        % (
                            index,
                            total - A + index,
                            float(whole["moved"][total - A + index]),
                            index,
                            index,
                            RESOLVED_VALUES[index],
                            A,
                            rate * (RESOLVED_VALUES[index] / A),
                            rate * RESOLVED_VALUES[index],
                        ),
                )
        self.assertEqual(
            {int(index) for index in np.nonzero(whole["moved"] != 0.0)[0]},
            {total - A + index for index in ALL_MASK},
            "the member's resolved transition moved parameter indices %r: at a zero "
            "observation only the %d output biases the steps write can move, and each of them "
            "must have (rule.md §3, backends.md §2)"
            % (sorted(int(index) for index in np.nonzero(whole["moved"] != 0.0)[0]), A),
        )
        self.assertAlmostEqual(
            float(whole["moved"][applied_slot]) * A,
            float(reference["moved"][applied_slot]),
            places=15,
            msg="the member's step at index %d moved that bias %r and the ordinary path's "
                "single step at the same raw residual moved it %r: the member's step carries "
                "the residual divided by the %d steps the transition takes, so the rule's "
                "move is exactly `A` times the member's — an undivided residual would have "
                "moved both alike (rule.md §3, counterfactual.md §4, §6, D-43)"
                % (
                    applied,
                    float(whole["moved"][applied_slot]),
                    float(reference["moved"][applied_slot]),
                    A,
                ),
        )

        # The two-index mask: two legal actions on a three-descriptor shape take **two** steps,
        # so the divisor is two and not the shape's three (`counterfactual.md` §6).
        pair_legal = (0, 1)
        pair_values = (RESOLVED_VALUES[0], RESOLVED_VALUES[1], None)
        pair = run(
            "zero-pair",
            transition(
                zero,
                action=0,
                reward=RESOLVED_VALUES[0],
                terminal=False,
                legal=pair_legal,
                next_legal=pair_legal,
                counterfactual=pair_values,
            ),
            under=member,
        )
        self.assertEqual(
            pair["steps"],
            len(pair_legal),
            "a transition whose own legal mask is %r left the target copy's step counter at %r "
            "instead of %d: `A` is the number of steps **that transition** takes "
            "(counterfactual.md §6, rule.md §3)" % (pair_legal, pair["steps"], len(pair_legal)),
        )
        for index in pair_legal:
            with self.subTest(legal=pair_legal, action=index):
                self.assertAlmostEqual(
                    float(pair["moved"][total - A + index]),
                    rate * (RESOLVED_VALUES[index] / len(pair_legal)),
                    places=15,
                    msg="the step at action index %d of the two-index mask %r moved that bias "
                        "by %r: that transition takes %d steps, so each applies its raw "
                        "residual over %d and writes %r — dividing by the shape's %d descriptor "
                        "count would write %r, a fraction of a step and not the mean over the "
                        "steps taken (rule.md §3, counterfactual.md §6)"
                        % (
                            index,
                            pair_legal,
                            float(pair["moved"][total - A + index]),
                            len(pair_legal),
                            len(pair_legal),
                            rate * (RESOLVED_VALUES[index] / len(pair_legal)),
                            A,
                            rate * (RESOLVED_VALUES[index] / A),
                        ),
                )
        self.assertEqual(
            float(pair["moved"][total - A + 2]),
            0.0,
            "a step moved the output bias of action index 2, which is outside the transition's "
            "own legal mask %r: a masked action is never valued and never updated (rule.md §2, "
            "counterfactual.md §5)" % (pair_legal,),
        )

        # The statistic keeps the scale of the raw values: the mean of the residual magnitudes
        # over the steps, with the divisor applied to the movement and not to the figure
        # (`counterfactual.md` §6).
        raw_total = sum(abs(value) for value in RESOLVED_VALUES)
        self.assertAlmostEqual(
            whole["td_error"],
            raw_total / A,
            places=15,
            msg="the member reported td_error %r for one transition of %d steps over the raw "
                "residuals %r: the batch's statistic is the mean of their magnitudes, %r, "
                "accumulated **before** the divisor — a curve reading %r would be reading a "
                "statistic that divided the residual a second time "
                "(counterfactual.md §6, rule.md §3)"
                % (
                    whole["td_error"],
                    A,
                    [RESOLVED_VALUES[index] for index in ALL_MASK],
                    raw_total / A,
                    raw_total / A / A,
                ),
        )
        self.assertGreater(
            whole["td_error"],
            raw_total / A / A,
            "the member reported td_error %r for %d steps and the same mean divided by `A` a "
            "second time is %r: the figure a curve reads is the raw residual's own scale "
            "(counterfactual.md §6, rule.md §3)" % (whole["td_error"], A, raw_total / A / A),
        )

        # A complete resolution of zero values is a no-op at that same zero observation: every
        # residual is `0.0 − 0.0`, so each of the member's `A` steps adds nothing — while the
        # steps are still taken and counted (rule.md §3, counterfactual.md §6).
        quiet = run(
            "zero-resolution",
            transition(
                zero,
                action=applied,
                reward=0.0,
                terminal=False,
                legal=ALL_MASK,
                next_legal=ALL_MASK,
                counterfactual=tuple(0.0 for _index in ALL_MASK),
            ),
            under=member,
        )
        self.assertEqual(
            quiet["transitions"],
            1,
            "a resolved transition reports one consumed record whatever its step count "
            "(rule.md §3, counterfactual.md §6)",
        )
        self.assertEqual(
            quiet["steps"],
            A,
            "a resolution of zero values left the target copy's step counter at %r instead of "
            "%d: the steps are taken however little they move (rule.md §3, "
            "counterfactual.md §6)" % (quiet["steps"], A),
        )
        self.assertTrue(
            np.array_equal(quiet["before"], quiet["after"]),
            "one `learn` call on a complete resolution of zero values moved the online "
            "parameters: at a zero observation every masked value is `0.0`, so every residual "
            "is `0.0` and the member's %d steps add nothing — a movement here means the step "
            "is not driven by the residual the same transition reports (rule.md §3, "
            "counterfactual.md §6)" % (A,),
        )


_ABSENT = object()


if __name__ == "__main__":
    unittest.main()
