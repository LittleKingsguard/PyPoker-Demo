# Does always-raise lose against an opponent who only plays strong hands? · measured 2026-11-07

The user's argument: against a strong-hand-only opponent, always-raising should lose over a game,
because the marginal blinds are outweighed by raising into losing hands. Tested at game level — games to
a buy-in (±100 chips), 200 games per cell, seats alternating (D-14):

| strategy | vs D-21 folder | hands/game | vs tight (pair-or-better) | hands/game |
|---|---|---|---|---|
| always **min-raise** | **96.5 %** games won | 151.4 | **100.0 %** | 67.6 |
| always **pot-raise** | **37.0 %** | 6.0 | 62.5 % | 78.8 |
| always **all-in** | 50.5 % | 2.6 | 48.5 % | 15.0 |

## The argument is right about big raises and wrong about minimum ones

- **Pot-sized always-raising loses** (D-6): 37 % of games against the folder. Large bets commit a wide range
  against a range that only continues when strong, so the losses arrive faster than the blinds.
- **Minimum raising wins almost every game** (D-6): 96.5 % against the folder and **100 %** against an
  opponent that continues only with a pair or better. A minimum raise risks 2 chips to win the blinds,
  and an opponent who folds most hands surrenders them nearly every time; the drift is small per hand
  and certain over the ~70–150 hands a game lasts, so absorption at one buy-in is almost inevitable.
- **All-in is a coin flip** (48.5–50.5 %, D-6): it neither steals cheaply nor commits selectively.

The per-hand numbers agree with the game-level ones: min-raise measured **+0.68 ± 0.21** chips/hand
against the folder, and 151.4 hands × 0.68 ≈ 103 chips — one buy-in, i.e. the 96.5 % win rate.
Against the tighter opponent the drift is larger (≈1.5 chips/hand, ≈68 hands to a buy-in), which is the
100 %.

## What it settles for the project

1. **Stealing is the dominant strategy against this pool**, and it is why the trained learner collapsed
   onto raise-minimum with **+2.361 ± 0.448** chips/hand (`sized-criterion.md`). The collapse is not a
   pathology: it is the game's answer.
2. **"Major losses from continually raising" is real, and it is a function of size, not of frequency.**
   The sizing ladder measured the same split (−8.89 ± 1.93 at 1× pot against +0.68 ± 0.21 at the
   minimum).
3. **Variety is therefore the wrong test for this pool.** An agent that mixes in big raises loses games;
   the criterion that demanded spread was measuring a preference the game punishes (D-31).

Caveats (D-6): scripted bettors, one stack depth (100), blinds 1/2, and opponents that never raise —
the 100 % belongs to an opponent that is *only* a folder, which no real pool member is every hand.
