# The scenario suite: flat models use their cards, token models do not · measured 2026-11-08

D-70's suite, built and run: sixteen declared scenarios (eight hole sets × helpful and unhelpful board, all
eight unhelpful cases on **one** dry board so the hole contrast is eight hands in one state), six post-D-61
cells × seeds 0–2, two seatings, **576 decisions** with their full score vectors (D-14).
## The answer

**Flat encodings: the action depends on the cards.** AA and 72o offsuit diverge, and a helpful board moves the
flop action for **3–7 of the 8** hole sets at every seed — same pot, same stacks, same history, same legal set.

**Token encodings: it does not.** They fold **all sixteen hands at every seed** wherever folding is offered, and
hold one or two constants where it is not. The two encodings give **opposite** answers to the question.
## The tables, in one example each

| scenario (big-blind, seed 0) | `masked-flat` | `masked-tokens` |
|---|---|---|
| AA, helpful | check-call / **raise-all-in** | raise-quarter / raise-quarter |
| AA, dry | check-call / raise-quarter | raise-quarter / raise-quarter |
| 72o, helpful | check-call / check-call | raise-quarter / raise-quarter |
| 72o, dry | check-call / raise-quarter | raise-quarter / raise-quarter |

Opening seating, where a fold is offered, is starker: `masked-tokens` folds **all sixteen hands** (AA included)
at all three seeds; `masked-flat` folds none and varies.
## The token arms are blind, not collapsed

D-59's failure was one constant vector. Here the token models produce **8–24 distinct score vectors** per
seating, so their values move with the hole (AA `fold −0.004` against 72o `−0.003`) — but the argmax sits on
`fold` whenever folding is legal and on one raise band when it is not, so the *decision* cannot change: blind
values, fixed action.
## What this does to the encoding claim

**It refutes the behavioural reading of it.** "Tokens fold 92.7 % against flat's 77.5 %" (D-56) and "tokens lose
four to forty times less" (D-67) are both true and mean the opposite of what the percentages suggested: the token
models lose less **because they fold cheaply**. The flat models are the only ones whose decisions depend on the
cards they hold.
## Two results worth keeping, stated as results

`norm-doubleq-tokens` **seed 2 shoves all-in preflop in all sixteen scenarios**, so those rows carry no flop
decision — an all-in, not a missing row. And seeds agree action-for-action only for the token cells in the
opening seating; elsewhere every cell varies by seed — the attractor lottery, unchanged.
