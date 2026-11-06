# agents — a version

- **Owner:** the checkpoint (D-16, ASM-5, ASM-18): what a restore recovers, the exact bytes of the container,
  the file-format version, `save`/`load`'s refusals and the loss-free equality
- **Ceiling:** 110 lines. At the ceiling, split by owner — never append
- **Read with:** `architecture.md` §4–§6, `rule.md` §4–§5, `backends.md` §4

## 1. What a restore must recover

A version is a checkpoint of a run and a league member (D-16), so `save`/`load` is what lets a shipped member decide
as its learner did (`learner.md` §4, `protocol.md` §5). A restore recovers, **from the file alone**:

- the **backend**, `numpy` or `torch` (`backends.md` §1);
- the **kind** and its four resolved settings — width, depth, sparsity and residual — so the model is rebuilt
  before any value is scattered into it (`architecture.md` §1, §3);
- the **representation**: family, size, encoding, `shape` and `dtype` for an encoder build (`architecture.md` §6);
- the learner's **seed** (`surface.md` §4, ASM-2);
- every **parameter value** the update can change, in the declaration order (`architecture.md` §4);
- the **target copy**, its **counter** and the **schedule position**, the only state `learn` moves (`rule.md` §3–§4);
- the **sparse masks**, if the kind pins any weights to zero (`architecture.md` §2);
- the **tie-break**'s rule and tolerance, recorded as the design constant they are (`rule.md` §5).

Nothing the file does not hold is defaulted (`surface.md` §1, §9); the fixed hyper-declarations are the ladder's one
declaration, published by `learners()`, which no per-file copy can drift from (`rule.md` §6, `learner.md` §1).

## 2. The bytes

A checkpoint is a **zip container** with exactly two members, written through an open file handle:

    open(path, "wb")            → the caller's path, byte for byte: no suffix is appended or rewritten
    zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_STORED)
    ├── "metadata.json"          UTF-8 JSON, one object, the fields of §2.1
    └── "parameters.npy"         numpy.lib.format: one array, dtype float64, C order, 1-D

**Why an open handle.** `numpy.savez(path)` appends `.npz`, so a caller's `version-3.ckpt` would come back as
`version-3.ckpt.npz` and `save`'s return, the run record's path and `evaluation.policy_from`'s load would disagree
(`records.md` §7, §12, `e2e-surface.md` §3.4); a handle `save` opened honours the caller's spelling exactly — `.pt`,
`.pth`, `.ckpt`, `.npz` — which is what "writes exactly `path`" means (`surface.md` §8, `e2e-surface.md` §2).

**The array's layout.** One `float64` array of length `2·P + M`, where `P` is `param_count`'s count and `M` the
total number of sparse mask slots:

    [0, P)        the online parameters, in architecture.md §4's declaration order
    [P, 2P)       the target copy, the same order and shapes
    [2P, 2P + M)  each sparse layer's mask in ascending layer order, W² values of 0.0 and 1.0

**Why in the array.** One member only, so each mask rides as `0.0`/`1.0` values and §2.1 records its layer and slots.

### 2.1 `metadata.json`

| Key | Content |
|---|---|
| `format` | `"pypoker-agents-checkpoint"` — the magic name; anything else is not this module's file |
| `format_version` | `1`, an integer (§3) |
| `dtype` | `"float64"` — the array member's type, stated and checked |
| `backend` | `"numpy"` or `"torch"` |
| `kind` | one of the seven kind names (`architecture.md` §1) |
| `settings` | `{"width": W, "depth": D, "sparsity": s, "residual": bool}` — the resolved values in force |
| `representation` | `{"family", "encoding", "size", "shape", "dtype"}` — the sizing record (`architecture.md` §6), `shape` and `dtype` `null` for an encoder-less build |
| `seed` | the learner's seed, an integer |
| `exploration` | `{"position": n, "schedule": {"start", "end", "samples"}}` (`rule.md` §4, §6) |
| `target` | `{"counter": c, "interval": i}` — the target copy's counter and its interval (`rule.md` §3) |
| `params` | `{"count": P, "target_offset": P, "length": 2P + M, "tensors": [{"name", "shape", "offset", "count"}, …], "masks": [{"layer", "slots", "offset", "kept"}, …]}` |
| `tie_break` | `{"rule": "smallest-masked-index-within-tolerance", "tolerance": 1e-09}` (`rule.md` §5) |

`params.count` is `param_count`'s answer. On load the count, the `length` and each sparse mask's `kept` are checked
against the rebuilt layout and the array, so a disagreement is refused (§3) and not half-restored; offsets are not read.

## 3. The format version, and the refusals

`format_version` is `1`. A load reads `format`, `format_version` and `dtype` first and refuses a file that is not
this container, not this magic, not version `1`, or not `float64` — forward compatibility is a new version and
never a guess (`e2e-surface.md` §2). The refusals are the two checkpoint classes of `errors.md` §2:

| Refusal | When |
|---|---|
| `CheckpointUnwritable` | `save`: the path is not a location a file can be written to — a directory, a path whose parent does not exist, a path with no write permission — **named in the message**. `save` invents no directory, substitutes no default and writes no part of a checkpoint (`surface.md` §8, `e2e-surface.md` §2) |
| `CheckpointUnreadable` | `load`: the path is missing or unreadable; it is not a zip; it lacks `metadata.json` or `parameters.npy`; the JSON does not parse, lacks a field of §2.1, carries a field of the wrong JSON type — an integer field holding a string, a float, a `bool` or `null` is coerced by nothing (`surface.md` §1) — or carries a value §2.1 does not declare or one outside its range (the *Values are checked* paragraph below), the message naming the field and the value in every one of those cases, since a truncating `int()` would invent a learner (`errors.md` §3); `format`/`format_version`/`dtype` are not this module's; the array's length disagrees with `params.length` |
| `CheckpointMismatch` | `load` with a spec: it disagrees with the file on `backend`, on the kind, on `seed`, or — when the spec carries an encoder — on the representation or the size that encoder declares. The message names **the key** and both values (`surface.md` §9, `learner.md` §4). A compared key is validated **before** it is compared, so a `seed` that is not an integer — or a spec that is neither `None` nor a mapping — is refused naming `load(spec)` and the offending value, and never coerced: `int("1")` and `bool`-as-`0`/`1` are exactly the coercions `surface.md` §1 forbids (`errors.md` §4) |

**What `load` compares, and what it does not.** `records.md` §3's spec always carries `backend`,
`architecture` and `seed`, so those three and the encoder's representation and size are the compared keys; a
spec may name the kind bare (`surface.md` §4), so width and depth are *not* compared — the file's `settings`
and `params` are the authority, and `sizes` never disagrees because `architecture` is authoritative
(`surface.md` §9, `records.md` §3). An extra key in the spec is ignored (`surface.md` §4).

**Values are checked, not only JSON types.** A field whose value is not one §2.1 declares — `backend` outside
`backends.md` §1's two, `kind` outside `architecture.md` §1's seven, a `representation` not that kind's row — or
outside its range — `width`/`depth` not positive, `sparsity` outside `[0, 1]`, a negative `position` or `counter`, a
`counter` at or past its `interval` — is refused naming the field and the value. `backend` is checked **before** any
backend module is imported, so a `numpy` checkpoint imports no `torch` (`README.md` §5, §6, G6).

## 4. The loss-free equality, stated testably

For one learner `L`, its saved file `save(L, path)`, and any observation and mask of `L`'s family:

    act(load(spec, path), observation, mask)["action"] == act(L, observation, mask)["action"]
    param_count(load(spec, path)) == param_count(L)
    load(None, path) is a learner of the same kind, settings, representation and backend as L

and, with `pol = as_policy(L, encoder, seed)` and `pol2 = as_policy(load(None, path), encoder, seed)`, the two
policies choose the same descriptor on one readout (`surface.md` §10, ASM-5): FAM-12.2 and FAM-16.17's assertion, and
why the file carries the seed, the position and the target copy and not just the parameters (`protocol.md` §5).

## 5. What is left to L4

The compression method's default, the JSON's key order, an `indent`, and the private helpers that flatten and scatter
the array — `_read_metadata` excepted, its name and object being fixed (`rule.md` §8). Not L4's: the two member names,
the zip-through-a-handle container, §2.1's field names, the array's three sections, `format_version` 1, and §3's
refusals and value checks (`guardrails.md`).
