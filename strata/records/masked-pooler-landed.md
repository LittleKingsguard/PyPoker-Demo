# The mask is in the product's pooler — D-79's remedy, with discriminating tests · 2026-11-08

The change D-110 named the project's highest-value item is **landed in both backends** (D-14).

**What changed:** `src/agents/numpy_backend.py` and `src/agents/torch_backend.py` now pool only the **real** rows
(`ids != 0`), with all-pad → zeros, and `apply` scatters with the **real** count and skips pad positions — so the pad
row receives **no** gradient. Nothing else moved: vocabulary, widths, layout, declarations, checkpoint version, trunk,
output layer.

**The tests discriminate.** `tests/agents/test_pooling.py` (AGT-21.1–21.5, 5 tests / 24 subtests): `[card,0,0,0]` pools
to the card's row **exactly** (not a quarter of it); the pool is invariant to trailing pad count; after one step the
embedding's **row-0 delta is exactly zero** while addressed rows move; an all-pad sequence pools to zeros with a zero
embedding gradient and no exception; numpy and torch agree with `rtol 0` and `atol 1e-12` (sum/count, so the pool is
bit-identical across backends). **Run against the pre-change backends, all five fail** — they cannot pass on an unmasked
pass. Two cases that had pinned the old behaviour (AGT-20.1, AGT-20.3) were corrected, not deleted.

| battery | before | after |
|---|---|---|
| `tests/agents` | 207 passed, 1439 subtests | **212 passed, 1463 subtests** |
| `tests/training` · `tests/evaluation` · `tests/e2e` | 144 · 172 · 341 | unchanged |

`strata-lint`: **404 checks, no failures**.
## The era boundary this declares

The pooler is a **forward pass**, so every token checkpoint trained before this change is **pre-mask era**: trained with
the pad row inside its mean, and it will behave differently under the mask. All pre-mask token results — every number
from D-79 through D-113 — are era-bound, and no post-mask run may be compared with them. The dense (`flat-numeric`)
family is unaffected.
## Statements the change makes false (recorded, not edited)

`docs/L3/agents/input-read.md:18,33,61,79`, `docs/L3/agents/backends.md:36`, `docs/L3/agents/architecture.md:41-42` (which
asserted "row 0 is a row like any other, because features' pad is an id and not a mask"), `docs/L3/agents/rule.md:164`,
`docs/L2/agents/learner.md:46,226` and `docs/L1/normalisation.md:77,126,143` all describe an unmasked mean and need an L3
pass; this record is the citation for it.
## The measurement in flight

`net-chips-normalised`, 15,000 hands, both arms, six seats, against the league. The unmasked baselines it is measured
against: **control −0.600, fold 100 %, 0.0 % showdown**; **strength+seeded −9.97 ±0.88** (D-109).
