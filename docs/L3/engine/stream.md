# engine — the global `random` stream

- **Owner:** the seeding rule of the whole project as this module holds it — one seeding point, the two save/seed/restore sites, and what the measured cost implies for ASM-15
- **Ceiling:** 70 lines. At the ceiling, split by owner — never append

## 1. The rule

`new_hand` calls `random.seed(seed)` and creates the state, and it is the **only** place in this
project that seeds the stream (`hand.md` §2, ASM-2, `protocol.md` §4). `play_hand` deals through it and
seeds nothing itself, so `play_hand`’s effect on the stream is exactly `new_hand`’s.

Every other entry point — `game_config`, `readout`, `legal_actions`, `apply_action`, `is_terminal`,
`payoffs`, `equity` — hands `random.getstate()` back exactly as it found it. Two of them need work to
do it, and both wrap their work in the same three lines:

    saved = random.getstate()
    try:
        <the operation>
    finally:
        random.setstate(saved)

- **`apply_action`** needs it because `pokerkit` draws while advancing: `_begin_dealing` evaluates
  `get_dealable_cards(None, False)` on every street transition, and that path runs
  `shuffled(self.reserved_cards)` just to obtain a length (`state.py:2406-2411`, `3546-3593`) —
  measured at 1 to 3 draws per hand (`platform.md` §4). The deal is unaffected (the board comes from
  the deck order fixed at creation), but the caller’s stream is not, so the restore is what makes
  "`apply_action` draws no randomness" (`L2 surface.md` §7) true rather than nearly true
  (`advance.md` §1).
- **`equity`** needs it because it must sample, and `pokerkit`’s `calculate_equities` draws from
  Python’s **global** `random` with no generator argument (`from random import choices, sample`,
  `analysis.py:22,163,328`). It saves, seeds with the caller’s seed, computes, restores
  (`equity.md` §3).

**Seed before, restore after**, because together they buy the two properties the contract states and
neither does alone: the *seed* makes the estimate a function of `(decision, seed, samples)` and of
nothing else, so two calls agree to the last bit (FAM-16.8) — unseeded, the oracle’s pot-odds decision
would not be reproducible and a run’s record would be a lie; the *restore*, in a `finally`, keeps
`new_hand` the only thing that moves the deal stream, even when the sample raises. Without it, the
oracle calling `equity` at every decision of a live hand would advance the stream mid-hand — the exact
failure FAM-5.7 is built to catch (`L2 surface.md` §1, `L2 environment.md` §4).

The restore is a `finally`, never a plain trailing statement: a library `ValueError` must not leave the
stream advanced, and a caller must be able to retry after a refusal.

## 2. What is rejected, and why

- **A private `random.Random(seed)` instance.** `calculate_equities` would not use it — it calls the
  module-level functions — so the estimate would still be drawn from the global stream and would still
  have to be saved and restored; the instance would be decoration, not isolation.
- **Patching `random` or the library’s names for the duration of a call.** It would make engine
  behaviour depend on import order and on which module imported `pokerkit.analysis` first, and it would
  re-enter under a threaded caller — D-13 and D-16 both forbid it.
- **Seeding per hand inside `apply_action`, or "re-seeding to be safe" after a sample.** A second
  seeding point is exactly what ASM-2 forbids, and it would re-deal a hand in flight.
- **Leaving the stream advanced after a query and letting callers reseed.** Then every caller would
  have to know the engine’s sampling internals, and the deal would depend on how many questions were
  asked — the failure mode the `random.getstate()` assertions exist for.

## 3. Cost (ASM-15)

Per decision the engine pays one `deepcopy` and one predicate-and-method pair; per hand it pays 8 to 12
of those (measured under always-check-or-call and always-raise-if-legal, `platform.md` §1). The one
call whose cost is not negligible is `equity`: it is asked once per decision by the oracle, it is
linear in `samples`, and its opponent range is 1225 combinations pre-flop, 1081 on the flop, 1035 on
the turn and 990 on the river. ASM-15 states the per-hand cost as a measurement in ASM-21’s band,
never a bound, and gives `harness.timings` the measuring job; what this design must not do is hide the
question — so it fixes no sample count, caches no estimate, and rounds no number. The sample count is
`agents`’ parameter (`guardrails.md` G6).
