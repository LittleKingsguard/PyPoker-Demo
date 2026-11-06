# training — the curves

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-05
- **Owner:** the ten snapshot points (§2), the learning signal (§3), the spread across seeds (§4), and the curve record this
  module returns (§5)
- **Ceiling:** 90 lines. At the ceiling, split by owner — never append
- **Read with:** `loop.md` §1 steps 7–9, §4, `episode.md` §5, `checkpoints.md` §3, `errors.md` §4

## 1. What a curve is for, and what it is not

A rung reports curves because a table alone does not show learning happening and a curve alone does not show skill (D-6,
`protocol.md` §1): the curve is the record that the update moved, and its value is that it exists per variant and per seed with
the spread across seeds beside it (`records.md` §12, `battery.md` §3 FAM-4). It is **not** a claim: `training` plots nothing,
ranks nothing and asserts no value, and no case requires a curve to fall (`battery.md` §5, D-6).

## 2. The axis: ten points, at `budget // 10`

    _axis(budget, interval) -> list[int]        # [interval, 2·interval, … , 10·interval], strictly ascending

Ten points, equally spaced, the *k*-th after `k × interval` hands (`ASM-18`, `loop.md` §2). `interval` is `budget // 10`, so at a
1,000-hand run the axis is `100, 200, … 1,000`, and the tenth point is the budget's end; at the battery's 60- and 250-hand runs
it is `6, 12, … 60` and `25, 50, … 250` (`battery.md` §2). The interval is fixed by the budget the run was **given**, not by the
configuration's declared `snapshot_every`, and `loop.md` §2 gives the reason: a 250-hand run at a declared interval of 100 would
write two snapshots, and the five-version window FAM-12.4 observes needs five.

A budget that is not a multiple of ten shifts nothing: `10 × interval ≤ budget` always, because `interval = budget // 10`, and the
hands between `10 × interval` and the budget train and close no interval. They are still trained hands and they still move the
final model (`loop.md` §1 step 8); they simply carry no point, because ASM-18 fixes the count at ten.

Rejected: a point per 100 hands regardless of budget, which gives 0 or 2 points at the battery's budgets; and a point per hand,
which is a plot of noise and a snapshot per update ASM-18 explicitly rejects.

## 3. The signal: the mean absolute `td_error` of each interval

`agents.learn` returns `td_error`, the batch's mean absolute TD error as a plain float (`agents/surface.md` §7, `agents/rule.md`
§3). One hand's batch is one number, so interval *k* holds the signals of hands `(k − 1)·interval + 1 … k·interval` and its point
is their mean:

    signal[k] = mean(hand signals filed into interval k)          # statistics.fmean, plain floats

The mean is over the hands in the interval that produced an **update**: a hand in which the learner's seat never acted makes no
`learn` call and files no signal (`episode.md` §3). An interval that produced no update at all reads `0.0` — the declared value of
an empty mean — and cannot mislead, because an interval holds at least `budget // 10 ≥ 1` hands and a hand of this game is a
handful of decisions for both seats (`ASM-6`). Rejected: carrying the previous point forward, which invents a measurement where
there was none, and `None`, which would make the axis and the signal two lengths.

The values are plain `float`s in `[0, ∞)`, unrounded, and `math`/`statistics` compute them: no `numpy` import is needed and none
is taken (`README.md` §5).

## 4. The spread across seeds

Every point carries the spread across the run's seeds at that point: the **max minus the min** of the seeds' signals at index *k*,
a plain `float` (`records.md` §12, `protocol.md` §1). With one seed the set holds one value and the spread is exactly `0.0` at
every point — the recorded fact that a one-seed run has no spread, not a missing measurement (D-4, D-6). Rejected: a standard
deviation, which is `0.0` for one seed as well but is undefined-ish for two and invites a "sample or population" argument the
record cannot settle; the max-minus-min spread is one line, total, and needs no divisor.

The spread is a property of the **variant and the point**, so it is repeated at each of that variant's seeds in §5's record rather
than stored once: a reader that asks one seed's entry for its spread gets the answer without knowing which seed was first
(`loop.md` §4).

## 5. The curve record, and `_Curve`

    _axis(budget, interval) -> list[int]        # [interval, 2·interval, … , 10·interval], strictly ascending
    _spread(series) -> list[float]              # §4's max minus min at each point of a per-seed series
    _Curve(samples)                             # one variant × one seed: .samples, .signal, .spread
        .add(hand_index, td_error)              # file one hand's signal into its interval (§3)
        .close(spread)                          # finalise .signal (the ten means) and store §4's spread
        .record()                               # {"samples": [...], "td_error": [...], "spread": [...]}

`_Curve` is the accumulator the per-pair pass fills (`loop.md` §2) and the three attributes are the three lists of the record, in
that order. `_axis` is §2's ten points; `_spread` is §4's one line applied point by point across the seeds. `_record` assembles
the run's `curves` key as **variant → seed (a decimal string) → that mapping** (`loop.md` §4), so one variant's three seeds are
three entries with one shared axis and one shared spread. `agents.learn`'s `transitions` count is **not** part of the record: it
counts decisions, and a version's `samples` is the run's count of hands (`agents/surface.md` §7, `records.md` §7).

## 6. What is left to L4

Whether the accumulator keeps a list of lists or ten running sums, whether the mean is `statistics.fmean` or `sum/len`, and
whether `.record()` returns a fresh mapping. Not L4's: the ten points at `budget // 10` and `_axis`'s signature, the signal's
definition and its `0.0` for an empty interval, §4's max-minus-min spread with `0.0` for one seed, and the record's three keys
and their nesting (`guardrails.md` G4, G6).
