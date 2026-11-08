# evaluation — the learning rule at this module's edge

- **Layer:** L2 · **Module:** `evaluation` · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-09
- **Owner of this file:** the **rule** — the estimator axis at the eleven entry points: what a pool
  member declares, the **families** a heterogeneous window is grouped into and the fair-share
  eviction that keeps them, the pool **id** that certifies each version's rule, the `rules` every
  record carries, the rule `policy_from` reports and the disagreement it refuses, and the one
  population a report states (D-19, ASM-26, ASM-27, `e2e-surface.md` §2, §3.4)
- **Rev 3:** D-19 lands here — a member carries its rule, the id digests it, a window holds several
  families and evicts fair-share, and five records name the rule
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append

## 1. One catalogue, read through the granted arrow

`agents.learners()` publishes the learning-rule catalogue: `masked-q-learning` first, then
`double-q-learning`, each with the target it aims at, and its **first** member is the declared
default a learner spec naming none is built under (`rules.md` §2, §4, D-19; `e2e-surface.md` §2
`Learning rule`). This module **reads that catalogue** through the arrow `docs/L1/module-map.md` §2
grants it and never keeps a copy of the names: a name is accepted because the catalogue carries it,
which is what keeps a rule refused where it is declared from arriving here as a second list that
drifts (`rules.md` §4, D-19, D-13).

Nothing in this module **branches on the rule**. The catalogue's members consume one `hyper`
declaration and one state layout, so `agents.act`, `learn`, `save`, `load`, `param_count` and
`as_policy` answer with one shape whatever the rule, and the one capacity and the one masked draw
are the rules' own (`rules.md` §3, ASM-10, D-19). A rule therefore reaches this module as **data it
carries and records**, never as arithmetic it performs: `evaluation` measures, and the estimator is
a fact about a member (`module-map.md` §3, `league.md` §4).

## 2. A member declares its rule (`build_pool`, `offer`)

`records.md` §7 marks a version member's `rule` **required**: the catalogue member the version was
trained under. `build_pool` and `offer` read it as a **non-empty `str`** and refuse, by name:

- a member whose `rule` is absent, naming the key, because a version with no rule cannot say which
  population it belongs to (`records.md` §7, `surface.md` §5);
- a `rule` that is not a non-empty `str`, or that contains `"\n"`, `"\r"` or `"\x1f"` — the digest's
  own separator — naming the member and the value, because a field that can carry the separator
  would let two memberships digest alike (`ASM-27`, `surface.md` §5);
- a name the catalogue does not carry, naming the member and both the name and the catalogue,
  refused exactly as a learner spec's is and never mapped onto the declared default (`rules.md` §4,
  `e2e-surface.md` §2, D-19).

A declared member without a `path` is still admitted — `matrix` and `opponent` refuse it when it
must be a policy (`surface.md` §5, `surface.md` §8) — and the rule is checked beside `id` and
`lineage`, before any checkpoint is touched (`errors.md` §1, `pool.md` §2).

## 3. The families, the window and the id (`ASM-26`, `ASM-27`)

A window that holds several estimators is grouped into **families**: one lineage chain each, every
member of it trained under one rule, its label the start its first member names. The window lists a
family's members **contiguously, oldest to newest**, and the families in the order they entered it —
for a declared membership, the order of each family's start in the declaration; and a chain whose
members declare two rules is refused naming the member and both rules, because a family is one rule
(`ASM-26`, `league.md` §2, `records.md` §8).

- **`offer` extends one family.** The offered version's `lineage` must be the id of a member that is
  its own family's **newest** — which advances that family — or a label no member carries, which
  opens a new family; a lineage naming a member that is not its family's newest is refused naming
  both, because the chain would fork, and a version whose `rule` differs from the rule of the family
  it extends is refused naming the member and both values (`ASM-26`, `surface.md` §7). "No member
  carries" is read as **no member's `id`**: a family's label is the start its first member names, and
  a second arm's first snapshot names the same rung start its sibling's does, so reading the label as
  something a member carries would refuse the second family's opening version — which is the finding
  V-F4 `offer` exists to clear (`ASM-26`, D-19, `docs/L1/league.md` §2).
- **Eviction is fair-share.** When the window already holds `m` versions the member that leaves is
  the **oldest member of the family that currently holds the most**, ties broken by which family's
  oldest member is the older. So no family is emptied while another holds two or more, and with F
  families resident each keeps a member while F ≤ m (`ASM-26`, `league.md` §2).
- **`build_pool` windows by the same rule**, rather than by "the last `m` of the concatenation", and
  refuses a declaration holding **more than `m` families** by name, because windowing could not keep
  one member of each (`ASM-26`, `surface.md` §5).
- **A window holding one family behaves exactly as it did before the catalogue**: the last `m` of
  its chain survive, which is what every pool in the shipped tree holds (`league.md` §2, ASM-16).
- **The id certifies the rule.** The digest's payload is one line per member in the pool's order: a
  baseline contributes its `id` alone, a version its `id`, then `"\x1f"`, then its `rule`; the lines
  are joined by `"\n"` with no trailing separator, and the id is `"pool-" +
  sha256(payload)[:16]`. `m`, `frozen` and every other member field stay outside it, so a corrected
  seed or step does not rename the pool — and **a baselines-only pool keeps exactly the id it had**,
  which is why R1's pool, the one id a shipped artefact records, survives this change (`ASM-27`,
  `records.md` §8, `surface.md` §5).

## 4. The records that name the rule

Five records carry the fact, and each carries it in its own shape (`rules.md` §7, D-19):

| Record | What it carries | Where |
|---|---|---|
| a version member | `rule` — the catalogue member it was trained under | `records.md` §7, `pool.md` §2 |
| a pool record | `rules` — the **distinct** rules its version members declare, in the window's order; the **empty tuple** for R1's pool | `records.md` §8, `surface.md` §6 |
| a cell record | `rules` — each member's rule **by id**, `None` for a baseline and for an opaque policy that carries none | `records.md` §9, `surface.md` §9 |
| a matrix record | `rules` (each member's rule by id) and `population` (the distinct rules those members declared, **sorted**); each `member_records` entry carries its rule | `records.md` §10, `surface.md` §10 |
| the report's pool family, and its header | the rules the measured **population** held: the pool's version members' rules plus the rung's variants', exactly the population the matrix names | `e2e-surface.md` §3.4, `surface.md` §13 |

**Nothing new is required of the report.** It gains no family and no new required content item: the
seven families of `protocol.md` §1 and the nine header items are unchanged, and the population rides
inside keys that already exist — the pool family, which is `records.md` §8's record, and the header,
which the run record already fills (`protocol.md` §1, `records.md` §13, `surface.md` §13). A new
*required* item would refuse records other batteries hand-build, which is over-refusal
(`errors.md` §5). A report handed a pool block that declares no rule still states the population its
matrix names: it completes that one key on its own copy, and never edits the record it is handed
(`surface.md` §13, `report.md` §2).

## 5. `policy_from`, and the disagreement it refuses

`policy_from(path)` returns a policy that carries `learning_rule`, the catalogue member its learner
was trained under, so playback names the estimator it plays (`e2e-surface.md` §2, `rules.md` §6).
The fact is the **policy's own**: it is read from the `learning_rule` attribute of the policy
`agents.as_policy` built, which is the rule the file records — this module reads no further fact from
a checkpoint's container, since a checkpoint is `agents`' own (`rules.md` §6, ASM-20,
`scheduler.md` §5.1). A **version-1** container legitimately reads as `masked-q-learning`, the only
rule its writer could have used, and nothing else is inferred (`rules.md` §6, D-19).

When a member **record** declares a `rule`, it is compared with the rule its policy carries and a
disagreement is refused naming the member and both values: `RuleMismatch`, in this module's grammar,
raised before a cell is played and after the member is loaded — the one refusal of this change that
cannot precede the load, because the file is the only witness of what it records (`surface.md` §12,
`records.md` §7, ASM-20, `errors.md` §4).

## 6. What this module still does not decide

- **It does not choose the membership.** Which estimators a window holds, how many, and which
  version extends which family are the declaration's and `training`'s (`module-map.md` §3, ASM-16,
  D-19); this module reads a declaration, refuses what it cannot order and records what it holds.
- **It does not train, tune or re-weight a rule.** A rule swap moves no budget: both members consume
  one `hyper` declaration and one layout (`rules.md` §2, §3, ASM-7).
- **It does not regenerate a measured artefact.** `tables/league-full.json` and the evidence bundle
  were measured under the old single-rule arrangement, and re-measuring them is D-19's own
  re-baseline and the user's decision, not this module's (`league.md` §5, D-19). `tables.py`'s
  producer builds a **baselines-only** pool and an **untrained** learner, so it declares no rule of
  its own and needs no change to keep running (`tables.md` §2, §5).
