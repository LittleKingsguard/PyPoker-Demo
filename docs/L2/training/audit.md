# training — the audit: every configuration key against the one loop

- **Layer:** L2 · **Module:** `training` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-11
- **Owner of this file:** the per-key audit of `ladder.md` §3's schema — the four fates a declared key can have, key by
  key, and the four annotations that are deliberately not refusals — split out of `declarations.md` §1 at that file's
  ceiling, which keeps the numbering its readers cite (§1) (D-3, ASM-7, D-19, D-20, D-21, D-29)
- **Reads:** `ladder.md` §2–§4, `records.md` §2, `surface.md` §4–§5, `declarations.md` §2–§5, `loop.md` §3,
  `agents/surface.md` §3–§4, `shapes.md` §2–§3
- **Ceiling:** 45 lines. At the ceiling, split by owner — never append

## 1. The audit

A configuration is data for one loop (`loop.md` §3), so every key it may declare has exactly one of four fates: the run
**reads** it, the run **records** it, another entry point of this module **quotes** it, or the run would **discard** it.
The fourth fate is the defect this file exists to close: a key a run neither uses nor refuses is a caller's intent
dropped in silence, and a sweep written that way measures one model N times (D-3, ASM-7). Every row below is a statement
about `run`, and the discarded ones are named as refused in `declarations.md` §2.

| The key | What a run does with it |
|---|---|
| `name` | read: the record's `rung` (`surface.md` §4) |
| `variants`, `pool` | read: the pool's `members`, `m` and `frozen` go to `evaluation.build_pool`, its optional `baselines` key is forwarded as it stands — a name the catalogue lacks is that entry point's `UnknownBaseline`, naming it, never this module's substitution — and its `id` and `lineage` are carried in the record (`loop.md` §3 step 2, `records.md` §8, ASM-32, D-21) |
| `seeds`, `samples`, `device`, `table` | read, at the configuration and then at its first variant entry, and recorded (`surface.md` §4) |
| `game` | read, at the configuration and then at its first variant entry, and **recorded**: the shape the run trains and is evaluated on, one of the declared shapes, absence meaning the catalogue's first — and a name outside it is **refused** naming it and the declared names (`declarations.md` §2, §5, `shapes.md` §2–§3, D-29) |
| variant `name`, `backend`, `encoding`, `architecture` | read: `kind`, `width`, `depth` and `sparsity` build the learner, and `residual` is forwarded to `agents.build_learner`, whose kind decides (`surface.md` §4.2, `agents/surface.md` §3) |
| variant `param_budget`, `samples`, `seeds`, `device`, `table` | read: the declared budget the `params` block reports, and the defaults `surface.md` §4 names |
| `axis`, `primary` | quoted by `fairness` — the axis a pair is reported on, and the variant the next rung inherits — and read by `run` nowhere (`surface.md` §5, `ladder.md` §2) |
| `carried_from` | read by `registry.rung` when it builds a rung's window; for a configuration in no registry nothing reads it, because the window a run freezes is `pool.members` (`loop.md` §3 step 2) |
| variant `learning_rule`, variant `utility` | read: forwarded into `agents.build_learner`'s spec, so a variant trains under the rule it names and on the reward of the utility it names — each a member of its catalogue (`rules.md` §2, `utilities.md` §2, D-19, D-20) — and a name either catalogue does not carry is **refused** (`declarations.md` §2) |
| variant `hyper` | **refused** when it declares another value: one hyper declaration serves every rule, so a run holds ASM-7's six declarations (`declarations.md` §2, `rules.md` §2) |
| `snapshot_every`, at either level | **refused** when it declares another interval: ASM-18 fixes ten, so the interval is the declared budget ÷ 10 (`declarations.md` §2) |
| `param_budget` at the configuration | read as the declaration the `params` block reports for an entry that declares none — honoured, never dropped (`declarations.md` §2) |

Two rows are deliberately *not* refusals. `axis`, `primary` and `carried_from` are annotations: they name a rung's role
in the ladder, no behaviour follows from them, and this module's own `rung()` writes all three, so refusing them would
refuse the registry (`ladder.md` §3, `surface.md` §3). `residual` is a setting whose reader is `agents`' kind table and
not this module (`agents/surface.md` §3).

The pass's two bounds are **not a configuration key at all** and are audited with the refusals, and neither refuses a
**run**: the hand bound bounds the **sample** — one pass plays `min(budget, 2,000)` hands, the run's own first `hands`
ones — so a budget above it is sampled and never refused, while a *pass* asked for more than 2,000 hands, or for no
positive number of hands, is refused naming that request and the bound; the record bound is the **run's own shape's**,
1,000 decision records per slot of its history capacity — 24,000 at the default shape, 66,000 and 98,000 on the
uncapped ones — read once through `declarations.greedy_decisions(shape)` and refused with the count, the bound, the
shape and its capacity, never truncated (`sizing.md` §4, `records.md` §15, `shapes.md` §8, ASM-38, ASM-42, D-36).
