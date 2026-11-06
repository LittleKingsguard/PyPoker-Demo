"""The run record's joins -- TRNJ-1, 2, 3, 4, 7 and 8.

A run record is the only thing `training` produces, and six of the battery's eight
joins are its edges (`docs/L1/battery.md` §5):

* TRNJ-1 -- training x engine: the hands a run counts in `timings` are hands the
  engine dealt, at the seeds `seeds._deal_seed` derives, with the engine's own
  terminal chip delta as the reward (`docs/L3/training/seeds.md` §2,
  `docs/L3/training/episode.md` §4, `docs/L2/engine/surface.md` §4, §10);
* TRNJ-2 -- training x features: the encoder a variant names is the encoder the
  run used, and no rung changes what the agent knows (`docs/L2/training/surface.md`
  §4, `docs/L2/features/surface.md` §5, D-3);
* TRNJ-3 -- training x agents: the learning signal is `agents.learn`'s, on the
  batch `episode._transitions` builds, and one seed with two backends is one
  decision boundary (D-7, `docs/L1/ladder.md` §5);
* TRNJ-4 -- training x evaluation: the pool the loop trains against is the pool
  `build_pool` freezes, `pool_members` reads back and `opponent` draws from
  (D-16, ASM-16, `docs/L2/evaluation/surface.md` §5-§8);
* TRNJ-7 -- the report join: a run's record is the record `evaluation.report`
  wants, with the three further keys of `surface.md` §4.1 (`records.md` §13);
* TRNJ-8 -- determinism and the one stream: one `(configuration, seed set,
  budget)` gives one record, and only dealing moves the global `random` stream
  (ASM-2, `docs/L2/training/surface.md` §1, §4).

Every case states the design section whose claim it reads; none asserts a value a
document leaves to the run (`docs/L1/battery.md` §5, D-6).
"""

import importlib.util
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "training_join_support" in sys.modules:
    J = sys.modules["training_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "training_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["training_join_support"] = J
    _spec.loader.exec_module(J)


class EngineJoin(J.JoinCase):
    """TRNJ-1 -- a run's hands are the engine's hands."""

    def test_trnj_1_1_a_runs_timings_count_the_hands_the_engine_played(self):
        """TRNJ-1.1 `timings` counts `budget` hands per variant per seed.

        `docs/L2/training/surface.md` §4 states `budget` as "hands per variant per
        seed", and `docs/L3/training/loop.md` §3-§4 fix `timings[V][str(seed)]` as
        one record per pair carrying `hands`, the wall clock, the seconds per hand
        and the throughput.  A run therefore plays one engine episode for every hand
        it counts, on every variant of the rung (`docs/L1/ladder.md` §6, ASM-8).
        """
        record = J.small_run()
        timing = J.timings_of(record, "naive-numeric", J.RUN_SEED)
        for key in ("hands", "wall_clock_seconds", "seconds_per_hand",
                    "hands_per_second"):
            self.assertIn(
                key,
                timing,
                "a pair's timing carries the four facts `harness.timings` reports "
                "(docs/L3/training/loop.md §4, records.md §12): %r" % (timing,),
            )
        self.assertEqual(
            int(timing["hands"]),
            J.RUN_BUDGET,
            "a run at budget %r plays %r hands per variant per seed, and its record "
            "says so (docs/L2/training/surface.md §4, docs/L3/training/loop.md §3, "
            "ASM-8)" % (J.RUN_BUDGET, J.RUN_BUDGET),
        )
        self.assert_finite(timing["seconds_per_hand"], "the seconds per hand",
                           "docs/L3/training/loop.md §4")
        self.assertGreater(
            float(timing["wall_clock_seconds"]),
            0.0,
            "the wall clock a run measured is positive because it played the hands "
            "(ASM-15, docs/L3/training/loop.md §2)",
        )
        self.assertAlmostEqual(
            float(timing["seconds_per_hand"]) * float(timing["hands_per_second"]),
            1.0,
            places=6,
            msg="the per-hand cost and the throughput are one measurement seen two "
                "ways (docs/L3/training/loop.md §4)",
        )
        pair = J.pair_run()
        for variant in pair["variants"]:
            name = str(variant["name"])
            counted = J.timings_of(pair, name, J.RUN_SEED)
            self.assertEqual(
                int(counted["hands"]),
                J.PAIR_BUDGET,
                "every variant of a pair plays the same %r hands, because the "
                "comparison is matched in samples and not in wall clock "
                "(docs/L1/ladder.md §5, ASM-8): variant %r" % (J.PAIR_BUDGET, name),
            )

    def test_trnj_1_2_the_run_deals_at_the_engine_seeds_its_derivation_names(self):
        """TRNJ-1.2 the run's deals are the engine's seeded deals.

        `docs/L3/training/seeds.md` §2 fixes the derivation: hand *i* of a run at
        seed *s* is dealt at `_deal_seed(s, i)`, a `sha256` function of `(s, i)`
        and of nothing else, and that seed is handed to `engine.play_hand`, which
        deals through `engine.new_hand` -- the project's single seeding point
        (`docs/L2/engine/surface.md` §4, §10, ASM-2).  One seed deals one hand
        however that hand is played, so the first readout of `new_hand(seed)` is
        the first readout of the episode at that seed.
        """
        derived = []
        for index in (0, 1, J.REPLAY_INDEX, J.RUN_BUDGET - 1):
            seed = J.deal_seed(J.RUN_SEED, index)
            self.assertIsInstance(
                seed, int,
                "the deal seed is an integer, the sum of sha256's first eight bytes "
                "big-endian reduced modulo 2**63 (docs/L3/training/seeds.md §2)",
            )
            self.assertGreaterEqual(seed, 0, "a derived deal seed is in [0, 2**63)")
            self.assertLess(seed, 2 ** 63, "a derived deal seed is in [0, 2**63)")
            self.assertNotEqual(
                seed,
                J.opponent_seed(J.RUN_SEED, index),
                "the deal and the opponent are two independent questions about one "
                "hand and carry two domains, so their seeds differ "
                "(docs/L3/training/seeds.md §2)",
            )
            derived.append(seed)
            first = J.readout(J.new_hand(seed))
            second = J.readout(J.new_hand(seed))
            self.assertEqual(
                J.canonical(first),
                J.canonical(second),
                "one seed deals one hand however that hand is played, so the first "
                "readout is stable across two calls (docs/L2/engine/surface.md §4, "
                "§10, ASM-2): hand %r of run seed %r" % (index, J.RUN_SEED),
            )
            episode = J.play_hand(seed, J.caller, J.caller)
            self.assertEqual(
                int(J.episode_seed(episode)),
                seed,
                "the episode the hand is played as records the seed it was dealt at "
                "(records.md §5, docs/L2/engine/surface.md §10)",
            )
            decisions = J.episode_decisions(episode)
            self.assertTrue(
                decisions,
                "an episode record carries the ordered decisions of one hand "
                "(records.md §5)",
            )
            self.assertEqual(
                J.canonical(decisions[0]["readout"]),
                J.canonical(first),
                "the hand the run trains on is the engine's seeded hand: the first "
                "decision of `play_hand` at a seed faces the readout `new_hand` at "
                "that seed declares (docs/L2/engine/surface.md §4, §10)",
            )
        self.assertEqual(
            len(set(derived)),
            len(derived),
            "a derivation of (seed, index) gives distinct seeds for distinct hand "
            "indices, so adjacent hands of one run are unrelated samples "
            "(docs/L3/training/seeds.md §2)",
        )

    def test_trnj_1_3_the_terminal_reward_is_the_engines_chip_delta_unshaped(self):
        """TRNJ-1.3 the terminal reward is the seat's net chip delta, unshaped.

        `docs/L3/training/episode.md` §4: `terminal` is positional -- the last
        transition of the seat's list -- `reward` is `0.0` at every decision but the
        seat's terminal one, and there it is that seat's net chip delta.  The reward
        is read as given from `records.md` §5's episode record, which is what
        `engine.play_hand` returns, and no term is added, clipped or shaped
        (ASM-12, `docs/L2/engine/surface.md` §9-§10).
        """
        episode = J.episode()
        payoffs = J.episode_payoffs(episode)
        self.assertEqual(
            sorted(payoffs),
            [0, 1],
            "the payoffs are net chips per seat and every seat of the hand is named "
            "(docs/L2/engine/surface.md §9, records.md §5)",
        )
        self.assertAlmostEqual(
            sum(payoffs.values()),
            0.0,
            places=9,
            msg="a hand's net chips sum to zero, so an unshaped terminal reward "
                "cannot carry a shaped term (ASM-12, "
                "docs/L2/engine/surface.md §9)",
        )
        checked = 0
        for seat in (0, 1):
            batch = J.transitions(episode, seat, J.flat_encoder())
            if not batch:
                continue  # a hand the seat never acted in files no signal (§3)
            for item in batch:
                for key in ("observation", "next_observation", "action", "reward",
                            "terminal", "legal", "next_legal"):
                    self.assertIn(
                        key,
                        item,
                        "a transition carries the seven keys of records.md §4; the "
                        "batch for seat %r is missing %r" % (seat, key),
                    )
                self.assertIn(
                    item["action"],
                    list(item["legal"]),
                    "a transition's action is one of its own legal indices, so a "
                    "masked update re-derives nothing (records.md §4, "
                    "docs/L3/training/episode.md §3)",
                )
            self.assertEqual(
                [bool(item["terminal"]) for item in batch],
                [False] * (len(batch) - 1) + [True],
                "`terminal` is positional: it marks the last decision the seat made "
                "in the hand and no earlier one (docs/L3/training/episode.md §4)",
            )
            for item in batch[:-1]:
                self.assertEqual(
                    float(item["reward"]),
                    0.0,
                    "every decision but the seat's terminal one rewards nothing, "
                    "because the reward is the hand's outcome and not a per-decision "
                    "term (ASM-12, docs/L3/training/episode.md §4)",
                )
            self.assertEqual(
                float(batch[-1]["reward"]),
                payoffs[seat],
                "the terminal reward is the seat's net chip delta for the completed "
                "hand, read from the episode the engine played and unshaped "
                "(ASM-12, docs/L2/engine/surface.md §9, "
                "docs/L3/training/episode.md §4)",
            )
            checked += 1
        self.assertGreaterEqual(
            checked,
            1,
            "at least one seat of a hand acts, so at least one batch exists to carry "
            "the hand's terminal chip delta (records.md §5, "
            "docs/L3/training/episode.md §3)",
        )

    def test_trnj_1_4_every_td_error_is_finite_and_non_negative(self):
        """TRNJ-1.4 the curve's signal is ten finite, non-negative numbers.

        `docs/L3/training/curves.md` §2-§3: the axis is the ten snapshot points at
        `budget // 10`, and the signal is the mean absolute `td_error` of each
        interval, "plain floats in [0, infty)".  An unshaped chip delta at one
        terminal decision per hand is what makes the signal a magnitude and never a
        signed value (`docs/L2/training/surface.md` §4, ASM-18, ASM-12).
        """
        for record in (J.small_run(), J.window_run(), J.pair_run()):
            budget = int(record["budget"])
            interval = budget // 10
            for declared in record["variants"]:
                self.assertEqual(
                    int(declared["snapshot_every"]),
                    interval,
                    "the interval a run used is `budget // 10` and is recorded in "
                    "the `variants` row, so a 12-hand run writes ten snapshots and "
                    "not the declared 100 (docs/L3/training/loop.md §2-§4, ASM-18)",
                )
            for variant in record["curves"]:
                for seed in record["seeds"]:
                    curve = J.curve_of(record, variant, seed)
                    self.assertEqual(
                        [int(sample) for sample in curve["samples"]],
                        [k * interval for k in range(1, J.SNAPSHOT_POINTS + 1)],
                        "the axis is the ten points at `budget // 10`, strictly "
                        "ascending (docs/L3/training/curves.md §2, ASM-18): "
                        "variant %r, seed %r" % (variant, seed),
                    )
                    self.assertEqual(
                        len(curve["td_error"]),
                        J.SNAPSHOT_POINTS,
                        "the ten snapshot intervals carry one signal each "
                        "(docs/L3/training/curves.md §2-§5)",
                    )
                    for value in curve["td_error"]:
                        magnitude = self.assert_finite(
                            value,
                            "a `td_error` of variant %r at seed %r" % (variant, seed),
                            "docs/L3/training/curves.md §3",
                        )
                        self.assertGreaterEqual(
                            magnitude,
                            0.0,
                            "the signal is a mean absolute TD error, so it is in "
                            "[0, infty); a negative value would be a signed reward "
                            "where ASM-12 shapes nothing "
                            "(docs/L3/training/curves.md §3, ASM-12)",
                        )
                    self.assertEqual(
                        len(curve["spread"]),
                        J.SNAPSHOT_POINTS,
                        "the spread across seeds is recorded at every point "
                        "(docs/L3/training/curves.md §4)",
                    )
                    if len(record["seeds"]) == 1:
                        self.assertEqual(
                            [float(value) for value in curve["spread"]],
                            [0.0] * J.SNAPSHOT_POINTS,
                            "a one-seed run has no spread, recorded as exactly 0.0 "
                            "at every point and not as a missing measurement "
                            "(docs/L3/training/curves.md §4, D-6)",
                        )


class FeaturesJoin(J.JoinCase):
    """TRNJ-2 -- the encoder a variant names is the encoder the run used."""

    def test_trnj_2_1_every_variants_encoding_is_the_encoder_its_kind_consumes(self):
        """TRNJ-2.1 `build_encoder` and `observation_spec` agree with every kind.

        `docs/L3/training/loop.md` §1 step 3 builds `features.build_encoder` for the
        entry's `encoding` and cross-checks it against the entry's
        `architecture.kind` through `features.observation_spec`; the kind's
        declared representation family is `agents.learners()["architectures"]`'s
        (`docs/L2/agents/surface.md` §3).  The dense family is the `(203,)` vector
        and the token families are vocabulary 96, which is what sizes a learner
        (`docs/L2/features/surface.md` §5, ASM-10).
        """
        catalogue = J.learners()["architectures"]
        for name in J.rung_order():
            configuration = J.rung(name)
            for entry in J.variants_of(configuration):
                kind = str(entry["architecture"]["kind"])
                self.assertIn(
                    kind,
                    catalogue,
                    "the kind %r of rung %r is one of learners()'s seven declared "
                    "kinds (docs/L2/agents/surface.md §3, "
                    "docs/L3/training/loop.md §2)" % (kind, name),
                )
                encoder = J.build_encoder(entry["encoding"])
                spec = J.observation_spec(encoder)
                self.assertEqual(
                    str(spec["representation"]),
                    str(entry["encoding"]),
                    "the encoder declares the encoding the variant names "
                    "(docs/L2/features/surface.md §5): rung %r, kind %r"
                    % (name, kind),
                )
                self.assertEqual(
                    str(spec["kind"]),
                    str(catalogue[kind]["observation"]),
                    "the representation family the encoder declares is the family "
                    "its kind consumes (docs/L2/agents/surface.md §3): rung %r, "
                    "encoding %r" % (name, entry["encoding"]),
                )
                if str(spec["kind"]) == "dense-numeric":
                    self.assertEqual(
                        tuple(spec["shape"]),
                        (203,),
                        "the dense encoding is one 203-wide observation, and "
                        "observation_spec is the cross-check that keeps a declared "
                        "size and an observed one equal "
                        "(docs/L2/features/surface.md §5, "
                        "docs/L2/agents/surface.md §3)",
                    )
                    self.assertIsNone(
                        spec["vocabulary"],
                        "the flat encoding carries no token vocabulary "
                        "(docs/L2/features/surface.md §5)",
                    )
                    self.assertEqual(
                        int(catalogue[kind]["observation_size"]),
                        203,
                        "the kind's declared observation size is the width of the "
                        "dense encoding's shape (docs/L2/agents/surface.md §3)",
                    )
                else:
                    self.assertEqual(
                        int(spec["vocabulary"]),
                        96,
                        "a token encoding declares the vocabulary a learner's "
                        "embedding table is sized from "
                        "(docs/L2/features/surface.md §5, ASM-10)",
                    )
                    self.assertEqual(
                        int(catalogue[kind]["observation_size"]),
                        int(spec["vocabulary"]),
                        "the kind's declared observation size is that vocabulary, "
                        "which is the only size a token learner is built for "
                        "(docs/L2/agents/surface.md §3, ASM-10)",
                    )

    def test_trnj_2_2_the_two_encodings_carry_one_set_of_fields(self):
        """TRNJ-2.2 the two encodings' `fields` are identical (D-3).

        `docs/L1/e2e-surface.md` §2 and `docs/L2/features/surface.md` §5: `fields`
        is "identical for every encoding: the ladder never changes what the agent
        may know, only how it is represented".  A rung that added or dropped a fact
        would make a rung-to-rung difference an information difference and not the
        declared axis (D-3, `docs/L1/ladder.md` §4).
        """
        names = sorted({str(entry["encoding"])
                        for name in J.rung_order()
                        for entry in J.variants_of(J.rung(name))})
        self.assertEqual(
            len(names),
            2,
            "the ladder declares two encodings and no third "
            "(docs/L3/training/loop.md) -- the registry names %r" % (names,),
        )
        declared = {}
        for encoding in names:
            spec = J.observation_spec(J.build_encoder(encoding))
            declared[encoding] = tuple(str(field) for field in spec["fields"])
        first, second = names[0], names[1]
        self.assertEqual(
            declared[first],
            declared[second],
            "the two encodings carry the same readout facts in the same order, so "
            "the ladder changes the representation and never the information set "
            "(D-3, docs/L1/e2e-surface.md §2, "
            "docs/L2/features/surface.md §5): %r vs %r"
            % (declared[first], declared[second]),
        )
        self.assertGreater(
            len(declared[first]),
            0,
            "an observation carries the readout facts, so its field list is not "
            "empty (docs/L2/features/surface.md §5)",
        )

    def test_trnj_2_3_the_records_variants_name_the_encoders_the_run_used(self):
        """TRNJ-2.3 the `variants` row is the registry's declaration, verbatim.

        `docs/L3/training/loop.md` §4: `variants[i]` carries `{name, backend,
        encoding, architecture, samples, snapshot_every}` and "`architecture` is the
        entry's record copied verbatim, so the record shows the four settings the
        run was built from".  A reader can therefore rebuild the encoder and the
        learner a run used from the record and the registry together, which is what
        makes the run reproducible from its tuple (`records.md` §2, D-3).
        """
        for record in (J.small_run(), J.pair_run()):
            configuration = J.rung(str(record["rung"]))
            self.assertEqual(
                [str(entry["name"]) for entry in record["variants"]],
                [str(entry["name"]) for entry in J.variants_of(configuration)],
                "the record names the configuration's variants in the registry's "
                "declaration order (docs/L3/training/registry.md §1, "
                "docs/L3/training/loop.md §4)",
            )
            for declared in record["variants"]:
                entry = J.variant_entry(configuration, declared["name"])
                for key in ("name", "backend", "encoding", "architecture",
                            "samples", "snapshot_every"):
                    self.assertIn(
                        key,
                        declared,
                        "a `variants` row carries records.md §2's entry keys "
                        "(docs/L3/training/loop.md §4, records.md §2)",
                    )
                self.assertEqual(
                    str(declared["encoding"]),
                    str(entry["encoding"]),
                    "the record's encoding is the declared encoding of that variant "
                    "(records.md §2, D-3): rung %r, variant %r"
                    % (record["rung"], declared["name"]),
                )
                self.assertEqual(
                    str(declared["backend"]),
                    str(entry["backend"]),
                    "the record's backend is the declared backend of that variant, "
                    "which is D-7's axis on R1-R2 (records.md §2, D-7)",
                )
                self.assertEqual(
                    J.canonical(declared["architecture"]),
                    J.canonical(entry["architecture"]),
                    "`architecture` is the entry's record copied verbatim, so the "
                    "record shows the four settings the run was built from "
                    "(docs/L3/training/loop.md §4)",
                )
                encoder = J.build_encoder(declared["encoding"])
                spec = J.observation_spec(encoder)
                kind = str(declared["architecture"]["kind"])
                self.assertEqual(
                    str(spec["kind"]),
                    str(J.learners()["architectures"][kind]["observation"]),
                    "the encoder the record names consumes the representation family "
                    "its recorded kind declares -- the encoder the run built and the "
                    "architecture it built it for agree "
                    "(docs/L3/training/loop.md §1 step 3, "
                    "docs/L2/agents/surface.md §3)",
                )


class AgentsJoin(J.JoinCase):
    """TRNJ-3 -- the learning signal is `agents.learn`'s."""

    def test_trnj_3_1_learn_returns_a_finite_td_error_on_a_real_hand(self):
        """TRNJ-3.1 `learn` consumes the hand's batch and reports one signal.

        `docs/L3/training/loop.md` §1 step 6: the episode's decisions for the
        learner's own seat, in decision order, become `records.md` §4 transitions
        and go to `agents.learn` as one batch; its `td_error` is the curve's
        learning signal.  The batch is built by `episode._transitions` here, because
        that is the one place the loop builds one (`episode.md` §3, §5), and the
        learner is built exactly as the loop builds it -- the entry's `backend` and
        `architecture`, the run's seed and that encoder (`loop.md` §1 step 3).
        """
        entry = J.variant_entry(J.rung("R1"), "naive-numeric")
        encoder = J.build_encoder(entry["encoding"])
        learner = J.build_learner(J.learner_spec(entry, J.RUN_SEED, encoder))
        batch = J.batch()
        self.assertGreater(
            len(batch),
            0,
            "the battery's episode gives its acting seat at least one decision, so "
            "one batch exists to learn from (docs/L3/training/episode.md §3)",
        )
        statistics = J.learn(learner, batch)
        signal = self.assert_finite(
            J.statistic(statistics, "td_error"),
            "the update's `td_error`",
            "docs/L2/agents/surface.md §7, docs/L3/training/curves.md §3",
        )
        self.assertGreaterEqual(
            signal,
            0.0,
            "`td_error` is the batch's mean absolute TD error, so it is never "
            "negative (docs/L2/agents/surface.md §7)",
        )
        self.assertEqual(
            int(J.statistic(statistics, "transitions")),
            len(batch),
            "`learn` consumes the caller's batch whole, in the caller's order and "
            "neither sampled nor shuffled (docs/L2/agents/surface.md §7, ASM-7)",
        )

    def test_trnj_3_2_one_seed_and_two_backends_are_one_decision_boundary(self):
        """TRNJ-3.2 R1's and R2's arms, at one seed, decide alike.

        D-7 recreates the naive rung in PyTorch "for the speed difference", so the
        two backends may change which library performs the arithmetic and nothing a
        decision reads (`docs/L1/ladder.md` §5).  The registry's own R1 and R2
        entries declare one architecture key for key and differ only in `backend`
        (`docs/L3/training/registry.md` §1), so two learners built from them at one
        seed are one capacity and one decision boundary -- before and after the same
        real batch (`docs/L2/agents/surface.md` §4, §10, ASM-10).
        """
        pair = J.parity_learners()
        self.assertEqual(
            J.canonical(pair["r1_entry"]["architecture"]),
            J.canonical(pair["r2_entry"]["architecture"]),
            "R1 and R2 declare one architecture key for key, so the parity pair "
            "differs on the backend and on nothing else "
            "(docs/L3/training/registry.md §1, D-7)",
        )
        self.assertNotEqual(
            str(pair["r1_entry"]["backend"]),
            str(pair["r2_entry"]["backend"]),
            "the parity pair's declared axis is the backend (D-7, "
            "docs/L1/ladder.md §5)",
        )
        self.assertEqual(
            J.param_count(pair["torch"]),
            J.param_count(pair["numpy"]),
            "one model shape is one parameter count whatever backend counts it "
            "(ASM-10, docs/L2/agents/surface.md §5)",
        )
        batch = J.batch()
        self.assertGreater(len(batch), 0, "the episode gives the seat a batch")
        fresh_numpy = J.decisions(pair["numpy"], batch)
        fresh_torch = J.decisions(pair["torch"], batch)
        self.assertEqual(
            fresh_numpy,
            fresh_torch,
            "at one seed the two backends choose the same index on every decision of "
            "the hand, because the exploration draw is keyed by the seed and the "
            "decision and not by the library (D-7, docs/L2/agents/surface.md §6, "
            "docs/L3/training/seeds.md §4)",
        )
        J.learn(pair["numpy"], batch)
        J.learn(pair["torch"], batch)
        self.assertEqual(
            J.decisions(pair["numpy"], batch),
            J.decisions(pair["torch"], batch),
            "after the same real batch the two arms still decide alike, so the "
            "parity is the update rule's and not the initialisation's "
            "(docs/L2/agents/surface.md §10, docs/L1/ladder.md §5)",
        )

    def test_trnj_3_3_another_seed_decides_differently_and_the_same_seed_again(self):
        """TRNJ-3.3 the learner's seed is a decision input, and one seed is one arm.

        `docs/L3/training/seeds.md` §4 hands `agents.build_learner` the run seed
        itself as the learner's own seed, and `docs/L2/agents/surface.md` §6 keys
        the exploration draw on that seed and the decision -- so another seed is
        another arm and differs somewhere, while one seed built twice is one learner
        in every decision (`docs/L2/agents/surface.md` §4).
        """
        pair = J.parity_learners()
        batch = J.batch()
        self.assertGreater(len(batch), 0, "the episode gives the seat a batch")
        same = J.decisions(pair["numpy"], batch)
        again = J.decisions(pair["same_seed_again"], batch)
        other = J.decisions(pair["other_seed"], batch)
        self.assertEqual(
            same,
            again,
            "two learners from one spec are one learner in capacity and in every "
            "decision, because the initialisation draws from the learner's own "
            "seeded generator and from nothing else "
            "(docs/L2/agents/surface.md §4, ASM-2)",
        )
        self.assertNotEqual(
            same,
            other,
            "a learner built at another seed applies the same rule with an "
            "independent exploration key, so it must answer differently on some "
            "decision of the hand (docs/L2/agents/surface.md §10, D-7, "
            "docs/L3/training/seeds.md §4)",
        )


class EvaluationJoin(J.JoinCase):
    """TRNJ-4 -- the pool the loop trains against is the pool the table measures."""

    def frozen_pool(self):
        """The R2 run's pool declaration and the pool `build_pool` freezes from it.

        A run freezes the declaration before the first hand and reads it back
        (`docs/L3/training/loop.md` §1 step 2), so the declaration is the record's
        own version members, bound and frozen flag -- never a second membership
        (`docs/L2/evaluation/surface.md` §5-§6).
        """
        record = J.window_run()
        pool_record = J.pool_of(record)
        declaration = {
            "members": J.clone(J.version_members(pool_record)),
            "m": pool_record["m"],
            "frozen": pool_record["frozen"],
        }
        return record, pool_record, J.build_pool(declaration)

    def test_trnj_4_1_the_records_pool_is_the_pool_the_table_measures(self):
        """TRNJ-4.1 one declaration, one id, one ordered membership.

        `docs/L2/evaluation/surface.md` §5-§6 and `docs/L1/records.md` §8: one
        declaration yields one ordered member list and one id, the id is a function
        of the ordered member ids and of nothing else, and the three pinned
        baselines come first in `agents.baselines()`'s order.  The record carries
        that read-back id and that membership, which is what lets a table and a run
        be compared by the id alone (D-16, ASM-16,
        `docs/L2/training/surface.md` §3.1).
        """
        record, pool_record, pool = self.frozen_pool()
        back = J.pool_members(pool)
        self.assertEqual(
            J.pool_member_ids(back),
            J.pool_member_ids(pool_record),
            "the membership a run trained against is the membership the league reads "
            "back, in one order (docs/L2/evaluation/surface.md §6, "
            "docs/L1/records.md §8)",
        )
        self.assertEqual(
            str(back["id"]),
            str(pool_record["id"]),
            "`build_pool` over the record's own version members returns the record's "
            "own pool id, because the id is the digest of the ordered membership "
            "and of nothing else (docs/L2/evaluation/surface.md §5, "
            "docs/L1/records.md §8, D-16)",
        )
        self.assertEqual(
            [str(member["id"]) for member in J.baseline_members(back)],
            J.baseline_names(),
            "the three pinned baselines are the first members, in the catalogue's "
            "order (docs/L2/evaluation/surface.md §6, "
            "docs/L1/league.md §2)",
        )
        for member in J.baseline_members(back):
            self.assertTrue(
                member.get("pinned"),
                "a baseline is pinned and never evicted "
                "(docs/L1/league.md §2, ASM-14): %r" % (member,),
            )
            self.assertEqual(
                int(member["params"]),
                0,
                "a baseline's declared capacity is the zero `agents.baselines()` "
                "declares (ASM-10, docs/L2/evaluation/surface.md §6)",
            )
        self.assertEqual(
            int(back["m"]),
            int(pool_record["m"]),
            "`pool_members` reads back the bound the declaration named "
            "(docs/L2/evaluation/surface.md §6, docs/L1/records.md §8)",
        )
        self.assertIs(
            bool(back["frozen"]),
            True,
            "the pool is frozen before the first hand, and the read-back records it "
            "(docs/L3/training/loop.md §1 step 2, ASM-16)",
        )
        self.assertEqual(
            str(pool_record["id"]),
            str(J.pool_declaration_of(J.rung("R2"))["id"]),
            "the record's pool id is the configuration's declared id, which is the "
            "read-back id of the membership the repository carries, so a record "
            "carries one id and not two (docs/L2/training/surface.md §3.1, "
            "docs/L3/training/loop.md §3)",
        )

    def test_trnj_4_2_a_frozen_pool_cannot_be_advanced(self):
        """TRNJ-4.2 `offer` refuses a frozen pool, and the pool is untouched.

        `docs/L2/evaluation/surface.md` §7 refuses a frozen pool "because a frozen
        membership does not change while it is used" (`docs/L1/records.md` §8,
        ASM-16).  The training loop relies on exactly that property: no snapshot of
        a run enters its own pool, and rolling is `offer` between runs
        (`docs/L3/training/loop.md` §1 step 2, `docs/L2/training/surface.md` §1).
        """
        record, pool_record, pool = self.frozen_pool()
        versions = J.version_members(pool_record)
        variant = str(record["variants"][0]["name"])
        newest = str(versions[-1]["id"]) if versions else "training-join-start"
        candidate = {
            "id": "%s/%s/seed-%d/step-%04d" % (record["rung"], variant,
                                               J.RUN_SEED, J.PAIR_BUDGET),
            "path": str(J.checkpoints_of(record, variant, J.RUN_SEED)["final"]),
            "rung": str(record["rung"]),
            "variant": variant,
            "seed": J.RUN_SEED,
            "step": J.PAIR_BUDGET,
            "samples": J.PAIR_BUDGET,
            "lineage": newest,
        }
        before = J.canonical(J.pool_members(pool))
        message = self.assert_refusal(
            "offer",
            [("frozen",)],
            lambda: J.offer(pool, candidate),
            "an offer to a frozen pool",
        )
        self.assertIn(
            "frozen",
            message.lower(),
            "the refusal names the frozen flag it read "
            "(docs/L2/evaluation/surface.md §7, ASM-16): %r" % (message,),
        )
        self.assertEqual(
            J.canonical(J.pool_members(pool)),
            before,
            "a refused offer leaves the pool unchanged, so a caller may keep it "
            "(docs/L2/evaluation/surface.md §7)",
        )

    def test_trnj_4_3_opponent_draws_a_policy_from_that_membership(self):
        """TRNJ-4.3 `opponent(pool, seed)` is the drawn member's own policy.

        `docs/L2/evaluation/surface.md` §8: the draw is the seed reduced modulo the
        membership's size, a baseline is `agents.build_baseline(name, seed)` and a
        version is `policy_from` of its checkpoint beside its member record.  The
        loop hands every hand's opponent seed to exactly this call
        (`docs/L3/training/loop.md` §1 step 4), so the training opposition and the
        table's member are one object (D-16, ASM-16).
        """
        record, pool_record, pool = self.frozen_pool()
        members = list(J.pool_members(pool)["members"])
        self.assertGreaterEqual(
            len(members),
            len(J.baseline_names()),
            "a pool always holds the three baselines "
            "(docs/L1/league.md §2, ASM-14)",
        )
        readouts = [J.readout_at(J.REPLAY_SEED), J.readout_at(J.REPLAY_SEED + 2)]
        for position in range(len(members)):
            seed = position + len(members) * J.DRAW_STEP
            member = members[seed % len(members)]
            drawn = J.opponent(pool, seed)
            self.assertTrue(
                callable(drawn),
                "`opponent` returns a policy in the sense of e2e-surface.md §2 "
                "(docs/L2/evaluation/surface.md §8): position %r" % (position,),
            )
            if J.is_baseline(member):
                reference = J.build_baseline(str(member["id"]), seed)
            else:
                reference = J.policy_from(str(member["path"]))
            for readout_record, legal in readouts:
                descriptor = drawn(readout_record, legal)
                self.assert_descriptor_in(
                    legal, descriptor,
                    "the drawn policy answers one decision of a real readout",
                )
                self.assertEqual(
                    J.descriptor_index(legal, descriptor),
                    J.descriptor_index(legal, reference(readout_record, legal)),
                    "the drawn policy is the member's own: `build_baseline` for a "
                    "baseline and `policy_from` for a version, at the seed the draw "
                    "reduced (docs/L2/evaluation/surface.md §8): member %r at "
                    "position %r" % (member["id"], position),
                )


class ReportJoin(J.JoinCase):
    """TRNJ-7 -- a run's record is the record `evaluation.report` wants."""

    def test_trnj_7_1_the_report_accepts_the_run_record_and_carries_seven_families(self):
        """TRNJ-7.1 a complete record yields a report carrying all seven families.

        `docs/L2/evaluation/surface.md` §13: a report is returned only when every
        family `protocol()` declares is present, and it carries the rung, the
        seeds, the table budget, the table seed and the device beside them
        (`docs/L1/protocol.md` §1-§2).  The record handed in is the one a run
        produced, with only the matrix and the rating attached -- the two families a
        run does not measure (`docs/L2/training/surface.md` §4.1, `records.md` §13,
        D-13).
        """
        record = J.report_record()
        matrix_record, rating_record = J.matrix_and_rating()
        assembled = J.report(str(record["rung"]), record, matrix_record,
                             rating_record)
        declared = J.family_names()
        self.assertEqual(
            len(declared),
            7,
            "the evidence contract declares seven families "
            "(docs/L2/evaluation/surface.md §3, docs/L1/protocol.md §1)",
        )
        for name in declared:
            self.assertIn(
                J.token(name),
                {J.token(key) for key in assembled},
                "the report carries the %r family, so a run's complete record is a "
                "reportable one (docs/L2/evaluation/surface.md §13, "
                "docs/L1/protocol.md §1)" % (name,),
            )
            value = assembled[[key for key in assembled
                               if J.token(key) == J.token(name)][0]]
            self.assertTrue(
                value is not None and (not hasattr(value, "__len__")
                                       or len(value) > 0),
                "no family is reduced to a blank in a report "
                "(docs/L1/protocol.md §1, D-6): family %r" % (name,),
            )
        self.assertEqual(
            str(assembled["rung"]),
            str(record["rung"]),
            "the report carries the rung label it was given "
            "(docs/L2/evaluation/surface.md §13, records.md §12)",
        )
        self.assertEqual(
            tuple(int(seed) for seed in assembled["seeds"]),
            tuple(int(seed) for seed in record["seeds"]),
            "the report carries the seed set the run used, so a third party can "
            "re-run what it describes (docs/L1/protocol.md §2, D-6)",
        )

    def test_trnj_7_2_dropping_curves_is_refused_by_its_own_word(self):
        """TRNJ-7.2 an absent family is refused by name -- `curves` included.

        `docs/L2/evaluation/surface.md` §13 and `docs/L1/protocol.md` §1: an absent
        family is refused "naming it exactly as `protocol()` spells it", and no
        family is invented or filled in.  The run is the only producer of the curves
        family (`docs/L2/training/surface.md` §4.1, D-6), so a record without it is
        the record of a run that did not happen.
        """
        record = J.report_record()
        matrix_record, rating_record = J.matrix_and_rating()
        broken = J.clone(record)
        broken.pop("curves")
        message = self.assert_refusal(
            "report",
            [("curves",)],
            lambda: J.report(str(broken["rung"]), broken, matrix_record,
                             rating_record),
            "a record whose `curves` family is absent",
        )
        self.assertIn(
            "curves",
            message.lower(),
            "the refusal names the missing family `curves` "
            "(docs/L1/protocol.md §1, docs/L2/evaluation/surface.md §13): %r"
            % (message,),
        )

    def test_trnj_7_3_the_run_states_the_three_keys_a_report_needs(self):
        """TRNJ-7.3 `header`, `baselines` and `axis row` are the run's own.

        `docs/L2/training/surface.md` §4.1 (Rev 2): a run states the three further
        families a complete report needs and claims nothing it did not measure --
        the header's nine items from granted calls, the three baselines as declared
        rows with `measured: false`, and an explicit axis row for a one-variant
        rung.  D-5 forbids a notebook importing `engine` or `features`, so the
        header is the only route by which the game and the vocabulary reach a
        report (`docs/L1/protocol.md` §1, `docs/L3/training/loop.md` §6).
        """
        record = J.small_run()
        for key in ("header", "baselines", "axis row"):
            self.assertIn(
                key,
                record,
                "a run states the %r family, which is the only producer of three of "
                "a report's seven (docs/L2/training/surface.md §4.1, Rev 2)" % (key,),
            )
        header = J.header_of(record)
        header_tokens = {J.token(key): str(value) for key, value in header.items()}
        for item in J.header_items():
            wanted = J.token(item)
            matched = [
                key for key in header_tokens
                if wanted == key or wanted in key or key in wanted
            ]
            self.assertTrue(
                matched,
                "the header carries the %r item, one of protocol.md §1's nine "
                "(docs/L2/training/surface.md §4.1): it carries %r"
                % (item, sorted(header_tokens)),
            )
        game_keys = [key for key in header
                     if "game" in J.token(key)]
        self.assertTrue(
            game_keys,
            "the header carries the game item, because D-5 forbids a notebook "
            "importing `engine` and the header is the only route by which the game "
            "reaches a report (docs/L2/training/surface.md §4.1, "
            "docs/L3/training/loop.md §6): it carries %r" % (sorted(header),),
        )
        self.assertEqual(
            J.canonical(header[game_keys[0]]),
            J.canonical(J.game_config()),
            "the header's game is `engine.game_config`'s fixed game, the one game "
            "every rung plays (docs/L2/training/surface.md §4.1, "
            "docs/L2/engine/surface.md §3, D-2)",
        )
        rows = J.baseline_rows(record)
        self.assertEqual(
            len(rows),
            3,
            "the `baselines` family carries the three pinned baselines as declared "
            "rows (docs/L2/training/surface.md §4.1, "
            "docs/L1/protocol.md §3)",
        )
        named = []
        for row in rows:
            record_text = J.canonical(row)
            for name in J.baseline_names():
                if name in record_text:
                    named.append(name)
            self.assertIn(
                "false",
                record_text.lower(),
                "a declared baseline row is `measured: false`, because the rows are "
                "the matrix's to fill and a run plays no cell "
                "(docs/L2/training/surface.md §4.1, D-16): %r" % (row,),
            )
            counted = [value for key, value in row.items()
                       if "hand" in J.token(key) and isinstance(value, int)
                       and not isinstance(value, bool)]
            self.assertTrue(
                counted,
                "a baseline row is declared at the league's cell size, which is what "
                "makes it the same row every league cell is played at "
                "(docs/L2/training/surface.md §4.1, "
                "docs/L2/evaluation/league.md §5): %r" % (row,),
            )
            self.assertEqual(
                int(counted[0]),
                J.live_cell_size(),
                "the declared row is at the league's `live` cell size, the budget a "
                "talk produces (docs/L2/evaluation/league.md §5-§6, ASM-14): %r"
                % (row,),
            )
        self.assertEqual(
            named,
            J.baseline_names(),
            "the three rows are the baselines in the catalogue's order "
            "(docs/L1/protocol.md §3, docs/L2/agents/surface.md §11)",
        )
        self.assertEqual(
            J.axis_row(record),
            "n/a, single variant",
            "a one-variant rung carries the explicit axis row `n/a, single "
            "variant`, never a blank (docs/L1/protocol.md §1, "
            "docs/L2/training/surface.md §4.1, D-6)",
        )


class StreamJoin(J.JoinCase):
    """TRNJ-8 -- determinism and the one global stream (ASM-2)."""

    def test_trnj_8_1_one_tuple_gives_one_record_and_another_seed_another(self):
        """TRNJ-8.1 one `(configuration, seed set, budget)` gives one record.

        `docs/L2/training/surface.md` §4: one tuple gives one record twice -- "the
        same curves, the same pool id and the same checkpoint paths" -- because the
        deal seeds are a function of the run seed and the hand index, the learner's
        generator is seeded from the run seed, and the pool is frozen before the
        first hand (`docs/L3/training/loop.md` §7, `docs/L3/training/seeds.md` §5).
        A different seed gives a different record, and the pool -- which depends on
        the membership and not on the seed -- is unchanged
        (`docs/L1/records.md` §8, FAM-4.8).
        """
        first = J.small_run()
        second = J.repeat_run()
        self.assertEqual(
            J.canonical(first["curves"]),
            J.canonical(second["curves"]),
            "two runs of one (configuration, seed set, budget) give the same curves, "
            "because the hands and the learner's generator are functions of the run "
            "seed (docs/L2/training/surface.md §4, FAM-4.7)",
        )
        self.assertEqual(
            str(first["pool"]["id"]),
            str(second["pool"]["id"]),
            "two runs of one tuple train against one pool id "
            "(docs/L2/training/surface.md §4, D-16)",
        )
        self.assertEqual(
            J.canonical(first["checkpoints"]),
            J.canonical(second["checkpoints"]),
            "two runs of one tuple write the same checkpoint paths, because the "
            "paths are a function of rung, variant, seed and step "
            "(docs/L3/training/checkpoints.md §1-§2, FAM-4.7)",
        )
        other = J.other_seed_run()
        self.assertNotEqual(
            J.canonical(other["curves"]),
            J.canonical(first["curves"]),
            "a different seed gives different curves, because every hand's deal is "
            "derived from the run seed and the hand index and not from `seed + i` "
            "(docs/L2/training/surface.md §4, docs/L3/training/seeds.md §2, "
            "FAM-4.8)",
        )
        self.assertNotEqual(
            tuple(int(seed) for seed in other["seeds"]),
            tuple(int(seed) for seed in first["seeds"]),
            "the record states the seed set the run actually used "
            "(docs/L3/training/loop.md §5, records.md §12)",
        )
        self.assertEqual(
            str(other["pool"]["id"]),
            str(first["pool"]["id"]),
            "the pool id changes when and only when the membership does, so two "
            "seeds of one rung hold one id (docs/L1/records.md §8, ASM-16)",
        )

    def test_trnj_8_2_resolving_comparing_listing_move_no_stream(self):
        """TRNJ-8.2 `rung`, `fairness` and `checkpoints` move no stream.

        `docs/L2/training/surface.md` §1: "The global `random` stream is moved by
        dealing and nothing else ... no call here seeds or advances it".  Resolving
        is not training (§3), `fairness` plays no hand and builds no learner
        (`docs/L3/training/fairness.md` §7), and the index is declared data over
        `checkpoints/` and never a scan (§7, `docs/L3/training/checkpoints.md` §4).
        """
        left = J.rung("R1")
        right = J.rung("R2")
        self.assert_stream_unchanged(lambda: J.rungs(), "training.rungs")
        self.assert_stream_unchanged(lambda: J.rung("R2"), "training.rung")
        self.assert_stream_unchanged(
            lambda: J.fairness(left, right), "training.fairness"
        )
        self.assert_stream_unchanged(
            lambda: J.checkpoints(), "training.checkpoints"
        )
        self.assert_stream_unchanged(lambda: J.devices(), "training.devices")

    def test_trnj_8_3_a_run_leaves_the_stream_where_its_last_deal_left_it(self):
        """TRNJ-8.3 a run moves the stream by dealing and a repeat proves it.

        `docs/L2/training/surface.md` §1 and `docs/L3/training/seeds.md` §1: the
        global stream is moved by dealing and nothing else, every deal goes through
        `engine.new_hand`, and no call here seeds or advances it.  So after a pass
        the stream stands exactly where hand `budget - 1` at the run seed left it --
        and a second run of the same tuple reproduces the first only if nothing
        seeds the stream outside the engine (ASM-2, FAM-4.4).
        """
        shared = J.small_run_stream()
        self.assertNotEqual(
            shared["after"],
            shared["before"],
            "a run deals hands, and dealing is what moves the global `random` "
            "stream (docs/L2/training/surface.md §1, ASM-2)",
        )
        self.assert_stream_at_last_deal(
            shared["after"], J.RUN_SEED, J.RUN_BUDGET - 1,
            "a run of %r hands at seed %r" % (J.RUN_BUDGET, J.RUN_SEED),
        )
        repeated = J.repeat_run_stream()
        self.assertNotEqual(
            repeated["after"],
            repeated["before"],
            "the repeat deals its own hands and moves the stream itself, so the "
            "first run's state is not what the second one inherits "
            "(docs/L2/training/surface.md §1, ASM-2)",
        )
        self.assert_stream_at_last_deal(
            repeated["after"], J.RUN_SEED, J.RUN_BUDGET - 1,
            "the repeat of that run",
        )
        self.assertEqual(
            J.canonical(J.small_run()["curves"]),
            J.canonical(J.repeat_run()["curves"]),
            "a second run at the same seed reproduces the first, which can only hold "
            "if nothing seeds the global stream outside the engine "
            "(docs/L2/training/surface.md §1, docs/L3/training/loop.md §7, ASM-2)",
        )


if __name__ == "__main__":
    unittest.main()
