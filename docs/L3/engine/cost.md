# engine — the cost of a hand, and what is measured

- **Owner:** the per-hand cost question — what dominates it, the one knob that decides it, and which figures this design did and did not measure
- **Ceiling:** 30 lines. At the ceiling, split by owner — never append
- **Split from:** `guardrails.md` G6 and G6.1, moved here whole when that file passed its 120-line limit

## G6 — Cost per hand (ASM-15), and why the equity sample dominates

ASM-15 states the per-hand cost as a measurement in ASM-21’s 0.105–0.153 s band, never a bound. The
engine’s own per-decision cost is a `deepcopy` of the state plus one predicate-and-method call, paid
8 to 12 times a hand. The one call in this module that can exceed the whole band on its own is
`equity`: it is asked once per decision by the oracle, and its cost is linear in `sample_count` and
in the size of the opponent range (1225 combinations pre-flop, 1081 on the flop, 1035 on the turn,
990 on the river). So the sample count is the one knob that decides whether a cell fits ASM-21’s band
— and it is `agents`’ parameter, not this module’s. The engine must not "fix" the cost by caching an
estimate, by reducing `samples` itself or by rounding the number: a cache would make `equity`
no longer a function of its arguments, and the other two would report a question nobody asked.

### G6.1 What is measured, and what is not

Measured: the decision counts above, and `pokerkit`’s `calculate_equities` repeating bit-exactly under a
fixed seed inside [0, 1] (`platform.md` §1, §5) — but only within one pinned-`PYTHONHASHSEED` process,
because its sampling universe is a `set` difference (`analysis.py:316`, drawn at `:163`), so processes
can differ (`protocol.md` §4). **Not** measured here: per-call wall clock. ASM-15 states the per-hand cost
as a measurement in ASM-21’s band, not a bound, and `harness.timings` is the module that reports it
(`e2e-surface.md` §3.6, FAM-10); a case reads `seconds_per_hand` and never asserts a bound, and this
design records no millisecond figure it did not observe (`battery.md` §2).
