"""EVL-1 — the two declarations: `protocol()` and `league()`.

Drives `docs/L3/evaluation/declarations.md` §1-§8, `docs/L2/evaluation/surface.md`
§3-§4 and the numbers of `docs/L1/protocol.md` §1-§2 and `docs/L1/league.md` §6:
the evidence contract's key-by-key shape (`families` with the seven names in order,
`seeds` `(0, 1, 2)`, the nine header items, `table_budgets`, the three pinned
baselines, the rating row), the league's parameters (M = 5, both budgets with their
`hands_played` arithmetic, the one table seed `20261105`, the rating row equal on
both sides) and the one callable `league()` carries, `cell_count`, with its three
shapes and its `InvalidMembership` refusals.

Both rows are `fixed`: neither takes an argument, so both are rebuilt on every call
and equal on two calls (`surface.md` §1), and neither plays a hand, reads a file or
moves the global `random` stream (`surface.md` §1, ASM-2). The one place the design
leaves the two records unequal is `cell_count`'s identity -- "the identity of the
`cell_count` callable ... [is] free ... only that `league()` returns a callable with
§5's behaviour" (`declarations.md` §8) -- so EVL-1.11 compares the two records key by
key and the callable by behaviour.
"""

import unittest

from _evaluation_support import (
    BASELINES,
    BUDGETS,
    ELEVEN_NAMES,
    FAMILIES,
    HEADER_ITEMS,
    SEED_SET,
    EvaluationCase,
    no_file_reads,
)

#: The seven families' declared content items (`declarations.md` §3, `protocol.md` §1).
FAMILY_REQUIRED = {
    "curves": ("samples", "signal", "spread"),
    "pool": ("id", "m", "frozen", "members"),
    "matrix": ("members", "cells", "hands_per_cell", "table_seed", "table"),
    "rating": ("values", "method", "anchor", "bound_applied", "bootstrap_seed", "converged"),
    "baselines": ("rows",),
    "axis row": ("value",),
    "header": HEADER_ITEMS,
}

#: `protocol()`'s six keys, in `declarations.md` §2's order.
PROTOCOL_KEYS = ("families", "seeds", "header", "table_budgets", "baselines", "rating")

#: `league()`'s six keys, in `declarations.md` §4's order.
LEAGUE_KEYS = ("m", "baselines", "tables", "cell_count", "table_seed", "rating")


class DeclarationsTest(EvaluationCase):
    def test_evl_1_1_the_eleven_entry_points_exist_in_the_l1_order(self):
        """EVL-1.1 exactly the eleven names of `e2e-surface.md` §3.4 exist, are callable and are `__all__`, in that order (`README.md` §3, D-12, G1)."""
        package = self.evaluation()
        for name in ELEVEN_NAMES:
            with self.subTest(entry=name):
                self.assertTrue(
                    hasattr(package, name),
                    "the evaluation package declares no %r entry point "
                    "(e2e-surface.md §3.4, README.md §3)" % name,
                )
                self.assertTrue(
                    callable(getattr(package, name)),
                    "evaluation.%s exists but is not callable (e2e-surface.md §3.4)" % name,
                )
        exported = getattr(package, "__all__", None)
        self.assertIsNotNone(
            exported, "the evaluation package declares no __all__ (README.md §3, G1)"
        )
        self.assertEqual(
            tuple(exported),
            ELEVEN_NAMES,
            "__all__ must be the eleven entry points in the L1 order "
            "(e2e-surface.md §3.4, README.md §3, G1), got %r" % (tuple(exported),),
        )

    def test_evl_1_2_all_exports_no_twelfth_name(self):
        """EVL-1.2 `Pool`, `EvaluationError`, `TABLE_SEED` and every other name below an entry point stay out of the package's exports (`README.md` §3, `errors.md` §2, D-12, G1)."""
        package = self.evaluation()
        exported = tuple(getattr(package, "__all__", ()))
        for name in ("Pool", "_MemberPolicy", "EvaluationError", "TABLE_SEED", "BOUND", "VARIANT_SEED"):
            with self.subTest(name=name):
                self.assertNotIn(
                    name,
                    exported,
                    "%r is below an entry point and is not a twelfth surface name "
                    "(README.md §3, e2e-surface.md §1, D-12, G1): %r" % (name, exported),
                )
        for name in ("Pool", "EvaluationError", "TABLE_SEED"):
            with self.subTest(attribute=name):
                self.assertFalse(
                    hasattr(package, name),
                    "evaluation.%s is a module-level name of the package, and the package "
                    "exports exactly the eleven entry points and no twelfth "
                    "(README.md §3, D-12, G1)" % name,
                )

    def test_evl_1_3_protocol_has_its_six_keys_in_order(self):
        """EVL-1.3 `protocol()` is one mapping read under exactly six keys, in `declarations.md` §2's order (`surface.md` §3)."""
        package = self.evaluation()
        record = package.protocol()
        self.assertIsInstance(record, dict, "protocol() returns one mapping (surface.md §3)")
        self.assertEqual(
            tuple(record),
            PROTOCOL_KEYS,
            "protocol() is read under exactly these six keys, in this order "
            "(declarations.md §2, surface.md §3), got %r" % (tuple(record),),
        )
        from collections.abc import Mapping

        self.assertIsInstance(record["families"], Mapping)
        self.assertIsInstance(record["rating"], Mapping)
        for key in ("seeds", "header", "table_budgets", "baselines"):
            with self.subTest(key=key):
                self.assertFalse(
                    isinstance(record[key], (str, bytes)),
                    "protocol()[%r] is a sequence of names, not one name "
                    "(declarations.md §2)" % key,
                )
                self.assertIn(
                    len(tuple(record[key])),
                    (2, 3, 7, 9),
                    "protocol()[%r] is one item per declared name (declarations.md §2): %r"
                    % (key, record[key]),
                )

    def test_evl_1_4_protocol_declares_the_seven_families_with_their_refusal_words(self):
        """EVL-1.4 `protocol()["families"]` is the seven families of `protocol.md` §1, in its order, each `{required, refusal}` with the pinned items and the exact refusal word -- `axis row`'s space included (`declarations.md` §3, D-6)."""
        package = self.evaluation()
        families = package.protocol()["families"]
        self.assertEqual(
            tuple(families),
            FAMILIES,
            "the seven families are protocol.md §1's names, in its order "
            "(declarations.md §3, surface.md §3), got %r" % (tuple(families),),
        )
        for name in FAMILIES:
            with self.subTest(family=name):
                entry = families[name]
                self.assertEqual(
                    set(entry),
                    {"required", "refusal"},
                    "a family's record carries `required` and `refusal` and nothing else "
                    "(declarations.md §3): %r" % (entry,),
                )
                self.assertEqual(
                    tuple(entry["required"]),
                    FAMILY_REQUIRED[name],
                    "the %r family's content items are protocol.md §1's "
                    "(declarations.md §3): %r" % (name, entry["required"]),
                )
                self.assertEqual(
                    entry["refusal"],
                    name,
                    "a family's absence is refused with the word protocol.md §1 spells, "
                    "`axis row`'s space included (declarations.md §3, D-6): %r"
                    % (entry["refusal"],),
                )

    def test_evl_1_5_protocol_declares_the_seed_set_the_budgets_and_the_baselines(self):
        """EVL-1.5 `seeds` is `(0, 1, 2)`, `table_budgets` is `("live", "full")` and `baselines` is the three pinned names in `agents.baselines()`'s order (`protocol.md` §2, `records.md` §10, `agents/surface.md` §11)."""
        package = self.evaluation()
        record = package.protocol()
        self.assertEqual(
            tuple(record["seeds"]),
            SEED_SET,
            "the seed set is fixed at 0, 1, 2 (protocol.md §2, declarations.md §2): %r"
            % (record["seeds"],),
        )
        self.assertEqual(
            tuple(record["table_budgets"]),
            BUDGETS,
            "the two table budgets are declared `live` then `full` "
            "(declarations.md §2, records.md §10): %r" % (record["table_budgets"],),
        )
        self.assertEqual(
            tuple(record["baselines"]),
            BASELINES,
            "the three pinned baselines are random, always-call, oracle in "
            "agents.baselines()'s order (declarations.md §2, agents/surface.md §11): %r"
            % (record["baselines"],),
        )
        self.assertEqual(
            tuple(record["baselines"]),
            tuple(self.agents().baselines()),
            "protocol()'s baseline names are agents.baselines()'s own order "
            "(README.md §6, agents/surface.md §11)",
        )

    def test_evl_1_6_protocol_declares_the_nine_header_items_in_order(self):
        """EVL-1.6 `header` is the nine item names of `declarations.md` §2.1, in that order (`protocol.md` §1)."""
        package = self.evaluation()
        record = package.protocol()
        self.assertEqual(
            tuple(record["header"]),
            HEADER_ITEMS,
            "the header carries the nine items of protocol.md §1 in "
            "declarations.md §2.1's order -- game, action space, parameter counts, "
            "sample budget, cell size, seeds, table seed, device, checkpoints: %r"
            % (record["header"],),
        )
        for item in record["header"]:
            with self.subTest(item=item):
                self.assertIsInstance(
                    item,
                    str,
                    "a header item is a name, so a report can look one up "
                    "(declarations.md §2.1): %r" % (item,),
                )

    def test_evl_1_7_protocol_declares_the_rating_row(self):
        """EVL-1.7 `protocol()["rating"]` names the Bradley-Terry method, the 95% interval and the three-baseline anchor (`declarations.md` §2.2, `league.md` §5, ASM-17)."""
        package = self.evaluation()
        row = package.protocol()["rating"]
        self.assertEqual(
            set(row),
            {"method", "confidence", "anchor"},
            "the rating row is declarations.md §2.2's three-key record: %r" % (row,),
        )
        self.assertEqual(
            row["method"],
            "Bradley-Terry",
            "the fitted method is the one string `Bradley-Terry` "
            "(declarations.md §2.2, league.md §5): %r" % (row["method"],),
        )
        self.assertEqual(
            float(row["confidence"]),
            0.95,
            "the interval's level is 0.95 (declarations.md §2.2, ASM-17): %r"
            % (row["confidence"],),
        )
        anchor = row["anchor"]
        self.assertIsInstance(
            anchor, str, "the anchor is the sentence rating() carries (declarations.md §2.2)"
        )
        lowered = anchor.lower()
        for token in ("baseline", "mean"):
            with self.subTest(token=token):
                self.assertIn(
                    token,
                    lowered,
                    "the anchor names the three baselines' mean fixed at 0, so a reader "
                    "is not left to infer it (declarations.md §2.2, ASM-17): %r" % (anchor,),
                )
        self.assertTrue(
            "0" in anchor or "zero" in lowered,
            "the anchor states that the baselines' mean is fixed at zero "
            "(declarations.md §2.2, rating.md §2): %r" % (anchor,),
        )

    def test_evl_1_8_protocol_is_deterministic_and_plays_nothing(self):
        """EVL-1.8 two `protocol()` calls return equal records, and the call plays no hand, reads no file and leaves the global stream where it found it (`surface.md` §1, §3, declarations.md §1)."""
        package = self.evaluation()
        before = self.stream_state()
        with no_file_reads("protocol()"):
            first = package.protocol()
            second = package.protocol()
        self.assertEqual(
            first,
            second,
            "protocol() is plain data rebuilt on every call, so two calls return equal "
            "records (surface.md §3, declarations.md §1)",
        )
        self.assert_stream_unchanged(before, "protocol()")

    def test_evl_1_9_league_has_its_six_keys_and_the_declared_numbers(self):
        """EVL-1.9 `league()` is read under six keys in `declarations.md` §4's order, with M = 5 and the one table seed `20261105` (`surface.md` §4, declarations.md §4, §6)."""
        package = self.evaluation()
        record = package.league()
        self.assertEqual(
            tuple(record),
            LEAGUE_KEYS,
            "league() is read under exactly these six keys, in this order "
            "(declarations.md §4, surface.md §4), got %r" % (tuple(record),),
        )
        self.assertEqual(
            int(record["m"]),
            5,
            "M, the window's bound, is 5 (league.md §2, ASM-14, declarations.md §4): %r"
            % (record["m"],),
        )
        self.assertEqual(
            int(record["table_seed"]),
            20261105,
            "the league's one table seed is the design's declared 20261105, and every "
            "matrix is played from it (declarations.md §6, surface.md §4): %r"
            % (record["table_seed"],),
        )
        self.assertEqual(
            tuple(record["baselines"]),
            BASELINES,
            "league() declares the same three pinned baselines in the same order "
            "(declarations.md §4): %r" % (record["baselines"],),
        )

    def test_evl_1_10_league_declares_both_budgets_with_their_arithmetic(self):
        """EVL-1.10 each budget row carries `hands_per_cell` (120, 1500), its `hands_played` per K and `produced_by` — and no per-hand cost figure, ASM-15's bound being superseded — and each `hands_played` is `cell_count(K) x hands_per_cell` (`declarations.md` §4.1, `tables.md` §1, ASM-21)."""
        package = self.evaluation()
        league = package.league()
        tables = league["tables"]
        self.assertEqual(
            tuple(tables),
            BUDGETS,
            "league()['tables'] is keyed `live` then `full` (declarations.md §4.1): %r"
            % (tuple(tables),),
        )
        expected = {
            "live": {"hands": 120, "played": {4: 720, 9: 4320, 10: 5400}, "produced": "the talk, on the fly"},
            "full": {
                "hands": 1500,
                "played": {4: 9000, 9: 54000, 10: 67500},
                "produced": "an offline job shipped under tables/",
            },
        }
        for budget in BUDGETS:
            with self.subTest(budget=budget):
                row = tables[budget]
                self.assertEqual(
                    set(row),
                    {"hands_per_cell", "hands_played", "produced_by"},
                    "a budget row carries these three keys, in declarations.md §4.1's order, and "
                    "no per-hand cost figure: ASM-21 supersedes ASM-15's bound, so a 'ceiling' "
                    "here would have no ratified source (ASM-21, tables.md §5): %r" % (row,),
                )
                self.assertEqual(
                    int(row["hands_per_cell"]),
                    expected[budget]["hands"],
                    "the %s cell size is %d hands (league.md §6, ASM-14, "
                    "declarations.md §4.1): %r"
                    % (budget, expected[budget]["hands"], row["hands_per_cell"]),
                )
                self.assertEqual(
                    row["produced_by"],
                    expected[budget]["produced"],
                    "the %s table is produced by what declarations.md §4.1 declares: %r"
                    % (budget, row["produced_by"]),
                )
                self.assertNotIn(
                    "per_hand_ceiling_seconds",
                    row,
                    "ASM-21 ratifies the measured 0.105-0.130 s per hand and supersedes ASM-15's "
                    "0.04 bound, so no budget row carries a per-hand figure at all "
                    "(declarations.md §4.1, tables.md §5, ASM-21): %r"
                    % (row.get("per_hand_ceiling_seconds"),),
                )
                played = row["hands_played"]
                for size, hands in expected[budget]["played"].items():
                    with self.subTest(budget=budget, k=size):
                        self.assertEqual(
                            int(played[size]),
                            hands,
                            "a K = %d %s table plays %d hands, which is cell_count(K) x "
                            "hands_per_cell (tables.md §1, ASM-14): %r"
                            % (size, budget, hands, played.get(size)),
                        )
                        self.assertEqual(
                            int(played[size]),
                            int(row["hands_per_cell"]) * (size * (size - 1) // 2),
                            "hands_played is the product of the cell count and the cell "
                            "size, so the budget is arithmetic on K (tables.md §1): %r"
                            % (played[size],),
                        )

    def test_evl_1_11_league_and_protocol_declare_one_rating_row_and_one_baseline_order(self):
        """EVL-1.11 `protocol()["rating"]` and `league()["rating"]` are one value equal on both sides, and both name the same three baselines (`declarations.md` §2.2, §4)."""
        package = self.evaluation()
        protocol = package.protocol()
        league = package.league()
        self.assertEqual(
            protocol["rating"],
            league["rating"],
            "the rating row is one value, equal on both declarations "
            "(declarations.md §2.2): %r != %r"
            % (protocol["rating"], league["rating"]),
        )
        self.assertEqual(
            tuple(league["baselines"]),
            tuple(protocol["baselines"]),
            "the league and the protocol name the same baselines in the same order "
            "(declarations.md §2, §4)",
        )

    def test_evl_1_12_league_is_deterministic_and_plays_nothing(self):
        """EVL-1.12 two `league()` calls agree key by key -- `cell_count` by behaviour, its identity being free -- and the call plays no hand, reads no file and moves no stream (`surface.md` §4, `declarations.md` §8)."""
        package = self.evaluation()
        before = self.stream_state()
        with no_file_reads("league()"):
            first = package.league()
            second = package.league()
        for key in LEAGUE_KEYS:
            with self.subTest(key=key):
                if key == "cell_count":
                    continue
                self.assertEqual(
                    first[key],
                    second[key],
                    "two league() calls return equal records, and %r is plain data "
                    "(surface.md §4, declarations.md §1, §8)" % key,
                )
        for size in (4, 9, 10):
            with self.subTest(cell_count=size):
                self.assertEqual(
                    first["cell_count"](size),
                    second["cell_count"](size),
                    "the two calls' cell_count are one callable by behaviour, its "
                    "identity being free (declarations.md §8, surface.md §1): %r != %r"
                    % (first["cell_count"](size), second["cell_count"](size)),
                )
        self.assert_stream_unchanged(before, "league()")

    def test_evl_1_13_cell_count_accepts_its_three_shapes(self):
        """EVL-1.13 `cell_count` returns K(K-1)/2 for an integer K, a membership sequence and a mapping carrying `members` (`declarations.md` §5, `surface.md` §4)."""
        package = self.evaluation()
        cell_count = package.league()["cell_count"]
        self.assertTrue(
            callable(cell_count),
            "league() carries one callable, cell_count (surface.md §4, declarations.md §5)",
        )
        for size, expected in ((4, 6), (9, 36), (10, 45)):
            with self.subTest(kind="integer", k=size):
                self.assertEqual(
                    cell_count(size),
                    expected,
                    "cell_count(%d) is K(K-1)/2 = %d (declarations.md §5, league.md §3)"
                    % (size, expected),
                )
        membership = ["random", "always-call", "oracle", "variant-1"]
        self.assertEqual(
            cell_count(membership),
            6,
            "cell_count reads a membership sequence as its size: 4 members have 6 "
            "unordered pairs (declarations.md §5)",
        )
        self.assertEqual(
            cell_count({"members": membership}),
            6,
            "cell_count reads a mapping carrying `members` as that membership's size "
            "(declarations.md §5)",
        )
        self.assertEqual(
            cell_count(tuple(membership)),
            cell_count(list(membership)),
            "the membership's container does not change the pair count "
            "(declarations.md §5)",
        )

    def test_evl_1_14_cell_count_refuses_everything_else(self):
        """EVL-1.14 `cell_count` refuses a bound below 2, a bool, a str and any other shape, raising `InvalidMembership` and naming itself (`declarations.md` §5, `errors.md` §2, §4)."""
        package = self.evaluation()
        cell_count = package.league()["cell_count"]
        cases = (
            ("one member", (1,), (("cell_count",),)),
            ("zero", (0,), (("cell_count",),)),
            ("negative", (-4,), (("cell_count",),)),
            ("a bool", (True,), (("cell_count",),)),
            ("a str", ("9",), (("cell_count",),)),
            ("None", (None,), (("cell_count",),)),
            ("another shape", (object(),), (("cell_count",),)),
        )
        for label, args, groups in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    cell_count, *args, entry="cell_count", groups=groups, label="cell_count(%s)" % label
                )


if __name__ == "__main__":
    unittest.main()
