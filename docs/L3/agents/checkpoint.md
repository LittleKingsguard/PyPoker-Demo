# agents — a version

- **Owner:** the checkpoint (D-16, ASM-5, ASM-18, D-19): what a restore recovers, the exact bytes of the container,
  the file-format version, its version-1 reading of the rule, `save`/`load`'s refusals and the loss-free equality
- **Ceiling:** 110 lines. At the ceiling, split by owner — never append
- **Read with:** `architecture.md` §4–§6, `rule.md` §4–§5, `backends.md` §4

## 1. What a restore must recover

A version is a checkpoint of a run and a league member (D-16), so `save`/`load` is what lets a shipped member decide as
its learner did (`learner.md` §4, `protocol.md` §5). A restore recovers, **from the file alone**:

- the **backend**, `numpy` or `torch` (`backends.md` §1);
- the **kind** and its four resolved settings — width, depth, sparsity and residual — so the model is rebuilt
  before any value is scattered into it (`architecture.md` §1, §3);
- the **representation**: family, size, encoding, `shape` and `dtype` for an encoder build (`architecture.md` §6);
- the learner's **seed** (`surface.md` §4, ASM-2) and the **rule** it learns under, a member of `rules.md` §2's
  catalogue (`rule.md` §2, `rules.md` §4, D-19), so a restored model learns as its writer did and a table can name its
  population;
- every **parameter value** the update can change, in the declaration order (`architecture.md` §4);
- the **target copy**, its **counter** and the **schedule position**, the only state `learn` moves (`rule.md` §3–§4),
  and the **sparse masks**, if the kind pins any weights to zero (`architecture.md` §2);
- the **tie-break**'s rule and tolerance, recorded as the design constant they are (`rule.md` §5).

Nothing the file does not hold is defaulted (`surface.md` §1, §9) — the one exception being the rule a version-1 file's
silence reads as (§3) — and the fixed hyper-declarations are `learners()`'s one declaration (`rule.md` §6).

## 2. The bytes

A checkpoint is a **zip container** with exactly two members, written through an open file handle:

    open(path, "wb")            → the caller's path, byte for byte: no suffix is appended or rewritten
    zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_STORED)
    ├── "metadata.json"          UTF-8 JSON, one object, the fields of §2.1
    └── "parameters.npy"         numpy.lib.format: one array, dtype float64, C order, 1-D

**Why an open handle.** `numpy.savez(path)` appends `.npz`, so a caller's `version-3.ckpt` would come back as
`version-3.ckpt.npz`, and `save`'s return, the run record's path and `evaluation.policy_from`'s load would disagree
(`records.md` §7, §12, `e2e-surface.md` §3.4); a handle `save` opened honours that spelling (`surface.md` §8).

**The array's layout.** One `float64` array of length `2·P + M` — one member only, so each mask rides as `0.0`/`1.0` values
that §2.1 records by layer and slots — `P` being `param_count`'s count and `M` the total sparse mask slots:

    [0, P)        the online parameters, in architecture.md §4's declaration order
    [P, 2P)       the target copy, the same order and shapes
    [2P, 2P + M)  each sparse layer's mask in ascending layer order, W² values of 0.0 and 1.0

### 2.1 `metadata.json`

| Key | Content |
|---|---|
| `format` | `"pypoker-agents-checkpoint"` — the magic name; anything else is not this module's file |
| `format_version` | `2`, an integer (§3) |
| `dtype` | `"float64"` — the array member's type, stated and checked |
| `backend` | `"numpy"` or `"torch"` |
| `kind` | one of the seven kind names (`architecture.md` §1) |
| `learning_rule` | the catalogue member the learner was trained under (`rule.md` §2) — **required** in a version 2 container, absent from a version 1 one (§3, D-19) |
| `settings` | `{"width": W, "depth": D, "sparsity": s, "residual": bool}` — the resolved values in force |
| `representation` | `{"family", "encoding", "size", "shape", "dtype"}` — the sizing record (`architecture.md` §6), `shape` and `dtype` `null` for an encoder-less build |
| `seed` | the learner's seed, an integer |
| `exploration` | `{"position": n, "schedule": {"start", "end", "samples"}}` (`rule.md` §4, §6) |
| `target` | `{"counter": c, "interval": i}` — the target copy's counter and its interval (`rule.md` §3) |
| `params` | `{"count": P, "target_offset": P, "length": 2P + M, "tensors": [{"name", "shape", "offset", "count"}, …], "masks": [{"layer", "slots", "offset", "kept"}, …]}` — `count` is `param_count`'s answer, and on load it, `length` and each mask's `kept` are checked against the rebuilt layout and the array, so a disagreement is refused (§3); offsets are not read |
| `tie_break` | `{"rule": "smallest-masked-index-within-tolerance", "tolerance": 1e-09}` (`rule.md` §5) |

## 3. The format version, and the refusals

`format_version` is `2`, and a version-2 `metadata.json` **requires** `learning_rule` (`rules.md` §6, D-19). A load reads
`format`, `format_version` and `dtype` first and refuses a file this module does not read — forward compatibility being a
new version and never a guess (`e2e-surface.md` §2). **A version 1 container carries no rule and is read as
`masked-q-learning`**, the only rule its writer could have used, so the 18 shipped containers load unchanged; a version-1
file carrying the field was edited and is refused by name, as is a version-2 one omitting it (D-19, ASM-5, `protocol.md`
§5). The refusals are the two checkpoint classes of `errors.md` §2, plus `UnknownRule` when the container's rule — or a
spec's — is one the catalogue does not carry:

| Refusal | When |
|---|---|
| `CheckpointUnwritable` | `save`: the path is not a location a file can be written to — a directory, a path whose parent does not exist, a path with no write permission — **named in the message**. `save` invents no directory, substitutes no default and writes no part of a checkpoint (`surface.md` §8, `e2e-surface.md` §2) |
| `CheckpointUnreadable` | `load`: the path is missing or unreadable; it is not a zip; it lacks `metadata.json` or `parameters.npy`; the JSON does not parse, lacks a field of §2.1 — the rule a version-2 container requires included — carries a field of the wrong JSON type — an integer field holding a string, a float, a `bool` or `null` is coerced by nothing (`surface.md` §1) — or carries a value §2.1 does not declare or one outside its range (the *Values are checked* paragraph below), the message naming the field and the value in every one of those cases, since a truncating `int()` would invent a learner (`errors.md` §3); `format`/`format_version`/`dtype` are not this module's; a version-1 container records a rule at all (§3's paragraph above); the array's length disagrees with `params.length` |
| `CheckpointMismatch` | `load` with a spec: it disagrees with the file on `backend`, on the kind, on `seed`, on `learning_rule` when it names one, or — when the spec carries an encoder — on the representation or the size that encoder declares. The message names **the key** and both values (`surface.md` §9, `learner.md` §4). A compared key is validated **before** it is compared, so a `seed` that is not an integer, a rule the catalogue does not carry — refused as `errors.md` §2's `UnknownRule` — or a spec that is neither `None` nor a mapping is refused naming `load(spec)` and the offending value, and never coerced (`errors.md` §4) |

**What `load` compares, and what it does not.** `records.md` §3's spec always carries `backend`, `architecture` and `seed`,
so those three, `learning_rule` whenever the spec names one, and the encoder's representation and size are the compared
keys; a bare kind name leaves width and depth *uncompared* (`surface.md` §4), and `sizes` never disagrees because
`architecture` is authoritative (`surface.md` §9, `records.md` §3). An extra key is ignored, and a spec naming no
`learning_rule` is compared on none — the declared default (`surface.md` §4, `rules.md` §4).

**Values are checked, not only JSON types.** A field whose value is not one §2.1 declares — `backend` outside
`backends.md` §1's two, `kind` outside `architecture.md` §1's seven, a `representation` not that kind's row, a
`learning_rule` outside the catalogue — or outside its range — `width`/`depth` not positive, `sparsity` outside `[0, 1]`,
a negative `position` or `counter`, a `counter` at or past its `interval` — is refused naming the field and the value.
`backend` is checked **before** any backend is imported, so a numpy file loads without `torch` (`README.md` §5, §6, G6).

## 4. The loss-free equality, stated testably

For one learner `L`, its saved file `save(L, path)`, and any observation and mask of `L`'s family:

    act(load(spec, path), observation, mask)["action"] == act(L, observation, mask)["action"]
    param_count(load(spec, path)) == param_count(L)
    load(None, path) is a learner of the same kind, settings, representation, backend and rule as L

and, with `pol = as_policy(L, encoder, seed)` and `pol2 = as_policy(load(None, path), encoder, seed)`, the two policies
choose the same descriptor on one readout (`surface.md` §10, ASM-5): FAM-12.2 and FAM-16.17's assertion, and why the
file carries the seed, the position, the target copy and the rule and not just the parameters (`protocol.md` §5).

## 5. What is left to L4

The compression method's default, the JSON's key order, an `indent`, and the private helpers that flatten and scatter the
array — `_read_metadata` excepted (`rule.md` §8). Not L4's: the two member names, the container, §2.1's field names, the
array's three sections, `format_version` 2, and §3's refusals and value checks (`guardrails.md`).
