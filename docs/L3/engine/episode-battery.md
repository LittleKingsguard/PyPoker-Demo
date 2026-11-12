# engine — what an episode's battery may assert

- **Owner:** the assertions the unit and integration batteries may make of one episode — driving `play_hand` and the other nine entry points and nothing below them — and the refusal messages they cite as measured
- **Ceiling:** 70 lines. At the ceiling, split by owner — never append
- **Split from:** `episode.md` §5, moved here whole when that page reached its 140-line ceiling for D-43's three post-hand facts

## 1. The refusals, and their measured messages

A non-callable policy, an illegal answer, an unknown shape and every refusal of `episode.md` §1 are
refused, and a policy that raises lets its own exception propagate (`surface.md` §1, §10, D-2). Measured,
on the six-seat shape: two positional policies raise `play_hand(shape): the shape 'six-seat-no-limit-100'
seats 6, so its hand needs 6 policies and the two positional policies seat 2`; a five-long seating raises
`play_hand(seats): the shape 'six-seat-no-limit-100' seats 6, so the seating must hold 6 policies in seat
order, got 5`; a seating handed beside a positional policy raises `…the two positional policies
seat0_policy and seat1_policy are absent, and one of them was given…`; and a non-callable at index 5
raises `play_hand(seats[5]): the policy must be callable, got NoneType` (`errors.md` §2, `seats.md` §4).

## 2. The record's keys, its decision facts, and the replay

Driving only `play_hand` (and the other nine): the record has `seed`, `decisions`, `payoffs` and
`reveal`; the seed is the seed it was called with; there is at least one decision and at most 200; every
decision carries the ten facts `records.md` §5 names and its readout the eleven, its action is a member
of its legal tuple, `minimum`/`maximum` are `None` exactly when no raise was legal while `amount` is
`None` exactly when it is no raise; the sequence of actions replays the same hand driven by hand; each
seat has at most one non-zero reward equal to its payoff; the payoffs sum to zero; two identical calls
give equal records and two seeds different ones (`episode.md` §1–§4, `shapes.md` §5, D-13).

`reveal` carries its three hand-level keys and one entry per seat in seat order with its four facts, and
no more: `board` of 0–5 card spellings, and at most `2·seats + 5` card spellings and `seats + 3` other
facts a hand — 9 and 5 on a two-seat shape, 17 and 9 on the six-seat one (`records.md` §5, §4 below). No
card of another seat is exposed anywhere a decision can reach it: the decision's `readout` is still
exactly the eleven facts of `readout.md` §2, and the reveal is written after the hand ends, so no policy
call can see it (`readout.md` §4, `e2e-surface.md` §2, FAM-2).

## 3. The six-seat readings

On `six-seat-no-limit-100` the same battery adds three: a six-long seating plays a hand whose decisions
name all six seats, whose payoffs hold six entries summing to zero, and whose rewards are those payoffs;
the two positional policies are refused on it; and an absent `seats` on a **two-seat** shape still plays
the same hand it played before this shape existed (`e2e-surface.md` §3.1, `seats.md` §4, ASM-43). The
reveal is per seat there too — six entries, `seat` in `0 .. 5`, and `hole` two spellings each, a folded
seat's included (`records.md` §5, `episode.md` §5).

## 4. What D-43 adds: `amounts`, the reveal's agreement, and the invariant

- **`amounts`** holds one entry per **legal** descriptor and no entry for a masked band; it is `None`
  exactly at `fold` and `check-call`, and its entry at the descriptor the hand applied equals that
  decision's `amount` — one value, not two derivations (`episode.md` §5, `sizing.md` §2, §3).
- **`won`, `showdown` and `split` agree with what the hand did**: a hand that ends by a fold shows at
  most one seat, so `showdown` is false and every `counterfactual` is `None`; a hand that reaches a
  river showdown shows two or more, and then `won` is true for a seat exactly when its cards were at
  least as good as every shown seat's and `split` is true exactly when two or more shown seats tie —
  never `CLASS_OF`'s class, which cannot see a kicker (`episode.md` §5, `counterfactual.md` §4).
- **`counterfactual`** is `None` at every decision of a hand without a showdown, with a split pot, or whose pot was
  built in **levels** — one in which some seat's take from the pot, its `payoffs[seat]` plus its whole-hand
  contribution, is neither `0` nor the whole pot — and otherwise a mapping over exactly that hand's per-decision legal
  descriptors, no illegal index valued and no legal index missing (`counterfactual.md` §2, §4, §5).
- **The level check is checked, not copied.** On its own six-seat run the battery recomputes every seat's whole-hand
  contribution from the record's `stacks` and `to_call`, asserts the invariant above at every decision wherever values
  are present, and asserts that no seat's take in that run lies outside `{0, the pot}` — the case names the hands it
  played, so the guard is a premise it measures rather than a branch it skips (`episode.md` §5, `counterfactual.md`
  §4's last paragraph).
- **The invariant**, on a two-seat and on a six-seat resolved hand: for every decision of it — a folded seat's own fold decisions and the live decisions any seat made **before** it folded included — the value at the descriptor the hand **applied** equals that seat's realised net chip delta, `episode["payoffs"][seat]`, the same number the terminal transition's `reward` carries. A realised fold gives `−C`, a realised live action on a `won` **and `shown`** seat `O = Δ`, on any other `−(C + added + later) = Δ`; the `shown` conjunct is what makes the middle branch true for a seat that folded later, and the two unresolvable cases are checked rather than assumed, so the equality has no exception to declare (`counterfactual.md` §4, ASM-12, FAM-22).
- **A resolved hand's seats all agree with the hand that was played**: `won` is true for every seat — a folded one included, whose figure answers "would its cards have been best" — whose best five-card hand is at least as good as **every shown** seat's, and false for every other, so it is true for the seat the pot was paid to and may also be true for a folded seat the pot was not; and the counterfactual's own descriptor is the number the record's terminal `reward` carries (`episode.md` §5, `counterfactual.md` §4).
- **Nothing the hand did moved**: the record's `payoffs`, its decisions and their `amount` are the
  hand's own after the change, a refused call still refuses the same way, and the record is still a
  function of the seed and the seating alone (`episode.md` §1, §4, D-43).
