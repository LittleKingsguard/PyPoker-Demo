# PyPoker-Demo — normalisation into [0, 1], and the mechanism grid

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-11
- **Owns:** every input value both encodings emit, the bound each slot carries, the one saturation
  rule, the refusal for a fact that cannot be normalised, the invariant and where it is asserted,
  and the twelve-cell mechanism grid that measures what normalisation changes (D-61, D-62)
- **Ceiling:** 210 lines. One document rather than two because the grid exists to measure this change
  and a second file would restate the map to explain the instrument (D-61, D-62)

## 1. What this change is, and what it is not

D-60 measured the input path dead: `flat + net-chips` keeps **0 of 36** trunk units alive and
`token + net-chips` **2 then 1 of 50**, so those models emit their output bias and their policy is a
constant function. The measured chain runs through input magnitude — O(100) rewards drive input-weight
norms to 313 and input biases to 82, every pre-activation sits on the negative side, and ReLU zeroes
the hidden vector (`input-collapse-rca.md`). D-61 attacks the input term of that chain: both encodings
emit values in [0, 1], and every slot that can saturate does so by a documented rule.

**The dense family is already divided; what is new for it is the declaration and the bound.** Every
magnitude slot of `flat-numeric` is a count over its shape's own divisor (`flat-numeric.md` §4), and
those divisors are per shape because the shapes' chips in play differ (`shapes.md` §2, ASM-6). What
the dense family did not have is a stated numerator and denominator per slot, a saturation rule, or
any assertion that a value above the denominator is impossible to emit (§2, §4, §5). It has all three
now.

**The token family is where the change bites.** Its slots are categorical ids, not magnitudes
(`card-tokens.md` §3-§4), so its bound cannot be a divisor: it is imposed at the only place the token
path has a magnitude at all, the embedding row the trunk reads (§3). This is the half of D-61 that
changes what a trained token model computes.

**Declared plainly:** the layouts keep their widths, so every container still loads and every width,
head and `param_count` stands (`shapes.md` §8, ASM-44) — but a slot's **value means something
different**. Pre-change checkpoints are therefore not comparable with post-change ones; the shipped
**18** containers, `checkpoints/evidence/`, `tables/league-full.json` and both deep runs stay exactly
as filed and are read-only history (D-61, `shapes.md` §5). The fixed-limit byte-identical gate is
**superseded for this change only**, by D-61's instruction to alter the input representation, and it
is in force again for every later change that does not alter it (D-61).

## 2. The dense map — numerator, denominator, saturation, per shape

One row per block of `flat-numeric`'s declaration table, in the declaration's own order
(`declarations.py`, `encoder.md` §4). The denominator is the shape's published normaliser and no
other number: `engine.game_shapes()` publishes the five, `features` restates them, and the join
battery holds the two statements equal (`shapes.md` §2, `e2e-surface.md` §2).

| Block (slots) | Numerator | Denominator — `fixed-limit-20` / `no-limit-100` / `six-seat-no-limit-100` | Saturates |
|---|---|---|---|
| `street` (4) | 1 at the acting street | 1 — an indicator | no |
| `seat` (2 or 6) | 1 at the acting seat; on a two-seat row the seat's index | 1 on the one-hot rows, and the index over the seat count less one on the two-seat pair | no |
| `hole` (34) | 1 for the card's rank and 1 for its suit | 1 — indicators (`flat-numeric.md` §3) | no |
| `board` (85) | 1 for each dealt card's rank and suit | 1 — indicators; an undealt slot is 0 | no |
| `stacks` (2 or 6) | the seat's stack | the shape's **starting stack**: 20 / 100 / 100 | **yes** |
| `pot` (1) | chips in the pot | the shape's **chips in play**: 40 / 200 / **600** | **yes** |
| `to_call` (1) | chips to call | the shape's starting stack: 20 / 100 / 100 | **yes** |
| `limit` (2) | the bet size in force; the bet-or-raise actions this street | the amount normaliser 4 / 100 / 100; the count normaliser (the cap) 4 / 50 / 50 | **yes** |
| `history` (3 × capacity) | 1 at each applied action's kind | 1 — indicators; the pad is 0 (`flat-numeric.md` §5) | no |

**Why the denominators are the ones they are.** A hand's pot plus its stacks is the shape's chips in
play at every decision, so `pot` divides by exactly the largest value it can take and no seat can hold
more than its starting stack inside a hand — a stack only ever moves into the pot (`readout.md` §2,
`seats.md` §2). The two per-seat blocks are therefore bounded with no clamp reached by any hand the
engine can deal, and the six-seat row's `600` is what makes its pot slot a normalisation instead of a
clip (`seats.md` §2, `sizing.md` §5).

## 3. The token reading of "bounded"

An id is a label, not a magnitude: `card-tokens` emits one id per slot, each from a total bucket
ladder or from a fixed vocabulary (`card-tokens.md` §3-§4, `declarations.py`). `2c` is id 1 and
`Ah` is id 52; neither is "larger" than the other, so asking an id to lie in [0, 1] asks the wrong
question of the wrong quantity. **The bound is therefore stated in two parts, and the second is the
one that reaches the network:**

1. **The label is in range.** Every id lies in the shape's declared vocabulary — 96 on the two-seat
   rows, **102** on the six-seat one, whose seat block emits ids 96-101 (`seats.md` §3, ASM-44). The
   pad is id 0 and is the only id outside a block's own ladder (`card-tokens.md` §3).
2. **The value the trunk consumes is in [0, 1].** The token path's only magnitude is the input block:
   the trunk reads the **mean of the embedding rows the ids address** (`architecture.md` §2, §6). Each
   row is now read through the **bounded embedding**: `row = (1 + tanh θ_id) / 2`, so every row lies
   in [0, 1] and so does any mean of rows, **whatever the parameters do**. The interval is closed in
   float64 and the ends are reachable: `tanh` rounds to exactly ±1 from |θ| ≈ 19, so a table driven
   far from zero feeds the trunk exactly 0 or exactly 1 — the bound is a ceiling, and what it costs is
   resolution rather than an escape (`docs/L3/agents/input-read.md` §2).

**Why a squash and not a divisor.** The token family has no numeric slot to divide, and the quantity
D-60 measured blowing up is the embedding row itself — the table is where the reward scale lands
(`input-collapse-rca.md`). A divisor would need a bound the project cannot state for a learned table;
the squash bounds the read for **any** finite parameter value, keeps the table's width and therefore
`param_count`, `observation_size` and the matched-budget comparison (ASM-10), and is one monotone
function in both backends' forward passes with its derivative in the backward pass
(`rule.md` §3). Rejected: one-hot expanding a card into its 17 dense slots, which changes the family,
the declaration table and every container's width (`encoder.md` §4); and a clamp on the table, which
zeroes a gradient exactly where the reward scale has driven it (`rule.md` §3).

**What this costs the token family:** the embedding's output is compressed, so a row that has run far
from zero carries little resolution — the saturation of a `tanh`, declared here rather than discovered
later. The instrument that shows whether it is enough is the active-unit count of D-60, reported per
cell by §7.

## 4. Saturation, and the refusal

**One saturation rule, one place.** A magnitude slot — the five of §2 that can reach their denominator
— emits `min(1, numerator / denominator)` and **never** a value above 1. A readout whose numerator
exceeds its shape's denominator therefore saturates at exactly `1.0`: it is a value the engine cannot
produce (`readout.md` §2), it stays encodable rather than becoming a refusal, and the observation
records that the slot is at its ceiling rather than silently carrying a magnitude the trunk was never
trained to read (`flat-numeric.md` §4). **This supersedes `flat-numeric.md` §4's "keeps the magnitude
and is never clipped"** for those five slots and for no others; the case that asserted `7 / 4 = 1.75`
becomes the case that asserts `1.0` and the saturation, which is a stronger assertion about the same
block, not a weaker one (D-61, `battery.md` §3).

**The refusal by name.** A shape row that carries **no denominator** for a magnitude block is refused
when the declaration is built — `build_encoder` and `encodings` alike — as this
module's `InvalidReadout`, naming the **block**, the **missing normaliser key** and the **shape**, and
never scaled by a substituted denominator, defaulted or silently built (`errors.md` §3, `encoder.md` §4).
No declared shape reaches it — all three declare the five normalisers (`shapes.md` §2) — so it is a
structural guard that keeps a fourth row from emitting an unbounded slot, and it is asserted at the block
level in `tests/features/` rather than left untested (D-11, `battery.md` §5). Its second half matters
more than it looks: before this guard the dense path raised a bare `KeyError` while the **token** path
built silently on a row missing a key — the quiet failure, which is the one a refusal exists to prevent
(D-13).

## 5. The invariant, and the battery that asserts it

**INV-1 (dense).** Every slot of every observation `features.encode` emits, on every declared shape,
lies in [0, 1]. **INV-2 (tokens).** Every slot of every token observation is an integer inside the
shape's vocabulary, and the value the input block consumes — the mean of the addressed rows, read
through the bounded embedding — lies in [0, 1] (§3). The two together are D-61's invariant, and they
are **added**: no existing assertion is removed to make room for them.

Where each half is asserted, and why there:

- **`tests/e2e/` FAM-24** — the layer-level half, through declared surfaces only (`battery.md` §2): a
  sweep of real hands over all three shapes and both encodings asserting `max(observation) <= 1` and
  every id inside the vocabulary; the saturation case of §4, where a readout above its denominator
  encodes to exactly `1.0`; and a learner of each family built and decided at its shape's own width
  (`e2e-surface.md` §2).
- **`tests/features/`** — the per-block half: every magnitude block's denominator is its shape's
  published normaliser, at the normaliser the slot reads `1.0`, above it it reads `1.0` and no more,
  the supersession of §4 is stated where `flat-numeric.md` §4 is tested, and the refusal of §4 is
  exercised by doctoring a row's denominators — which is the only way to reach it, since no declared
  row omits one (`battery.md` §5).
- **`tests/agents/`** — INV-2's second part, which no e2e surface exposes: the forward cache's input
  is the mean of rows read through the squash, a table set to magnitudes far past the band still feeds
  the trunk a value in [0, 1], and the backward pass carries the squash's derivative so a step on the
  table is not silently zeroed (`rule.md` §3, `architecture.md` §2). Module-internal behaviour belongs
  to the module's battery and not to the layer's, which is the boundary `battery.md` §5 draws.

**The direct measurement** runs beside the batteries, not in place of them: a sweep of hands at the
six-seat shape reports the maximum value reached in each block on each encoding, and reports `1.0` or
below everywhere (§6, D-14).

## 6. The twelve-cell mechanism grid

**D-62's grid, and the reason it is this one.** The project measured each axis alone — the utility
decisive (0 % → 78-93 % folding), the encoding a modulator under that utility only, the rule inert, the
counterfactual inert on top — and D-60 then found why the net-chip cells were inert: their trunks are
dead (`token-seven-seeds.md`, `token-double-q.md`, `counterfactual-result.md`, `input-collapse-rca.md`).
The grid asks what those singles could not: **which combinations have a living input path, and does a
mechanism matter once the network can see** (D-62).

| Axis | Levels |
|---|---|
| utility | `net-chips` · `stack-shortfall` (D-20, `utilities.md` §2) |
| estimator / signal | masked-Q (baseline) · `double-q-learning` · `reveal-counterfactual` (D-19, D-43) |
| encoding | `flat-numeric` · `card-tokens` (D-3) |

**= 12 cells × seeds 0, 1, 2 = 36 runs**, each at `six-seat-no-limit-100`, **15,000 hands**, the mixed
pool `pool-8386c3ef83ae48b2` — D-6's three anchors, D-21's three folders and the trained six-seat raiser
at `/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt` — which every cell must hold
identically, so the pool a cell trained against is the same pool and the same id in all 36 records
(D-16, D-51, ASM-16). Each cell is one variant, one architecture per encoding — `naive-stack` at width
36 depth 2 for `flat-numeric`, `token-embedding` at width 50 depth 2 for `card-tokens`, the two the
D-60 instrument counted (`input-collapse-rca.md`) — and no cell claims a matched capacity: the grid
compares mechanisms, not budgets (ASM-10, D-3).

**Four instruments per cell, per seed and pooled** (`records.md` §15, D-59, D-60):

1. the **greedy action census**, ties excluded, from the run record's exploration-off pass;
2. **chips per hand** over the same hands, with its 95 % interval — reported, never thresholded (D-6);
3. the **active-unit count** in the trunk after training: active ReLU units in each hidden layer,
   beside ‖hidden‖ against ‖b_out‖, which is the number that says whether the input path survives;
4. **state dependence**: distinct score vectors over distinct observations, replayed on one fixed
   table for every cell so the counts are comparable (`value-blindness.md`, D-59).

**The comparison is against the recorded pre-normalisation values** — `net-chips` at 0 % folding with
0/36 live units under `flat-numeric`, `stack-shortfall` at 77.5 % flat and 92.7 % tokens with live
trunks, and double-Q and the counterfactual inert (`token-seven-seeds.md`, `token-double-q.md`,
`counterfactual-result.md`, `input-collapse-rca.md`). A cell is **unusable** when its trunk has no
active unit in a hidden layer and its score vectors are constant; a cell is **alive** when both
instruments read above that floor. Every cell is reported with that column whatever it says.

**Concurrency, declared:** the 36 runs are separate single-threaded processes, launched concurrently
and capped at 20 in flight on the machine's 24 cores, so the grid is not serialised and no two runs
share a process (D-61, D-55).

## 7. What the grid cannot say, and where its outcome is stated

No threshold is pinned before it, so the grid is a measurement and not a verdict (D-29, `sizing.md` §7);
it cannot compare a cell with a pre-change number as if both saw the same input (§1); its chip intervals
span zero at this variance (D-56); it says nothing about architecture (D-62). **`grid-result.md` states
what it measured and what L1 now rules out**, the figures staying beside the run records (ASM-23).

**Two properties of the instrument, stated before its numbers are read.** A cell's runs are the same
*regime* and not the same *digits*: the deal stream drifts between processes, so two processes at one
seed part after a few dozen hands and a recorded pre-change value is reachable rather than reproducible
(ASM-2, D-6). And a `net-chips` cell can **refuse at the declared parameter band** before its trunk is
measured — with the input bounded and the reward still O(100), a surviving input path carries the
reward's scale into the weights, and D-45's band stops the run by name rather than letting it diverge, so
a refused cell has a cause and no checkpoint for the D-60 instrument to read (D-45, D-61).
