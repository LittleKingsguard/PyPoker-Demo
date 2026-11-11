# engine — the cost of a hand, and what is measured

- **Owner:** the per-hand cost question — what dominates it, the one knob that decides it, and which figures this design did and did not measure
- **Ceiling:** 34 lines — raised from 30 for the third shape: the opponent range stated as the two-seat question's and the multi-way form named. At the ceiling, split by owner — never append
- **Split from:** `guardrails.md` G6 and G6.1, moved here whole when that file passed its 120-line limit

## G6 — Cost per hand (ASM-15), and why the equity sample dominates

ASM-15 states the per-hand cost as a measurement in ASM-21’s 0.105–0.153 s band, never a bound. The engine’s own
per-decision cost is a `deepcopy` of the state plus one predicate-and-method call, paid once per decision; how
many decisions a hand holds is the row’s and the policy’s, and the counts are `guardrails.md` G5’s — 8 to 12 in
the default shape, 2 to 8 on the two-seat no-cap row, 24 at six seats under always-check-or-call (`seats.md` §2). The
one call here that can exceed the band on its own is `equity`: asked once per decision by the oracle, its cost is
linear in `sample_count` and in the opponent range — the **two-seat** question’s explicit enumeration, 1225
combinations pre-flop, 1081 on the flop, 1035 on the turn and 990 on the river; on a shape with more seats each
opponent gets one empty selection instead, so that term collapses and the sample count is the whole knob
(`equity.md` §2.1, `seats.md` §2). The sample count is therefore the one knob that decides whether a cell fits
ASM-21’s band, and it is `agents`’ parameter, not this module’s. The engine must not "fix" the cost by caching an
estimate, reducing `samples` or rounding: a cache would make `equity` no longer a function of its arguments.

### G6.1 What is measured, and what is not

Measured: the decision counts above; `pokerkit`’s `calculate_equities` repeating bit-exactly under a fixed seed
inside [0, 1] (`platform.md` §1, §5) — but only within one pinned-`PYTHONHASHSEED` process, because its sampling
universe is a `set` difference (`analysis.py:316`, drawn at `:163`), so processes can differ (`protocol.md` §4) —
and, since D-21, the eleventh fact’s price, which follows the C(known cards, 5) five-card combinations the search
tries: 2.1 µs on the flop (1 combination), 34.5 µs on the turn (6) and 101 µs on the river (21), nothing pre-flop,
no equity sample in it (`readout.md` §2, ASM-30). A 300-hand oracle-free baseline-only cell — 8 readouts a hand,
2 per street — measured 3.50–3.56 ms per hand before that fact and 3.79–3.95 ms after it: **+0.28 to +0.34 ms per
hand, ≈+8 to +10 %** of that cell and **0.18–0.32 %** of ASM-21’s 0.105–0.153 s band, so the band does not move,
and the cell’s win/tie/loss counts are identical before and after it.

**Not** measured here: per-call wall clock beyond those figures. `harness.timings` reports a cell’s clock and a case
reads `seconds_per_hand` without asserting a bound, so no unobserved figure is recorded (ASM-15, ASM-23, FAM-10).
