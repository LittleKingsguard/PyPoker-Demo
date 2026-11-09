# Does more players fix the coin flip? Probe · 2026-11-07

Proposal (user): move from heads-up to 4–6 players, because 2 players is "50/50 by construction" and
more players "reduces the odds any given player has of having the best hand".

Probe, pokerkit directly, 400 hands per cell, seat 0 a *junk-folder* (folds both-under-T unpaired
preflop) against always-callers (D-14): **2 seats +0.030 ± 0.195**, **6 seats −0.310 ± 0.364** — more
players does not make folding right. Depth never enters: hands played by checking are ±2 chips at 20
and at 200, since the pot never passes the blinds. The limit structure, not the seat count, decides
how much money moves.

## Correction: the probe used `always-call`, not the oracle

The oracle *is* the pool's folding strategy and the probe wrongly benched against always-call.
Measured heads-up (`agents.build_baseline("oracle")`): it folds **4.9 %** of decisions overall, never
preflop, 4.9 % on the flop, 22.7 % on the turn, 15.9 % on the river, and never raises. Six-way it
folds **only when raised**: a limped pot offers 1 to win 11 (8.3 %), while 6-way equities of random
hands measure 0.126–0.226, so almost nothing folds; a raised pot (2 into 15 = 11.8 %, or 4 into 23 =
14.8 %) crosses the weak-hand range and the bottom third goes. So multi-way does not add a folder —
it makes folding conditional on being bet at (D-6).

## Why multi-way does not fix it

A limped 6-way pot offers the small blind **1 chip to win 11** — 8 % equity to continue, and almost no
hand is that bad (D-6). More players makes pot odds *more* generous, so folding stays wrong and calling
stays right; the always-call degeneration is *reinforced*, not broken. The 50/50 is not caused by the
seat count: it is caused by a never-folding opponent removing fold equity (no bet can win a pot
without showdown) plus small bets relative to stacks (no leverage).

## Cost

"Little extra processing" does not survive contact with the code: N seats touches the engine's
two-seat configuration, `features` (two stack slots, seat flags, the 203-slot layout), the oracle
(N-way equity — one 6-way call at 60 samples already costs 0.12 s, against 0.25–0.32 s per hand for
the whole 2-way oracle cell), `evaluation` (a pairwise matrix and Bradley-Terry rating become N-way
placements and a Plackett-Luce fit), the pool, the report, all 253 e2e cases and every artefact.

The levers that *would* create EV are the ones that make betting matter: opponents that fold (so
bluffs can win), bets that threaten a stack (no-limit or pot-limit sizing), or antes that make pots
worth contesting. None of them is player count (D-2, D-6).
