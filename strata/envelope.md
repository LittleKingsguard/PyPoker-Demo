# PyPoker-Demo — the layer return envelope

Every layer return ends with one fenced `json` block and nothing after it (D-11). Ceiling: 40 lines.

## 1. Fields

Required are `unit`, `from`, `to`, `verdict` and `artifact`; optional are `testIds`,
`rootCause`, `assumptions`, `question` and `citations` (D-11).

`from` and `to` are layer ids. A return travels exactly one layer up, so `to` is one below
`from` — except from `L4` on any non-`PASS` verdict, which routes to `L2`, because L4 owns no
design and L3 designed the thing under judgement (D-12).

## 2. Verdicts

The set is closed, and each verdict maps to exactly one state transition, so a return cannot be
ambiguous about what happens next (D-11):

| Verdict | Meaning | Transition |
|---|---|---|
| `PASS` | the layer's battery is green | `strata-state pass` |
| `FAIL` | root cause established, not a rebuild | `strata-state fail` |
| `ADJUDICATION` | cannot proceed without a decision (D-12) | counted as a failure |
| `REBUILD` | the artifact is not worth salvaging (D-12) | `strata-state rebuild` |

## 3. Conditions

- A non-`PASS` verdict carries `rootCause`: an examiner diagnoses and never patches (D-11).
- A `PASS` verdict carries `citations`, because a green claim names the document that supports
  it (D-11).
- No return carries code to insert — a non-`json` fenced block or a `@@` hunk fails the envelope
  check (D-11).
- Each `assumptions` entry carries `{id, text, alternative}`; the rejected alternative is
  mandatory, never omitted (D-1).
- A `question` that needs user intent is the only thing that climbs past this layer, and only L0
  puts it to the user (D-1).
