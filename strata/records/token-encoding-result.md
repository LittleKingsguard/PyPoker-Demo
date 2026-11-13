# The encoding moves the policy, not the money (net chips, six seats) · measured 2026-11-08

D-51's paired comparison: `R3 card-tokens` against `R1 flat-numeric`, six seats, no-limit, 100-chip
stacks, the mixed pool `pool-8386c3ef83ae48b2`, **15,000 hands × seeds 0, 1, 2**, `net-chips`, ties
excluded, arms differing only in the encoding (D-14). Wall clock 7,890 s and 8,291 s.

| arm | seed | decisions | fold | dominant action | chips/hand [95 %] |
|---|---|---|---|---|---|
| flat-numeric | 0 | 3,935 | 0 % | **raise-minimum 61.7 %** | −4.24 ± 7.09 |
| flat-numeric | 1 | 3,848 | 0 % | **raise-minimum 59.7 %** | +0.97 ± 7.18 |
| flat-numeric | 2 | 4,617 | 0 % | check-call 100 % | −2.68 ± 7.10 |
| card-tokens | 0 | 3,889 | 0 % | **raise-half 56.8 %** | −2.00 ± 7.54 |
| card-tokens | 1 | 4,432 | 0 % | check-call 100 % | −3.51 ± 7.05 |
| card-tokens | 2 | 4,617 | 0 % | check-call 100 % | −2.68 ± 7.10 |

## What the encoding does and does not do

**It moves the policy** (D-6). At seed 0 the flat encoding settles on **minimum raises** (61.7 %) where the token
encoding settles on **half-pot raises** (56.8 %) — the first attributable behavioural difference between
the two encodings in this project. At seed 1 they diverge the other way: flat keeps 59.7 % minimum raises,
tokens fold into always-call.

**It does not move the money** (D-6). Every chip interval spans zero by a wide margin (±7 on 2,000 hands), and at
seed 2 both encodings land on the *same* policy — always-call — with **identical** decision counts (4,617)
and identical payoffs (−2.6835), which is what two encodings reaching one behaviour on one deal set must
produce.

**Neither arm folds.** 0 % at all six cells, as `net-chips` has done in every multi-seat run recorded
(D-34, D-44, D-47).

## So what is the encoding worth?

It changes **which attractor a seed falls into**, not the outcome: the size of the bet, and whether the
agent bets at all. That is a real effect and a usable talk beat — *"tokenising the cards changed how the
agent played and not how much it won"* — but it is not evidence that tokens learn better poker, and the
zero chip difference is what says so.

The sharper test is the same pair under `stack-shortfall`, where the baseline folds 77–87 % and there is a
policy distribution for the encoding to disturb; that run is in flight (D-52).
