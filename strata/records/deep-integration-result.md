# Deep integration: the card representation pays +11.6 chips/hand, replicated over seeds · 2026-11-08

D-99's deep run — the **best-chips card model** (tok-60) frozen behind a policy head, **15,000 training hands** and
**2,000 greedy evaluation hands** per arm, six seats, **seeds 0–2 for both the card arm and the zeroed control** — the
same head, facts, opponents and seed, with only the card inputs ablated (D-14).

| arm | seed 0 | seed 1 | seed 2 | **mean** | sd | distinct decisions |
|---|---|---|---|---|---|---|
| **card** | **+14.26** ±4.58 | **+10.10** ±4.70 | **+10.53** ±4.15 | **+11.63** | 2.29 | 4 / 3 / 3 of 5 |
| **zeroed** | −0.18 ±0.08 | −3.03 ±3.75 | −0.09 ±0.18 | **−1.10** | 1.67 | 1 / 1 / 1 of 5 |

## The difference is far outside every interval

**Every card arm's 95 % interval excludes every control arm's point estimate** — the lowest card result is
10.10 − 4.70 = **+5.40**, the highest control is **−0.09**. A **+12.7 chip/hand gap** between the arms' means, with
per-seed intervals of ±4–5 and a seed-to-seed spread of only 2.3.

**And the behaviour replicates with it** (D-97): card-dependence in **all three** card seeds (3–4 distinct of 5) and **none**
of the three control seeds (1 of 5, always the same constant).

## What the card model changed, concretely

The card arm's action census (seed 0) against 2 folders and 1 caller (D-99): **`check-call` 45 %, `raise-minimum` 33 %,
`raise-quarter` 18 %, all-in 4 %, fold 0 %** — it raises into a mostly-folding table and never folds. The control arms
either fold half their hands or call everything. So the representation lets the policy find the exploit the scripted
opponents leave open, and the control proves it is the representation doing it.

## What this does and does not establish

**Establishes**: a **seed-replicated, ablation-controlled, chip-measurable** effect of the supervised card
representation on policy performance — the first such result in the project, and the one D-98 could not resolve at
500 evaluation hands.

**Does not establish**: that the policy plays *good poker*. The opponents are three scripted baselines, so the
exploit is "raise at a table that folds", not skill at equilibrium; the learned judgement is still not sound (seed 1
folds KQs and 87s while shoving AA and 22). The next test is the same run against the **league pool** rather than the
three fixed scripts.
