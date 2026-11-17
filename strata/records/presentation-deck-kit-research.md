# presentation — intake research: the Gardens deck kit (D-15)

- **Date:** 2026-11-17 · **Source:** `/home/ryanr/Downloads/20261117_gardens-not-platforms_deck-kit.zip`
  (extracted to `/tmp/deckkit`; Windows backslash paths and dirs without `+x` — extract with a
  path-normalising script, then `chmod -R u+rwX`) · **Procedure:** `strata/research.md` §1, run at L0
  because `role_l0_research` cannot be mounted (`strata/platform.md` §Delegation)
- **What it is:** a skill (`skill/talk-deck/SKILL.md`) plus the working deck it built — Gardens, Not
  Platforms, Code4y'all at Improving, 2 Nov 2026 — with `v3/build.mjs` (source → one HTML file),
  `v3/slides.mjs` + slide families + `v3/art.mjs` (inline SVG), `v3/deck.js` (presenter),
  `v3/check.mjs` (the gate), `v3/ART-DIRECTION.md`, `v3/FACTCHECK-2026-11-02.md`.

| # | Claim | Source | Confidence | If false |
|---|---|---|---|---|
| 1 | The gate screenshots every slide at four window shapes and flags: element outside the slide, text box clipping its text (`scrollHeight > clientHeight + 3` with non-`visible` overflow), overlapping text boxes, a label on a dot, labels overlapping, text under 14px; it must print "no issues", and "a clean check is not a design review" | `v3/check.mjs` L32–68, L101–106; `SKILL.md` §How the system is built | high — read | we keep only manual/pixel checks, and the defect our walkthrough found (a wrapped bullet overprinting) stays a walkthrough-only catch |
| 2 | Its Chrome-CDP half does not run here: snap Chromium dies with `snap-confine is packaged without necessary permissions`, and there is no `chromedriver`/`geckodriver` | measured this session | high | we could use `check.mjs` almost verbatim |
| 3 | Firefox 155 exposes WebDriver BiDi at `ws://127.0.0.1:PORT/session`; from Node 24's global `WebSocket`, `session.new` + `browsingContext.navigate` + `script.evaluate` + `browsingContext.captureScreenshot` all work — a probe read slide `s4` as 32 boxes, 0 clipped, min font 20px, and captured a 207 kB frame | measured: `/tmp/biditest/bidi.mjs` | high — measured | the gate would be pixel-geometry only (screenshot ink vs the design's px budgets), which cannot see every clip |
| 4 | The presenter layer: `N` notes (hidden panel, audience never sees them), `M`/More for sources per slide, `T` theme, `S` a Garden/Platform flip, `F` fullscreen; the count/act bar carries the act, slide counter and clock | `v3/deck.js` L1–80; `SKILL.md` §deck.js; `..._v3-deck_config.md` | high | a live talk has no notes and no per-slide sources — the two things our numbers rule needs at the moment of speaking |
| 5 | That kit is **fluid** — "every slide fills the window at any shape… no 16:9 box, no letterbox bands" — the opposite of D-118's fixed 1280×720 stage, which `docs/presentation/design.md` §8 rejects | `ART-DIRECTION.md` §visual system; D-118 | high | the fixed-stage decision would deserve re-opening — a user decision, not a research one |
| 6 | It builds from source ("Do not hand-edit the HTML": `slides.mjs` → `build.mjs` → HTML, inlining fonts, images, scripts), which is how notes/sources/assets travel | `v3/build.mjs`; `20261102_..._config.md` §Regeneration | high | D-118's no-build-step rejection would be wrong; as it stands the kit itself confirms the cost (see row 9) |
| 7 | Its fact-check form is per-figure prose: claim, source URL, date read ("read directly" vs "search summary"), what the source does **not** support, and a "Needs <author>" list of figures still unresolved | `v3/FACTCHECK-2026-11-02.md` | high — read | our numbers rule ("only from `strata/decisions.md`/`strata/records/`, with the date") would stay a policy with no artefact behind it |
| 8 | Slide rules it draws from real corrections: no eyebrow labels; explain, then ask (each act ends on a question); a drawing, a headline and one line; the fact is the biggest thing, not a slogan; one thread through the talk; ~1.2 min/slide counted against the slot; text floor 14px; notes carry dates, figures and caveats; no em dashes | `SKILL.md` §Slide rules | high for transfer of the first seven; the em-dash ban is that author's house style, not ours | the content pass would be shaped ad hoc instead of by rules that were paid for once already |
| 9 | Practice rules: agree the outline before building; write the facts first; dated copy of the current deck before a rebuild; test builds to a scratch path | `SKILL.md` §Order of work | high | we re-learn "building first and arguing about content after cost the most time on every earlier deck" |

**What this changes:** nothing yet — research commits no design (D-15). It arms an L0 decision:
the gate (rows 1–3) is portable and would have caught the clipped-bullet defect mechanically; the
presenter layer (row 4) and the fact-check form (row 7) are the two features our deck lacks that a
live talk needs. Rows 5–6 are considered and declined unless the user re-opens D-118. Row 8's rules
are content-pass material, not sampler material.
