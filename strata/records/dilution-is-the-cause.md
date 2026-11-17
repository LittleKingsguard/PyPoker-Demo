# The dilution is the cause: give the probe the product's pooler and it reproduces the product exactly

D-104/D-109 left one difference untested at equal budget with a live trunk: the two arms are fed different
representations. This feeds the **probe** the representation the product's pooler actually produces —
`pooled = (sum of the real card rows + 108 × pad_row) / 123`, with `pad_row` taken from the product's own table after
its `(1 + tanh)/2` squash — and changes nothing else. 15,000 hands, same league, same seed, live trunk (D-14).

| probe's card input | chips/hand | fold when facing a bet | census |
|---|---|---|---|
| **the product's pooler (diluted)** | **−0.600 ±0.04** | **100.0 %** | **fold 100 %** |
| the probe's own pooled representation (masked) | −0.22 ±6.98 | 2.3 % | call 97.7 % |
| *for comparison:* the product's own control arm | −0.600 ±0.04 | 100.0 % | fold 100 % |

**The diluted probe reproduces the product's result to three decimal places** — −0.600 against −0.600, fold 100 %
against fold 100 % — while the same probe with an undiluted representation does something else entirely.

## What this establishes

The difference between the probe and the product was **not** the target (a TD-style probe arm scored *higher* than the
Monte-Carlo one, +7.11 against +4.93), **not** the utility (`net-chips` and `stack-shortfall` both fold at 5,000), and
**not** the trunk (live in both, 22/50 in the product and 34/64 in the probe).

**It is the pooler.** 108 of the product's 123 token positions are padding, so the card information reaches the trunk at
roughly **12 % amplitude**; the policy cannot separate hands and pins to one action — and when the early updates land on
fold, ε → 0.05 keeps it there (D-72).

## Caveats

The masked probe arm is itself unstable across hand seeds (fold 61 % with call 39 % in one run, call 97.7 % in another),
so "the probe works" is not the claim. The claim is narrower and causal: **the diluted input reproduces the product's
exact failure**, which identifies the mechanism.

## The change this earns

**Mask the product's token pooler** — exclude pad ids from the pool *and* from the gradient scatter (D-79's remedy),
which the strength change was explicitly forbidden from shipping alongside (D-3, one thing at a time). With the trunk
already revived at `net-chips-normalised`, that is now the single highest-value change in the project.
