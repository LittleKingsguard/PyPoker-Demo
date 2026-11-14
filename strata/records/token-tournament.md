# Inference test: all ten token models against each other · measured 2026-11-08

Every `card-tokens` checkpoint on disk — three under `net-chips`, seven under `stack-shortfall` — plus the
pool's raiser as a reference: **11 entrants, 55 matches**, six seats, each match over 300 deals played
**twice** (entrant on the even seats, then the odd) so position cannot confound and the match is exactly
antisymmetric (D-14).

**Instrument checks:** antisymmetry `match(a,b) + match(b,a) = +0.000000`; within-family mean |chips|
**0.026** across 24 matches between models playing the same policy.

| entrant | chips/hand per seat | trained under |
|---|---|---|
| **raiser-6seat** | **+0.764** | the pool's raiser, not a token model |
| **tok-netchips s0** | **+0.223** | net chips |
| tok-netchips s1 / s2 | −0.036 / −0.036 | net chips |
| tok-shortfall s5 | −0.081 | stack-shortfall |
| tok-shortfall s6 · s1 · s4 · s3 · s2 · s0 | −0.121 · −0.135 · −0.137 · −0.142 · −0.143 · −0.156 | stack-shortfall |
## Family cross-comparisons

| matchup | chips/hand per seat | matches |
|---|---|---|
| **token + net-chips vs token + shortfall** | **+0.265** | 21 |
| raiser vs token + net-chips | +1.352 | 3 |
| raiser vs token + shortfall | +0.512 | 7 |
## What it says

1. **The folding models lose to the non-folding ones.** `token+shortfall` — reproducible folding across
   seven seeds (D-56) — gives up **0.265 chips/hand per seat** to `token+net-chips`, which never folds.
2. **They also lose to the raiser** (+0.512 for the raiser), and the raiser beats everyone at +0.764, which
   is what a model trained against the whole pool should do.
3. **The best individual model is a non-folding one** (+0.223); every folding model is negative against the
   field.

**So D-56's reproducible folding is priced: the behaviour that is reliable is the behaviour that loses.**
The folder surrenders a quarter of a chip a hand to the agent that never folds — reproducibility and
performance point opposite ways, which is a better slide than either alone.

**My own defects, caught by invariant before any number was read:** a seat-index bug that measured the
opponent's seats while labelling them the entrant's; different deal sets for the two seatings, breaking
antisymmetry (sum −0.216); and `payoffs` indexed as a list when it is seat-keyed.
