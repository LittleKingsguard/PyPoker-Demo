# A learner in the bettor's seat over the sized ladder · measured 2026-11-07

D-25 listed "a learner rather than a fixed policy in the bettor's seat" as the requirement the probes
had not met, and the sizing-ladder record repeats the caveat. This closes it at probe level: a tabular
Q-learner (state = street × facing-a-bet × hand strength band; actions = fold, call, min-raise, 1×, 4×,
all-in, masked by legality; ε 1.0 → 0.05 over 6,000 hands, α 0.15, γ 0.9) trained 20,000 hands against
D-21's folder, then evaluated **greedily** (ε = 0) over 2,000 hands.

**Greedy action distribution:** call **40 %**, min-raise **32 %**, 1× **27 %**, fold 0 %, 4× 0 %,
all-in 0 %.

**Chips/hand against the folder: +0.36 ± 0.20**, against the best fixed policy (min-raise always,
+0.68 ± 0.21) and the worst (1× always, −8.89 ± 1.93).

## What it settles

1. **The price is learnable, and quickly** (D-29) — 20,000 probe hands, not 600,000, reach within 0.3 chips of
   the best fixed policy. The graded action space gives the learner a signal the fixed-limit game never
   had.
2. **The learner shows variety** (D-29). Three actions are materially present (40/32/27) with no class above
   60 % — so the fear that learning the measured preference would concentrate play on a single size
   (critique F5) is not borne out by a learner that mixes call with two sizes.
3. **It never folds and never over-bets** (D-29) — the two actions the measurement says are bad against this
   opponent are the two it drops to zero.
4. **Greedy evaluation is possible in a probe** even though the product has no exploration-off surface
   (validity V-F10): the probe controls ε directly. The product still needs that surface before any
   census can be read, and the run record still carries no decisions for it to read (V-F6).

This is evidence for the *scientific* case and not for the *build*: no product artefact can yet hold a
game shape, a sized descriptor, a recorded amount or a greedy policy (D-29).
