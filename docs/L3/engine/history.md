# engine — the public history

- **Owner:** the one public record of a deal — one entry per applied action, and the grammar an entry is built from
- **Ceiling:** 45 lines. At the ceiling, split by owner — never append
- **Split from:** `advance.md` §2, moved here whole when that file passed its 70-line limit

## 1. The public history

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

One consequence to name rather than discover: in **heads-up** a fold always ends the hand, and `readout`
refuses a finished hand, so there the `folds` entry is never observable through the entry points. It is
built anyway — the grammar has no special case — and the fold is observable where it matters, as an
episode decision and as the payoffs that follow it. On a shape with more than two seats it is observable
directly, because a fold does not end the hand while other seats are live: measured on
`six-seat-no-limit-100`, the decision after seat 3 folds reads `seat == (4, False)` and
`history == ['preflop seat 3 folds']`, and three folds then a call leave four entries in order. The
grammar is one grammar for every seat count, not a heads-up special case (`seats.md` §2, `hand.md` §3).
