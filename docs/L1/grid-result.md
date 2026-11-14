# PyPoker-Demo — what the mechanism grid measured, and what L1 now rules out

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-14
- **Owns:** the outcome of D-62's twelve-cell grid as a **shape** — which cells are alive and which are
  unusable, which axis decides it, and what the [0,1] change of D-61 did and did not move — with every
  figure left beside the run records it belongs to (ASM-23, D-61, D-62)
- **Ceiling:** 70 lines. At the ceiling, split by owner — never append

## 1. The answer, in one line

The grid's alive-or-unusable column (`normalisation.md` §6) reads along the **utility** axis and no
other: every `net-chips` cell is a dead, constant network, and every `stack-shortfall` cell is alive and
state-dependent at the fold shares the pre-normalisation records carry. The [0,1] normalisation
therefore **did not revive the input path**, and the reason is measured rather than argued (§2, §3).

## 2. What normalisation changed, and what it did not

- **Dense: nothing a hand can produce.** Every `flat-numeric` slot was already inside [0,1] on every
  readout the engine deals (`normalisation.md` §2), so a before/after dump of every observation over the
  three shapes and both encodings is bit-identical and only the invented over-denominator readouts of
  `normalisation.md` §4 move. What the dense family gained is the **declared bound and its assertion**,
  not a new scale.
- **Tokens: the row the trunk reads, and only that.** The bounded embedding is a real change to what a
  trained token model computes (`normalisation.md` §3), and it changes no verdict.
- **Widths, heads, `param_count` and the container format are untouched**, so the shipped containers
  load and stay comparable — the cost D-61 declared is smaller than it declared (D-61, `shapes.md` §8).

## 3. Why the input bound is necessary and not sufficient

D-60's chain has five steps and the input's magnitude is the first while the value scale is the second
(`input-collapse-rca.md`). The grid shows the second one operative: with inputs bounded, the `net-chips`
cells reproduce the pre-change collapse **exactly** — a hidden layer with no active unit, ‖hidden‖ zero,
one score vector over thousands of distinct observations, and the output bias carrying the constant
(§4) — while the parameter norms the RCA measured at 313 and 82 are reproduced to the digit. A bound on
the input cannot move a fixed point that the target's scale sets.

- The same scale also breaks **numerically**, not only behaviourally: three `net-chips` × `flat-numeric`
  runs stopped on the declared parameter band instead of reaching a battery, and the bounded-reward
  cells never stopped in eighteen of eighteen (`normalisation.md` §4, D-45).
- **The encoding modulates magnitude only where the trunk is alive**: under `stack-shortfall` the token
  trunk is the more active one and folds higher, which is the pre-change separation; under `net-chips`
  the two encodings differ in which constant policy their output bias fixes, and in nothing else
  (D-3, D-56).
- **The estimator is inert in both regimes** — masked-Q, double-Q and the reveal counterfactual stay
  dead together and alive together — which is D-58's finding, now separated from its cause (D-58, D-59).

## 4. The verdict rule it was read with

A cell is **unusable** when a hidden layer has no active unit *and* the score vectors are constant,
**alive** when both instruments read above that floor, and **partial** otherwise (`normalisation.md`
§6). No measured cell was partial: the two instruments moved together in every one, which is itself
evidence that they measure one thing — the network's dependence on its input (D-59, D-60).

## 5. What L1 rules out, and what it puts next

- **Ruled out:** a further architecture rung as the repair for the dead trunk (`R4`, `R5` and `R6` stay
  declared and unmeasured, D-62); and the reading that the collapse is an **input-range** defect, which
  D-60's step 1 proposed and this grid falsifies (D-60, D-61).
- **Put next — an L0 decision, not taken here:** the **reward/value scale** — a normalised reward or a
  bounded target on the utility axis — because the axis that decides whether the trunk lives is the
  utility and the term the RCA measured operating is the target's magnitude (D-20, D-60).
- **Not claimed:** any chip edge. Every interval in the grid spans zero or sits below it, so "less
  negative" is not a gain (D-6, D-56).

## 6. Where the numbers are

Beside the run records, not here: a prose figure outlives its build by exactly one run, so a document
states the shape, the axis and the band and points at the artefact for the number (ASM-23,
`protocol.md` §2).
