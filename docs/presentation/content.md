# presentation — the deck's first real content slides (L3 design)

- **Layer:** L3 · **Artifact:** `presentation/index.html` (L4) · **Rev:** 2 · **Date:** 2026-11-17 · **Ceiling:** 140 lines
- **Realises D-132** — the six slides it inserts after the contact slide (`#s3`–`#s8`), the asset rule that lets a slide reference `figures/` by relative path, and the `A2`/`G12` replacement that rule forces. It owns those six slides' px, copy, surfaces and checks; `design.md` keeps the stage, the tokens, the areas, the clip rule and §5.3's ledger of the five shapes **D-133** deleted. **D-133 changes no id in this file:** `#s3`–`#s8` are the six slides it owns, and the demo sampler rows its §1 table used to carry, and its C9 count, are gone.
- **Read with:** `design.md` (§2 stage and clip rule, §3 tokens and ramp, §4 areas, A1–A16), `checks.md` (G1–G12, §7 the fact-check form), `presenter.md` (§1 templates, §1.1 the new slides' notes, §3 sources, P1–P12), `content-rules.md` (R1–R9), `contact.md` (`#s2` and the outtro, now `#s9`), `figures/README.md` and `figures/manifest.json` (per-figure provenance and `alt`).

## 1. The order, the count, and what is real

**Nine slides** `#s1`–`#s9`, `id`, `data-shape` and kind in this file order (A3; nine distinct words):

| # | `data-shape` | kind | what it is |
|---|---|---|---|
| `#s1` | `title` | real | the talk's title (D-131) |
| `#s2` | `contact` | real | the speaker's contact block and QR (D-129, `contact.md`) |
| `#s3` | `plan` | **real, new** | the talk's three-step promise — §2 |
| `#s4` | `pivot` | **real, new** | the pivot title and the dead-trunk grid — §3 |
| `#s5` | `livegrid` | **real, new** | the live-trunk grid — §3 |
| `#s6` | `trunk` | **real, new** | `network-compare`: two reward scales, one architecture — §4 |
| `#s7` | `cardmodel` | **real, new** | the card model's section divider — §5 |
| `#s8` | `signal` | **real, new** | the card model's first content slide — §5 |
| `#s9` | `outtro` | real | the contact block again, last (D-129) |

**All nine slides are real, and nothing is demo.** D-133 deleted the five sampler slides (`#s9`–`#s13` while they existed) with their `DEMO` badges and their `design.md` §5 budgets, so no placeholder copy is left to replace, the HUD's `demo slides: placeholder content` note is gone, and **nothing now sits between `#s8` and the outtro** — which is why the outtro is `#s9` and the deck is nine slides rather than fourteen. **At R5's 1.2 minutes a slide the deck is ≈10.8 minutes** — the count is a slot decision, not a sampler artefact. **No other figure enters the deck:** the six content slides draw from **three files in `figures/`** — the grid fragment (once per grid slide), `network-compare.svg` and `signal-by-street.svg` — and none carries a number that is not in one of them or in §4's caption.

## 2. The plan slide, `#s3`

Deck-native, no figure, one card. `card.a-hero` (interior **1136×512**) ▸ `h1.t-h1` ▸ `i.card__rule` ▸ `ol.t-plan` (3 × `li`) ▸ `p.t-note`. `t-plan`, `t-num` and `t-step` are three new block **names** like `contact.md`'s `.t-email`; every size they take is a §3 ramp token, so the ramp itself is untouched. Nothing on the card is a measurement, so §7 owes it no row.

| block | token | px | margin | running |
|---|---|---|---|---|
| `h1` “The plan” | `--fs-h1` 56/64 | 64 | `0 0 16px` | 80 |
| `i.card__rule` | 2px | 2 | `0 0 28px` | 110 |
| `ol.t-plan` 3 × `li` @ 104 + 2 × 16 gap | — | 344 | `0` | 454 |
| `p.t-note` | `--fs-small` 20/28 | 28 | `24px 0 0` | **506 / 512** |

**Each `li` is one numbered row, 104px tall:** `span.t-num` (`--font-mono`, `--fs-h1` 56/64, `--ink-muted` 6.5:1, `font-variant-numeric: tabular-nums`) in a **64px** column, a 20px gap, then `span.t-step` (`--font-display`, `--fs-h3` 28/36, `--ink`) filling the remaining **1052px**. No box, rule, tint or glyph is added to the rows — the numeral is the device, and the deck's §4 decoration list is unchanged. **Copy, exactly these three strings and the note, nothing else** — the user's words, unpunctuated and unedited:
1. `Naive, flat model`
2. `Tokenize the cards`
3. `Use attention to pick out opponent patterns`

Note line: **`Three steps, in the order the talk takes them.`** It is framing, not a claim, and it is the slide's one line (R2). **Budget:** the longest step is 43 characters at `--fs-h3`, ≈774px on §5's conservative ≈18px-per-character rule, inside 1052px; the note is 43 characters at 20px ≈555px inside 1136px. **Clip rules L4 owes this slide:** `#s3 .t-plan li { height: 104px }`, `#s3 .t-plan .t-num { height: 64px }`, `#s3 .t-plan .t-step { height: 36px }`, each of the three also under `html.js #s3 .a-hero .t-plan … { overflow: hidden }` — the boxes are grandchildren of the card, so §2's second tier does not reach them. **`nowrap` on both spans**: a `height` is a minimum in this engine, so one wrapped step would grow its row and push the note past 512.

## 3. The pivot and the live-grid slides, `#s4` and `#s5`

**The fragment is carried twice, and its CSS once.** `figures/reference-grids.html` is a self-contained fragment: one `<style>`, then `div.pp-wrap` holding a shared preamble, two `section.pp-grid` blocks and a legend. L4 copies **its `<style>` block once, verbatim and unmodified, into the deck's single `<style>` element** (so the document keeps exactly one `<style>`, A1, and no `<style>` element appears inside `<body>`), and each slide carries only `div.pp-wrap ▸ section.pp-grid ▸ table` for **its own grid** — the dead-trunk table on `#s4`, the live-trunk one on `#s5`, each with its `<thead>`, its eight `<tbody>` rows, its `scope` attributes, its `title="raise|call|fold"` cell attributes and its `caption.pp-sr`.
**What is not carried, and why:** the fragment's own five narration blocks — the wrap's `h3` “The reference hands” and its `.pp-note`, the dead section's `h3` and `.pp-note`, and `.pp-legend` — are not on the slides. At the scales below the two `.pp-note` blocks and the legend render at **11.5px**, under this deck's own 14px floor, and all five together cost **58px** of plate height — which is most of the scale these slides have to give. **Every datum is carried unaltered** — the eight hands, the eight equities, every per-street action letter and every column header — so nothing is invented, cropped or re-typed (D-132); what is not carried is the fragment's grey captions, and they are named here rather than silently lost. The headers say which column is which, `#s5`'s line prints the key, and `#s4`'s notes speak it; the legend and the notes' own words live in `presenter.md` §1.1.
**Scoping, and why it cannot leak:** every selector in the fragment begins with `.pp` (`.pp-wrap`, `.pp-note`, `.pp-hand`, …, or a descendant of `.pp-wrap`), it declares its custom properties on `.pp-wrap` only, and **no name in the deck's own vocabulary begins with `pp`** (`slide`, `card`, `a-*`, `t-*`, `note-list`, `src-list`, `qr`, `hud`, `dots`, `dot`, `panel*`). So no fragment rule can match a deck element and no deck rule can match a fragment element — the prefix *is* the scope — and C13 asserts it mechanically. Nothing is renamed inside the fragment, so a future regeneration drops in unchanged.

**Surface: the plate sits on the felt, as the tile — not inside an ivory card, and not on the card face.** The `.pp-wrap` **is** the surface: its own `#14120f` background, its own 14px radius, its own 22px padding, with the deck *adding* `#s4 .pp-wrap, #s5 .pp-wrap { box-shadow: var(--card-shadow) }` so it carries the brass rim and the drop shadow and reads as a card. Rejected: an ivory `article.card` with the plate inside it — the card's 28px padding plus the plate's 22px eats 100px of the 1192 width and 100px of the 568 height, which alone halves the scale below the cells' floor; and a dark plate floating in a cream card at this size reads as a hole in the card, not as a figure.

**`#s4 pivot`** — one text block, then the plate. `h1.t-h1` **`No plan survives contact with the enemy…`** at `--fs-h2` 40/48, margin `0 0 12px`; the ellipsis is the **single character U+2026**, not three periods, which is D-132's own spelling of the title and C11's comparison string. The title is the slide's one line (R2): a second 20px line would take the plate from 0.96 to **0.896**, i.e. the action letters from 12.48px to 11.64px — under the floor — and the columns already label themselves in the header row (`600-scale reward, 3k hands` · `600-scale reward, raiser run`).
```
#s4   h1 60px   ▸ plate: #s4 .pp-wrap { top: 60px; left: 68px; width: 1100px; transform: scale(0.96); transform-origin: 0 0 }
```
**`#s5 livegrid`** — one line, then the plate. `p.t-note` at `--fs-small` 20/28, margin `0 0 8px`, copy **`Live trunk: some of these models change their action with the hand, and some do not.`** (83 characters ≈1071px, inside 1192) — true of the fragment as drawn (`foldloop-high` is `rrrr` for all eight, `foldloop-control` differs only at the river, the two ε0.60 probes fold the kings and the junk), checked verbatim by C15 and for truth by §7's second row.

| slide | plate at natural size | scale | rendered | text block | sum |
|---|---|---|---|---|---|
| `#s4` | 1100 × 527 | **0.96** | 1056 × 506 | 60 | **566 / 568** |
| `#s5` | 1100 × 564 | **0.94** | 1034 × 530 | 36 | **566 / 568** |

**Where the natural heights come from** — measured, not assumed: the fragment's sections are **541px** (dead) and **578px** (live) tall at **1056px** of content width; each section is an `h3` (≈30px) + a `.pp-note` (≈28px) + its table, so the tables are **483** and **520**; the wrap's 22px padding on both sides makes the plates **527** (dead) and **564** (live). Both plates are 1100 wide because that is the width the fragment was measured at — the column geometry that fixes those heights is the measured one, and a wider plate would move every number here.

**Cell type at those scales** (the fragment's own sizes, `× scale`; 1080p is ×1.5):

| item | fragment | `#s4` @0.96 | `#s5` @0.94 | at 1080p |
|---|---|---|---|---|
| hand name, equity | 14px | **13.44** | **13.16** | 20.2 / 19.7 |
| action letter `r`/`c`/`f` | 13px | **12.48** | **12.22** | 18.7 / 18.3 |
| hole-card sub-label | 12px | 11.52 | 11.28 | 17.3 / 16.9 |
| column header | 11px | 10.56 | 10.34 | 15.8 / 15.5 |

**Every cell's text is ≥12px at design scale and ≥18px at 1080p**; the two label lines inside the fragment fall under that and are named here rather than rounded up — the hole-card sub-label sits directly beneath the hand name it belongs to, and the column headers are labels, not cells. The next rung down is the alternative D-132 measured and rejected: both grids on one slide is **≈0.40 scale and ≈5.6px type**. There is no `nowrap` and no font-size override on the plate: the fragment's own CSS is what renders, and C14 measures the ratio rather than trusting this table.
**What the eight rows are, from the fragment's own column** — true six-way equity from its 20,000-draw Monte Carlo, as `make_html_grid.py` formats it: `quad aces` (A♠ A♦) **100 %**, `nut flush` (A♠ Q♠) **100 %**, `ace-high straight` (A♠ K♦) **98 %**, `trip aces` (A♠ A♦) **92 %**, `pair of kings (dry)` (K♥ K♦) **45 %**, `2-3 offsuit junk` (2♣ 3♦) **0.0 %**, `2-7 offsuit junk` (2♦ 7♣) **0.0 %**, and the eighth, `2-3 offsuit, all-high board` (2♣ 3♦), at the **0.02 %** its source carries (`.probe/grids.json`'s `ref` block). The slides print none of these numbers themselves — the grid draws them, and §7's first row is the audit trail.
**What the two slides show, in one breath:** the same eight hands and the same equity column twice, with each model's per-street action beside it — on `#s4` two dead-trunk policies that play one action for every hand, on `#s5` five live-trunk models whose cells do and do not change with the hand. That contrast is the beat, and both slides draw it rather than assert it; the header row names each column, which is why neither slide needs a column key in deck type.

## 4. The trunk figure slide, `#s6`

`<img>` reference, never inlined: **`<img class="fig" src="../figures/network-compare.svg" width="653" height="568" alt="…">`** — 61 kB of matplotlib output carrying `xmlns`, five `http` strings and 172 `url(#…)` clip refs, so inlining it would end A2's greps (D-132). The path is relative, has no scheme, and resolves inside the repo (§6 C13, `checks.md` G12).

**Geometry.** The SVG is **494.5 × 429.9 pt**, aspect **1.1502 : 1**; its box on the stage is **653 × 568 design px at (0, 0)** — the slide's full height and 653/1.1502 = 568, so it is drawn at **0.990 of its intrinsic size**, as large as the stage allows. The caption is a card, `.a-fignote` at **(677, 0, 515, 568)**, interior **459×512**; 653 + 24 gap + 515 = **1192**, so the row sums exactly.
**Surface: the felt, with no plate and no card behind it.** The figure is `fill: none` with cream `#f2e8d5` and gold `#d9a441` type — on the ivory card face cream is **≈1.09:1** and unreadable, on the felt band it occupies it is **≥7.4:1**; so the felt is this figure's surface and the card carries the words. **Internal type at that box:** the figure's 8.5px labels (its unit names and the two count lines) render at **11.23px** design (16.8 at 1080p) and its 11px panel titles at **14.53px** (21.8) — that is the largest they can be at any box that fits the stage, which is exactly why the counts are restated on the card at `--fs-h2`.

| `.a-fignote` block | token | px | margin | running |
|---|---|---|---|---|
| `h2.t-h2` “The trunk” | `--fs-h2` 40/48 | 48 | `0 0 12px` | 60 |
| `i.card__rule` | 2px | 2 | `0 0 20px` | 82 |
| `p.t-note` “600-scale reward” | `--fs-small` 20/28 | 28 | `0 0 4px` | 114 |
| `p.t-count` “0 / 50 · 0 / 50” | `--fs-h2` 40/48 | 48 | `0 0 20px` | 182 |
| `p.t-note` “normalised reward · foldloop-high” | `--fs-small` 20/28 | 28 | `0 0 4px` | 214 |
| `p.t-count` “23 / 50 · 24 / 50” | `--fs-h2` 40/48 | 48 | `0 0 24px` | 286 |
| `p.t-note` “Two numbers per panel: hidden layer 1 and hidden layer 2, of 50 units each.” | `--fs-small` 20/28 ×2 | 56 | `0` | **342 / 512** |

**The four counts are the generator's own**, printed by `figures/make_network.py` into both panels: hidden 1 **0 / 50**, hidden 2 **0 / 50** under the 600-scale reward, and **23 / 50**, **24 / 50** under the normalised reward **on the `foldloop-high` checkpoint**. The caption states that checkpoint on the slide, because `figures/demo-data.json`'s `trunk_health` block says **22 / 50** for the normalised reward and measures a **different run**; the two numbers are never the same measurement, and the notes say which is which. **`alt`** is the manifest's own string, verbatim: `Two network diagrams side by side: the left has empty hidden layers, the right has lit units and edges.` The figure is `aria`-named by that `alt`; it carries no `aria-hidden`.

## 5. The card model's opening, `#s7` and `#s8`

**`#s7 cardmodel` — the section divider.** `card.a-hero` (interior 1136×512) ▸ `div.suit-circle` (96px, 2px `--suit-red` ring, ♥ at 6.7:1, `aria-hidden`) ▸ `span.--fs-badge` ▸ `h1.t-h1` ▸ `p.t-h3` — the shape the deleted demo divider used to carry, with real copy (`design.md` §5.3). Budget: `96+24 · 24+12 · 64+12 · 36` = **268 / 512**. Copy: eyebrow **`THE CARD MODEL`** (`--fs-badge` 18/24, uppercase), heading **`What the cards explain`** (22 characters at 56px ≈788px), sub **`From the hole cards to the river, by how many are known`** (52 characters at 28px ≈936px). No figure, no number, no act number — the deck does not invent a slot count.
**`#s8 signal` — the first content slide.** `h1.t-h1` **`Where the signal comes from`** at `--fs-h2` 40/48, margin `0 0 12px` (60); then **`<img class="fig" src="../figures/signal-by-street.svg" width="756" height="468" alt="…">`** at **(218, 60)** — 756/1.6150 = 468, the SVG being **407.5 × 252.3 pt** (aspect 1.6150); then `p.t-note` at `--fs-small` 20/28, margin `8px 0 0` (36). Sum **60 + 468 + 36 = 564 / 568**. The figure sits on the felt for §4's reason (cream and `#d9c7a3` type, one `fill:none` background); its 11px internal labels render at **20.41px** (30.6 at 1080p) and its own 13.2px title at 24.49px, so this figure is legible at its box and needs no plate. **`alt`** is the manifest's string verbatim: `Bars: 2.4% preflop, 14.4% flop, 20.9% turn, 52.8% river.`
**The one claim, and its provenance:** the line is **`By how many are known: 2.4 % preflop, 52.8 % at the river.`** Both endpoints are rows, not composites of convenience: **2.4 %** is D-86's preflop figure (2026-11-08) and **52.8 %** is D-93's converged river figure (2026-11-08); the drawing's two middle bars are D-86's flop and turn. The card model's section therefore opens on the figure the record already carries, and **no number appears in the slide's own text that is not one of those two**. The era caveat is real and goes where caveats belong: the record's `strata/records/card-model-design.md` table (2.4 / 17.4 / 30.6 / 36.3 %, 28.1 % pooled) is the **epoch-60 attention snapshot**, superseded by D-90 and D-93, whose attention model reaches **40.16 % pooled at epoch 360 and 52.81 % at the river**; the four bars are **not one checkpoint's four streets**, and the notes and §7's row say so. The representation ladder (13.1 → 15.3 → 20.4 → 32.4 → 40.0 %, D-84…D-96) is the second candidate for this slide and is **not** used: it answers "which encoding", which is the second act's question, not the opening one.

## 6. Acceptance checks C9–C16, and who runs them

**C9 (gate).** Exactly **nine** `section.slide`; `id` `s1`…`s9` in file order; `data-shape` in that order **`title contact plan pivot livegrid trunk cardmodel signal outtro`**, nine distinct values; nine `.dot` with exactly one `.is-on`; `#/1`…`#/9` put `n` in `#counter` and `Slide n of 9 — <shape>` in `#live` — all of it against the **derived** total (`checks.md` G3), never a constant.
**C10 (gate).** `#s3`'s `ol.t-plan` holds exactly three `li`, whose `.t-step` `textContent` values, in order and with no added words, equal `Naive, flat model`, `Tokenize the cards`, `Use attention to pick out opponent patterns` (compared after trimming whitespace, case-sensitively).
**C11 (gate).** `#s4`'s `h1` `textContent`, trimmed, equals `No plan survives contact with the enemy…` **with U+2026 as the last character** — a three-period form fails — and the `h1` contains no other text node.
**C12 (gate + reviewer).** Each `<img>` (exactly **two** in the file): `complete === true` and `naturalWidth > 0`; its rendered rect equals the §4/§5 declared box within **±1 design px**; its `alt` equals the `alt` string in `figures/manifest.json` for that file. **Reviewer:** the screenshot crop inside that box is not a single colour — a figure that loaded and drew nothing is the failure this half exists for.
**C13 (gate).** No `src` carries a scheme (`http:`, `https:`, `data:`), a leading `//`, or a query string; every `src` begins `../figures/` and resolves to an existing file inside the repo; and every rule inside the copied fragment CSS begins with `.pp` (its one `@media` block wraps nothing else), so no fragment rule can reach a deck element. (This is A2's replacement; `checks.md` G12 is its implementation.)
**C14 (gate).** On `#s4` and `#s5`, `getBoundingClientRect().width / offsetWidth` on `slide.querySelector('.pp-wrap')` equals the declared scale (**0.96** dead, **0.94** live) within **±0.005**, and `13 ×` that ratio is **≥ 12** and `14 ×` it is **≥ 12** — the action letters and the cell text, measured on the render rather than read off §3's table.
**C15 (gate).** `#s6`'s own text (outside the `<img>`) contains `0 / 50` exactly twice, `23 / 50` once, `24 / 50` once, `600-scale` once, `normalised` once and `foldloop-high` once; and `#s5`'s own text is the §3 line verbatim.
**C16 (gate + reviewer).** `#s8`'s `<img>` is `../figures/signal-by-street.svg`, its `alt` is the manifest's, and the slide's own text (outside the `<img>`) contains **exactly two numerals, `2.4` and `52.8`, and no others**; **reviewer:** the drawn bars read 2.4 / 14.4 / 20.9 / 52.8 and equal `figures/demo-data.json`'s `signal_by_street` rows. A number in the deck's own type that the figure beside it does not draw is a defect against C16, and on `#s6` against C15.
**Split.** C9, C10, C11, C13, C14, C15 and C16's static half are gate checks (DOM and file assertions, no sixth BiDi command); C12's ink test, C16's bar reading and the whole "is the figure the right size to read from the back" question are the reviewer's, on the screenshots the gate already writes (§5, `checks.md`: **a clean check is not a design review**).

## 7. The fact-check rows L4 must write into `presentation/FACTCHECK.md`

Four rows, and only these four — the plan slide, the divider and the outtro carry no figure and owe none.

| slide | claim as it appears | source | source date | what the source does NOT support |
|---|---|---|---|---|
| `#s4`, `#s5` | the grid as drawn: the eight reference hands, their true six-way equities (**100, 100, 98, 92, 45, 0.0, 0.0** and the eighth at **0.02 %**), and every model's per-street action, `r`/`c`/`f` | `figures/reference-grids.html` from the replay behind it (`.probe/make_grids.py`, `.probe/grids.json`), row **D-129** | **2026-11-08**, regenerated **2026-11-17** | that any cell is illustrative, and that the dead-trunk columns' one-action rows are a training result rather than the dead trunk's consequence |
| `#s5` | `Live trunk: some of these models change their action with the hand, and some do not.` | same fragment and replay | **2026-11-08** / read **2026-11-17** | that all of them do: `foldloop-high` is `rrrr` on all eight, and `foldloop-control` differs only at the river |
| `#s6` | `0 / 50 · 0 / 50` and `23 / 50 · 24 / 50`, on the `foldloop-high` checkpoint | `figures/network-compare.svg` as printed by `figures/make_network.py`, rows **D-60, D-67, D-108**, restated by **D-132** | **2026-11-08** / **2026-11-17** | that the normalised count is 22 / 50 (a different run, `figures/demo-data.json` `trunk_health`), and that both panels are one checkpoint — the dead panel is `.probe/dead/dead-ckpt` |
| `#s8` | `By how many are known: 2.4 % preflop, 52.8 % at the river.` | `strata/decisions.md` **D-86** (preflop 2.4 %) and **D-93** (river 52.81 %) | **2026-11-08** | that both are one model's run, and that the figure's four bars are one checkpoint's four streets |

Every row's `disposition` is **VERIFIED** on the wording above; if L4 finds a string it cannot verify it does not reach the slide, and the claim is weakened until the source carries it (`checks.md` §7).
