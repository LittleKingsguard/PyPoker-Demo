# agents — the callable surface

- **Layer:** L2 · **Module:** `agents` · **Unit:** phase1 · **Rev:** 10 · **Date:** 2026-11-10
- **Owner of this file:** the surface — the ten module-level names of `src/agents/`, each with its argument
  contract, its return, its refusals and its determinism (D-12, `e2e-surface.md` §1, §3.3)
- **Rev 10:** a measured defect (`strata/records/lr-probe.md`) gives this surface one refusal that is not an argument contract — a non-finite td_error, a non-finite parameter, or a non-finite value in a decision's masked set is refused by name instead of reaching the tie-break — so §1, §6, §7 and §10 point at its new owner, `divergence.md`, and the ten signatures, the six hyper-declarations, the two rules, the two utilities and the finite path are unchanged (D-19, D-20)
- **Rev 9:** D-21 reaches this surface in three places and moves no signature: §11's `baselines` publishes **six** records instead of three — D-6's `random`, `always-call` and `oracle`, then D-21's `fold-no-pair-or-face`, `fold-no-pair-or-better` and `fold-large-bet` — each carrying an `anchor` flag, `True` for the first three and `False` for the folders, which is the set the rating is zeroed on; §12's `build_baseline` takes one of the six and refuses a name outside them, the folders folding only where `fold` is legal and never raising while check/call is legal (`folders.md` §2, ASM-31); and every policy's readout is now the **eleven** facts, `hand_class` accepted as `None` or an integer 0–8 and refused by name otherwise (`engine/environment.md` §2, ASM-30)
- **Rev 8 and 6:** D-20 reaches this surface beside D-19 and in the same five places: §3's `learners` publishes a second catalogue, `utilities` (two members, each with its reward, `utilities.md` §2), §4 reads the spec's optional `utility` and refuses a name outside it, §8/§9's container is format version 3 with a required `utility` field while a version-1 or version-2 file is read as `net-chips`, and §10's policy carries `utility` beside `learning_rule`; the ten names keep their signatures and return shapes, so neither caller branches on a rule or a utility (`utility.md` §1–§6, `rules.md` §2–§8, D-19, D-20). §1's seeding rule restated as *leaves the stream as found*, because `engine.equity` reseeds and restores the global stream inside its own call, so *never touches it* was unsatisfiable (ASM-2, `engine/surface.md` §11)
- **Ceiling:** 275 lines. At the ceiling, split by owner — never append

## 1. Rules that hold of every entry point

Each of the ten names is a module-level name of the `agents` package, and nothing below one of them is
contract (`e2e-surface.md` §1, brief §5). Seven rules are shared and are stated here once (D-12, D-13):

- The ten names are fixed: L2 refines types, record keys, defaults and error classes and never adds,
  removes or renames an entry point (D-12, `e2e-surface.md` §1).
- An invalid argument is refused by raising an error that names the violated contract; no entry point coerces a value,
  substitutes a default, swallows an error or returns part of a record (`e2e-surface.md` §2).
- **No entry point leaves the global `random` stream moved**, and none takes a seed for the deal: `engine.new_hand`
  is the single seeding point, every seed here is a learner's or a baseline's own, and `engine.equity` reseeds and
  restores that stream inside its own call (ASM-2, `engine/surface.md` §11).
- **An answer depends on the deciding state and on the decision, not on call order.** A learner is complete when
  it is built (§4), its schedule advances inside `learn` only, and a policy's and a baseline's state advances nowhere.
  The decision is the observation and the legal mask (§6, §10), and the exploration is drawn from its own seeded
  generator keyed by that decision, so one state and one decision give one answer (ASM-5, `protocol.md` §5, ASM-2).
- A learner, an encoder and a policy are opaque values a caller only passes back; no caller inspects, compares,
  serialises or rebuilds one (`e2e-surface.md` §1, `features/surface.md` §1). Every other returned value is plain
  data, and the catalogues of §3 and §11 are what a report's header quotes (`records.md` §9, `protocol.md` §1).
- A record returned here carries the keys `records.md` marks **required** and, beyond them, only this
  module's own keys, which no caller may depend on (`records.md` §1, §6, D-13).

## 2. The action index and the legal mask

This module's decisions are indices of the game's three-index vocabulary, and the mask it chooses from is
`features`' (`e2e-surface.md` §2, `features/surface.md` §2, §8):

- a mask is the decision's legal index sequence as `features.legal_indices` returns it: distinct, at most
  one entry per vocabulary index, and never empty (`features/surface.md` §8, `engine/surface.md` §6);
- a chosen index is a member of that mask and so is in `{0, 1, 2}` — fold, check/call, raise — and the descriptor a
  policy returns is `features.decode_action` of it, the action `engine` applies (D-2, `features/surface.md` §9);
- the mask is not carried in an observation, because it reaches a decision beside the observation and a second
  statement of legality could disagree with the first (`encodings.md` §2, `battery.md` §3 FAM-2);
- nothing here invents an index outside the mask; a value outside it is a contract violation and never a fold on
  the caller's behalf (D-2, `e2e-surface.md` §2).

## 3. `learners` — the declared backends, kinds, rule and utility catalogues (`fixed` row)

- **Signature:** `learners()`.
- **Arguments:** none: the catalogue is the ladder's and is published for a report to quote, while the rule and the
  utility a learner learns under are its spec's own keys (§4) and never arguments here (`e2e-surface.md` §3.3, D-19, D-20).
- **Returns:** one mapping, read under these keys:

| Key | Content |
|---|---|
| `backends` | keyed by the two backend names — `numpy` and `torch` — each value a record whose only string is that name, so a caller reading names out of this catalogue cannot mistake a sentence for one (D-7, §4) |
| `architectures` | keyed by the seven architecture kinds, each value a record carrying `name`, `observation` (the representation family it consumes) and `observation_size` (the input width a dense kind is built for, or the token vocabulary a token kind is built for) — the size a learner with no encoder is built for (`e2e-surface.md` §3.3, `encodings.md` §1, §4) |
| `learning_rules` | keyed by the two catalogue members in this order — `masked-q-learning`, then `double-q-learning` — each value a record carrying its `name` and its `target` as a stable token and never a sentence: `max-of-target-copy-over-next-legal` and `target-copy-at-online-argmax-over-next-legal`, the arithmetics §7 states (`rules.md` §2, D-19) |
| `utilities` | keyed by the two terminal-reward members in `utilities.md` §2's order — `net-chips`, then `stack-shortfall` — each value a record carrying its `name`, its `reward` as a stable token (`net-chip-delta`, `squared-stack-shortfall-delta`) and the `normaliser` that reward is divided by (`none`, then `U(s_0)`): the objective a learner's terminal target carries (`utility.md` §1, `utilities.md` §2, D-20) |
| `hyper` | the fixed declarations, one value each and **not a per-rule block**: `learning_rate`, `batch_size`, `target_update_interval`, the optimiser family, the exploration schedule and the `discount` — named by no L1 declaration, since `ladder.md` §3 lists the other four and ASM-7 the optimiser family, and no bootstrap target can be computed without it; **both rules consume these same six**, so a rule swap is one axis and no budget moves with it (ASM-7, `rules.md` §2, `ladder.md` §3, §4) |

- **The first member of each catalogue is that axis's declared default.** A spec naming no
  `learning_rule` is built under `masked-q-learning`, and one naming no `utility` is trained on the
  reward of `net-chips`; each catalogue and not a module constant is what exists, so each order is
  contract and a name outside it — in a spec, a variant entry, a pool member or a `load` spec — is
  refused by name, the defaults declared in `rules.md` §4 and `utilities.md` §5 (§4, §9, `utility.md` §1, D-19, D-20).

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
- **`observation_size` is a contract, not a second source of truth.** Each kind's declared `observation_size` must
  equal the width of the `shape` a dense encoding's `observation_spec` declares — a one-element tuple — or the
  `vocabulary` a token encoding's declares, and §4 refuses an encoder-bearing build whose kind and encoder
  disagree, naming both, so a drifted declaration fails at the first build and no width is copied out of a
  document (`e2e-surface.md` §3.3, `encodings.md` §1, §6, `features/surface.md` §5, D-3).
- **Refusals:** none; it has no argument and nothing to vary (`e2e-surface.md` §3.3, ASM-7, D-19).
- **Determinism and ordering:** two calls return equal records, the backends in `numpy` then `torch` order
  and the kinds in the order of the table; the catalogue is plain data a report may quote (D-7, `protocol.md` §1).
  Its `learning_rules`, `utilities` and `hyper` are this module's own keys (`records.md` §1), published so a report
  can name them and never a second copy a fairness check compares — the copy audited is the variant entries' (`ladder.md` §3, §4, D-19, D-20).

## 4. `build_learner` — one learner from one spec (`general` row)

- **Signature:** `build_learner(spec)`.
- **Arguments:** one mapping, `records.md` §3's learner spec. Three keys are required and three are read when
  present; **every other key is ignored**, including a variant entry's `hyper`, which is the run record's data
  and not a per-learner argument (`records.md` §3, `learner.md` §1):

| Key | Contract |
|---|---|
| `backend` | **required** — `numpy` or `torch`, one of `learners()`'s backends (D-7, `records.md` §3) |
| `architecture` | **required** — a mapping with `kind`, a kind name §3 declares, plus that kind's settings from `width`, `depth`, `sparsity` and `residual`, **or** a bare kind name, in which case `sizes` must carry the width and depth because the name alone sources no size; a setting the kind does not read is ignored (`records.md` §2, §3, `ladder.md` §3) |
| `seed` | **required** — the seed of the learner's own generator, an integer, recorded by the run that builds it (ASM-2, `protocol.md` §4) |
| `learning_rule`, `utility` | optional — the catalogue members the learner learns under and whose reward its training target carries: one of §3's `learning_rules` and one of §3's `utilities`, **each absent meaning its own first**, the defaults this document declares and never infers from a caller's silence, and the keys a two-rule or a two-utility pair differs on (`records.md` §2, §3, `rules.md` §2, §4, `utilities.md` §2, §5, `utility.md` §2, D-19, D-20) |
| `sizes` | optional and redundant: width and depth, with `architecture` authoritative when both are present — but the only source of width and depth under a bare kind name (`records.md` §3) |
| `encoder` | optional — *the encoder when the caller has one*: an encoder from `features.build_encoder`, supplied by the caller because building one is not among the five calls `module-map.md` §2 grants this module. The learner is built for it and checked against it; absent, its kind's `observation_size` is the size it is built for (`e2e-surface.md` §3.3, `module-map.md` §2, §3 of this file) |

- **Returns:** a learner, **complete at construction** in either case above — sized from the encoder's
  `observation_spec` or, with no encoder, from the `observation_size` its kind declares (§3, `e2e-surface.md`
  §3.3) — under the rule its spec names and on the reward of the utility it names, each catalogue's first when it
  names none, and the only way to obtain one, so every learner came from a declared backend, kind, rule and
  utility (`e2e-surface.md` §1, D-7, `utility.md` §2, D-19, D-20). Completion draws from the learner's own seeded
  generator, so two learners from one spec are one learner in capacity, in rule and utility, and in every decision (§1, ASM-2).
- **Refusals:** a missing required key, with that key in the error (`records.md` §3); a bare kind name with no
  `sizes`, because its width and depth then have no source and no default is substituted (D-12, `records.md` §3); a
  backend or a kind §3 does not declare, or a `learning_rule` or a `utility` §3 does not carry — a non-string and an
  uncarried name alike — with that value and the catalogue's names in the error (D-7, D-19, D-20, `e2e-surface.md` §2);
  a seed that is not an integer (ASM-2); a width or depth that is not a positive integer, or a `sparsity` outside `[0, 1]`
  (`ladder.md` §3, `records.md` §2); a value that is not an encoder; and an `encoder` whose `observation_spec` kind
  or size contradicts the kind's own row, naming both (`e2e-surface.md` §3.3, D-3, `encodings.md` §1, §6).
- **Determinism:** one spec builds one learner: two learners from one spec carry one parameter count, one
  rule and one utility, and make one decision on one observation, because the initialisation draws from the
  learner's own seeded generator and from nothing else (ASM-2, `protocol.md` §4, ASM-10, `utility.md` §3).

## 5. `param_count` — the capacity measurement (`general` row)

- **Signature:** `param_count(learner)`.
- **Arguments:** a learner from `build_learner` (`e2e-surface.md` §3.3, §4).
- **Returns:** one integer — the count of the learner's trainable parameters, which is the ladder's matched
  capacity (`e2e-surface.md` §3.3, ASM-10). The counting rule is `learner.md` §3's: one rule over every trainable
  value, the input block included and the target copy and buffers excluded, so the number is a measurement and not
  a per-backend, per-state or per-rule convention — **the rule does not move it**: both catalogue members hold the
  same trainable parameters, so one architecture reports one count under either (D-7, ASM-10, `rules.md` §3, D-19).
- **Refusals:** a value that is not a learner, naming that contract; a baseline is not a learner, and its parameter
  count is the `0` that `baselines()` declares — the count `records.md` §9 records for a baseline cell member
  (ASM-10, `records.md` §9, §11 of this file).
- **Determinism:** one learner reports one count; a learner built twice from one spec reports the same one, and a restored learner reports the saved one (`protocol.md` §5, ASM-5).

## 6. `act` — one training-time decision (`general` row)

- **Signature:** `act(learner, observation, legal_mask)`.
- **Arguments:** a learner; one observation as `features.encode` returns it for the decision; and the
  decision's legal index sequence of §2 (`e2e-surface.md` §3.3, `records.md` §4).
- **Returns:** the decision record — a mapping carrying the chosen index under `action` as a plain Python integer,
  plus the learner's own record of the decision: the mapping form rather than a bare index, because the record
  travels beside the index, which is a member of the mask (`e2e-surface.md` §3.3, `records.md` §6, §2 of this file).
- **Refusals:** a value that is not a learner; an observation whose shape, dtype or representation family
  contradicts the learner's, naming both (D-3, `encodings.md` §1); a mask that is empty, repeats an index, or
  holds an index outside `{0, 1, 2}` (D-2, §2); and a value in the masked set that is not finite, refused by name
  rather than reaching the tie-break (`divergence.md` §2, §3, D-19).
- **Determinism:** one learner state, one observation and one mask give one index, because the decision is **the
  observation and the mask** and the exploration is drawn from the learner's own seeded generator keyed by it: a
  second call at the same state answers the same index rather than advancing a stream, and a policy at the
  learner's own seed answers the same index (§1, §10, `learner.md` §1, ASM-7). The rule is not read here: schedule,
  keyed draw, tie-break and masked maximum run over three values it never changes (`rules.md` §3, D-19).

## 7. `learn` — one update and its statistics (`general` row)

- **Signature:** `learn(learner, transitions)`.
- **Arguments:** a learner, and a non-empty sequence of the transition records `records.md` §4 fixes —
  **required**: `observation`, `next_observation`, `action`, `reward`, `terminal`, `legal`, `next_legal`
  (`records.md` §4). The batch is the caller's order and neither sampled nor shuffled, which is what lets a
  comparison pair declare one sample order (ASM-7, `ladder.md` §5).
- **Returns:** one mapping of the update's own statistics, read under these keys:

| Key | Content |
|---|---|
| `td_error` | **the learning signal**: one number, the batch's mean absolute temporal-difference error, which is the curve's signal in the report (`protocol.md` §1) |
| `transitions` | the transitions this call consumed, an integer — the learner's own progress, **not** the hands behind a version: one hand holds several decisions and this module never sees a hand, so a version's `samples` is the run's count of hands and not the sum of these (`records.md` §7, `module-map.md` §3) |

- **The rule fixes the target, and nothing else.** `masked-q-learning` aims at `reward + discount ×` the **maximum**
  of the successor's target-copy values over `next_legal`; `double-q-learning` aims at `reward + discount ×` the
  target copy's value **at the index the online parameters' masked argmax selects** over `next_legal` — selection by
  the online parameters, evaluation by the copy. Both aim at `reward` alone at a terminal transition, and
  everything else — validation, loop, statistics, step, refresh counter, position — is one path (`rules.md` §2, §3).
- **Refusals:** a value that is not a learner — a baseline never learns from a match (D-6, `protocol.md` §3); an
  empty batch; a transition missing a required key of `records.md` §4, with that key named; an `action` outside that
  transition's `legal`, a mask outside `{0, 1, 2}` (D-2), or an observation of another shape or family (D-3); and a
  divergence — a transition whose td_error or whose step left a value not finite — refused by name at that
  transition (`divergence.md` §2, §3, D-19).
- **Determinism:** one learner state, one rule and one batch give one update and one statistic set, this call being
  the only place a learner's schedule moves (§1); the aim, the masking and the terminal reward are the bullet above,
  never a per-backend or per-call choice (ASM-7, ASM-12, D-19).

## 8. `save` — write one checkpoint (`general` row)

- **Signature:** `save(learner, path)`.
- **Arguments:** a learner, and a file path to write, which the caller owns: `checkpoints/` belongs to
  `training` and this module writes only where it is told (`module-map.md` §5, `e2e-surface.md` §3.3).
- **Returns:** the path it wrote, so a run record names the artefact it produced (`records.md` §12). The container
  is **format version 3** and records the learner's `learning_rule` and its `utility` beside its seed and its
  representation, so a member is read under the rule and on the objective it was trained under (§9, `utility.md` §4, D-19, D-20).
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
  representation and size, same parameter values, same decision boundary, **the rule its container records** and
  **the utility it records** — the equality `protocol.md` §5 requires of `save`/`load` (ASM-5, D-19, D-20). A
  **version-1** container carries neither field and is read as `masked-q-learning` and `net-chips`; a **version-2**
  container carries the rule and is read as `net-chips`; one of either older version carrying a field its writer
  never wrote is refused by name (`utility.md` §4, `rules.md` §6, D-20).
- **Refusals:** a missing or unreadable path, with that path named; a checkpoint whose recorded form this module
  does not read, a `learning_rule` or a `utility` outside the catalogue included; **and a `spec` that disagrees with
  the checkpoint on a key the spec carries** — its `backend`, its kind, its `seed`, its `learning_rule`, its
  `utility`, or the representation and size an encoder it carries declares — naming that key and both values, never
  coercing the spec onto the parameters (`e2e-surface.md` §2, ASM-5, `utility.md` §4, §5). `sizes` never disagrees,
  `architecture` being authoritative, and with no encoder the representation comes from the file (`records.md` §3, §7).
- **Determinism:** one checkpoint restored twice gives two learners that decide alike, because §1 makes a decision a
  function of state and decision rather than of call order (`protocol.md` §5, ASM-5).

## 10. `as_policy` — one learner as a policy (`general` row)

- **Signature:** `as_policy(learner, encoder, seed)`.
- **Arguments:** a learner; an encoder from `features.build_encoder`, with which the policy turns a readout into an
  observation — built by the caller, who may be `training` or `evaluation`, because `build_encoder` is not among
  the five calls `module-map.md` §2 grants this module; and a seed, an integer, for the policy's own generator — for a
  learner restored by §9, the seed its checkpoint records (`e2e-surface.md` §3.3, `module-map.md` §2, `records.md` §7).
- **Returns:** a policy in the sense of `e2e-surface.md` §2 — a callable taking the readout and the legal
  descriptors and returning one of them (`e2e-surface.md` §2, `engine/environment.md` §6) — and carrying
  `learning_rule` and `utility`, the catalogue members its learner was built under and trained on: the two
  attributes §2 declares, the **only** things a policy gains here, and the labels `evaluation` reads to name a
  table's population and its objectives. The callable, its seeding and its decision are unchanged by them, and a
  baseline's policy carries neither (`rules.md` §7, `utility.md` §3, D-19, D-20). The policy applies the learner's
  own decision rule to the decision its arguments name — the observation `encode` produces and the mask
  `legal_indices` gives — so at the learner's own seed it decides exactly as `act` does on that decision, and at
  another seed it applies the same rule with an independent exploration key; and it holds the state as it was at
  build time, so a later `learn` does not change a policy already built (§1, ASM-5, `protocol.md` §5, `learner.md` §1).
- **Refusals:** a value that is not a learner or not an encoder, naming that contract; a seed that is not an
  integer (ASM-2); an encoder whose `observation_spec` kind or size contradicts the learner's kind, naming both
  (§4, D-3); and a non-finite masked value (`divergence.md` §2). It never returns a descriptor outside `legal_actions` (D-2).
- **Determinism:** two policies built from one learner, one encoder and one seed answer the same decisions, the only
  randomness being the policy's own seeded generator keyed by the decision (§1, `protocol.md` §4, ASM-2).

## 11. `baselines` — the six fixed baselines (`fixed` row)

- **Signature:** `baselines()`.
- **Arguments:** none: they are D-6's three and D-21's three folders, so there is no parameter by which the set can be
  varied, and nothing to refuse (`e2e-surface.md` §3.3, D-6, D-21).
- **Returns:** one mapping keyed by the six names in `protocol.md` §3's order — `random`, `always-call`, `oracle`,
  `fold-no-pair-or-face`, `fold-no-pair-or-better`, `fold-large-bet` — each value carrying that baseline's name, the
  rule `protocol.md` §3 states for it, its `params` of `0`, because a baseline has no trainable parameter, and its
  `anchor` flag: `True` for the three of D-6 and `False` for D-21's folders, which is the set the rating is zeroed on
  (`protocol.md` §3, `records.md` §9, ASM-32, D-21). The oracle's value also declares the sample count its equity query
  uses — the count `build_baseline`'s `oracle` itself queries, so a caller that built the baseline at one seed
  re-issues the same query, at that seed and at the declared count, and checks the inequality itself; a re-issue at any
  other count is a different query and cannot falsify the rule (§12, `learner.md` §5, `engine/surface.md` §11, ASM-4).
- **Determinism and ordering:** two calls return equal records, in the order §11's Returns gives the six names; the
  catalogue is plain data a report's header quotes (`protocol.md` §1, §3).

## 12. `build_baseline` — one baseline as a policy (`fixed` row)

- **Signature:** `build_baseline(name, seed)`.
- **Arguments:** one of the six names §11 declares, and a seed for that baseline's own generator
  (`e2e-surface.md` §3.3, ASM-4).
- **Returns:** a policy in the sense of `e2e-surface.md` §2 (ASM-4, `protocol.md` §3). Its rule is
  `learner.md` §5's; it receives only the readout and the legal descriptors, which is why the oracle asks
  `engine.equity` with the readout it was handed rather than with a hand, and why `fold-large-bet` reads the declared
  starting stack through `engine.game_config` rather than holding a copy of it (`e2e-surface.md` §2,
  `engine/surface.md` §11, `folders.md` §2, ASM-31).
- **Refusals:** a name the six do not include, with that name in the error (`e2e-surface.md` §2,
  `protocol.md` §3); a seed that is not an integer (ASM-2).
- **Determinism:** one decision gives one descriptor, because no baseline advances any state; for `random` one seed
  repeats its choices and two seeds differ (`protocol.md` §3), while `always-call`, `oracle` and the three folders are
  functions of the decision alone — a folder decides identically at one seed twice and at two different seeds. The draw
  is keyed by the decision as a learner's exploration is, since a uniform draw over a decision's legal indices cannot
  come from a stream position (§1, `protocol.md` §3, §4, ASM-4). A baseline never learns, and its policy carries no
  `learning_rule` and no `utility` (D-6, `e2e-surface.md` §2, D-19, D-20).
