# PyPoker-Demo — the rebuild protocol

Procedure for D-12. Ceiling: 40 lines.

## 1. Eligibility

**Repeat failure**: the same artifact id fails the same test class on **3 consecutive repair
passes**. The count lives in `strata-state` as `failStreak`, never counted by eye — an undefined
"repeat" is the prose trigger that rots first (D-12). A rebuild below threshold is a rejected
recommendation; the streak alone is also not enough, the examiner must still judge the code not
worth salvaging. An adjudication request from a lower layer counts as one failure (D-12) — asking
is not a pause and is not free.

## 2. What the examiner may emit

`strata/examiner.md` §4 — one statement of the rule, not two. `strata-lint` enforces it (D-11).

## 3. Who decides

One layer above the examiner (D-12). Recommending a rebuild asserts that the examiner's own layer
designed wrongly — three passes on one design indicts the design, not the code — and a layer
cannot adjudicate its own design (D-11).

## 4. Retrospective, before teardown

The owning layer's designer writes ≤ 20 lines answering exactly three questions: what did we
believe that was false; which test should have caught it and why it did not; what changes next
cycle (D-12). It is archived beside the torn-down artifact — never appended to a live document,
and it never re-opens an earlier cycle's reasoning.

## 5. Then

Teardown, then a fresh cycle from the layer that owns the artifact. The unit keeps its id and the
retrospective is the only carry-over — no salvage mixing; the new cycle starts from the artifact
spec, never from the abandoned code (D-12).

A second rebuild of the same artifact escalates again rather than repeating: two rebuilds are
evidence about the upstream design, not about the implementer (D-12).
