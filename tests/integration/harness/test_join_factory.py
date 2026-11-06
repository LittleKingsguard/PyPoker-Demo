"""The factory join -- HRNJ-2.

`docs/L2/harness/surface.md` §4: the factory is "a dispatcher and not a builder".  It
validates nothing about `options`, supplies no default, and returns "exactly the object
that entry point returned, not a copy, not a wrapper and not a second implementation of
it": an `encoder` is one `features.encode` accepts, a `learner` carries the parameter
count `agents.build_learner` gives the same spec and `agents.act` accepts it, a `baseline`
is a policy `engine.play_hand` plays and the owner's `always-call` rule never folds, a
`hand` is one `engine.readout` and `engine.legal_actions` accept, a `rung` configuration is
one `training.fairness` accepts, and a `pool` is one `evaluation.pool_members` reads back
with its id, bound, frozen flag and the three pinned baselines.  A kind the map does not
declare is refused by name, and an owning entry point's refusal arrives unchanged --
same class, same message -- because repairing it would be the harness inventing a second
spelling of another module's contract (`surface.md` §4, `e2e-surface.md` §2, brief §5,
D-13, `docs/L1/battery.md` §5, `docs/L3/harness/support.md` §2).
"""

import importlib.util
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
if "harness_join_support" in sys.modules:
    J = sys.modules["harness_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "harness_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["harness_join_support"] = J
    _spec.loader.exec_module(J)


class FactoryJoin(J.JoinCase):
    """HRNJ-2 -- a factory builds the owning module's own object."""

    def test_hrnj_2_1_the_encoders_object_encodes_a_real_readout(self):
        """HRNJ-2.1 `factory("encoder")` is `features.build_encoder`'s own encoder.

        `features/surface.md` §4: an encoder is the opaque value `observation_spec` and
        `encode` take, and `build_encoder` is the only way to obtain one.  A factory that
        returned a wrapper or a second implementation could not be handed to `encode`, so
        the join is that the object encodes a real readout -- and encodes it to the value
        the owner's own encoder gives (`surface.md` §4, FAM-14.3, FAM-16.34).
        """
        encoder = J.factory("encoder", J.ENCODING)
        record, legal = J.readout_and_legal(J.DEAL_SEED)
        observation = J.encode(encoder, record)
        self.assertIsNotNone(
            observation,
            "an encoder the factory built must be one `features.encode` accepts on a real "
            "`engine.readout` readout -- it is `features.build_encoder`'s own object "
            "(docs/L2/harness/surface.md §4, docs/L2/features/surface.md §6): %r"
            % (observation,),
        )
        direct = J.encode(J.build_encoder(J.ENCODING), record)
        self.assertEqual(
            J.as_plain(J.observation_spec(encoder)),
            J.as_plain(J.observation_spec(J.build_encoder(J.ENCODING))),
            "an encoder built here declares the spec its owner declares for the same "
            "encoding, because it is that owner's object and not a copy "
            "(docs/L2/harness/surface.md §4, docs/L2/features/surface.md §5): %r against %r"
            % (J.observation_spec(encoder), J.observation_spec(J.build_encoder(J.ENCODING))),
        )
        self.assertEqual(
            J.as_plain(observation), J.as_plain(direct),
            "one encoder and one readout give one observation: the factory's encoder "
            "encodes the readout to the value the owner's own encoder gives it "
            "(docs/L2/features/surface.md §6, ASM-2): %r against %r"
            % (J.as_plain(observation)[:4], J.as_plain(direct)[:4]),
        )
        self.assertTrue(
            list(legal),
            "the readout the battery encodes is a decision with at least one legal "
            "descriptor, so the observation is a decision's and not a static fact "
            "(docs/L2/engine/surface.md §6): %r" % (list(legal),),
        )

    def test_hrnj_2_2_the_learners_capacity_is_build_learners_and_it_acts(self):
        """HRNJ-2.2 `factory("learner")` carries `build_learner`'s count and acts.

        `agents/surface.md` §4, §5: a learner is built from `records.md` §3's spec,
        `param_count` measures its capacity (ASM-10) and `act` takes it beside an
        observation and a legal mask.  `surface.md` §4 names the two consequences: "a
        learner built here has the parameter count `agents.build_learner` gives the same
        spec", and it is the object `act` accepts -- and it decides what the owner's
        learner decides on the same observation, or it would not be that object
        (FAM-14.2, FAM-16.34).
        """
        spec = J.learner_spec()
        built = J.factory("learner", spec)
        direct = J.build_learner(spec)
        self.assertEqual(
            J.param_count(built), J.param_count(direct),
            "a learner the factory built carries the parameter count "
            "`agents.build_learner` gives the same spec -- the matched-capacity "
            "measurement of ASM-10 (docs/L2/harness/surface.md §4, "
            "docs/L2/agents/surface.md §5): %r against %r"
            % (J.param_count(built), J.param_count(direct)),
        )
        record, legal = J.readout_and_legal(J.DEAL_SEED_OTHER)
        observation = J.encode(J.shared_encoder(), record)
        mask = J.legal_indices(legal)
        decision = J.act(built, observation, mask)
        index = J.chosen_index(decision)
        self.assertIn(
            index, tuple(mask),
            "`agents.act` accepts the factory's learner beside a real observation and a "
            "real legal mask, and answers with a member of that mask "
            "(docs/L2/harness/surface.md §4, docs/L2/agents/surface.md §6, D-2): %r"
            % (decision,),
        )
        self.assertEqual(
            index, J.chosen_index(J.act(direct, observation, mask)),
            "a learner built here *is* the learner `agents.build_learner` would have "
            "built: at one state and one decision it answers the same index, so the "
            "factory wrapped nothing (docs/L2/harness/surface.md §4, "
            "docs/L2/agents/surface.md §1, §4): %r against %r"
            % (index, J.chosen_index(J.act(direct, observation, mask))),
        )

    def test_hrnj_2_3_the_baseline_plays_a_real_hand_and_never_folds(self):
        """HRNJ-2.3 `factory("baseline")` takes the name and the seed, in that order.

        `agents/surface.md` §12 makes `build_baseline(name, seed)` the one factory kind
        whose owning entry point takes two arguments, so `options` is those two "in the
        entry point's order" (`surface.md` §4).  The battery asserts the order by what the
        owner does with the other one, and asserts the rule the catalogue declares: with
        `always-call` at either seat, `engine.play_hand` plays the hand and no decision of
        that seat folds (`protocol.md` §3, D-6, FAM-14.7).
        """
        name, seed = "always-call", J.BASELINE_SEED
        policy = J.factory("baseline", (name, seed))
        self.assertTrue(
            callable(policy),
            "a baseline the factory built is a policy in the sense of e2e-surface.md §2 "
            "-- a callable taking a readout and a legal set "
            "(docs/L2/agents/surface.md §12, docs/L2/harness/surface.md §4): %r"
            % (policy,),
        )
        self.assert_same_refusal(
            lambda: J.factory("baseline", (seed, name)),
            lambda: J.build_baseline(seed, name),
            "the two options are the name and the seed in the entry point's order, so the "
            "reversed pair is not an option the owner accepts",
            "docs/L2/harness/surface.md §4, docs/L2/agents/surface.md §12",
        )
        catalogue = J.baselines()
        self.assertIn(
            name, catalogue,
            "the baseline's name and its rule are the owner's catalogue, which the pool "
            "and the report both quote (docs/L2/agents/surface.md §11, records.md §9): %r"
            % (sorted(catalogue),),
        )
        rule = str(dict(catalogue[name]).get("rule", ""))
        self.assertIn(
            "never", rule.lower(),
            "the owner's catalogue declares this baseline's rule as never folding, which "
            "is the rule the case holds the factory's policy to "
            "(docs/L1/protocol.md §3, docs/L2/agents/surface.md §11): %r" % (rule,),
        )
        self.assertIn(
            "fold", rule.lower(),
            "the rule the owner declares is about folding, and the case reads it there "
            "rather than restating it (docs/L1/protocol.md §3): %r" % (rule,),
        )
        other = J.build_baseline("random", J.BASELINE_SEED_OTHER)
        for seat in (0, 1):
            opponent = J.build_baseline("random", J.BASELINE_SEED_OTHER + seat)
            policies = (policy, opponent) if seat == 0 else (other, policy)
            episode = J.play_hand(J.DEAL_SEED, policies[0], policies[1])
            self.assert_required_keys(
                episode, J.EPISODE_KEYS, "the episode the factory's baseline played",
                "docs/L1/records.md §5",
            )
            self.assertEqual(
                len(episode["payoffs"]), 2,
                "the engine played the hand against the factory's baseline and reports "
                "one net chip delta per seat (docs/L1/records.md §5, ASM-12): %r"
                % (episode["payoffs"],),
            )
            self.assertEqual(
                sum(float(delta) for delta in episode["payoffs"].values()), 0.0,
                "the episode stays the engine's: its payoffs sum to zero whatever policy "
                "the factory returned (docs/L2/harness/surface.md §5, ASM-12, FAM-14.7): "
                "%r" % (episode["payoffs"],),
            )
            decisions = [decision for decision in episode["decisions"]
                         if J.seat_index(decision["seat"]) == seat]
            self.assertTrue(
                decisions,
                "the hand the engine played gave the factory's baseline at seat %d at "
                "least one decision, so its rule is observable at all "
                "(docs/L1/records.md §5): %r" % (seat, episode["decisions"]),
            )
            for decision in decisions:
                self.assertNotEqual(
                    str(decision["action"]), "fold",
                    "`always-call` never folds in any decision of any hand, and the "
                    "factory's baseline is that owner's policy at seat %d "
                    "(docs/L1/protocol.md §3, docs/L2/agents/surface.md §12, FAM-5): %r"
                    % (seat, decision),
                )
                self.assert_descriptor_in(
                    decision["legal"], decision["action"],
                    "the engine applied what the policy returned, at seat %d" % (seat,),
                    "docs/L1/records.md §5, D-2",
                )
        direct_episode = J.play_hand(
            J.DEAL_SEED, J.build_baseline(name, seed), other
        )
        factory_episode = J.play_hand(J.DEAL_SEED, policy, other)
        self.assertEqual(
            J.canon(factory_episode), J.canon(direct_episode),
            "the episode the factory's baseline plays is the one the owner's own baseline "
            "plays on the same seed against the same opponent, because the factory "
            "returned that object and not a copy of it "
            "(docs/L2/harness/surface.md §4, docs/L2/agents/surface.md §12): %r against %r"
            % (factory_episode["payoffs"], direct_episode["payoffs"]),
        )

    def test_hrnj_2_4_the_hands_readout_and_legal_set_are_the_engines(self):
        """HRNJ-2.4 `factory("hand")` is a deal `engine.readout` accepts.

        `engine/surface.md` §4: `new_hand(seed)` seeds the global `random` with its seed
        and deals the hand, and the same seed deals the same hand.  A hand the factory
        builds is therefore read by `readout` and `legal_actions`, and it is the deal the
        owner makes at that seed -- not a second deal the harness invented
        (`surface.md` §4, ASM-2, FAM-14.1).
        """
        hand = J.factory("hand", J.DEAL_SEED)
        record = J.readout(hand)
        legal = tuple(J.legal_actions(hand))
        self.assertIsInstance(
            record, dict,
            "`engine.readout` accepts the hand the factory dealt "
            "(docs/L2/engine/surface.md §5, docs/L2/harness/surface.md §4): %r" % (record,),
        )
        self.assertTrue(
            legal,
            "`engine.legal_actions` accepts that hand and returns at least one descriptor, "
            "because a non-terminal hand has an acting seat "
            "(docs/L2/engine/surface.md §6): %r" % (legal,),
        )
        self.assertIs(
            J.is_terminal(hand), False,
            "a freshly dealt hand is not terminal, so it is a hand a policy can be called "
            "on (docs/L2/engine/surface.md §8): %r" % (J.is_terminal(hand),),
        )
        self.assertEqual(
            J.canon(record), J.canon(J.readout(J.new_hand(J.DEAL_SEED))),
            "the factory's hand is the deal `engine.new_hand` makes at that seed: one "
            "seed deals one hand, and a hand depends on its seed and not on the hands "
            "dealt before it (docs/L2/engine/surface.md §4, ASM-2, protocol.md §4): %r "
            "against %r" % (record.get("hole"), J.readout(J.new_hand(J.DEAL_SEED)).get("hole")),
        )
        self.assertEqual(
            J.canon(record), J.canon(J.readout(J.factory("hand", J.DEAL_SEED))),
            "two hands the factory deals at one seed are one deal, so a case that deals "
            "through the factory is reproducible from its seed alone "
            "(docs/L2/harness/surface.md §4, ASM-2): %r against %r"
            % (record.get("hole"), J.readout(J.factory("hand", J.DEAL_SEED)).get("hole")),
        )
        self.assertEqual(
            [J.as_plain(descriptor) for descriptor in legal],
            [J.as_plain(descriptor) for descriptor in record.get("legal", ())],
            "the engine's `legal_actions` and the readout's `legal` fact are one set in "
            "one order, so the hand's legality is the engine's (docs/L2/engine/surface.md "
            "§6): %r against %r" % (legal, record.get("legal")),
        )

    def test_hrnj_2_5_the_rung_configuration_is_one_fairness_accepts(self):
        """HRNJ-2.5 `factory("rung")` resolves a configuration `fairness` compares.

        `training/surface.md` §3 resolves one rung name to a configuration, and §5 makes
        `fairness` take two of them and report "what a comparison pair holds constant ...
        and the single axis on which it differs".  The factory's configuration is that
        owner's own resolution -- the case reads every required key of `ladder.md` §3's
        schema back out of it and hands it to `fairness` beside the next rung
        (`surface.md` §4, D-3, FAM-3).
        """
        configuration = J.factory("rung", J.RUNG_NAME)
        self.assert_required_keys(
            configuration, ("name", "axis", "primary", "variants", "pool"),
            "the rung configuration the factory resolved",
            "docs/L2/harness/surface.md §4, docs/L1/records.md §2",
        )
        self.assertEqual(
            J.canon(configuration), J.canon(J.rung(J.RUNG_NAME)),
            "the factory resolves the configuration `training.rung` resolves for that "
            "name: one name, one configuration, and the factory adds nothing of its own "
            "(docs/L2/harness/surface.md §4, docs/L2/training/surface.md §3): %r"
            % (configuration.get("name"),),
        )
        self.assertTrue(
            list(configuration["variants"]),
            "a configuration declares at least one variant entry (records.md §2): %r"
            % (configuration["variants"],),
        )
        successor = J.rung(J.RUNG_NEXT)
        report = J.fairness(configuration, successor)
        self.assert_required_keys(
            report, ("pair", "axis", "constants", "pool"),
            "the record `training.fairness` returns for the factory's configuration",
            "docs/L2/training/surface.md §5",
        )
        self.assertEqual(
            [J.as_plain(name) for name in report["pair"]],
            [J.as_plain(configuration["primary"]), J.as_plain(successor["primary"])],
            "`fairness` accepts the factory's configuration as one side of a pair and "
            "names both primaries, because the primary is the lineage the next rung "
            "inherits (docs/L2/training/surface.md §5, docs/L2/harness/surface.md §4): %r"
            % (report["pair"],),
        )
        self.assertIn(
            "backend", J.token(report["axis"].get("differs")),
            "the pair R1-R2 is the ladder's backend axis (D-7), and `fairness` reports "
            "the one axis the pair differs on, so the configuration the factory built is "
            "the one the registry declares (docs/L2/training/surface.md §5, D-3): %r"
            % (report["axis"],),
        )

    def test_hrnj_2_6_the_pool_reads_back_with_its_id_bound_and_baselines(self):
        """HRNJ-2.6 `factory("pool")` is the pool `pool_members` reads back.

        `evaluation/surface.md` §5: `build_pool(declaration)` returns a pool carrying the
        id `records.md` §8 requires, the bound and the frozen flag, with the three
        baselines pinned.  The declaration is R1's own, as `training.rung` resolves it
        (`training/surface.md` §3), so the join is that the id the *training* side declares
        is the id the *evaluation* side reads back for the pool the factory built
        (`surface.md` §4, ASM-16, records.md §8).
        """
        declaration = J.pool_declaration()
        pool = J.factory("pool", declaration)
        record = J.pool_members(pool)
        self.assert_required_keys(
            record, ("id", "m", "frozen", "members"),
            "the pool record `evaluation.pool_members` reads back from the factory's pool",
            "docs/L1/records.md §8",
        )
        self.assertEqual(
            str(record["id"]), str(declaration["id"]),
            "the declared id is the read-back id: one membership has one id, and a "
            "configuration's declared pool id is the read-back id of that membership "
            "(docs/L2/harness/surface.md §4, docs/L2/training/surface.md §3, "
            "records.md §8): %r against %r" % (record["id"], declaration["id"]),
        )
        self.assertEqual(
            int(record["m"]), int(declaration["m"]),
            "the pool holds to the bound its declaration names "
            "(docs/L1/records.md §8, docs/L2/evaluation/surface.md §5): %r against %r"
            % (record["m"], declaration["m"]),
        )
        self.assertEqual(
            bool(record["frozen"]), bool(declaration["frozen"]),
            "the frozen flag a pool reports is the one it was declared with, which is how "
            "a pair's parity is read (docs/L1/records.md §8, ASM-16): %r against %r"
            % (record["frozen"], declaration["frozen"]),
        )
        ids = J.member_ids(record)
        for name in J.baseline_names():
            self.assertIn(
                name, ids,
                "a pool always holds the three pinned baselines, and the one the factory "
                "built is no exception (docs/L1/records.md §8, docs/L2/evaluation/surface.md "
                "§6, ASM-16): %r" % (record,),
            )
        self.assertEqual(
            sorted(member["id"] for member in record["members"] if J.pinned(member)),
            sorted(J.baseline_names()),
            "the three baselines are the pool's pinned members and nothing else is pinned "
            "(docs/L1/records.md §8, ASM-16): %r" % (record["members"],),
        )
        self.assertEqual(
            J.canon(record), J.canon(J.pool_members(J.build_pool(declaration))),
            "the factory returned `evaluation.build_pool`'s own pool: the record read back "
            "from it is the record read back from the pool the owner builds from the same "
            "declaration (docs/L2/harness/surface.md §4, docs/L2/evaluation/surface.md §6): "
            "%r" % (record["id"],),
        )

    def test_hrnj_2_7_a_kind_the_map_does_not_declare_is_refused_by_name(self):
        """HRNJ-2.7 an undeclared object kind is refused, naming it and the six.

        `docs/L2/harness/surface.md` §4: a `kind` that is not one of the six is refused
        "naming the kind and the six declared -- because a factory that built an
        undeclared object *is* the substitution this module never makes".  The battery
        invents the kind (`battery.md` §4, D-15), so the refusal must name the invented
        value and the six names the map does declare (FAM-14.4, brief §5).
        """
        _klass, message = self.assert_refusal(
            lambda: J.factory(J.UNDECLARED_OBJECT, {"suits": 7}),
            (J.UNDECLARED_OBJECT,),
            "the factory must refuse an object kind the map does not declare",
            "docs/L2/harness/surface.md §4, FAM-14.4",
        )
        for name in J.DECLARED_OBJECTS:
            self.assertIn(
                name, str(message).lower(),
                "the refusal names the six declared kinds, so a caller learns what the map "
                "does build -- %r is missing from %r"
                % (name, message),
            )
        for declared in J.DECLARED_OBJECTS:
            self.assertNotEqual(
                declared, J.UNDECLARED_OBJECT,
                "the invented kind is not a declared one, or the case would be asserting "
                "that the map refuses something it declares "
                "(docs/L1/battery.md §4, D-15): %r" % (J.UNDECLARED_OBJECT,),
            )

    def test_hrnj_2_8_an_owners_refusal_arrives_unchanged(self):
        """HRNJ-2.8 every declared kind surfaces its owner's refusal, unrepaired.

        `docs/L2/harness/surface.md` §4: "a refusal the owning entry point raises",
        surfaced "as it is, named and never repaired", because the owning entry point is
        the authority on its own argument (`e2e-surface.md` §2, D-13).  For each of the
        six kinds the battery hands the factory an option the owner refuses and compares
        class and message with the direct call (`surface.md` §4, §1, FAM-14.4).
        """
        missing_key_spec = {"backend": "numpy",
                            "architecture": {"kind": "naive-stack", "width": J.WIDTH,
                                             "depth": J.DEPTH}}
        bad_declaration = {"members": [], "m": 999, "frozen": True}
        cases = [
            ("encoder", J.UNKNOWN_ENCODING,
             lambda: J.build_encoder(J.UNKNOWN_ENCODING), "an encoding `features` has not"),
            ("learner", missing_key_spec,
             lambda: J.build_learner(missing_key_spec), "a learner spec with no seed"),
            ("baseline", ("join-probe-no-such-baseline", 1),
             lambda: J.build_baseline("join-probe-no-such-baseline", 1),
             "a baseline name the three do not include"),
            ("hand", "join-probe-not-a-seed",
             lambda: J.new_hand("join-probe-not-a-seed"), "a seed that is not an integer"),
            ("rung", "R97", lambda: J.rung("R97"), "a rung name the registry has not"),
            ("pool", bad_declaration,
             lambda: J.build_pool(bad_declaration), "a bound beyond the league's M"),
        ]
        for kind, options, direct, what in cases:
            self.assert_same_refusal(
                lambda kind=kind, options=options: J.factory(kind, options),
                direct,
                "the %r kind with %s must surface the owner's own refusal" % (kind, what),
                "docs/L2/harness/surface.md §4, e2e-surface.md §2, D-13",
            )
        self.assertEqual(
            sorted(kind for kind, _o, _d, _w in cases),
            sorted(J.DECLARED_OBJECTS),
            "the case exercises one refusal for each of the six declared kinds, because "
            "the factory is a dispatch over those six and no seventh "
            "(docs/L2/harness/surface.md §4, D-13): %r" % ([kind for kind, _o, _d, _w in cases],),
        )


if __name__ == "__main__":
    unittest.main()
