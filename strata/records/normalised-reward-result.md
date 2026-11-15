# The normalised reward revives the trunk: prediction confirmed · measured 2026-11-08

D-66's test: a utility that is net chips ÷ (seats × starting stack) — range `[-1, +1]` at six seats, differing
from `net-chips` in **scale and nothing else**. Six cells × seeds 0–2, six seats, 15,000 hands, the mixed pool
`pool-8386c3ef83ae48b2`; 18 concurrent runs, all completed, none failed (D-14).

| measure | `net-chips` (recorded) | **normalised reward** | predicted |
|---|---|---|---|
| ‖w_in‖ | **298.6 – 313** | **8.44 – 10.01** | order 10 ✔ |
| active units, layer 1 | **0 / 36–50** | **14 – 30** | alive ✔ |
| active units, layer 2 | **0 / 36–50** | **12.9 – 26.9** | alive ✔ |
| distinct scores / distinct observations | **1** over thousands | **1.000 — equal in all 18 runs** | state-dependent ✔ |
| fold share | ~0 % (constant policy) | flat **4–21 %**, tokens **55.3 %** | changes |

**Every part of the prediction held.** Weights stay of order 10 instead of exploding to 300, every hidden layer
keeps a third to two thirds of its units alive, and in all eighteen runs the distinct score vectors **equal**
the distinct observations — the first state-dependent policy this project has produced outside
`stack-shortfall`.
## Behaviour, and one unexplained number

| cells | fold | chips/hand |
|---|---|---|
| `norm-*-flat` | **4–21 %** (mean 6–10 %) | −3.4 to −7.1 |
| `norm-*-tokens` | **55.3 %** | **−0.15 to −1.2** |

The token cells lose **four to forty times less** than the flat ones and fold half their decisions. But **all
nine token runs — three cells, three seeds — report exactly 55.3 %**, which is too exact to be three
independently trained policies agreeing: it is flagged as **unexplained**, not accepted as convergent
behaviour, and it is the first thing to check if this line continues.
## What it settles

D-65's mechanism is confirmed causally: the reward's **magnitude** set the step size, the step size exploded the
weights, the explosion killed the rectifiers, and a dead rectifier froze the parameters. Normalising the reward
puts the declared learning rate inside the window, and the network reads its input again.

**And the estimator axis is still inert where it can now be seen**: masked-Q, double-Q and the counterfactual
produce 15.0 / 15.4 / 15.3 active units per layer and 6.1 / 6.6 / 9.6 % fold at flat, and 26.3 / 26.2 / 26.5
units and 55.3 % at tokens. Differences sit inside the seed spread — so the estimator is inert **even in a live
network**, which is a stronger statement than the dead-trunk null it replaces.
