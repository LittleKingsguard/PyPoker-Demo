# PyPoker-Demo — L1 folding baselines: the catalogue, the facts, the anchor and the cost

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-09
- **Covers:** D-21 — the three folding baselines, the hand-class fact they need, the anchor they must not move, what the full declared set does to K, the cells and the tables' cost, and the live-budget verification D-21 exists for
- **Ceiling:** 90 lines. At the ceiling, split by owner — never append

## 1. Why the catalogue grows

The measured degeneracy `strata/records/multiway-probe.md` records is not the seat count: **no bet can win a pot without showdown**, because `always-call` never folds and the `oracle` folds 4.9 % of its decisions — never pre-flop, and only when a raise crosses the pot odds it prices. In a league whose every opponent calls, fold equity is zero by construction, so aggression has nothing to buy and a betting strategy is unlearnable; the ladder would keep measuring a coin flip (`strata/records/r2-plateau-diagnosis.md`, D-6, D-16). Three simple, deterministic, non-learning folders give aggression something to win. That is the whole purpose of D-21, and §6 measures whether it is delivered — and it also measures **how much of the three this game can use**: two of the rules fire and the third cannot, which ASM-34 pins and §2 states.

## 2. The three rules, as implemented

A folder is a policy of `e2e-surface.md` §2: it takes `(readout, legal_actions)` and returns one descriptor from `legal_actions`, it carries no trainable parameter (`params: 0`) and it learns from no match (D-6, ASM-4). All three answer `agents.baselines()` and `agents.build_baseline(name, seed)` exactly as the three of D-6 do, and all three validate the readout they are handed before any rule reads it (`protocol.md` §3, ASM-31).

| Baseline | Folds when | Otherwise |
|---|---|---|
| `fold-no-pair-or-face` | the street is `preflop` **and** the two hole cards are unpaired **and** neither card's rank is a face card — pinned as J, Q, K **or A** (D-21) | check/calls; never folds from the flop onward |
| `fold-no-pair-or-better` | the street is the flop, turn or river **and** `hand_class` is `0` — the best five-card hand of hole plus board is a high card (D-21) | check/calls; never folds pre-flop |
| `fold-large-bet` | `to_call` exceeds half the declared starting stack — **more than 10 chips** at ASM-6's 20, on any street (D-21) | check/calls |

Each is deterministic and seeded in the catalogue's sense: `build_baseline(name, seed)` refuses a non-integer seed as it always has, and the rule consumes no randomness, so two builds at one seed and two builds at different seeds decide identically — the property `always-call` and `oracle` already have (`protocol.md` §3). Every baseline validates the same readout facts, now ten — the nine `baselines.md` §1 fixes today plus `hand_class` — so a malformed readout is refused once, by one rule, whichever of the six is called, and `hand_class` that is neither `None` nor an integer 0–8 is refused naming the fact. A folder's rank test reads the rank character of the one card spelling (`docs/L3/engine/readout.md` §3), so `agents` parses no card and imports no `pokerkit` (D-13).

**And one of the three rules cannot fire in this game, which is stated rather than repaired (ASM-34).** Two-seat fixed limit ends a street on the first call, so the chips to call are always **one bet increment** — 2 pre-flop and on the flop, 4 on the turn and the river — and the measured maximum is **4** over 12,882 decisions; `fold-large-bet` folds only above half of ASM-6's 20-chip stack, which is 10. So that folder is **behaviourally `always-call`** in D-2's game: measured, 0 folds in 6,000 decisions, with `always-call`'s own decision counts and per-street splits. It is not a defective rule and not a defective implementation — it is a rule D-21 pins for a game that threatens a stack, and it would fire in Phase 2's no-limit game (D-4). What it does here is add a **caller**, so a configuration that declares all three buys two folders and one duplicate (§5, §6).

## 3. The hand-class fact, and where it comes from (ASM-30)

`fold-no-pair-or-better` needs a fact the readout did not carry, and `agents` may not import `pokerkit` (D-13), so the fact arrives through the surface: **`engine.readout` gains one key, `hand_class`** — the class of the acting seat's best five-card hand of hole plus board as an integer: 0 high card, 1 one pair, 2 two pair, 3 three of a kind, 4 straight, 5 flush, 6 full house, 7 four of a kind, 8 straight flush — and `None` before the flop, where fewer than five cards are known and no five-card hand exists (ASM-30, `e2e-surface.md` §2). It is a **derived** fact and not a wider information set: it is a function of `hole` and `board`, which the readout already carries, so D-3's information set is unchanged.

**What it costs, and what it does not.** No encoding carries it: `features.observation_spec`'s `fields`, both 203-slot layouts and every shipped checkpoint's encoding are unchanged, so a learner still cannot see it and no rung's observation moves (D-3). The map is unchanged at **49 endpoints**, `modules.json` is untouched, and every harness ceiling stands at `50 + 10×N` (brief §5). `engine` pays the best-hand search per readout — at most 21 five-card lookups from seven known cards, a table lookup each, and none before the flop — and **no equity sample**, so the per-hand cost that ASM-21's band measures (the oracle's sampled equity) does not move with it; the implementation measures that delta rather than asserting it.

The alternative rejected is a `features` evaluator, and ASM-30 states why in full: it would make `features` 8 endpoints, the map 50 and its harness ceiling 130, add an `e2e-surface.md` row and a `general` blind instance, and require an edit to `modules.json` — which this layer neither owns nor edits — while putting hand evaluation in the module whose boundary is "maps a readout to an observation" (`module-map.md` §3, D-13).

## 4. The anchor does not move (ASM-32)

The catalogue's records carry an `anchor` flag: true for the three of D-6, false for the three folders. The Bradley-Terry fit is zeroed on the mean of the **flagged three**, exactly as `league.md` §5 and ASM-17 already state, so a rating recorded before D-21 and a rating recorded after it are read on one scale (D-16, D-21). A pool pins the flagged three always and admits a folder only when a configuration's membership declaration names it (`records.md` §8, ASM-32), so every pool already in the tree — the shipped R1 window included — keeps its membership, its id and its table.

## 5. What the full declared set does to K and to the cells (ASM-33)

Membership is the frozen pool plus the rung's variants, `K = |pool| + V` (`league.md` §4). With M = 5, the three anchor baselines, the three folders declared and a full window:

| Configurations | K today | K declared | Cells today | Cells declared | Hands live / full |
|---|---|---|---|---|---|
| one variant | 9 | **12** | 36 | **66** | 7,920 / 99,000 |
| two variants | 10 | **13** | 45 | **78** | 9,360 / 117,000 |

Cost, at ASM-21's measured band and stated as a forecast and never as a measurement (ASM-23): the oracle is the cost and it sits in **11 of 66 cells** at K = 12 — a sixth, against half at K = 4 — so at ASM-15's composition rates (0.255–0.315 s/hand oracle-bearing, 0.002–0.004 oracle-free) a K = 12 table prices at ≈0.05 s/hand, which is **≈7 minutes live and ≈1.4 hours full**; holding the live table's own 0.1415–0.1532 s/hand instead gives the conservative bound of **≈19–20 minutes live and ≈3.6 hours full**. The band's own composition says the truth sits nearer the cheap end, because the hands grow by 1.47× while the oracle's share of them falls by 3×. What a talk plans for is the conservative end (ASM-21, D-8). **That direction is measured, for a training run rather than for a table**: §6's two runs cost 0.106–0.113 s/hand against the three-member pool and **0.046–0.060 s/hand** against the six-member one, because the oracle's share of the hands halves.

**And two of the three declared members earn their cell.** `fold-large-bet` is `always-call`'s duplicate in this game (§2, ASM-34), so declaring it buys a row and a column of cells that measure a rule already in the table: 66 cells at K = 12 become 55 at K = 11 if a configuration declares only the two folders that fire, and the hands fall from 7,920 to 6,600 live. The cost table above is the price of the **full** declared set D-21 names; a configuration may declare two (`records.md` §8, ASM-32, ASM-34).

## 6. The verification D-21 asks for

Two `training.run` calls of **one** variant — one backend, encoding, architecture, learning rule and utility, on the fixed seeds `0, 1, 2`, at the live budget of 1,000 hands per variant per seed (`protocol.md` §2, ASM-8) — differing in **one** thing: whether the configuration's membership declaration names the three folders. The question is the one the change exists to answer: **does a learner facing opponents that fold bet more?** The action census is `strata/records/r2-plateau-diagnosis.md`'s method — seats alternating, the learner's own decisions counted by descriptor — and the chips per hand are that same match's payoffs, against `always-call` and against each folder, with a 95 % interval from the standard error over hands. The folders' own fold rates are measured the same way, on hands the learner does not touch, so a folder is never credited with an opponent's folds (D-6, D-16, ASM-23).

```text
PYTHONPATH=src .venv/bin/python notebooks/folder-ablation.py
```

**One generation, measured 2026-11-09 on CPU in this sandbox (D-8), and re-run it for your own** (`protocol.md` §2, ASM-23). The pools are `pool-bcbea031cb617939` (the anchor three) and `pool-11b03e0a5ff07c13` (the six), and the declared folders faced the learner in 1,501 of its 3,000 training hands, so the treatment is real.

| The learner's own decisions, vs `always-call` | Raise | Check-call | Fold | Chips/hand vs `always-call` |
|---|---|---|---|---|
| trained against the anchor three | 85.8 % (per seed 97.5 / 63.1 / 97.0) | 14.1 % | 0.1 % | +0.26 (per seed +0.44, +0.32, +0.02) |
| trained against the three folders too | 45.2 % (per seed 88.4 / 18.3 / 28.8) | 54.6 % | 0.1 % | +0.16 (per seed +0.23, −0.02, +0.25) |

| The folders' own fold rate, pooled over 750 hands per opponent | vs `always-call` | vs `random` |
|---|---|---|
| `fold-no-pair-or-face` | 6.3 % (21.2 % of its pre-flop decisions, 0 % after) | 9.6 % (29.4 % pre-flop) |
| `fold-no-pair-or-better` | 0 % — a caller never makes it fold | 9.7 % (22.7 % of flops, 11.6 % of turns, 3.4 % of rivers) |
| `fold-large-bet` | 0 % | 0 % (ASM-34: the trigger is unreachable) |
| `always-call` / `oracle`, this generation | 0 % / 0 % | 0 % / 4.3 % (2.8 % of flops, 8.8 % of turns, 6.6 % of rivers) |

**The plain verdict on the question: no — at the live budget, facing opponents that fold did not make this learner bet more.** The raise share **fell** 40.7 points pooled, and all three seeds move the same way, but the arms' own per-seed ranges overlap over [63.1 %, 88.4 %] and the paired drop is 40.7 ± 17.2 points across three seeds, so the direction is **unresolved** at this budget and no cause is claimed for it: the declaration also halves each anchor baseline's share of the training hands, and 1,000 hands leaves the policy dominated by seed variance. What *is* established is that the fold equity now exists at the street where each rule bites — 21 % of pre-flop decisions and 23 % of flops, against the oracle's 0 % and 2.8 % on those streets — and that a bet still wins only ±2 chips, because fixed limit's one-increment call is the whole of what a folder can be made to surrender (`strata/records/multiway-probe.md`). Chips per hand resolve nothing: against `always-call` and against every folder, every interval spans zero in both arms. A talk reads this table as *a population that folds exists now*, not as a stronger learner (D-21, D-6, ASM-23).

## 7. What a table over folding opponents may not be read as

A member that beats a folder has shown that it wins more hands than it loses against that fixed rule at this cell size, and **nothing about poker skill** (`league.md` §8, D-16). A folder is a fixed standard chosen to be simple, not a standard chosen to be strong: `fold-no-pair-or-face` folds a fifth of its pre-flop hands and `fold-no-pair-or-better` a fifth of its flops, so a learner that exploits them has demonstrated fold equity and not sound play — and with `fold-large-bet` inert in this game (§2, ASM-34), two of the three are all the fold equity the catalogue offers. The census is the evidence this change is read by — a share of decisions, not a rank — and it answers one behavioural question at one seed set (D-21, D-6, ASM-23).
