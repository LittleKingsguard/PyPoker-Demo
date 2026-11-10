# training — the rung registry as data, the one loop, and the edges

- **Layer:** L2 · **Module:** `training` · **Unit:** phase1 · **Rev:** 6 · **Date:** 2026-11-09
- **Owner of this file:** the registry as data (§1, §2), the one loop (§3), what a comparison holds constant and
  the R1/R2 parity rung (§4), budgets and devices (§5), the notebooks this module owns (§6), the checkpoints that
  ship (§7), the contracts at this edge (§8) and the battery invariants it carries (§9)
  (D-3, D-5, D-7, D-8, D-16, ASM-8, ASM-16, ASM-18, `battery.md` §3)
- **Rev 3:** §1's step 1 and §2 refuse a declaration the run would not honour — `declarations.md` §1–§4 owns it (ASM-7). **Rev 5:** §1 step 9 and §9's FAM-12 row name the `rules`, and `checkpoints()`'s entries carry each artefact's `rule` (D-19). **Rev 6:** §1 step 2 forwards a `pool` entry's `baselines`, §3 reads the pinned set through `evaluation.league` and §9 gains a D-21 row (ASM-32, D-21). **Rev 7:** D-29 reaches §1's steps 2, 3, 5 and 8 (the shape through the pool, the encoder, the learner, the hand and the pass), §4's fairness list and shape refusal, §5's pass budget and §8–§9 — the pass itself is `docs/L3/training/greedy.md`'s, its bound `declarations.md` §2's (D-29, ASM-38, D-28)
- **Ceiling:** 220 lines. At the ceiling, split by owner — never append

## 1. The registry is data (D-3)

There is one rollout driver, one encoder factory, one learner family, one loop and one league; a rung is a row of
data, so no rung can drift into its own copy of the loop and a seventh configuration runs without new code
(`ladder.md` §1, D-3, FAM-15). The six rows are `rungs()`'s content, in brief §2's fixed order (D-2, `ladder.md` §2):

| Rung | Its declared axis | Variants, with the kind each is built from | Primary | `carried_from` | The pool it trains against |
|---|---|---|---|---|---|
| R1 | a naive numeric encoding, hand-rolled NumPy (D-7) | `naive-numeric` (`naive-stack`) | `naive-numeric` | `None` | the three baselines alone: R1 inherits no lineage (D-16, `league.md` §2) |
| R2 | the same model in PyTorch, for the speed difference (D-7) | `naive-numeric-torch` (`naive-stack`) | `naive-numeric-torch` | `naive-numeric` | R1's last M `naive-numeric` snapshots plus the baselines |
| R3 | card tokenisation into a learned embedding | `card-tokens` (`token-embedding`) | `card-tokens` | `naive-numeric-torch` | R2's last M `naive-numeric-torch` snapshots plus the baselines |
| R4 | width against depth, at one budget | `wide` (`wide`), `deep` (`deep`) | `deep` | `card-tokens` | R3's last M `card-tokens` snapshots plus the baselines, frozen for both arms |
| R5 | dense against sparse connectivity, at one budget | `dense` (`deep`, `sparsity` 0), `sparse` (`sparse`) | `dense` | `deep` | R4's last M `deep` snapshots plus the baselines, frozen for both arms |
| R6 | a residual path against none, at R5's depth | `residual` (`residual`), `plain` (`plain`) | `residual` | `dense` | R5's last M `dense` snapshots plus the baselines, frozen for both arms |

R1–R3 are single-variant rungs; R4–R6 carry a pair, because a rung named for a technique proves nothing on a
curve alone and the pair is the rung's own control (ASM-9, D-6, D-3). The **primary** is the variant the next rung
inherits and the one whose row the next rung's table carries (D-16, `ladder.md` §2). Each pool declares `m` = 5 and
`frozen` = true — the league's M — and no declaration exceeds it (D-16, ASM-14, `league.md` §2). The window is the
**primary** variant's snapshots of the inherited rung, that being the lineage the next rung is carried from; a
configuration in no registry reaches the same loop through `run` as data (`ladder.md` §2, §3, D-3, FAM-15).

## 2. The configuration schema, and the settings that are the axis (D-3)

`rung(name)` and a caller's configuration are one schema (`ladder.md` §3), and `records.md` §2 fixes a variant
entry's required keys; this module's own keys name no behaviour (`records.md` §1, D-13). Two declarations are fixed
here, and each is what a battery can assert:

- **The kind vocabulary is `agents.learners()`'s seven kinds and no other spelling** (`agents/surface.md` §3,
  `records.md` §2). `dense` and `naive-numeric` are *variant names*: R5's `dense` arm is the `deep` kind at
  `sparsity` 0. So the kind enters a comparison only through the representation family it consumes, and the
  *settings* — width, depth, sparsity, residual — are the axis (`agents/surface.md` §3, D-3, `surface.md` §5).
- **A pair is matched before it is trained.** Two entries of one rung declare one `hyper` set, one sample budget, one
  parameter budget, one seed set, one device, one `snapshot_every` and one `table`, and a pair declaring two values for
  any of the seven is refused rather than silently read from its first entry (`declarations.md` §4) — `learning_rule`
  is no longer one of them, because D-19 makes the rule an axis a pair may differ on (`rules.md` §8). Their widths,
  depths, sparsity and residual are chosen so `agents.param_count` of the two learners agrees within ±2% of 10,000
  (ASM-7, ASM-8, ASM-10, `ladder.md` §4, §6). The literals are the registry's data, fixed with `src/training/`; the
  property is this document's, and FAM-3 measures it (ASM-10).

`snapshot_every` is the declared budget ÷ 10 hands and a configuration omitting it is recorded at that interval; one
declaring another number is refused (`declarations.md` §2, ASM-18); one omitting `table` is recorded at `live`, the
budget a talk produces (`league.md` §6). A variant's `learning_rule` and its `utility` are read and forwarded to `build_learner`, and a name
either catalogue `agents.learners()` publishes does not carry is refused (`declarations.md` §1–§2, `rules.md` §2, `utility.md` §1, D-19, D-20).

## 3. The one loop every rung is a configuration of (D-3, D-16)

One pass of `run`, in this order, for any configuration:

1. **Resolve, refusing what the run would discard.** A name goes through `rung`; a configuration is used as it stands
   once `declarations.md` §2's declarations are read — one it declares and the run would not honour is refused here,
   before the first hand and before anything is written (§2, ASM-7, ASM-18, `e2e-surface.md` §2).
2. **Freeze the pool before the first hand.** The `pool` declaration goes to `evaluation.build_pool` — its optional `baselines`
   sequence forwarded as it stands, so a configuration that names a folder trains against it and one that names none keeps the
   membership, the order and the id it has today, and its **shape** forwarded too, so the pool is one shape's and a member of
   another is refused by name — and
   `evaluation.pool_members` reads back the id, the bound, the `frozen` flag, the shape and the ordered members. A declared
   version whose checkpoint the repository does not carry is not a member: the record states the membership it used,
   and a pool never pretends a version it could not load (`protocol.md` §5, `records.md` §8, ASM-32, D-21, `shapes.md` §3, D-29). It is frozen and never
   advanced during a run — rolling is `evaluation.offer` between runs (D-16, ASM-16, `evaluation/surface.md` §7).
3. **Build the variant.** `features.build_encoder` for the entry's `encoding` **and the run's shape**, cross-checked against its kind by
   `features.observation_spec`, and, per seed, `agents.build_learner` with the entry's `backend`, `architecture`,
   `learning_rule` and `utility`, the run's seed as the learner's own seed, that encoder and that shape — so its head is
   the shape's width and a six-descriptor learner trains without a branch on the game (`agents/surface.md` §4, `utility.md` §1, `e2e-surface.md` §3.3, `utilities.md` §5, `protocol.md` §4, `sizing.md` §6, D-20, D-29).
4. **Seed the work, not the arm.** Hand *i*'s deal seed and its opponent seed are functions of the run seed and *i*
   alone, so both arms of a pair play the same hands in the same order against the same opponents and differ only on
   their declared axis (`ladder.md` §5, ASM-8, D-7); the derivation is L3's and draws from no stream
   (`protocol.md` §4, ASM-2). The opponent is `evaluation.opponent(pool, opponent_seed)` (D-16, §8 of that surface).
5. **Play the hand through `engine`.** The learner's side is a policy assembled from this module's granted calls —
   `features.encode`, `features.legal_indices`, `agents.act`, `features.decode_action`, the last decoding in the run's
   shape — because `agents.as_policy` is the pass's call and not the training-time decision (`module-map.md` §2,
   `agents/surface.md` §6, `features/surface.md` §6, §8, §9). The hand is
   `engine.play_hand(hand_seed, seat-0 policy, seat-1 policy, shape=shape)`, so the run plays **its own shape** and not
   the engine's default, with the two sides swapped hand by hand because seat 0 holds the button in every hand
   (`engine/surface.md` §4, §10, D-2, D-29).
6. **Learn once per hand.** The episode's decisions for the learner's own seat, in decision order, become
   `records.md` §4 transitions and go to `agents.learn`; the batch is the caller's order and neither sampled nor
   shuffled, which is what lets two arms declare one sample order (`agents/surface.md` §7, ASM-7, `ladder.md` §5).
   The terminal reward is **the variant's utility's** reward — the seat's net chip delta under `net-chips`, the
   normalised shortfall delta under `stack-shortfall` — computed in this module's transition record and never in
   `agents.learn` (`utilities.md` §4, D-20, ASM-12), and its `td_error` is the curve's learning signal (`records.md` §5, `agents/surface.md` §7, `protocol.md` §1).
7. **Snapshot every `snapshot_every` hands** with `agents.save`, recording the path it returns: ten snapshots at
   equal intervals, of which the window retains the last M (ASM-18, `agents/surface.md` §8, `ladder.md` §6).
8. **Write the final model, then play the pair's greedy pass.** At the budget's end `agents.save` writes the final
   model, the pair's curve closes at one point per snapshot step with the spread across seeds (`records.md` §12,
   `protocol.md` §1, D-6), and the run then plays `records.md` §15's pass: its own sample again, against the same
   frozen pool and at the same seed, with `agents.as_policy(learner, encoder, seed, "off")` — the masked maximum and the
   tie-break alone, no generator drawn from — recorded under `greedy`. It is **the one decision stream a run retains**,
   and the block is a function of the checkpoint the record names (`sizing.md` §4, §7, ASM-38, `greedy.md` §1–§3, D-28).
9. **Assemble and return `records.md` §12's record** — curves, pool, checkpoints, seeds, budget, device, parameter
   budget, table, timings, `game` and `greedy`, plus `variants`, `rules` and `utilities`, which name each variant's rule and utility and the run's two sets (D-19, D-20, D-29) —
   and nothing beyond it: a run claims no table position and fits no rating (`module-map.md` §3, `records.md` §13, `surface.md` §4).

The nine steps are the same for R1 and for a configuration written to no design document; only the data differs, and that is the whole of D-3 (`ladder.md` §1, FAM-15).

## 4. What a comparison holds constant, and R1 against R2 (D-7)

`fairness` reports this list for every adjacent pair and every intra-rung pair (`ladder.md` §4, `surface.md` §5, D-3).
An adjacent pair's one axis is the **later** rung's declared axis — the rung that varies against the lineage it
inherits — because R4's primary and R5's dense arm may declare one stack and the pair still names the axis R5 is for.

- **the shape**, named as a constant of the pair and never as an axis: one `game` for every rung (D-2, `shapes.md` §1, §6, D-29);
- that shape's game configuration from `engine.game_config` and its action vocabulary from `features.decode_action` —
  three descriptors in the fixed-limit shape, six in the no-cap one (D-2, `engine/surface.md` §3, `features/surface.md` §7, `sizing.md` §3);
- the readout facts, identical for every encoding: the ladder changes how the information set is represented and
  never what the agent may know (D-3, `e2e-surface.md` §2);
- the reward: each side's declared utility's reward at the terminal decision, applied in the transition step (`utility.md` §2, ASM-12, D-20);
- the **sets** of learning rules and of utilities the two sides declare, every hyperparameter, the optimiser family and the schedule (`rules.md` §8, `utilities.md` §8, ASM-7, D-20);
- the sample budget in hands and the parameter budget within ±2% (ASM-8, ASM-10);
- **the frozen pool**: the same id, the same members and the same window for both arms of a pair (D-16, ASM-16);
- the seed set, and the table budget with its hand count per cell and its seat alternation (D-16, ASM-14);
- the checkpoint policy and the device policy (ASM-5, ASM-18, D-8).

**The frozen pool, read exactly.** An intra-rung pair's two arms declare one pool id, and two differing ids are a
refusal (`surface.md` §5). An *adjacent* pair's rungs cannot share one: a rung's pool is the previous rung's window, so
R2's contains R1's snapshots while R1's is the baselines alone, and `fairness` reports each arm's id, `same: None`, and
the pool the pair is compared *on* (`ladder.md` §2, `league.md` §2, D-16, ASM-16). A pair whose two sides name **two
shapes** is refused before any axis is read, naming both: a shape is a property of a configuration and never a rung's
axis, so such a pair is not a comparison at all (`shapes.md` §1, §6, D-3, D-29).

**R1 against R2 is the backend-only parity rung (D-7, `ladder.md` §5).** They declare one architecture record key for
key, one encoding, one update rule and one sample order, so they are handed the same deals, and being one window
apart they are compared on the membership both name: R1's three baselines alone, which R2's window holds as well —
the same-work check plays there, and both arms must choose the same actions on the same seeded hands (D-7,
`league.md` §2). Their evidence is throughput and wall clock per hand, from the two records' `timings` and from
`harness.timings`, never an assertion that a clock was beaten; R2 still reports the table its own pool yields, labelled
a parity comparison, where a large skill difference is a defect and not a finding (D-7, D-8, ASM-15, D-16, FAM-13).

## 5. Budgets and devices (ASM-8, D-8)

| Quantity | Live run | Shipped run |
|---|---|---|
| Hands per variant per seed | 1,000 | 200,000 (ASM-8, D-8) |
| Seeds | `0, 1, 2`, recorded in every run record (`protocol.md` §2) | the same three |
| Snapshots per run | 10 at equal intervals, `snapshot_every` = budget ÷ 10; the window retains the last M (ASM-18) | the same rule |
| Table budget of the row | `live`, 120 hands per cell (ASM-14) | `full`, 1,500 (ASM-14) |
| Parameter budget of a pair | 10,000 ±2%, as declared (ASM-10) | the same |
| Greedy pass, per variant per seed | the run's own budget — 1,000 hands at the live budget — and at most 2,000 hands and 24,000 decision records, refused beyond and never truncated (`sizing.md` §4, `records.md` §15, ASM-38) | the same bound: a 200,000-hand run would be **refused**, because its pass could not be recorded at all |

The comparison is matched in **samples, not wall clock**: every rung trains the same number of hands, so a slow
engine costs the clock and never the comparison's fairness (ASM-8, ASM-15, C-C2). The live budget keeps a rung at a
few minutes in a talk and the shipped checkpoints show that training time matters; both use one protocol and one
membership, so the sample count and the cell size are what separate them (D-8, `ladder.md` §6, D-6). The pass is
**sample-matched** to the run's own budget, so a ten-hand case costs twenty and no case pays a fixed 1,000
(`sizing.md` §4, ASM-38, `greedy.md` §1).

`devices()` reports what the platform offers and the device a run uses by default (`surface.md` §6, `devices.md` §1). A
run started by this workflow is CPU-bound: the sandbox denies the read-write opens a driver performs, so no delegated
layer reaches the GPU, and a GPU run is the user's, outside the sandbox — whose record says so and records its device, so
the two are never confused — and no shape changes it: one device policy serves both (D-8, `strata/platform.md`, `protocol.md` §6, D-6, D-29).

## 6. The notebooks this module owns (D-5)

`notebooks/` is this module's (`ladder.md` §7, `module-map.md` §5). **The contract is `ladder.md` §7's, in full**, and is
not restated here: one notebook per rung, named for its rung, story in markdown and cells that call the declared entry
points of `training` and `evaluation` only, with `engine`, `features`, `agents` and `harness` unimportable and no loop,
model, encoder, metric or match inlined (D-5, D-16). `r1-naive-numpy.ipynb` ships; a notebook needing something the six
entry points do not expose returns as an `ADJUDICATION` rather than inlining it (`modules.md` §3, D-12).

## 7. The checkpoints that ship, and the window they are (D-16, ASM-18)

**`shipped.md` §7's**, split out at this file's ceiling with the numbering kept: what the shipped `checkpoints/` set is,
that a run writes under the write root and reads under the declared root, that what ships is the retained set plus each
variant's final model per seed, what a window is in lineage order, that a declaration richer than the bound is windowed
and not refused, what a loaded version chooses, and that a lineage checkpoint the repository does not carry leaves the
pool short (`write-root.md` §1–§3, `records.md` §7, ASM-5, ASM-18, `protocol.md` §5). The **greedy pass adds no artefact
there**: it is played after the pair's final model is written, writes nothing, and the block is the record's
(`shipped.md` §7, `docs/L3/training/greedy.md` §1, ASM-38, D-29).

## 8. Contracts at this edge (D-13, `module-map.md` §2)

Calls go one way along `engine` → `features` → `agents` → `evaluation` → `training` → `harness`; each row below is
what this module requires of a module it calls, or grants to the one that calls it (`module-map.md` §2).

- **`evaluation`** — five calls and no sixth: `protocol` (the evidence contract the record is read against),
  `league` (M and both cell sizes), `build_pool` (the freeze), `pool_members` (the pool record and the id the run
  carries) and `opponent` (the per-hand draw) (`evaluation/surface.md` §3–§8, D-16, ASM-16). This module never calls
  `match`, `matrix`, `rating`, `report`, `offer` or `policy_from`, and never measures a cell (`module-map.md` §3).
- **`agents`** — five reads and **one policy builder**: `learners` (the rule and utility catalogues a variant's members are refused against, D-19, D-20),
  `build_learner` (complete when built, under the rule, on the reward and in the shape the entry names), `act` (the training-time decision), `learn` (the update and its
  `td_error`) and `save` (the path it wrote) (`agents/surface.md` §4, §6–§8, §11, `utility.md` §1, ASM-7); and
  `as_policy(learner, encoder, seed, "off")`, the **only** exploration-off surface this module uses, because a run's one
  retained decision stream must be a greedy one and `act` is the schedule's (`sizing.md` §4, `shapes.md` §4, `greedy.md`
  §1, D-29, ASM-38). Capacity is `param_count`, which is not granted, so a run reports a declared budget and no
  measurement (ASM-10).
- **`features`** — five calls: `build_encoder` (this module owns the encoder, because `agents` cannot build one, and it
  is built for the run's shape), `observation_spec` (the cross-check that keeps a declared size and an observed one
  equal), `encode`, `legal_indices` (the mask) and `decode_action` (an index back to the engine's descriptor, decoded in
  the run's shape's vocabulary) (`features/surface.md` §4–§9).
- **`engine`** — four calls: `game_config` (the header's game, for the run's shape), `new_hand` (the single seeding point
  and the same-work check's deal), `play_hand` (the episode the transitions come from, dealt on that shape) and `payoffs`
  (the zero-sum chips the reward is) (`engine/surface.md` §3, §4, §9, §10, D-2, ASM-2, ASM-12, D-29).
- **Upward** — `evaluation.report` receives this module's run record as data with the families attached and a D-5
  notebook reads the six entry points; no module calls `training`, so its record is the whole interface it offers
  (`records.md` §13, `evaluation/surface.md` §13, `module-map.md` §2, D-13).

## 9. The battery invariants this module carries (`battery.md` §3)

| Family | The entry points it drives | What is asserted here |
|---|---|---|
| FAM-3 | `rungs`, `rung`, `fairness` | six rungs in brief §2's order; each adjacent and each intra-rung pair differs on exactly one declared axis and is matched on budget and parameter count; R4, R5 and R6's two arms name one frozen pool id, and every rung declares the pool it trains against (D-3, D-16, ASM-16) |
| FAM-4 | `run` | one seed, one configuration and one pool give identical curves and one pool id twice; a different seed gives different curves; the seed set and the budget used appear in the record (ASM-2, D-16) |
| FAM-12 | `run`, `checkpoints` | a run writes ten snapshots and its final model and names the retained M beside that pair's final; the index carries each variant's final model, each entry's `rule` (FAM-12.8) and its `utility` (FAM-18.6), and lists no artefact twice (ASM-5, ASM-18, D-19, D-20) |
| FAM-13 | `rungs`, `rung`, `fairness`, `run` | R1 and R2 declare one encoding, one architecture, one rule and one budget and differ only on the backend; both run records carry throughput, the D-7 speed evidence (D-7, D-8, `ladder.md` §5) |
| FAM-15 | `run`, `fairness`, `rung` | a configuration and a membership in no design document run through the same loop and report their own axis; `rung` refuses a name the registry does not carry (D-3, D-16) |
| FAM-16 | `rung`, `run`, `fairness`, `checkpoints` | the four `general` rows, one invented instance apiece — a rung name, a budget and seed, a variant pair, an artefact set — from this surface alone (D-15, `battery.md` §4) |
| FAM-6 | `run`, `fairness` | a configuration whose `pool` entry declares catalogue baselines trains against a pool holding them — one `baselines` row and one declared `0` per baseline it holds — and one that declares none trains against the pinned three alone, with the pool id it had (ASM-32, D-21) |
| FAM-19, FAM-20 | `run`, `fairness`, `rung` | the record names the shape it played and a `game` outside the catalogue is refused naming it and the declared names; a `no-limit-100` run trains and passes end to end on six descriptors and 200 chips in play; the pass's block carries `mode: off` and is reproducible from the tuple; both bounds are refused with the counts; no training decision is retained; and `fairness` names the shape and refuses a pair of two (D-29, ASM-38, D-28, `shapes.md` §2–§3, `sizing.md` §4) |

FAM-3's matched capacity is measured through `agents.param_count` by the battery, never by a run record, because a run measures no capacity (ASM-10, `surface.md` §4); no invariant here asserts a result, a version outranking a baseline being `evaluation`'s to report (D-6, `battery.md` §5); and FAM-18's utility arithmetic is the unit battery's (`battery.md` §5, `utility.md` §6). FAM-19's and FAM-20's **unit** cases are `tests/training/test_shapes.py` and `test_greedy.py`, and the shape join — the restated catalogue against `engine.game_shapes()` and `features.action_space` — is `tests/integration/training/test_shape_join.py` (`shapes.md` §4, D-13, D-29).
