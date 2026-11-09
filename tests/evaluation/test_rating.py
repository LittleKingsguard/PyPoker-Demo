"""EVL-5 — the fitted rating: `rating`.

Drives `docs/L3/evaluation/rating.md` §1-§7, `docs/L2/evaluation/surface.md` §11 and
`docs/L1/league.md` §5: one value and a 95% interval containing it per matrix member,
`method == "Bradley-Terry"`, the anchor fixing the three baselines' mean at 0,
`hands_per_cell x (K-1)` hands behind every value, the bootstrap recorded by its seed
(the `_bootstrap_seed(table_seed)` derivation) and `converged` recorded, and the
bound -- the largest `|theta|` the fit may return, `rating.BOUND = 10.0` -- applied to
a member with no finite maximum-likelihood value, with its interval widened so the
value stays inside it (`rating.md` §3-§4, G17, G18).

`rating` reads only its record's five required keys and fits a hand-built table as
readily as a played one (`rating.md` §1, `surface.md` §11), so the arithmetic cases
here are hand-built `records.md` §10 records and the integration cases use the
battery's cached real `k4` table. The refusals are `rating.md` §6's seven checks, in
its order, and nothing is fitted when one fires.

One note on EVL-5.5: `rating.md` §3 states one iteration in five steps -- the MM
increment for every member with `W_a > 0`, its addition, the ±`BOUND` clamp, then the
anchor's shift **and, after it, the two ends pinned** (`W_a == 0` at `-BOUND`, `W_a ==
n_a` at `+BOUND`, `bound_applied` set), then the convergence test. The pin comes after
the shift, so the value the record carries is the bound itself and not what the shift
left of it, and a member at either end is pinned on the first iteration. The case
asserts that stated outcome (a finite value at the bound, `bound_applied` True, the
member's own `bounded` True, the value inside its widened interval), which is what
`league.md` §5, `records.md` §11 and the L1 battery's FAM-9.6 require of a member with
no finite maximum-likelihood value. It deliberately does not assert `converged` for
that table: `converged` is step 5's own claim about reaching a stationary point within
`TOLERANCE`, driven where nothing is pinned (`EVL-5.9`), and the one table on which
step 4's pin and the anchor cannot both hold -- the one whose pinned member is itself
a baseline -- is declared Unverified in `guardrails.md` G15 and driven by no case. The
pin is what this case owns; the convergence test has its own case.
"""

import copy
import unittest

from _evaluation_support import (
    BASELINES,
    HANDS_PER_CELL,
    TABLE_SEED_HAND,
    EvaluationCase,
    all_ties,
    balanced,
    bootstrap_seed,
    champion_lost_everything,
    champion_won_everything,
    count,
    declared_internal,
    entry_bounded,
    entry_hands,
    entry_value,
    hand_matrix,
    interval_bounds,
    lopsided,
    matrix_cells,
    matrix_member_ids,
    no_file_reads,
    rating_entries,
)


def mean(values):
    """The arithmetic mean of a sequence of numbers."""
    values = list(values)
    return sum(values) / float(len(values))


class RatingTest(EvaluationCase):
    def test_evl_5_1_one_value_and_interval_and_hands_for_every_member(self):
        """EVL-5.1 `values` carries one entry per matrix member with a fitted value, a 95% interval containing it and the hands behind it; `method` is the Bradley-Terry string and `anchor` names the three baselines' mean at 0 (`rating.md` §5, `records.md` §11, FAM-9.1)."""
        package = self.evaluation()
        matrix = hand_matrix(balanced)
        rating = package.rating(matrix)
        members = matrix_member_ids(matrix)
        for key in ("values", "method", "anchor", "bound_applied", "bootstrap_seed", "converged"):
            with self.subTest(key=key):
                self.assertIn(
                    key,
                    rating,
                    "the rating record carries records.md §11's required key %r, and the "
                    "six required keys come first (rating.md §5): %r" % (key, tuple(rating)),
                )
        entries = rating_entries(rating)
        self.assertEqual(
            set(entries),
            set(members),
            "the rating carries one entry per matrix member, keyed by the member's id "
            "(records.md §11, surface.md §11): %r" % (sorted(entries),),
        )
        for member in members:
            with self.subTest(member=member):
                entry = entries[member]
                value = entry_value(entry)
                low, high = interval_bounds(entry)
                self.assertLessEqual(
                    low,
                    value,
                    "the fitted value lies inside its own 95%% interval "
                    "(rating.md §4, records.md §11, FAM-9.2): %r" % (entry,),
                )
                self.assertGreaterEqual(
                    high,
                    value,
                    "the fitted value lies inside its own 95%% interval "
                    "(rating.md §4, records.md §11, FAM-9.2): %r" % (entry,),
                )
                self.assertGreaterEqual(
                    entry_hands(entry),
                    0,
                    "an entry states the hands behind its value (records.md §11): %r"
                    % (entry,),
                )
        self.assertEqual(
            rating["method"],
            "Bradley-Terry",
            "the fitted method is the one string `Bradley-Terry`, the same "
            "protocol()['rating']['method'] declares (rating.md §5, "
            "declarations.md §2.2): %r" % (rating["method"],),
        )
        lowered = str(rating["anchor"]).lower()
        for word in ("baseline", "mean"):
            with self.subTest(anchor=word):
                self.assertIn(
                    word,
                    lowered,
                    "the anchor names the rule it applies: the three baselines' mean "
                    "fixed at 0 (rating.md §2, §5, league.md §5): %r" % (rating["anchor"],),
                )

    def test_evl_5_2_the_three_baselines_mean_is_anchored_at_zero(self):
        """EVL-5.2 the anchor sets the three baselines' mean value to 0 -- applied after every iteration, so the mean is 0 and every value reads as a distance from that standard (`rating.md` §2-§3, league.md §5, ASM-17, G15, FAM-9.4)."""
        tables = (
            ("a hand-built table", lambda: self.evaluation().rating(hand_matrix(lopsided))),
            ("a played table", lambda: self.shared_rating("k4")),
        )
        for label, fitted in tables:
            rating = fitted()
            entries = rating_entries(rating)
            baselines = [entry_value(entries[name]) for name in BASELINES]
            with self.subTest(table=label):
                self.assertAlmostEqual(
                    mean(baselines),
                    0.0,
                    places=3,
                    msg="the anchor fixes the three baselines' mean at 0, so every value "
                    "reads as a distance from the only fixed standard in the table "
                    "(rating.md §2-§3, league.md §5, G15): %r" % (baselines,),
                )
                self.assertLess(
                    abs(mean(baselines)),
                    1e-6,
                    "the anchor's shift is applied after every iteration, so the three "
                    "baselines' mean is exactly 0 and not merely close (rating.md §3 "
                    "step 4, G15): %r" % (baselines,),
                )

    def test_evl_5_3_every_value_carries_hands_per_cell_times_k_minus_one_hands(self):
        """EVL-5.3 an entry's `hands` is `hands_per_cell x (K-1)` -- one cell against each other member -- so no member's row is measured more precisely than another's (`rating.md` §5, `records.md` §11, FAM-9.5)."""
        tables = (
            (
                "a hand-built four-member table",
                hand_matrix(balanced),
                lambda matrix: self.evaluation().rating(matrix),
            ),
            (
                "a played four-member table",
                self.shared_matrix("k4"),
                lambda matrix: self.shared_rating("k4"),
            ),
        )
        for label, matrix, fitted in tables:
            rating = fitted(matrix)
            entries = rating_entries(rating)
            members = matrix_member_ids(matrix)
            expected = count(matrix["hands_per_cell"], "hands_per_cell") * (len(members) - 1)
            with self.subTest(table=label):
                for member in members:
                    self.assertEqual(
                        entry_hands(entries[member]),
                        expected,
                        "each value carries hands_per_cell x (K-1) hands, one cell against "
                        "each other member (rating.md §5, records.md §11, FAM-9.5): %r for "
                        "%r" % (entry_hands(entries[member]), member),
                    )

    def test_evl_5_4_one_matrix_gives_one_rating_and_one_bootstrap_seed(self):
        """EVL-5.4 two `rating` calls on one matrix are equal value for value, `bootstrap_seed` is recorded and equal for the same matrix, and `converged`/`bound_applied` are recorded flags (`surface.md` §11, `rating.md` §4-§5, FAM-9.2)."""
        package = self.evaluation()
        matrix = hand_matrix(lopsided)
        first = package.rating(matrix)
        second = package.rating(matrix)
        self.assertEqual(
            first,
            second,
            "one matrix gives one rating: the fit is deterministic and the bootstrap is "
            "seeded from the table seed (surface.md §11, rating.md §4)",
        )
        self.assertEqual(
            count(first["bootstrap_seed"], "a rating's bootstrap_seed"),
            count(second["bootstrap_seed"], "a rating's bootstrap_seed"),
            "the bootstrap seed is recorded and equal for one matrix, so the interval "
            "can be re-run (surface.md §11, rating.md §4)",
        )
        for key in ("bound_applied", "converged"):
            with self.subTest(flag=key):
                self.assertIsInstance(
                    first[key],
                    bool,
                    "the rating records %r as a boolean (records.md §11, rating.md §5): %r"
                    % (key, first[key]),
                )
        self.assertFalse(
            bool(first["bound_applied"]),
            "a table where every member won some hand has a finite fit, so no bound is "
            "applied (rating.md §3, FAM-9.6): %r" % (first["bound_applied"],),
        )

    def test_evl_5_5_a_member_with_no_finite_value_is_bounded_not_infinite(self):
        """EVL-5.5 a member that won (or lost) every hand of every cell has no finite maximum-likelihood value: the fit holds it at `BOUND`, flags that it bounded a member, and its value stays inside the widened interval (`rating.md` §3-§4, `records.md` §11, G17, FAM-9.6)."""
        package = self.evaluation()
        bound = float(declared_internal("rating", "BOUND"))
        self.assertEqual(
            bound,
            10.0,
            "rating.py fixes BOUND = 10.0, the largest |theta| the fit may return "
            "(rating.md §3, G17): %r" % (bound,),
        )
        cases = (
            ("won every hand", hand_matrix(champion_won_everything), bound),
            ("lost every hand", hand_matrix(champion_lost_everything), -bound),
        )
        for label, matrix, expected in cases:
            rating = package.rating(matrix)
            entries = rating_entries(rating)
            entry = entries["variant-1"]
            value = entry_value(entry)
            low, high = interval_bounds(entry)
            with self.subTest(case=label):
                self.assertTrue(
                    bool(rating["bound_applied"]),
                    "the fit bounded a member with no finite maximum-likelihood value "
                    "and records that it did (rating.md §3, records.md §11, G17, "
                    "FAM-9.6): %r" % (rating["bound_applied"],),
                )
                self.assertTrue(
                    entry_bounded(entry),
                    "that member's own `bounded` flag says the evidence pinned it "
                    "(rating.md §5, G17): %r" % (entry,),
                )
                self.assertLessEqual(
                    abs(value - expected),
                    0.01,
                    "the clamp holds the member at BOUND %r, so it reports a value at "
                    "the bound and never an infinity (rating.md §3, G17, FAM-9.6): %r"
                    % (expected, value),
                )
                self.assertLessEqual(
                    low,
                    value,
                    "the widened interval still contains the bounded value, so its bound "
                    "is never broken open (rating.md §4, G17): %r" % (entry,),
                )
                self.assertGreaterEqual(
                    high,
                    value,
                    "the widened interval still contains the bounded value "
                    "(rating.md §4, G17): %r" % (entry,),
                )

    def test_evl_5_6_the_interval_is_widened_to_hold_the_value_and_the_constants_are_the_design_s(self):
        """EVL-5.6 `RESAMPLES = 200`, `TOLERANCE = 1e-10` and `MAX_ITERATIONS = 10000` are `rating.py`'s declared constants, and the widening -- `lower = min(lower, value)`, `upper = max(upper, value)` -- keeps every value inside its interval (`rating.md` §3-§4, §7, G18)."""
        resamples = int(declared_internal("rating", "RESAMPLES"))
        tolerance = float(declared_internal("rating", "TOLERANCE"))
        iterations = int(declared_internal("rating", "MAX_ITERATIONS"))
        self.assertEqual(
            resamples,
            200,
            "the bootstrap draws RESAMPLES = 200 replicates (rating.md §4, G18): %r"
            % (resamples,),
        )
        self.assertEqual(
            tolerance,
            1e-10,
            "TOLERANCE = 1e-10 is the largest |delta theta| a step may move and still "
            "count as converged (rating.md §3, G18): %r" % (tolerance,),
        )
        self.assertEqual(
            iterations,
            10000,
            "MAX_ITERATIONS = 10_000 is the cap, and reaching it is what converged false "
            "means (rating.md §3): %r" % (iterations,),
        )
        rating = self.evaluation().rating(hand_matrix(lopsided))
        for member, entry in rating_entries(rating).items():
            with self.subTest(member=member):
                value = entry_value(entry)
                low, high = interval_bounds(entry)
                self.assertLessEqual(
                    low,
                    value,
                    "the lower bound is widened to hold the fitted value "
                    "(rating.md §4, FAM-9.2): %r" % (entry,),
                )
                self.assertGreaterEqual(
                    high,
                    value,
                    "the upper bound is widened to hold the fitted value "
                    "(rating.md §4, FAM-9.2): %r" % (entry,),
                )

    def test_evl_5_7_the_bootstrap_is_seeded_from_the_table_seed(self):
        """EVL-5.7 `bootstrap_seed` is the `_bootstrap_seed(table_seed)` derivation over the matrix's own `table_seed`, so two tables at two table seeds carry two bootstrap seeds (`rating.md` §4, `scheduler.md` §3, ASM-17, G18)."""
        package = self.evaluation()
        matrix = hand_matrix(lopsided)
        rating = package.rating(matrix)
        self.assertEqual(
            count(rating["bootstrap_seed"], "a rating's bootstrap_seed"),
            bootstrap_seed(matrix["table_seed"]),
            "the bootstrap's generator is built from _bootstrap_seed(matrix['table_seed']) "
            "and its seed is recorded, so the interval can be re-run (rating.md §4, "
            "scheduler.md §3, G18): %r" % (rating["bootstrap_seed"],),
        )
        other = hand_matrix(lopsided, table_seed=TABLE_SEED_HAND + 9)
        other_rating = package.rating(other)
        self.assertEqual(
            count(other_rating["bootstrap_seed"], "a rating's bootstrap_seed"),
            bootstrap_seed(other["table_seed"]),
            "a different matrix's own table seed derives its own bootstrap seed "
            "(rating.md §4, scheduler.md §3): %r" % (other_rating["bootstrap_seed"],),
        )
        self.assertNotEqual(
            count(other_rating["bootstrap_seed"], "a rating's bootstrap_seed"),
            count(rating["bootstrap_seed"], "a rating's bootstrap_seed"),
            "the bootstrap seed is a derivation of the table seed, so two table seeds "
            "give two bootstrap seeds (rating.md §4, G18)",
        )

    def test_evl_5_8_rating_refuses_a_matrix_that_is_not_a_table(self):
        """EVL-5.8 `rating` refuses, before fitting anything, a value that is not a matrix, a missing required key, a wrong cell count, a repeated pair, a foreign member, an uneven cell and a missing baseline -- each naming the violated rule (`rating.md` §6, `surface.md` §11, G16)."""
        package = self.evaluation()
        matrix = hand_matrix(balanced)
        cells = list(matrix_cells(matrix))
        five_cells = dict(matrix, cells=tuple(cells[:5]))
        repeated = list(cells)
        repeated[-1] = cells[0]
        foreign = list(cells)
        foreign[0] = dict(cells[0], members=("random", "version-ghost-5599"))
        uneven = list(cells)
        uneven[0] = dict(cells[0], hands=HANDS_PER_CELL - 1)
        no_baseline = hand_matrix(balanced, members=("random", "always-call", "variant-1"))
        cases = (
            ("not a mapping", ([],), (("matrix",), ("record",))),
            ("a string record", ("not-a-record",), (("matrix",),)),
            ("a wrong cell count", (five_cells,), (("cells",),)),
            ("a repeated pair", (dict(matrix, cells=tuple(repeated)),), (("pair",),)),
            ("a foreign member", (dict(matrix, cells=tuple(foreign)),), (("version-ghost-5599",),)),
            (
                "an uneven cell",
                (dict(matrix, cells=tuple(uneven)),),
                (("hands",), (str(HANDS_PER_CELL),)),
            ),
            ("a missing baseline", (no_baseline,), (("oracle",), ("baseline",))),
        )
        for label, args, groups in cases:
            with self.subTest(case=label):
                self.assert_evaluation_refusal(
                    package.rating, *args, entry="rating", groups=groups, label=label
                )
        for key in ("members", "cells", "hands_per_cell", "table_seed", "table"):
            with self.subTest(missing_key=key):
                absent = dict(matrix)
                absent.pop(key)
                self.assert_evaluation_refusal(
                    package.rating,
                    absent,
                    entry="rating",
                    groups=((key,),),
                    label="a missing %s" % key,
                )

    def test_evl_5_9_a_table_of_ties_rates_every_member_at_zero(self):
        """EVL-5.9 a hand-built table whose every cell is all ties has the closed form `theta = 0` for every member: it converges at once, bounds nothing and states 0 in every value with 0 inside its interval (`rating.md` §2-§3)."""
        package = self.evaluation()
        matrix = hand_matrix(all_ties)
        rating = package.rating(matrix)
        self.assertTrue(
            bool(rating["converged"]),
            "the all-ties iterate is already the stationary point, so the fit stops on "
            "TOLERANCE and records converged true (rating.md §3 step 5): %r"
            % (rating["converged"],),
        )
        self.assertFalse(
            bool(rating["bound_applied"]),
            "no member needed a clamp in a table of ties (rating.md §3): %r"
            % (rating["bound_applied"],),
        )
        for member, entry in rating_entries(rating).items():
            with self.subTest(member=member):
                value = entry_value(entry)
                low, high = interval_bounds(entry)
                self.assertLess(
                    abs(value),
                    1e-9,
                    "every member's win mass and expected win mass are equal in an "
                    "all-ties table, so the Bradley-Terry value is exactly 0 "
                    "(rating.md §2-§3): %r" % (value,),
                )
                self.assertLessEqual(
                    low, value, "the interval holds the value 0 (rating.md §4)"
                )
                self.assertGreaterEqual(
                    high, value, "the interval holds the value 0 (rating.md §4)"
                )
                self.assertFalse(
                    entry_bounded(entry),
                    "no member was pinned at a bound (rating.md §5): %r" % (entry,),
                )

    def test_evl_5_10_a_member_that_wins_more_rates_above_the_baselines(self):
        """EVL-5.10 a hand-built table where one member wins more than it loses in every cell gives that member a value above every baseline's, while the anchor still holds the baselines' mean at 0 and the matrix is not mutated (`rating.md` §1-§2, `league.md` §5)."""
        package = self.evaluation()
        matrix = hand_matrix(lopsided)
        snapshot = copy.deepcopy(matrix)
        rating = package.rating(matrix)
        entries = rating_entries(rating)
        variant = entry_value(entries["variant-1"])
        baselines = [entry_value(entries[name]) for name in BASELINES]
        self.assertGreater(
            variant,
            max(baselines),
            "a member that wins more hands than it loses in every cell stands above the "
            "baselines on the Bradley-Terry fit (rating.md §1-§2, league.md §5): %r vs %r"
            % (variant, baselines),
        )
        self.assertAlmostEqual(
            mean(baselines),
            0.0,
            places=3,
            msg="the anchor still holds the baselines' mean at 0 (rating.md §2-§3)",
        )
        self.assertEqual(
            matrix,
            snapshot,
            "rating reads the matrix record and fits it; it neither plays a hand nor "
            "repairs the record (rating.md §1, §6): %r" % (matrix,),
        )

    def test_evl_5_12_the_anchor_is_the_flagged_three_and_never_a_folder(self):
        """EVL-5.12 a table over the whole catalogue is anchored on the three flagged baselines' mean alone: the anchors' mean is exactly 0 while the folders' values are free, and the record's `anchor` names the three and no folder (`rating.md` §2-§3, §5, `records.md` §11, ASM-32, D-21).

        The table makes every anchor beat every folder and the members of each group tie
        one another, so a fit that anchored all six would hold the folders at 0 with the
        anchors and one that anchored none would leave the three off 0: only the flagged
        three's mean can be exactly 0 here (`docs/L1/folders.md` §4, ASM-32).
        """
        package = self.evaluation()
        catalogue = tuple(package.protocol()["baselines"]) + tuple(
            name
            for name in self.agents().baselines()
            if name not in tuple(package.protocol()["baselines"])
        )
        self.assertEqual(
            tuple(package.protocol()["baselines"]),
            BASELINES,
            "the pinned set is the three baselines of D-6 (declarations.md §2.2, ASM-32)",
        )

        def anchors_beat_folders(left, right):
            left_anchor = left in BASELINES
            right_anchor = right in BASELINES
            if left_anchor and not right_anchor:
                return HANDS_PER_CELL, 0
            if right_anchor and not left_anchor:
                return 0, 0
            return 0, HANDS_PER_CELL

        matrix = hand_matrix(anchors_beat_folders, members=catalogue)
        rating = package.rating(matrix)
        entries = rating_entries(rating)
        anchored = [entry_value(entries[name]) for name in BASELINES]
        self.assertAlmostEqual(
            mean(anchored),
            0.0,
            places=9,
            msg="the fit is zeroed on the flagged three's mean, and on nothing else "
            "(rating.md §2-§3, ASM-32): %r" % (anchored,),
        )
        for name in catalogue:
            if name in BASELINES:
                continue
            with self.subTest(folder=name):
                value = entry_value(entries[name])
                self.assertLess(
                    value,
                    -1.0,
                    "a folder that lost every cell is not held at the anchor: an anchor "
                    "of all six would pin it with the three, and a folder is a member and "
                    "never an anchor (rating.md §3, ASM-32, D-21): %r" % (value,),
                )
                self.assertNotIn(
                    name,
                    str(rating["anchor"]),
                    "the record's `anchor` never names a folding baseline "
                    "(records.md §11, ASM-32, D-21): %r" % (rating["anchor"],),
                )
        for name in BASELINES:
            self.assertIn(
                name,
                str(rating["anchor"]),
                "the record's `anchor` names the three baselines it zeroes the fit on "
                "(records.md §11, ASM-32): %r" % (rating["anchor"],),
            )

    def test_evl_5_11_rating_plays_no_hand_reads_no_file_and_moves_no_stream(self):
        """EVL-5.11 `rating` plays no hand, reads no file and leaves Python's global `random` stream where it found it, its bootstrap drawing from its own generator (`surface.md` §1, `rating.md` §1, §4, ASM-17)."""
        package = self.evaluation()
        matrix = hand_matrix(balanced)
        before = self.stream_state()
        with no_file_reads("rating()"):
            rating = package.rating(matrix)
        self.assert_stream_unchanged(before, "rating()")
        self.assertIn(
            "values",
            rating,
            "rating returned a records.md §11 record (surface.md §11): %r" % (rating,),
        )


if __name__ == "__main__":
    unittest.main()
