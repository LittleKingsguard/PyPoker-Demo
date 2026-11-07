# training — the artefacts and the index

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-08
- **Owner:** the file layout under `checkpoints/` (§1), the write root a run writes under (§1–§2), the naming rules and the `.ckpt`
  suffix (§2), the ten snapshots and the retained five (§3), `checkpoints()` — declared data, never a scan (§4), and what ships (§5)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `loop.md` §1 steps 7–8, §3–§4, `registry.md` §3, `curves.md` §2, `agents/checkpoint.md` §2, `errors.md` §4

## 1. The layout, and the private names

    checkpoints/<rung>/<variant>/seed-<seed>/step-<step:04d>.ckpt      the ten snapshots
    checkpoints/<rung>/<variant>/seed-<seed>/final.ckpt                that pair's final model

| Name | Signature | One-line contract |
|---|---|---|
| `layout.ROOT` | a `str` | the repository root, derived from `layout.py`'s own location and never from the caller's working directory; `CHECKPOINT_ROOT` is `checkpoints/` under it and is the **declared** root, which every read and the index resolve against (`write-root.md` §1–§2) |
| `layout.OVERRIDE` | a `str` | `"PYPOKER_CHECKPOINT_ROOT"`: the one ambient override's name, read from `os.environ` and never a seventh entry point (`write-root.md` §3) |
| `layout._snapshot_path` | `_snapshot_path(rung, variant, seed, step)` | §1's snapshot path for that pair and that step, `step` formatted `04d` — of the **declared** layout and never of the write root |
| `layout._final_path` | `_final_path(rung, variant, seed)` | §1's `final.ckpt` path for that pair, of the **declared** layout |
| `layout._write_root` | `_write_root()` | the root a run writes under: `os.path.abspath(os.environ[OVERRIDE])` when that variable is set to a non-empty value, else `CHECKPOINT_ROOT`; read on **every** call and never cached, so an override set after `import training` still applies |
| `layout._write_path` | `_write_path(declared)` | one declared path re-rooted at the write root: `os.path.join(_write_root(), os.path.relpath(declared, CHECKPOINT_ROOT))`, and the declared path itself when the two roots are equal |
| `layout._prepare` | `_prepare(rung, variant, seed)` | makes that pair's directory **under the write root** — `_write_path(_directory(rung, variant, seed))` — with `os.makedirs(..., exist_ok=True)`, and returns it, because `save` invents none |
| `layout._relative` | `_relative(path)` | that path as §2's record spells it: relative to the repository root with POSIX separators when the artefact is inside it, **unchanged** when it is outside (`write-root.md` §5) |
| `layout._resolve` | `_resolve(path)` | a recorded path as a filesystem path: an absolute one as it stands, a relative one read from the repository root and never from the caller's working directory |
| `layout._resolved` | `_resolved(records)` | the same member records with each `path` resolved — what a `build_pool` call is handed, because a pool tests a path with `os.path.isfile` and a record spells it from the root |

The ten are contract for `tests/training/` (`README.md` §4). `ROOT` is not a directory scan: nothing here lists the tree (`§4`),
no name creates a directory on import, and `_prepare` is the one that creates one at all — under the write root (§2).

## 2. The names, the suffix, and who makes the directory

- **`seed-<seed>` is the decimal seed and nothing else** — no zero padding, no sign, no hash — because the seed set is integers and
  a reader must be able to match a directory to a record's `seeds` entry by eye (`protocol.md` §2, `records.md` §7).
- **`step-<step:04d>`** is the snapshot's step, zero-padded to four digits so the ten names sort lexicographically in the order
  they were written: `step-0025.ckpt` … `step-0250.ckpt`. A step of 10,000 hands is `step-10000.ckpt` and sorts after them, which
  is why the padding is a minimimum width and not a truncation.
- **The suffix is `.ckpt`.** `.gitignore` ignores `*.pt` and `*.npz`, so a checkpoint written with either suffix cannot be
  committed and the shipped set would not travel with the repository (D-7, D-8); `.ckpt` is neither ignored nor a format claim —
  `agents.save` writes the container it always writes, through an open handle, so the caller's suffix is honoured byte for byte
  (`agents/checkpoint.md` §2). Rejected: `*.pt` plus a `.gitignore` exception, which makes every later artefact an argument about
  the ignore file.
- **The run makes the pair's directory under the write root** with `os.makedirs(parent, exist_ok=True)` before the first `agents.save`,
  because `save` invents no directory and refuses a path whose parent is missing (`agents/surface.md` §8, `loop.md` §2). One
  directory per variant × seed keeps a pair's six named artefacts together and makes a run's ten snapshots and its final model one
  folder.
- **The write root is `_write_root()`**: the declared root unless `PYPOKER_CHECKPOINT_ROOT` names another one, so a run with the
  override unset writes the shipped layout exactly as before and a redirected run writes the same layout elsewhere
  (`write-root.md` §1, §3, §6). Every path a run hands `agents.save` is `_write_path` of a declared path, and
  `_snapshot_path`/`_final_path` keep naming the declared layout, which is what keeps the index's `root` and every declared
  window resolving from `<repo>` (`write-root.md` §2).
- **The run record carries the path `agents.save` returned, spelled `_relative`**, and the rule is exact: an artefact **inside** the
  repository root is spelled repository-relative with POSIX separators, so it travels with the tree; one **outside** it is carried
  **unchanged** — the absolute path `agents.save` was handed — so a redirected run's record names a file that exists
  (`write-root.md` §5, `protocol.md` §5, FAM-12.1, FAM-15.1). A default run carries `checkpoints/R1/…/final.ckpt` and one at
  `PYPOKER_CHECKPOINT_ROOT=/tmp/pypoker-run` carries `/tmp/pypoker-run/R1/…/final.ckpt`; **the index carries the
  repository-relative spelling only**, because it is a shipped declaration (`battery.md` §2, FAM-12.5, FAM-16.31).
- **Every path this module reads back goes through `_resolve`**, which reads a relative spelling from the repository root:
  a declared version whose `path` is `checkpoints/R1/…/step-0600.ckpt` is a member whatever directory the process was
  started in, and a pool whose window emptied because a talk ran elsewhere would pretend a version the repository carries is
  absent (`registry.md` §3, `protocol.md` §5, `run`'s own pool filter in `loop.md` §1 step 2).
- **So a path is resolved for a call and spelled in a record.** What is handed to `evaluation.build_pool` is
  `_resolved(members)` — the same records with each `path` a filesystem path — because a pool tests a member's path with
  `os.path.isfile` against the process's working directory; what every returned record carries is `_relative` of it, so a
  run's pool members, its `checkpoints` block and the index name one artefact one way (`evaluation/surface.md` §5,
  `records.md` §7, `protocol.md` §5).

## 3. Ten written, five retained, six named

A pair (one variant × one seed) **writes** ten snapshots at `interval, 2·interval, … 10·interval` and one final model at the
budget's end (`loop.md` §1 steps 7–8, ASM-18). Its run record **names** the last M = 5 of the ten plus that pair's final model —
**six artefacts**, and never the five earlier snapshots (`records.md` §12, `surface.md` §4).

    named = {step-<6·interval>, … step-<10·interval>} ∪ {final}      # 5 + 1 per variant × seed

The battery reads exactly this. `tests/e2e/_records.py`'s `checkpoint_span(M, variants, seeds)` allows between `variants × seeds`
and `variants × seeds × (M + 1)` paths in the record's `checkpoints` entry, and the two bounds are tight against a 60- or
250-hand run: FAM-12.1 (R1, 250 hands, one seed) requires **exactly 6**, its floor being the final model and its ceiling `1 × (5 +
1)`; FAM-12.4 requires at least `M + 1 = 6`, so that one run is pinned to six; FAM-15.1 and FAM-16.29 (the custom two-variant
rung, 60 hands, one seed) allow **exactly 12** — `2 × 6`. A design that named all ten snapshots and the final would report 11 per
pair and fail all three cases.

Snapshot *k+1* descends from snapshot *k*: a snapshot's `lineage` is the `id` of the previous one written by that run, a seed's
first snapshot descends from the last version the run wrote before it, and the run's first descends from its rung's own start —
so a rung's retained versions are one chain in the recorded seed set's order (`loop.md` §7, `records.md` §7). The three seeds'
passes lie end to end in the seed set's order, which is how a 15-version declaration becomes a five-version window
(`registry.md` §3, `league.md` §2).

## 4. `checkpoints()` — declared data, never a directory scan

`checkpoints()` returns one mapping, read under two keys (`surface.md` §7):

| Key | Content |
|---|---|
| `entries` | one ordered list; **each entry one artefact**, listed once |
| `shipped` | the rung names whose runs exist — `["R1"]` today |

One entry is a `records.md` §7 record extended with `kind`:

    {"id", "path", "rung", "variant", "seed", "step", "samples", "lineage", "kind"}

- `id` — `"<rung>/<variant>/seed-<seed>/step-<step:04d>"` for a snapshot and `"<rung>/<variant>/seed-<seed>/final"` for a final
  model: stable across tables, unique within the index, and containing none of the three baseline names (`records.md` §7,
  `league.md` §2).
- `path` — §2's spelling, the artefact the entry names and no other.
- `step` and `samples` — both the hands trained when the artefact was written: the loop trains one hand and learns once, so a
  snapshot's step and its sample count are the same integer and the file name carries it (`records.md` §7, `loop.md` §1 step 7).
- `kind` — `"snapshot"` or `"final"`, which is what lets a window be read as the snapshot entries alone (`registry.md` §3).
- `lineage` — §3's chain.

**Order.** Rung in brief §2's order, then variant in `registry.md` §1's declaration order, then seed ascending, then step
ascending, then that pair's `final`. Ordering is by the declaration and never by a directory listing, so two calls return equal
lists and a reader gets one order (`surface.md` §7, `battery.md` §3 FAM-12).

**Declared, so never scanned.** `_entries()` reads `SHIPPED_FINALS` and `SHIPPED_WINDOWS` — two literal declarations in
`index.py` — and concatenates them; no entry point lists a directory, stats a scratch path or filters by what happens to be on
disk (`protocol.md` §5, FAM-16.31's `carried` assertion: none of the battery's own scratch checkpoints appears in the index).
`SHIPPED_FINALS` names per rung and variant and seed the final model that run wrote; `SHIPPED_WINDOWS` names per rung the
retained snapshot window in lineage order, which is also what `registry._window` reads (`registry.md` §3). A declaration is
cheaper and honest; a scan is neither.

**Once, and once only.** Every artefact appears in `entries` exactly one time, because `tests/e2e/_surface.py`'s
`checkpoint_path_listing` counts *listings* — every path the index names anywhere, repeats included — and FAM-12.6 fails on a
single repeat. So the index carries **one** list of paths and no second list beside it: `shipped` holds rung names, and a pair's
tenth snapshot and its final model are two distinct paths (`step-<10·interval>.ckpt` and `final.ckpt` hold the same state at the
budget's end and are two files, so naming both is not a repeat), so no artefact is listed twice (ASM-18, `protocol.md` §5).

## 5. What ships, and what a missing run means

- **R1's live run ships**: three seeds × (five retained snapshots + one final model) = **18 artefacts**, and `shipped` is
  `["R1"]`: `checkpoints/R1/naive-numeric/seed-{0,1,2}/step-{0600,0700,0800,0900,1000}.ckpt` and `…/final.ckpt`. A run **writes** 33 paths for
  three seeds — ten snapshots plus that pair's final, 11 per variant × seed, regenerable, a run rewrites them — while the repository
  **ships** 18: the window's last five per seed plus each seed's final, six per pair, the set a reader protects, what `training.checkpoints()` indexes and `checkpoints/` holds (ASM-18, `protocol.md` §5, `checkpoints/evidence/r1-live.json`).
- **R2–R6's entries appear when their runs exist**: a rung whose run has not been written contributes **nothing** to `entries`,
  rather than a fabricated path. This is the one place where "declared data" and "the artefact exists" are reconciled: the
  declaration lists the runs that exist, so every path it names is a file (`protocol.md` §5); an entry for a run that was never
  executed would fail FAM-12.5's and FAM-16.31's existence checks, and a scan would list the battery's own scratch files.
- **What does not ship**: the five earlier snapshots of each pair (fifteen of the 33 a run writes), any scratch path, `tables/` (that is `evaluation`'s) and any
  path outside the repository (`module-map.md` §5, `battery.md` §3 FAM-12). A talk loads an entry through
  `evaluation.policy_from`, which reads the seed and the encoding from the container, so the first entry must be a checkpoint
  `agents.save` wrote and never a manifest (`evaluation/surface.md` §12, FAM-16.31).
- **A battery writes into a temporary root, so this shipped set is never added to and never overwritten.** The battery's
  two hooks — `tests/conftest.py` under `pytest`, `tests/e2e/__init__.py` under the `unittest` census — point
  `PYPOKER_CHECKPOINT_ROOT` at a private `mkdtemp` per session (`write-root.md` §4, `docs/L3/harness/layout.md` §5), so
  the eighteen artefacts above are as the shipped run left them (`battery.md` §2, the write-root finding in `strata/records/phase1-walkthrough.md`).

## 6. What is left to L4

Whether a path is a `str` or a `Path`, how the two declarations are written out, and whether `_entries` sorts or concatenates.
Not L4's: §1's two name forms and the ten names' contracts, the `.ckpt` suffix and its reason, the six named artefacts per pair,
the entry's nine keys, §4's order, the one-listing rule, and `shipped` being rung names (`guardrails.md` G11–G13).
