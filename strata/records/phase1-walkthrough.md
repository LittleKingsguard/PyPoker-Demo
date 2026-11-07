# phase1 walkthrough — blind documentation pass (D-14) · run 9, 2026-11-06 · **PASS**

Runner: a fresh agent that never saw the build, staged at `/tmp/wt9` as a listener's clone.
Scenarios: 13, unchanged across all nine runs. Verdict: **PASS** — every documented command ran as
written, every checkable figure matched the surface, and nothing a reader would meet is misleading.
This is the green that D-14 requires before a unit may be recommended as ready.

## What the runner exercised, and what it checked

Orientation and the reading order; the fixed game and the raise cap (0–4 bet-or-raise actions per
street, including the assumption's warning against the raise-only reading); dependencies and the
six-package import; the fastest battery, the 219-case `unittest` census and the thirteen-battery
script, with `checkpoints/` **byte-identical (19 files, sha256 unchanged) after every run**; a
redirected live R1 run writing **33** artefacts while the repository **ships 18**, nothing shipped
disturbed; the curves and their reading rules; a 108 s live table reproducing the shipped cells and
rating; the rating ranking top while losing to `always-call` and drawing `oracle`, with the docs
explaining exactly that shape; the shipped full table's untrained membership and its 9,000-hand
cost; the notebook headless at exit 0 writing only to its own root; the claims and refusals; a
decision from a shipped checkpoint; and the whole GPU page, whose every command behaved as
documented, `devices()`'s reason being byte-identical to the evidence bundle's.

`docs-insufficient` / `docs-stale` / `undocumented`: none. `guessed`: one false start (it indexed an
opaque pool before finding the documented read-back), corrected from the docs.

## What nine runs cost, and what they found

Findings per run: **12 → 4 → 4 → 2 → 3 → 1 → 4 → 0 → 0**. The run that mattered most was the
seventh, which found the *encoding* wrong rather than the prose: the readout's raise count reaches 4
while the docs and the encoder assumed 0–3, so `encode` wrote 1.3333 into a slot documented as
[0,1]. Fixing it invalidated both shipped artefacts, and both were regenerated.

Three defect classes recurred until the mechanism, not the sentence, was fixed: test isolation became
runner-agnostic, prose stopped quoting artefact figures, and `docs/` ceilings are now enforced by lint.

## Standing, for a reader

Phase 1 is ready: six modules, 1,113 unit and integration cases plus a 219-case acceptance battery,
all green; one real measured R1 run; two shipped artefacts regenerated against the current build and
reproducible under a pinned interpreter. Not done: R2–R6 are untrained, no long-budget run ships, and
the multi-round attention objective remains Phase 2.
