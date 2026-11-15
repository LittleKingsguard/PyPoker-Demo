# Are the cards meaningfully distinct? The token embedding is still its initialization · 2026-11-08

D-73 left one question: why does a token model whose score vectors are demonstrably live still map every hand to
one action? This measures the embedding itself — the table the trunk reads, ids `1..52` for the 52 cards by
`1 + 4·rank + suit` (D-14).

## Distinct, but only as random vectors are

52 of 52 rows are distinct, pairwise cosines span **−0.435 to +0.453**, mean −0.001 — exactly the profile of 52
random unit vectors in 50 dimensions (per-pair sd 0.139).

**No card structure.** Same-rank pairs (`As Ad`) average **+0.0071** cosine and same-suit pairs (`As Ks`)
**+0.0072**, against unrelated pairs' −0.0049 — an excess of 0.012 against a per-pair spread of 0.139, which is
noise. Nothing in the table says aces resemble aces, or hearts resemble hearts.

## The decisive fact: it is the initialization

Seven named pairs — `As-Ad`, `As-Ah`, `As-Ks`, `As-7d`, `2c-2d`, `7c-2d`, `Ks-Qd` — all match, **to four decimal
places**, the cosines of a fresh `numpy.random.PCG64(0).standard_normal((102, 50))` draw. That is not a
coincidence: `model.py` initialises every parameter from exactly that generator and scaling, so the trained table
**is** its initialization.

The measured movement over training is **max |Δ| 0.0004** against an initial row scale of ~0.14 — **0.3 %**. Two
independent runs (masked-Q and the counterfactual) differ by 0.0004 as well; after 15,000 hands they are
indistinguishable from their shared starting point and from each other.

## So the answer, and the mechanism

**The cards are not meaningfully distinct.** They are distinct as noise, carry no rank or suit structure, and the
table that would carry it has not moved from where it started. The token model therefore reads a *random
projection* of its hole cards — which is exactly why its decisions cannot depend on them, however live its score
vectors are.

**Why it does not train** (leading hypothesis, consistent with D-67's 0.0011): only the **addressed rows** receive
gradient, mean-pooling divides it across every token position, and the squash's derivative is ≤ 0.5 — so each
row's share is tiny and thousands of hands move it 0.3 %. The flat encoding has no such bottleneck: 433 values go
straight into the trunk, and it is the only encoding whose play depends on the cards (D-71).
