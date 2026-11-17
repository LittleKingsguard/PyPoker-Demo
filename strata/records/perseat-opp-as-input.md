# The better opponent model still collapses the policy: prediction quality is not the problem · 2026-11-08

D-122 fixed the opponent model as a *predictor* — per-seat history and identity lift balanced accuracy from the
table-level degenerate to **0.821**, and raise recall from 0 to 1.00. This wires the improved artefact into the policy,
same mask, same card model, same league, 5,000 train + 2,000 greedy hands (D-14).

| arm | dim | chips/hand | census | card-dep |
|---|---|---|---|---|
| **base** (card + strength + facts) | 56 | **+3.68 ±3.22** | fold 78 %, call 22 % | 3/5 |
| **+ per-seat opponent model** | 59 | **−0.56 ±0.11** | **fold 99.7 %** | 1/5 |
| *+ table-level opponent model* (D-119) | 60 | −0.60 ±0.04 | fold 100 % | 1/5 |
| *+ table-level opponent + bet size* (D-119) | 61 | −0.60 ±0.04 | fold 100 % | 1/5 |

## What this settles

**The collapse is not caused by the opponent model's accuracy.** A model that predicts raises (recall 1.00), tracks
each member's own action mix, and reaches 0.82 balanced accuracy does exactly what the near-constant table-level model
did: it **drives the policy into the fold corner** (−0.56 against the base arm's +3.68).

So the input is not the issue and the predictor is not the issue — **three extra dimensions, whatever they contain, move
this learner off the only configuration it reliably finds.** That is the credit-assignment fragility D-72/D-116 describe,
appearing again: the policy sits at a corner of the action simplex, and perturbing its input space changes *which* corner
it reaches rather than adding skill.

## What this means for the opponent-modelling goal

A better estimator of an opponent is **necessary and not sufficient**: it can be measured, improved and validated
(D-122), and still be unusable as a policy input under this learning rule. The bottleneck has moved, again, to the
**learner** — which has been the finding of every record since D-84.

**Caveats:** one seed each; the base arm itself ranged +3.68 to +9.09 across seeds (D-120); the probe's learner, not the
product's head; and "three extra constant-ish dimensions collapse it" is an observation, not a mechanism — a controlled
test (three extra *irrelevant-but-varying* dimensions vs three constant ones) would separate perturbation from
degeneracy.
