"""TRN-7 — what a comparison holds constant: `fairness(left, right)`.

Drives `docs/L3/training/fairness.md` §1-§7 and `docs/L2/training/surface.md` §5 (Rev 2,
§5.1's axis rule included): the eight reportable pairs and their one axis each, the
`{of, differs, declared}` reading for two configurations and for two variant entries, the
thirteen `constants` keys — the game and the pool among them — the pool report's six keys
with `same` and the intersection for an adjacent pair, and the five refusals.

Reportability is `§2`'s correction and not a restatement: `architecture` is compared only
where the two sides agree on the representation family and on `sparsity`, so R5's `sparse`
(62 wide) against its `dense` (50 wide) differs on `sparsity` alone (ASM-10, guardrails
G14). `fairness` plays no hand, builds no learner, writes nothing and moves no stream
(§7, G19), and the last case proves it by patching every route it could have taken.
"""

import unittest

from _training_support import (
    ADJACENT_PAIRS,
    CONSTANT_KEYS,
    ENTRY_PAIRS,
    HYPER,
    INVENTED_POOL_A,
    INVENTED_POOL_B,
    INVENTED_PAIR_POOL,
    LEARNING_RULE,
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
    engine,
    entry_of,
    error_class,
    member_ids,
    training,
    variant_entries,
    with_pool,
    with_setting,
    write_tree,
)

#: `fairness.md` §4's `readout facts`, the ten fact names every encoding carries.
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
        """TRN-7.4 `constants` carries `fairness.md` §4's thirteen keys, with `game` equal to `engine.game_config()`, a `pool` report repeated inside it, and the vocabulary and readout facts declared as data (fairness.md §4, guardrails G15, FAM-3.14, FAM-13.3)."""
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
            "the ten readout facts are declared here for the same reason, identical for "
            "every encoding (fairness.md §4, D-3): %r" % (constants["readout facts"],),
        )
        self.assertEqual(
            as_text(constants["learning rule"], "learning rule"),
            LEARNING_RULE,
            "the ladder declares one rule (fairness.md §4, ASM-7)",
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
            baseline_names(),
            "the three baselines are reported in agents.baselines()'s order "
            "(fairness.md §5, records.md §8)",
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
            baseline_names(),
            "`membership` is the intersection of the two windows in lineage order, which "
            "for R1-R2 is the three baselines alone — the pool the parity check plays on "
            "(fairness.md §5, D-7): %r" % (report["membership"],),
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


if __name__ == "__main__":
    unittest.main()
