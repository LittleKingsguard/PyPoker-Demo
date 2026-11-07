"""TRN-2 — the one loop: `run(rung, seeds=None, budget=None, device=None)`.

Drives `docs/L3/training/loop.md` §1-§7, `docs/L2/training/surface.md` §4 (Rev 2, §4.1's
three further keys included) and `docs/L1/records.md` §12: the record's keys, the curve
shape at `budget // 10`, the declared parameter band, the four timing key names, the
`variants` block carrying the interval the run *used*, the one pool id a two-variant
record carries, the defaults of §5, and the record of a configuration that is in no
registry.

The battery's budgets are 10 and 60 hands, so `budget // 10` is 1 and 6 and the ten
points are observable at both (`loop.md` §2, `curves.md` §2). Every run is cached in
`_training_support` and handed to the cases that read it, because a `torch` build costs
a second and a 60-hand `numpy` run about five.
"""

import os
import unittest

from _training_support import (
    CHECKPOINT_ROOT,
    CUSTOM_SEED,
    FALLBACK_SEED,
    INVENTED_POOL,
    INVENTED_VARIANT,
    PARAM_BUDGET,
    PARAM_TOLERANCE,
    PAIR_SEED,
    REPO_ROOT,
    RETAINED,
    RUN_SEED,
    OTHER_SEED,
    SHARED,
    SIXTY_BUDGET,
    SPREAD_SEED,
    TINY_BUDGET,
    TrainingCase,
    VARIANTS,
    as_float,
    as_int,
    as_mapping,
    as_sequence,
    as_text,
    baseline_names,
    checkpoint_block,
    custom_configuration,
    custom_run,
    curve_block,
    fallback_run,
    member_ids,
    one_seed_run,
    other_seed_run,
    pair_run,
    repeated_run,
    repo_relative,
    resolved,
    seed_key,
    seed_set,
    sixty_hand_run,
    training,
    two_seed_run,
    write_root,
)

#: `records.md` §12's ten required keys (`surface.md` §4).
REQUIRED_KEYS = (
    "rung",
    "curves",
    "pool",
    "checkpoints",
    "seeds",
    "budget",
    "device",
    "params",
    "table",
    "timings",
)

#: §4.1's three further keys a complete report needs (Rev 2, measured).
FURTHER_KEYS = ("header", "baselines", "axis row")

#: `loop.md` §4's four timing facts, by the name each one names (FAM-13.5).
TIMING_KEYS = ("hands", "wall_clock_seconds", "seconds_per_hand", "hands_per_second")

#: `loop.md` §4's keys of one `variants` row.
VARIANT_ROW_KEYS = (
    "name",
    "backend",
    "encoding",
    "architecture",
    "samples",
    "snapshot_every",
)


class RunTest(TrainingCase):
    def test_trn_2_1_the_record_carries_the_ten_keys_and_the_three_further_ones(self):
        """TRN-2.1 one run record carries `records.md` §12's ten keys, this module's `variants`, §4.1's `header` and `baselines`, and `axis row` for a one-variant rung (records.md §12, surface.md §4, §4.1, loop.md §3)."""
        record = as_mapping(one_seed_run(), "a run record")
        for key in REQUIRED_KEYS + ("variants",) + FURTHER_KEYS:
            with self.subTest(key=key):
                self.assertIn(
                    key,
                    record,
                    "a run record carries %r: records.md §12's ten keys, this module's "
                    "own `variants`, and §4.1's three further keys a complete report "
                    "needs (surface.md §4, §4.1, loop.md §3): %r"
                    % (key, sorted(record)),
                )
        self.assertEqual(
            as_text(record["rung"], "rung"),
            "R1",
            "`rung` is the rung name the run was asked for (records.md §12)",
        )
        self.assertEqual(
            as_text(record["axis row"], "axis row"),
            "n/a, single variant",
            "a one-variant rung's axis row is the explicit string `n/a, single "
            "variant`, never a blank (surface.md §4.1, protocol.md §1)",
        )
        as_mapping(record["header"], "header")
        self.assertTrue(
            record["header"],
            "the header carries protocol.md §1's nine items, because D-5 forbids a "
            "notebook importing engine or features (surface.md §4.1)",
        )
        pair_record = as_mapping(pair_run(), "a two-variant run record")
        self.assertNotIn(
            "axis row",
            pair_record,
            "a two-variant rung omits the axis row, its pair's cell being evaluation's "
            "measurement (surface.md §4.1)",
        )

    def test_trn_2_2_the_curve_is_ten_points_at_budget_over_ten(self):
        """TRN-2.2 `curves[variant][str(seed)]` carries ten sample points at `budget // 10`, a `td_error` of the same length and — at one seed — an all-zero spread (curves.md §2, §4, §5, loop.md §4, FAM-4.1)."""
        record = one_seed_run()
        curves = as_mapping(record["curves"], "'curves'")
        self.assertEqual(
            set(curves),
            set(VARIANTS["R1"]),
            "one entry per variant (loop.md §4): %r" % (sorted(curves),),
        )
        block = curve_block(record, "naive-numeric", RUN_SEED)
        self.assertEqual(
            set(block),
            {"samples", "td_error", "spread"},
            "the curve record carries `samples`, `td_error` and `spread` and nothing "
            "else (curves.md §5, loop.md §4): %r" % (sorted(block),),
        )
        samples = [
            as_int(value, "a sample axis point")
            for value in as_sequence(block["samples"], "'samples'")
        ]
        interval = TINY_BUDGET // 10
        self.assertEqual(
            samples,
            [interval * step for step in range(1, 11)],
            "the axis is the ten snapshot steps at budget // 10, strictly ascending "
            "(curves.md §2, ASM-18): %r" % (samples,),
        )
        signal = as_sequence(block["td_error"], "'td_error'")
        self.assertEqual(
            len(signal),
            len(samples),
            "the signal is one point per step, so the axis and the signal are one "
            "length (curves.md §3, §5): %r" % (signal,),
        )
        for value in signal:
            as_float(value, "a td_error point")
        spread = [
            as_float(value, "a spread point")
            for value in as_sequence(block["spread"], "'spread'")
        ]
        self.assertEqual(
            spread,
            [0.0] * 10,
            "with one seed the spread is exactly 0.0 at every point — the recorded fact "
            "that a one-seed run has no spread (curves.md §4, D-4, D-6): %r" % (spread,),
        )

    def test_trn_2_3_the_spread_is_the_max_minus_the_min_across_seeds(self):
        """TRN-2.3 at two seeds the spread is max minus min of the seeds' signals at each point, repeated at each of the variant's seeds, and non-zero at some point (curves.md §4, §5, loop.md §4, FAM-4.8)."""
        record = two_seed_run()
        first = curve_block(record, "naive-numeric", SPREAD_SEED)
        second = curve_block(record, "naive-numeric", RUN_SEED)
        first_signal = [as_float(value, "a td_error point") for value in first["td_error"]]
        second_signal = [as_float(value, "a td_error point") for value in second["td_error"]]
        expected = [
            max(left, right) - min(left, right)
            for left, right in zip(first_signal, second_signal)
        ]
        first_spread = [as_float(value, "a spread point") for value in first["spread"]]
        second_spread = [as_float(value, "a spread point") for value in second["spread"]]
        for index, (recorded, wanted) in enumerate(zip(first_spread, expected)):
            with self.subTest(point=index):
                self.assertAlmostEqual(
                    recorded,
                    wanted,
                    places=12,
                    msg="the spread at point %d is the max minus the min of the seeds' "
                    "signals, not a standard deviation (curves.md §4): %r against %r"
                    % (index, recorded, wanted),
                )
        self.assertEqual(
            first_spread,
            second_spread,
            "the spread is a property of the variant and the point, so it is repeated "
            "at each of that variant's seeds (curves.md §4, §5)",
        )
        self.assertTrue(
            any(value > 0.0 for value in first_spread),
            "two seeds are two learners and two curves, so the spread is not zero "
            "everywhere (curves.md §4, FAM-4.8): %r" % (first_spread,),
        )

    def test_trn_2_4_params_is_the_declared_band_and_measures_nothing(self):
        """TRN-2.4 `params[variant]` is `{budget: 10000, lower: 9800.0, upper: 10200.0}` — declared, never measured (loop.md §4, ASM-10, registry.md §2, surface.md §4)."""
        record = one_seed_run()
        params = as_mapping(record["params"], "'params'")
        self.assertEqual(
            set(params),
            set(VARIANTS["R1"]),
            "one entry per variant (loop.md §4): %r" % (sorted(params),),
        )
        band = as_mapping(params["naive-numeric"], "params['naive-numeric']")
        self.assertEqual(
            set(band),
            {"budget", "lower", "upper"},
            "the band carries the declared budget and its ±2%% bound (loop.md §4, "
            "ASM-10): %r" % (sorted(band),),
        )
        self.assertEqual(
            as_int(band["budget"], "params['budget']"),
            PARAM_BUDGET,
            "the declared parameter budget is ASM-10's 10,000 (registry.md §1)",
        )
        self.assertAlmostEqual(
            as_float(band["lower"], "params['lower']"),
            PARAM_BUDGET * (1.0 - PARAM_TOLERANCE),
            places=9,
            msg="lower is the declared band's floor, 9,800.0 (loop.md §4)",
        )
        self.assertAlmostEqual(
            as_float(band["upper"], "params['upper']"),
            PARAM_BUDGET * (1.0 + PARAM_TOLERANCE),
            places=9,
            msg="upper is the declared band's ceiling, 10,200.0 (loop.md §4)",
        )

    def test_trn_2_5_timings_carry_the_four_documented_facts(self):
        """TRN-2.5 `timings[variant][str(seed)]` carries exactly `hands`, `wall_clock_seconds`, `seconds_per_hand` and `hands_per_second`, with a positive per-hand cost (loop.md §4, records.md §12, guardrails G6, FAM-13.5)."""
        record = one_seed_run()
        timings = as_mapping(record["timings"], "'timings'")
        self.assertEqual(
            set(timings),
            set(VARIANTS["R1"]),
            "one entry per variant (loop.md §4): %r" % (sorted(timings),),
        )
        per_seed = as_mapping(timings["naive-numeric"], "timings['naive-numeric']")
        self.assertEqual(
            list(timings["naive-numeric"]),
            [seed_key(RUN_SEED)],
            "the seed is the decimal string a record keys its entries by (loop.md §4): "
            "%r" % (sorted(per_seed),),
        )
        facts = as_mapping(per_seed[seed_key(RUN_SEED)], "one timing record")
        self.assertEqual(
            set(facts),
            set(TIMING_KEYS),
            "the four key names are deliberate: the battery's timing_facts classifies a "
            "key by what it names, so `perf`, `t` or `rate` would lose the D-7 evidence "
            "reader (loop.md §4, guardrails G6, FAM-13.5): %r" % (sorted(facts),),
        )
        self.assertEqual(
            as_int(facts["hands"], "timings['hands']"),
            TINY_BUDGET,
            "the hands a pair played are the run's budget (loop.md §4)",
        )
        self.assertGreater(
            as_float(facts["seconds_per_hand"], "seconds_per_hand"),
            0.0,
            "the per-hand cost is measured, not asserted, and a hand costs time "
            "(loop.md §2, §4, ASM-15)",
        )
        self.assertGreaterEqual(
            as_float(facts["wall_clock_seconds"], "wall_clock_seconds"),
            0.0,
            "a wall clock is measured and never claimed beaten (ASM-15, FAM-13.5)",
        )

    def test_trn_2_6_variants_carries_the_interval_the_run_used(self):
        """TRN-2.6 `variants` is the list of `{name, backend, encoding, architecture, samples, snapshot_every}` with `samples` the entry's declared budget and `snapshot_every` the interval the run used — `budget // 10`, not the declared 100 (loop.md §2, §4, guardrails G4, FAM-12.1)."""
        record = sixty_hand_run()
        rows = as_sequence(record["variants"], "'variants'")
        self.assertEqual(
            [as_text(as_mapping(row, "a variants row")["name"], "a row's name") for row in rows],
            list(VARIANTS["R1"]),
            "one row per variant, in the declaration's order (registry.md §1, loop.md §4)",
        )
        row = as_mapping(rows[0], "one variants row")
        self.assertEqual(
            set(row),
            set(VARIANT_ROW_KEYS),
            "the row carries the entry's declaration and the interval used, and no "
            "other key (loop.md §4): %r" % (sorted(row),),
        )
        self.assertEqual(
            as_int(row["samples"], "a row's samples"),
            SHARED["samples"],
            "`samples` is the entry's declared budget, not the run's (loop.md §4)",
        )
        self.assertEqual(
            as_int(row["snapshot_every"], "a row's snapshot_every"),
            SIXTY_BUDGET // 10,
            "`snapshot_every` is the interval the run actually used, budget // 10, and "
            "not the declared 100: at 60 hands the declared 100 would write no snapshot "
            "at all (loop.md §2, guardrails G4, FAM-12.1)",
        )
        self.assertNotEqual(
            as_int(row["snapshot_every"], "a row's snapshot_every"),
            SHARED["snapshot_every"],
            "the declared 100 is the declared budget's interval and is not what a "
            "60-hand run uses (loop.md §2)",
        )
        self.assertEqual(
            as_text(row["backend"], "a row's backend"),
            "numpy",
            "the row repeats the entry's backend (records.md §2)",
        )
        self.assertIn(
            "kind",
            as_mapping(row["architecture"], "a row's architecture"),
            "`architecture` is the entry's record copied verbatim, so the record shows "
            "the settings the run was built from (loop.md §4, records.md §2)",
        )

    def test_trn_2_7_checkpoint_blocks_are_nested_by_variant_and_seed(self):
        """TRN-2.7 `checkpoints[variant][str(seed)]` is `{snapshots, final}` for every variant × seed pair the run trained, every path a file that exists and a file under the write root and never under the shipped tree, spelled repository-relative with POSIX separators when the artefact is inside the repository root and carried unchanged — absolute, exactly what `agents.save` was handed — when it is outside it (loop.md §3, §4, checkpoints.md §2, §3, docs/L2/training/write-root.md §5, FAM-12.1)."""
        record = one_seed_run()
        block = as_mapping(record["checkpoints"], "'checkpoints'")
        self.assertEqual(
            set(block),
            set(VARIANTS["R1"]),
            "one entry per variant (loop.md §4): %r" % (sorted(block),),
        )
        root = write_root()
        repository = os.path.abspath(REPO_ROOT)
        declared = os.path.abspath(CHECKPOINT_ROOT)
        for variant in VARIANTS["R1"]:
            entry = checkpoint_block(record, variant, RUN_SEED)
            with self.subTest(variant=variant):
                self.assertEqual(
                    set(entry),
                    {"snapshots", "final"},
                    "a pair's record names the retained snapshots and that pair's final "
                    "model (loop.md §4, checkpoints.md §3): %r" % (sorted(entry),),
                )
                snapshots = as_sequence(entry["snapshots"], "a pair's 'snapshots'")
                self.assertEqual(
                    len(snapshots),
                    RETAINED,
                    "the record names the last M = 5 of the ten snapshots the pair "
                    "wrote (checkpoints.md §3, ASM-18): %r" % (snapshots,),
                )
                for path in snapshots + [entry["final"]]:
                    recorded = as_text(path, "a checkpoint path")
                    absolute = os.path.abspath(resolved(recorded))
                    self.assertTrue(
                        os.path.exists(resolved(recorded)),
                        "a recorded path resolves to the file agents.save wrote "
                        "(checkpoints.md §2, FAM-12.1): %r" % (recorded,),
                    )
                    self.assertTrue(
                        absolute == root or absolute.startswith(root + os.sep),
                        "the pair's artefacts are written under the write root, which "
                        "is where agents.save was handed the path (write-root.md §1, "
                        "§3, §5): %r is not under %r" % (absolute, root),
                    )
                    if absolute == repository or absolute.startswith(
                        repository + os.sep
                    ):
                        self.assertFalse(
                            os.path.isabs(recorded),
                            "the artefact is inside the repository root, so this is the "
                            "inside-the-repository branch: the record spells it "
                            "repository-relative and not absolute (write-root.md §5, "
                            "checkpoints.md §2): %r (the file is %r)"
                            % (recorded, absolute),
                        )
                        self.assertNotIn(
                            "\\",
                            recorded,
                            "a repository-relative spelling uses POSIX separators, so "
                            "the record travels with the tree (checkpoints.md §2, "
                            "write-root.md §5): %r" % (recorded,),
                        )
                        self.assertEqual(
                            recorded,
                            repo_relative(absolute),
                            "the artefact is inside the repository root, so the recorded "
                            "string is exactly the repository-relative POSIX spelling "
                            "(write-root.md §5): %r against %r"
                            % (recorded, repo_relative(absolute)),
                        )
                        self.assertEqual(
                            os.path.abspath(resolved(recorded)),
                            absolute,
                            "a repository-relative spelling resolves from the repository "
                            "root to the very file agents.save wrote (checkpoints.md §2): "
                            "%r against %r"
                            % (os.path.abspath(resolved(recorded)), absolute),
                        )
                    else:
                        self.assertTrue(
                            os.path.isabs(recorded),
                            "the artefact is outside the repository root, so this is the "
                            "outside-the-repository branch: the record carries it "
                            "unchanged, i.e. absolute (write-root.md §5, "
                            "checkpoints.md §2): %r (the file is %r)"
                            % (recorded, absolute),
                        )
                        self.assertEqual(
                            os.path.abspath(recorded),
                            absolute,
                            "an artefact outside the repository root is carried "
                            "unchanged — exactly the path agents.save was handed "
                            "(write-root.md §5, checkpoints.md §2): %r against %r"
                            % (os.path.abspath(recorded), absolute),
                        )
                    if root != declared:
                        self.assertFalse(
                            absolute == declared
                            or absolute.startswith(declared + os.sep),
                            "the write root differs from the declared <repo>/checkpoints "
                            "root (%r against %r), so no artefact of this run may lie "
                            "under the shipped tree — a battery writes nowhere under "
                            "`checkpoints/`, whichever runner runs it "
                            "(battery.md §2, write-root.md §1, §3, checkpoints.md §5): %r"
                            % (root, declared, absolute),
                        )

    def test_trn_2_8_the_pool_is_frozen_with_one_id_and_the_three_baselines(self):
        """TRN-2.8 `pool` carries the declared id, the read-back `m` and `frozen`, and the ordered members with the three pinned baselines (loop.md §3, records.md §8, ASM-16, FAM-3.17)."""
        record = one_seed_run()
        pool = as_mapping(record["pool"], "'pool'")
        for key in ("id", "m", "frozen", "members"):
            with self.subTest(key=key):
                self.assertIn(
                    key,
                    pool,
                    "records.md §8's pool record carries `id`, `m`, `frozen` and "
                    "`members`, and loop.md §3 reads exactly those (surface.md §4): %r"
                    % (sorted(pool),),
                )
        self.assertTrue(
            as_text(pool["id"], "pool.id").strip(),
            "the record carries one pool id: the declared one (loop.md §3, D-3)",
        )
        self.assertEqual(
            as_int(pool["m"], "pool.m"),
            RETAINED,
            "the read-back bound is the league's M = 5 (registry.md §3, ASM-18)",
        )
        self.assertIs(
            as_mapping(record["pool"], "'pool'").get("frozen"),
            True,
            "the pool is frozen before the first hand and never advanced during the run "
            "(loop.md §1 step 2, ASM-16)",
        )
        ids = member_ids(pool["members"])
        for baseline in baseline_names():
            self.assertIn(
                baseline,
                ids,
                "the three pinned baselines are pool members, in agents.baselines()'s "
                "order (records.md §8, fairness.md §5): %r" % (ids,),
            )
        self.assertEqual(
            as_text(pool["id"], "pool.id"),
            as_text(training().rung("R1")["pool"]["id"], "the declared pool id"),
            "the declared id is the read-back id of the membership, and the run record "
            "carries it and no second one (registry.md §5, surface.md §3.1, FAM-4.7)",
        )

    def test_trn_2_9_one_tuple_gives_one_record_and_a_second_seed_another(self):
        """TRN-2.9 two runs of one `(configuration, seed set, budget)` give equal curves and one pool id, while a different seed set gives different curves (loop.md §7, surface.md §4, FAM-4.7, FAM-4.8)."""
        first = one_seed_run()
        second = repeated_run()
        self.assertIsNot(
            first,
            second,
            "the case compares two runs and not one cached record",
        )
        self.assertEqual(
            as_mapping(first["curves"], "curves"),
            as_mapping(second["curves"], "curves"),
            "the deal and opponent seeds are derivations of (seed, index) and the "
            "learner's generator is seeded from the run seed, so one tuple gives equal "
            "curves twice (loop.md §7, seeds.md §5, FAM-4.7)",
        )
        self.assertEqual(
            as_text(second["pool"]["id"], "the second run's pool id"),
            as_text(first["pool"]["id"], "the first run's pool id"),
            "the pool is frozen before the first hand, so both runs train against one "
            "membership and carry one id (loop.md §7, ASM-16)",
        )
        other = other_seed_run()
        self.assertNotEqual(
            as_mapping(other["curves"], "curves"),
            as_mapping(first["curves"], "curves"),
            "a different seed set gives different curves, because the hands and the "
            "opponents are drawn from the seed (loop.md §7, FAM-4.8)",
        )
        self.assertEqual(
            seed_set(other),
            (OTHER_SEED,),
            "the record states the seed set the run used (loop.md §3, protocol.md §2)",
        )

    def test_trn_2_10_a_two_variant_record_carries_one_pool_id_for_both_arms(self):
        """TRN-2.10 one run of R4 records both arms in one record, and the record carries one pool id — the declared one — for both (loop.md §3, §4, registry.md §3, guardrails G8, FAM-3.18)."""
        record = as_mapping(pair_run(), "a two-variant run record")
        curves = as_mapping(record["curves"], "'curves'")
        self.assertEqual(
            set(curves),
            set(VARIANTS["R4"]),
            "one record trains both arms, so its curve block holds both variants "
            "(registry.md §1, loop.md §4): %r" % (sorted(curves),),
        )
        for variant in VARIANTS["R4"]:
            self.assertIn(
                seed_key(PAIR_SEED),
                as_mapping(curves[variant], "curves[%r]" % (variant,)),
                "both arms trained at the run's one seed (loop.md §1 step 3): %r"
                % (sorted(curves[variant]),),
            )
        pool = as_mapping(record["pool"], "'pool'")
        identifiers = []
        for key in ("id", "pool id", "pool_id"):
            if key in pool:
                identifiers.append((key, pool[key]))
        self.assertEqual(
            len(identifiers),
            1,
            "one id per record, and it is the declared one: the read-back digest id is "
            "carried nowhere, because a two-variant record showing two ids fails "
            "FAM-3.18 (loop.md §3, guardrails G8): %r" % (sorted(pool),),
        )
        self.assertEqual(
            as_text(identifiers[0][1], "the record's pool id"),
            as_text(training().rung("R4")["pool"]["id"], "R4's declared pool id"),
            "both arms of R4 declare one configuration-level pool entry, so the record "
            "carries that one declared id (registry.md §3, surface.md §3.1, FAM-3.18)",
        )
        self.assertEqual(
            as_text(record["rung"], "rung"),
            "R4",
            "one record for the rung, not one per arm (records.md §12)",
        )

    def test_trn_2_11_omitted_arguments_are_the_configuration_s_declared_values(self):
        """TRN-2.11 with `seeds` and `budget` omitted the record states the configuration's own declared values, and the device resolves to `devices()['default']` (loop.md §5, surface.md §4, D-8, records.md §12)."""
        record = as_mapping(custom_run(), "a custom configuration's run record")
        self.assertEqual(
            seed_set(record),
            (CUSTOM_SEED,),
            "an omitted seed set is the configuration's own `seeds`, and the record "
            "states the set used (loop.md §5, surface.md §4): %r" % (record["seeds"],),
        )
        self.assertEqual(
            as_int(record["budget"], "budget"),
            TINY_BUDGET,
            "an omitted budget is the configuration's `samples`, and the record states "
            "the budget used (loop.md §5): %r" % (record["budget"],),
        )
        self.assertEqual(
            as_text(record["device"], "device"),
            as_text(training().devices()["default"], "the default device"),
            "an omitted device is devices()['default'], which is cpu (loop.md §5, "
            "devices.md §1): %r" % (record["device"],),
        )

    def test_trn_2_12_a_variant_entry_s_seeds_are_the_fallback_and_absence_is_refused(self):
        """TRN-2.12 a configuration declaring no `seeds` of its own takes its first variant entry's, and one carrying neither is refused naming the key (loop.md §5, §6, surface.md §4, e2e-surface.md §2)."""
        record = as_mapping(fallback_run(), "a run record with the entry's seeds")
        self.assertEqual(
            seed_set(record),
            (FALLBACK_SEED,),
            "an omitted seed set falls back to the first variant entry's `seeds`, and "
            "no other default is substituted (loop.md §5, D-12): %r" % (record["seeds"],),
        )
        configuration = custom_configuration()
        del configuration["seeds"]
        del configuration["samples"]
        for entry in configuration["variants"]:
            del entry["seeds"]
            del entry["samples"]
        self.refuse(
            lambda: training().run(configuration),
            "MissingConfigurationKey",
            groups=(("seed", "samples"),),
            label="run of a configuration declaring neither seeds nor samples",
        )

    def test_trn_2_13_an_unregistered_configuration_is_recorded_under_its_own_name_and_pool(self):
        """TRN-2.13 a record from a caller's own configuration carries that configuration's own `name` and its declared `pool.id`, so a configuration and a membership in no design document run through the one loop (loop.md §1 step 1, §3, registry.md §3, FAM-15.1, FAM-15.2)."""
        configuration = custom_configuration()
        record = as_mapping(custom_run(), "a custom configuration's run record")
        self.assertEqual(
            as_text(record["rung"], "rung"),
            as_text(configuration["name"], "the configuration's name"),
            "`rung` carries an unregistered configuration's own name (records.md §12, "
            "loop.md §3, FAM-15.1): %r" % (record["rung"],),
        )
        self.assertEqual(
            as_text(record["pool"]["id"], "pool.id"),
            INVENTED_POOL,
            "a configuration in no registry declares its own id and the record carries "
            "that one, with the frozen pool's digest listed beside it nowhere (loop.md "
            "§3, registry.md §3, surface.md §3.1, FAM-15.2): %r" % (record["pool"]["id"],),
        )
        self.assertNotEqual(
            as_text(record["pool"]["id"], "pool.id"),
            as_text(training().rung("R1")["pool"]["id"], "a registry rung's pool id"),
            "the invented membership is its own pool and is not the registry's, so its "
            "id differs (records.md §8)",
        )
        self.assertEqual(
            set(as_mapping(record["curves"], "'curves'")),
            {INVENTED_VARIANT},
            "the record's curves are the configuration's own variant's (loop.md §4): %r"
            % (sorted(as_mapping(record["curves"], "'curves'")),),
        )
        self.assertEqual(
            set(as_mapping(record["params"], "'params'")),
            {INVENTED_VARIANT},
            "the declared band is recorded per variant, the invented one included "
            "(loop.md §4): %r" % (sorted(as_mapping(record["params"], "'params'")),),
        )
        self.assertEqual(
            as_int(record["budget"], "budget"),
            TINY_BUDGET,
            "the custom run trained at the budget the configuration declares (loop.md "
            "§5)",
        )


if __name__ == "__main__":
    unittest.main()
