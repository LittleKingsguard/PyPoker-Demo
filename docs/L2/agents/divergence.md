# agents — the divergence refusal

- **Layer:** L2 · **Module:** `agents` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-10
- **Owner of this file:** the one refusal of this surface whose fault is the learner's own accumulated state, never
  the caller's argument: the measurement it answers (§1), its sites (§2), their messages (§3), what it never does (§4)
- **Read with:** `surface.md` §1, §6, §7, §9, §10; `learner.md` §1, §4; `docs/L3/agents/errors.md` §2–§3;
  `docs/L3/agents/rule.md` §3, §5, §8
- **Ceiling:** 60 lines. At the ceiling, split by owner — never append

Split out of `surface.md`, which keeps one-line pointers, when a measured defect gave this surface a refusal that is
not an argument contract: every refusal §4–§12 refuses a value the caller passed; this one refuses the state (D-12).

## 1. The measurement it answers

`strata/records/lr-probe.md`: at `learning_rate` 0.1 the value function went non-finite on 2 of 3 seeds, and at 0.03
on 1 of 3; training died with `ValueError: min() iterable argument is empty` inside the tie-break, because a squared TD
error on a ±20-chip terminal reward, stepped at a large rate, drives the delta or the parameters past finite range.

- **Refused by name, never clipped.** Clipping the step would be a change to the declared learning rule (ASM-7, D-19)
  and a silent substitution for the value the caller's arithmetic produced, which §1 of `surface.md` forbids.
- **The declared arithmetic is not the fix.** The six declarations, the two rules and the two utilities are untouched:
  same action, same step, bit for bit, and the shipped `learning_rate` stands as declared (ASM-7, D-20).
- **Reachable from this surface.** Both sites are reached by a caller holding only the ten entry points: a
  transition whose `reward` is not finite, and a container carrying a non-finite parameter (`records.md` §4, `surface.md` §9).

## 2. The two sites

| Site | What it refuses | The message names |
|---|---|---|
| `learn` (§7) | a transition whose td_error is not finite, and one whose step left any parameter not finite | the entry point, the transition's 0-based index, and the td_error or the first parameter index (§3) |
| the decision (§6, §10) | a value in the **masked set** that is not finite | the site, the index inside the mask, and the value (§3) |

- **The update first, and the only site some runs reach.** `learn` refuses a non-finite `td = target − q[a]` **before**
  its step is applied and checks every parameter — online values and target copy — after it; and `masked-q-learning`'s
  bootstrap is a `max`, never the tie-break, so a learn-only loop would otherwise go non-finite in silence. Neither
  refusal consumes a further transition: the position does not advance and no statistics are returned (§7, ASM-7).
- **The decision defensively.** `act` and every policy `as_policy` returns decide through the same rule, so a
  non-finite masked value is refused there too, by name instead of reaching the tie-break's `min()` on an empty
  generator. It cannot fire on a learner the update guard has passed; it exists because a checkpoint written before
  this refusal, or read from a doctored file, may carry one. `load` gains nothing — it reads such a parameter as it
  always did, and the refusal arrives at the restored member's first decision (§6, §9, §10, `learner.md` §4, ASM-5).

## 3. The messages

`docs/L3/agents/errors.md` §3 carries these; each follows the module's grammar and is this module's own class (§1–§2):

| Where | Message |
|---|---|
| `learn`, a non-finite td_error | `learn(transitions): transition index 41 computed a non-finite td_error and the learner has diverged, got nan` |
| `learn`, a non-finite parameter | `learn(transitions): transition index 41 drove parameter index 118 out of finite range and the learner has diverged, got nan` |
| the decision: `act`, every policy, and `learn`'s bootstrap | `decide(values): the masked value at index 2 is not finite and the learner has diverged, got nan`, or `_tie_break(values): …` at the bootstrap index `double-q-learning` reads |

The message names the **site that raised** — `decide` or `_tie_break`, one raise serving `act`, every policy and
`learn`'s bootstrap — while a policy's own refusals are still `policy(readout)` (`surface.md` §10).

## 4. What it never does, and what a caller is left with

It clips, clamps, skips and resets nothing: no finite value stands in for a non-finite one, no transition leaves the
batch, and the learner stays where it was (D-19, D-20). A non-finite `reward` is a number `records.md` §4 allows, so the
batch is not refused; the caller discards the learner or loads an earlier checkpoint, and the rate is never lowered (D-19).
