# Who is the league's best member? Re-measured, there is no stable answer · measured 2026-11-08

Ten six-seat checkpoints played **1,000 hands each** against the same league mix (folder / 50-50 raiser / 83 %
raiser / caller), same seats, same hand sequence (D-14).

| member | chips/hand | 95 % interval | behaviour |
|---|---|---|---|
| **83 % raiser** | **−0.05** | ±10.09 | call 83 %, raise-min 17 % |
| **our model (15k, seed 0)** | **−0.05** | ±10.09 | call 83 %, raise-quarter 17 % |
| **50-50 raiser** | **−0.08** | ±3.96 | fold 80 %, all-in 20 % |
| folder | −0.60 | ±0.05 | fold 100 % |
| mask-only · pool-today · pool-mean-real · pool-no-squash · pool-sum | −0.60 | ±0.05 | fold 100 % |
| **mask-no-squash** | **−6.20** | **±0.69** | fold 83 %, raise-quarter 17 % |

## The ranking does not reproduce

The **50-50 raiser** scored **+2.24 ±3.33** in the earlier 1,500-hand measurement (D-105) and **−0.08 ±3.96** here —
a 2.3-chip swing on a different hand set, inside its own interval. So **D-105's "level with the league's best member" is
weaker than it read**: on this hand set there is no top member to be level with, because the top three are within
**0.03 chips** of each other and their intervals are **±4 to ±10**.

## What is stable

1. **The folder is exactly −0.60** — deterministic, it surrenders the blind.
2. **Seven of the ten members are −0.60** — pure folder behaviour (mask-only, all four pool-probe arms, the foldloop
   control). The league is mostly folders.
3. **One member is genuinely bad**: `mask-no-squash` at **−6.20 ±0.69** — it raises into a table that raises back.
   This is the D-77 "remedy" arm, and on this table it is the worst policy measured in the project.
4. **Everything in between is break-even within noise**: −0.05 to −0.08 with ±4–10 intervals.

## The answer to the question

**There is no best member that survives measurement.** The league is a set of near-break-even policies plus one pure
folder plus one clear loser; the chip instrument against a fixed mix cannot rank the near-break-even ones at any sample
size this project has run. Ranking them needs the head-to-head instrument (D-21) with many more games, or a much
stronger pool — which is the same conclusion D-105 reached from the other side.
