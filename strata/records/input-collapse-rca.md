# RCA: where the input falls out of the net-chip models · measured 2026-11-08

D-59 measured the symptom — a constant score vector for 477 distinct observations. This locates the cause by
re-running each network's forward pass and counting **active ReLU units** (D-14).

| model | after input | **after trunk** | ‖hidden‖ | ‖hidden·out‖ | ‖b_out‖ | verdict |
|---|---|---|---|---|---|---|
| **flat + net-chips** | 1/36 | **0 / 0** | **0** | **0** | 9.73 | **bias only** |
| **token + net-chips** | 24/50 | **2 / 1** | 0.0012 | 0.0003 | 9.39 | bias only |
| flat + shortfall | 17/36 | 16 / 12 | 0.429 | 0.224 | 0.136 | input-driven |
| token + shortfall | 27/50 | 21 / 25 | 0.480 | 0.148 | 0.043 | input-driven |

**The trunk is dead in both net-chip models.** One has *zero* active units in both hidden layers, so the
hidden vector is exactly zero and the output **is** the output bias; the other keeps 2 then 1 unit alive,
contributing 0.0003 against a bias of 9.39 — four orders of magnitude, the same constant function.
## The chain

1. **The reward is chips** — a hand's net delta runs to ±600 at six seats with large variance.
2. **Squared TD at the declared rate drives parameter magnitudes to fit that scale**: input-weight norms
   **313 vs 8.5** and input biases **82 vs 0.083**, i.e. 37× and 1000× the shortfall models'.
3. **Large pre-activations plus ReLU kill units**: with big weights and biases, hidden pre-activations sit
   far to one side and every negative unit contributes 0. The trunk collapses.
4. **A dead trunk makes the policy constant**: output = `b_out`, a fixed arg-max, the same action in every
   state for ever.
5. **Everything downstream follows** — identical payoffs across seeds, Double-Q moving nothing (no input
   path to repair), the 0.026-chip same-family agreement, every single-action census, and the finding that
   **200× more hands changed nothing**: no gradient reaches an action through a zeroed unit.
## Why the shortfall models survive

Their reward is O(1) rather than O(100), so the same learning rate yields small parameters (‖w_in‖ 8.5),
units stay alive (16–25 active), and the hidden vector drives the output as much as the bias does. **The
utility did not change what the model prefers; it changed whether the network has a living hidden layer.**
## What this implies, and it is testable

- **The fix is scale, not architecture**: normalising the reward should keep parameters small and the trunk
  alive — and the project already has the rung for keeping a trunk alive, **R6 `residual`**, where the
  trunk adds to a carried signal instead of replacing it.
- **The instrument to watch is active-unit count**, not the action census: dead units are the earliest
  visible failure, and `agents` exposes the arrays to count them.
