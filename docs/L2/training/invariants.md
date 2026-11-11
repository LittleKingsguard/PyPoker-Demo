# training — the battery invariants this module carries

- **Layer:** L2 · **Module:** `training` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-10
- **Owner of this file:** `loop.md` §9's subject — the case families that drive this module's six entry points, what each
  one asserts here, the matched capacity the FAM-3 row reads through `agents.param_count`, and the two joins the
  families make across modules: the shape catalogue and the pass's own bound — split out of `loop.md` at that file's
  ceiling with the numbering kept (`battery.md` §3, §4, §5, D-3, D-15, D-16)
- **Reads:** `loop.md` §1–§8 (every row below rests on them), `surface.md` §4–§7, `battery.md` §2–§5, `records.md` §8,
  §12, §15, `shapes.md` §2–§8, `seats.md` §4–§6, `sizing.md` §4, `docs/L1/assumptions.md` (ASM-5, ASM-10, ASM-32,
  ASM-38, ASM-42, ASM-43, ASM-44)
- **Ceiling:** 50 lines. At the ceiling, split by owner — never append

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
| FAM-19, FAM-20, FAM-21 | `run`, `fairness`, `rung` | the record names the shape it played, and a `game` outside the three-row catalogue is refused naming it and the three declared names; a `no-limit-100` run trains and passes end to end on six descriptors and 200 chips in play, and a `six-seat-no-limit-100` run on six descriptors and 600; the hand is `episode._hand`'s, with the learner at `index % seats` and `seats − 1` distinct opponents on a shape with more seats; the pass's block carries `mode: off`, is reproducible from the tuple and is bounded by **its own shape's** 1,000 records a slot — 24,000 / 66,000 / 98,000 — refused with the count reached, the bound, the shape and its capacity; no training decision is retained; `fairness` names the shape and refuses a pair of two; and a six-seat run's record is complete while no matrix, rating or report is producible from it (D-28, D-29, D-33, ASM-38, ASM-42, ASM-43, ASM-44, `shapes.md` §2–§3, §8, `seats.md` §4–§6, `sizing.md` §4) |

FAM-3's matched capacity is measured through `agents.param_count` by the battery, never by a run record, because a run
measures no capacity (ASM-10, `surface.md` §4); no invariant here asserts a result, a version outranking a baseline
being `evaluation`'s to report (D-6, `battery.md` §5); and FAM-18's utility arithmetic is the unit battery's
(`battery.md` §5, `utility.md` §6).

FAM-19's and FAM-20's **unit** cases are `tests/training/test_shapes.py` and `test_greedy.py`, and the shape join — the
restated catalogue against `engine.game_shapes()` and `features.action_space` — is
`tests/integration/training/test_shape_join.py` (TRNJ-11.1: the names, their order and each shape's descriptor count).
Since D-33 that restatement is **three** tables and not two: three names, three descriptor counts and each shape's
history capacity (`shapes.md` §8, ASM-42, `declarations.py`'s `SHAPE_HISTORY`), whose authority is the catalogue row's
own `history` key and which no case inside this module can check about itself, the map granting `engine.game_config`
and no `game_shapes` (`module-map.md` §2, `shapes.md` §4, D-13, D-33). FAM-21 is D-33's family and drives the widened
block, the six-seat hand, the draw without replacement and `evaluation`'s four refusals, so the capacity a run reads
is the catalogue's own row and the refusals are the ones `seats.md` §5 states (`battery.md` §3, `seats.md` §5–§6).
