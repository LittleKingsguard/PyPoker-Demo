# Does no-limit make bet sizing matter? Probe · 2026-11-07

No-limit heads-up in the probe harness (pokerkit directly), blinds 1/2, 100-chip stacks, 400 hands per
cell, seats alternating, sizing as a pot fraction. The fixed-limit game this project shipped is
EV-neutral across actions (`r2-plateau-diagnosis.md`); the question here is whether no-limit is not.

| cell | bettor's chips/hand | folds by the folder |
|---|---|---|
| **pot-bet vs folder** | **−6.582 ± 4.656** | 306 |
| **half-pot vs folder** | **−0.802 ± 1.521** | 306 |
| pot-bet vs caller | −1.750 ± 9.847 | — |
| half-pot vs caller | −0.560 ± 3.151 | — |
| folder vs caller | −0.147 ± 0.181 | 81 |

## Sizing now has consequences

The same bettor, the same folding opponent, two sizes: **−6.6 ± 4.7 at one pot against −0.8 ± 1.5 at
half a pot** — a ~5.8 chips/hand difference that clears its interval. In the fixed-limit game the
identical comparison was inside noise because a four-bet cap made every size the same size. This is
the first measured quantity in the project that *rewards a decision*: over-betting into a disciplined
folder is punished, restraint pays, and the gradient the learner needs finally exists.

Why the sign is negative for the bettor: the folder continues only with a pair or better, so a pot
bet is called exactly when the bettor is behind and folds out everything it beats — the classic price
of betting into a folder with a wide range.

## What it costs to have it in the product

The action vocabulary is three indices today (`fold`, `check-call`, `raise` at the minimum legal
completion). No-limit needs a *size* in the action: an extra dimension in the vocabulary, in the
record, in every policy's decision, and in the encoder if the size is to be seen at all; plus the
engine variant (`NoLimitTexasHoldem`), the legal-amount facts in the readout, and a decision about
whether sizes are a discrete ladder (half/full pot, all-in) or a regression head.

## Caveat on the probe itself

Three defects before it ran clean, all mine, all caught by assertions added after the first two: a
policy's `fold` executed as a call, a counter attribute on one policy only, and two illegal actions
(folding when checking was free; a bet above the maximum completion). Probe code has no battery; the
product's batteries exist for this (D-11) and the harness should keep the assertions.
