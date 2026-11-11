# engine — L4 guardrails

- **Owner:** one note per risk this design identified, in the order they bite, each with the rule L4 must hold and the symptom of getting it wrong
- **Ceiling:** 190 lines — raised from 152 for the third seat count: G2 restated as the general map and its blind vector, G16 for the multi-way equity range, and the seat-count clauses in G5, G8, G9 and G14. At the ceiling, split by owner — never append
- **Read with:** `hand.md`, `actions.md`, `readout.md`, `episode.md`, `equity.md`, `errors.md`, `layout.md`

These are not suggestions. Each one is a place where a plausible, tidy-looking implementation breaks a
contract the unit battery and the e2e battery both assert.

## G1 — Mutation: a step returns a new handle and never touches its argument

`apply_action` deep-copies the state **first** and validates against the **argument** hand’s legal
set. The argument’s `_state` and `_history` must be the objects it arrived with, and no attribute of
it may be rebound (`advance.md` §1, `L2 surface.md` §1 rule 6). Symptom of getting it wrong: a caller
that keeps an earlier handle and re-reads it after the hand moved on sees the wrong seat acting — an
e2e case that drives a hand and then asks an old handle passes only by luck. Related: `readout`
returns fresh containers, so a caller’s edit of `hole`, `board`, `stacks`, `legal` or `history`
cannot reach the handle.

## G2 — The seat map: the blinds are per player index above two seats, and reversed twice at two

At `player_count == 2` the library reads the blind through `not player_index` (`state.py:3336-3339`)
and reverses the pair again when it computes the pre-flop opener (`state.py:4203-4212`), so
`raw_blinds_or_straddles=(1, 2)` makes **player 0** post the 2 and **player 1** the 1. Above two seats it
reads `blinds_or_straddles[player_index]` (`state.py:3338-3339`), so the padded vector
`(1, 2, 0, 0, 0, 0)` gives player 0 the 1 and player 1 the 2. In both cases `collect_bets` zeroes every
bet before the next street opens (`state.py:3266-3267`, `:3621-3627`), so the post-flop opener is player
0 for **every** player count and the button — the seat that acts last post-flop — is player
`player_count − 1`. Engine seat 0 holds the button on every shape, so the one translation is

    seat_map(seats)    = tuple((s - 1) % seats for s in range(seats))    # (1, 0) | (5, 0, 1, 2, 3, 4)
    blind_vector(row)  = tuple(row["blinds"]) + (0,) * (row["seats"] - 2)  # (1, 2) | (1, 2, 0, 0, 0, 0)

(`hand.md` §3, `seats.md` §2). Two wrong fixes that look right and are not: passing `(2, 1)` to
`create_state` (the library reverses an already-reversed pair and the button moves back to where you
started), and sorting the stacks (chips are per seat, not ascending). Symptom of getting it wrong: the
first decision reads `stacks == (18, 19)` or `seat == (1, False)` on a two-seat shape, or reads
`seat == (0, True)` on the six-seat one where it must read `seat == (3, False)` and
`stacks == (100, 99, 98, 100, 100, 100)` — and `payoffs` is keyed by the wrong seat, so every per-seat
fact in the project is mirrored (`hand.md` §4).

## G3 — The one spelling: a card is a two-character `str`, an action is one of its shape's `str`s

No `pokerkit` object leaves this module: not a `Card`, not a `Deck`, not an operation, not the state
(`readout.md` §3, `actions.md` §1). The reason is not taste: `features` must read a readout without
importing `pokerkit`, and a second spelling of a card anywhere in the project is a D-3 violation
(`e2e-surface.md` §2). Symptom: an encoder that starts `from pokerkit import Card` to understand a
readout.

## G4 — The global `random` stream: one seeding point, and two save/restore sites

`new_hand` seeds; nothing else does, and `play_hand`’s effect on the stream is exactly `new_hand`’s
because it deals through it. `readout`, `legal_actions`, `apply_action`, `is_terminal`, `payoffs` and
`equity` must leave `random.getstate()` untouched — and two of them need a save/restore to manage it:
`apply_action`, because `pokerkit` draws while advancing (1–3 draws per hand from the reserved-card
shuffle of `platform.md` §4), and `equity`, because it samples (`stream.md` §1). Both wrap their work
in `saved = random.getstate()` / `try:` / `finally: random.setstate(saved)`. Three wrong shapes to
avoid: seeding per hand *inside* `apply_action` (a second seeding point, and the hand would re-deal
mid-play); leaving the stream advanced after a step or a query (the oracle asks at every decision, so
the deal stream would move mid-hand — the failure FAM-5.7 exists to catch); and restoring with a plain
trailing statement instead of `finally`, which leaks the stream whenever the library raises. Symptom:
two `new_hand(SAME_SEED)` calls followed by `random.random()` disagree, or an assertion on
`random.getstate()` after a step or a query fails.

## G5 — The 200-decision bound, and the hand that must end

Every hand must reach `is_terminal` within 200 applied actions — measured at 8 under always-check-or-call
and 12 under always-raise-if-legal in the default shape, at 8 and 2 in the no-cap row, and at 24 on the
six-seat shape under always-check-or-call, all far below (`platform.md` §1, `config.md` §6, `seats.md` §2). A property of the declared rows plus the automations, not something to
force; it is a *test* of the automations being complete. Symptom: a `while not is_terminal(hand)` loop in
`play_hand` spins because an un-automated operation (a missing `HAND_KILLING`, or an un-dealt board) stalls
the state. Do not add a decision cap to `play_hand` as a "safety": a hand that does not end is a defect to
report, not a loop to truncate — and a truncation would return a record whose payoffs are not the hand’s.

## G6 — Cost per hand (ASM-15), and why the equity sample dominates

`cost.md` G6 and G6.1 own this question — the band, the knobs and what is measured moved there
whole when this file reached its ceiling. The id stays as a safety net for a reference from outside
this tree, since no citation inside it needs the redirect (ASM-24).

## G7 — Refuse early, and refuse only what the contract refuses

Every refusal happens before the first side effect (`errors.md` §1, §4): before `random.seed`, before
the deep copy, before the policy is called. Do not add refusals the contract does not have — a seed
of 0 or a negative seed, `samples == 1`, an empty board, an extra key in a readout, a lambda policy.
A battery may pass any valid instance and a superfluous refusal turns a valid call into a failure.

## G8 — `play_hand` is a driver, not a guard

It calls the seat’s policy as `seating[readout["seat"][0]](readout, legal)`, applies what comes back, and
lets the policy’s own exception propagate (`episode.md` §1, §2). It does not retry, does not fall back to
`check-call`, does not inspect the signature, and does not catch `Exception` around the policy call. It
also does not call the policy for a hand that is over, and does not call `readout` on a terminal hand —
the loop condition is checked first (`readout` refuses a finished hand). The seating is a sequence of
callables and nothing else: it is not padded, truncated, re-ordered or inferred from the positional pair
(`seats.md` §4).

## G9 — The reward is the hand’s outcome, placed at each seat’s last decision

Every decision starts at reward 0; at the end, each seat’s last decision carries that seat’s net chip
delta and no other decision changes (`episode.md` §3, ASM-12). Two ways to get it wrong: shaping the
reward per decision, and awarding it to the seat’s *first* decision. A split deliberately leaves every
seat’s reward 0; a seat that never acted has no decision to carry one. `records.md` §5 is exact: at most
one non-zero reward per seat, equal to that seat’s payoff — one rule per seat, so a six-seat hand carries
at most six non-zero rewards (`seats.md` §3, ASM-43).

## G10 — Two facts `pokerkit` spells in a way that reads right and is wrong

Both were found by measuring, not by reading the received fact sheet (`platform.md` §2, §3):

- **the board** is `tuple(state.get_board_cards(0))`, never `state.board_cards[0]`. `board_cards` holds
  one row per *dealing operation*, so its row 0 is a single card on the flop: a build that reads it
  reports a one-card board where the contract requires three, and every board-length, street and
  equality assertion fails at once;
- **the street** is `STREETS[state.street_index]`, never `STREETS[state.streets.index(state.street)]`.
  The turn and river `Street` values are equal by value, so `.index()` answers 2 on the river too: the
  river would be reported as the turn and a five-card board would sit on the "turn".

The symptom in both cases is a hand that plays correctly and reports wrongly — which is why the
battery pairs the street name with the board length (`0 ⟺ preflop`, `3 ⟺ flop`, `4 ⟺ turn`,
`5 ⟺ river`) rather than checking either alone.

## G11 — Nothing below an entry point is surface

No battery may reach past the ten names, so the helper names in `layout.md` §1 are free to change;
but the ten names, their argument counts, their returns and their value types are not
(`layout.md` §2, `e2e-surface.md` §1). In particular do not add an eleventh module-level name to
`src/engine/__init__.py` for convenience — not `Hand`, not `EngineError`, not a vocabulary constant. A caller that
needs a seat index reads it out of `readout["seat"]`; a caller that needs the vocabulary reads it from
`features.action_space()`.

## G12 — A shape name is refused, never defaulted, and `None` is not a name

`require_shape` is the only place the shape question is answered: `None` returns `DEFAULT_SHAPE`, which is
absence, and any value the catalogue does not carry raises `UnknownShape` naming it and the declared names
(`config.md` §1, D-13). Do not fall back to the default on an unknown name — the silent substitution
`surface.md` §1 forbids, and it would play a 20-chip hand under a no-limit name — and do not let `None`
reach the handle. Symptom: `new_hand(seed, "no-limit-50")` deals a hand instead of raising, or
`legal_actions` finds no vocabulary because `_shape` was never canonicalised.

## G13 — The four bands are disjoint and total, and an empty band is masked out

The arithmetic is `sizing.md` §2's and must be exact: `raise-quarter` → `m + L//4`, legal iff `L//4 >= 1`;
`raise-half` → `m + L//2`, legal iff `L//2 > L//4`; `raise-all-in` → `A`, legal iff `A > m + L//2`;
`raise-minimum` → `m`, legal whenever a raise is (`actions.md` §2, `config.md` §5). A band with no legal
integer in it is **absent from `legal_actions`**, never collapsed onto a neighbour: at `L = 0` only
`raise-minimum` is legal, at `L = 1` only it and `raise-all-in`. Symptom: a build offers `raise-half` where
`L//2 == L//4`, so two descriptors resolve to one amount and the recorded amount names no single band.

## G14 — The fixed-limit path is byte-identical

Neither later shape may move the first: `game_config()` with no argument returns the same fifteen keys
and values, and a fixed-limit hand's deal, history entries, payoffs and episode record's five existing
facts are unchanged — the only change is the three keys added beside them (`episode.md` §3, `shapes.md`
§5). The six-seat row may not move the two-seat ones either: `seat_map(2)` and `blind_vector` at two
seats are the arguments this module always passed, and both two-seat first decisions still read `pot 3`,
`stacks == (19, 18)` and `(99, 98)`, `to_call == 1`, `seat == (0, True)` (`hand.md` §3–§4, `seats.md` §2).
Three ways to break it: threading an amount into the fixed-limit step, turning
`complete_bet_or_raise_to()` from a no-argument call into a one-argument one, and moving the row's
derivation inside `new_hand` **after** `random.seed` — where nothing fails today, because `shape_row`
re-canonicalises a name that is already canonical, but where the next helper that can refuse would move
the stream before refusing instead of after (`hand.md` §2, `errors.md` §1). Symptom: a `history`
entry, a `game_config()` key or a two-seat stack tuple differs.

## G15 — The index order is the shape's declaration, never a sort

`fold` 0, `check-call` 1, then the shape's raise descriptors in the declared order — the measured price
order, worst first, so the all-in sits **before** the minimum (`config.md` §6, `sizing.md` §3). A build must
not sort a legal set, must not re-order for readability, and must never derive an index from an amount.
Symptom: `features.legal_indices` lands a descriptor on the wrong head position, or a tie-break resolves
toward the cheapest band and manufactures a PASS (`sizing.md` §3, D-29).

## G16 — The multi-way equity range is one empty selection, `[[]]`, and never a bare `[]`

`calculate_equities` builds its selections with `product(*hole_ranges)` (`analysis.py:311`), so a **bare**
empty range contributes no selection at all: the product comes out empty, `choices(range(0), ...)` raises
`IndexError: range object index out of range` at `analysis.py:328`, and the call fails before a single
sample is drawn. The form the library's own `calculate_hand_strength` builds for its opponents is a range
holding **one empty combination** — `[[]]` — which `__calculate_equities_0` completes by dealing that
player's cards from the sampled deck (`analysis.py:404-406`, `:157-169`, `:225-337`). Measured on the
six-seat row: `[[[Kd, 2d]], [[]], [[]], [[]], [[]], [[]]]` returns six shares summing to 1.0 with the
acting seat's equal to `calculate_hand_strength(6, ...)`, while `[[[Kd, 2d]], [], [], [], [], []]` raises
that `IndexError` (`equity.md` §2.1, `seats.md` §2). Two ways to get it wrong: writing the bare `[]` per
opponent, which empties the product and raises, and extending the two-seat enumeration to five opponents,
which enumerates a product of five combinations before sampling once. `src/engine/equity.py` writes the
one-empty-range form; the two-seat path is untouched by either mistake — it enumerates the unseen two-card
combinations and is bit-identical to a direct call on that enumeration (`equity.md` §2.1, `shapes.md` §5).
