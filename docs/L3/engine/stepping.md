# engine — legality and the step

- **Owner:** `legal_actions` and `apply_action` — the two entry points that ask what the acting seat may
  do and advance the hand by one chosen action
- **Ceiling:** 80 lines. At the ceiling, split by owner — never append

## 1. `legal_actions(hand)`

    def legal_actions(hand: Hand) -> tuple[str, ...]

    refuse unless the handle is a Hand                                # errors.md, InvalidHand
    refuse if the hand is over                                        # L2 surface.md §6
    legal = []
    if state.can_fold():                     legal.append("fold")
    if state.can_check_or_call():            legal.append("check-call")
    if state.can_complete_bet_or_raise_to(): legal.append("raise")
    return tuple(legal)

The order is the vocabulary’s own — `fold`, `check-call`, `raise` (`actions.md` §1) — which is also the
`features` index order, so `features.legal_indices` is a positional mapping and never a lookup
(`e2e-surface.md` §2, FAM-2.11). At most one entry per index, no duplicates, never empty for a live
hand, and deterministic: two calls on one hand return equal tuples.

**Fold appears only when `to_call` is non-zero**, and that is not something to implement: `pokerkit`
refuses a fold when the actor’s bet already equals the maximum bet (`verify_folding`,
`state.py:4375-4381`; `Mode.TOURNAMENT` raises rather than warning), so `can_fold()` and
`to_call > 0` agree by construction. That is exactly FAM-16.10’s "after the small blind calls, folding
is not legal".

`raise` is likewise `state.can_complete_bet_or_raise_to()`: False when the street’s cap of four bets is
reached, when the actor is already covered, and when every other player has folded or is all-in
(`state.py:4767-4833`). The engine declares no legality of its own beyond these three predicates — a
second source of truth would let `legal_actions` and `apply_action` disagree.

## 2. `apply_action(hand, action)`

    def apply_action(hand: Hand, action: str) -> Hand

    refuse unless the handle is a Hand                                    # InvalidHand
    refuse if the hand is over                                            # InvalidHand
    refuse unless isinstance(action, str) and action in ACTIONS           # InvalidAction
    refuse unless action is a member of legal_actions(hand)               # InvalidAction
    return advance(hand, action)                                          # advance.md §1

Validation is against the **argument** handle’s legal tuple, by value, before any state is copied. An
illegal descriptor is a contract violation and is never turned into a fold or a call on the violator’s
behalf (`L2 surface.md` §7, D-2). There is no coercion, so `0`, `"Fold"`, a `pokerkit` operation and
`None` all raise with the contract named.

The step on the copy is the three-method idiom `strata/platform.md` records — a `can_*` predicate, then
the method:

    if action == "fold":          state.fold()
    elif action == "check-call":  state.check_or_call()
    else:                         state.complete_bet_or_raise_to()

`complete_bet_or_raise_to()` is called **with no argument**. In fixed-limit games `pokerkit` resolves
that to `min_completion_betting_or_raising_to_amount` (`state.py:4855-4856`), and the fixed-limit
maximum is that same number (`state.py:4746-4748`), so the descriptor’s "no amount" is honoured
exactly. Passing an amount would move the size into this module’s hands and make the descriptor untrue
(`actions.md` §2).

The returned handle holds the advanced state and one appended history entry (`history.md` §1); the
argument handle is untouched, and the step draws no randomness because the deck was fixed at creation
(`L2 surface.md` §7, ASM-2). Applying the hand’s last action returns a handle for which `is_terminal`
is true.

## 3. What the battery may assert

Driving only the declared entry points: the tuple’s order is `fold`/`check-call`/`raise`; every
descriptor it returns is accepted by `apply_action` on a fresh hand of the same seed; a descriptor
outside it is refused with the contract named; `readout(h)["legal"] == legal_actions(h)`; `to_call == 0`
implies `"fold" not in legal_actions(h)`; one applied action grows `history` by exactly one and leaves
the argument handle’s readout unchanged; two different actions applied to one handle both succeed and
yield handles whose subsequent readouts differ; and `is_terminal(apply_action(h, a))` is a real `bool`.
