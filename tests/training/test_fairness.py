"""TRN-7 — what a comparison holds constant: `fairness(left, right)`.

Drives `docs/L3/training/fairness.md` §1-§7 and `docs/L2/training/surface.md` §5 (Rev 2,
§5.1's axis rule included): the eight reportable pairs and their one axis each, the
`{of, differs, declared}` reading for two configurations and for two variant entries, the
thirteen `constants` keys — the game, the pool and the **set** of rules among them — the
pool report's six keys with `same` and the intersection for an adjacent pair, the five
refusals, Rev 2's sixth: two arms declaring two `hyper` blocks are `PairDeclarationsDiffer`,
because a pair that declares two blocks holds no constant there (`TRN-7.8`,
`declarations.md` §4), and D-19's sixth axis: two arms declaring two catalogue rules are
reportable on `rule` and their `constants["rules"]` holds both (`TRN-7.9`, `rules.md` §8), and D-20's seventh axis: two arms declaring two catalogue
utilities are reportable on `utility` with `constants["utilities"]` holding both
(`TRN-7.10`), a side naming none is the catalogue's first and not a phantom difference
(`TRN-7.11`), the `reward` row states the reward each side's utility delivers (`TRN-7.12`),
and a pair differing on `utility` **and** on another axis is refused naming both
(`TRN-7.13`, `utilities.md` §8, D-20).

Reportability is `§2`'s correction and not a restatement: `architecture` is compared only
where the two sides agree on the representation family and on `sparsity`, so R5's `sparse`
(62 wide) against its `dense` (50 wide) differs on `sparsity` alone (ASM-10, guardrails
G14). `fairness` plays no hand, builds no learner, writes nothing and moves no stream
(§7, G19), and `TRN-7.7` proves it by patching every route it could have taken.
"""

import unittest

from _training_support import (
    ADJACENT_PAIRS,
    CONSTANT_KEYS,
    ENTRY_PAIRS,
    HELD_RATE_LEFT,
    HELD_RATE_RIGHT,
    HYPER,
    INVENTED_POOL_A,
    INVENTED_POOL_B,
    INVENTED_PAIR_POOL,
    PARAM_BUDGET,
    RETAINED,
    RUNG_NAMES,
    SHARED,
    TrainingCase,
    agents,
    as_int,
    as_mapping,
    as_sequence,
    as_text,
    baseline_names,
    checkpoint_tree,
    counterfactual_configuration,
    counterfactual_names,
    engine,
    entry_of,
    error_class,
    folder_baselines,
    member_ids,
    pinned_baselines,
    rule_set,
    training,
    two_counterfactual_names,
    two_rule_configuration,
    two_rule_names,
    two_utility_configuration,
    two_utility_names,
    utility_names,
    utility_reward,
    utility_set,
    variant_entries,
    variant_name,
    with_pool,
    with_pool_baselines,
    with_setting,
    write_tree,
)

#: `fairness.md` §4's `readout facts`, the eleven fact names of the information set --
#: the ten every encoding carries plus D-21's derived `hand_class` (ASM-30).
READOUT_FACTS = (
    "street",
    "seat",
    "hole",
    "board",
    "stacks",
    "pot",
    "to_call",
    "limit",
    "history",
    "legal",
    "hand_class",
)

#: `fairness.md` §4's `action vocabulary`, declared there as data.
ACTION_VOCABULARY = {0: "fold", 1: "check-call", 2: "raise"}


class FairnessTest(TrainingCase):
    def rung(self, name):
        return training().rung(name)

    def entry(self, rung_name, variant):
        return entry_of(self.rung(rung_name), variant)

    def result(self, left, right):
        return as_mapping(training().fairness(left, right), "a fairness record")

    def test_trn_7_1_the_five_adjacent_pairs_differ_on_the_later_rung_s_axis(self):
        """TRN-7.1 each adjacent pair reports the axis `fairness.md` §3 tabulates — `backend`, `encoding`, nothing, nothing, `residual` — and `of` is the later rung's declared axis (fairness.md §2-§3, ladder.md §4, FAM-3.6-3.10)."""
        for left, right, axis in ADJACENT_PAIRS:
            record = self.result(self.rung(left), self.rung(right))
            differs = {
                as_text(field, "a differing field")
                for field in as_sequence(
                    as_mapping(record["axis"], "axis")["differs"], "'differs'"
                )
            }
            with self.subTest(pair="%s-%s" % (left, right)):
                self.assertEqual(
                    differs,
                    {axis} if axis is not None else set(),
                    "the eight reportable pairs differ on one axis exactly, and %s-%s "
                    "differs on %r (fairness.md §2-§3, surface.md §5.1): %r"
                    % (left, right, axis or "nothing", sorted(differs)),
                )
                self.assertEqual(
                    as_text(as_mapping(record["axis"], "axis")["of"], "of"),
                    as_text(self.rung(right)["axis"], "%s's declared axis" % (right,)),
                    "for two configurations `of` is the later one's declared axis — the "
                    "rung that varies against the lineage it inherits — so a pair whose "
                    "primaries declare one stack still names the axis the rung is for "
                    "(fairness.md §2-§3, D-3, D-16): %r" % (record["axis"]["of"],),
                )
                self.assertEqual(
                    as_text(as_mapping(record["axis"], "axis")["declared"], "declared"),
                    as_text(self.rung(right)["axis"], "%s's declared axis" % (right,)),
                    "`declared` is that declaration, quoted from the configuration "
                    "(fairness.md §2, surface.md §5)",
                )

    def test_trn_7_2_the_three_intra_rung_pairs_differ_on_their_own_axis(self):
        """TRN-7.2 R4's, R5's and R6's own pairs report `architecture`/`width`+`depth`, `connectivity`/`sparsity` and `residual`/`residual`, with `declared` `None` (fairness.md §2-§3, surface.md §5.1, guardrails G14, FAM-3.11-3.13)."""
        for (rung_name, left, right), (axis, fields) in ENTRY_PAIRS.items():
            record = self.result(self.entry(rung_name, left), self.entry(rung_name, right))
            body = as_mapping(record["axis"], "axis")
            with self.subTest(pair="%s %s-%s" % (rung_name, left, right)):
                self.assertEqual(
                    as_text(body["of"], "of"),
                    axis,
                    "an entry pair's `of` is the one axis the difference falls in "
                    "(fairness.md §2): %r" % (body["of"],),
                )
                self.assertEqual(
                    {
                        as_text(field, "a differing field")
                        for field in as_sequence(body["differs"], "'differs'")
                    },
                    fields,
                    "`differs` names the field names that differ, so a reader sees the "
                    "words FAM-3.11 and FAM-3.12 read (fairness.md §2): %r"
                    % (body["differs"],),
                )
                self.assertIsNone(
                    body["declared"],
                    "for two entries `declared` is None: the axis is the one the "
                    "difference falls in and there is no configuration's sentence to "
                    "quote (fairness.md §2, surface.md §5)",
                )
                self.assertEqual(
                    [as_text(name, "a pair name") for name in
                     as_sequence(record["pair"], "'pair'")],
                    [left, right],
                    "`pair` reports the two sides by their own names (fairness.md §1)",
                )

    def test_trn_7_3_the_pair_is_the_primaries_and_the_axis_is_the_later_declaration(self):
        """TRN-7.3 for two configurations `pair` names their **primary** variants and `axis.declared` is the later configuration's declaration; for two entries `pair` names the entries themselves (fairness.md §1-§2, ladder.md §2, D-16)."""
        for left, right, _axis in ADJACENT_PAIRS:
            record = self.result(self.rung(left), self.rung(right))
            with self.subTest(pair="%s-%s" % (left, right)):
                self.assertEqual(
                    [as_text(name, "a pair name") for name in
                     as_sequence(record["pair"], "'pair'")],
                    [as_text(self.rung(left)["primary"], "the primary"),
                     as_text(self.rung(right)["primary"], "the primary")],
                    "the two sides are compared on their primary variants, because the "
                    "primary is the lineage the next rung inherits (fairness.md §1, "
                    "ladder.md §2, D-16)",
                )
        record = self.result(self.rung("R2"), self.rung("R3"))
        self.assertEqual(
            as_text(as_mapping(record["axis"], "axis")["of"], "of"),
            as_text(self.rung("R3")["axis"], "R3's declared axis"),
            "the axis is read from the later configuration — R3 tokenises what R2 left "
            "numeric (fairness.md §2): %r" % (record["axis"]["of"],),
        )
        self.assertEqual(
            set(as_mapping(record, "a fairness record")),
            {"pair", "axis", "constants", "pool"},
            "the record carries `pair`, `axis`, `constants` and `pool` (surface.md §5): "
            "%r" % (sorted(record),),
        )

    def test_trn_7_4_constants_carries_the_thirteen_held_declarations(self):
        """TRN-7.4 `constants` carries `fairness.md` §4's thirteen keys — `rules` among them, holding the **set** of rules the two sides are trained under and never one side's value — with `game` equal to `engine.game_config()`, a `pool` report repeated inside it, and the vocabulary and readout facts declared as data (fairness.md §4, declarations.md §4, rules.md §8, guardrails G15, FAM-3.14, FAM-13.3, D-19)."""
        record = self.result(self.rung("R1"), self.rung("R2"))
        constants = as_mapping(record["constants"], "'constants'")
        for key in CONSTANT_KEYS:
            with self.subTest(key=key):
                self.assertIn(
                    key,
                    constants,
                    "a comparison reports what ladder.md §4 holds constant, under "
                    "fairness.md §4's key names: %r is missing from %r"
                    % (key, sorted(constants)),
                )
        self.assertEqual(
            set(constants),
            set(CONSTANT_KEYS),
            "the thirteen declarations are the list, and a row that drops one fails "
            "FAM-3.14's token scan (fairness.md §4): %r" % (sorted(constants),),
        )
        self.assertEqual(
            constants["game"],
            engine().game_config(),
            "the game is engine.game_config's, identical for every rung (fairness.md §4, "
            "engine/surface.md §3, D-2)",
        )
        self.assertEqual(
            constants["action vocabulary"],
            ACTION_VOCABULARY,
            "the three-index vocabulary is declared here as data, because "
            "features.action_space is not among the five granted calls (fairness.md §4, "
            "D-13): %r" % (constants["action vocabulary"],),
        )
        self.assertEqual(
            set(as_sequence(constants["readout facts"], "readout facts")),
            set(READOUT_FACTS),
            "the eleven readout facts are declared here for the same reason, identical for "
            "every encoding (fairness.md §4, D-3, ASM-30): %r" % (constants["readout facts"],),
        )
        declared_rules = {
            as_text(entry["learning_rule"], "a declared rule")
            for entry in (self.entry("R1", "naive-numeric"),
                          self.entry("R2", "naive-numeric-torch"))
        }
        self.assertEqual(
            rule_set(constants["rules"]),
            declared_rules,
            "`rules` is the **set** of rules the two sides are trained under — one name for "
            "a pair declaring one rule — and never one side's value, because `learning_rule` "
            "left the settings a pair must share when D-19 made it a sixth axis; the "
            "invented two-rule pair is TRN-7.9's (fairness.md §4, declarations.md §4, "
            "rules.md §8, D-19): %r" % (constants["rules"],),
        )
        self.assertEqual(
            len(rule_set(constants["rules"])),
            1,
            "R1 and R2 declare one rule, so the set holds one member and not two copies of "
            "it: what the row reports is a set, deduplicated (fairness.md §4, rules.md §8, "
            "D-19): %r" % (constants["rules"],),
        )
        self.assertEqual(
            constants["hyper"],
            HYPER,
            "every hyperparameter is held constant, copied from the declaration "
            "(fairness.md §4, ASM-7)",
        )
        band = as_mapping(constants["param budget"], "param budget")
        self.assertEqual(
            as_int(band.get("budget"), "the parameter budget"),
            PARAM_BUDGET,
            "the parameter budget is the declared 10,000 within ±2%%, and a run measures "
            "none of it (fairness.md §4, ASM-10): %r" % (band,),
        )
        self.assertEqual(
            as_int(constants["sample budget"], "sample budget"),
            SHARED["samples"],
            "the sample budget is the hands per variant per seed the pair is trained at "
            "(fairness.md §4, ASM-8)",
        )
        self.assertEqual(
            tuple(as_int(seed, "a seed") for seed in as_sequence(
                constants["seed set"], "seed set")),
            tuple(SHARED["seeds"]),
            "the seed set is protocol.md §2's (fairness.md §4)",
        )
        repeated = as_mapping(constants["pool"], "the constant's pool report")
        self.assertEqual(
            set(repeated),
            set(as_mapping(record["pool"], "'pool'")),
            "§5's pool report is repeated here as one of the held-constant facts, so the "
            "two readings agree key for key (fairness.md §4, §5, D-16)",
        )
        self.assertEqual(
            repeated, record["pool"],
            "the pool a pair is held constant on is the pool the record reports "
            "(fairness.md §4-§5, ASM-16)",
        )
        self.assertIn(
            as_text(constants["table budget"]["table"], "table budget's table"),
            ("live", "full"),
            "the table budget is `live` or `full` with its hands per cell and its seat "
            "alternation (fairness.md §4, league.md §6)",
        )

    def test_trn_7_5_the_pool_report_carries_one_id_or_two_and_the_shared_membership(self):
        """TRN-7.5 `pool` carries `m`, `frozen`, the three `baselines`, each arm's declared `id`, `same` (`None` for an adjacent pair, the one id for an intra-rung pair) and `membership` — the intersection, which for R1-R2 is the three baselines (fairness.md §5, surface.md §5, FAM-3.17, FAM-3.18)."""
        adjacent = self.result(self.rung("R1"), self.rung("R2"))
        report = as_mapping(adjacent["pool"], "'pool'")
        for key in ("m", "frozen", "baselines", "ids", "same", "membership"):
            with self.subTest(key=key):
                self.assertIn(
                    key,
                    report,
                    "§5's pool report carries `m`, `frozen`, the three `baselines`, the "
                    "declared `ids`, `same` and `membership` (fairness.md §5, "
                    "surface.md §5): %r" % (sorted(report),),
                )
        self.assertEqual(
            set(report),
            {"m", "frozen", "baselines", "ids", "same", "membership"},
            "the six keys are the report and a seventh is an invention (fairness.md §5, "
            "§8): %r" % (sorted(report),),
        )
        self.assertEqual(
            as_int(report["m"], "pool.m"),
            RETAINED,
            "the pool's bound is the league's M = 5 (fairness.md §5, ASM-18)",
        )
        self.assertIs(
            report["frozen"],
            True,
            "each pool declares frozen true — the league's M and the freeze are what a "
            "pair's parity is read against (fairness.md §5, ASM-16)",
        )
        self.assertEqual(
            [as_text(name, "a baseline") for name in
             as_sequence(report["baselines"], "'baselines'")],
            pinned_baselines(),
            "the three pinned baselines are reported in agents.baselines()'s order, and a "
            "registry row declares no folder (fairness.md §5, records.md §8, ASM-32)",
        )
        self.assertIsNone(
            report["same"],
            "an adjacent pair cannot share one id: R2's pool holds R1's snapshots while "
            "R1's is the baselines alone, so `same` is None (fairness.md §5, "
            "ladder.md §2): %r" % (report["same"],),
        )
        ids = [as_text(value, "a declared id") for value in
               as_sequence(report["ids"], "'ids'")]
        self.assertEqual(
            ids,
            [as_text(self.rung("R1")["pool"]["id"], "R1's declared id"),
             as_text(self.rung("R2")["pool"]["id"], "R2's declared id")],
            "both ids are reported, because both arms train against the pools their "
            "rungs declare (fairness.md §5, surface.md §5): %r" % (ids,),
        )
        self.assertNotEqual(
            ids[0], ids[1],
            "the two windows differ, so the two declared ids differ (records.md §8)",
        )
        self.assertEqual(
            member_ids(report["membership"]),
            pinned_baselines(),
            "`membership` is the intersection of the two windows in lineage order, which "
            "for R1-R2 is the three pinned baselines alone — the pool the parity check "
            "plays on (fairness.md §5, D-7, ASM-32): %r" % (report["membership"],),
        )
        pair = self.result(
            with_pool(self.entry("R5", "dense"), INVENTED_PAIR_POOL),
            with_pool(self.entry("R5", "sparse"), INVENTED_PAIR_POOL),
        )
        shared = as_mapping(pair["pool"], "'pool'")
        self.assertEqual(
            as_text(shared["same"], "same"),
            INVENTED_PAIR_POOL,
            "two arms of one rung declare one configuration-level pool entry, so `same` "
            "is that id (fairness.md §5, FAM-3.17, FAM-3.18): %r" % (shared["same"],),
        )
        self.assertEqual(
            [as_text(value, "a declared id") for value in
             as_sequence(shared["ids"], "'ids'")],
            [INVENTED_PAIR_POOL, INVENTED_PAIR_POOL],
            "both arms declare the one id, so both are reported and they agree "
            "(fairness.md §5)",
        )

    def test_trn_7_14_a_declared_folder_is_reported_beside_the_anchor_three(self):
        """TRN-7.14 a pair whose two arms declare D-21's folders reports them as the baselines their pools hold — pinned after the three anchors and never among the anchors — and a pair that declares none reports the three alone (fairness.md §5, records.md §8, ASM-32, D-21)."""
        declared = list(folder_baselines())
        self.assertTrue(declared, "the catalogue carries at least one folding baseline")
        left = with_pool_baselines(self.rung("R1"), declared)
        right = with_pool_baselines(self.rung("R2"), declared)
        report = as_mapping(self.result(left, right)["pool"], "'pool'")
        self.assertEqual(
            [as_text(name, "a baseline") for name in
             as_sequence(report["baselines"], "'baselines'")],
            pinned_baselines() + declared,
            "the report names the anchor three and then the declared folders, in the "
            "catalogue's order (fairness.md §5, records.md §8, D-21): %r"
            % (report["baselines"],),
        )
        self.assertEqual(
            member_ids(report["membership"])[: len(pinned_baselines())],
            pinned_baselines(),
            "the pinned three open the shared membership whatever a declaration names "
            "(fairness.md §5, ASM-32): %r" % (report["membership"],),
        )
        plain = as_mapping(
            self.result(self.rung("R1"), self.rung("R2"))["pool"], "'pool'"
        )
        self.assertEqual(
            [as_text(name, "a baseline") for name in
             as_sequence(plain["baselines"], "'baselines'")],
            pinned_baselines(),
            "a pair that declares no folder reports the anchor three and no more "
            "(fairness.md §5, D-21)",
        )

    def test_trn_7_6_the_five_refusals(self):
        """TRN-7.6 a rung *name* is not a side, two sides of different kinds are refused, a key the comparison reads is named when absent, differences in two axes are refused naming both, and two pool ids are refused naming both (fairness.md §6, errors.md §2, §4)."""
        package = training()
        self.refuse(
            lambda: package.fairness(RUNG_NAMES[0], RUNG_NAMES[1]),
            "NotAComparisonSide",
            groups=((RUNG_NAMES[0],), ("side", "configuration", "entry")),
            label="fairness of two rung names",
        )
        self.refuse(
            lambda: package.fairness(self.rung("R1"), self.entry("R1", "naive-numeric")),
            "SideKindMismatch",
            groups=(("kind", "configuration", "entry"),),
            label="fairness of a configuration and an entry",
        )
        stripped = dict(self.rung("R5"))
        stripped["variants"] = [
            {key: value for key, value in entry.items() if key != "architecture"}
            for entry in variant_entries(stripped)
        ]
        self.refuse(
            lambda: package.fairness(stripped, self.rung("R5")),
            "ComparisonKeyMissing",
            groups=(("architecture",),),
            label="fairness of a configuration whose entries carry no architecture",
        )
        self.refuse(
            lambda: package.fairness(
                self.entry("R5", "dense"),
                with_setting(self.entry("R5", "sparse"), encoding="flat-numeric"),
            ),
            "MultipleAxes",
            groups=(("encoding",), ("connectivity", "sparsity")),
            label="fairness of a pair differing on two axes",
        )
        self.refuse(
            lambda: package.fairness(
                with_pool(self.entry("R6", "residual"), INVENTED_POOL_A),
                with_pool(self.entry("R6", "plain"), INVENTED_POOL_B),
            ),
            "PoolIdsDiffer",
            groups=((INVENTED_POOL_A,), (INVENTED_POOL_B,)),
            label="fairness of two variants declaring two pool ids",
        )
        self.assertEqual(
            error_class("MultipleAxes").__name__,
            "MultipleAxes",
            "errors.md §2 names the class the two-axis difference is refused with",
        )

    def test_trn_7_7_fairness_plays_no_hand_builds_nothing_and_writes_nothing(self):
        """TRN-7.7 `fairness` plays no hand, builds no learner or encoder, writes no file and leaves the global `random` stream where it found it (fairness.md §7, surface.md §5, guardrails G19, ASM-2)."""
        import random
        from unittest import mock

        package = training()
        before_tree = checkpoint_tree()
        before_write = write_tree()
        before_stream = random.getstate()
        with mock.patch.object(agents(), "build_learner") as build_learner, mock.patch.object(
            agents(), "save"
        ) as save, mock.patch.object(engine(), "play_hand") as play_hand, mock.patch.object(
            engine(), "new_hand"
        ) as new_hand, mock.patch("os.makedirs") as makedirs:
            pair = package.fairness(self.rung("R1"), self.rung("R2"))
            entries = package.fairness(
                self.entry("R6", "residual"), self.entry("R6", "plain")
            )
        build_learner.assert_not_called()
        save.assert_not_called()
        play_hand.assert_not_called()
        new_hand.assert_not_called()
        makedirs.assert_not_called()
        self.assertIn("axis", pair, "the comparison returns its axis (surface.md §5)")
        self.assertIn("pool", entries, "the entries' comparison returns their pool")
        self.assert_no_hand_dealt(before_stream, "fairness")
        self.assert_tree_untouched(before_tree, "fairness")
        self.assertEqual(
            [path for path in write_tree() if path not in before_write],
            [],
            "`fairness` writes no file under the write root either, and that is the "
            "tree a battery's run writes: the shipped tree is empty of a run's files by "
            "construction, so this is the assertion that could still fail (fairness.md "
            "§7, guardrails G19, docs/L2/training/write-root.md §1, §3): %r"
            % ([path for path in write_tree() if path not in before_write],),
        )

    def test_trn_7_8_two_hyper_blocks_are_a_pair_difference(self):
        """TRN-7.8 two variant entries declaring two `hyper` blocks are `PairDeclarationsDiffer` and both blocks are named, because a pair that declares two blocks holds no constant there and reporting one of them as held would be the same defect in a report instead of a run (declarations.md §3-§4, errors.md §2, §4, surface.md §5, ASM-7).

        `PairDeclarationsDiffer` is the one class two entry points raise — `run` for a configuration's two arms (`TRN-9.16`) and `fairness` here — and the support's refusal reader maps a class to an entry point once, defaulting to `run`. This case therefore passes `entry="fairness"` explicitly instead of relaxing the assertion: the message it accepts is the one `training.fairness` writes.
        """
        held_left = with_setting(
            self.entry("R6", "residual"), hyper=dict(HYPER, learning_rate=HELD_RATE_LEFT)
        )
        held_right = with_setting(
            self.entry("R6", "plain"), hyper=dict(HYPER, learning_rate=HELD_RATE_RIGHT)
        )
        self.refuse(
            lambda: training().fairness(held_left, held_right),
            "PairDeclarationsDiffer",
            groups=(
                ("hyper",),
                (str(HELD_RATE_LEFT),),
                (str(HELD_RATE_RIGHT),),
                ("held constant",),
            ),
            label="fairness of two variants declaring two hyper blocks",
            entry="fairness",
        )
        accepted = as_mapping(
            training().fairness(
                with_setting(self.entry("R6", "residual"), hyper=dict(HYPER)),
                with_setting(self.entry("R6", "plain"), hyper=dict(HYPER)),
            ),
            "a fairness record of two equal hyper blocks",
        )
        self.assertIn(
            "constants",
            accepted,
            "two sides declaring the declared `hyper` block are accepted and their "
            "constants are reported, so the refusal above is about the difference and not "
            "about `hyper` being named at all (declarations.md §4, fairness.md §4): %r"
            % (sorted(accepted),),
        )

    def test_trn_7_9_two_rules_are_the_rule_axis_and_the_set_is_reported(self):
        """TRN-7.9 two entries declaring the catalogue's two rules differ on the `rule` axis — `of` names the axis and `differs` names `learning_rule` — and are **not** refused, their `constants["rules"]` holding both rules; the control: two entries declaring one rule report a one-element set (fairness.md §2, §4, §6, surface.md §5, declarations.md §3-§4, rules.md §8, D-19)."""
        first_rule, second_rule = two_rule_names()
        entries = variant_entries(two_rule_configuration())
        self.assertEqual(
            [as_text(entry["learning_rule"], "a declared rule") for entry in entries],
            [first_rule, second_rule],
            "the invented pair declares the catalogue's two rules in its order, read from "
            "agents.learners() and not restated (rules.md §2, §4, D-19)",
        )
        pair = self.result(entries[0], entries[1])
        self.assertEqual(
            set(as_mapping(pair, "a fairness record")),
            {"pair", "axis", "constants", "pool"},
            "a pair whose arms declare two catalogue rules is reportable and returns the "
            "record every comparison returns, so a differing `learning_rule` is the `rule` "
            "axis and never a PairDeclarationsDiffer refusal (fairness.md §2, §6, "
            "declarations.md §3-§4, rules.md §8, D-19): %r" % (sorted(pair),),
        )
        self.assertEqual(
            [as_text(name, "a pair name") for name in as_sequence(pair["pair"], "'pair'")],
            [variant_name(entry) for entry in entries],
            "`pair` reports the two sides by their own names (fairness.md §1)",
        )
        axis = as_mapping(pair["axis"], "axis")
        self.assertEqual(
            as_text(axis["of"], "of"),
            "rule",
            "`of` is the one axis the difference falls in, and two estimators are the "
            "`rule` axis D-19 added beside the five (fairness.md §2, surface.md §5, "
            "rules.md §4, §8, D-19): %r" % (axis["of"],),
        )
        self.assertEqual(
            {
                as_text(field, "a differing field")
                for field in as_sequence(axis["differs"], "'differs'")
            },
            {"learning_rule"},
            "`differs` names the field that differs, and it is `learning_rule` alone: the "
            "two arms agree on backend, encoding, architecture, connectivity and residual, "
            "so the rule is the whole difference (fairness.md §2, rules.md §8, D-19): %r"
            % (axis["differs"],),
        )
        self.assertIsNone(
            axis["declared"],
            "for two entries `declared` is None, there being no configuration's axis "
            "sentence to quote (fairness.md §2)",
        )
        constants = as_mapping(pair["constants"], "'constants'")
        self.assertEqual(
            rule_set(constants["rules"]),
            {first_rule, second_rule},
            "what the pair holds constant is the **set** of rules it declares — both, in "
            "declaration order and never one side's — because two estimators are reported "
            "as the axis and not imposed as a constant (fairness.md §4, §6, declarations.md "
            "§4, rules.md §8, D-19): %r" % (constants["rules"],),
        )
        self.assertEqual(
            len(rule_set(constants["rules"])),
            2,
            "two rules are two members of the set and not one name repeated, which is what "
            "a report quoting one side would show (fairness.md §4, rules.md §8): %r"
            % (constants["rules"],),
        )
        control = as_mapping(
            self.result(entries[0], with_setting(entries[1], learning_rule=first_rule)),
            "a fairness record of two entries declaring one rule",
        )
        control_constants = as_mapping(control["constants"], "'constants'")
        self.assertEqual(
            rule_set(control_constants["rules"]),
            {first_rule},
            "the control: two entries declaring one rule report a one-element set, so the "
            "row above is what the pair declares and not a fixed pair of names "
            "(fairness.md §4, rules.md §8, D-19): %r" % (control_constants["rules"],),
        )

    # -- D-20: the utility axis --------------------------------------------
    def test_trn_7_10_two_utilities_are_the_utility_axis_and_the_set_is_reported(self):
        """TRN-7.10 two entries declaring the catalogue's two utilities differ on the `utility` axis — the token and the field are one word, unlike the rule's `rule`/`learning_rule` — and are **not** refused, their `constants['utilities']` holding **both**; the control: two entries declaring one utility report a one-element set (fairness.md §2, §4, §6, surface.md §5, declarations.md §3-§4, utilities.md §8, D-20)."""
        axes = tuple(
            as_text(axis, "an axis") for axis in self.internal("declarations", "AXES")
        )
        self.assertEqual(
            len(axes),
            8,
            "`utility` joins six axes as the seventh and D-43's `counterfactual` joins "
            "them as the eighth, so a comparison is read on eight and a report can say "
            "which one a pair differs on (declarations.md §3, utilities.md §8, "
            "counterfactual.md §6, D-20, D-43): %r" % (axes,),
        )
        self.assertIn(
            "counterfactual",
            axes,
            "the counterfactual member is one of the axes a comparison reports, and it is "
            "the third catalogue's and not a rule's or a utility's (counterfactual.md "
            "§6, D-43): %r" % (axes,),
        )
        self.assertIn(
            "utility",
            axes,
            "the utility is one of the axes a comparison reports (utilities.md §8, "
            "D-20): %r" % (axes,),
        )
        first_utility, second_utility = two_utility_names()
        entries = variant_entries(two_utility_configuration())
        self.assertEqual(
            [as_text(entry["utility"], "a declared utility") for entry in entries],
            [first_utility, second_utility],
            "the invented pair declares the catalogue's two utilities in its order, read "
            "from agents.learners() and not restated (utilities.md §2, §5, D-20): %r"
            % ([entry.get("utility") for entry in entries],),
        )
        pair = self.result(entries[0], entries[1])
        self.assertEqual(
            set(as_mapping(pair, "a fairness record")),
            {"pair", "axis", "constants", "pool"},
            "a pair whose arms declare two catalogue utilities is reportable and returns "
            "the record every comparison returns, so a differing utility is the `utility` "
            "axis and never a refusal (fairness.md §2, §6, utilities.md §8, D-20): %r"
            % (sorted(pair),),
        )
        self.assertEqual(
            [as_text(name, "a pair name") for name in as_sequence(pair["pair"], "'pair'")],
            [variant_name(entry) for entry in entries],
            "`pair` reports the two sides by their own names (fairness.md §1)",
        )
        axis = as_mapping(pair["axis"], "axis")
        self.assertEqual(
            as_text(axis["of"], "of"),
            "utility",
            "`of` is the one axis the difference falls in, and two objectives are the "
            "`utility` axis D-20 added beside the six (fairness.md §2, surface.md §5, "
            "utilities.md §8, D-20): %r" % (axis["of"],),
        )
        self.assertEqual(
            {
                as_text(field, "a differing field")
                for field in as_sequence(axis["differs"], "'differs'")
            },
            {"utility"},
            "`differs` names the field that differs, and it is `utility` — **one word**, "
            "the axis token and the field name being the same, unlike the rule's pairing "
            "of the token `rule` with the field `learning_rule` (utilities.md §8, D-20): "
            "%r" % (axis["differs"],),
        )
        self.assertIsNone(
            axis["declared"],
            "for two entries `declared` is None, there being no configuration's axis "
            "sentence to quote (fairness.md §2)",
        )
        constants = as_mapping(pair["constants"], "'constants'")
        self.assertEqual(
            [as_text(utility, "a utility name") for utility in
             as_sequence(constants["utilities"], "a utilities row")],
            [first_utility, second_utility],
            "what the pair holds constant is the **set** of utilities it declares — both, "
            "in declaration order, left first, and never one side's — because two "
            "objectives are reported as the axis and not imposed as a constant "
            "(fairness.md §4, §6, declarations.md §4, utilities.md §8, D-20): %r"
            % (constants["utilities"],),
        )
        self.assertEqual(
            utility_set(constants["utilities"]),
            {first_utility, second_utility},
            "the row holds both members, so a report of a two-utility pair states both "
            "objectives it was trained on (utilities.md §8, records.md §13, D-20): %r"
            % (constants["utilities"],),
        )
        control = as_mapping(
            self.result(entries[0], with_setting(entries[1], utility=first_utility)),
            "a fairness record of two entries declaring one utility",
        )
        control_constants = as_mapping(control["constants"], "'constants'")
        self.assertEqual(
            utility_set(control_constants["utilities"]),
            {first_utility},
            "the control: two entries declaring one utility report a one-element set, so "
            "the row above is what the pair declares and not a fixed pair of names "
            "(fairness.md §4, utilities.md §8, D-20): %r"
            % (control_constants["utilities"],),
        )
        self.assertEqual(
            len(as_sequence(control_constants["utilities"], "a utilities row")),
            1,
            "one utility is one member of the set and not the same name twice "
            "(fairness.md §4, utilities.md §8): %r" % (control_constants["utilities"],),
        )

    def test_trn_7_11_a_side_declaring_no_utility_is_the_catalogue_s_first(self):
        """TRN-7.11 a side that declares no `utility` is trained under the catalogue's **first** member, so a side spelling that member out and a side leaving it unsaid are one utility and never a phantom difference — resolved through the catalogue and not compared as a raw key (fairness.md §2, §4, §7, utilities.md §5, §8, records.md §2, D-20)."""
        first_utility, _second_utility = two_utility_names()
        self.assertEqual(
            utility_names()[0],
            first_utility,
            "the catalogue's first member is the declared default of utilities.md §5, so "
            "a side naming none is that member: %r" % (utility_names(),),
        )
        entries = variant_entries(two_utility_configuration())
        self.assertEqual(
            as_text(entries[0]["utility"], "the first arm's declared utility"),
            first_utility,
            "the invented pair's first arm spells the catalogue's first member out, which "
            "is what makes the silent side below comparable with it (utilities.md §2, "
            "§5): %r" % (entries[0].get("utility"),),
        )
        silent = {
            key: value for key, value in entries[0].items() if key != "utility"
        }
        self.assertNotIn(
            "utility",
            silent,
            "this side declares no utility at all, which is the input utilities.md §5 "
            "gives one answer to: %r" % (sorted(silent),),
        )
        pair = self.result(silent, entries[0])
        axis = as_mapping(pair["axis"], "axis")
        self.assertEqual(
            as_text(axis["of"], "of"),
            "no difference",
            "a side leaving the default unsaid and a side spelling it out are one "
            "utility, so the pair differs on no axis at all — a phantom `utility` "
            "difference would be the raw-key comparison utilities.md §5 forbids "
            "(fairness.md §2, §7, D-20): %r" % (axis["of"],),
        )
        self.assertEqual(
            as_sequence(axis["differs"], "'differs'"),
            [],
            "nothing differs, so `differs` is empty and the axis is not named (fairness.md "
            "§2, utilities.md §5, D-20): %r" % (axis["differs"],),
        )
        constants = as_mapping(pair["constants"], "'constants'")
        self.assertEqual(
            utility_set(constants["utilities"]),
            {first_utility},
            "the silent side's utility is the catalogue's first, resolved through "
            "agents.learners() and never stood in for by a constant of this module "
            "(fairness.md §4, utilities.md §5, §8, D-20): %r" % (constants["utilities"],),
        )
        differing = self.result(silent, entries[1])
        self.assertEqual(
            as_text(as_mapping(differing["axis"], "axis")["of"], "of"),
            "utility",
            "the control: the same silent side against an arm declaring the catalogue's "
            "second utility is a real difference, so the silence is resolved to one "
            "member and not to whatever makes a pair agree (fairness.md §2, "
            "utilities.md §5, §8, D-20): %r" % (differing["axis"]["of"],),
        )

    def test_trn_7_12_the_reward_row_states_what_each_side_s_utility_delivers(self):
        """TRN-7.12 `constants['reward']` states the reward each side's utility delivers — both members' tokens for a two-utility pair, one for a pair of one objective — named for the member it belongs to and keeping its ASM-12 citation, because a comparison holds the **set** of rewards constant and never one side's (fairness.md §4, utilities.md §2, §8, ASM-12, D-20)."""
        first_utility, second_utility = two_utility_names()
        entries = variant_entries(two_utility_configuration())
        pair = self.result(entries[0], entries[1])
        row = as_text(
            as_mapping(pair["constants"], "'constants'")["reward"], "the reward row"
        )
        for utility in (first_utility, second_utility):
            with self.subTest(utility=utility):
                self.assertIn(
                    utility_reward(utility),
                    row,
                    "the row states the reward token the catalogue gives %r, so a reader "
                    "sees which arithmetic each arm's terminal transition carried "
                    "(utilities.md §2, §8, D-20): %r" % (utility, row),
                )
                self.assertIn(
                    utility,
                    row,
                    "the row says **whose** reward each statement is, so a two-utility "
                    "pair's row is two statements and not one (utilities.md §8, D-20): "
                    "%r" % (row,),
                )
        self.assertIn(
            "ASM-12",
            row,
            "the row keeps its ASM-12 citation, because the delivery rule the rewards "
            "share — the terminal decision, unshaped — is that assumption and not the "
            "utility (utilities.md §2, ASM-12, D-20): %r" % (row,),
        )
        control = as_mapping(
            self.result(entries[0], with_setting(entries[1], utility=first_utility)),
            "a fairness record of two entries declaring one utility",
        )
        one = as_text(
            as_mapping(control["constants"], "'constants'")["reward"], "the reward row"
        )
        self.assertIn(
            utility_reward(first_utility),
            one,
            "a pair of one objective states the one reward both arms delivered "
            "(fairness.md §4, utilities.md §8, D-20): %r" % (one,),
        )
        self.assertNotIn(
            utility_reward(second_utility),
            one,
            "and it states no second reward, because neither side named a second "
            "utility: a row holding both would report a difference the pair does not "
            "have (fairness.md §4, utilities.md §8, D-20): %r" % (one,),
        )
        self.assertIn(
            "ASM-12",
            one,
            "the one-utility row keeps the citation too (utilities.md §2, ASM-12): %r"
            % (one,),
        )

    def test_trn_7_13_a_pair_differing_on_the_utility_and_the_backend_is_refused(self):
        """TRN-7.13 two entries declaring two utilities **and** two backends differ on two axes and are refused as `MultipleAxes` naming both, because a reportable pair differs on one (fairness.md §2, §6, errors.md §2, §4, utilities.md §8, D-20)."""
        first_utility, second_utility = two_utility_names()
        entries = variant_entries(two_utility_configuration())
        doctored = with_setting(entries[1], backend="torch")
        self.assertEqual(
            as_text(entries[0]["utility"], "a declared utility"),
            first_utility,
            "the pair is the two-utility pair before the backend is doctored "
            "(utilities.md §2, D-20): %r" % (entries[0].get("utility"),),
        )
        self.assertEqual(
            as_text(doctored["utility"], "a declared utility"),
            second_utility,
            "and its second arm still declares the catalogue's second utility, so the two "
            "differences are both present (utilities.md §8, D-20): %r"
            % (doctored.get("utility"),),
        )
        self.assertNotEqual(
            as_text(entries[0]["backend"], "a declared backend"),
            as_text(doctored["backend"], "a declared backend"),
            "the doctored arm names another backend, which is the second axis "
            "(fairness.md §3, D-7): %r against %r"
            % (entries[0].get("backend"), doctored.get("backend")),
        )
        refused = self.refuse(
            lambda: training().fairness(entries[0], doctored),
            "MultipleAxes",
            groups=(("backend",), ("utility",)),
            label="fairness of a pair differing on the utility and the backend",
            entry="fairness",
        )
        for axis_name in ("backend", "utility"):
            self.assertIn(
                axis_name,
                str(refused),
                "the refusal names every axis the pair differs on — %r among them — so a "
                "reader can see which comparison the pair was not (fairness.md §6, "
                "utilities.md §8, D-20): %r" % (axis_name, str(refused)),
            )
        reported = self.result(entries[0], entries[1])
        self.assertEqual(
            as_text(as_mapping(reported["axis"], "axis")["of"], "of"),
            "utility",
            "the control: the same pair with one backend is reportable on the utility "
            "alone, so the refusal above is about the second axis and not about two "
            "utilities meeting (fairness.md §2, §6, utilities.md §8, D-20): %r"
            % (reported["axis"]["of"],),
        )

    # -- D-43: the counterfactual axis --------------------------------------
    def test_trn_7_14_two_counterfactual_members_are_the_axis_and_the_default_is_one_member(self):
        """TRN-7.14 two entries declaring the catalogue's two counterfactual members differ on the `counterfactual` axis — one word in both places, as the utility's is — and are **not** refused, while a side naming the catalogue's first and a side naming nothing are one member and no phantom difference; and the axis is the eighth and by no means one of the settings a pair must share (fairness.md §2, §4, §6, §7, declarations.md §4, counterfactual.md §6, D-43)."""
        first_member, second_member = two_counterfactual_names()
        self.assertEqual(
            counterfactual_names()[0],
            first_member,
            "the catalogue's first member is the declared default of counterfactual.md §6, "
            "so a side naming none is that member: %r" % (counterfactual_names(),),
        )
        self.assertNotIn(
            "counterfactual",
            self.internal("declarations", "PAIR_SETTINGS"),
            "the member is an axis and never a setting both arms must share: two arms of "
            "one pair declare two of them and both are trained (declarations.md §4, "
            "counterfactual.md §6, §9, D-43): %r"
            % (self.internal("declarations", "PAIR_SETTINGS"),),
        )
        entries = variant_entries(
            counterfactual_configuration(member=second_member)
        )
        declaring_second = entries[0]
        self.assertEqual(
            as_text(declaring_second["counterfactual"], "a declared member"),
            second_member,
            "the invented entry declares the catalogue's second member, which is what "
            "makes it differ from a side on the first (counterfactual.md §6, D-43): %r"
            % (declaring_second.get("counterfactual"),),
        )
        declaring_first = with_setting(
            declaring_second, counterfactual=first_member, name="variant-invented-5533"
        )
        silent = {
            key: value
            for key, value in declaring_first.items()
            if key != "counterfactual"
        }
        self.assertNotIn(
            "counterfactual",
            silent,
            "the silent side declares no member at all, which counterfactual.md §6 gives "
            "one answer to: %r" % (sorted(silent),),
        )
        pair = self.result(declaring_second, declaring_second)
        self.assertEqual(
            as_text(as_mapping(pair["axis"], "axis")["of"], "of"),
            "no difference",
            "one entry against itself differs on nothing, which is the control the two "
            "sides below are read against (fairness.md §2): %r" % (pair["axis"],),
        )
        report = self.result(declaring_first, declaring_second)
        axis = as_mapping(report["axis"], "axis")
        self.assertEqual(
            as_text(axis["of"], "of"),
            "counterfactual",
            "two training targets are the `counterfactual` axis D-43 added beside the "
            "seven, and the pair is reportable rather than refused "
            "(counterfactual.md §6, D-43): %r" % (axis,),
        )
        self.assertEqual(
            {
                as_text(field, "a differing field")
                for field in as_sequence(axis["differs"], "'differs'")
            },
            {"counterfactual"},
            "`differs` names the field that differs, and it is `counterfactual` — **one "
            "word**, the axis token and the field name being the same, unlike the rule's "
            "pairing of the token `rule` with the field `learning_rule` "
            "(counterfactual.md §6, D-43): %r" % (axis["differs"],),
        )
        self.assertIsNone(
            axis["declared"],
            "for two entries `declared` is None, there being no configuration's axis "
            "sentence to quote (fairness.md §2)",
        )
        same = self.result(silent, declaring_first)
        self.assertEqual(
            as_text(as_mapping(same["axis"], "axis")["of"], "of"),
            "no difference",
            "a side leaving the default unsaid against a side spelling it out is one "
            "member resolved through the catalogue, so nothing differs — a phantom "
            "`counterfactual` difference would be the raw-key comparison "
            "counterfactual.md §6 forbids (fairness.md §2, §7, D-43): %r"
            % (same["axis"],),
        )
        self.assertEqual(
            as_sequence(as_mapping(same["axis"], "axis")["differs"], "'differs'"),
            [],
            "nothing differs, so `differs` is empty (fairness.md §2, counterfactual.md "
            "§6): %r" % (same["axis"]["differs"],),
        )


if __name__ == "__main__":
    unittest.main()
