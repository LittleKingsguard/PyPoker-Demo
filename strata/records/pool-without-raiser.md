# The pool had no raiser, and adding one breaks the observation · measured 2026-11-07

The user's observation: the previous models *are* the aggressive raisers the league should supply. Two
findings follow, and the second is a hard blocker.
## 1. The no-limit pool held no raiser at all

The criterion's configuration was `training.rung("R1")` relabelled, and R1's declaration carries **no
version members** — the pool is D-6's three anchors plus D-21's three folders. None of those six raises:
`always-call` and the oracle 0 %, `random` a third, the folders fold. Folding was almost never correct,
so the ~0 % fold rate was the pool's answer rather than a learning failure — a learner folds 100 %
against a raiser when one exists (`fold-when-correct.md`).

The models that would have supplied the aggression are all fixed-limit containers — 18, each carrying
the two-seat, 203-slot, three-wide shape — and a no-limit pool refuses them as foreign. The second shape
therefore started with an empty league by construction: the shape change orphaned exactly the population
the league exists to provide.
## 2. Seating one breaks the encoder

A pool with one trained no-limit model added (three anchors, three folders, one version) trains until a
hand reaches **25 decisions**, then:

```
features.errors.InvalidReadout: encode(readout): 'history' must be at most 24 entries, got 25
```

The 24 slots are derived from the *fixed-limit cap* ("at most 3 × 6 + 5 = 23 applied actions"), and an
uncapped no-limit street against a raiser exceeds them. The refusal is correct and named — the encoder
truncates nothing — but it means **the no-limit shape cannot yet face the aggressive opposition the
league exists to supply**. The design kept 203 slots for both shapes and changed only the divisors, so
the overflow was latent until a raiser was seated (V-F6, D-31).
## The three ways out, none of them L0's to choose

- **Widen the history per shape** (24 → that shape's worst case): changes that shape's width, head,
  `param_count` and containers — the cost the design hoped to avoid by fixing 203.
- **Coarsen it for the uncapped shape** (aggregated entries): keeps the width, loses resolution exactly
  where the price signal lives.
- **Truncate to the most recent 24**: refused today, because a shorter history is a silently different
  observation.

This is D-32; the overnight run stays blocked until it is decided.
