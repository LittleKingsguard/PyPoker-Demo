# Which configuration selects the calling attractor? 30 runs · 2026-11-07

Grid: learning rate × utility × five seeds, 1,000 hands each, folders pool, torch backend, seed = 0..4.
Mode is read from the action census against `random` (raise > 60 % = raise, check-call > 60 % = call,
otherwise mixed). Learning rate patched in-process; the declared rate is unchanged (D-14).

| utility | lr | raise | mixed | call | diverged |
|---|---|---|---|---|---|
| `net-chips` | 0.001 | **5** | 0 | 0 | 0 |
| `net-chips` | 0.01 | 3 | 0 | **2** | 0 |
| `net-chips` | 0.03 | 2 | 0 | **2** | 1 |
| `stack-shortfall` | 0.001 | 1 | **3** | 1 | 0 |
| `stack-shortfall` | 0.01 | 2 | 1 | 2 | 0 |
| `stack-shortfall` | 0.03 | **4** | 1 | 0 | 0 |

## The hypothesis this tested, and its result

The prediction was that pairing the risk-averse utility (D-20) with a higher learning rate would make
the calling attractor **reliable** rather than a seed lottery. It does not:

- at `net-chips`, raising the rate to 0.01–0.03 reaches the call mode in **2 of 5 seeds each** — a
  lottery, not a selection;
- at `stack-shortfall` the utility does **not** stabilise it: at 0.001 the runs go *mixed* (raise
  17–56 %, call 24–54 %, no clean attractor), and at 0.03 the learner returns to **raise in 4 of 5**.

So the two levers that each moved behaviour on their own (D-20's utility; a higher rate) do not
compose into a selector. At the live budget, which attractor a run reaches is dominated by the seed.

## What the sweep did establish

1. **The divergence fix works in situ**: one of thirty runs at lr 0.03 failed by name
   (`LearningDiverged`) instead of corrupting quietly — the failure mode is now loud.
2. **The raise attractor is the default**: `net-chips` at the declared rate is raise in 5 of 5, and the
   200,000-hand deep run stayed there. Nothing tested reliably leaves it.
3. **`stack-shortfall` buys indecision, not calling**: at the declared rate it produces mixed policies
   rather than callers, which is consistent with D-20's pooled 63 % raise at the same budget.
4. **The seed lottery is the finding.** With five seeds per cell, no cell is deterministic in its
   mode, so a single-seed demo number is a coin flip — and every behavioural claim in this project
   should be quoted as a distribution over seeds or not at all (D-6).
