# training — what a configuration declares, and what the run honours

- **Layer:** L2 · **Module:** `training` · **Unit:** phase1 · **Rev:** 6 · **Date:** 2026-11-11
- **Ceiling:** 110 lines. At the ceiling, split by owner — never append
- **Owner of this file:** every key of `ladder.md` §3's schema read against the one loop's own behaviour (§1, whose table
  is `audit.md`'s), the rule that keeps a discarded declaration out of a run (§2), the refusals it raises and what each
  message names (§3), the declarations a matched pair must share (§4), and why this module forwards a rule, a utility and
  a shape and refuses a `hyper` block (§5) — D-3, ASM-7, ASM-8, ASM-18, ASM-38, D-19, D-20, D-29. **Rev 4:** D-29 reaches
  §1's `game` row, §2's shape refusal, §4's eighth held setting and §5; the pass's two bounds are declared and refused
  with them (§2, `docs/L3/training/greedy.md` §4, ASM-38). **Rev 5:** D-33 makes the catalogue **three** rows and that
  shape declaration **three** tables — the names, the descriptor counts and each shape's history capacity — and the
  pass's record bound the run's own shape's, 1,000 records a slot; the seat count is none of them, being read from
  `engine.game_config` (§1–§2, `shapes.md` §2, §8, ASM-42, ASM-44, `seats.md` §2–§5, D-33). **Rev 6:** D-36 makes the hand bound the **sample's** (`min(budget, 2,000)`) and no run's, so a pass is refused for a request and never a run for its budget (§2, `greedy.md` §4, D-36)
- **Reads:** `ladder.md` §3–§4, `records.md` §2, `loop.md` §2–§3, `surface.md` §4–§5, `agents/surface.md` §3–§4,
  `shapes.md` §2–§3, §8, `seats.md` §2–§5

## 1. The audit: each key against the one loop

A configuration is data for one loop (`loop.md` §3), so every key it may declare has exactly one of four fates: the run
**reads** it, **records** it, another entry point **quotes** it, or the run would **discard** it. The fourth fate is the
defect this file exists to close: a key a run neither uses nor refuses is a caller's intent dropped in silence, and a
sweep written that way measures one model N times (D-3, ASM-7). **The table is `audit.md` §1's**, split out at this
file's ceiling with the numbering kept: it carries every key `ladder.md` §3 lets a configuration declare — `game` among
them, read at either level and recorded, refused when it names a shape the catalogue does not carry (§2, §5) — and the
discarded ones are named as refused below.

## 2. The rule: a declaration the run would discard is refused

ASM-7's one rule became the catalogue D-19 ratifies — two estimators a variant may name — while its hyperparameters stay
one declaration for both (`rules.md` §2), and ASM-18 fixes ten snapshots at the declared budget ÷ 10. So the loop reads a
`learning_rule` and forwards it, reads neither a `hyper` block nor a `snapshot_every`, and refuses a declaration it cannot
honour rather than replacing it — four of them, before the first hand and before anything is written (§3 step 1):

- **a `hyper` whose declared key disagrees with the declared hyper**, at either level — a configuration may carry the
  block beside its entries, and a block at a level nothing reads is the same discard. A key the block does not name is
  no claim and is accepted; a key it names must carry the value the run will use, in the shape the run will use
  (`agents/surface.md` §3). A differently typed `exploration` — a sentence where the schedule record is declared — is a
  disagreement, not a tolerance.
- **a `learning_rule` or a `utility` a catalogue does not carry**, at either level: each is read and forwarded (§1), so
  what is refused is a name no learner can be built under — not a second rule or a second utility, because a configuration
  may declare two of either and train two (`rules.md` §2, §7, `utilities.md` §5, §8, D-19, D-20).
- **a `snapshot_every` that is not the declared budget ÷ 10**, naming both numbers: honouring it would write fewer than
  ten snapshots and leave ASM-18's retained window unobservable (`loop.md` §3 step 7, guardrails G4). The declared budget
  is resolved as the run resolves the budget itself — the configuration's, else its first entry's — so the number the
  refusal quotes is the interval a run of this configuration would actually use (`surface.md` §4, `loop.md` §3 step 1).
- **a `game` the three declared shapes do not carry**, at either level: the shape a run trains and is evaluated on is a
  **named** declaration (`records.md` §2), so a name outside the catalogue is refused naming it and every declared name
  rather than forwarded or defaulted — while a level declaring none is no claim and reads as the catalogue's first
  shape (`shapes.md` §2–§3, D-13, D-29). A pair of two shapes is refused too: two arms of one comparison are one
  shape's (§4, `shapes.md` §1).
- **a pair whose two entries declare different values for a setting both arms must share** — §4's list — because a run
  uses one value for both arms and would silently keep the first (`ladder.md` §4, ASM-8, ASM-16).

The one declaration the run does not read and does not refuse is the **pass's bound**, because it is not a caller's to
declare: one pass plays `min(budget, 2,000)` of the run's own hands, so a budget above it is **sampled, never refused**;
and the record bound is the run's own shape's — 1,000 records a slot, 24,000 / 66,000 / 98,000 — read through
`declarations.greedy_decisions(shape)` and refused by `GreedyPassRefused` naming the count, the shape and its capacity,
never truncated (`sizing.md` §4, `records.md` §15, `shapes.md` §8, ASM-38, ASM-42, `greedy.md` §4, D-36).

The one key honoured where it was dropped is `param_budget`: the `params` block is per variant, so it reports that
variant's own declared budget, else the configuration's, else the declared 10,000 — an entry-first order, unlike
`seeds` and `samples`, which one run uses once. A `param_budget` that is not a positive integer is
`VariantSettingInvalid` naming the value, never a `ValueError` out of an `int()` (`surface.md` §1, §4, ASM-10).

## 3. The refusals, and what each message names

Two classes, so a caller routes on the class and never on a message (`surface.md` §1). The name, the grammar and the
canonical text are L3's (`docs/L3/training/errors.md` §2–§4); what this file fixes is what each message names:

- **`IgnoredDeclaration`** — the entry and the configuration it belongs to, the key, **the value the caller declared**,
  **the value the run uses**, and that varying it means changing the module's declaration (ASM-7). A message that says
  only "ignored" leaves the caller without the number that was in force.
- **`PairDeclarationsDiffer`** — the key, and **both** arms' declared values, the same way `PoolIdsDiffer` names both
  pool ids (`surface.md` §5, ASM-16). `fairness` raises it too, for the one key it quotes as a held constant: two
  `hyper` blocks hold no constant there, and reporting one as held would be the same defect in a report instead of a
  run (`surface.md` §5, `ladder.md` §4); a differing `learning_rule` is the pair's axis instead (`rules.md` §8, §4).

A refusal here is a refusal of the run, so it deals no hand, builds no learner and writes no file (`e2e-surface.md` §2).
No declared value is replaced by the run's own in silence: a run uses what the configuration declares or refuses it (§2).

## 4. The declarations a matched pair shares

Two entries of one configuration are the two arms of one comparison, so they declare one `hyper` set, one `samples`, one
`seeds`, one `device`, one `snapshot_every`, one `table`, one `param_budget` and one `game` (`loop.md` §2, `ladder.md` §4)
— eight settings, and a second value for any of them is refused, because both arms train against one frozen pool on one
shape at one budget (`surface.md` §4, ASM-16, `shapes.md` §1). Six are refused by `PairDeclarationsDiffer` naming both
arms; `hyper` and `snapshot_every` are refused earlier and per arm by `IgnoredDeclaration` (§2). `learning_rule`,
`utility` and the shape are never an axis: `fairness` reports the sets it read, not one side's (`rules.md` §8,
`utilities.md` §8, `utility.md` §5, `shapes.md` §1, D-19, D-20, D-29).

## 5. Why the rule, the utility and the shape are forwarded and the hyper refused

The three answers differ because the register does. D-19 makes the estimator a parameter a variant names, D-20 makes the
objective one and D-29 the game one, so the run reads `learning_rule`, `utility` and `game` and hands each on: the first
two to `agents.build_learner`, which builds them and refuses an uncatalogued name itself (`rules.md` §2, §4,
`utilities.md` §5, D-20), and the shape to the encoder, the learner's head, the hand and the pool — because a shape
names no behaviour of this module's and changing it changes what every downstream call is built from (`shapes.md`
§2–§3, `sizing.md` §5–§6, D-29). The hyper declaration is not per rule — both rules consume the same six values — so
honouring a per-configuration `hyper` would make "every hyperparameter held fixed across the ladder" a convention
nothing enforces, and a rung-to-rung difference no longer attributable to the representation it is named for
(`rules.md` §2, D-3, ASM-7); it would also mean another module's learner reading it, designed there and not here
(D-13, `module-map.md` §2). The caller's sweep moves to the one auditable place, the module's declared hyper
(`src/training/declarations.py`), changed once and visibly for every rung after it (ASM-7, `r2-plateau-diagnosis.md`).

## 6. What is left to L3

The class names' definitions and their docstrings, the message texts and their order, where each check sits inside the
resolve step, and the shape of the comparison (`docs/L3/training/errors.md`, `docs/L3/training/loop.md` §1, §6). Not
L3's: that these declarations are refused, that a message names both values, the pair's eight settings, the two axis
exceptions and the pass's two bounds (§1–§5, G16, D-20, ASM-38).
