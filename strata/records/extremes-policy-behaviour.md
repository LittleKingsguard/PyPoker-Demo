# The masked policy on the extreme states: folded locks, raised junk · measured 2026-11-08

The eight verified battery states (D-91: no flush or straight possible, Monte-Carlo truth), replayed through the two
**masked** policies (D-115), every decision on every street (D-14).

| state | true equity | masked **control** | masked **strength** |
|---|---|---|---|
| quad aces | 100.00 % | **fold** preflop | raise-min ×4 |
| nut flush | 100.00 % | **fold** preflop | raise-min ×4 |
| ace-high straight | 97.77 % | raise ¼ → raise ½ ×3 | raise-min ×4 |
| trip aces | 91.84 % | **fold** preflop | raise-min ×4 |
| pair of kings, dry | 45.07 % | raise ¼ → raise ½ ×3 | raise-min ×4 |
| **2-3 offsuit, no pair** | **0.00 %** | raise ¼ → raise ½ ×3 | **raise-min ×4** |
| 2-7 offsuit | 0.00 % | fold preflop | **fold** preflop |
| 2-3 offsuit, all-high board | 0.02 % | raise ¼ → raise ½ ×3 | raise-min ×4 |

## Two different failures, neither a ranking

**The control is anti-correlated.** It **folds quads, the nut flush and trip aces preflop** and **raises the worst hand
in the battery to the river** (2-3 offsuit, 0.00 % equity). Folding a lock and raising junk is worse than not reading
the hand at all — it is reading it backwards.

**The strength arm is a single-point threshold.** It raises minimum on **everything** — quads, the nut flush, the
straight, trip aces, kings, *and* the 2-3 junk — and folds only **2-7 offsuit**. So the "card-dependence" of D-115 is
**one distinction, keyed to one hand shape**, not a strength ordering: quads and 2-3 are played identically, and the only
hand it folds happens to be the one it saw most often as junk in training.

## What this settles

**The policy does not rank hands by strength — at either arm.** The mask fixed the input channel (D-115) and the
policy still has no monotone relationship between equity and aggression: one arm inverts it, the other flattens it to
"raise unless it's the specific hand I learned to fold".

That is the card model's own defect arriving in the policy: a **binary** target taught a lock detector (D-95 predicted
2.7 % for trip aces at 91.8 % true), so a policy built on it cannot distinguish a lock from a coin-flip — and a policy
whose only distinction is "junk vs everything" cannot be a poker player.

**The next honest measurement** is a monotonicity test rather than a census: rank a ladder of hands by true equity and
check that the policy's aggression is non-decreasing along it. Both arms would fail it today, and that is the number to
put beside the card model's calibration error.
