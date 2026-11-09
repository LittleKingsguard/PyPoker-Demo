# Measuring games won instead of hands won · measured 2026-11-07

A game is played until one side is a **buy-in down** (cumulative delta ±20; each hand deals fresh
20-chip stacks), seats alternating. 200 games per pair, 95 % interval ≈ ±7 pp (D-14).

| pair | games won | W/L | hands per game |
|---|---|---|---|
| `always-call` vs `always-call` (control) | 46.0 % ± 7.0 | 92/108 | **109.6** |
| always-raise vs `always-call` | 45.0 % ± 7.0 | 90/110 | **4.2** |
| R1 shipped vs `always-call` | 44.5 % ± 7.0 | 89/111 | **4.2** |
| `stack-shortfall` model vs `always-call` | 45.5 % ± 7.0 | 91/109 | **5.9** |
| **`net-chips` model vs `stack-shortfall` model** | **78.0 % ± 5.9** | **156/44** | 4.2 |
| R1 shipped vs R2-deep | 49.0 % ± 7.1 | 98/102 | **1.7** |

## The metric works — where there is an edge

D-20's head-to-head was unresolvable per seed on hands won ("no single seed's interval excludes
zero") and becomes **78 / 22 at game level**. A per-hand edge compounds through the absorption
barrier: for a walk with drift µ, variance σ² and barrier L, the win probability is roughly
`0.5 + µL/(2σ²)`, so a small edge becomes a large win-rate difference when a game lasts many hands.
That is the amplification the hand-level table never had.

## And it degenerates exactly where the game does

The amplification needs **long** games. Aggression makes them short: aggressive pairs end a game in
**1.7–4.2 hands**, because one all-in moves ±20 and absorbs at once — a 1.7-hand game is a coin flip
wearing a game's clothes, which is why R1 vs R2-deep sits at 49 %, the same null the hand table
reported. The passive control takes 109.6 hands per game and would amplify an edge, but its EV is
zero so there is nothing to amplify (46.0 % ± 7). The models also do not separate from `always-call`
at this power (44.5–45.5 % ± 7) — consistent with the coin flip, not contradicting it.

## The consequence

Game-level win rate is the better instrument and should replace hands-won as the league's headline
metric, with two conditions: games must be **long enough to amplify** — which the 20-chip stack and
four-bet cap prevent — and must not be **shortened by the aggression models actually use**, which the
utility axis (D-20) only partly counteracts. Deeper stacks fix both at once.

Per-hand EV over absorbed games is biased by optional stopping and is not reported; only game win
rates are meaningful here (D-6).
