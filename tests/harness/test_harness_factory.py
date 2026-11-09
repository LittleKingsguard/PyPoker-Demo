"""HRN-5 — `factory`: a dispatch table, never a builder.

Drives `docs/L3/harness/support.md` §2 and `docs/L2/harness/surface.md` §4: each of the
six declared kinds reaches its owning entry point and returns **that entry point's own
object** — an encoder `features.encode` accepts, a learner with `agents.build_learner`'s
parameter count, a baseline playable by `engine.play_hand`, a handle `engine.readout`
reads, a configuration `training.rung` resolves and a pool `evaluation.pool_members`
reads back — with `baseline`'s two options in the owner's order, no option validated
locally, and every delegated refusal arriving in the owner's own class
(`guardrails.md` G3-G6, FAM-14.2, FAM-14.3, FAM-16.34, FAM-1.46).
"""

import unittest

from _harness_support import (
    BAD_POOL_DECLARATION,
    BASELINE_CALL,
    BASELINE_ORACLE,
    BASELINE_RANDOM,
    ENCODING_DENSE,
    ENCODING_TOKENS,
    LEARNER_SPEC,
    POOL_DECLARATION,
    RUNG_NAME,
    SEED_HAND,
    SEED_OTHER,
    SEED_POLICY,
    HarnessCase,
    agents,
    as_int,
    as_mapping,
    as_number,
    as_sequence,
    as_text,
    engine,
    evaluation,
    features,
    readout,
    same_observation,
    training,
)


class FactoryTest(HarnessCase):
    def build(self, kind, options):
        """`factory(kind, options)` once, through the surface."""
        return self.ep("factory")(kind, options)

    def test_hrn_5_1_encoder_returns_one_features_encode_accepts(self):
        """HRN-5.1 `factory("encoder", name)` returns the encoder `features.build_encoder` returns: `observation_spec` names the encoding and `encode` accepts it on a real readout (support §2, features/surface.md §4, G3, FAM-14.3)."""
        observation = readout()
        for name in (ENCODING_DENSE, ENCODING_TOKENS):
            with self.subTest(encoding=name):
                built = self.build("encoder", name)
                direct = features().build_encoder(name)
                self.assertTrue(
                    same_observation(
                        features().observation_spec(built),
                        features().observation_spec(direct),
                    ),
                    "the encoder built here declares the spec the owner's encoder "
                    "declares (support §2, features/surface.md §4-§5, G3): %r"
                    % (features().observation_spec(built),),
                )
                self.assertEqual(
                    features().observation_spec(built)["representation"],
                    name,
                    "and that spec names the encoding that was asked for (features/"
                    "surface.md §5, FAM-14.3): %r" % (name,),
                )
                self.assertTrue(
                    same_observation(
                        features().encode(built, observation),
                        features().encode(direct, observation),
                    ),
                    "an encoder built here is one features.encode accepts, and it "
                    "encodes one readout to the observation the owner's encoder "
                    "encodes (support §2, FAM-14.3, G3): %r" % (name,),
                )

    def test_hrn_5_2_baseline_spreads_name_and_seed_in_the_owner_s_order(self):
        """HRN-5.2 `factory("baseline", (name, seed))` calls `agents.build_baseline(name, seed)` — the oracle's decisions equal a directly built oracle's, and the policy it returns plays a real `engine.play_hand` (support §2, agents/surface.md §12, G3-G4, FAM-14.7)."""
        hand = engine().new_hand(SEED_HAND)
        observation = engine().readout(hand)
        legal = engine().legal_actions(hand)
        for name in (BASELINE_ORACLE, BASELINE_RANDOM):
            with self.subTest(baseline=name):
                built = self.build("baseline", (name, SEED_POLICY))
                direct = agents().build_baseline(name, SEED_POLICY)
                self.assertTrue(
                    callable(built),
                    "a baseline is a policy in the sense of e2e-surface.md §2 (agents/"
                    "surface.md §12, G3): %r" % (built,),
                )
                chosen = built(observation, legal)
                self.assertEqual(
                    chosen,
                    direct(observation, legal),
                    "the pair is spread in the entry point's order — name first, seed "
                    "second — so the decision is the one a directly built %r makes "
                    "(support §2, G4): %r" % (name, chosen),
                )
                self.assertIn(
                    chosen,
                    list(legal),
                    "a baseline returns one descriptor from the legal set it was "
                    "handed (e2e-surface.md §2, D-2): %r" % (chosen,),
                )
        seat0 = self.build("baseline", (BASELINE_CALL, SEED_POLICY))
        seat1 = self.build("baseline", (BASELINE_RANDOM, SEED_POLICY))
        episode = engine().play_hand(SEED_OTHER, seat0, seat1)
        episode = as_mapping(episode, "the episode a factory-built baseline played")
        decisions = as_sequence(episode["decisions"], "the episode's decisions")
        self.assertTrue(
            len(decisions),
            "a baseline built here is playable: engine.play_hand drove the hand to its "
            "end (agents/surface.md §12, engine/surface.md §10, G3): %r" % (episode,),
        )
        payoffs = as_mapping(episode["payoffs"], "the episode's payoffs")
        self.assertEqual(
            sum(as_number(value, "a seat's net chips") for value in payoffs.values()),
            0,
            "and the episode it played is the engine's, whose payoffs sum to zero "
            "(records.md §5, ASM-12, G3): %r" % (dict(payoffs),),
        )

    def test_hrn_5_3_learner_has_the_parameter_count_the_owner_gives_the_same_spec(self):
        """HRN-5.3 a learner built here has the parameter count `agents.build_learner` gives the same spec, because it is that learner and not a copy (support §2, agents/surface.md §4-§5, G3, FAM-14.2, FAM-16.34)."""
        built = self.build("learner", LEARNER_SPEC)
        direct = agents().build_learner(LEARNER_SPEC)
        built_count = as_int(
            agents().param_count(built), "the built learner's parameter count"
        )
        direct_count = as_int(
            agents().param_count(direct), "the owner's parameter count"
        )
        self.assertEqual(
            built_count,
            direct_count,
            "a learner built here has the parameter count agents.build_learner gives "
            "the same spec (support §2, agents/surface.md §5, FAM-14.2, FAM-16.34): "
            "%r vs %r" % (built_count, direct_count),
        )
        self.assertGreater(
            built_count,
            0,
            "the learner is complete at construction, so it carries a positive count "
            "(agents/surface.md §4, ASM-10): %r" % (built,),
        )

    def test_hrn_5_4_hand_is_a_handle_the_engine_reads(self):
        """HRN-5.4 `factory("hand", seed)` is a real hand handle: `engine.readout` reads it, `engine.is_terminal` refuses it as over, and the same seed deals the same hand as `engine.new_hand` (support §2, engine/surface.md §4-§8, G3, FAM-1.46)."""
        hand = self.build("hand", SEED_HAND)
        self.assertFalse(
            engine().is_terminal(hand),
            "a freshly dealt hand is not terminal (engine/surface.md §8, G3): %r"
            % (hand,),
        )
        observation = as_mapping(engine().readout(hand), "the factory hand's readout")
        self.assertEqual(
            len(observation),
            11,
            "the readout is the mapping of eleven facts engine/surface.md §5 declares — "
            "D-21's `hand_class` included (G3, ASM-30): %r" % (sorted(observation),),
        )
        self.assertTrue(
            len(engine().legal_actions(hand)),
            "and its acting seat has at least one legal descriptor (engine/surface.md "
            "§6, G3): %r" % (engine().legal_actions(hand),),
        )
        self.assertEqual(
            dict(observation),
            dict(engine().readout(engine().new_hand(SEED_HAND))),
            "the same seed deals the same hand, so the factory's handle reads as "
            "engine.new_hand's does (engine/surface.md §4, ASM-2, G3): %r"
            % (dict(observation),),
        )

    def test_hrn_5_5_rung_is_the_configuration_the_registry_resolves(self):
        """HRN-5.5 `factory("rung", name)` is the resolved configuration `training.rung` returns: the name, no `carried_from` for R1, variants and a pool carrying an id (support §2, training/surface.md §3, G3)."""
        configuration = as_mapping(
            self.build("rung", RUNG_NAME), "the rung configuration"
        )
        self.assertEqual(
            dict(configuration),
            dict(training().rung(RUNG_NAME)),
            "a rung built here is the configuration the registry resolves, not a copy "
            "or a re-derivation (support §2, training/surface.md §3, G3): %r"
            % (configuration,),
        )
        self.assertEqual(
            as_text(configuration["name"], "the configuration's name"),
            RUNG_NAME,
            "the configuration names the rung that was asked for (training/surface.md "
            "§3, G3): %r" % (configuration.get("name"),),
        )
        self.assertIsNone(
            configuration["carried_from"],
            "R1 is the first rung, so nothing is carried into it (training/surface.md "
            "§3): %r" % (configuration["carried_from"],),
        )
        variants = as_sequence(configuration["variants"], "the configuration's variants")
        self.assertTrue(
            len(variants),
            "one or two variant entries are resolved (training/surface.md §3, "
            "records.md §2): %r" % (variants,),
        )
        pool = as_mapping(configuration["pool"], "the configuration's pool")
        self.assertTrue(
            as_text(pool["id"], "the pool's id"),
            "a rung's pool carries the id the run record will carry, read back through "
            "evaluation.pool_members (training/surface.md §3, §3.1, G3): %r" % (pool,),
        )

    def test_hrn_5_6_pool_reads_back_through_evaluation_pool_members(self):
        """HRN-5.6 `factory("pool", declaration)` is the pool `evaluation.build_pool` returns: `evaluation.pool_members` reads it back with the declaration's `m`, its frozen flag, the same id and the three pinned baselines (support §2, evaluation/surface.md §5-§6, G3)."""
        pool = self.build("pool", POOL_DECLARATION)
        record = as_mapping(
            evaluation().pool_members(pool), "the pool read back through pool_members"
        )
        direct = as_mapping(
            evaluation().pool_members(evaluation().build_pool(POOL_DECLARATION)),
            "a directly built pool read back",
        )
        self.assertEqual(
            dict(record),
            dict(direct),
            "the factory's pool and the owner's are one pool: the read-back records "
            "agree (support §2, evaluation/surface.md §5-§6, G3): %r vs %r"
            % (dict(record), dict(direct)),
        )
        self.assertEqual(
            record["m"],
            POOL_DECLARATION["m"],
            "the read-back carries the bound the declaration named (records.md §8, "
            "evaluation/surface.md §6): %r" % (record["m"],),
        )
        self.assertEqual(
            record["frozen"],
            POOL_DECLARATION["frozen"],
            "and the frozen flag the declaration named (records.md §8, ASM-16): %r"
            % (record["frozen"],),
        )
        self.assertTrue(
            as_text(record["id"], "the pool's id"),
            "a pool carries the id records.md §8 requires, and it is a function of the "
            "ordered member ids (evaluation/surface.md §5): %r" % (record["id"],),
        )
        members = list(as_sequence(record["members"], "the pool's members"))
        self.assertEqual(
            [member["id"] for member in members[:3]],
            [BASELINE_RANDOM, BASELINE_CALL, BASELINE_ORACLE],
            "the three baselines are pinned first, in agents.baselines()' order "
            "(evaluation/surface.md §6, records.md §8, G3): %r" % (members,),
        )

    def test_hrn_5_7_a_delegated_encoder_refusal_keeps_its_owner_s_class(self):
        """HRN-5.7 `factory("encoder", "no-such-encoding")` raises `features`' own error with the owner's own message, and never a `HarnessError` (support §2, errors §1, errors §4, G6)."""
        direct = self.raised(
            lambda: features().build_encoder("no-such-encoding"),
            "features.build_encoder('no-such-encoding')",
        )
        delegated = self.raised(
            lambda: self.build("encoder", "no-such-encoding"),
            "factory('encoder', 'no-such-encoding')",
        )
        self.assertIs(
            type(delegated),
            type(direct),
            "the catalogue is the owner's, so an unknown encoding arrives in features' "
            "own class and is never re-raised as a harness error (support §2, errors "
            "§1, §4, G6): %s vs %s"
            % (type(delegated).__name__, type(direct).__name__),
        )
        self.assertEqual(
            str(delegated),
            str(direct),
            "and the owner's message arrives verbatim, naming the offending value "
            "(errors §1, §4, G6): %r vs %r" % (str(delegated), str(direct)),
        )
        self.assertNotIsInstance(
            delegated,
            self.refusal_class("HarnessError"),
            "re-wrapping would hide which module owns the catalogue (errors §1, "
            "module-map.md §2, G6): %r" % (delegated,),
        )

    def test_hrn_5_8_every_delegated_refusal_keeps_its_owner_s_class(self):
        """HRN-5.8 the owner's own class and message arrive for an unknown baseline name, an unknown learner backend, an unknown rung name, a bad pool declaration and a non-integer hand seed (support §2, errors §1, §4, G6)."""
        bad_spec = dict(LEARNER_SPEC)
        bad_spec["backend"] = "no-such-backend"
        refusals = (
            (
                "an unknown baseline name",
                "baseline",
                (BASELINE_RANDOM + "-no-such-name", SEED_POLICY),
                lambda options: agents().build_baseline(*options),
            ),
            (
                "an unknown learner backend",
                "learner",
                bad_spec,
                lambda options: agents().build_learner(options),
            ),
            (
                "an unknown rung name",
                "rung",
                "R99",
                lambda options: training().rung(options),
            ),
            (
                "a bad pool declaration",
                "pool",
                BAD_POOL_DECLARATION,
                lambda options: evaluation().build_pool(options),
            ),
            (
                "a non-integer hand seed",
                "hand",
                "not-a-seed",
                lambda options: engine().new_hand(options),
            ),
        )
        for label, kind, options, owner in refusals:
            with self.subTest(refusal=label):
                direct = self.raised(lambda: owner(options), "the owner's own refusal")
                delegated = self.raised(
                    lambda: self.build(kind, options),
                    "factory(%r, ...)" % (kind,),
                )
                self.assertIs(
                    type(delegated),
                    type(direct),
                    "%s must arrive in the owner's class, unmodified (%s; support §2, "
                    "errors §1, G6): %s vs %s"
                    % (label, kind, type(delegated).__name__, type(direct).__name__),
                )
                self.assertEqual(
                    str(delegated),
                    str(direct),
                    "%s must keep the owner's message, which names the value it "
                    "refused (support §2, errors §4, G6): %r vs %r"
                    % (label, str(delegated), str(direct)),
                )

    def test_hrn_5_9_the_factory_validates_no_option_and_supplies_no_default(self):
        """HRN-5.9 a spec missing a required key reaches `agents.build_learner` whole and is refused by the owner, naming the key — the factory pre-checks nothing and substitutes no default (support §2, surface §4, records.md §14, D-13)."""
        incomplete = dict(LEARNER_SPEC)
        del incomplete["seed"]
        direct = self.raised(
            lambda: agents().build_learner(incomplete),
            "agents.build_learner(spec without 'seed')",
        )
        delegated = self.raised(
            lambda: self.build("learner", incomplete),
            "factory('learner', spec without 'seed')",
        )
        self.assertIs(
            type(delegated),
            type(direct),
            "the owning entry point is the authority on what it accepts, so the refusal "
            "is the owner's (support §2, surface §4, G6): %s vs %s"
            % (type(delegated).__name__, type(direct).__name__),
        )
        self.assertIn(
            "seed",
            str(delegated),
            "the owner's refusal names the key that is missing, which shows the options "
            "arrived whole and no default was supplied (support §2, agents/surface.md "
            "§4): %r" % (str(delegated),),
        )
        self.assertNotIsInstance(
            delegated,
            self.refusal_class("HarnessError"),
            "the factory adds no refusal of its own for an argument: only an undeclared "
            "kind is a harness error (support §2, errors §2, G6): %r" % (delegated,),
        )


if __name__ == "__main__":
    unittest.main()
