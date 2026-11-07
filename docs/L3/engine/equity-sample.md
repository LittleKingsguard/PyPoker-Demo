# engine — the equity sample

- **Owner:** the sample behind the number — the unseen deck, the one library call, the tie share, and the five things that bind the implementation
- **Ceiling:** 45 lines. At the ceiling, split by owner — never append
- **Split from:** `equity.md` §3, moved here whole when that file passed its 90-line limit

## 1. The sample

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
  iteration of this project’s own — but the library beneath it does exactly that: `calculate_equities`
  builds each selection’s run-out deck as `list(set(deck) - counter.keys())` (`analysis.py:316`) and
  draws from that list with `sample` (`analysis.py:163`), over a `Card` whose frozen hash comes from
  its `Rank` and `Suit` fields (`utilities.py:35`, `:215`, `:256`), so those set orders follow the
  per-process string-hash seed; a run is bit-reproducible only under a pinned `PYTHONHASHSEED`. That
  the estimator should be order-stable instead is `engine`’s recorded defect (`protocol.md` §4), and
  the counts sit beside the bundle they were made against (`docs/L3/training/evidence.md` §6).

The cost of this call is `stream.md` §3 — the equity sample is nearly all of a table’s cost and the
one knob that decides where in ASM-21’s 0.105–0.153 s band a table’s per-hand cost lands.
