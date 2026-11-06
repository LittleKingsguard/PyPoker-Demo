"""TRN-5 — the curves: `_axis(budget, interval)`, `_Curve(samples)`, `_spread(series)`.

Drives `docs/L3/training/curves.md` §2-§5: the ten equally spaced points at
`budget // 10`, the signal as the mean absolute `td_error` of each interval with `0.0` for
an interval that produced no update, the spread as **max minus min** across seeds (a
standard deviation is §4's rejected alternative), and the curve record's three keys.

`_Curve` is fed 1-based snapshot steps, because §3 fixes interval *k* as the hands
`(k − 1)·interval + 1 … k·interval` — the step the axis names, not the 0-based index the
loop counts with (`loop.md` §1 step 7). Nothing here requires a curve to fall: the design
plots nothing and asserts no value (`curves.md` §1, battery.md §5).
"""

import unittest

from _training_support import (
    SIXTY_BUDGET,
    TrainingCase,
    as_float,
    as_int,
    as_mapping,
    as_sequence,
    internal,
)

#: A small budget and its interval, the battery's own (60 hands, 6 per point).
BUDGET = SIXTY_BUDGET
INTERVAL = BUDGET // 10


class CurveTest(TrainingCase):
    def axis(self, budget, interval):
        return [
            as_int(point, "a sample axis point")
            for point in as_sequence(
                internal("curves", "_axis")(budget, interval), "the sample axis"
            )
        ]

    def spread(self, series):
        return [
            as_float(point, "a spread point")
            for point in as_sequence(internal("curves", "_spread")(series), "a spread")
        ]

    def curve(self, axis, steps):
        """A `_Curve` fed `{step: td_error}` over the axis the run would use."""
        accumulator = internal("curves", "_Curve")(list(axis))
        add = getattr(accumulator, "observe", None) or getattr(accumulator, "add")
        for step in sorted(steps):
            add(step, float(steps[step]))
        return accumulator

    def test_trn_5_1_the_axis_is_ten_points_at_budget_over_ten(self):
        """TRN-5.1 `_axis(budget, interval)` is `[interval, 2·interval, … , 10·interval]`, strictly ascending, with the tenth point at or before the budget (curves.md §2, ASM-18, guardrails G4)."""
        for budget in (20, BUDGET, 250, 1000):
            interval = budget // 10
            with self.subTest(budget=budget):
                axis = self.axis(budget, interval)
                self.assertEqual(
                    axis,
                    [interval * step for step in range(1, 11)],
                    "ten points, equally spaced, the k-th after k × interval hands "
                    "(curves.md §2): %r" % (axis,),
                )
                self.assertEqual(
                    len(axis), 10, "ASM-18 fixes the count at ten: %r" % (len(axis),)
                )
                self.assertEqual(
                    axis,
                    sorted(set(axis)),
                    "the axis is strictly ascending: %r" % (axis,),
                )
                self.assertLessEqual(
                    axis[-1],
                    budget,
                    "10 × interval ≤ budget always, because interval = budget // 10 "
                    "(curves.md §2)",
                )
        self.assertEqual(
            self.axis(60, 6),
            [6, 12, 18, 24, 30, 36, 42, 48, 54, 60],
            "at the battery's 60-hand run the axis is 6, 12, … 60 (curves.md §2, "
            "battery.md §2)",
        )
        self.assertEqual(
            self.axis(250, 25),
            [25, 50, 75, 100, 125, 150, 175, 200, 225, 250],
            "at a 250-hand run it is 25, 50, … 250, and the declared 100 would write "
            "two snapshots instead of ten (curves.md §2, loop.md §2)",
        )

    def test_trn_5_2_the_signal_is_the_mean_of_each_interval(self):
        """TRN-5.2 one point per interval, and interval *k*'s point is the mean of the signals filed into the hands `(k − 1)·interval + 1 … k·interval` (curves.md §3, §5, episode.md §5)."""
        axis = self.axis(BUDGET, INTERVAL)
        steps = {step: float(step) for step in range(1, 11 * INTERVAL + 1)}
        accumulator = self.curve(axis, steps)
        accumulator.close([0.0] * 10)
        recorded = as_mapping(accumulator.record(), "a curve record")
        signal = [
            as_float(value, "a td_error point")
            for value in as_sequence(recorded["td_error"], "'td_error'")
        ]
        expected = []
        for index in range(10):
            hands = range(index * INTERVAL + 1, (index + 1) * INTERVAL + 1)
            values = [steps[step] for step in hands]
            expected.append(sum(values) / len(values))
        for index, (got, wanted) in enumerate(zip(signal, expected)):
            with self.subTest(point=index):
                self.assertAlmostEqual(
                    got,
                    wanted,
                    places=12,
                    msg="interval %d's point is the mean of the signals filed into it "
                    "(curves.md §3): %r against %r" % (index, got, wanted),
                )
        self.assertEqual(
            len(signal),
            len(axis),
            "the signal is one point per step, so the axis and the signal are one "
            "length (curves.md §3, §5): %r against %r" % (len(signal), len(axis)),
        )

    def test_trn_5_3_an_interval_with_no_update_reads_zero(self):
        """TRN-5.3 an interval that produced no update at all reads `0.0` — the declared value of an empty mean — and the axis and the signal stay one length (curves.md §3)."""
        axis = self.axis(BUDGET, INTERVAL)
        steps = {}
        for step in range(1, 11 * INTERVAL + 1):
            if step in (7, 8, 9, 10, 11, 12):
                continue  # the second interval's hands produced no update
            steps[step] = float(step)
        accumulator = self.curve(axis, steps)
        accumulator.close([0.0] * 10)
        recorded = as_mapping(accumulator.record(), "a curve record")
        signal = [
            as_float(value, "a td_error point")
            for value in as_sequence(recorded["td_error"], "'td_error'")
        ]
        self.assertEqual(
            len(signal),
            10,
            "an empty interval carries a point and not a hole, because the axis and the "
            "signal must be one length (curves.md §3): %r" % (signal,),
        )
        self.assertEqual(
            signal[1],
            0.0,
            "an interval that produced no update reads 0.0 and never carries the "
            "previous point forward or None (curves.md §3): %r" % (signal[1],),
        )
        self.assertAlmostEqual(
            signal[0],
            (1.0 + 2.0 + 3.0 + 4.0 + 5.0 + 6.0) / 6.0,
            places=12,
            msg="the intervals that did produce updates keep their own means "
            "(curves.md §3)",
        )

    def test_trn_5_4_the_spread_is_max_minus_min(self):
        """TRN-5.4 `_spread` is the max minus the min across the seeds' signals at each point: exactly `0.0` for one series and the difference for several (curves.md §4, records.md §12)."""
        alone = self.spread([[4.0, -2.0, 0.5]])
        self.assertEqual(
            alone,
            [0.0, 0.0, 0.0],
            "with one seed the set holds one value and the spread is exactly 0.0 at "
            "every point (curves.md §4, D-4, D-6): %r" % (alone,),
        )
        several = self.spread([[1.0, 5.0, -3.0], [3.0, 5.0, 7.0], [2.0, 0.0, 4.0]])
        self.assertEqual(
            several,
            [2.0, 5.0, 10.0],
            "the spread is max minus min, a plain float (curves.md §4): %r" % (several,),
        )
        mean = (1.0 + 3.0 + 2.0) / 3.0
        deviation = ((1.0 - mean) ** 2 + (3.0 - mean) ** 2 + (2.0 - mean) ** 2) / 3.0
        self.assertNotAlmostEqual(
            several[0],
            deviation ** 0.5,
            places=12,
            msg="the spread is max minus min and not a standard deviation: §4 rejects "
            "a deviation about the mean because it is undefined-ish for two seeds "
            "(curves.md §4)",
        )

    def test_trn_5_5_the_record_carries_the_three_lists(self):
        """TRN-5.5 `.record()` returns `{samples, td_error, spread}`, the ten means and the spread the pair's pass closed it with, and `.samples` is the axis (curves.md §5, loop.md §4)."""
        axis = self.axis(BUDGET, INTERVAL)
        accumulator = self.curve(axis, {step: 1.0 for step in range(1, 11 * INTERVAL + 1)})
        spread = [float(index) / 4.0 for index in range(10)]
        accumulator.close(spread)
        recorded = as_mapping(accumulator.record(), "a curve record")
        self.assertEqual(
            set(recorded),
            {"samples", "td_error", "spread"},
            "the curve record's three keys are the three lists, in that order "
            "(curves.md §5, loop.md §4): %r" % (sorted(recorded),),
        )
        self.assertEqual(
            [as_int(value, "a sample axis point") for value in
             as_sequence(recorded["samples"], "'samples'")],
            axis,
            "`samples` is the axis the run used (curves.md §2, §5)",
        )
        self.assertEqual(
            [as_float(value, "a spread point") for value in
             as_sequence(recorded["spread"], "'spread'")],
            spread,
            "`.close(spread)` stores the across-seed spread at every point, and the "
            "record hands it back unchanged (curves.md §4, §5): %r"
            % (recorded["spread"],),
        )
        self.assertEqual(
            [as_float(value, "a td_error point") for value in
             as_sequence(recorded["td_error"], "'td_error'")],
            [1.0] * 10,
            "every interval of a constant signal reads that constant, so the ten means "
            "are ten points and not a running total (curves.md §3)",
        )
        self.assertEqual(
            [as_int(value, "a sample axis point") for value in
             as_sequence(accumulator.samples, "a curve's 'samples'")],
            axis,
            "the accumulator's `samples` attribute is one of the three lists "
            "(curves.md §5)",
        )


if __name__ == "__main__":
    unittest.main()
