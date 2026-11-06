# engine — advancing a hand

- **Owner:** one applied action — the advance by copy, its justification against the rejected replay, and the public history each step appends
- **Ceiling:** 70 lines. At the ceiling, split by owner — never append

## 1. Copy, never replay

    def advance(hand: Hand, action: str) -> Hand      # src/engine/hand.py; called by apply_action

    saved = random.getstate()                         # the platform draws, so the caller's stream is kept
    try:
        state = copy.deepcopy(hand._state)            # the copy is taken first, unconditionally
        operation = apply_one(state, action)          # stepping.md §2 — predicate then method
    finally:
        random.setstate(saved)
    entry = history_entry(hand._state, operation)     # the PRE-step street, §2
    return Hand(state, hand._history + (entry,))

The save/restore is not decoration. `_begin_dealing` evaluates `get_dealable_cards(None, False)` on
every street transition and that path runs `shuffled(self.reserved_cards)` merely to take a length, so
a step *does* consume 1–3 draws of Python’s global `random` over a hand — while leaving the actual
deal untouched, because the board comes from the `deck_cards` fixed at creation (`platform.md` §4).
Restoring keeps `L2 surface.md` §1 and §7 true ("draws no randomness", "hands the stream back as it
found it") and keeps a caller’s own draws — a `random` baseline policy’s, for instance — from reaching
the deal.

Chosen shape: `deepcopy` of the `pokerkit` state, then the action on the copy. The handle is immutable
by construction — `Hand._state` and `Hand._history` are never rebound and never mutated — so
"`apply_action` leaves its argument at its own state" (`L2 surface.md` §1 rule 6) holds without the
implementer having to remember anything.

Rejected: **replay** — store the seed in the handle and re-create the state by re-seeding `random` and
re-applying the action list. Rejected on three independent grounds:

1. re-seeding inside a step makes a second seeding point, which ASM-2 and `L2 surface.md` §1 forbid
   outright (only `new_hand` seeds);
2. re-applying every action is O(n²) in the hand’s length, on a per-decision path;
3. a replay re-derives the deck *from the stream*, so a caller’s own `random` draws between two steps
   would silently change a hand in flight. `deepcopy` cannot: the deck order was fixed at creation
   (`hand.md` §2).

Cost: measured, one `deepcopy` is about 0.1 ms per decision — well inside ASM-15’s envelope
(`guardrails.md` G6).

Also rejected: mutating and returning the same handle. Every e2e case that keeps an earlier handle
(`finished_hand`, `decision_walk`, the oracle’s mid-hand `equity`) depends on the old handle still
reading its own state.

## 2. The public history

`Hand._history` is a tuple: **one entry per applied action and one only**, whatever the action, and
however many `pokerkit` operations it caused internally (bet collection, board dealing, showdown
setup — none of those is an applied action, `L2 surface.md` §7).

An entry is a plain `str` of one grammar, built from the state *before* the step plus the operation’s
own amount:

    "<street> seat <index> folds"
    "<street> seat <index> checks"                 # check_or_call with amount == 0
    "<street> seat <index> calls <amount>"         # check_or_call with amount > 0
    "<street> seat <index> raises to <amount>"     # complete_bet_or_raise_to

`<amount>` is the chips added to the caller’s street bet for a call, and the total street bet level
for a raise (the value `pokerkit` reports on the operation it returns). `<index>` is the **engine**
seat (`hand.md` §3), never a `pokerkit` index.

A card never appears in a history entry: the revealed cards are already in `board`, and a street
change is visible both in the entry’s `<street>` and in `board`’s length. So the one-spelling rule of
`readout.md` §3 binds `hole` and `board` only and cannot be broken through the history.

Two records of one deal therefore compare through `history` alone, which is what FAM-16’s
applied-action case and FAM-4’s reproducibility case read (`battery.md` §3, ASM-2).

One consequence to name rather than discover: in heads-up a fold always ends the hand, and `readout`
refuses a finished hand, so the `folds` entry is never observable through the entry points. It is built
anyway — the grammar has no special case — and the fold is observable where it matters, as an episode
decision and as the payoffs that follow it.

## 3. What the battery may assert

Driving only the declared entry points: `readout(apply_action(h, a))["history"]` has exactly one more
entry than `readout(h)["history"]`; the earlier handle still reports its own shorter history and its
own seat after the step; the entries are stable `str`s, so two driven hands of one seed and one policy
sequence produce identical `history` lists; every entry names an engine seat index and a street; and a
refused step (illegal descriptor, finished hand) leaves the argument handle’s history unchanged.
