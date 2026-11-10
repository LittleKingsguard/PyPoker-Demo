# training — the artefacts and the index

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 5 · **Date:** 2026-11-09 · **Rev 4** makes an entry's `utility` required beside its `rule`, declared per rung in `SHIPPED_UTILITIES` (§4, `records.md` §7, D-20) · **Rev 5** states that the greedy pass reads the final model and adds no artefact, so a pair still names exactly six (§3, `record.md` §2, `greedy.md` §1, ASM-38, D-29)
- **Owner:** the file layout under `checkpoints/` (§1), the write root a run writes under (§1–§2), the naming rules and the `.ckpt` suffix (§2), the ten snapshots, the retained five and the pass's silence (§3), `checkpoints()` — declared data, never a scan (§4), and what ships (§5)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `loop.md` §1 steps 7–8, §3–§4, `record.md` §1–§2, `registry.md` §3, `curves.md` §2, `agents/checkpoint.md` §2, `errors.md` §4

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

The ten are contract for `tests/training/` (`README.md` §4). `ROOT` is not a directory scan: nothing here lists the tree (§4), no name creates a directory on import, and `_prepare` is the one that creates one at all — under the write root (§2).

## 2. The names, the suffix, and who makes the directory

- **`seed-<seed>` is the decimal seed and nothing else** — no zero padding, no sign, no hash — because the seed set is integers and a reader must be able to match a directory to a record's `seeds` entry by eye (`protocol.md` §2, `records.md` §7).
- **`step-<step:04d>`** is the snapshot's step, zero-padded to four digits so the ten names sort lexicographically in the order they were written: `step-0025.ckpt` … `step-0250.ckpt`. A step of 10,000 hands is `step-10000.ckpt` and sorts after them, which is why the padding is a minimum width and not a truncation.
- **The suffix is `.ckpt`.** `.gitignore` ignores `*.pt` and `*.npz`, so a checkpoint written with either suffix cannot be committed and the shipped set would not travel with the repository (D-7, D-8); `.ckpt` is neither ignored nor a format claim — `agents.save` writes the container it always writes, through an open handle, so the caller's suffix is honoured byte for byte (`agents/checkpoint.md` §2). Rejected: `*.pt` plus a `.gitignore` exception, which makes every later artefact an argument about the ignore file.
- **The run makes the pair's directory under the write root** with `os.makedirs(parent, exist_ok=True)` before the first `agents.save`, because `save` invents no directory and refuses a path whose parent is missing (`agents/surface.md` §8, `loop.md` §2). One directory per variant × seed keeps a pair's six named artefacts together, ten snapshots and the final model in one folder.
- **The write root is `_write_root()`**: the declared root unless `PYPOKER_CHECKPOINT_ROOT` names another one, so a run with the override unset writes the shipped layout exactly as before and a redirected run writes the same layout elsewhere (`write-root.md` §1, §3, §6). Every path a run hands `agents.save` is `_write_path` of a declared path, and `_snapshot_path`/`_final_path` keep naming the declared layout, which is what keeps the index's `root` and every declared window resolving from `<repo>` (`write-root.md` §2).
- **The run record carries the path `agents.save` returned, spelled `_relative`**, and the rule is exact: an artefact **inside** the repository root is spelled repository-relative with POSIX separators, so it travels with the tree; one **outside** it is carried **unchanged** — the absolute path `agents.save` was handed — so a redirected run's record names a file that exists (`write-root.md` §5, `protocol.md` §5, FAM-12.1, FAM-15.1). A default run carries `checkpoints/R1/…/final.ckpt` and one at `PYPOKER_CHECKPOINT_ROOT=/tmp/pypoker-run` carries `/tmp/pypoker-run/R1/…/final.ckpt`; **the index carries the repository-relative spelling only**, because it is a shipped declaration (`battery.md` §2, FAM-12.5, FAM-16.31).
- **Every path this module reads back goes through `_resolve`**, which reads a relative spelling from the repository root: a declared version whose `path` is `checkpoints/R1/…/step-0600.ckpt` is a member whatever directory the process was started in, and a pool whose window emptied because a talk ran elsewhere would pretend a version the repository carries is absent (`registry.md` §3, `protocol.md` §5, `run`'s own pool filter in `loop.md` §1 step 2).
- **So a path is resolved for a call and spelled in a record.** What is handed to `evaluation.build_pool` is `_resolved(members)` — the same records with each `path` a filesystem path, because a pool tests a member's path with `os.path.isfile` against the process's working directory; what every returned record carries is `_relative` of it, so a run's pool members, its `checkpoints` block and the index name one artefact one way (`evaluation/pool.md` §1, `records.md` §7, `protocol.md` §5).

## 3. Ten written, five retained, six named — and the pass adds nothing

A pair (one variant × one seed) **writes** ten snapshots at `interval, 2·interval, … 10·interval` and one final model at the budget's end (`loop.md` §1 steps 7–8, ASM-18). Its run record **names** the last M = 5 of the ten plus that pair's final model — **six artefacts**, and never the five earlier snapshots (`records.md` §12, `surface.md` §4).

    named = {step-<6·interval>, … step-<10·interval>} ∪ {final}      # 5 + 1 per variant × seed

**The greedy pass is not one of them.** The pass runs after `agents.save` of the final model and reads that model — the artefact the record's `final` names — so it needs no checkpoint of its own, produces no path, makes no directory and writes no file: a pair is six named artefacts before D-29 and six after it (`greedy.md` §1, `record.md` §2, ASM-38, D-29). Its block's reproducibility comes from *that* file, which is why the order (save, then pass) is part of the claim (`loop.md` §1 step 8).

The battery reads exactly this. `tests/e2e/_records.py`'s `checkpoint_span(M, variants, seeds)` allows between `variants × seeds` and `variants × seeds × (M + 1)` paths in the record's `checkpoints` entry, tight against a 60- or 250-hand run: FAM-12.1 (R1, 250 hands, one seed) requires exactly 6, FAM-12.4 at least `M + 1 = 6`, and FAM-15.1/FAM-16.29 (two-variant rung, 60 hands) exactly 12. Naming all ten snapshots and the final would report 11 per pair and fail all three (ASM-18).

Snapshot *k+1* descends from snapshot *k*: a snapshot's `lineage` is the `id` of the previous one written by that run, a seed's first snapshot from the last version the run wrote before it, and the run's first from its rung's own start — so a rung's retained versions are one chain in the recorded seed set's order (`loop.md` §7, `records.md` §7). The three seeds' passes lie end to end, which is how a 15-version declaration becomes a five-version window (`registry.md` §3, `league.md` §2).

## 4. `checkpoints()` — declared data, never a directory scan

`checkpoints()` returns one mapping of eight keys, each one declared and never scanned (`surface.md` §7):

| Key | Content | Key | Content |
|---|---|---|---|
| `format` | the mapping's own name: `"pypoker-training-checkpoint-index"` | `version` | its schema number: `1` |
| `root` | `checkpoints`: §1's **declared** root, spelled `_relative` from the repository root, so a redirected run's write root never moves it (`write-root.md` §2) | `shipped` | the rung names whose runs exist — `["R1"]` today |
| `pending` | the rung names whose runs do **not** exist — `["R2", "R3", "R4", "R5", "R6"]` today, which is also why every path `entries` names is a file (§5) | `entries` | one ordered list; **each entry one artefact**, listed once |
| `successor` | each rung's successor and no rung left out: `R1`→`R2` … `R5`→`R6`, `R6`→`None` (`ladder.md` §2, ASM-16) | `windows` | per shipped rung's primary variant, the retained window its successor inherits: `rung`, `retained`, `seeds`, `rule`, `utility`, `inherited_by` (`registry.md` §3, D-19, D-20) |

One entry is a `records.md` §7 record extended with `kind`, and since D-19 and D-20 it carries the rule it was trained under and the utility whose reward it was trained on:

    {"id", "path", "rung", "variant", "seed", "step", "samples", "lineage", "rule", "utility", "kind"}

- `id` — `"<rung>/<variant>/seed-<seed>/step-<step:04d>"` for a snapshot and `"<rung>/<variant>/seed-<seed>/final"` for a final model: stable across tables, unique within the index, and containing none of the three baseline names (`records.md` §7, `league.md` §2).
- `path` — §2's spelling, the artefact the entry names and no other.
- `step` and `samples` — both the hands trained when the artefact was written: the loop trains one hand and learns once, so a snapshot's step and its sample count are one integer and the file name carries it (`records.md` §7, `loop.md` §1 step 7). The pass trains nothing, so no entry and no step is the pass's.
- `kind` — `"snapshot"` or `"final"`, what lets a window be read as the snapshot entries alone (`registry.md` §3); `lineage` — §3's chain.
- `rule` — the catalogue member the artefact was **trained under**, **required** by `records.md` §7 since D-19, so the membership a successor inherits is a window `evaluation.build_pool` accepts and the pool id certifies each member's estimator (`records.md` §7, §8, `rules.md` §6, ASM-27). It is declared per rung in `index.py`'s `SHIPPED_RULES`, beside `SHIPPED`, and never inferred: R1's rule is **`masked-q-learning`**, the only rule that existed when its version-1 containers were written (`rules.md` §6, ASM-5).
- `utility` — the catalogue member whose **reward** the artefact was trained on, **required** on the same terms by D-20, so the pool id certifies each member's objective as well as its estimator (ASM-27, `utilities.md` §6, §7). It is declared per rung beside `SHIPPED_RULES` in `index.py`'s `SHIPPED_UTILITIES` and never inferred: R1's shipped run **predates the catalogue**, its version-1 containers carry no utility, and they are read as **`net-chips`** — the only utility its writer could have used. The shipped set is **not regenerated**: eighteen artefacts stand as the shipped run left them (`utilities.md` §6, ASM-5, D-20).

**Order.** Rung in brief §2's order, then variant in `registry.md` §1's declaration order, then seed ascending, then step ascending, then that pair's `final`. Ordering is by the declaration and never by a directory listing, so two calls return equal lists and a reader gets one order (`surface.md` §7, `battery.md` §3 FAM-12).

**Declared, so never scanned.** `_entries()` reads `SHIPPED`, `SHIPPED_RULES`, `SHIPPED_UTILITIES`, `SHIPPED_FINALS` and `SHIPPED_WINDOWS` — literal declarations in `index.py` — and concatenates them; no entry point lists a directory, stats a scratch path or filters by what happens to be on disk (`protocol.md` §5, FAM-16.31's `carried` assertion: no scratch checkpoint appears). `SHIPPED_FINALS` names per rung, variant and seed the final model that run wrote; `SHIPPED_WINDOWS` names per rung the retained window in lineage order, which `registry._window` also reads; `SHIPPED_RULES` and `SHIPPED_UTILITIES` name each shipped run's rule and utility (`registry.md` §3, D-19, D-20).

**Once, and once only.** Every artefact appears in `entries` exactly one time: `tests/e2e/_surface.py`'s `checkpoint_path_listing` counts *listings*, repeats included, and FAM-12.6 fails on a single repeat, so the index carries **one** list of paths and `shipped` holds rung names — a pair's tenth snapshot and its final model being two distinct files, so naming both is no repeat (ASM-18, `protocol.md` §5).

## 5. What ships, and what a missing run means

- **R1's live run ships**: three seeds × (five retained snapshots + one final model) = **18 artefacts**, `shipped` is `["R1"]`, and every one of them names one rule and one utility, `masked-q-learning` and `net-chips`: `checkpoints/R1/naive-numeric/seed-{0,1,2}/step-{0600,0700,0800,0900,1000}.ckpt` and `…/final.ckpt`. A run **writes** 33 paths for three seeds — ten snapshots plus that pair's final, 11 per variant × seed, regenerable — while the repository **ships** 18: the window's last five per seed plus each seed's final, six per pair, the set a reader protects and what `training.checkpoints()` indexes (ASM-18, `protocol.md` §5, D-19, D-20). The pass adds no 34th path at either count (`greedy.md` §1, §3, ASM-38).
- **R2–R6's entries appear when their runs exist**: a rung whose run has not been written contributes **nothing** to `entries`, rather than a fabricated path — "declared data" and "the artefact exists" are reconciled because the declaration lists the runs that exist, so every path it names is a file (`protocol.md` §5); an entry for a run never executed would fail FAM-12.5's and FAM-16.31's existence checks, and a scan would list the battery's own scratch files.
- **What does not ship**: the five earlier snapshots of each pair (fifteen of the 33 a run writes), any scratch path, `tables/` (that is `evaluation`'s) and any path outside the repository (`module-map.md` §5, FAM-12). A talk loads an entry through `evaluation.policy_from`, so the first entry is a checkpoint `agents.save` wrote, never a manifest (`evaluation/surface.md` §12).
- **A battery writes into a temporary root, so this shipped set is never added to and never overwritten**: `tests/conftest.py` under `pytest` and `tests/e2e/__init__.py` under the `unittest` census point `PYPOKER_CHECKPOINT_ROOT` at a private `mkdtemp` per session (`write-root.md` §4, `docs/L3/harness/layout.md` §5), so the eighteen artefacts are as the shipped run left them (`battery.md` §2 owns that rule, ASM-18 names the eighteen).

## 6. What is left to L4

Whether a path is a `str` or a `Path`, how the declarations are written out, and whether `_entries` sorts or concatenates. Not L4's: §1's two name forms and the ten names' contracts, the `.ckpt` suffix and its reason, the six named artefacts per pair with the pass outside the count, the entry's eleven keys (`rule` and `utility` among them), §4's order, the one-listing rule, `shipped` being rung names (`guardrails.md` G11–G13, G24, ASM-38).
