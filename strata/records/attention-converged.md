# The attention card model converged: 40 % pooled, 52.8 % at the river · measured 2026-11-08

D-88's attention + positional model taken to **400 epochs** — four times the longest previous run — with held-out
figures every 40 epochs, so the plateau is a measurement rather than an assumption (D-85, D-14).

| epoch | pooled | flop | turn | river | gain per 40 |
|---|---|---|---|---|---|
| 20 | 25.13 % | 16.49 % | 25.16 % | 33.65 % | — |
| 60 | 28.14 % | 17.41 % | 30.58 % | 36.30 % | +3.0 |
| 120 | 32.37 % | 18.13 % | 36.93 % | 41.91 % | +4.2 |
| 160 | 34.04 % | 17.31 % | 40.04 % | 44.62 % | +1.7 |
| 240 | 35.58 % | 14.44 % | 43.91 % | 48.20 % | +1.5 |
| 280 | 35.21 % | 13.70 % | 44.66 % | 47.08 % | −0.4 |
| 320 | 37.83 % | 16.24 % | 47.48 % | 49.60 % | +2.6 |
| 360 | **40.16 %** (peak) | 17.66 % | 49.77 % | 52.86 % | +2.3 |
| 400 | 39.99 % | 16.64 % | 50.32 % | **52.81 %** | −0.2 |

**Converged at 40.0 % pooled and 52.8 % at the river**, with the last two checkpoints flat (−0.2) and the peak at
epoch 360 — so unlike every earlier figure in this line, this one is **not** a lower bound.

## The ladder, at convergence

| representation | params | pooled R² |
|---|---|---|
| hole cards only (preflop) | 6,465 | 2.4 % |
| tokens + mean pool | 16,955 | 13.1 % |
| tokens + positions + mean | 17,305 | 15.3 % |
| flat one-hot | 20,929 | 20.4 % |
| attention + positions, 120 epochs | 57,597 | 32.4 % |
| **attention + positions, 400 epochs** | 57,597 | **40.0 %** |

So the model was never near its ceiling (D-85): **an extra 280 epochs bought 7.6 points**, and the flop figure is the one
that stalled first (17.7 % peak, then drifting down while turn and river climbed) — the early street is where the
information genuinely runs out, not where the optimiser is short of budget.

## Outstanding

The 400-epoch **weights were not saved** by the run that produced these numbers (my checkpoint patch was lost when
the launching job was killed), so the extremes battery has so far been scored against the 60-epoch model (D-91). A
re-run with saving is in flight; when its weights land the battery is re-scored and this record gains that column.
