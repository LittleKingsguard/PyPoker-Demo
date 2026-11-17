# P-talk-deck — exit walkthrough (D-14), run 5

- **Date:** 2026-11-17 · **Verdict:** `PASS` · **Runner:** fresh L3 examiner, blind, staged to
  `/tmp/deck-walkthrough/` (4 design docs + README + deck + gate + FACTCHECK; `work/` scratch)
- **Scenarios:** 11, L0-authored · **Stage:** docs only — no staged file edited, no source access

| # | what was attempted | outcome |
|---|---|---|
| 1 | open, one key step | `2 / 7`, dot 2 lit, `#live` "Slide 2 of 7 — divider" |
| 2 | cold jump to slide 5 | `#/5` renders the chart slide |
| 3 | `#/99`, `#/0`, then `←`/`→` in each | bar keeps the typed value; `→` at the clamped end writes nothing; the first real move rewrites it |
| 4 | notes for slide 4, then steps | drawer 435 px outside `#stage`, 20 px notes, stage rect and `--scale` unchanged; notes follow the slide, `#/2` says "No notes for this slide" |
| 5 | sources on `#/4`, then `#/3` | two entries each containing a `D-\d+` row or `strata/records/` path plus an ISO date; on `#/3` the control is focusable, `aria-disabled`, and opens nothing; four demo entries in the file, two slides |
| 6 | fullscreen, `Esc` with both panes | `Esc` closes the most recently opened, then the other, then nothing; no navigation |
| 7 | bullet at 2× budget | clipped at its own 38 px box, words lost silently; found before the talk by gate G4 (measured 39 px clipped) |
| 8 | run the gate | `slides: 7 (derived from section.slide)` then `no issues`, exit 0, 16 PNGs at 1280×720 and 1600×1000 |
| 9 | eighth slide by the recipe | recipe followed literally produced `slides: 8` + `no issues`, exit 0 |
| 10 | a training figure | only from `strata/` records with the date, plus a `FACTCHECK.md` row; no row, no slide |
| 11 | Python surface | deck is not a module; `check.mjs`, `FACTCHECK.md`, the docs are dev-only |

**docs-insufficient:** none. **docs-stale:** none.

**undocumented:** the gate counts a clipped block's hidden line boxes as overlapping text (a 2× bullet
reports an `overlap` line while the pixels show no ink outside the block) — an editor cannot tell an
invisible line box from text painted over its neighbour. Carried, not blocking: one code comment at
`refreshPanels()` still reads "an open drawer follows the slide" (true for notes only), and the README's
wheel row omits the 250 ms quiet reset that `design.md` §6 states.

**Prior findings, all fixed:** the source-entry count (docs now say two slides, two entries each, four in
the file); the pane behaviour (notes follow the slide, sources never outlive it, the drawer closes with the
last pane, nothing reopens); `disabled` vs `aria-disabled` in the README's controls table; and the clamped
`#/0` address-bar rule in `design.md` §6.

**History:** run 1 STALE (clipping claimed but absent) → run 2 STALE (stale §2 wording, `data-shape`
contradiction) → run 3 DOC-GAP (incomplete eighth-slide recipe, stale cross-references) → run 4 STALE
(source count, pane promise, `disabled` wording, `#/0` bar) → run 5 PASS. Each run's findings were routed
to the owning layer and the record replaced.

**Reported ready:** `presentation/index.html` (7 sampler slides, presenter mode, fixed 16:9 stage, offline, one
file) with `presentation/check.mjs` as its dev gate and the four design documents that pass this walkthrough.
