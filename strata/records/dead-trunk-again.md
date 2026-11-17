# Yes — the trunk died again, and it explains the never-fold behaviour · measured 2026-11-08

The D-60 instrument (active hidden units, weight norms, distinct activations) on the checkpoints in play:

| checkpoint | utility | layer 1 alive | layer 2 alive | ‖W1‖ | distinct activations |
|---|---|---|---|---|---|
| **ours, 15,000 hands** | **`net-chips`** | **0 / 50** | **0 / 50** | 10.08 | **1** |
| foldloop-high | `net-chips-normalised` | 23 / 50 | 23 / 50 | 10.13 | 277 |
| foldloop-control | `net-chips-normalised` | 22 / 50 | 23 / 50 | 10.13 | 277 |
| raiser-seed | `net-chips` | 9 / 50 | **0 / 50** | **1,377.16** | 277 |

**Our 15,000-hand model has every unit dead in both hidden layers, and only one distinct activation vector across 300
observations.** Its output is a constant plus the output bias, so the policy **cannot condition on its input at all** —
which is exactly why it never folds and calls every hand (D-107), and why the strength input and the seeded embeddings
changed nothing (D-104): the input was never reaching the decision.

## This is D-60/D-67's bug, reintroduced by me

D-67 established that the **600-scale `net-chips` reward kills the trunk** and that the **normalised** reward revives it
(‖w_in‖ 298.6 → 8.4–10.0; active units 14–30). I switched the product runs to `net-chips` when chasing a fair
comparison with the probe's chip-based reward, and thereby **reproduced the defect on three of the last four records**.

## What must be withdrawn or re-read

- **D-107 (never folds)** — the behaviour is real but its cause is a dead trunk, not a learned policy. It says nothing
  about what a live policy would do.
- **D-105 (break-even against the league)** — a dead-trunk policy can only be roughly break-even or worse; +1.82 ±8.81
  is the measurement of a constant-action policy, not of the agent's strategy.
- **D-104 (strength input changes nothing)** — correct as stated, but for the wrong reason: with a dead trunk *no*
  input can change anything. It must be re-run with a live trunk to be informative.
- **D-106 (no stable best member)** — unaffected: those members were independently trained, and two of the three are
  normalised and alive.

## The fix, in flight

The same 15,000-hand comparison at `net-chips-normalised` — the utility D-67 showed revives the trunk — control and
strength arms, seed 0. When it lands the three questions above can be asked again of a policy that can actually see its
input.
