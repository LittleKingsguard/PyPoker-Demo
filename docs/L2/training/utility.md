# training — the utility axis: what a variant is trained on, and where it is applied

- **Layer:** L2 · **Module:** `training` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-09
- **Owner of this file:** D-20's terminal-reward *utility* at this module's edge — what a configuration declares
  and what a run honours (§1), **the one place the reward is transformed** (§2), what the loop records (§3), what the
  shipped index says (§4), the seventh fairness axis (§5), and the four numbers that are this layer's to assert (§6)
  — D-19, D-20, `utilities.md` §2–§8, `battery.md` §5
- **Read with:** `surface.md` §4 (the run record), §5 (`fairness`), §7 (`checkpoints`); `declarations.md` §1–§4 (the
  audit each declaration is judged by); `docs/L3/training/reward.md` (the design of the transform), `docs/L3/training/loop.md` §1–§4
- **Ceiling:** 100 lines. At the ceiling, split by owner — never append

This file was split out of `surface.md` and `declarations.md` when D-20 reached both at their ceilings; each of them
keeps a one-line pointer here, so a record's keys and this axis have one owner each (`surface.md` §1, D-12).

## 1. The declaration: one more axis a configuration may name

- **`UTILITY` is a module constant beside `LEARNING_RULE`.** Both name the catalogue's **first** member — and both
  are what the six rung rows declare, never a value a run is fixed to (`declarations.py`, `utilities.md` §5, D-19,
  D-20). Every variant entry of every rung row carries `"utility": UTILITY`, so both arms of every rung ask one
  objective and no rung quietly differs on this axis (`utilities.md` §8, D-3, ASM-7).
- **A variant entry's `utility` is read and forwarded**, at the entry first and then at its configuration, exactly as
  `learning_rule` is: the value reaches `agents.build_learner`'s spec, so the variant is trained on the reward it
  names (`records.md` §2, `utilities.md` §5, D-20).
- **`utilities()` reads the catalogue, never a copy of it.** `tuple(agents.learners()["utilities"])`, the mirror of
  `learning_rules()`, so the names a run refuses an unknown value against are the names `agents` publishes
  (`module-map.md` §2, `utilities.md` §2, D-20).
- **`utility` is an axis, not a shared setting.** It is in `AXES` (seven axes: `backend`, `encoding`,
  `architecture`, `connectivity`, `residual`, `rule`, `utility`) and **not** in `PAIR_SETTINGS`, because two arms may
  declare two utilities and every variant is trained (`declarations.md` §4, `utilities.md` §8, D-19, D-20).
- **`_check_utility` refuses an uncatalogued name**, at the configuration and at each entry, naming the value and the
  catalogue and raising `IgnoredDeclaration` — the mirror of `_check_learning_rule`, and like it a refusal of a name
  no learner can be built under, never of a *second catalogued* utility (`declarations.md` §2–§3, D-20).

## 2. Where the transform is applied, and only there

**`episode._transitions` is the one place a utility reaches a number** (`utilities.md` §4, `src/training/episode.py`):

- the step takes the utility's name, and at the seat's **terminal** decision only it replaces the record's `reward`:
  under `net-chips` with `r = delta`, and under `stack-shortfall` with `r = (U(s_before) − U(s_after)) / U(s_0)`,
  `U(s) = (T − s)²`, `s_before = s_0`, `s_after = s_0 + delta`, `delta` the decision's own reward (`utilities.md` §2, §4);
- `s_0 = engine.game_config()["starting_stack"]` (20) and `T = sum(readout["stacks"]) + readout["pot"]` read from
  that decision's readout — 40 at every decision of the fixed game, the pot being un-awarded and chips conserved
  (`utilities.md` §4, ASM-6, D-2);
- **every non-terminal decision keeps `0.0`**, and the arithmetic is selected by the catalogue's **reward token**
  (`net-chip-delta`, `squared-stack-shortfall-delta`), so no member name is copied into this module (D-20);
- **a hand whose two totals disagree** — `T` against `seats × s_0` — is refused by name with the hand's seed and both
  totals, as `ChipConservationBroken`, a `training` class; it can fire only if the game stops holding its chips
  (`utilities.md` §4, ASM-6);
- **`src/agents/learner.py`'s reward arithmetic is untouched**: its terminal branch stays `target = record["reward"]`
  and its non-terminal branch stays the rule's, so the utility decides what a terminal transition is worth while the
  rule decides how a non-terminal one bootstraps (`utilities.md` §4, ASM-12, ASM-25, D-19, D-20).

## 3. What the loop records

- **`_declared_utility` / `_trained_utility` mirror the rule pair:** the entry's value, else its configuration's,
  else the catalogue's first, so a variant naming none is trained on `net-chips` and this module substitutes no
  default of its own (`utilities.md` §5, `docs/L3/training/loop.md` §1 step 3, D-20).
- **The spec carries `utility` when the entry declares one**, and carries no key when it does not — the shape
  `records.md` §3 and `surface.md` §4 give `learning_rule` (`records.md` §3, D-20).
- **The transition step is handed the trained utility**, once per variant per seed, and never per hand (`§2`).
- **A run record's `variants` entries carry `utility` beside `learning_rule`**, so a run says which objective
  produced which curve (`records.md` §12, `utilities.md` §7, D-20).
- **The record's top-level `utilities` is the set the run declared and trained**, beside `rules`: one name for a
  ladder rung and two for a configuration whose arms name two (`records.md` §12, D-20).
- **The `pool` block carries `utilities` beside `rules`** — the distinct utilities the pool's **version** members
  declare, read off `pool_members` and never invented here; a baselines-only window reports the empty set
  (`records.md` §8, §12, `utilities.md` §7, D-20).

## 4. What the shipped index says

`SHIPPED_UTILITIES` sits beside `SHIPPED_RULES`, keyed by rung, and every index entry and every `windows` block
carries `utility` for the same reason it carries `rule`: a version record's `utility` is required and no default
stands in for one (`records.md` §7, `utilities.md` §6, ASM-5, D-20). R1's live run predates the catalogue, so its
containers are version 1 and are read as `net-chips`; the shipped set is not regenerated (`surface.md` §7, `utility.md`
§4 of `agents`, D-20).

## 5. The seventh fairness axis

- **The token and the field are one word: `utility`** — unlike the rule's pairing of the token `rule` with the field
  `learning_rule` (`utilities.md` §8, D-20).
- **`_utility` / `_utility_set` mirror the rule pair:** entry's, else its configuration's, else the catalogue's
  first, so a side spelling the default out and a side leaving it unsaid are one utility and never a phantom
  difference (`utilities.md` §5, §8, `fairness.md` §2).
- **`_differences` appends the axis** and `_constants` reports a `utilities` **set** beside `rules`; a pair differing
  on `utility` *and* on another axis stays `MultipleAxes`, naming both (`surface.md` §5, D-3, D-6, D-20).
- **The `reward` constant states the utility's reward** rather than one fixed sentence — the catalogue's own token for
  each utility the pair names, both for a two-utility pair — and keeps its ASM-12 citation (`utilities.md` §2,
  `fairness.md` §4, D-20).

## 6. The four numbers this layer asserts, because the battery cannot

The e2e battery never asserts the transform's arithmetic — `battery.md` §5 says so explicitly — so the reward's
values are asserted at module level, in `tests/training/test_episode.py`, from the implementation rather than from a
constant: **+0.190 / −0.210** for a ±2-chip hand and **+1.000 / −3.000** for an all-in, the zero non-terminal term
under both utilities, and the guard's refusal naming a hand's seed and both totals (`battery.md` §5, `utilities.md`
§2, §4, D-20). A run's two arms under two utilities are asserted to produce **different curves on the same hands**,
which is the observable the changed reward must produce (`battery.md` §3 FAM-18, D-20).
