# P-talk-deck — exit walkthrough (D-14)

- **Date:** 2026-11-17 · **Verdict:** `STALE` · **Runner:** fresh L3 examiner, blind, staged to
  `/tmp/deck-walkthrough/` (docs + artifact only; `work/` scratch) · **Scenario set:** 10 steps, L0-authored
- **Staged:** `docs/presentation/design.md`, `presentation/README.md`, `presentation/index.html`
- One row per step: action · citation · outcome · guessed?. Verdict closed set `PASS|DOC-GAP|STALE|UNUSABLE`.

| # | action | citation | outcome | guessed |
|---|---|---|---|---|
| 1 | `→` from slide 1 | README §Controls; design §6 | slide 2, `2 / 7`, `#/2`, `#live` announces | no |
| 2 | open `…#/5` cold | README §Opening it; design §7 A9 | chart slide renders | no |
| 3 | open `…#/99` | design §6 Hash; §7 A11 | closing slide; address keeps `#/99` | no |
| 4 | `f` then `Esc` | README §Controls; design §6 Fullscreen | fullscreen, guarded | no |
| 5 | lengthen a slide-3 bullet | README §Editing; design §2, §5.3 | **bullet overprints the separator and the next bullet** | no |
| 6 | add an eighth slide | README §Editing; design §4, §5 | works; `data-shape` vocabulary undocumented | **yes** |
| 7 | paste a measured figure | README §Numbers; design header, §5 | allowed only from `strata/` records, with date | no |
| 8 | re-skin the felt | design §3 Theme tokens | one `:root`, `--felt-*` in one place | no |
| 9 | is it a Python module? | design header bullet (D-118) | not a module; no lint/test owed | no |
| 10 | why no network; what breaks it | design §1, §8 row 1 | inline only; a `<link href>`/`@font-face url()` breaks it | no |

**docs-insufficient:** no per-bullet character limit (a bullet must hold one 38px line; §5.3 gives heights only);
`data-shape` values have no vocabulary and no stated effect; the two `strata/` paths and `modules.json` are cited
but outside the quarantine, so steps 7 and 9 were read, not verified.

**docs-stale:** (1) README §Editing and design §2 claim longer copy "clips in its own block" — measured false: the
clipping rule is `.card > *` (direct children), so `.t-list li` (38px), `.t-group p` (76px) and table cells (44px)
paint over what follows; A8's re-added sum and `.card{overflow:hidden}` both pass while the text collides.
(2) §7 A11 says an out-of-range hash clamps to the **last** slide, but `#/0` opens slide 1 (byte-identical render
to `#/1`), which is what §6's "clamped into range" implies.

**undocumented:** an out-of-range hash is swallowed without normalising the address bar (`#/99` stays displayed);
Ctrl/Alt/Meta+arrow is ignored outright, so it neither navigates nor reads as unavailable.

**Routing (walkthrough §6):** both stale findings cite L3-owned documents → amend at L3 (design §2/§4/§5, A8, A11;
README §Editing), with the clipping correction stated as the CSS rule L4 must apply to `presentation/index.html`.
Step 6's vocabulary gap is L3's too. Re-run this walkthrough after the correction; this record is replaced.
