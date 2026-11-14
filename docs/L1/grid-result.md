# PyPoker-Demo — what the mechanism grid measured, and what L1 rules out

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-14
- **Owns:** the outcome of D-62's twelve-cell grid as a **shape and a verdict** — which cells are alive
  and which unusable, which axis decides it, and what D-61's [0,1] change did and did not move — with
  the figures beside the run records they belong to (ASM-23, D-61, D-62)
- **Ceiling:** 105 lines. The table is the deliverable and the caveats are what make it readable; a split
  by owner would separate a verdict from the numbers it is read with (D-62, ASM-23)

## 1. The answer, in one line

**Normalisation did not revive the input path.** Every `net-chips` cell is a dead, constant network —
one score vector per seed over 219-879 distinct observations, ‖hidden‖ 0.0000, the output bias doing all
the work — and every `stack-shortfall` cell is alive and state-dependent at the fold shares the
pre-normalisation records carry (`normalisation.md` §6, §7; D-59, D-60, D-61). The axis that decides
whether the trunk lives is the **utility**, and it decided it before this change as well.

## 2. The grid, as measured

12 cells × seeds 0-2, `six-seat-no-limit-100`, 15,000 training hands, one exploration-off pass of 2,000
hands per seed, `pool-8386c3ef83ae48b2` in **36 of 36** records, 36 of 36 instrument passes. Pooled
columns are over the three seeds' hands; `distinct` is score vectors over distinct observations summed
across seeds, so the ratio is the readable figure (`normalisation.md` §6, `records.md` §15).

| cell | utility | est. | enc. | fold % | chips/hand ± 95 % | active L1 / L2 | ‖hidden‖ / ‖b_out‖ | distinct | verdict |
|---|---|---|---|---|---|---|---|---|---|
| net-masked-flat | net-chips | masked-Q | flat | 7.4 | −1.77 ± 3.69 | 1/36 · **0/36** | 0.00 / 12.32 | 3 / 1977 | **unusable** |
| net-masked-tokens | net-chips | masked-Q | tokens | 0.0 | −1.78 ± 4.10 | **0/50 · 0/50** | 0.00 / 11.02 | 3 / 2637 | **unusable** |
| net-doubleq-flat | net-chips | double-Q | flat | 12.5 | −1.80 ± 3.48 | 2/36 · **0/36** | 0.00 / 11.19 | 3 / 2637 | **unusable** |
| net-doubleq-tokens | net-chips | double-Q | tokens | 0.0 | −1.89 ± 4.03 | **0/50 · 0/50** | 0.00 / 10.08 | 3 / 2637 | **unusable** |
| net-cf-flat | net-chips | counterfactual | flat | 66.7 | −1.52 ± 0.86 | 1/36 · **0/36** | 1.99 / 35.87 | 8 / 1539 | **unusable** |
| net-cf-tokens | net-chips | counterfactual | tokens | 0.0 | −3.87 ± 4.00 | **0/50 · 0/50** | 0.00 / 53.04 | 3 / 2637 | **unusable** |
| short-masked-flat | shortfall | masked-Q | flat | 81.5 | −0.99 ± 1.01 | 19/36 · 19/36 | 0.75 / 0.13 | 1101 / 1101 | alive |
| short-masked-tokens | shortfall | masked-Q | tokens | 81.7 | −1.02 ± 0.25 | 23/50 · 24/50 | 3.79 / 0.03 | 1314 / 1314 | alive |
| short-doubleq-flat | shortfall | double-Q | flat | 80.6 | −1.80 ± 0.94 | 19/36 · 20/36 | 0.75 / 0.13 | 1115 / 1115 | alive |
| short-doubleq-tokens | shortfall | double-Q | tokens | 69.1 | −8.24 ± 1.02 | 22/50 · 25/50 | 3.78 / 0.03 | 1539 / 1539 | alive |
| short-cf-flat | shortfall | counterfactual | flat | 77.4 | −0.98 ± 0.97 | 20/36 · 20/36 | 0.77 / 0.15 | 1243 / 1243 | alive |
| short-cf-tokens | shortfall | counterfactual | tokens | 92.7 | −0.48 ± 0.04 | 22/50 · 24/50 | 3.81 / 0.03 | 990 / 990 | alive |

**Six unusable, six alive, and the split is exactly the utility axis.** The recorded pre-change values
were `net-chips` 0 of 36 live units at flat with 0 % folds, and `stack-shortfall` 77.5 % flat and 92.7 %
tokens with live trunks (`input-collapse-rca.md`, `token-seven-seeds.md`): the same six-and-six, at the
same fold shares, read with the same instrument (D-60).

## 3. What normalisation changed, and why it was not enough

- **Dense: nothing a hand can produce.** Every `flat-numeric` slot was already inside [0,1] on every
  readout the engine deals (`normalisation.md` §2), so a before/after dump of every observation over the
  three shapes and both encodings is bit-identical; the clamp fires only on the invented
  over-denominator readouts of `normalisation.md` §4. Measured over 7,405 real decisions: the largest
  `to_call` and `stacks` numerators sat exactly at 1.0 of their denominator, `pot` at 0.883, `limit` at
  0.14 — **zero** slots above 1. What the dense family gained is the declared bound and its assertion.
- **Tokens: the row the trunk reads, and only that.** The bounded embedding is a real change to what a
  trained token model computes (`normalisation.md` §3), and it moved no verdict.
- **Why the trunk stayed dead:** D-60's chain has the input's magnitude first and the **target's scale**
  second, and the grid shows the second operative — with inputs bounded and the reward still O(100), the
  `net-chips` cells reproduce the pre-change collapse and the same parameter regimes (D-60, D-61). A
  bound on the input cannot move a fixed point the reward sets.
- **The same scale also breaks numerically**: two `net-chips` runs stopped on the declared parameter band
  at 45 s and 60 s (`LearningDiverged`, D-45), and neither the twelve `stack-shortfall` arms nor any
  token arm did. Both refused runs then **completed on an identical retry**, so the refusal is a
  stability fact and not a property of the cell (§5).

## 4. Once the network can see, does the mechanism matter?

- **The utility still dominates, and it is the only unambiguous effect**: 0-12.5 % folding against
  69-93 %, one score vector against one per distinct observation, 0-2 live units against 19-25 in both
  layers (D-20, D-58).
- **The encoding still modulates, where there is a trunk to modulate**: `card-tokens` carries **more**
  active units than `flat-numeric` in all three estimator pairs under `stack-shortfall` (L1 19→23, 19→22,
  20→22; L2 19→24, 20→25, 20→24) and folds 92.7 % at its steadiest cell — the pre-change direction
  (D-53, D-56). Its fraction of width is slightly lower (46 % of 50 against 53 % of 36), so the honest
  form is "more live units, not a larger share", and distinct-score totals favour tokens in two pairs of
  three (1101→1314, 1115→1539, but 1243→990 under the counterfactual).
- **The rule and the counterfactual still move nothing attributable**: every estimator delta is inside
  the within-cell seed spread — `short-masked-tokens` folds 93.6 / 65.3 / 92.1 % across its own seeds,
  and `net-cf-flat` folds 38.6 / 93.1 / 91.9 %, the attractor lottery recorded before
  (`attractor-sweep.md`, D-58). At three seeds the estimator axis is not separable from the seed.

## 5. What it does not say, and what would be needed to say more

- **No chip edge anywhere**: every pooled rate is negative, several intervals reach zero, and "less
  negative" is not a gain (D-6, D-56). The one large-looking number, `short-doubleq-tokens` at −8.24, is
  one seed's outlier (−23.88 against −0.38 and −0.47).
- **Two "alive" readings rest on one unit**: `net-cf-flat` seeds 0 and 2 pass the §6 rule with a single
  active L2 unit of 36 (mean 0.0) and one score vector of 5 and 2 — by the letter alive, by substance
  indistinguishable from dead. The verdict column is the rule's, and the substance is this bullet.
- **The two refusals are unreproducible**: identical seed, configuration and pool, and both completed at
  the second attempt, so those seeds are single-shot survivors and the learner's stability is unmeasured
  (D-45).
- **The instrument is not the training table**: the census and chips come from each run's own mixed-pool
  pass, the active units and score vectors from one pinned oracle-free replay, so the two readings are
  two samples and never one (ASM-23).
- **The deal stream drifts between processes**, so a cell reproduces its regime and not its digits
  (ASM-2, `normalisation.md` §7).
- **What would settle the mechanism question**: more seeds on the estimator axis, which is the only
  lever still inside the noise, and a decision on the **reward/value scale** — an L0 decision, not taken
  here — because that is the term the RCA measured operating (`input-collapse-rca.md`, D-20).

## 6. Where the numbers are

Beside the run records: 36 records under `/tmp/grid62/records/<cell>/seed-<k>.json` and 36 instrument
files under `/tmp/grid62/instruments/<cell>/`. A prose figure outlives its build by exactly one run, so
this document states the shape, the axis and the band and points at the artefact for the number
(ASM-23, `protocol.md` §2).
