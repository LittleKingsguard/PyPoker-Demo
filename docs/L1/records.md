# PyPoker-Demo — L1 record shapes

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-05
- **Covers:** the mapping shapes the entry points of `e2e-surface.md` §3 exchange — the league objects of D-16 included
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append

## 1. Why these are L1's

Every entry point above the engine exchanges a plain mapping, and a shape declared only in prose is a
contract nobody can build against: L2, the batteries and a notebook would each invent their own (D-13).
The shapes below are therefore part of the surface. A key marked **required** is asserted by the e2e
battery (`battery.md` §3); any other key is the owning module's own and a caller must not depend on it.

## 2. Variant entry — one entry of a rung configuration's `variants`

| Key | Content |
|---|---|
| `name`, `backend`, `encoding` | **required** — the variant name from `ladder.md` §2; `numpy` for R1 and `torch` from R2 on (D-7); `flat-numeric` for R1/R2 and `card-tokens` for R3–R6 (D-3) |
| `architecture` | **required** — `kind`, plus `width`, `depth`, `sparsity`, `residual` as the kind uses them (D-3) |
| `learning_rule`, `hyper`, `param_budget`, `samples`, `seeds`, `device`, `snapshot_every`, `table` | the rule and its hyperparameters (ASM-7); the budgets, the snapshot interval and the table budget of `ladder.md` §3, §6 (ASM-8, ASM-18) |

## 3. Learner spec — `agents.build_learner`

`backend` and `architecture` (**required**, as in §2), `seed` (**required** — the seed of the learner's
own generator, `protocol.md` §4), and `sizes`, an optional redundant shorthand for width and depth;
`architecture` is authoritative when both are present.

## 4. Transition record — `agents.learn`

`learn` takes a sequence of these; one record is one decision and its successor. **Required**:
`observation`, `next_observation` (from `features.encode`), `action`, `reward` (zero except at a terminal
decision, ASM-12), `terminal`, and `legal` / `next_legal` (the legal index sets of the decision and its
successor, as `features.legal_indices` returns them, so a masked update re-derives nothing).

## 5. Episode record — `engine.play_hand`

**Required**: `seed`; `decisions`, the ordered decisions, each carrying `seat`, `readout`, `legal`,
`action` and `reward`; and `payoffs`, net chips per seat summing to zero (`protocol.md` §2). Rewards are
zero except at most one non-zero reward per seat, at that seat's terminal decision — the reward is the
hand's outcome, not a shaped term (ASM-12).

## 6. Decision record — `agents.act`

`act` returns the chosen index, or a mapping carrying it under a key containing `action`, `index` or
`choice`. Anything else in that mapping is the learner's own record of the decision and is not surface.

## 7. Version record — a pool member of a checkpoint

| Key | Content |
|---|---|
| `id`, `path` | **required** — the member's id, stable across tables so two reports can name the same version (D-16); the checkpoint path `evaluation.policy_from` loads |
| `rung`, `variant`, `seed`, `step`, `samples` | **required** — what produced it: the rung, the variant, the seed, the snapshot's step and the hands trained (ASM-18) |
| `lineage` | **required** — the version this one descends from, or its rung's own start for the first; the pool's window is ordered by it (D-16, ASM-18) |

## 8. Pool declaration and pool record — `build_pool`, `pool_members`, `offer`

A declaration is `members` (**required** — the versions, by id and lineage), `m` (**required** — the
bound) and `frozen` (**required** — whether the pool may not change while used). A pool record returns
`id` and `m` (**required**), `frozen` (**required** — whether the pool was frozen when it was used, which
is how a pair's parity is read), and `members` (**required**) in lineage order, each a §7 record, with the
three baselines present and marked pinned (D-16, ASM-16). The id changes when and only when the
membership does, so a run record and a table can be compared by the id alone (D-16).

## 9. Cell record — `evaluation.match`

| Key | Content |
|---|---|
| `members` | **required** — the two members of the pair, by id |
| `hands` | **required** — the hands played, one seat alternation across them |
| `directions` | **required** — one entry per seat, each with `wins`, `ties`, `losses`, `mean_chip_delta` and `seat_split`; the two directions are the same hands seen from each seat (D-16, ASM-14) |
| `params` | **required** — each member's parameter count: `agents.param_count` for a version, the zero `agents.baselines()` declares for a baseline (ASM-10) |
| `seed` | **required** — the seed the cell was played at |

`seat_split` names the hands each seat held the button, and each row's numbers are for its own member's
side of those hands (`protocol.md` §2).

## 10. Matrix record — `evaluation.matrix`

`members` (**required** — the ordered membership: the frozen pool plus the rung's variants), `cells`
(**required** — exactly K(K−1)/2 §9 records, one per unordered pair), `hands_per_cell` (**required** —
one value for every cell, the baseline cells included), `table_seed` (**required**), and `table`
(**required** — `live` or `full`, which the report's header repeats). A matrix with a cell of a different
hand count, a member outside the pool, or a missing baseline is refused and is not a table (`league.md`
§4, D-16).

## 11. Rating record — `evaluation.rating`

| Key | Content |
|---|---|
| `values` | **required** — one entry per matrix member: the fitted value, its 95% interval and the hands behind it |
| `method`, `anchor` | **required** — `Bradley-Terry` (`league.md` §5), and the anchor: the three baselines' mean fixed at zero (ASM-17) |
| `bound_applied`, `bootstrap_seed`, `converged` | **required** — whether a member with no finite maximum-likelihood value was bounded, and that its interval says so (ASM-17); the interval's seed, recorded so the fit can be re-run; the fit's convergence (D-6) |

## 12. Run record — `training.run`

`rung` (**required** — the rung name, or an unregistered configuration's label), `curves` (**required** —
per variant per seed: the sample axis, a learning signal, the spread across seeds), `pool` (**required** —
the id and membership trained against, one id for both arms of a pair), `checkpoints` (**required** — the
retained snapshots and the final model per variant per seed), `seeds`, `budget`, `device` (**required** —
what the run used), `params` (**required** — the declared parameter budget; a cell records the measured
count), `table` (**required** — the declared table budget, `live` or `full`), and `timings` (**required** —
hands and seconds per hand, in `harness.timings`'s facts (D-7, ASM-15)). The seed set is the one the run
used, and the record is the record of what happened (D-6, D-16).

## 13. The assembled record handed to `evaluation.report`

`training` produces a run record and measures no cell; `evaluation` plays cells and edits no curve
(`module-map.md` §3). `report` requires the seven families of `protocol.md` §1; an explicit `n/a` value
satisfies one, and an absent family is refused by name (D-6, D-16).

## 14. Harness inputs

The harness's consumers are test batteries (brief §5), so its inputs are declared only as far as a
battery needs. `harness.drive` **requires** `id`, `steps` and `expect` and records each step's outcome
and a verdict; `harness.fixtures` yields a scratch root, the pinned seed, the pinned device (CPU,
`protocol.md` §6) and the expectation kinds `expect` accepts; and `harness.factory` builds a declared
object kind — an encoder, a learner, a baseline, a hand, a rung configuration or a pool — through its
owning entry point, never in place of it. `harness.seam` takes any label (its contract is the policy
protocol, not the label) and `harness.expect` takes a kind `fixtures` listed; L1 fixes only that a seam
satisfies the policy protocol, re-implements no subsystem, and yields a verdict (D-13).
