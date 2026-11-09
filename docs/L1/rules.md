# PyPoker-Demo — L1 learning rules: the estimator catalogue

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-09
- **Covers:** D-19's estimator axis — the catalogue, each rule's target, the one contract they share, what a checkpoint records, how a configuration declares several, and the fairness rule that replaces ASM-7's single-rule clause
- **Ceiling:** 70 lines. At the ceiling, split by owner — never append

## 1. Why the rule is a parameter

The learning rule was one module constant for the whole ladder (ASM-7). The measured reason it stops being one is `strata/records/r2-plateau-diagnosis.md`: max-operator Q-learning on a ±20-chip terminal reward that must resolve an action-value difference of about 0.06–0.7 chips takes whichever of three noisy estimates drew positive noise, so it converges on raise-almost-always and loses to `always-call`. D-18 put models trained under other estimators in the pool as opponents; D-19 makes them **training targets** too. A catalogue a learner spec selects from is the smallest change that admits a second estimator without touching the learner family, the backends or the state layout (`module-map.md` §1, D-19).

## 2. The catalogue

`agents.learners()["learning_rules"]` publishes exactly two, in this order, each with its name and the target it aims at. Its first member is the declared default of §4. `hyper` is not per rule: both rules consume the same six declarations, so a rule swap is one axis and no budget moves with it (D-19, ASM-7).

| Rule | The target it aims at | What it reads |
|---|---|---|
| `masked-q-learning` | `r + discount × max(Q_target(s', i) for i in next_legal)`, and `r` alone at a terminal transition | the target copy's three values, and the mask (ASM-25, D-19) |
| `double-q-learning` | `r + discount × Q_target(s', argmax(Q_online(s', i) for i in next_legal))`, and `r` alone at a terminal transition | the online parameters choose the index, the target copy values it |

Double Q-learning is the direct remedy for the diagnosis's measured bias: it **decouples action selection from action evaluation**, so the index the bootstrap is read at is the one the online parameters would take and the value at that index is a second estimate's. That is the decoupling the function-approximation form of the algorithm makes, and it needs no parameter the masked rule does not already hold — which is why the pair stays capacity-matched (D-19, `strata/records/r2-plateau-diagnosis.md`, ASM-10).

## 3. The one contract every rule answers

Whatever its rule, a learner is one object built by `agents.build_learner`, and it answers the same five calls with the same shapes: `act` returns one index of the legal mask; `learn` returns `td_error` and `transitions`; `save` and `load` are loss-free at the decision boundary; `param_count` returns one integer; `as_policy` returns a policy. **The two rules are one capacity**: a rule changes the arithmetic of a target and nothing of the state layout — the online parameters plus their target copy — so `param_count`, the checkpoint's `2·P + M` array and the ±2% budget match of ASM-10 are identical under either. `act` is rule-free: the exploration schedule, the keyed draw, the tie-break and the masked maximum run over three values the rule never changes. `training` and `evaluation` therefore never branch on the rule (D-19, `e2e-surface.md` §2, ASM-10). A rule owns the **bootstrap** and nothing else: what a terminal transition is worth is the learner's utility's business, `learn`'s terminal target stays `target = reward`, and the two axes compose without either reading the other (D-20, `utilities.md` §3).

## 4. The declared default, and where a rule is named

A learner spec that names no `learning_rule` is built under the catalogue's **first** member, `masked-q-learning`; that default is declared here and in `records.md` §3, and is never inferred from the caller. One rule is named in four places that must agree: a variant entry's `learning_rule` (`records.md` §2), the learner spec (`records.md` §3), the checkpoint's `learning_rule` field (§6), and a pool member's `rule` (`records.md` §7). A name outside the catalogue is refused where it is declared, by name (D-19, ASM-7).

## 5. Why two, and the third that was declined

A third rule — Monte-Carlo or n-step returns, D-18's other named candidate — was judged and **declined**. It is cheap and it is not safe: a return is defined over an episode, and `learn`'s transition record carries one decision and its successor with nothing that delimits an episode (`records.md` §4). Accepting any batch would make such a rule learn nothing from a one-transition batch, an input the surface admits; refusing a batch without a terminal transition would make the **admissible inputs** differ per rule, which is an interface difference and exactly what D-19 forbids the catalogue's members from having. Giving the transition record an episode field is a surface change this decision does not make. Two rules answer D-19's question, and no fourth is added (D-19, ASM-25).

## 6. What a checkpoint records, and what a restore checks

A checkpoint records the rule its learner was trained under, in a required `learning_rule` field of a **format version 3** container — the version `utilities.md` §6 fixes, where the same container also carries the utility — and `agents.load` restores the learner under that rule. The 18 checkpoints the repository ships were written before the catalogue existed, so a **version 1** container — which carries no `learning_rule` — is read as `masked-q-learning`, the only rule its writer could have used, and it loads unchanged: the shipped set is not regenerated (D-19, D-20, ASM-5, `protocol.md` §5). A version-2 container is read as the rule it records and as `net-chips`, because it predates the utility (`utilities.md` §6). A `load` spec that carries a `learning_rule` is compared with the file's, and a disagreement is refused naming both as a spec's `seed` is; a rule the catalogue does not carry is refused naming it. `evaluation.policy_from` needs nothing new — playback is rule-free — and the rule it reports is the one the file records (ASM-20).

## 7. Several rules in one configuration, and what the records say

A configuration may declare its variants under **different** rules, and every variant it declares is trained: its own curves, snapshots, final checkpoint, timings, record entry and pool membership. A pair whose two arms declare two rules differs on the `rule` axis; one whose arms declare one rule each, the same one, is what the ladder declares today. The records that name a rule are the run record, per variant and as the run's `rules` set (`records.md` §12); a pool record, per version member and as its `rules` set (`records.md` §7, §8); a cell record, per member (`records.md` §9); and a matrix record, per member and as its `population` (`records.md` §10). A policy returned by `agents.as_policy` or `evaluation.policy_from` carries `learning_rule`, so a table names the population it measured even when a variant was built in process and no record of it exists yet (`e2e-surface.md` §2, D-19).

## 8. The fairness rule that replaces ASM-7's single-rule clause

What a rung holds constant is the **set** of rules its variants declare and their declarations, not a single rule: two rungs are compared under one set, and two arms of a pair still train against one frozen pool on one game and one seed set (D-19, D-3, D-16, `ladder.md` §4, ASM-7). `training.fairness` reports that set, and `learning_rule` leaves the settings a pair must share — it is an axis a pair may differ on, beside `backend`, `encoding`, `architecture`, `connectivity` and `residual` (`ladder.md` §4, D-3).
