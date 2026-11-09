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

**Consequences the design must carry.** `fold-no-pair-or-better` needs a hand-strength fact that the
readout does not expose today, so either `engine`'s readout gains one or `features` gains an
evaluator — `agents` must not import `pokerkit` (D-13). Baseline count changes pool membership and
therefore K and the K(K−1)/2 cell count, so the table's cost moves with it (ASM-14). The e2e battery's
baseline family asserts three and must be extended, never weakened. The shipped artefacts were
measured over a three-baseline pool and are not re-baselined by this row.
