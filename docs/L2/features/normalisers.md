# features — the denominator refusal: a magnitude block with no normaliser

- **Layer:** L2 · **Module:** `features` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-11
- **Owner of this file:** the refusal a shape row that carries no denominator for a magnitude block gets,
  and the declaration that raises it — its error name, the three facts its message names, that it is a
  **declaration-time** refusal, and that no declared row reaches it. Split out of `shapes.md` §2 and §6
  rather than appended to them, which are at their ceilings (D-61, `docs/L1/normalisation.md` §4,
  `docs/L3/features/errors.md` §3)
- **Reads:** `shapes.md` §2 (the divisor table) and §6 (the shape refusals), `surface.md` §4–§6 (what
  `build_encoder` and `encode` refuse), `docs/L3/features/encoder.md` §4 (the declaration table),
  `docs/L3/features/flat-numeric.md` §4 (the five denominators), `docs/L3/features/errors.md` §2–§3
  (the error family and the message grammar), `docs/L1/battery.md` §5
- **Ceiling:** 70 lines. At the ceiling, split by owner — never append

## 1. The rule: one denominator per magnitude block, and it is the shape's

Four blocks of `flat-numeric` are magnitudes — `stacks`, `pot`, `to_call` and the two slots of `limit` —
and each emits a numerator over **one** denominator, the shape row's normaliser under the key
`docs/L1/normalisation.md` §2 names (`shapes.md` §2, `docs/L3/features/flat-numeric.md` §4, D-61). The
five keys are `stack`, `pot`, `to_call`, `amount` and `count`. A block whose key is absent has no
denominator, and this module holds no second source for one: it never borrows another row's normaliser,
never divides by the largest value a run has seen, never leaves the magnitude unscaled, and never
defaults the key to a divisor (`surface.md` §6, `docs/L1/normalisation.md` §4, D-61).

## 2. The refusal, by name

A row that carries no denominator for a magnitude block is refused: building the declaration for that
shape raises `InvalidReadout` from `src/features/errors.py` — one of this module's own refusals, below
`FeaturesError`, so a caller catches "this module refused me" and never a `KeyError` from a mistyped
table (`docs/L3/features/errors.md` §2, D-61). The field named is the block's own:

| The row carries | Field named | Normaliser key named |
|---|---|---|
| no `normalisers` mapping at all | all four: `stacks`, `pot`, `to_call`, `limit` | all five: `stack`, `pot`, `to_call`, `amount`, `count` |
| no `stack` | `stacks` | `stack` |
| no `pot` | `pot` | `pot` |
| no `to_call` | `to_call` | `to_call` |
| no `amount` | `limit` (its first slot) | `amount` |
| no `count` | `limit` (its second slot) | `count` |

The message follows `docs/L3/features/errors.md` §3's grammar and names three things beside the entry
point: the **field/block** whose denominator is missing, the **missing normaliser key**, and the
**shape**. It states that the readout cannot be normalised — refused, never clamped, defaulted or
scaled by a substituted denominator (`docs/L1/normalisation.md` §4, D-61).

## 3. It is a declaration-time refusal, not a per-observation one

The refusal is raised while the declaration for that shape is built, so `build_encoder` and
`observation_spec` reach it through `declarations.declaration` and `encodings()` reaches it through the
default row's declaration. Nothing on `encode`'s path re-checks it: a built encoder's declaration is
validated once, the hot path pays nothing, and no readout can be refused for a denominator reason after
the encoder exists (`docs/L3/features/encoder.md` §4–§5, D-11). The normalisers are the declaration's and
never the observation's, which is exactly why one check per build is enough.

## 4. No declared row reaches it, and nothing else moves

All three declared rows carry all five normalisers (`shapes.md` §2), so the refusal is a structural guard
against a fourth row that would otherwise emit an unbounded slot silently — not a behaviour any declared
shape reaches (`docs/L1/normalisation.md` §4, D-61). It adds no eighth entry point to this module and no
rung to the layer map, moves no value the three declared shapes emit, and changes no width, dtype,
vocabulary or bucket ladder (`docs/L1/normalisation.md` §1, §3, D-61).

**Where it is asserted:** `FEA-12.1`–`FEA-12.3` in `tests/features/` — for **both** encodings, a
doctored catalogue row with no `normalisers` mapping and one with each of the five keys missing is
refused with the field, the key and the shape named; and a control shows the three declared rows still
build and still emit the values they emitted, so the guard cannot be met by refusing everything
(`docs/L1/battery.md` §5). Those cases patch `declarations.SHAPE_ROWS` in process and restore it, the
declared exception to "the battery reaches only the seven names" (`docs/L3/features/README.md` §3). The
layer-level family declines the case by design, because a row without a normaliser cannot be declared —
only doctored (`tests/e2e/test_fam24_normalisation.py`).
