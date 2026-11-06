"""The training curve: ten points, one learning signal, and the spread across seeds.

A run writes ten equally spaced snapshots (ASM-18), so the curve's sample axis is
`interval, 2·interval, …, 10·interval` at `interval = budget // 10`, and its learning signal
is `agents.learn`'s `td_error` — the batch's mean absolute temporal-difference error —
averaged over the hands filed into each interval (`protocol.md` §1, `agents/surface.md` §7).
An interval that produced no update reads `0.0`, which is the declared value of an empty
mean. The spread is **max minus min** across the seeds at each point — one line, total, and
exactly `0.0` for a one-seed run: a recorded fact, not a missing measurement (D-6,
docs/L3/training/curves.md §3–§4).
"""

import statistics

from . import declarations


def _axis(budget, interval):
    """The ten sample points of a run's curve: `interval, 2·interval, …, 10·interval`."""
    return [int(interval) * step for step in range(1, declarations.SNAPSHOTS + 1)]


def _spread(series):
    """The spread across seeds at each point: the max minus the min of the signals.

    `series` is one signal list per seed, in the run's seed order; `0.0` at every point
    when the set holds one seed (`docs/L3/training/curves.md` §4).
    """
    lists = [list(item) for item in series]
    if not lists:
        return []
    length = min(len(item) for item in lists)
    return [
        max(item[point] for item in lists) - min(item[point] for item in lists)
        for point in range(length)
    ]


class _Curve:
    """One variant × one seed's curve: the axis, the interval means, the spread."""

    def __init__(self, samples):
        self.samples = list(samples)
        self.signal = []
        self.spread = []
        self._interval = int(self.samples[0]) if self.samples else 1
        self._buckets = [[] for _ in self.samples]

    def add(self, hand_index, td_error):
        """File one hand's learning signal into the interval it belongs to."""
        bucket = (int(hand_index) - 1) // self._interval
        if 0 <= bucket < len(self._buckets):
            self._buckets[bucket].append(abs(float(td_error)))

    def close(self, spread):
        """Finalise the ten interval means and store the variant's spread."""
        self.signal = [
            statistics.fmean(bucket) if bucket else 0.0 for bucket in self._buckets
        ]
        self.spread = list(spread)
        return self.record()

    def record(self):
        """The curve as plain data: the axis, the signal on it, the spread beside it."""
        return {
            "samples": list(self.samples),
            "td_error": list(self.signal),
            "spread": list(self.spread),
        }
