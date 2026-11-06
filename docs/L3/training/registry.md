# training — the registry as data

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-05
- **Owner:** `rungs()` and `rung()` — the six rows as literal data (§1), the resolved configuration key by key (§2), the pool
  entry and the read-back id (§3), the parameter arithmetic (§4), the refusals and the determinism of resolution (§5)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `README.md` §3, §7, `loop.md` §1, §5, `checkpoints.md` §5, `fairness.md` §2, `errors.md` §4

## 1. The six rows (D1)

`RUNGS` in `declarations.py` is one literal table; `rungs()` reads it and adds no code path (D-3, `surface.md` §2). The order
is brief §2's and is never rearranged without an L0 decision (D-2, FAM-3.1). Nine variants, one row each:

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

The **order within a rung is the order above**, so a run trains R4's `wide` then its `deep` (`loop.md` §2). R1–R3 carry one
variant; R4–R6 carry the pair that is the rung's own control (ASM-9, `ladder.md` §2). `dense` and `deep` are **variant
names**, never kind names: R5's `dense` arm is the `deep` kind at `sparsity` 0 (`agents/surface.md` §3).

Per rung, three declarations the battery reads as text and as names (FAM-3.4, FAM-3.5, FAM-3.6–3.10):

| Rung | `axis` — the sentence `rung(name)["axis"]` carries | `primary` | `carried_from` |
|---|---|---|---|
| R1 | `encoding — a naive numeric encoding, hand-rolled NumPy (D-7)` | `naive-numeric` | `None` |
| R2 | `backend — the same model in PyTorch, for the speed difference (D-7)` | `naive-numeric-torch` | `naive-numeric` |
| R3 | `tokenisation — card tokenisation into a learned embedding` | `card-tokens` | `naive-numeric-torch` |
| R4 | `width against depth, at one budget` | `deep` | `card-tokens` |
| R5 | `dense against sparse connectivity, at one budget` | `dense` | `deep` |
| R6 | `residual — a residual path against none, at R5's depth` | `residual` | `dense` |

Each `axis` is `ladder.md` §2's rung-row sentence under a one-word label, and the label is what makes FAM-3.6–3.10 read as
text: R1 names `encoding`, R2 `backend`, R3 `tokenisation`, R4 `width`/`depth`, R5 `dense`/`sparse`/`connectivity`, R6
`residual`. `carried_from` is the previous rung's **variant name**, the primary the next rung inherits (D-16, `ladder.md` §2).

**The declarations every variant entry shares** (`records.md` §2, `ladder.md` §3), written once in `declarations.py`:

    LEARNING_RULE = "masked-q-learning"                       # ASM-7
    HYPER = {"learning_rate": 0.001, "batch_size": 32, "target_update_interval": 200, "optimiser": "sgd",
             "exploration": {"start": 1.0, "end": 0.05, "samples": 2000}, "discount": 0.99}
    PARAM_BUDGET = 10000          # ASM-10; the ±2% bound is 9,800 … 10,200
    LIVE_BUDGET  = 1000           # hands per variant per seed, live (ASM-8)
    SEEDS        = (0, 1, 2)      # protocol.md §2
    DEVICE       = "cpu"          # D-8
    TABLE        = "live"         # league.md §6
    RETAINED, SNAPSHOTS = 5, 10   # M and the ten snapshot points (ASM-18)

`HYPER` is the record `agents.learners()["hyper"]` publishes, copied here as the run record's data and never compared against
it (`agents/surface.md` §3, `rule.md` §6); `param_budget` is **declared** and no run measures it (`surface.md` §4). Each rung's
`snapshot_every` is 100 — its declared budget's interval, 1000 ÷ 10 — and `loop.md` §3 fixes what a run does with it.

## 2. The resolved configuration, key by key (D2)

`rung(name)` returns one mapping with these keys and no other (`ladder.md` §3, `surface.md` §3):

| Key | Value |
|---|---|
| `name` | the rung name, `"R1"` … `"R6"` |
| `axis` | §1's sentence for that rung |
| `carried_from` | `None` for R1, else the previous rung's primary variant name |
| `primary` | this rung's primary variant name |
| `variants` | one or two `records.md` §2 entries in §1's order, each carrying `name`, `backend`, `encoding`, `architecture` (`kind`, `width`, `depth`, `sparsity`, `residual`), `learning_rule`, `hyper`, `param_budget`, `samples`, `seeds`, `device`, `snapshot_every`, `table` |
| `pool` | §3's pool entry |
| `seeds`, `samples`, `param_budget` | `(0, 1, 2)`, `1000`, `10000` |
| `table`, `device`, `snapshot_every` | `"live"`, `"cpu"`, `100` |

The last three rows are this module's own keys and duplicate the entries' values deliberately: `run` reads the configuration's
values when an argument is omitted (`loop.md` §5), and a reader sees the budgets without walking the variants. Every value is
plain data (`e2e-surface.md` §1, D-1). **Resolving is not training**: `rung` plays no hand, builds no encoder or learner,
writes no file and moves no stream (D-3, `surface.md` §3); it reads the index's declared windows and calls
`evaluation.build_pool`/`pool_members`, both pure (`evaluation/surface.md` §5, §6).

## 3. The pool entry, and the id it carries (D2)

    "pool": {"id": ..., "lineage": <carried_from or None>, "m": 5, "frozen": True,
             "members": [<records.md §7 version records, in lineage order>]}

`_pool_entry(name, carried_from)` builds it in four steps and no others:

1. `_window(carried_from)` reads the declared window of the rung this one inherits — `index.SHIPPED_WINDOWS[carried_from]`,
   version records in lineage order — and **drops every version whose `path` names no readable file**, so a declared but absent
   lineage checkpoint leaves the window short and the record states the membership it used (`protocol.md` §5, `loop.md` §3).
   R1 has no `carried_from`, so its window is empty and its pool is the three baselines alone (FAM-3.17).
2. The declaration is `{"members": <that filtered window>, "m": 5, "frozen": True}` — `records.md` §8's shape, with no
   baselines in it, because `build_pool` adds and pins them itself.
3. `evaluation.build_pool(declaration)`, then `evaluation.pool_members(pool)`; a refusal from either **propagates unrepaired**
   (`surface.md` §4, `e2e-surface.md` §2).
4. `id` is the read-back's `id` and `members` is the filtered window as declared; the read-back's own member list (baselines
   first, then the window) is **not** copied into the configuration, because it belongs to the run record (`loop.md` §4).

So **the declared `id` is the read-back id of the membership the repository actually carries** — never a fabricated one and
never two (D2, `records.md` §8). Two arms of one rung name one pool entry, hence one id (FAM-3.17, FAM-3.18, ASM-16).

**A configuration in no registry** carries the same entry and supplies its own `members` and `id`, which is how a custom league
reaches the loop as data (`ladder.md` §3, FAM-15.4). Its members may carry no `path`: they are filtered out by step 1's
readability rule, the pool it trains against is the three baselines, and its run record still carries **its own declared id**
(`loop.md` §4, FAM-15.2).

## 4. The parameter budget, shown as arithmetic (ASM-10)

`param_count` is `docs/L3/agents/architecture.md` §5's sum at `I = 203` and `V = 96` (`features/surface.md` §5): input block,
trunk, then `3·W + 3`. `sparse`'s trunk term is `D·(k + W)` with `k = round((1 − s)·W²)` = `round(0.5 × 3,844)` = **1,922**.

| Variant | Input | Trunk | Output | Total | Inside 10,000 ± 2% (9,800–10,200) |
|---|---|---|---|---|---|
| `naive-numeric`, `naive-numeric-torch` | 203·36 + 36 = 7,344 | 2·(1,296 + 36) = 2,664 | 3·36 + 3 = 111 | **10,119** | yes |
| `card-tokens` | 96·50 = 4,800 | 2·(2,500 + 50) = 5,100 | 3·50 + 3 = 153 | **10,053** | yes |
| `wide` | 96·62 = 5,952 | 1·(3,844 + 62) = 3,906 | 3·62 + 3 = 189 | **10,047** | yes |
| `deep`, `dense`, `residual`, `plain` | 96·50 = 4,800 | 2·(2,500 + 50) = 5,100 | 3·50 + 3 = 153 | **10,053** | yes |
| `sparse` | 96·62 = 5,952 | 2·(1,922 + 62) = 3,968 | 3·62 + 3 = 189 | **10,109** | yes |

The four comparison pairs the battery measures through `agents.param_count` (FAM-3.15, FAM-13.3): R1–R2 **0** apart on
10,119; R4 `wide`–`deep` **6** apart against a tolerance of 201; R5 `dense`–`sparse` **56** apart, tolerance 202; R6
`residual`–`plain` **0** apart. All nine variants and all four pairs land inside ASM-10's ±2%, which is what the literals are
for: a pair differs on its axis and on nothing else, capacity included (`ladder.md` §4, §6). `sparse`'s trunk shrinks with
`s`, so it matches its dense mate by being declared **wider** (`architecture.md` §5). R4's `wide` declares `depth` 1 so the
declared depth and the kind's single trunk layer agree; the kind does not read the setting (`architecture.md` §3).

## 5. `rungs()`, `rung()`, and the determinism of resolution

- `rungs()` returns `{name: rung(name)}` for `RUNG_NAMES`'s six names in order, so the registry is read one way and not two
  (FAM-3.1, FAM-3.2); two calls return equal records in that order (`surface.md` §2).
- `rung(name)` returns `_configuration(name)`, whose `pool` is `_pool_entry(name, carried_from)`. **A rung name that is a
  configuration is still not a configuration**: `rung("R7")` refuses, and a configuration reaches the loop through `run` and
  no other entry point (`surface.md` §3, FAM-15.5, FAM-16.28).
- One name resolves one configuration whose `pool.id` is the id the run record will carry, both being the read-back id of one
  declaration (`surface.md` §3, FAM-4.7); a changed membership changes the id and nothing else (`records.md` §8).

**The one refusal of this document** is `UnknownRung`, raised by `rung` for a name `RUNG_NAMES` does not carry, with the name in
the message — `training.rung refused the rung name 'R7-bottleneck': the registry carries R1, R2, R3, R4, R5, R6` (`errors.md`
§4). A value that is not a string is the same refusal with that value named (`errors.md` §2), and `rungs()` refuses nothing.

## 6. What is left to L4

Whether `RUNGS` is a tuple of mappings or a dict of them, a mapping's key order, whether `_configuration` caches, and every
private name other than `_configuration`, `_pool_entry`, `_window` and `RUNG_NAMES`, whose spellings and signatures are
contract for `tests/training/` (`README.md` §4). Not L4's: the nine literals, the shared declarations, the six axis sentences,
the schema's keys, the pool entry's five keys, the readability filter and the read-back id, and §4's arithmetic.
