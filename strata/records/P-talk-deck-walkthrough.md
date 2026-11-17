# P-talk-deck — exit walkthrough (D-14): WAIVED at run 6

- **Date:** 2026-11-17 · **Status:** waived for `presentation/` by **D-130** (user: "this is html. I will inspect visually")
- **Last completed run:** run 5, `PASS`, against the **seven-slide** deck (record history in git).
- **Run 6** was staged against the eight-slide deck (the contact slides and the QR, D-129) and **cancelled** at the
  user's instruction. The eight-slide deck is therefore **not** walkthrough-verified, and this file does not claim
  that it is.

## The evidence that replaces the loop

| check | result |
|---|---|
| `node presentation/check.mjs --out …` | `slides: 8 (derived from section.slide)`, `no issues`, exit 0, 18 screenshots at 1280×720 and 1600×1000 |
| static, `presentation/index.html` (1,637 lines) | `http` 0, `<img` 0, `url(` 0, `src=` 0, `xmlns` 0, one `<style>`, one `<script>`, 8 slides, 8 distinct `data-shape`, 424 QR rects, 6 demo badges, 8 dots |
| QR from the **render**, not the asset | both contact slides screenshotted at 1280×720, the drawn code re-sampled out of the pixels (8 px/module), decoded by an independent decoder: version 3, EC L, mask 2, payload `https://www.linkedin.com/in/ryan-rasey-930403a4/`, 0 of 841 modules differing from the verified source matrix |
| contact copy | `#s2`: Ryan Rasey · Founder/Dev @ Auspicion · ryan.rasey@auspicion.ai · the URL; `#s8`: "Thank you", the same three details in the side cards plus the URL; no `DEMO` badge on either |
| no collateral damage | slides 1, 3–7 differ from their pre-change renders only inside the HUD strip (y 642–670), where the dots and counter went from seven to eight |
| gate not vacuous | a planted clipped bullet is caught at both sizes, exit 1; G11 was negative-tested on QR copies (a rect outside the quiet zone, `aria-hidden`, 211 rects) |

**What is left to the eye (the user's):** the theme and card composition, the contact slides' balance, whether the QR
reads at projector size, and the HUD with eight dots. Known cosmetics carried: one stale code comment at
`refreshPanels()` ("follows the slide", true for notes only), the README wheel row omits the 250 ms quiet reset, and
the printed URL wraps at its path boundary across two mono lines by design.
