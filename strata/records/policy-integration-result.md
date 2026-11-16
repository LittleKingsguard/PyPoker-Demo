# The first card-dependent policy: the supervised representation drives the decision · measured 2026-11-08

D-92 wired the supervised model into a policy. This runs it: a policy head takes the card model's **pooled
representation (50)** *and* its **probability estimate (1)** *and* five table facts (pot, `to_call`, street, stack,
board count) — 56 inputs — and learns Q-values over the six descriptors by masked-Q on the terminal chip reward, six
seats, 4,000 hands, ε 1.0 → 0.05 (D-14). The card model is the **best-performing checkpoint** (epoch 400, pooled R²
40.0 %) and is frozen.
## With the card model's inputs — the loaded-deal suite

| hole | decision | truthful read |
|---|---|---|
| **AA** | `raise-all-in` | strong |
| **KQs** | `raise-all-in` | strong |
| **87s** | `raise-all-in` | speculative but playable |
| **22** | `fold` | small pair |
| **72o** | `fold` | junk |

**2 of 5 distinct decisions — the first card-dependent policy this project has produced.** Every policy experiment
before this one (D-71, D-73, D-77, D-82, D-92) reported **1 of 5**: one action for every hand, at every seed.
## And the control that makes it real

The identical run with the **card inputs zeroed** — same head, same facts, same opponents, same 4,000 hands:

| inputs | AA | KQs | 22 | 87s | 72o | distinct |
|---|---|---|---|---|---|---|
| card representation + probability | `raise-all-in` | `raise-all-in` | `fold` | `raise-all-in` | `fold` | **2 / 5** |
| **both zeroed** | `fold` | `fold` | `fold` | `fold` | `fold` | **1 / 5** |

So the discrimination comes from the supervised representation and **not** from the table facts, the opponents or the
optimisation noise.
## What it does and does not establish

**Establishes**: the two-layer diagnosis (D-84) is actionable — supply a card representation to a policy head and it
starts reading hands. The mechanism is named and reproducible in a 4,000-hand probe.

**Does not establish**: that the judgement is *sound*. It shoves 87s all-in while folding 22 — variation, not skill —
and it is one run, one seed, and a hand-rolled semi-gradient step rather than the product's learner. The next step is
the product's own rule with this input, over seeds, judged by the scenario battery rather than by one table.
