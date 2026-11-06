"""TRN-1 — the registry as data: `rungs()`, `rung(name)`.

Drives `docs/L3/training/registry.md` §1-§5 and `docs/L2/training/surface.md` §2-§3: the
six names in brief §2's order, the nine variants as literals, the resolved
configuration's twelve keys, the six `axis` sentences, the pool entry and the read-back
id, and the arithmetic that proves the literals are ASM-10's — nine counts inside
10,000 ± 2% and four comparison pairs matched within it.

Resolving is not training (`registry.md` §2, guardrails G19): the last case patches every
route a write or a deal could take and asserts none was taken, because `rung` builds no
learner, plays no hand, writes no file and moves no stream (D-3, ASM-2).
"""

import unittest

from _training_support import (
    ARCHITECTURE,
    AXES,
    AXIS_LABELS,
    BACKEND,
    CARRIED_FROM,
    ENCODING,
    HYPER,
    INVENTED_RUNG,
    LEARNING_RULE,
    PARAM_BUDGET,
    PARAM_COUNT,
    PARAM_TOLERANCE,
    PRIMARY,
    RETAINED,
    RUNG_NAMES,
    SHARED,
    SIX_NAMES,
    TrainingCase,
    VARIANTS,
    agents,
    architecture_of,
    as_float,
    as_int,
    as_mapping,
    as_sequence,
    as_text,
    checkpoint_tree,
    engine,
    error_class,
    evaluation,
    member_ids,
    param_count_of,
    training,
    variant_entries,
    variant_name,
)

#: `registry.md` §2's twelve keys of a resolved configuration, and no other.
CONFIGURATION_KEYS = {
    "name",
    "axis",
    "carried_from",
    "primary",
    "variants",
    "pool",
    "seeds",
    "samples",
    "param_budget",
    "table",
    "device",
    "snapshot_every",
}

#: `registry.md` §2's keys of one variant entry (`records.md` §2's shape).
ENTRY_KEYS = {
    "name",
    "backend",
    "encoding",
    "architecture",
    "learning_rule",
    "hyper",
    "param_budget",
    "samples",
    "seeds",
    "device",
    "snapshot_every",
    "table",
}

#: The four comparison pairs ASM-10 matches, and `registry.md` §4's own differences.
COMPARISON_PAIRS = (
    ("R1", "naive-numeric", "R2", "naive-numeric-torch"),
    ("R4", "wide", "R4", "deep"),
    ("R5", "dense", "R5", "sparse"),
    ("R6", "residual", "R6", "plain"),
)


class RegistryTest(TrainingCase):
    def test_trn_1_1_six_names_in_brief_order_and_the_surface_is_six(self):
        """TRN-1.1 `rungs()` declares R1..R6 in brief §2's order, twice alike, and the package exports exactly the six entry points in `README.md` §3's order (D-12, FAM-3.1, FAM-3.2, guardrails G1)."""
        package = training()
        self.assertEqual(
            tuple(getattr(package, "__all__", ())),
            SIX_NAMES,
            "src/training/__init__.py exports the six entry points of e2e-surface.md §3.5 "
            "in that order and declares them in __all__, adding, removing and renaming "
            "none (README.md §3, D-12, guardrails G1): %r"
            % (getattr(package, "__all__", None),),
        )
        for forbidden in ("RUNGS", "HYPER", "_Curve", "TrainingError"):
            self.assertNotIn(
                forbidden,
                tuple(getattr(package, "__all__", ())),
                "%r stays below an entry point and is not surface (README.md §3, D-12)"
                % (forbidden,),
            )
        first = package.rungs()
        second = package.rungs()
        self.assertEqual(
            tuple(first),
            RUNG_NAMES,
            "the registry is read one way and not two, in brief §2's order, which is "
            "never rearranged without an L0 decision (D-2, registry.md §5): %r"
            % (tuple(first),),
        )
        self.assertEqual(
            tuple(second), tuple(first), "two calls return equal records in that order"
        )
        for name in RUNG_NAMES:
            self.assertEqual(
                second[name],
                first[name],
                "one name resolves one configuration (registry.md §5, FAM-3.2): %r" % (name,),
            )

    def test_trn_1_2_the_nine_variants_are_the_declared_literals(self):
        """TRN-1.2 every variant's `architecture` kind/width/depth/sparsity/residual, `backend` and `encoding` is `registry.md` §1's literal (D-3, D-7, guardrails G2, FAM-3.2)."""
        registry = training().rungs()
        seen = set()
        for rung_name in RUNG_NAMES:
            entries = variant_entries(registry[rung_name])
            self.assertEqual(
                [variant_name(entry) for entry in entries],
                list(VARIANTS[rung_name]),
                "rung %r carries %r in registry.md §1's order, so R4 trains `wide` then "
                "`deep` (loop.md §2, ASM-9): %r"
                % (rung_name, VARIANTS[rung_name], entries),
            )
            for entry in entries:
                name = variant_name(entry)
                seen.add(name)
                kind, width, depth, sparsity, residual = ARCHITECTURE[name]
                with self.subTest(variant=name):
                    architecture = architecture_of(entry)
                    self.assertEqual(
                        as_text(architecture.get("kind"), "architecture.kind"),
                        kind,
                        "%s's kind is %r and the kind vocabulary is agents.learners()'s "
                        "seven names (registry.md §1, agents/surface.md §3)"
                        % (name, kind),
                    )
                    self.assertEqual(
                        as_int(architecture.get("width"), "architecture.width"), width,
                        "%s declares width %d, which is the capacity match's literal "
                        "(registry.md §1, §4, ASM-10)" % (name, width),
                    )
                    self.assertEqual(
                        as_int(architecture.get("depth"), "architecture.depth"), depth,
                        "%s declares depth %d (registry.md §1)" % (name, depth),
                    )
                    self.assertAlmostEqual(
                        as_float(architecture.get("sparsity"), "architecture.sparsity"),
                        sparsity,
                        places=12,
                        msg="%s declares sparsity %r (registry.md §1)" % (name, sparsity),
                    )
                    self.assertEqual(
                        bool(architecture.get("residual")), residual,
                        "%s declares residual %r (registry.md §1)" % (name, residual),
                    )
                    self.assertEqual(
                        as_text(entry.get("backend"), "backend"),
                        BACKEND[name],
                        "%s's backend is %r (D-7, registry.md §1)" % (name, BACKEND[name]),
                    )
                    self.assertEqual(
                        as_text(entry.get("encoding"), "encoding"),
                        ENCODING[name],
                        "%s's encoding is %r (D-3, registry.md §1)"
                        % (name, ENCODING[name]),
                    )
        self.assertEqual(
            seen,
            set(ARCHITECTURE),
            "the registry declares registry.md §1's nine variants and no tenth: %r"
            % (sorted(seen),),
        )

    def test_trn_1_3_every_entry_carries_the_one_shared_declaration(self):
        """TRN-1.3 each variant entry declares the ladder's one `learning_rule`, the documented `hyper`, `param_budget` 10000, `samples` 1000, `seeds` `[0, 1, 2]`, `device` `cpu`, `snapshot_every` 100 and `table` `live` (registry.md §1, records.md §2, ASM-7, ASM-8, ASM-18)."""
        registry = training().rungs()
        for rung_name in RUNG_NAMES:
            for entry in variant_entries(registry[rung_name]):
                name = variant_name(entry)
                with self.subTest(variant=name):
                    missing = ENTRY_KEYS - set(entry)
                    self.assertEqual(
                        missing,
                        set(),
                        "records.md §2's variant entry carries %r; %s is missing %r "
                        "(registry.md §2)" % (sorted(ENTRY_KEYS), name, sorted(missing)),
                    )
                    self.assertEqual(
                        as_text(entry.get("learning_rule"), "learning_rule"),
                        LEARNING_RULE,
                        "the ladder declares one rule, ASM-7's (registry.md §1)",
                    )
                    self.assertEqual(
                        entry.get("hyper"),
                        HYPER,
                        "hyper is the ladder's fixed declaration, copied as data "
                        "(registry.md §1, agents/rule.md §6)",
                    )
                    self.assertEqual(
                        as_int(entry.get("param_budget"), "param_budget"), PARAM_BUDGET,
                        "ASM-10's declared parameter budget (registry.md §1)",
                    )
                    self.assertEqual(
                        as_int(entry.get("samples"), "samples"), SHARED["samples"],
                        "ASM-8's live budget is 1,000 hands per variant per seed",
                    )
                    self.assertEqual(
                        tuple(as_int(seed, "a seed") for seed in as_sequence(
                            entry.get("seeds"), "seeds")),
                        tuple(SHARED["seeds"]),
                        "protocol.md §2 fixes the seed set at 0, 1, 2",
                    )
                    self.assertEqual(
                        as_text(entry.get("device"), "device"), SHARED["device"],
                        "every rung runs on cpu (D-8, registry.md §1)",
                    )
                    self.assertEqual(
                        as_int(entry.get("snapshot_every"), "snapshot_every"),
                        SHARED["snapshot_every"],
                        "the declared interval is the declared budget's, 1000 / 10 "
                        "(registry.md §1, ASM-18)",
                    )
                    self.assertEqual(
                        as_text(entry.get("table"), "table"), SHARED["table"],
                        "the live table is the declared budget (league.md §6)",
                    )

    def test_trn_1_4_the_nine_counts_land_inside_asms_band(self):
        """TRN-1.4 `agents.param_count` of each of the nine variants' learners lands inside 10,000 ± 2%, and each of the four comparison pairs matches within ±2% (registry.md §4, ASM-10, FAM-3.15, FAM-13.3)."""
        registry = training().rungs()
        counts = {}
        for rung_name in RUNG_NAMES:
            for entry in variant_entries(registry[rung_name]):
                name = variant_name(entry)
                count = param_count_of(entry)
                counts[name] = count
                with self.subTest(variant=name):
                    self.assertIsInstance(
                        count,
                        int,
                        "agents.param_count returns one integer (agents/surface.md §5)",
                    )
                    self.assertEqual(
                        count,
                        PARAM_COUNT[name],
                        "%s's count is registry.md §4's arithmetic at I = 203 and "
                        "V = 96: 10,119 / 10,053 / 10,047 / 10,109 are the four the "
                        "table fixes (registry.md §4, architecture.md §5)"
                        % (name,),
                    )
                    lower = PARAM_BUDGET * (1.0 - PARAM_TOLERANCE)
                    upper = PARAM_BUDGET * (1.0 + PARAM_TOLERANCE)
                    self.assertGreaterEqual(
                        count,
                        lower,
                        "%s must land inside ASM-10's 9,800 … 10,200 band: %d"
                        % (name, count),
                    )
                    self.assertLessEqual(
                        count,
                        upper,
                        "%s must land inside ASM-10's 9,800 … 10,200 band: %d"
                        % (name, count),
                    )
        for left_rung, left, right_rung, right in COMPARISON_PAIRS:
            with self.subTest(pair="%s-%s" % (left, right)):
                left_count = counts[left]
                right_count = counts[right]
                tolerance = PARAM_TOLERANCE * max(left_count, right_count)
                self.assertLessEqual(
                    abs(left_count - right_count),
                    tolerance,
                    "%s (%s) and %s (%s) are compared on their one axis and on nothing "
                    "else, capacity included: %d against %d (registry.md §4, ASM-10, "
                    "ladder.md §4)"
                    % (left, left_rung, right, right_rung, left_count, right_count),
                )

    def test_trn_1_5_the_resolved_configuration_carries_its_twelve_keys(self):
        """TRN-1.5 `rung(name)` returns one mapping with `registry.md` §2's twelve keys and no other, `variants` holding one or two entries, and the module's own three keys duplicating the entries' values (registry.md §2, ladder.md §3, surface.md §3)."""
        package = training()
        for rung_name in RUNG_NAMES:
            configuration = as_mapping(package.rung(rung_name), "a resolved configuration")
            with self.subTest(rung=rung_name):
                self.assertEqual(
                    set(configuration),
                    CONFIGURATION_KEYS,
                    "registry.md §2 fixes the configuration's keys and adds no other: "
                    "%r" % (sorted(configuration),),
                )
                self.assertEqual(
                    as_text(configuration["name"], "name"),
                    rung_name,
                    "the configuration's name is the rung name R1 … R6 (registry.md §2)",
                )
                self.assertEqual(
                    as_text(configuration["primary"], "primary"),
                    PRIMARY[rung_name],
                    "the primary is the variant the next rung inherits (ladder.md §2, "
                    "D-16): %r" % (PRIMARY[rung_name],),
                )
                self.assertEqual(
                    len(variant_entries(configuration)),
                    len(VARIANTS[rung_name]),
                    "a configuration declares one or two variants (ladder.md §2, "
                    "surface.md §4): %r" % (len(variant_entries(configuration)),),
                )
                self.assertEqual(
                    tuple(as_int(seed, "a seed") for seed in as_sequence(
                        configuration["seeds"], "seeds")),
                    tuple(SHARED["seeds"]),
                    "the configuration's own `seeds` is protocol.md §2's set "
                    "(registry.md §2)",
                )
                self.assertEqual(
                    as_int(configuration["samples"], "samples"), SHARED["samples"],
                    "the configuration's own `samples` is ASM-8's live budget",
                )
                self.assertEqual(
                    as_int(configuration["param_budget"], "param_budget"), PARAM_BUDGET,
                    "the configuration's own `param_budget` is ASM-10's declaration",
                )
                self.assertEqual(
                    as_text(configuration["table"], "table"), SHARED["table"],
                    "the configuration's declared table budget (loop.md §3)",
                )
                self.assertEqual(
                    as_text(configuration["device"], "device"), SHARED["device"],
                    "every rung runs on cpu (D-8)",
                )
                self.assertEqual(
                    as_int(configuration["snapshot_every"], "snapshot_every"),
                    SHARED["snapshot_every"],
                    "the declared interval is 100; what a run uses is budget // 10 "
                    "(registry.md §1, loop.md §2)",
                )

    def test_trn_1_6_axis_and_carried_from_are_the_ladder_s_sentences(self):
        """TRN-1.6 `carried_from` is `None` for R1 and the previous rung's primary variant after it, and `axis` is `registry.md` §1's sentence under its one-word label (registry.md §1-§2, ladder.md §2, FAM-3.4, FAM-3.5, FAM-3.6-3.10)."""
        package = training()
        for rung_name in RUNG_NAMES:
            configuration = package.rung(rung_name)
            with self.subTest(rung=rung_name):
                self.assertEqual(
                    configuration["carried_from"],
                    CARRIED_FROM[rung_name],
                    "carried_from is None for R1 and the previous rung's primary variant "
                    "after it (registry.md §1-§2, D-16): %r"
                    % (configuration["carried_from"],),
                )
                axis = as_text(configuration["axis"], "axis")
                self.assertEqual(
                    axis,
                    AXES[rung_name],
                    "registry.md §1 fixes the sentence `rung(name)[\"axis\"]` carries, "
                    "and it is not L4's (registry.md §5): %r" % (axis,),
                )
                for label in AXIS_LABELS[rung_name]:
                    self.assertIn(
                        label,
                        axis.lower(),
                        "the axis carries its one-word label %r, which is what makes "
                        "FAM-3.6-3.10 read as text (registry.md §1): %r" % (label, axis),
                    )

    def test_trn_1_7_the_pool_entry_is_one_frozen_declaration_with_an_id(self):
        """TRN-1.7 each rung's `pool` entry carries an id, `lineage` = `carried_from`, `m` = 5, `frozen` true and the version window as a member list, R1's being the baselines alone (registry.md §3, records.md §7-§8, FAM-3.17, FAM-3.18)."""
        package = training()
        seen_ids = {}
        for rung_name in RUNG_NAMES:
            configuration = package.rung(rung_name)
            pool = as_mapping(configuration["pool"], "a pool entry")
            with self.subTest(rung=rung_name):
                self.assertTrue(
                    as_text(pool.get("id"), "pool.id").strip(),
                    "a pool entry carries an id; it is the read-back id of the "
                    "membership the repository carries (registry.md §3, surface.md §3.1)",
                )
                self.assertEqual(
                    pool.get("lineage"),
                    CARRIED_FROM[rung_name],
                    "the pool's lineage is the rung it inherits (registry.md §3)",
                )
                self.assertEqual(
                    as_int(pool.get("m"), "pool.m"),
                    RETAINED,
                    "each pool declares m = 5, the league's M (registry.md §3, ASM-18)",
                )
                self.assertIs(
                    pool.get("frozen"),
                    True,
                    "the pool is frozen before the first hand (registry.md §3, ASM-16)",
                )
                members = as_sequence(pool.get("members"), "a pool entry's 'members'")
                if rung_name == "R1":
                    self.assertEqual(
                        members,
                        [],
                        "R1 inherits no lineage, so its window is empty and its pool is "
                        "the three baselines alone (registry.md §3, FAM-3.17)",
                    )
                for member in members:
                    as_mapping(member, "a pool member")
                    ids = member_ids([member])
                    self.assertTrue(
                        as_text(ids[0], "a member's id").strip(),
                        "records.md §7 makes a member's `id` required (registry.md §3)",
                    )
                seen_ids[rung_name] = as_text(pool["id"], "pool.id")
        for rung_name in RUNG_NAMES:
            pool = as_mapping(package.rung(rung_name)["pool"], "a pool entry")
            with self.subTest(read_back=rung_name):
                built = evaluation().build_pool(
                    {
                        "members": list(as_sequence(pool["members"], "a pool entry's members")),
                        "m": as_int(pool["m"], "pool.m"),
                        "frozen": bool(pool["frozen"]),
                    }
                )
                self.assertEqual(
                    as_text(pool["id"], "pool.id"),
                    as_text(
                        as_mapping(evaluation().pool_members(built), "a pool record")["id"],
                        "the read-back id",
                    ),
                    "the declared id is pool_members' read-back for the membership the "
                    "repository actually carries, never a fabricated one (registry.md §3, "
                    "surface.md §3.1, records.md §8): %r" % (pool["id"],),
                )
        self.assertEqual(
            package.rung("R1")["pool"],
            package.rung("R1")["pool"],
            "one name resolves one configuration, so one membership reads back one "
            "entry and one id (registry.md §5, FAM-3.17)",
        )
        self.assertEqual(
            set(seen_ids),
            set(RUNG_NAMES),
            "every rung declares the pool it trains against (registry.md §3, FAM-3.17)",
        )

    def test_trn_1_8_an_unknown_rung_name_is_refused_with_the_name_in_it(self):
        """TRN-1.8 `rung` refuses a name `RUNG_NAMES` does not carry with `UnknownRung`, naming the name and the six it carries (registry.md §5, errors.md §2, §4, FAM-15.5, FAM-16.28)."""
        package = training()
        self.refuse(
            lambda: package.rung(INVENTED_RUNG),
            "UnknownRung",
            groups=((INVENTED_RUNG,), ("R1", "R2", "R3", "R4", "R5", "R6")),
            label="rung(%r)" % (INVENTED_RUNG,),
        )
        self.refuse(
            lambda: package.rung(5519),
            error_class("UnknownRung").__name__,
            groups=(("5519",),),
            label="rung of a value that is not a string",
        )

    def test_trn_1_9_resolving_builds_no_learner_plays_no_hand_and_writes_nothing(self):
        """TRN-1.9 `rung` and `rungs` build no learner, deal no hand, write no file and move no stream — resolving is not training (registry.md §2, D-3, guardrails G19, surface.md §3)."""
        import random
        from unittest import mock

        package = training()
        before_tree = checkpoint_tree()
        before_stream = random.getstate()
        with mock.patch.object(agents(), "build_learner") as build_learner, mock.patch.object(
            agents(), "save"
        ) as save, mock.patch.object(engine(), "play_hand") as play_hand, mock.patch.object(
            engine(), "new_hand"
        ) as new_hand, mock.patch("os.makedirs") as makedirs:
            registry = package.rungs()
            one = package.rung("R1")
        build_learner.assert_not_called()
        save.assert_not_called()
        play_hand.assert_not_called()
        new_hand.assert_not_called()
        makedirs.assert_not_called()
        self.assertEqual(
            tuple(registry),
            RUNG_NAMES,
            "resolution returns the six configurations it is asked for: %r"
            % (tuple(registry),),
        )
        self.assertEqual(one["name"], "R1", "resolution returns the name it resolved")
        self.assert_no_hand_dealt(before_stream, "rung() and rungs()")
        self.assert_tree_untouched(before_tree, "rung() and rungs()")


if __name__ == "__main__":
    unittest.main()
