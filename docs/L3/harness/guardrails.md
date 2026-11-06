# harness — L4 guardrails

- **Layer:** L3 · **Module:** `harness` · **Unit:** phase1 · **Rev:** 4 · **Date:** 2026-11-05 · G9 scoped (surface.md Rev 2)
- **Owner:** one numbered note per risk this design identified, in the order they bite, each naming its rule and the
  test that catches it
- **Ceiling:** 175 lines. At the ceiling, split by owner — never append
- **Read with:** all of `README.md`, `layout.md`, `driver.md`, `support.md`, `expectations.md`, `errors.md`

The unit battery's files are contract: `tests/harness/test_harness_surface.py` (`HRN-1.k`), `test_harness_drive.py`
(`HRN-2.k`), `test_harness_expectations.py` (`HRN-3.k`), `test_harness_fixtures.py` (`HRN-4.k`),
`test_harness_factory.py` (`HRN-5.k`), `test_harness_seam.py` (`HRN-6.k`), `test_harness_timings.py` (`HRN-7.k`),
`test_harness_errors.py` (`HRN-8.k`). It drives the **real** five modules — this module's whole job is calling them, so
a stub here would test the stub — and a missing entry point must fail loudly rather than pass through a substitute.

## G1 — One file, six names in `__all__`, and no seventh name at module level
`src/harness/__init__.py` exports the six names of `README.md` §5 in that order; `KINDS`, `OBJECTS`, `COUNTS`, `ROOT`,
`COST`, the four classes, the names the import statements bind (`tempfile`, `time`, `Mapping` and the five packages)
and every `_`-name are the only other module-level names (`layout.md` §1, D-12).
Caught by: `test_harness_surface.py::HRN-1.1`, FAM-1.44–FAM-1.49.

## G2 — Exactly six calls, one per factory kind, and never a seventh
The module's source imports the five packages and spells no other project name; it never reaches a sibling's internal
module, `pokerkit`, `numpy` or `torch`, and it adds no dependency (`README.md` §5, `battery.md` §2, D-13).
Caught by: `test_harness_surface.py::HRN-1.2` (the source's import lines), `HRN-1.3` (a seventh call would need a
seventh name, and `OBJECTS` holds six).

## G3 — The factory returns the owner's own object, not a wrapper
An `encoder` built here is one `features.encode` accepts; a `learner`'s `agents.param_count` equals the count of
`agents.build_learner(spec)`; a `baseline` is playable by `engine.play_hand`; a `hand` is a handle `engine.readout`
reads; a `rung` is a configuration a `run` could take; a `pool` is one `evaluation.pool_members` reads back
(`support.md` §2, FAM-14.2, FAM-14.3, FAM-1.46).
Caught by: `test_harness_factory.py::HRN-5.1`–`HRN-5.6`, FAM-14.2, FAM-14.3, FAM-16.34, FAM-1.46.

## G4 — `baseline` spreads its two options in the owner's order
`agents.build_baseline(name, seed)` takes the name first, so `factory("baseline", ("oracle", 7))` calls
`build_baseline("oracle", 7)`. Reversing them, or passing the pair whole, hands `build_baseline` a tuple as its name and
the refusal names the wrong argument (`support.md` §2).
Caught by: `test_harness_factory.py::HRN-5.2` (the oracle's decisions equal a directly built one's), FAM-14.7.

## G5 — An undeclared kind is refused by name, and an unhashable one too
`factory("deck-of-cards", …)` raises `UnknownFactoryKind` naming the kind and the six declared in sorted order. The
check must be `not isinstance(kind, str) or kind not in OBJECTS`: `kind not in OBJECTS` alone raises `TypeError` for an
unhashable kind, which is not this module's refusal (`support.md` §2, `errors.md` §4, FAM-14.4).
Caught by: `test_harness_errors.py::HRN-8.1`, `HRN-8.2`, FAM-14.4.

## G6 — A delegated refusal keeps its owner's class
`factory("encoder", "no-such-encoding")` raises `features`' own error, not a `HarnessError`; likewise `agents`' for an
unknown baseline name or backend and `evaluation`'s for a bad declaration. Re-wrapping hides which module owns the
catalogue (`errors.md` §1, `support.md` §2).
Caught by: `test_harness_factory.py::HRN-5.7`, `HRN-5.8`.

## G7 — The fixture is one root per process, created and writable
`fixtures()` returns an absolute `root` that exists and accepts a written file, returns the **same** root on every later
call, and returns `seed == 0`, `device == "cpu"`, `expectations == list(KINDS)` in `KINDS` order. A root under the
repository, a fresh root per call, or a root deleted at a case's end all break it (`support.md` §1, FAM-14.1, FAM-16.33).
Caught by: `test_harness_fixtures.py::HRN-4.1`–`HRN-4.4`, FAM-14.1, FAM-16.33, FAM-1.45.

## G8 — `fixtures()` reads no other module
No `training.devices()` call and no `evaluation.protocol()` call: a pinned precondition that depended on another
module's implementation would make a red case unattributable (`support.md` §1, `surface.md` §3, D-13).
Caught by: `test_harness_fixtures.py::HRN-4.5` (the device string is the literal, so a probe that changed its mind
cannot move it), FAM-14.1's `cpu`.

## G9 — Every kind is total over §1's plain data, and totality is enforced in exactly one place
Each of the four kinds yields `{kind, verdict, reason}` for `None`, `0`, `""`, `[]`, `{}`, `True`, an opaque object, a
1000-digit integer, a nested record, a `10**999`-with-float pair in all four `zero-sum` shapes, a `counted` cell mixing
them, and a descriptor whose equality raises or returns no boolean; a value a kind cannot read is a `fail`, never a pass
and never a silence (`expectations.md` §3, FAM-14.8). **One guard**, in `expect`: one `try`/`except Exception` around its
one call into `_CHECKS`, fact `the value could not be read: <Class>: <message>`, so a reader bug stays visible; `drive`
inherits it. Rejected: a `try` per reader, or more odd battery values. Totality itself is `surface.md` §6's, scoped to
§1's plain data: `HRN-3.19` and `HRN-3.20` hand the kinds an object whose `==` raises, and are deliberately **stricter**
than the rule — they hold the guard without widening it. Caught by: `test_harness_expectations.py::HRN-3.1`, `HRN-3.2`,
`HRN-3.17`–`HRN-3.21`, FAM-14.8.

## G10 — `zero-sum` reads its four shapes in order, and tolerates a float sum
An episode record's `payoffs`, a cell record's two `mean_chip_delta`s, a mapping of two per-seat numbers and a sequence
of two numbers each pass when they balance; a bare number and a record with three or more numbers fail. The tolerance is
`abs(sum) <= 1e-9` — an exact `== 0` fails a real cell whose means are `0.5217391304347826` and its negative
(`expectations.md` §2.1, FAM-7).
A non-finite pair is a **fail**: `(NaN, NaN)` and `(+inf, -inf)` do not balance, and no comparison with their sum is true,
so the pass predicate `abs(sum(deltas)) <= 1e-9` is evaluated and never negated — testing `abs(sum) > 1e-9` passes both
(`expectations.md` §2.1).
The cell-shaped branch keeps **quantities only**: a string, `None` or boolean `mean_chip_delta` is dropped before the pair
is counted, so a cell-shaped value whose means are not quantities reaches *no two per-seat chip deltas* — never a raise out
of `sum`, and never a `True`/`-1` pair summed as `1 + -1` and passing (`expectations.md` §2.5).
Caught by: `test_harness_expectations.py::HRN-3.3`–`HRN-3.6`, `HRN-3.13`, `HRN-3.15`, `HRN-3.16`, FAM-14.8, FAM-16.36.

## G11 — A refusal is a declared flag, never a word
`expect("refused", {"refused": True})` passes; `{"error": "refused"}`, `{"text": "the work refused"}`, a raised
exception and a returned record that merely *says* refused all fail (`expectations.md` §2.4, D-13, L2's H-1). The flag
must be the boolean `True` and not a truthy value: `{"refused": "yes"}` and `{"refused": 1}` fail too.
Caught by: `test_harness_expectations.py::HRN-3.7`, `HRN-3.8`, `HRN-3.14`.

## G12 — An unlisted kind fails; a non-string kind raises
`expect("no-such-kind", v)` returns `fail` with the kind verbatim in `reason`; `expect(3, v)` raises
`UnknownExpectationKind`. Both halves are contract and the asymmetry is deliberate (`expectations.md` §4, FAM-14.8,
FAM-16.36, FAM-14.10).
Caught by: `test_harness_errors.py::HRN-8.3`, `HRN-8.4`, FAM-14.8, FAM-16.36.

## G13 — Each step is called exactly once, in order, and the pass does not stop
A case of three steps that append their index to a list shows `[0, 1, 2]` after one `drive`; a step that raises does not
prevent the third from running; nothing is retried or reordered (`driver.md` §2, FAM-14.9, FAM-16.32).
Caught by: `test_harness_drive.py::HRN-2.1`, `HRN-2.2`, FAM-14.9, FAM-16.32.

## G14 — A raised step is an observation, not a case failure
A case whose step raises and whose `expect` is `["refused"]` **passes**; the same case with `["zero-sum"]` fails. The
driver must not raise and must not turn a refusal into a `fail` of its own (`driver.md` §2, §3,
`expectations.md` §2.4, FAM-14.10).
Caught by: `test_harness_drive.py::HRN-2.3`, `HRN-2.4`.

## G15 — `drive` never raises, for any of the five malformed shapes
Not a mapping; no `id`; an empty `id`; no `steps`; an empty `steps`; no `expect`; an empty `expect`; a step that is not
callable — each returns §4's seven-key record as `fail` with `driver.md` §1's own sentence (`driver.md` §1, FAM-14.10).
Caught by: `test_harness_drive.py::HRN-2.5`–`HRN-2.7`.

## G16 — The three expectation-entry failures are named, and nothing is judged silently
An out-of-range `step` index, a non-integer index, an entry that is neither string nor mapping, and a step no entry
judges each make the case `fail` with a sentence naming it; every entry that *did* judge is recorded (`driver.md` §3).
Caught by: `test_harness_drive.py::HRN-2.8`–`HRN-2.10`.

## G17 — The result's seven keys, in the declared order, with `verdict` readable
`id`, `steps`, `expectations`, `hands`, `wall_clock_seconds`, `verdict`, `reason`; the id verbatim; `reason is None` on a
pass and one sentence on a failure; no key before `verdict` containing `pass`, `ok`, `success`, `result`, `verdict` or
`status`, or a tolerant reader answers with the wrong key (`driver.md` §4, FAM-14.9, FAM-16.32).
Caught by: `test_harness_drive.py::HRN-2.11`, `HRN-2.12`, FAM-14.9.

## G18 — Hands come from the outcomes and nowhere else
An episode record counts 1; a mapping declaring **both** `hands` and `directions` counts its `hands` when that is a
non-negative `int` — an integral float such as `2.0` is not a count — and 0 when it is fractional, negative, boolean or
not a number; every other value counts 0 — a bare number, a refusal observation, and a mapping with `hands` and no
`directions` among them. A step that composes an episode is counted like one that returned `play_hand`'s. So the count is
an integer ≥ 0 and no per-hand cost is negative. Counting steps, reading the *number* a `hands` fact carries, or wrapping
`play_hand`, breaks the FAM-10/FAM-13 cost evidence (`driver.md` §5, FAM-10.4, FAM-13.6).
Caught by: `test_harness_drive.py::HRN-2.13`, `HRN-2.14`, `HRN-2.18`, `test_harness_timings.py::HRN-7.8`.

## G19 — `timings()` is monotone, consistent and a fresh copy
Measured as deltas between two calls: a driven episode case adds exactly its hands and its steps to a case count that
grew by one; `seconds_per_hand × hands` equals the clock and `hands_per_second × clock` equals the hands; a case that
counted no hand adds nothing to `hands`; and mutating the record a call returned does not change the next call's numbers
(`driver.md` §6, FAM-14.11, FAM-16.37).
Caught by: `test_harness_timings.py::HRN-7.1`–`HRN-7.4`, FAM-10.4, FAM-13.6, FAM-14.11, FAM-16.37.

## G20 — The four cost keys are spelled by what they name
`hands`, `wall_clock_seconds`, `seconds_per_hand`, `hands_per_second`: renamed to `rate`, `perf` or `t`, the D-7 and
ASM-15 readers lose the number, because they classify a key by the words in it (`driver.md` §6, `records.md` §12).
Caught by: `test_harness_timings.py::HRN-7.5`, FAM-10.4, FAM-13.6.

## G21 — The seam returns a member of the list it was handed, by identity
`engine.apply_action` accepts what the seam returned, so the seam returns `legal[position]` itself and not a copy, a
name or a rebuilt descriptor; `features.legal_indices` then gives it an index in `{0, 1, 2}`
(`support.md` §3, `e2e-surface.md` §2, FAM-14.5, FAM-14.7, FAM-16.35).
Caught by: `test_harness_seam.py::HRN-6.1`, `HRN-6.2`, FAM-14.5, FAM-14.7, FAM-16.35.

## G22 — Both behaviours record, and `synthetic` starts at the first descriptor
`recording` — and `echo-legal`, and `""` — take `legal[0]` every call; `synthetic` takes `legal[0]`, `legal[1]`, … and
wraps, so its schedule differs from `recording` from the second call on. Both append one entry per call holding
`readout`, `legal` and `chosen` (`support.md` §3, L2's H-2, H-3).
Caught by: `test_harness_seam.py::HRN-6.3`, `HRN-6.4`.

## G23 — Two seams of one label agree; two `seam()` calls are two instances
Two closures from `seam("synthetic")` driven over the same pairs answer the same descriptors and hold equal logs, while
the second's log does not contain the first's calls — a cached instance would fail both halves
(`support.md` §3, FAM-14.5, FAM-14.6, FAM-16.35).
Caught by: `test_harness_seam.py::HRN-6.5`, `HRN-6.6`.

## G24 — An empty legal set is refused, never folded and never invented
`seam(label)(readout, [])` raises `NoLegalAction` naming the label and the contract; it does not return `None`, does not
invent a `"fold"` and does not log the call (`support.md` §3, D-2, `errors.md` §4).
Caught by: `test_harness_seam.py::HRN-6.7`, `test_harness_errors.py::HRN-8.5`, `HRN-8.8`.

## G25 — Nothing here seeds or advances the global `random` stream
`random.seed(0)`; a `drive` of a case over pure values (no engine call) and a `fixtures()`, `expect`, `seam`, `timings`
call must leave `random.random()` at the value it would have had. `factory("hand", n)` is the one legitimate exception:
it delegates the deal to `engine.new_hand` (ASM-2, `protocol.md` §4, `support.md` §2).
Caught by: `test_harness_surface.py::HRN-1.4`, `test_harness_seam.py::HRN-6.8`.
