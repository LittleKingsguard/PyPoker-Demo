# Intake: replace the history block with a trained opponent model · both reviews + the falsification test

**Proposal (user):** replace the encoder's `history` inputs with a trained attention model's outputs — an opponent's
likely next action and their likely hand strength — over that opponent's history, within the hand and across prior hands.

## The falsification test, run first (0.2 s)

Fixed dry board `3s 6d 9d 4c Jh`, the D-70 hole set, both seatings — does a league member's action depend on its own
hole cards? **folder 1/5 · raiser-50-50 1/5 · raiser-83 1/5 · mask-no-squash 2/5 with an identical first action.**

**Every member is card-invariant.** Their actions cannot carry their hand strength, because their strength never entered
the action. So the proposal's second output has a **ceiling of zero on the only population the project has**, and its
first output predicts a constant — accurate, and carrying no information (D-59, D-71, D-82, D-108).

## Validity — FAIL

The history block carries **three action kinds and nothing else** (`src/features/history.py:35` — no seat, amount or
street), so an opponent's history is not recoverable from it. Cross-hand memory has **no carrier**: `play_hand` is one
hand per call, opponents are re-drawn and anonymous every hand, and a policy depending on state outside the readout
breaks checkpoint-equals-policy (protocol §5). It re-proposes **D-9's deferred Phase 2**, whose exploiting premise
D-23/D-34/D-57 measured negative, and it inherits the dilution defect, the dead-trunk trap and the
aggregate-hides-local-error lesson — and it is **not one variable** (K7).

## Critique — ADJUDICATION, 18 findings, three blocking

- **K7/K13:** removing the 98-token block removes ~90 % of the padding the unmasked pooler averages, **shipping
  D-110's mask effect** alongside the input change — the bundling D-102 forbade.
- **K14:** the `strength` licence (a deterministic function of facts already carried, injected) does **not** reach a
  cross-hand estimate, and no module holds per-hand state; the matrix's member reuse and D-57's antisymmetry check
  break by construction.
- **K20:** on a pool where **seven of ten members are one behaviour**, a majority-action predictor scores high having
  read nothing — **accuracy is a base-rate artefact**, the same shape as D-59, D-67→D-68 and D-95.
- **K15:** the history block is the **only** route by which a bet's *size* could ever reach the learner, and size is the
  one dimension this project measured a price for (D-26: ¼-pot beats ½-pot by **+2.03 ± 0.62**).

## Disposition

**Deferred, not refused** — D-111. The premise is false on today's population, and two blocking findings concern how the
experiment would be confounded rather than whether the idea could work.
