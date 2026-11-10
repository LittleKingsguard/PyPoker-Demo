# training — the registry as data

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 4 · **Date:** 2026-11-09
- **Owner:** `rungs()` and `rung()` — the six rows as literal data (§1), the resolved configuration key by key (§2), the pool entry and the read-back id (§3), the parameter arithmetic (§4), the refusals and the determinism of resolution (§5); **Rev 2** states that a row's `learning_rule` is what the six rows declare and not a rule a run is fixed to, refused only against the catalogue (D-19); **Rev 3** gives the inherited window's members their `rule` (§3); **Rev 4** adds `game` to the configuration schema — optional, at either level, absence meaning the default shape and never a name defaulted — and states that the six rows declare none (`shapes.md` §1–§3, D-29)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `README.md` §3, §7, `loop.md` §1, §5, `record.md` §3, `checkpoints.md` §5, `fairness.md` §2, §7, `errors.md` §4, `shapes.md` §2–§3

## 1. The six rows (D1)

`RUNGS` in `declarations.py` is one literal table; `rungs()` reads it and adds no code path (D-3, `surface.md` §2). The order is brief §2's and is never rearranged without an L0 decision (D-2, FAM-3.1). Nine variants, one row each:

| Rung | Variant | `backend` | `encoding` | `architecture`: `kind`, width, depth, sparsity, residual | Params | The pool it trains against |
|---|---|---|---|---|---|---|
| R1 | `naive-numeric` | `numpy` | `flat-numeric` | `naive-stack`, 36, 2, 0.0, false | 10,119 | the three baselines alone: R1 inherits no lineage |
| R2 | `naive-numeric-torch` | `torch` | `flat-numeric` | `naive-stack`, 36, 2, 0.0, false | 10,119 | R1's retained window + the baselines |
| R3 | `card-tokens` | `torch` | `card-tokens` | `token-embedding`, 50, 2, 0.0, false | 10,053 | R2's retained window + the baselines |
| R4 | `wide` | `torch` | `card-tokens` | `wide`, 62, 1, 0.0, false | 10,047 | R3's retained window + the baselines, one pool for both arms |
| R4 | `deep` (primary) | `torch` | `card-tokens` | `deep`, 50, 2, 0.0, false | 10,053 | as above |
| R5 | `dense` (primary) | `torch` | `card-tokens` | `deep`, 50, 2, 0.0, false | 10,053 | R4's retained window + the baselines, one pool for both arms |
| R5 | `sparse` | `torch` | `card-tokens` | `sparse`, 62, 2, 0.5, false | 10,109 | as above |
| R6 | `residual` (primary) | `torch` | `card-tokens` | `residual`, 50, 2, 0.0, true | 10,053 | R5's retained window + the baselines, one pool for both arms |
| R6 | `plain` | `torch` | `card-tokens` | `plain`, 50, 2, 0.0, false | 10,053 | as above |

The **order within a rung is the order above**, so a run trains R4's `wide` then its `deep` (`loop.md` §2). R1–R3 carry one variant; R4–R6 carry the pair that is the rung's own control (ASM-9, `ladder.md` §2). `dense` and `deep` are **variant names**, never kind names: R5's `dense` arm is the `deep` kind at `sparsity` 0 (`agents/surface.md` §3).

Per rung, three declarations the battery reads as text and as names (FAM-3.4, FAM-3.5, FAM-3.6–3.10):

| Rung | `axis` — the sentence `rung(name)["axis"]` carries | `primary` | `carried_from` |
|---|---|---|---|
| R1 | `encoding — a naive numeric encoding, hand-rolled NumPy (D-7)` | `naive-numeric` | `None` |
| R2 | `backend — the same model in PyTorch, for the speed difference (D-7)` | `naive-numeric-torch` | `naive-numeric` |
| R3 | `tokenisation — card tokenisation into a learned embedding` | `card-tokens` | `naive-numeric-torch` |
| R4 | `width against depth, at one budget` | `deep` | `card-tokens` |
| R5 | `dense against sparse connectivity, at one budget` | `dense` | `deep` |
| R6 | `residual — a residual path against none, at R5's depth` | `residual` | `dense` |

Each `axis` is `ladder.md` §2's rung-row sentence under a one-word label, and the label is what makes FAM-3.6–3.10 read as text: R1 names `encoding`, R2 `backend`, R3 `tokenisation`, R4 `width`/`depth`, R5 `dense`/`sparse`/`connectivity`, R6 `residual`. `carried_from` is the previous rung's **variant name**, the primary the next rung inherits (D-16, `ladder.md` §2).

**The declarations every variant entry of the six rows carries** (`records.md` §2, `ladder.md` §3), written once in `declarations.py`:

    LEARNING_RULE = "masked-q-learning"   # the catalogue's first member (rules.md §2, §4, D-19); a row may name another
    UTILITY       = "net-chips"           # the utility catalogue's first member (utilities.md §2, §5, D-20); a row may name another
    HYPER = {"learning_rate": 0.001, "batch_size": 32, "target_update_interval": 200, "optimiser": "sgd",
             "exploration": {"start": 1.0, "end": 0.05, "samples": 2000}, "discount": 0.99}
    PARAM_BUDGET = 10000          # ASM-10; the ±2% bound is 9,800 … 10,200
    LIVE_BUDGET  = 1000           # hands per variant per seed, live (ASM-8)
    SEEDS        = (0, 1, 2)      # protocol.md §2
    DEVICE       = "cpu"          # D-8
    TABLE        = "live"         # league.md §6
    RETAINED, SNAPSHOTS = 5, 10   # M and the ten snapshot points (ASM-18)

`HYPER` is the record `agents.learners()["hyper"]` publishes, copied here as the run record's data and never compared against it (`agents/surface.md` §3, `rule.md` §6); `param_budget` is **declared** and no run measures it (`surface.md` §4). Neither `LEARNING_RULE` nor `UTILITY` is a member the run is fixed to: they are what these six rows declare, and a run refuses one only when the catalogue `declarations.learning_rules()` or `declarations.utilities()` reads from `agents.learners()` does not carry it (`loop.md` §1 step 1, `rules.md` §4, `utilities.md` §5, D-19, D-20). Each rung's `snapshot_every` is 100 — its declared budget's interval, 1000 ÷ 10 — and `loop.md` §3 fixes what a run does with it.

**The three shape declarations, and the six rows declare none.** `declarations.py` also carries `SHAPE_NAMES`, the two declared shapes' names in the catalogue's order with the default first; `DEFAULT_SHAPE`, that first name; and `SHAPE_ACTIONS`, `{"fixed-limit-20": 3, "no-limit-100": 6}` — each shape's descriptor count, which is its head's width and the number of indices `features.decode_action` answers for it (`shapes.md` §2, `sizing.md` §3, §6, D-29). They are a restated table and not a second claim: `engine.game_shapes()` is granted to nobody and `features.action_space` is not this module's, so the names, their order and their counts are held equal to those two calls by the integration battery's shape join, and every descriptor a record reports comes back from `features.decode_action(index, shape=...)` (`docs/L2/training/surface.md` §4.2, `module-map.md` §2, D-13, D-29). Three reads sit on top of them and nothing else does:

- `require_game(value, entry, argument="game")` → the shape name `value` denotes, or `errors.UnknownShape` naming the level, the value and **both declared names**. `None` is the **default** shape — the absence of a name and never a name defaulted — and a value the two names do not carry, a non-string included, is refused and never substituted (`shapes.md` §2–§3, `errors.md` §4, D-13, D-29).
- `shape_actions(shape=None)` → **`A`**, that shape's descriptor count, `3` or `6`, read off `SHAPE_ACTIONS` for the name `require_game` resolved, so no caller spells a number inline.
- `vocabulary(shape=None)` → `{index: descriptor}` for that shape, each descriptor read through the granted `features.decode_action(index, shape=...)` over `range(shape_actions(shape))`, so the module holds no spelling of a descriptor and the default shape answers the `{0: fold, 1: check-call, 2: raise}` a run has always reported (`features/surface.md` §7, §9, `fairness.md` §4, `record.md` §3, D-13).

**No row of the six declares a `game`**, so every rung — and every pair of rungs — is on the default shape, and the ladder's one game is unchanged by D-29 (`shapes.md` §1, §5, D-2, D-3).

## 2. The resolved configuration, key by key (D2)

`rung(name)` returns one mapping with these keys and no other (`ladder.md` §3, `resolve.md` §3):

| Key | Value |
|---|---|
| `name` | the rung name, `"R1"` … `"R6"` |
| `axis` | §1's sentence for that rung |
| `carried_from` | `None` for R1, else the previous rung's primary variant name |
| `primary` | this rung's primary variant name |
| `variants` | one or two `records.md` §2 entries in §1's order, each carrying `name`, `backend`, `encoding`, `architecture` (`kind`, `width`, `depth`, `sparsity`, `residual`), `learning_rule`, `utility`, `hyper`, `param_budget`, `samples`, `seeds`, `device`, `snapshot_every`, `table` |
| `pool` | §3's pool entry |
| `seeds`, `samples`, `param_budget` | `(0, 1, 2)`, `1000`, `10000` |
| `table`, `device`, `snapshot_every` | `"live"`, `"cpu"`, `100` |
| `game` | **not a key of the resolved mapping, and that is the declaration**: a row names no shape, so its configuration resolves to the catalogue's first through `declarations.require_game`, and a run that resolves one records it (`shapes.md` §3, `loop.md` §1 step 1, D-29) |

The last three rows are this module's own: the first two duplicate the entries' values deliberately, because `run` reads the configuration's values when an argument is omitted (`loop.md` §5) and a reader sees the budgets without walking the variants, and `game` is **absent** rather than `None` because absence *is* the default shape and a key spelled `None` is no claim either (`loop.md` §1 step 1, `shapes.md` §3, D-29). Every value is plain data (`e2e-surface.md` §1, D-1). **Resolving is not training**: `rung` plays no hand, builds no encoder or learner, writes no file and moves no stream (D-3, `resolve.md` §3); it reads the index's declared windows and calls `evaluation.build_pool`/`pool_members`, both pure (`evaluation/pool.md` §1–§2).

## 3. The pool entry, and the id it carries (D2)

    "pool": {"id": ..., "lineage": <carried_from or None>, "m": 5, "frozen": True,
             "members": [<records.md §7 version records, in lineage order>]}

`_pool_entry(name, carried_from)` builds it in four steps and no others:

1. `_window(carried_from)` reads the declared window of the rung this one inherits — `index.SHIPPED_WINDOWS[carried_from]`, version records in lineage order, each carrying its `rule` and `utility` — and **drops every version whose `path` names no readable file**, so a declared but absent lineage checkpoint leaves the window short and the record states the membership it used (`protocol.md` §5, `loop.md` §3); R1 has no `carried_from`, so its window is empty and its pool is the three anchor baselines alone (FAM-3.17, D-20).
2. The declaration is `{"members": <that filtered window>, "m": 5, "frozen": True}` — `records.md` §8's shape, with no baselines in it and **no `baselines` key either**, because `build_pool` adds and pins the three anchor baselines itself; a registry row therefore declares no folding baseline, and the six rows resolve to exactly the pool ids they resolve to today (ASM-32, D-21). No `game` key is declared here either: `loop._pool` adds the run's resolved shape to the declaration it forwards, because a pool is one shape's and the row's shape is the catalogue's first (`loop.md` §1 step 2, `shapes.md` §3, D-29).
3. `evaluation.build_pool(declaration)`, then `evaluation.pool_members(pool)`; a refusal from either **propagates unrepaired** (`surface.md` §4, `e2e-surface.md` §2).
4. `id` is the read-back's `id` and `members` is the filtered window as declared; the read-back's own member list is **not** copied into the configuration, because it belongs to the run record (`loop.md` §4, `record.md` §1).

So **the declared `id` is the read-back id of the membership the repository actually carries** — never a fabricated one and never two (D2, `records.md` §8; ASM-27, whose digest covers each version's `rule` and its `utility`). Two arms of one rung name one entry, hence one id (FAM-3.17, FAM-3.18, ASM-16).

**A configuration in no registry** carries the same entry and supplies its own `members` and `id`, which is how a custom league reaches the loop as data (`ladder.md` §3, FAM-15.4). Its members may carry no `path`: they are filtered out by step 1's readability rule, the pool it trains against is the pinned baselines — the three anchors, plus any its own `baselines` names — and its run record still carries **its own declared id** (`loop.md` §3, FAM-15.2, ASM-32, D-21). Such a configuration may also declare `game`, at its own level or at an entry's, and then its pool is that shape's pool and its run record says so — which is the one route by which the second shape is reached, because no rung of §1 declares it (`registry.md` §1, `shapes.md` §1, §3, `ladder.md` §3, D-29).

## 4. The parameter budget, shown as arithmetic (ASM-10)

`param_count` is `docs/L3/agents/architecture.md` §5's sum at `I = 203` and `V = 96` (`features/surface.md` §5): input block, trunk, then `3·W + 3`. At the second shape the output term is `A·W + A` with `A = 6`, so every count below is the default shape's and stays so: no rung declares the other shape (`sizing.md` §6, `shapes.md` §5, D-29). `sparse`'s trunk term is `D·(k + W)` with `k = round((1 − s)·W²)` = `round(0.5 × 3,844)` = **1,922**.

| Variant | Input | Trunk | Output | Total | Inside 10,000 ± 2% (9,800–10,200) |
|---|---|---|---|---|---|
| `naive-numeric`, `naive-numeric-torch` | 203·36 + 36 = 7,344 | 2·(1,296 + 36) = 2,664 | 3·36 + 3 = 111 | **10,119** | yes |
| `card-tokens` | 96·50 = 4,800 | 2·(2,500 + 50) = 5,100 | 3·50 + 3 = 153 | **10,053** | yes |
| `wide` | 96·62 = 5,952 | 1·(3,844 + 62) = 3,906 | 3·62 + 3 = 189 | **10,047** | yes |
| `deep`, `dense`, `residual`, `plain` | 96·50 = 4,800 | 2·(2,500 + 50) = 5,100 | 3·50 + 3 = 153 | **10,053** | yes |
| `sparse` | 96·62 = 5,952 | 2·(1,922 + 62) = 3,968 | 3·62 + 3 = 189 | **10,109** | yes |

The four comparison pairs the battery measures through `agents.param_count` (FAM-3.15, FAM-13.3): R1–R2 **0** apart on 10,119; R4 `wide`–`deep` **6** apart against a tolerance of 201; R5 `dense`–`sparse` **56** apart, tolerance 202; R6 `residual`–`plain` **0** apart. All nine variants and all four pairs land inside ASM-10's ±2%, which is what the literals are for: a pair differs on its axis and on nothing else, capacity included (`ladder.md` §4, §6). `sparse`'s trunk shrinks with `s`, so it matches its dense mate by being declared **wider** (`architecture.md` §5); R4's `wide` declares `depth` 1 so the declared depth and the kind's single trunk layer agree (§3).

## 5. `rungs()`, `rung()`, and the determinism of resolution

- `rungs()` returns `{name: rung(name)}` for `RUNG_NAMES`'s six names in order, so the registry is read one way and not two (FAM-3.1, FAM-3.2); two calls return equal records in that order (`surface.md` §2).
- `rung(name)` returns `_configuration(name)`, whose `pool` is `_pool_entry(name, carried_from)`. **A rung name that is a configuration is still not a configuration**: `rung("R7")` refuses, and a configuration reaches the loop through `run` and no other entry point (`resolve.md` §3, FAM-15.5, FAM-16.28).
- One name resolves one configuration whose `pool.id` is the id the run record will carry, both being the read-back id of one declaration (`resolve.md` §3, FAM-4.7); a changed membership changes the id and nothing else (`records.md` §8). And one name resolves one **shape**: a row declaring no `game` resolves to the catalogue's first, so two calls resolve the same game as well as the same id (`shapes.md` §3, D-29).

**The one refusal of this document** is `UnknownRung`, raised by `rung` for a name `RUNG_NAMES` does not carry, with the name in the message — `training.rung refused the rung name 'R7-bottleneck': the registry carries R1, R2, R3, R4, R5, R6` (`errors.md` §4). A value that is not a string is the same refusal with that value named (`errors.md` §2), and `rungs()` refuses nothing. A declared `game` is not this document's refusal: `require_game` raises `UnknownShape` at `run` and at `fairness`, and `rung` resolves no shape of its own (`errors.md` §2, `shapes.md` §3, D-13, D-29).

## 6. What is left to L4

Whether `RUNGS` is a tuple of mappings or a dict of them, a mapping's key order, whether `_configuration` caches, and every private name other than `_configuration`, `_pool_entry`, `_window` and `RUNG_NAMES`, whose spellings and signatures are contract for `tests/training/` (`README.md` §4). Not L4's: the nine literals, the shared declarations, the three shape declarations and the fact that no row declares a `game`, the six axis sentences, the schema's keys with `game` absent from every row, the pool entry's five keys, the readability filter and the read-back id, and §4's arithmetic (`shapes.md` §2, D-29).
