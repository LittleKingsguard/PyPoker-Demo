# The deck — how to open, drive and edit it
`presentation/index.html` is the slideshow: one file, inline CSS and JS, no network, no build step. **Nine slides, all real** — since D-133 deleted the five demo sampler slides — and since D-132 it references two SVGs in `figures/`, by relative path, so **the deck travels with the repo, not alone** (see Figures).

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
**The audience sees** the stage and its HUD, and nothing else: the notes panel is closed at load, is never opened by a URL, a hover or a slide change, and its text is not in the page's rendered text at all. **You see**, on `N`, a drawer on the right edge of your window with the notes for the current slide (dates, figures, caveats); on `M`, a pane with that slide's sources, each naming a `strata/decisions.md` row or a `strata/records/` path and a date. Notes **follow** the slide — all nine carry notes, and a slide without one would say `No notes for this slide`; sources **never outlive** their slide — step onto a slide with none and that pane closes, and if it was the only one open the drawer closes with it. Nothing reopens by itself. The drawer is fixed to the window, so it does **not** scale with the stage: notes stay readable on a small laptop screen, it covers the right of the stage while open, and the counter never. **If you mirror your screen, your notes are on the projector** — open them deliberately and close them before a question. Notes live in the file, in a `<template class="talk">` inside **all nine** slides; sources in `<template class="more">` on **four**: `#/4`, `#/5`, `#/6` and `#/8` (one entry each) — the other five carry none and say so through `aria-disabled`. Full specification: `docs/presentation/presenter.md`, and the six content slides' notes: `docs/presentation/presenter.md` §1.1.

## Editing a slide
All slides live in this one file, inside `<div class="deck">`, one `<section class="slide">` each, in order — `#s1` title, `#s2` contact, `#s3` plan, `#s4` pivot (dead-trunk grid), `#s5` live-trunk grid, `#s6` trunk figure, `#s7` card-model divider, `#s8` card-model opening, `#s9` outtro. **All nine are real** and carry no `DEMO` badge; the five demo sampler slides were deleted (D-133), so no placeholder copy is left to replace. `#s2` and `#s9` carry the same four contact lines and the same LinkedIn QR — **drawn as inline vector geometry**, so it is crisp at any projector size and there is no image file to lose. A slide is a section holding one to three `article.card` elements in named areas — `.a-hero`, `.a-wide`/`.a-side`, `.a-side-top`/`.a-side-bottom`, `.a-fignote` — **or, on `#s4`, `#s5` and `#s8`, a `div.pp-wrap` plate or an `img.fig` with no card behind it, and on `#s6` an `img.fig` beside its caption card** (those slides spend the stage's full 568px of height, which is what makes their type legible). At a glance:

    <section class="slide" id="s3" data-shape="plan">
      <article class="card a-hero"> <h1 class="t-h1">The plan</h1> <ol class="t-plan"> <li><span class="t-num">1</span><span class="t-step">Naive, flat model</span></li> … </ol> <p class="t-note">…</p> </article>
      <template class="talk"><ul class="note-list"><li>what to say</li></ul></template>
    </section>

**Edit text inside an existing block, not its size.** Each shape's block heights are `#sN`-scoped CSS rules — that is what keeps every slide inside the 1280×720 surface, so the copy has to fit the block it is written into. The budgets are in characters, approximate and deliberately conservative (`docs/presentation/design.md` §5, and `content.md` §2–§5 for the content slides): a plan step (`#s3 .t-step`, 28px) **≤ ≈58**; a `.t-url` line is 24 mono characters; a caption, note or heading is one line.
**Longer text is clipped, not reflowed.** The card clips, and the nested boxes (the plan's `.t-num`/`.t-step`, the `.t-url` line spans) clip themselves and also run `nowrap`, because a `height` here is only a minimum: the plan's row stays 104px, and an over-long line is cut off at its own box instead of painting across its neighbour. Clipping loses words silently, so the copy must fit: shorten it, never edit the px.
**A tenth slide is one ordered change** — copying a section alone gives an unstyled slide, because the heights and the clips are both `#sN`-scoped; the next id would be `#s10`:
1. **The section, last in the deck** — or, if it belongs mid-talk, accept that **inserting one anywhere but the end renumbers every `#sN` after it**: the section id, its `#sN`-scoped rules and its HUD dot all move together, which is what inserting six slides did to the outtro (`#s8` → `#s14`) and what deleting the five demo slides undid (`#s14` → `#s9`).
2. **Its own `#sN` height rules**, one per block, each a literal px `height` and `margin`, summing to **≤ the container's inner box** (512 for a card, 568 on the felt) — an unstyled block has no height and paints over its neighbour.
3. **Its own `#sN`-scoped clip and `nowrap` rules** — the step that has been missed: `.card > *` clips on every slide, but the boxes one level deeper clip **only** because of `#sN`-selectors, and a cell that clips without `nowrap` loses text to the right with no height change (the defect G4 exists for).
4. **One more `.dot`** — the dots are static markup and do **not** follow the count; the counter, `#live` and the `#/N` range are computed and need no edit.
5. **A new `data-shape` word**, declared in `design.md` §5 and added to A3's list in the same change; never reuse one of the nine.
6. **The hand-edited counts:** `design.md` A3 (nine), A4 (zero badges — the rule is vacuous since D-133, and still applies to any placeholder that arrives), A9 (`#/1`…`#/9`) and A11 (`#/99` → 9), this file's slide list and count, and `presenter.md`'s `#/N` references. Run the gate and read the total it printed: if that is not the count you wrote, the edit is incomplete.
7. **Optional per slide, and legal to omit: the two templates** — `<template class="talk">` for notes, `<template class="more">` for sources, both direct children of the section and never inside a card. Omit the notes and `N` says `No notes for this slide`; omit the sources and `.more-btn` stays `aria-disabled`. Both are legal and both are **visible**, so choose deliberately.

## Numbers
A measured number may be pasted **only** from `strata/decisions.md` or `strata/records/` — **or read out of a figure generated from them and quoted as the figure draws it** — with the record's date beside it; invented or rounded-up figures are banned everywhere. Every such figure is entered in `presentation/FACTCHECK.md` (claim as it appears, record path, date, what the source does not support, what is unresolved), a figure with no entry never reaches a slide, and the four rows the new slides owe are specified in `docs/presentation/content.md` §7. Form: `docs/presentation/checks.md` §7.

## Figures (D-132)
A slide may show a figure from `figures/` as **`<img src="../figures/<name>.svg">`** — a relative path, no scheme, resolving inside this repo — or, for the reference grids, as the fragment's own markup with its `.pp-wrap` styles copied into the deck's single `<style>`. **Never inline a generated SVG** (`network-compare.svg` is 61 kB carrying `xmlns`, five `http` strings and 172 `url(#…)` refs, which would end the greps that keep the deck offline), **never copy a figure into `presentation/`** (two copies drift), and **never re-type a number off one** — quote it as drawn. **A figure file must travel with the repo:** copy `presentation/index.html` alone to a talk machine and its two figures are broken pictures. Each figure's provenance and `alt` live in `figures/manifest.json`; regenerate with `python figures/make_figures.py` (the eight data figures) and `python figures/make_network.py` (the two trunk diagrams, read from the checkpoints), and `python figures/make_html_grid.py` for the reference grids — edit the values in the script, never the SVG. Palette: `figures/README.md`.

## Checking it before a talk
The gate is a **dev tool**, not part of the deck, so there is still no build step. With Firefox installed:

    node presentation/check.mjs --out /tmp/check-shots

It opens the deck headless, screenshots every slide at 1280×720 and 1600×1000 into that folder, and flags anything outside the slide, any clipped or overlapping text, text under 14px, a broken `#/N` round-trip, a presenter panel that overflows or leaks, and (G12) a figure whose `src` is not repo-relative, whose file is missing, or which did not load into its declared box. It prints the slide total it derived from the deck, then one line per issue, or `no issues`, and exits 0 or 1. It does **not** decode the QR (`docs/presentation/contact.md` C8) and cannot see whether a figure drew anything — that is the screenshot. **A clean check is not a design review.** Contract and checks G1–G12: `docs/presentation/checks.md`.

## Not in this pass
The deck ships as **nine real slides** and there is no placeholder copy left to replace: the demo sampler is gone (D-133), so the slides are the title (D-131), the contact pair (D-129), the six content slides (D-132, `docs/presentation/content.md`) and the outtro. The rest of the real talk — the representation ladder, the aggregate-metric failure, the exploration floor, what the policy still cannot do — is a later pass (D-118, D-121), as is the fact-check file's own first writing.
