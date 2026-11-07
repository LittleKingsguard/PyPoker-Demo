# harness — module design (L3)

- **Layer:** L3 · **Module:** `harness` · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-05 · §3, §8 scoped (surface.md Rev 2)
- **Owner:** the module — what it is, the document map, the six names, the layout of `src/harness/`, the import
  boundary, the facts it inherits, and the decisions a later module must not re-derive
- **Realises:** `docs/L2/harness/surface.md` — its six entry points and the two vocabularies only this module owns:
  the four expectation kinds and the two seam behaviours
- **Reads:** `docs/L1/e2e-surface.md` §1–§2, §3.6, §5, `records.md` §5, §9, §13–§14, `module-map.md` §1–§5,
  `battery.md` §2–§5, `protocol.md` §2, §4, §6, `assumptions.md` (ASM-2, ASM-11, ASM-15), `strata/brief.md` §5,
  `strata/platform.md`, `strata/examiner.md`, `strata/decisions.md` (D-1, D-6, D-8, D-11, D-12, D-13, D-15); at the
  consumed edge `docs/L2/features/surface.md` §4, `agents/surface.md` §4, §12, `engine/surface.md` §4,
  `training/surface.md` §3, `evaluation/surface.md` §5; and the battery that judges it —
  `tests/e2e/test_fam14_harness.py`, the harness cases of `test_fam16_blind.py` (FAM-16.32–16.37),
  `test_fam01_surface.py` (FAM-1.44–1.49), `test_fam10_tables.py` (FAM-10.4), `test_fam13_parity.py` (FAM-13.6)
- **Ceiling:** 130 lines. At the ceiling, split by owner — never append
- **Read with:** `layout.md`, `driver.md`, `support.md`, `expectations.md`, `errors.md`, `guardrails.md`
- **Implements:** `src/harness/`, written by L4 and never by L3. `tests/harness/` is this module's unit battery
  (`HRN-1`–`HRN-9`); `tests/e2e/` is its consumer and is never edited from here

## 1. What this module is

`harness` is test support and nothing else (brief §5, `module-map.md` §1, §3): it drives a case from pinned
preconditions, builds the six declared objects a battery may need, hands a case a policy double, judges one observed
value, and reports the cost of the work that ran (`surface.md` §2–§7).

It sits above all five modules and no module calls it (D-13). It imports the five packages and makes **six** calls in
total, one per factory kind (§5); everything else is bookkeeping over values a case's steps returned. A verdict is a
statement about a value the harness was handed — never a claim that a rung works, that a member outranks a baseline, or
that a wall clock was beaten (`battery.md` §2, §5, ASM-15, D-6).

## 2. The documents, one per owner

| Document | Owns | What it fixes |
|---|---|---|
| `layout.md` | the package and its budget | the one file and its order (§1), the budget per unit and the measured cap finding (§2), the import boundary (§3), the compression ladder (§4), the session write root (§5) |
| `driver.md` | `drive()`, `timings()` | the case's shape and its refused-as-failure shapes (§1), the step pass (§2), judging (§3), the case-result record key by key (§4), hands (§5), the cost accumulation and its four facts (§6), determinism (§7) |
| `support.md` | `fixtures()`, `factory()`, `seam()` | the scratch root's creation and name (§1), the six-kind dispatch and `baseline`'s two options in order (§2), the seam closure, the two behaviours, the call-log entry, the empty-set refusal (§3) |
| `expectations.md` | `expect()` | the verdict record (§1), the four kinds in order with each reader's order and its failed fact (§2), totality scoped to §1's plain data and determinism (§3), the two refusal edges (§4) |
| `errors.md` | refusals | one base and three subclasses (§2), the four-part message grammar (§3), one canonical message per refusal (§4) |
| `guardrails.md` | L4 | one numbered note per risk, in the order they bite, each naming the test that catches it |

## 3. The six names

`src/harness/__init__.py` exports exactly the six entry points of `e2e-surface.md` §3.6, declares them in `__all__`,
and adds, removes and renames none (D-12, `surface.md` §1):

    drive(case)                -> Mapping   # the case-result record, never raised for §1's plain data (driver.md §4)
    expect(kind, observation)  -> Mapping   # {kind, verdict, reason} (expectations.md §1)
    factory(kind, options)     -> object    # the owning module's own object, never a wrapper (support.md §2)
    fixtures()                 -> Mapping   # {root, seed, device, expectations} (support.md §1)
    seam(label)                -> Callable  # a policy of e2e-surface.md §2, carrying `.calls` (support.md §3)
    timings()                  -> Mapping   # the cost the driver collected (driver.md §6)

`KINDS`, `OBJECTS`, `COUNTS`, `ROOT`, `COST` and every `_`-name stay below an entry point and are **not** surface
(`surface.md` §1). The four refusal classes of `errors.md` §2 are the only other names `tests/harness/` may import.

## 4. The layout — one file, and the ceiling measured

`src/harness/` is one file, `__init__.py`, ordered as `layout.md` §1: a file per concern would cost two lines of import
scaffolding, one docstring and a blank each, six times over. The private names are not contract — the unit battery
reaches this module through the six names and the refusal classes only — so a refactor inside the file cannot break it.
Asserted as layout: one file `__init__.py` (`HRN-1.5`); `HRN-4.7` pins `fixtures()`'s empty signature, the rest by call arity.

`strata-lint` prints `harness:110` as an INFO row and measures nothing (brief §5, `module-map.md` §4). The brief's
`50 + 10 × N` budgets *the harness files that drive a module*, and every shipped module's tree exceeds its cap
(140/120/150/160/110 for engine, features, agents, evaluation and training) — declaration arithmetic, never measurement
— against trees one reading (2026-11-05) puts from a few hundred to a couple of thousand lines, several to roughly
twenty times their caps — so the tree, not this page, holds the number (ASM-23). This module reads the cap as those
five do: it governs the support code a battery carries, not a module's declared entry points, which the brief capped
at six. The contract of `surface.md` §2–§7 is about 150 delivered, roughly 40 over its 110 — a hedged reading (ASM-23)
from `src/harness/__init__.py` and `layout.md` §2's dated table; the delta is reported to L2, not paid for by a clause.

## 5. The import boundary (D-13)

`harness` imports the standard library (`tempfile`, `time`, `collections.abc`) and the five packages, and calls
exactly six of the 49 declared entry points — one per factory kind (`surface.md` §4):

    features    build_encoder
    agents      build_learner, build_baseline
    engine      new_hand
    training    rung
    evaluation  build_pool

Six calls and never a seventh: no name below another module's entry point, no sibling's internal module, no `pokerkit`,
`numpy` or `torch`, no added dependency (`battery.md` §2, `strata/platform.md`, D-8). A record a case produces is read
as **plain data** and never through a sibling's reader: a cell's `hands`, an episode's `payoffs` and a refusal
observation are the only shapes this module knows, and each is `records.md`'s required key (`records.md` §5, §9, §14).
The five packages are imported once at module scope, so `factory` is a table over bound entry points and no call is
spelled twice (`support.md` §2).

## 6. Facts inherited from the five modules

- `features.build_encoder(name)` takes the encoding name alone and returns the opaque encoder `encode` accepts
  (`features/surface.md` §4); `agents.build_learner(spec)` takes `records.md` §3's spec and returns a learner complete
  at construction, whose `param_count` is a function of the spec (`agents/surface.md` §4).
- `agents.build_baseline(name, seed)` takes the name and the seed, in that order, and returns a policy of
  `e2e-surface.md` §2 (`agents/surface.md` §12): the only factory kind whose entry point takes two arguments.
- `engine.new_hand(seed)` is the project's single seeding point and refuses a non-integer seed (`engine/surface.md`
  §4, ASM-2, `protocol.md` §4). A `hand` is the only object here that moves the global stream; nothing else does.
- `training.rung(name)` resolves one configuration or refuses a name outside the registry (`training/surface.md` §3);
  `evaluation.build_pool(declaration)` takes `records.md` §8's declaration and refuses a bad one in its own class
  (`evaluation/surface.md` §5). Both refusals propagate unchanged — the harness wraps nothing (`errors.md` §1).
- `engine.play_hand(seed, seat0, seat1)` returns `records.md` §5's episode record, carrying `payoffs` and `decisions`,
  which is how `drive` recognises one hand played (`driver.md` §5). A seam is playable beside any policy because it is a
  policy of §2 and nothing else (`support.md` §3, FAM-14.7).

## 7. The decisions this design fixed, each with the alternative it rejected

| # | Decision | Rejected alternative |
|---|---|---|
| 1 | one file, `__init__.py`, ordered as `layout.md` §1 | a file per concern: its scaffolding costs ≈20 of a 140-line package (§4) |
| 2 | one refusal base and three subclasses, raised by `factory`, `expect` and `seam` (`errors.md` §2) | one class for three contracts; or a class per clause, which is thirteen |
| 3 | `drive` counts a malformed case in `cases` and counts no step (`driver.md` §6) | not counting it, which hides "the driver refused a case" |
| 4 | `synthetic` chooses position `len(calls) % len(legal)`, 0-based, so its first call agrees with `recording` (`support.md` §3) | 1-based: an off-by-one nothing asks for and no reader can see |
| 5 | a step that raised is judged from `{"refused": True, "error": "<Class>: <message>"}` — never re-raised, never retried (`driver.md` §2) | re-raising (errors the caller's runner, FAM-14.10); retrying (calls a step twice) |
| 6 | a case's shape is checked explicitly and reported, not caught by a blanket `except` (`driver.md` §1) | one catch-all, four lines shorter and blind to a bug in `expect` |
| 7 | hands are read in one order: an episode record is one, a cell record declares its `hands` when that is a non-negative integer, every other value is none (`driver.md` §5) | counting steps as hands (false); wrapping `play_hand` (the harness schedules hands); reading a real-valued `hands` fact, which counts `{"hands": -3}` and reports a negative cost |
| 8 | `timings()` returns a fresh copy of the accumulators plus the two derived facts (`driver.md` §6) | returning the accumulator, which a caller's edit would corrupt |
| 9 | the root is `tempfile.mkdtemp(prefix="pypoker-harness-")`, made once and never removed (`support.md` §1) | a fixed path (writes into the shipped tree); `TemporaryDirectory` (deletes a case's artefact) |
| 10 | the four kinds stay four and the cap's delta is reported, not paid for by a clause (§4) | trimming to one kind: still ≈13 over, and `expect` becomes the one-assertion runner L2's H-1 rejected |

## 8. Decisions a later module must not re-derive

1. **`drive` judges through `expect` and adds no second judging rule**; a step that raised is an observation, not a
   case-level failure, and its never-raise is scoped as `surface.md` §2 scopes it (`driver.md` §3, §7).
2. **`factory` is a dispatch table and validates no option**; the owning entry point owns its argument and its refusal,
   and the object returned is its object (`support.md` §2).
3. **A seam returns a member of `legal_actions` and refuses an empty set**; it never folds and never invents a
   descriptor (`support.md` §3, D-2).
4. **A verdict reads the value it was handed, and a refusal is a declared flag, never a word** (`expectations.md` §3).
