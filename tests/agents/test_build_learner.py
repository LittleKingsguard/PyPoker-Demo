"""AGT-3 — `build_learner(spec)`.

Drives `docs/L2/agents/surface.md` §4, `docs/L3/agents/architecture.md` §3, §5,
§6, `docs/L3/agents/errors.md` §2-§4 and `docs/L1/rules.md` §2, §4: one mapping
in, one learner out; a spec that is not a mapping; the bare kind name needs
`sizes`; the declared backend, kind, seed, settings, encoder and learning rule
are refused with the offending key and value; the optional `learning_rule` builds
the catalogue's first member when absent and the named member when present; an
extra key and an unread setting are accepted; `architecture` beats `sizes`; and
an encoder-less build is sized from the kind's declared `observation_size`
(D-3, D-12, ASM-2, D-19).
"""

import unittest

from _agents_support import (
    DENSE_KIND,
    LEARNER_SEED,
    AgentsCase,
    ALL_MASK,
    dense_observation,
    flat_encoder,
    learner_spec,
    token_encoder,
    token_observation,
)


def architecture(kind="deep", width=6, depth=1, **settings):
    """One invented architecture record for a spec."""
    record = {"kind": kind, "width": width, "depth": depth}
    record.update(settings)
    return record


class BuildLearnerTest(AgentsCase):
    def test_agt3_1_a_full_spec_builds(self):
        """AGT-3.1 a spec with backend, an architecture mapping and a seed builds (`surface.md` §4, `records.md` §3)."""
        package = self.agents()
        learner = package.build_learner(learner_spec())
        self.assertGreater(package.param_count(learner), 0)

    def test_agt3_2_a_bare_kind_name_with_sizes_builds(self):
        """AGT-3.2 a bare kind name plus `sizes` builds the same model as the mapping (`surface.md` §4, D-12)."""
        package = self.agents()
        bare = package.build_learner(
            learner_spec(architecture="deep", sizes={"width": 6, "depth": 1})
        )
        full = package.build_learner(learner_spec())
        self.assertEqual(package.param_count(bare), package.param_count(full))

    def test_agt3_3_a_bare_kind_name_without_sizes_is_refused(self):
        """AGT-3.3 a bare kind name with no `sizes` is refused naming the kind (`surface.md` §4, D-12, `errors.md` §3)."""
        package = self.agents()
        self.assert_refused(
            package.build_learner,
            learner_spec(architecture="wide"),
            entry="build_learner",
            groups=(("wide",), ("sizes",)),
            label="a bare kind name without sizes",
        )

    def test_agt3_4_an_undeclared_backend_is_refused(self):
        """AGT-3.4 a backend `learners()` does not declare is refused naming it (`surface.md` §4, D-7)."""
        package = self.agents()
        self.assert_refused(
            package.build_learner,
            learner_spec(backend="jax"),
            entry="build_learner",
            groups=(("backend",), ("jax",)),
            label="an undeclared backend",
        )

    def test_agt3_5_an_undeclared_kind_is_refused(self):
        """AGT-3.5 a kind `learners()` does not declare is refused naming it (`surface.md` §4, D-3)."""
        package = self.agents()
        self.assert_refused(
            package.build_learner,
            learner_spec(architecture=architecture(kind="naivestack")),
            entry="build_learner",
            groups=(("kind",), ("naivestack",)),
            label="an undeclared kind",
        )

    def test_agt3_6_a_missing_required_key_is_refused(self):
        """AGT-3.6 each missing required key is refused naming that key (`surface.md` §4, `records.md` §3)."""
        package = self.agents()
        for key in ("backend", "architecture", "seed"):
            with self.subTest(missing=key):
                spec = learner_spec()
                del spec[key]
                self.assert_refused(
                    package.build_learner,
                    spec,
                    entry="build_learner",
                    groups=((key,),),
                    label="a spec missing %r" % key,
                )

    def test_agt3_7_a_non_integer_seed_is_refused(self):
        """AGT-3.7 a seed that is a string, a float or a bool is refused naming it (ASM-2, `errors.md` §4)."""
        package = self.agents()
        for seed in ("6174", 2.5, True):
            with self.subTest(seed=seed):
                self.assert_refused(
                    package.build_learner,
                    learner_spec(seed=seed),
                    entry="build_learner",
                    groups=(("seed",), (str(seed),)),
                    label="a %s seed" % type(seed).__name__,
                )

    def test_agt3_8_a_setting_that_is_not_a_positive_integer_is_refused(self):
        """AGT-3.8 a width or depth that is not a positive integer is refused naming it (`architecture.md` §3, `surface.md` §4)."""
        package = self.agents()
        for key in ("width", "depth"):
            for value in (0, -3, 2.5, "12", True):
                with self.subTest(setting=key, value=value):
                    self.assert_refused(
                        package.build_learner,
                        learner_spec(
                            architecture=architecture(**{key: value})
                        ),
                        entry="build_learner",
                        groups=((key,), (str(value),)),
                        label="a %s of %r" % (key, value),
                    )

    def test_agt3_9_a_sparsity_outside_the_unit_interval_is_refused(self):
        """AGT-3.9 `sparsity` outside [0, 1] is refused for a kind that reads it and one that does not (`architecture.md` §3)."""
        package = self.agents()
        for kind in ("sparse", "deep"):
            for value in (1.5, -0.25):
                with self.subTest(kind=kind, sparsity=value):
                    self.assert_refused(
                        package.build_learner,
                        learner_spec(
                            architecture=architecture(kind=kind, sparsity=value)
                        ),
                        entry="build_learner",
                        groups=(("sparsity",), (str(value),)),
                        label="a sparsity of %r on %r" % (value, kind),
                    )

    def test_agt3_10_a_value_that_is_not_an_encoder_is_refused(self):
        """AGT-3.10 a value that is not an encoder is refused naming the key (`surface.md` §4, `learner.md` §6)."""
        package = self.agents()
        self.assert_refused(
            package.build_learner,
            learner_spec(encoder={"shape": (203,)}),
            entry="build_learner",
            groups=(("encoder",),),
            label="a plain dict as the encoder",
        )

    def test_agt3_11_an_encoder_contradicting_the_kind_is_refused_naming_both(self):
        """AGT-3.11 an encoder whose family contradicts the kind is refused naming both sides (`architecture.md` §6, D-3)."""
        package = self.agents()
        cases = (
            (
                architecture(kind=DENSE_KIND),
                token_encoder(),
                (("encoder",), ("card-tokens", "token-sequence", "96"), ("naive-stack", "dense-numeric", "203")),
                "a card-tokens encoder on naive-stack",
            ),
            (
                architecture(kind="deep"),
                flat_encoder(),
                (("encoder",), ("flat-numeric", "dense-numeric", "203"), ("deep", "token-sequence", "96")),
                "a flat-numeric encoder on deep",
            ),
        )
        for arch, encoder, groups, label in cases:
            with self.subTest(case=label):
                self.assert_refused(
                    package.build_learner,
                    learner_spec(architecture=arch, encoder=encoder),
                    entry="build_learner",
                    groups=groups,
                    label=label,
                )

    def test_agt3_12_an_extra_spec_key_is_ignored(self):
        """AGT-3.12 a variant entry's `hyper` and the other extra keys are ignored (`surface.md` §4, `errors.md` §4).

        `learning_rule` left this set when D-19 made it the spec key the learner is
        built under: absent it is the catalogue's first member, and present it is
        read and refused when it names no member (AGT-3.17, AGT-3.18).  The keys
        below are still a run record's data and never a per-learner argument
        (`records.md` §3, `rules.md` §6, D-19).
        """
        package = self.agents()
        extra = {
            "hyper": {"learning_rate": 0.001, "discount": 0.99},
            "param_budget": 10000,
            "samples": 1000,
            "seeds": (0, 1, 2),
            "device": "cpu",
            "name": "invented-variant",
        }
        with_extra = package.build_learner(learner_spec(extra=extra))
        control = package.build_learner(learner_spec())
        self.assertEqual(package.param_count(with_extra), package.param_count(control))

    def test_agt3_13_architecture_wins_over_sizes(self):
        """AGT-3.13 when both are present `architecture` is authoritative, observable in `param_count` (`surface.md` §4, `records.md` §3)."""
        package = self.agents()
        both = package.build_learner(
            learner_spec(
                architecture=architecture(kind="deep", width=6, depth=1),
                sizes={"width": 13, "depth": 2},
            )
        )
        named = package.build_learner(
            learner_spec(architecture=architecture(kind="deep", width=6, depth=1))
        )
        other = package.build_learner(
            learner_spec(architecture=architecture(kind="deep", width=13, depth=2))
        )
        self.assertEqual(package.param_count(both), package.param_count(named))
        self.assertNotEqual(package.param_count(both), package.param_count(other))

    def test_agt3_14_an_encoderless_build_is_sized_from_the_declared_size(self):
        """AGT-3.14 with no encoder the learner is sized from `observation_size`, and `act` accepts that size (`architecture.md` §6)."""
        package = self.agents()
        dense = package.build_learner(
            learner_spec(architecture=architecture(kind=DENSE_KIND))
        )
        record = package.act(dense, dense_observation(), ALL_MASK)
        self.assertIn(record["action"], ALL_MASK)
        self.assert_refused(
            package.act,
            dense,
            dense_observation(width=96),
            ALL_MASK,
            entry="act",
            groups=(("observation",), ("96",), ("203",)),
            label="a dense observation of width 96",
        )

        token = package.build_learner(
            learner_spec(architecture=architecture(kind="deep"))
        )
        record = package.act(token, token_observation(), ALL_MASK)
        self.assertIn(record["action"], ALL_MASK)
        self.assert_refused(
            package.act,
            token,
            token_observation(ids=[3] * 39 + [96]),
            ALL_MASK,
            entry="act",
            groups=(("observation",), ("96",)),
            label="a token observation carrying an id outside the vocabulary",
        )

    def test_agt3_15_a_matching_encoder_builds(self):
        """AGT-3.15 a matching encoder builds, and its size is the size the model is built for (`architecture.md` §6, `learner.md` §6)."""
        package = self.agents()
        with_encoder = package.build_learner(
            learner_spec(architecture=architecture(kind=DENSE_KIND), encoder=flat_encoder())
        )
        without = package.build_learner(
            learner_spec(architecture=architecture(kind=DENSE_KIND))
        )
        self.assertEqual(package.param_count(with_encoder), package.param_count(without))

        token_with = package.build_learner(
            learner_spec(architecture=architecture(kind="deep"), encoder=token_encoder())
        )
        token_without = package.build_learner(
            learner_spec(architecture=architecture(kind="deep"))
        )
        self.assertEqual(package.param_count(token_with), package.param_count(token_without))


    def test_agt3_16_a_spec_that_is_not_a_mapping_is_refused(self):
        """AGT-3.16 a spec that is not a mapping (`None`, a list, a string) is refused naming that a mapping is required (`surface.md` §4, `errors.md` §2-§3, G14)."""
        package = self.agents()
        for label, spec in (
            ("None", None),
            ("a list", []),
            ("a string", "deep"),
            ("a tuple", ("numpy",)),
        ):
            with self.subTest(spec=label):
                self.assert_refused(
                    package.build_learner,
                    spec,
                    entry="build_learner",
                    groups=(("mapping",),),
                    label="a spec that is %s" % label,
                )

    def test_agt3_17_the_rule_is_the_declared_default_or_the_named_member(self):
        """AGT-3.17 no `learning_rule` builds the catalogue's first member, a named one builds that member (`surface.md` §4, `rules.md` §2, §4, D-19).

        The observation is `as_policy(learner, encoder, seed).learning_rule`, the
        attribute `e2e-surface.md` §2 declares and `surface.md` §10 makes public, so
        nothing here reads a private field of the learner.  Absent, the rule is
        `learning_rules`'s first key and never inferred from the caller's silence;
        present, it is the member the spec names.
        """
        package = self.agents()
        catalogue = tuple(package.learners()["learning_rules"])
        self.assertGreaterEqual(len(catalogue), 2, "the catalogue carries two members")
        first, second = catalogue[0], "double-q-learning"
        self.assertIn(second, catalogue, "the declared second member is in the catalogue")

        def rule_of(learner):
            policy = package.as_policy(learner, flat_encoder(), LEARNER_SEED)
            return getattr(policy, "learning_rule", None)

        default = package.build_learner(learner_spec(kind=DENSE_KIND))
        self.assertEqual(
            rule_of(default),
            first,
            "a spec naming no `learning_rule` is built under the catalogue's first "
            "member, %r, the declared default (surface.md §4, rules.md §4)"
            % (first,),
        )
        explicit = package.build_learner(
            learner_spec(kind=DENSE_KIND, extra={"learning_rule": second})
        )
        self.assertEqual(
            rule_of(explicit),
            second,
            "a spec naming %r builds a learner that learns under it (surface.md §4, "
            "rules.md §2)" % (second,),
        )
        self.assertEqual(package.param_count(default), package.param_count(explicit))

    def test_agt3_18_an_uncarried_learning_rule_is_refused(self):
        """AGT-3.18 a name the catalogue does not carry, and a value that is not a string, are refused naming the key and the value (`surface.md` §4, `rules.md` §2, `errors.md` §3-§4, D-19).

        §4 refuses a `learning_rule` §3 does not carry — a non-string and an
        uncarried name alike — and the message names the entry point, the key, the
        offending value and the catalogue's two names, so a caller reads which
        values exist.  The refusal is this module's own (`errors.md` §2): a caller
        catching `AgentsError` catches it, which a `KeyError` from a mistyped
        catalogue would escape.
        """
        package = self.agents()
        catalogue = tuple(package.learners()["learning_rules"])
        cases = (
            ("a name outside the catalogue", "monte-carlo"),
            ("another name outside the catalogue", "sarsa"),
            ("an integer", 7),
            ("a float", 2.5),
            ("None", None),
            ("a bool", True),
        )
        for label, value in cases:
            with self.subTest(case=label):
                self.assert_agents_refusal(
                    package.build_learner,
                    learner_spec(kind=DENSE_KIND, extra={"learning_rule": value}),
                    entry="build_learner",
                    groups=(
                        ("learning_rule",),
                        (str(value),),
                        (catalogue[0],),
                        (catalogue[1],),
                    ),
                    label="%s: learning_rule = %r" % (label, value),
                )


if __name__ == "__main__":
    unittest.main()
