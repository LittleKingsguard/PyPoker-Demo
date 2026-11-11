# engine — the equity question

- **Owner:** `equity`’s question — what it is conditional on, how many opponents the shape seats, and how a hand and a readout give the same number (the sample itself is `equity-sample.md`’s; the stream discipline that makes it repeatable is `stream.md`’s)
- **Ceiling:** 126 lines — raised from 90 for the third seat count: the multi-way opposition, the two range forms and the empty-range form's measured failure, and the seat count's source. At the ceiling, split by owner — never append

## 1. The signature and its refusals

    def equity(decision, seed: int, samples: int) -> float

- `decision` is a `Hand` **or** that hand’s `readout` mapping — both denote the same decision
  (`L2 surface.md` §11, ASM-4). Anything else, and a `Hand` that is over, is refused
  (`errors.md`, `InvalidDecision`).
- A mapping is accepted only if it really is a decision’s facts: `hole` must be exactly two card
  strings of the declared spelling and `board` must be 0, 3, 4 or 5 of them, all distinct. A mapping
  missing either, carrying a non-card, or naming the same card twice, is refused rather than sampled
  (`errors.md` §4) — an equity asked about a "hand" of no cards is not a question this module answers,
  and answering it with a number would report a decision nobody made. Extra keys carried beside the two
  facts are ignored. The distinctness clause is not decoration: the library silently drops a selection
  whose cards collide and then draws from an empty universe, so a duplicate would surface as a library
  `IndexError` instead of this module’s refusal.
- `seed` must be an `int` and not a `bool`; `samples` must be a positive `int` and not a `bool`. Both
  are refused before any sampling, so a refused call cannot move the stream (`stream.md` §1).
- A coarse sample count and a count of 1 are legal calls and not errors: the count is the caller’s
  accuracy knob, not a validity rule (FAM-16, ASM-4).

The **opponent count is the shape’s**, and it is read from one of two places: a hand’s own shape
(`seat_count(hand._shape)`), or, for a readout mapping, the length of its `stacks` fact — which is one
entry per seat in seat order — falling back to two when the mapping carries no such sequence, because
two is what an absent shape reads as (`readout.md` §2, `seats.md` §3, ASM-44). Measured:
`_opponents_of_readout` answers 6 for a six-seat readout, 2 for a two-seat one, and 2 for a mapping with
no `stacks` at all (`seats.md` §2).

## 2. The question, and the two inputs it needs

On a **two-seat** shape the question is: *if the opponent’s two cards were a uniform draw from the cards
this seat has not seen, what share of the pot does the seat win, ties counted as their share?*
(`L2 environment.md` §4, ASM-4). On a shape with **more** seats it is the same question asked
`seats − 1` times at once: the opponents are the other seats, each holding a uniform draw from what the
acting seat has not seen, and the answer is still the acting seat’s own share — a six-seat call is
six-way, against five random hands (`e2e-surface.md` §3.1, `seats.md` §2, D-33). The sample count is the
caller’s and does not change with the seat count.

So the answer is a function of exactly two things — the acting seat’s two cards and the board — plus the
seat count, the caller’s seed and sample count, and of nothing else: not the pot, not the stacks, not
the street’s name. It is a share of the pot and not a win-or-lose flag, which is what lets the oracle
compare it with `to_call / (pot + to_call)` (ASM-6, `protocol.md` §3).

`cards_of(decision)` is the one place the two argument shapes meet, and the one place the seat count
comes from:

    Hand     -> (state.hole_cards[player_index(state.actor_index, seats)],
                 state.get_board_cards(0), seats)      # the board, NOT state.board_cards[0]
    readout  -> (parse_card(c) for c in readout["hole"],
                 parse_card(c) for c in readout["board"],
                 the length of readout["stacks"] when it exceeds two, else two)

The hand path reads the board exactly as `readout` does — `state.get_board_cards(0)`, never
`state.board_cards[0]`, which is one row per *dealing operation* and is empty pre-flop and one card
wide on the flop (`readout.md` §2, `platform.md` §2, `guardrails.md` G10). A hand path that read the
raw rows would raise or mis-answer at every pre-flop query and could not equal the readout path at a
flop decision.

The readout path parses the two-character spelling back to a card (`readout.md` §3) and hands back the
**same ordered pair** the hand path hands back, because `readout` wrote `hole` from that very list and
in that very order. Identical ranges in, identical sample universe, identical stream, identical float
out — that is how "the same number for both" is guaranteed rather than hoped for, and the battery
asserts the equality directly at the same decision, on every shape.

The acting seat of a hand path is `seat_of(state.actor_index, seats)` (`hand.md` §3): the equity is the
*seat to act*’s share, never seat 0’s, whatever the argument shape.

### 2.1 The opposition, per seat count

`pokerkit` takes one hole range per player (`analysis.py:225-337`), and the two shapes of range are what
the two questions need (`equity-sample.md` §1, ASM-4):

- **Two seats — the explicit enumeration, unchanged.** The opponent’s range is every two-card
  combination of the unseen deck, built in `Deck.STANDARD` order: 1225 combinations pre-flop, 1081 on
  the flop, 1035 on the turn, 990 on the river. This is the answer this module has always given, and it
  is measured to be bit-identical to a direct `calculate_equities` call on that enumeration at the same
  seed and sample count (`shapes.md` §5).
- **More than two seats — one empty selection per opponent.** The range is the single **empty**
  combination per opponent, which is the form `calculate_hand_strength` builds for its
  `player_count - 1` opponents (`analysis.py:404-406`); `__calculate_equities_0` completes each player’s
  hole cards from the sampled deck (`analysis.py:157-169`), so an empty selection means "deal this
  seat’s cards at random from what is left". The enumeration **cannot** be used here: six players would
  be the product of five opponent combinations over a fifty-card deck, and `product(*hole_ranges)`
  (`analysis.py:311`) would enumerate it whole before sampling once — the reason the library offers the
  empty form at all (`seats.md` §2).

**Measured, and stated as the form to hold.** The empty form is `[[]]` — a range **holding** one empty
selection — and **not** `[]`, because `product` over a bare `[]` yields no selection at all and the call
then raises `IndexError: range object index out of range` at `analysis.py:328`. On the six-seat row,
`[[[Kd, 2d]], [[]], [[]], [[]], [[]], [[]]]` returns six shares summing to 1.0, with the acting seat’s
share equal to `calculate_hand_strength(6, ...)`’s answer at the same seed and sample count, while
`[[[Kd, 2d]], [], [], [], [], []]` raises. `src/engine/equity.py` writes the first of those two forms, and
`guardrails.md` G16 is the note that keeps it (`seats.md` §2, D-33).

## 3. The sample

`equity-sample.md` §1 owns this question — the unseen deck, the `calculate_equities` call, the
library's tie share and the five bindings moved there whole when this file reached its ceiling. The
number stays so every citation of `equity.md` §3 still resolves.

## 4. What the battery may assert

Driving only the declared entry points: the first decision’s estimate is in [0, 1] and is a real
number; the same `(decision, seed, samples)` gives the same float twice; `equity(hand, s, n)` equals
`equity(readout(hand), s, n)` at the same decision; a coarse count (97) and a count of 1 are accepted
and in range; the hand’s own readout is unchanged before and after the call and the hand can still be
advanced afterwards; `random.getstate()` is identical before and after the call; and a non-integer
seed, a non-positive count, a non-hand-and-non-readout decision and a finished hand are refused with
the contract named.

On `six-seat-no-limit-100` the same battery asserts the same seven properties at a six-way decision,
plus two of its own: the answer is the acting seat’s share against **five** random hands — the six
shares of one sample sum to 1.0, and the seat’s own value equals `calculate_hand_strength(6, ...)` at the
same seed and count — and the seat count is read from the decision, so a six-seat readout and its hand
answer one number while a two-seat decision is still answered by the enumeration (`seats.md` §2,
ASM-44).
