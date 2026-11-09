# agents — the learner family, the baselines, and the contracts at this edge

- **Layer:** L2 · **Module:** `agents` · **Unit:** phase1 · **Rev:** 7 · **Date:** 2026-11-09
- **Owner of this file:** the one learner family and the rule catalogue it learns under (§1), the R1↔R2 backend
  axis (§2), the parameter budget (§3), a version as a checkpoint (§4), the six fixed baselines and their anchor
  (§5), the contracts `features`, `engine`, `training` and `evaluation` hold at this edge (§6–§8), the battery
  invariants this module carries (§9) and what is left to L3 (§10) (D-6, D-7, ASM-7, ASM-10, ASM-25, D-19, D-21, D-13)
- **Rev 7:** D-21's folder baselines carried here — §5 names **six** baselines instead of three, states the three
  folders' predicates under ASM-31's one legality rule and the `anchor` flag that keeps the rating's scale, §7's
  readout is the **eleven** facts with `hand_class`, and §8/§9 say what a caller may assume of the six (`folders.md`
  §2, §4, ASM-30, ASM-31, ASM-32, D-21)
- **Rev 6:** D-19's estimator axis carried here — §1 states the catalogue's two rules and the one contract they
  answer, §3's capacity is unmoved by a rule, §4's checkpoint records the rule, and §5/§8 say what a policy and a
  caller may assume (`rules.md` §2–§8, D-19)
- **Ceiling:** 250 lines. At the ceiling, split by owner — never append

## 1. One learner family, and the rules it learns under

The ladder has one learner family and a **catalogue** of two learning rules, each named by the learner spec
(`rules.md` §2, §4, ASM-7, D-19). A learner is a function from an observation and a legal mask to three values; the
value of an index outside the mask is never read, never a target and never updated (D-2, `records.md` §4, ASM-25).

- **The two rules, and what each aims at.** `masked-q-learning` moves the value of the transition's `action`
  toward `reward + discount ×` the masked **maximum** of the target copy's successor values; `double-q-learning`
  toward `reward + discount ×` the target copy's value **at the index the online parameters' masked argmax
  selects** — selection by the online parameters, evaluation by the copy, the remedy the diagnosis names for an
  upward-biased maximum (`strata/records/r2-plateau-diagnosis.md`, `rules.md` §2, ASM-25). Both aim at `reward`
  alone at a terminal transition, and the masking is the contract: an index outside `next_legal` is not a
  bootstrapping candidate (D-2, `records.md` §4).
- **One capacity, one state layout, one contract.** The rules differ in the target's arithmetic and nowhere else:
  validation, loop, statistics, step and refresh counter are one path, and the parameters plus their target copy are
  the same under either — so `param_count`, the checkpoint's array and ASM-10's ±2% match are identical, and
  `act`, `save`, `load` and `as_policy` never read the rule (`rules.md` §3, ASM-10, ASM-25, D-19).
- **The reward, and the utility that re-expresses it.** `learn` aims at the terminal transition's `reward` as the
  caller wrote it; that number is the reward of the catalogue member the learner's spec names (`utility.md` §1–§2,
  `utilities.md` §2). `net-chips` is the seat's net chip delta at its terminal decision, zero elsewhere, with no shaped
  term and no intermediate reward — this module adds none (ASM-12, `engine/environment.md` §3); `stack-shortfall`
  re-expresses that same delta in `training`'s transition step, and neither arithmetic normalises or clips it here (ASM-25).
- **The exploration.** An ε-greedy draw governed by the schedule `learners()` declares, from the learner's own
  seeded generator and **keyed by the decision**, a decision being the observation and the legal mask — so one
  learner state and one decision give one index, and a policy at the learner's own seed answers the same index
  (`surface.md` §1, §6, §10). Its position is part of the learner's state and advances inside `learn` only
  (ASM-7, ASM-5, `protocol.md` §4), and the rule is not read here (`rules.md` §3).
- **The declarations the two rules share.** Learning rate, batch size, target-update interval, optimiser family,
  exploration schedule and discount are one value each for the whole ladder, published by `learners()` so a report
  can name them; there is **no per-rule block**, so a rule swap is one axis and no budget moves with it
  (`surface.md` §3, ASM-7, `rules.md` §2, `ladder.md` §3, §4). The `discount` is named by no L1 declaration and no
  bootstrap target can be computed without it. A variant entry that names them (`records.md` §2) is the run record's
  data, never a per-learner argument: the copy a pair's fairness check compares is its rules' set (`rules.md` §8).
- **Nothing rung-shaped, and one signal.** No entry point takes a rung, a variant name, an opponent, a hand count or a
  table budget, so no rung can carry a copy of the rule (`module-map.md` §3, D-3, `ladder.md` §1), and `learn` reports
  a mean absolute TD error per batch — both backends', both rules', the ladder's common curve signal (`surface.md` §7).

## 2. R1 against R2: the backend is the only axis

D-7 gives the ladder a hand-rolled NumPy learner at R1 and PyTorch from R2 on, and R2 recreates R1 so the speed
difference is measured on identical work (`ladder.md` §5, D-7). At this edge that means one family with one switch:

| The backend swap may change | The backend swap may **not** change |
|---|---|
| which library performs the arithmetic, and so the cost of it (D-7, D-8) | the encoding: both variants declare one encoding, `flat-numeric`, whose observation family is `dense-numeric` (`ladder.md` §5, `encodings.md` §1, `surface.md` §3) |
| the checkpoint's own bytes, provided `save`/`load` stay loss-free at the decision boundary (§4, ASM-5) | the architecture kind and its width, depth, sparsity and residual settings — one model shape and one declared family (`ladder.md` §5, D-3) |
| — | the rule, the reward, every hyperparameter, the initialisation the seed defines, the exploration schedule with its keyed draws, and the tie-break among equal masked values: the ladder's declared set (§1, ASM-7, `rules.md` §8, `protocol.md` §4) |
| — | the sample order: `learn` consumes the caller's batch in the caller's order (`surface.md` §7, `ladder.md` §5) |
| — | the decision boundary: one observation and one mask give one index, and a policy at the learner's own seed decides as `act` does (`surface.md` §6, §10, `protocol.md` §5) |
| — | the capacity: one model shape is one model, so the two backends' counts coincide under §3's one counting rule (`ladder.md` §5, ASM-10) |

What this buys is the same-work check `ladder.md` §5 asks for: both backends are held to one initialisation order,
one forward-pass arithmetic order and one tie-break rule — a constraint on the design, whose realisation is L3's
(§10 below) — so on the same seeded hands against the same opponents they choose the same actions, which is what
FAM-13 asserts and what a parity row showing a large skill difference would falsify (`battery.md` §3 FAM-13). The
check is on **decisions and not on values**: what it forbids is a backend that differs in the model, the rule, the
order or the tie-break, and agreeing where a decision reads three values and one comparison is L3's obligation
(`ladder.md` §5, D-7). R2's own evidence is the clock the run record and `harness.timings` carry, never a wall clock
the battery demands, and R2 still reports its table labelled a parity comparison (D-7, D-8, ASM-15, `ladder.md` §5).

## 3. The parameter budget, as `param_count` measures it

A comparison pair — adjacent rungs and every intra-rung pair — is matched to 10,000 trainable parameters within
±2%, measured by `agents.param_count` (ASM-10, `ladder.md` §4, §6). The measurement is one rule:

- **Counted:** every value the update can change — the input block first: for a dense kind the first layer's
  weights at the width the encoding declares, for a token kind the embedding table at the vocabulary it declares,
  and then the value network the kind's `width` and `depth` fix (`encodings.md` §1, §4, §6, `e2e-surface.md` §3.3).
  The observation itself is never counted, being `encode`'s output and not a parameter; which layers and how many are
  the kind's design and L3's (§10 below), while what binds here is that the count covers the whole model.
- **Not counted:** a copy of the parameters kept for a target, any non-trainable buffer, and the exploration
  schedule's constants, because none of them is a trainable parameter (`e2e-surface.md` §3.3, ASM-10).
- **The rule does not move the number.** Both catalogue members learn over the same online parameters and the same
  target copy, so a two-rule pair is matched by its architecture alone: one kind, width and depth report one count
  under either rule (`rules.md` §3, ASM-10, ASM-25, D-19).
- **The count is a function of the spec and the seed, never of a decision handed to the learner,** and a pair is
  measured by one rule on both arms: a learner complete at construction — sized from its encoder or from its kind's
  declared `observation_size` (`surface.md` §3, §4) — holds one count for its lifetime, and the rule set and
  hyperparameters a pair holds constant mean a matched budget cannot be an artefact of the measurement
  (`rules.md` §8, ASM-7, ASM-10, D-19). **`sizes` never moves the number** (`records.md` §3, `protocol.md` §4).

## 4. A version is a checkpoint

D-16 makes a version a checkpoint of a run and a league member, so `save`/`load` is not a convenience: it is what
lets a shipped member decide as its learner did (D-16, `protocol.md` §5). The pair is **loss-free at the decision
boundary**, a function of state and decision rather than a stream position (`surface.md` §1, §6, ASM-5):

- **What a restore must recover,** from the file alone, is everything a decision reads: the backend, the kind and its
  settings, the representation — family, size and encoding name — the learner's seed, its parameter values, its
  schedule's position, **the rule it was trained under** and **the utility whose reward it was trained on**, so a member
  is read under the members its file records (`surface.md` §3, §4, §9, `encodings.md` §1, D-19, D-20, `utility.md` §4).
- **A version-1 or version-2 file is read by defaults, not refused.** The repository ships 18 version-1 checkpoints
  written before either catalogue existed: they carry neither field and are read as `masked-q-learning` and
  `net-chips`; a version-2 container carries the rule and is read as `net-chips`, and either older version
  carrying a field its writer never wrote is refused by name. Nothing is regenerated (`utility.md` §4, `rules.md` §6, ASM-5).
- **The record's own form is not contract:** what the file is called inside, how it is laid out and which version
  number it writes are L3's (§10). What binds is the recovery above and `surface.md` §9's refusals — an unreadable
  path, a form this module does not read, and a spec disagreeing with the file on a key it carries (`records.md` §3).
- **A shipped member's policy is built at the checkpoint's recorded seed,** which is why a checkpoint records it: at
  that seed the policy decides as `act` does, the loss-free equality `protocol.md` §5 states (ASM-5), and the rule and
  utility a member reports are its file's (`utility.md` §3, D-20).
- **What this module contributes to a version record.** `records.md` §7 requires `id`, `path`, `rung`, `variant`,
  `seed`, `step`, `samples`, `lineage`, `rule` and `utility`; this module supplies the `path` `save` returns and the
  learner's `seed`, `rule` and `utility`, and nothing else — `rung` and `variant` are labels a learner never learns
  (D-3, `module-map.md` §3), `lineage` is the pool's (`league.md` §2), and `samples` counts hands (`records.md` §7).
- **Retention is not this module's.** Ten equally spaced snapshots plus a final model, the last M kept in the
  window, is the run's and the pool's rule (ASM-18, `protocol.md` §5, `league.md` §2); `save` writes the one file it
  was asked for (`surface.md` §8).

## 5. The six fixed baselines

`baselines()` names **six**: `random`, `always-call` and `oracle` are D-6's, and `fold-no-pair-or-face`,
`fold-no-pair-or-better` and `fold-large-bet` are D-21's three folders. None of them learns from a match, and all six
are pool members and matrix columns at the same hand count as every league cell — the only fixed standard a self-play
league has — and a baseline policy carries **no** `learning_rule` (D-6, `protocol.md` §3, D-16, `league.md` §4, D-19).

| Baseline | Its rule | What a battery can assert |
|---|---|---|
| `random` | a uniform draw over the decision's legal indices, from a generator seeded from the baseline's seed (`protocol.md` §3) | it never returns an illegal index; one seed agrees twice and two seeds differ (`protocol.md` §3, `surface.md` §12) |
| `always-call` | check/call whenever that is legal, never fold, and the minimum legal completion when raising is the only option (`protocol.md` §3) | it folds in no decision of any hand (`protocol.md` §3) |
| `oracle` | check/call when the hand's equity is at least the pot odds `to_call / (pot + to_call)`, and fold when that inequality fails and folding is legal (`protocol.md` §3, ASM-4) | its choice is consistent with that inequality at every decision, recomputable from `engine.equity` and the readout (`protocol.md` §3, ASM-4) |

The three folders carry one fold predicate each — `fold-no-pair-or-face` pre-flop on unpaired hole cards with no J, Q,
K or A, `fold-no-pair-or-better` from the flop on a `hand_class` of `0`, and `fold-large-bet` on any street where the
call exceeds half the declared starting stack — and otherwise check/call; each folds only where folding is legal and
never raises while check/call is legal, and consumes no randomness (`protocol.md` §3, `folders.md` §2, ASM-31, D-21).

- **The `anchor` flag keeps the rating's scale.** Every record carries it: true for D-6's three, false for the folders,
  and `evaluation` zeros the fit on the mean of the flagged three, so a rating recorded before D-21 and one recorded
  after it are read on one scale (ASM-32, `league.md` §5, D-16).
- **The oracle is a rule, not a model.** Its equity comes from `engine.equity`, queried with the readout it was
  handed, **the seed the baseline was built with** and the sample count `baselines()` declares — so a caller
  holding that seed and that count re-issues the query and checks the inequality itself, which is why a rebuilt
  baseline repeats its decisions (`surface.md` §11, `engine/surface.md` §11, `protocol.md` §3, §4, ASM-4).
- **The oracle is blind by construction.** It never raises, because a raise is not a pot-odds question: it is
  deliberately strong on the pot-odds axis `protocol.md` §3 names and blind on every other — no history, no
  opponent, no adaptation (ASM-4, D-6). That blindness is what makes it a baseline rather than a competitor (D-6).
- **A baseline never learns, and its state advances nowhere.** `learn` refuses a value that is not a learner, and
  nothing here retains anything from a hand a baseline played, so a baseline's column is the same rule at every hand
  count and every call order (`surface.md` §1, §7, §12, D-6, `protocol.md` §3). Because no state advances, its random
  draw is keyed by the decision as a learner's exploration is (`surface.md` §1, §12).
- **A baseline has no trainable parameters:** `baselines()` declares its `params` as `0`, and that declared zero is
  the count a cell records beside every other member's count — `param_count` refuses a baseline because a baseline
  is not a learner (`surface.md` §5, §11, `records.md` §9).
- **A policy receives only `(readout, legal_actions)`,** so a baseline is a function of the decision it is handed and
  never of the hand it is inside — which is why `engine.equity` accepts a readout as well as a hand
  (`e2e-surface.md` §2, `engine/surface.md` §11, `engine/environment.md` §6).

## 6. The contract at the `features` edge (D-13)

What this module may rely on, as what it consumes and never as that module's internals (`module-map.md` §2, D-13):

- `observation_spec(encoder)` declares `representation`, `kind`, `fields`, `shape`, `dtype` and `vocabulary`;
  `shape` is a dense input's width and `vocabulary` an embedding table's row count, so a learner is sized from the
  spec, never from a width copied out of a document (`features/surface.md` §5, `encodings.md` §6);
- `observation_spec.kind` — `dense-numeric` or `token-sequence` — is the representation family a learner's architecture
  kind must agree with; `observation_spec.representation` — `flat-numeric` or `card-tokens` — is the encoding a variant
  declares, and each maps onto exactly one family, two keys of one record and never one for the other
  (`encodings.md` §1, `surface.md` §3, §4);
- `encode(encoder, readout)` returns one array of the declared shape and dtype, value for value, drawing no
  randomness and mutating nothing, so an observation this module trains on is reproducible from the readout
  (D-3, `features/surface.md` §6);
- `legal_indices(legal_actions)` returns the decision's legal indices, position-aligned with the descriptors it was
  given, distinct, ascending and never empty — the mask `act` takes is exactly this sequence (`features/surface.md`
  §8, `surface.md` §2);
- `decode_action(index)` returns the descriptor `engine.apply_action` accepts, so the index a learner chooses
  becomes the action a policy returns, and `action_space()` fixes the three output units of every learner and the
  vocabulary a report's header quotes (`features/surface.md` §7, §9, `e2e-surface.md` §2, `protocol.md` §1);
- **The edge is granted and five calls wide.** `module-map.md` §2 grants this module `encode`, `observation_spec`,
  `action_space`, `legal_indices` and `decode_action`, because a learner consumes an observation and `as_policy`
  must encode the readouts its policy receives. `build_encoder` is not among the five, so the encoder always
  arrives from the caller — in a learner spec, in `as_policy`, or from `training` and `evaluation` — and this module
  builds none (`surface.md` §4, §10, `features/surface.md` §4, D-3, D-13).
- **The sizing rule is a contract in both directions.** Each kind's declared `observation_size` must equal the width
  of the `shape` a dense encoding's `observation_spec` declares — a one-element tuple — or the `vocabulary` a token
  encoding's declares, that vocabulary being the datum `e2e-surface.md` §2 makes the size of a token learner, never an
  observation's length; and `build_learner` given an encoder must refuse a disagreement, naming both, while a caller
  with no encoder is sized from the declared value (`e2e-surface.md` §3.3, `surface.md` §3, §4, D-3).

## 7. The contract at the `engine` edge (D-13)

- `readout(hand)` is the eleven-fact information set — D-21's `hand_class` included, `None` before the flop and 0–8
  from it on — and this module reads it only as the thing a policy receives and an encoder consumes, never asking a
  hand for anything (D-3, ASM-30, `engine/environment.md` §2).
- `equity(decision, seed, sample_count)` returns the acting seat's win probability in `[0, 1]`, takes a hand **or**
  its readout, repeats for one decision, seed and count, and hands the global stream back as it found it — which is
  why an oracle can ask it mid-hand (`engine/surface.md` §11, `engine/environment.md` §4, ASM-4). The third granted
  call is `game_config`, read by `fold-large-bet` for the declared starting stack rather than a copied `20`
  (`folders.md` §2, ASM-31); nothing else in `engine` is called (`module-map.md` §2, §3, D-2).

## 8. What `training` and `evaluation` may assume

| Caller | May assume |
|---|---|
| `training` | `build_learner`, `act`, `learn` and `save` drive one learner and nothing else (`module-map.md` §2); every initialisation and every exploration draw comes from the learner's own generator seeded from the spec's `seed`, and the learner's schedule advances only inside `learn`, so a run is reproducible from its configuration and seed set and the deal stream is untouched (D-6, `protocol.md` §4, ASM-2); **a `learning_rule` the spec names is the rule the learner learns under**, absent meaning the catalogue's first, and every variant it declares is trained under its own (`rules.md` §4, §7, D-19); the batch it hands `learn` is consumed in its own order, so a pair's sample order is one (`ladder.md` §5); the curve comes from `learn`'s `td_error`, which is the same statistic under both rules (`protocol.md` §1, `rules.md` §3) |
| `evaluation` | `baselines` and `build_baseline` yield the six policies a table needs as members, each with the `params` of `0` and the `anchor` flag the catalogue declares and no `learning_rule` (`e2e-surface.md` §3.4, `records.md` §9, ASM-32, D-19, D-21); `load` restores a member from its path alone, under the rule its container records, and `param_count` reports that member's capacity (`records.md` §7, §9, `rules.md` §6); `as_policy` at the member's recorded seed decides as its learner did, and the policy it returns carries the member's `learning_rule`, so a cell names the estimator that produced each member even for a variant built in process (`e2e-surface.md` §2, `records.md` §9, ASM-5, D-19); the encoder that call needs is `evaluation`'s own, because `module-map.md` §2 grants `evaluation` `build_encoder` and `encode` precisely so `policy_from` turns a checkpoint into a policy (D-16, this file's §6); no baseline's behaviour depends on any match it played (D-6) |

Neither caller may assume anything about a learner's internals, its file format, its error classes or its arithmetic
order — those are L3's (`module-map.md` §5, D-12) — and neither branches on the rule (`rules.md` §3, D-19).

## 9. The invariants the battery asserts against this module

Each family of `battery.md` §3 that lands here, with the entry points that carry it (`battery.md` §3, D-11):

| Family | What it asserts | Carried by |
|---|---|---|
| FAM-1 | all ten names exist and are callable, and a minimal call returns the declared kind (`battery.md` §3) | all ten (`e2e-surface.md` §3.3) |
| FAM-5 | the six baselines are exactly D-6's three and D-21's three folders, each builds a policy of the protocol, `random` is uniform over the legal indices and seeded, `always-call` never folds, the three folders fold only where `fold` is legal and never raise while check/call is legal, and the oracle is consistent with the pot odds against `engine.equity` when that query is re-issued at the baseline's own seed and the count `baselines()` declares (`protocol.md` §3, ASM-4, ASM-31, `surface.md` §11, D-21) | `baselines`, `build_baseline` |
| FAM-12 | `save`/`load` is loss-free at the decision boundary: a loaded checkpoint chooses the action its learner chooses on the same readout (`protocol.md` §5, ASM-5) | `save`, `load` |
| FAM-13 | R1 and R2 declare one encoding and one architecture, differ only in `backend`, choose the same actions on the same seeded hands, and report matched capacities (D-7, `ladder.md` §5, ASM-10) | `learners`, `build_learner`, `param_count` |
| FAM-16 | seven blind instances — an invented spec, an invented `param_count` pair, and an invented `act`, `learn`, `save`, `load` and `as_policy` (`battery.md` §4, D-15) | `build_learner`, `param_count`, `act`, `learn`, `save`, `load`, `as_policy` |

The other families reach this module only as a path: FAM-4's seed contract bites through the generator
`build_learner` seeds (`protocol.md` §4), FAM-3 and FAM-15 through the specs a custom rung hands `build_learner`
(`ladder.md` §3), and FAM-7 through the baseline policies `match` is given beside the members it loads (`league.md` §3).
D-19's cases — the catalogue's two members and their order, the spec's rule and its default, the two targets, the
checkpoint's field and the policy's attribute — are the unit battery's, since no L1 family reads a rule, and the
module's own internals belong to `tests/agents/` (`battery.md` §5, `rules.md` §3, `module-map.md` §5).

## 10. What is left to L3

This document stops at the entry point and at the records they exchange. `role_l3_designer` owns the module design (D-1, `module-map.md` §5):

- the learner's own type and what it holds, which no caller may inspect (`surface.md` §1);
- how one backend realises the forward pass and the update, and how the two backends are made to agree on the
  decisions §2 requires (`ladder.md` §5, D-7);
- the initialisation order the seed defines, the tie-break among equal masked values, and how the keyed
  exploration draw of §1 is derived from the learner's generator (`protocol.md` §4, ASM-7);
- **how each rule's target is computed** and that the two rules share one state layout, one update and one return
  (`rules.md` §3, ASM-25);
- the checkpoint format's bytes, version and field names, subject to the recovery §4 states and a version-1 file's
  reading, and the error classes the refusals raise, the rule's refusal included (`protocol.md` §5, `rules.md` §6).

Each is free here and designed there; none may change a record key `surface.md` marks **required**, a refusal that document names, or the one contract of §1 (`records.md` §1, `battery.md` §3, `rules.md` §3, D-19, D-20).
