# How closely does the opponent model track the reviewed models? It predicts fold and nothing else · 2026-11-08

The frozen `.probe/opp.pt` run over each opponent's own decisions (250 self-play hands per opponent, every decision
scored; D-14).

| opponent | n | actual fold/call/raise % | **predicted fold/call/raise %** | acc | base rate | **lift** | fold prec / rec |
|---|---|---|---|---|---|---|---|
| folder (league) | 1,806 | 69 / 2 / 29 | **83 / 17 / 0** | 0.558 | 0.692 | **−0.135** | 0.66 / 0.79 |
| raiser-50-50 (league) | 1,500 | 83 / 0 / 17 | **100 / 0 / 0** | 0.833 | 0.833 | 0.000 | 0.83 / 1.00 |
| **raiser-83 (league)** | 1,965 | **10 / 53 / 36** | **97 / 3 / 0** | **0.110** | 0.533 | **−0.423** | 0.10 / 0.91 |
| `fold-no-pair-or-face` | 4,338 | 13 / 87 / 0 | 18 / 82 / 0 | 0.845 | 0.873 | −0.028 | 0.42 / 0.61 |
| `fold-large-bet` | 6,000 | 0 / 100 / 0 | 4 / 96 / 0 | 0.958 | 1.000 | −0.042 | 0.00 / 0.00 |

## Three facts

1. **It never predicts a raise** (D-121). Zero raise predictions against an opponent that raises 36 % of its decisions — the
   model's output is effectively binary, fold-or-call.
2. **It over-predicts fold everywhere**: 83–100 % predicted against 0–83 % actual, with fold precision 0.10–0.83 and
   recall 0.61–1.00. It finds most folds and misfires on most of what it calls a fold.
3. **It beats the majority-class baseline on no opponent** (D-121). Lift is **≤ 0 for all five**, and for the most active member
   (raiser-83) it is **−0.423**: 11 % accuracy against a 53 % baseline, worse than a coin weighted by the marginal.

## Why, and why it matters for the policy

The model was trained on mixed six-seat tables where **95.9 % of labels are calls** (D-113), and with class weights that
still leave calls dominant. Faced with a member whose action mix is *not* call-dominant, it has no representation for
"raise" and defaults to fold. So its output is a **near-constant vector**, which is exactly what made it useless as a
policy input and destructive in the four-arm test (D-119: both arms carrying it collapsed to fold-100 %).

## The honest summary

**Alignment is poor in a specific, diagnosable way** (D-121): the model has learned the marginal of its training population, not
any member's policy. It is right about folds it has seen many of, blind to raises it has seen almost none of, and never
better than the base rate. Any claim that it "reads opponents" would need balanced accuracy or per-class F1 on a
class-balanced evaluation — and on this measurement, with raise predictions at zero, it cannot be made.
