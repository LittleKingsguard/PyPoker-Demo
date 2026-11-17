# Correction: the project does have card-sensitive opponents — the scripted folders · measured 2026-11-08

D-111's falsification was scoped to the **checkpoint** league members, and I reported it as "the opponents are
card-invariant", full stop. That was too strong: the project's **scripted baselines are card-reading policies**, and
the instrument shows it. Fixed dry board, the D-70 hole set, opening seat (D-14).

| policy | distinct decisions over AA / KQs / 22 / 87s / 72o | what it does |
|---|---|---|
| **`fold-no-pair-or-face`** | **2 / 5** | folds **87s and 72o** (unpaired, no J-Q-K-A), calls AA, KQs, 22 |
| **`oracle`** | **2 / 5** | calls **AA**, folds KQs, 22, 87s, 72o |
| `fold-no-pair-or-better` | 1 / 5 **preflop** | by design: it folds a high-card-only hand **from the flop**, never preflop |
| `fold-large-bet` | 1 / 5 **preflop** | by design: it folds when the call exceeds half the starting stack |
| *all four checkpoint members* | *1 / 5 each* | card-invariant (D-111) |

So the population is **mixed**, and both kinds are in the pool the product runs against: three scripted folders
(`baselines: fold-no-pair-or-face, fold-no-pair-or-better, fold-large-bet`) beside checkpoint members.

## What this does to the proposal's ceiling

**A history→strength estimator has a non-zero ceiling after all** — against `fold-no-pair-or-face` and `oracle` their
action genuinely depends on their holding (87s and 72o fold; AA calls), so their history *does* carry information about
their cards. D-111's "the target is absent" is true of the checkpoint league only.

## But the correction does not unfreeze it

The card-sensitive members are **transparent**: their rule is published source (`baselines.py:477-487`, `FACE_RANKS =
JQKA`, fold unpaired preflop), so a model that predicts them has learned **an explicit rule**, not a read. That is a
legitimate feasibility demonstration and a **worthless bluff detector** — the whole point of the Phase 2 objective (D-9)
is opponents whose policy is *not* known to the learner. The critique's blockers also stand unchanged: the history
block carries three action kinds with no seat or amount, there is no cross-hand carrier, and removing 98 pad-heavy
tokens ships D-110's mask effect (K7/K14).

**So the corrected sentence is:** *the project has one card-sensitive, transparent opponent family and one card-blind,
opaque one — and the proposal is testable on the first but only interesting on the second.*
