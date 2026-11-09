# Does more players fix the coin flip? Probe · 2026-11-07

Proposal (user): move from heads-up to 4–6 players, because 2 players is "50/50 by construction" and
more players "reduces the odds any given player has of having the best hand".

Probe, pokerkit directly at 2 and 6 seats, 400 hands per cell, seat 0 playing a *junk-folder*
(folds both-under-T unpaired preflop, calls otherwise) against always-callers (D-14):

| seats | junk-folder, chips/hand | note |
|---|---|---|
| 2 | +0.030 ± 0.195 | indistinguishable from zero |
| 6 | **−0.310 ± 0.364** | folding junk is a little worse, not better |

Depth does not enter: hands played by checking only are **±2 chips at 20-chip stacks and at 200**
(the pot never grows past the blinds), which is why the same numbers appear at both depths. That is
itself the finding about the game — the limit structure, not the seat count, decides how much money
moves.

## Why multi-way does not fix it

A limped 6-way pot offers the small blind **1 chip to win 11** — 8 % equity to continue, and almost no
hand is that bad (D-6). More players makes pot odds *more* generous, so folding stays wrong and calling
stays right; the always-call degeneration is *reinforced*, not broken. The 50/50 is not caused by the
seat count: it is caused by a never-folding opponent removing fold equity (no bet can win a pot
without showdown) plus small bets relative to stacks (no leverage).

## What the same probe implies about cost

"Little extra processing" does not survive contact with the code: N seats touches the engine's
two-seat configuration and readouts, `features` (two stack slots, seat flags, 203-slot layout), the
oracle (equity against N hands and pot odds with multiple callers), `evaluation` (a pairwise matrix
and Bradley-Terry rating would have to become N-way placements and a Plackett-Luce-style fit), the
pool and report, all 253 e2e cases, and every shipped artefact. It is a multi-day change with a
re-baseline, not a parameter flip — and on the measurement above it would not buy the EV it is for.

The levers that *would* create EV are the ones that make betting matter: opponents that fold (so
bluffs can win), bets that threaten a stack (no-limit or pot-limit sizing), or antes that make pots
worth contesting. None of them is player count (D-2, D-6).
