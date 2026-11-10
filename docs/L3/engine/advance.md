# engine — advancing a hand

- **Owner:** one applied action — the advance by copy, and its justification against the rejected replay (the history that step appends is `history.md`'s)
- **Ceiling:** 70 lines. At the ceiling, split by owner — never append

## 1. Copy, never replay

    def advance(hand: Hand, action: str, amount=None) -> Hand   # src/engine/hand.py; apply_action calls it

    saved = random.getstate()                         # the platform draws, so the caller's stream is kept
    try:
        state = copy.deepcopy(hand._state)            # the copy is taken first, unconditionally
        operation = apply_one(state, action, amount)  # stepping.md §2 — predicate then method
    finally:
        random.setstate(saved)
    entry = history_entry(hand._state, action, operation)   # the PRE-step street, §2
    return Hand(state, hand._history + (entry,), hand._shape)

`amount` travels with the step and is the raise-to `apply_action` resolved for a sized descriptor; it is
`None` for a fold, for a check-call and for the fixed row's `raise`, which is what keeps that shape
byte-identical — its step is still `complete_bet_or_raise_to()` with no argument, so its deals, its
history entries and its payoffs are unchanged card for card (`actions.md` §2, `sizing.md` §2). The shape's
name travels with it too: the returned handle is the same shape's, because no entry point takes a shape
beside a hand (`hand.md` §1).

The save/restore is not decoration. `_begin_dealing` evaluates `get_dealable_cards(None, False)` on
every street transition and that path runs `shuffled(self.reserved_cards)` merely to take a length, so
a step *does* consume 1–3 draws of Python’s global `random` over a hand — while leaving the actual
deal untouched, because the board comes from the `deck_cards` fixed at creation (`platform.md` §4).
Restoring keeps `L2 surface.md` §1 and §7 true ("draws no randomness", "hands the stream back as it
found it") and keeps a caller’s own draws — a `random` baseline policy’s, for instance — from reaching
the deal.

Chosen shape: `deepcopy` of the `pokerkit` state, then the action on the copy. The handle is immutable
by construction — `Hand._state`, `Hand._history` and `Hand._shape` are never rebound and never mutated —
so "`apply_action` leaves its argument at its own state" (`L2 surface.md` §1 rule 6) holds without the
implementer having to remember anything.

Rejected: **replay** — store the seed in the handle and re-create the state by re-seeding `random` and
re-applying the action list. Rejected on three independent grounds:

1. re-seeding inside a step makes a second seeding point, which ASM-2 and `L2 surface.md` §1 forbid
   outright (only `new_hand` seeds);
2. re-applying every action is O(n²) in the hand’s length, on a per-decision path;
3. a replay re-derives the deck *from the stream*, so a caller’s own `random` draws between two steps
   would silently change a hand in flight. `deepcopy` cannot: the deck order was fixed at creation
   (`hand.md` §2).

Cost: measured, one `deepcopy` is about 0.1 ms per decision — well inside ASM-21’s 0.105–0.153 s
per-hand band (`cost.md` G6).

Also rejected: mutating and returning the same handle. Every e2e case that keeps an earlier handle
(`finished_hand`, `decision_walk`, the oracle’s mid-hand `equity`) depends on the old handle still
reading its own state.

## 2. The public history

`history.md` §1 owns this question — the one-entry rule, the entry grammar, the `<amount>` and
`<index>` definitions and the heads-up fold note moved there whole when this file reached its
ceiling. The number stays so every citation of `advance.md` §2 still resolves.

## 3. What the battery may assert

Driving only the declared entry points: `readout(apply_action(h, a))["history"]` has exactly one more
entry than `readout(h)["history"]`; the earlier handle still reports its own shorter history and its
own seat after the step; the entries are stable `str`s, so two driven hands of one seed and one policy
sequence produce identical `history` lists; every entry names an engine seat index and a street; and a
refused step (illegal descriptor, finished hand) leaves the argument handle’s history unchanged.
