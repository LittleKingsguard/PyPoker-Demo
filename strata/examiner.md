# PyPoker-Demo — the examiner

Procedure for D-11 and D-12. Ceiling: 45 lines.

## 1. Order of operations

Validate the battery, then examine the code. Never reversed — a code finding against an invalid
test sends the implementer to fix code that was never wrong (D-11).

## 2. Is the test real?

It drives the declared surface; it does not mock or re-implement the subject. It asserts an
observable outcome, not an internal call. It is not skipped, not conditionally disabled, and not a
restatement of the implementation. A failure here is a finding against the **test writer of that
layer**, never the implementer (D-11).

## 3. Is it theoretically completable?

Some implementation satisfies the assertion without violating another test in the same battery.
"Completable" does not mean "passing today" — a red test is expected before implementation exists.
Two mutually contradictory tests, or an assertion no implementation can satisfy, is a test finding
and not a code finding (D-11).

This is also where an over-fit battery surfaces: if only the design's own example instance can
satisfy the assertion, the surface was never general and the test is the evidence (D-15).

## 4. What an examiner may emit

May: root cause, owning artifact id, failing test id, routing layer, rebuild recommendation.
May not: a snippet, a diff hunk, a signature, or an ordered fix list (D-11).
Reads code and artifacts; reads the designer's rationale only where a rule needs it, so the
examination stays as blind as the design allows.

`strata-lint` fails any report carrying a fenced code block or a `@@` / `+` / `-` diff hunk.

## 5. Where a failure goes

- **Code wrong, design sound** → the owning designer at the same layer.
- **Test invalid** → the test writer at the same layer.
- **L4 cannot drive green** → **L2** (D-12). L4 owns no design, and L3 authored the design under
  judgement, so neither can adjudicate it; L2 revises the interface or behaviour brief and
  re-issues downward.
- **Lower layer requests adjudication** → answered above, counted as a failure (D-12).
- **Repeat failure at threshold** → rebuild recommendation (`strata/rebuild.md`).
