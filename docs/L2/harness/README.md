# harness — L2 integration interface

- **Layer:** L2 · **Module:** `harness` · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-06 · §4 corrected by measurement
- **Covers:** the six entry points of `docs/L1/e2e-surface.md` §3.6 — test support whose consumers are test
  batteries (brief §5, `module-map.md` §1) — and the paths this module owns beside them: `tests/conftest.py`, the
  L1 battery under `tests/e2e/` (its consumer, never its implementation) and `pyproject.toml` with the dependency
  lock (ASM-11, `module-map.md` §5)
- **Reads:** `docs/L1/module-map.md` §1–§5, `e2e-surface.md` §1, §2, §3.6, §5, `records.md` §1, §5, §9, §12, §14,
  `battery.md` §1–§5, `protocol.md` §2, §4, §6, `assumptions.md` (ASM-2, ASM-11, ASM-15); at the consumed edge
  `training/surface.md` §4, `agents/surface.md` §4, §12, `features/surface.md` §4, `engine/surface.md` §4,
  `evaluation/surface.md` §5; and the battery — `tests/e2e/README.md`, `_surface.py`, `_records.py`,
  `test_fam14_harness.py`, the harness cases of `test_fam16_blind.py`
- **Ceiling:** 112 lines. At the ceiling, split by owner — never append

## 1. The one job

`harness` is test support: it drives a case from pinned preconditions, builds only the objects the map declares,
hands a case a policy double, judges an observed value and reports the cost of the work that ran
(`module-map.md` §1, brief §5). It never re-implements, simplifies or substitutes for a subsystem: the objects it
returns are an owning module's own, or a policy double of the shared policy protocol and no more, and every
judgement is about a value a step returned (`e2e-surface.md` §2, `module-map.md` §3, brief §5, D-13). Its
consumers are test batteries, so its contract is what a case needs (`records.md` §14, `module-map.md` §5).

## 2. The two documents

| Document | The owner of that question | What it fixes |
|---|---|---|
| `surface.md` | the callable surface | per entry point: signature, argument contract, returned record, refusals, determinism; the driver's case and result records (§2); the fixture facts and the four expectation kinds (§3, §6); the factory's six kinds (§4); the two documented seam behaviours (§5); the four timing facts (§7) (`e2e-surface.md` §3.6, `records.md` §14) |
| this file | the boundary, the counts, what is left below | where the harness sits and the dependency direction (§3); counts, cap and blind instances (§4); the invariants the battery asserts (§5); the choices this layer made (§6); what L3 owns (§7) (D-1, D-12, D-13) |

## 3. The boundary and the dependency direction

- **Above every module, calling down.** Every call this module makes is on one of the 49 declared entry points of
  `e2e-surface.md` §3, and it reaches no name below one: no import from `src/<other>/` internals, no private
  helper, no second spelling of another module's contract (`module-map.md` §2, §3, brief §5, D-13).
- **The two loops it must not write.** The loop is `training`'s (D-3, D-16, `module-map.md` §1) and the match is
  `evaluation`'s (D-16, `module-map.md` §3): a step calls `training.run` or `evaluation.match` when a case wants
  one, and the harness never iterates hands, draws an opponent, plays a cell or fits a rating (brief §5).
- **No substituted subsystem.** It deals no hand (`engine`), encodes no observation (`features`), chooses and learns
  no action (`agents`), schedules no opponent and measures no cell (`evaluation`), runs no loop (`training`). A
  `seam` doubles a *policy* only, and a `factory` returns the owning module's own object (`surface.md` §4,
  `module-map.md` §3, D-13).
- **One seeding point.** The only way an entry point here moves the global `random` stream is by delegating to
  `engine.new_hand` through `factory`; the harness seeds nothing itself (ASM-2, `protocol.md` §4).
- **CPU, network-free, no dependency.** Every entry point runs on CPU and touches no network — a workflow-started run
  is CPU-bound because the sandbox denies the GPU nodes, and a GPU run is the user's (`battery.md` §2, D-8,
  `protocol.md` §6) — and none adds a dependency: the battery it supports runs on `unittest` (`battery.md` §2).
- **The freedom split.** A *seam label* is the battery's to invent, because a seam's contract is the policy
  protocol of `e2e-surface.md` §2 and not its label; an *expectation kind* is this module's own set, discovered
  from `fixtures()`, so a battery invents an observed value and never a kind (`e2e-surface.md` §3.6,
  `records.md` §14, D-13, D-15).
- **Nothing is claimed about a result.** The harness judges records a case produced; it never requires a member to
  outrank a baseline, and `timings` never asserts that a wall clock was beaten (`battery.md` §2, §5, ASM-15, D-6).

## 4. Counts, cap and the blind instances

Six entry points, and L2 adds, removes and renames none: needing a seventh is a defect that returns as an
adjudication to L1 and is never invented here (D-12, `e2e-surface.md` §1, `modules.md` §3). **All six rows are
`general`** — `drive`, `fixtures`, `factory`, `seam`, `expect`, `timings` — so the battery carries six instances
invented from this surface alone (FAM-16.32–FAM-16.37, `battery.md` §4, D-15). No row here is exempt as `fixed`,
and the instances are the test writer's: `surface.md` fixes this module's own vocabulary — its kinds, choices and
facts — and no instance of a battery's case (`e2e-surface.md` §5, D-15).

The harness cap is `50 + 10 × 6 = 110` lines, printed by `strata-lint` as an INFO row and never measured by it (brief
§5, `module-map.md` §4); the five sibling READMEs read it as bounding the harness files that drive a module, and
measured 2026-11-05 every shipped module exceeds it under either reading (`engine`'s `src/` 703 against 140, its own
support 358 against 140; `training`'s support 1005 against 110). So this module reports its figure rather than
asserting a bound nothing meets: `src/harness/` is **one file of 147 lines, 37 over** (144 before §6's totality was moved into the
entry point, which is where it is now enforced once for every kind), the delta is structural
(`docs/L3/harness/layout.md` §2 breaks the contract of `surface.md` §6 into what the six entry points cost before a
kind exists) and it returns to L1 as a finding, not as a clause dropped from §6 — the alternative, one expectation
kind, still measures ≈127 and is the one-assertion runner H-1 rejects. The cap governs no part of the L1 battery under
`tests/e2e/`, whose size is the test writer's (brief §5, `module-map.md` §5, ASM-11).

## 5. The invariants the battery asserts against this module

| Family | The harness rows it drives | What is asserted here |
|---|---|---|
| FAM-1 | all six (FAM-1.44–1.49) | each name exists, is callable and returns something: the declared surface is present, and an absent name is one finding per name (brief §5, `battery.md` §3) |
| FAM-14 | `fixtures`, `factory`, `seam`, `expect`, `drive`, `timings` | a case runs through the driver from a pinned fixture; the factory builds only declared objects and refuses an undeclared one; a seam of either documented behaviour satisfies the policy protocol and yields a real, zero-sum engine episode; `expect` yields a verdict for every kind `fixtures()` lists and a named failure for a kind it does not; `drive` runs each step once, names the case and judges it; `timings` reports the cost (FAM-14.1–14.11, `records.md` §14, brief §5) |
| FAM-16 | all six (FAM-16.32–16.37) | one invented instance per `general` row: a case, a scratch probe, a 48-wide 4-deep learner, two invented seam labels, an invented observed value under a listed kind, and the clock of a driven case (D-15, `battery.md` §4) |
| FAM-10 | `timings` | the cost record carries the hands counted and a per-hand cost or throughput, read by what its keys name (FAM-10.4, ASM-15) |
| FAM-13 | `drive`, `timings` | the parity pair's clock comes from the driver: `timings` is the cost of work the driver measured (FAM-13.6, D-7) |

Every case in these families is satisfiable from `surface.md` alone (D-11, D-12).

## 6. The choices this layer made, and the alternative each rejected

| Id | The choice | The alternative rejected |
|---|---|---|
| H-1 | the expectation-kind set is `zero-sum`, `legal-choice`, `counted`, `refused`, in that order (`surface.md` §6) | one kind per record shape — episode, cell, matrix, rating — which would make `fixtures()` a copy of `records.md` and grow with the league's record vocabulary; and a single `zero-sum` kind, which judges one contract and makes the driver a one-assertion runner (`e2e-surface.md` §3.6, `battery.md` §3 FAM-14) |
| H-2 | `recording` chooses the first descriptor `legal_actions` returns; `synthetic` chooses by a cyclic schedule over the legal descriptors; any other label behaves as `recording` | a seeded random draw in either behaviour: a seam takes a label and no seed, so it would have to borrow the global `random` stream and couple a test double to the engine's seeding (ASM-2, `protocol.md` §4) |
| H-3 | every seam, whatever its label, records the readouts it was called with | letting `synthetic` record nothing, which `e2e-surface.md` §3.6's Returns column forbids: every seam returns "a policy that records the readouts it was called with", so the label can only decide the choice rule |
| H-4 | a case's step is a zero-argument callable that calls declared entry points | a structured step naming an entry point and its arguments, which would restate 49 argument contracts inside the harness — the substitution brief §5 forbids |
| H-5 | the driver counts hands from the records its steps returned: one per episode record, a cell's own `hands`, none otherwise | counting steps as hands, or wrapping `engine.play_hand` to count hands directly — the first is false (a step may play 120 hands), the second makes the harness a scheduler of hands (`module-map.md` §3) |
| H-6 | `drive` reports a broken case as a failure and never raises; `fixtures()` pins one scratch root per process, the protocol's first seed and `cpu` | raising on a malformed case (it converts a broken case into an error in the caller's runner, FAM-14.10), a fresh root per call (a case's own writes become unfindable), a per-process random seed, and the device catalogue `training.devices()` owns (D-8, `protocol.md` §2, §6) |

## 7. What is left to L3, and the packaging this layer owns

- **L3 owns** the error classes the refusals raise, the driver's step bookkeeping and the layout of one seam call
  log entry (the `calls` sequence is contract, its keys are not), how the scratch root is created and named, the
  factory's dispatch, `src/harness/`'s layout, `tests/harness/`'s unit tests and `tests/conftest.py` (D-1, D-13).
- **`tests/conftest.py` also points `training`'s write root at a private temporary directory** for the whole pytest
  session (`PYPOKER_CHECKPOINT_ROOT`, `training/write-root.md` §3–§4), so no battery writes into the shipped tree (D-8).
- **Not left to L3:** the six names, the four expectation kinds and their order, the six factory kinds, the two seam
  behaviours, the driver's case and result keys, the timing facts — a battery reads them (`e2e-surface.md` §1, D-12).
- **Packaging, owned by path and not designed here.** `pyproject.toml` and the lock file are this module's
  (`module-map.md` §5, ASM-11): the dependencies are `strata/platform.md`'s, and this layer fixes only that the
  harness adds none of its own and that none is added to make the battery collectable (`battery.md` §2, D-8, brief §4).
- **One L1 wording is a naming contract, not a call.** `records.md` §12 says a run record's `timings` carries "in
  `harness.timings`'s facts", while `module-map.md` §2 grants no module a call into the harness: the two sides share
  the four fact names `surface.md` §7 fixes, and `training` measures them itself (`training/surface.md` §4, D-13).
