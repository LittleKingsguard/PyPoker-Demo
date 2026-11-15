# RCA: why the token models pin to fold-when-legal · measured 2026-11-08

D-71 showed the token arms fold all sixteen loaded hands, aces included, wherever folding is legal. This finds
the cause. It is not the cards, not the reward's shape, and not a tie-break (D-14).

**It is not a near-tie.** Across the **164 scenarios where a preflop fold was chosen**, fold beats the best
alternative by a **mean +0.0157** (median +0.0141, range +0.0022 to +0.0523) — orders above the tie tolerance.
The model prefers fold; it does not drift into it.

**And its value for folding is correct.** Fold's own value averages **−0.0027**, the blind loss in normalised units
(1 chip in 600), while every alternative sits at **−0.01 to −0.14**. The model estimates that **playing on loses
more than folding does**, so folding is coherent *given the way it plays on*.

**The loop, demonstrated by one parameter.** Same configuration, pool and 5,000 hands, only the exploration floor
changed:

| arm | fold share | what it does instead |
|---|---|---|
| **ε_end 0.05** (declared) | **92.9 %** | check-call 7 % |
| **ε_end 0.60** | **0.0 %** | raise-minimum 63 %, call 27 %, all-in 10 % |

The pinning **vanishes entirely** (D-6) when the learner is forced to keep trying the other actions. With a low floor it
folds, folding ends the hand, the on-policy samples that would price *playing on* are never collected, their
estimates stay bad, folding stays optimal, and the policy never leaves.

**The cause, stated:** a **data-starvation loop between the policy and its own value estimates, amplified by an
exploration floor that is too low** (D-6). Not a card-blind network (D-71: 8–24 distinct score vectors), not a
dead trunk (D-67: 22–30 active units), not a tie-break, not the reward's scale.

It also explains why the **token** arms pin: their action values are compressed into a narrow band (~0.05 against
the flat arms' ~0.3), so a smaller estimation error makes fold win, and less data locks it in.

**Remedies, in order:** **raise the exploration floor** — one declared number, measured to move fold from 92.9 %
to 0.0 % — and, if that is not enough, **estimate the values of actions not taken**, which is what D-39/D-40's
reveal-only counterfactual does. It was set aside because it did not fix folding in a two-player pool; this RCA
says it was aimed at the wrong symptom.
