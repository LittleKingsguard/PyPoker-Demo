"""TRN-9 — refusals: the fifteen classes, one message each.

Drives `docs/L3/training/errors.md` §1-§4, `docs/L2/training/surface.md` §1-§5 and
`docs/L3/training/loop.md` §6: every row of `errors.md` §4's canonical-message table, the
class `§2` names for it, the base `TrainingError` a caller catches, and — `§3`'s first
rule — the offending value in the message. A refused call has no observable effect:
`TRN-9.14` asserts a refused `run` deals no hand and writes no file (`errors.md`
§1, `e2e-surface.md` §2).

Rev 2 adds this module's two declaration refusals (`docs/L2/training/declarations.md`
§2-§4): `TRN-9.15` drives `IgnoredDeclaration`'s seven shapes and the two blocks that are
no claim, and `TRN-9.16` the five settings §4 has `PairDeclarationsDiffer` refuse at
`run` — the other two of the seven, `hyper` and `snapshot_every`, are refused earlier and
per arm by `IgnoredDeclaration`, so the pair class is unreachable for them, and a pair
`fairness` is asked to hold constant is `TRN-7.8`'s, in `test_fairness.py`, because
`fairness` owns that message. Rev 3 adds `TRN-9.17`: a `learning_rule` the catalogue does
not carry is judged before the pool is built, so a run refused for its rule freezes no
membership and deals no hand (`rules.md` §4, D-19).

The instances are the battery's: an invented rung name, an invented device, an invented
backend, encoding and kind, a seed and a budget no design document carries
(`battery.md` §4). The three refusals that are not this module's — an unknown encoding, an
unknown backend or kind and a pool declaration its owner refuses — are exercised here as
`VariantSettingInvalid`, because `surface.md` §4.2 (Rev 2) makes a run refuse them
against this module's own declaration of the two backends, two encodings and seven kinds,
naming the value.
"""

import random
import unittest

from _training_support import (
    CONFIGURATION_INTERVAL,
    HYPER,
    IGNORED_HYPER_KEY,
    IGNORED_HYPER_VALUE,
    IGNORED_INTERVAL,
    IGNORED_RATE,
    IGNORED_RULE,
    IGNORED_SCHEDULE,
    INVENTED_CUSTOM,
    INVENTED_DEVICE,
    INVENTED_PAIR_LEFT,
    INVENTED_PAIR_RIGHT,
    INVENTED_PAIR_RUNG,
    INVENTED_POOL_A,
    INVENTED_POOL_B,
    INVENTED_RUNG,
    INVENTED_SECOND_BUDGET,
    INVENTED_VARIANT,
    PAIR_SAMPLES,
    PARAM_BUDGET,
    REFUSED_SEED,
    RUN_SEED,
    RUNG_NAMES,
    SNAPSHOTS,
    SPREAD_SEED,
    TINY_BUDGET,
    TrainingCase,
    as_mapping,
    as_sequence,
    as_text,
    checkpoint_tree,
    custom_configuration,
    custom_run,
    error_class,
    error_root,
    paths_mentioning,
    training,
    two_rule_names,
    variant_entries,
    with_architecture,
    with_pool,
    with_setting,
    write_tree,
)


class RefusalTest(TrainingCase):
    def config(self):
        """R1's configuration, the base the invented refusals are built from."""
        return training().rung("R1")

    def entry(self, rung_name="R1", variant=None):
        configuration = training().rung(rung_name)
        entries = as_sequence(configuration["variants"], "'variants'")
        if variant is None:
            return entries[0]
        for entry in entries:
            if entry.get("name") == variant:
                return entry
        raise AssertionError("rung %r declares no variant %r" % (rung_name, variant))

    def test_trn_9_1_unknown_rung_names_the_name(self):
        """TRN-9.1 an unknown rung name is `UnknownRung`, a `TrainingError`, and the message names the name and the six the registry carries (errors.md §2, §4, registry.md §5, FAM-15.5, FAM-16.28)."""
        self.refuse(
            lambda: training().rung(INVENTED_RUNG),
            "UnknownRung",
            groups=((INVENTED_RUNG,), tuple(RUNG_NAMES)),
            label="rung(%r)" % (INVENTED_RUNG,),
        )
        self.refuse(
            lambda: training().run(INVENTED_RUNG),
            "UnknownRung",
            groups=((INVENTED_RUNG,),),
            label="run(%r)" % (INVENTED_RUNG,),
        )

    def test_trn_9_2_configuration_invalid_names_the_value(self):
        """TRN-9.2 a `rung` argument that is neither a name nor a mapping is `ConfigurationInvalid`, and the message names the value it was given (errors.md §2, §4, loop.md §6, surface.md §4)."""
        for value in (5517, None, ["R1"]):
            with self.subTest(value=repr(value)):
                label = str(value) if value is not None else "None"
                self.refuse(
                    lambda: training().run(value),
                    "ConfigurationInvalid",
                    groups=((label, "None"),),
                    label="run(%r)" % (value,),
                )

    def test_trn_9_3_missing_configuration_key_names_the_key(self):
        """TRN-9.3 a configuration carrying none of the places `loop.md` §5 looks for a seed set, a budget or the pool is `MissingConfigurationKey`, naming the key it looked for (errors.md §2, §4, loop.md §5-§6)."""
        no_seeds = custom_configuration()
        del no_seeds["seeds"]
        for entry in no_seeds["variants"]:
            del entry["seeds"]
        self.refuse(
            lambda: training().run(no_seeds),
            "MissingConfigurationKey",
            groups=(("seed",),),
            label="run of a configuration declaring no seed set",
        )
        no_samples = custom_configuration()
        del no_samples["samples"]
        for entry in no_samples["variants"]:
            del entry["samples"]
        self.refuse(
            lambda: training().run(no_samples, seeds=(RUN_SEED,)),
            "MissingConfigurationKey",
            groups=(("sample",),),
            label="run of a configuration declaring no budget",
        )
        no_pool = custom_configuration()
        del no_pool["pool"]
        self.refuse(
            lambda: training().run(no_pool),
            "MissingConfigurationKey",
            groups=(("pool",),),
            label="run of a configuration declaring no pool",
        )

    def test_trn_9_4_variant_count_invalid_names_the_count(self):
        """TRN-9.4 a configuration declaring zero, three or more variant entries is `VariantCountInvalid`, and the message names the count it found (errors.md §2, §4, ladder.md §2, surface.md §4)."""
        entry = self.entry()
        for count in (0, 3):
            with self.subTest(count=count):
                configuration = custom_configuration()
                configuration["variants"] = [dict(entry) for _ in range(count)]
                self.refuse(
                    lambda: training().run(configuration),
                    "VariantCountInvalid",
                    groups=((str(count),),),
                    label="run of a configuration declaring %d variants" % (count,),
                )

    def test_trn_9_5_variant_setting_invalid_names_the_setting(self):
        """TRN-9.5 a backend, encoding or kind this module does not declare, a width or depth that is not a positive integer and a sparsity outside `[0, 1]` are all `VariantSettingInvalid`, naming the setting and its value (errors.md §2, §4, loop.md §6, surface.md §4.2)."""
        base = self.entry()
        cases = (
            ("an unknown backend", with_setting(base, backend="theano-5517"), ("theano-5517",)),
            ("an unknown encoding", with_setting(base, encoding="hashed-5517"), ("hashed-5517",)),
            (
                "an unknown kind",
                with_architecture(base, kind="transformer-5517"),
                ("transformer-5517",),
            ),
            ("a zero width", with_architecture(base, width=0), ("width", "0")),
            ("a negative depth", with_architecture(base, depth=-2), ("depth", "-2")),
            ("a sparsity above one", with_architecture(base, sparsity=1.5), ("sparsity", "1.5")),
            ("a negative sparsity", with_architecture(base, sparsity=-0.5), ("sparsity", "-0.5")),
        )
        for label, entry, groups in cases:
            with self.subTest(setting=label):
                configuration = custom_configuration()
                configuration["variants"] = [entry]
                self.refuse(
                    lambda: training().run(configuration),
                    "VariantSettingInvalid",
                    groups=groups,
                    label="run with %s" % (label,),
                )

    def test_trn_9_6_invalid_seeds_names_the_set(self):
        """TRN-9.6 a seed set that is empty, repeats a seed or holds a non-integer is `InvalidSeeds`, and the message names the set (errors.md §2, §4, ASM-2, surface.md §4)."""
        cases = (
            ("an empty set", (), "a run needs at least one distinct integer seed", "[]"),
            ("a repeated seed", (7, 7), "the seeds must be distinct integers", "7"),
            ("a non-integer seed", ("x",), "the seeds must be distinct integers", "x"),
        )
        for label, seeds, contract, token in cases:
            with self.subTest(seed_set=label):
                self.refuse(
                    lambda: training().run("R1", seeds=seeds, budget=TINY_BUDGET),
                    "InvalidSeeds",
                    groups=((token,), (contract,)),
                    label="run with %s" % (label,),
                )

    def test_trn_9_7_invalid_budget_names_the_budget(self):
        """TRN-9.7 a budget that is not a positive integer, or is below ten hands, is `InvalidBudget`, naming the budget (errors.md §2, §4, loop.md §6, ASM-18, surface.md §4)."""
        for budget, contract in (
            (0, "positive"),
            (-5, "positive"),
            (9, "ten"),
        ):
            with self.subTest(budget=budget):
                self.refuse(
                    lambda: training().run("R1", seeds=(RUN_SEED,), budget=budget),
                    "InvalidBudget",
                    groups=((str(budget),), (contract,)),
                    label="run at a budget of %r" % (budget,),
                )

    def test_trn_9_8_unknown_device_names_the_device(self):
        """TRN-9.8 a named device `devices()` does not list is `UnknownDevice`, naming the device and the catalogue (errors.md §2, §4, devices.md §3, D-8)."""
        self.refuse(
            lambda: training().run(
                "R1", seeds=(RUN_SEED,), budget=TINY_BUDGET, device=INVENTED_DEVICE
            ),
            "UnknownDevice",
            groups=((INVENTED_DEVICE,), ("cpu",)),
            label="run at %r" % (INVENTED_DEVICE,),
        )

    def test_trn_9_9_not_a_comparison_side_names_the_side(self):
        """TRN-9.9 a rung *name* is not a comparison side, and `NotAComparisonSide` names what it saw: a side is a configuration or a variant entry and never a lookup (errors.md §2, §4, fairness.md §1, §6)."""
        self.refuse(
            lambda: training().fairness(RUNG_NAMES[0], RUNG_NAMES[1]),
            "NotAComparisonSide",
            groups=((RUNG_NAMES[0],), ("side", "configuration", "entry", "architecture")),
            label="fairness(%r, %r)" % (RUNG_NAMES[0], RUNG_NAMES[1]),
        )

    def test_trn_9_10_side_kind_mismatch_names_both_kinds(self):
        """TRN-9.10 two sides of different kinds are `SideKindMismatch`, and the message says which side is which (errors.md §2, §4, fairness.md §1, §6)."""
        self.refuse(
            lambda: training().fairness(self.config(), self.entry()),
            "SideKindMismatch",
            groups=(("configuration",), ("entry",), ("left", "right")),
            label="fairness of a configuration and an entry",
        )

    def test_trn_9_11_comparison_key_missing_names_the_key(self):
        """TRN-9.11 a side missing a key the comparison reads — `architecture`, `backend` or `pool` — is `ComparisonKeyMissing`, naming the key (errors.md §2, §4, fairness.md §6, §8)."""
        stripped = dict(self.config())
        stripped["variants"] = [
            {key: value for key, value in entry.items() if key != "architecture"}
            for entry in as_sequence(stripped["variants"], "'variants'")
        ]
        self.refuse(
            lambda: training().fairness(stripped, self.config()),
            "ComparisonKeyMissing",
            groups=(("architecture",),),
            label="fairness of a configuration whose entries carry no architecture",
        )
        entry = self.entry()
        self.refuse(
            lambda: training().fairness(
                {key: value for key, value in entry.items() if key != "backend"}, entry
            ),
            "ComparisonKeyMissing",
            groups=(("backend",),),
            label="fairness of an entry carrying no backend",
        )
        without_pool = dict(self.config())
        del without_pool["pool"]
        self.refuse(
            lambda: training().fairness(without_pool, self.config()),
            "ComparisonKeyMissing",
            groups=(("pool",),),
            label="fairness of a configuration carrying no pool",
        )

    def test_trn_9_12_multiple_axes_names_every_axis(self):
        """TRN-9.12 a pair whose differences fall in more than one axis is `MultipleAxes`, and **every** axis is named, in `fairness.md` §2's table order (errors.md §2, §4, fairness.md §6, FAM-3.12)."""
        dense = self.entry("R5", "dense")
        sparse = with_setting(self.entry("R5", "sparse"), encoding="flat-numeric")
        self.refuse(
            lambda: training().fairness(dense, sparse),
            "MultipleAxes",
            groups=(("encoding",), ("connectivity",)),
            label="fairness of a pair differing on encoding and connectivity",
        )

    def test_trn_9_13_pool_ids_differ_names_both_ids(self):
        """TRN-9.13 two variants of one configuration declaring two pool ids are `PoolIdsDiffer`, and both ids are named, because both arms train against one frozen pool (errors.md §2, §4, fairness.md §6, ASM-16)."""
        self.refuse(
            lambda: training().fairness(
                with_pool(self.entry("R6", "residual"), INVENTED_POOL_A),
                with_pool(self.entry("R6", "plain"), INVENTED_POOL_B),
            ),
            "PoolIdsDiffer",
            groups=((INVENTED_POOL_A,), (INVENTED_POOL_B,)),
            label="fairness of two variants declaring two pool ids",
        )

    def test_trn_9_14_a_refused_run_deals_no_hand_and_writes_no_file(self):
        """TRN-9.14 a refused run is refused before the first hand is dealt and before anything is written: the global stream is where it was and no artefact appears (errors.md §1, loop.md §6, e2e-surface.md §2, ASM-2)."""
        before_tree = checkpoint_tree()
        before_write = write_tree()
        before_stream = random.getstate()
        before_refused = paths_mentioning("seed-%d" % (REFUSED_SEED,), before_tree)
        self.assertEqual(
            before_refused,
            [],
            "the invented seed names no artefact before the refused run, so the check "
            "below is about the refusal and not about an earlier run",
        )
        self.assertEqual(
            paths_mentioning("seed-%d" % (REFUSED_SEED,), before_write),
            [],
            "the invented seed names no artefact under the write root before the "
            "refused run either, and that is where a battery's runs write (docs/L2/"
            "training/write-root.md §1, §3), so the check below is about the refusal "
            "and not about an earlier run: %r"
            % (paths_mentioning("seed-%d" % (REFUSED_SEED,), before_write),),
        )
        self.refuse(
            lambda: training().run("R1", seeds=(REFUSED_SEED,), budget=9),
            "InvalidBudget",
            groups=(("9",),),
            label="run at a budget of nine hands",
        )
        self.assert_no_hand_dealt(before_stream, "a refused run")
        self.assert_tree_untouched(before_tree, "a refused run")
        self.assertEqual(
            paths_mentioning("seed-%d" % (REFUSED_SEED,)),
            [],
            "a refused run writes no snapshot and no final model at the seed it was "
            "given (errors.md §1, loop.md §6, e2e-surface.md §2)",
        )
        self.assertEqual(
            [path for path in write_tree() if path not in before_write],
            [],
            "a refused run writes no file under the write root either, and that is the "
            "tree a battery's run writes: the shipped tree is empty of a run's files by "
            "construction, so this is the assertion that could still fail (errors.md "
            "§1, loop.md §6, docs/L2/training/write-root.md §1, §3): %r"
            % ([path for path in write_tree() if path not in before_write],),
        )
        self.assertEqual(
            paths_mentioning("seed-%d" % (REFUSED_SEED,), write_tree()),
            [],
            "a refused run writes nothing at the refused seed under the write root "
            "either, where a run's artefacts would land (errors.md §1, loop.md §6, "
            "docs/L2/training/write-root.md §1, §3): %r"
            % (paths_mentioning("seed-%d" % (REFUSED_SEED,), write_tree()),),
        )

    def configuration_with(self, **settings):
        """The invented configuration with its one entry's settings replaced."""
        body = dict(custom_configuration())
        body["variants"] = [with_setting(variant_entries(body)[0], **settings)]
        return body

    def test_trn_9_15_ignored_declaration_names_the_declared_and_the_used_value(self):
        """TRN-9.15 a `learning_rate` the declaration does not carry, an `exploration` written as a sentence, an unknown `hyper` key, a `learning_rule` the catalogue does not carry and a `snapshot_every` off the declared budget ÷ 10 at either level are each `IgnoredDeclaration`, naming the entry, the configuration, the key, the value declared **and** the catalogue or value the run uses; a block that equals the declaration and one that names neither key at all are no claim and are not refused, and the two rules a `learning_rule` is judged against are the catalogue's own, read from `agents.learners()` (declarations.md §2-§3, errors.md §2, §4, loop.md §1 step 1, §2, ASM-7, ASM-18, D-19)."""
        first_rule, second_rule = two_rule_names()
        interval = "the interval the declared %d samples fix, %d" % (
            TINY_BUDGET,
            TINY_BUDGET // SNAPSHOTS,
        )
        shapes = (
            (
                "a learning_rate the declaration does not carry",
                self.configuration_with(
                    hyper=dict(HYPER, learning_rate=IGNORED_RATE)
                ),
                (
                    (str(IGNORED_RATE),),
                    (str(HYPER["learning_rate"]),),
                    ("learning_rate",),
                    (INVENTED_VARIANT,),
                    (INVENTED_CUSTOM,),
                    ("declarations.py",),
                ),
            ),
            (
                "an exploration written where the schedule record is declared",
                self.configuration_with(
                    hyper=dict(HYPER, exploration=IGNORED_SCHEDULE)
                ),
                (
                    (IGNORED_SCHEDULE,),
                    ("'start': 1.0",),
                    ("2000",),
                    ("exploration",),
                    (INVENTED_VARIANT,),
                    (INVENTED_CUSTOM,),
                    ("declarations.py",),
                ),
            ),
            (
                "a hyper key the declaration does not carry",
                self.configuration_with(
                    hyper=dict(HYPER, **{IGNORED_HYPER_KEY: IGNORED_HYPER_VALUE})
                ),
                # `errors.md` §4 fixes this shape's tokens — the key, its own value and the
                # six names `HYPER` carries — and not the wording of the clause between
                # them, so no phrase of that clause is pinned here.
                (
                    (IGNORED_HYPER_KEY,),
                    (str(IGNORED_HYPER_VALUE),),
                    ("learning_rate",),
                    ("batch_size",),
                    ("target_update_interval",),
                    ("optimiser",),
                    ("exploration",),
                    ("discount",),
                    (INVENTED_VARIANT,),
                    (INVENTED_CUSTOM,),
                    ("declarations.py",),
                ),
            ),
            (
                "a learning_rule the catalogue does not carry",
                self.configuration_with(learning_rule=IGNORED_RULE),
                (
                    (IGNORED_RULE,),
                    ("learning_rule",),
                    (INVENTED_VARIANT,),
                    (INVENTED_CUSTOM,),
                    (first_rule,),
                    (second_rule,),
                    ("agents.learners()", "catalogue"),
                ),
            ),
            (
                "an entry-level snapshot_every off the declared interval",
                self.configuration_with(snapshot_every=IGNORED_INTERVAL),
                (
                    (str(IGNORED_INTERVAL),),
                    (interval,),
                    ("snapshot_every",),
                    (INVENTED_VARIANT,),
                    (INVENTED_CUSTOM,),
                    ("declarations.py",),
                ),
            ),
        )
        for label, configuration, groups in shapes:
            with self.subTest(declaration=label):
                self.refuse(
                    lambda: training().run(configuration),
                    "IgnoredDeclaration",
                    groups=groups,
                    label="run with %s" % (label,),
                )
        overridden = self.configuration_with()
        overridden["snapshot_every"] = CONFIGURATION_INTERVAL
        with self.subTest(declaration="a configuration-level snapshot_every"):
            self.refuse(
                lambda: training().run(overridden),
                "IgnoredDeclaration",
                groups=(
                    (str(CONFIGURATION_INTERVAL),),
                    (interval,),
                    ("snapshot_every",),
                    (INVENTED_CUSTOM,),
                    ("declarations.py",),
                ),
                label="run with a configuration-level snapshot_every off the interval",
            )

        own_rule = dict(custom_configuration())
        own_rule["learning_rule"] = IGNORED_RULE
        with self.subTest(declaration="a configuration-level learning_rule"):
            self.refuse(
                lambda: training().run(own_rule),
                "IgnoredDeclaration",
                groups=(
                    (IGNORED_RULE,),
                    ("learning_rule",),
                    (INVENTED_CUSTOM,),
                    (first_rule,),
                    (second_rule,),
                    ("agents.learners()", "catalogue"),
                ),
                label="run with a configuration-level learning_rule off the catalogue",
            )

        accepted = as_mapping(custom_run(), "a run record of the invented configuration")
        self.assertEqual(
            as_text(accepted["rung"], "rung"),
            INVENTED_CUSTOM,
            "a block that carries the declared `hyper` and a catalogued `learning_rule` is "
            "accepted and the run returns its record, so what is refused is an uncatalogued "
            "name and never a rule the run is not fixed to (declarations.md §2, rules.md §2, "
            "§4, D-19): %r" % (accepted["rung"],),
        )
        bare = self.configuration_with()
        del bare["variants"][0]["hyper"]
        del bare["variants"][0]["learning_rule"]
        with self.subTest(declaration="no hyper and no learning_rule at all"):
            self._reaches_the_pool(bare, "a configuration naming neither key")
        partial = self.configuration_with(
            hyper={key: HYPER[key] for key in ("learning_rate",)}
        )
        with self.subTest(declaration="a hyper naming one key at its declared value"):
            self._reaches_the_pool(
                partial, "a configuration whose hyper names one declared key"
            )
        disagreeing = dict(bare)
        disagreeing["variants"] = [
            with_setting(bare["variants"][0], hyper=dict(HYPER, learning_rate=IGNORED_RATE))
        ]
        with self.subTest(declaration="the same shape with one disagreeing key"):
            self.refuse(
                lambda: training().run(disagreeing),
                "IgnoredDeclaration",
                groups=((str(IGNORED_RATE),), ("learning_rate",)),
                label="run of the same configuration with a disagreeing learning_rate",
            )

    def _reaches_the_pool(self, configuration, label):
        """Assert a run gets past step 1's declaration checks to the pool's refusal.

        The case injects one defect: a membership bound above the league's M, which
        `docs/L3/training/loop.md` §6 has the pool's owner refuse in its **own** class at
        step 2 — after step 1 has refused everything it would refuse, and therefore only
        once this configuration's absent `hyper` and `learning_rule` were accepted as no
        claim. That is what keeps the negative half off a real run without making it
        vacuous: were the block refused, the refusal would be this module's, and the
        assertions below would see it (declarations.md §2, loop.md §1 step 1-2, §2).
        """
        body = dict(configuration)
        body["pool"] = dict(configuration["pool"], m=6)
        try:
            value = training().run(body)
        except Exception as exc:
            self.assertNotIsInstance(
                exc,
                error_class("IgnoredDeclaration"),
                "%s names no `hyper` key and no `learning_rule` the run would discard, so "
                "it is no claim and is not refused as an ignored declaration "
                "(declarations.md §2, loop.md §2): %r" % (label, exc),
            )
            self.assertNotIsInstance(
                exc,
                error_root(),
                "%s must reach the pool and be refused there, and the pool's refusal "
                "propagates in its owner's class rather than this module's (loop.md §1 "
                "step 2, §6): %r" % (label, exc),
            )
            return exc
        self.fail(
            "%s was accepted, and the injected membership bound above the league's M is "
            "refused at step 2, so the run cannot have returned a record (loop.md §6): %r"
            % (label, value)
        )

    def test_trn_9_16_pair_declarations_differ_names_both_values(self):
        """TRN-9.16 a two-entry configuration whose arms declare two `samples`, two `seeds`, two `device`, two `table` or two `param_budget` values — the five of §4's seven settings this class refuses — is `PairDeclarationsDiffer`, and the message names the key and both arms' declared values in declaration order; `hyper` and `snapshot_every` never reach this class, because each is refused earlier and per arm by `IgnoredDeclaration` (TRN-9.15), the pair class being unreachable for them, and the two `hyper` blocks `fairness` is asked to hold constant are `TRN-7.8`'s in `test_fairness.py` (declarations.md §4, errors.md §2, §4, loop.md §1 step 1, §6, ASM-7, ASM-8, ASM-16)."""
        left = with_setting(variant_entries(custom_configuration())[0], name=INVENTED_PAIR_LEFT)
        catalogue = as_mapping(training().devices(), "the device catalogue")
        available = [
            as_text(name, "a device name")
            for name in as_sequence(catalogue["available"], "'available'")
        ]
        shared_device = as_text(catalogue["default"], "'default'")
        # A device name is read from the catalogue and never invented (`devices.md` §1, §3):
        # the pair's second declaration is the first name `available` lists beside the
        # shared one, and `available` is `['cpu']` on every platform by Rev 3 — a reachable
        # GPU adds no name — so on this platform the second value is the battery's invented
        # device, which names a device in no design document (`battery.md` §4).
        second_device = next(
            (name for name in available if name != shared_device), INVENTED_DEVICE
        )
        shapes = (
            (
                "two sample budgets",
                with_setting(left, samples=TINY_BUDGET),
                with_setting(left, name=INVENTED_PAIR_RIGHT, samples=PAIR_SAMPLES),
                (
                    ("samples",),
                    ("%d and %d" % (TINY_BUDGET, PAIR_SAMPLES),),
                    (str(TINY_BUDGET),),
                    (str(PAIR_SAMPLES),),
                ),
            ),
            (
                "two seed sets",
                with_setting(left, seeds=[RUN_SEED]),
                with_setting(left, name=INVENTED_PAIR_RIGHT, seeds=[SPREAD_SEED]),
                (
                    ("seeds",),
                    (
                        "%d and %d" % (RUN_SEED, SPREAD_SEED),
                        "[%d] and [%d]" % (RUN_SEED, SPREAD_SEED),
                    ),
                    (str(RUN_SEED),),
                    (str(SPREAD_SEED),),
                ),
            ),
            (
                "two devices",
                with_setting(left, device=shared_device),
                with_setting(left, name=INVENTED_PAIR_RIGHT, device=second_device),
                (
                    ("device",),
                    ("%r and %r" % (shared_device, second_device),),
                    (shared_device,),
                    (second_device,),
                ),
            ),
            (
                "two table budgets",
                with_setting(left, table="live"),
                with_setting(left, name=INVENTED_PAIR_RIGHT, table="full"),
                (("table",), ("'live' and 'full'",)),
            ),
            (
                "two parameter budgets",
                with_setting(left, param_budget=PARAM_BUDGET),
                with_setting(
                    left, name=INVENTED_PAIR_RIGHT, param_budget=INVENTED_SECOND_BUDGET
                ),
                (
                    ("param_budget",),
                    ("%d and %d" % (PARAM_BUDGET, INVENTED_SECOND_BUDGET),),
                ),
            ),
        )
        for label, first, second, groups in shapes:
            with self.subTest(declaration=label):
                configuration = custom_configuration(name=INVENTED_PAIR_RUNG)
                configuration["variants"] = [first, second]
                self.refuse(
                    lambda: training().run(configuration),
                    "PairDeclarationsDiffer",
                    groups=groups
                    + (
                        (INVENTED_PAIR_LEFT,),
                        (INVENTED_PAIR_RIGHT,),
                        (INVENTED_PAIR_RUNG,),
                    ),
                    label="run of a pair declaring %s" % (label,),
                )

    def test_trn_9_17_an_uncatalogued_rule_is_refused_before_the_pool_is_built(self):
        """TRN-9.17 a configuration whose variant names a rule off the catalogue **and** whose pool declaration its owner would refuse is refused as `IgnoredDeclaration` naming the rule — so the declaration is judged at step 1, before the pool is frozen, before a learner is built and before the first hand is dealt — and the refusal raises no hand (declarations.md §2-§3, loop.md §1 steps 1-2, §6, errors.md §1-§2, rules.md §4, D-19)."""
        body = custom_configuration()
        body["variants"][0]["learning_rule"] = IGNORED_RULE
        # A bound above the league's M = 5 is `build_pool`'s own refusal (`loop.md` §6): if
        # the declaration were judged after the pool, this run would raise that class.
        body["pool"] = dict(body["pool"], m=6)
        before = random.getstate()
        self.refuse(
            lambda: training().run(body),
            "IgnoredDeclaration",
            groups=(
                (IGNORED_RULE,),
                ("learning_rule",),
                (INVENTED_CUSTOM,),
                (INVENTED_VARIANT,),
            ),
            label="run naming an uncatalogued rule beside a pool its owner refuses",
        )
        self.assert_no_hand_dealt(
            before, "a run refused for the rule its variant declares"
        )


if __name__ == "__main__":
    unittest.main()
