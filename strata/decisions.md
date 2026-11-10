# strata — decisions log

The only record of user intent for `PyPoker-Demo`. Append-only: a decision is never edited,
reworded, or annotated. A later decision supersedes an earlier one by naming it; the earlier
row stays exactly as filed.

Format: one section per decision, ≤ 40 lines. `Source` is the user's own words or the exact
option they chose. A row with no user source is not a decision and belongs in the brief as
an `ASM-n`.

---

## D-1 — This project runs under the strata layered workflow

**Status:** ACTIVE · **Date:** 2026-11-05

**Source:** This session is provisioned with the `strata` preset (L0 supervisor, layered
delegation). No user instruction conflicts with it.

**Decision:** The project is developed by the strata workflow: L0 interviews and decides,
L1 designs end-to-end, L2 designs integration, L3 designs modules, L4 implements in one
shot. Every layer return carries the envelope of `strata/envelope.md`. The rules the layers
run under are the procedure files in `strata/` and are adopted by D-10..D-15.

---

## D-2 — The technique ladder's fixed game is heads-up fixed-limit Hold'em

**Status:** ACTIVE · **Date:** 2026-11-05

**Source (user, verbatim):** "Heads-up fixed-limit Hold'em, one game throughout the technique
ladder"

**Decision:** Every rung of the technique ladder plays heads-up fixed-limit Hold'em through
`pokerkit`. The game never changes across the ladder, so a rung-to-rung difference is
attributable to the network, not the game.

Rejected: Leduc only (too simple — most architecture changes would land inside noise), and a
Kuhn/Leduc warm-up followed by limit Hold'em (the game would change mid-ladder).

---

## D-3 — The technique ladder is the primary axis; game expansion is a separate phase

**Status:** ACTIVE · **Date:** 2026-11-05

**Source (user, verbatim):** "Technique ladder on a fixed game; game expansion is a separate
later phase"

**Decision:** Phase 1 walks the technique ladder (encoding, width/depth, density, residual
streaming) on D-2's fixed game. Changing the game is Phase 2+ work (D-4), not a rung.

Rejected: game ladder first, then technique; interleaving game and technique per rung (each
rung would change two things at once, so no rung isolates the technique it is named for).

---

## D-4 — Phase 2 expands the game to heads-up no-limit Hold'em; multi-player is a late bonus

**Status:** ACTIVE · **Date:** 2026-11-05

**Source (user, verbatim):** "Start with 3, then expand to 2 to demonstrate the limits of
model skill transfer. Upgradeable to 4 as a late bonus objective" — where 3 was the
Kuhn/Leduc-then-limit-Hold'em option, 2 heads-up no-limit Hold'em, and 4 multi-player
(3-6) limit Hold'em.

**Decision:** Phase 2 moves the trained techniques to heads-up no-limit Hold'em to show where
skill transfers and where it does not (D-2 governs Phase 1). Multi-player limit Hold'em is a
late bonus objective, not Phase 1 or 2 scope.

---

## D-5 — The deliverable is one notebook per rung, thin, importing repo modules

**Status:** ACTIVE · **Date:** 2026-11-05

**Source (user, verbatim):** "For now, 2. Circle back to 3 as a speculative feature depending
on project progress" — option 2 being one Jupyter notebook per rung — and "Thin notebooks
importing repo modules".

**Decision:** Each rung ships one notebook that imports the project's modules and reads as the
talk's per-rung narrative. Code lives once in the repo, never copied into a notebook. A web UI
(option 3) is speculative and waits on project progress.

Rejected: self-contained notebooks with copied code (copies drift per rung, which defeats the
rung-to-rung comparison).

---

## D-6 — Evidence: curves, self-play against the previous rung, and fixed baselines

**Status:** ACTIVE · **Date:** 2026-11-05

**Source (user, verbatim):** "Show training curves, and then #2" — option 2 being each rung
head-to-head against the previous rung — and "Add fixed baselines: random, always-call, and
oracle (only calls on winning odds)".

**Decision:** Every rung reports (a) its training curves, (b) a head-to-head result against the
previous rung, and (c) results against three fixed, non-learning baselines: random, always-call,
and an oracle that only calls when the pot odds justify it. Seeds are fixed and recorded so a
third party can re-run the comparison.

---

## D-7 — NumPy for the naive rung, PyTorch from the next rung, plus a PyTorch recreation

**Status:** ACTIVE · **Date:** 2026-11-05

**Source (user, verbatim):** "As 3, but include a recreation of the numPy rung in PyTorch to
demonstrate performance speed difference before moving on to deeper implementations" — option 3
being NumPy for the naive rung and PyTorch later.

**Decision:** The naive rung is hand-rolled NumPy so the arithmetic is visible. The remaining
rungs are PyTorch. Before the ladder deepens, the naive rung is recreated in PyTorch to measure
the speed difference on identical work.

---

## D-8 — A GPU exists; live quick runs plus pre-trained checkpoints

**Status:** ACTIVE · **Date:** 2026-11-05

**Source (user, verbatim):** "There should be a GPU, this is probably a sandboxing issue. Plan
for a live test a la 1, but also include the option 3 models as a demonstration of how much
training time matters" — option 1 being a few minutes per rung rerunnable live, option 3 being
long offline training with shipped checkpoints.

**Decision:** The demo supports a live, few-minutes-per-rung run and also ships pre-trained
checkpoints from longer runs, which is how the talk shows that training time matters. Every rung
stays runnable without a GPU so the audience can reproduce it.

---

## D-9 — The multi-round attention objective is deferred to Phase 2

**Status:** ACTIVE · **Date:** 2026-11-05

**Source (user, verbatim):** selected "Defer to a second phase, after the core ladder works".

**Decision:** Multi-round context with attention over prior-round opponent behaviour (bluffing
and conservative/reckless detection) is Phase 2 scope, designed and evidenced on its own terms
after the Phase 1 ladder is green. It is not a Phase 1 rung.

---

## D-10 — Intake gate: speculative proposals get two independent reviews

**Status:** ACTIVE · **Date:** 2026-11-05

**Source:** Adopted from the strata contract under D-1; procedure in `strata/proposals.md`.

**Decision:** A speculative proposal or a major expansion runs `role_l0_validity` (can it be
built as stated, does it solve the stated problem and only that, what does it need that does not
exist yet) and `role_l0_critique` (externalities, cost and scale, paradigm violations, over-fit
hazard) in parallel and without either seeing the other's findings. L0 dispositions findings
into a decision row. Neither review writes a design.

---

## D-11 — The examiner validates the battery before the code, and never patches

**Status:** ACTIVE · **Date:** 2026-11-05

**Source:** Adopted from the strata contract under D-1; procedure in `strata/examiner.md`.

**Decision:** An examiner establishes first that the test is real and satisfiable, then examines
the code. A bad test is a finding against the test writer, never the implementer. An examiner
emits root cause, owning artifact, failing test and routing layer — never a snippet, diff,
signature or ordered fix list.

---

## D-12 — Failure routing: adjudication is a failure, and L4 bubbles to L2

**Status:** ACTIVE · **Date:** 2026-11-05

**Source:** Adopted from the strata contract under D-1; procedures in `strata/examiner.md` and
`strata/rebuild.md`.

**Decision:** A lower layer that asks for adjudication is answered above and counted as a
failure, never treated as a pause. An L4 that cannot drive green on a non-`PASS` verdict routes
to L2, because L4 owns no design and L3 authored the design under judgement. Repeat failure at
the measured threshold escalates as a rebuild recommendation.

---

## D-13 — Module isolation: one module per agent, writes confined to its subtree

**Status:** ACTIVE · **Date:** 2026-11-05

**Source:** Adopted from the strata contract under D-1; procedure in `strata/modules.md`.

**Decision:** A module agent receives exactly one module's docs, source and tests plus that
module's L2 interface document. Isolation is prompt-and-lint enforced, not sandbox-enforced:
`strata-lint` checks that every written path lies inside the module's declared subtree, and
`modules.json` is the declaration.

---

## D-14 — No unit is reported ready without a blind documentation walkthrough

**Status:** ACTIVE · **Date:** 2026-11-05

**Source:** Adopted from the strata contract under D-1; procedure in `strata/walkthrough.md`.

**Decision:** Before L0 reports a unit ready, a subagent that has never seen the code attempts
a scenario set using only the documentation and the built surface, citing for every step the doc
section that told it what to do. A non-`PASS` verdict still reaches the user, as a finding with
a loop recommendation — never as readiness.

---

## D-15 — Research establishes facts with sources; a package is an option, not a rule

**Status:** ACTIVE · **Date:** 2026-11-05

**Source:** Adopted from the strata contract under D-1; procedure in `strata/research.md`.

**Decision:** Intake research establishes what is true outside the project, with a source for
every claim, an `unsourced` label where none exists, and no design commitment. Any package or
technology it names is recorded with the acceptance predicate it satisfies, so a substitute is
judged against the predicate rather than the name.

---

## D-16 — The opponent is a bounded round-robin league plus the three oracles

**Status:** ACTIVE · **Date:** 2026-11-05

**Source (user, verbatim):** "The opponent will be round-robin matches against multiple versions
of itself + the three oracles", followed by the four options chosen: "Both: the agent learns
against the pool, and the league table is also the evaluation"; "Bounded rolling pool: keep the
last M versions plus the baselines"; "Fit a rating (Elo / Bradley-Terry) with confidence
intervals"; "Both: a small live table in minutes, and the full table precomputed offline".

**Decision:** This supersedes D-6's "head-to-head result against the previous rung" clause. D-6's
other clauses — curves, the three fixed baselines, fixed and recorded seeds — stay in force, and
D-6 itself is not reworded.

- A version is a checkpoint of a run, and the pool is a bounded rolling window of the last M of
  them (D-16).
- The agent trains against that pool, and the same pool is its evaluation opponent.
- Evidence is a pairwise matrix plus a fitted rating (Elo or Bradley-Terry) with confidence
  intervals; the matrix is reported because poker payoffs need not be transitive.
- A small table is produced live in minutes; the full table is precomputed offline and shipped
  (D-8).
- Because training now varies with the pool, both arms of a two-variant rung (R4, R5, R6) train
  and evaluate against an identical frozen pool, so a rung still changes one thing (D-3).

**Intake gate (D-10):** validity returned `FAIL` (L-F1 membership undefined, L-F2 no lineage,
L-F4/L-F5 cost O(K²), L-F6/L-F7 self-play cannot show absolute strength so the baselines are the
only fixed anchor, L-F8 budget parity, L-F9 one global `random` stream forces sequential play,
L-F10/F11 comparability and register); critique returned `ADJUDICATION` (K1..K21). The adjudicated
unknowns — scope, membership, aggregation — are answered by the four user options above. The
remaining findings become design constraints for L1: the baselines sit inside the table at the
same hand count as every league cell, matches run sequentially, and no claim of poker skill is
made beyond the table's named members.

**Consequences:** M, hands per pairing and match counts are L1's parameters (`ASM-13`); checkpoint
retention follows the pool policy and supersedes the lean shipping rule of ASM-5.

---

## D-17 — GPU live-speed runs: an agent checks feasibility first, and the user gets instructions

**Status:** ACTIVE · **Date:** 2026-11-06

**Source (user, verbatim):** "When the PyTorch implementation is ready for the live-speed tests,
check if it can be run on the GPU by agent and if not, provide instructions for user"

**Decision:** When the PyTorch rung (R2, D-7) is ready for its live-speed measurement, the
workflow must establish first whether a delegated agent can run that measurement on the GPU. The
check is empirical — a delegated agent attempts it and reports what actually happens — not an
assumption either way.

- If an agent can run it on the GPU: the agent runs it, and the evidence records the device.
- If an agent cannot: the agent does not pretend otherwise. The project ships user-facing
  instructions for running the same measurement on the GPU outside the development sandbox, in
  `docs/L1/getting-started.md` and the root `README.md`, with the exact commands and the expected
  wall clock.
- Either way the measurement produces the same evidence shape, and every run record carries its
  device, so a CPU number and a GPU number are never confused with each other (D-6, D-8).

Rejected: assuming CPU-only and never offering the GPU path, which would waste hardware the user
has confirmed is present; and assuming the agent can reach the GPU, which measurement has already
contradicted.

---

## D-18 — The pool holds models trained under different estimators

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Change pool to include multiple training models using different
estimators" — following the diagnosis that a pool of one estimator's own descendants produces a
raise-maniac which loses to `always-call` (`strata/records/r2-plateau-diagnosis.md`).

**Decision:** This supersedes D-16's pool-composition clause. The league pool is deliberately
**heterogeneous**: it holds models trained under different estimators, not only the rung's own
lineage and the three pinned baselines.

- The **learner** of a rung keeps that rung's declared rule, so ASM-7's one-rule-for-the-ladder
  fairness still holds for the thing being measured (D-3).
- The **opponents** vary in estimator on purpose. A population descended from one estimator is a
  monoculture: it rewards whatever that estimator's bias favours — measured, always-raise — and a
  policy optimal inside it is weak against a calling station.
- Alternative estimators therefore have to exist as trainable pool members (Monte-Carlo or n-step
  returns and Double Q-learning are the named candidates; the set is not fixed here).
- The pool record carries each member's estimator, so a table can say which population a rating was
  fitted over, and so a member is never confused with one from a different rule.
- Cost grows with membership under the existing arithmetic: K rises, cells rise as K(K−1)/2, and the
  live-table budget of D-16 is the cap that decides how many members may be admitted (ASM-14).

**Gate (D-10):** this changes an existing decision row, so it goes to `role_l0_validity` and
`role_l0_critique` before any design work. Their findings are dispositioned here or in a following
row — the pool's size, the estimator set and the cost share are the questions they will be asked.

---

## D-19 — The estimator is a parameter, and every estimator trains

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Fix the learning rule constant so that multiple estimators work. With
the multiple estimators in play, all of them are training targets, not just opponents for one
training"

**Decision:** This extends D-18 and supersedes the single-rule clause of the ladder's fairness rule.

- `LEARNING_RULE` stops being a module constant and becomes a catalogue with more than one member,
  and the learner spec carries the rule it learns under.
- A configuration may declare its variants with **different** rules, and **every variant it declares
  is trained** — each produces its own curves, snapshots, final checkpoint and pool membership. A
  model trained under one rule is not merely borrowed opposition for another's run.
- A pool member therefore carries its rule, and the pool id must be able to certify it, so a table
  can say which population a rating was fitted over.
- The ladder's fairness rule is restated accordingly: what a rung holds constant is the **set** of
  rules and their declarations, not a single rule. Two arms of a pair still train against one frozen
  pool, and two rungs are still compared on one game and one seed set (D-3, D-16).
- This re-baselines the shipped artifacts: R1's live evidence, R2's deep run and the full table were
  all measured under the old single-rule arrangement.

**Gate (D-10):** D-18's intake review already names the blockers this decision must clear — no
second estimator exists to train (V-F1), `learning_rule` is carried but never honoured (V-F2), the
member record has no rule field and the pool id digests ids alone (V-F3), one lineage chain is
extendable so a multi-family pool cannot roll (V-F4), and M bounds total versions (V-F5) — plus the
critique's questions of cost, eviction and who decides membership. A design that departs from those
findings needs its own gate; one that follows them needs only the findings cited.

---

## D-20 — A utility axis: reward progress in the squared stack shortfall

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Add a new model with a changed loss function so that it measures net
progress towards winning nonlinearly, ex. delta of (total of stacks - current stack)^2. This will
make the loss asymmetric between losses and wins of the same magnitude, discouraging aggressive
play."

**Decision:** The terminal reward becomes selectable per variant, as the learning rule already is
(D-19). The existing `net-chips` utility stays (ASM-12); a second utility scores progress in the
square of the stack's shortfall from all the chips in play:

- `U(s) = (T − s)²`, where `T` is the total chips in play and `s` the seat's stack;
- reward `r = (U(s_before) − U(s_after)) / U(s_0)`, delivered at the terminal decision only, with no
  intermediate term and no shaping — the same delivery rule as ASM-12;
- normalising by `U(s_0)` keeps the objective on the scale the learner was tuned for: a ±2-chip pair
  scores **+0.190 / −0.210**, and an all-in scores **+1.000 / −3.000**, so a loss of a given size is
  always penalised more than a win of the same size and all-in aggression is penalised threefold.

**What it is, and is not.** It changes what the learner optimises, not the game (D-2). It cannot
create EV where the game has none: the measured coin-flip (`r2-plateau-diagnosis.md`) means call and
raise are equally good, so this utility does not make play "better" — it makes the equal-EV choice
*prefer the cheaper variance*, which is exactly the pathology it was proposed for (always-raise at
±20 over always-call at ±2).

**Constraint that binds the evidence.** The league keeps measuring the game in its own currency —
hands won and chips per hand — so a variant trained on one utility and judged beside one trained on
another is not a like-for-like comparison. Every record, member and table must name the utility a
model was trained under, and a report must state both, or the ladder would silently compare models
that were asked different questions (D-6, D-16).

---

## D-21 — Three simple folding baselines join the catalogue

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Add additional, simpler folding strategies
- folds if pocket cards do not contain a pair or face card
- folds if hand does not contain a pair or better on the flop
- folds if bet is greater than half its stack at start of hand"

**Decision:** The baseline catalogue grows from three fixed rules to six. The three new ones are
simple, deterministic, non-learning folders, each with one pinned reading:

- `fold-no-pair-or-face` — preflop only: fold when the hole cards are unpaired **and** neither card is
  a face card. "Face card" is pinned as **J, Q, K or A**; rejected: J/Q/K alone, which leaves ace-high
  hands folding and is a one-line change if the talk wants it.
- `fold-no-pair-or-better` — from the flop onward: fold when the best five-card hand of hole plus
  board is **worse than a pair** (high card only). Before the flop it calls.
- `fold-large-bet` — fold when `to_call` exceeds half the starting stack (`> 10 chips` at the
  declared 20), at any street; otherwise it calls.

Each calls (check/calls) in every case it does not fold, and none of them raises. The three original
baselines stay exactly as they are and stay the rating's anchor: the Bradley-Terry fit is still
zeroed on **their** mean, so a shipped rating stays comparable with every one already recorded. The
three new rules are pool members and table rows when a configuration declares them; they do not
silently join the anchor.

**Why this is the change that matters.** The measured degeneracy is that no bet can win a pot without
showdown, because `always-call` and the oracle almost never fold (`multiway-probe.md`). Three folders
give aggression something to win, which is what makes bluffing, position and bet-sizing learnable —
and it is the precondition for the Phase 2 opponent-modelling objective (D-9) being more than a
diagram.

**Consequences the design must carry.** `fold-no-pair-or-better` needs a hand-strength fact the readout
does not expose, so either the readout gains one or `features` gains an evaluator — `agents` must not
import `pokerkit` (D-13). The baseline count changes pool membership and so K and the K(K−1)/2 cells
(ASM-14); the e2e baseline family asserts three and must be extended, never weakened; and the shipped
artefacts, measured over a three-baseline pool, are not re-baselined by this row.

---

## D-22 — A six-player table drawn from the pool

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Run it as a six-player table, drawing from the pool"

**Decision:** The unit's game gains a multi-seat configuration. A run may seat **six players** — one
learner and five opponents drawn from the pool — instead of the heads-up table of D-2. This supersedes
D-2's "heads-up fixed-limit Hold'em" as the *only* seat count; heads-up does not disappear, it becomes
the smaller of two declared shapes, and every artefact already shipped remains a heads-up measurement.

- The opponents are pool members: the pinned baselines (D-6) and any declared folders (D-21), plus
  version members where a configuration declares them. Five opponents are drawn per hand, without
  replacement, so a seat never faces itself.
- Seats rotate: the learner must not be locked to one position, since position is a real and unequal
  advantage in a multi-way pot.
- The league's instrument changes shape with the game: a pairwise matrix stays the head-to-head
  record, but a six-way hand produces a **placement**, not a pair, so the rating needs a
  permutation model (Plackett-Luce or equivalent) beside Bradley-Terry, and the report must say which
  it used.
- The measurement that motivated this — a two-player game being a coin flip for non-folding strategies
  — was probed and did **not** resolve on player count alone (`multiway-probe.md`); what six seats
  genuinely add is *more folding opponents simultaneously*, which is what the user asked for.

**Cost, before it is spent.** The oracle's equity becomes N-way and one 6-way call at 60 samples
already costs 0.12 s; the encoding's two stack slots and two seat flags grow with the table; every
table is K(K−1)/2 cells today and N-way placements tomorrow; 268 e2e cases assume two seats; and every
artefact measured under D-2 stays a heads-up measurement, so nothing is comparable across the change
without being re-measured. A run at the shipped budget is hours per configuration.

**Gate (D-10):** this changes a decision row and adds a declared game shape, so it goes to
`role_l0_validity` and `role_l0_critique` before design work. Their findings are dispositioned into
this row or a following one.

---

## D-23 — Six-player seating is not adopted; the probe refuted its premise

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** the disposition option chosen for D-22 — "Settle the hypothesis in the
probe harness first".

**Decision:** D-22's six-seat shape is **not adopted** for Phase 1. Heads-up remains the game of D-2,
and every shipped artefact keeps its meaning. The probe settled the premise, and it failed:

- aggression against a folder is **worse** than against a caller heads-up (−0.29 / −0.91 chips/hand in
  two seed blocks), because a folder only puts money in ahead while a bluff earns nothing from it;
- six seats does not improve that (−1.89 ± 1.97 against five folders), since a bluff must buy five
  folds, and the payoff does not cover it;
- six seats widens variance until nothing resolves: identical policies in different seats measured
  **+1.96 and −2.63** chips/hand, so a 0.3-chip edge needs ≈40,000 hands per cell.

Rejected: building the six-seat shape and re-measuring after (the gate's FAIL stands on its own —
encodings refuse three seats, equity is two-handed, the matrix is pairwise, and all 18 checkpoints
carry the two-seat encoding); and taking the seats as a Phase 2 shape without first testing the
premise, which this probe has now done.

**What this leaves.** The untried lever with a mechanism behind it is the **game's structure**, not the
table's size: deeper stacks so bets have leverage, or no-limit where a bet can threaten a whole stack
(D-4). That is where the next gated change should go (D-6).

---

## D-24 — No-limit as a second declared game shape, with action variety as its test

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Proceed and if it shows positive outcomes for fold/raise + call variety
start overnight training run"

**Decision:** Heads-up **no-limit** Hold'em becomes a declared second game shape beside D-2's
fixed-limit one, which stays Phase 1's evidence and is not re-measured. The probe measured why it is
worth having: the same bettor against the same folder scores **−6.58 ± 4.66** at one pot and
**−0.80 ± 1.52** at half a pot, a size-dependent difference that clears its interval where the
fixed-limit comparison was inside noise (`nolimit-probe.md`). No-limit is the first configuration in
this project in which a decision has a measurable price.

- **The test is variety, not a curve.** The shape is judged successful when a trained learner's play
  shows **fold, raise and check-call all materially present and situation-dependent** — not the single
  mode every fixed-limit run collapsed into. A learner stuck at ~90 % one action fails the test
  whether or not its chips move.
- **If it passes, an overnight deep run follows** at the shipped budget; if it fails, the failure is
  recorded and the run is not spent.
- The **sizing abstraction is a design decision to be recorded with its rejected alternative**: a
  discrete ladder of bet sizes against a regression head, with the observation's treatment of size
  decided explicitly rather than inherited.
- Two seats stay: the matrix, the Bradley-Terry rating and the pool keep their shapes, so every
  Phase 1 artefact stays comparable within its own game and is never compared across the two.

Rejected: promoting no-limit by silently changing D-2's game (it would orphan every shipped figure);
and building a continuous bet-size head first (the action space, the encoding and the learner's output
would all change at once, and D-3 has no way to attribute the result).

**Gate (D-10):** a new declared shape and a Phase 2 scope promotion, so it goes to `role_l0_validity`
and `role_l0_critique` before design work; their findings are dispositioned here or in a following row.

---

## D-25 — No-limit is not built; the probe's gradient is retracted

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Proceed and if it shows positive outcomes for fold/raise + call variety
start overnight training run" — a conditional.

**Disposition:** The condition is **not met**, so the overnight run is not started and D-24's shape is
not built.

- The gate returned `FAIL` (validity) and `ADJUDICATION` (critique). Validity's root cause: the change
  is judged by a criterion with no pinned observable, threshold, opponent, seed set or stratum, on a
  shape whose sized action **no record, encoder, vocabulary or learner can carry** (the readout's
  eleven facts have no legal amounts; `raise` means the minimum completion, unique only in
  fixed-limit; a learner is three-valued by contract; a transition's action is an index and an episode
  decision "carries no amount"; history is 24 slots derived from the fixed-limit cap; the amount
  divisors assume a 40-chip game).
- The probe's headline is **retracted**: the two size cells ran on the same deals and their
  non-overlap was read as significance. Paired on the same deals over 600 hands the difference is
  **−0.907 ± 3.026** chips/hand, with only 93 of 600 hands differing at all. There is no resolvable
  sizing gradient to justify hours.
- The criterion itself was also wrong as written: a three-descriptor census scores a minimum raise and
  a pot bet identically, so it cannot test sizing at all; and the ~90 % threshold it implied is
  straddled by recorded results (87 % read as failure, 74 % read as "not selective play").

**What it would take to revisit:** a fixed instrument first — per-hand paired deltas kept and
reported, several seeds and seat blocks, more than two sizes, a learner rather than a fixed policy in
the bettor's seat, and an acceptance threshold with a metric and sample size named before the run —
plus an L0 decision on the sized action's path through the vocabulary, record and encoding, which is a
50-endpoint surface change. Rejected: building the shape and reading the census afterwards, which is
how this record's error would repeat at the level of a twelve-hour run (D-3, D-6, D-10).

---

## D-26 — The no-limit sizing gradient is confirmed; the build is justified on a pinned criterion

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Proceed" — proceeding with the corrected instrument D-25 required.

**Decision:** D-25's retraction is **superseded**. The corrected paired measurement — four sizes,
1,000 paired hands, seats alternating — finds a resolvable, monotone price for bet size against a
folding opponent: **¼ pot beats ½ pot by +2.03 ± 0.62** chips/hand, and **a full pot loses 7.28 ± 2.21**
against ½ pot, with nothing resolvable against a caller. Two of my own errors produced the earlier
figures (independent intervals on paired data; a sign bug that negated half the paired differences),
both recorded in `nolimit-probe.md` rather than quietly fixed.

So the no-limit shape has the one thing Phase 1's game never had: **a decision with a measured price**.
The build is therefore justified — on conditions, because D-24's FAIL stands until they are met:

- **A pinned acceptance criterion, fixed before any run**: the metric (an amount-conditioned action
  distribution, not a three-descriptor census that cannot see size), the seed set, the sample size,
  the threshold, and who computes the verdict. Variety must be measurable from a recorded amount,
  which means the sized action has to reach the transition record and the report.
- **The sized-action path decided as a surface change**: the vocabulary, the transition record, the
  encoding's treatment of size, and the learner's head — a 50-endpoint decision, taken on its merits
  with its rejected alternative, not as a side effect of a demo.
- **The pool must carry folders into the no-limit run**, since the gradient is folder-borne; a
  baselines-only pool would hold no opponent the price applies to.
- The overnight run is authorised **after** a live-budget check shows the pinned criterion met, and
  not before (D-10, D-6).

---

## D-27 — The no-limit shape's acceptance criterion, pinned before any run

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Continue. If everything's green proceed to the overnight run without
asking for permission, it's 2AM"

**Decision:** The sized-action shape is built **with a discrete sizing ladder**, and the criterion that
authorises the overnight run is fixed here, before the build and before any number exists:

- **The game**: heads-up no-limit Hold'em, blinds 1/2, **100-chip starting stacks**, one blind level.
  Rejected: keeping D-2's 20 chips, where one pot-sized bet is all-in and a size has no room to matter.
- **The vocabulary**: `fold`, `check-call`, and raises at **½ pot, 1 pot, all-in** (plus the minimum
  legal completion where that is the only legal raise), each masked by legality so an illegal size is
  never offered. Rejected: a continuous bet-size regression head, which changes the head's type, breaks
  ASM-10's matched-parameter comparison with the fixed-limit rungs, and cannot be attributed by D-3.
- **The metric**: an **amount-conditioned action census** computed from the run record's own episode
  decisions, which therefore requires the record to carry the chosen amount. A three-descriptor census
  scores a minimum raise and a pot bet alike and cannot pass judgement here (D-25).
- **The sample**: five seeds (0–4) × 1,000 hands, so ≥5,000 hands and ≥10,000 decisions.
- **PASS** requires all three: every class in {fold, check-call, raise} is **≥3 %** of decisions; **no
  single class exceeds 60 %**; and **at least two distinct raise sizes** each reach 3 %. Anything else
  is FAIL, including a run whose chips improve.
- **The verdict is computed by a script from the artefacts**, never read by eye, and is recorded either
  way. A PASS authorises the overnight run at the shipped budget; a FAIL does not, and the record says
  why (D-6, D-10, D-25).

**Gate (D-10):** a new game shape plus a surface change (vocabulary, record, encoding, learner head), so
it goes to `role_l0_validity` and `role_l0_critique` before design. Their findings are dispositioned in
this row or a following one; the criterion above is not theirs to move.

---

## D-28 — D-27's criterion is withdrawn; the sized-action build is blocked

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Continue. If everything's green proceed to the overnight run without
asking for permission, it's 2AM" — a conditional, and the condition is not met.

**Disposition:** The gate returned `FAIL` (validity) and `ADJUDICATION` (critique). D-27's criterion is
**withdrawn** and no build or run is authorised. Two of its defects are mine and fatal:

1. **The criterion is satisfiable without learning.** Exploration is uniform over the legal mask from
   ε = 1.0, annealed to 0.05 only after 2,000 decisions; at 1,000 hands per seed almost the whole
   sample sits on that ramp, so every action class and every size clears a 3 % threshold **by
   construction** from forced exploration. A census of the behaviour policy cannot distinguish a
   learner that found a size from one that learned nothing. The metric must read the **greedy** policy,
   with exploration off, or it measures the exploration schedule.
2. **The sizing ladder is wrong in two ways.** Its rungs were ½ pot, 1 pot and all-in — the probe's
   measured winner (a small bet, +0.33 ± 0.45) is absent, so "two distinct sizes ≥3 %" is satisfiable
   only with the sizes that measured negative. Worse, the probe's own fractions collapse under the
   minimum-raise clamp: at a 3-chip pot, int(3 × ¼) is below the minimum completion, so "¼ pot" and
   "½ pot" both bet the minimum raise most of the time and differ only once the pot is large. The
   ladder must be defined in **legal amounts**, not nominal pot fractions.

Also recorded from the gate, independent of the above: the sized action has **no path through any
declared artefact** — no no-limit `game_config` row, no legal-amount fact (the readout's eleventh facts
are closed, and `pot + stacks == 40` is an asserted invariant), a three-index vocabulary that **an
existing e2e case forbids widening**, no chosen amount in the episode or transition record, **no
episode decisions in the run record at all**, and a three-wide output head hard-coded in both backends.
And this row names what D-27 should have named: it supersedes D-2's single game, D-3's "changing the
game is Phase 2+", D-4's Phase 2 placement and ASM-6's rejected 100-chip alternative — otherwise they
stay ACTIVE and false, which the log's own rule forbids.

**To revisit**, in this order: pin the ladder in legal amounts and measure it *paired and greedy*;
make the metric read a greedy policy with a per-seed breakdown, since the seed lottery dominates
(`attractor-sweep.md`); decide the sized action's full artefact path (vocabulary, record, encoding,
head, endpoint count); and only then authorise a build — with the overnight run still gated on a
live-budget pass (D-6, D-10, D-25, D-26).
