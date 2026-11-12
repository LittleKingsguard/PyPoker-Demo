# The counterfactual member diverges at a third seed · measured 2026-11-07

D-44 asked for seeds 2–6 at the published configuration to estimate how often the revealed
counterfactual reaches the folding attractor. The run died on its **first transition** of the first new
seed:

```
agents.errors.LearningDiverged: learn(transitions): transition index 0 drove parameter index 17713
out of finite range and the learner has diverged, got -inf
```

## What this is, and what it is not

- **The guard worked exactly as designed.** A non-finite value was refused by name, with the transition
  and parameter index, instead of corrupting the run silently — the failure mode D-26 and the NaN fix
  exist for.
- **It is the member's arithmetic, not the game's.** The same configuration ran seeds 0 and 1 to
  completion (largest |td_error| 97.5 and 91.3, no non-finite value). The six-seat shape, the pool and
  the criterion are unchanged between those runs and this one, so the difference is a **target the member
  produced on a particular hand** at seed 2.
- **The build already met this once.** Full residuals (`v − q` per legal action) drove a parameter out of
  range within a hundred hands during the build, and the member's contract was changed to aggregate them
  as the mean, `(Σ v_i − q_i)/A`. That fixed the configuration the build measured; this run shows the
  aggregation is not sufficient at every seed.

## What it needs before it can be measured

A finiteness argument (D-6), not another aggregation: the member must be **unable** to emit a non-finite value —
either by bounding the target to the chip range a hand can produce (`|v| ≤ stacks × seats`) or by
refusing a branch whose inputs are outside that range, naming it. The `-inf` also implies an overflow in
the update rather than a bad input alone, which is the second half of the same defect.

## Where it leaves the counterfactual

**Kept, measured once, and not part of the first rung's close-out.** Its result stands as recorded —
folding at one seed of two, 40 % against 0 % — and it is not runnable across seeds until the finiteness
argument exists. With the talk a week away, the spend belongs to the deep run (D-45).
