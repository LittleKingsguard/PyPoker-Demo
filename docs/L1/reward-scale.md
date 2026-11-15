# PyPoker-Demo — the normalised reward, and the test that decides whether it revives the trunk

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-14
- **Owns:** D-20's third utility member — its formula, its normaliser, the alternatives it rejects,
  what it costs (nothing structural) and how a record's chips stay readable in raw chips beside it —
  together with the six-cell test that measures whether it keeps the trunk alive, the prediction
  that test was pinned to test, and what it measured (D-65, D-20, D-60)
- **Ceiling:** 215 lines. Raised from 150 at Rev 2, before the measurement was added, because the
  per-seed table and the verdict are this argument's second half: splitting them out would leave a
  verdict in one document and the prediction it answers in another, which is the one split
  `grid-result.md` §1 forbids for a document whose whole purpose is to answer one question (D-65)

## 1. The chain this acts on

`strata/records/trunk-death-rca.md` measured the trunk dying by **weight explosion** and then
freezing on a **zero gradient**: ‖w_in‖ goes 11.0 at hand 300 → **298.6 at hand 600** → and stays
298.6 to four significant figures for 2,400 more hands while only `b_out` moves. The cause is the
step size, `lr·δ·x` ≈ **0.6 per hand**, because the reward is chips — ±600 a hand at six seats — so
the first TD errors are |δ| ≈ 600 at the declared `lr` of 1e-3. The weights climb ~1 per hand, every
trunk pre-activation lands on the negative side of the rectifier, the rectifier's derivative is 0,
and no gradient reaches the input path again. **No learning rate in that span works**: at 1e-6 the
weights stay at their initial values for all 3,000 hands (‖w_in‖ 8.471, `b_out` 0.022) — nothing
explodes and nothing learns (D-65, D-60, D-63).

The term the RCA names is therefore the **scale of the value being learned**, and D-63 leaves it the
last experiment this cause admits: not another input transform (D-61 measured as inert), not an
architecture rung, not another estimator (`grid-result.md` §4). This document adds that utility.

## 2. The member: `net-chips-normalised`

`agents.learners()["utilities"]` publishes a **third** member, appended after the two of `utilities.md`
§2 so no existing member's position — and so the declared default — moves:

| Utility | The reward it delivers at the terminal decision | What it reads |
|---|---|---|
| `net-chips-normalised` | `normalised-net-chip-delta` — the seat's net chip delta divided by the chips a hand can move for one seat | the same payoff, and the game's chips in play (§3) |

**The formula.** `r = Δ / T`, where `Δ` is the seat's net chip delta for the completed hand — the
number `engine.payoffs` already places, unchanged — and `T` is the game's **chips in play**,
`seats × starting_stack` from `engine.game_config(shape)`: 40 on `fixed-limit-20`, 200 on
`no-limit-100`, **600** on `six-seat-no-limit-100` (`shapes.md` §2, `seats.md` §2). `Δ` and `T` are
read through the same conservation guard `stack-shortfall` uses (`utilities.md` §4), so a hand whose
totals disagree is refused by the same name rather than divided by a substituted number (ASM-28).

**The interval, stated exactly.** A seat can lose at most its own stack and win at most the rest of
the table, so on a shape with `S` seats and starting stack `s0`, `Δ ∈ [−s0, (S−1)·s0]` and
`r ∈ [−1/S, (S−1)/S]` — at six seats **`[−1/6, +5/6]`**, at two `[−1/2, +1/2]`. The property the RCA
needs is the bound it gives: **`|r| ≤ 1` on every declared shape, with no clamp and no reachable end**,
so the first TD error is |δ| ≲ 1 and one step is `lr·δ·x` ≈ **1e-3** rather than 0.6. Dividing by the
starting stack instead would bound nothing (`|r| ≤ 5` at six seats); `T` is the divisor that bounds
the reward for every seat of every shape at once (ASM-45).

**Terminal-only, exactly as the other two are.** Every non-terminal decision carries `0.0`, `learn`'s
terminal branch stays `target = reward`, its non-terminal branch stays the rule's, and the transform is
applied in `training`'s transition record and nowhere else (`utilities.md` §3, §4, ASM-12). **So this
member differs from `net-chips` in scale and in nothing else**: one terminal number, one zero
elsewhere, one bootstrap rule, one state layout, one `param_count`, one checkpoint array — which is
what makes a two-member comparison attributable to the scale (ASM-10, ASM-28, D-3).

## 3. The alternatives this rejects

- **Clamping the raw reward** at ±c. It changes the **objective**, not its scale: two hands the game
  paid +300 and +600 become one value, so the learner stops preferring the larger pot — a preference
  D-20's axis already owns and this change does not touch. It also flattens δ exactly where the
  gradient lives, which is the stall D-65 measured at a small rate, arriving from the other side
  (ASM-28's own rejected alternative, `strata/records/r2-plateau-diagnosis.md`).
- **Lowering the learning rate.** Measured rather than argued: at 1e-6 the trunk stays alive and
  **nothing learns** (‖w_in‖ 8.471 frozen from hand 300, `b_out` 0.022); at 1e-3 it explodes by hand
  600. At a 600-scale reward the usable window between those two is empty, so no rate in that span is
  a fix (D-65).
- **A bounded advantage or TD-target normalisation inside the rule.** That axis owns the **bootstrap**
  and the rule's `learn` contract is one target per transition, so a target transform there would
  make a catalogue member accept a different input from its sibling — the interface defect ASM-25
  refuses for a returns-based rule, one axis over (D-19, `rules.md` §5).
- **Dividing by the starting stack alone.** It bounds the reward by the seat count and not by 1
  (§2), so the six-seat reward keeps an O(5) range and the step it produces is five times the one
  this change exists to reach (ASM-45).
- **Dividing by the hand's own pot.** The pot at a terminal decision is a fact of the hand rather
  than of the game, differs between the two seats of one hand, and is 0 whenever a hand ends without
  a pot — so the reward would be incommensurable between two hands and undefined in a corner, which
  is precisely what ASM-28's "a normaliser that is not the game's own" refuses.

## 4. What it costs: nothing structural

No encoder, no layout, no observation, no head, no container geometry and no entry point changes:
the reward is one arithmetic on a number the engine already places, selected by a catalogue token
(`training`'s `REWARDS` table). The catalogue record keeps its three keys — `name`, `reward`,
`normaliser` — so no published record grows; the container's **required `utility` field** carries the
new name inside format 3, which is the version it already is; the **18 shipped containers**,
`checkpoints/evidence/`, `tables/` and both deep runs are untouched and are never compared with a
model trained on another scale (`utilities.md` §6, D-20, ASM-5). The map stays at **50 endpoints** and
no module's harness ceiling moves (`e2e-surface.md` §4, brief §5).

**The existing members are provably untouched**, which is the other half of "cost-free": the two
arithmetics of §2 of `utilities.md` are not edited, the catalogue's first member stays first, and a
`net-chips` run reproduces a baseline captured **before** this change **field for field** — every
numeric block, the census, the chips and each container's decompressed `metadata.json` and
`parameters.npy` — with only the two fields the harness itself injects normalised identically on both
sides: the `timings` block's wall clock and the checkpoint paths under the run's own write root. Those
two, and a container's zip entry stamps, are **not reproducible run to run** — measured so on two
pre-change runs of the one configuration — so the claim is field-for-field and member-for-member and
never byte-for-byte, which no run of this tree can deliver (ASM-46, `protocol.md` §2, §8).

## 5. Reporting: the chips stay raw

A record's chips never come from the reward. The greedy block carries one `net_chips` entry per hand,
read off `engine.payoffs` — the game's own zero-sum outcome — and a cell's chips come from the match
payoffs (`records.md` §15, `greedy.md`). So under this utility a run's **chips per hand is a raw-chip
figure on the same footing as every recorded multi-seat cell** (−1.8 against `net-chips`, −1.0 to
−8.2 under `stack-shortfall`, `grid-result.md` §2), and a reader can put them side by side without
converting anything. Both are kept and neither is derived from the other: **the reward says what the
model was asked to maximise, the chips say what it earned** (D-20, `utilities.md` §9, ASM-29). What
changes is only what a record *names*: the utility a model was trained under, which every record that
can carry a member already carries (`utilities.md` §7).

## 6. The test: six cells

Six cells at the six-seat shape, **15,000 hands × seeds 0–2**, one variant each, backend `numpy`,
device `cpu`, the mixed pool **`pool-8386c3ef83ae48b2`** — D-6's three anchors, D-21's three folders
and the trained six-seat raiser at
`/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt`, the pool every recorded cell
of `grid-result.md` trained against (D-16, D-51, ASM-16). **Utility = `net-chips-normalised` in all six
cells**, crossing the grid's other two axes:

| axis | levels |
|---|---|
| estimator / signal | masked-Q · `double-q-learning` · `reveal-counterfactual` (D-19, D-43) |
| encoding | `flat-numeric` · `card-tokens` (D-3) |

`naive-stack` at width 36 depth 2 for the dense cells and `token-embedding` at width 50 depth 2 for
the token ones — the two architectures the D-60 instrument counted, so the reading is comparable with
the twelve cells already recorded (`grid-result.md` §2). The six runs are **separate single-threaded
processes launched concurrently**, not serialised (`normalisation.md` §6, D-55).

**Four instruments per cell, per seed**, the same four `normalisation.md` §6 declares so the numbers
are read with the same ruler: the greedy **census**; **chips per hand in raw chips** with a 95 %
interval; **‖w_in‖, ‖b_in‖ and the active-unit count in both hidden layers**, from the same pinned
oracle-free replay the recorded grid used; and **state dependence** as distinct score vectors over
distinct observations on that one replay. Plus, for **one** dense cell at seed 0, a **snapshot
trajectory**: a 3,000-hand companion run of the same configuration, whose ten equally spaced snapshots
report ‖w_in‖ at hands 300 / 600 / 1,500 / 3,000 — the direct reading of D-65's explosion, which the
records carry at 11.0 → 298.6 → frozen (ASM-18, D-65).

**The comparison anchors are recorded, not assumed**: `net-chips` at ‖w_in‖ **298.6** with **0** active
units in the second hidden layer, ‖b_in‖ 78.87, ‖w_out‖ 312.0 and one score vector over thousands of
observations; `stack-shortfall` at ‖w_in‖ **8.5**, ‖b_in‖ 0.083 and 16–25 active units
(`trunk-death-rca.md`, `input-collapse-rca.md`, `grid-result.md` §2, D-60).

## 7. The prediction, pinned before the run

Stated here so the test can refute it, and not read off the result afterwards (D-29's rule, D-56):

> With the reward in `[−1, 1]`, one step is `lr·δ·x` ≈ **1e-3** rather than 0.6, so **‖w_in‖ should
> stay small — order 10, not order 300 — the trunk should keep live units in both hidden layers, and
> the policy should become state-dependent** (distinct score vectors tracking distinct observations).
> None of the six `net-chips` cells achieved any of the three.

**What a PASS means, and what a FAIL means.** If the weights stay small, the units stay alive and the
policy reads its input, D-65's cause is confirmed and the fix works. **If the trunk dies anyway, the
cause was not the scale and that is the result** — recorded as such, with nothing retuned to rescue it
(D-65, D-6). The chips are reported and never thresholded: at 15,000 hands with three seeds no chip
difference resolves, and the prediction makes no claim about one (`grid-result.md` §5, D-56).

## 8. The measurement

*This section is filled from the artefacts once the six cells have run: the per-seed census, chips in
raw chips with intervals, ‖w_in‖/‖b_in‖/active units per layer, distinct score vectors, the snapshot
trajectory, the `net-chips` reproduction, and the verdict. The run records live under
`/tmp/reward-scale/records/<cell>/seed-<k>.json` and the instrument files beside them (ASM-23).*

## 9. What this document does not say

No claim that a normalised reward **wins chips**: it changes the learner's scale, not the game, and a
model trained under it is not thereby a stronger player (D-20, `utilities.md` §9). No claim beyond
three seeds and one budget: the seed lottery dominates this project's censuses and the estimator axis
has never separated from it (`grid-result.md` §4, `strata/records/attractor-sweep.md`). And no claim
about the rungs: `R4`/`R5`/`R6` stay declared and unmeasured, and the ladder's six registry rows keep
declaring `net-chips`, so no shipped artefact is re-measured by this change (D-62, `ladder.md` §3).
