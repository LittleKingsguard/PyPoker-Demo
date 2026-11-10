# Does no-limit make bet sizing matter? Probe, and its retraction · 2026-11-07

No-limit heads-up in the probe harness, blinds 1/2, 100-chip stacks, sizing as a pot fraction, D-21's
folder as the opponent. **The headline this record first carried does not survive a paired test**, and
the gate (`D-25`) forced the corrected arithmetic.

## What was first reported, and why it was wrong

Against the same folder, 400 hands each: pot-bet **−6.582 ± 4.656**, half-pot **−0.802 ± 1.521** — read
as a ~5.8 chips/hand size effect. Both cells reported **exactly 306 folds**, which is the tell: they
ran on the *same* deals, so the two intervals were not independent and their non-overlap is not a
test. Comparing two independent intervals on paired data overstates significance.

## The paired measurement

Same deals, seats alternating, 600 paired hands, difference taken per hand:

**pot-bet minus half-pot = −0.907 ± 3.026 chips/hand**, and only **93 of 600** hands differ at all
(the other 507 produce the same payoff, because the folder folds in both runs or both reach the same
showdown).

So the size effect is real in direction and **not resolvable**: −0.91 with a ±3.03 interval. In
fixed-limit the comparison was inside noise; here it is also inside noise, with a larger variance
(σ ≈ 37 on the difference against ≈2 in the fixed game).

## What survives

- The *mechanism* is visible in the 15 % of hands that differ: over-betting into a disciplined folder
  can be punished, because the folder continues only with a pair or better.
- Nothing measured here supports spending an overnight run, and D-24's conditional — "if it shows
  positive outcomes for fold/raise + call variety" — is **not met**.
- The probe's own defects (three before it ran clean, no per-hand deltas kept, no battery) plus this
  arithmetic error mean the no-limit direction needs a *fixed instrument* before any build: per-hand
  paired deltas kept and reported, several seeds and seat blocks, more than two sizes, and a learner —
  not a fixed policy — in the bettor's seat (D-25).
