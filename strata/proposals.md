# PyPoker-Demo — the L0 intake gate

Procedure for D-10: speculative proposals and major feature expansions. Ceiling: 40 lines.

## 1. Trigger

The gate runs when a proposal is **speculative** — no implementation committed yet — or a **major
expansion**: one that would add a module or change an existing decision row (D-10).

Ordinary work inside an accepted unit does not run it; that is the loop's job (D-1). A new project
intake is the largest case of the gate: the whole project is the proposal (D-10).

## 2. Two reviews, in parallel and independently

- `role_l0_validity` — can it be built as stated, does it solve the stated problem and only that,
  and what does it need that does not exist yet.
- `role_l0_critique` — externalities, cost and scale, paradigm violations, and the over-fit
  hazard: anything that would turn one example into a rule.

Neither reviewer sees the other's findings. A review that has read its partner's report is no
longer an independent check (D-10).

## 3. Findings, not verdicts

The reviews keep the closed verdict set of `strata/envelope.md`: `PASS` means no blocking finding
and carries its citations; `FAIL` means findings with a root cause; `ADJUDICATION` means the answer
needs user intent (D-11).

L0 dispositions the findings into a decision row — proceed, proceed with conditions recorded,
change the proposal, or ask the user. The disposition is a `D-n`, never a verdict document: a
verdict that grows its own record is the accretion this workflow exists to stop (D-10).

## 4. Output

Findings are archived at `strata/records/<topic>-findings.md`, at most 40 lines, replaced on every
pass. The decision row is the durable record (D-10).
