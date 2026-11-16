# Three card models driving the same policy: no performance difference, but different card-dependence

The 400-epoch card model has the **worst mid-range calibration** of the three (D-95: 2.7 % predicted for trip aces
whose true equity is 91.8 %, and a 24-point mean battery error). This asks whether that hurts the policy. Same head,
same 4,000 training hands, same opponents, same seed; only the frozen card model differs (D-14).

| card model | battery mean err | chips/hand (500 greedy) | distinct decisions |
|---|---|---|---|
| **tok-60** | **11.9** | **+10.96 ± 7.16** | 2 / 5 |
| **tok-400** | **24.2** | +4.62 ± 7.59 | **5 / 5** |
| onehot-200 | — | +2.64 ± 15.13 | 3 / 5 |
## No performance difference exists in this comparison

**All three chip intervals overlap** (+10.96 ± 7.16, +4.62 ± 7.59, +2.64 ± 15.13), so the battery-calibration ranking
does **not** translate into a resolvable play difference. The best-chips arm is the *least* calibrated card model, and
its interval covers the other two.
## But card-dependence tracks training, not calibration

| card model | what the policy does with AA / 72o |
|---|---|
| tok-60 | check-call for every hand — effectively constant |
| tok-400 | **AA check-call, 22 fold, 87s raise-half, 72o raise-half** — five distinct sequences |
| onehot-200 | three distinct sequences |

So **the more-trained the card representation, the more the policy varies** (2 → 5 distinct of 5), which is what
D-97 found and this reproduces with a different seed path. And the least-varied arm is the one with the best
*calibration*.
## What that means

1. **The user's premise is confirmed**: the 400-epoch model is the worst-calibrated of the three.
2. **Its consequence is not worse play** — the chip intervals overlap, so the miscalibration does not show up as
   measurable chips at this sample size.
3. **What it does produce is variation without measured skill** — five different decisions, no better result. That is
   exactly the distinction D-97 flagged: reproducible card-dependence, not demonstrated judgement.

**The lesson for the deck**: at 500 evaluation hands, ±7–15 chips/hand is wider than any difference this integration
produces, so **performance claims here need a much larger sample — or none at all**. What is measurable is
*behaviour* (distinct decisions, and the ablation that removes it), and that is what should be claimed.
