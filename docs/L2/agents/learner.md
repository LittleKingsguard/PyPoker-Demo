# agents — the learner family, the baselines, and the contracts at this edge

- **Layer:** L2 · **Module:** `agents` · **Unit:** phase1 · **Rev:** 5 · **Date:** 2026-11-05
- **Owner of this file:** the one learner family and the R1↔R2 backend axis (§1–§2), the parameter budget
  (§3), a version as a checkpoint (§4), the three fixed baselines (§5), the contracts `features`, `engine`,
  `training` and `evaluation` hold at this edge (§6–§8), the battery invariants this module carries (§9) and
  what is left to L3 (§10) (D-6, D-7, ASM-7, ASM-10, D-13)
- **Ceiling:** 250 lines. At the ceiling, split by owner — never append

## 1. One learner family: masked Q-learning

The ladder has one learning rule and it is fixed for the whole ladder: masked Q-learning over the
three-index action vocabulary (ASM-7). A learner is a function from an observation and a legal mask to three
values; the value of an index outside the mask is never read, never a target and never updated, so a masked
update re-derives nothing the transition record already carries (`records.md` §4, ASM-7).

- **The aim.** For each transition the value of its `action` moves toward a target: the transition's
  `reward` when it is `terminal`, and `reward + discount × max` of the successor's values **over
  `next_legal`** otherwise (`records.md` §4, ASM-7). The masking is the contract: an index outside
  `next_legal` is not a bootstrapping candidate (D-2, `records.md` §4).
- **The reward.** The seat's net chip delta for the completed hand, delivered at that seat's terminal
  decision and zero at every other one, with no shaped term and no intermediate reward — this module adds
  none (ASM-12, `engine/environment.md` §3).
- **The exploration.** An ε-greedy draw governed by the schedule `learners()` declares, from the learner's
  own seeded generator and **keyed by the decision**, a decision being the observation and the legal mask —
  so one learner state and one decision give one index, nothing depends on how many decisions came before,
  and a policy at the learner's own seed answers the same index for the same decision (`surface.md` §1, §6,
  §10, `protocol.md` §4). The schedule's position is part of the learner's state and advances inside `learn`
  and nowhere else (ASM-7, ASM-5).
- **The fixed declarations.** The rule and its hyperparameters — learning rate, batch size, target-update
  interval, optimiser family, exploration schedule and discount — are one value each for the whole ladder and
  are published by `learners()` so a report can name them (`surface.md` §3, ASM-7, `ladder.md` §3, §4). The
  `discount` is named by no L1 declaration — `ladder.md` §3 lists the other four and ASM-7 the optimiser
  family — and masked Q-learning's target cannot be computed without it: it is fixed here, for the whole
  ladder (ASM-7). A variant entry that names them (`records.md` §2, `ladder.md` §3) is the run record's data —
  the copy a pair's fairness check compares (`ladder.md` §4) — and not a per-learner argument, because a
  learner that took them would let one rung drift out of the one rule (ASM-7, `ladder.md` §1).
- **Nothing rung-shaped.** No entry point takes a rung, a variant name, an opponent, a hand count or a
  table budget, so no rung can carry a copy of the rule (`module-map.md` §3, D-3, `ladder.md` §1).
- **The signal.** `learn` reports a mean absolute TD error per batch, which exists in both backends and is
  therefore the ladder's common curve signal (`surface.md` §7, `protocol.md` §1).

## 2. R1 against R2: the backend is the only axis

D-7 gives the ladder a hand-rolled NumPy learner at R1 and PyTorch from R2 on, and R2 recreates R1 so the
speed difference is measured on identical work (`ladder.md` §5, D-7). At this edge that means one learner
family with one switch:

| The backend swap may change | The backend swap may **not** change |
|---|---|
| which library performs the arithmetic, and so the cost of that arithmetic (D-7, D-8) | the encoding: both variants declare one encoding, `flat-numeric`, whose observation family is `dense-numeric` (`ladder.md` §5, `encodings.md` §1, `surface.md` §3) |
| the checkpoint's own bytes, provided `save`/`load` stay loss-free at the decision boundary (§4, ASM-5) | the architecture kind and its width, depth, sparsity and residual settings — one model shape and one declared family (`ladder.md` §5, D-3) |
| — | the update rule, the reward and every hyperparameter, which are the ladder's fixed declarations (§1, ASM-7) |
| — | the sample order: `learn` consumes the caller's batch in the caller's order (`surface.md` §7, `ladder.md` §5) |
| — | the initialisation the seed defines, the exploration schedule and its keyed draws, and the tie-break among equal masked values (`protocol.md` §4, `surface.md` §1) |
| — | the decision boundary: one observation and one mask give one index, and a policy at the learner's own seed decides as `act` does (`surface.md` §6, §10, `protocol.md` §5) |
| — | the capacity: one model shape is one model, so the two backends' counts coincide under §3's one counting rule (`ladder.md` §5, ASM-10) |

What this buys is the same-work check `ladder.md` §5 asks for: the two backends are held to one initialisation
order, one forward-pass arithmetic order and one tie-break rule — a constraint on the design, whose
realisation is L3's (§10 below) — so on the same seeded hands against the same opponents they choose the same
actions, which is what FAM-13 asserts and what a parity row showing a large skill difference would falsify
(`battery.md` §3 FAM-13). The check is on **decisions and not on values**: two independent numerical libraries
are not guaranteed to round identically and the interface promises nothing about that. What it forbids is a
backend that differs in the model, the rule, the order or the tie-break; making the two forward passes agree
where a decision reads them is L3's obligation, since a decision reads three values and one comparison
(`ladder.md` §5, D-7, §10 below). R2's own evidence is the clock the run record and `harness.timings` carry,
never a wall clock the battery demands (D-7, D-8, ASM-15); R2 still reports its table, labelled a parity
comparison (D-16, `ladder.md` §5).

## 3. The parameter budget, as `param_count` measures it

A comparison pair — adjacent rungs and every intra-rung pair — is matched to 10,000 trainable parameters
within ±2%, measured by `agents.param_count` (ASM-10, `ladder.md` §4, §6). The measurement is one rule:

- **Counted:** every value the update can change — the input block first: for a dense kind the first layer's
  weights at the width the encoding declares, for a token kind the embedding table at the vocabulary the
  encoding declares, and then the value network the kind's `width` and `depth` fix (`encodings.md` §1, §4,
  §6, `e2e-surface.md` §3.3). The observation itself is never counted, being `encode`'s output and not a
  parameter (`features/surface.md` §6). Which layer weights and how many are the kind's design and L3's (§10
  below); what binds here is that the count covers the whole model and that it is measured by one rule.
- **Not counted:** a copy of the parameters kept for a target, any non-trainable buffer, and the exploration
  schedule's constants, because none of them is a trainable parameter (`e2e-surface.md` §3.3, ASM-10).
- **The count is a function of the spec and the seed, never of a decision handed to the learner.** A learner
  is complete at construction — sized from its encoder, or from its kind's declared `observation_size`
  (`surface.md` §3, §4) — so it holds one count for its lifetime, and the number is the capacity the budget
  is matched on whichever way its input was sized (ASM-10, `protocol.md` §4).
- **A pair is measured by one rule on both arms:** the rule and the hyperparameters are identical inside a
  pair and both arms are built from the same spec shape, so a matched budget cannot be an artefact of the
  measurement (`ladder.md` §4, ASM-7).
- **`sizes` never moves the number,** since `architecture` is authoritative when both are present
  (`records.md` §3).

## 4. A version is a checkpoint

D-16 makes a version a checkpoint of a run and a league member, so `save`/`load` is not a convenience: it is
what lets a shipped member decide as its learner did (D-16, `protocol.md` §5). The pair is **loss-free at the
decision boundary**, and the boundary is a function of state and decision rather than a stream position
(`surface.md` §1, §6, ASM-5):

- **What a restore must recover,** from the file alone, is everything a decision reads: the backend, the kind
  and its settings, the representation — the family the kind consumes, the size it was built for, and the
  encoding name, which is either the one the encoder declared or the one the kind's table names
  (`surface.md` §3, §4, §9, `encodings.md` §1) — the learner's seed, its parameter values, and its
  exploration schedule's position, and nothing is invented on the way back (`protocol.md` §5, ASM-5).
- **The record's own form is not contract:** what the file is called inside, how it is laid out and which
  identifiers it uses are L3's (§10 below). What binds is the recovery above and `surface.md` §9's refusals:
  a path that cannot be read, a file whose form this module does not read, and a spec that disagrees with the
  file on a key that spec carries — its `backend`, its kind, its `seed`, and, when it carries an encoder, the
  representation and size that encoder declares (`sizes` never disagrees, `architecture` being authoritative,
  `records.md` §3).
- **A shipped member's policy is built at the checkpoint's recorded seed,** which is why a checkpoint records
  it: at that seed the policy decides as `act` does, the loss-free equality `protocol.md` §5 states (ASM-5).
- **What this module contributes to a version record.** `records.md` §7 requires `id`, `path`, `rung`,
  `variant`, `seed`, `step`, `samples` and `lineage`; this module supplies the `path` `save` returns and the
  learner's `seed`, and nothing else — `rung` and `variant` are labels a learner never learns (D-3,
  `module-map.md` §3), `lineage` is the pool's ordering (`league.md` §2), and `samples` counts hands, which
  this module never sees (`records.md` §7, `surface.md` §7).
- **Retention is not this module's.** Ten equally spaced snapshots plus a final model, the last M kept in the
  window, is the run's and the pool's rule (ASM-18, `protocol.md` §5, `league.md` §2); `save` writes the one
  file it is asked for (`surface.md` §8).

## 5. The three fixed baselines

`random`, `always-call` and `oracle` are D-6's, none of them learns from a match, and all three are pool
members and matrix columns at the same hand count as every league cell — they are the only fixed standard a
self-play league has (D-6, `protocol.md` §3, D-16, `league.md` §4).

| Baseline | Its rule | What a battery can assert |
|---|---|---|
| `random` | a uniform draw over the decision's legal indices, from a generator seeded from the baseline's seed (`protocol.md` §3) | it never returns an illegal index; one seed agrees twice and two seeds differ (`protocol.md` §3, `surface.md` §12) |
| `always-call` | check/call whenever that is legal, never fold, and the minimum legal completion when raising is the only option (`protocol.md` §3) | it folds in no decision of any hand (`protocol.md` §3) |
| `oracle` | check/call when the hand's equity is at least the pot odds `to_call / (pot + to_call)`, and fold when that inequality fails and folding is legal (`protocol.md` §3, ASM-4) | its choice is consistent with that inequality at every decision, recomputable from `engine.equity` and the readout (`protocol.md` §3, ASM-4) |

- **The oracle is a rule, not a model.** Its equity comes from `engine.equity`, queried with the readout it
  was handed, **the seed the baseline was built with** and the sample count `baselines()` declares — so a
  caller holding that seed and that count re-issues the same query and checks the inequality itself
  (`surface.md` §11, `engine/surface.md` §11, ASM-4). The seed is the caller's own record of the baseline it
  built, which is why a rebuilt baseline repeats its decisions (`protocol.md` §3, §4).
- **The oracle is blind by construction.** It never raises, because a raise is not a pot-odds question: it is
  deliberately strong on the pot-odds axis `protocol.md` §3 names and blind on every other — it reads the pot,
  the amount to call and the equity, and nothing else: no history, no opponent, no adaptation (ASM-4, D-6).
  That blindness is what makes it a baseline rather than a competitor (D-6).
- **A baseline never learns, and its state advances nowhere.** `learn` refuses a value that is not a
  learner, and nothing here retains anything from a hand a baseline played, so a baseline's column is the
  same rule at every hand count and at every call order (`surface.md` §1, §7, §12, D-6, `protocol.md` §3).
  Because no state advances, a baseline's random draw is keyed by the decision as a learner's exploration is:
  a stream position could not give a uniform draw over each decision's legal indices once the order of
  decisions is free (`surface.md` §1, §12, `protocol.md` §3).
- **A baseline has no trainable parameters:** `baselines()` declares its `params` as `0`, and that declared
  zero is the count a cell records beside every other member's count — `param_count` refuses a baseline
  because a baseline is not a learner (`surface.md` §5, §11, `records.md` §9).
- **A policy receives only `(readout, legal_actions)`,** so a baseline is a function of the decision it is
  handed and never of the hand it is inside — which is exactly why `engine.equity` accepts a readout as well
  as a hand (`e2e-surface.md` §2, `engine/surface.md` §11, `engine/environment.md` §6).

## 6. The contract at the `features` edge (D-13)

What this module may rely on, stated as what it consumes and never as a description of that module's
internals (`module-map.md` §2, D-13):

- `observation_spec(encoder)` declares `representation`, `kind`, `fields`, `shape`, `dtype` and `vocabulary`;
  `shape` is a dense input's width and `vocabulary` an embedding table's row count, so a learner is sized from
  the spec, never from a width copied out of a document (`features/surface.md` §5, `encodings.md` §6);
- `observation_spec.kind` — `dense-numeric` or `token-sequence` — is the representation family, which is what
  a learner's architecture kind must agree with under the pairing `learners()` declares;
  `observation_spec.representation` — `flat-numeric` or `card-tokens` — is the encoding a variant declares,
  and each of the two maps onto exactly one family (`encodings.md` §1, `surface.md` §3, §4). The two keys are
  different keys of one record and this document never uses one for the other;
- `encode(encoder, readout)` returns one array of the declared shape and dtype, value for value, drawing no
  randomness and mutating nothing, so an observation this module trains on is reproducible from the readout
  (D-3, `features/surface.md` §6);
- `legal_indices(legal_actions)` returns the decision's legal indices, position-aligned with the descriptors
  it was given, distinct and ascending, and never empty — the mask `act` takes is exactly this sequence
  (`features/surface.md` §8, `surface.md` §2);
- `decode_action(index)` returns the descriptor `engine.apply_action` accepts, so the index a learner chooses
  becomes the action a policy returns (`features/surface.md` §9, `e2e-surface.md` §2);
- `action_space()` fixes the three output units of every learner and the vocabulary a report's header quotes
  (`features/surface.md` §7, `protocol.md` §1);
- **The edge is granted and five calls wide.** `module-map.md` §2 grants this module `encode`,
  `observation_spec`, `action_space`, `legal_indices` and `decode_action`, for the reason it states there: a
  learner consumes an observation and `as_policy` must encode the readouts its policy receives (D-3,
  `module-map.md` §2). `build_encoder` is not among the five, so the encoder always arrives from the caller —
  in a learner spec, in `as_policy`, or from `training` and `evaluation` — and this module builds none
  (`surface.md` §4, §10, `features/surface.md` §4, D-13).
- **The sizing rule is a contract in both directions.** `learners()` declares each kind's `observation_size`
  as a scalar width; it must equal the width of the `shape` a dense encoding's `observation_spec` declares — a
  one-element tuple — or the `vocabulary` a token encoding's declares, that vocabulary being the datum
  `e2e-surface.md` §2 makes the size of a token learner, never an observation's length. `build_learner` given
  an encoder must refuse a disagreement, naming both: the declaration and the encoding are held equal by a
  refusal and not by a comment, while a caller with no encoder is sized from the declared value and never from
  a width copied out of a document (`e2e-surface.md` §2, §3.3, `surface.md` §3, §4, D-3).

## 7. The contract at the `engine` edge (D-13)

- `readout(hand)` is the ten-fact information set, and this module reads it only as the thing a policy
  receives and an encoder consumes; it never asks a hand for anything (D-3, `engine/environment.md` §2).
- `equity(decision, seed, sample_count)` returns the acting seat's win probability in `[0, 1]`, takes a hand
  **or** that hand's readout, is repeatable for one decision, seed and count, and hands the global stream
  back as it found it — which is why an oracle can ask it mid-hand while `play_hand` drives that same hand
  (`engine/surface.md` §11, `engine/environment.md` §4, ASM-4).
- Nothing else in `engine` is called: this module never deals, advances, ends or pays a hand
  (`module-map.md` §2, §3, D-2).

## 8. What `training` and `evaluation` may assume

| Caller | May assume |
|---|---|
| `training` | `build_learner`, `act`, `learn` and `save` drive one learner and nothing else (`module-map.md` §2); every initialisation and every exploration draw comes from the learner's own generator seeded from the spec's `seed`, and the learner's schedule advances only inside `learn`, so a run is reproducible from its configuration and seed set and the deal stream is untouched (D-6, `protocol.md` §4, ASM-2); the batch it hands `learn` is consumed in its own order, so a pair's sample order is one (`ladder.md` §5); the curve comes from `learn`'s `td_error` (`protocol.md` §1) |
| `evaluation` | `baselines` and `build_baseline` yield the three policies a table needs as members, each with the `params` of `0` the catalogue declares (`e2e-surface.md` §3.4, `records.md` §9); `load` restores a member from its path alone and `param_count` reports that member's capacity (`records.md` §7, §9); `as_policy` at the member's recorded seed decides as its learner did, which is the equality `protocol.md` §5 asks for (ASM-5, `surface.md` §10); the encoder that call needs is `evaluation`'s own, because `module-map.md` §2 grants `evaluation` `build_encoder` and `encode` precisely so `policy_from` turns a checkpoint into a policy (D-16, `module-map.md` §2, this file's §6); no baseline's behaviour depends on any match it played (D-6, `protocol.md` §3) |

Neither caller may assume anything about a learner's internals, its file format, its error classes or its
arithmetic order: those are L3's (`module-map.md` §5, D-12).

## 9. The invariants the battery asserts against this module

Each family of `battery.md` §3 that lands here, with the entry points that carry it (`battery.md` §3, D-11):

| Family | What it asserts | Carried by |
|---|---|---|
| FAM-1 | all ten names exist and are callable, and a minimal call returns the declared kind (`battery.md` §3) | all ten (`e2e-surface.md` §3.3) |
| FAM-5 | the three baselines are exactly D-6's, each builds a policy of the protocol, `random` is uniform over the legal indices and seeded, `always-call` never folds, and the oracle is consistent with the pot odds against `engine.equity` when that query is re-issued at the baseline's own seed and the count `baselines()` declares (`protocol.md` §3, ASM-4, `surface.md` §11) | `baselines`, `build_baseline` |
| FAM-12 | `save`/`load` is loss-free at the decision boundary: a loaded checkpoint chooses the action its learner chooses on the same readout (`protocol.md` §5, ASM-5) | `save`, `load` |
| FAM-13 | R1 and R2 declare one encoding and one architecture, differ only in `backend`, choose the same actions on the same seeded hands, and report matched capacities (D-7, `ladder.md` §5, ASM-10) | `learners`, `build_learner`, `param_count` |
| FAM-16 | seven blind instances — an invented spec, an invented `param_count` pair, and an invented `act`, `learn`, `save`, `load` and `as_policy` (`battery.md` §4, D-15) | `build_learner`, `param_count`, `act`, `learn`, `save`, `load`, `as_policy` |

The other families reach this module only as a path: FAM-4's seed contract bites through the generator
`build_learner` seeds (`protocol.md` §4), FAM-3 and FAM-15 through the specs a custom rung hands
`build_learner` (`ladder.md` §3), and FAM-7 through the baseline policies `match` is given beside the
members it loads (`league.md` §3). The module's own internals belong to `tests/agents/` (`battery.md` §5,
`module-map.md` §5).

## 10. What is left to L3

This document stops at the entry point and at the records they exchange. `role_l3_designer` owns the module
design (D-1, `module-map.md` §5):

- the learner's own type and what it holds, which no caller may inspect (`surface.md` §1);
- how one backend realises the forward pass and the update, and how the two backends are made to agree on
  the decisions §2 requires (`ladder.md` §5, D-7);
- the initialisation order the seed defines, the tie-break among equal masked values, and how the keyed
  exploration draw of §1 is derived from the learner's generator (`protocol.md` §4, ASM-7);
- the checkpoint format's bytes and field names, subject to the recovery §4 states (`protocol.md` §5,
  ASM-5);
- the error classes the refusals raise, and the file layout under `src/agents/`.

Each is free here and designed there; none may change a record key `surface.md` marks **required**, a refusal
that document names, or the one rule of §1 — those are what the callers and the battery read (`records.md`
§1, `battery.md` §3, ASM-7).
