# In the product's learner the strength input and seeded embeddings change nothing · measured 2026-11-08

The surface change landed (S1–S3, D-102), so the question D-92 left open could finally be asked **of the product**:
does feeding the supervised strength, with the card embeddings seeded from the same model, change what the product's
`masked-q-learning` learner does?

**Configuration**: six seats, `card-tokens`, `token-embedding` 50×2, `stack-shortfall`, the league pool (pure folder /
50-50 raiser / aggressive raiser), 5,000 hands, seeds 0–2, both arms identical except the two new keys (D-14).

| arm | seed 0 | seed 1 | seed 2 | census |
|---|---|---|---|---|
| **strength + seeded** (obs 123, v6) | **−0.600** ±0.036 | **−0.600** ±0.036 | **−0.600** ±0.036 | **fold 100 %** |
| **control** (obs 122, v4) | −0.600 ±0.036 | −0.600 ±0.036 | −0.600 ±0.036 | **fold 100 %** |

**Identical.** Both arms fold every hand and lose exactly the blind (D-72's fold value) in all six runs. The
declarations are live — the strength arm's observations are 123 long, its containers are version 6, and its card rows
are seeded from `attn-60` — and the behaviour is unchanged.

## What this reframes

The probe gained **+11.6 chips/hand against scripted opponents** and **+2.5 against this same league** (D-99, D-101).
The product's learner gains **nothing** with the same representation available. The remaining difference between the
two is the **learning rule**: the probe applied a **Monte-Carlo per-hand target** to every decision of the hand, while
the product bootstraps a one-step TD target per transition.

**So the credit-assignment fix that mattered in the probe was not the representation alone** — it was the
representation *plus* a target that carries the hand's outcome back to the decisions that caused it. A representation
is necessary and, in the product's rule, not sufficient.

## Consequence

The next change worth making is the one this isolates: a **Monte-Carlo return target** as a declared learning-rule
axis, then the same two-arm comparison. That is a surface change of the same size as the counterfactual axis, and it
is the only remaining explanation consistent with every measurement in this line.
