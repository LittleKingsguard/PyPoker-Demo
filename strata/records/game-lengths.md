# How long a full game lasts, and a shape-mismatch defect · measured 2026-11-07

A game is played to one buy-in (100 chips) at blinds 1/2 with 100-chip stacks, seats alternating
(D-14). Measured hands per game:

| player | opponent | hands/game | games won |
|---|---|---|---|
| always all-in | either folder | **2.6–15.0** | 48.5–50.5 % |
| always pot-sized raise | D-21 folder / tight | **6.0 / 78.8** | 37.0 / 62.5 % |
| always min-raise | tight (pair or better) | **67.6** | 100.0 % |
| always min-raise | D-21 folder | **151.4** | 96.5 % |
| the trained model (seed 0), greedy | `fold-no-pair-or-better` | **142.1** | 98.3 % |
| the trained model (seed 0), greedy | `fold-no-pair-or-face` | **171.6** | **30.0 %** |

So the trained agent's full game against a folding opponent runs **~140–170 hands**; a scripted stealer
takes 68–151; a pot-sized aggressor ends one in 6 or fewer; an all-in shover in under 15.

Two readings matter. The **length is set by the steal, not by the stack**: a minimum raise wins a few
chips a hand, so absorbing a 100-chip buy-in takes ~100–170 hands, and a game shorter than ~10 hands is
one or two all-ins decided by the draw. And the trained model wins **98 % against the folder that folds,
30 % against the folder that calls** — the same agent, the same strategy, opposite results, which is the
steal's whole dependence on a folding opponent in one pair of rows.

## A defect this exposed

Loading a **fixed-limit** checkpoint and playing it in the six-descriptor shape was not refused: the
policy loaded (a container with no `game` reads as the default shape) and then failed obscurely at
decision time as `IndexError: index 3 is out of bounds for axis 0 with size 3`, instead of a named
shape-mismatch refusal. The pool already refuses a foreign-shape member; a bare policy does not.
Routed, not fixed here.
