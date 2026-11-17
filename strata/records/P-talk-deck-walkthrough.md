# P-talk-deck — exit walkthrough (D-14), run 3

- **Date:** 2026-11-17 · **Verdict:** `DOC-GAP` · **Runner:** fresh L3 examiner, blind, staged to
  `/tmp/deck-walkthrough/` (5 docs + deck + gate + FACTCHECK; `work/` scratch) · **Scenarios:** 11, L0-authored
- **Staged:** `docs/presentation/{design,presenter,checks,content-rules}.md`, `presentation/README.md`,
  `presentation/index.html`, `presentation/check.mjs`, `presentation/FACTCHECK.md`

| # | what was attempted | outcome |
|---|---|---|
| 1 | open, one key step | `2 / 7`, `#/2`, dots + counter + `#live` all agree |
| 2 | cold jump to slide 5 | `#/5` renders the chart slide |
| 3 | `#/99`, `#/0` | 7 and 1, exactly as A11 predicts; address bar keeps the typed value |
| 4 | notes for slide 4 | drawer 435×720, `20/28` notes, `16px` refs, stage untouched, closed → no notes text in `innerText` |
| 5 | sources on `#/4`, then `#/3` | two entries with `D-118 · 2026-11-17` and the records path; `.more-btn` `aria-disabled` on the slide with none |
| 6 | fullscreen, `Esc`, slide change with a pane open | panes close `Esc`-newest-first; the pane follows the slide |
| 7 | bullet at 2× budget | gate flags `G4 li clips 39px vertically` on an injected copy, exit 1 — the documented procedure answers it |
| 8 | run the gate | `no issues`, exit 0, 16 PNGs at 1280×720 and 1600×1000 |
| 9 | add an eighth slide | **incomplete: the recipe omits the `#sN` clip/`nowrap` rules and the four seven-slide constants** |
| 10 | a training figure | only from `strata/` records with the date, plus a `FACTCHECK.md` row and a sources entry |
| 11 | Python surface? | deck is not a module; `check.mjs`, `FACTCHECK.md`, `docs/presentation/` are dev-only |

**docs-insufficient:** the eighth-slide recipe (`README.md` §Editing a slide) omits that the clip and
`nowrap` rules are `#sN`-scoped, so a copied shape lands unclipped; and no doc says that A3 ("exactly
seven"), A4 (seven badges), A9 (`#/7` shows three cards) and `check.mjs`'s own slide total must move with
it — following the docs leaves the deck red at its own gate. Minor: nothing states that a step press at a
clamped `#/99` is a no-op, so the address bar stays stale (`design.md` §6 reads as "next keypress").

**docs-stale:** `design.md` §5 cites "`presentation/README.md`, §6" — README has no numbered sections and
the rule lives under "Editing a slide"; and `design.md` §2's HUD sketch omits `button.more-btn`, which sits
in the HUD and is documented two sections later.

**undocumented:** none.

**Prior findings:** the stale clipping passage (§2) is **fixed** — three clip tiers as described, deck
G4-clean, a 2× injection clips at its own box; the `data-shape` contradiction is **fixed** — both docs call
it a label, no CSS parses it, only the `#live` string reads it.

**Routing (§6):** both stale citations and the gap sit in L3-owned documents; the gate's slide-count
constant is an L3 design question (derive it, or make the number one declared place) with a small L4 change.
Re-run this walkthrough after the correction; this record is replaced.
