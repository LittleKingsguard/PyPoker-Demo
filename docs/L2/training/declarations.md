# training — what a configuration declares, and what the run honours

- **Layer:** L2 · **Module:** `training` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-08
- **Owner of this file:** every key of `ladder.md` §3's schema read against the one loop's own behaviour (§1), the
  rule that keeps a discarded declaration out of a run (§2), the refusals it raises and what each message names (§3),
  the declarations a matched pair must share (§4), and why this module refuses a `hyper` block instead of learning to
  honour one (§5) — D-3, ASM-7, ASM-8, ASM-18, `strata/records/r2-plateau-diagnosis.md`
- **Reads:** `ladder.md` §3–§4, `records.md` §2, `loop.md` §2–§3, `surface.md` §4–§5, `agents/surface.md` §3–§4
- **Ceiling:** 110 lines. At the ceiling, split by owner — never append

## 1. The audit: each key against the one loop

A configuration is data for one loop (`loop.md` §3), so every key it may declare has exactly one of four fates: the run
**reads** it, the run **records** it, another entry point of this module **quotes** it, or the run would **discard** it.
The fourth fate is the defect this file exists to close: a key a run neither uses nor refuses is a caller's intent
dropped in silence, and a sweep written that way measures one model N times
(`strata/records/r2-plateau-diagnosis.md`, D-3). Every row below is a statement about `run`, and the discarded ones are
named as refused in §2.

| The key | What a run does with it |
|---|---|
| `name` | read: the record's `rung` (`surface.md` §4) |
| `variants`, `pool` | read: the pool's `members`, `m` and `frozen` go to `evaluation.build_pool`, and its `id` and `lineage` are carried in the record (`loop.md` §3 step 2) |
| `seeds`, `samples`, `device`, `table` | read, at the configuration and then at its first variant entry, and recorded (`surface.md` §4) |
| variant `name`, `backend`, `encoding`, `architecture` | read: `kind`, `width`, `depth` and `sparsity` build the learner, and `residual` is forwarded to `agents.build_learner`, whose kind decides (`surface.md` §4.2, `agents/surface.md` §3) |
| variant `param_budget`, `samples`, `seeds`, `device`, `table` | read: the declared budget the `params` block reports, and the defaults `surface.md` §4 names |
| `axis`, `primary` | quoted by `fairness` — the axis a pair is reported on, and the variant the next rung inherits — and read by `run` nowhere (`surface.md` §5, `ladder.md` §2) |
| `carried_from` | read by `registry.rung` when it builds a rung's window; for a configuration in no registry nothing reads it, because the window a run freezes is `pool.members` (`loop.md` §3 step 2) |
| variant `learning_rule` | **refused** when it names another rule: a run holds ASM-7's one rule (§2) |
| variant `hyper` | **refused** when it declares another value: a run holds ASM-7's six declarations (§2) |
| `snapshot_every`, at either level | **refused** when it declares another interval: ASM-18 fixes ten, so the interval is the declared budget ÷ 10 (§2) |
| `param_budget` at the configuration | read as the declaration the `params` block reports for an entry that declares none — honoured, never dropped (§2) |

Two rows are deliberately *not* refusals. `axis`, `primary` and `carried_from` are annotations: they name a rung's role
in the ladder, no behaviour follows from them, and this module's own `rung()` writes all three, so refusing them would
refuse the registry (`ladder.md` §3, `surface.md` §3). `residual` is a setting whose reader is `agents`' kind table and
not this module (`agents/surface.md` §3).

## 2. The rule: a declaration the run would discard is refused

ASM-7 fixes one learning rule and its hyperparameters for the whole ladder, and ASM-18 fixes ten snapshots at the
declared budget ÷ 10; that is *why* the loop reads neither a `hyper` block nor a `snapshot_every`, and it is why the
honest answer is a refusal and not a silent substitution (`ladder.md` §4, ASM-7, ASM-18). Four declarations are refused,
each before the first hand is dealt and before anything is written (`loop.md` §3 step 1, `e2e-surface.md` §2):

- **a `hyper` whose declared key disagrees with the declared hyper**, at either level — a configuration may carry the
  block beside its entries, and a block at a level nothing reads is the same discard. A key the block does not name is
  no claim and is accepted; a key it names must carry the value the run will use, in the shape the run will use
  (`agents/surface.md` §3). A differently typed `exploration` — a sentence where the schedule record is declared — is a
  disagreement, not a tolerance.
- **a `learning_rule` naming anything but ASM-7's rule**, at either level. The rule is the ladder's, so a configuration
  cannot hold a second one (`ladder.md` §4).
- **a `snapshot_every` that is not the declared budget ÷ 10**, naming both numbers: honouring it would write fewer than
  ten snapshots and leave ASM-18's retained window unobservable (`loop.md` §3 step 7, guardrails G4). The declared budget
  is resolved as the run resolves the budget itself — the configuration's, else its first entry's — so the number the
  refusal quotes is the interval a run of this configuration would actually use (`surface.md` §4, `loop.md` §3 step 1).
- **a pair whose two entries declare different values for a setting both arms must share** — §4's list — because a run
  uses one value for both arms and would silently keep the first (`ladder.md` §4, ASM-8, ASM-16).

The one key honoured where it was dropped is `param_budget`: the `params` block is per variant, so it reports that
variant's own declared budget, else the configuration's, else the declared 10,000 — an entry-first order, unlike
`seeds` and `samples`, which one run uses once. It is a declaration and not a capacity — a run measures no capacity
(`surface.md` §4, ASM-10). Read, it is validated like every other setting this module reads: a `param_budget` that is
not a positive integer is `VariantSettingInvalid` naming the value, never a `ValueError` out of an `int()` and never a
coin that a band is computed around (`surface.md` §1, `docs/L3/training/errors.md` §2).

## 3. The refusals, and what each message names

Two classes, so a caller routes on the class and never on a message (`surface.md` §1). The names, the message grammar
and the canonical sentence are L3's (`docs/L3/training/errors.md` §2–§4); what this file fixes is that each refusal
names, in its message:

- **`IgnoredDeclaration`** — the entry and the configuration it belongs to, the key, **the value the caller declared**,
  **the value the run uses**, and that varying it means changing the module's declaration (ASM-7). A message that says
  only "ignored" leaves the caller without the number that was in force.
- **`PairDeclarationsDiffer`** — the key, and **both** arms' declared values, the same way `PoolIdsDiffer` names both
  pool ids (`surface.md` §5, ASM-16). `fairness` raises it too, for the two keys it quotes as a held constant: a pair
  that declares two `hyper` blocks holds no constant there, and reporting one of them as held would be the same defect
  in a report instead of a run (`surface.md` §5, `ladder.md` §4).

A refusal here is a refusal of the run, so it deals no hand, builds no learner and writes no file (`e2e-surface.md` §2).
Nothing is repaired and no declared value is replaced by the declared one in silence: a run either uses what the
configuration declares or refuses it (§2).

## 4. The declarations a matched pair shares

Two entries of one configuration are the two arms of one comparison, so they declare one `learning_rule`, one `hyper`
set, one `samples`, one `seeds`, one `device`, one `snapshot_every`, one `table` and one `param_budget` (`loop.md` §2,
`ladder.md` §4). A run trains both arms against one frozen pool and at one budget (`surface.md` §4, ASM-16), so an entry
declaring a second value for any of the eight is `PairDeclarationsDiffer` naming both values; the rule and the hyper set
are already forced to ASM-7's by §2, and the other six are what §4 adds.

## 5. Why a refusal, and not a learner built from the block

Honouring a `hyper` block would mean handing it to `agents.build_learner`'s spec and having `learn`, `act`, `save` and
`load` read it — a change in another module's surface, rule and checkpoint container, designed there and not here
(D-13, `module-map.md` §2, `agents/surface.md` §4). It would also end the claim ASM-7 makes: if two configurations can
carry two hyper sets, then "one rule and every hyperparameter held fixed across the ladder" is a convention nothing
enforces, and a rung-to-rung difference is no longer attributable to the representation it is named for (D-3). The
caller's sweep is not lost by refusing it: it is moved to the one place where it is auditable — the module's declared
hyper (`src/training/declarations.py`), changed once, visibly, and then true for every rung that runs after it
(ASM-7, `strata/records/r2-plateau-diagnosis.md`).

## 6. What is left to L3

The class names' definitions and their docstrings, the four message texts and their order, where each check sits inside
the resolve step, and the shape of the comparison itself — value by value, or a normalised copy of the declaration
(`docs/L3/training/errors.md`, `docs/L3/training/loop.md` §1, §6). Not L3's: that the four declarations are refused,
that a `hyper` key the block omits is no claim, that the message names both values, and the pair's eight settings
(§1–§4, guardrails G16).
