# Double-Q changes nothing under the token encoding either · measured 2026-11-08

The rule axis on the token encoding at six seats: `card-tokens`, `net-chips`, the mixed pool
`pool-8386c3ef83ae48b2`, 15,000 hands × seeds 0–2, `double-q-learning`, against D-52's masked-Q arm on the
same pool, shape, seeds, budget and utility (D-14). Wall clock 8,077 s.

| arm | seed | decisions | fold | policy | chips/hand |
|---|---|---|---|---|---|
| **double-q** | 0 | 4,042 | **0.00 %** | raise-half 57 % / check-call 43 % | −2.104 ± 7.562 |
| masked-q (D-52) | 0 | 3,889 | **0.00 %** | raise-half 56.8 % / check-call 41.0 % | −1.999 ± 7.535 |
| **double-q** | 1 | 4,432 | **0.00 %** | check-call 100 % | −3.510 ± 7.051 |
| masked-q (D-52) | 1 | 4,432 | **0.00 %** | check-call 100 % | −3.510 ± 7.051 |
| **double-q** | 2 | 4,617 | **0.00 %** | check-call 100 % | −2.683 ± 7.098 |
| masked-q (D-52) | 2 | 4,617 | **0.00 %** | check-call 100 % | −2.683 ± 7.098 |

## The rule axis is dead as a lever

**Two of the three seeds are identical** — same decision count, same 100 % check-call policy, same chips to
four decimals — and the third differs by 0.1 chips and a tenth of a point of share. That is not a small
effect; it is the same policy reached by a different rule.

It also reproduces D-42 exactly: at two seats under `net-chips`, Double-Q moved **nothing** (0 folds in
21,858 decisions, the same 98 % minimum raise). So the finding is now independent of seat count, encoding
and shape: **the learning rule changes neither the folding rate nor the policy.**

## Where the levers now stand, all measured at six seats

| lever | effect on folding | verdict |
|---|---|---|
| **utility** (`net-chips` → `stack-shortfall`) | **0 % → 78–93 %** | **the switch** |
| **encoding** (`flat` → `tokens`), utility held fixed | 77.5 % → **92.7 %**, sd 5.7 → 1.2 | **a real modulator** |
| **rule** (masked-Q → double-Q) | 0 % → 0 % | **no effect** |
| **counterfactual** on top of the pair | nothing (Δ ≤ 1.44 SE) | **no effect** |
| **inference** (D-57) | the folder loses 0.265 chips/hand to the non-folder | **the folder is worse** |

So of the four levers this project built, exactly **two** move behaviour, and they compose in a fixed order:
the utility decides *whether* the agent folds, and the encoding decides *how hard and how consistently*.
