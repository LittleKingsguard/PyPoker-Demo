# The stack-shortfall runs do not converge to never-fold · measured 2026-11-08

Raised against D-47's review, which omitted the utility axis: does the `stack-shortfall` utility (D-20)
fold where `net-chips` does not? The ablation artefact answers it — `/tmp/pypoker-utility-ablation.json`,
two-seat no-limit, 100-chip stacks, the folder pool, **1,000 training hands** and a 1,000-hand census per
seed, three seeds per arm (D-14).

| arm | seed | decisions | folds | fold % | raise % | check-call % | chips/hand |
|---|---|---|---|---|---|---|---|
| `net-chips` | 0 | 3,988 | 4 | **0.10 %** | 97.3 % | 2.6 % | +0.102 |
| `net-chips` | 1 | 3,988 | 4 | **0.10 %** | 95.9 % | 4.0 % | −0.276 |
| `net-chips` | 2 | 3,967 | 11 | **0.28 %** | 86.9 % | 12.9 % | +0.131 |
| **`stack-shortfall`** | 0 | 3,904 | 32 | **0.82 %** | 60.6 % | 38.6 % | +0.068 |
| **`stack-shortfall`** | 1 | 3,637 | 121 | **3.33 %** | 48.3 % | 48.4 % | −0.341 |
| **`stack-shortfall`** | 2 | 3,622 | 126 | **3.48 %** | 82.4 % | 14.2 % | +0.048 |

## What it means for D-47

D-47 said folding appears in "one run of twelve" and described everything else as never-fold. That was
wrong on two counts, both mine:

1. **The utility axis was omitted from the review**, and it is the one axis where folding appears **at all
   three seeds**: 0.82 / 3.33 / 3.48 % against 0.10 / 0.10 / 0.28 % for the net-chip control on the same
   pool — a ten-to-thirty-fold difference, consistent across seeds.
2. **"Never fold" was too strong** (D-6). The net-chip arms fold 0.10–0.28 % of decisions; what is true is that
   they are *effectively* never-folding, not literally so.

## What it does not mean

- **The rate is small** (D-6): 3.5 % of decisions is not a folding strategy, and the two arms' chip intervals
  overlap, so no chip advantage is established.
- **No deep run exists for this axis.** Every stack-shortfall measurement is at 1,000 training hands, while
  the counterfactual's 40 % came at 20,000. The comparison across axes is therefore not yet like-for-like,
  and the utility axis is the cheaper of the two to take deep — one variable, no surface change.

One recorded defect of my own (D-48): the attractor sweep (`attractor-sweep.md`) labelled modes by raise and
call shares alone, so its "mixed" category **hid the fold share entirely** — the very quantity this line
of enquiry turns on. Any future sweep must count folds as a first-class column.
