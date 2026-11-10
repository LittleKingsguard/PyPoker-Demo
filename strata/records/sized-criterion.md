# The sized-action build, and the criterion's verdict · 2026-11-07

The build is green; the pinned criterion is not, and the way it fails is not the way the design predicted.

## The build

Six modules, map at 50 endpoints, `game_shapes()` publishing `fixed-limit-20` (default) and
`no-limit-100`. **1,105 cases and 7,093 subtests green** across thirteen batteries, **e2e 298/298**
(268 + FAM-19's 12 + FAM-20's 9, ten older cases extended, none weakened), lint 112 checks green,
shipped artefacts untouched. **The fixed-limit path is byte-identical**: a baseline captured at
`450664e` recomputes to `ALL MATCH` over 51 gated fields in 6 sections, with two additive exemptions the
design mandates for both shapes (the episode's amount facts, the run record's `game`/`greedy`). One real
cost reported rather than absorbed: every run now plays its greedy pass, so a fixed-limit run's wall
clock roughly doubles (21.5 s → 47.5 s) while its curves, chips and parameters are unchanged.

## The criterion: FAIL, by the designed collapse

Five seeds, each judged alone (D-14) — decision count, raise share, the two largest bands, chips:

- seed 0: 3270, 98.5 %, min 100.0 %, largest 98.5 %, **+1.40 ± 0.79** — fails 4
- seed 1: 2992, 97.4 %, min 82.7 %, quarter 17.3 %, **+3.00 ± 1.21** — **passes all seven**
- seed 2: 3226, 98.5 %, min 100.0 %, **+3.18 ± 1.02** — fails 4
- seed 3: 3149, 98.2 %, min 99.9 %, **+2.85 ± 0.82** — fails 4
- seed 4: 3269, 97.9 %, min 100.0 %, **+1.37 ± 1.12** — fails 4

Pooled: 15,906 decisions, 96.8 % of raises at the minimum, largest descriptor 94.9 % of decisions,
**+2.361 ± 0.448 chips/hand**. Conjuncts 1, 2, 3 and 5 hold everywhere; **4** fails on four seeds (no
band beyond the minimum reaches 10 % of raises), and 6 and 7 with it.

## Why this is not the failure the design named

The design called this "the collapse — the raise attractor one level down" and treated it as a bad
agent. It is not: the collapse is onto **raise-minimum**, the only rung the sizing ladder measured
positive (+0.68 fixed, against −5.5 to −8.9), and this learner's **+2.36 ± 0.45** beats every fixed
policy and the tabular probe learner's +0.36. So the criterion fails the best agent this project has
produced, for lacking variety in a game where the variety it asks for is measurably worse. That is mine:
D-24's "variety" is the user's word, but the hard threshold operationalising it is not (D-31).
