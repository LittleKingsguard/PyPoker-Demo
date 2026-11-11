# agents — a version

- **Owner:** the checkpoint (D-16, ASM-5, ASM-18, D-19, D-20, D-29, D-33, ASM-40): the exact bytes of the container,
  format version 3 for a default-shape learner and version 4 with a `game` field for either other declared shape, the
  four version rules, the `utility` field written beside `learning_rule`, and `save`/`load`'s refusals
- **Ceiling:** 110 lines. At the ceiling, split by owner — never append
- **Read with:** `architecture.md` §4–§6, `rule.md` §4–§5, `utility.md` §2–§4, `restore.md` §1–§2, `shapes.md` §2, §5, `seats.md` §5

## 1. What a restore must recover

A version is a checkpoint of a run and a league member (D-16), so `save`/`load` is what lets a shipped member decide as
its learner did (`learner.md` §4, `protocol.md` §5). From the file alone, a restore recovers:

- the **backend** (`backends.md` §1); the **kind** and its four resolved settings — width, depth, sparsity and
  residual — so the model is rebuilt before a value is scattered into it (`architecture.md` §1, §3); and the
  **representation**: family, size, encoding, `shape` and `dtype`, the size being the width it was built at
  (`architecture.md` §6, `shapes.md` §8, ASM-44);
- the **seed** (`surface.md` §4, ASM-2), the **rule** it learns under, the **utility** its target carries and the
  **shape** it decides in — `learning_rule`, `utility`, `game` (`rule.md` §2, `utility.md` §2, §4, `shapes.md` §5,
  D-19, D-20, D-29) — so a restored model learns and decides as its writer did;
- every **parameter value** the update can change, in the declaration order (`architecture.md` §4); the **target
  copy**, its **counter** and the **schedule position**, the only state `learn` moves (`rule.md` §3–§4); the
  **sparse masks** a kind pins (`architecture.md` §2); and the **tie-break**'s rule and tolerance (`rule.md` §5).

Nothing the file does not hold is defaulted (`surface.md` §1, §9) — the one exception being the three names a
version-1-to-3 file is read as (§3) — and what the restore then promises is `restore.md` §1.

## 2. The bytes

A checkpoint is a **zip container** with exactly two members, written through an open file handle:

    open(path, "wb")            → the caller's path, byte for byte: no suffix is appended or rewritten
    zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_STORED)
    ├── "metadata.json"          UTF-8 JSON, one object, the fields of §2.1 in the order §2.1 lists
    └── "parameters.npy"         numpy.lib.format: one array, dtype float64, C order, 1-D

**Why an open handle.** `numpy.savez` would append `.npz` and hand back a path that `save`'s return and
`evaluation.policy_from`'s load disagree with (`records.md` §7, §12); `save` opens the handle itself (`surface.md` §8).
**The array's layout:** one `float64` array of length `2·P + M` — one member only, so each mask rides as `0.0`/`1.0`
values §2.1 records by layer and slots — `P` being `param_count`'s count and `M` the total sparse mask slots:

    [0, P)        the online parameters, in architecture.md §4's declaration order
    [P, 2P)       the target copy, the same order and shapes
    [2P, 2P + M)  each sparse layer's mask in ascending layer order, W² values of 0.0 and 1.0

### 2.1 `metadata.json`

| Key | Content |
|---|---|
| `format`, `dtype` | `"pypoker-agents-checkpoint"` — the magic name; anything else is not this module's file — and `"float64"`, the array member's type, stated and checked |
| `format_version` | `3` for a learner of the **default** shape, `4` for any other declared shape (§3, `shapes.md` §5) |
| `backend` | `"numpy"` or `"torch"` |
| `kind` | one of the seven kind names (`architecture.md` §1) |
| `game` | the declared shape the learner was built on — **required** in a version 4 container, written immediately after `kind`, and absent from a version 1, 2 or 3 one (§3, `shapes.md` §1, §5) |
| `learning_rule` | the catalogue member the learner was trained under (`rule.md` §2) — **required** in a version 4, 3 or 2 container, absent from a version 1 one (§3, D-19) |
| `utility` | the catalogue member whose reward its training target carried (`utility.md` §2), written **immediately after** `learning_rule` — **required** in a version 4 or 3 container, and a version 2 or 1 container must not carry it (§3, D-20) |
| `settings` | `{"width": W, "depth": D, "sparsity": s, "residual": bool}` — the resolved values in force |
| `representation` | `{"family", "encoding", "size", "shape", "dtype"}` — the sizing record (`architecture.md` §6), `shape` and `dtype` `null` for an encoder-less build. `size` is the width the learner was **built at**: 203 on the default shape, 329 on `no-limit-100` and 433 over 98 slots on `six-seat-no-limit-100`, whose encoders declare it, so a version-4 container carries its shape's own width, `shape` `[433]` on that row (`shapes.md` §8, `seats.md` §5, ASM-44, D-33) |
| `seed` | the learner's seed, an integer |
| `exploration`, `target` | `{"position": n, "schedule": {"start", "end", "samples"}}` and `{"counter": c, "interval": i}` — the schedule position, and the target copy's counter and interval (`rule.md` §3, §4, §6) |
| `params` | `{"count": P, "target_offset": P, "length": 2P + M, "tensors": [{"name", "shape", "offset", "count"}, …], "masks": [{"layer", "slots", "offset", "kept"}, …]}` — `count` is `param_count`'s answer, and on load it, `length` and each mask's `kept` are checked against the rebuilt layout and the array, so a disagreement is refused (§3); offsets are not read |
| `tie_break` | `{"rule": "smallest-masked-index-within-tolerance", "tolerance": 1e-09}` (`rule.md` §5) |

## 3. Format versions 3 and 4, and the four version rules

`format_version` is `3` for a learner of the **default** shape and `4` for any other declared shape
(`SUPPORTED_VERSIONS` is `(1, 2, 3, 4)`), and which fields a container carries is that version's question: a file of an
older version carrying a field its writer never wrote was edited and is refused **by name** (ASM-40, `shapes.md` §5).

| `format_version` | It must carry | It must **not** carry | It is read as |
|---|---|---|---|
| `4` | `game`, and `learning_rule` and `utility`, each validated against its own catalogue; `game` must name a declared shape other than the default | — | the shape and the two names it records |
| `3` | `learning_rule` and `utility`, each validated against its own catalogue | `game` — a default-shape learner writes version 3 | the default shape, and the two names it records |
| `2` | `learning_rule` | `utility` and `game` — no writer of that version wrote either | the default shape, that rule, and `net-chips` |
| `1` | neither | `learning_rule`, `utility` and `game` | the default shape, `masked-q-learning` and `net-chips` |

`_form` checks the **type** of every field of the form, `game` included while it is present, and `_declared` the
recorded **values**: a version-4 `game` outside the catalogue as `UnknownShape`, an uncarried `learning_rule` as
`UnknownRule`, a `utility` as `UnknownUtility` — each naming the field, the value and the catalogue — and a field another
version forbids by that field (`errors.md` §2–§3, `utility.md` §8).

The older versions' members are assigned in **one place** — `_read_container`, where a version-1 file's `learning_rule`
is filled from `declarations.DEFAULT_LEARNING_RULE`, a version-1-or-2 file's `utility` from `declarations.DEFAULT_UTILITY`
and a version-1-to-3 file's `game` from `declarations.DEFAULT_SHAPE` — so `_compare` and `_rebuild` see the members and
shape the file is **read as** (`utility.md` §3, `utilities.md` §6, `shapes.md` §5, D-19, D-20, D-29, D-33). `_rebuild` resolves
that shape's `A`, hands the layout the **file's own** `representation.size` and checks `params.count` and `params.length`
against the geometry that pair gives: a widened container restores to the head it was written at, the 433-wide one
included, `size` is held equal to the kind's 203/96 only where the file is read as the default shape, and a recorded size
that disagrees with the count is refused naming both (`restore.md` §2, `shapes.md` §8, `seats.md` §5, ASM-44, D-33).

A path that is not a zip, or a `metadata.json` that is not one object, is refused as *not a pypoker-agents-checkpoint of
format version 1, 2, 3 or 4* (`e2e-surface.md` §2, `errors.md` §3). **The shipped set:** the 18 version-1 containers load
unchanged as the default shape (`masked-q-learning`, `net-chips`) and none is regenerated (ASM-5, ASM-18, ASM-40).

The refusals are the two checkpoint classes of `errors.md` §2, plus `UnknownRule`, `UnknownUtility` and `UnknownShape` when a container's or a spec's name is one its catalogue does not carry:

| Refusal | When |
|---|---|
| `CheckpointUnwritable` | `save`: the path is not a location a file can be written to — a directory, a path whose parent does not exist, a path with no write permission — **named in the message**. `save` invents no directory, substitutes no default and writes no part of a checkpoint (`surface.md` §8, `e2e-surface.md` §2) |
| `CheckpointUnreadable` | `load`: the path is missing or unreadable; it is not a zip; it lacks `metadata.json` or `parameters.npy`; the JSON does not parse, lacks a field of §2.1 — `game`, `learning_rule` and `utility` where the version requires them — carries a field of the wrong JSON type — an integer field holding a string, a float, a `bool` or `null` is coerced by nothing (`surface.md` §1) — carries a field §2.1's version forbids — a version-1-to-3 `game` among them — or a value §2.1 does not declare — `backend` outside `backends.md` §1's two, `kind` outside `architecture.md` §1's seven, a `representation` whose `family` or `encoding` is not that kind's row, or whose `size` is not that row's where the file is read as the default shape — a version-4 `game` naming the default shape, a catalogue member outside its own catalogue — or one outside its range — `width`/`depth` not positive, `sparsity` outside `[0, 1]`, a negative `position`, a `counter` at or past its `interval` — the message naming the field and the value in every one of those cases, since a truncating `int()` would invent a learner (`errors.md` §3); `format`, `format_version` and `dtype` are not this module's; the array's length disagrees with `params.length`, or `params.count` with the geometry the recorded `representation.size` gives. `backend` is checked before any backend module is imported, so a numpy file loads without `torch` (`README.md` §6, G6) |
| `CheckpointMismatch` | `load` with a spec: it disagrees with the file on `backend`, the kind, `seed`, `learning_rule`, `utility` or `game` when it names one — naming **both shapes** when the key is the shape — or, when the spec carries an encoder, on the representation or the size that encoder declares. The message names **the key** and both values (`surface.md` §9, `learner.md` §4, `shapes.md` §5). A compared key is validated **before** it is compared, so a `seed` that is not an integer, a name a catalogue does not carry — `UnknownRule`, `UnknownUtility`, `UnknownShape` — or a spec that is neither `None` nor a mapping is refused naming `load(spec)` and the offending value, and never coerced (`errors.md` §2, §4) |

**What a spec's keys mean.** `records.md` §3's spec always carries `backend`, `architecture` and `seed`, so those are
compared; a bare kind name leaves width and depth *uncompared* and `sizes` never disagrees, `architecture` being
authoritative (`surface.md` §4, §9); an extra key is ignored; and a spec naming none of `learning_rule`, `utility` and
`game` is compared on none — the three declared defaults (`rules.md` §4, `utility.md` §3, `shapes.md` §1).

## 4. The equality and the L4 frontier

`load`'s equality and its L4 frontier are `restore.md` §1–§3; the bytes, the version and the refusals above (G11–G13).
