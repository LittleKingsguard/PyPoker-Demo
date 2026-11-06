# harness — the callable surface

- **Layer:** L2 · **Module:** `harness` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-05 · §2, §6: totality and never-raise scoped to §1's plain data
- **Owner of this file:** the surface — the six module-level names of `src/harness/`, each with its argument
  contract, its returned record, its refusals and its determinism (D-12, `e2e-surface.md` §1, §3.6) — plus the two
  vocabularies only this module declares: the expectation kinds (§6) and the seam labels (§5)
- **Ceiling:** 245 lines. At the ceiling, split by owner — never append

## 1. Rules that hold of every entry point

The six names are module-level names of the `harness` package, and nothing below one of them is contract
(`e2e-surface.md` §1, brief §5). Seven rules are shared and are stated once here (D-12, D-13):

- The six are fixed: L2 refines types, record keys, ordering and error classes and never adds, removes or renames
  an entry point (D-12, `e2e-surface.md` §1, `modules.md` §3).
- Every returned value is plain data — a mapping, a sequence of names, a path, a verdict — except `factory`'s,
  which is the owning module's own object, and `seam`'s, which is a callable satisfying the policy protocol of
  `e2e-surface.md` §2 (`e2e-surface.md` §1, §2).
- No entry point re-implements, simplifies or substitutes for a subsystem, and none imports a name below another
  module's declared entry point (brief §5, `module-map.md` §3, D-13).
- The only path any entry point creates is `fixtures()`'s scratch root; nothing here writes a checkpoint, a table
  or a report, because those are `training`'s and `evaluation`'s artefacts (`module-map.md` §5, D-13).
- No entry point seeds or advances the global `random` stream except by delegating to `engine.new_hand` through
  `factory`, and none draws from a generator of its own (ASM-2, `protocol.md` §4).
- Every entry point runs on CPU and touches no network (`battery.md` §2, D-8, `protocol.md` §6).
- A violated contract is refused with an error naming it, except where an entry point is contracted to *report* the
  failure instead — `drive` (§2) for the case it is handed, `expect` (§6) for an unlisted kind — because L1
  contracts a verdict there and a battery must be able to read it (`e2e-surface.md` §2, `records.md` §14).

## 2. `drive` — one case, one verdict (`general` row)

- **Signature:** `drive(case)`.
- **Arguments:** one case, a mapping with three **required** keys (`records.md` §14):
  - `id` — a non-empty string naming the case. The result repeats it verbatim, because a layer return cites the
    case by it (FAM-14.9, FAM-16.32).
  - `steps` — a non-empty ordered sequence of **zero-argument callables**. A step is a case's call on one or more
    declared entry points of `e2e-surface.md` §3, and a callable is the only form it takes, so the harness never
    restates an entry point's arguments (brief §5, H-4, README §6). The driver does not police that provenance: it
    calls the callable it is handed and judges what came back, so a case that composes a value is judged the same
    way (FAM-14.10).
  - `expect` — a non-empty ordered sequence of expectation entries (`records.md` §14). An entry is either a kind
    name `fixtures()` lists — judging the case's **last** step — or a mapping `{"kind", "step"}` judging the step
    at that index (`e2e-surface.md` §3.6, §6 below). **Every step is judged by at least one entry**, and a step
    judged twice must pass both judgements: this layer's refinement of `records.md` §14's "records each step's
    outcome and a verdict", since a verdict over a step nobody judged is not a verdict about the case as run.
- **Behaviour:**
  - Every step is called **exactly once**, in declared order: never twice, never retried, never reordered, never
    skipped, never evaluated speculatively, and not stopped at a step that refused — a case's later steps may be
    independent, and each step's outcome is judged separately (FAM-14.9, FAM-16.32).
  - The driver holds a monotonic clock around each step and around the case, and adds what it measured to the
    record `timings` reports (§7, `records.md` §12).
  - Judging is `expect`: one kind and one observed value give the same verdict here as when a battery calls
    `expect` directly, so the driver adds no second judging rule (§6, FAM-14.8).
  - The observation a kind is handed is the step's outcome — the value the step returned, or, for a step that
    raised, the refusal observation `{"refused": true, "error": "<the error's class and message>"}` (§6).
  - `hands` is counted from the outcomes the steps returned and never from the driver's own work: one hand per
    episode record (`records.md` §5 — `play_hand` plays one hand), the `hands` a cell record declares
    (`records.md` §9), and nothing for any other value (H-5, README §6).
  - `drive` **never raises**: a case that is not a mapping, a missing or empty `id`, `steps` or `expect`, a step
    that is not callable, an unlisted expectation kind, an out-of-range step index and an unjudged step are each a
    named failure inside the result (`records.md` §14, FAM-14.10). A step that **raised** is not a case-level
    failure: it is recorded as the refusal observation above and judged by the entry covering it, so a case that
    expected the refusal passes and any other case fails (§6). This is §1's report edge — `e2e-surface.md` §2 lets a
    violated contract raise or refuse, and `drive` reports so a broken case fails rather than erroring in the
    caller's runner (FAM-14.10, H-6). The guarantee covers those shapes and any outcome that is §1's plain data; an
    object whose own mapping protocol raises is no such value, and the counter behind `hands` is no kind (§6).
- **Returns:** the case-result record:

| Key | Content |
|---|---|
| `id` | the case's own id, verbatim (`records.md` §14, FAM-14.9) |
| `steps` | one entry per step, in declared order: `index`, `outcome` (the returned value or §2's refusal observation), `refused` (a flag), `seconds` (the time measured around that one call) |
| `expectations` | one entry per expectation entry, in declared order: the `expect` record of §6 — `kind`, `step`, `verdict`, `reason` |
| `hands` | the hands the steps' outcomes declared, under §2's counting rule |
| `wall_clock_seconds` | the elapsed time the driver measured for the case |
| `verdict` | `pass` when every expectation passed and every step's outcome was judged; otherwise `fail` |
| `reason` | `None` on a pass; on a failure one sentence naming the step or the kind that failed |

  A passing result states its verdict once, in `verdict`, and its `reason` is `None`: a `pass` whose reason argued
  for a failure would not be a record (FAM-14.9, FAM-14.10, FAM-16.32).
- **Refusals:** none. The one argument is reported rather than refused (H-6, FAM-14.10).
- **Determinism:** one case gives one result twice — the same step outcomes, the same expectation verdicts and the
  same `verdict` — for the same steps, seeds and pool membership; only the measured seconds differ
  (`protocol.md` §4, ASM-2, `battery.md` §3 FAM-4). One `drive` call is one run of the case, so a second call runs
  its steps a second time.

## 3. `fixtures` — the preconditions a case starts from (`general` row)

- **Signature:** `fixtures()`.
- **Arguments:** none: a precondition that the caller could vary is not pinned (`records.md` §14).
- **Returns:** one mapping with these keys:

| Key | Content |
|---|---|
| `root` | the scratch root: an absolute path this module owns, created on the first call and reused by every later call in the process, empty at process start, and writable (`records.md` §14, FAM-14.1, FAM-16.33) |
| `seed` | the pinned seed: `0`, the protocol's first seed, so the fixture invents no value a design document owns (`protocol.md` §2) |
| `device` | the pinned device: `cpu` — a workflow-started run is CPU-bound because the file sandbox denies the GPU device nodes, and a GPU run is the user's, started outside it (D-8, `protocol.md` §6) |
| `expectations` | the expectation kinds §6 accepts, as an ordered sequence of names, first kind first (§6, `e2e-surface.md` §3.6, FAM-14.1, FAM-14.8) |

- **Behaviour:** the root is created once and named once, so a case that writes a file into it and reads it back in
  a later call finds it (H-6, FAM-16.33). The harness does not delete it: an artefact a case wrote may still be
  needed after the case ended, and the platform's temporary area owns cleanup (`battery.md` §2).
- **Refusals:** none; it has no argument.
- **Determinism:** `seed`, `device` and `expectations` are equal on every call, in every process — a precondition
  that varied would make a red case unreproducible (`protocol.md` §2, D-6). `root` is stable within a process, and
  a caller that needs a fresh directory creates one inside it (`battery.md` §2).
- **Never:** it restates no catalogue another module owns. The device list and its default are
  `training.devices()`'s (`e2e-surface.md` §3.5, D-8) and the seed set is `evaluation.protocol()`'s
  (`e2e-surface.md` §3.4, `protocol.md` §2): a fixture that read either would make pinned preconditions depend on
  another module's implementation (D-13, H-6).

## 4. `factory` — one declared object, built by its owner (`general` row)

- **Signature:** `factory(kind, options)`.
- **Arguments:** `kind` — one of six declared object kinds and nothing else (`records.md` §14); `options` — the
  owning entry point's own argument, or, for the one kind whose entry point takes two, those two in the entry
  point's order.
- **The six kinds** (`records.md` §14, D-13):

| `kind` | The owning entry point it calls | `options` |
|---|---|---|
| `encoder` | `features.build_encoder` (`features/surface.md` §4) | the encoding name |
| `learner` | `agents.build_learner` (`agents/surface.md` §4) | one learner spec, `records.md` §3 |
| `baseline` | `agents.build_baseline` (`agents/surface.md` §12) | the name and the seed, in that order |
| `hand` | `engine.new_hand` (`engine/surface.md` §4) | the seed |
| `rung` | `training.rung` (`training/surface.md` §3) | the rung name |
| `pool` | `evaluation.build_pool` (`evaluation/surface.md` §5) | one membership declaration, `records.md` §8 |

- **Behaviour:** the factory is a dispatcher and not a builder. It validates nothing about `options` — the owning
  entry point is the authority on its own argument — supplies no default for an argument that entry point
  requires, and returns exactly the object that entry point returned, not a copy, not a wrapper and not a second
  implementation of it (brief §5, `module-map.md` §3, D-13). Two consequences a battery asserts: a learner built
  here has the parameter count `agents.build_learner` gives the same spec (FAM-14.2, FAM-16.34), and an encoder
  built here is one `features.encode` accepts (FAM-14.3).
- **Refusals:** a `kind` that is not one of the six, naming the kind and the six declared — because a factory that
  built an undeclared object *is* the substitution this module never makes (FAM-14.4, `module-map.md` §3) — and a
  refusal the owning entry point raises, surfaced as it is, named and never repaired (`e2e-surface.md` §2). The
  factory validates no option itself: a missing argument is arity, and the owning entry point is the authority on
  what it accepts (`records.md` §14, D-13).
- **Determinism:** one kind and one `options` value reach one call of one entry point and add no state of their own;
  what the object then does is the owning module's contract (`agents/surface.md` §4, `engine/surface.md` §4). A
  `hand` is a deal, so `engine.new_hand`'s seeding rule applies to it and to nothing else here (ASM-2, `protocol.md` §4).
- **Never:** it builds no fourth baseline, no seventh rung, no third encoding and no version of its own: those
  vocabularies belong to `agents`, `training`, `features` and `evaluation`, and an invented instance of one
  reaches the surface through the owning entry point or not at all (`e2e-surface.md` §5, D-13, `battery.md` §4).

## 5. `seam` — one policy double, any label (`general` row)

- **Signature:** `seam(label)`.
- **Arguments:** `label` — any string, including one in no design document. The label selects a documented
  behaviour and is never checked against a list, because a seam's contract is the policy protocol and not the
  label (`e2e-surface.md` §3.6, `records.md` §14, `battery.md` §4, D-15).
- **Returns:** a policy in the sense of `e2e-surface.md` §2 — a callable taking `(readout, legal_actions)` and
  returning one descriptor **from `legal_actions`**, drawn in the engine's order (`e2e-surface.md` §2) — which
  records every call it answered, in a `calls` sequence on the returned policy: one record per call, in call
  order, holding the `readout` and the `legal_actions` it was handed and the descriptor it returned
  (`e2e-surface.md` §3.6, H-3).
- **The documented behaviours.** Both record; the label decides only the choice rule inside `legal_actions`
  (H-2, H-3):

| `label` | The choice rule |
|---|---|
| `recording`, and every label that is not `synthetic` | the **first** descriptor `legal_actions` returned, every call |
| `synthetic` | a synthetic schedule: call *n* of that instance returns the descriptor at position *n* modulo the number of legal descriptors, so a case gets a policy that spreads its choices over the vocabulary and needs no learner (FAM-14.6) |

- **Refusals:** an **empty** legal set, naming that a policy must return a member of `legal_actions`
  (`e2e-surface.md` §2, D-2) — a seam never folds instead and never invents a descriptor, because a policy that
  returns an illegal action is a contract violation and not a fold (D-2).
- **Determinism:** two seams of one label, driven over the same sequence of `(readout, legal_actions)` pairs,
  return the same descriptors, because each `seam(label)` call returns a fresh instance whose log starts empty and
  whose schedule starts at its first call (FAM-14.5, FAM-14.6, FAM-16.35). A seam's choice is a function of its
  label and of the calls it answered, and of no clock, generator, global stream or ambient fixture (ASM-2, D-6).
- **Never:** it is a synthetic double of a *policy* and of nothing else. It deals no hand, encodes no observation,
  computes no equity, holds no learner, learns nothing and measures nothing (brief §5, `module-map.md` §3); it
  knows the readout only as the argument of `e2e-surface.md` §2 and reads no field of it to choose (D-13).
  The episode it plays is the engine's: `engine.play_hand` stays zero-sum because the engine decided the hand and
  the seam only chose inside the legal set (FAM-14.7, ASM-12).

## 6. `expect` — one verdict for one observed value (`general` row)

- **Signature:** `expect(kind, observation)`.
- **Arguments:** `kind` — one of the kinds `fixtures()` lists, as a string (§3); `observation` — any observed
  value: a step's returned record, a refusal observation, or a value a case composed (`e2e-surface.md` §3.6,
  `records.md` §14).
- **Returns:** the verdict record — `kind` (the kind as handed), `verdict` (`pass` or `fail`), and `reason`:
  `None` on a pass, and on a failure one sentence that names the kind verbatim, states the violated contract and
  names the fact that did not hold (`e2e-surface.md` §3.6, FAM-14.8, FAM-16.36).
- **The kind set.** These four, in this order, and `fixtures()` lists them in it; the first listed kind is the one
  a battery that takes the first listed kind gets, so it is the kind that judges an episode record — the value
  most cases drive (FAM-14.8, H-1):

| Kind | Passes when | Names a failure when | The contract it judges |
|---|---|---|---|
| `zero-sum` | the value's per-seat chip deltas sum to zero — read, in this order, from an episode record's `payoffs` (`records.md` §5), a cell record's two directions' `mean_chip_delta` (`records.md` §9), a mapping of two per-seat numbers, or a sequence of two numbers | the deltas do not sum to zero, or the value states no per-seat deltas | `protocol.md` §2, `records.md` §5, §9, ASM-12, FAM-7 |
| `legal-choice` | the value is `{"chosen", "legal"}` and the chosen descriptor is one of the legal descriptors | the chosen descriptor is outside the legal set, or the value states no legal descriptors | `e2e-surface.md` §2, D-2 |
| `counted` | the value is a cell record and each direction's wins + ties + losses equals the `hands` it reports | the counts do not account for the hands, or the value is not a cell record | `protocol.md` §2, `records.md` §9, FAM-7 |
| `refused` | the value is a refusal observation: a mapping whose `refused` flag is true — the shape §2's driver builds for a step that raised | the observed work returned a value rather than refusing | `e2e-surface.md` §2, `records.md` §10, §13, FAM-8, FAM-11 |

- **Rules:**
  - **Total.** Every listed kind yields a verdict for *any* observed value — the plain data of §1, one a reader raised on included — so a
    value a kind cannot read is a named failure and never a pass and never a silence (`e2e-surface.md` §3.6, `records.md` §14, FAM-14.8).
  - **Deterministic.** One kind and one observed value give one verdict, in one process and across processes: an
    expectation reads only the value it was handed — never a clock, a stream, a file, an ambient fixture or a
    second observation (FAM-16.36).
  - **A refusal is never inferred from wording.** `refused` reads a declared flag and not the text of a record: a
    kind whose verdict depended on which words an entry point chose would not be deterministic in this sense, and
    the harness would be inventing a refusal semantics no entry point declared (D-13, H-1).
- **Refusals:** a `kind` that is not a string, naming `fixtures()`'s kind set — `e2e-surface.md` §3.6's
  named-failure edge is about a kind *name*, so a non-name is an invalid argument under §1's rule
  (`e2e-surface.md` §2). A string kind `fixtures()` does not list is **not** raised: it is a `fail` whose `reason`
  names the kind verbatim, because L1 contracts exactly that named failure and the driver must be able to report
  the case that rested on it (`e2e-surface.md` §3.6, `records.md` §14, FAM-14.8, FAM-14.10, FAM-16.36).
- **Never:** it judges a record and computes nothing a module declares — it decides no legality, encodes nothing,
  plays no hand, measures no match and fits nothing (`module-map.md` §3, D-13). A verdict is a statement about the
  value it was handed and never a claim about a rung's worth (`battery.md` §5, D-6).

## 7. `timings` — the cost the driver collected (`general` row)

- **Signature:** `timings()`.
- **Arguments:** none: the record is what the driver collected, and a caller that could name a subset would have a
  second measurement path (`e2e-surface.md` §3.6).
- **Returns:** one mapping with these facts (`e2e-surface.md` §3.6, `records.md` §12):

| Key | Content |
|---|---|
| `hands` | the hands the driven cases' outcomes declared, under §2's counting rule — an integer, never negative |
| `wall_clock_seconds` | the summed elapsed time the driver measured for the cases it drove, from the standard library's monotonic clock |
| `seconds_per_hand` | `wall_clock_seconds / hands`, and `0.0` when no hand was counted |
| `hands_per_second` | `hands / wall_clock_seconds`, and `0.0` when no time was measured |
| `cases`, `steps` | this module's own counts of what the driver ran, so a caller can tell "measured nothing yet" from "measured something cheap" |

- **Why this record.** This is the R1/R2 speed evidence of D-7 (FAM-13) and the measurement of ASM-15's per-hand
  bound (ASM-15, FAM-10). These four names are also what a run record carries, because `training` measures them
  itself: no module calls the harness (`records.md` §12, `training/surface.md` §4, `module-map.md` §2, D-13).
- **What a case may assert.** That the record exists, that it carries the hands it counted, and that it carries a
  positive per-hand cost or throughput. A case never asserts that a wall clock was beaten: ASM-15's bound sizes the
  table and is not a test, and a beaten clock would be a flaky assertion rather than a contract (`battery.md` §2,
  ASM-15, FAM-10.4, FAM-13.6, FAM-14.11, FAM-16.37).
- **Refusals:** none; it has no argument.
- **Determinism:** the shape is fixed and the record accumulates over everything the driver *collected* — the plural
  of `e2e-surface.md` §3.6, so `hands`, `cases`, `steps` and the measured clock never decrease between two calls —
  while the numbers themselves are what the work cost (`e2e-surface.md` §3.6, `records.md` §12).
- **Never:** it measures nothing itself, plays no hand and reports no fact the driver did not collect: every number
  here is a measurement of work that ran (FAM-10.4, FAM-14.11, brief §5).
