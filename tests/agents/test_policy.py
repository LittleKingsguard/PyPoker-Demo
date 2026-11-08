"""AGT-8 — `as_policy(learner, encoder, seed)`.

Drives `docs/L2/agents/surface.md` §10, `docs/L3/agents/rule.md` §7 and
`docs/L1/e2e-surface.md` §2: a policy in the protocol sense, one of the
descriptors it was handed, the learner's own seed deciding exactly as `act`
does on a **learned** learner (20 decisions, at least 16 greedy-expected), a
snapshot a later `learn` cannot move, an independent exploration key at another
seed, the `learning_rule` attribute a policy carries and a baseline's policy does
not, and the learner/encoder/seed refusals (ASM-5, D-2, D-19).
"""

import unittest

from _agents_support import (
    BASELINE_SEED,
    LEARNER_SEED,
    OTHER_SEED,
    AgentsCase,
    chosen_index,
    flat_encoder,
    learner_spec,
    taught_batch,
    token_encoder,
)


class PolicyTest(AgentsCase):
    def _learner(self):
        return self.build(kind="naive-stack", width=8, depth=1)

    def test_agt8_1_a_policy_answers_one_of_the_descriptors_it_was_handed(self):
        """AGT-8.1 the policy is callable and returns a descriptor from `legal_actions` (`surface.md` §10, G16, D-2)."""
        package = self.agents()
        policy = package.as_policy(self._learner(), flat_encoder(), LEARNER_SEED)
        self.assertTrue(callable(policy))
        for row in self.decisions(3):
            with self.subTest(hand=row["readout"]["hole"]):
                answer = policy(row["readout"], row["legal"])
                self.assertIn(answer, tuple(row["legal"]))
                self.assertIsNotNone(chosen_index(answer, row["legal"]))

    def test_agt8_2_the_learners_own_seed_decides_as_act(self):
        """AGT-8.2 at the learner's own seed the policy decides exactly as `act` does on a learned learner, over 20 decisions at least 16 of them greedy-expected (`surface.md` §10, `rule.md` §4, §7, ASM-5)."""
        package = self.agents()
        learner = self.annealed_learner(
            "policy-act", {"kind": "naive-stack", "width": 8, "depth": 1}
        )
        policy = package.as_policy(learner, flat_encoder(), LEARNER_SEED)
        rows = self.decisions(20)
        observations, masks = map(list, zip(*self.decision_observations(rows, "naive-stack")))
        self.greedy_arm(LEARNER_SEED, "naive-stack", observations, masks, 16)
        for row in rows:
            with self.subTest(hand=row["readout"]["hole"]):
                answer = policy(row["readout"], row["legal"])
                acted = package.act(learner, row["dense"], row["mask"])["action"]
                self.assertEqual(
                    chosen_index(answer, row["legal"]),
                    acted,
                    "the policy and act disagree on one decision, so they do not "
                    "derive one key and take one tie-break",
                )

    def test_agt8_3_two_policies_from_one_seed_agree(self):
        """AGT-8.3 two policies from one learner, one encoder and one seed answer alike (`surface.md` §10)."""
        package = self.agents()
        learner = self._learner()
        first = package.as_policy(learner, flat_encoder(), LEARNER_SEED)
        second = package.as_policy(learner, flat_encoder(), LEARNER_SEED)
        for row in self.decisions(3):
            with self.subTest(hand=row["readout"]["hole"]):
                self.assertEqual(
                    first(row["readout"], row["legal"]),
                    second(row["readout"], row["legal"]),
                )

    def test_agt8_4_a_policy_is_a_snapshot(self):
        """AGT-8.4 a `learn` after the policy was built does not change its answers, on a learned learner and over 20 decisions (`surface.md` §10, `rule.md` §7, G16, ASM-5)."""
        package = self.agents()
        learner = self.annealed_learner(
            "policy-snapshot", {"kind": "naive-stack", "width": 8, "depth": 1}
        )
        policy = package.as_policy(learner, flat_encoder(), LEARNER_SEED)
        rows = self.decisions(20)
        observations, masks = map(list, zip(*self.decision_observations(rows, "naive-stack")))
        self.greedy_arm(LEARNER_SEED, "naive-stack", observations, masks, 16)
        before = [policy(row["readout"], row["legal"]) for row in rows]
        package.learn(learner, taught_batch("naive-stack", -30.0))
        after = [policy(row["readout"], row["legal"]) for row in rows]
        self.assertEqual(
            before,
            after,
            "a later learn moved a policy already built: the snapshot is not a copy "
            "of the parameters and the position",
        )
        for row, answer in zip(rows, after):
            with self.subTest(hand=row["readout"]["hole"]):
                self.assertIn(answer, tuple(row["legal"]))

    def test_agt8_5_another_seed_answers_legally_and_explores_differently(self):
        """AGT-8.5 another seed answers legally and differs on at least one of several decisions (`surface.md` §10, `rule.md` §4)."""
        package = self.agents()
        learner = self._learner()
        encoder = flat_encoder()
        own = package.as_policy(learner, encoder, LEARNER_SEED)
        other = package.as_policy(learner, encoder, OTHER_SEED)
        differences = 0
        for row in self.decisions(10):
            answer = other(row["readout"], row["legal"])
            self.assertIn(answer, tuple(row["legal"]))
            if answer != own(row["readout"], row["legal"]):
                differences += 1
        self.assertGreater(
            differences,
            0,
            "a policy at another seed answered every decision identically, so "
            "its exploration key is not its own",
        )

    def test_agt8_6_the_refusals(self):
        """AGT-8.6 a non-learner, a non-encoder, a non-integer seed and a contradicting encoder are refused (`surface.md` §10, `errors.md` §3)."""
        package = self.agents()
        learner = self._learner()
        cases = (
            ("a dict as the learner", ({"learner": 1}, flat_encoder(), LEARNER_SEED),
             (("learner",),)),
            ("a dict as the encoder", (learner, {"shape": (203,)}, LEARNER_SEED),
             (("encoder",),)),
            ("a None seed", (learner, flat_encoder(), None), (("seed",), ("none",))),
            ("a string seed", (learner, flat_encoder(), "8127"), (("seed",), ("8127",))),
            ("a float seed", (learner, flat_encoder(), 2.5), (("seed",), ("2.5",))),
            ("a bool seed", (learner, flat_encoder(), True), (("seed",), ("true",))),
            (
                "an encoder contradicting the learner",
                (learner, token_encoder(), LEARNER_SEED),
                (
                    ("encoder",),
                    ("card-tokens", "token-sequence", "96"),
                    ("naive-stack", "dense-numeric", "203"),
                ),
            ),
        )
        for label, args, groups in cases:
            with self.subTest(case=label):
                self.assert_refused(
                    package.as_policy, *args, entry="as_policy", groups=groups, label=label
                )

    def test_agt8_7_the_policy_carries_the_rule_its_learner_was_built_under(self):
        """AGT-8.7 a policy's `learning_rule` is the catalogue member its learner was built under, and a baseline's policy carries none (`surface.md` §10, §12, `rules.md` §7, `e2e-surface.md` §2, D-19).

        `e2e-surface.md` §2 declares the attribute and `surface.md` §10 makes it the
        only thing a policy gains here: it is what `evaluation` reads to label a
        table's members, so a table names the population it measured even when a
        variant was built in process.  It does not move the decision, and a baseline
        policy carries none — no rule trained one (`surface.md` §12, D-6).
        """
        package = self.agents()
        catalogue = tuple(package.learners()["learning_rules"])
        self.assertGreaterEqual(len(catalogue), 2)
        for rule in catalogue:
            with self.subTest(rule=rule):
                learner = package.build_learner(
                    learner_spec(extra={"learning_rule": rule})
                )
                policy = package.as_policy(learner, token_encoder(), LEARNER_SEED)
                carried = getattr(policy, "learning_rule", None)
                self.assertEqual(
                    carried,
                    rule,
                    "a policy carries the catalogue member its learner was built "
                    "under, and this one carries %r (e2e-surface.md §2, "
                    "surface.md §10, D-19)" % (carried,),
                )
                self.assertIn(
                    carried,
                    catalogue,
                    "the attribute names a catalogue member, never a sentence "
                    "(surface.md §3, §10)",
                )
                second = package.as_policy(learner, token_encoder(), LEARNER_SEED)
                self.assertEqual(
                    getattr(second, "learning_rule", None),
                    carried,
                    "two policies from one learner carry the same rule (§10)",
                )
        for name in package.baselines():
            with self.subTest(baseline=name):
                baseline = package.build_baseline(name, BASELINE_SEED)
                self.assertIsNone(
                    getattr(baseline, "learning_rule", None),
                    "a baseline's policy carries no `learning_rule`: no rule trained "
                    "it (surface.md §12, e2e-surface.md §2, D-6)",
                )


if __name__ == "__main__":
    unittest.main()
