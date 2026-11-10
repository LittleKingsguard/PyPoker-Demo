# No-limit bet sizing: a resolvable gradient, after two of my own errors · 2026-11-07

No-limit heads-up in the probe harness (pokerkit directly), blinds 1/2, 100-chip stacks, sizing as a
pot fraction, D-21's folder as the opponent. This measurement took three attempts; the first two were
wrong and both were mine.

## Error 1 — independent intervals on paired data

The first run reported pot-bet −6.582 ± 4.656 against half-pot −0.802 ± 1.521 and called a ~5.8-chip
effect. Both cells reported **exactly 306 folds**: they ran the same deals, so the two intervals were
not independent and their non-overlap proved nothing. (Critique, F21.)

## Error 2 — a sign bug in the "paired" test

The second run paired the two sizes on identical deals and produced −0.907 ± 3.026, which I took as
evidence the effect was not resolvable — but the odd-hand branch took the *folder's* payoff difference,
the negative of the bettor's, so half the differences were negated and the mean cancelled (D-26).
cancelled. The retraction was an artefact of that bug.

## The corrected measurement

Four sizes, 1,000 paired hands, seats alternating, the bettor's payoff taken in both seatings:

| size | vs folder | paired vs 0.5-pot | hands differing |
|---|---|---|---|
| **¼ pot** | **+0.33 ± 0.45** | **+2.03 ± 0.62** | 275/1000 |
| ½ pot | −1.70 ± 1.07 | — | — |
| **1 pot** | **−8.98 ± 3.27** | **−7.28 ± 2.21** | 275/1000 |
| all-in | −9.63 ± 4.55 | −7.93 ± 3.86 | 538/1000 |

Against a **caller** every paired difference spans zero (+0.91 ± 1.17 for ¼ pot, −3.26 ± 4.19 for pot
size), so the gradient is folder-borne as the mechanism predicts: a folder continues only with a pair
or better, so a big bet is called exactly when the bettor is behind.
## What this establishes

**Sizing has a resolvable, monotone price against folding opponents** — smaller is better, by
+2.03 ± 0.62 chips/hand from ½ pot to ¼ pot and −7.28 ± 2.21 from ½ pot to a full pot: the EV signal
the fixed-limit game never had, where every action was EV-neutral to within noise. It establishes the
*mechanism*, not that a learner finds it — that needs the sized action in the product, the surface
change D-26 now authorises on a pinned criterion.
