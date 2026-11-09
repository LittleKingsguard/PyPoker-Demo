# training — L2 integration interface

- **Layer:** L2 · **Module:** `training` · **Unit:** phase1 · **Rev:** 4 · **Date:** 2026-11-08
- **Covers:** the six entry points of `docs/L1/e2e-surface.md` §3.5 — the rung registry and the one training loop every
  rung is a configuration of (D-3, D-16) — plus the two paths this module owns: `notebooks/`, one thin notebook per rung
  (D-5), and `checkpoints/`, the shipped models and intra-run snapshots the pool is a view over (`module-map.md` §5, ASM-18)
- **Reads:** `docs/L1/module-map.md` §1–§5, `e2e-surface.md` §1, §2, §3.5 and §5, `records.md` §1–§5, §7–§8, §12–§13,
  `ladder.md` §1–§7, `league.md` §1–§6, `protocol.md` §1–§6, `battery.md` §2–§5, `assumptions.md` (ASM-2, ASM-5,
  ASM-7–ASM-10, ASM-12, ASM-15, ASM-16, ASM-18); at the consumed edge `evaluation/surface.md` §3–§8, `evaluation/league.md`
  §1–§7, `agents/surface.md` §3–§8, `features/surface.md` §3–§9 and `engine/surface.md` §3–§10, plus `tests/e2e/`
- **Ceiling:** 62 lines. At the ceiling, split by owner — never append

## 1. The one job

`training` is the rung registry plus the one training loop every rung is a configuration of: it declares the lineage it
inherits, freezes the pool that lineage yields before a variant trains, draws each hand's opponent from that pool,
plays the hands through `engine` on an observation from `features` and a decision and update from `agents`, and returns
the run record (`module-map.md` §1, §3, D-3, D-16). It never claims a result, never measures a cell, never fits a
rating and never chooses the pool's membership (`module-map.md` §3, D-16, ASM-16). Because there is one loop and a rung
is a row of data, a rung-to-rung difference is attributable to the configuration and to nothing else, and a seventh
configuration runs without new code (D-3, `ladder.md` §1, `battery.md` §3 FAM-15).

## 2. The seven documents

| Document | The owner of that question | What it fixes |
|---|---|---|
| `surface.md` | the callable surface | for each of the six entry points: its signature, its argument contract, the record `records.md` §12 pins, its refusals and its determinism (`e2e-surface.md` §3.5, D-12). **Rev 2** adds §3.1 (a pool's id, read once), §4.1 (the three further keys a report needs), §4.2 (the vocabulary a run refuses against) and §5.1 (the axis rule the matched capacities force); **Rev 3** states in §4 where a run writes and how it spells a path; **Rev 4** moves §6's probe rule out to `devices.md`; **Rev 5** points §4's and §5's refusals at `declarations.md`; **Rev 7** makes §4's `pool` row and §7's entries carry the `rule` (D-19) |
| `declarations.md` | what a configuration may declare | every key of `ladder.md` §3 read against the loop (§1), the rule that a declaration the run would discard is refused (§2), the two classes and what each message names (§3), the eight declarations a matched pair shares (§4) and why a `hyper` block is refused rather than honoured (§5) (ASM-7, ASM-8, ASM-18, D-3) |
| `devices.md` | the device record | `devices()`'s three keys (§1), the **read-write** open the probe measures and the four situations its `reason` tells apart (§2), and the one thing a run does with the device it records (§3) (D-8, `protocol.md` §6, `docs/L1/gpu.md` §2) |
| `loop.md` | the ladder and its edges | the registry as data (§1); the configuration schema and the matched pair (§2); the one loop, step by step (§3); what a comparison holds constant and the R1/R2 parity rung (§4); budgets and devices (§5); the notebooks (§6); the checkpoints that ship (§7); the contracts at this edge (§8) and the battery invariants this module carries (§9) (D-3, D-7, D-8, D-16, ASM-8, ASM-18) |
| `write-root.md` | where a run writes | the declared root and the write root (§1), the reads that never move (§2), the one ambient override `PYPOKER_CHECKPOINT_ROOT` and why it is not an entry point (§3), who points it where — the battery session and the reader's one command (§4), the spelling a record gives a written path (§5), what the redirection does not change (§6) and the battery cases that carry it (§7) (D-12, D-13, `battery.md` §2, `protocol.md` §5) |
| `evidence.md` | the one shipped evidence file | `checkpoints/evidence/r1-live.json` as an integration fact: it is evidence and not a surface (§1), which of its blocks are this module's record (§2), the repository-relative spelling of its paths (§3), the two curve layouts (§4) and what no caller may do with it (§5) (D-8, D-12, `protocol.md` §5) |
| `utility.md` | the terminal-reward utility at this edge | what a configuration declares and a run honours (§1), **the one place the reward is transformed** (§2), what the loop records (§3), the shipped index's field (§4), the seventh fairness axis (§5) and the four numbers this layer asserts (§6) (`utilities.md` §2–§8, D-20, `battery.md` §5) |

## 3. Boundaries

Each of the following is a boundary and not a preference (`module-map.md` §3, D-3, D-13):

- never trains a second loop, a second variant or a second rung: every rung is a configuration of one driver (D-3, `ladder.md` §1);
- never chooses the pool's membership and never rolls the window: it declares the lineage it inherits and freezes what it yields, and `evaluation.offer` is the only roller (D-16, ASM-16, `module-map.md` §3);
- never measures a cell, fits a rating, assembles a report or reduces a table to a ranking (D-16, `module-map.md` §3);
- never claims a result: it reports curves, a pool, seeds, budgets, devices and costs, and a version's worth is a table position `evaluation` measures (D-6, `league.md` §8, `records.md` §13);
- never seeds, reads or advances the global `random` stream except through `engine.new_hand`, because one stream deals
  every hand and sequential play is the contract (ASM-2, `protocol.md` §4);
- never calls a module the map does not grant it: five `evaluation`, four `agents`, five `features` and four `engine`
  calls, and no `harness` at all (`module-map.md` §2, D-13);
- never carries code into a notebook and never lets one reach past an entry point (D-5, `ladder.md` §7).

## 4. Counts, cap and the blind instances

Six entry points, and L2 adds, removes and renames none of them: needing a seventh is a defect that returns as an
adjudication to L1 and is never invented here (D-12, `e2e-surface.md` §1). The harness files that drive this module are
capped at `50 + 10 × 6 = 110` lines, computed by `strata-lint` and never asserted by a harness author (brief §5,
`module-map.md` §4). Two rows are `fixed` — `rungs`, `devices` — and four are `general`, so the battery carries four
instances invented from this surface alone (`e2e-surface.md` §5, D-15).

## 5. What is left to L3

This document stops at the entry point, the record it returns and the data that is the registry. `role_l3_designer`
owns the module design: the widths, depths and sparsity that make a pair match within ±2% (ASM-10), the derivation of a
hand's deal and opponent seeds from the run seed and the hand index, the transition batch and the reward transform it
applies, the snapshot naming and the layout under the write root (`write-root.md` §1, §5), the index's own nesting, the error classes, and the layout of `src/training/` (D-1, ASM-18, `module-map.md` §5, D-12, D-13, D-20).
