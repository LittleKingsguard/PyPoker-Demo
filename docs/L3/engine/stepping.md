# engine — legality and the step

- **Owner:** `legal_actions` and `apply_action` — the two entry points that ask what the acting seat may
  do and advance the hand by one chosen action
- **Ceiling:** 82 lines — raised from 80 for the second vocabulary and its masked bands. At the ceiling, split by owner — never append

## 1. `legal_actions(hand)`

    def legal_actions(hand: Hand) -> tuple[str, ...]

    refuse unless the handle is a Hand                                  # errors.md, InvalidHand
    refuse if the hand is over                                          # L2 surface.md §6
    legal = []
    for descriptor in vocabulary(hand):     # the hand's OWN shape's tuple, in its own index order
        if descriptor == "fold":            append iff state.can_fold()
        elif descriptor == "check-call":    append iff state.can_check_or_call()
        elif raise_amount(hand, descriptor) is not None:  append
    return tuple(legal)

The order is the hand's own shape's — `fold`, `check-call`, then that row's raise descriptors in its index
order (`config.md` §6, `actions.md` §1) — which is also the `features` index order for that shape, so
`features.legal_indices` is a positional mapping and never a lookup (`e2e-surface.md` §2, FAM-2.11). At
most one entry per index, no duplicates, never empty for a live hand, and deterministic.

**Fold appears only when `to_call` is non-zero**, and that is not something to implement: `pokerkit`
refuses a fold when the actor’s bet already equals the maximum bet (`verify_folding`,
`state.py:4375-4381`; `Mode.TOURNAMENT` raises rather than warning), so `can_fold()` and `to_call > 0`
agree by construction — exactly FAM-16.10’s "after the small blind calls, folding is not legal".

A raise descriptor appears only when **its band holds a legal integer**: `raise_amount` returns `None`
for a band that is empty at this decision, so the descriptor is absent from the tuple and is **never
collapsed onto a neighbouring band** — a decision may offer one raise descriptor and not the other three
(`actions.md` §2, `sizing.md` §2). The fixed row's single `raise` follows the same rule through
`can_complete_bet_or_raise_to()`, which is False when the street's cap is reached, when the actor is
already covered, and when every other player has folded or is all-in (`state.py:4767-4833`). The engine
declares no legality of its own beyond these predicates and that arithmetic — a second source of truth
would let `legal_actions` and `apply_action` disagree.

## 2. `apply_action(hand, action)`

    def apply_action(hand: Hand, action: str) -> Hand

    refuse unless the handle is a Hand                                       # InvalidHand
    refuse if the hand is over                                              # InvalidHand
    refuse unless isinstance(action, str) and action in vocabulary(hand)    # InvalidAction
    refuse unless action is a member of legal_actions(hand)                 # InvalidAction
    amount = raise_amount(hand, action)                                     # actions.md §2
    return advance(hand, action)              if the row is the fixed-limit one
    return advance(hand, action, amount)      otherwise                     # advance.md §1

Validation is against the **argument** handle’s own shape’s vocabulary and its legal tuple, by value,
before any state is copied: a descriptor the shape does not declare and one outside the decision’s legal
set are both contract violations, and an illegal action is never turned into a fold or a call on the
violator’s behalf (`L2 surface.md` §7, D-2). No coercion exists: `0`, `"Fold"` and `None` all raise.

The step on the copy is the three-method idiom `strata/platform.md` records — a `can_*` predicate, then
the method:

    if action == "fold":          state.fold()
    elif action == "check-call":  state.check_or_call()
    elif amount is None:          state.complete_bet_or_raise_to()      # the fixed row's raise
    else:                         state.complete_bet_or_raise_to(amount)  # the resolved sized raise

For the fixed row `complete_bet_or_raise_to()` is called **with no argument**: `pokerkit` resolves that to
`min_completion_betting_or_raising_to_amount` (`state.py:4855-4856`), and the fixed-limit maximum is that
same number (`state.py:4746-4748`), so the descriptor’s "no amount" is honoured exactly and the default
shape's step is the one this module has always taken — an amount here would make it untrue (`actions.md` §2).

The returned handle holds the advanced state, one appended history entry (`history.md` §1) and the same
shape's name; the argument handle is untouched, and the step draws no randomness because the deck was
fixed at creation (`L2 surface.md` §7, ASM-2). Applying the hand's last action returns a handle for which
`is_terminal` is true.

## 3. What the battery may assert

Driving only the declared entry points: the tuple's order is the hand's shape's index order; every
descriptor it returns is accepted by `apply_action` on a fresh hand of the same seed and shape; a
descriptor outside it — and another shape's descriptor — is refused with the contract named;
`readout(h)["legal"] == legal_actions(h)`; `to_call == 0` implies `"fold" not in legal_actions(h)`; one
applied action grows `history` by exactly one and leaves the argument handle's readout unchanged; two
different actions on one handle both succeed and yield handles whose later readouts differ; and
`is_terminal(apply_action(h, a))` is a real `bool`.
