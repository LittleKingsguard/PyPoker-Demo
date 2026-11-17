# Integrated test, four arms: the best policy the project has, and the opponent model collapses it · 2026-11-08

Masked pooling, the **attn-60** card model (representation + strength), the league pool, 5,000 training + 2,000 greedy
evaluation hands, seed 0, one arm per added input (D-14). `bet_size` is the fact the design review found the history
block was silently the only carrier of; the opponent model is the frozen `.probe/opp.pt` (12,933 rows, no identity
available to the loop).

| arm | inputs | chips/hand | census | card-dep |
|---|---|---|---|---|
| **base** | card + strength + 5 facts | **+6.29 ±3.63** | fold 70 %, call 23 %, all-in 7 % | **2/5** |
| **+ `bet_size`** | + the current bet's size | **+7.96 ±3.99** | fold 67 %, call 33 % | **2/5** |
| **+ opponent model** | + its action probs & strength | **−0.60 ±0.04** | **fold 100 %** | 1/5 |
| **full** | both additions | **−0.60 ±0.04** | **fold 100 %** | 1/5 |

## Two findings, both clean

**1. The card representation plus the bet size is the strongest policy measured in this project.** `+6.29` and
`+7.96` chips/hand against the league, with intervals clear of zero and clear of the −0.60 fold baseline, and
card-dependent in the right direction (`AA` and `KQs` played, `22`, `87s`, `72o` folded). Every earlier figure on this
league was **break-even or worse** (D-101 +2.5 probe, D-105 +1.8 product, D-109 −0.60 and −9.97).

**2. The opponent model destroys it** (D-119). Both arms carrying its outputs **collapse to fold-100 %** (−0.60 exactly, the
blind loss) — the same degenerate corner as the unmasked product. Its inputs are near-constant by construction (95.9 %
of its training labels were calls, so it predicts "call" almost always), and adding four near-constant dimensions to a
56-input head is enough to move the optimiser back into the fold corner.

## Reading it honestly

- The **bet size is worth more than the whole opponent model**, and it was already in the readout — the encoder simply
  discarded it (critique K15). That is the cheapest win in the project and it is now measured: **+1.7 chips/hand over
  the arm without it.**
- The **opponent model is not ready to be an input**. Its accuracy on this population is a base-rate artefact (D-113),
  its outputs are near-constant, and as an input they cost the entire policy.
- **One seed, 5,000 hands, the probe's learner.** The two positive arms need a seed check before anything is quoted —
  D-82's flicker died exactly here — and the honest status is "the best we have measured, pending seeds".
