# harness — the package, and its line budget

- **Layer:** L3 · **Module:** `harness` · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-06 · §5 added (walkthrough finding 5)
- **Owner:** the layout of `src/harness/` — the one file and the order inside it (§1), the line budget unit by unit and
  what the ceiling may not be paid with (§2), the import boundary (§3), the compression ladder (§4), and the session
  write root `tests/conftest.py` sets (§5)
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
- **Read with:** `README.md` §3–§5, `driver.md`, `support.md`, `expectations.md`, `errors.md`, `guardrails.md`

## 1. One file, in this order

`src/harness/__init__.py` is the whole module. A file per concern would cost two lines of import scaffolding, one
docstring and a blank separator each, six times over, and `50 + 10 × 6` leaves no room for that (`README.md` §4). The
order below is the design; every unit is private except the six names in §5 of `README.md`.

1. the module docstring (one line), `import tempfile, time`, `from collections.abc import Mapping`, a blank, the five
   package imports on one line, `__all__` with the six names in `README.md` §5's order;
2. the five declarations — `KINDS`, `COUNTS`, `OBJECTS`, and `ROOT, COST = [], {...}` — in that order, each one
   literal, so a kind, a count spelling, a factory kind and the two accumulators each have one home;
3. the four refusal classes of `errors.md` §2, base first;
4. the three quantity readers of `expectations.md` §2.4 — `_quantity`, `_numbers`, `_deltas` — in that order, because
   each is written in terms of the one before it;
5. the four kind readers of `expectations.md` §2, in the kind set's order — `_zero_sum`, `_legal_choice`, `_counted`,
   `_refused` — then the `_CHECKS` table binding each kind name to its reader;
6. `expect`, then `fixtures`, `factory`, `seam` (`support.md`), then `timings` (`driver.md` §6);
7. `drive` and the three units it is written in terms of — `_hands`, `_judge`, and the shape check `driver.md` §1
   describes — grouped together and placed before `drive`, so the reader meets the parts before the whole.

Nothing else. No `__main__`, no `if TYPE_CHECKING`, no logging, no cache, no module-level state beyond `ROOT` and
`COST`, and no second spelling of any of the six names.

## 2. The budget, unit by unit

The measured target for the whole package is **≤ 140 lines** as `wc -l` counts them — blank and comment lines
included, which is the strictest reading. The allowance below sums to 133, leaving seven lines of slack for a
long-wrapped expression or a blank line a reviewer needs:

| # | Unit | Allowance |
|---|---|---|
| 1 | docstring, three import lines, `__all__`, two blanks | 7 |
| 2 | `KINDS`, `COUNTS`, `OBJECTS`, `ROOT, COST` and one blank | 6 |
| 3 | four refusal classes and three separators | 11 |
| 4 | `_quantity`, `_numbers`, `_deltas` and two blanks | 11 |
| 5 | the four kind readers, `_CHECKS`, four blanks | 24 |
| 6 | `expect` | 7 |
| 7 | `fixtures`, `factory` | 10 |
| 8 | `seam` — the closure and its attributes | 12 |
| 9 | `_hands`, `_judge` and two blanks | 18 |
| 10 | `drive` | 22 |
| 11 | `timings` | 5 |
| | **total** | **133** |

**Delivered and measured** (2026-11-05): `src/harness/__init__.py` is **147 lines** — the allowance above plus one blank
line between each of the seven public definitions, four expressions that wrapped, and the three lines of `expect`'s
totality guard (`expectations.md` §3: one `try`, the one `_CHECKS` read, one `except` that turns a reader's exception
into the kind's named failure). The design's **hard limit is 150**; over 150 means the file carries something no
document asks for. 147 is inside that limit, seven over the ≤140 target and fourteen over the allowance, and the gap to
the brief's 110 is 37.

**Why 110 is not reachable, measured.** The ceiling the brief computes is `50 + 10 × 6 = 110`, and `strata-lint`
prints it as an INFO row without measuring anything (`strata-lint.mjs` §6, `module-map.md` §4). The six entry points
of `surface.md` do not fit in 110 lines:

- the irreducible bookkeeping of the six names — the case pass, the judgement pass, the six-kind dispatch table, the
  seam closure, the fixture root, the cost record — is ≈100 lines before a single expectation kind exists;
- the four kinds and the three readers they share cost ≈35 more (`expectations.md` §2);
- trimming the kind set to one frees 17 and still leaves ≈116, and it makes `expect` the one-assertion runner L2's H-1
  rejected — so the trim buys nothing and costs a contract clause.

A 110-line version exists only as unformatted code: no blank line anywhere, no docstring on any entry point, several
statements per line. That is not a smaller harness, it is an unreadable one, and `strata/examiner.md` §2 has to read it
in full. **The measured overrun is reported to L2 rather than paid for with a clause of `surface.md`** — L2 owns the
ceiling's arithmetic (`50 + 10 × N` with N L1's) and the kind set is the only vocabulary this layer could trim.
`README.md` §4 records the reading of the cap this design adopts: it governs the support code a battery carries, as it
does for the other five modules, whose `src/` trees measure 703 (cap 140), 804 (120), 2564 (150), 2267 (160) and 1742
(110) lines — measured 2026-11-05.

## 3. The import boundary

The three standard-library imports are `tempfile` (the scratch root), `time` (`perf_counter`, the monotonic clock) and
`collections.abc.Mapping` (the case, the record and the observation tests). The five packages are imported once, on one
line, so that `OBJECTS` binds six callables and `factory` contains no import of its own. Six calls, one per factory
kind (`README.md` §5) — and nothing else, ever: no `os` (nothing here writes or removes a path), no `random` (the only
stream this module touches moves inside `engine.new_hand`, ASM-2), no `json`, no `math`.

## 4. The compression ladder

When the file measures over its allowance, compress in this order and stop at the first rung that pays:

1. a private helper loses its docstring; only the module and the six public names keep one line each;
2. an expression wrapped over several lines becomes one line if it fits in about 120 columns;
3. two adjacent private definitions share one blank line, not two;
4. the four kind readers become one block with no blank line between them, and so do `_quantity`/`_numbers`/`_deltas`.

**Never compressed**: a key `surface.md` §2, §3, §6 or §7 names; a refusal `surface.md` §4, §5, §6 declares; the
`__all__` line; the one-line docstring of a public name that says which `§` of `surface.md` it realises; the four
`KINDS` in their declared order; and the `COST` keys' four fact names. A rung that would remove one of those is not a
rung — it is `layout.md` §2's report to L2.

## 5. The session write root

A battery writes checkpoints, so `tests/conftest.py` — harness-owned and the one file every battery's pytest invocation
executes (`module-map.md` §5) — sets `PYPOKER_CHECKPOINT_ROOT` to
`tempfile.mkdtemp(prefix="pypoker-battery-checkpoints-")` at import, before a case is collected:

- **unconditionally**, whatever the shell carries, because an inherited value must not send a battery's writes into
  `<repo>/checkpoints` — the walkthrough's defect, where running the batteries left `seed-4103`, `R2/` and `R4/` in a
  tree `.gitignore` hides (`write-root.md` §3–§4, `strata/records/phase1-walkthrough.md` finding 5);
- **the override a reader already has**, never a second mechanism — one name, one meaning, the one `write-root.md`
  §3–§4 gives a single command line (D-13);
- **removed at session end** with `atexit` and `shutil.rmtree(path, True)`, because a battery leaves the repository as
  it found it. `fixtures()`'s scratch root is deliberately kept (`support.md` §1) — it holds a case's own artefacts,
  while this root only catches what a run would otherwise have written into the shipped tree (`checkpoints.md` §5);
- **reads do not follow it**: the index, the declared windows and every pool built from a repository-relative
  declaration still resolve against `<repo>` (`write-root.md` §2), a written path is absolute and its record relative
  or unchanged (`checkpoints.md` §2);
- **no import, no judgement**: `<repo>/src` goes on `sys.path` once (`module-map.md` §5) — the outcome, not a position;
  the additions are `atexit`, `shutil` and `tempfile`, no entry point of `README.md` §3 is stood in for, and no case is
  skipped, configured or re-meant (`battery.md` §2, D-13); `src/harness/` is untouched, so §3 and §4 stand. Caught by
  `HRN-9.1`–`HRN-9.3`.
