# engine — L4 guardrails

- **Owner:** one note per risk this design identified, in the order they bite, each with the rule L4 must hold and the symptom of getting it wrong
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
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

## G2 — The seat map: `pokerkit`’s heads-up blinds are reversed, twice

`create_state(..., raw_blinds_or_straddles=(1, 2), ..., player_count=2)` makes **pokerkit player 0**
post the 2 and **player 1** post the 1, and `_begin_betting` reverses the blinds again for the
pre-flop opener (`state.py:3336-3339`, `4203-4212`). So the engine’s seat 0 — the button, post 1, act
first pre-flop, act second afterwards — is pokerkit’s index **1**, and the translation is
`SEAT_TO_PLAYER = (1, 0)` (`hand.md` §3). Two wrong fixes that look right and are not: passing
`(2, 1)` to `create_state` (the library reverses an already-reversed pair and the button moves back
to where you started), and sorting the stacks (chips are per seat, not ascending). Symptom of getting
it wrong: the first decision reads `stacks == (18, 19)` or `seat == (1, False)`, `payoffs` is keyed
by the wrong seat, and every per-seat fact in the project is mirrored.

## G3 — The one spelling: a card is a two-character `str`, an action is one of three `str`s

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

Every hand must reach `is_terminal` within 200 applied actions — measured at 8 under
always-check-or-call and 12 under always-raise-if-legal, far below (`platform.md` §1). A property of
the fixed game plus the automations, not something to force; it is a *test* of the automations being
complete. Symptom: a `while not is_terminal(hand)` loop in `play_hand` spins because an un-automated
operation (a missing `HAND_KILLING`, or an un-dealt board) stalls the state. Do not add a decision cap
to `play_hand` as a "safety": a hand that does not end is a defect to report, not a loop to truncate —
and a truncation would return a record whose payoffs are not the hand’s.

## G6 — Cost per hand (ASM-15), and why the equity sample dominates

ASM-15 states the per-hand cost as a measurement in ASM-21’s 0.105–0.153 s band, never a bound. The
engine’s own per-decision cost is a `deepcopy` of the state plus one predicate-and-method call, paid
8 to 12 times a hand. The one call in this module that can exceed the whole band on its own is
`equity`: it is asked once per decision by the oracle, and its cost is linear in `sample_count` and
in the size of the opponent range (1225 combinations pre-flop, 1081 on the flop, 1035 on the turn,
990 on the river). So the sample count is the one knob that decides whether a cell fits ASM-21’s band
— and it is `agents`’ parameter, not this module’s. The engine must not "fix" the cost by caching an
estimate, by reducing `samples` itself or by rounding the number: a cache would make `equity`
no longer a function of its arguments, and the other two would report a question nobody asked.

### G6.1 What is measured, and what is not

Measured: the decision counts above, and `pokerkit`’s `calculate_equities` repeating bit-exactly under
a fixed seed inside [0, 1] (`platform.md` §1, §5). **Not** measured here: per-call wall clock. ASM-15
states the per-hand cost as a measurement in ASM-21’s band, not a bound, and `harness.timings` is the
module that reports it (`e2e-surface.md` §3.6, FAM-10); a case reads `seconds_per_hand` and never
asserts a bound, and this design records no millisecond figure it did not observe (`battery.md` §2).

## G7 — Refuse early, and refuse only what the contract refuses

Every refusal happens before the first side effect (`errors.md` §1, §4): before `random.seed`, before
the deep copy, before the policy is called. Do not add refusals the contract does not have — a seed
of 0 or a negative seed, `samples == 1`, an empty board, an extra key in a readout, a lambda policy.
A battery may pass any valid instance and a superfluous refusal turns a valid call into a failure.

## G8 — `play_hand` is a driver, not a guard

It calls the seat’s policy as `policy(readout, legal)`, applies what comes back, and lets the policy’s
own exception propagate (`episode.md` §1). It does not retry, does not fall back to `check-call`, does
not inspect the signature, and does not catch `Exception` around the policy call. It also does not
call the policy for a hand that is over, and does not call `readout` on a terminal hand — the loop
condition is checked first (`readout` refuses a finished hand).

## G9 — The reward is the hand’s outcome, placed at each seat’s last decision

Every decision starts at reward 0; at the end, each seat’s last decision carries that seat’s net chip
delta and no other decision changes (`episode.md` §3, ASM-12). Two ways to get it wrong: shaping the
reward per decision, and awarding it to the seat’s *first* decision. A split deliberately leaves both
rewards 0; a seat that never acted has no decision to carry one. `records.md` §5 is exact: at most one
non-zero reward per seat, equal to that seat’s payoff.

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

No battery may reach past the nine names, so the helper names in `layout.md` §1 are free to change;
but the nine names, their argument counts, their returns and their value types are not
(`layout.md` §2, `e2e-surface.md` §1). In particular do not add a tenth module-level name to
`src/engine/__init__.py` for convenience — not `Hand`, not `EngineError`, not `ACTIONS`. A caller that
needs a seat index reads it out of `readout["seat"]`; a caller that needs the vocabulary reads it from
`features.action_space()`.
