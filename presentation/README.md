# The deck — how to open, drive and edit it

`presentation/index.html` is the whole slideshow: one file, inline CSS and JS, no network, no build step.

## Opening it
Double-click `presentation/index.html`, or `firefox presentation/index.html` — it runs from `file://` with no server, fills the window letterboxed on a felt field, and the stage is always 16:9 (1280×720, scaled). Add `#/3` to the address to open slide 3 directly; to project, put the browser in fullscreen (`f`, or the browser's own control).

## Controls
| Input | Action |
|---|---|
| `→` `↓` `PageDown` `Space` | next slide |
| `←` `↑` `PageUp` `Shift+Space` | previous slide |
| `Home` / `End` | first / last slide |
| Wheel (down / up) | next / previous (one step per 60 px, 400 ms cooldown) |
| Click right 30% / left 30% of the window | next / previous; the middle 40% does nothing |
| `f` | enter fullscreen (`Esc` leaves it; a browser that refuses does nothing) |
| `N` | presenter notes for this slide, on and off |
| `M` (or the HUD's `More`) | this slide's sources, on and off; on a slide with none it stays focusable and reads `aria-disabled` — `M` opens nothing, and the control never disappears (a `disabled` button would be unfocusable, so the fact would be announced to nobody) |
| `Esc` | close the panel you opened last; `N` and `M` also close it |
| `Ctrl` / `Alt` / `Meta` + anything | nothing: the deck never hijacks a browser shortcut |

With a panel open, wheel and click navigation are off so that scrolling notes cannot change slides; the arrows still work. Design: `docs/presentation/design.md` §6.

## Presenter mode
**The audience sees** the stage and its HUD, and nothing else: the notes panel is closed at load, is never opened by a URL, a hover or a slide change, and its text is not in the page's rendered text at all. **You see**, on `N`, a drawer on the right edge of your window with the notes for the current slide (dates, figures, caveats); on `M`, a pane with that slide's sources, each naming a `strata/decisions.md` row or a `strata/records/` path and a date. Both panes can be open at once, stacked in the same drawer, and they behave differently when you step: **notes** follow the slide (a slide with no notes says `No notes for this slide`), while **sources** never outlive their slide — step onto a slide with none and that pane closes, and if it was the only one open the drawer closes with it, so press `M` again on a slide that has sources to bring it back. Nothing reopens by itself.
The drawer is fixed to the window, so it does **not** scale with the stage and never changes the slide: notes stay readable on a small laptop screen. It covers the right of the stage while open, and the counter never. Notes live in the file itself, in a `<template class="talk">` inside six of the seven slides (`#/2` has none); sources in `<template class="more">` on `#/4` and `#/5` only, two entries each. **If you mirror your screen, your notes are on the projector** — nothing can prevent that, so open them deliberately and close them before a question. Full specification: `docs/presentation/presenter.md`.

## Editing a slide
All slides live in this one file, inside `<div class="deck">`, one `<section class="slide">` each, in order — `#s1` title, `#s2` divider, `#s3` bullets, `#s4` comparison, `#s5` chart, `#s6` quote, `#s7` closing. A slide is a section holding one to three `article.card` elements in named areas: `.a-hero`, `.a-lead`/`.a-body`, `.a-wide`/`.a-side`, `.a-chart`/`.a-legend`, `.a-side-top`/`.a-side-bottom`. At a glance:

    <section class="slide" id="s3" data-shape="bullets">
      <article class="card a-lead"> <div class="t-badge"><span class="demo-badge">DEMO</span></div> <h2 class="t-h2">Demo bullet card</h2> </article>
      <article class="card a-body"> <ul class="t-list"> <li>…</li> </ul> <p class="t-note">…</p> </article>
      <template class="talk"><ul class="note-list"><li>what to say (demo)</li></ul></template>
    </section>

**Edit text inside an existing block, not its size.** Each shape's block heights are `#sN`-scoped CSS rules — that is what keeps every slide inside the 1280×720 surface, so the copy has to fit the block it is written into. The budgets are in characters, approximate and deliberately conservative (`docs/presentation/design.md` §5): a bullet (`.t-list li`, one 38px line) **≤ ≈62**; a side note (`.t-group p`, two 38px lines in a 76px box) **≤ ≈36, ≈18 a line**; a table cell (`.t-table th`/`td`, one 44px line) **≤ ≈13**; a caption, note or heading is one line.
**Longer text is clipped, not reflowed.** The clip rule in `docs/presentation/design.md` §2 is in the file: the card clips, and the nested block boxes (`.t-list li`, `.t-group p`, `th`/`td`) clip themselves, the table cells also running `nowrap` so a row stays 44px under a cell `height` that is only a minimum. So an over-long bullet is cut off at its own 38px line instead of painting across the 16px separator and over the next bullet, an over-long side note stops inside its 76px box, an over-long cell stops at 44px. Clipping loses words silently, so the copy must fit: shorten it, never edit the px.
**An eighth slide is one ordered change, and every step is load-bearing** — copying a section alone gives an unstyled slide, because the heights and the clips are both `#sN`-scoped:
1. **The section, last in the deck.** A new `<section class="slide" id="s8" data-shape="<new word>">` after `#s7`, holding one to three `article.card` in the existing area classes (`.a-hero`, `.a-lead`/`.a-body`, `.a-wide`/`.a-side`, `.a-chart`/`.a-legend`, `.a-side-top`/`.a-side-bottom`); a new area means a new area-class rule at design §4's literal px, not a new layout idea.
2. **Its own `#s8` height rules.** One `#s8 .a-… .t-…` rule per block in the `<style>`, each a literal px `height` and `margin`, summing to **≤ the card's inner box** (design §5, A8a) — an unstyled block has no height and paints over its neighbour. The text budgets are **per block** (≈62 characters a bullet, ≈36 a side note, ≈13 a cell), so the new slide's copy must fit its own blocks, not a copy of the old slide's. **Note:** the `margin` is load-bearing, not decoration — dropping the `li + li { margin-top: 16px }` separator still builds gate-clean at both window sizes while leaving the bullets visibly bunched, and no check sees it.
3. **Its own `#s8`-scoped clip and `nowrap` rules — the step that has been missed.** `html.js .card` and `.card > *` clip on every slide, but the boxes one level deeper clip **only** because of `#sN`-scoped selectors, so a copied shape arrives unclipped. So copy the clip for the blocks **your shape actually has** — the blocks whose height you fixed in step 2 — and for no others; no shipped shape has all four (`#s3` carries `.t-list li`, `#s4` carries `.t-group p` and the two cells). One selector each, with your own `#s8`: `html.js #s8 .a-body .t-list li` (a 38px bullet stops inside its own line instead of painting across the 16px separator and over the next bullet), `html.js #s8 .a-side .t-group p` (a 76px side note stops instead of overprinting the next `.t-group`), `html.js #s8 .a-wide .t-table th` and `html.js #s8 .a-wide .t-table td` (a 44px cell likewise — and a cell's `height` is only a *minimum* in this engine, so those two also take `white-space: nowrap`, without which one wrapped line makes the row 79px, not 44px). Writing a selector for a block the slide does not contain is harmless but pointless — it matches nothing — so match the shape's own blocks and leave the absent ones out; a cell that clips without `nowrap` loses text to the right with no height change at all, which is the defect `G4` looks for.
4. **One more `.dot`.** The HUD's dots are static markup (`#hud .dots .dot`, one `<span>` each), so they do **not** follow the count and the HUD would under-report the deck. The counter (`n / N`), the `#live` line (`Slide n of N — shape`) and the `#/N` range are computed from the section count in the script and need no edit.
5. **A new `data-shape` word.** Declare it in `docs/presentation/design.md` §5 **and** add it to A3's ordered list in the same change as the section; never reuse one of the seven, because the attribute is only the label `#live` announces and a reused word describes a shape the slide is not.
6. **The three document counts — and the gate's own total.** `design.md` A3 ("exactly seven `<section class="slide"`"), A4 (seven `class="demo-badge"`) and A9 ("`#/7` shows three cards") are the deck's numbers and are updated with it; the gate holds no constant, because `presentation/check.mjs` derives the total from the deck it loads, prints `slides: N (derived from section.slide)`, and checks the counter, `#live`, the dot count and every `#/N` round-trip against it (`docs/presentation/checks.md` §4, G3). Run it and read the number it printed: if that is not the count you just wrote into the three rows, the edit is incomplete.
7. **Optional per slide, and legal to omit: the two templates.** `<template class="talk">` with `ul.note-list > li` for notes, `<template class="more">` with `ul.src-list > li > span.src-claim + span.src-ref` for sources, both direct children of the section and never inside a card. Omit the notes and `N` opens the pane reading `No notes for this slide`; omit the sources and `.more-btn` stays `aria-disabled` and `M` opens nothing. Both are legal, and both are **visible** — that is the choice an editor makes for a new slide, so make it deliberately (`docs/presentation/presenter.md` §1, P4, P5).

## Numbers
A measured number may be pasted **only** from `strata/decisions.md` or `strata/records/`, with the record's date beside it; invented or rounded-up figures are banned everywhere in the deck. When real content arrives, every such figure is also entered in `presentation/FACTCHECK.md` (claim as it appears, record path, date, what the source does not support, and what is still unresolved). A figure with no entry never reaches a slide. Form: `docs/presentation/checks.md` §7. Content rules for that pass: `docs/presentation/content-rules.md`.

## Checking it before a talk
The gate is a **dev tool**, not part of the deck: the deck is presented as this one file and never needs it, so there is still no build step. With Firefox installed:

    node presentation/check.mjs --out /tmp/check-shots

It opens the deck headless, screenshots every slide at 1280×720 and 1600×1000 into that folder, and flags anything outside the slide, any clipped or overlapping text, text under 14px, a broken `#/N` round-trip and a presenter panel that overflows or leaks. It prints the slide total it derived from the deck, then one line per issue, or `no issues`, and exits 0 or 1. **A clean check is not a design review:** look at the screenshots. Contract and checks G1–G10: `docs/presentation/checks.md`.

## Not in this pass
Every slide is placeholder demo content, marked `DEMO`, so theme and navigation can be tested first; real talk content, real numbers and the real narrative are a later pass (D-118, D-121). The presenter drawer and the gate exist and are exercised with demo notes and demo sources: two slides carry sources (`#/4`, `#/5`), two demo entries each, and the rest carry none, which is the state the HUD's `More` control reports; the fact-check file is written with the real content. Design authority: `docs/presentation/design.md`.
