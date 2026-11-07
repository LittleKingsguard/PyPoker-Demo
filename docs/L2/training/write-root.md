# training — where a run writes: the write root

- **Layer:** L2 · **Module:** `training` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-06
- **Owner of this file:** the root a run writes into (§1), the declared root every read resolves against (§2), the one
  ambient override and its name (§3), who points it where and the one command a reader uses (§4), the spelling a record
  gives a written path (§5), what the redirection does not change (§6) and the battery this contract carries (§7)
- **Reads:** `docs/L1/e2e-surface.md` §1, §2, §3.5, `protocol.md` §4, §5, `records.md` §7, §12, `battery.md` §2,
  `module-map.md` §4, §5, `assumptions.md` (ASM-2, ASM-5, ASM-18), `tests/conftest.py`, `tests/e2e/__init__.py`; the L3 file this one is not —
  the layout's names, its index and its write root — is always cited here as `docs/L3/training/checkpoints.md`
- **Ceiling:** 90 lines. At the ceiling, split by owner — never append

## 1. Two roots, and one layout over both

A run writes `docs/L3/training/checkpoints.md` §1's layout — `<rung>/<variant>/seed-<seed>/step-<step:04d>.ckpt` for the
ten snapshots and `final.ckpt` for that pair's model — and the root it writes under is the one thing this file fixes
(`protocol.md` §5, ASM-18):

- **the declared root** is `<repo>/checkpoints`, `layout.CHECKPOINT_ROOT`: derived from `layout.py`'s own location and
  never from the caller's working directory (`module-map.md` §5, `docs/L3/training/checkpoints.md` §1);
- **the write root** is what a run actually writes under, `layout._write_root()`'s answer: the declared root unless §3's
  override names another one;
- **with the override unset the two are one root**, so a run started by a reader from the repository root writes the
  shipped layout exactly as before — the default is unchanged and nothing a reader does today changes meaning
  (`battery.md` §2, D-8).

## 2. What never moves: every read

Reads resolve against `<repo>` whatever the write root is, because they are declarations about what ships and not
statements about what a run just wrote (`protocol.md` §5):

- `training.checkpoints()` and its `root` key, and the declared `SHIPPED_FINALS`/`SHIPPED_WINDOWS` sets behind it
  (`docs/L3/training/checkpoints.md` §4–§5);
- `layout._resolve` for a recorded path, and `layout._snapshot_path`/`_final_path`, which name the *declared* layout and
  never the write root (`docs/L3/training/checkpoints.md` §1–§2);
- every pool built from a repository-relative declaration — `rung()`'s window and a run's frozen pool — so no version the
  repository carries goes missing because a run was pointed elsewhere (`protocol.md` §5, D-16).

A battery that wrote into a temporary root therefore leaves the index, the rungs' declared windows and every shipped
artefact exactly as they were (FAM-12.5, FAM-16.31, `protocol.md` §5).

## 3. The one ambient override

**Name: `PYPOKER_CHECKPOINT_ROOT`.** `training.layout` reads it on **every call** and never caches it at import, so an
override set after `import training` — by a test session, a shell, a notebook kernel — still applies
(`docs/L3/training/checkpoints.md` §2, D-13). Three rules:

- unset, or empty, is the declared root: the default of §1; a value equal to `<repo>/checkpoints` behaves as the default;
- a value is a filesystem path used as the write root, made absolute from the process's working directory, so an absolute
  value is what makes §4's one command work from any directory;
- **it is not an entry point.** The six names and their signatures are fixed, and `modules.json` declares `training` 6
  endpoints, from which `strata-lint` computes the harness ceiling `50 + 10×6 = 110` (`e2e-surface.md` §1, §3.5,
  `module-map.md` §4). Rejected: a `root` keyword on `run` (a signature change) and a seventh exported setter (a new
  entry point) — either is an `ADJUDICATION` to L1 and never L2's to invent (`modules.md` §3, D-12).

The override sits outside Python's call signature on purpose: one ambient fact points every caller elsewhere (D-13).

## 4. Who points it where

- **Every battery session, whichever runner.** `tests/conftest.py` under `pytest` and `tests/e2e/__init__.py` under the
  `unittest` census — both `harness`-owned (`module-map.md` §5) — set `PYPOKER_CHECKPOINT_ROOT` to a private
  `tempfile.mkdtemp(prefix="pypoker-battery-checkpoints-")`, **unconditionally**, recording the one root in the
  battery-only `PYPOKER_BATTERY_ROOT` so the second hook declines; it goes at exit (`docs/L3/harness/layout.md` §5, finding 5, D-13).
- **A reader, on one command line** — the one-liner L1's `getting-started.md` §4 must carry (owed by L1, named here):

      PYPOKER_CHECKPOINT_ROOT=/tmp/pypoker-run PYTHONPATH=src .venv/bin/python -c "import training; print(training.run('R1')['checkpoints'])"

## 5. The spelling a record gives a written path

A record spells an artefact **relative to the repository root, POSIX separators, when the artefact is inside it — and
unchanged, i.e. the absolute path `agents.save` was handed, when it is outside it.** That is `layout._relative`'s
behaviour, and it keeps the record portable without pretending an outside artefact ships (`protocol.md` §5, `records.md`
§12, `docs/L3/training/checkpoints.md` §2): a default run carries `checkpoints/R1/…/seed-0/final.ckpt`, a redirected run
`/tmp/pypoker-run/R1/…/seed-0/final.ckpt`, and both name a file that exists (§7's cases assert exactly that).

## 6. What the redirection does not change

Same seeds, hands, values, pool ids and index contents; the same six signatures, the same record keys and the same ten
snapshots plus final model per variant per seed (`e2e-surface.md` §2, `records.md` §12, ASM-18, D-6). `checkpoints()` still
lists no artefact a run wrote (declared data, never a scan), and only *where a run writes* moves — when §3's name is set.

## 7. The battery this contract carries

| Case | What it asserts |
|---|---|
| `tests/training/test_loop.py` TRN-2.7 | a record's path is repository-relative when the artefact is inside the repository and unchanged when it is outside (§5) |
| `tests/training/test_checkpoints.py` TRN-6.5 | the layout makes the pair's directory under the write root and nothing else (§1) |
| `tests/training/test_checkpoints.py` TRN-6.4, TRN-6.8 | `_snapshot_path`, `_final_path` and a declared window stay repository-rooted (§2) |
| `tests/training/test_checkpoints.py` TRN-6.9 | a successful run adds no path and changes no byte under `<repo>/checkpoints/` (§1, §6) |
| `tests/harness/test_harness_session_root.py` HRN-9.1–HRN-9.2, HRN-9.4, HRN-9.5 | each hook points the override at a private temporary directory, unconditionally and once, and removes it at exit; one name still points a run (§4) |
| FAM-12.1, FAM-12.5, FAM-16.31 | a record's paths exist, and every index path exists inside the repository, whatever the write root (§2, §5) |
