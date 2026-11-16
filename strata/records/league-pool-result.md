# League pool: the gain shrinks from +12.7 to +2.5 chips/hand, and one seed is not significant

The probe fix plus the league opponents, both in one run. **The fix**: features and actions are gathered during play
with `no_grad`, then **one batched forward-and-backward per hand** instead of a backward and Adam step per decision
(D-100). **The league**: three six-seat checkpoints with distinct measured behaviour — a **pure folder** (100 % fold),
a **50/50 raiser**, and an **aggressive raiser** (83 % raise) — plus one scripted caller, rotating by seat. 15,000
training + 2,000 greedy evaluation hands, seeds 0–2 for both arms (D-14).

| arm | seed 0 | seed 1 | seed 2 | mean | census, seed 0 |
|---|---|---|---|---|---|
| **card** | **+1.61** ±2.56 | +0.32 ±5.27 | **+3.83** ±3.06 | **+1.92** | fold 86 %, call 14 %, raise 0 % |
| **zeroed** | −0.60 ±0.04 | −0.60 ±0.04 | −0.60 ±0.04 | **−0.60** | **fold 100 %** |

## What the league did to the result

**The gap in means falls from +12.7 to +2.5 chips/hand** — a **20 % retention** of the scripted-opponent effect. The
control is pinned at exactly **−0.60**, the blind loss, because it folds every hand (D-72's fold value); the card arms
clear it in **seeds 0 and 2** and **not** in seed 1, whose interval (±5.3) straddles both.

So the honest statement is: **the card representation still pays against a league that includes an aggressive raiser,
but the effect is smaller, more variable, and not significant in every seed.**

## And the behaviour changed to suit the table

Against the scripted folders the card arm **raised 54 % and never folded** (D-99). Against this league it **folds 86 %
and raises 0 %** — because two of the three league members punish raising. The policy found a different reply to a
different table, which is the first sign in this project of a response that depends on the *opponents* rather than only
on the cards.

## Caveats

- The league is **three checkpoints and one scripted caller**, not the product's full pool machinery, and the members
  are six-seat policies chosen for behavioural spread rather than for strength.
- The probe is still not the product's learner; the fix removed the per-decision autograd but league opponents are
  themselves checkpoint policies and dominate the 60–165 ms/hand evaluation cost.
- Three seeds and 2,000 hands per arm leave ±2.6–5.3 chip intervals; **seed 1 is genuinely unresolved**, not merely
  noisy.
