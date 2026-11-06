# agents — the callable surface

- **Layer:** L2 · **Module:** `agents` · **Unit:** phase1 · **Rev:** 6 · **Date:** 2026-11-05
- **Owner of this file:** the surface — the ten module-level names of `src/agents/`, each with its argument
  contract, its return, its refusals and its determinism (D-12, `e2e-surface.md` §1, §3.3)
- **Rev 6:** §1's seeding rule restated as *leaves the stream as found*, because `engine.equity` reseeds and restores the global stream inside its own call, so *never touches it* was unsatisfiable (ASM-2, `engine/surface.md` §11)
- **Ceiling:** 275 lines. At the ceiling, split by owner — never append

## 1. Rules that hold of every entry point

Each of the ten names is a module-level name of the `agents` package, and nothing below one of them is
contract (`e2e-surface.md` §1, brief §5). Seven rules are shared and are stated here once (D-12, D-13):

- The ten names are fixed: L2 refines types, record keys, defaults and error classes and never adds,
  removes or renames an entry point (D-12, `e2e-surface.md` §1).
- An invalid argument is refused by raising an error that names the violated contract; no entry point
  coerces a value, substitutes a default, swallows an error or returns part of a record
  (`e2e-surface.md` §2).
- **No entry point leaves the global `random` stream moved**, and none takes a seed for the deal:
  `engine.new_hand` is the single seeding point and every seed here is a learner's or a baseline's own;
  `engine.equity` reseeds and restores that stream inside its own call (ASM-2, `engine/surface.md` §11).
- **An answer depends on the deciding state and on the decision, not on call order.** A learner is complete
  when it is built (§4), its schedule advances inside `learn` and nowhere else, and a policy's and a
  baseline's state advances nowhere. The decision is the observation and the legal mask (§6, §10), and the
  exploration a learner or a baseline needs is drawn from its own seeded generator keyed by that decision.
  One state and one decision therefore give one answer, which is what makes the decision boundary a function
  and not a position in a stream — the property `save`/`load` is measured against (ASM-5, `protocol.md` §5,
  ASM-2).
- A learner, an encoder and a policy are opaque values a caller only passes back; no caller inspects,
  compares, serialises or rebuilds one, and no record returned here exposes one (`e2e-surface.md` §1,
  `features/surface.md` §1).
- Every other returned value is plain data, and the catalogues of §3 and §11 are what a report's header
  quotes — a cell's parameter counts and the fixed baselines' rules — because a header a third party cannot
  read is not evidence (`records.md` §9, `protocol.md` §1).
- A record returned here carries the keys `records.md` marks **required** and, beyond them, only this
  module's own keys, which no caller may depend on (`records.md` §1, §6, D-13).

## 2. The action index and the legal mask

This module's decisions are indices of the game's three-index vocabulary, and the mask it chooses from is
`features`' (`e2e-surface.md` §2, `features/surface.md` §2, §8):

- a mask is the decision's legal index sequence as `features.legal_indices` returns it: distinct, at most
  one entry per vocabulary index, and never empty (`features/surface.md` §8, `engine/surface.md` §6);
- a chosen index is a member of that mask and is therefore in `{0, 1, 2}` — fold, check/call, raise — and
  the descriptor a policy returns is `features.decode_action` of it, which is the action `engine` applies
  (D-2, `features/surface.md` §9);
- the mask is not carried in an observation, because it reaches a decision beside the observation and a
  second statement of legality could disagree with the first (`encodings.md` §2, `battery.md` §3 FAM-2);
- nothing here invents an index outside the mask; a value outside it is a contract violation and never a
  fold on the caller's behalf (D-2, `e2e-surface.md` §2).

## 3. `learners` — the declared backends, kinds and rule (`fixed` row)

- **Signature:** `learners()`.
- **Arguments:** none: the learner family is the ladder's, so there is no parameter by which it can be
  varied (`e2e-surface.md` §3.3, ASM-7).
- **Returns:** one mapping, read under these keys:

| Key | Content |
|---|---|
| `backends` | keyed by the two backend names — `numpy` and `torch` — each value a record whose only string is that name, so a caller reading names out of this catalogue cannot mistake a sentence for one (D-7, §4) |
| `architectures` | keyed by the seven architecture kinds, each value a record carrying `name`, `observation` (the representation family it consumes) and `observation_size` (the input width a dense kind is built for, or the token vocabulary a token kind is built for) — the size a learner with no encoder is built for (`e2e-surface.md` §3.3, `encodings.md` §1, §4) |
| `learning_rule` | `masked-q-learning`, and that is the only value (ASM-7) |
| `hyper` | the rule's fixed declarations, one value each for the whole ladder: `learning_rate`, `batch_size`, `target_update_interval`, the optimiser family, the exploration schedule and the rule's `discount` — named by no L1 declaration, since `ladder.md` §3 lists the other four and ASM-7 the optimiser family, and without it masked Q-learning's target cannot be computed; fixed here, for the whole ladder (ASM-7, `ladder.md` §3, §4) |

The exploration schedule is a record of its own — the rate a learner starts at (`start`), the rate it anneals
to (`end`) and the samples over which it anneals (`samples`) — so a reader can quote it and two arms can be
compared on it (ASM-7, `ladder.md` §4). The seven kinds, the family each consumes and the encoding each is
built for are declared here, because a learner is sized and refused against this table (§4):

| Kind | `observation` | `observation_size` | The encoding its rungs declare |
|---|---|---|---|
| `naive-stack` | `dense-numeric` | the dense input width | R1 and R2's `flat-numeric` (`ladder.md` §2, `encodings.md` §1) |
| `token-embedding`, `wide`, `deep`, `sparse`, `residual`, `plain` | `token-sequence` | the token vocabulary | R3–R6's `card-tokens` (`ladder.md` §2, `encodings.md` §1) |

- **The kinds' spelling is this table's.** A variant entry's `architecture.kind` uses these names exactly: a
  catalogue a caller reads by name must be one spelling (`ladder.md` §3, `records.md` §2, D-3).
- **`observation_size` is a contract, not a second source of truth.** `e2e-surface.md` §3.3 makes the
  encoder-less build the sized-from-declaration case and `observation_spec` the cross-check that keeps the
  two equal (D-3): each kind's declared `observation_size` is a scalar width and must equal the width of the
  `shape` the dense encoding's `observation_spec` declares — one observation's shape being a one-element
  tuple — or the `vocabulary` the token encoding's declares, and §4 refuses an encoder-bearing build whose
  kind and encoder disagree, naming both. A declaration that drifted from `features` therefore fails at the
  first encoder-bearing build instead of silently sizing a learner, and no width is ever copied out of a
  document (`e2e-surface.md` §3.3, `encodings.md` §1, §6, `features/surface.md` §5).
- **Refusals:** none; it has no argument and nothing to vary (`e2e-surface.md` §3.3, ASM-7).
- **Determinism and ordering:** two calls return equal records, the backends in `numpy` then `torch` order
  and the kinds in the order of the table; the catalogue is plain data a report may quote (D-7,
  `protocol.md` §1). Its `learning_rule` and `hyper` are this module's own keys (`records.md` §1): the
  ladder's fixed declarations, published so a report can name them, and never a second copy that a fairness
  check compares — the copy a pair is audited on is its variant entries' (`ladder.md` §3, §4).

## 4. `build_learner` — one learner from one spec (`general` row)

- **Signature:** `build_learner(spec)`.
- **Arguments:** one mapping, `records.md` §3's learner spec. Three keys are required and two are read when
  present; **every other key is ignored**, including a variant entry's `learning_rule` and `hyper`, which
  are the run record's data and not a per-learner argument (`records.md` §3, `learner.md` §1):

| Key | Contract |
|---|---|
| `backend` | **required** — `numpy` or `torch`, one of `learners()`'s backends (D-7, `records.md` §3) |
| `architecture` | **required** — a mapping with `kind`, a kind name §3 declares, plus that kind's settings from `width`, `depth`, `sparsity` and `residual`, **or** a bare kind name, in which case `sizes` must carry the width and depth because the name alone sources no size; a setting the kind does not read is ignored (`records.md` §2, §3, `ladder.md` §3) |
| `seed` | **required** — the seed of the learner's own generator, an integer, recorded by the run that builds it (ASM-2, `protocol.md` §4) |
| `sizes` | optional and redundant: width and depth, with `architecture` authoritative when both are present — but the only source of width and depth under a bare kind name (`records.md` §3) |
| `encoder` | optional — *the encoder when the caller has one*: an encoder from `features.build_encoder`, supplied by the caller because building one is not among the five calls `module-map.md` §2 grants this module. The learner is built for it and checked against it; absent, its kind's `observation_size` is the size it is built for (`e2e-surface.md` §3.3, `module-map.md` §2, §3 of this file) |

- **Returns:** a learner, **complete at construction** in either case above — its input block sized either
  from the encoder's `observation_spec` or, with no encoder, from the `observation_size` its kind declares
  (§3, `e2e-surface.md` §3.3). It is the only way to obtain one, so every learner the ladder trains came from
  a declared backend and a declared kind (`e2e-surface.md` §1, D-7). Because completion happens at
  construction and draws from the learner's own seeded generator, two learners from one spec are one learner
  in capacity and in every decision (§1, ASM-2).
- **Refusals:** a missing required key, with that key in the error (`records.md` §3); a bare kind name with no
  `sizes`, because then its width and depth have no source and no default is substituted (D-12, `records.md`
  §3); a backend or a kind §3 does not declare, with that value named (D-7, `e2e-surface.md` §2); a seed that
  is not an integer (ASM-2); a width or a depth that is not a positive integer, or a `sparsity` outside
  `[0, 1]` (`ladder.md` §3, `records.md` §2); a value that is not an encoder; an `encoder` whose
  `observation_spec` kind or size contradicts the kind's `observation` or `observation_size`, naming both —
  the cross-check that keeps the two declarations equal (`e2e-surface.md` §3.3, D-3, `encodings.md` §1, §6).
- **Determinism:** one spec builds one learner: two learners from one spec carry one parameter count and
  make one decision on one observation, because the initialisation draws from the learner's own seeded
  generator and from nothing else (ASM-2, `protocol.md` §4, ASM-10).

## 5. `param_count` — the capacity measurement (`general` row)

- **Signature:** `param_count(learner)`.
- **Arguments:** a learner from `build_learner` (`e2e-surface.md` §3.3, §4).
- **Returns:** one integer — the count of the learner's trainable parameters, which is the ladder's matched
  capacity (`e2e-surface.md` §3.3, ASM-10). The counting rule is `learner.md` §3's: one rule over every
  trainable value, the input layer's weights or the embedding table included, the target copy and the buffers
  excluded, so the number is a measurement and not a per-backend or per-state convention (D-7, ASM-10). A
  learner is complete when it is built (§4), so one learner holds one count for its lifetime, whatever it is
  later asked (ASM-10, `protocol.md` §4).
- **Refusals:** a value that is not a learner, naming that contract; a baseline is not a learner, and its
  parameter count is the `0` that `baselines()` declares — which is exactly the count `records.md` §9 records
  for a baseline cell member, that record asking `agents.param_count` for a version and this declared zero for
  a baseline (ASM-10, `records.md` §9, §11 of this file).
- **Determinism:** one learner reports one count; a learner built twice from one spec reports the same one,
  and a restored learner reports the saved one (`protocol.md` §5, ASM-5).

## 6. `act` — one training-time decision (`general` row)

- **Signature:** `act(learner, observation, legal_mask)`.
- **Arguments:** a learner; one observation as `features.encode` returns it for the decision; and the
  decision's legal index sequence of §2 (`e2e-surface.md` §3.3, `records.md` §4).
- **Returns:** the decision record — a mapping carrying the chosen index under `action`, as a plain Python
  integer, plus the learner's own record of the decision, whose other keys are not surface
  (`e2e-surface.md` §3.3, `records.md` §6). This document fixes the mapping form; a bare index would satisfy
  `records.md` §6 as well, and the mapping is chosen because the learner's record travels with it. The index
  is a member of the mask (§2).
- **Refusals:** a value that is not a learner; an observation whose shape, dtype or representation family
  contradicts the learner's, naming both (D-3, `encodings.md` §1); a mask that is empty, repeats an index, or
  holds an index outside `{0, 1, 2}` (D-2, §2).
- **Determinism:** one learner state, one observation and one mask give one index. The decision is **the
  observation and the mask**, and the exploration is drawn from the learner's own seeded generator keyed by
  that decision, so a second call at the same state answers the same index rather than advancing a stream,
  and a policy at the learner's own seed answers the same index (§1, §10, `learner.md` §1, ASM-7).

## 7. `learn` — one update and its statistics (`general` row)

- **Signature:** `learn(learner, transitions)`.
- **Arguments:** a learner, and a non-empty sequence of the transition records `records.md` §4 fixes —
  **required**: `observation`, `next_observation`, `action`, `reward`, `terminal`, `legal`, `next_legal`
  (`records.md` §4). The batch is the caller's order and this module neither samples nor shuffles it, which
  is what lets a comparison pair declare one sample order (ASM-7, `ladder.md` §5).
- **Returns:** one mapping of the update's own statistics, read under these keys:

| Key | Content |
|---|---|
| `td_error` | **the learning signal**: one number, the batch's mean absolute temporal-difference error, which is the curve's signal in the report (`protocol.md` §1) |
| `transitions` | the transitions this call consumed, an integer — the learner's own progress, **not** the hands behind a version: one hand holds several decisions and this module never sees a hand, so a version's `samples` is the run's count of hands and not the sum of these (`records.md` §7, `module-map.md` §3) |

- **Refusals:** a value that is not a learner — a baseline never learns from a match (D-6,
  `protocol.md` §3); an empty batch; a transition missing a required key of `records.md` §4, with that key
  named; an `action` outside that transition's `legal`, or a mask outside `{0, 1, 2}` (D-2); an observation
  whose shape or representation family contradicts the learner's (D-3).
- **Determinism:** one learner state and one batch give one update and one statistic set — this call is the
  only place a learner's schedule moves (§1). The update's aim, its masking and its terminal reward are
  `learner.md` §1's and never a per-backend choice (ASM-7, ASM-12).

## 8. `save` — write one checkpoint (`general` row)

- **Signature:** `save(learner, path)`.
- **Arguments:** a learner, and a file path to write, which the caller owns: `checkpoints/` belongs to
  `training` and this module writes only where it is told (`module-map.md` §5, `e2e-surface.md` §3.3).
- **Returns:** the path it wrote, so a run record names the artefact it produced (`records.md` §12).
- **Refusals:** a value that is not a learner; a path that is not a writable file location, with that path
  named — no entry point invents a directory, substitutes a default or writes part of a checkpoint
  (`e2e-surface.md` §2).
- **Determinism:** one learner saved twice writes one decision boundary; what the checkpoint must recover is
  `learner.md` §4's and is asserted through §9 (ASM-5, `protocol.md` §5).

## 9. `load` — restore one learner (`general` row)

- **Signature:** `load(spec, path)`.
- **Arguments:** a learner spec in `records.md` §3's shape **or** `None`, and a path `save` wrote
  (`e2e-surface.md` §3.3). A checkpoint recovers everything from the file itself, so a member is loadable
  from its path alone (`records.md` §7, `learner.md` §4).
- **Returns:** the restored learner, at the state that was saved: same backend, kind and settings, same
  representation and size, same parameter values and same decision boundary — the equality `protocol.md` §5
  requires of `save`/`load` (ASM-5).
- **Refusals:** a missing or unreadable path, with that path named; a checkpoint whose recorded form this
  module does not read; **and a `spec` that disagrees with the checkpoint on a key the spec carries**, naming
  that key — a mismatched spec is never coerced onto the parameters (`e2e-surface.md` §2, ASM-5). A spec of
  `records.md` §3 always carries `backend`, `architecture` and `seed`, so a `seed` other than the seed the
  checkpoint records is refused, as is a backend or a kind the file does not hold (`records.md` §3, §7,
  `learner.md` §4); `sizes` never disagrees, `architecture` being authoritative (`records.md` §3). The
  representation and the size are compared only when the spec carries an encoder, and then against that
  encoder's `observation_spec` as §4 compares them; with no encoder they come from the file, which is why a
  member is loadable from its path alone (§3, §4).
- **Determinism:** one checkpoint restored twice gives two learners that decide alike, and a restored
  learner's next decision is the saved learner's next decision, because §1 makes a decision a function of
  state and decision rather than of call order (`protocol.md` §5, ASM-5).

## 10. `as_policy` — one learner as a policy (`general` row)

- **Signature:** `as_policy(learner, encoder, seed)`.
- **Arguments:** a learner; an encoder from `features.build_encoder`, with which the policy turns a readout
  into an observation — built by the caller, who may be `training` or `evaluation`, because `build_encoder` is
  not among the five calls `module-map.md` §2 grants this module; and a seed, an integer, for the policy's own
  generator (`e2e-surface.md` §3.3, `module-map.md` §2, `protocol.md` §4). For a learner restored by §9 the
  seed to pass is the checkpoint's recorded seed, which a caller reads from the version record's `seed`
  beside the `path` (`records.md` §7, `learner.md` §4): no entry point here returns a learner's seed, because
  a learner is opaque (§1).
- **Returns:** a policy in the sense of `e2e-surface.md` §2 — a callable taking the readout and the legal
  descriptors and returning one of those descriptors (`e2e-surface.md` §2, `engine/environment.md` §6). The
  policy applies the learner's own decision rule to the decision its arguments name — the observation
  `encode` produces and the mask `legal_indices` gives — so at the learner's own seed it decides exactly as
  `act` decides on the same decision, and at another seed it applies the same rule with an independent
  exploration key (`protocol.md` §5, `learner.md` §1). It holds the learner's state as that state was when
  it was built, and a later `learn` does not change a policy already built (§1, ASM-5) — so `protocol.md` §5's
  equality is not defeated by a policy being neither updated nor cut off from its exploration. What
  `e2e-surface.md` §3.4 calls "evaluation mode" qualifies `evaluation.policy_from` and is that module's to
  realise; a policy here is never updated and never frozen (`learner.md` §1, ASM-5, D-16).
- **Refusals:** a value that is not a learner or not an encoder, naming that contract; a seed that is not an
  integer (ASM-2); an encoder whose `observation_spec` kind or size contradicts the learner's kind, naming
  both (§4, D-3). It never returns a descriptor outside `legal_actions` (D-2).
- **Determinism:** two policies built from one learner, one encoder and one seed answer the same decisions on
  the same decisions, because the only randomness is the policy's own seeded generator keyed by the decision
  (§1, `protocol.md` §4, ASM-2).

## 11. `baselines` — the three fixed baselines (`fixed` row)

- **Signature:** `baselines()`.
- **Arguments:** none: the three are D-6's, so there is no parameter by which the set can be varied
  (`e2e-surface.md` §3.3, D-6).
- **Returns:** one mapping keyed by the three names — `random`, `always-call`, `oracle` — each value
  carrying that baseline's name, the rule `protocol.md` §3 states for it, and its `params` of `0`, because a
  baseline has no trainable parameter (`protocol.md` §3, `records.md` §9). The oracle's value also declares
  the sample count its equity query uses — the count `build_baseline`'s `oracle` itself queries, so a caller
  that built the baseline at one seed re-issues the same query, at that seed and at the count declared here,
  and checks the inequality itself (§12, `learner.md` §5, `engine/surface.md` §11, ASM-4). A re-issue at any
  other count is a different query and cannot falsify the rule (ASM-4).
- **Refusals:** none; it has no argument (`e2e-surface.md` §3.3, D-6).
- **Determinism and ordering:** two calls return equal records, in the order `random`, `always-call`,
  `oracle`; the catalogue is plain data a report's header quotes (`protocol.md` §1, §3).

## 12. `build_baseline` — one baseline as a policy (`fixed` row)

- **Signature:** `build_baseline(name, seed)`.
- **Arguments:** one of the three names §11 declares, and a seed for that baseline's own generator
  (`e2e-surface.md` §3.3, ASM-4).
- **Returns:** a policy in the sense of `e2e-surface.md` §2 (ASM-4, `protocol.md` §3). Its rule is
  `learner.md` §5's; it receives only the readout and the legal descriptors, which is why the oracle asks
  `engine.equity` with the readout it was handed rather than with a hand (`e2e-surface.md` §2,
  `engine/surface.md` §11).
- **Refusals:** a name the three do not include, with that name in the error (`e2e-surface.md` §2,
  `protocol.md` §3); a seed that is not an integer (ASM-2).
- **Determinism:** one decision gives one descriptor, because no baseline advances any state; for `random` one
  seed repeats its choices and two seeds differ, which is the seed property `protocol.md` §3 states for it,
  while `always-call` and `oracle` are functions of the decision alone and have no seed to differ by. The draw
  is keyed by the decision as a learner's exploration is, since a uniform draw over a decision's legal indices
  cannot come from a stream position (§1, `protocol.md` §3, §4, ASM-4). A baseline never learns (D-6).
