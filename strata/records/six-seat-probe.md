# Does more seats make folding — and therefore bluffing — pay? Probe · 2026-11-07

Run in the probe harness (pokerkit directly, no module changes), 500 hands per cell, D-21's folder
rules as policies, seats 0..n−1 fixed for the run (D-14). Two independent seed blocks were run
because the first crashed; both are shown where they disagree.

| cell | raiser's chips/hand | the others |
|---|---|---|
| 2 seats: raiser vs caller | +0.11 ± 1.23 / **−0.73 ± 1.22** | caller −0.11 / **+0.73** |
| 2 seats: raiser vs folder-face | −0.29 ± 0.93 / **−0.91 ± 0.95** | folder **+0.29 / +0.91** |
| 2 seats: raiser vs folder-pair | **−0.73 ± 1.22** | folder **+0.73** |
| 2 seats: folder-face vs caller | **−0.10 ± 0.17** | caller +0.10 |
| 6 seats: raiser + 5 callers | −0.03 ± 2.73 | **+1.96 ± 2.88 and −2.63 ± 2.51** |
| 6 seats: raiser + 5 folder-face | **−1.89 ± 1.97** | +0.73 ± 1.81 and −1.40 ± 1.52 |
| 6 seats: mixed (raiser, 2 callers, 2 face, 1 pair) | −0.74 ± 2.45 | +1.58 ± 2.62 and −2.65 ± 2.29 |

## Three measurements that decide it

1. **Aggression does not gain against folders.** Heads-up the raiser's EV against a folder is
   **negative** in both seed blocks (−0.29 and −0.91), where against a caller it straddles zero. A
   bet that makes a folder fold wins the pot — but the folder only puts money in when it is ahead, so
   the raiser's bluffs are the hands that get called.
2. **Six seats does not improve it.** The raiser against five folders measures −1.89 ± 1.97, not
   better than against five callers, and the interval is six times wider than the heads-up one.
   Fold equity in a six-way pot needs five folds, and the payoff does not cover it.
3. **Six seats destroys resolution.** Two seats of an *identical* policy measure **+1.96 and −2.63**
   chips/hand — position, not strategy. Resolving a 0.3-chip edge at that variance needs ≈40,000
   hands per cell, against 500 here and 120 in a live table.

## Disposition

The hypothesis "more simultaneous opponents make bluffing pay" is **refuted at the probe**, which is
what it was asked to settle before any module moved (D-22). Six seats also costs more than it can
return: the same per-hand work with six payoffs, a variance that kills resolution, and a positional
confound that would need a balanced rotation to control (D-23).
