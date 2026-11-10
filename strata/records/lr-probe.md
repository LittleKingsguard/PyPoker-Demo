# More aggressive learning: two attractors, and a crash · measured 2026-11-07

Learning rate varied in-process (`learn` reads `declarations.HYPER` at call time; the declaration
itself is unchanged and the run still refuses a `hyper` override). Config = the folders pool, budget
1,000 hands, seeds 0/1/2 per rate (D-14).

| lr | seed 0 | seed 1 | seed 2 |
|---|---|---|---|
| 0.003 | raise 88 / call 10 (TD 1.90→2.93) | raise 69 / call 29 (1.87→1.90) | raise 57 / call 42 (1.79→1.78) |
| 0.01 | raise 88 / call 10 (2.05→2.13) | **raise 2 / call 96 (1.96→0.77)** | raise 89 / call 10 (1.80→3.08) |
| 0.03 | **raise 2 / call 97 (2.03→1.12)** | **DIVERGED** | raise 89 / call 10 (1.83→3.11) |
| 0.1 | raise 88 / call 10 (2.17→2.76) | **DIVERGED** | **DIVERGED** |

## Two attractors exist, and the rate does not select between them

Every run lands in one of two modes: **raise** (raise ~88 %, mean |TD| rising to ~3) or **call**
(raise ~2 %, check-call ~97 %, mean |TD| **falling** to 0.77–1.12). Both appear at lr 0.01 and 0.03;
which one a run reaches is **seed-dependent**, not rate-dependent. The long-standing "plateau at 3"
was the raise attractor's signature, not a universal ceiling: the call attractor converges.

This is the user's original expectation realised — a more aggressive rate *can* learn the calling
degenerate state — but only in 3 of 9 runs, and never by asking for it (D-14).

## Neither attractor is better at game level

300 games to a buy-in, seats alternating: **call-mode vs `always-call` 49.0 % ± 11.3** (69.8
hands/game), **raise-mode vs `always-call` 47.7 % ± 11.3** (4.4 hands/game), **call-mode vs
raise-mode 44.3 % ± 11.2** — i.e. the raise mode takes 55.7 %, inside noise. What differs sharply is
game length: the call mode plays 69.8 hands a game against 4.4, so it is the mode that gives the
amplified metric room to work.

## A defect this surfaced

At lr 0.03 and 0.1 the value function goes non-finite and the tie-break crashes with
`ValueError: min() iterable argument is empty` — 2 of 3 seeds at 0.1, 1 of 3 at 0.03. A NaN blow-up
surfaces as an obscure `ValueError` deep in `_tie_break` instead of a named refusal, and nothing clips
or guards the update. Routed: the learner should refuse a non-finite value by name, and the step
should be guarded (D-19, D-20).
