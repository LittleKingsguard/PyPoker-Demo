# Deep run with fold equity in the pool · 600,000 hands, 2026-11-07

Same rule, utility, backend, architecture, seeds and budget as `r2-deep.md` — **only the pool**
differs: three anchors plus `fold-no-pair-or-face` and `fold-no-pair-or-better` (`pool-1ccac5e029403cce`).
It took **42,569 s (11.8 h)**, 600,000 hands at 0.0705–0.0712 s/hand — cheaper per hand than the
anchors-only run, since folders end hands sooner and the oracle is a fifth of the pool (D-21).

## The learning signal moves, a little

| seed | anchors-only deep | folders deep |
|---|---|---|
| 0 | 3.08 → 3.13 | **2.466 → 2.339** |
| 1 | 2.75 → 2.91 | **2.342 → 2.232** |
| 2 | 3.08 → 3.00 | 2.479 → 2.531 |

Lower, and gently falling on two seeds — the first curve here that does not simply plateau, though a
pool whose opponents fold makes smaller, less variable pots, so part of the lower error is the pool's
variance rather than the learner's skill (D-6).

## The behaviour barely changes

Action census (D-14): against `random` **87 / 11 / 2** raise/call/fold (anchors deep: 80 / 18 / 2);
against `always-call` **74 / 25 / 0** (anchors deep: 87 / 13 / 0) — still a raise-maniac, with 13 points
less raising against a caller, so mildly opponent-sensitive, but 74 % is not selective play. The
1,000-hand result that folders cut raising to 45 % (D-21) does not survive 200× more hands: that
number was noise, retired here.

## Outcomes stay unresolved

Games to a buy-in, 200 games, seats alternating: vs the anchors-deep twin **47.5 %** (95/105, **1.6
hands/game**), vs `always-call` **50.0 %** (100/100), vs `fold-no-pair-or-face` **53.5 %** (107/93,
**10.9 hands/game**); anchors-deep vs `always-call` 48.0 %. The only positive edge is against the
folder, inside ±7, with the longest games — the most chance to resolve.

## Verdict

**Fold equity in the pool did not change this agent in any way that matters.** Five levers tried —
estimator (D-19), capacity, 200× time, utility (D-20), opponent population (D-21) — and exactly one
moved behaviour (the risk-averse utility, −30 points of raising). None produced a resolvable EV edge,
which is what the coin flip predicts: the best available play is worth about nothing (D-6).
