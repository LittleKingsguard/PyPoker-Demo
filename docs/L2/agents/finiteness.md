# agents — the finiteness envelope of the counterfactual member

- **Layer:** L2 · **Module:** `agents` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-11
- **Owner of this file:** D-45's two bounds — the target bounded by the game and the declared parameter band (§1–§2), the
  three sites `learn` refuses at (§3), the record's block and what none of it changes (§4)
- **Read with:** `divergence.md` §1–§4, `surface.md` §3, §7, `learner.md` §1, `docs/L3/agents/finiteness.md` §1–§5,
  `docs/L1/counterfactual.md` §10, `records.md` §12, `docs/L2/training/loop.md` §3
- **Ceiling:** 60 lines. At the ceiling, split by owner — never append

## 1. The measurement, and the two quantities it separates

A `reveal-counterfactual` + `stack-shortfall` variant died on the **first transition** of a six-seat run — `600` chips in
play — with `LearningDiverged … got -inf`, though its counterfactual values were bounded. The `-inf` came from the **update**:
a plain step `θ ← θ + rate·δ·g` whose `δ = v − q` reads the learner's own output is positive feedback, and nothing bounded
`|θ|` (D-45, `counterfactual.md` §10). This file is split out of `divergence.md` at its ceiling, because that refusal's fault
is neither the caller's argument nor the learner's state alone (`divergence.md` §1).

- **The target is bounded by the game.** A branch's value is one seat's whole-hand net chip delta, so it lies in
  `[−s₀, T − s₀]`, `T = seats × starting_stack` the chips in play, and §4's transform keeps it inside `±T` under both
  utilities — so `T` is the declared bound, **read** from `engine.game_config(learner.game)` and never a number here
  (`counterfactual.md` §4, §10, `shapes.md` §2, `seats.md` §2, ASM-44, D-29).
- **The update is not**, and `divergence.md` says what its guard is worth: it catches only non-finite values, so a run could
  walk past the float64 maximum before anything objected — and neither bound clamps anything, because a clamp would change
  the target the record carries (ASM-7, `surface.md` §1, `docs/L3/agents/divergence.md` §1, D-45).

## 2. The declared parameter band, and why `1e6` makes `-inf` unreachable

`declarations.py` declares `PARAMETER_BAND = 1e6` **beside `HYPER`** and publishes it nowhere new — `learners()`'s six keys and
each `counterfactuals` member's three stand, so no published record grows (`surface.md` §3, `rule.md` §6, D-45): no parameter of
the `2·P` array — online and target copy — may keep a magnitude above it (`learner.md` §3). **The argument is arithmetic:** inside
the band a forward pass of the catalogue's kinds is bounded by `Θ^(D+1)·X·W^D` and one step's movement by
`rate·Θ^(D+2)·X²·W^(D+1)`, so with `Θ = 1e6`, the declared `rate = 1e-3`, `D ≤ 4`, `W ≤ 512` and an observation bounded by the
chips in play (`X ≤ 600`) those are ≈1e33 and ≈1e58 — eleven to twenty orders below the float64 maximum of 1.8e308. So **no step
taken from inside the band can write a non-finite value**, and the first step that would leave it is refused after it is written
but before the counter, the refresh and the statistics move (`architecture.md` §4, `seats.md` §2, `docs/L3/agents/rule.md` §3, §6).

## 3. The three sites, and their order in `learn` (`docs/L3/agents/finiteness.md` §2)

| What it refuses | The message names |
|---|---|
| a learner restored with a parameter already outside the band, before the batch is read | the entry point, the parameter's index, its value and the band; no transition is read (§4) |
| a step that left a **finite** value above the band, in GUARD 2's place — and the non-finite one it always refused | the site, the parameter index, the value and the band (`docs/L3/agents/divergence.md` §2) |
| a `counterfactual` value whose magnitude exceeds the chips in play, during a transition's validation | the entry point, the transition's 0-based index in the caller's batch, the action index, the value and the bound (§4) |

The target's bound is a **validation** refusal — before any forward pass, parameter change, target refresh or advance of the
schedule position, with a value exactly at `±T` inside it and stepped normally — and only `reveal-counterfactual` reads it, so no
`none` run can reach it (`divergence.md` §4, `surface.md` §7, `counterfactual.md` §6, D-45). The two band refusals are the existing
`LearningDiverged`; the target's is the new `CounterfactualUnbounded`, its sibling under `AgentsError` (`errors.md` §2, D-12).

## 4. The record's block, and what none of it changes

A run whose member is not `none` gains one **conditional** key, `finiteness`, beside `counterfactuals`: per variant per seed, the
member, the `transitions` its episodes resolved fully, the `steps` it took, the `largest_target` it was handed and the
`target_bound` in force (`records.md` §12, `docs/L2/training/loop.md` §3, `docs/L3/training/record.md` §5). A run declaring no
member writes no such key, and a run a guard refused writes no record — its refusal being the other half of the evidence, the
conditionality what keeps the two committed captures byte-identical (`counterfactual.md` §9, §10, `battery.md` §3 FAM-23).

The guards are **comparisons only**: no clipping, rescaling, gradient normalisation or change of `rate`, `HYPER`, either backend,
the two rules, the three utilities, the initialisation, the tie-break, the schedule or the step counts, so a finite run's digits are
unchanged and every artefact keeps its bytes (ASM-7, D-19, D-20, `divergence.md` §4, `counterfactual.md` §9).
