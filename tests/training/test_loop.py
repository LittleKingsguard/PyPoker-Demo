"""TRN-2 — the one loop: `run(rung, seeds=None, budget=None, device=None)`.

Drives `docs/L3/training/loop.md` §1-§7, `docs/L2/training/surface.md` §4 (Rev 2, §4.1's
three further keys included) and `docs/L1/records.md` §12: the record's keys, the curve
shape at `budget // 10`, the declared parameter band, the four timing key names, the
`variants` block carrying the rule each variant was **built under** and the interval the
run *used*, the record's `rules` set, the one pool id a two-variant record carries, the
defaults of §5, and the record of a configuration that is in no registry.

D-19's `TRN-2.15` is the shape the rule catalogue adds: a configuration whose two entries
declare the catalogue's two rules trains both arms, and the record says which rule each was
built under (`rules.md` §7-§8). The rules are read from `agents.learners()` and never
restated here (`rules.md` §2, §4).

D-20's `TRN-2.17`-`TRN-2.19` are the shape the utility catalogue adds: a record that names
each variant's utility and the set the run declared and trained, a pool block carrying the
utilities its version members declare beside their rules, and a run that refuses an
uncatalogued utility **before a hand is dealt** (`utilities.md` §5, §7, `records.md` §12,
D-20). The utilities are read from `agents.learners()` and never restated here
(`utilities.md` §2, §5).

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
    IGNORED_COUNTERFACTUAL,
    IGNORED_UTILITY,
    INVENTED_BUDGET_POOL,
    INVENTED_BUDGET_RUNG,
    INVENTED_BUDGET_VARIANT,
    INVENTED_PARAM_BUDGET,
    INVENTED_POOL,
    INVENTED_UTILITY_LEFT,
    INVENTED_UTILITY_POOL,
    INVENTED_UTILITY_RUNG,
    INVENTED_VARIANT,
    LEARNING_RULE,
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
    counterfactual_configuration,
    counterfactual_names,
    counterfactual_run,
    counterfactual_set,
    custom_configuration,
    custom_run,
    curve_block,
    fallback_run,
    folder_baselines,
    learning_rules,
    member_ids,
    one_seed_run,
    other_seed_run,
    pair_run,
    pinned_baselines,
    registry_run,
    repeated_run,
    repo_relative,
    resolved,
    seed_key,
    seed_set,
    sixty_hand_run,
    training,
    two_counterfactual_names,
    two_rule_configuration,
    two_rule_run,
    two_seed_run,
    two_utility_configuration,
    two_utility_names,
    two_utility_run,
    utility_names,
    utility_set,
    variant_entries,
    variant_name,
    with_pool_baselines,
    write_root,
    write_tree,
)

#: `records.md` §12's required keys, `rules` among them since D-19 and `utilities` since
#: D-20 (`surface.md` §4, `loop.md` §3); this module's own `variants` is asserted beside
#: them in TRN-2.1.
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
    "rules",
    "utilities",
)

#: §4.1's three further keys a complete report needs (Rev 2, measured).
FURTHER_KEYS = ("header", "baselines", "axis row")

#: `loop.md` §4's four timing facts, by the name each one names (FAM-13.5).
TIMING_KEYS = ("hands", "wall_clock_seconds", "seconds_per_hand", "hands_per_second")

#: `loop.md` §4's keys of one `variants` row: the entry's declaration, the **rule** that
#: variant was built under, the **utility** its reward came from, and the interval the run
#: used (D-19, D-20, `rules.md` §7, `utilities.md` §7).
VARIANT_ROW_KEYS = (
    "name",
    "backend",
    "encoding",
    "architecture",
    "learning_rule",
    "utility",
    "samples",
    "snapshot_every",
)


class RunTest(TrainingCase):
    def test_trn_2_1_the_record_carries_the_required_keys_and_the_three_further_ones(self):
        """TRN-2.1 one run record carries `records.md` §12's required keys — `rules` among them since D-19 — this module's `variants`, §4.1's `header` and `baselines`, and `axis row` for a one-variant rung (records.md §12, surface.md §4, §4.1, loop.md §3, rules.md §7, D-19)."""
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
        """TRN-2.6 `variants` is the list of `{name, backend, encoding, architecture, learning_rule, samples, snapshot_every}` with `samples` the entry's declared budget, `snapshot_every` the interval the run used — `budget // 10`, not the declared 100 — and `learning_rule` the rule that variant was actually built under, its own and not its mate's (loop.md §2, §4, declarations.md §1, §4, rules.md §7-§8, guardrails G4, FAM-12.1, D-19)."""
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
            "the row carries the entry's declaration, the rule the variant was built under "
            "and the interval used, and no other key (loop.md §4, rules.md §7, D-19): %r"
            % (sorted(row),),
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
        declared = as_text(
            variant_entries(training().rung("R1"))[0]["learning_rule"],
            "R1's declared learning_rule",
        )
        self.assertEqual(
            as_text(row["learning_rule"], "a row's learning_rule"),
            declared,
            "`learning_rule` is the rule the variant was actually built under — the "
            "entry's declaration, forwarded into agents.build_learner's spec — so a reader "
            "rebuilds the learner the curve came from (loop.md §1 step 3, §4, "
            "declarations.md §1, rules.md §4, D-19): %r" % (row["learning_rule"],),
        )
        invented = as_mapping(two_rule_run(), "a two-rule configuration's run record")
        wanted = {
            variant_name(entry): as_text(entry["learning_rule"], "a declared rule")
            for entry in variant_entries(two_rule_configuration())
        }
        self.assertEqual(
            len(set(wanted.values())),
            2,
            "the invented configuration declares agents.learners()' two rules, so the "
            "rows below are two rules and not one rule twice (rules.md §2, §7-§8, D-19): "
            "%r" % (wanted,),
        )
        invented_rows = [
            as_mapping(invented_row, "a variants row")
            for invented_row in as_sequence(invented["variants"], "'variants'")
        ]
        self.assertEqual(
            [as_text(invented_row["name"], "a row's name") for invented_row in invented_rows],
            list(wanted),
            "a two-entry configuration's record carries one row per arm, in declaration "
            "order (loop.md §4, rules.md §7)",
        )
        for invented_row in invented_rows:
            name = as_text(invented_row["name"], "a row's name")
            with self.subTest(variant=name):
                self.assertEqual(
                    set(invented_row),
                    set(VARIANT_ROW_KEYS),
                    "the seven keys are one row's keys, both arms included (loop.md §4, "
                    "rules.md §7): %r" % (sorted(invented_row),),
                )
                self.assertEqual(
                    as_text(invented_row["learning_rule"], "a row's learning_rule"),
                    wanted[name],
                    "each row names the rule *that* variant was built under, so a run that "
                    "trained both arms under one rule and copied it into both rows fails "
                    "here (loop.md §4, declarations.md §4, rules.md §7-§8, D-19): %r"
                    % (invented_row["learning_rule"],),
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

    def test_trn_2_8_the_pool_is_frozen_with_one_id_and_the_pinned_baselines(self):
        """TRN-2.8 `pool` carries the declared id, the read-back `m` and `frozen`, and the ordered members with the three pinned baselines — and no folder, because the six registry rows declare none (loop.md §3, records.md §8, ASM-16, ASM-32, FAM-3.17, D-21)."""
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
        for baseline in pinned_baselines():
            self.assertIn(
                baseline,
                ids,
                "the three pinned baselines are pool members, first and in "
                "agents.baselines()'s order (records.md §8, fairness.md §5, ASM-32): %r"
                % (ids,),
            )
        for folder in folder_baselines():
            self.assertNotIn(
                folder,
                ids,
                "a folding baseline joins a pool only when the membership declaration "
                "names it, and no registry row names one (records.md §8, ASM-32, D-21): "
                "%r" % (ids,),
            )
        self.assertEqual(
            ids[: len(pinned_baselines())],
            pinned_baselines(),
            "the pinned baselines come first, in the catalogue's order (records.md §8, "
            "league.md §2): %r" % (ids,),
        )
        self.assertEqual(
            as_text(pool["id"], "pool.id"),
            as_text(training().rung("R1")["pool"]["id"], "the declared pool id"),
            "the declared id is the read-back id of the membership, and the run record "
            "carries it and no second one (registry.md §5, surface.md §3.1, FAM-4.7)",
        )

    def test_trn_2_20_a_configuration_that_declares_folders_admits_them_pinned(self):
        """TRN-2.20 a configuration whose pool entry names D-21's folders trains against a pool that pins them after the three anchor baselines, and its record's `baselines` rows, header counts, membership and id all describe the members it actually holds (loop.md §3, records.md §8, §12, ASM-32, D-21)."""
        declared = list(folder_baselines())
        self.assertTrue(declared, "the catalogue carries at least one folding baseline")
        plain = custom_run()
        named = training().run(
            with_pool_baselines(custom_configuration(), declared),
            (CUSTOM_SEED,),
            TINY_BUDGET,
        )
        pool = as_mapping(named["pool"], "'pool'")
        ids = member_ids(pool["members"])
        self.assertEqual(
            ids,
            pinned_baselines() + declared,
            "the anchor three come first and the declared folders follow them in the "
            "catalogue's order, all pinned (records.md §8, ASM-32, ASM-33, D-21): %r"
            % (ids,),
        )
        self.assertNotEqual(
            ids,
            member_ids(as_mapping(plain["pool"], "'pool")["members"]),
            "the membership a folder-bearing declaration freezes is not the anchors-only "
            "one, so the record describes the members it actually held (records.md §8, "
            "ASM-32, D-21)",
        )
        rows = [
            as_text(row.get("member", ""), "a baseline row")
            if isinstance(row, dict)
            else as_text(row, "a baseline row")
            for row in as_sequence(
                as_mapping(named["baselines"], "'baselines'").get("rows"), "the rows"
            )
        ]
        self.assertEqual(
            rows,
            pinned_baselines() + declared,
            "the run declares one row per baseline the pool holds, so a declared folder "
            "is a row of its own record (records.md §12, protocol.md §3, D-21): %r"
            % (rows,),
        )
        counts = as_mapping(named["header"], "'header'").get("parameter counts")
        for baseline in pinned_baselines() + declared:
            self.assertIn(
                baseline,
                counts,
                "the header's parameter counts name every baseline the pool holds, at the "
                "declared 0 (protocol.md §1, ASM-10, ASM-32, D-21): %r" % (counts,),
            )
        self.assertNotIn(
            declared[0],
            as_mapping(plain["header"], "'header'").get("parameter counts"),
            "a configuration that declares no folder reports none, so the record "
            "describes the membership it had (records.md §8, D-21)",
        )

    def test_trn_2_16_the_pool_block_carries_the_set_its_members_declare(self):
        """TRN-2.16 `pool` carries `rules` — the distinct rules its version members declare, read off the members `pool_members` returned — so R1's baselines-only window reports an empty set and R2's inherited window reports the shipped run's rule, each version member carrying its own (records.md §7, §8, §12, rules.md §6, §7, ASM-27, D-19)."""
        baselines_only = as_mapping(
            as_mapping(one_seed_run(), "a run record").get("pool"), "'pool'"
        )
        self.assertIn(
            "rules",
            baselines_only,
            "records.md §12 makes the pool's `rules` part of the run record, so a record "
            "says which population its opposition held (records.md §8, §12, D-19): %r"
            % (sorted(baselines_only),),
        )
        self.assertEqual(
            as_sequence(baselines_only["rules"], "'pool rules'"),
            [],
            "R1 inherits no lineage, so its pool holds the three pinned baselines and no "
            "version, and a baseline declares no rule — the set is empty and no name is "
            "invented for it (records.md §7, §8, league.md §2): %r"
            % (baselines_only["rules"],),
        )
        inherited = as_mapping(
            as_mapping(
                registry_run("R2", (OTHER_SEED,), TINY_BUDGET), "R2's run record"
            ).get("pool"),
            "R2's 'pool'",
        )
        versions = [
            as_mapping(member, "a version member")
            for member in as_sequence(inherited.get("members"), "'members'")
            if not as_mapping(member, "a pool member").get("baseline")
        ]
        self.assertGreaterEqual(
            len(versions),
            RETAINED,
            "R2 trains against R1's retained window, so its pool carries M versions and "
            "not the baselines alone (registry.md §3, ASM-18, FAM-12.4): %r"
            % (versions,),
        )
        declared = []
        for member in versions:
            rule = as_text(member.get("rule"), "a version member's rule")
            self.assertIn(
                rule,
                learning_rules(),
                "each version member carries the rule its artefact was trained under, and "
                "it is a member of the catalogue agents.learners() publishes "
                "(records.md §7, rules.md §2, §6, D-19): %r" % (member,),
            )
            if rule not in declared:
                declared.append(rule)
        self.assertEqual(
            [
                as_text(rule, "a pool rule")
                for rule in as_sequence(inherited.get("rules"), "'pool rules'")
            ],
            declared,
            "the record's `pool.rules` is exactly the distinct rules its version members "
            "declare, in membership order — read off the members `pool_members` returned "
            "and never one name the run chose (records.md §7, §8, §12, D-19): %r"
            % (inherited.get("rules"),),
        )
        self.assertEqual(
            declared,
            [LEARNING_RULE],
            "the window R2 inherits is the shipped run's, whose rule is %r — the only rule "
            "that existed when its version-1 containers were written (rules.md §6, ASM-5, "
            "D-19): %r" % (LEARNING_RULE, declared),
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

    def test_trn_2_14_a_configuration_level_param_budget_is_reported(self):
        """TRN-2.14 an entry declaring no `param_budget` of its own takes the configuration's, and the record's `params` block reports that number and its ±2% bound — the configuration-level declaration is honoured rather than dropped (loop.md §3-§4, §1 step 9, declarations.md §2, surface.md §4, ASM-10)."""
        configuration = custom_configuration(
            name=INVENTED_BUDGET_RUNG,
            variant=INVENTED_BUDGET_VARIANT,
            pool_id=INVENTED_BUDGET_POOL,
        )
        configuration["param_budget"] = INVENTED_PARAM_BUDGET
        for entry in configuration["variants"]:
            del entry["param_budget"]
        record = as_mapping(
            training().run(configuration),
            "a run record of a configuration declaring the budget at its own level",
        )
        params = as_mapping(record["params"], "'params'")
        self.assertEqual(
            set(params),
            {INVENTED_BUDGET_VARIANT},
            "the band is per variant, so it is keyed by the entry's name (loop.md §4): %r"
            % (sorted(params),),
        )
        band = as_mapping(
            params[INVENTED_BUDGET_VARIANT], "params[%r]" % (INVENTED_BUDGET_VARIANT,)
        )
        self.assertEqual(
            set(band),
            {"budget", "lower", "upper"},
            "the band carries the declared budget and its ±2%% bound (loop.md §4, "
            "ASM-10): %r" % (sorted(band),),
        )
        declared = as_int(band["budget"], "params['budget']")
        self.assertEqual(
            declared,
            INVENTED_PARAM_BUDGET,
            "an entry declaring no `param_budget` takes the configuration's, and the "
            "record reports it: the declared 10,000 is the fallback and not a substitute "
            "for a configuration that declares its own number (declarations.md §2, "
            "loop.md §4): %r" % (declared,),
        )
        self.assertNotEqual(
            declared,
            PARAM_BUDGET,
            "the configuration's own declaration is not replaced by the module's "
            "default, which is what a dropped configuration-level key would look like "
            "(declarations.md §2, surface.md §4): %r" % (declared,),
        )
        self.assertAlmostEqual(
            as_float(band["lower"], "params['lower']"),
            INVENTED_PARAM_BUDGET * (1.0 - PARAM_TOLERANCE),
            places=9,
            msg="lower is that budget's floor, %r (loop.md §4)"
            % (INVENTED_PARAM_BUDGET * (1.0 - PARAM_TOLERANCE),),
        )
        self.assertAlmostEqual(
            as_float(band["upper"], "params['upper']"),
            INVENTED_PARAM_BUDGET * (1.0 + PARAM_TOLERANCE),
            places=9,
            msg="upper is that budget's ceiling, %r (loop.md §4)"
            % (INVENTED_PARAM_BUDGET * (1.0 + PARAM_TOLERANCE),),
        )

    def test_trn_2_15_a_two_rule_configuration_trains_and_records_both(self):
        """TRN-2.15 a configuration whose two entries declare the catalogue's two rules runs and records them: both variants appear in `curves`, each `variants` row names the rule that variant was built under, and the record's `rules` names both, in declaration order (declarations.md §1, §4, surface.md §4, loop.md §1 step 3, §3-§4, rules.md §7, records.md §12, D-19)."""
        configuration = two_rule_configuration()
        entries = variant_entries(configuration)
        names = [variant_name(entry) for entry in entries]
        declared = [
            as_text(entry["learning_rule"], "a declared learning_rule")
            for entry in entries
        ]
        self.assertEqual(
            len(set(declared)),
            2,
            "the invented configuration declares the catalogue's two rules, read from "
            "agents.learners() and never restated (rules.md §2, §4, D-19): %r" % (declared,),
        )
        record = as_mapping(two_rule_run(), "a two-rule configuration's run record")
        curves = as_mapping(record["curves"], "'curves'")
        self.assertEqual(
            list(curves),
            names,
            "a run trains every variant its configuration declares, so both arms appear in "
            "`curves`, in declaration order (loop.md §1 step 3, §4, rules.md §7, D-19): %r"
            % (sorted(curves),),
        )
        seed = as_int(as_sequence(configuration["seeds"], "the declared seed set")[0], "a seed")
        for name in names:
            with self.subTest(variant=name):
                block = curve_block(record, name, seed)
                self.assertIn(
                    seed_key(seed),
                    as_mapping(curves[name], "curves[%r]" % (name,)),
                    "each arm is trained at the run's seed set, so each arm's block is "
                    "keyed by it (loop.md §4, rules.md §7): %r"
                    % (sorted(curves[name]),),
                )
                self.assertEqual(
                    len(as_sequence(block["samples"], "'samples'")),
                    len(as_sequence(block["td_error"], "'td_error'")),
                    "each arm's curve carries one signal point per sample point, so a "
                    "variant that was recorded but never trained has no curve (loop.md §4, "
                    "records.md §12): %r" % (block,),
                )
        self.assertEqual(
            set(as_mapping(record["params"], "'params'")),
            set(names),
            "both arms were trained, so both declared bands are recorded (loop.md §4, "
            "rules.md §7): %r" % (sorted(as_mapping(record["params"], "'params'")),),
        )
        rows = [
            as_mapping(row, "a variants row")
            for row in as_sequence(record["variants"], "'variants'")
        ]
        self.assertEqual(
            [as_text(row["name"], "a row's name") for row in rows],
            names,
            "one `variants` row per arm, in declaration order (loop.md §4, rules.md §7)",
        )
        built_under = [
            as_text(row["learning_rule"], "a row's learning_rule") for row in rows
        ]
        self.assertEqual(
            built_under,
            declared,
            "each row names the rule that variant was built under — its own, forwarded into "
            "agents.build_learner's spec — and never one rule copied into both rows "
            "(loop.md §1 step 3, §4, declarations.md §1, §4, rules.md §7-§8, D-19): %r"
            % (built_under,),
        )
        rules = [
            as_text(rule, "a rule name")
            for rule in as_sequence(record["rules"], "'rules'")
        ]
        self.assertEqual(
            rules,
            declared,
            "the record carries `rules`, the distinct rules the run declared and trained, "
            "in declaration order and de-duplicated, so a two-rule configuration says so "
            "without walking `variants` (records.md §12, loop.md §3-§4, surface.md §4, "
            "rules.md §7, D-19): %r" % (rules,),
        )

    # -- D-20: the utility in the run record -------------------------------
    def rows_of(self, record):
        """One record's `variants` rows, in declaration order (`loop.md` §4)."""
        return [
            as_mapping(row, "a variants row")
            for row in as_sequence(
                as_mapping(record, "a run record")["variants"], "'variants'"
            )
        ]

    def test_trn_2_17_the_record_names_each_variant_s_utility_and_the_set_it_trained(self):
        """TRN-2.17 every `variants` row carries `utility` — the member its entry declares, else the catalogue's **first** — and the record's top-level `utilities` is the set the run declared and trained, one name for a rung and both members for a two-utility configuration (records.md §12, loop.md §3-§4, surface.md §4, utilities.md §5, §7, D-20)."""
        first_utility, second_utility = two_utility_names()
        record = one_seed_run()
        declared = as_text(
            variant_entries(training().rung("R1"))[0]["utility"], "R1's declared utility"
        )
        rows = self.rows_of(record)
        self.assertEqual(
            [as_text(row["utility"], "a row's utility") for row in rows],
            [declared],
            "`variants[i].utility` is the utility that variant was trained on — the "
            "member its entry declares — so a reader rebuilds the reward the curve came "
            "from (loop.md §1 step 3, §4, declarations.md §1, utilities.md §7, D-20): %r"
            % ([row.get("utility") for row in rows],),
        )
        self.assertEqual(
            [as_text(utility, "a utility name") for utility in
             as_sequence(record["utilities"], "'utilities'")],
            [declared],
            "the record carries `utilities`, the distinct utilities the run declared and "
            "trained, in declaration order and de-duplicated — one name for a rung whose "
            "single variant declares one (records.md §12, loop.md §3-§4, utilities.md §7, "
            "D-20): %r" % (record["utilities"],),
        )
        self.assertEqual(
            utility_set(record["utilities"]),
            {declared},
            "the row is a **set** of members and not one side's value: one utility is one "
            "member (records.md §12, utilities.md §7, §8, D-20): %r" % (record["utilities"],),
        )
        silent_configuration = custom_configuration()
        self.assertNotIn(
            "utility",
            variant_entries(silent_configuration)[0],
            "the invented configuration's entry names no utility at all, which is what "
            "makes the catalogue's first member observable below (utilities.md §5)",
        )
        silent = as_mapping(custom_run(), "a custom configuration's run record")
        self.assertEqual(
            [as_text(row["utility"], "a row's utility") for row in self.rows_of(silent)],
            [first_utility],
            "a variant naming no utility is built and trained under the catalogue's "
            "**first** member — the declared default of utilities.md §5 — and the record "
            "says that name rather than a value this module substituted "
            "(declarations.md §1, §4, records.md §12, utilities.md §5, D-20): %r"
            % ([row.get("utility") for row in self.rows_of(silent)],),
        )
        self.assertEqual(
            utility_set(silent["utilities"]),
            {first_utility},
            "and the run's set is that one member, resolved through agents.learners() and "
            "never through a constant of this module (rules.md §4's precedent, "
            "utilities.md §5, D-20): %r" % (silent["utilities"],),
        )
        configuration = two_utility_configuration()
        entries = variant_entries(configuration)
        names = [variant_name(entry) for entry in entries]
        wanted = [as_text(entry["utility"], "a declared utility") for entry in entries]
        self.assertEqual(
            wanted,
            [first_utility, second_utility],
            "the invented configuration declares the catalogue's two utilities, so the "
            "rows below are two members and not one member twice (utilities.md §2, §7, "
            "D-20): %r" % (wanted,),
        )
        paired = as_mapping(two_utility_run(), "a two-utility configuration's run record")
        self.assertEqual(
            list(as_mapping(paired["curves"], "'curves'")),
            names,
            "a run trains every variant its configuration declares, so both arms appear "
            "in `curves`, in declaration order (loop.md §1 step 3, §4, utilities.md §7, "
            "D-20): %r" % (sorted(as_mapping(paired["curves"], "'curves'")),),
        )
        self.assertEqual(
            [as_text(row["name"], "a row's name") for row in self.rows_of(paired)],
            names,
            "one `variants` row per arm, in declaration order (loop.md §4, utilities.md "
            "§7)",
        )
        self.assertEqual(
            [as_text(row["utility"], "a row's utility") for row in self.rows_of(paired)],
            wanted,
            "each row names the utility *that* variant was trained on, so a run that "
            "trained both arms on one reward and copied it into both rows fails here "
            "(loop.md §1 step 3, §4, utilities.md §7, records.md §12, D-20): %r"
            % ([row.get("utility") for row in self.rows_of(paired)],),
        )
        self.assertEqual(
            [as_text(utility, "a utility name") for utility in
             as_sequence(paired["utilities"], "'utilities'")],
            wanted,
            "the run's `utilities` names both members, in declaration order, so a "
            "two-utility configuration says which objectives it trained without walking "
            "`variants` (records.md §12, loop.md §3-§4, surface.md §4, utilities.md §7, "
            "D-20): %r" % (paired["utilities"],),
        )
        self.assertEqual(
            utility_set(paired["utilities"]),
            {first_utility, second_utility},
            "both members are in the set — the run declared and trained both — and never "
            "one arm's utility standing for the run (records.md §12, utilities.md §8, "
            "D-20): %r" % (paired["utilities"],),
        )

    def test_trn_2_18_the_pool_block_carries_the_utilities_its_members_declare(self):
        """TRN-2.18 `pool` carries `utilities` beside `rules` — the distinct utilities its **version** members declare, read off the members `pool_members` returned — so a baselines-only window reports an empty set and R2's inherited window reports the shipped run's utility, each version member carrying its own (records.md §7, §8, §12, utilities.md §6, §7, ASM-27, D-20)."""
        first_utility, _second_utility = two_utility_names()
        baselines_only = as_mapping(
            as_mapping(one_seed_run(), "a run record").get("pool"), "'pool'"
        )
        for key in ("rules", "utilities"):
            with self.subTest(key=key):
                self.assertIn(
                    key,
                    baselines_only,
                    "records.md §12 makes the pool's `rules` **and** `utilities` part of "
                    "the run record, so a record says which estimators and which "
                    "objectives its opposition held (records.md §8, §12, utilities.md §7, "
                    "D-20): %r" % (sorted(baselines_only),),
                )
        self.assertEqual(
            as_sequence(baselines_only["utilities"], "'pool utilities'"),
            [],
            "R1 inherits no lineage, so its pool holds the three pinned baselines and no "
            "version, and a baseline declares no utility — the set is empty and no name "
            "is invented for it (records.md §7, §8, league.md §2, utilities.md §7, D-20): "
            "%r" % (baselines_only["utilities"],),
        )
        invented = as_mapping(
            as_mapping(custom_run(), "a custom configuration's run record").get("pool"),
            "a custom run's 'pool'",
        )
        self.assertEqual(
            as_sequence(invented["utilities"], "'pool utilities'"),
            [],
            "a configuration whose declared window is empty trains against the three "
            "baselines alone, so its pool's utility set is empty too "
            "(records.md §8, league.md §2, D-20): %r" % (invented["utilities"],),
        )
        inherited = as_mapping(
            as_mapping(
                registry_run("R2", (OTHER_SEED,), TINY_BUDGET), "R2's run record"
            ).get("pool"),
            "R2's 'pool'",
        )
        versions = [
            as_mapping(member, "a version member")
            for member in as_sequence(inherited.get("members"), "'members'")
            if not as_mapping(member, "a pool member").get("baseline")
        ]
        self.assertGreaterEqual(
            len(versions),
            RETAINED,
            "R2 trains against R1's retained window, so its pool carries M versions and "
            "not the baselines alone (registry.md §3, ASM-18, FAM-12.4): %r"
            % (versions,),
        )
        declared = []
        for member in versions:
            utility = as_text(member.get("utility"), "a version member's utility")
            self.assertIn(
                utility,
                utility_names(),
                "each version member carries the utility whose reward its artefact was "
                "trained on, and it is a member of the catalogue agents.learners() "
                "publishes (records.md §7, utilities.md §2, §6, D-20): %r" % (member,),
            )
            if utility not in declared:
                declared.append(utility)
        self.assertEqual(
            [as_text(utility, "a pool utility") for utility in
             as_sequence(inherited.get("utilities"), "'pool utilities'")],
            declared,
            "the record's `pool.utilities` is exactly the distinct utilities its version "
            "members declare, in membership order — read off the members `pool_members` "
            "returned and never one name the run chose (records.md §7, §8, §12, "
            "utilities.md §7, D-20): %r" % (inherited.get("utilities"),),
        )
        self.assertEqual(
            declared,
            [first_utility],
            "the window R2 inherits is the shipped run's, whose version-1 containers "
            "carry no `utility` and are read as the catalogue's first — the only utility "
            "its writer could have used (utilities.md §6, ASM-5, D-20): %r" % (declared,),
        )

    def test_trn_2_19_an_uncatalogued_utility_is_refused_before_a_hand_is_dealt(self):
        """TRN-2.19 `training.run` refuses a variant entry naming an uncatalogued utility, by name and against the catalogue, **before any hand is dealt** and before anything is written — and a catalogued second utility is trained, so the refusal is about the name (declarations.md §1-§2, errors.md §2, §3, loop.md §1 step 1, utilities.md §5, §7, ASM-2, D-20)."""
        import random

        configuration = custom_configuration(
            name=INVENTED_UTILITY_RUNG,
            variant=INVENTED_UTILITY_LEFT,
            pool_id=INVENTED_UTILITY_POOL,
        )
        configuration["variants"][0]["utility"] = IGNORED_UTILITY
        before_stream = random.getstate()
        before_write = write_tree()
        refused = self.refuse(
            lambda: training().run(configuration),
            "IgnoredDeclaration",
            groups=((IGNORED_UTILITY,), ("utility",), (INVENTED_UTILITY_LEFT,)),
            label="run of a variant entry naming an uncatalogued utility",
        )
        self.assert_no_hand_dealt(
            before_stream, "a run refusing an uncatalogued utility"
        )
        self.assertEqual(
            [path for path in write_tree() if path not in before_write],
            [],
            "the refusal is raised before the first hand is dealt and before anything is "
            "written, so a declared utility the run would not honour costs no hand and "
            "leaves no artefact (loop.md §1 step 1, declarations.md §2, ASM-2, D-20): %r"
            % ([path for path in write_tree() if path not in before_write],),
        )
        for name in utility_names():
            self.assertIn(
                name,
                str(refused),
                "the refusal names every utility the catalogue carries, so a reader sees "
                "the vocabulary it may name instead (utilities.md §2, §5, D-20): %r"
                % (str(refused),),
            )
        at_configuration = custom_configuration(
            name=INVENTED_UTILITY_RUNG,
            variant=INVENTED_UTILITY_LEFT,
            pool_id=INVENTED_UTILITY_POOL,
        )
        at_configuration["utility"] = IGNORED_UTILITY
        self.refuse(
            lambda: training().run(at_configuration),
            "IgnoredDeclaration",
            groups=((IGNORED_UTILITY,), ("utility",), ("configuration",)),
            label="run of a configuration declaring an uncatalogued utility at its level",
        )
        _first_utility, second_utility = two_utility_names()
        paired = as_mapping(two_utility_run(), "a two-utility configuration's run record")
        self.assertEqual(
            utility_set(paired["utilities"]),
            set(two_utility_names()),
            "the control: a configuration naming a **catalogued** second utility is "
            "accepted and both arms are trained, so the refusal above is about the name "
            "and not about declaring a utility at all (utilities.md §5, §7, D-20): %r"
            % (paired["utilities"],),
        )
        self.assertIn(
            second_utility,
            [as_text(row["utility"], "a row's utility") for row in self.rows_of(paired)],
            "and the catalogued second member reaches the record it trained, which is "
            "what an uncatalogued name never does (records.md §12, utilities.md §7, "
            "D-20): %r" % (second_utility,),
        )

    def test_trn_2_21_a_counterfactual_member_is_recorded_only_when_it_is_not_the_default(self):
        """TRN-2.21 a variant declaring a non-default counterfactual member forwards it to the learner, records it in its `variants` row and in the run's `counterfactuals` set, while a run declaring nothing writes **neither** — no phantom `"none"` row and no empty set — and a name the catalogue does not carry is refused before a hand is dealt (records.md §12, loop.md §1 step 3, §3-§4, counterfactual.md §6, §9, declarations.md §2, D-43)."""
        first_member, second_member = two_counterfactual_names()
        self.assertEqual(
            counterfactual_names()[0],
            first_member,
            "the catalogue's first member is the declared default of counterfactual.md §6, "
            "so the run's conditionality is `not the first`: %r" % (counterfactual_names(),),
        )
        default = as_mapping(custom_run(), "the invented configuration's run record")
        self.assertNotIn(
            "counterfactuals",
            default,
            "a run whose every variant is on the catalogue's first member writes no "
            "`counterfactuals` key at all, which is what keeps a default record field for "
            "field at its capture (records.md §12, counterfactual.md §6, §9, D-43): %r"
            % (sorted(default),),
        )
        for row in self.rows_of(default):
            with self.subTest(variant=row.get("name")):
                self.assertNotIn(
                    "counterfactual",
                    row,
                    "and no `variants` row names the default either: a row naming "
                    "`none` would be a key the capture does not carry "
                    "(counterfactual.md §6, §9, D-43): %r" % (sorted(row),),
                )
        declared = as_mapping(
            counterfactual_run(),
            "a run record of the invented configuration declaring a member",
        )
        self.assertEqual(
            counterfactual_set(declared["counterfactuals"]),
            {second_member},
            "a variant declaring a non-default member writes it into the run's "
            "`counterfactuals` set — the set the run declared and trained "
            "(records.md §12, counterfactual.md §6, D-43): %r"
            % (declared.get("counterfactuals"),),
        )
        rows = self.rows_of(declared)
        self.assertEqual(
            [as_text(row.get("counterfactual"), "a row's member") for row in rows],
            [second_member],
            "and its own `variants` row names the member it was built under, so a run "
            "says which targets produced which curve (records.md §12, loop.md §4, "
            "D-43): %r" % ([row.get("counterfactual") for row in rows],),
        )
        for row in rows:
            with self.subTest(row=row.get("name")):
                self.assertEqual(
                    set(row),
                    set(VARIANT_ROW_KEYS) | {"counterfactual"},
                    "the row is §4's eight keys plus the one conditional ninth and "
                    "nothing else, so the conditional key is the only growth a declaring "
                    "run's row carries (loop.md §4, counterfactual.md §6, D-43): %r"
                    % (sorted(row),),
                )
        doctored = counterfactual_configuration(member=IGNORED_COUNTERFACTUAL)
        refused = self.refuse(
            lambda: training().run(doctored),
            "IgnoredDeclaration",
            groups=((IGNORED_COUNTERFACTUAL,), ("counterfactual",)),
            label="run of a variant entry naming an uncatalogued counterfactual member",
        )
        for name in counterfactual_names():
            self.assertIn(
                name,
                str(refused),
                "the refusal names every member the catalogue carries, so a reader sees "
                "the vocabulary it may name instead (counterfactual.md §6, "
                "declarations.md §2, D-43): %r" % (str(refused),),
            )
        at_configuration = counterfactual_configuration()
        at_configuration["variants"][0].pop("counterfactual")
        at_configuration["counterfactual"] = IGNORED_COUNTERFACTUAL
        self.refuse(
            lambda: training().run(at_configuration),
            "IgnoredDeclaration",
            groups=((IGNORED_COUNTERFACTUAL,), ("counterfactual",), ("configuration",)),
            label="run of a configuration declaring an uncatalogued member at its level",
        )


if __name__ == "__main__":
    unittest.main()
