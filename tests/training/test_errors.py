"""TRN-9 — refusals: the fourteen classes, one message each.

Drives `docs/L3/training/errors.md` §1-§4, `docs/L2/training/surface.md` §1-§5 and
`docs/L3/training/loop.md` §6: every row of `errors.md` §4's canonical-message table, the
class `§2` names for it, the base `TrainingError` a caller catches, and — `§3`'s first
rule — the offending value in the message. A refused call has no observable effect: the
last case asserts a refused `run` deals no hand and writes no file (`errors.md` §1,
`e2e-surface.md` §2).

The instances are the battery's: an invented rung name, an invented device, an invented
backend, encoding and kind, and a seed and a budget no design document carries
(`battery.md` §4). The three refusals that are not this module's — an unknown encoding, an
unknown backend or kind and a pool declaration its owner refuses — are exercised here as
`VariantSettingInvalid`, because `surface.md` §4.2 (Rev 2) makes a run refuse them
against this module's own declaration of the two backends, two encodings and seven kinds,
naming the value.
"""

import random
import unittest

from _training_support import (
    INVENTED_DEVICE,
    INVENTED_POOL_A,
    INVENTED_POOL_B,
    INVENTED_RUNG,
    REFUSED_SEED,
    RUN_SEED,
    RUNG_NAMES,
    TINY_BUDGET,
    TrainingCase,
    as_sequence,
    checkpoint_tree,
    custom_configuration,
    paths_mentioning,
    training,
    with_architecture,
    with_pool,
    with_setting,
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
        before_stream = random.getstate()
        before_refused = paths_mentioning("seed-%d" % (REFUSED_SEED,), before_tree)
        self.assertEqual(
            before_refused,
            [],
            "the invented seed names no artefact before the refused run, so the check "
            "below is about the refusal and not about an earlier run",
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


if __name__ == "__main__":
    unittest.main()
