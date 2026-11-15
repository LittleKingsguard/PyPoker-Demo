# How the trunk dies, and why no learning rate saves it · measured 2026-11-08

The challenge: the input is diverse (477 distinct observations), so ignoring it should cost error — why does the
network ignore it anyway? Traced with ten snapshots over 3,000 hands, and again at a 1000× lower rate (D-14).

| checkpoint | ‖w_in‖ | ‖b_in‖ | ‖w_out‖ | ‖b_out‖ |
|---|---|---|---|---|
| hand 300 | 11.0 | 1.22 | 4.67 | 1.12 |
| **hand 600** | **298.6** | **78.87** | **312.0** | 3.77 |
| hand 900 … 3,000, final | **298.6** | **78.87** | **312.0** | 3.98 → 7.52 |

**An explosion, then a freeze.** Between hands 300 and 600 the weights grow 27×, then freeze to four
significant figures for the remaining 2,400 hands; only `b_out` keeps moving, learning each action's marginal
value. That freeze is the signature of a **zero gradient**: once every trunk unit's pre-activation is negative
the rectifier's derivative is 0, no gradient reaches `w_in`, `b_in` or `w_out`, and the path is dead for good.

**Why it explodes.** The reward is chips — ±600 a hand at six seats — and Q starts near 0, so the first TD
errors are |δ| ≈ 600. One step is `lr·δ·x` = **1e-3 × 600 × x ≈ 0.6 per hand**: weights climb ~1 per hand,
reach 300 inside 300 hands, the pre-activations become enormous, every unit lands negative, and the trunk
switches off.

**Lowering the rate trades one failure for another** (D-6): at **1e-6** the weights stay at their initial
values for all 3,000 hands — ‖w_in‖ **8.471** from hand 300 onward, `b_in` 0.0096, `b_out` 0.022. Nothing
explodes and nothing learns; the trunk stays alive and the model is a constant function anyway.

**The answer to the challenge.** The input is informative and ignoring it *does* cost error — but the error
signal cannot reach the input. The loss is not the problem; the parameterisation is: a dead rectifier has zero
derivative, so the cost of ignoring the input is real in the objective and invisible to the optimizer.

And the usable window is narrow: `lr × reward-scale` must be small enough not to explode the weights within a
few hundred hands and large enough to move them within the budget. At a 600-scale reward **1e-3 explodes and
1e-6 stalls** — no rate in that span works, which is why the utility's *scale* is decisive. `stack-shortfall`'s
O(1) reward puts the same 1e-3 at an effective step of 0.001, inside the window, which is why its trunks are
alive (D-60, D-63).

**The fix:** normalise the reward — divide by the stack, or target a bounded advantage — so the declared rate
is the right size for the reward actually delivered. Then weights stay small, units stay alive, the error
reaches the input, and the input's diversity finally gets to matter.
