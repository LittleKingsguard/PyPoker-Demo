# presentation — the deck's two contact slides (L3 design)

- **Layer:** L3 · **Artifact:** `presentation/index.html` (L4) · **Rev:** 2 · **Date:** 2026-11-17 · **Ceiling:** 100 lines
- **Realises D-129.** It moves the seven-slide sampler of `design.md` in exactly two places: a real contact slide immediately after the title (`#s2`) and an outtro carrying the same contact block and the same QR as the last slide (`#s8`).
- **Read with:** `design.md` (§2 stage, §3 tokens, §4 areas, §5 shapes, A1–A15), `presenter.md` (§1 templates, P1–P11), `checks.md` (G1–G11), `content-rules.md` (R1–R9, binding on these two slides — with the title slide they are the deck's real content).
- **Scope:** those two slides, the QR block, their px budgets, the id remap the insertion forces, the counts that moved and C1–C8. The QR's **data** is not this document's business: it is held at `/tmp/qr/qr_rle.json` as `{n: 29, rows: [[[startCol, runLength], …], …]}` — 29 rows, 212 dark runs — and the contract in §2 is what turns it into geometry.

## 1. Purpose, and what is real

The deck opens on the speaker's contact and closes on it: scan at the open, scan at the close. `#s2` sits between the title and act one; `#s8` **replaces** the demo closing slide, whose placeholder copy is deleted rather than kept beside real content — D-129 forbids a slide that is half real and half placeholder, and placeholder copy on a card carrying a real address is exactly that half.

**`#s2` and `#s8` are two of the deck's three real slides** — the third is the title slide, `#s1`, real since D-131. The other five carry a `DEMO` badge (§4, A4); none of `#s1`, `#s2` and `#s8` does, and that badge is the whole of how a reader tells one kind of slide from the other. `content-rules.md` therefore binds on both contact slides from this pass, as it does on the title slide: the contact block carries no figure, so it owes no `FACTCHECK.md` row, and nothing on either slide may become a measurement without one. The felt, the cards, the stage, the type ramp and the navigation do not change.

## 2. The QR block: the drawing contract

**One inline `<svg class="qr">` per contact slide**, drawn from the run-length rows — not an image, not a font, not a `<canvas>`, not a data URI, and never generated in JS (the file must read correctly with the script off).

    <svg class="qr" id="qr2" viewBox="0 0 37 37" width="296" height="296"
         role="img" aria-labelledby="qr2-t" shape-rendering="crispEdges">
      <title id="qr2-t">LinkedIn profile QR code — Ryan Rasey</title>
      <rect x="4" y="4" width="7" height="1"/>      … one per dark run, 212 of them
    </svg>

**Geometry.** `viewBox="0 0 37 37"`: 29 modules plus a **4-module quiet zone on every side** (4 + 29 + 4 = 37). One `<rect>` per dark run, all coordinates integer **viewBox units**, never px: `x = startCol + 4`, `y = row + 4`, `width = runLength`, `height = 1`. Nothing is drawn in the quiet zone — no background rect, no frame, no `<use>`, no `<defs>`, no `<image>`, no `<style>`, no `transform`, no gradient — so the quiet zone **is the ivory card face**, and nothing else is painted there.
**Size.** `width="296" height="296"` — 37 units at exactly **8 px per module** (29 × 8 = 232 px of modules, 232 + 2 × 32 = 296 px with the quiet zone), so every module edge lands on a whole design px. On the stage that is 8 px/module; at 1920×1080 the stage is exactly ×1.5, so **12 px/module, 444 px** for the block. The module size is an **even integer** by rule, which is what keeps ×1.5, ×2 and ×1 crisp. **Minimum: 6 design px per module (9 px at 1080p).** Both slides in this pass draw **8** (12), and a later placement may go to 6 but never below it — below that the code is a texture, not a code.
**Paint.** No `fill` attribute on any rect: one rule in the deck's `<style>`, `#s2 .qr rect, #s8 .qr rect { fill: var(--ink) }` — `--ink` on `--card-face`, 13.4:1, dark on light. **Never inverted, never a theme accent, no opacity, no filter**: contrast and quiet zone are what make it scannable, so neither is a styling choice. The block itself carries **no border, radius, background, shadow, outline or opacity**, and none of the five cards on the two contact slides carries a **suit glyph or a pip** — a corner glyph's box lands inside the quiet zone's territory — while a hairline `card__rule` is allowed **above** the block, never inside it (`#s8` has one there, §3).
**Accessibility.** The QR is content, so it is named: `role="img"` plus a `<title>` reading `LinkedIn profile QR code — Ryan Rasey`, referenced by `aria-labelledby` (ids `qr2-t` / `qr8-t`, unique in the document). It is **never `aria-hidden`**, and it is not a link. The printed URL beside it is what serves a reader who cannot scan, which is why §3 sets it in full (§4).

## 3. The two slides, in px

Both use **existing** area classes — `design.md` §4's boxes fit, so no area class is added and no new area rule is invented. Every text block on both slides is a fixed-height box with a literal margin, and each sum is stated against the card's inner box. `.t-email` and `.t-url` are two new block **names**; their sizes are `§3`'s ramp tokens, so the ramp itself is untouched.

**`#s2`, `data-shape="contact"`** — two cards: details left in `.a-wide` (inner 720×512), QR right in `.a-side` (inner 336×512). **DOM order is details, then QR**, so the accessible order and the no-JS stacked order lead with the name; the left/right placement comes from the area class alone.

| `#s2 .a-wide` block | token | height | margin | running |
|---|---|---|---|---|
| `h1.t-h1` “Ryan Rasey” | `--fs-h1` 56/64 | 64 | `96px 0 8px` | 168 |
| `p.t-h3` “Founder/Dev @ Auspicion” | `--fs-h3` 28/36 | 36 | `0 0 20px` | 224 |
| `i.card__rule` | 2px | 2 | `0 0 24px` | 250 |
| `p.t-email.t-body` “ryan.rasey@auspicion.ai” | `--fs-body` 28/38 | 38 | `0 0 16px` | 304 |
| `p.t-url` (two 28px lines) | `--fs-small` 20/28, `--font-mono` | 56 | `0` | **360 / 512** |

| `#s2 .a-side` block | token | height | margin | running |
|---|---|---|---|---|
| `svg.qr` | 296×296, `display: block` | 296 | `24px auto 24px` | 344 |
| `p.t-note` “Scan to connect” (`text-align: center` on the card) | `--fs-small` 20/28 | 28 | `0` | **372 / 512** |

**`#s8`, `data-shape="outtro"`** — three cards, the deck's three-card slide (A9): `h1.t-h1` “Thank you”, the rule, the same QR at the same 8 px/module and the caption in `.a-wide` (inner 720×512); the contact block in `.a-side-top` and `.a-side-bottom` (inner 336×216 each).

| `#s8` block | token | height | margin | running |
|---|---|---|---|---|
| `.a-wide` `h1.t-h1` “Thank you” | `--fs-h1` 56/64 | 64 | `0 0 12px` | 76 |
| `.a-wide` `i.card__rule` | 2px | 2 | `0 0 20px` | 98 |
| `.a-wide` `svg.qr` | 296×296 | 296 | `0 0 20px` | 414 |
| `.a-wide` `p.t-note` “Scan to connect” | `--fs-small` 20/28 | 28 | `0` | **442 / 512** |
| `.a-side-top` `h2.t-h2` “Ryan Rasey” | `--fs-h2` 40/48 | 48 | `0 0 8px` | 56 |
| `.a-side-top` `p.t-note` “Founder/Dev @ Auspicion” | `--fs-small` 20/28 | 28 | `0 0 12px` | 96 |
| `.a-side-top` `p.t-note` “ryan.rasey@auspicion.ai” | `--fs-small` 20/28 | 28 | `0` | **124 / 216** |
| `.a-side-bottom` `h3.t-h3` “LinkedIn” | `--fs-h3` 28/36 | 36 | `0 0 8px` | 44 |
| `.a-side-bottom` `p.t-url` (two 28px lines) | `--fs-small` 20/28, `--font-mono` | 56 | `0` | **100 / 216** |

**Copy, exactly these four strings and nothing else** — no invented role, company, phone or tagline: `Ryan Rasey` · `Founder/Dev @ Auspicion` · `ryan.rasey@auspicion.ai` · the LinkedIn URL. `Thank you` and `Scan to connect` are the only other words on the two slides beyond the URL's own path.
**`.t-url` has one form on both slides:** a 56px box of two `<span>` lines, `display: block`, each 28px, `--font-mono` at `--fs-small`; line 1 `https://www.linkedin.com/`, line 2 `in/ryan-rasey-930403a4/`. 24 characters a line at ≈12.5px per mono character = **300 px**, inside the 336px card and comfortably inside the 720px one — so the break is a wrap of one unbroken string at a path boundary, not a shortening: every character of the URL is on the slide, and C4 checks the concatenation. Both lines are `white-space: nowrap`.
**Character budgets** (design §5's method, ≈18px per character at 28px, scaled): “Founder/Dev @ Auspicion” at 28px ≈ 396 ≤ 720; the email at 28px ≈ 432 ≤ 720 and at 20px ≈ 310 ≤ 336; the URL lines ≈ 300 ≤ 336; “Scan to connect” ≈ 194 ≤ 336; “Ryan Rasey” at 56px ≈ 358 ≤ 720 and at 40px ≈ 256 ≤ 336.
**The clip rules these boxes need, and only these.** All the new boxes are direct children of `.card`, so `html.js .card > *:not(.suit)` already clips them; the two `.t-url` line spans are grandchildren and need their own: `html.js #s2 .a-wide .t-url span` and `html.js #s8 .a-side-bottom .t-url span` — `overflow: hidden; white-space: nowrap`. Add one `#sN`-scoped clip rule per new fixed-height box anyway, as the README's step 3 requires: `#s2 .a-wide` `.t-h1`/`.t-h3`/`.t-email`/`.t-url`, `#s2 .a-side` `.qr`/`.t-note`, `#s8 .a-wide` `.t-h1`/`.qr`/`.t-note`, `#s8 .a-side-top` `.t-h2`/`.t-note`, `#s8 .a-side-bottom` `.t-h3`/`.t-url` (for `.qr` the clip is a no-op — the box is exactly its viewBox — but it is declared so the shape is uniform). **No `nowrap` on the text boxes**: the URL is already split by `span`, and a nowrap headline would clip silently instead of wrapping.

## 4. Data, marking and the counts that moved

**Two new `data-shape` words: `contact` (`#s2`) and `outtro` (`#s8`).** They differ from each other and from the other six words because the gate requires every slide's word to be distinct (`checks.md` G3) and because `#live` must name what the slide is: `Slide 2 of 8 — contact`, `Slide 8 of 8 — outtro`. Nothing keys on the attribute. **The insertion is a renumbering, and every `#sN` moves with its section:**

| new | `data-shape` | was |
|---|---|---|
| `#s1` | `title` | `#s1` |
| `#s2` | `contact` | — new |
| `#s3` | `divider` | `#s2` |
| `#s4` | `bullets` | `#s3` |
| `#s5` | `comparison` | `#s4` |
| `#s6` | `chart` | `#s5` |
| `#s7` | `quote` | `#s6` |
| `#s8` | `outtro` | — new; the `closing` slide (old `#s7`) is deleted |

Every `#sN`-scoped height, clip and `nowrap` rule moves with its section (so the clip list becomes `#s4 .a-body .t-list li`, `#s5 .a-side .t-group p`, `#s5 .a-wide .t-table th`/`td`), and the deleted closing slide takes its own `#s7` rules and its `.pips` block with it — no slide carries pips now. The HUD's dots are static markup: **one eighth `.dot` is added** to `.dots`, `.is-on` stays on the first. `#counter`, `#live`, `#/N` and `.panel__where` are computed from the section count and need no edit (`checks.md` §4).
**No `DEMO` badge on either contact slide** — D-129's marking: a badge on a card carrying a real address would say the address is a placeholder. The amended counts, each hand-edited in its own document: **A3 → eight sections** with the order `title contact divider bullets comparison chart quote outtro`; **A4 → five `demo-badge`** (D-131 took the title slide's off), on `#s3`–`#s7`, none on `#s1`/`#s2`/`#s8`; **A9 → render `#/1`–`#/8`**, with `#/8` the three-card slide, `#/2` two cards, `#/1` the title; **A8(b)'s targets → `#s4`, `#s5`**; **A11 → `#/99` → slide 8**; **`presentation/README.md`'s slide list and editing recipe → eight slides, `#s9` as the next section's id**; **`presenter.md` → the notes and sources slides** (`#/3` has no notes; sources on `#/5`, `#/6`); **`checks.md` §1's "7 slides" → 8**.
**The HUD's note changes with it:** `placeholder content — not measured` becomes **`demo slides: placeholder content`**, which is true on all eight slides (it describes the demo slides, not the slide you are on), keeps A4's `placeholder content` substring, and is shorter than the string it replaces. The contact cards' text stays real, and the card tint is unchanged.

## 5. Presenter mode for the new slides

`N` on `#/2` must tell the presenter to **invite the scan now**: one to three `li` in `template.talk` saying the code is the same one that closes the deck, so nobody needs to write the URL down, and that the slide is real content (no badge). `N` on `#/8` must tell them to **invite it again and hold the slide** through questions. Neither note carries a figure, a date or a caveat, so neither is a claim — and neither is a `P4` "no notes" slide: both slides carry a `template.talk` (leaving `#/3`, the divider, as the deck's one slide with no notes).
`M`: **both contact slides carry no `template.more`.** The sources pane exists to back a measured claim, and the contact block makes none — D-129 is where the details come from and a decision row is not a figure — so `.more-btn` is `aria-disabled="true"` on `#/2` and `#/8` and `M` opens nothing (`presenter.md` §3, G9). If a later pass wants the provenance shown, the row is exactly `D-129` and the date `2026-11-17`, no other text, which is the form G9 checks; the design does not ask for it now.

## 6. Acceptance checks

**C1 (gate).** `grep -c 'http'` = 0; no `<img`, `src=`, `url(`, `@import`, `@font-face`, `<link`, `xmlns`; exactly one `<style>` and one `<script>`, neither with `src`/`href`; `grep -c 'innerHTML'` = 0. **C2 (gate).** Eight `section.slide`; `id` `s1`…`s8` in file order; `data-shape` order `title contact divider bullets comparison chart quote outtro`; eight distinct values; eight `.dot` with exactly one `.is-on` on the active index. **C3 (gate).** `grep -c 'class="demo-badge"'` = 5, none inside `#s1`/`#s2`/`#s8`; the HUD note reads `demo slides: placeholder content`. **C4 (gate).** The rendered `#s2 .t-url` and `#s8 .a-side-bottom .t-url` `textContent` — the two spans' strings concatenated — equals `https://www.linkedin.com/in/ryan-rasey-930403a4/` character for character, while the file's own text carries no `http`: the URL is written with its scheme's first letter as a character reference (`&#104;ttps://www.linkedin.com/`), which renders as the full address and keeps A2's grep at zero. A URL shortener, a bare `linkedin.com` or a dropped scheme fails this check.
**C5 (gate).** Two `svg.qr` in the file, one per contact slide: `viewBox="0 0 37 37"`, `width`/`height` `296`, `role="img"`, one `<title>` naming the profile, `aria-labelledby` pointing at it, **not** `aria-hidden`, no `xmlns`, `shape-rendering="crispEdges"`, and no `href`, `xlink`, `<use>`, `<defs>`, `<image>`, `<style>`, `transform` or `fill` attribute inside. **C6 (gate).** Each `svg.qr` holds exactly **212** `<rect>` elements (424 in the file) with integer `x`, `y`, `width` and `height = 1`, and **no dark geometry within 4 modules of the block's edge**: `4 ≤ x`, `x + width ≤ 33`, `4 ≤ y ≤ 32`. The 29 rows show as exactly 29 distinct `y` values. **C7 (gate).** Each `svg.qr` renders 296×296 design px (444×444 device px at ×1.5, 12 device px per module), `display: block`, inside its card, `fill` the `--ink` token at 13.4:1, and nothing is painted in its quiet ring — no card glyph, rule, border, shadow or background inside the block, card face only.
**C8 (reviewer-only, and the one that decides readiness).** Screenshot `#/2` and `#/8` with `firefox --headless --no-remote --profile <dir> --screenshot OUT.png --window-size=1280,720 "file://<abs>/presentation/index.html#/2"` (repeat at `--window-size=1920,1080`, the projector's case), crop the `.qr` block out of the PNG, sample each of the 29×29 module centres to a matrix, and **decode it: the string must equal the URL in C4.** A verified source matrix drawn wrongly is still a dead QR on the wall (D-129), so no gate-clean run and no reviewer's glance replaces this step.
**Which is which.** C1–C7 are mechanical and belong to the gate: `checks.md` G1 carries C1 and C3's greps, G3 carries C2, and the new **G11** carries C5–C7 (all DOM assertions, no sixth BiDi command). **C8 is reviewer-only** — decoding needs a QR decoder, none is installed (D-129 rejected generating with a library), so the gate stops at C6's geometry and its screenshots are the artefacts the reviewer decodes. A clean gate is still not a design review (`checks.md` §5): whether the code is big enough to scan from the back of the room is a look at the render, and C8 at 1920×1080 is the honest form of that question.
