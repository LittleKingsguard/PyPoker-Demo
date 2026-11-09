# PyPoker-Demo — L1 evaluation protocol

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 8 · **Date:** 2026-11-09
- **Covers:** brief §3 — curves, the league table, the fitted rating, the fixed baselines, fixed seeds, and the rule set and utility set a table measured (D-6, D-16, D-19, D-20)
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append

## 1. What a rung must report

A rung is not progress on the strength of a curve alone (D-6), and since D-16 its opponent is the
league, so the evidence is a matrix and a rating over that matrix (`league.md` §4, §5). `evaluation.report`
refuses to return a report unless all of the following families are present, and names the missing
family when it refuses:

| Evidence family | Content |
|---|---|
| curves | per variant, per seed: the sample axis and at least one learning signal from `agents.learn`, with the spread across seeds recorded (D-6) |
| pool | the frozen pool the run trained against and was evaluated over: its id, M, its ordered members with lineage and each member's rule and utility, the `rules` and `utilities` those members declare, and — for a two-variant rung — the one id both arms recorded (D-16, D-19, D-20) |
| matrix | the pairwise matrix of `league.md` §4 at one table budget: one cell per unordered pair, both directions, the hand count, the seat split, and the mean chip delta per hand (D-16) |
| rating | the fitted rating of `league.md` §5: one value and a 95% interval per member with the method, the anchor and the hands behind each value (D-16) |
| baselines | the three baseline rows inside that matrix, each at the same hand count as every league cell (D-16) |
| axis row | R4, R5 and R6 carry their own pair's cell of the matrix plus the matched budgets of `ladder.md` §4. R1–R3 carry the explicit value `n/a, single variant` |
| header | the game configuration, the action vocabulary, the parameter counts of every member, the sample budget, the cell size, the seed set, the table seed, the device and the checkpoint paths — everything a third party needs to re-run the table (D-6, D-16) |

That table is the whole list, and it is the only place the count is fixed: those seven names are
`evaluation.protocol()["families"]`'s keys and the only names a report can refuse a record for. A report
carries **five further keys** beside them — `rung`, `seeds`, `table`, `table seed` and `device` — the facts a
report states about the run it reports, and not evidence families, so a report is **seven families plus five
facts, twelve keys in all** (`records.md` §13, `docs/L3/evaluation/report.md` §2). The two numbers never
compete: the shipped bundle's `report_families` lists a report's twelve **keys**, sorted, so it is a key list
and not a family count — read as a family count it is five too many.

Every cell alternates seats across hands and reports the seat split, because a heads-up result that
only ever gives one member the button is a positional artefact and not a measurement (D-16). Members
are reported by the id the pool gave them, never by rank order alone (D-16).

## 2. The recorded comparison

- The seed set is fixed at `0, 1, 2` and is recorded in every run record and every report; a comparison a third party cannot re-run from the record is not evidence (D-6).
- A run trains for 1,000 hands per variant per seed live and 200,000 for a long shipped run, at the seed set above (`ladder.md` §6, ASM-8). What ships today is R1's set from a live-budget run — 1,000 hands per variant per seed — so the record of that set says a live budget and no long run exists yet to stand beside it (D-8, ASM-18).
- A table cell is 120 hands live and 1,500 hands full, seats alternating, for every pair in the membership — the three baselines included (`league.md` §6, ASM-14).
- Every cell reports wins, ties and losses, the mean chip delta per hand, the seat split and the hands played. Chip delta, not only win rate: fixed-limit heads-up with short stacks makes ties and splits common (ASM-6), and a win rate alone hides them.
- The matrix is reported in raw form alongside the rating, because a fitted rating assumes a transitive order and poker payoffs need not be (D-16).
- No claim beyond the table is made: Phase 1 compares architectures on one small game, and a league rank is not a claim of poker skill, exploitative play or superhuman play (D-16, brief §8).
- **A rung's variants may be trained under different rules, and every variant declared is trained** — its own curve, its own snapshots and final model, and its own row in the run record — so a configuration that declares two estimators has two learners' evidence and not one learner's opponent (D-19, `rules.md` §7). A report states the **population its table measured**: the matrix's `population`, the pool's `rules` and each variant's declared rule, in the run record's `variants` (`records.md` §10, §12, D-19). Reading a cell means reading which two estimators met in it, which its `rules` entry says (`records.md` §9).
- **A rung's variants may likewise be trained under different utilities, and a report states which** (D-20). The matrix's `utility_population`, the pool's and the run record's `utilities` and each variant's declared `utility` are the objective side of the same statement (`records.md` §10, §12), and a cell's `utilities` entry says which two objectives met in it (`records.md` §9). The cells are still in chips and hands, because chips are what the game pays: a member trained on `stack-shortfall` is judged in the game's currency and is neither better nor worse by it, which every report says plainly (`utilities.md` §9, ASM-29).
- **This document and every layer below it state the shape of a result, never a figure a regeneration moves** (ASM-23). A rating is an ordering and a separation, a cell a direction, a cost a band plus the file, and the number itself is read from `checkpoints/evidence/r1-live.json`, `tables/league-full.json` or the record that measured it — because both artefacts have already been regenerated under an unchanged shape, and a prose figure outlives its build by exactly one run. One exception: a document whose whole purpose is one generation of one artefact, identified by that generation's commit and `generated_utc`, quotes it exactly and says so (`docs/L3/training/evidence.md` §3); a page that needs rhetorical force uses an approximation a re-run cannot falsify (ASM-23, ASM-15, ASM-21, `league.md` §7, D-6, D-8).

## 3. The three fixed baselines (D-6, ASM-4)

`agents.baselines()` names exactly three, none of them learns from a match, and all three are pool
members and matrix columns at the same hand count as every league cell — they are the only fixed
standard in a self-play league, so they anchor every claim the table makes (D-16):

| Baseline | Rule | Property a battery can assert |
|---|---|---|
| `random` | a uniform draw over the legal indices, from an explicitly seeded generator | never returns an illegal index; two runs at one seed agree and two seeds differ (D-6) |
| `always-call` | check/call whenever legal, never fold, and the minimum legal completion when raising is the only option | never folds in any decision of any hand (D-6) |
| `oracle` | call/continue when the hand's equity from `engine.equity` is at least the pot odds `to_call / (pot + to_call)`, otherwise fold when folding is legal | its choice is consistent with that inequality at every decision, computed from the same two entry points a battery can call (ASM-4) |

The oracle is fixed by construction: it is a rule over pot odds against `pokerkit`'s equity calculation,
not a policy distilled from a trained rung (ASM-4). It is deliberately strong on the pot-odds axis and
blind on everything else — that is what makes it a baseline rather than a competitor (D-6). The three
baselines play each other in the table as well as playing every version, so the matrix carries three
cells whose result no model can influence (D-16).

## 4. Seeds (ASM-2)

- `pokerkit` shuffles its deck with Python's global `random` at state creation and accepts no seed parameter (`strata/platform.md`). `engine.new_hand(seed)` is therefore the single point that seeds the global `random`, and no module seeds it anywhere else (ASM-2).
- Because one global stream deals every hand, matches run sequentially: a cell is played hand after hand, and two cells are never interleaved or threaded (D-16, ASM-2). Sequential play is the contract, not an implementation choice.
- A learner's exploration and any sampling of transitions draw from an explicitly constructed generator seeded from the run's seed, so a rung never depends on accidental shared global state (D-6).
- A run is reproducible from `(configuration, seed set, budget, pool membership)`. Exactness is promised on CPU, which is the sandbox and the audience's laptop (D-8); a user-started GPU run records its device, and a third party reading the record can tell the two apart (D-6).
- **Reproducibility is one build's and one interpreter's, and both are recorded.** `engine.equity`'s sampled estimate — the oracle's decision input (ASM-4) — orders its sampling universe from a set whose iteration order follows Python's per-process hash seed, so two processes of one build can differ in the `oracle` cells and in a run's last curve points: measured on this build, one live cell's win/tie/loss counts moved by a hand between two processes, and two 60-hand runs of one `(configuration, seed set, budget)` differed in their last two curve points. The counts that measurement read are beside the bundle it was made against, in `docs/L3/training/evidence.md` §6, and not here, because a live cell's own counts move with every regeneration (ASM-23). A re-run that has to reproduce the shipped evidence therefore sets `PYTHONHASHSEED=0`, the condition `checkpoints/evidence/r1-live.json`'s `provenance` records; and a different build rewrites different curves whatever the pin (D-6, D-16). That the estimator should be order-stable rather than pinned is a defect of `engine`'s, recorded with `docs/L3/training/evidence.md` §6 and routed, not a licence to soften this clause.
- The battery asserts the contract at its observable edge: one seed, one configuration and one pool produce identical outcomes on two runs, a different seed or a different pool produces a different one, and the table seed a cell used appears in the cell (ASM-2, D-16).

## 5. Checkpoints and pool retention (ASM-5 as D-16 amends it)

- **Two artefact sets, and only one of them ships.** A run **writes** eleven artefacts per variant × seed — ten equally spaced snapshots plus that pair's final model, **33** for R1's three seeds at the live budget — and the repository **ships** only the retained window plus each pair's final model: six per variant × seed, **18** for R1's three seeds, the fifteen earlier snapshots staying intra-run. The 33 are a run's own and **regenerable** — the same run rewrites them at the declared budget — while the 18 are the set a reader **protects**: they are what `training.checkpoints()` indexes and what `checkpoints/` holds, a battery never touches them because both its hooks point the write root at a private temporary directory (`battery.md` §2), and a deliberate run is redirected rather than aimed at them (`getting-started.md` §4). The rolling window retains the last M=5 of the ten snapshots; the lean rule of ASM-5 is superseded, because without snapshots the league has no opponents and the table is a claim the audience cannot reproduce (D-16, ASM-18).
- `training.checkpoints()` is the index over exactly that set, and `evaluation.policy_from` loads one member in evaluation mode (D-16).
- A loaded checkpoint chooses the same action as the learner that produced it on the same readout: the pair `agents.save`/`agents.load` is required to be loss-free at the decision boundary, and that is what lets a shipped version be a league member (ASM-5, D-16).
- The pool is built from the checkpoints the repository ships. When a lineage checkpoint is absent, the pool holds the baselines and whatever versions are present, and the run record states the membership it actually used — it never pretends a version it could not load (D-16, D-8).
- `checkpoints/evidence/r1-live.json` is the shipped record of the R1 live run, and it is the only one of its kind: that run's run record (`records.md` §12), the frozen pool it trained against, its four-member/six-cell `live` table, the Bradley-Terry rating over it, its report of §1's seven families plus the five facts beside them — twelve keys in all, and its `report_families` is that twelve-name key list and not a family count — the device it ran on and the shipped checkpoint index — three seeds at 1,000 hands, so 3,000 hands at a per-hand cost inside ASM-21's 0.105–0.120 s/hand run band, the file carrying that build's own seconds per seed and per stage rather than this document — and, as its seventeenth key, the **build it came from**: a source digest over `src/` and `pyproject.toml`, the commit and whether the tree was dirty, the interpreter, its dependency versions and the hash seed it was pinned to, because a committed number nobody can attribute to a build is not evidence a third party can reproduce (D-6, D-8). It is **evidence and not an interface**: no entry point reads it, the one writer is the offline producer `scripts/regenerate-evidence.py`, and every path inside it is repository-relative, so the record travels with the tree instead of naming one machine's home directory (D-8, D-16, ASM-18). Its shape and status are `training`'s to document under `docs/L3/training/`, exactly as `tables/league-full.json`'s are `evaluation`'s (`docs/L3/evaluation/tables.md` §3–§5).
- The two tables of `league.md` §6 ship as those two files and no others: a `live` table is played by the talk and is not written to `tables/`, whose one occupant is the offline `full` table, and one member id does not identify one player across the two — `league.md` §9 states the rule each file obeys (D-8, D-16).
- **The shipped artefacts measured a population of one rule and one objective, and that is stated rather than repaired.** `checkpoints/evidence/r1-live.json` and `tables/league-full.json` were measured under the single-rule, single-utility arrangement that preceded D-19 and D-20, and the 18 checkpoints they name are version-1 containers, which read as `masked-q-learning` and `net-chips` (`rules.md` §6, `utilities.md` §6): their population is one rule and their utility is one objective, and each member's record says so. Re-measuring them under the catalogues is D-19's and D-20's own re-baseline, and it is a separate decision — what it costs is stated in this layer's return, not assumed here. So no figure in either file is regenerated by this change, and no document quotes one as though it had been (D-19, D-20, D-8, ASM-8, ASM-23).

## 6. Where the device rule bites (`strata/platform.md`, D-8)

A run started by this workflow is CPU-bound, because the file sandbox denies the GPU device nodes.
`training.devices()` reports what is available and records the default, so a run never silently claims a
GPU it did not get (D-8). A GPU run is the user's, started outside the sandbox, and its record says so —
the checkpoint and the report carry the device, so the two are never confused (D-6, D-8). No part of the
protocol requires a GPU: every rung and both table budgets run on CPU (D-8, ASM-15), which is also why
the live table's cost is bounded by hands played and not by a device (D-16).
