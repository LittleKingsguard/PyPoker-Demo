# agents — a version

- **Owner:** the checkpoint (D-16, ASM-5, ASM-18, D-19, D-20): the exact bytes of the container, format version 3
  and its three version rules, the `utility` field written beside `learning_rule`, and `save`/`load`'s refusals
- **Ceiling:** 110 lines. At the ceiling, split by owner — never append
- **Read with:** `architecture.md` §4–§6, `rule.md` §4–§5, `utility.md` §2–§4, `restore.md` §1–§2, `backends.md` §4

## 1. What a restore must recover

A version is a checkpoint of a run and a league member (D-16), so `save`/`load` is what lets a shipped member decide
as its learner did (`learner.md` §4, `protocol.md` §5). From the file alone, a restore recovers:

- the **backend** (`backends.md` §1); the **kind** and its four resolved settings — width, depth, sparsity and
  residual — so the model is rebuilt before a value is scattered into it (`architecture.md` §1, §3); and the
  **representation**: family, size, encoding, `shape` and `dtype` (`architecture.md` §6);
- the **seed** (`surface.md` §4, ASM-2), the **rule** it learns under and the **utility** whose reward its training
  target carries — `learning_rule` and `utility` (`rule.md` §2, `utility.md` §2, §4, D-19, D-20) — so a restored
  model learns as its writer did and a table names the population and the objectives it measured;
- every **parameter value** the update can change, in the declaration order (`architecture.md` §4); the **target
  copy**, its **counter** and the **schedule position**, the only state `learn` moves (`rule.md` §3–§4); the
  **sparse masks** a kind pins (`architecture.md` §2); and the **tie-break**'s rule and tolerance (`rule.md` §5).

Nothing the file does not hold is defaulted (`surface.md` §1, §9) — the one exception being the two members a
version-1 or version-2 file is read as (§3) — and what the restore then promises is `restore.md` §1.

## 2. The bytes

A checkpoint is a **zip container** with exactly two members, written through an open file handle:

    open(path, "wb")            → the caller's path, byte for byte: no suffix is appended or rewritten
    zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_STORED)
    ├── "metadata.json"          UTF-8 JSON, one object, the fields of §2.1 in the order §2.1 lists
    └── "parameters.npy"         numpy.lib.format: one array, dtype float64, C order, 1-D

**Why an open handle.** `numpy.savez` would append `.npz` and hand back a path that `save`'s return and
`evaluation.policy_from`'s load disagree with (`records.md` §7, §12); `save` opens the handle itself (`surface.md` §8).

**The array's layout.** One `float64` array of length `2·P + M` — one member only, so each mask rides as `0.0`/`1.0`
values §2.1 records by layer and slots — `P` being `param_count`'s count and `M` the total sparse mask slots:

    [0, P)        the online parameters, in architecture.md §4's declaration order
    [P, 2P)       the target copy, the same order and shapes
    [2P, 2P + M)  each sparse layer's mask in ascending layer order, W² values of 0.0 and 1.0

### 2.1 `metadata.json`

| Key | Content |
|---|---|
| `format` | `"pypoker-agents-checkpoint"` — the magic name; anything else is not this module's file |
| `format_version` | `3`, an integer (§3) |
| `dtype` | `"float64"` — the array member's type, stated and checked |
| `backend` | `"numpy"` or `"torch"` |
| `kind` | one of the seven kind names (`architecture.md` §1) |
| `learning_rule` | the catalogue member the learner was trained under (`rule.md` §2) — **required** in a version 3 or 2 container, absent from a version 1 one (§3, D-19) |
| `utility` | the catalogue member whose reward its training target carried (`utility.md` §2), written **immediately after** `learning_rule` — **required** in a version 3 container, and a version 2 or 1 container must not carry it (§3, D-20) |
| `settings` | `{"width": W, "depth": D, "sparsity": s, "residual": bool}` — the resolved values in force |
| `representation` | `{"family", "encoding", "size", "shape", "dtype"}` — the sizing record (`architecture.md` §6), `shape` and `dtype` `null` for an encoder-less build |
| `seed` | the learner's seed, an integer |
| `exploration` | `{"position": n, "schedule": {"start", "end", "samples"}}` (`rule.md` §4, §6) |
| `target` | `{"counter": c, "interval": i}` — the target copy's counter and its interval (`rule.md` §3) |
| `params` | `{"count": P, "target_offset": P, "length": 2P + M, "tensors": [{"name", "shape", "offset", "count"}, …], "masks": [{"layer", "slots", "offset", "kept"}, …]}` — `count` is `param_count`'s answer, and on load it, `length` and each mask's `kept` are checked against the rebuilt layout and the array, so a disagreement is refused (§3); offsets are not read |
| `tie_break` | `{"rule": "smallest-masked-index-within-tolerance", "tolerance": 1e-09}` (`rule.md` §5) |

## 3. Format version 3, and the three version rules

`format_version` is `3` (`SUPPORTED_VERSIONS` is `(1, 2, 3)`), and which of the two catalogue fields a container
carries is that version's question: a file of an older version carrying a field its writer never wrote was edited
and is refused **by name** (D-19, D-20, ASM-5, `protocol.md` §5).

| `format_version` | It must carry | It must **not** carry | It is read as |
|---|---|---|---|
| `3` | `learning_rule` and `utility`, each validated against its own catalogue | — | the two names it records |
| `2` | `learning_rule` | `utility` — no writer of that version wrote one | that rule, and `net-chips` |
| `1` | neither | `learning_rule` and `utility` | `masked-q-learning` and `net-chips` |

`_form` checks the **type** of every field of the form, `utility` and `learning_rule` among them while present, and
`_declared` checks the recorded **values**: a version-3 `utility` the catalogue does not carry is refused as
`UnknownUtility` naming the field and the value, its `learning_rule` as `UnknownRule`, and a field a version-1 or
version-2 container forbids is refused naming it (`errors.md` §2–§3, `utility.md` §8).

The older versions' members are assigned in **one place** — `_read_container`, where a version-1 file's
`learning_rule` is filled from `declarations.DEFAULT_LEARNING_RULE` and a version-1-or-2 file's `utility` from
`declarations.DEFAULT_UTILITY`, the utility assignment beside the version-1 rule default — so `_compare` and
`_rebuild` see the members the file is **read as** (`utility.md` §3, `rules.md` §6, `utilities.md` §6, D-19, D-20).

A path that is not a zip, or a `metadata.json` that is not one object, is refused as *not a
pypoker-agents-checkpoint of format version 1, 2 or 3*, naming no field because no field was at fault — forward
compatibility being a new version and never a guess (`e2e-surface.md` §2, `errors.md` §3).

**The shipped set.** The 18 containers the repository ships predate both catalogues and are version 1; they load
unchanged as `masked-q-learning` and `net-chips`, and neither they nor any other artefact under `checkpoints/` is
regenerated (ASM-5, ASM-18, `protocol.md` §5, `utilities.md` §6).

The refusals are the two checkpoint classes of `errors.md` §2, plus `UnknownRule` when the container's rule — or a
spec's — is one the catalogue does not carry, and `UnknownUtility` on the same terms for a utility:

| Refusal | When |
|---|---|
| `CheckpointUnwritable` | `save`: the path is not a location a file can be written to — a directory, a path whose parent does not exist, a path with no write permission — **named in the message**. `save` invents no directory, substitutes no default and writes no part of a checkpoint (`surface.md` §8, `e2e-surface.md` §2) |
| `CheckpointUnreadable` | `load`: the path is missing or unreadable; it is not a zip; it lacks `metadata.json` or `parameters.npy`; the JSON does not parse, lacks a field of §2.1 — the rule and the utility a version-3 container requires and the rule a version-2 one does — carries a field of the wrong JSON type — an integer field holding a string, a float, a `bool` or `null` is coerced by nothing (`surface.md` §1) — carries a field of §2.1 that its own version forbids, or a value §2.1 does not declare — `backend` outside `backends.md` §1's two, `kind` outside `architecture.md` §1's seven, a `representation` not that kind's row, a catalogue member outside its own catalogue — or one outside its range — `width`/`depth` not positive, `sparsity` outside `[0, 1]`, a negative `position`, a `counter` at or past its `interval` — the message naming the field and the value in every one of those cases, since a truncating `int()` would invent a learner (`errors.md` §3); `format`, `format_version` and `dtype` are not this module's; the array's length disagrees with `params.length`. `backend` is checked before any backend module is imported, so a numpy file loads without `torch` (`README.md` §6, G6) |
| `CheckpointMismatch` | `load` with a spec: it disagrees with the file on `backend`, on the kind, on `seed`, on `learning_rule` or `utility` when it names one, or — when the spec carries an encoder — on the representation or the size that encoder declares. The message names **the key** and both values (`surface.md` §9, `learner.md` §4). A compared key is validated **before** it is compared, so a `seed` that is not an integer, a rule the catalogue does not carry — `UnknownRule` — a utility it does not carry — `UnknownUtility` — or a spec that is neither `None` nor a mapping is refused naming `load(spec)` and the offending value, and never coerced (`errors.md` §2, §4) |

**What a spec's keys mean.** `records.md` §3's spec always carries `backend`, `architecture` and `seed`, so those
three are compared; a bare kind name leaves width and depth *uncompared* and `sizes` never disagrees, `architecture`
being authoritative (`surface.md` §4, §9); an extra key is ignored; and a spec naming neither `learning_rule` nor
`utility` is compared on neither — the two declared defaults (`rules.md` §4, `utility.md` §3).

## 4. The equality and the L4 frontier

`load`'s equality and its L4 frontier are `restore.md` §1–§3; the bytes, the version and the refusals above (G11–G13).
