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

---

## D-29 — The sized-action path goes to design; the run stays gated

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Then continue. This is a looping preset for a reason"

**Disposition of the gate:** both reviews returned red (`FAIL` validity, `ADJUDICATION` critique) and
their findings are accepted, including three against my own work: the ladder record's non-monotonicity
claim was false (1× −8.89, 2× −7.77, 4× and all-in −5.54 is monotone above the minimum), the rungs'
amount sets **overlap** so an amount-conditioned census cannot attribute a recorded amount, and the
"variety" criterion ran opposite to the measurement until a learner was actually put in the seat.

**New evidence that changes the disposition:** a tabular Q-learner in the bettor's seat, trained 20,000
probe hands and evaluated greedily, reaches **+0.36 ± 0.20** chips/hand against the folder — within 0.3
of the best fixed policy, +0.68 ± 0.21 — with a **mixed** distribution of call 40 %, min-raise 32 %,
1× 27 %, and zero folds and zero over-bets. So the price is learnable quickly, variety is attainable,
and the fear that learning would collapse play onto one size (critique F5) is not borne out
(`sized-learner.md`).

**Decision:** the sized-action **artefact path is authorised for design only** (L1), with the gate's
findings as its requirement list — a declared game shape beside D-2's; run-level retention of the
episode decisions a census must read; an exploration-off evaluation surface; a shape-dependent
vocabulary with **non-overlapping** amount rungs; the chosen amount in the record and attributable to
one descriptor; the encoding seeing size only where the shape's price requires it; the head width a
declared per-shape property; the 18 checkpoints, the evidence bundle and the full table staying
fixed-limit and never compared across shapes; and D-2, D-3, D-4 and ASM-6 **superseded by name**.

**Still gated:** no overnight run until an acceptance criterion is pinned (amount-attributable, greedy,
per-seed) and a live-budget pass meets it (D-6, D-28).

---

## D-30 — The shape design is accepted; the supersessions are filed and the build is authorised

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Then continue. This is a looping preset for a reason" — continuing the
loop into the build the design enables.

**Decision:** L1's design of the sized-action path is accepted (`docs/L1/shapes.md`, `docs/L1/sizing.md`)
and the build is authorised against it, with the overnight run still gated on its criterion.

- **Supersessions filed, by name, as the register requires:** **D-2** — the project no longer declares
  one game; two shapes exist and the fixed-limit one remains the default and Phase 1's evidence.
  **D-3** — a second shape is designed inside Phase 1 but is still not a rung; no rung's game changes.
  **D-4** — no-limit's placement is now gated on the pinned criterion rather than on a phase boundary.
  **ASM-6** — its parameterisation survives as the default shape's row and stops being *the* game.
- **Declarations:** `modules.json`'s engine row moves 9 → 10 endpoints, and its harness ceiling with it.
- **The build** proceeds per the design: shape as data with optional arguments defaulting to today's
  values; four raise descriptors partitioning `[m, A]` so every amount attributes to exactly one; the
  index order set to the measured price order **worst first** so a tie can never look like a
  preference, with a `tie` flag the criterion can exclude; one greedy evaluation pass retained per
  variant per seed and **no training decisions retained**; the normalisers declared per shape; the head
  and container made shape-aware with the default shape still writing format 3, so the 18 shipped
  containers are untouched; and the battery extended, never weakened, for the second shape.
- **The criterion stands as pinned in the design**: five seeds, each judged alone, seven conjuncts,
  chips reported and never thresholded, and a FAIL named for the shover, the collapse, the tie artefact
  and the exploration artefact. A PASS authorises the overnight run; nothing else does (D-6, D-28).

This row does not supersede D-29; it is what D-29 authorised.

---

## D-31 — The criterion FAILS; the variety test is in tension with the game's own price

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Proceed and if it shows positive outcomes for fold/raise + call variety
start overnight training run" — the condition, and D-30's authorisation to build.

**Verdict:** The build is green and the criterion **FAILS**. Per D-30 the overnight run is not spent.

- **The build succeeded on every mechanical gate**: 1,105 cases and 7,093 subtests, e2e 298/298, lint
  112 checks, map at 50 endpoints, and the fixed-limit path proven **byte-identical** against a
  pre-build baseline (51 gated fields, 6 sections, two additive exemptions the design mandates).
- **The criterion fails on four of five seeds** at conjunct 4 (no raise band beyond the minimum reaches
  10 %), with 6 and 7 alongside: the exploration-off policy concentrates 97.9–98.5 % of its decisions on
  **raise-minimum**. Seed 1 passes all seven, so the criterion is satisfiable.
- **The failure is the criterion's, not the learner's.** The collapse is onto the rung the sizing-ladder
  record measured as *the only positive one*, and this learner's **+2.361 ± 0.448 chips/hand** exceeds
  every fixed policy measured (+0.68 best) and the probe learner (+0.36). The variety the criterion
  demands is measurably *worse* play against a folding pool.

**The user's condition is therefore not met in the form it was given** — the learner shows no fold/raise/
call variety — while the *other* half of the condition, "positive outcomes", is met more strongly than
anything previously measured. Resolving that contradiction is a user decision, not an L0 one: it decides
whether the demo shows a varied agent or a winning one. Rejected here: retuning the threshold to pass
the observed distribution, and reading the chips as a pass — both would be D-28's defect again, after
five at this locus.

**Also recorded, and needed before any deep run**: the greedy pass is sampled at `min(budget, 1,000)` by
this build, so the shipped 200,000-hand budget is currently **refused** by the pass's 2,000-hand bound;
the `tie` flag is not returned by any exploration-off surface, so conjunct 7 records `T = 0` rather than
verifying it; and a min-raise-versus-min-raise pair can exceed the 24-slot history block, which the
shipped population never reaches but an uncapped shape can.

---

## D-32 — The no-limit pool contains no raiser, and cannot yet seat one

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "The alternate/previous models are already the aggressive raisers in the
pool"

**Finding:** they are, and they are not in it. Every shipped model is a fixed-limit container (two seats,
203 slots, three-wide head) and a no-limit pool refuses it as a foreign shape, so the no-limit league
started empty of version members: six baselines, of which `always-call` and the oracle raise 0 % of the
time and the three folders fold. The learner's ~0 % fold rate was that pool's answer, not a learning
failure.

**Blocker:** seating one trained no-limit model in the pool trains until a hand reaches 25 decisions and
then refuses by name — `encode(readout): 'history' must be at most 24 entries, got 25`. The 24-slot
history is derived from the fixed-limit cap, and the design kept the 203-slot layout for both shapes, so
the overflow was latent until a raiser was seated (V-F6, D-31).

**Decision:** the no-limit shape is **not runnable against a raiser** until the history block's capacity
is decided — widen it per shape (touching that shape's width, head, parameter count and containers),
coarsen it for the uncapped shape (keeps the width, loses resolution where the price signal lives), or
truncate (refused by the encoder today, and a silently shorter observation). That decision is the next
design question; the overnight run stays blocked because the league it would enter has no opposition
that makes folding correct.

Rejected: seating a scripted raiser baseline instead — it would test folding without fixing the league,
and D-21's baselines are meant to be fixed rules, not stand-ins for trained opponents.

---

## D-33 — Widen the history per shape, then test a six-seat no-limit table

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Widen and then run test with six-seat game containing both folders and
raisers in pool"

**Decision:** supersedes D-32's open question and D-23's refusal of six-player seating for this test.

1. **Widen the history block per shape.** The fixed-limit shape keeps its 24 slots; the no-limit shape
   gets the capacity its uncapped betting needs. Accepting the consequence the design tried to avoid:
   the sized shape's layout width, head width, `param_count` and containers are that shape's own, and
   the default shape is untouched.
2. **A third game shape: six-seat no-limit, 100-chip stacks, blinds 1/2.** The learner is one seat and
   the other five are drawn per hand from the pool, which holds **both folders and raisers** — the
   folders from D-21 and trained raisers as version members. This is what makes folding correct: a raise
   from a strong-hand opponent is the situation the earlier pools never presented.
3. **The test's evidence is the greedy census and the chips**, because the question is behavioural —
   does the learner fold when folding pays? The pairwise matrix and the Bradley-Terry rating stay
   pairwise and **refuse a six-seat table**; no league table is built for this shape in this pass.
4. Phase 1's fixed-limit artefacts — 18 containers, the evidence bundle, the full table, six rungs and
   both deep runs — remain untouched and are never compared across shapes.

Rejected: coarsening or truncating the history (D-32's alternatives — the first throws away the
resolution the sizing design exists for, the second changes the observation silently); and a scripted
raiser baseline as a stand-in for trained opposition, which would test folding without building the
league that must supply it (D-32).

**Gate (D-10):** a second and third declared shape plus an N-seat game is a major expansion. The
findings of D-24's and D-28's gates on multi-seat and sized actions are cited as the requirement list;
any departure from them needs its own review. The overnight run stays gated on the test's result.

---

## D-34 — Six seats makes folding less correct; the test's answer is zero folds

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Widen and then run test with six-seat game containing both folders and
raisers in pool" — executed as D-33.

**Result:** the build succeeded on every gate — 1,145 cases and 8,141 subtests, e2e 316/316, lint 132
checks, endpoints still 50, the fixed-limit shape proven byte-identical after each stage (4,238 of
4,238 leaf paths) — and the **test failed its question**: **zero folds in 15,127 decisions** with folding
legal in 11,212 of them, in a pool holding three folders and a trained raiser.

**Finding:** six seats makes folding *less* correct, not more. A six-way pot is ~6× the blinds before any
raise, so the price of continuing is generous and the raisers enlarge the pot being offered rather than
narrowing it. Folding is learnable where it is correct — heads-up against a raiser a learner folds 100 %
and profits (`fold-when-correct.md`) — so the conditions that make it correct are **few opponents, deep
stacks and large relative bets**, which six seats contradicts.

**Decision:** the six-seat shape stays declared and green, and is **not** the vehicle for a
fold-behaviour demo nor for the overnight run. The next test of folding belongs in the **two-seat
no-limit shape with a raiser in the pool**, where the earlier probe already showed the behaviour appears.

**Also recorded, and needed before any further run:** the divergence guard catches only non-finite
values, so a learner whose curve reaches 4e79 passes it (two of five seeds did); the retained record
carries no seat, so the rotation cannot be verified; and `engine.equity` is process-dependent through a
set-ordered sampling deck, contradicting `docs/L3/engine/stream.md` (D-6).

---

## D-35 — The zero fold rate is a learner failure, not the pool's answer

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Are you testing an entire hand, played to the reveal, or only the pocket?
Folding is absolutely the correct decision for junk hands in a seven-seat game, but not before the flop"

**Finding:** the census could not answer that — the retained decision record carries no street — so it was
measured directly. At a six-seat table against five always-raisers the trained learner faced a bet on
**200 of 200 preflop decisions and folded none**, choosing check-call 62 % and raise-minimum 38 %.

**Correction:** D-34's "six seats make folding less correct" holds post-flop, where a six-way pot is a
cheap price, and **not pre-flop facing a raise**, where junk is a clear fold. The learner's zero fold
rate is therefore not the pool's answer; against raisers it declines a fold that is correct every time
it is offered one.

**Decision:** the cause is now the question, and it is separable in one cheap test — the **two-seat
no-limit shape against a raiser**, where a tabular learner with the same terminal reward folded 100 %
(`fold-when-correct.md`). If the product learner folds there, the cause is exposure or budget; if it does
not, the cause is its value estimate or its representation, and that is a design finding about the
learner rather than about the game.

Rejected: reading the six-seat run as decisive on folding, which the missing street fact made impossible
(D-34), and changing the game again before that test is run (D-6).

---

## D-36 — The RCA's blocking cause is mechanical: no run may exceed 2,000 hands

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "RCA how it learned to fold 0/15,127 of the time. This is not the
consequence of the game being biased against folding, that is an algorithm failure."

**Findings:** folding is not blocked by the reward (a tabular learner with the same terminal payoff folds
100 %), not by the missing `hand_class` fact (the same learner folds 100 % without strength in its state),
and not by the pool (a learner trained with a raiser in the pool folds 0 of 12,856 decisions). The one
remaining difference is scale: 8 states and 20,000 hands against 14,766 parameters and ~3,000 decisions.

**The blocker:** that hypothesis needs more hands, and **the build refuses any budget above 2,000** —
`GreedyPassRefused`, because the greedy pass plays the whole budget and one pass is capped at 2,000 hands.
So the deep run cannot start, and the zero-fold rate is not yet attributable.

**Decision:** lift the pass's cap by **sampling the pass from the run** (a fixed number of hands drawn
from the run's own distribution) rather than by refusing the run, then re-run the RCA at 20,000+ hands
with a raiser in the pool. A learner that folds there makes budget the cause; one that still does not
makes the max operator's overestimation the cause, and the already-implemented Double-Q rule is the
untried candidate for it (D-19).

Rejected: capping every run at 2,000 hands (it would make the deep run impossible and hide the
attribution), and re-running the six-seat test at this budget to look for folding (it cannot distinguish
the two causes, D-35).

---

## D-37 — The greedy pass samples its bound instead of refusing the run

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Proceed with fix"

**Fix:** one pass plays `min(budget, 2,000)` hands, drawn as **the run's own first that-many hands** —
the same deal and opponent derivations, the same learner seat, the same frozen pool — with exploration
off and no generator drawn. Below the bound the rule is the identity, so a 1,000-hand run's block is
unchanged: the committed pre-change capture (`tests/integration/training/_greedy_sample_baseline.json`,
sha256 `6394f22b…`) is replayed over 21 fields with no tolerance and matches. The cap still binds a
**pass request**, never a run: a 20,000-hand run completes in 42 m 54 s and its block reports a 2,000-hand
sample.

**Rejected:** stride sampling (a 10-wide stride would land one seat of a two-seat shape and misreport the
seat split); a fresh generator (not replayable from the record's tuple); the run's tail (a 10,000- and a
20,000-hand run must pass over the *same* hands for a budget sweep to attribute to training); raising the
cap (that was the defect); a sixth block key naming the rule (it would move the block that must stay
byte-identical — the rule is a published function of budget and bound instead).

**Verification:** twelve batteries green, 1,190 cases and 9,241 subtests; lint 144 checks; endpoints 50;
the fixed-limit shape byte-identical for a 1,000-hand run; **e2e 316/316 confirmed separately by L0**.
Corrections routed to L1, not written here: `records.md` §15's `hands` is now the sample's count,
`sizing.md` §4's "refused, never truncated" and its "global stream" bullet, `assumptions.md` ASM-38's
"refused beyond", and `battery.md`'s two clauses.

---

## D-38 — The RCA concludes: budget eliminated, the max operator is the cause, Double-Q is next

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "RCA how it learned to fold 0/15,127 of the time. This is not the consequence
of the game being biased against folding, that is an algorithm failure."

**Result:** with the budget unblocked, the answer is measured, not inferred — **0 folds in 17,181 greedy
decisions at 20,000 hands per seed**, and 0 in the 8,725 where `fold` was legal, in a pool holding three
folders and a trained raiser.

**Conclusion:** the reward, the missing `hand_class` fact, the pool's composition and the budget are all
eliminated. What remains is **the max operator's overestimation**: the calling arm is valued by a `max`
taken over estimates from the same samples, so a certain small loss always looks worse than an
optimistically valued call. This is the classical masked-Q failure, and it explains why an eight-state
tabular learner does not suffer it while a 14,766-parameter one does.

**Next:** **Double-Q** — catalogued since D-19, implemented, never trained against this question —
decouples selection from evaluation and removes exactly that bias. It is the experiment, not a design
change; no new shape or game is involved.

**Corrections this row makes:** D-31's "sampled at `min(budget, 1,000)` … currently refused by its
2,000-hand bound" is false on both counts (the sample is `min(budget, 2,000)` and no run is refused);
D-36's blocking clause is resolved. And the RCA record's earlier "any budget above 2,000 hands is
refused" is corrected to what was true — it was refused until D-37.

---

## D-39 — Counterfactual regret is a measured repair to the estimator, and is gated for the product

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Change the reward function to use counterfactual regret if the reveal shows
that calling would have lost more money than folding"

**Measured first in the probe**, because it is a paradigm change (a privileged signal the opponent cannot
see) and the project's rule is to prove the mechanism before touching six modules:

- **The signal must be estimated for the arm not taken.** Firing it only at folds yields **zero**
  updates — the learner never folds, so the signal never exists. Estimating the *call* arm at every
  decision removes that circularity.
- **It repairs the estimator**: against D-21's folder, chips/hand move **−2.89 → +3.49** and over-betting
  collapses (pot-size 35 % → 2 %). That is precisely the overestimation D-38 identified as the cause of
  the zero-fold rate.
- **It is not a fold generator**: against a raiser the baseline already folded 100 %, and the
  counterfactual traded most of that for calling at equal EV (+0.73 against +0.75). Expected product
  effect: **calibration**, not more folding.

**Decision:** the counterfactual signal is **gated for the product** (D-10) as a privileged-reward
change: its definition, its mixing rule against the TD target, its per-shape cost (equity sampling per
decision), its record fields, and whether it is a reward or an estimator correction are design questions
the gate must settle before implementation. It is not implemented in the product by this row.

Rejected: implementing it as a *fold-only* reward (measured to do nothing, for the circularity above);
and rewarding folding with the savings it produced, which would put the fold's value on a different scale
from every other action and make the comparison meaningless.

---

## D-40 — Reveal-only counterfactual, multi-seat mixed pools: measured, and it is the estimator

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Use counterfactual regret for all actions only on cases where the cards are
revealed into public knowledge, use the previous reward scaling otherwise. I know it won't reward folding
in two-player games, we're not training for two-player any more. Use mixed pools of folders, raisers, and
callers in multi-seat tables"

**Measured** in the probe at the configuration the user named — six seats, mixed folder/caller/raiser
pool, the learner seated at random, counterfactual applied only at showdowns and the ordinary net-chip
reward elsewhere:

- **Folding appears**: the tabular learner folds **87 %** at six seats with a mixed pool. The product's
  six-seat run folds **0 %** on the same kind of table, so the zero-fold rate is confirmed as an
  **estimator** failure, not a game or pool property (D-38).
- **The signal works exactly as specified** — 19,889 exact counterfactual updates across 7,978 showdowns,
  no privileged sampling — and it changes little where the learner is already correct (+0.362 → +0.297
  chips/hand, inside noise).
- **Its product value is repair**: D-39 measured +6.4 chips/hand from the same correction against an
  overestimating learner, which is the failure the product exhibits.

**Decision:** the reveal-only form is the one to build, with the net-chip reward retained for every
hand without a showdown; the multi-seat mixed pool is the configuration to train in. Recorded limitation:
one revealed board gives **one sample** per decision, so the signal is high-variance and needs many
showdowns; lowering variance by averaging over holdings would abandon the reveal and is refused.

**Next:** implement in the product as a gated change (D-39's open items: definition, mixing rule,
per-shape cost, record fields), then re-run the six-seat mixed-pool test whose 0 % fold rate motivated
this line of enquiry.

---

## D-41 — The reveal-counterfactual rule cannot be built as stated; Double-Q is spent first

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Proceed" — proceeding with the reveal-only counterfactual.

**Gate result:** `FAIL` (validity) and `ADJUDICATION` (critique), and the findings are structural rather
than fixable-in-passing:

- **The rule axis cannot carry it.** "A rule owns the **bootstrap** and nothing else"; `rules.md` §5
  already declined a returns-based member because a transition carries one decision and no episode
  boundary, and "giving the transition record an episode field is a surface change this decision does not
  make". A per-hand, per-action target needs exactly that surface change first.
- **The reveal is not an observable.** `learn` drops any transition key beyond the declared seven, the
  episode record names no card outside a readout, and the readout never carries another seat's hole
  cards — so "the cards were revealed" and "who won" exist in no declared record.
- **The arithmetic is not one quantity.** `v_call` charges `to_call` on the loss branch and not on the
  win branch and omits later-street commitments, which *overstates* the call arm — the direction of the
  bias this change exists to remove.
- **A rule swap would move the budget**, contradicting the axis's own promise, because writing two
  actions' values at a decision the learner raised at needs extra steps per transition.
- **It cannot answer the question.** Its own measured arm moved nothing (87 % both arms), the +6.4 that
  motivates it belongs to the two-seat form the user excluded, and the reveal is conditional on reaching
  showdown — so a learner that folds more receives fewer updates, the fold-only circularity in weaker form.
- **D-40 reverses D-34 and D-35 without naming them**, which this log forbids.

**Decision:** the reveal-counterfactual rule is **not built**. The next experiment is **Double-Q at 20,000
hands** against the raiser pool — catalogued since D-19, implemented, capacity-matched, never trained
against this question, and the direct test of D-38's overestimation finding. It needs no new axis, no new
record and no new surface, and the cap fix (D-37) has made the budget possible.

D-40 is **superseded as an implementation plan** and retained as a measurement: its five eliminations and
its 87 %-both-arms result stand. D-34 and D-35 are named here as the rows this decision follows rather
than reverses.

---

## D-42 — Double-Q moves nothing; the RCA's attribution is not confirmed

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Proceed" — with D-41 selecting Double-Q as the experiment spent.

**Result:** `double-q-learning` at 20,000 hands per seed, two seeds: **0 folds in 21,858 decisions**, fold
legal in 14,046, and the same **98 % raise-minimum** as masked-Q produces in that configuration. The
classical remedy for the overestimation D-38 named changes nothing.

**Consequence:** D-38's conclusion is **not confirmed**. Overestimation is not excluded — function
approximation can bias values in ways decoupled selection does not remove — but the remedy it named fails,
so the attribution cannot stand as written. The RCA's elimination table now reads: reward, `hand_class`,
pool composition, budget and the max-operator remedy all tested, none explaining the zero fold rate.

**Decision:** the next experiment is the **matched-configuration** test — the six-seat mixed table, the
product learner, 20,000 hands, now possible after D-37 — because that is the only cell where a tabular
learner folds 87 % and the product folds 0 % on the same table. If the product still does not fold there,
the finding is about its **representation**; if it does, the earlier six-seat zero was its 1,000-hand
budget and the two-seat zeros were a configuration not to generalise from.

Rejected: building the reveal-counterfactual rule (D-41: no carrier on either axis), and reading Double-Q's
null as evidence that folding is not worth pursuing (it is a null about one remedy, not about the cause).

---

## D-43 — The counterfactual is authorised: episode resolution comes first

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Do the counterfactual anyway. Add the necessary resolution changes to
determine the reveal and whether the caller/folder (would have) lost/won, all of the needed
functionality is present in the package"

**Decision:** overrides D-41's refusal and authorises the surface change it required: the transition
record gains the **episode boundary** `rules.md` §5 declined, and the episode record gains the **reveal**
(which seats were revealed, with what, the outcome) so a counterfactual resolves from declared artefacts
and never from a privileged peek at decision time. `readout.md` §4 stays true — no seat's cards are
visible to another while a hand is live.

The gate's findings are the build's requirement list: (1) **resolution, not privilege** — the reveal is
post-hand data consumed by the training step; (2) **one quantity** — the counterfactual must be a
whole-hand net-chip delta, no `to_call` on one branch and not the other, no omitted later commitments;
(3) **the budget must not move**, or the promise is corrected; (4) **all actions** — every raise band the
shape declares, with a declared opponent-continuation assumption where the reveal cannot supply one;
(5) **opt-in per variant** so a paired arm differs only in it (D-3); (6) **a pinned criterion** before any
run; (7) **shapes declared**, since the fixed-limit shape has showdowns too (D-33).

**Method authority:** the user's last clause — the state machine copies and continues, hole cards are
known, the board is dealt — so replay is available; choosing replay or the showdown reveal is L1's
decision with its cost declared.

---

## D-44 — The revealed counterfactual is built; it folds at one seed of two

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Do the counterfactual anyway. Add the necessary resolution changes to
determine the reveal and whether the caller/folder (would have) lost/won, all of the needed functionality
is present in the package"

**Built:** as D-43 specified — the reveal recorded after the hand (board, showdown, split, per-seat hole
cards, `shown`, `won`), the transition carrying `episode` and the per-action `counterfactual`, the
counterfactual value a **whole-hand net-chip delta** with `v(a_realised) = Δ` proved at every transition of
a resolved episode, **all legal actions** targeted, a third catalogue (`counterfactuals`: `none` |
`reveal-counterfactual`) rather than a rule or a utility, and the step-count promise corrected rather than
evaded. Method: the reveal, not the replay — replay costs 0.07 s a hand and ≈3 s when its continuation
meets an oracle decision, against +2.4 ms a six-seat hand for the reveal.

**Measured:** six seats, mixed pool of folders, raisers and callers, 20,000 hands per seed, seeds 0 and 1,
paired arms differing only in the member. **Folding appears at seed 1 — 40.01 % against 0.00 %, a 40-point
gap — and not at seed 0.** Chips overlap at both seeds. The criterion pinned before the run **FAILS**,
because it required every pinned seed to pass.

**Decision:** the member is **kept** — it is the first mechanism in the project to produce folding where
none existed, and its effect is behavioural rather than chip-borne. What remains is a **probability, not a
threshold**: seeds 2–6 at the same configuration would put the first estimate on how often the member
reaches the folding attractor. The criterion is not retuned; a null at five of seven seeds would be the
result.

**Also recorded for the next run**: the reveal resolves 27–28 % of training transitions, so three
quarters of the learner's updates are unchanged, and a member that covers more hands would need the
no-showdown case to be resolvable — the replay the cost analysis rejected.

---

## D-45 — The counterfactual cannot be measured across seeds yet; the deep run takes the budget

**Status:** ACTIVE · **Date:** 2026-11-07

**Source (user, verbatim):** "Try the run, and prepare to close out the first rung with whatever is the
best performing deep run, we need to move on to the later rungs while there is still time for deep runs
(Talk is on next Tuesday)"

**Result of the run:** seeds 2–6 of the revealed counterfactual **died on the first transition** of the
first new seed — `LearningDiverged … got -inf`. The guard refused it by name, so this is a loud failure
and not a silent corruption; the same configuration completed at seeds 0 and 1, so the cause is a target
the member produced on a particular hand, and the build's own mean-aggregation remedy is insufficient at
every seed. What it needs is a **finiteness argument** — bound the target to the chips a hand can produce,
or refuse the branch by name — not another aggregation rate.

**Decision:** with the talk a week away, the counterfactual is **set aside**: kept, recorded, not part of
the first rung's close-out and not runnable across seeds until the finiteness argument exists. The spend
goes to **the deep run at the best-measured configuration** — two-seat no-limit, 100-chip stacks, the
folders pool, masked-Q, net chips, 200,000 hands × seeds 0–2 — which measured **+2.361 ± 0.448 chips/hand**
at the live budget and is the strongest behavioural result the project has. It is in flight.

**Close-out plan for the first rung**, to be written when the run lands: R1's evidence is the deep run's
curves, chip rate with intervals and greedy census, beside the published rungs and the measurements that
justify its configuration (the sizing ladder, the steal result, the fold eliminations). Later rungs then
inherit the same shape so their deep runs can start while time remains.

---

## D-46 — R1 closes on a converged steal; R3 takes the machine

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Check if deep run is going, there's no background job shown" — answered,
then "Has it resolved yet?"

**Result:** the deep run resolved. **200,000 hands × three seeds in 11.5 h**, pool
`pool-11b03e0a5ff07c13`: **98.46 % raise-minimum, 1.54 % check-call, 0 folds, +1.188 ± 0.466 chips/hand**
against a folding opponent, identical across seeds because the policies are behaviourally identical.

**R1 is closed** on a converged steal: 200× the live budget reproduces the live-budget policy within a
point (98.46 % against 96.8 %), so the rung's claim — a flat numeric encoding and a naive stack learn to
steal from opponents that fold — holds at the deepest budget the project runs. The curve was not captured
(the launcher's formatting bug and a missing record dump), which is recorded as owed rather than implied.

**Decision:** with six days to the talk and ~11.5 h per three-seed deep run, the machine goes to **R3,
`card-tokens`** — the encoding axis and the talk's "tokenising cards into embeddings" beat — at the same
configuration (two-seat no-limit, 100-chip stacks, the folder pool, 200,000 hands × seeds 0–2), so the
only variable against R1 is the encoding (D-3). Launched as a tracked job this time.

**Queue after R3**, in this order, as time allows: **R6 `residual`** (the beat the user asked for
explicitly at intake: residual streaming per `llm-arch-kb`), then **R4 `wide`** or **R5 `dense`/`sparse`**
if a rung still fits. Every deep run inherits R1's shape so the table compares rung to rung.

---

## D-47 — One run of twelve folds, and only at one seed of two

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Review all of the runs and identify which ones did *not* converge to
never-fold"

**Finding:** of twelve product runs — two game shapes, three seat counts, four pools, two learning rules,
budgets from 200 to 200,000 hands — **exactly one** produced folding: the `reveal-counterfactual` member at
**seed 1**, 1,545 folds of 3,862 decisions (**40.01 %**) against its own control arm's **0.00 %** on the
same pool, seed set and budget. Its seed 0 and every other run folded **not once**; the seeds 2–6 attempt
diverged before a verdict.

Probe runs are the counter-pattern and confirm reachability: a tabular learner folds **100 %** against a
tight aggressor (with or without hand strength in its state) and **87 %** at a six-seat mixed table.

**Consequence:** folding is reachable by this stack but appears in **one run of twelve**, and in that run
at one seed of two. The counterfactual effect is therefore **real where it appears and not reproducible
across seeds** at the shipped budget — the attractor lottery recorded since `attractor-sweep.md`, now with
its first exception rather than an absence.

**No action taken on the runs**: none was restarted, retuned or filtered (the user's instruction to wait
for confirmation on runs stands).

---

## D-48 — The utility axis folds, consistently; D-47's "one run of twelve" is corrected

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "What about the stack-shortfall runs?"

**Correction:** D-47 omitted the utility axis and overstated the pattern as never-fold. From the ablation
artefact, two-seat no-limit, folder pool, 1,000 training hands × 3 seeds: **`stack-shortfall` folds
0.82 / 3.33 / 3.48 %** where **`net-chips` folds 0.10 / 0.10 / 0.28 %** on the same pool — a
ten-to-thirty-fold difference **consistent across all three seeds**, at a twentieth of the
counterfactual's budget. The net-chip arms are therefore *effectively* never-folding, not literally.

**Consequence for the record:** folding appears in **two** places in the product, not one — the utility
axis at every seed, and the counterfactual member at seed 1 only. The utility's rate is smaller in
absolute terms (3.5 % against 40 %) but **reproducible across seeds**, which the counterfactual's is not.
Neither establishes a chip advantage: both arms' intervals overlap.

**Decision:** the **utilities axis is the cheapest deep run left** — one variable, no surface change, and
already runnable — and it is the natural next spend after the encoding rung. No run is started without the
user's confirmation (which stands from the previous instruction).

**Also recorded, my defect:** the attractor sweep labelled its modes by raise and call shares alone, so its
"mixed" bucket hid the fold share — the quantity this entire line of enquiry turns on. Future sweeps count
folds as a first-class column.

---

## D-49 — Deep runs reduced, and the counterfactual is combined with the shortfall utility

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Reduce the deep run length, then try a run that combines reveal-counterfactual
with the stack-shortfall loss/reward calculation"

**Reduced length:** a deep run is now **15,000 hands × 3 seeds** for six-seat shapes and **50,000 × 3** for
two-seat ones, chosen so either lands in **3–4 h** instead of the 11.5 h a 200,000-hand run costs. The
reduction is a budget decision under the talk deadline, not a claim that 200,000 hands is unnecessary —
R1's deep run showed the policy converged long before it, and the plateau it measured is what licenses a
shorter default.

**The combined run:** six-seat no-limit, the mixed pool `raiser-seed-six-seat-s0` plus three anchors and
D-21's three folders, **`reveal-counterfactual` + `stack-shortfall`**, paired against
**`counterfactual: none` + `stack-shortfall`** on the same pool, seeds and budget, so the only difference is
the member. Both halves have measured, opposite characters — the utility folds **reliably but weakly**
(0.82 / 3.33 / 3.48 % across seeds, D-48) and the counterfactual folds **strongly but at one seed of two**
(40.01 %, D-44) — so the pairing asks whether the reliable half makes the strong half reproducible.

**Attribution:** the two arms differ in exactly one key (D-3); chips and fold shares are reported per seed
and never thresholded, since no criterion is pinned for this combination and none is being invented after
the fact.

---

## D-50 — The risk-averse utility folds reproducibly; the counterfactual adds nothing

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Reduce the deep run length, then try a run that combines reveal-counterfactual
with the stack-shortfall loss/reward calculation"

**Result:** at six seats, the mixed pool, 15,000 hands × seeds 0–2, **both arms fold at every seed**:
`reveal-counterfactual` + `stack-shortfall` at **74.71 / 77.97 / 77.46 %**, and the control with the member
off at **78.33 / 87.01 / 77.58 %**. The control folds *more*, so the reproducible folding is the
**utility's**, not the counterfactual's.

**Attribution** is clean — same pool id `pool-8386c3ef83ae48b2`, same shape, same seeds, where
`net-chips` folded **0.00 %** at 20,000 hands (D-44) and **0 %** at five seeds of 1,000 (D-34). The
utility is the sole difference.

**What it settles:** the project now has a configuration whose folding is **reproducible across seeds** —
the first — and it needs neither the new counterfactual nor a new shape. `stack-shortfall` at six seats
with a mixed pool folds three quarters or more of its decisions at every seed, against a utility-matched
control that folds none.

**What it does not settle:** folding is **not profitable** in this configuration (chips −0.48 to −1.92,
two of six intervals reaching above zero), so this is a behavioural result and not a chip edge; and the
two-seat rate for the same utility was 0.82–3.48 % (D-48), so seat count dominates its effect.

**No criterion was pinned** before this run and none is invented after it. If this configuration is to
carry a verdict for the talk, the criterion belongs to the user and should be pinned before a confirming
run.

---

## D-51 — Multi-seat only; the token build runs as a paired encoding comparison

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "We're not doing two seats. Start the token build"

**Decision:** **every run from here is multi-seat.** Two-seat configurations are retired as training and
measurement targets; D-49's two-seat length (50,000 × 3) is void, and the six-seat length stands at
**15,000 hands × 3 seeds**. Two-seat results already recorded stay as recorded — they are the history that
justifies the six-seat work, not targets to extend.

**The token build** is run as a **paired encoding comparison at six seats**, not as a lone rung: `R3
card-tokens` against `R1 flat-numeric`, same six-seat shape, same mixed pool, same seeds, same budget, same
utility (`net-chips`), so the encoding is the only variable (D-3). Without its flat-numeric twin at the same
shape there is no attributable encoding result — the two-seat R1 deep run cannot serve as the control for a
six-seat token run.

**Why the encoding matters here beyond the talk's narrative:** the token encoding is the only one that could
carry a card's identity into a discrete vocabulary, and the six-seat shape is where behaviour finally
separates (the utility axis produced 77–87 % folding where the chip reward produced none). If the encoding
moves behaviour at six seats, it is attributable to the encoding; if it does not, the negative is equally
usable.

---

## D-52 — The token encoding moves play, not chips; the sharper pair is under way

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Start the token build" and "Try the stack-shortfall"

**Result of the net-chip pair** (six seats, `pool-8386c3ef83ae48b2`, 15,000 hands × seeds 0–2, encoding the
only variable): the encodings **diverge in policy and agree in money**. At seed 0, flat-numeric settles on
minimum raises (61.7 %) and card-tokens on half-pot raises (56.8 %); at seed 1 flat keeps minimum raises
while tokens fall into always-call. Every chip interval spans zero (±7), and at seed 2 both land on the same
always-call policy with identical decision counts and identical payoffs. Neither arm folds — `net-chips`
has produced 0 % folding in every multi-seat run on record.

**Reading:** the encoding changes **which attractor a seed falls into**, not the outcome. That is a usable
talk beat and a real effect, and it is not evidence that tokens learn better poker.

**Decision:** the same pair under **`stack-shortfall`** is the sharper test — the baseline there folds
77–87 %, so there is a policy distribution for the encoding to disturb — and it is running now (six seats,
same pool, same seeds, same budget, arms one key apart). Its result decides whether the encoding claim has
anything behind it beyond seed selection.

---

## D-53 — The encoding bites under the risk-averse utility: more folding, less variance

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Try the stack-shortfall"

**Result** (six seats, `pool-8386c3ef83ae48b2`, 15,000 hands × seeds 0–2, `stack-shortfall` both arms,
encoding the only variable): **`card-tokens` folds 91.8 / 93.5 / 92.3 %** against `flat-numeric`'s
**78.3 / 87.0 / 77.6 %**, loses less at every seed (−0.94 / −0.11 / −0.51 against −1.92 / −0.48 / −1.19),
and its payoffs are far tighter (±0.25 / ±0.81 / ±0.05 against ±1.70 / ±1.47 / ±2.05).

**Two levers, in order of size:** the **utility** moves the agent from stealer to folder (0 % → 78–93 %),
and the **encoding** then decides how hard and how consistently it folds (78–87 % → 92–93 %, with a third
of the variance and a fifth of the seed spread). The encoding's effect is **conditional on the utility** —
under `net-chips` the same comparison produced no chip difference at all (D-52).

**What it does not establish:** neither arm wins (all chip rates negative), the arms' intervals still
overlap at every seed so no chip difference is resolvable, and folding 92 % is a behaviour rather than an
edge.

**For the talk:** this is the first encoding result in the project that is attributable, reproducible across
seeds and consistent in direction — and it composes with the utility result rather than competing with it.

---

## D-54 — The encoding claim is hardened on seven seeds

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Run the rest of the seeds"

**Decision:** the `card-tokens` vs `flat-numeric` pair under `stack-shortfall` is re-run on **seeds 3–6**
(four more per arm), at the same six-seat shape, pool, budget and utility, on top of the recorded seeds
0–2 (D-53). Together that is **seven seeds per arm**, which is what the claim needs: on three seeds the
token arm folded 91.8–93.5 % with a spread of 1.6 points, and a spread that tight is exactly what a
three-seed sample cannot distinguish from luck.

The purpose is falsification, not confirmation. If seeds 3–6 keep the token arm above 90 % while the flat
arm wanders in the 70s–80s, the encoding result stands on seven seeds. If the token arm falls to the flat
arm's range on the new seeds, then D-53's 92–93 % was **seeds 0–2**, not the encoding, and that is the
result — the criterion is the *separation between arms per seed*, not any absolute rate, and no threshold
is invented after the data.

Cost: eight runs at the reduced length, ~6 h. No two-seat configuration is involved (D-51).

---

## D-55 — The finiteness fix, then the three-way combination

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Do the finiteness fix and then test the combination. There are plenty of
unused cores, run both as long as they're not on the same thread"

**The gap this closes:** every counterfactual run to date is `flat-numeric` — verified from the
containers, whose `representation.encoding` is `flat-numeric` in all of them — so the encoding has never
been combined with the counterfactual. The untested cell is **`card-tokens` + `reveal-counterfactual` +
`stack-shortfall`**, and it is the promising one because the two mechanisms have opposite profiles: the
counterfactual is strong but seed-dependent (40 % at one seed of two, nothing at the other), while the
token encoding is weaker but steady (1.6-point spread against the flat encoding's 9.4).

**Order of work, and why:** the counterfactual **diverges** at a third seed (`-inf` at the first
transition, D-45), so the combination cannot be measured before the fix — a partially-filled table would
be the result instead of the cell. The fix must make the member **unable** to emit a non-finite target
(bound it to the chips a hand can produce, or refuse by name), not clip silently.

**The control is reused, not re-run:** D-53's `R3-card-tokens-shortfall` arm (91.83 / 93.45 / 92.25 %,
chips −0.939 / −0.110 / −0.509) is the counterfactual-free baseline on the same pool, shape, seeds and
budget, so the combination arm is one variable away from a measured result.

**Concurrency:** the seeds 3–6 hardening run (`/tmp/token-shortfall-seeds36`) continues untouched; the fix
and the combination run in separate single-threaded processes on other cores. **No threshold is pinned**
for the combination; it is a measurement, and criteria are pinned before runs, not after them.

---

## D-56 — The encoding claim survives seven seeds; it is the project's strongest result

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Run the rest of the seeds"

**Result:** over **seven seeds** (0–6) at six seats, `stack-shortfall` held fixed and the encoding the only
variable: **`card-tokens` folds 92.74 % (sd 1.22, range 91.02–94.82)** against **`flat-numeric`'s 77.53 %
(sd 5.71, range 70.69–87.01)**. The arms' **ranges do not overlap** — the lowest token seed is 4.01 points
above the highest flat seed — and every individual seed favours tokens by 6.4–22.3 points (mean +15.22).

**D-54's falsification attempt failed to falsify:** seeds 3–6 alone give 91.02 / 93.01 / 94.82 / 92.82 for
tokens against 76.99 / 70.69 / 81.21 / 70.87 for flat, so D-53's three-seed result was not seed selection.

**What it does not establish:** neither arm wins (every chip rate is negative, so this compares two losing
policies); the effect is conditional on the utility (under `net-chips` the same comparison showed no chip
difference, D-52); and folding 92.7 % is a behaviour rather than an edge.

**Decision:** this is the **lead claim for the talk** — attributable, reproducible across seven seeds and
falsification-tested — stated as *"tokenising the cards makes the agent fold 15 points more, with a fifth
of the variance, and no seed reverses it"*, never as a claim that tokens win chips. The counterfactual is
not part of it: it added nothing to this pair (D-55).

---

## D-57 — Inference test: the folding models lose to the non-folding ones

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Test both the net chips and double Q versions, Then run all of the token models
against each other for an inference test"

**Result of the inference test** — 11 entrants (ten `card-tokens` checkpoints plus the pool's raiser),
55 matches, six seats, 300 deals played twice per match with the entrant on each side, antisymmetry
verified at `+0.000000` and within-family agreement at 0.026 chips:

- **`token+net-chips` beats `token+shortfall` by +0.265 chips/hand per seat** across 21 matches.
- **The raiser beats both** (+1.352 against net-chips models, +0.512 against shortfall models) and is the
  strongest single entrant at +0.764 overall.
- **Every folding model is negative against the field** (−0.08 to −0.16); the best individual model is a
  non-folding one at +0.223.

**Consequence:** D-56's reproducible folding is now priced — **the behaviour that is reliable is the
behaviour that loses**. The talk can pair the two results honestly: the risk-averse utility makes folding
reproducible, and the inference test shows the folder gives up a quarter of a chip a hand to the agent that
never folds.

**Also recorded, my own defects in this instrument, caught before any number was read**: a seat-index bug
that measured the opponent's seats while labelling them the entrant's (every match cancelled toward zero);
different deal sets for the two seatings, which broke antisymmetry (sum −0.216); and `payoffs` indexed as a
list when it is a seat-keyed mapping. Each was caught by an invariant — the antisymmetry and within-family
checks — and the corrected instrument reports both as passing.

**Still running:** the `card-tokens` + `double-q` arm, which decides whether the rule axis changes the
folding rate the utility produces.

---

## D-58 — The rule axis is dead; the utility is the only switch

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Test both the net chips and double Q versions, Then run all of the token models
against each other for an inference test"

**Result:** `card-tokens` + `double-q-learning` at six seats produces the **same policy** as the masked-Q arm
on the same pool, shape, seeds and utility — **0 % folding**, and two of three seeds byte-identical
(4,432/4,617 decisions, 100 % check-call, chips −3.510/−2.683), the third differing by 0.1 chips and 0.1
points of share. This reproduces D-42's two-seat finding (0 folds in 21,858 decisions under Double-Q), so it
now holds across seat counts, encodings and shapes: **the rule changes neither the folding rate nor the
policy.**

**The lever table, all measured at six seats:** the **utility** is the switch (0 % → 78–93 %); the
**encoding** is a real modulator (77.5 % → 92.7 %, sd 5.7 → 1.2) when the utility is held fixed; the
**rule** and the **counterfactual** do nothing; and the **inference test** (D-57) prices the result — the
folder loses 0.265 chips/hand per seat to the non-folder.

**For the talk:** of four levers built, exactly two move behaviour, and they compose in a fixed order. That
is the deck's spine, and it is the honest form of the claim: **the reward decides whether the agent folds,
the encoding decides how hard and how consistently, and neither makes it win.**

---

## D-59 — The never-fold models are state-blind: one constant score vector, not a weighted choice

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "What is the percentage weighting that the different models give to
fold/check-call/raise? Is it that they zero out the fold chance entirely, or that they're outweighted?"

**Answer:** neither — and the distinction matters. The learner is an **argmax over six Q-values**, so it has
no probability weighting to report. Measured on 477 distinct observations at a table with all four streets:

- **All four net-chip models emit exactly ONE score vector for every decision** — a constant function of no
  input. `fold` is not zeroed and not outcompeted: the model is not reading the state. Its constant margin
  puts fold 6.03 below the call and 7.59 below the best raise, hand after hand.
- **The seven token+shortfall models do read their input** (115 distinct vectors of 117) but the spread is
  tiny (sd 0.001–0.004) and fold wins by ≈0.013 — genuinely outweighed, by a hair.
- **Only flat+shortfall is both state-dependent and mixed** (175 vectors of 175; fold 53 %, raises 40 %,
  call 7 %).

**Consequence:** "never folds" is not a preference but a **collapsed network**, which explains three seeds
with identical payoffs, the inference test's 0.026-chip same-family agreements, and every single-action
census. The utility's real effect is not on *what* the model prefers but on **whether it learns to depend
on its input at all** — and only the flat encoding under the risk-averse utility produces a policy with
genuine state dependence.

**For the talk:** this is the strongest methodological beat in the project — a census that looked like a
strategy ("it never folds") turned out to be a constant function, and only reading the values rather than
the argmax revealed it.

---

## D-60 — The net-chip models' trunks are dead: the input path collapses at the ReLU

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "RCA where the input is falling out of the net-chips model"

**Cause, measured by counting active ReLU units in each network's own forward pass:** the **trunk is dead**.
`flat + net-chips` keeps **0 of 36** units alive in both hidden layers, so its hidden vector is exactly
zero and its output **is** its output bias; `token + net-chips` keeps **2 then 1 of 50**, contributing
0.0003 against a bias of 9.39. Both are constant functions. The shortfall models keep 16–25 units alive and
are input-driven.

**The chain:** the reward is chips (±600 at six seats) → squared TD at the declared rate drives parameter
magnitudes to fit that scale (input-weight norms **313 vs 8.5**, input biases **82 vs 0.083**) → large
pre-activations plus ReLU leave every trunk unit on the negative side → the hidden vector is zero → the
output is the bias → the policy is a constant.

**Consequences:** this explains three seeds with identical payoffs, Double-Q moving nothing (there is no
input path for a better bootstrap to repair), the inference test's same-family agreement, and every
single-action census — *including the project's earlier finding that 200× more training changed nothing*,
because no gradient reaches an action through a zeroed unit.

**What follows:** the fix is **scale, not architecture** — normalising the reward should keep parameters
small and the trunk alive — and the project already has the rung for keeping a trunk alive: **R6
`residual`**. The instrument to watch is **active-unit count**, not the action census: it is the earliest
visible failure and `agents` already exposes the arrays to count it.

---

## D-61 — Normalise every input into [0, 1] and re-train every model version in parallel

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Normalize all input values to between 0 and 1 and then rerun training for all
model versions in parallel"

**Why:** D-60's RCA found the input path dead — `net-chips` models keep **0 of 36** (flat) and **2 then 1 of
50** (tokens) hidden units alive, so their output is their output bias and their policy is a constant. The
measured chain runs through **input magnitude**: the O(100) chip reward drives input-weight norms to 313 and
input biases to 82, the pre-activations leave every trunk unit negative, and ReLU zeroes the hidden vector.
Normalising the input to [0, 1] attacks the first term of that chain rather than the reward.

**Decision:** both encodings emit values in [0, 1] — the dense layout slot by slot with a declared numerator,
denominator and clamp, the token path with its own justified reading of "bounded" — and **every slot that can
saturate does so by a documented rule, never silently**; a readout that cannot be normalised is refused by
name. The invariant becomes a **battery assertion**: no observation emitted anywhere exceeds 1.

**Costs, declared:** the layouts keep their widths, so containers still load, but their **values mean
something different** — pre-change checkpoints are no longer comparable, and the shipped 18 are read-only
history. The fixed-limit byte-identical gate is therefore superseded **for this change only**, by the user's
instruction to alter the input representation; it remains in force for every future change that does not.

**Then:** all **nine variants** across the six rungs re-trained at the six-seat shape, 15,000 hands × seeds
0–2, the mixed pool, `net-chips`, as **concurrent single-threaded processes** on 24 cores. Every variant
reports its census, chips, **active-unit count** (the D-60 instrument) and **state-dependence** (distinct
score vectors, the D-59 instrument) — because the question is not only whether behaviour changes but whether
the input path survives at all.

---

## D-62 — "Model versions" means the mechanism grid, not the six architecture rungs

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "What I meant by 'model versions' was the net-chips vs. stack-shortfall +
double-Q vs counterfactual + flat vs. tokenized"

**Correction:** D-61's stage 2 specified the six rungs (`R1`…`R6`, the architecture and encoding ladder).
That was the wrong grid. The user's "model versions" are the **combinations of the three mechanisms those
rungs varied separately**:

| axis | levels |
|---|---|
| **utility** | `net-chips` · `stack-shortfall` |
| **estimator / signal** | masked-Q · `double-q-learning` · `reveal-counterfactual` |
| **encoding** | `flat-numeric` · `card-tokens` |

**= 12 cells**, each at six seats, 15,000 hands × seeds 0–2, the mixed pool `pool-8386c3ef83ae48b2`,
running **concurrently** as separate single-threaded processes.

**Why this grid is the right one:** the project measured each axis alone and found the utility decisive
(0 % → 78–93 % folding), the encoding a modulator under that utility only, the rule inert, the counterfactual
inert on top — and D-60 then found the *reason* the net-chip cells were inert: their trunks are dead. So the
grid asks the question the singles could not: **which combinations have a living input path, and does the
mechanism matter once the network can see?** The D-60 (active units) and D-59 (distinct score vectors)
instruments are reported per cell, and the [0,1] normalisation of D-61 is the precondition that may revive
them.

**Cancelled:** the nine-rung sweep (D-61 stage 2). The rungs R4/R5/R6 remain declared and unmeasured; they are
architecture questions and belong to a later pass, not to this grid.

---

## D-63 — Normalisation is real but inert; the cause is the value scale, and D-60's step 1 is refuted

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Normalize all input values to between 0 and 1 and then rerun training for all
model versions in parallel" — executed as D-61 + D-62.

**Result:** the **[0,1] invariant holds** everywhere (dense `[0.000, 1.000]` on all three shapes, token ids in
vocabulary, trunk input `(0.204, 0.630)`) and is now a battery assertion. But the 12-cell grid shows
normalisation changed **nothing**, for a reason my RCA got wrong: a before/after dump of every observation
over 4,744 decisions is **bit-identical**, because the dense slots were already inside [0,1] by D-30's
per-shape divisors. **D-60's step 1 — "large inputs drive large weights" — is refuted**; step 2, the O(100)
reward scale, is the whole cause.

**The grid (36 runs, six seats, 15,000 hands × seeds 0–2):** **six cells alive** (`stack-shortfall`, all
encodings and estimators: 12.7–31.4 active units, fold 74.7–93.6 %) and **six dead** (`net-chips`: **0 active
units** in the second hidden layer, one score vector over 3,143–10,700 observations), with **three
`LearningDiverged` crashes** in the net-chip × flat corner. The utility decides whether the trunk lives; the
encoding modulates magnitude only where it lives; the estimator is inert in both regimes.

**Correction to D-61's declared cost:** the shipped 18 containers stay **comparable** for the dense family —
their observations are bit-identical — and only the token path's trunk input changed.

**Decision:** the repair is the **value scale** (a normalised or bounded target on the utility axis), not
another input transform, not an architecture rung (`R4`/`R5`/`R6` stay declared and unmeasured, D-62), and not
another estimator. That is the next experiment, and it is the last one this cause admits.

---

## D-64 — The grid ran twice; both passes agree at seed level, and pooled census shares are invalid

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (L0's own defect):** I launched the corrected 12-cell brief (`subagent-508`) before the earlier
pass (`subagent-507`) had stopped, so **two concurrent L1 passes ran the same grid** on the same pool,
seeds and budget. Both reported `PASS`; their summary numbers disagree.

**Reconciliation, done by hand before either set was published:**

- **Seed 0 of `net-masked-flat` agrees to rounding**: 3,934 decisions / raise-minimum 61.5 % / check-call
  38.5 % in one pass, 3,935 / 61.7 % / 38.35 % in the other — and both match the pre-change record, as they
  must, because the encoder's output is **provably identical** pre- and post-change on real readouts (all
  four shape × encoding combinations, max difference **0.0**, checked by importing the pre-change package
  from `git archive 0e030e1`) and the dense backend was untouched (only the token path gained the `tanh`
  squash).
- **The summary rows differ because one pass pooled census shares across seeds whose policies differ** —
  seed 0 raise-minimum 61.5 %, seed 1 raise-all-in 57.9 % with 39.1 % folding, seed 2 check-call 100 %. A
  pooled "census" of three different attractors is not a policy; that is the trap `attractor-sweep.md`
  recorded and this row re-learns.
- The two passes also differ on the **band refusals**: one saw three `LearningDiverged` at the 1e6 band, the
  other two, and reported that both completed on an identical retry — so the refusal is an intermittency,
  not a cell property.

**Substantive verdict, identical in both passes:** **the utility is the only axis that revives the trunk.**
Every `net-chips` cell is a constant function (0 active units in the second hidden layer, one score vector
over hundreds to thousands of observations, ‖hidden‖ 0.00 against a bias of 10–57); every
`stack-shortfall` cell is alive (19–25 active units per layer, distinct score vectors equal to distinct
observations). The encoding modulates only where a trunk lives; `double-q` and `reveal-counterfactual` are
indistinguishable from the seed spread.

**Decision:** the substantive finding stands and both passes support it; **per-seed tables are the form of
record and pooled census shares are not**, from here on. The duplication was my scheduling error, and the
cost was two grids' worth of compute rather than a wrong conclusion.

---

## D-65 — The trunk dies by weight explosion at hand ~600, then freezes on a zero gradient

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "RCA how the trunk is dying. The input data should be sufficiently diverse and
meaningful that the code can't justify ignoring it entirely without errors being made"

**Finding, from ten snapshots over 3,000 hands:** ‖w_in‖ goes **11.0 at hand 300 → 298.6 at hand 600 → and
then stays 298.6 to four significant figures for the remaining 2,400 hands**, with ‖b_in‖ 78.87 and ‖w_out‖
312.0 likewise frozen while only `b_out` drifts. That freeze is a **zero gradient**: every trunk unit's
pre-activation is negative, the rectifier's derivative is 0, and no gradient reaches the input path again.

**Why the explosion:** the reward is ±600 chips a hand, so the first TD errors are |δ| ≈ 600 and one step is
`lr·δ·x` ≈ **0.6 per hand** at the declared 1e-3. The weights climb ~1 per hand and reach 300 within 300
hands, at which point every unit dies.

**The window is narrow, and that is the answer to the challenge:** at **1e-6** the weights stay at their
initial values for all 3,000 hands (‖w_in‖ 8.471 from hand 300 onward, `b_out` 0.022) — nothing explodes and
nothing learns. So `lr × reward-scale` must be small enough not to explode and large enough to move within
the budget, and at a 600-scale reward **1e-3 explodes while 1e-6 stalls**: no rate in that span works.

**Consequence:** the input *is* informative and ignoring it *does* cost error — but the cost never reaches the
input path, because a dead rectifier has zero derivative. The loss is sound; the parameterisation and the
value scale are not. The fix is a **normalised reward** (or a bounded advantage target), which places the
declared rate inside the window — and that is also why `stack-shortfall`'s O(1) reward leaves its trunks
alive (D-60, D-63).

---

## D-66 — Test the normalised reward: the one predicted repair for the dead trunk

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Proceed with normalized reward test"

**What is tested:** a new utility on D-20's axis — **net chips ÷ (seats × starting stack)**, so the six-seat
range is `[-1, +1]` — differing from `net-chips` in **scale and nothing else**: terminal-only, same axis, same
encoders, same containers.

**The prediction, stated before the run:** with the reward in `[-1, 1]`, one step is `lr·δ·x` ≈ 1e-3 rather
than **0.6**, so **‖w_in‖ should stay of order 10 rather than 298.6, the trunk should keep live units, and the
policy should become state-dependent** — none of which any `net-chips` cell has achieved (‖w_in‖ 298.6, zero
active units, one score vector over thousands of observations).

**Six cells** at six seats, 15,000 hands × seeds 0–2, the mixed pool: the normalised reward × {masked-Q,
`double-q-learning`, `reveal-counterfactual`} × {`flat-numeric`, `card-tokens`}, run concurrently. One cell
carries a **snapshot trajectory** at hands 300/600/1,500/3,000 — the direct test of the explosion that D-65
measured between hands 300 and 600.

**Why this is the right test and the last one of its kind:** D-65 established that at a 600-scale reward **no
learning rate works** — 1e-3 explodes the weights in 300 hands and 1e-6 never moves them. The only remaining
term in that arithmetic is the reward's magnitude, and it is the one the utility axis owns. If the trunk dies
under a normalised reward too, the cause was not the scale and the RCA must be reopened; **no threshold will be
invented to rescue it**.

---

## D-67 — The normalised reward revives the trunk: D-65's mechanism is confirmed causally

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Proceed with normalized reward test"

**Result:** every part of D-66's stated prediction held, on 18 concurrent runs at six seats, 15,000 hands ×
seeds 0–2:

| measure | `net-chips` (recorded) | normalised | predicted |
|---|---|---|---|
| ‖w_in‖ | 298.6–313 | **8.44–10.01** | order 10 ✔ |
| active units L1 / L2 | **0 / 0** | **14–30 / 12.9–26.9** | alive ✔ |
| distinct scores ÷ distinct observations | **1** over thousands | **1.000 in all 18 runs** | state-dependent ✔ |

**The mechanism is confirmed causally:** the reward's magnitude set the step size, the step size exploded the
weights, the explosion killed the rectifiers, a dead rectifier froze the parameters. Normalising the reward
puts the declared rate inside the window and the network reads its input again — the first state-dependent
policy this project has produced outside `stack-shortfall`.

**Behaviour:** flat cells fold 4–21 % at −3.4 to −7.1 chips/hand; token cells fold **55.3 %** at **−0.15 to
−1.2** — four to forty times smaller losses than flat. The estimator axis is **inert even in a live network**
(active units 15.0 / 15.4 / 15.3 at flat and 26.3 / 26.2 / 26.5 at tokens; fold 6.1 / 6.6 / 9.6 %), a stronger
statement than the dead-trunk null it replaces.

**Flagged, unexplained:** all nine token runs report **exactly 55.3 %** fold across three cells and three
seeds. That is too exact to be independent convergence and is recorded as unexplained rather than as
behaviour; it is the first thing to check if this line continues.

---

## D-68 — The 55.3 % was one policy reported nine times, and folding is conditional on the opposition

**Status:** ACTIVE · **Date:** 2026-11-08

**Source:** D-67's flagged anomaly — nine token runs, three estimators × three seeds, all reporting exactly
55.3 % fold.

**Finding:** they are **the same function**. Four token models replayed on one fixed 150-hand table chose fold at
every decision, and all six pairwise action-sequence comparisons were **identical**. On the census pool, folding
is legal in **55.3 %** of the learner's decisions — exactly the reported share — so the models fold *whenever
they can*, and 55.3 % is how often the pool offers it.

**But they are not constant folders:** on a table of two folders and a caller the same models diverge — `norm-tok`
folds 120/120, `short-flat` 88/120, `norm-flat` 20/120, and `short-tok` **0/120**. Behaviour is conditional on
the opposition, and the token+shortfall model that folds 92.7 % on its pool folds not once against an all-passive
table.

**Consequences:** (1) the estimator axis's apparent agreement at tokens is **one measurement, not three**;
(2) the encoding claim is better stated as *tokens fold whenever the pool lets them, flat folds three times in
four* — a real difference and a cleaner one to explain; (3) **both claims must be re-measured on the other's
table before either is presented**, because the direction reverses with the opposition.

**For the talk:** the defensible sentence is narrower than the prepared one — *the risk-averse utility makes the
agent fold whenever folding is legal against a betting pool, and the token encoding makes it do so more
consistently, while against an all-passive table the same models stop folding entirely.* Conditionality is the
finding; the percentage is a property of the opposition.

---

## D-69 — The cross-condition check exposed era mixing; D-68's token findings stand, older token censuses cannot be reproduced

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "proceed" — with D-68's cross-condition check.

**Result:** the replay **contradicted the recorded censuses** (`short-tok-s0` folded 0 % of 460 decisions where
its own greedy pass recorded 91.8 %), so the harness was tested first: the same file, same table, same seeds now
plays **raise-half on 400 of 400 decisions**. The file did not change; **the code did**.

D-61's bounded embedding — `row = (1 + tanh θ)/2`, applied at forward time — **silently reinterprets every
pre-squash token checkpoint**. All token models in `/tmp/token-shortfall`, `-seeds36`, `/tmp/token-build` and
`/tmp/token-dq` predate it and cannot be evaluated meaningfully now.

**What survives:** **D-68's token findings** (the nine runs are one policy; it folds whenever folding is legal),
because those were measured on `norm-*` models trained **and** evaluated after the squash — internally consistent.

**What does not survive as current measurement:** every recorded token census from before D-61 — D-53's 92.7 %,
D-56's seven-seed table, D-63's grid. They were correct **in their era** and remain true statements about models
that no longer exist; reloading the same files cannot reproduce them.

**Invalid:** this pass's cross-condition table, which mixed eras and therefore measures nothing in its `short-*`
rows.

**To close D-68:** train a **post-squash stack-shortfall token model** (one cell, three seeds) and run the
cross-condition test entirely within one era. Until then the conditionality claim rests on a single cell and is
not a contrast.

**Lesson recorded:** changing a forward pass must declare **the era of the containers it invalidates**. D-61
declared the dense family comparable — the encoder dump proved that — but not the token family, and this is the
cost of that omission.

---

## D-70 — A loaded-deal scenario suite: does the model's play depend on its cards?

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Set up a test suite that contains loaded games setting up a variety of hands of
different strengths, ex. paired aces, K-Q (on/off-suite), paired 2's, 8/7 (on/off-suite), 7/2 (on/off-suite),
etc. with both helpful and unhelpful community cards for each hole set"

**Why this is the right instrument now:** every behavioural result in this project has been an **aggregate
census** — a share of actions across thousands of hands — and D-59 showed that an aggregate can look like a
strategy while being a constant function. A loaded-deal suite replaces the census with the question directly:
*what does this model do when it holds aces, and what does it do when it holds seven-deuce offsuit?*

**Decision:** build a **declared table of concrete scenarios** — cards spelled out, each hole set against one
board that helps it and one that does not, with boards reused across hole sets where that is the honest
comparison — served by a **declared loaded-deal surface** that plays a hand with prescribed hole cards and board,
validates every malformed deal by name, and leaves the seeded path byte-identical.

**Measurement discipline:**
- the model's decision is reported **before the flop and on the flop**, with the scored values, so the table
  reads as behaviour rather than as an average;
- **only post-D-61 models** are used (`/tmp/reward-scale/checkpoints/norm-*`), because D-69 established that
  earlier token checkpoints are silently reinterpreted by the bounded embedding and cannot be evaluated today;
- the answer required is binary and plain: **does the action depend on the cards at all** — AA against 72o, and
  a helpful board against an unhelpful one for the same hole cards — and if it does not, that is the result.

This supersedes the census as the primary behavioural instrument; censuses stay for population-level questions,
but every "the model does X%" claim in the talk must be backed by a scenario table showing *when* it does X.

---

## D-71 — The scenario suite refutes the behavioural reading of the token encoding claim

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Set up a test suite that contains loaded games setting up a variety of hands of
different strengths … with both helpful and unhelpful community cards for each hole set"

**Built:** the loaded-deal surface (`new_hand(seed, shape, deal)`, `play_hand(..., deal=)`, six named refusals,
`InvalidDeal`, endpoints still 50) with the seeded path proven **byte-identical — 71,774 of 71,774 leaves** —
and sixteen scenarios run against the six post-D-61 cells × seeds 0–2 in two seatings (576 decisions).

**The answer:** **flat models use their cards; token models do not.** For flat, AA and 72o diverge and a helpful
board moves the flop action for **3–7 of 8** hole sets at every seed. For tokens, **all sixteen hands are folded
at every seed** wherever folding is offered, regardless of holding aces.

**And the token arms are blind rather than collapsed:** they produce 8–24 distinct score vectors per seating, so
their values move with the hole, but the argmax is pinned to `fold`-when-legal. Their *decisions* cannot change.

**Consequence:** this **refutes the behavioural reading** of the encoding claim. D-56's "tokens fold 92.7 %
against flat's 77.5 %" and D-67's "tokens lose four to forty times less" are both true and both mean the opposite
of what the percentages suggested: the token models lose less **because they fold cheaply**, not because they
play better. **The flat models are the only ones in this project whose decisions depend on the cards.**

**Also recorded:** `norm-doubleq-tokens` seed 2 shoves all-in preflop in all sixteen scenarios (an all-in, not a
missing row), and seeds agree action-for-action only for the token cells in the opening seating — the attractor
lottery, unchanged.

This supersedes every aggregate-census claim about what the models "do": the census is retired as the primary
behavioural instrument (D-70), and the scenario table is now the form of record.

---

## D-72 — The fold-pinning is a data-starvation loop, proven by the exploration floor

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Pinning into fold-when-legal is a training failure, RCA"

**Not the cause:** not a near-tie (fold wins by a mean **+0.0157**, range +0.0022 to +0.0523 across 164
scenarios); not a card-blind network (D-71: 8–24 distinct score vectors); not a dead trunk (D-67: 22–30 active
units); not the reward's scale (these cells are already normalised).

**The finding:** fold's own value averages **−0.0027** — the blind loss, which is *correct* — while every
alternative sits at **−0.01 to −0.14**. The model folds because it estimates that **playing on loses more than
folding**, and that estimate is self-fulfilling: folding ends the hand, so the on-policy samples that would
price the other actions are never collected.

**Proven by one parameter.** Same configuration, pool and 5,000 hands, only the exploration floor changed:

| arm | fold |
|---|---|
| **ε_end 0.05** (declared) | **92.9 %** |
| **ε_end 0.60** | **0.0 %** (raise-minimum 63 %, call 27 %, all-in 10 %) |

**The pinning vanishes entirely when the learner is forced to keep trying the other actions.**

**Why the token arms pin and the flat ones do not:** their action values are compressed into a narrow band
(~0.05 against the flat arms' ~0.3), so a smaller estimation error is enough to make fold win, and less data
locks it in.

**Remedies, in order:** **raise the exploration floor** — one declared number, measured to move fold from
92.9 % to 0.0 % — and, if that is not enough, **estimate the values of actions not taken**, which is exactly what
D-39/D-40's reveal-only counterfactual does. It was set aside because it did not fix folding in a two-player
pool; this RCA says it was aimed at the wrong symptom.

---

## D-73 — The counterfactual breaks the fold loop but not the card-blindness; the failure has two layers

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Try the second option" — D-72's second remedy, the off-policy counterfactual.

**Result, one key apart, 5,000 hands × seeds 0–1:** the `reveal-counterfactual` member cuts fold from **93.1 % to
29.6 %** and raises decisions per run by 57 % — the agent plays on, so the samples that price playing on arrive.
D-72's mechanism is confirmed by a second, independent remedy.

**But it does not touch the card-blindness.** On the loaded-deal probe (same dry board, same seat, three hole
sets): control folds AA, 72o and KQs alike at both seeds; the counterfactual **calls all three at seed 0 and folds
all three at seed 1**. It changes *which constant* the model picks, not *whether it picks by its cards*.

**The failure therefore has two layers**, and the three remedies tried separate cleanly across them: the **reward
scale** (D-67) and the **exploration floor** (D-72) and the **counterfactual** all move the control layer — which
action the policy settles on — while **none moves the discrimination layer**, whether the decision depends on the
hole cards. The only card-dependent models in the project remain the **flat** encodings under the scenario suite
(D-71).

**The sharpest open question:** why a token model whose score vectors are demonstrably live (8–24 distinct
vectors per seating) still maps every hand to one action. That is now the question a further pass should attack,
and it is a representation question, not a reward or exploration one.

---

## D-74 — The cards are not meaningfully distinct: the token embedding is still its initialization

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Cluster-map the embedding vectors. Are the cards meaningfully distinct?"

**Answer:** **no.** The 52 card rows are distinct only as random vectors are distinct (pairwise cosine −0.435 to
+0.453, mean −0.001), and they carry **no card structure**: same-rank pairs average **+0.0071** and same-suit
**+0.0072** against unrelated pairs' −0.0049, an excess of 0.012 against a per-pair spread of 0.139.

**The decisive measurement:** seven named pairs match a fresh `PCG64(0)` draw **to four decimals**, and `model.py`
initialises from exactly that generator — so the trained table **is** its initialization. Movement over training
is **max |Δ| 0.0004** against a row scale of ~0.14, i.e. **0.3 %**; two independent runs are 0.0004 apart from each
other as well.

**Mechanism (leading hypothesis):** only the **addressed rows** receive gradient, the mean-pooling divides it
across every token position, and the bounded squash's derivative is ≤ 0.5 — so each row's share is tiny and
thousands of hands move it by a fraction of a percent.

**This closes D-73's open question:** the token model maps every hand to one action because it reads a **random
projection** of its hole cards, not because the trunk or the estimator is inadequate. The flat encoding, which
feeds 433 values directly into the trunk, is the only one in this project whose play depends on the cards (D-71).
The discrimination layer is a **representation** failure, located.

---

## D-75 — The embedding learns at 0.3 % because its gradient is divided by 122

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Why is the embedding learning so slow?"

**Cause, from the backward pass:** `add.at(gathered, ids, (upstream / len(ids)) * slope)` divides every addressed
row's gradient by the **whole observation length — 122 positions at six seats — of which only 14 carry a real
token.** Each card row therefore receives **≤ 1/122 × 0.5 ≈ 0.0041** of the upstream gradient per appearance,
against a flat input slot's full share, and only when that exact card appears.

**The arithmetic closes against D-74's measurement:** `appearances × lr × upstream × 0.0041` at `lr = 1e-3`, an
upstream of order `1e-2`, and hundreds to a couple of thousand appearances gives **order 1e-4** — the measured
**max |Δ| 0.0004** on a row scale of 0.14. The 0.3 % is predicted by the dilution, not an accident of tuning.

**Remedies, cheapest first:** divide by the **real** token count or mask padding out of the pool (recovers 8.7×,
one line); drop the squash or widen the embedding scale (another ≤ 2×); sum-pool instead of mean-pool; or use the
flat encoding, which has no pooling and is the only card-aware encoding in the project (D-71).

**Consequence for every earlier encoding result:** the token encoding never had a fair test — its card
representation received **0.4 %** of the learning signal the flat encoding's did, throughout. D-52, D-56, D-67,
D-71 and D-73 are statements about an **untrained embedding**, not about tokenisation as an idea, and must be
reported that way.

---

## D-76 — The three dilution remedies, run under the flat encoding's best configuration

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Try the first three, in parallel, using the current best performing training
combination from the flat encodings"

**The three remedies** become a declared axis on the token path only, each defaulting to today's behaviour so
every existing run reproduces byte-identically:

1. **`mean-real`** — divide the pooled gradient by the **non-padding** token count (14), not by `len(ids)` (122):
   recovers **8.7×**.
2. **`no-squash`** — drop the bounded embedding `(1 + tanh θ)/2`: recovers up to **2×** and removes saturation.
3. **`sum-pool`** — sum rather than mean: removes the denominator entirely.

**The configuration is the flat encoding's best, not the token default:** `stack-shortfall` (the best chips among
the flat arms, −1.14 to −1.20 against −1.8 to −7.1 elsewhere), masked-Q, six seats, the mixed pool, **15,000 hands
× seeds 0–2**, the three arms concurrent.

**What decides it:** embedding movement against its own initialization (does the table leave its draw at all), the
appearance of rank/suit structure, the greedy census and chips, and — decisively — the **loaded-deal probe**:
`AA` against `72o` offsuit on the **same dry board**, at the opening seat where folding is legal and at the
big-blind seat where it is not. Three remedies have already moved *which constant* the models choose without
moving card-dependence (D-67, D-72, D-73); this asks whether the representation was the missing term.

**Falsifiable prediction, stated before the run:** with the dilution removed the embedding should move by roughly
the recovered factor and the token arms should **start discriminating AA from 72o** in the loaded-deal probe — the
test that has failed for every token model so far. If the embedding moves and the decisions still do not depend on
the cards, the representation was not the only missing term and D-75's remedy list is incomplete.

---

## D-77 — The dilution remedies work on the embedding and leave behaviour unchanged

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Try the first three, in parallel, using the current best performing training
combination from the flat encodings"

**Executed as probes** (the declared axis needs three shipped assertions rev'd and a `src/training/` change, which
L4 reported rather than shipping). Applied to the **torch** backend, which is R3's; patching numpy first produced
four identical arms and was caught by comparing embeddings — a probe error, recorded.

**The remedies work exactly as the arithmetic predicted:** embedding movement from initialization **0.0056 →
0.0468 (8.4×)** for `mean-real` (predicted 8.7×), **0.0179 (3.2×)** for `no-squash` (predicted ≤ 2×), and
`sum-pool` **diverges** past the 1e6 band (the 122× amplification). **D-75's dilution was real and is fixed.**

**And behaviour does not move at all:** fold 93.0 / 92.7 / 93.0 / 93.1 % for today / `mean-real` / `no-squash`
(masked-both); the loaded-deal probe returns **the same decision for AA, 72o and KQs in every arm** — `fold` in
three, `raise-half` for `no-squash`. **Not one remedy makes the model treat aces differently from seven-deuce.**

**The honest conclusion:** D-74/D-75 correctly explained the *slow learning* and were **wrong about the
blindness**. D-75's remedy list is incomplete — the failure mode D-76 named before the run. What remains
consistent with every measurement: the policy is set by the **exploration loop** (D-72: 93 % at ε_end 0.05, 0 % at
ε_end 0.60), and inside that loop the risk terms make the six action values nearly equal, so the winner is decided
by a margin the cards do not enter. The card signal reaches the trunk; the decision does not use it.

**Practical consequence:** the **flat encoding is the only card-aware family** (D-71) and should carry any
demonstration of card-dependent play. The token path needs a change that reaches the *decision*, not the
representation — a different and larger piece of work than a pooling fix.

---

## D-78 — The card rows of the embedding barely move; D-77's 8.4× was the padding row

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "How different are the embeddings in the mean-real version"

**Answer:** essentially not at all. Row-by-row cosine between the baseline and `mean-real` over the 52 card rows is
**1.000000 (min and max), a turn of 0.01°**; the card rows moved max **1.2 × 10⁻⁵ → 7.7 × 10⁻⁵** (6.3×) while the
**padding row moved 0.0056 → 0.0468 (8.4×)**. The whole-table difference I reported as "the embedding moves 8.4×"
in D-77 was **the padding row**, not the cards.

**Why:** the backward scatter writes to **every** addressed position, and 108 of 122 positions are padding. Raising
every share 8.7× therefore inflates the row addressed 108 times per decision, while a card row addressed once or
twice gains 6.3× from a negligible base.

**Only the `masked-both` probe fixes the right row**: padding excluded from pool and scatter gives a padding-row
movement of **exactly 0** and card-row movement of **1.2 × 10⁻⁴ (9.5×)** — which is still **0.02 %** of the initial
row scale of 0.55.

**Consequences:** (1) D-77's "trains 8.4× faster" is corrected to a padding artefact — the dilution is real and the
remedy real, but the **absolute** card learning stays negligible, a second independent reason a 108-padding pooler
cannot learn card identity in thousands of hands; (2) the behavioural null it reported stands, now with a much
better explanation; (3) any future token work must **mask padding out of both passes and check the card rows
specifically** — never the table-wide maximum, which is dominated by scaffolding.

---

## D-79 — The padding is pre-allocated worst-case capacity; the missing mask is the defect

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "What are the padding rows for?"

**Answer:** the observation is a **fixed-width sequence** — every decision on every street must produce the same
tensor — so its width fits the **worst case** and the unused remainder is filled with the pad id 0. At six seats
that width is 122: **24 tokens before the history** (street 1, seat block 6, hole 2, board 5, stacks 6, `pot` 1,
`to_call` 1, `limit` 2) plus a **98-token history block** sized for the longest legal hand at this shape.

**Measured on a preflop decision: 14 real, 108 pad — 89 %.** The history block is the bulk of it (zero entries
preflop, a handful even in a long hand), and the board's five slots are empty until cards are dealt.

**The padding is correct; the mask is missing.** A fixed width is ordinary sequence practice and its standard
companion is a mask. This project pools `rows.mean(dim=0)` over all 122 positions and scatters the gradient to all
108 pad positions, so **89 % of the trunk's input is one constant vector and the pad row absorbs most of the
learning signal** — which is exactly the per-row asymmetry D-78 measured (pad row 8.4×, card rows 0.01°).

**The fix is the mask, not the width:** keep 122 tokens, exclude pads from pool and scatter. The `masked-both`
probe is that change and moved card rows 9.5×, still only 0.02 % of their scale in 5,000 hands — the second,
separate limit D-78 recorded.

---

## D-80 — Masked token models: the first non-zero card sensitivity, narrow and fragile

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Rerun the last training test with a mask"

**Result** (`stack-shortfall`, `card-tokens`, 5,000 hands × seed 0, padding masked out of pool **and** scatter):

| arm | fold | pad-row movement | card-row movement | card-sensitive |
|---|---|---|---|---|
| **mask** | 93.1 % | **0.0 exactly** | 1.17 × 10⁻⁴ | **no** — every hand folds |
| **mask + `no-squash`** | 89.5 % | **0.0 exactly** | 1.33 × 10⁻⁴ | **yes, weakly** |
| mask + `sum-pool` | diverged past the 1e6 band | — | — | — |

**The mask works**: the padding row moves exactly zero in both surviving arms, against 8.4× the card rows'
movement without it (D-78).

**The sensitivity, stated narrowly:** with mask + `no-squash`, five hole sets on one dry board give **two distinct
action sequences at the opening seat** — `72o` separated from AA, KQs, 22 and 87s on the flop — and **one sequence
at the big-blind seat**. It separates only the weakest hand, only on one street, only where folding is legal.

**Why it is narrow:** both changes were necessary (the mask alone leaves every hand folding; `no-squash` alone
changes the constant without discriminating), and the card rows still move only **1.3 × 10⁻⁴** against a row scale
of 0.55 — 0.02 % — because a card is addressed once or twice per decision.

**What it means:** the token representation **can** carry card information once the padding stops dominating it, so
D-71/D-73/D-77's unanimous null is broken — and this is still not a card-aware agent. The flat encoding remains the
only family that discriminates broadly (AA ≠ 72o, 3–7 of 8 board contrasts, D-71).

---

## D-81 — Annealing from a hot start rescues nothing and erases the token flicker

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Run a pass with annealing behavior to start with very aggressive learning and tone
down to current speed"

**Run:** learning rate scheduled geometrically from **3 × 10⁻² to the declared 10⁻³** over the first 60 % of 5,000
hands (verified in-run), at `stack-shortfall`, six seats, seed 0, on the flat baseline and on the token frontier
(mask + `no-squash`).

| arm | fold | fixed-rate record | card-dependent |
|---|---|---|---|
| **flat** | **91.3 %** | 78–87 % | **yes** — 2/5 opening, 3/5 big-blind |
| **tokens** | **90.8 %** | 89.5 % | **no** — 1/5 both |

**It helped neither arm and hurt one:** the fold share rose on both, and the token arm's single card-sensitivity
(D-80: 72o separated at the opening seat) is **gone** — all five hands identical at both seats under annealing.

**And what discrimination remained is not sound play:** the annealed flat model **folds AA** at the opening seat
while shoving all-in with KQs — it reads the cards and reads them wrongly, a reminder that card-dependence is
necessary for a poker agent and far from sufficient.

**Why:** a 30× hotter start drives the first few hundred updates well above the usable `lr × reward-scale` window
D-65 measured, moves the parameters a long way before the exploration ramp yields diverse experience, and lands in
the attractor the annealed end cannot leave — the same rate D-72 showed pins the policy to fold on its own.

**Conclusion:** annealing is not the missing mechanism. The pinning is the **exploration loop** (D-72) and the
discrimination is the **representation** (D-79/D-80); a schedule over the learning rate touches neither.

---

## D-82 — The token flicker does not survive the budget: three seeds, one constant each

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Proceed with that attempt" — D-80's masked-no-squash arm at **15,000 hands × seeds
0–2**, fixed rate.

**Result:** **every seed plays every hand identically**, in both seatings, on five hole sets (AA, KQs, 22, 87s,
72o): seed 0 all `raise-quarter`, seed 1 all `raise-half`, seed 2 all `check-call`. Fold share 88.6 / 86.5 / 90.3 %.
**Distinct sequences: 1 of 5 in all six cells.**

**So D-80 is corrected:** the 5,000-hand card separation was a **transient of short training**, not the token
encoding beginning to read its hand. At three times the budget the pinning reasserts completely, and the only thing
that varies is which constant — the attractor lottery.

**Why more hands erase rather than build:** the mask and squash-removal work (padding row stops absorbing the
learning, card rows move 9.5× further, D-78), but a card is addressed once or twice per decision, so 15,000 hands
move a card row ~10⁻⁴ against a row scale of 0.55; meanwhile exploration decays to 0.05, so the longer run converges
**harder** onto the constant and the short run's noise was exactly what produced the flicker.

**Standing rule, re-learned:** a behavioural difference measured at the live budget must be re-measured at a longer
budget before it is called a capability. The token encoding's card-blindness is now measured at 5,000 **and** 15,000
hands, three seeds, two seatings, five hole sets, with the padding masked and the squash dropped.

---

## D-83 — A simplified equity model works, and its 2.4 % ceiling explains the policy failure

**Status:** ACTIVE · **Date:** 2026-11-08

**Source (user, verbatim):** "Try a simplified model: instead of trying to game pass/raise/fold, try to estimate the
odds that a hand will win in a six-player game, using just the cards. Later this probability can be fitted into the
model if it proves more capable of learning"

**Result:** a 34-input one-hot (rank + suit per hole card) into a 64-64 MLP, trained on **900,000 samples from
150,000 random six-way deals**, learns the win probability: **most hands within 1–3 points of the empirical rate**
(AA 44.7 against 52.2, KQs 29.6 against 29.8, 22 12.8 against 14.1, 72o 10.4 against 8.7), the ordering correct, and
the **calibration curve close to the diagonal by decile**. **The network can estimate poker equity from cards** —
precisely what it never managed for the policy.

**And the same measurement sizes the original problem:** card identity explains **2.4 % of the variance** in a
six-way win/lose outcome (held-out MSE 0.13004 against the constant predictor's 0.13325). The board and five unknown
opponent hands account for the rest. That is the signal the value function was trying to bootstrap from — the same
structure that left the action values nearly equal (D-72) and the game "nearly a coin flip".

**On the proposed next step:** feeding this probability into the policy model is right and cheap, because it is a
well-calibrated supervised estimate of exactly the quantity the value function estimates from noisy returns. Two
caveats stated: it is **marginal over random opponents**, so it must be recomputed or conditioned for a real pool; and
its 2.4 % ceiling means it should sharpen the **ranking** of hands, not make decisions profitable by itself.
