I have the repository grounded. Two statements in the brief are contradicted by the tree, and I flag them at the top because the design depends on them. Everything below is design only — no file was written or edited.

---

# L1 design — the `strength` fact, the `strength` axis, and supervised embedding seeding

**Unit** phase1 · **Layer** L1 · **Status** design, for L0 sign-off (D-10 gate owed before L2) · **Writes** none

## 0. Corrections to the brief, measured

| # | The brief says | The tree says | Consequence for this design |
|---|---|---|---|
| 0.1 | `IgnoredDeclaration` lives in `agents/errors.py` | it is `src/training/errors.py:68`; `src/agents/errors.py` has 24 classes and none of that name | the new axis' refusal is `training.errors.IgnoredDeclaration`, exactly as `_check_learning_rule` (`src/training/declarations.py:704-721`) raises it |
| 0.2 | "the token path pools with a **masked** mean over real ids; D-79 established padding is excluded from pool **and** scatter" | the shipped pooler is **unmasked**: `src/agents/numpy_backend.py:115-116` `rows = (1 + tanh θ)/2; carried = rows.mean(axis=0)`, `:178` `numpy.add.at(gathered, ids, (upstream / len(ids)) * slope)`, and `src/agents/torch_backend.py:136-137` `rows.mean(dim=0)`. The mask exists only in the `masked-both` **probe** (D-80) | the design may not claim a mask it does not have. The strength token must be a **non-zero** id (never the pad), and this change is forbidden from shipping a mask change at the same time (D-3, one thing at a time). Stated as risk G1 |
| 0.3 | `.probe/attn60.pt` uses `pos./n1./n2.`, `.probe/attnconv.pt` uses `posemb./norm./ffn.` | confirmed from `.probe/wire_policy.py:9-13` (layout A) and `.probe/policy_sup.py:10-14` (layout B); both are `emb=nn.Embedding(53,50)`, 2 layers, 5 heads, 50-wide, FFN 96, `head` → sigmoid | `load_strength` declares **two layout rows**, one attribute map each (§D.1) |

Everything else in the brief's measured facts checked out against the code I read: `FIELDS` and the nine block tables (`src/features/declarations.py:58-68`, `:359-412`), the four id-base constants (`:73-77`), the eleven readout facts (`src/engine/readout.py:75-99`), the literal spec key list (`src/training/loop.py:441-467`), the pad id (`src/features/encode.py:38`), and the token learner's embedding block at flat parameters `0..5099` for `(102, 50)` (`src/agents/model.py:134`, `:183-187`).

---

## A. The fact: where `strength` goes, its bound, and every resulting width

### A.1 Placement — one slot, appended **last** in both block tables

The nine fields are the readout's carried facts (`declarations.py:58-68`). `strength` is a **tenth declared field with no readout position**: it is a value the observation carries and the information set does not (it is a deterministic function of `hole` and `board`, so it widens nothing — the argument `hand_class` already makes at `src/engine/readout.py:8-12`, for a fact that *is* in the readout).

Appended **after `history`** in both tables, deliberately, so that **every pre-existing offset is untouched** and only the width grows:

| encoding | shape | today | with `strength` | strength slot index |
|---|---|---|---|---|
| `flat-numeric` | `fixed-limit-20` | 203 | **204** | 203 |
| `flat-numeric` | `no-limit-100` | 329 | **330** | 329 |
| `flat-numeric` | `six-seat-no-limit-100` | 433 | **434** | 433 |
| `card-tokens` | `fixed-limit-20` | 40 ids | **41** ids | 40 |
| `card-tokens` | `no-limit-100` | 82 | **83** | 82 |
| `card-tokens` | `six-seat-no-limit-100` | 122 | **123** | 122 |

A block records are, verbatim:

```
flat-numeric : ("strength", <pre-change width>, 1, "strength-scaled", ("strength",), None)
card-tokens  : ("strength", <pre-change width>, 1, "strength-bucket", ("strength",), STRENGTH_BANDS)
```

appended by `_flat_blocks` (`declarations.py:359-378`) and `_token_blocks` (`:394-412`) only when the declaration is strength-declaring, and `declaration()`/`spec()` (`:534-576`) report `fields = FIELDS` or `FIELDS + ("strength",)` accordingly through one helper `_fields(strength)`.

**Why last, and why the token position is semantically free.** The token learner's pooler is `mean over rows` (`numpy_backend.py:116`, `torch_backend.py:137`), so token *position* carries no information to any of the seven kinds; only the id matters. Putting the token at index 122 (after the history block's pads) therefore costs nothing and buys the invariant "**the strength slot sits at the offset the pre-change observation's width named**", which is one assertion instead of six.

### A.2 The bound, and why `strength` declares **no normaliser**

The bound convention is one table keyed by writer tag (`declarations.py:268-285`, applied in the one loop at `encode.py:370-376`) with exactly three policies, and the dense numerator/denominator table plus its saturation rule is `docs/L1/normalisation.md:46-56` and `:99-109`. Two records are added:

| writer tag | bound record | policy | why |
|---|---|---|---|
| `strength-scaled` | `(0.0, 1.0, "exact")` | checked, never clipped | a probability is already a fraction and cannot leave `[0,1]`; the writer **refuses** a value outside it or non-finite (§A.3), so the bound is a statement about the writer, exactly as `normalisation.md:99-109` defines `exact` |
| `strength-bucket` | `(0, "vocabulary", "id")` | id | a token block's bound follows the shape row's vocabulary (`declarations.py:277-284`) — and the vocabulary itself grows with the band ladder, see A.3 |

**No `normaliser` key is added to any shape row, and `strength` joins neither `_BLOCK_NORMALISERS` nor `SHAPE_ROWS[...]["normalisers"]`.** The reason is mechanical, not stylistic: the row's five normalisers are *restated from* `engine.game_shapes()` and the join battery asserts the sets are equal — `tests/integration/features/test_join_shapes.py:250` `set(normalisers) == set(NORMALISERS)`. A sixth key would break that join and `_require_normalisers`'s message (`declarations.py:452-458`). The strength slot's denominator is **1**: it divides nothing.

The `exact` policy now covers two writer classes (indicators, and a value already inside the interval). That requires one amended sentence in `declarations.py:255-267`'s docstring and in `tests/features/test_features_bounds.py:312-318`'s docstring; **no assertion changes**. Rejected: a fourth `"range"` policy, which would add a value to a closed set that `encode`'s loop, `POLICIES` (`test_features_bounds.py:86`) and the `BLOCK_BOUNDS` docstring all enumerate, for a distinction exactly one block makes.

### A.3 The value's domain, and the token ladder

One validator, declared once and reached by both writers — the module's own stated rule ("A rule lives here once and both encodings reach it", `encode.py:44`): `_probability(value)` accepts a real that is not a `bool`, is finite, and lies in `[0.0, 1.0]`; it refuses otherwise with `InvalidReadout("encode(readout): 'strength' must be a probability in [0.0, 1.0], got …")`, naming the injected key. There is **no clamp**: D-95's lesson is that a silently clipped value hides a broken estimator.

The token bands, one ladder in a module constant (not per row — the edges are shape-invariant, unlike the chip ladders of `:120-153`):

```
STRENGTH_ID_BASE   = 102                      # above every id any row allocates (96-101 are the six seat ids)
STRENGTH_BANDS = ((0.05, 102), (0.10, 103), (0.20, 104), (0.30, 105),
                  (0.45, 106), (0.60, 107), (0.80, 108), (None, 109))
STRENGTH_VOCABULARY = 110                     # derived: STRENGTH_ID_BASE + len(STRENGTH_BANDS)
```

* Eight bands, the same cardinality as the `to_call`/`pot`/`stacks` ladders, and **total over `[0,1]`** because the last bound is `None` (the convention at `encode.py:147-156`).
* The edges are placed where the measurements put the mass and the error: five of eight bands inside `[0.05, 0.60]` (D-86's calibration deciles run 1.1 → 61.6 at the river; 10.8 → 28.3 preflop), with the two ends coarse because the model is near-exact there (D-94: quad aces 99.95 %, junk 0.00–0.77 %) and a lock does not need resolution.
* **No band emits the pad.** `encode.PAD`'s docstring (`encode.py:36-38`) already says "No other block may emit it"; the lowest strength id is 102, so the brief's padding concern is met by construction — and a strength representation that *could* emit `0` is refused by the design, not by luck.
* A strength-declaring token declaration reports `vocabulary = 110` on **every** row (`max(row["vocabulary"], STRENGTH_ID_BASE) + 8`, derived). The two-seat rows therefore carry six never-addressed rows (ids 96-101, the six-seat seat block's) — dead rows receive no gradient (`numpy.add.at` scatters only addressed ids, `:178`), so they cost 300 parameters and no behaviour. Rejected: a per-row base (`vocabulary` = 104 at two seats, 110 at six), which would make the same band mean two ids and restate one ladder three times.

### A.4 Resulting widths *and* what follows from them

| shape | `flat-numeric` | `card-tokens` seq | token vocabulary | `naive-stack` W36 D2 | `token-embedding` W50 D2 A=A(shape) |
|---|---|---|---|---|---|
| `fixed-limit-20` | 203 → **204** | 40 → **41** | 96 → **110** | 10,119 → **10,155** (+36) | 10,053 → **10,753** (+700) |
| `no-limit-100` | 329 → **330** | 82 → **83** | 96 → **110** | 14,766 → **14,802** | n/a (head 6: 10,506 → **11,206**) |
| `six-seat-no-limit-100` | 433 → **434** | 122 → **123** | 102 → **110** | 18,510 → **18,546** | 10,506 → **10,906** (+400) |

The parameter counts are read off `src/agents/model.py:50-71` at the widths the registry declares (`src/training/declarations.py:380-465`); both arms of a strength-on/off pair therefore **cannot** be called a matched-parameter comparison (ASM-10 is a *declared* budget, `loop.py:169-189`), which is stated as risk G4.

### A.5 The absence path is byte-identical

`build_encoder(name, shape=None)` with no `strength` builds today's declaration exactly: same six-key spec record, same `fields` tuple of nine, same widths 203/329/433 and 40/82/122, same vocabularies 96/102. This is the property that keeps the ~250 width assertions of the battery untouched — see §F.1's "does not change" list.

---

## B. How the value reaches the encoder

### B.1 The three candidates

| | mechanism | what it costs |
|---|---|---|
| **(i)** | `engine.readout` grows a twelfth fact | the engine would own a neural network — `engine` "never imports another project module" and depends on `pokerkit` + stdlib only (`docs/L1/module-map.md:54`). And the closed information set is asserted at four helper declarations (`tests/integration/engine/_support.py:128`, `tests/integration/features/_join_support.py:137`, `tests/features/_features_support.py:67`, `tests/e2e/_surface.py:338`) and compared ~40 times (`FAM-2.3`, `FAM-2.10`, `FAM-2.18`, `FAM-21.4`, `FAM-22.5`, `FAM-24.1`, `ENG-4`, `AGT-9.10`, `test_join_purity.py:158`, …). **Rejected.** |
| **(ii)** | the harness injects the value into a **copy** of the readout immediately before encoding | the encoder stays a pure function of the mapping it is handed; the engine stays model-free; the readout stays eleven facts. Cost: 4 call sites must inject (§B.3) |
| **(iii)** | the **encoder** holds the frozen model and computes the slot inside `encode` from `hole`/`board` | zero call sites, but it puts weights behind the declaration table, which is plain data rebuilt per call (`declarations.py:534-553`), and behind the six-key spec, which cannot report them (`encoder.py:70-90`); and a writer that derives a model value contradicts the block contract "a pure function of the values its block declares it reads … params the writer's own constants" (`encode.py:10-12`, `declarations.py:13-16`). **Rejected.** |

### B.2 Recommendation: (ii), with the injection written **once**

`strength` is a **declared field with an injected value**:

* `features.encode` requires it (`encode.py:363-368` refuses a mapping missing a declared field) — so a forgotten injection is a **named refusal**, never a silent zero. This is the property part C's "cannot silently unqualified" needs.
* `agents.as_policy`'s `Policy._facts = (LEGAL,) + fields` (`src/agents/policy.py:190`, checked at `:117-122`) makes the same demand of any policy built over a strength encoder.
* The four features entry points of §D.1 do the work; `features.stated(model, readout)` returns **a fresh mapping** — never a mutation, because `tests/integration/features/test_join_purity.py:158` asserts a readout keeps its own eleven facts through an encode, and `tests/features/test_features_observation.py:152` (FEA-3.7) asserts the readout is unchanged after encoding.

### B.3 The four injection sites, each one line

| # | file:line | change |
|---|---|---|
| 1 | `src/training/policies.py:28-32` (`_learner_policy`) | gains `model=None`; the closure begins `readout = features.stated(model, readout)` |
| 2 | `src/training/episode.py:473` and `:484` (`_transitions`) | both `features.encode(encoder, …)` calls wrap the decision/successor readout; `_transitions` gains a `model=None` argument |
| 3 | `src/training/loop.py:511-518` (the greedy pass) | the `agents.as_policy(...)` policy handed to `greedy._pass` is wrapped by a second helper in `policies.py`. **`greedy.py` itself is untouched** — its retained records carry `index`/`descriptor`/`amount`/`limit`/`legal`/`tie` and no readout (`greedy.py:166-175`), so nothing in the retained block changes |
| 4 | `src/evaluation/policy.py:278-315` (`_checkpoint_policy`) | reads the container's recorded `strength` member (a **fourth recorded fact**, §D.4), builds the encoder with it, and wraps the policy |

Nothing else in the project may inject. `harness` fixtures build readouts; a strength case hands the extra key through `_features_support.readout(extra={...})` (`tests/features/_features_support.py:795-796`), which already exists.

---

## C. The `strength` axis

### C.1 Name and members

* **Axis:** `strength` · **members:** `none` (default, first) | `supervised`.
* Published under a **seventh key** of `agents.learners()`: `strengths`, after `counterfactuals` and before `hyper`, each member a record `{"name": <name>, "carries": <stable token>}` — `none` → `no-model-input`, `supervised` → `predicted-win-probability` (no sentence, no whitespace, mirroring `LEARNING_RULES` at `src/agents/declarations.py:101-110`).

### C.2 The two companion spec keys

| key | values | condition |
|---|---|---|
| `strength` | `"none"` \| `"supervised"` | absence = the catalogue's first member, nothing substituted (`build_learner`, `src/agents/learner.py:525-539` pattern) |
| `strength_source` | a name from the declared source table (§D.1): `"attn-60"` \| `"attn-400"` | **required** exactly when `strength != "none"` or `embedding_init` is declared; declaring it otherwise is `IgnoredDeclaration` |
| `embedding_init` | `{"source": <same name>, "rows": "cards"}` \| absent | refused on a dense-numeric variant (there is no embedding table, `model.py:136-140`) |

`strength` is a catalogue axis and lives in `agents`; `strength_source` and `embedding_init` are **spec keys**, like `encoder` and `game`, because a path is data and a catalogue is rebuilt per call (`declarations.py:335-348`).

### C.3 Where it is read in `src/training/loop.py`, and where it is refused

Follow the counterfactual pattern verbatim (D-43 is the precedent for adding a fourth axis):

| what | anchor |
|---|---|
| `_declared_strength(configuration, entry)` — entry's, else the configuration's, else `None` | new, modelled on `_declared_counterfactual` at `loop.py:348-365` |
| `_trained_strength(configuration, entry)` — declared, else `declarations.strengths()[0]` | new, modelled on `_trained_counterfactual` at `:368-381` |
| the encoder is built **with** the resolved member | `loop.py:439` moves *after* the resolution: `features.build_encoder(entry["encoding"], shape=shape, strength=member)` |
| the learner spec gains `spec["strength"]` and, when declared, `spec["embedding_init"]` | between `loop.py:439-467`, on the same "only when declared" rule as `:451-466` |
| the frozen model is loaded **once per variant**, not per seed and not per hand | `loop.py:436-441` region (next to `encoder = …`) |
| the model is handed to `_learner_policy`, `episode._transitions` and the wrapped greedy policy | `loop.py:468`, `:483-485`, `:511-518` |
| the record writes `variants[].strength`, `variants[].seeding`, and the run-level `strengths` set | `_record`, `loop.py:701-720` and `:850-866`, on D-43's conditional rule |
| the run's own model reference rides in the header | `_header`, `loop.py:548-578` (a tenth **key inside the header mapping** would break "the nine items … do not grow", `:545-546` — so it goes in `variants`, not the header) |

**Refusals, three layers, each at its own boundary (the pattern `game` already uses — `loop.py:285-296`, `declarations.py:311-333`):**

1. `training.declarations._check_strength(where, configuration, entries)` — an uncatalogued name, a non-string, or `None`-with-a-source at either level → `errors.IgnoredDeclaration`, naming the level, the value and the catalogue, **before the pool is built and before the first hand** (called from `check_declarations`, `src/training/declarations.py:831-870`, after `_check_counterfactual` at `:849`). This is the trap the brief names: the key is read here *and* forwarded, so it can never be silently dropped.
2. `training.declarations._check_embedding_init(...)` — a malformed record, an undeclared source, or a `flat-numeric` variant → `IgnoredDeclaration` / `VariantSettingInvalid`, same place.
3. `features.build_encoder(..., strength=<unknown>)` → `UnknownStrength` (a `FeaturesError`), naming the value and the two members — the encoder never defaults a member, as it never defaults an encoding name (`encoder.py:60-67`).

### C.4 Interaction with the two encodings and the seven kinds

| kind | family | `strength: supervised` | `embedding_init` |
|---|---|---|---|
| `naive-stack` | dense | one slot at 203/329/433, width 204/330/434 | **refused** (no embedding block) |
| `token-embedding`, `wide`, `deep`, `sparse`, `residual`, `plain` | token | one id at 40/82/122, vocabulary 110, sequence 41/83/123 | allowed |

Nothing in `agents`' arithmetic branches on the member: `act`, `learn`, `param_count` and the two checkpoints' members are strength-free (the same rule that keeps `counterfactual` out of the arithmetic, `src/agents/learner.py:342-356`); `strength` is carried, recorded and reported, and read by **no** arithmetic inside `agents`.

### C.5 Fairness

`AXES` (`src/training/declarations.py:158-167`) gains a ninth axis `"strength"`. `PAIR_SETTINGS` (`:184-193`) gains `"strength_source"` and `"embedding_init"` and **not** `"strength"` — the two arms of D-3's pair differ on exactly the axis under test, while the *source* and the *seed declaration* must match, or one arm's numbers are attributable to a different frozen model.

---

## D. The embedding seeding

### D.1 The declared source table, and where the model lives

The frozen model is **not a seventh module**: `module-map.md:87-96`'s doctrine is that an addition costs an entry point rather than a subtree, and `:89-90` already refuses an attention module for the *Phase-2 objective* — this artefact is D-90's card model, a frozen input, not a policy feature. It goes in `features` as the submodule `src/features/cardmodel.py`, with **torch imported lazily inside the functions** (the project's own precedent for keeping a module-level edge from forming: `agents/learner.py:845` `import engine` inside `_chips_in_play`). A non-strength import of `features` still pulls no torch.

**Four new entry points** (`features` 7 → 11; map 50 → 54; `modules.json` and every ceiling follow, §F.4):

| endpoint | contract |
|---|---|
| `load_strength(source)` | an **opaque** frozen estimator for one declared source, or a refusal naming the source and the declared sources. Validates: the file exists, the state dict matches the source's declared **layout row**, the attribute names are exactly that row's, `emb.weight` is `(53, 50)`, weight width is 50 |
| `strength(model, readout)` | `p ∈ [0,1]` for the decision's `hole` + `board` (2 + up to 5 card ids, pad 0), through the source's own forward (attention + positional, masked mean, sigmoid). Refuses a malformed `hole`/`board` by name |
| `stated(model, readout)` | **a fresh mapping** equal to `readout` plus `{"strength": p}` — the injection, written once (§B.3) |
| `card_rows(model)` | a fresh `(52, width)` float64 array for ids **1..52**, plus a **digest** of those rows — or a refusal when the source has no embedding table |

The declared table (in `features`, restated in `training/declarations.py` and held equal by a join case, exactly as `SHAPE_NAMES`/`SHAPE_HISTORY` are at `training/declarations.py:76-96`):

```
"attn-60"  → .probe/attn60.pt    layout A: pos / n1 / n2 / ff / mha / emb / head   rows: yes
"attn-400" → .probe/attnconv.pt  layout B: posemb / norm / ffn / ff / mha / emb / head  rows: yes
```

Two layout rows, one parameterised module builder whose attribute names are constructor arguments — **one** statement of the architecture, two attribute maps, and a refusal by name for a state dict that matches neither. `attn-60` is the recommended default: it is D-98's best-chips arm and the better-calibrated one (battery mean |err| 11.9 against 24.2). `.probe/attn_onehot.pt` is deliberately **not** declared: its projection is `Linear(17→50)`, so it can produce a probability but cannot seed rows, and a source that cannot seed is a second kind of row this slice does not need.

Rejected: converting the `.pt` files to a `.npz` the product reads with numpy only (a second statement of the model's arithmetic, which D-13 forbids); shipping a whole pickled module object (`weights_only=True` on a state dict is the safe default, and a pickled class path binds the artefact to its source tree).

### D.2 The moment: inside `build_learner`, before the learner exists

`agents.build_learner(spec)` (`src/agents/learner.py:474-658`) gains two optional keys and copies the rows **between `model.initial_draw` and `backend.new_state`** (`:620-624`):

```
layout, parameters, masks, _kept = model.initial_draw(...)      # today
parameters[w_in] reshaped (input_dim, width)[1:53, :] = rows    # the seeding, new
state = backend.new_state(layout, parameters, masks)            # today
```

Seeding there — and not through a `seed_embedding(learner, source)` API — buys three properties:

1. **A learner is never observable unseeded.** `learner.py:1-5` states the invariant ("built from one spec, complete at construction"), and a post-build mutator would break it and make `save`/`load` order-dependent.
2. **The target copy starts seeded**: `numpy_backend.new_state:44-49` copies the online parameters into the target copy, so the first `learn` bootstraps from seeded values, not from a stale draw.
3. **A refused seed leaves nothing built** — the refusal is raised before `new_state` and before any mutation, which is the module's stated validation order (`learner.py:8-12`).

### D.3 What validates it

| check | refusal |
|---|---|
| the family is token (`layout.dense` is False) | `InvalidEmbeddingInit` naming the kind and "a dense-numeric learner has no embedding table" |
| `layout.width` equals the source's declared width (50) | names both widths |
| `layout.input_dim` (the vocabulary) ≥ 53 | names the vocabulary and the 52 card ids |
| the rows are `(52, width)`, finite, real | names the shape it got and the shape it needed; a non-finite row is refused because D-45's `PARAMETER_BAND` (`declarations.py:212`) would otherwise refuse the first batch with a message about divergence |
| dtype | the source's tensors are float32; the product's parameters are float64 (`checkpoint.py:87`) — the conversion is `numpy.asarray(..., dtype=numpy.float64)`, and the *recorded* digest is taken over the converted rows so a replay compares like with like |

The copy touches **rows 1..52 and nothing else**: row 0 (the pad) and rows 53..(vocabulary−1) (street, seat, bucket and strength ids) keep the seed's own draw. That is asserted bit-for-bit (§F.2, AGT-19.4).

**The composition, stated plainly because it is the one honest caveat:** the product's embedding is read through the bounded squash `row = (1 + tanh θ)/2` (`normalisation.md:76-82`), so a parameter-space copy means the learner *reads* `squash(v)`, not `v`. A read-space copy would need `θ = arctanh(2v − 1)`, which is **undefined** for the supervised rows (they are unbounded reals from `nn.Embedding`, not values in `(0,1)`). So the copy is parameter-exact and read-monotone, and the record says which space it was written in (`"space": "parameter"`). A read-space seed becomes available only with the `no-squash` embedding axis D-76 declared and never shipped (D-77 recorded that it costs a third of the explanatory power to keep the squash).

### D.4 Reporting: a run cannot silently be seeded, and cannot silently be unseeded either

| where | what |
|---|---|
| `Learner` | `__slots__` (`learner.py:359-382`) gains `strength` and `seeding`; `seeding` is `None` or the record `{"source", "rows", "width", "space", "digest"}` |
| `Policy` | `__slots__` (`policy.py:58-71`) gains the same two, carried and never read by a decision (`:191-204` pattern); `docs/L1/e2e-surface.md` §2's list of attributes a policy carries grows by two |
| container metadata | version 6, fields `strength` and `seeding` (§E) |
| run record | `variants[]` rows gain `strength` and `seeding` on D-43's **conditional** rule (`loop.py:860-865`), and the record gains a run-level `strengths` set only when some variant declares a non-default member (`:711-720`, `:775-776`) |
| operator visibility | three independent witnesses: the variant row, the container's `seeding.source`+`seeding.digest`, and `agents.load(None, path)`'s learner carrying the same digest. A run that declared `embedding_init` but wrote no `seeding` is a **test failure** (§F.2 AGT-19.7), and a run that declared `strength: supervised` with no `embedding_init` records `seeding` **absent** — so "strength-fed" and "seeded" can never be confused in a record |

---

## E. Checkpoint compatibility: the era boundary

### E.1 Format version 6

Following the shape (v4) and counterfactual (v5) precedents exactly (`src/agents/checkpoint.py:21-45`, `:500-673`):

* `STRENGTH_FORMAT_VERSION = 6`; `SUPPORTED_VERSIONS = (1, 2, 3, 4, 5, 6)` (`:80-86`); `_or_written` derives the message from the tuple, so the refusal text follows automatically (`:337-344`).
* **Written when** `learner.strength != "none"` **or** `learner.seeding is not None`; otherwise today's rules stand untouched (v3 default shape, v4 other shape, v5 revealed member). So **a run that declares neither writes byte-identical containers**, and the 18 shipped v1 containers, `checkpoints/evidence/`, `tables/league-full.json` and both deep runs are untouched.
* **Fields, in §2.1's order:** `strength` immediately after `counterfactual`, then `seeding` immediately after `strength`. Within v6 the presence of each is its own condition — `strength` present iff the member is not `none`, `seeding` iff the learner was seeded — and v6 requires **at least one**, exactly as v5 carries `game` exactly when its shape is not the default (`:549-564`).
* **Refusals:** v1–v5 must carry neither field (a file that does was edited); a v6 container must carry at least one; a v6 `strength` naming an uncatalogued member, or naming `none` (whose container is a v3/v4/v5 one), is refused by name; a v6 `seeding` must be a record with the five keys and a `digest` of 16 hex characters.

### E.2 The width exemption, and the one place it can go wrong

`_declared` (`checkpoint.py:716-723`) holds a container's `representation.size` to the **kind's** declared 203/96 whenever `sized_by_kind(game)` — a statement that is true for every version up to 5 and false for a strength-declaring default-shape container (204 / vocabulary 110). The design's rule:

> the `sized_by_kind` equality applies to versions **1–5 only**; for a v6 container `representation.size` is checked for positivity and then held to the geometry by `_rebuild`'s `params.count`, exactly as a v4 container's own width already is (`:966-994`).

Without it, every strength-on default-shape container is refused with a misleading "`representation.size` must be 203"; with it relaxed too widely, `tests/agents/test_checkpoint.py:1059-1067`'s existing refusal of a doctored size silently disappears. Both directions are asserted (§F.2 AGT-19.9).

### E.3 How old checkpoints are handled: **refusal by name, in both directions**

| situation | behaviour |
|---|---|
| a pre-change container (v1–v5, size 203 or vocabulary 96) loaded against a strength-declaring encoder's spec | `_compare` (`:920-932`) refuses: "the encoder is 'flat-numeric' (dense-numeric, width **204**) and the checkpoint is dense-numeric at **203**" — a named refusal, **not** a silent reinterpretation. This is the explicit lesson of D-61/D-69 (`decisions.md:1858-1860`: "changing a forward pass must declare the era of the containers it invalidates") |
| a v6 container read by a pre-change build | refused at `_declared:517-521`: "format_version must be 1, 2, 3, 4 or 5" |
| a v1–v5 container loaded with `load(None, path)` by the new build | restores at its recorded size and decides exactly as before — nothing about the absence path moves |
| `evaluation.policy_from` of a v6 container | works, because §B.3 site 4 reads the recorded `strength` before building the encoder; a v6 container whose recorded member is `supervised` and whose reader built the encoder without it would fail as an `InvalidObservation` size mismatch — which is why the reading is a **required** fourth recorded fact, not an optional one |

### E.4 The strata of prior results that become "pre-strength era"

Named so no report can mix them:

* the 18 shipped containers (`checkpoints/`, v1) and every census computed from them — D-53's 92.7 %, D-56's seven-seed table, D-63's grid, D-68's nine runs;
* `checkpoints/evidence/`, `tables/league-full.json` and both deep runs;
* every `flat-numeric` result at 203/329/433 and every `card-tokens` result at 40/82/122 over 96/102 ids — including this repository's own recent findings (D-92, D-97, D-99, D-101 are **probe** results on a hand-rolled semi-gradient step, not the product's learner, and D-92 explicitly left the strength input undone);
* the Bradley-Terry ratings: the fit is anchored on the same three baselines (D-21, `league.md`), so a rating stays comparable **within** an era and never across one.

**Not** in the era: the card models themselves (`.probe/attn60.pt`, `.probe/attnconv.pt`). They are frozen inputs, not learners; their readings (D-93's 40.0 % pooled, D-95's 24.2-point battery error) stay current and are the *reason* the input is worth feeding.

---

## F. The test plan

### F.1 Existing assertions that must change — quoted, with the reason

**Enumerations of the catalogue's key count (four sites, all grow 6 → 7):**

| file:line | today | change |
|---|---|---|
| `tests/agents/test_learners.py:36-52` (AGT-2.1) | `tuple(record) == ("backends","architectures","learning_rules","utilities","counterfactuals","hyper")` | `strengths` inserted **after `counterfactuals`, before `hyper`** |
| `tests/agents/test_counterfactual.py:309-341` (AGT-18.2) | `self.assertEqual(len(keys), 6, …)` plus the tuple at `:317-324` and the two index relations at `:330-341` | 7, the tuple gains `strengths`, and the two relations become `utilities` + 1 = `counterfactuals` < `strengths` = `hyper` − 1 |
| `tests/e2e/test_fam22_counterfactual.py:1419-1426` (FAM-22.6) | `self.assertEqual(len(declared), 6, …)` | 7, and the token loop at `:1428` gains `"strength"` |
| `tests/e2e/test_fam22_counterfactual.py:1440-1457` | `names[0] is none`, `names[1] is reveal-counterfactual` | unchanged (a different catalogue) — listed so nobody "helpfully" reorders it |

**`tests/agents/test_learners.py:143-148` (AGT-2.4, `tuple(architectures) == SEVEN_KINDS`) does not change**: the kinds stay seven, and `SEVEN_KINDS` in `tests/agents/_agents_support.py` is untouched. Stated explicitly because the brief asked which of these enumerate the surface.

**Block-count and declaration shapes (amended, never weakened):**

| file:line | today | change |
|---|---|---|
| `tests/features/test_features_bounds.py:223-227` | `len(record["blocks"]) == len(S.FIELDS)` | stays true for the default declaration; the strength-on declaration is asserted by a **new** case (FEA-12.5) as `len(blocks) == len(FIELDS) + 1` |
| `tests/features/test_features_bounds.py:312-318` (FEA-11.3 docstring) | "each `exact` block … holds only 0.0 and 1.0" | amended: the five **indicator** blocks; the strength block is `exact` over a continuous interval and has its own case |
| `tests/features/test_features_bounds.py:85-86` | `POLICIES = ("saturate","exact","id")` | unchanged (no fourth policy, §A.2) |
| `tests/features/_features_support.py:101-115` (`DECLARED`) and `:171-175` (`DECLARED_BY_SHAPE`) | the absence widths | a **twin** table `DECLARED_STRENGTH` / `DECLARED_BY_SHAPE_STRENGTH` (204/330/434, 41/83/123, 110), so no new case writes those numbers as literals |
| `tests/e2e/_surface.py:163-165` | the same three rows | the same twin, same reason |
| `tests/e2e/test_fam24_normalisation.py:653-...` (FAM-24.4) and `:788-...` (FAM-24.5) | pins 203/329/433 and 40/82/122 and the nine fields | **unchanged** — they assert the absence path, which §A.5 keeps byte-identical. FAM-25.1 and FEA-12.1 carry the strength-on widths |

**Checkpoint-version enumerations:**

| file:line | change |
|---|---|
| `src/agents/checkpoint.py:80-86` / `:71-76` | `SUPPORTED_VERSIONS` gains 6 (§E.1) |
| `tests/agents/test_checkpoint.py:942` (prose naming `(1,2,3,4)`) and `:515-535` (AGT-7.13's version list) | re-quoted against the six-member tuple |
| `tests/agents/test_counterfactual.py:106`, `:290`, `:911`, `:936`, `:959`, `:1001`, `:1130` | unchanged in value (v5 pins); each gains a sibling asserting v6's two fields exist **only** when declared |
| `tests/integration/agents/test_join_resolution.py:76` | `STRENGTH_FORMAT_VERSION = 6` beside `COUNTERFACTUAL_FORMAT_VERSION = 5` |
| `tests/e2e/test_fam22_counterfactual.py:1712-1782` and `tests/e2e/test_fam19_shapes.py:670-690`, `:751` | unchanged in value; the shipped-container case (`SHIPPED_VERSION`) keeps asserting **v1** |

**Readout assertions: none change.** Every `set(readout) == set(S.READOUT_FACTS)` comparison stays green because §B.2 keeps the readout at eleven facts, and one **new** case asserts the strength key is *not* a readout fact (FAM-25.6).

### F.2 New assertions — names in the project's convention

**`tests/features/` (`tests/features/test_features_strength.py`, FEA-12):**

* **FEA-12.1** the strength block is the tenth and last block of both encodings on all three shapes; its offset is the **pre-change width** (203/329/433 and 40/82/122), its width 1, and the declaration's width is +1 — never a moved offset for any earlier block.
* **FEA-12.2** the dense slot carries `p` exactly for `p ∈ {0.0, 0.25, 0.5, 0.87, 1.0}` at `float32`, on all three shapes; a value of `−0.01`, `1.01`, `nan` or `inf` is **refused by name** (naming `'strength'`), never clamped, defaulted or dropped.
* **FEA-12.3** the token slot is the last id, drawn from the eight-band ladder over `[0,1]`: `0.0 → 102`, `0.05 → 102`, `0.051 → 103`, `0.30 → 105`, `0.61 → 108`, `1.0 → 109`; the ladder is total (every value in `[0,1]` maps to exactly one id); no band emits the pad; the declaration's vocabulary is 110 on every row while the spec of the *absence* encoder still declares 96/102.
* **FEA-12.4** a strength-declaring encoder **refuses** a readout that carries no `strength` key — the anti-silence assertion — and accepts one that carries it, on all three shapes and both encodings.
* **FEA-12.5** `observation_spec(...)["fields"]` is the nine for an absence encoder and the ten with `"strength"` **last** for a declaring one; the block count equals the field count on both, and the six spec keys are the six in both.
* **FEA-12.6** the bound table covers the two new tags and every block of a strength-on declaration sits inside a declared bound — FEA-11.1's totality re-run against the strength-on twin, including `holders == [1] * width`.
* **FEA-12.7** the era guard: the absence declaration on all three shapes is the record it was — six-key spec, nine fields, 203/329/433, 40/82/122, vocabularies 96/102 — asserted against the values this change found, not against the new code's own arithmetic.
* **FEA-12.8** `build_encoder(name, strength=<unknown>)` is refused naming the value and the two members, and `strength=None` is the absence and not a defaulting of a member.

**`tests/agents/` (AGT-19, `test_strength.py` and `test_embedding_init.py`):**

* **AGT-19.1** `learners()["strengths"]` is `{none, supervised}` in that order, each a record of `name` and a stable `carries` token (no whitespace, no sentence punctuation), `none` first, and `DEFAULT_STRENGTH` derived from the order.
* **AGT-19.2** a spec naming an uncatalogued member, or a non-string, is refused by name and never mapped onto the default; a spec naming `none` explicitly builds the byte-identical learner an absent key builds (`param_count` and the whole `2·P` array compared, the AGT-18.3 method).
* **AGT-19.3** a version-6 container records `strength` immediately after `counterfactual` and `seeding` immediately after it; a `none`+unseeded learner still writes v3 (default shape) / v4 (other) / v5 (revealed), and v1–v5 refuse either field.
* **AGT-19.4** the seeding is **exact and bounded to the card rows**: after `build_learner` with `embedding_init`, `parameters[w_in]` reshaped `(input_dim, width)` has rows 1..52 equal to `card_rows(model)` bit-for-bit, row 0 and rows 53.. equal to the same seed's unseeded draw, on **both** backends; and the row the forward reads is `(1 + tanh v)/2` — the composition of §D.3, asserted rather than assumed.
* **AGT-19.5** a seed is refused before any mutation for: a dense kind, a source width ≠ the learner's width, a vocabulary below 53, a non-`(52, width)` row set, and a non-finite row — each naming what it got and what it needed, and the learner is not built.
* **AGT-19.6** `param_count` of a strength-on token learner at the default shape and width 50 is **10,753** (10,053 + 700 = 110×50 − 96×50), and the recorded `params.count` is that number; at six seats and width 50 it is **10,906**.
* **AGT-19.7** a seeded learner saved and loaded restores `strength` and `seeding` (`source`, `digest`, `rows`, `width`, `space`) byte for byte; `load(spec)` compares both against the file and refuses a disagreement naming both values — and a container that carries `strength: supervised` but no `seeding` is *legal and distinguishable*, which is the anti-confusion assertion.
* **AGT-19.8** `as_policy`'s policy carries `strength` and `seeding`, and neither is read by a decision: the same two decisions at the same mask on the same learner, with and without the labels, are one answer.
* **AGT-19.9** the width exemption is version-scoped: a v6 strength-on container loads at its own 204/vocabulary 110, while a v3 container whose `representation.size` was doctored to 204 is still refused naming both numbers (the existing `test_checkpoint.py:1059-1067` refusal, re-run).

**`tests/training/` and `tests/integration/training/` (TRN-9):**

* **TRN-9.1** `_check_strength` refuses an uncatalogued member at the configuration and at each entry as `IgnoredDeclaration` (the D-19/D-20/D-43 pattern at `declarations.py:691-791`), and a `strength_source` declared with `strength: none` and no `embedding_init` is refused as a declaration the run would not use (the `_check_hyper` precedent at `:642-688`).
* **TRN-9.2** a two-arm pair differing only in `strength` trains both arms; the record's `variants` rows name the member on the non-default arm **only**, the run-level `strengths` set appears only then, and a default configuration's record is field-for-field its captured form.
* **TRN-9.3** the join: `training.declarations.STRENGTH_SOURCES` equals `features`' declared table row for row (the restatement pattern of `SHAPE_HISTORY`, `declarations.py:90-96`).
* **TRN-9.4** a declared `strength` is never silently dropped: the spec handed to `agents.build_learner` carries the key, the encoder was built **with** the member (`observation_spec(encoder)["shape"]` is 204/41), and the learner's `strength` is the declared member — three witnesses to one declaration.

**`tests/evaluation/` (EVL-12):** **EVL-12.1** `policy_from` of a strength-arm checkpoint builds the encoder **with** the recorded member (the fourth recorded fact) and its policy decides; a v6 container whose `strength` field was removed is refused at `_read_container`.

### F.3 The end-to-end case

**FAM-25.1 — a seeded, strength-fed learner trains for a few hands.** In `tests/e2e/test_fam25_strength.py`, through declared surfaces only:

* configuration: `six-seat-no-limit-100`, one variant, `backend: "torch"`, `encoding: "card-tokens"`, `architecture: {kind: "token-embedding", width: 50, depth: 2}`, `utility: "stack-shortfall"`, `learning_rule: "masked-q-learning"`, `strength: "supervised"`, `strength_source: "attn-60"`, `embedding_init: {"source": "attn-60", "rows": "cards"}`, the three folders as the pool, `seeds: (0,)`, **budget 30 hands** (≥ ten so the snapshot rule holds, `loop.py:133-137`);
* assertions: the run returns green; `record["variants"][0]["strength"] == "supervised"`; `record["variants"][0]["seeding"]["source"] == "attn-60"` with a 16-hex digest; the final container's `format_version` is **6** with both fields; its `parameters.npy` reshaped at `(110, 50)` has rows 1..52 equal to `card_rows` of the same source; every observation of the run is **123 ids** with its last id in `102..109`; the greedy block's `mode` is `"off"` and its records are unchanged in shape;
* **the control in the same case**: the identical configuration with `strength` and `embedding_init` absent trains green and writes a **version-4** container with a 122-long sequence over 102 ids — so the two arms differ in exactly the declared axis (D-3) and in nothing else;
* **FAM-25.2** the value is not a constant and not card-blind: on the loaded-deal instrument (D-70/D-71's suite, `docs/L1/loaded-deal.md`), `AA` and `72o` on the same dry board map to **different bands**, and the probability is in `[0,1]` at every decision of both hands — the assertion D-71 shows a policy cannot make but a supervised input can.
* **FAM-25.6** the strength key is **not** a readout fact: the run's own decisions' readouts still hold exactly the eleven facts.

### F.4 The map and ceiling bookkeeping (a test-visible change)

`features` 7 → **11** endpoints; the map 50 → **54**; `strata/modules.json:15-24` (`"endpoints": 7`) → 11; `docs/L1/module-map.md:18` and `:63`'s count sentence; `docs/L1/e2e-surface.md` §3.2's row count and five new rows; and every `features` harness ceiling moves 120 → 160 (`50 + 10×N`, `module-map.md:61-65`). `strata-lint` enforces the three-way equality, so this is not optional prose.

---

## G. Risks, and the smallest reversible slice

### G.1 Risks, each with the measurement behind it

1. **The value is systematically wrong where play is decided.** The supervised target is marginal over random opponents (D-83) and at convergence the model is a *lock detector*: D-95 measured **2.71 %** predicted for trip aces against a true 91.84 %. Feeding it as an input teaches the policy a wrong ordering in exactly the region where folding decisions live. *Mitigation:* it is an input and never a target (the target stays the utility axis' business, D-20); the source is **named in the record** so a result is attributable to one calibration profile; the recommended default is `attn-60` (battery mean |err| 11.9, D-98), not the 400-epoch model (24.2); and the acceptance instrument is the extremes battery (D-91/D-94), not an aggregate R².
2. **The squash compresses the seed.** §D.3: the learner reads `squash(v)`, a monotone but distance-distorting map, and the bounded embedding costs a third of the explanatory power (D-84, D-87). *Mitigation:* the composition is asserted (AGT-19.4) and reported; a read-space seed waits on the `no-squash` axis.
3. **The card rows still barely learn, and this change does not fix it.** The shipped pooler is unmasked (§0.2), so 108 of 122 positions are pad and D-75's dilution stands; growing the sequence to 123 changes that factor by 0.8 %. A strength-fed, seeded run's card rows will still move ~0.02 % per 5,000 hands (D-78, D-80). *Mitigation:* the seeding supplies the card information in that interval, which is precisely why D-97's two changes travel together; and this change is **forbidden** from shipping a mask change at the same time.
4. **ASM-10's matched-budget claim is defeated for a strength-on/off pair** (+36 dense, +400…+700 token). *Mitigation:* the pair declares one `param_budget` (which `pair_difference` requires, `declarations.py:184-193`) and both arms' **measured** `param_count` are reported beside it; the report may not call the pair matched.
5. **A strength variant imports torch whatever its backend** (the value's production is torch). A `numpy` variant declaring `strength: supervised` is legal and imports torch. *Mitigation:* stated, and the `numpy`-checkpoint-imports-no-torch guard (`tests/agents/test_checkpoint.py:515`) is confined to the loading path, which is untouched.
6. **`evaluation.policy_from`'s "exactly three facts" contract** becomes four (`src/evaluation/policy.py:23-30`). *Mitigation:* the fourth is read from the container's own metadata; a container played by a reader that ignores it fails as a named size mismatch, never silently.
7. **The `sized_by_kind` equality is the one-line trap** (§E.2). *Mitigation:* version-scoped, and both directions asserted.
8. **Two state-dict layouts.** A loader that maps only one refuses the other; D-93's re-run and D-98's three models disagree on attribute names. *Mitigation:* two declared layout rows plus a refusal by name for a third shape, and a case that loads **both** files.
9. **Cost.** One model forward per decision: D-100 measured 197 µs per sample at batch 1, so ~3.9 ms/hand at 20 decisions against the product learner's measured 0.19 s/hand — about **2 %**, and the model load is once per learner build. Acceptable; recorded so the next deep run's wall clock is not a surprise.

### G.2 The staged slice — each stage independently green and independently revertible

| stage | scope | green on | rollback |
|---|---|---|---|
| **S1 — the fact** (`features` only) | the two writers, the two bound records, the tenth block behind `build_encoder(..., strength=…)`, `_fields`, the FEA-12 battery. **No axis, no model, no container, no training change**; the value is supplied by the test | the whole existing battery, untouched | delete the kwarg's branch; the absence path never saw it |
| **S2 — the axis and the container** (`agents` + `training/declarations.py`) | `strengths` catalogue member, `Learner.strength`/`seeding`, format version 6, `embedding_init` seeding from a **supplied** row array, AGT-19, TRN-9.1-9.2 | S1's battery; nothing writes v6 unless declared | stop declaring the member; v6 is additive and nothing reads it |
| **S3 — the model and the loop** (`features.cardmodel` + `training/loop.py`, `episode.py`, `policies.py`) | the four entry points, the source table, the three spec keys, the loop's forwarding and the four injection sites, the record keys, TRN-9.3-9.4, FAM-25.2 | FAM-25.1's *arm*, with and without the seed | stop declaring `strength`/`embedding_init`; the model is inert |
| **S4 — evaluation** | the fourth recorded fact, the policy wrapper, EVL-12.1, FAM-25.4 | a strength member played as an opponent | play strength members only in-process |
| **S5 — the experiment** | a `strength: supervised` + `embedding_init` arm against D-97's **zeroed control** at the product's own learner, six seats, seeds 0–2, the loaded-deal battery as the instrument, chips reported and never thresholded (D-6, D-82's sample-size lesson) | the run records | nothing to roll back; it is a configuration |

**S1 alone is the reversible probe that answers the briefest question** — does a tenth declared slot break anything at all — and it does so without touching a checkpoint, which is what keeps the era boundary a single, dated fact (§E) instead of a moving one.

### G.3 What this design rejects, with the alternative recorded

* **an always-declared strength block** — would silently reinterpret every saved checkpoint (D-61/D-69's measured cost) and rewrite ~250 width assertions across nine test files. *Rejected:* the opt-in declaration of §A.5.
* **a twelfth readout fact** — puts a model in the engine (§B.1). *Rejected:* the injected derived key.
* **a seventh module for the card model** — contradicts `module-map.md:87-96`. *Rejected:* four names on `features`.
* **a read-space seed via `arctanh`** — undefined for the supervised rows. *Rejected:* a parameter-space copy with the composition asserted.
* **strength as a target or a reward term** — that is the utility axis (D-20), and mixing it with the input confounds D-3's one-axis rule. *Rejected.*

### G.4 What needs L0 before L2 starts

The change is a surface change (four entry points, a seventh catalogue key, format version 6) and D-92 already priced it as gated ("the surface change D-61 priced, requiring the gate (D-10)"). D-10's two independent reviews are owed, and one decision row should record: the member names (`none`/`supervised`), the source table and its default (`attn-60`), the eight bands' edges, and the era declaration of §E.4.

```json
{
  "unit": "phase1",
  "from": "L1",
  "to": "L0",
  "verdict": "PASS",
  "artifact": "L1 design of the strength fact, the strength axis and supervised embedding seeding (this return, sections A-G); no file written",
  "testIds": [
    "FEA-12.1-12.8", "AGT-19.1-19.9", "TRN-9.1-9.4", "EVL-12.1",
    "FAM-25.1", "FAM-25.2", "FAM-25.4", "FAM-25.6"
  ],
  "assumptions": [
    {
      "id": "ASM-46",
      "text": "the strength block is opt-in on the encoder declaration (build_encoder's strength keyword). Its absence is today's encoder byte for byte, so 203/329/433 and 40/82/122 over 96/102 stand and no saved checkpoint is reinterpreted",
      "alternative": "an always-declared tenth block, which grows every width unconditionally and silently reinterprets every shipped container (the cost D-61/D-69 measured) and rewrites ~250 width assertions"
    },
    {
      "id": "ASM-47",
      "text": "the value reaches the observation as an injected derived key in a copy of the readout, produced by four new features entry points (load_strength, strength, stated, card_rows); the readout stays eleven facts and the engine stays model-free",
      "alternative": "a twelfth engine readout fact, which puts a neural network inside engine and breaks the closed eleven-fact set that four test helpers and ~40 comparisons assert"
    },
    {
      "id": "ASM-48",
      "text": "the token path carries strength as one id from an eight-band ladder over [0,1], ids 102-109, vocabulary 110 on every row, one shape-invariant ladder in a module constant",
      "alternative": "a per-row base (104 at two seats, 110 at six), which makes the same band mean two ids and restates one ladder three times"
    },
    {
      "id": "ASM-49",
      "text": "the seeding copies the source's (53,50) card rows 1..52 into the parameter block as raw values, so the learner reads squash(v); the copy is parameter-exact and the record names the space",
      "alternative": "a read-space copy via arctanh(2v-1), which is undefined for the supervised rows because nn.Embedding weights are unbounded reals"
    },
    {
      "id": "ASM-50",
      "text": "a strength-declaring or seeded learner is a format version 6 container with two conditional fields, and the sized_by_kind width equality applies to versions 1-5 only",
      "alternative": "no version bump, reusing v3/v4 on a widened container, which would make an old reader accept an observation width it cannot encode"
    },
    {
      "id": "ASM-51",
      "text": "the declared sources are attn-60 (.probe/attn60.pt, layout pos/n1/n2) and attn-400 (.probe/attnconv.pt, layout posemb/norm/ffn), with attn-60 the recommended default",
      "alternative": "attn-400, the converged model, which is the worst calibrated in the middle (battery mean |err| 24.2) and the least varied play (D-95, D-98)"
    }
  ],
  "citations": [
    "docs/L1/normalisation.md §2-§5",
    "docs/L1/shapes.md §2, §8",
    "docs/L1/seats.md §3",
    "docs/L1/module-map.md §4, §7",
    "docs/L1/e2e-surface.md §2, §3.2",
    "strata/decisions.md D-3, D-19, D-20, D-43, D-61, D-69, D-79, D-83, D-86, D-92, D-93, D-95, D-97, D-98, D-100",
    "src/features/declarations.py:58-68, :268-302, :359-412",
    "src/features/encode.py:36-38, :327-343, :363-368",
    "src/agents/checkpoint.py:21-45, :500-723",
    "src/training/loop.py:348-381, :441-467",
    "src/training/declarations.py:158-193, :691-791, :831-870",
    "src/agents/numpy_backend.py:106-179"
  ],
  "question": "does L0 authorise this surface change (four features entry points, a seventh learners() catalogue key, format version 6) as the price of wiring the supervised card model into the product's learner, which D-92 left undone and priced as gated?"
}
```