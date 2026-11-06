"""AGT-2 — `learners()`, the declared catalogue.

Drives `docs/L2/agents/surface.md` §3, `docs/L3/agents/README.md` §5,
`docs/L3/agents/architecture.md` §1-§2 and `docs/L3/agents/rule.md` §6: four
keys in order, two backends, one learning rule, seven kinds keyed in the
design's order, `observation_size` cross-checked against `features` rather than
copied, its count read as a count (a NumPy integer is accepted,
`errors.md` §4), and the six fixed hyper-declarations (ASM-7, D-3, D-7).
"""

import operator
import unittest
from collections.abc import Mapping

from _agents_support import (
    DENSE_KIND,
    SEVEN_KINDS,
    TOKEN_KINDS,
    AgentsCase,
    flat_encoder,
    features,
    token_encoder,
)


class LearnersTest(AgentsCase):
    def test_agt2_1_four_keys_in_order(self):
        """AGT-2.1 the record's four keys, in order (`surface.md` §3, `README.md` §5)."""
        record = self.agents().learners()
        self.assertEqual(
            tuple(record),
            ("backends", "architectures", "learning_rule", "hyper"),
            "learners() must carry backends, architectures, learning_rule, hyper in that order",
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

    def test_agt2_3_learning_rule_is_masked_q_learning(self):
        """AGT-2.3 `learning_rule` is exactly `masked-q-learning` (ASM-7, `surface.md` §3)."""
        rule = self.agents().learners()["learning_rule"]
        self.assertIsInstance(rule, str)
        self.assertEqual(rule, "masked-q-learning")

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


if __name__ == "__main__":
    unittest.main()
