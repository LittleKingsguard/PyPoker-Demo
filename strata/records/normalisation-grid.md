# Normalisation changed nothing, and the grid says why · measured 2026-11-08

D-61 normalised every input into [0, 1]; D-62 ran the **12-cell mechanism grid** (utility × estimator ×
encoding) at six seats, 15,000 hands × seeds 0–2, `pool-8386c3ef83ae48b2`, 36 runs concurrent (D-14).

## The normalisation is real, and the dense inputs were already inside it

The invariant holds everywhere — dense `[0.000, 1.000]` on all three shapes, token ids inside vocabulary,
trunk input `(0.204, 0.630)` — and is now a **battery assertion** (FEA-11, J-8.12, FAM-24).

**But a before/after dump of every observation over three shapes and both encodings — 4,744 decisions — is
bit-identical.** The dense slots *already* lay inside [0,1] because D-30's per-shape divisors were chosen for
exactly that. **D-61's declared cost was wrong for the dense family**: the shipped 18 containers stay
comparable, and only invented over-denominator readouts move. What did change is the token path, whose trunk
input is now a bounded embedding `(1 + tanh θ)/2`.

## And it did not revive the input path, because it could not

D-60's chain had two steps: (1) large inputs drive large weights, (2) the O(100) reward scale drives large
weights. **Step 1 is refuted** — the inputs were already bounded — so bounding them cannot move a fixed point
that step 2 sets. The numbers came back to the digit: ‖w_in‖ **312.9** against 313, ‖b_in‖ **82.4** against 82.

## The grid: six cells alive, six dead, three crashed

| cells | verdict | trunk | fold |
|---|---|---|---|
| **stack-shortfall** (6 cells, 18 runs) | **alive** | 12.7–31.4 active units, ‖h·W_out‖ 0.16–0.45 vs ‖b_out‖ 0.02–0.17 | flat 74.7–87.0 %, tokens 92.2–93.6 % |
| **net-chips** (6 cells, 18 runs) | **dead** | **0 active units** in the second hidden layer, one score vector over 3,143–10,700 observations | effectively 0 % (two fixed-point fold cases) |
| net-chips × flat | **3 crashes** | `LearningDiverged` against the 1e6 band (three seeds) | — |

**The axes separate with their cause identified:** the **utility decides whether the trunk lives**, the
**encoding modulates magnitude only where it lives** (‖h‖ 3.5–4.3 tokens, 0.5–0.8 flat), and the **estimator is
inert in both regimes** — `double-q` and `reveal-counterfactual` change neither census nor trunk.

## What this closes

Every flat behavioural result in this project had the same cause, and it is not the reward's *shape*:
**the reward's scale kills the hidden layer**. The repair is therefore the **value scale** — a normalised or
bounded target on the utility axis — not another input transform, not an architecture rung, and not another
estimator. R4/R5/R6 remain declared and unmeasured (D-62); they are the wrong next step for this cause.
