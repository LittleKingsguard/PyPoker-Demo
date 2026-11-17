# The opponent model, built and trained: actions partial, strength zero · 2026-11-08

Built as requested: **nine noisy opponents** (three folders × ignore-the-rule-and-raise at p = 0, 0.25, 0.50) plus a
caller, and an attention model over a seat's **action history** with two heads — next action family (fold/call/raise)
and that seat's hand strength (Monte-Carlo equity given the board it could see). 17,216 decision rows, 800 six-seat
hands, 85/15 split (D-14).

| head | held-out |
|---|---|
| **action accuracy** | **0.9284** against base rate **0.9574** → **lift −0.029** |
| fold (90 cases) | recall 0.26, precision 0.18 |
| raise (20 cases) | **recall 0.00** |
| **hand strength** | **R² −0.016** |

**Give it the opponent's identity** — a 9-way one-hot standing in for the cross-hand memory the project lacks:

| head | without | **with identity** |
|---|---|---|
| fold recall · raise recall | 0.26 · 0.00 | **0.83 · 0.25** |
| accuracy · **strength R²** | 0.9284 · −0.016 | 0.9388 · **−0.012** |

**Knowing who the opponent is transforms the rare-action heads**; precision stays poor (0.37 / 0.19) and accuracy stays
below the majority baseline — with 95.8 % of decisions being calls, **accuracy is the wrong metric**, as the critique
predicted (K20).

## What it establishes

1. **Strength is not in the history** — R² ≈ 0 with and without identity: their actions depend on their cards, but
   nothing in their *prior actions* reveals them at the decision that matters.
2. **Actions are partially learnable, only with identity** — within-hand history finds folds at 26 % and raises at 0 %;
   a persistent id lifts fold recall to 83 %. That is the **cross-hand carrier** the critique found no home for (K14).
3. **The variants work**: the noise parameter produces the rare events (3.5 % folds, 0.8 % raises) that made the
   per-class analysis possible.

## Limits

One collection seed, 800 hands, 2,583 held-out rows, a 120-draw equity label; precision is low enough that a threshold
sweep is owed before any "it detects opponents" claim. This record establishes **where the signal is**, not how well it
extracts. Two of my own defects were caught mid-build: the label used the **final** board for preflop decisions (the
alignment error the critique named), and the evaluator needed the **runout sampled** for partial boards.
