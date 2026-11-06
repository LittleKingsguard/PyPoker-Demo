"""JOIN-EVL-13 — the two declarations at the join (`fixed` rows).

`protocol()` and `league()` take no argument, so they are not blind rows; what
they *declare* is a join nonetheless: the seven evidence families and their
refusal words are what `report` judges a run record against, the three baselines
are `agents.baselines()`'s names, the header items are the facts `engine` and
`features` publish, and the rating row is the method and anchor `rating` carries
(`docs/L2/evaluation/surface.md` §3–§4, `docs/L2/evaluation/league.md` §6,
`docs/L3/evaluation/declarations.md` §1–§4).  This family checks that the two
declarations agree with the modules they name and with the records the rest of
this battery drives.
"""

import importlib.util
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "evaluation_join_support" in sys.modules:
    J = sys.modules["evaluation_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "evaluation_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["evaluation_join_support"] = J
    _spec.loader.exec_module(J)


class DeclarationsAtTheJoin(J.JoinCase):
    """The two fixed rows read against the modules and records they describe."""

    def test_join_evl_13_1_the_seven_families_are_the_ones_report_refuses(self):
        """JOIN-EVL-13.1 `protocol()` names the seven families and their refusal words.

        `docs/L2/evaluation/surface.md` §3 and `docs/L3/evaluation/declarations.md`
        §3: the families are `protocol.md` §1's seven in its order, each carrying a
        `refusal` word that is the word a report raises when that family is absent —
        `axis row`'s space included, because a report is machine-readable evidence
        and a reader finds a family by the name the protocol spells
        (`docs/L2/evaluation/league.md` §6, `docs/L3/evaluation/report.md` §1).
        """
        declared = J.protocol()["families"]
        names = [str(name) for name in declared]
        self.assertEqual(
            names,
            ["curves", "pool", "matrix", "rating", "baselines", "axis row",
             "header"],
            "protocol() declares protocol.md §1's seven families in its order "
            "(docs/L3/evaluation/declarations.md §3)",
        )
        for name in names:
            record = declared[name]
            self.assertIn(
                "required",
                record,
                "the %r family declares its required content items "
                "(docs/L2/evaluation/surface.md §3)" % (name,),
            )
            self.assertEqual(
                str(record["refusal"]),
                name,
                "a family's refusal word is the family's own name — `axis row` "
                "with its space (docs/L3/evaluation/declarations.md §3): %r"
                % (record,),
            )
        table = J.hand_built_matrix()
        fitted = J.rating(table)
        record = J.run_record(table, fitted, J.hand_built_pool_record())
        broken = J.clone(record)
        broken.pop("axis row")
        message = self.assert_refusal(
            "report",
            [(J.family_refusal("axis row"),)],
            lambda: J.report(J.RUNG, broken, table, fitted),
            "a record with the axis row family absent",
        )
        self.assertIn(
            "axis row",
            message.lower(),
            "the report refuses the absent family by the word protocol() "
            "declares (docs/L3/evaluation/report.md §3 item 1, "
            "docs/L2/evaluation/league.md §6): %r" % (message,),
        )

    def test_join_evl_13_2_the_declared_baselines_are_agents_catalogue(self):
        """JOIN-EVL-13.2 both declarations name `agents.baselines()`'s three.

        `docs/L2/evaluation/surface.md` §3–§4 and `docs/L2/evaluation/league.md` §1:
        `protocol()["baselines"]` and `league()["baselines"]` are the tuple
        `("random", "always-call", "oracle")`, `agents.baselines()`'s order, because
        the catalogue is the one home of the three names (`docs/L2/agents/
        surface.md` §11, D-6), and `league()["m"]` is M = 5 (`docs/L3/evaluation/
        declarations.md` §4, ASM-14).
        """
        catalogue = [str(name) for name in J.baselines()]
        for entry in ("protocol", "league"):
            with self.subTest(declaration=entry):
                declared = J.protocol() if entry == "protocol" else J.league()
                self.assertEqual(
                    [str(name) for name in declared["baselines"]],
                    catalogue,
                    "%s()'s baselines are agents.baselines()'s names in its order "
                    "(docs/L2/evaluation/surface.md §3, §4, "
                    "docs/L2/agents/surface.md §11)" % (entry,),
                )
        self.assertEqual(
            int(J.league()["m"]),
            5,
            "league() declares M = 5, the window's bound "
            "(docs/L3/evaluation/declarations.md §4, ASM-14)",
        )
        self.assertEqual(
            tuple(J.protocol()["seeds"]),
            (0, 1, 2),
            "protocol() declares the fixed seed set 0, 1, 2 "
            "(docs/L1/protocol.md §2, docs/L3/evaluation/declarations.md §2)",
        )
        self.assertEqual(
            tuple(J.protocol()["table_budgets"]),
            ("live", "full"),
            "protocol() declares the two table budgets in that order "
            "(docs/L3/evaluation/declarations.md §2, records.md §10)",
        )

    def test_join_evl_13_3_the_table_budgets_are_arithmetic_on_the_membership(self):
        """JOIN-EVL-13.3 `league()`'s tables and `cell_count` are the table's arithmetic.

        `docs/L2/evaluation/surface.md` §4 and `docs/L3/evaluation/declarations.md`
        §4.1, §5: a cell is 120 hands live and 1,500 full, `hands_played` is
        `cell_count(K) × hands_per_cell` for the K a rung can build (4, 9, 10), and
        `cell_count` takes a K, a membership sequence or a members mapping and
        returns K(K−1)/2 — so a talk sizes its table before it plays one
        (`docs/L1/league.md` §6, ASM-14).
        """
        declared = J.league()
        cell_count = declared["cell_count"]
        budgets = declared["tables"]
        self.assertEqual(
            [str(key) for key in budgets],
            ["live", "full"],
            "the two budget rows are keyed live then full "
            "(docs/L3/evaluation/declarations.md §4.1)",
        )
        self.assertEqual(
            (int(budgets["live"]["hands_per_cell"]),
             int(budgets["full"]["hands_per_cell"])),
            (120, 1500),
            "a cell is 120 hands live and 1,500 full "
            "(docs/L2/evaluation/league.md §5, ASM-14)",
        )
        for label in ("live", "full"):
            row = budgets[label]
            for size, hands in sorted(row["hands_played"].items()):
                self.assertEqual(
                    int(hands),
                    cell_count(int(size)) * int(row["hands_per_cell"]),
                    "the %s budget's hands_played for K=%r is cell_count(K) × "
                    "hands_per_cell (docs/L3/evaluation/declarations.md §4.1)"
                    % (label, size),
                )
            self.assertNotIn(
                "per_hand_ceiling_seconds",
                row,
                "no budget row carries a per-hand figure: ASM-21 ratifies the measured "
                "0.105-0.130 s/hand and supersedes ASM-15's 0.04 bound, so a ceiling here "
                "would have no ratified source (docs/L3/evaluation/declarations.md §4.1, "
                "ASM-21)",
            )
        table = J.hand_built_matrix()
        members = J.matrix_members(table)
        self.assertEqual(
            int(cell_count(len(members))),
            J.matrix_cell_count(table),
            "cell_count(K) is the cells a K-member table carries "
            "(docs/L2/evaluation/surface.md §4, records.md §10)",
        )
        self.assertEqual(
            int(cell_count(members)),
            J.matrix_cell_count(table),
            "cell_count takes a membership sequence and returns K(K−1)/2 "
            "(docs/L3/evaluation/declarations.md §5)",
        )
        self.assertEqual(
            int(cell_count({"members": members})),
            J.matrix_cell_count(table),
            "cell_count takes a mapping carrying `members` "
            "(docs/L3/evaluation/declarations.md §5)",
        )
        for bad in (1, True, "members"):
            with self.subTest(bad=bad):
                self.assert_refusal(
                    "cell_count",
                    [("2", "membership", "integer", "sequence", "mapping")],
                    lambda bad=bad: cell_count(bad),
                    "cell_count(%r)" % (bad,),
                )

    def test_join_evl_13_4_the_header_items_are_the_facts_engine_and_features_publish(self):
        """JOIN-EVL-13.4 a header built from `engine` and `features` satisfies the nine.

        `docs/L2/evaluation/surface.md` §3 and `docs/L3/evaluation/declarations.md`
        §2.1: the nine header items are the game, the action space, every member's
        parameter counts, the sample budget, the cell size, the seed set, the table
        seed, the device and the checkpoint paths — the first two are what
        `engine.game_config()` and `features.action_space()` publish, and the
        presence rule matches by letters-and-digits token.  A header built that way
        must therefore satisfy `report`, and the report must read the device from it
        (`docs/L3/evaluation/report.md` §2, `docs/L1/protocol.md` §1).
        """
        table = J.hand_built_matrix()
        fitted = J.rating(table)
        pool_record = J.hand_built_pool_record()
        header = J.header_record(table, pool_record)
        items = [str(item) for item in J.protocol()["header"]]
        self.assertEqual(
            len(items),
            9,
            "protocol() declares nine header items "
            "(docs/L3/evaluation/declarations.md §2.1)",
        )
        keys = [J.token(key) for key in header]
        for item in items:
            wanted = J.token(item)
            self.assertTrue(
                any(key == wanted or wanted in key or key in wanted for key in keys),
                "the header item %r must be satisfied by the header the run "
                "records, built from engine.game_config() and "
                "features.action_space() (docs/L3/evaluation/declarations.md §2.1, "
                "docs/L1/protocol.md §1)" % (item,),
            )
        self.assertEqual(
            J.canonical(header["game"]),
            J.canonical(J.game_config()),
            "the header's game item is the fixed game engine.game_config() "
            "publishes (docs/L2/engine/surface.md §3, protocol.md §1)",
        )
        self.assertEqual(
            J.canonical(header["action space"]),
            J.canonical(J.action_space()),
            "the header's action space item is the vocabulary "
            "features.action_space() publishes (docs/L2/features/surface.md §7, "
            "protocol.md §1)",
        )
        record = J.run_record(table, fitted, pool_record)
        assembled = J.report(J.RUNG, record, table, fitted)
        self.assertEqual(
            str(assembled["device"]),
            str(header["device"]),
            "the report reads the device from the header family "
            "(docs/L3/evaluation/report.md §2, protocol.md §6)",
        )

    def test_join_evl_13_5_the_rating_row_is_one_value_on_both_sides(self):
        """JOIN-EVL-13.5 protocol's and league()'s rating row is the fit's own record.

        `docs/L2/evaluation/surface.md` §3–§4 and `docs/L3/evaluation/declarations.md`
        §2.2: `protocol()["rating"]` and `league()["rating"]` are one value — the
        method `Bradley-Terry`, the 0.95 interval and the anchor naming the three
        baselines' mean fixed at 0 — and `rating(matrix)` carries that method and
        that anchor unchanged, so the declaration and the fitted record name one
        method and one scale (ASM-17, `records.md` §11).
        """
        declared = J.protocol()["rating"]
        self.assertEqual(
            J.canonical(declared),
            J.canonical(J.league()["rating"]),
            "protocol() and league() carry one rating row "
            "(docs/L3/evaluation/declarations.md §2.2)",
        )
        self.assertEqual(
            str(declared["method"]),
            "Bradley-Terry",
            "the declared method is the one string `Bradley-Terry` "
            "(docs/L3/evaluation/declarations.md §2.2, records.md §11)",
        )
        self.assertAlmostEqual(
            float(declared["confidence"]),
            0.95,
            places=12,
            msg="the declared interval's confidence is 95% "
                "(docs/L3/evaluation/declarations.md §2.2, ASM-17)",
        )
        fitted = J.rating(J.hand_built_matrix())
        self.assertEqual(
            str(fitted["method"]),
            str(declared["method"]),
            "the fit carries the declared method (records.md §11)",
        )
        self.assertEqual(
            str(fitted["anchor"]),
            str(declared["anchor"]),
            "the fit carries the declared anchor unchanged "
            "(docs/L3/evaluation/declarations.md §2.2, ASM-17)",
        )


if __name__ == "__main__":
    unittest.main()
