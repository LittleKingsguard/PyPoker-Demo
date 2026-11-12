# training — what a comparison holds constant

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 8 · **Date:** 2026-11-11
- **Owner:** `fairness()` — the two argument shapes, `_sides` and the shape-resolution pair (§1), the eight axes and the one rule that is L2's correction (§2), the eight reportable pairs (§3), the `constants` list with the shape first (§4), the pool report and the R1/R2 parity reading (§5), refusals and the order the shape is judged in (§6), determinism and what an absent `game` means (§7); Rev 3 adds the `rule` axis and the rule **set** (D-19); **Rev 4** adds the seventh axis, `utility`, the utility set beside it and the `reward` row (D-20); **Rev 5** makes `readout facts` eleven names (D-21); **Rev 6** adds the fifteenth constant `shape`, makes `game` and `action vocabulary` that shape's rows, and refuses a pair naming two shapes before any axis is read (`shapes.md` §1–§3, §6, `ladder.md` §4, D-29); **Rev 7** reads that constant against a catalogue of **three** shapes, so `shape` names whichever of the three both sides are on, a pair of any two is still no pair, and the vocabulary row is the shape's six on either uncapped one (`seats.md` §2, §5, `shapes.md` §8, ASM-42, ASM-44, D-33); **Rev 8** adds D-43's **eighth** axis, `counterfactual` — two training targets a pair may differ on, one word for token and field as the utility's is, resolved through `declarations.counterfactuals()` — and states that it is an axis and never a constant row (`counterfactual.md` §6, §9, `declarations.md` §4, D-43)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `registry.md` §1–§3, `loop.md` §1 step 1–2, §3, `record.md` §3, `checkpoints.md` §5, `reward.md` §1, `errors.md` §2, §4, `shapes.md` §1–§3, §6

## 1. The two argument shapes, `_sides`, and the pair's one shape

    fairness(left, right)            -> Mapping     # {pair, axis, constants, pool}
    _sides(left, right)              -> (kind, Mapping, Mapping)
    _shape(entry, configuration=None) -> str        # the shape one side is on, or UnknownShape
    _pair_shapes(left, right)        -> str         # the pair's one shape, or PairDeclarationsDiffer

A side is one of exactly two things (`surface.md` §5, `e2e-surface.md` §3.5):

- a **configuration** — a mapping carrying `variants`: `rung(name)`'s return, or a configuration written to `ladder.md` §3;
- a **variant entry** — a mapping carrying `architecture` and no `variants`: one element of a configuration's `variants` (`records.md` §2), which is what a battery passes for an intra-rung pair (FAM-3.11–3.13, FAM-15.3).

`_sides` classifies both arguments, refuses two sides of different kinds, and refuses anything that is neither — naming what it saw, never a class name this module invented. A rung *name* is not a side: `rung` resolves it first, and `fairness("R1", "R2")` is the refusal, not a lookup (`surface.md` §5, `e2e-surface.md` §2). **The two sides are compared on their primary variants** when they are configurations, because the primary is the lineage the next rung inherits (`ladder.md` §2, D-16); on their own names when they are entries. Both are reported in `pair`, under `left` and `right`. Nothing is played, built or written here (§7).

**The shape is resolved first, on the same reading the rule and the utility get.** `_shape(entry, configuration)` reads the side's `game`, else its configuration's copy, else the catalogue's first shape through `declarations.require_game` — so absence is the **default shape** and never "no claim" — and `_pair_shapes` then holds the two sides to **one** shape: a pair naming two shapes is `PairDeclarationsDiffer` naming both, raised before any axis is read (§6, `shapes.md` §1, §3, §6, D-29).

## 2. The eight axes, and the matching rule (D5)

| Axis | The compared value |
|---|---|
| `backend` | the variant's `backend` (D-7) |
| `encoding` | the variant's `encoding`, **together with** the representation family `architecture.kind` consumes — `dense-numeric` for `naive-stack`, `token-sequence` for the six token kinds (`agents/surface.md` §3) |
| `architecture` | `architecture.width` and `architecture.depth` |
| `connectivity` | `architecture.sparsity` |
| `residual` | `architecture.residual` |
| `rule` | the rule a variant is trained under — its `learning_rule`, else its configuration's copy, else the catalogue's first — an axis a pair may differ on (D-19, `rules.md` §8) |
| `utility` | the utility a variant is trained on, resolved by the same reading — its `utility`, else its configuration's copy, else the catalogue's first — the seventh axis, and **one word for both the axis token and the field** (D-20, `utilities.md` §8) |
| `counterfactual` | the catalogue member a variant takes its **training targets** from, resolved by the same reading through `declarations.counterfactuals()` — its `counterfactual`, else its configuration's copy, else the catalogue's first, `none` — the eighth axis, one word for token and field as the utility's is, and a third catalogue and neither a rule nor a utility (D-43, `counterfactual.md` §6) |

**`game` is not an eighth axis, and the counterfactual is.** The shape is a property of a configuration and not a difference a pair reports: two sides on two shapes are refused as not a comparison at all, before the axes are read, so `AXES` names the eight of this table and `_differences` never looks at a `game` (`declarations.py`'s `AXES`, §6, `shapes.md` §1, §6, `ladder.md` §4, D-29). The counterfactual member **is** one: two arms may declare two of them and both are trained, which is the pair D-43's criterion reads, and it is therefore an axis and never one of the settings a pair must share (`counterfactual.md` §6, §9, `declarations.md` §4, D-43).

The rule, which is L2's correction: a pair compares `architecture` only when the two sides agree on the representation family and on `sparsity`. Where either differs, the width (and depth) gap is the capacity match's *compensation* — ASM-10 wants `sparse` wider than its dense mate and a token encoding at another width — so it belongs to `encoding` or `connectivity` and never to a second axis; with the rule and the utility, each of §3's eight pairs differs on one (`docs/L2/training/surface.md` §5, ASM-10).

Rejected: comparing width and depth always — R5's `dense` (50) against its `sparse` (62) would differ on two axes, `fairness` would refuse the rung's own control, and FAM-3.12 could not pass. Also rejected: a tolerance band on width ("within 20% counts as equal"), which invents a number and hides the compensation instead of attributing it. Also rejected: a `game` axis, which would report a comparison the two sides' curves, cells and ratings cannot make (`shapes.md` §6, D-29).

`_differences(left, right, rules=None, utilities=None, counterfactuals=None)` returns `(axes, fields)` — the axes two entries differ on and the fields that differ, the `rule`, `utility` and `counterfactual` axes appended from the resolved members — and `_axis` returns `{of, differs, declared}` (`surface.md` §5):

- **two configurations**: `of` is the **later** configuration's declared `axis` — the rung that varies against the lineage it inherits — and `declared` is that declaration (FAM-3.6–3.10 read it as text);
- **two variant entries**: `of` is the one axis the difference falls in, `declared` is `None`, and `differs` names the field names that differ (`width`, `depth`, `sparsity`, `residual`, `backend`, `encoding`, `learning_rule`, `utility`, `counterfactual`) so a reader sees the words — FAM-17.8 wants `learning_rule` for the `rule` axis, and the `utility` and `counterfactual` axes name token and field alike (D-20, D-43);
- `differs: []` — two sides that differ on nothing — invents no axis: `of` is the later configuration's declared axis for two configurations, and the literal `"no difference"` for two entries (`surface.md` §5); more than one differing axis is a refusal naming them all (§6).

## 3. The eight reportable pairs

| Pair | `differs` | `of` |
|---|---|---|
| R1–R2 | `["backend"]` | R2's declared axis: `backend — the same model in PyTorch, for the speed difference (D-7)` |
| R2–R3 | `["encoding"]` | R3's declared axis: `tokenisation — card tokenisation into a learned embedding` |
| R3–R4 | `[]` — both primaries are the `deep` stack at 50/2 | R4's declared axis: `width against depth, at one budget` |
| R4–R5 | `[]` — `deep` is R4's primary and `dense` is R5's, one stack | R5's declared axis: `dense against sparse connectivity, at one budget` |
| R5–R6 | `["residual"]` | R6's declared axis: `residual — a residual path against none, at R5's depth` |
| R4 `wide`–`deep` | `["width", "depth"]` — 62/1 against 50/2 | `architecture` |
| R5 `dense`–`sparse` | `["sparsity"]` — 0.0 against 0.5 | `connectivity` |
| R6 `residual`–`plain` | `["residual"]` | `residual` |

R3–R4 and R4–R5 differ on **nothing**, which is the design's point: R4's primary is the `deep` stack R3 already tokenised, and R5's primary is the `deep` stack R4 chose, so the later rung's axis names the *question it asked*, not a pair of stacks that already differ (D-3, D-16, `ladder.md` §2). R5's `dense` arm and R6's `residual` arm are the `deep` kind at `sparsity` 0, so R5–R6 differs only on the residual flag (`registry.md` §1). A pair whose arms declare two catalogue rules — or two utilities — is **reportable on that one axis**: the member left the settings a pair must share, and two estimators or two objectives are one capacity, so nothing else moves with it — hence the eight rows above, the six rungs declaring one of each (D-19, D-20, `rules.md` §8, `utilities.md` §8). Every one of the eight is on **one** shape, because the six rows declare no `game` at all (§7, `registry.md` §2, D-29).

## 4. `constants` — the fifteen declarations every comparison holds

`_constants(left, right, pool_report=None, rules=None, utilities=None, shape=None)` returns `ladder.md` §4's list under these key names (`record.md` §1), each quoted from the declaration that owns it (`surface.md` §5, FAM-3.14, FAM-13.3):

| Key | Value |
|---|---|
| `shape` | the one shape the pair is on, resolved by `_shape` and held by `_pair_shapes` — `fixed-limit-20` unless a side names one of the other two (§6, `shapes.md` §3, `seats.md` §2, D-29, D-33) |
| `game` | `engine.game_config(shape)` — that shape's row, and the row a run has always reported on the default shape (D-2, ASM-6, `engine/surface.md` §3, D-29) |
| `action vocabulary` | `declarations.vocabulary(shape)` — `{0: "fold", 1: "check-call", 2: "raise"}` on the default shape and six descriptors on either uncapped one, each read through the granted `features.decode_action(index, shape=...)`, because `features.action_space` is not among this module's five granted `features` calls (`module-map.md` §2, `e2e-surface.md` §2, `features/surface.md` §9, `sizing.md` §3, D-13, D-29) |
| `readout facts` | the **eleven** fact names of `e2e-surface.md` §2, `hand_class` included — declared here for the same reason, and identical on all three shapes and for every encoding, because it is a derived fact of `hole` and `board` and no encoding carries it (D-3, ASM-30, D-21, `seats.md` §3) |
| `reward` | what each side's **utility** delivers at the seat's terminal decision, read off the catalogue's own reward tokens — one for a one-utility pair and both for a two-utility pair — the net chip delta among them (ASM-12, `utilities.md` §2, §8, D-20) |
| `rules` | the **set** of rules the two sides are trained under — each side's `learning_rule`, else its configuration's copy, else the catalogue's first — in declaration order and never one side's, because what a rung holds constant is the set (`rules.md` §8, D-19, ASM-7) |
| `utilities` | the same **set** on D-20's axis — each side's `utility` through `_utility`, deduped by `_utility_set` — so a side spelling the default out and a side leaving it unsaid are one utility and never a phantom difference (`utilities.md` §5, §8, D-20) |
| `hyper` | the block a side declares, else `declarations.HYPER` — learning rate, batch size, target interval, optimiser, exploration schedule, discount (`rule.md` §6); a pair declaring two differing blocks is refused, because a constant one side only declares is no constant (§6) |
| `sample budget` | the hands per variant per seed the pair is trained at (ASM-8) |
| `param budget` | 10,000 ± 2%, declared (`registry.md` §4, ASM-10) |
| `seed set` | the seeds the pair is trained at (`protocol.md` §2) |
| `pool` | §5's report, repeated here as one of the held-constant facts (D-16, ASM-16) |
| `table budget` | `live` or `full` with its hands per cell and its seat alternation (`league.md` §6, ASM-14) |
| `checkpoint policy` | ten snapshots at `budget // 10`, the last M retained plus the final model, and the greedy pass reading the final one and adding no artefact (ASM-18, ASM-38, `greedy.md` §1) |
| `device policy` | `cpu` inside the sandbox; a user-started run records the device it used (D-8, `protocol.md` §6) |

The declared-as-data rows are deliberate: the ladder never changes the game, the vocabulary or the readout facts, so a constant naming them is a *report*, and reading a catalogue this module is not granted would be a sixth `features` call (`module-map.md` §2, D-13). The shape is the one row that is a **declaration and not a report**: it is read from the two sides and refused when they disagree (§6). The budgets, the seed set and the rule and utility **sets** are read from the two sides; a pair declaring two `hyper` blocks is **refused** rather than reported with one side's value, and two rules or two utilities are no held constant — they are the axes (`declarations.md` §3–§4, `rules.md` §8, ASM-7, D-19, D-20).

## 5. The pool report, and the R1/R2 parity reading

`pool` carries `m` = 5, `frozen`, the **baselines either side's pool holds** — the anchor three in every pool and any folding baseline a membership declaration named, the anchors first and never one side's — each arm's declared `id` under `ids`, `same` — the one id both declare, or `None` — and `membership`, the pinned set plus the version window both arms train against (`surface.md` §5, ASM-16, ASM-32, D-21). Two arms of R4, R5 or R6 declare **one** configuration-level pool entry, so `same` is that id and `membership` is that entry's window (FAM-3.17, FAM-3.18). An **adjacent** pair cannot share one: a rung's pool is the previous rung's window, so R2's contains R1's snapshots while R1's is the baselines alone — `same` is `None`, both ids are reported, and `membership` is the **intersection** of the two memberships in order, which for R1–R2 is the three baselines alone and carries a folder both sides declared (`record.md` §1, `league.md` §2, `records.md` §8). A pool is one shape's, and both sides of every pair here are on the one shape §7 names, so the report never mixes two (`records.md` §8, `shapes.md` §3, D-29).

That intersection is what the parity check plays on: R1 and R2 declare one encoding, one architecture, one update rule, one utility and one sample order, so they are handed the same deals against the same opponents and **must choose the same actions on the same seeded hands**; a parity row showing a large skill difference is a defect, not a finding (D-7, `ladder.md` §5, FAM-13.4). Their evidence is throughput and wall clock from the two run records' `timings`, never an assertion that a clock was beaten (`record.md` §2, FAM-13.5, ASM-15). `fairness` reports what it found; it never labels a pair fair, because a non-reportable pair never gets that far (D-3, D-6, D-20).

## 6. The refusals, and the order the shape is judged in

All raise a `TrainingError` subclass naming the offending value (`errors.md` §2, §4), before anything is built or returned (`surface.md` §5). **The shape is judged before any axis is**: `_pair_shapes` runs where the two sides' shapes are known and before `_axis`/`_differences` is asked anything, because a pair on two shapes is not a comparison that differs on an axis — it is not a comparison at all, and reporting one of the two as the constant held would be the same defect in a report instead of a run (`shapes.md` §1, §6, `ladder.md` §4, D-29).

| Refusal | When |
|---|---|
| `NotAComparisonSide` | a side is neither a configuration (it carries `variants`) nor an entry (it carries `architecture`) — the value is named |
| `SideKindMismatch` | one side is a configuration and the other an entry |
| `ComparisonKeyMissing` | a configuration or entry missing a key the comparison reads — `variants`, `architecture`, `backend`, `encoding`, `pool` — the key is named |
| `MultipleAxes` | the differences fall in more than one axis — **every** axis is named, in §2's table order, so a pair differing on `utility` *and* another axis names both and is refused (D-3, D-6, D-20) |
| `PoolIdsDiffer` | two entries of one configuration declare two pool ids — both are named, because both arms of a pair train against one frozen pool (ASM-16) |
| `PairDeclarationsDiffer` | the two sides (configurations on their `primary` entries, §1) declare two `hyper` blocks — the key and **both** values are named, and only both-declared-and-different is a refusal, so one side declaring neither is no claim (`declarations.md` §3–§4, ASM-7). **Also** the two sides name two **shapes**: `fairness` raises it naming both shapes, before any axis is read, because a shape is a property of a configuration and never a rung's axis (`shapes.md` §1, §6, D-29). **Not** a refusal: two `learning_rule` values or two `utility` values, which are the `rule` and `utility` axes (D-19, D-20, `rules.md` §8, `utilities.md` §8) |
| `UnknownShape` | a side names a `game` the catalogue `engine.game_shapes()` publishes does not carry — or a value that is not a name at all — refused by `_shape` through `declarations.require_game`, naming the name and **every declared name**; a name is never defaulted onto the catalogue's first, and only absence is (`shapes.md` §2–§3, `seats.md` §2, D-29, D-13) |

An **unregistered** configuration is not refused for being unregistered: it declares its own axis and its own pool, and `fairness` reports them like any rung's (`ladder.md` §3, FAM-15.3, FAM-16.30). It may also declare **another of the three shapes**, and then it is a pair on that shape and nothing about it is compared with a pair on either other (`shapes.md` §6, `seats.md` §2, D-29, D-33).

## 7. Determinism, and what an absent `game` means

One pair gives one record: `fairness` plays no hand, builds no encoder or learner, writes nothing and moves no stream (`surface.md` §5, ASM-2). It reads the two sides' entries, their pool entries, `declarations.HYPER`, the three declared shapes' names and — for a side declaring no rule, no utility or no shape — the catalogue `agents.learners()` publishes and `declarations.require_game`, so the record is a function of its arguments and of no earlier call (`battery.md` §3 FAM-3, FAM-15, `rules.md` §4, `utilities.md` §5, `shapes.md` §3, D-29); equal sides give equal records, and §3's eight pairs give eight results in any order.

**Two sides naming no shape are one shape, not two declarations.** An absent `game` reads as the catalogue's first shape, so two registry rows — which declare none at all — are on one shape and their comparison is reportable; absence is never a difference and never a "no claim" that could not be compared (`shapes.md` §3, §6, `registry.md` §2, D-29). A side naming the shape out loud and a side leaving it unsaid are one shape and one held constant, exactly as a side spelling the default rule out is one rule (§2, D-19).

## 8. What is left to L4

Whether a side is classified by its keys or by a tag, whether `differs` is a list or a tuple, whether `_shape` is called once per side or inside `_pair_shapes`, and the private helpers below §1's four signatures — `_rule`, `_utility`, `_rule_set`, `_utility_set`, `_member_ids`, `_pinned_ids`, `_pool_report`, `_reward_row` and `_differences` among them. Not L4's: the seven axes and their compared values, §2's matching rule and its ruling that `game` is no eighth axis, §3's eight results, the fifteen `constants` keys with `shape` first, the shape-aware `game` and `action vocabulary` rows and the rule and utility **sets**, the two declared-as-data rows, the pool report's six keys, the `same`-and-intersection reading, the shape-before-axes order and §6's seven refusals (`guardrails.md` G14, G15, G21); §1's four signatures — `_shape` and `_pair_shapes` included — are contract for `tests/training/` (`README.md` §4).
