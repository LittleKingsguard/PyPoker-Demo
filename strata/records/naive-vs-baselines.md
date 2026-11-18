# The naive model against the baselines — and the live model beside it · measured 2026-11-08

The project's starting point, trained fresh at six seats for this figure: **flat numbers, plain stack** (`flat-numeric`,
433 slots; `naive-stack`, 36 wide, 2 layers, 18,510 parameters; normalised reward; 5,000 hands). Each cell is 1,000 hands
with the model in one seat and **five copies of that baseline** at the table (D-14; D-134).

| opponent | **naive model** | live model (token embedding, normalised) |
|---|---|---|
| `fold-large-bet` | **+11.30 ±0.59** | **+7.40 ±0.18** |
| `random` | **+11.56 ±10.05** | −3.45 ±8.74 |
| `always-call` | +0.93 ±9.86 | **−14.20 ±12.84** |
| `oracle` (equity) | −0.74 ±1.07 | **+0.84 ±0.87** |
| `fold-no-pair-or-face` | −6.12 ±7.08 | **−17.80 ±9.44** |
| `fold-no-pair-or-better` | −7.82 ±8.22 | −2.72 ±11.16 |

## What the graph says

1. **Both beat the trivial exploiter.** `fold-large-bet` surrenders large bets and both models collect: **+11.3** and
   **+7.4**, with the tightest intervals on the chart.
2. **Neither beats a selective opponent.** The two scripted folders — which fold by hand class — beat the naive model by
   6–8 chips and the live model by up to 18.
3. **The naive model is the better player against noise, and the live model is the better player against equity.**
   Against `random` and `always-call` the naive model is ahead (+11.6 and +0.9 against −3.4 and −14.2); against the
   `oracle` the live model is (+0.8 against −0.7). The live model **raises on 70–90 % of its decisions**, which is
   punished by anything that calls or traps.
4. **Nothing here is good poker.** The best cell on the chart is beating a baseline that gives up on large bets; the
   worst is losing 18 chips a hand to a policy that folds unpaired non-face hands.

## Caveats

One seed per model, and the two models differ in *both* representation and reward, so the contrast is not a controlled
comparison — it is "the starting point" against "something the project later built". The baseline opponents are five
copies of one policy, which is not a real table.
