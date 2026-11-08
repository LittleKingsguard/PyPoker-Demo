"""AGT-2 — `learners()`, the declared catalogue.

Drives `docs/L2/agents/surface.md` §3, `docs/L3/agents/README.md` §5,
`docs/L3/agents/architecture.md` §1-§2, `docs/L3/agents/rule.md` §6 and
`docs/L1/rules.md` §2: four keys in order, two backends, the **rule catalogue**
of two members in the declared order with the target each aims at (D-19), seven
kinds keyed in the design's order, `observation_size` cross-checked against
`features` rather than copied, its count read as a count (a NumPy integer is
accepted, `errors.md` §4), and the six fixed hyper-declarations (ASM-7, D-3,
D-7).  AGT-2.3 replaced a case that asserted the singular `learning_rule` key:
D-19 turned that one constant into `rules.md` §2's catalogue, and the singular
key is gone (`surface.md` §3, `README.md` §5).
"""

import operator
import unittest
from collections.abc import Mapping

from _agents_support import (
    DENSE_KIND,
    LEARNER_SEED,
    SEVEN_KINDS,
    TOKEN_KINDS,
    AgentsCase,
    flat_encoder,
    features,
    learner_spec,
    token_encoder,
)


class LearnersTest(AgentsCase):
    def test_agt2_1_four_keys_in_order(self):
        """AGT-2.1 the record's four keys, in order (`surface.md` §3, `README.md` §5, D-19)."""
        record = self.agents().learners()
        self.assertEqual(
            tuple(record),
            ("backends", "architectures", "learning_rules", "hyper"),
            "learners() must carry backends, architectures, learning_rules, hyper in "
            "that order: D-19 replaced the singular `learning_rule` with the catalogue "
            "`learning_rules` (surface.md §3, rules.md §2)",
        )

    def test_agt2_2_backends_keyed_numpy_then_torch(self):
        """AGT-2.2 `backends` is keyed `numpy` then `torch`, each naming itself (D-7, `surface.md` §3)."""
        backends = self.agents().learners()["backends"]
        self.assertEqual(tuple(backends), ("numpy", "torch"))
        for name, value in backends.items():
            with self.subTest(backend=name):
                self.assertIsInstance(value, Mapping, "each backend value is a plain record")
                self.assertEqual(value.get("name"), name)
                for field, held in value.items():
                    if isinstance(held, str):
                        self.assertEqual(
                            held,
                            name,
                            "the backend record %r holds the prose string %r"
                            % (field, held),
                        )

    def test_agt2_3_learning_rules_is_the_two_member_catalogue(self):
        """AGT-2.3 `learning_rules` is exactly two members in the declared order, each `name` + `target` (`surface.md` §3, `rules.md` §2, D-19).

        The singular `learning_rule` key this case used to read is gone: D-19
        replaced the one module constant with `rules.md` §2's catalogue, and
        `surface.md` §3 makes the order contract — `masked-q-learning` first, the
        declared default of `rules.md` §4, then `double-q-learning`.  Each value is
        a plain record carrying its `name`, equal to its key, and the `target` it
        aims at as a **stable token and never a sentence** — no whitespace, no
        sentence punctuation — because a report quotes the token as a name, and the
        two targets must differ or the two members would aim at one arithmetic.
        """
        catalogue = self.agents().learners()["learning_rules"]
        self.assertIsInstance(catalogue, Mapping, "learning_rules is one plain record")
        self.assertEqual(
            tuple(catalogue),
            ("masked-q-learning", "double-q-learning"),
            "learning_rules is keyed by the two catalogue members in rules.md §2's "
            "order, masked-q-learning first (surface.md §3, D-19)",
        )
        targets = []
        for name, entry in catalogue.items():
            with self.subTest(rule=name):
                self.assertIsInstance(entry, Mapping, "a member is a plain record")
                self.assertEqual(
                    set(entry),
                    {"name", "target"},
                    "a member carries its name and the target it aims at (surface.md §3)",
                )
                self.assertEqual(
                    entry["name"],
                    name,
                    "a catalogue member's `name` is the key it is published under",
                )
                target = entry["target"]
                self.assertIsInstance(
                    target,
                    str,
                    "a member's `target` is a stable token, so it is a string "
                    "(surface.md §3): %r" % (target,),
                )
                self.assertTrue(
                    target.strip(),
                    "a member's `target` is a non-empty token: %r" % (target,),
                )
                self.assertEqual(
                    target,
                    target.strip(),
                    "a member's `target` carries no surrounding whitespace: %r"
                    % (target,),
                )
                forbidden = [
                    character
                    for character in target
                    if character.isspace() or character in ".,;:!?()'\""
                ]
                self.assertEqual(
                    forbidden,
                    [],
                    "the target %r of %r carries %r: surface.md §3 declares a stable "
                    "token and never a sentence" % (target, name, forbidden),
                )
                targets.append(target)
        self.assertEqual(
            len(set(targets)),
            len(targets),
            "the two members aim at different targets, and these are identical: %r "
            "(rules.md §2, D-19)" % (targets,),
        )

    def test_agt2_4_architectures_keyed_in_design_order(self):
        """AGT-2.4 seven architectures in `architecture.md` §1's order, each entry with `name`, `observation`, `observation_size` in order; the size is read as the count it is, so a NumPy integer is accepted (`architecture.md` §1, `surface.md` §3, `errors.md` §4)."""
        architectures = self.agents().learners()["architectures"]
        self.assertEqual(
            tuple(architectures),
            SEVEN_KINDS,
            "the kinds must be the seven of `architecture.md` §1 in that order",
        )
        for kind, entry in architectures.items():
            with self.subTest(kind=kind):
                self.assertEqual(
                    tuple(entry),
                    ("name", "observation", "observation_size"),
                    "a catalogue entry is name, observation, observation_size in that order",
                )
                self.assertEqual(entry["name"], kind)
                size = entry["observation_size"]
                self.assertNotIsInstance(size, bool, "a flag is not a count")
                try:
                    value = operator.index(size)
                except TypeError:
                    self.fail(
                        "the declared `observation_size` of %r is %r (%s), which "
                        "is not an integer count: a numpy integer is accepted "
                        "where a count is expected (errors.md §4)"
                        % (kind, size, type(size).__name__)
                    )
                self.assertGreater(value, 0)

    def test_agt2_5_observation_families_match_the_kind_table(self):
        """AGT-2.5 `naive-stack` is dense-numeric and the six token kinds token-sequence (`architecture.md` §1-§2)."""
        architectures = self.agents().learners()["architectures"]
        self.assertEqual(architectures[DENSE_KIND]["observation"], "dense-numeric")
        for kind in TOKEN_KINDS:
            with self.subTest(kind=kind):
                self.assertEqual(
                    architectures[kind]["observation"],
                    "token-sequence",
                    "kind %r must consume a token-sequence observation" % kind,
                )

    def test_agt2_6_declared_sizes_cross_check_observation_spec(self):
        """AGT-2.6 every declared `observation_size` equals the size `features.observation_spec` declares (D-3, `surface.md` §3)."""
        architectures = self.agents().learners()["architectures"]
        dense_spec = features().observation_spec(flat_encoder())
        token_spec = features().observation_spec(token_encoder())
        self.assertEqual(
            architectures[DENSE_KIND]["observation_size"],
            dense_spec["shape"][0],
            "naive-stack's declared size is not the dense encoding's width",
        )
        self.assertEqual(architectures[DENSE_KIND]["observation"], dense_spec["kind"])
        for kind in TOKEN_KINDS:
            with self.subTest(kind=kind):
                self.assertEqual(
                    architectures[kind]["observation_size"],
                    token_spec["vocabulary"],
                    "kind %r's declared size is not the token encoding's vocabulary" % kind,
                )
                self.assertEqual(architectures[kind]["observation"], token_spec["kind"])

    def test_agt2_7_hyper_carries_the_six_declarations(self):
        """AGT-2.7 `hyper` is the rule's six fixed declarations and the schedule is `{start, end, samples}` (`rule.md` §6)."""
        hyper = self.agents().learners()["hyper"]
        self.assertEqual(
            set(hyper),
            {
                "learning_rate",
                "batch_size",
                "target_update_interval",
                "optimiser",
                "exploration",
                "discount",
            },
        )
        self.assertEqual(hyper["learning_rate"], 0.001)
        self.assertEqual(hyper["batch_size"], 32)
        self.assertEqual(hyper["target_update_interval"], 200)
        self.assertEqual(hyper["optimiser"], "sgd")
        self.assertEqual(hyper["discount"], 0.99)
        schedule = hyper["exploration"]
        self.assertEqual(set(schedule), {"start", "end", "samples"})
        self.assertEqual(schedule["start"], 1.0)
        self.assertEqual(schedule["end"], 0.05)
        self.assertEqual(schedule["samples"], 2000)

    def test_agt2_8_two_calls_return_equal_records(self):
        """AGT-2.8 two calls are equal plain data (`surface.md` §3, `rule.md` §6)."""
        package = self.agents()
        first = package.learners()
        second = package.learners()
        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_agt2_9_the_members_are_the_rules_build_learner_accepts(self):
        """AGT-2.9 each catalogue member builds a learner, and that learner learns under it (`surface.md` §3-§4, §10, `rules.md` §2, §4, D-19).

        §3's catalogue is what a spec selects from and §4 is the selection: a spec
        naming a member builds, and the learner it builds carries that member — read
        through the public attribute `e2e-surface.md` §2 declares for exactly this,
        `as_policy(learner, encoder, seed).learning_rule`, and never through a
        private field.  So the catalogue is neither shorter nor longer than the set
        of rules `build_learner` accepts, one direction here and the other in
        AGT-3.18.
        """
        package = self.agents()
        catalogue = package.learners()["learning_rules"]
        for name in catalogue:
            with self.subTest(rule=name):
                learner = package.build_learner(
                    learner_spec(kind=DENSE_KIND, extra={"learning_rule": name})
                )
                self.assertGreater(
                    package.param_count(learner),
                    0,
                    "a spec naming the catalogue member %r builds a learner "
                    "(surface.md §4, rules.md §2)" % (name,),
                )
                policy = package.as_policy(learner, flat_encoder(), LEARNER_SEED)
                self.assertEqual(
                    getattr(policy, "learning_rule", None),
                    name,
                    "a learner built under the catalogue member %r learns under it, "
                    "and its policy carries that member (e2e-surface.md §2, "
                    "surface.md §10, D-19)" % (name,),
                )


if __name__ == "__main__":
    unittest.main()
