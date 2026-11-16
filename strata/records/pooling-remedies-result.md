# The dilution remedies work on the embedding and change nothing about behaviour · 2026-11-08

D-76 asked whether removing the token path's gradient dilution makes the token models card-aware. Measured as
probes — the remedy applied in-process to the **torch** backend (R3's; patching numpy first gave four identical
arms and was caught by comparing embeddings), 5,000 hands × seed 0, six seats, `stack-shortfall` (D-14).

| arm | what it changes | embedding max |Δ| vs init | predicted |
|---|---|---|---|
| **today** | — | 0.0056 (1.0 % of row scale) | — |
| **`mean-real`** | backward ÷ real token count | **0.0468 — 8.4×** | 8.7× ✔ |
| **`no-squash`** | drop the bounded embedding | **0.0179 — 3.2×** | ≤ 2× ✔ |
| **`sum-pool`** | no denominator | **diverged** past the 1e6 band | 122× ✔ |

**D-75's dilution was real and is fixed**: the embedding moves 8.4× further in the same number of hands.

**And behaviour does not move.**

| arm | fold | card-dependent (AA vs 72o)? |
|---|---|---|
| today | **93.0 %** | no — fold / fold |
| `mean-real` | **92.7 %** | no — fold / fold |
| `no-squash` | **93.0 %** | no — raise-half / raise-half |
| `sum-pool` | diverged | — |
| masked-both (probe) | **93.1 %** | — |

Loaded-deal probe, same dry board, opening seat: **AA, 72o and KQs draw the same decision in every arm** — `fold`
in three, `raise-half` for `no-squash`. Not one remedy makes the model treat aces differently from seven-deuce.
## What this establishes, and what it costs

**D-74/D-75 explained why the embedding learns slowly, and that was correct — but it is not why the models are
blind.** A better-trained embedding, a padding-free forward pool and an unsquashed one all leave the policy folding
aces and seven-deuce alike. **D-75's remedy list is incomplete** — the failure mode D-76 named before the run.

What remains consistent with every measurement: the policy is set by the **exploration loop** (D-72: 93 % at
ε_end 0.05, 0 % at ε_end 0.60), and inside it the risk terms leave the six action values nearly equal, so the
winner is decided by a margin the cards do not enter. The card signal reaches the trunk; the decision ignores it.

**Practical consequence:** the **flat encoding is the only card-aware family** (D-71: AA ≠ 72o, a helpful board
moves the flop action for 3–7 of 8 hole sets) and should carry any demonstration of card-dependent play. The token
path needs a change that reaches the decision, not the representation.
