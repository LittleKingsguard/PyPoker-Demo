# engine — the equity question

- **Owner:** `equity`’s question — what it is conditional on, how the sample is obtained, and how a hand and a readout give the same number. The stream discipline that makes it repeatable is `stream.md`’s
- **Ceiling:** 90 lines. At the ceiling, split by owner — never append

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

## 2. The question, and the two inputs it needs

The question is conditional on what the acting seat has seen: *if the opponent’s two cards were a
uniform draw from the cards this seat has not seen, what share of the pot does the seat win, ties
counted as their share?* (`L2 environment.md` §4, ASM-4). So the answer is a function of exactly two
things — the acting seat’s two cards and the board — plus the caller’s seed and sample count, and of
nothing else: not the pot, not the stacks, not the street’s name. It is a share of the pot and not a
win-or-lose flag, which is what lets the oracle compare it with `to_call / (pot + to_call)` (ASM-6,
`protocol.md` §3).

`cards_of(decision)` is the one place the two argument shapes meet:

    Hand     -> (state.hole_cards[player_index(state.actor_index)],
                 state.get_board_cards(0))          # the board, NOT state.board_cards[0]
    readout  -> (parse_card(c) for c in readout["hole"], parse_card(c) for c in readout["board"])

The hand path reads the board exactly as `readout` does — `state.get_board_cards(0)`, never
`state.board_cards[0]`, which is one row per *dealing operation* and is empty pre-flop and one card
wide on the flop (`readout.md` §2, `platform.md` §2, `guardrails.md` G10). A hand path that read the
raw rows would raise or mis-answer at every pre-flop query and could not equal the readout path at a
flop decision.

The readout path parses the two-character spelling back to a card (`readout.md` §3) and hands back the
**same ordered pair** the hand path hands back, because `readout` wrote `hole` from that very list and
in that very order. Identical ranges in, identical sample universe, identical stream, identical float
out — that is how "the same number for both" is guaranteed rather than hoped for, and the battery
asserts the equality directly at the same decision.

The acting seat of a hand path is `seat_of(state.actor_index)` (`hand.md` §3): the equity is the *seat
to act*’s share, never seat 0’s, whatever the argument shape.

## 3. The sample

    unseen = [c for c in Deck.STANDARD if c not in set(hole + board)]   # 50, 47, 46 or 45 cards
    opponent_range = [[a, b] for a, b in itertools.combinations(unseen, 2)]
    value = calculate_equities(
                ([[h1, h2]], opponent_range),      # the seat, then a uniform opponent hand
                list(board),
                2,                                 # hole_dealing_count
                5,                                 # board_dealing_count
                Deck.STANDARD,
                (StandardHighHand,),
                sample_count=samples,
            )[0]

What binds the implementation here:

- the ranges are passed as lists of card combinations, the shape
  `pokerkit.analysis.calculate_equities` documents (`analysis.py:225-337`), and the seat’s range holds
  exactly one combination, so element `0` of the answer is the acting seat’s share;
- `board` may be empty (pre-flop): the library completes it from the unseen deck per sample, which is
  exactly the uniform opponent-and-runout model the question states;
- ties count as their share inside the library (`increment = 1 / sum(statuses)`,
  `analysis.py:194-198`), so no post-processing of the number happens here;
- the result is `float(...)` of element `0`, and nothing else: no rounding, no clamping, no caching, no
  memoisation. Rounding would make two different decisions report one number, clamping would hide a
  library answer instead of reporting it, and a cache would make the estimate no longer the function
  of `(decision, seed, samples)` that `L2 surface.md` §11 promises;
- the opponent range is built in `Deck.STANDARD` order over the unseen cards, never from a `set`
  iteration, so the sample universe is the same on every call and on every machine.

The cost of this call is `stream.md` §3 — the equity sample is nearly all of a table’s cost and the
one knob that decides where in ASM-21’s 0.105–0.153 s band a table’s per-hand cost lands.

## 4. What the battery may assert

Driving only the declared entry points: the first decision’s estimate is in [0, 1] and is a real
number; the same `(decision, seed, samples)` gives the same float twice; `equity(hand, s, n)` equals
`equity(readout(hand), s, n)` at the same decision; a coarse count (97) and a count of 1 are accepted
and in range; the hand’s own readout is unchanged before and after the call and the hand can still be
advanced afterwards; `random.getstate()` is identical before and after the call; and a non-integer
seed, a non-positive count, a non-hand-and-non-readout decision and a finished hand are refused with
the contract named.
