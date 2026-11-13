# agents — the divergence refusal

- **Owner:** the one refusal whose fault is the learner's own accumulated state, never the caller's argument: the
  class (§1), its two sites and where each guard sits (§2), the messages (§3), what it never does (§4), its guardrail
  and cases (§5)
- **Ceiling:** 60 lines. At the ceiling, split by owner — never append
- **Rev:** 3 · **Date:** 2026-11-11 — D-45 adds the declared parameter band to GUARD 2's read of the array and a batch-start
  sweep beside it, and gives the target its own bound and class; both are `finiteness.md`'s (§2, §3)
- **Read with:** `README.md` §2, §4, §8, `errors.md` §1–§4, `rule.md` §3, §5, §8, `checkpoint.md` §1, `backends.md` §2,
  `finiteness.md` §1–§5 and the L2 owner `docs/L2/agents/divergence.md` §1–§4, whose contract, sites and strings this realises

## 1. The class, and the measurement it answers

`errors.py` gains a twenty-second subclass, one of the family `errors.md` §2 lists and never a surface name:
`class LearningDiverged(AgentsError)` — the name says what happened, so a caller catching `AgentsError` knows what it holds —
and D-45 adds its sibling `class CounterfactualUnbounded(AgentsError)` for the target's bound (`finiteness.md` §1). The ladder's
own probe of the declared `learning_rate` (ASM-7, D-19): at 0.1 the value function went non-finite on 2 of 3 seeds and at 0.03 on
1 of 3, so the tie-break's `min()` met an empty generator and the run died.

- **Refused by name, never clipped.** A clip, a skip, a reset or a finite substitute would change the declared learning rule
  (ASM-7, D-19) and hand the caller an answer its arithmetic did not produce (`surface.md` §1).
- **The finite path is untouched**: the declarations, both rules, both utilities, the initialisation order, the tie-break, the
  schedule and the composition are unchanged, so a finite batch takes the same steps and returns the same `td_error` digits
  (D-19, D-20, ASM-10, `rule.md` §3, §6).
- **`load` gains nothing**: a container with a non-finite parameter is read exactly as it always was, and the refusal arrives at
  the restored learner's first decision (`checkpoint.md` §1, `surface.md` §9, §10).

## 2. The two sites, and where each guard sits

**The update, first and best — `learner.py`'s `learn`.** For transition *k*, 0-based in the caller's order, `rule.md` §3's order
becomes: `forward`, `target` (§2), `delta = target − float(scored[action])`, **GUARD 1** — a non-finite `delta` refuses **before**
`|delta|` is accumulated and before the step — `total += |delta|`, `backend.apply(...)`, **GUARD 2** — a non-finite parameter
refuses **after** the step and **before** the counter moves — then the counter, the refresh and §3's last line, `position`, all
unchanged. Both name *k* and neither consumes a further transition: GUARD 1 reads `delta`; GUARD 2 reads `backend.parameters(state)`,
the whole `2·P` array both backends give (`backends.md` §2, `rule.md` §3). **D-45 puts the band on that same read** (`finiteness.md`
§2): a finite value above `declarations.PARAMETER_BAND` refuses after the step as `LearningDiverged`, and `learn`'s first read of the
array refuses a learner restored outside the band before the batch is read.

**The decision, defensively — `rule.py`'s `decide`, `decide_greedy` and `_tie_break`.** `decide` checks the masked values **first**,
before `_draws` and so before either arm, since a draw must never mask a non-finite value; `decide_greedy` checks its own because an
`off` policy reaches it without `decide` (`shapes.md` §4), and `_tie_break` its own because `learn` calls it for
`double-q-learning`'s bootstrap (`rule.md` §2). One raise serves `act`, every policy and that bootstrap (D-2, §6, §10).

## 3. The messages

`errors.md` §3's last two rows carry them verbatim, in that section's grammar — the site, the argument, the violated contract, the
offending value. GUARD 1 and GUARD 2 name `learn`, transition *k* — and, under `reveal-counterfactual`, the action index too, once per
step — and the `td_error` or the first non-finite parameter index, each as `%d`; D-45's three are `finiteness.md` §3's.

## 4. What it never does, and what the learner is left as

It clips, clamps, scales, skips and resets nothing: no transition leaves the batch, no finite value stands in for a non-finite one nor
for one the band refuses, and a non-finite `reward` is a number `records.md` §4 allows, so it passes validation and the step reports
what it produced (D-19, D-20). The steps before *k* stand, the position stays and the rate is never lowered (`errors.md` §4, `rule.md` §3).

## 5. The guardrail, and the cases that catch it

L4: two comparisons in front of statements that already exist — no arithmetic added, moved or reordered, and neither backend changed
(`backends.md` §2). AGT-16.1–16.3 pin the update's two refusals, AGT-16.4–16.6 the decision at its three call sites, AGT-16.7 the
finite path's digits (`test_divergence.py`, G5, G14) — AGT-18.6 the member's steps, FAM-23 the envelope's bounds and block.
