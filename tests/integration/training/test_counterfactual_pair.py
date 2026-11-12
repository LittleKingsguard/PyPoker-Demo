"""TRNJ-16 — a pair differing in the counterfactual member alone (D-43).

`docs/L1/counterfactual.md` §6 makes the member a **third** catalogue rather than a rule or
a utility: it rides **opt-in per variant** — a variant entry's `counterfactual`, absent
meaning `none` — so a paired arm differs only in it, on one frozen pool, one seed set and
one budget (D-3).  Its scope boundary is declared there too: no cell and no matrix record
names the member in this pass, because the shapes it is declared for a table refuse a cell,
and the paired difference the criterion reads is in the two **run records**, which do name
it.

So this file is the run record's half of that join, and it is three facts that no single
module can check about itself:

- the run record's `counterfactuals` set names the non-default member and **no `none` arm's
  row carries the key**, so a run says which member produced which curve (`records.md` §12);
- both arms of the pair name **one** frozen pool id, which is what makes the comparison a
  paired one (`counterfactual.md` §6, §7, ASM-16);
- `training.fairness` reports the pair on the `counterfactual` axis, so the axis the member
  rides is a reported axis and not a silent difference (`e2e-surface.md` §3.5, §6).

And the conditional half: a configuration whose arms declare no member at all returns a
record with **no** `counterfactuals` key, which is what keeps the two committed captures
byte-identical (`counterfactual.md` §6, §9, `tests/integration/training/
test_default_baseline.py`, `test_greedy_sample.py`, D-43).

Two runs are played: the pair at the invented budget of twelve hands per variant per seed on
the default shape (seconds), and the same pair on the catalogue's six-seat shape, which is the
one D-43 is measured on and needs a pool of five members for its five opponents
(`counterfactual.md` §8, `seats.md` §4).  Every label, seed, budget and pool id below is this
battery's own (`docs/L1/battery.md` §4, D-15); the two catalogue members, the shapes and the
pool's baseline names are read off `agents.learners()` and `engine.game_shapes()`.
"""

import copy
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

#: The invented pair's facts (`docs/L1/battery.md` §4, D-15): the configuration's label, its
#: two arms' names, the pool it declares, one seed and a budget of twelve hands per variant
#: per seed — inside the ten-to-twenty-four band a paired comparison is cheap at
#: (`counterfactual.md` §7's 20,000-hand measurement is the pinned criterion's, not this
#: case's).
PAIR_RUNG = "rung-invented-counterfactual-pair-16"
PAIR_DEFAULT_ARM = "arm-invented-counterfactual-none-16"
PAIR_REVEAL_ARM = "arm-invented-counterfactual-reveal-16"
PAIR_POOL = "pool-invented-counterfactual-pair-16"
PAIR_SEED = 64283
PAIR_BUDGET = 12

#: The same pair on the catalogue's six-seat shape, with its own labels and seed
#: (`counterfactual.md` §8, `seats.md` §2, §4, D-15).
SIX_PAIR_RUNG = "rung-invented-counterfactual-six-16"
SIX_PAIR_DEFAULT_ARM = "arm-invented-counterfactual-six-none-16"
SIX_PAIR_REVEAL_ARM = "arm-invented-counterfactual-six-reveal-16"
SIX_PAIR_POOL = "pool-invented-counterfactual-six-16"
SIX_PAIR_SEED = 27541
SIX_PAIR_BUDGET = 12

#: The control pair, whose two arms declare **no** member at all (`counterfactual.md` §9):
#: it is the shape a default declaration's record keeps.
CONTROL_RUNG = "rung-invented-counterfactual-control-16"
CONTROL_LEFT = "arm-invented-counterfactual-control-a-16"
CONTROL_RIGHT = "arm-invented-counterfactual-control-b-16"
CONTROL_POOL = "pool-invented-counterfactual-control-16"
CONTROL_SEED = 58031
CONTROL_BUDGET = 10


def pair_configuration(reveal):
    """One configuration, two variants identical but for `counterfactual` (`D-3`).

    `docs/L1/records.md` §2's variant entry, taken from the registry's own R1 entry so the two
    arms are one backend, one encoding, one architecture, one rule, one `hyper`, one seed set
    and one budget, and declared twice under two names: the left arm names no
    `counterfactual` — which is the declared default `none` — and the right arm names the
    catalogue's second member, read off `agents.learners()` and never restated
    (`counterfactual.md` §6, `records.md` §2, §3, D-43).
    """
    template = copy.deepcopy(J.variant_entry(J.rung("R1"), "naive-numeric"))
    template["samples"] = PAIR_BUDGET
    template["seeds"] = [PAIR_SEED]
    template["snapshot_every"] = max(1, PAIR_BUDGET // J.SNAPSHOT_POINTS)
    template.pop("counterfactual", None)
    left = copy.deepcopy(template)
    left["name"] = PAIR_DEFAULT_ARM
    right = copy.deepcopy(template)
    right["name"] = PAIR_REVEAL_ARM
    right["counterfactual"] = reveal
    return {
        "name": PAIR_RUNG,
        "axis": "the counterfactual member, at one architecture",
        "carried_from": None,
        "primary": PAIR_DEFAULT_ARM,
        "variants": [left, right],
        "pool": {
            "id": PAIR_POOL,
            "lineage": None,
            "m": 5,
            "frozen": True,
            "members": [],
        },
        "seeds": [PAIR_SEED],
        "samples": PAIR_BUDGET,
        "param_budget": int(template["param_budget"]),
        "table": "live",
        "device": "cpu",
        "snapshot_every": max(1, PAIR_BUDGET // J.SNAPSHOT_POINTS),
    }


def six_pair_configuration(reveal):
    """The same pair on the catalogue's six-seat shape, its pool holding five members.

    A six-seat hand seats five **distinct** opponents, so the frozen pool must hold at least
    five members and is refused by name otherwise; the catalogue's three anchors plus two
    declared folders are exactly five (`seats.md` §4, ASM-43, `records.md` §8, D-21).
    """
    configuration = pair_configuration(reveal)
    configuration["name"] = SIX_PAIR_RUNG
    configuration["axis"] = "the game shape, which is never a rung's axis"
    configuration["game"] = J.third_shape()
    configuration["primary"] = SIX_PAIR_DEFAULT_ARM
    configuration["seeds"] = [SIX_PAIR_SEED]
    configuration["samples"] = SIX_PAIR_BUDGET
    configuration["snapshot_every"] = max(1, SIX_PAIR_BUDGET // J.SNAPSHOT_POINTS)
    configuration["pool"] = {
        "id": SIX_PAIR_POOL,
        "lineage": None,
        "m": 5,
        "frozen": True,
        "members": [],
        "baselines": [str(name) for name in J.folders()[:2]],
    }
    left = copy.deepcopy(configuration["variants"][0])
    left["name"] = SIX_PAIR_DEFAULT_ARM
    left["seeds"] = [SIX_PAIR_SEED]
    left["samples"] = SIX_PAIR_BUDGET
    left["snapshot_every"] = max(1, SIX_PAIR_BUDGET // J.SNAPSHOT_POINTS)
    right = copy.deepcopy(configuration["variants"][1])
    right["name"] = SIX_PAIR_REVEAL_ARM
    right["seeds"] = [SIX_PAIR_SEED]
    right["samples"] = SIX_PAIR_BUDGET
    right["snapshot_every"] = max(1, SIX_PAIR_BUDGET // J.SNAPSHOT_POINTS)
    right["counterfactual"] = reveal
    configuration["variants"] = [left, right]
    return configuration


def control_configuration():
    """The same two-arm shape with **no** member declared on either arm (`§9`)."""
    template = copy.deepcopy(J.variant_entry(J.rung("R1"), "naive-numeric"))
    template["samples"] = CONTROL_BUDGET
    template["seeds"] = [CONTROL_SEED]
    template["snapshot_every"] = max(1, CONTROL_BUDGET // J.SNAPSHOT_POINTS)
    template.pop("counterfactual", None)
    left = copy.deepcopy(template)
    left["name"] = CONTROL_LEFT
    right = copy.deepcopy(template)
    right["name"] = CONTROL_RIGHT
    return {
        "name": CONTROL_RUNG,
        "axis": "the counterfactual member, declared on neither arm",
        "carried_from": None,
        "primary": CONTROL_LEFT,
        "variants": [left, right],
        "pool": {
            "id": CONTROL_POOL,
            "lineage": None,
            "m": 5,
            "frozen": True,
            "members": [],
        },
        "seeds": [CONTROL_SEED],
        "samples": CONTROL_BUDGET,
        "param_budget": int(template["param_budget"]),
        "table": "live",
        "device": "cpu",
        "snapshot_every": max(1, CONTROL_BUDGET // J.SNAPSHOT_POINTS),
    }


#: The three runs this file reads, built once per process: a run is a run record and its
#: artefacts, so a second case that read a second run of one configuration would be reading a
#: different observation at twice the cost (`battery.md` §2, §5, D-6).
_RUNS = {}


def pair_run():
    """The default-shape pair: two arms, two members, one record, twelve hands each."""
    if "pair" not in _RUNS:
        _RUNS["pair"] = J.run(
            pair_configuration(J.counterfactual_names()[1]),
            seeds=[PAIR_SEED],
            budget=PAIR_BUDGET,
        )
    return _RUNS["pair"]


def six_pair_run():
    """The same pair on the six-seat shape: the file's expensive observable."""
    if "six" not in _RUNS:
        _RUNS["six"] = J.run(
            six_pair_configuration(J.counterfactual_names()[1]),
            seeds=[SIX_PAIR_SEED],
            budget=SIX_PAIR_BUDGET,
        )
    return _RUNS["six"]


def control_run():
    """The control pair: two arms declaring no member at all (`counterfactual.md` §9)."""
    if "control" not in _RUNS:
        _RUNS["control"] = J.run(
            control_configuration(), seeds=[CONTROL_SEED], budget=CONTROL_BUDGET
        )
    return _RUNS["control"]


class CounterfactualPair(J.JoinCase):
    """One configuration, two arms differing in the member alone, and what the record says."""

    def test_trnj_16_1_the_run_names_the_member_only_on_the_arm_that_declares_it(self):
        """TRNJ-16.1 a paired run names the non-default member in its `counterfactuals` set and in the declaring arm's row, and no `none` arm carries the key at all.

        `docs/L1/records.md` §12: `counterfactuals` is the set of members the run declared and
        trained, **absent** when every variant declares `none`, and each `variants` entry
        names its own `counterfactual` only when it is not `none` — that conditionality is
        what keeps a default declaration's record at the shape its capture took
        (`counterfactual.md` §6, §9, D-43).  So the case reads one paired run and one control
        pair: the first names the catalogue's second member once and on the declaring arm
        only, the second names no member and carries no key, and the six-seat pass names it on
        the shape D-43 is measured on (`counterfactual.md` §6, §8, FAM-22).
        """
        catalogue = J.counterfactual_names()
        self.assertEqual(
            list(catalogue[:2]),
            ["none", "reveal-counterfactual"],
            "agents.learners() publishes the counterfactual catalogue with `none` first and "
            "the declared default and `reveal-counterfactual` second, which is the member "
            "this pair's right arm declares (counterfactual.md §6, D-43): %r" % (catalogue,),
        )
        member = catalogue[1]
        pair, six, control = pair_run(), six_pair_run(), control_run()
        for label, record, arms in (
            ("the default-shape pair", pair, (PAIR_DEFAULT_ARM, PAIR_REVEAL_ARM)),
            ("the six-seat pair", six, (SIX_PAIR_DEFAULT_ARM, SIX_PAIR_REVEAL_ARM)),
        ):
            with self.subTest(pair=label):
                self.assertEqual(
                    [str(name) for name in record.get("counterfactuals") or ()],
                    [member],
                    "the run's `counterfactuals` set holds the member its declaring arm "
                    "trained under, once and in the declared order, so a run says which "
                    "targets produced which curve (records.md §12, counterfactual.md §6, "
                    "D-43): %r" % (record.get("counterfactuals"),),
                )
                rows = {
                    str(row.get("name")): row for row in record["variants"]
                }
                self.assertEqual(
                    sorted(rows),
                    sorted(arms),
                    "the record carries one `variants` row per declared arm (records.md §12): "
                    "%r against %r" % (sorted(rows), sorted(arms)),
                )
                self.assertNotIn(
                    "counterfactual",
                    rows[arms[0]],
                    "the arm that declares no member carries **no** `counterfactual` key, "
                    "because absence is the member `none` and no key is invented for it — "
                    "records.md §12 makes the field conditional, which is what keeps a "
                    "default declaration's row at the shape its capture took "
                    "(counterfactual.md §6, §9, D-43): %r" % (sorted(rows[arms[0]]),),
                )
                self.assertEqual(
                    rows[arms[1]].get("counterfactual"),
                    member,
                    "and the declaring arm names the member it was trained under in its own "
                    "row (records.md §12, counterfactual.md §6, D-43): %r"
                    % (rows[arms[1]].get("counterfactual"),),
                )
                for name in arms:
                    self.assertEqual(
                        str(rows[name].get("learning_rule")),
                        str(rows[arms[0]].get("learning_rule")),
                        "the two arms are one rule and one utility and differ in the member "
                        "alone, so the record says which axis the pair moved "
                        "(counterfactual.md §6, records.md §12, D-3): %r against %r"
                        % (rows[name].get("learning_rule"),
                           rows[arms[0]].get("learning_rule")),
                    )
                    self.assertEqual(
                        str(rows[name].get("utility")),
                        str(rows[arms[0]].get("utility")),
                        "…and the utility is the same on both arms, so no second axis moved "
                        "beside the member (counterfactual.md §6, records.md §12, D-3): %r"
                        % (rows[name].get("utility"),),
                    )
        self.assertNotIn(
            "counterfactuals",
            control,
            "a configuration whose arms declare no member returns a record with **no** "
            "`counterfactuals` key at all, which is what keeps the shipped captures "
            "byte-identical (counterfactual.md §6, §9, records.md §12, D-43): %r"
            % (sorted(control),),
        )
        for row in control["variants"]:
            self.assertNotIn(
                "counterfactual",
                row,
                "and no `variants` row of it names the default either: a declaration naming "
                "nothing is the shape a default run's record keeps "
                "(counterfactual.md §6, §9, D-43): %r" % (sorted(row),),
            )

    def test_trnj_16_2_both_arms_name_one_pool_id_and_fairness_reads_the_member_axis(self):
        """TRNJ-16.2 the two arms train against one frozen pool id and `training.fairness` reports the `counterfactual` axis for the pair.

        `docs/L1/counterfactual.md` §6 and §7: the member rides opt-in per variant, so a
        paired arm differs only in it **on one frozen pool**, one seed set and one budget
        (D-3, ASM-16), and the pair is a comparison `training` reports rather than refuses —
        `fairness` names the one axis the pair differs on, which for this pair is
        `counterfactual` (`e2e-surface.md` §3.5, `rules.md` §8, `counterfactual.md` §6).  The
        case reads the run record's pool — one id and one membership for both arms — and then
        the report `fairness` gives for the same two variant entries, so the axis is the one
        the record's own arms make (`records.md` §12, D-43).
        """
        reveal = J.counterfactual_names()[1]
        configuration = pair_configuration(reveal)
        record = pair_run()
        pool = record["pool"]
        self.assertEqual(
            str(pool["id"]),
            PAIR_POOL,
            "the run trained against the frozen pool its configuration declared, and its "
            "record names that one id (records.md §12, e2e-surface.md §3.5, D-16): %r"
            % (pool.get("id"),),
        )
        self.assertTrue(
            bool(pool["frozen"]),
            "a pair's pool is frozen while it is used, which is how the parity of the two "
            "arms is read (records.md §8, §12, ASM-16): %r" % (pool,),
        )
        self.assertEqual(
            [str(row["name"]) for row in record["variants"]],
            [PAIR_DEFAULT_ARM, PAIR_REVEAL_ARM],
            "both arms are in the one record and both were trained, so one pool served the "
            "pair and not each arm its own (records.md §12, counterfactual.md §6, §7): %r"
            % (record["variants"],),
        )
        report = J.fairness(
            configuration["variants"][0], configuration["variants"][1]
        )
        self.assertIn(
            "axis",
            report,
            "fairness reports the one axis the pair differs on, and never labels the pair "
            "fair or unfair (e2e-surface.md §3.5, docs/L2/training/surface.md §5): %r"
            % (sorted(report),),
        )
        axis = report["axis"]
        differs = axis.get("differs") if isinstance(axis, dict) else axis
        fields = [J.token(item) for item in ([differs]
                                             if isinstance(differs, str) else differs)]
        self.assertEqual(
            fields,
            ["counterfactual"],
            "the two arms are identical but for the counterfactual member, so the axis "
            "fairness reports is that axis alone — one axis, named in both places, and the "
            "budget, the seed set, the architecture and the rule held constant beside it "
            "(counterfactual.md §6, rules.md §8, ladder.md §4, D-3): %r" % (axis,),
        )
        held = report.get("constants") or {}
        constants = J.token(
            " ".join(
                "%s %s" % (key, value)
                for key, value in (held.items() if isinstance(held, dict)
                                   else [("", held)])
            )
        )
        for token in ("budget", "seed", "param"):
            self.assertIn(
                token,
                constants,
                "and the report still states what the pair holds constant, %r among it, or a "
                "reader cannot see that only the member moved (rules.md §8, ladder.md §4, "
                "D-3): %r" % (token, report.get("constants")),
            )

    def test_trnj_16_3_the_six_seat_pair_names_the_member_on_the_shape_it_is_measured_on(self):
        """TRNJ-16.3 the same pair on `six-seat-no-limit-100` names the member in its set and in the declaring arm's row, on one pool of five members.

        `docs/L1/counterfactual.md` §8 declares the member on all three shapes and measures it
        on `six-seat-no-limit-100`, the one cell where a tabular learner folds 87 % and the
        product 0 % — and a six-seat hand seats five distinct opponents, so the pool must hold
        at least five members or the run is refused by name (`seats.md` §4, ASM-43, D-33,
        D-40, D-42).  The case is the third of the file's runs and the one that says the
        record's carriers behave the same on the shape the criterion reads
        (`records.md` §12, counterfactual.md §6, §8).
        """
        reveal = J.counterfactual_names()[1]
        configuration = six_pair_configuration(reveal)
        shape = str(configuration["game"])
        record = six_pair_run()
        self.assertEqual(
            str(record["game"]),
            shape,
            "the run record names the shape it played, and it is the catalogue's six-seat row "
            "(records.md §12, shapes.md §3, seats.md §2): %r" % (record.get("game"),),
        )
        self.assertEqual(
            [str(name) for name in record.get("counterfactuals") or ()],
            [reveal],
            "the `counterfactuals` set names the member on this shape too, because the third "
            "catalogue is the shape's own declaration and not a rung's "
            "(counterfactual.md §6, §8, records.md §12): %r"
            % (record.get("counterfactuals"),),
        )
        rows = {str(row.get("name")): row for row in record["variants"]}
        self.assertNotIn(
            "counterfactual",
            rows[SIX_PAIR_DEFAULT_ARM],
            "the silent arm's row names no member on the six-seat shape either: the "
            "conditionality is the record's and not the shape's (records.md §12, "
            "counterfactual.md §6, §9, D-43): %r" % (sorted(rows[SIX_PAIR_DEFAULT_ARM]),),
        )
        self.assertEqual(
            rows[SIX_PAIR_REVEAL_ARM].get("counterfactual"),
            reveal,
            "and the declaring arm names it (records.md §12, counterfactual.md §6, §8, D-43): "
            "%r" % (rows[SIX_PAIR_REVEAL_ARM].get("counterfactual"),),
        )
        self.assertEqual(
            str(record["pool"]["id"]),
            SIX_PAIR_POOL,
            "both arms trained against the one frozen pool the configuration declared "
            "(records.md §12, ASM-16, D-16): %r" % (record["pool"].get("id"),),
        )
        members = [str(member.get("id")) for member in record["pool"]["members"]]
        self.assertGreaterEqual(
            len(members),
            int(J.shaped_game_config(shape)["seats"]) - 1,
            "a six-seat hand draws five distinct opponents, so the frozen pool it trains "
            "against holds at least five members or the run is refused by name "
            "(seats.md §4, ASM-43, records.md §8): %r" % (members,),
        )


if __name__ == "__main__":
    unittest.main()
