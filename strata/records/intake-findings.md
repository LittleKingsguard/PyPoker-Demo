# PyPoker-Demo — intake findings (validity + critique) · 2026-11-05

Two independent reviews of the project proposal, before any design (D-10). Verdicts: validity
`FAIL` (blocking), critique `PASS` (no blocking finding). Dispositions are the decision rows
named per row; the reviews are archived by replacement, never appended (D-10).

| # | Finding (condensed) | Disposition |
|---|---|---|
| V-F1 | Engine is not a training environment: no reset/step loop, observation, reward, RNG control, opponent | Accepted. `pokerkit` ships none of these (research record); the project builds them. L1 must design them |
| V-F2 | The game is never named, and it decides learnability | Closed by user: D-2 (heads-up fixed-limit Hold'em), D-4 (Phase 2 no-limit) |
| V-F3 | Invokes third-tier vocabulary (bluff detection, opponent modelling) on first-tier signal | Accepted; D-9 defers it, D-6 fixes what Phase 1 may claim |
| V-F4 | No algorithm and no opponent named | Partly closed: D-6 fixes the opponents/baselines; the algorithm is `ASM-3`, an L1 decision |
| V-F5 | The ladder varies the network, not the learning problem; the transfer is asserted | Accepted. The ladder is now explicitly an architecture/representation ladder on one fixed game (D-3) |
| V-F6 | Rungs are not comparable artifacts: no fixed opponent, seeds, sample size, metric | Closed by D-6 (fixed seeds, recorded, head-to-head plus baselines) |
| V-F7 | R1 and R3 may be near-identical: a 52-slot embedding is a reparameterisation of 52 flat inputs | Accepted as a real risk for L1: R3 must be specified so it changes more than the parameterisation |
| V-F8 | Reward and baseline unstated | Closed by D-6: three fixed baselines |
| V-F9 | No seed contract, no wall-clock budget, live vs pre-recorded unstated | Closed by D-6 (seeds) and D-8 (live quick runs plus shipped checkpoints) |
| V-F10 | Bluff labels are sparse and mostly unobservable (uncalled bluffs, folds) | Accepted; becomes Phase 2 design input (D-9), not Phase 1 work |
| V-F11 | Style detection is circular when opponents are scripted | Accepted; Phase 2 must name its signal before claiming detection (D-9) |
| V-F12 | Attention weights are not evidence of detection | Accepted; Phase 2 must state a falsifiable measure (D-9) |
| V-F13 | No success criterion anywhere; "deeper" measures the codebase | Closed by D-6: curves, head-to-head against the previous rung, and baselines with fixed seeds |
| V-F14 | Everything the proposal needs does not exist yet | Accepted; it is the project's work, sequenced by L1 |
| C-C1 | Per-rung compute is unbudgeted | Accepted; L1 must state a per-rung budget (D-8) |
| C-C2 | A pure-Python engine dominates wall-clock in self-play | Accepted as a measured-risk item; L1 sizes the hand count against it |
| C-C3 | "Demo run" ambiguous: live training vs checkpoint inference have opposite costs | Closed by D-8: both, deliberately |
| C-C4 | Checkpoint storage and distribution unaddressed | Accepted; `ASM-5` records a lean checkpoint policy for L1 to honour |
| C-C5 | Audience rerun on a laptop or conference network is fragile | Partly closed by D-8 (every rung runs without a GPU); dependency pinning is L1's |
| C-C6 | Licence surface unverified | Closed by research: `pokerkit` is MIT (research record); PyTorch, NumPy, matplotlib are permissive |
| C-C7 | Python and platform assumptions implicit; engine seeding unmentioned | Closed by `ASM-2` (global `random` seeding) and the environment rows in the brief |
| C-C8 | Naming a technique is not demonstrating it | Accepted; D-6 forbids a rung claiming benefit on a curve alone, and the talk claims only what a rung measured |
| C-C9 | "Residual streaming" is a borrowed label | Accepted; L1 must define what the rung actually computes before it is built |
| C-C10 | Bluff detection is the weakest evidential claim | Accepted; deferred by D-9 with Phase 2 evidence rules |
| C-C11 | The ladder is a narrative, not a measurement | Accepted; D-6's fixed seeds and baselines are the countermeasure |
| C-C12 | No multi-seed variance, matched budgets, or independent evaluation protocol | Partly closed by D-6; matched budgets are L1's to specify per rung |
| C-C13 | Wide-vs-deep and dense-vs-sparse are confounded at unequal budgets | Accepted; L1 must fix matched parameter and sample budgets per comparison (D-3) |
| C-C14 | No fallback if a live run fails to converge or overruns | Closed by D-8: shipped checkpoints are the fallback |
| C-C15 | Preparation cost is unowned | Accepted; it is this project's work, not hidden |
| C-C16 | The bonus rung is the most expensive and least supportable | Accepted; deferred by D-9 |
