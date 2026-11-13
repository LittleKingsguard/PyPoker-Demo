# agents — the finiteness envelope: the target's bound and the parameter band

- **Owner:** D-45's two bounds realised — the class (§1), `learn`'s three sites and their order (§2), the three messages (§3), the
  finiteness argument and why a band message never prints `inf` (§4), the guardrail and the cases (§5)
- **Ceiling:** 60 lines. At the ceiling, split by owner — never append
- **Rev:** 1 · **Date:** 2026-11-11 — D-45's envelope: `CounterfactualUnbounded`, `declarations.PARAMETER_BAND`, the batch-start
  band sweep and GUARD 2's second predicate
- **Read with:** `README.md` §2, §4, §5, `errors.md` §2–§3, `rule.md` §3, §6, `divergence.md` §1–§4, `checkpoint.md` §1 and the L2
  owner `docs/L2/agents/finiteness.md` §1–§5, whose contract, sites and strings this document realises

## 1. The class, the declaration, and the measurement they answer

`errors.py` gains a **twenty-third** subclass, `class CounterfactualUnbounded(AgentsError)`, the sibling of `LearningDiverged`:
the target's fault rather than the state's. `declarations.py` gains one declaration beside `HYPER`, `PARAMETER_BAND = 1e6`, whose
own comment carries §4's argument and which is published nowhere new — `learners()` keeps its six keys and each `counterfactuals`
member its three (`surface.md` §3, `rule.md` §6, D-45). The measurement stands: a `reveal-counterfactual` variant died on its **first
transition** with `-inf` while its targets were bounded, so the `-inf` was the **update**'s, where `δ = v − q` reads the learner's own
output (`counterfactual.md` §10, `docs/L2/agents/finiteness.md` §1).

## 2. The three sites, in the order `learn` reaches them

1. **Before the batch is read.** `learn` reads `backend.parameters(state)` — the whole `2·P` array — through `learner._outside_band`,
   which answers the first `(index, value)` that is **finite and above `PARAMETER_BAND`**, and refuses as `LearningDiverged` before
   any validation, forward pass, step, refresh or move of the position (`checkpoint.md` §1, `surface.md` §9).
2. **During a transition's validation.** `_transition(learner, record, index, bound)` refuses as `CounterfactualUnbounded` any
   `counterfactual` value whose magnitude exceeds `bound` — the chips in play `T = seats × starting_stack`, read once per batch through
   `learner._chips_in_play` from `engine.game_config(learner.game)`, never a number written here (`shapes.md` §2, `seats.md` §2, D-29).
   `bound` is `None` on the `none` path, which reads no sequence, and a value exactly at `±T` is inside the bound and is stepped.
3. **After each step, in GUARD 2's place.** The `numpy.isfinite` sweep is unchanged and runs first, so a step that left a non-finite
   value keeps its own message and value; the **same read of the same array** then goes through `_outside_band`, and a step that
   left a finite value above the band refuses as `LearningDiverged`, naming the site — transition index, and the action index on the
   member's path — the parameter index, the value and the band, after the step and before the counter, the refresh and the returned
   statistics (`divergence.md` §2, `rule.md` §3, §6).

## 3. The three messages

`errors.md` §3's last rows carry them verbatim, and **no band message can report a non-finite number**: both band sweeps are
`isfinite(values) & (|values| > band)` on one read of one array, so the non-finite branch raises first (`divergence.md` §3, D-45).

    learn(transitions): the learner's parameter index 118 is already 15000000.0, beyond the declared parameter band 1000000.0, so no transition is read
    learn(transitions): transition index 41 at action index 2 drove parameter index 118 to -32000000.0, beyond the declared parameter band 1000000.0, and the learner has diverged
    learn(transitions): transition index 0 at action index 1 carries the counterfactual value -812.5, which is outside the bound 600.0 of the chips in play on the shape 'six-seat-no-limit-100'

## 4. The finiteness argument, and the two readers it justifies

A step writes `θ ← θ + rate·δ·g`; inside the band a forward pass of the catalogue's kinds is bounded by `Θ^(D+1)·X·W^D` and a
step's movement by `rate·Θ^(D+2)·X²·W^(D+1)`, which with `Θ = 1e6`, `rate = 1e-3`, `D ≤ 4`, `W ≤ 512` and `X ≤ 600` are ≈1e33 and
≈1e58 — eleven to twenty orders below the float64 maximum. So no step taken from inside the band can write a non-finite value, and
the first step that would leave it is refused after it is written but before the counter, the refresh and the statistics move —
which is what makes `-inf` unreachable (`declarations.py`, `architecture.md` §4, `seats.md` §2, D-45). Both readers are
**comparisons**: `_chips_in_play(learner)` imports the granted `engine.game_config(learner.game)` inside the function and
`_outside_band(values)` is an `argmax` over one boolean array — no clip, rescale or change of `rate`, so the finite path's digits
do not move (`backends.md` §2, `baselines.md` §9, `divergence.md` §4, D-45).

## 5. The guardrail, the cases, and what is left to L4

L4: two comparisons added to `learn`, one class, one constant and the frozen `learners()` record. AGT-16.1–16.7 keep the divergence
family's digits and refusals; FAM-23 pins the envelope — a target out of bounds refused by name with the learner untouched, a value at
the bound stepped, a container restored outside the band refused before any forward pass, no message reporting `inf` or `nan`, and a
`none` run carrying no `finiteness` key (`battery.md` §3 FAM-23, `guardrails.md`, `docs/L3/training/record.md` §5, `records.md` §12).
