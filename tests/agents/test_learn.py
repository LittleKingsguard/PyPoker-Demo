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
ASM-25).
"""

import os
import unittest
from collections.abc import Mapping

from _agents_support import (
    ALL_MASK,
    LEARNER_SEED,
    NONEMPTY_MASKS,
    TEACH_REWARD,
    AgentsCase,
    batch,
    declared_internal,
    dense_observation,
    finite_float,
    greedy_expectation,
    learner_spec,
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


_ABSENT = object()


if __name__ == "__main__":
    unittest.main()
