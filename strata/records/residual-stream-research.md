# The residual stream — what R6 must compute · 2026-11-05 (D-15)

Source: `https://lizeman.github.io/llm-arch-kb/residual/residual-overview/` (LLM Architecture KB,
"The Residual Stream (Residual)"), fetched 2026-11-05. This record defines the technique the
brief's R6 row names, so R6 is a construction and not a borrowed label (intake finding C-C9).

| Claim | Source | Confidence | If false |
|---|---|---|---|
| The residual stream is the `R^d` vector flowing through the model's depth; a sublayer **writes a delta into it** rather than replacing it | page §1 premise, §2 derivation | high | R6 would be misnamed and must be redefined |
| A plain block is reparametrised from `x_{l+1} = H_l(x_l)` to `x_{l+1} = x_l + f_l(x_l)`, with `f_l = H_l - x_l` | page §2 | high | the rung's arithmetic changes |
| The "do nothing" default becomes `f_l ≡ 0`, reachable by zeroing a sublayer's last linear term — the identity is a default rather than a coordinated weight pattern | page §2 | high | the rung's initialisation story changes |
| For a transformer block the construction is applied twice, pre-norm: `y_l = x_l + Attn_l(Norm(x_l))`, `x_{l+1} = y_l + FFN_l(Norm(y_l))` | page §2, §3 | high | the block arrangement at R6 differs |
| The gradient through `L − l` blocks is a product of `(I + ∂f_k/∂x_k)` factors, so a bounded local Jacobian keeps the gradient from collapsing with depth | page §2 | high | the justification for the rung weakens |
| The motivating failure is an optimisation gap, not generalisation: past ~19–22 plain layers, training error itself regresses | page §1 (citing He et al. 2015, Simonyan & Zisserman 2015, Szegedy et al. 2015) | high | the rung's motivation changes |
| The paper documents depth-wise accumulation in the stream (each block adds a perturbation and nothing trims it) | page §4, citing Xiong et al. 2020 §4.2 | medium (summary of a cited work) | the "stream as shared bandwidth" reading weakens |

## What this fixes for R6

- The rung is a **construction**, not a metaphor: a stack whose every block computes an additive
  delta on one carried vector, with pre-norm feeding each sublayer and the residual path present
  from initialisation (D-3).
- Its control is the same stack with the residual path removed at matched parameter budget
  (`ASM-13`, D-6): "residual vs plain" is the pair, so the rung demonstrates the technique instead
  of naming it.
- Nothing here licenses a claim that the stream "carries context across streets" for a poker
  model — that would be this project's hypothesis, and it is only reportable if the paired rung
  measures it (D-6, D-16).
