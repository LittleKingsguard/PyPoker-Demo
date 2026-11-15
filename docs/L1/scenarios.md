# PyPoker-Demo — L1 the loaded-deal scenario suite

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-15
- **Covers:** D-70's instrument — the declared table of sixteen concrete scenarios (eight hole sets, each on one board that helps it and on one board that helps none of them), the scripted six-seat opposition and the two seatings the model decides in, the post-D-61 models the table is read against and the era rule that admits only them, what each row reports and the tables the report is, the answer rule, and the state of the measurement (D-70, D-69, D-59)
- **Ceiling:** 160 lines — 115 for the design as filed and 45 reserved for the tables §6 declares, which arrive with the measurement. At the ceiling, split by owner — never append

## 1. The question, and why a scenario replaces a census

Every behavioural result this project has recorded is an **aggregate census** — a share of actions over thousands of hands — and D-59 showed what an aggregate can hide: four models reported "never folds" as a strategy while emitting **one constant score vector** for 477 different observations — a collapsed network, not a preference (D-59, D-60). A census cannot tell "it folds because its hand is weak" from "it folds because it cannot see".

This instrument asks the question directly, and D-70 makes it primary: **what does this model do when it holds aces, and what does it do when it holds seven-deuce offsuit** — and, for the same hole cards, on a board that helps them and on one that does not. It is served by the **loaded deal** of `loaded-deal.md`: prescribed hole cards per seat and a prescribed board, validated by name and recorded in the episode.

**A census is not abolished**: it stays the instrument for population-level questions. What is abolished is quoting a per-cent as if it were a strategy — every "the model does X %" claim must be backed by a table showing *when* it does X (D-70).

## 2. The declared data

The table is `docs/L1/scenarios.json`, and it is **data**: a scenario, a board, a seating or a model is an edit to that file and touches no code, which is D-70's requirement of the suite. Its keys are four metadata ones — `unit`, `decision`, `rev`, `date` — and the data ones: `shape`, `card_spelling`, `era`, `opponents`, `seatings`, `boards`, `scenarios`, `models`, `run`, `report`, `checks` and `measurement_state`.

Its `checks` block is not decoration: those eight invariants are what make the file self-consistent, the runner asserts them before it deals a hand, and a file that breaks one is refused by name rather than measured. They were verified by hand when this Rev was written, and again by the layer's examiner, which is how Rev 2 found that Rev 1's `7-2 offsuit` hand was dealt two clubs — suited, and therefore not the hand D-70 names.

## 3. The sixteen scenarios

Seven boards serve sixteen scenarios. **All eight** negative cases share one board, `common-dry` — and the six helper boards serve the other eight rows — because the honest comparison the brief invites is a **single** board on which every hole set is played: it makes the hole contrast a comparison of eight hands in one state, and the board contrast a comparison of two states differing in nothing but the board.

Rev 1 used an all-broadway board for that role and withdrew it: an all-broadway board holds an ace, a king and a queen, so it makes aces **trips** and K-Q **top pair** — it helps three of the eight hole sets and cannot be the common non-helper. `common-dry` is instead `3s 6d 9d 4c Jh`: no ace, king, queen, deuce, seven or eight, so no hole pair is made or set and the board itself pairs nothing; no suit runs past three, so no hand is within one card of a flush, a draw being four; and 8-7 makes no straight against it, its 6-7-8-9 being four to a run that needs a five or a ten.

The class column is `readout`'s `hand_class` at the flop — 0 high card, 1 pair, 2 two pair, 3 trips, 4 straight — so a helper is a strictly better hand than its partner and not a matter of opinion (`readout.md` §2, `folders.md` §3).

| # | Hole set | Hole | Board | Flop | Class | What the board is |
|---|---|---|---|---|---|---|
| S1 | paired aces | `As Ad` | `Ah Kd 7c 5s 2c` | trip aces | 3 | helps: an ace, so the pair is a set |
| S2 | paired aces | `As Ad` | `3s 6d 9d 4c Jh` | one pair | 1 | does not: no ace, and the board pairs nothing |
| S3 | K-Q suited | `Ks Qs` | `Kh 9s 8s 4h 2d` | top pair, 4 spades | 1 | helps: top pair **and** a flush draw |
| S4 | K-Q suited | `Ks Qs` | `3s 6d 9d 4c Jh` | high card | 0 | does not: no pair, and 3 spades is no draw |
| S5 | K-Q offsuit | `Kh Qd` | `Kc 9h 4h 2s 8c` | top pair | 1 | helps: top pair |
| S6 | K-Q offsuit | `Kh Qd` | `3s 6d 9d 4c Jh` | high card | 0 | does not |
| S7 | paired deuces | `2s 2h` | `2c Kd 9c 6d 5c` | trip deuces | 3 | helps: a deuce, so the pair is a set |
| S8 | paired deuces | `2s 2h` | `3s 6d 9d 4c Jh` | one pair | 1 | does not: no deuce, board unpaired |
| S9 | 8-7 suited | `8s 7s` | `Js Th 9d 2h 4c` | straight | 4 | helps: 7-8-9-T-J |
| S10 | 8-7 suited | `8s 7s` | `3s 6d 9d 4c Jh` | high card | 0 | does not: four to a straight, no draw |
| S11 | 8-7 offsuit | `8h 7d` | `Js Th 9d 2h 4c` | straight | 4 | helps: the same straight, offsuit |
| S12 | 8-7 offsuit | `8h 7d` | `3s 6d 9d 4c Jh` | high card | 0 | does not |
| S13 | 7-2 suited | `7h 2h` | `7d 2s Kc 8d 4h` | two pair | 2 | helps: both hole ranks pair |
| S14 | 7-2 suited | `7h 2h` | `3s 6d 9d 4c Jh` | high card | 0 | does not |
| S15 | 7-2 offsuit | `7c 2d` | `7d 2s Kc 8d 4h` | two pair | 2 | helps: the same two pair, offsuit |
| S16 | 7-2 offsuit | `7c 2d` | `3s 6d 9d 4c Jh` | high card | 0 | does not |

Seven boards, sixteen rows: `common-dry` serves eight of them, and the six helper boards serve the remaining eight (`straight-eight-seven` and `two-pair-seven-deuce` each serve a suited and an offsuit hand, which is the on/off-suit comparison held on one board).

A helper board need not be specific to its hand, and two of these are not: `straight-eight-seven` gives K-Q a straight as well, and `two-pair-seven-deuce` repeats a deuce that a pair of deuces would collide with — which the `duplicate-card` refusal would catch as a deal rather than as a hand. Neither costs anything, because no row plays those hands on those boards, and the data's own card check is what keeps an extension honest (`loaded-deal.md` §3).

## 4. The opposition and the two seatings

**Four folders and one caller**, at the six-seat shape, all of them D-21 baselines: `fold-no-pair-or-face` four times with unpaired non-face hole cards, so they fold before the flop and leave a pot between the model and one opponent, and `always-call` once, which never folds and never raises — so the hand always has one live opponent and always reaches the flop (D-21, `folders.md` §2). The five holdings are seated in ascending index among the seats the model does not hold, so one opponent block serves both seatings.

**Two seatings, both declared, both reported.** `big-blind` is the **primary**: the model (seat 2) posts the big blind and acts **last** before the flop, after the caller has called, so its preflop decision is made with `to_call` 0 and **folding is not legal**; post-flop it acts second, immediately after the caller checks, again with `to_call` 0. Both reported decisions are choices between continuing actions — check/call or one of the four raise bands — and the flop is always reached, so the table is complete for every model by construction.

`opening` is **supplementary**: the model (seat 3) is first to act before the flop facing the big blind, so folding **is** offered, and this is the seating in which D-68's fold-when-legal behaviour shows itself. Two differences from the primary are declared rather than discovered: a hand the model folds ends its participation before the flop and that scenario reports **no flop decision**, which is a result and is written as one; and the big blind (seat 2, a folder) is **not** offered a fold when its bet already equals the maximum, so it checks and stays in unless the model raises — the supplementary seating's flop pot can therefore be three-handed where the primary's is always heads-up.

Why the primary seat is the big blind: with folding illegal, a difference between AA and 72o cannot be the fold/continue switch every recorded census collapsed onto, so the two decisions measure what the model does with a hand rather than whether it is willing to be in the pot at all. Rejected: the opening seat as the only seating, which would report "fold" for AA and 72o alike on the era's own measurement and leave the flop column empty for every model (D-68, D-59).

## 5. The models, and the era rule

**Eighteen containers, six cells × seeds 0–2**, all under `/tmp/reward-scale/checkpoints/`: `norm-masked-flat`, `norm-masked-tokens`, `norm-doubleq-flat`, `norm-doubleq-tokens`, `norm-cf-flat`, `norm-cf-tokens` — the flat and the token arm of `masked` and of two other estimators, the counterfactual included. Every one is on the six-seat shape under `net-chips-normalised`. The report reads each container's own **rule, utility, encoding and shape** and refuses a container that contradicts its directory; it never infers them from the path (ASM-20, `reward-scale.md` §3).

**The era rule: post-D-61 only, and it is enforced rather than assumed.** D-69 records that D-61's bounded embedding is applied at forward time, so every pre-squash token checkpoint is **silently reinterpreted** — `short-tok-s0`, whose own run recorded folding 91.8 % of its decisions, now plays raise-half on 400 of 400. A table that mixed it with `norm-*` would measure the forward pass and not the model (D-69). So the runner admits a container only from the six declared cells, refuses any other path by name, and prints the era it measured beside every row.

The era is a **provenance** claim and no container field carries it, so the report also prints, per model, the D-59 instrument **on its own decisions**: the number of distinct score vectors over the seating's decisions. A model that returns one vector for sixteen different hands is a constant function, and the table then says so instead of reading its actions as strategy (D-59, D-60).

**The decision mode is `off` at every model.** A decision read off the schedule measures the exploration ramp — at the live budget almost the whole sample sits on it — so every reported action is the masked maximum and the tie-break alone, and two seeds of one model can be compared without the ramp between them (D-28, `sizing.md` §4).

## 6. What each row reports, and the tables the report is

For each **model × scenario × seating** the report records the **preflop** decision and, where the hand reached it, the **flop** decision: `street`, `seat`, `on_button`, `hole`, `board`, `hand_class`, `legal`, `action`, `index`, `amount`, and `scores` — the shape's **six** entries in its declared index order, each with the descriptor, whether it was legal, and its value, so an illegal action is reported as masked rather than omitted (`sizing.md` §3).

Three tables, one per declared grouping:

- **T1a — the scenario table, primary seating**: sixteen rows, one column per cell at seed 0, each cell the preflop and the flop action with the scored values. This is the table D-70 asks for: *what does it do with AA on a helpful board, and what does it do with 7-2 offsuit on a dry one*.
- **T1b — the scenario table, supplementary seating**: the same sixteen rows in the `opening` seat, where a fold is offered and a folded hand's flop cell reads *no flop decision — folded preflop*.
- **T2 — the seed table**: one row per model **per seating** (six cells × three seeds), each with the count of distinct score vectors over that seating's decisions and whether its three seeds agree action for action. This is D-68's "nine runs were one policy" asked of this instrument, and it is the difference between a behaviour and a seed.

The report cross-checks itself before it is written: the reported vector must reproduce the reported action under the greedy rule, or the row is refused by name; the row's `hole` must equal the deal's pair for that seat and its `board` must be the deal's own spelling prefix of the length that street has dealt — three on the flop, four on the turn, five on the river, and never the whole prescribed board, which is a different fact (`loaded-deal.md` §4); and `hand_class` must equal §3's column on the flop. It writes `<write root>/report.json` outside the repository and never touches `checkpoints/`, `tables/` or `checkpoints/evidence/` (`battery.md` §2's write-root rule, applied to a script that is not a battery). The runner is `notebooks/loaded-deal-report.py`, named here as the build's deliverable and not present in the tree (§8).

This document states the tables' **shape** and points at the artefact for the numbers, which is the rule for a measured figure (`protocol.md` §2). The numbers are not here because they do not exist yet — §8.

## 7. The answer rule

The question is binary and it is asked of one model at a time, off T1a at seed 0 and re-read at seeds 1–2 (D-70):

- **the hole contrast** — on `common-dry`, AA's decision differs from 72o's, and any other pair of hole sets differs as the table shows. Eight hole sets in one state is what makes this contrast a comparison rather than an inference; the preflop decisions of all sixteen scenarios are also identical in every fact but the hole cards, so the same contrast is read a second time there.
- **the board contrast** — for one hole set, the helper board's decision differs from the `common-dry` decision. Because the board is not dealt before the flop and the seating is fixed, the two scenarios' preflop states are identical, their preflop actions are therefore identical, and their flop decisions differ in **nothing but the board cards** — same pot, same stacks, same history, same legal set. That is the strongest form this comparison can take and it is a property of the declared data, not of the runner.

**The criterion is the chosen descriptor**, and a tie cannot make it: the report compares `action`, and two decisions are different exactly when their descriptors differ, which is observable and independent of whether the tie-break chose either. A **vector** contrast is reported beside it — the two score vectors entry by entry, restricted to the descriptors legal in *both* decisions — and a vector difference with an unchanged choice is reported as **not** card-dependent play, because it cannot change what the model does. The report carries no `tie` flag and must not pretend to: no exploration-off surface reports one, and the greedy pass writes `false` on every decision (`docs/L3/training/greedy.md` §6).

If neither contrast holds for a model, **its play does not depend on its cards**, and that is the answer — reported as the result, not as a null and not softened into "card awareness is limited". If one holds, the pattern is stated: which hole sets separate, which boards move it, and whether the separation is an action change or only a score change. No threshold is invented: the criterion is the **presence** of a difference, per model and per seed.

## 8. The measurement state, and what runs next

**This Rev measured nothing, and says so plainly.** The session that filed the design and the data had **no execution surface** — no shell, no interpreter, no process — so no battery ran, no lint ran, no capture was taken and no report exists. The design (`loaded-deal.md`), the data (`scenarios.json`) and this instrument are filed; the loaded-deal capability is **not built**, so T1a, T1b and T2 have no rows and the task's own PASS condition is unmet. Nothing in the tree was changed except `docs/L1/`.

What must run, in this order, by a seat that has a shell:

1. the twelve module batteries, then `.venv/bin/python -m pytest tests/e2e -q`, which must stay green and may only grow (`battery.md` §2);
2. `node strata/lint/strata-lint.mjs strata`, whose check count and endpoint line are the return's to report;
3. `loaded-deal.md` §6 P1's capture on a pre-change tree — `git archive ea4b1b6 | tar -x -C <dir>` — against this tree, `N of N` leaf paths;
4. the build itself, and then FAM-25;
5. `PYTHONPATH=src .venv/bin/python notebooks/loaded-deal-report.py docs/L1/scenarios.json`, which writes the three tables to its write root.

Until step 5 has run, the honest state of this unit is **designed, not measured**, and the envelope returned with this Rev says so.
