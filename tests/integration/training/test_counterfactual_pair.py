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

**And the divergence D-45 repaired**, which is the fourth run here (`counterfactual.md` §10,
`records.md` §12, `docs/L1/battery.md` §3 FAM-23, D-45).  `strata/records/
counterfactual-divergence.md` recorded a six-seat run of this member, at the mixed pool and at
seed 2, dying with `agents.errors.LearningDiverged: learn(transitions): transition index 0
drove parameter index 17713 out of finite range and the learner has diverged, got -inf` — the
member's own update walking past the float64 range because nothing bounded a parameter's
magnitude.  §10 answers it with two bounds, and this file's half of that answer is the run:
the configuration that died, at the seed the record names, must now **either** complete with
every reported value finite **or** refuse by name, and the record states which
(`counterfactual.md` §10).  Both halves are measured here and asserted as measured — the
declared arithmetic completes, because the bound is not reachable inside the budget a case can
afford, and one run whose **declared rate is raised for its length** reaches the band inside
its first hand and is refused by name.  **The repair is measured twice over**, because the case
that owes it is not the guard: `TRNJ-16.4` reads the same configuration, pool, shape and seed at
the forty hands a battery may spend — §11's measurement is a 20,000-hand pass — and asserts the
outcome that budget actually gives, which is the completion, with the `finiteness` facts that
make it checkable (`counterfactual.md` §10, §11, `docs/L1/records.md` §12, FAM-23).  That
raised-rate run is the regression the record asks for: the same configuration, and the pre-fix
code wrote a non-finite parameter and reported it
(measured 2026-11-13, `got inf` at `1e7` and `got nan` at `1e8`), while the fixed code refuses
the step that leaves the band and reports no non-finite number at all.
"""

import copy
import importlib
import importlib.util
import math
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

#: The configuration `strata/records/counterfactual-divergence.md` recorded as fatal: six
#: seats, the frozen mixed pool of this battery's own support module, one variant declaring
#: **both** the member and the risk-averse utility, at the seed the record names.  The labels
#: and the pool id are this battery's own (`docs/L1/battery.md` §4, D-15); **seed 2 is the
#: record's**, and so is the pair — the record's run died at the first seed past 0 and 1.
DIVERGENCE_RUNG = "rung-invented-counterfactual-divergence-17"
DIVERGENCE_ARM = "arm-invented-counterfactual-shortfall-17"
DIVERGENCE_POOL = "pool-invented-counterfactual-divergence-17"
DIVERGENCE_SEED = 2

#: The two budgets of the divergence case: both are `training.run`'s smallest accepted budget
#: of ten hands (`docs/L1/records.md` §12's ten snapshot intervals, measured — the run refuses
#: anything below it), which is what keeps the case inside the three minutes a battery case may
#: cost (`docs/L1/battery.md` §2, ASM-18).
DIVERGENCE_BUDGET = 10
DIVERGENCE_GUARDED_BUDGET = 10

#: The declared rate the guard run raises for its own length and this case restores: the
#: shipped `learning_rate` stands as declared for every other case, exactly as AGT-16.3 holds
#: `agents.declarations.HYPER` (`docs/L3/agents/divergence.md` §1, §4).  An invented instance;
#: at `1e7` one step of the member's own update lands past the declared band and the pre-fix
#: code overflowed to `inf` here (measured 2026-11-13, see the case).
DIVERGENCE_GUARD_RATE = 1e7

#: The budget TRNJ-16.4 measures the repaired configuration at.  `counterfactual.md` §11's
#: measurement is a 20,000-hand pass at seeds 2 and 3, which no battery case may spend; the
#: case reads the **same** configuration — one shape, one member, one utility, one pool, one
#: seed — at **forty hands**, the smallest budget that keeps the ten snapshot intervals and
#: exercises the same path, measured 2026-11-13 at ≈19 s of wall clock (Python 3.12, the
#: project venv, beside two other batteries).  An invented budget of this battery's
#: (`docs/L1/battery.md` §2, §4, D-15, D-45).
DIVERGENCE_REPAIR_BUDGET = 40


def divergence_configuration():
    """The recorded divergence's configuration: six seats, the mixed pool, member **and** utility.

    `strata/records/counterfactual-divergence.md` and D-45 describe the run that died: the
    catalogue's six-seat shape, a frozen mixed pool of folders, raisers and callers, one
    variant trained under the revealed counterfactual **and** the risk-averse utility, at seed
    2.  The pool here is the mixed one this battery's support module already declares — D-6's
    three anchors and two of D-21's three folders, five members, the least a six-seat hand's
    draw of five distinct opponents can be satisfied from (`seats.md` §4, ASM-43, `records.md`
    §8, D-21) — and the variant is R1's own entry, unchanged but for the shape, the two
    catalogue selections and the budget, so nothing but the member and the utility is this
    case's invention (`counterfactual.md` §6, §8, §10, D-33, D-45).
    """
    reveal = J.counterfactual_names()[1]
    shaped_utility = J.utility_names()[1]
    shape = J.third_shape()
    template = copy.deepcopy(J.variant_entry(J.rung("R1"), "naive-numeric"))
    template["samples"] = DIVERGENCE_BUDGET
    template["seeds"] = [DIVERGENCE_SEED]
    template["snapshot_every"] = max(1, DIVERGENCE_BUDGET // J.SNAPSHOT_POINTS)
    template.pop("counterfactual", None)
    template["name"] = DIVERGENCE_ARM
    template["counterfactual"] = reveal
    template["utility"] = shaped_utility
    template["game"] = shape
    return {
        "name": DIVERGENCE_RUNG,
        "axis": "the counterfactual member, at one architecture",
        "carried_from": None,
        "primary": DIVERGENCE_ARM,
        "game": shape,
        "variants": [template],
        "pool": {
            "id": DIVERGENCE_POOL,
            "lineage": None,
            "m": 5,
            "frozen": True,
            "members": [],
            "baselines": [str(name) for name in J.folders()[:2]],
        },
        "seeds": [DIVERGENCE_SEED],
        "samples": DIVERGENCE_BUDGET,
        "param_budget": int(template["param_budget"]),
        "table": "live",
        "device": "cpu",
        "snapshot_every": max(1, DIVERGENCE_BUDGET // J.SNAPSHOT_POINTS),
    }


def divergence_repair_configuration():
    """The same configuration at the budget a battery case can spend (`counterfactual.md` §11).

    One helper, so the case that reads the recorded divergence and the case that measures the
    repair cannot drift apart in the shape, the member, the utility, the pool or the seed: the
    only thing this function moves is `divergence_configuration()`'s budget — from
    `training.run`'s smallest accepted ten hands to :data:`DIVERGENCE_REPAIR_BUDGET` — in the
    variant entry, the configuration and the snapshot interval, exactly as the run reads them
    (`records.md` §2, §12, `docs/L1/battery.md` §2, §4, D-15, D-45).
    """
    configuration = divergence_configuration()
    interval = max(1, DIVERGENCE_REPAIR_BUDGET // J.SNAPSHOT_POINTS)
    configuration["samples"] = DIVERGENCE_REPAIR_BUDGET
    configuration["snapshot_every"] = interval
    for entry in configuration["variants"]:
        entry["samples"] = DIVERGENCE_REPAIR_BUDGET
        entry["snapshot_every"] = interval
    return configuration


def run_outcome(call):
    """One run's outcome: `("completed", record)` or `("refused", exception)`.

    `counterfactual.md` §10 allows two outcomes for the recorded configuration — a run that
    completes with finite values, or a refusal by name — and a case has to say which one
    happened, so the call is made once and both halves of the alternative are kept
    (`docs/L1/battery.md` §3 FAM-23).
    """
    try:
        return ("completed", call())
    except Exception as exc:  # the refusal this case is about, or a defect it fails on
        return ("refused", exc)


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


def divergence_runs():
    """The recorded divergence twice: `(declared, guarded)` outcomes, built once per process.

    The first run is the configuration as the record states it, at the declared rate; the
    second is the same configuration, seed and budget with `agents.declarations.HYPER`'s
    `learning_rate` raised for its length only — restored in a `finally` before this function
    returns, so no case of this battery ever runs under a moved catalogue
    (`docs/L3/agents/divergence.md` §1, §4, AGT-16.3).  Both outcomes are measured and both are
    read by TRNJ-17.1: a run either completes with finite values or refuses by name, and the
    case says which one each of these did (`counterfactual.md` §10, `docs/L1/battery.md` §3
    FAM-23, D-45).
    """
    if "divergence" not in _RUNS:
        configuration = divergence_configuration()
        declared = run_outcome(
            lambda: J.run(
                configuration, seeds=[DIVERGENCE_SEED], budget=DIVERGENCE_BUDGET
            )
        )
        declarations = importlib.import_module("agents.declarations")
        shipped = declarations.HYPER["learning_rate"]
        try:
            declarations.HYPER["learning_rate"] = DIVERGENCE_GUARD_RATE
            guarded = run_outcome(
                lambda: J.run(
                    configuration,
                    seeds=[DIVERGENCE_SEED],
                    budget=DIVERGENCE_GUARDED_BUDGET,
                )
            )
        finally:
            declarations.HYPER["learning_rate"] = shipped
        _RUNS["divergence"] = (declared, guarded)
    return _RUNS["divergence"]


def divergence_repair_run():
    """The repaired configuration's one run at this case's budget, built once per process.

    `counterfactual.md` §11 measures the repair on a 20,000-hand pass; a battery case spends
    forty hands of the same configuration instead, and takes the run's outcome whole —
    `("completed", record)` or `("refused", exception)` — because §10 allows the recorded
    configuration both answers and the case has to say which one it got
    (`counterfactual.md` §10, §11, `docs/L1/battery.md` §2, §3 FAM-23, D-45).
    """
    if "repair" not in _RUNS:
        _RUNS["repair"] = run_outcome(
            lambda: J.run(
                divergence_repair_configuration(),
                seeds=[DIVERGENCE_SEED],
                budget=DIVERGENCE_REPAIR_BUDGET,
            )
        )
    return _RUNS["repair"]


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

    # -- TRNJ-16.4 ---------------------------------------------------------
    def test_trnj_16_4_the_recorded_divergence_completes_finite_at_the_budget_a_case_can_spend(self):
        """TRNJ-16.4 the configuration that died with `-inf` — six seats, `reveal-counterfactual` with `stack-shortfall`, mixed pool, seed 2 — completes at the budget a case can spend with every value it reports finite, and its `finiteness` row names the member, counts what the member used and holds the largest target inside the bound in force (`docs/L1/counterfactual.md` §10, §11, `docs/L1/records.md` §12, D-45, `docs/L1/battery.md` §3 FAM-23).

        `strata/records/counterfactual-divergence.md` recorded this configuration dying on its
        first transition of seed 2 — `LearningDiverged … got -inf`, a parameter walked past the
        float64 range because nothing bounded its magnitude.  §10 answers it with two bounds and
        §11 measures the answer on the seed that died: at **20,000 hands** seeds 2 and 3 both
        complete, with 6,024 and 6,660 resolved transitions, 32,415 and 35,445 member updates, a
        largest counterfactual target of **0.966** and **0.994** against a bound of **600**, a
        largest `|td_error|` of 0.248 and 0.296, and no refusal; a 200-hand run at seed 2
        completes too, with max `|θ|` 0.946, max `|δ|` 1.42 and no non-finite value anywhere.

        **Measured 2026-11-13** on the budget this case spends (Python 3.12, the project venv,
        ≈19 s of wall clock): the same configuration, the same frozen pool and the same seed at
        **forty hands** — an invented budget of this battery's, because 20,000 is a day of wall
        clock — **completes**, with no refusal, 38–40 resolved transitions and 201–210 member
        updates off a fold set that moves with `PYTHONHASHSEED`, a largest target of 0.915
        against the bound of 600, and every number of its record finite.  The budget is forty
        and not ten because the case is the repair and not the guard: it reads the member's own
        path far enough past the first hand that the record's `finiteness` row is a count and
        not a single hand's accident, and the same path is what §11's pass measures at length
        (`docs/L1/battery.md` §2, §4, D-15, D-45).

        §10 allows the recorded configuration **either** answer, so the case takes the run's
        outcome whole and validates the half it did not get first: a refusal has to arrive as
        one of §10's two named refusals — `agents.errors.CounterfactualUnbounded` for a value
        outside the chips in play, `agents.errors.LearningDiverged` for a parameter beyond the
        declared band — has to state the bound it crossed, and has to report no non-finite
        number.  Then it asserts the outcome §11 measures, which at this budget is the
        completion, and reads out of the record the facts that make the completion checkable:
        the `finiteness` block is present, keyed by the one variant that declared the member and
        by the one seed, names `reveal-counterfactual`, counts a positive `transitions` and
        `steps`, and holds its `largest_target` inside the `target_bound` the shape's own chips
        in play set.
        """
        declarations = importlib.import_module("agents.declarations")
        errors = importlib.import_module("agents.errors")
        configuration = divergence_repair_configuration()
        shape = str(configuration["game"])
        member = J.counterfactual_names()[1]
        outcome, value = divergence_repair_run()

        # 1. The other half of §10's alternative, validated first: a refusal is by name, it
        #    states the bound it crossed, and it reports no non-finite number.
        if outcome == "refused":
            refusal = value
            self.assertIsInstance(
                refusal,
                (errors.CounterfactualUnbounded, errors.LearningDiverged),
                "a run of the recorded configuration that does not complete is refused by one "
                "of the two names §10 gives its two bounds — CounterfactualUnbounded outside "
                "the chips in play, LearningDiverged beyond the declared parameter band — and "
                "this one arrived as %s: %r"
                % (type(refusal).__name__, str(refusal)),
            )
            message = str(refusal)
            lowered = message.lower()
            for spelling in ("inf", "nan"):
                self.assertNotIn(
                    spelling,
                    lowered,
                    "no refusal of the member reports a non-finite number, which is exactly "
                    "what the recorded divergence's message did and one half of what §10 "
                    "repairs (counterfactual.md §10, docs/L3/agents/divergence.md §2): %r"
                    % (message,),
                )
            chips = float(
                int(J.shaped_game_config(shape)["seats"])
                * int(J.shaped_game_config(shape)["starting_stack"])
            )
            stated = numbers_in(message)
            self.assertTrue(
                any(
                    abs(number - bound) <= bound * 1e-9
                    for bound in (chips, float(declarations.PARAMETER_BAND))
                    for number in stated
                ),
                "the refusal names the bound the step crossed — the chips in play %r of %r, or "
                "the declared band %r, read from engine.game_config and agents.declarations "
                "and never restated here — and the numbers it states are %r: %r"
                % (chips, shape, float(declarations.PARAMETER_BAND), stated, message),
            )
            for number in stated:
                self.assertTrue(
                    math.isfinite(float(number)),
                    "and every number the refusal states is finite (counterfactual.md §10): %r "
                    "in %r" % (number, message),
                )

        # 2. And the outcome §11 measures at this budget, which is the completion.
        self.assertEqual(
            outcome,
            "completed",
            "the recorded configuration — six seats, one variant declaring the member **and** "
            "the risk-averse utility, the frozen mixed pool of five members, at seed %d — "
            "COMPLETES at the budget of %d hands this case spends, with no refusal: §11 "
            "measures the same configuration completing at 20,000 hands on this seed, and this "
            "run %r (counterfactual.md §10, §11, D-45, docs/L1/battery.md §3 FAM-23)"
            % (DIVERGENCE_SEED, DIVERGENCE_REPAIR_BUDGET, outcome),
        )
        record = value
        for number in walk_numbers(record):
            self.assertTrue(
                math.isfinite(float(number)),
                "every number the completed run reports is finite, which is the outcome "
                "counterfactual.md §10 allows beside a refusal by name — and the recorded "
                "divergence reported a non-finite one instead: %r" % (number,),
            )

        # 3. The record's own account of the repair.
        block = record.get("finiteness")
        self.assertIsInstance(
            block,
            dict,
            "a run declaring a member carries the `finiteness` block records.md §12 makes "
            "conditional on exactly that (counterfactual.md §10, D-45): %r"
            % (sorted(str(key) for key in record),),
        )
        self.assertEqual(
            sorted(str(name) for name in block),
            [DIVERGENCE_ARM],
            "the block carries one row per variant and seed, keyed by the variant that "
            "declared the member, so the counts are attributable to it (records.md §12, "
            "counterfactual.md §10): %r" % (block,),
        )
        per_seed = block[DIVERGENCE_ARM]
        self.assertEqual(
            sorted(str(key) for key in per_seed),
            [J.seed_key(DIVERGENCE_SEED)],
            "and the row is the one seed this case ran, keyed as the record keys every "
            "per-seed sub-record (records.md §12, docs/L3/training/loop.md §4): %r"
            % (per_seed,),
        )
        row = per_seed[J.seed_key(DIVERGENCE_SEED)]
        self.assertEqual(
            str(row.get("member")),
            member,
            "the row names the member the variant trained under, so a reader sees which "
            "targets the counts belong to (counterfactual.md §6, §10, records.md §12): %r"
            % (row.get("member"),),
        )
        self.assertGreater(
            int(row["transitions"]),
            0,
            "the member resolved transitions on this run, or the block would be counting a "
            "path no episode of it took (counterfactual.md §10, records.md §12): %r" % (row,),
        )
        self.assertGreater(
            int(row["steps"]),
            0,
            "and it took its own steps on them — `A` per transition under §6's contract — so "
            "the row counts the member's updates and not the run's hands "
            "(counterfactual.md §6, §10, records.md §12): %r" % (row,),
        )
        self.assertTrue(
            math.isfinite(float(row["largest_target"])),
            "the largest target the member was handed is a finite number, which is the claim "
            "§10's first bound makes and the pre-fix code broke (counterfactual.md §10): %r"
            % (row.get("largest_target"),),
        )
        self.assertLessEqual(
            abs(float(row["largest_target"])),
            float(row["target_bound"]),
            "every target the member was handed lies inside the bound in force, which is what "
            "makes this a finite completion and not the walk the record measured "
            "(counterfactual.md §10, §11, records.md §12): %r" % (row,),
        )
        seats = int(J.shaped_game_config(shape)["seats"])
        stack = int(J.shaped_game_config(shape)["starting_stack"])
        self.assertEqual(
            float(row["target_bound"]),
            float(seats * stack),
            "…and the bound in force is the shape's own chips in play, `seats × "
            "starting_stack` — %d on %r — read off engine.game_config and never written down "
            "here (counterfactual.md §10, shapes.md §2, seats.md §2, ASM-28): the row states %r"
            % (seats * stack, shape, row["target_bound"]),
        )

    # -- TRNJ-17.1 ---------------------------------------------------------
    def test_trnj_17_1_the_recorded_divergence_completes_finite_and_refuses_by_name(self):
        """TRNJ-17.1 the six-seat divergence of `strata/records/counterfactual-divergence.md` — member **and** risk-averse utility, mixed pool, seed 2 — completes with every reported value finite at the declared arithmetic, and a run whose declared rate is raised past the band is refused by name, naming the band and reporting no non-finite number (`docs/L1/counterfactual.md` §10, §6, `docs/L1/records.md` §12, D-45, `docs/L1/battery.md` §3 FAM-23).

        The record's run died on `LearningDiverged … got -inf`: the member's own update walked
        past the float64 range because nothing bounded a parameter's magnitude.  §10 answers it
        with a target bound and a parameter band, and allows the recorded configuration two
        outcomes — complete with finite values, or refuse by name — so this case measures both
        and asserts which one happens.

        **Measured 2026-11-13** (Python 3.12, the project venv): at the declared
        `learning_rate` of `agents.declarations.HYPER` the run completes in ≈7 s with all 330
        numbers of its record finite and a `finiteness` row of 10 resolved transitions, 52
        steps, a largest target of 0.92 and a bound of 600 — the bound is not reachable inside
        the budget a case can afford, for the same reason the record's own run needed the full
        20,000-hand pass: at the declared rate the member's largest parameter settles at
        `≈1.5e3` on `net-chips` and at `≈1.0` on `stack-shortfall` and then stands still
        (measured at 20, 40, 80 and 160 hands on the first and at 20, 40, 80, 160 and 320 on the
        second, in a pre-fix checkout).  With the declared rate raised to `1e7` for one run, the
        pre-fix code wrote a non-finite parameter and reported it (`… drove parameter index 36
        out of finite range and the learner has diverged, got inf`; `1e8` gave `got nan`),
        while the fixed code refuses **the step that leaves the band** — `… drove parameter
        index 0 to -835614151047404.6, beyond the declared parameter band 1000000.0 …` — a
        finite value and a named bound, which is the regression this case is.

        The case therefore asserts four things: the declared run **completes**; every number
        of its record is finite and its `finiteness` row holds its target inside the chips in
        play of the shape that played; the raised-rate run **refuses** as
        `agents.errors.LearningDiverged`, naming the declared band and stating only finite
        numbers; and the rate is back where the catalogue declared it afterwards
        (`docs/L3/agents/divergence.md` §1, §4).
        """
        declarations = importlib.import_module("agents.declarations")
        errors = importlib.import_module("agents.errors")
        band = float(declarations.PARAMETER_BAND)
        shipped = float(declarations.HYPER["learning_rate"])
        configuration = divergence_configuration()
        shape = str(configuration["game"])
        declared, guarded = divergence_runs()

        # 1. The recorded configuration, at the declared arithmetic, completes — and every
        #    number it reports is finite.
        self.assertEqual(
            declared[0],
            "completed",
            "the recorded configuration — six seats, the frozen mixed pool, one variant "
            "declaring the member **and** the risk-averse utility, at seed %d — COMPLETES at "
            "the declared rate, and this run %r (counterfactual.md §10, D-45): measured "
            "2026-11-13 at the budget of %d hands"
            % (DIVERGENCE_SEED, declared[0], DIVERGENCE_BUDGET),
        )
        record = declared[1]
        for number in walk_numbers(record):
            self.assertTrue(
                math.isfinite(float(number)),
                "every number the completed run reports is finite, which is the outcome "
                "counterfactual.md §10 allows beside a refusal by name: %r" % (number,),
            )
        block = record.get("finiteness")
        self.assertIsInstance(
            block,
            dict,
            "a run declaring a member carries the `finiteness` block records.md §12 makes "
            "conditional on exactly that (counterfactual.md §10, D-45): %r"
            % (sorted(str(key) for key in record),),
        )
        rows = [
            inner
            for per_seed in block.values()
            for inner in (per_seed.values() if isinstance(per_seed, dict) else ())
        ]
        self.assertTrue(
            rows,
            "the block states one row per variant per seed, carrying the member, the "
            "transitions it resolved, its steps, the largest target it was handed and the "
            "bound in force (records.md §12, counterfactual.md §10): %r" % (block,),
        )
        seats = int(J.shaped_game_config(shape)["seats"])
        stack = int(J.shaped_game_config(shape)["starting_stack"])
        for row in rows:
            self.assertEqual(
                str(row.get("member")),
                J.counterfactual_names()[1],
                "the row names the member the variant declared (counterfactual.md §6, §10): "
                "%r" % (row.get("member"),),
            )
            self.assertLessEqual(
                abs(float(row["largest_target"])),
                float(row["target_bound"]),
                "every target the member was handed lies inside the bound in force, which is "
                "the claim §10's first bound makes and the record states (counterfactual.md "
                "§10, records.md §12): %r" % (row,),
            )
            self.assertEqual(
                float(row["target_bound"]),
                float(seats * stack),
                "the bound in force is the shape's own chips in play, `seats × starting_stack` "
                "— %d on %r — read off engine.game_config and never written down here "
                "(counterfactual.md §10, shapes.md §2, seats.md §2, ASM-28): the row states %r"
                % (seats * stack, shape, row["target_bound"]),
            )

        # 2. The same configuration with the declared rate raised for one run: the step that
        #    would leave the band is refused by name, and the refusal reports no non-finite
        #    number.
        self.assertEqual(
            guarded[0],
            "refused",
            "the same configuration at seed %d with the declared rate raised to %r REFUSES by "
            "name — measured 2026-11-13 — and this run %r (counterfactual.md §10, D-45)"
            % (DIVERGENCE_SEED, DIVERGENCE_GUARD_RATE, guarded[0]),
        )
        refusal = guarded[1]
        self.assertIsInstance(
            refusal,
            errors.LearningDiverged,
            "a step that would leave the declared parameter band is refused as "
            "agents.errors.LearningDiverged, the name counterfactual.md §10 gives that "
            "refusal, and it arrived as %s: %r"
            % (type(refusal).__name__, str(refusal)),
        )
        message = str(refusal)
        lowered = message.lower()
        self.assertIn(
            "band",
            lowered,
            "the refusal names the band the step crossed, so a reader can see which envelope "
            "the learner left (counterfactual.md §10): %r" % (message,),
        )
        stated = numbers_in(message)
        self.assertTrue(
            any(abs(number - band) <= band * 1e-9 for number in stated),
            "the refusal names the declared band, %r — read from agents.declarations and "
            "never restated here — and the numbers it states are %r: %r"
            % (band, stated, message),
        )
        for spelling in ("inf", "nan"):
            self.assertNotIn(
                spelling,
                lowered,
                "no refusal of the member reports a non-finite number: this is the whole of "
                "§10's second bound, and the recorded divergence's message carried one "
                "(counterfactual.md §10, docs/L3/agents/divergence.md §2): %r" % (message,),
            )
        for number in stated:
            self.assertTrue(
                math.isfinite(float(number)),
                "and every number the refusal states is finite (counterfactual.md §10): %r "
                "in %r" % (number, message),
            )
        self.assertEqual(
            float(declarations.HYPER["learning_rate"]),
            shipped,
            "the declared rate is back where the catalogue declared it, so no case of this "
            "battery runs under a moved declaration (docs/L3/agents/divergence.md §1, §4): %r "
            "against %r" % (declarations.HYPER["learning_rate"], shipped),
        )


def walk_numbers(value, depth=0):
    """Every number inside one record, however it is nested (`records.md` §1's mappings)."""
    found = []
    if depth > 24:
        return found
    if isinstance(value, bool) or value is None or isinstance(value, (str, bytes)):
        return found
    if isinstance(value, (int, float)):
        return [value]
    if isinstance(value, dict):
        for inner in value.values():
            found.extend(walk_numbers(inner, depth + 1))
        return found
    if isinstance(value, (list, tuple, set, frozenset)):
        for inner in value:
            found.extend(walk_numbers(inner, depth + 1))
    return found


def numbers_in(text):
    """Every number one refusal message states, read by value and not by one spelling of it.

    `docs/L3/agents/errors.md` §3 leaves a refusal's wording to the implementation, so a case
    that asserts "the message names the band" reads the numbers it states: an integer, a
    decimal part and an exponent are one number here.
    """
    import re

    found = []
    for token in re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", str(text)):
        try:
            found.append(float(token))
        except ValueError:  # pragma: no cover - the pattern admits no such token
            continue
    return found


if __name__ == "__main__":
    unittest.main()
