# PyPoker-Demo — L1 record shapes

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 6 · **Date:** 2026-11-09
- **Covers:** the mapping shapes the entry points of `e2e-surface.md` §3 exchange — the league objects of D-16, the learning rule of D-19, the utility of D-20 and the folding baselines of D-21 included
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append

## 1. Why these are L1's

Every entry point above the engine exchanges a plain mapping, and a shape declared only in prose is a contract nobody can build against: L2, the batteries and a notebook would each invent their own (D-13). The shapes below are therefore part of the surface. A key marked **required** is asserted by the e2e battery (`battery.md` §3); any other key is the owning module's own and a caller must not depend on it.

## 2. Variant entry — one entry of a rung configuration's `variants`

| Key | Content |
|---|---|
| `name`, `backend`, `encoding` | **required** — the variant name from `ladder.md` §2; `numpy` for R1 and `torch` from R2 on (D-7); `flat-numeric` for R1/R2 and `card-tokens` for R3–R6 (D-3) |
| `architecture` | **required** — `kind`, plus `width`, `depth`, `sparsity`, `residual` as the kind uses them (D-3) |
| `learning_rule`, `hyper`, `param_budget`, `samples`, `seeds`, `device`, `snapshot_every`, `table` | the rule this variant is **trained** under — one of the catalogue's members, absent meaning its first, and two variants of one configuration may name two (`rules.md` §2, §4, D-19) — and its hyperparameters (ASM-7); the budgets, the snapshot interval and the table budget of `ladder.md` §3, §6 (ASM-8, ASM-18) |
| `utility` | the utility this variant is **trained** under — one of the catalogue's members, absent meaning its first, `net-chips`, and two variants of one configuration may name two (`utilities.md` §2, §5, D-20) |

## 3. Learner spec — `agents.build_learner`

`backend` and `architecture` (**required**, as in §2), `seed` (**required** — the seed of the learner's own generator, `protocol.md` §4), `learning_rule` (the catalogue member the learner learns under — **optional**, and a spec naming none is built under the catalogue's **first** member, `masked-q-learning`, a default declared here and in `rules.md` §4 and never inferred from the caller), `utility` (the catalogue member whose reward the learner is trained on — **optional**, and a spec naming none is built under the catalogue's **first** member, `net-chips`, a default declared here and in `utilities.md` §5 and never inferred from the caller, D-20), and `sizes`, an optional redundant shorthand for width and depth; `architecture` is authoritative when both are present.

## 4. Transition record — `agents.learn`

`learn` takes a sequence of these; one record is one decision and its successor. **Required**:
`observation`, `next_observation` (from `features.encode`), `action`, `reward` (zero except at a terminal
decision, where it is the reward of the learner's utility — the net chip delta under `net-chips` and the
shortfall delta under `stack-shortfall`, `utilities.md` §2, §4, ASM-12), `terminal`, and `legal` / `next_legal` (the legal index sets of the decision and its
successor, as `features.legal_indices` returns them, so a masked update re-derives nothing).

## 5. Episode record — `engine.play_hand`

**Required**: `seed`; `decisions`, the ordered decisions, each carrying `seat`, `readout`, `legal`, `action` and `reward`; and `payoffs`, net chips per seat summing to zero (`protocol.md` §2). Rewards are zero except at most one non-zero reward per seat, at that seat's terminal decision — the engine places the hand's **net chip delta** there and no shaped term, whatever utility the learner that consumes it is trained on: the utility is applied to that number when the transition record is built (`utilities.md` §4, ASM-12, D-20).

## 6. Decision record — `agents.act`

`act` returns the chosen index, or a mapping carrying it under a key containing `action`, `index` or
`choice`. Anything else in that mapping is the learner's own record of the decision and is not surface.

## 7. Version record — a pool member of a checkpoint

| Key | Content |
|---|---|
| `id`, `path` | **required** — the member's id, stable across tables so two reports can name the same version (D-16); the checkpoint path `evaluation.policy_from` loads |
| `rung`, `variant`, `seed`, `step`, `samples` | **required** — what produced it: the rung, the variant, the seed, the snapshot's step and the hands trained (ASM-18) |
| `lineage` | **required** — the version this one descends from, or its rung's own start for the first; the pool's window is ordered by it (D-16, ASM-18) |
| `rule` | **required** — the catalogue member the version was trained under, so a table can name the population it measured and the pool id can certify it (`rules.md` §6, ASM-27); it is the name the member's own container records, and a member whose rule disagrees with its file is refused **when the member is played**, naming the member and both values, as is a name the catalogue does not carry (D-19, ASM-20) |
| `utility` | **required** — the catalogue member whose reward the version was trained on, so a table can name it and the pool id can certify it (`utilities.md` §6, §7, ASM-27); it is the name the member's own container records, and a member whose utility disagrees with its file is refused **when the member is played**, naming the member and both values, as is a name the catalogue does not carry or a record that names none — the declared default speaks for a variant entry and a learner spec, never for a pool member (`utilities.md` §5, D-20, ASM-20) |

## 8. Pool declaration and pool record — `build_pool`, `pool_members`, `offer`

A declaration is `members` (**required** — the versions, by id, lineage, rule and utility), `m` (**required** — the bound), `frozen` (**required** — whether the pool may not change while used) and `baselines` (**optional** — the catalogue names of the baselines a configuration admits beyond the three anchor ones, which are members whether it names them or not, so D-21's folders join by declaration and never silently; a name outside the catalogue is refused by name, ASM-32, D-21). A pool record returns `id` and `m` (**required**), `frozen` (**required** — whether the pool was frozen when it was used, which is how a pair's parity is read), `members` (**required**) in the pool's order — the pinned baselines, the three of D-6 first and then the declared folders in the catalogue's order, then each family's chain oldest to newest, the families in the order they entered the window (ASM-26) — each a §7 record, `rules` (**required** — the distinct rules its version members declare, in that order, which is the population a table over it measured) and `utilities` (**required** — the distinct utilities those members declare, in that order, D-20) (D-16, D-19, ASM-16, ASM-26, D-21). The id changes when and only when the membership does — a version's rule and its utility included — so a run record and a table can be compared by the id alone, and a pool whose declaration names no folder keeps the id it had (D-16, ASM-27).

## 9. Cell record — `evaluation.match`

| Key | Content |
|---|---|
| `members` | **required** — the two members of the pair, by id |
| `hands` | **required** — the hands played, one seat alternation across them |
| `directions` | **required** — one entry per seat, each with `wins`, `ties`, `losses`, `mean_chip_delta` and `seat_split`; the two directions are the same hands seen from each seat (D-16, ASM-14) |
| `params` | **required** — each member's parameter count: `agents.param_count` for a version, the zero `agents.baselines()` declares for a baseline (ASM-10) |
| `rules` | **required** — each member's rule, by id: the catalogue name its policy carries, and `None` for a baseline or an opaque policy that carries none, so a cell says which estimators met (D-19, `e2e-surface.md` §2) |
| `utilities` | **required** — each member's utility, by id, on the same terms: the catalogue name its policy carries, and `None` for a baseline or an opaque policy that carries none, so a cell says which objectives met (D-20, `utilities.md` §9) |
| `seed` | **required** — the cell's own seed: the seed its hands were dealt from, derived from the matrix's table seed and the pair's membership positions. It is **not** a key that replays the cell on its own (`league.md` §3.1) |

`seat_split` names the hands each seat held the button, and each row's numbers are for its own member's
side of those hands (`protocol.md` §2).

## 10. Matrix record — `evaluation.matrix`

`members` (**required** — the ordered membership: the frozen pool plus the rung's variants), `cells` (**required** — exactly K(K−1)/2 §9 records, one per unordered pair), `rules` (**required** — each member's rule by id, as a §9 `rules` entry), `population` (**required** — the distinct rules those members declared, sorted, the population this table measured, D-19), `utilities` (**required** — each member's utility by id, as a §9 `utilities` entry), `utility_population` (**required** — the distinct utilities those members declared, sorted, the objectives this table measured, D-20), `hands_per_cell` (**required** — one value for every cell, the baseline cells included), `table_seed` (**required**), and `table` (**required** — `live` or `full`, which the report's header repeats). A matrix with a cell of a different hand count, a member outside the pool, or a missing baseline is refused and is not a table (`league.md` §4, D-16).

## 11. Rating record — `evaluation.rating`

| Key | Content |
|---|---|
| `values` | **required** — one entry per matrix member: the fitted value, its 95% interval and the hands behind it |
| `method`, `anchor` | **required** — `Bradley-Terry` (`league.md` §5), and the anchor: the **three anchor baselines of D-6**'s mean fixed at zero — the catalogue's `anchor` flag, never a folding baseline D-21 adds (ASM-17, ASM-32, D-21) |
| `bound_applied`, `bootstrap_seed`, `converged` | **required** — whether a member with no finite maximum-likelihood value was bounded, and that its interval says so (ASM-17); the interval's seed, recorded so the fit can be re-run; the fit's convergence (D-6) |

## 12. Run record — `training.run`

`rung` (**required** — the rung name, or an unregistered configuration's label), `curves` (**required** — per variant per
seed: the sample axis, a learning signal, and the variant's spread across seeds — one array per point, repeated in each
of its seeds' entries), `pool` (**required** — the id and membership trained against, one id for both arms of a pair, and the `rules` and `utilities` its members declare), `variants` (**required** — one entry per declared variant, each naming its `learning_rule` and its `utility`, so a run says which estimator and which objective produced which curve, D-19, D-20), `rules` (**required** — the set of rules the run declared and trained), `utilities` (**required** — the set of utilities the run declared and trained, D-20), `checkpoints` (**required** — the retained snapshots and the final model per variant per seed), `seeds`, `budget`,
`device` (**required** — what the run used), `params` (**required** — the declared parameter budget; a cell records the
measured count), `table` (**required** — the declared table budget, `live` or `full`), and `timings` (**required** — hands
and seconds per hand, in `harness.timings`'s facts (D-7, ASM-15)). The seed set is the one the run used, and the record
is the record of what happened (D-6, D-16, D-19).

## 13. The assembled record handed to `evaluation.report`

`training` produces a run record and measures no cell; `evaluation` plays cells and edits no curve
(`module-map.md` §3). `report` requires the seven families of `protocol.md` §1; an explicit `n/a` value
satisfies one, and an absent family is refused by name (D-6, D-16). The report's pool family carries the
**population its table measured** — the pool's own `rules` and `utilities` completed to the matrix's
`population` and `utility_population`, so a report states which estimators and which objectives its table
fitted over (D-19, D-20, `utilities.md` §7, §9).

## 14. Harness inputs

The harness's consumers are test batteries (brief §5), so its inputs are declared only as far as a
battery needs. `harness.drive` **requires** `id`, `steps` and `expect` and records each step's outcome
and a verdict; `harness.fixtures` yields a scratch root, the pinned seed, the pinned device (CPU,
`protocol.md` §6) and the expectation kinds `expect` accepts; and `harness.factory` builds a declared
object kind — an encoder, a learner, a baseline, a hand, a rung configuration or a pool — through its
owning entry point, never in place of it. `harness.seam` takes any label (its contract is the policy
protocol, not the label) and `harness.expect` takes a kind `fixtures` listed; L1 fixes only that a seam
satisfies the policy protocol, re-implements no subsystem, and yields a verdict (D-13).
