# With a live trunk the policy folds to every bet — D-107 was measuring the wrong field · 2026-11-08

The dead trunk of D-108 was real, so the same 15,000-hand comparison was rerun at **`net-chips-normalised`** (the
utility D-67 showed revives the trunk), and the trunk re-measured (D-14):

| configuration | trunk alive (layer1/layer2) | fold when facing a bet | **showdown** | chips/hand |
|---|---|---|---|---|
| `net-chips` 15k (D-107's model) | **0 / 50 · 0 / 50** | 0 % | — | −0.600 |
| **`net-chips-normalised` 15k, control** | **22 / 50 · 23 / 50** | **100 %** | **0.0 %** | −0.600 |
| **`net-chips-normalised` 15k, strength + seeded** | live | **83 %** (raises 15 %) | **0.0 %** | **−9.97 ±0.88** |

## Two corrections

**1. My showdown measure was wrong.** The record's `reveal` field is *always present* — it is the cards shown to the
agent, not a showdown indicator. D-107 read that field and reported "100 % reached the reveal"; the correct measure is
`reveal["showdown"]`, and on it the **live-trunk policy reaches showdown in 0.0 % of hands**.

**2. Therefore the behaviour D-107 reported was the dead trunk, and the live policy does the opposite.** With a dead
trunk the network is a constant and calls everything (fold 0 %). With a **live trunk** it **folds to every bet** —
100 % when facing one, 0 % when not — and never shows down. That is exactly D-72's fold pinning, now confirmed on a
policy that can see its input.

## What the strength input does, now that it reaches the decision

**It changes behaviour — and makes it much worse.** The control folds to every bet for −0.60; the strength+seeded arm
**raises half-pot 15 % of the time** into a league that contains raisers and loses **−9.97 ±0.88 chips/hand**, sixteen
times the blind. So:

- **D-104 is superseded**: with a dead trunk the input could not matter; with a live trunk it does, and its effect is
  **harmful** — it converts a folding policy into an aggressive one that gets punished.

## The corrected answer to "does it go to the reveal?"

**No — with a live trunk it never does** (D-109). It folds to any bet, keeps the blind loss, and never gets to showdown. The
"calls everything down" behaviour exists only in the dead-trunk checkpoint, where the policy cannot see anything.
