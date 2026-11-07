# phase1 walkthrough — blind documentation pass (D-14) · run 7, 2026-11-06

Runner: a fresh agent, staged at `/tmp/wt7` as a listener's clone. Scenarios: 13, unchanged across
all seven runs. Verdict: **STALE** — and this run found substance rather than wording: the built
surface contradicts the documented range of one observation slot, and a design assumption misstates
the raise cap on the pre-flop street.

## Confirmed clean (run 7)

Orientation and reading order; the fixed game's parameters; versions and imports; all batteries
green with `checkpoints/` byte-identical before and after **both** runners (19 files, digest
`efac1fc6…`); a redirected 33-artefact run that ships 18; the curves and their reading rules; a
109 s live table reproducing the shipped cells and rating; the rating's rank-versus-head-to-head
rule; the shipped full table's untrained membership; the notebook headless at exit 0 reproducing the
evidence; the claims and refusals; a decision from a shipped checkpoint; and the whole GPU page.

## Findings

| # | Finding | Owner |
|---|---|---|
| R-1 | **The readout's raise count can be 4, not 0–3.** `docs/L3/features/README.md` §5, `docs/L2/features/encodings.md` §3 and `docs/L3/features/flat-numeric.md` §4 state the count spans 0–3 with divisor 3, so the slot never leaves [0,1]. Measured on the surface over 400 random-policy hands: the count reaches **4** on all four streets, and `features.encode` therefore writes **1.3333** into a slot documented as [0,1]. Either the divisor/range or the encoding is wrong; the documents and the artefact disagree | `features` (L2 → L3 → L4) + the three documents |
| R-2 | **The cap gloss is wrong pre-flop.** The game-parameter assumption in `docs/L1/assumptions.md` says "the cap is four bets on a street — the opening bet plus three raises". That holds post-flop; pre-flop the posted blind is followed by the same four raises (five bet levels), and `README.md`'s "4 raises per street" matches the surface while the assumption's gloss does not | L1 |
| R-3 | **Dead record pointers.** Five distinct subjects are cited into *this* file — the write-root finding, the notebook-rewrite finding, the cell-replay finding, the one-build-seconds finding, the R1/R2 re-measurement — and none is in it, because the record is replaced every run (`strata/walkthrough.md` §7). The subject-form citation rule does not survive replacement: a subject in an ephemeral file is still an unresolvable citation | L0 (rule) + every citing layer |
| R-4 | `docs/L3/training/evidence.md` §2–§3 attributes `checkpoints()`'s `pending` key to `checkpoints.md` §4–§5, which declare only `entries` and `shipped` | L3 |

R-1 and R-2 are the substantive pair: a documented normalisation range the artefact exceeds, and a
game parameter stated one way in the brief's assumption and another way on the surface.

## L0's own share

R-3 is mine twice over (D-14): I created the ephemeral-record citation problem and then fixed it with a
rule (cite the subject) that fails for the same reason. The durable form is to cite the **decision
or assumption that carries the rule** — `D-n`, `ASM-n`, or a document section — and never the
walkthrough record. R-1's cost is not mine alone: if the divisor changes, every shipped model and
the evidence bundle are invalidated and must be regenerated, so the fix has a price that the user
should see.

A unit is recommended as ready only on a `PASS` (D-14); this is a loop recommendation.
