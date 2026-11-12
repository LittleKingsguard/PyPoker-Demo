# agents — a version

- **Owner:** the checkpoint (D-16, ASM-5, ASM-18, D-19, D-20, D-29, D-33, D-43, ASM-40): the exact bytes of the container,
  format version **3** for a default-shape learner, **4** with a `game` field for either other declared shape and **5**
  with a `counterfactual` field for a learner whose member is not `none`, the five version rules, the `utility` and
  `counterfactual` fields written beside `learning_rule`, and `save`/`load`'s refusals
- **Ceiling:** 110 lines. At the ceiling, split by owner — never append
- **Rev:** 2 · **Date:** 2026-11-11 — D-43 adds format version 5 and its required `counterfactual` field, absent under
  `none` and refused in a version 1–4 container (§2.1, §3)
- **Read with:** `architecture.md` §4–§6, `rule.md` §3–§5, `utility.md` §2–§4, `restore.md` §1–§2, `shapes.md` §2, §5

## 1. What a restore must recover

A version is a checkpoint of a run and a league member (D-16), so `save`/`load` is what lets a shipped member decide as
its learner did (`learner.md` §4, `protocol.md` §5). From the file alone, a restore recovers:

- the **backend** (`backends.md` §1); the **kind** and its four resolved settings — width, depth, sparsity and
  residual — so the model is rebuilt before a value is scattered into it (`architecture.md` §1, §3); and the
  **representation**: family, size, encoding, `shape` and `dtype`, `size` being the width it was built at (`shapes.md` §8);
- the **seed** (`surface.md` §4, ASM-2), the **rule** it learns under, the **utility** its target carries, the
  **counterfactual** member it takes its targets from and the **shape** it decides in: `learning_rule`, `utility`,
  `counterfactual`, `game` (`rule.md` §2–§3, `utility.md` §2, §4, `shapes.md` §5, `counterfactual.md` §6, D-43);
- every **parameter value** the update can change, in the declaration order (`architecture.md` §4); the **target
  copy**, its **counter** and the **schedule position**, the only state `learn` moves (`rule.md` §3–§4); the
  **sparse masks** a kind pins (`architecture.md` §2); and the **tie-break**'s rule and tolerance (`rule.md` §5).

Nothing the file does not hold is defaulted (`surface.md` §1, §9), bar the names a version-1-to-4 file is read as (§3).

## 2. The bytes

A checkpoint is a **zip container** with exactly two members, written through an open file handle:

    open(path, "wb")            → the caller's path, byte for byte: no suffix is appended or rewritten
    zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_STORED)
    ├── "metadata.json"          UTF-8 JSON, one object, the fields of §2.1 in the order §2.1 lists
    └── "parameters.npy"         numpy.lib.format: one array, dtype float64, C order, 1-D

**Why an open handle.** `numpy.savez` would append `.npz` and hand back a path no caller agrees with (`records.md` §7);
`save` opens the handle itself (`surface.md` §8). **The array's layout:** one `float64` array of length `2·P + M` — one
member only, so each mask rides as `0.0`/`1.0` values §2.1 records by layer and slots — `P` being `param_count`'s count
and `M` the total sparse mask slots:

    [0, P)        the online parameters, in architecture.md §4's declaration order
    [P, 2P)       the target copy, the same order and shapes
    [2P, 2P + M)  each sparse layer's mask in ascending layer order, W² values of 0.0 and 1.0

### 2.1 `metadata.json`

| Key | Content |
|---|---|
| `format`, `dtype` | `"pypoker-agents-checkpoint"` — the magic name; anything else is not this module's file — and `"float64"`, the array member's type, stated and checked |
| `format_version` | `3` for a learner of the **default** shape under `none`, `4` for any other declared shape under `none`, `5` for a learner whose counterfactual member is not `none` (§3, `shapes.md` §5, `counterfactual.md` §6) |
| `backend` | `"numpy"` or `"torch"` |
| `kind` | one of the seven kind names (`architecture.md` §1) |
| `game` | the declared shape the learner was built on — **required** in a version 4 container, written immediately after `kind`, written in a version 5 one **exactly when** that shape is not the default, and absent from a version 1, 2 or 3 one (§3, `shapes.md` §1, §5) |
| `learning_rule` | the catalogue member the learner was trained under (`rule.md` §2) — **required** in a version 5, 4, 3 or 2 container, absent from a version 1 one (§3, D-19) |
| `utility` | the catalogue member whose reward its training target carried (`utility.md` §2), written **immediately after** `learning_rule` — **required** in a version 5, 4 or 3 container, and a version 2 or 1 container must not carry it (§3, D-20) |
| `counterfactual` | the catalogue member the learner takes its targets from (`counterfactual.md` §6), written **immediately after** `utility` — **required** and never `none` in a version 5 container, and **absent** from a version 1, 2, 3 or 4 one, which are read as `none` (§3, D-43) |
| `settings` | `{"width": W, "depth": D, "sparsity": s, "residual": bool}` — the resolved values in force |
| `representation` | `{"family", "encoding", "size", "shape", "dtype"}` — the sizing record (`architecture.md` §6), `shape` and `dtype` `null` for an encoder-less build. `size` is the width the learner was **built at**: 203 on the default shape, 329 on `no-limit-100` and 433 over 98 slots on `six-seat-no-limit-100`, whose encoders declare it, so a version-4 or version-5 container carries its shape's own width, `shape` `[433]` on that row (`shapes.md` §8, `seats.md` §5, ASM-44, D-33) |
| `seed` | the learner's seed, an integer |
| `exploration`, `target` | `{"position": n, "schedule": {"start", "end", "samples"}}` and `{"counter": c, "interval": i}` — the schedule position, and the target copy's counter and interval, the counter counting **steps** and so moved `A` times as fast under the member (`rule.md` §3, §4, §6, `counterfactual.md` §6) |
| `params` | `{"count": P, "target_offset": P, "length": 2P + M, "tensors": [{"name", "shape", "offset", "count"}, …], "masks": [{"layer", "slots", "offset", "kept"}, …]}` — `count` is `param_count`'s answer, and on load it, `length` and each mask's `kept` are checked against the rebuilt layout and the array, so a disagreement is refused (§3); offsets are not read |
| `tie_break` | `{"rule": "smallest-masked-index-within-tolerance", "tolerance": 1e-09}` (`rule.md` §5) |

## 3. Format versions 1 to 5, and the five version rules

`SUPPORTED_VERSIONS` is `(1, 2, 3, 4, 5)`, and which fields a container carries is its version's question: a file of an
older version carrying a field its writer never wrote was edited and is refused **by name** (ASM-40, `shapes.md` §5).

| `format_version` | It must carry | It must **not** carry | It is read as |
|---|---|---|---|
| `5` | `counterfactual`, naming a member other than `none`; `learning_rule` and `utility`, each validated against its own catalogue; `game` **exactly when** its shape is not the default, and never naming it | a `counterfactual` naming `none` | the member, the two names and the shape it records — or the default shape when it carries no `game` |
| `4` | `game`, and `learning_rule` and `utility`, each validated against its own catalogue; `game` must name a declared shape other than the default | `counterfactual` | `none`, the shape and the two names it records |
| `3` | `learning_rule` and `utility`, each validated against its own catalogue | `game` — a default-shape learner writes version 3 — and `counterfactual` | the default shape, `none`, and the two names it records |
| `2` | `learning_rule` | `utility`, `game` and `counterfactual` — no writer of that version wrote any | the default shape, `none`, that rule, and `net-chips` |
| `1` | neither | all four | the default shape, `none`, `masked-q-learning` and `net-chips` |

`_form` checks the **type** of every field of the form, `game` and `counterfactual` included while present, and
`_declared` the recorded **values**: a `game` outside the catalogue as `UnknownShape`, a `counterfactual` as
`UnknownCounterfactual`, a `learning_rule` as `UnknownRule`, a `utility` as `UnknownUtility`, each naming the field, the
value and the catalogue, and a field another version forbids by that field (`errors.md` §3, `counterfactual.md` §6).

The older versions' members are assigned in **one place** — `_read_container`, where a version-1 file's `learning_rule`
is filled from `declarations.DEFAULT_LEARNING_RULE`, a version-1-or-2 file's `utility` from `declarations.DEFAULT_UTILITY`,
a version-1-to-3 file's `game`, and a version-5 file's absent one, from `declarations.DEFAULT_SHAPE`, and every
version-1-to-4 file's `counterfactual` from `declarations.DEFAULT_COUNTERFACTUAL` — so `_compare` and `_rebuild` see the
members and shape the file is **read as** (`utilities.md` §6, `shapes.md` §5, `counterfactual.md` §6, D-19, D-20, D-43).
`_rebuild` resolves that shape's `A`, hands the layout the **file's own** `representation.size` and checks `params.count`
and `params.length` against the geometry that pair gives: a widened container restores to the head it was written at, the
433-wide one included, `size` is held equal to the kind's 203/96 only where the file is read as the default shape, and a
recorded size that disagrees with the count is refused naming both (`restore.md` §2, `shapes.md` §8, `seats.md` §5, ASM-44).

A path that is not a zip, or a `metadata.json` that is not one object, is refused as *not a pypoker-agents-checkpoint of
format version 1, 2, 3, 4 or 5* (`e2e-surface.md` §2, `errors.md` §3). **The shipped set:** the 18 version-1 containers load
unchanged as the default shape (`masked-q-learning`, `net-chips`, `none`) and none is regenerated (ASM-5, ASM-18).

The refusals are the two checkpoint classes of `errors.md` §2, plus `UnknownRule`, `UnknownUtility`, `UnknownCounterfactual` and `UnknownShape` when a container's or a spec's name is one its catalogue does not carry:

| Refusal | When |
|---|---|
| `CheckpointUnwritable` | `save`: the path is not a location a file can be written to — a directory, a path whose parent does not exist, a path with no write permission — **named in the message**. `save` invents no directory, substitutes no default and writes no part of a checkpoint (`surface.md` §8, `e2e-surface.md` §2) |
| `CheckpointUnreadable` | `load`: the path is missing or unreadable; it is not a zip; it lacks `metadata.json` or `parameters.npy`; the JSON does not parse, lacks a field of §2.1 — `game`, `learning_rule`, `utility` and `counterfactual` where the version requires them — carries a field of the wrong JSON type — an integer field holding a string, a float, a `bool` or `null` is coerced by nothing (`surface.md` §1) — carries a field §2.1's version forbids — a version-1-to-4 `counterfactual`, a version-1-to-3 `game`, a version-5 `game` naming the default shape among them — or a value §2.1 does not declare — `backend` outside `backends.md` §1's two, `kind` outside `architecture.md` §1's seven, a `representation` whose `family` or `encoding` is not that kind's row, or whose `size` is not that row's where the file is read as the default shape, a version-5 `counterfactual` naming `none`, a catalogue member outside its own catalogue — or one outside its range — `width`/`depth` not positive, `sparsity` outside `[0, 1]`, a negative `position`, a `counter` at or past its `interval` — the message naming the field and the value in every one of those cases, since a truncating `int()` would invent a learner (`errors.md` §3); `format`, `format_version` and `dtype` are not this module's; the array's length disagrees with `params.length`, or `params.count` with the geometry the recorded `representation.size` gives. `backend` is checked before any backend module is imported, so a numpy file loads without `torch` (`README.md` §6, G6) |
| `CheckpointMismatch` | `load` with a spec: it disagrees with the file on `backend`, the kind, `seed`, `learning_rule`, `utility`, `counterfactual` or `game` when it names one — naming **both shapes** when the key is the shape, and both members when it is the counterfactual — or, when the spec carries an encoder, on the representation or the size that encoder declares. The message names **the key** and both values (`surface.md` §9, `learner.md` §4, `shapes.md` §5, `counterfactual.md` §6). A compared key is validated **before** it is compared, so a `seed` that is not an integer, a name a catalogue does not carry — `UnknownRule`, `UnknownUtility`, `UnknownCounterfactual`, `UnknownShape` — or a spec that is neither `None` nor a mapping is refused naming `load(spec)` and the offending value, and never coerced (`errors.md` §2, §4) |

**What a spec's keys mean.** `records.md` §3's spec always carries `backend`, `architecture` and `seed`, so those are
compared; a bare kind name leaves width and depth *uncompared*, `architecture` being authoritative (`surface.md` §9); an
extra key is ignored; a spec naming none of `learning_rule`, `utility`, `counterfactual` and `game` is compared on none,
and the equality a restore then promises is `restore.md` §1–§3 (G11–G13).
