# Why R1/R2 stall: the game is nearly a coin flip · measured 2026-11-07

Framing (user): if both sides call or raise almost always, the outcome is decided by the draw (D-14).

## The measurement that settles it

Two mirror matches, 1,000 hands each, seats alternating (D-14) — only **three payoffs**, identical
splits: `always-call` vs `always-call` gives **+2 / −2 / 0** at **48.0 % / 46.4 % / 5.6 %**, and
always-raise vs always-raise gives **+20 / −20 / 0** at the **same three shares**.

The win/loss split is **identical to the tenth of a percent**. The policy changes only the *stake*
(±2 chips vs ±20), never who wins. With 20-chip stacks and a four-bet cap a hand reaches showdown for
the same stake whatever the betting does, so the winner is the cards. Confirmed on the same deals:
`(caller, raiser)` and `(raiser, caller)` return byte-identical payoffs even though their decision
histories differ (D-14).

## What is true of the learner

- **Raise versus call is EV-neutral.** Over 2,000 alternating-seat hands: caller-vs-caller −0.060 ±
  0.088, raiser-vs-raiser −0.600 ± 0.87, caller-vs-raiser −0.420 ± 0.61 chips/hand. Every interval
  spans zero. The raise habit the earlier record called "a mistake worth 0.730 chips/hand" is inside
  noise (1.4 se) — that claim is retracted; it was a single-seat tally against a ±14-chip payoff.
- **Folding is the only lever the game offers, and it is expensive.** Always-fold loses 0.540 ± 0.06
  to a caller and 1.500 ± 0.02 to a raiser — many standard errors. The learner folds 1 %, i.e. it has
  already learned the one decision this game actually rewards (D-6).
- **Aggression raises variance, not expectation** (D-6): ±2 becomes ±20 on the same hands, and a max
  operator over noisy estimates makes the higher-variance action look best — which is why both rules
  landed on always-raise, not because it wins.

## The consequence for the ladder

Here the only behaviour that pays is "do not fold", which every rung reaches at once, so R1–R6 must
look indistinguishable — and did. Not only because the instrument is underpowered, but because **the
game was configured to make skill nearly irrelevant**: short stacks and a four-bet cap turn every
non-folding hand into an all-in showdown decided by the draw (D-6).

Fixing it is a game-parameter decision, not a network one: deeper stacks (or bets small against deep
stacks) so that bet, call and fold have distinguishable EV, and a re-baseline after it. That revises
the assumptions D-2 left to the brief, so it comes back to the user (D-2, D-14).
