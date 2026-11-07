# harness — the driver and the cost record

- **Layer:** L3 · **Module:** `harness` · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-05 · §1, §7 scoped (surface.md Rev 2)
- **Owner:** `drive()` — the case's shape and its refused-as-failure shapes (§1), the step pass (§2), judging (§3), the
  case-result record key by key (§4), the hands it counts (§5) — and `timings()`, the record of what the driver
  collected (§6), with the determinism both are contracted for (§7)
- **Ceiling:** 170 lines. At the ceiling, split by owner — never append
- **Read with:** `expectations.md` §1–§4, `errors.md` §3–§4, `layout.md` §1, `docs/L2/harness/surface.md` §2, §7

## 1. The case, and the five shapes that are a failure rather than a raise

A case is a mapping with three required keys (`records.md` §14, `surface.md` §2): `id` — a non-empty string; `steps` —
a non-empty sequence of zero-argument callables; `expect` — a non-empty sequence of expectation entries. `drive` **never
raises** for a case of `surface.md` §2's shapes, so each of these five is a `fail` with a sentence in `reason`:

| The shape | The sentence |
|---|---|
| not a mapping | `harness.drive refused the case: it is not a mapping` |
| no non-empty string `id` | `harness.drive refused the case: it carries no non-empty 'id'` |
| no non-empty `steps` sequence | `harness.drive refused the case: it carries no non-empty 'steps'` |
| no non-empty `expect` sequence | `harness.drive refused the case: it carries no non-empty 'expect'` |
| a step that is not callable | `harness.drive refused the case: a step is not a zero-argument callable` |

The checks are **explicit**, in that order, and the first one that fails is the sentence. A blanket `try` around the
body is rejected (`README.md` §7): it would report a defect inside `expect` as "the case failed", which is the one
failure a test-support module must never hide from the battery it serves.

A malformed case still returns the whole record of §4 with `verdict: "fail"`, and it still counts once in `cases` (§6);
it ran no step, so `steps` grows by zero and `hands` stays `0`.

## 2. The step pass

`steps` are called in declared order, and each is called **exactly once**: never twice, never retried, never reordered,
never evaluated speculatively, never skipped. The pass does **not stop** at a step that raised — a case's later steps
may be independent, and each step's outcome is judged separately (`surface.md` §2, FAM-14.9, FAM-16.32).

For each step, in order:

1. `began = time.perf_counter()` — the module's only clock, monotonic and wall-clock-free (`time.monotonic` is the
   rejected alternative: `perf_counter` has the better resolution and neither is a date);
2. call the step inside `try`, with `except Exception` — a step is a case's call on a declared entry point, and a
   refusal of one arrives as an exception from that module (`e2e-surface.md` §2);
3. a returned value is stored **verbatim** as `outcome` with `refused: False`; a raised value stores
   `outcome = {"refused": True, "error": "<ClassName>: <the message>"}` with `refused: True` — the refusal observation
   `expect`'s `refused` kind reads (`expectations.md` §2.4, FAM-14.8, FAM-14.10);
4. `seconds = time.perf_counter() - began` — one measurement per step, never a share of the case's;
5. append `{"index", "outcome", "refused", "seconds"}` to the record's `steps`, in that key order, and add `_hands`
   of the outcome to `hands` (§5).

No step's outcome is copied, normalised, re-encoded or compared to another. A step that raised is **not** a case-level
failure: it is an observation, and the entry covering it decides whether the case passes (`support.md` §3, §3 below).

## 3. Judging

Judging happens after the pass, in the declared order of `expect`, one entry at a time, through `expect` itself — the
driver adds no second judging rule, so one kind and one observed value give one verdict here and when a battery calls
`expect` directly (`surface.md` §2, §6, FAM-14.8):

| The entry | The step it judges |
|---|---|
| a kind name — a string | the **last** step |
| a mapping `{"kind", "step"}` | the step at that index |
| anything else — including a mapping whose `kind` is not a string | a named failure: `harness.drive refused the expectation <entry>: an entry is a kind name or a {"kind","step"} mapping` |

An entry whose `kind` is not a string is *not* routed to `expect`, because `expect` raises for a non-name
(`expectations.md` §4) and `drive` never raises (`surface.md` §2): the entry is reported as the unreadable entry it is,
and the case fails for that reason rather than for a refusal the harness itself made.

The observation handed to `expect` is the step's `outcome` — the returned value, or the refusal observation of §2.
Then, in this order:

- an index that is not an integer, or outside `0 … len(steps) - 1`, is a named failure — `harness.drive refused the
  expectation '<kind>': it names no step of this case` — and the entry is **not** recorded as judging a step;
- the `expect` record is appended to `expectations` with the step index folded in, under the keys `kind`, `step`,
  `verdict`, `reason`, in that order (`surface.md` §2);
- the **first** failure in declared order becomes the record's `reason`, as `harness.drive failed step <index>: <expect's
  reason>`; every later entry is still judged and still recorded, because a case that fails twice should say so twice;
- a step judged twice must pass both judgements — a verdict over a step nobody judged is not a verdict about the case
  as run (`surface.md` §2);
- after the pass, a step no entry judged is a named failure — `harness.drive ran step <index>, and no expectation judges
  it`. A malformed case of §1 records none of these, because it judged nothing.

`verdict` is `pass` **iff** the record's `reason` is `None`; `reason` is `None` on a pass and one sentence otherwise.
A pass never argues for a failure (`surface.md` §2, FAM-14.9).

## 4. The case-result record

Seven keys, in this order — the order matters: a reader that scans a mapping key by key must meet `verdict` before it
meets anything a tolerant pass/fail scan could misread, and none of the six keys before it contains `pass`, `ok`,
`success`, `result`, `verdict` or `status` (`tests/e2e/_surface.py`'s `verdict` reader, `surface.md` §2):

| Key | Content |
|---|---|
| `id` | the case's own id, verbatim, or `None` for a case that is not a mapping (`records.md` §14, FAM-14.9) |
| `steps` | one entry per step called, in order: `index`, `outcome`, `refused`, `seconds` (§2) |
| `expectations` | one entry per entry judged, in order: `kind`, `step`, `verdict`, `reason` (§3) |
| `hands` | the hands the outcomes declared (§5) |
| `wall_clock_seconds` | `time.perf_counter()` measured around the whole case, steps and judging included |
| `verdict` | `pass` or `fail` (§3) |
| `reason` | `None` on a pass; one sentence on a failure (§1, §3) |

The record is plain data: no learner, encoder, policy, pool, hand or generator appears anywhere inside it (D-1,
`surface.md` §1).

## 5. The hands a case declared

`hands` is read off the outcomes, never counted from the driver's own work and never from its step count:

1. an outcome that is a mapping carrying **both** `payoffs` and `decisions` is an episode record and is **one** hand —
   `engine.play_hand` plays one hand (`records.md` §5, H-5);
2. otherwise an outcome that is a mapping carrying **both** `hands` and `directions` is a cell record and contributes its
   `hands` **when that is a non-negative integer** — a cell declares the hands it played (`records.md` §9) — and it
   contributes **nothing** when that `hands` is not an `int` — fractional, negative, boolean, `2.0` or not a number;
3. otherwise it contributes nothing: a refusal observation, a bare number, a mapping with `hands` and no `directions`, a
   policy and a cell's `params` are not hands.

So `hands` stays an **integer ≥ 0**, because the rule reads a count and not the number a value states: `{"hands": -3}`,
`{"hands": 2.5}`, `{"hands": "7"}` and `{"hands": 5}` with no `directions` each add nothing, so `timings()` reports no
negative `seconds_per_hand` (`surface.md` §2, §7). The check is on the value, so a composed episode counts like
`play_hand`'s and a wrapper that counted hands itself is rejected (`surface.md` §2, `module-map.md` §3, `README.md` §7).
**Rejected:** "an outcome whose `hands` is a real number contributes that number" — it counts a negative `hands` as hands.

## 6. `timings()` — the cost the driver collected

`COST` is one module-level mapping initialised `{"hands": 0, "wall_clock_seconds": 0.0, "cases": 0, "steps": 0}`.
`drive` adds to it once per call, whatever the verdict: `hands` by the record's hands, `wall_clock_seconds` by the
record's clock, `cases` by one, `steps` by the number of steps it called. Nothing else ever writes to it.

`timings()` returns a **fresh copy** of those four keys with the two derived facts appended, in this order (`surface.md`
§7):

| Key | Content |
|---|---|
| `hands` | the hands the driven cases' outcomes declared, an integer ≥ 0 |
| `wall_clock_seconds` | the summed clock of the cases the driver drove |
| `cases`, `steps` | the driver's own counts of what it ran |
| `seconds_per_hand` | `wall_clock_seconds / hands`, and `0.0` when no hand was counted |
| `hands_per_second` | `hands / wall_clock_seconds`, and `0.0` when no time was measured |

Three rules:

- **the accumulators never decrease.** `hands`, `cases`, `steps` and the summed clock are monotone over the process, so
  a second call cannot report less than the first (`surface.md` §7). A per-call record, a window or a reset is rejected:
  the surface asks for the cost of everything the driver collected;
- **the key names are the facts.** `hands`, `wall_clock_seconds`, `seconds_per_hand` and `hands_per_second` are read by
  what they name, not by a literal spelling this module invents (`records.md` §12, `tests/e2e/_records.py`'s
  `timing_facts`): `seconds_per_hand` must stay a per-hand *duration* and `hands_per_second` a throughput, and neither
  may be renamed to `rate`, `perf` or `t`, or the D-7 and ASM-15 evidence readers lose the number (FAM-10.4, FAM-13.6);
- **nothing here asserts a bound.** The record says what the work cost; it never claims a wall clock was beaten and
  never compares two records. ASM-15's per-hand cost is a measurement in ASM-21's band, never a bound;
  it sizes the table and is not a test (`surface.md` §7, `battery.md` §2, FAM-10).

Zero is a real answer: before any case has been driven the record is
`{"hands": 0, "wall_clock_seconds": 0.0, "cases": 0, "steps": 0, "seconds_per_hand": 0.0, "hands_per_second": 0.0}`, so
a caller can tell "measured nothing yet" from "measured something cheap" (`surface.md` §7, FAM-1.49).

## 7. Determinism, and the one edge that reports instead of raising

One case, the same steps, seeds and pool membership, gives one result twice — the same step outcomes, the same
expectation verdicts and the same `verdict`; only the measured `seconds` differ (`protocol.md` §4, ASM-2, `battery.md`
§3). One `drive` call is one run of the case, so a second call runs its steps a second time and is not a replay
(`surface.md` §2).

`drive` has no refusal of its own: `surface.md` §2 contracts none, and §1's rule lets an entry point report where L1
contracts a verdict. `expect` reports too, for a kind it does not list (§4 of `expectations.md`); `factory`, `expect`'s
non-string kind and `seam`'s empty legal set raise (`errors.md` §2). Nothing else here raises for a case of the shapes
`surface.md` §2 enumerates, judged on an outcome that is `surface.md` §1's plain data. The one boundary: the counter
behind `hands` (§5) reads a mapping's own keys unguarded, so an object whose own mapping protocol raises is no observed
value, and `drive` raises there where `expect`, over that same object, still returns a named failure (§2, §6, Rev 2).
