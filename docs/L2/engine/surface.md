# engine — the callable surface

- **Layer:** L2 · **Module:** `engine` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-05
- **Owner of this file:** the surface — the nine module-level names of `src/engine/`, each with its argument contract, its return, its refusals and its ordering (D-12, `e2e-surface.md` §1)
- **Ceiling:** 110 lines. At the ceiling, split by owner — never append

## 1. Rules that hold of every entry point

Each of the nine names is a module-level name of the `engine` package, and nothing below one of them
is contract (`e2e-surface.md` §1, brief §5). Six rules are shared and are stated here once (D-12, D-13):

- The nine names are fixed: L2 refines types, defaults and error classes and never adds, removes or renames an entry point (D-12, `e2e-surface.md` §1).
- An invalid argument is refused by raising an error that names the violated contract; no entry point coerces a value, substitutes a default, swallows an error or returns part of a record (`e2e-surface.md` §2).
- `new_hand` is the project's single seeding point, and `play_hand` deals through it instead of seeding again, so no call seeds the stream twice (ASM-2, `protocol.md` §4).
- Dealing is the only thing that moves a caller's draws: `new_hand` leaves the stream where its own deal left it, `play_hand` leaves it where the deal it made through `new_hand` left it, and every other entry point returns it in the state a caller gave it — `equity`, the one that must sample, included, and `apply_action` included even though `pokerkit` draws from the stream while it deals a street (ASM-2, `battery.md` §3 FAM-4, `strata/platform.md`).
- A hand handle is an opaque value a caller only passes back; a caller never inspects, serialises or compares one, and no record returned here exposes one (`e2e-surface.md` §1, D-1).
- No entry point mutates the hand it is given: a step returns an advanced handle and leaves its argument at its own state, because a caller keeps an earlier handle and queries it after the hand has moved on (`battery.md` §3 FAM-5, ASM-2).

A record returned here carries the keys `records.md` marks **required** and, beyond them, only this
module's own keys, which no caller may depend on (`records.md` §1, D-13).

## 2. The action descriptor

A descriptor is a value naming one of the three vocabulary actions — fold, check/call and raise — and
it carries no amount: the raise descriptor denotes the minimum legal completion for the decision it
is applied to, which fixed-limit makes unique (`e2e-surface.md` §2, D-2). Four consequences bind both
sides of the edge (`e2e-surface.md` §2, D-3):

- descriptors compare by value and print stably, so two descriptors for one action at one decision are equal by value and by text, and a record holding one is comparable across two calls (D-2, `battery.md` §3 FAM-16);
- a descriptor is hand-independent, which is what lets `features.decode_action` build one from an index alone and `apply_action` accept it (`e2e-surface.md` §2, `battery.md` §3 FAM-2);
- a decision's descriptors hold at most one entry per vocabulary index, ordered as the vocabulary is: fold, then check/call, then raise (`e2e-surface.md` §2);
- fold appears only when `to_call` is non-zero, because folding where checking is free is not an action of that decision (`e2e-surface.md` §2, `battery.md` §3 FAM-16).

## 3. `game_config` — the fixed game

- Takes no argument and returns the game's parameters as one mapping: two seats, blinds 1 and 2, one blind level that never rises, starting stacks 20 chips, a small bet of 2, a big bet of 4 and a raise cap of 4 on a street (`e2e-surface.md` §3.1, ASM-6).
- Its quantities are stated as numbers and not only as prose, because the report's header and the invariance family read them numerically (`protocol.md` §1, `battery.md` §3 FAM-2).
- Two calls return equal values and there is no per-call state — no seed, no hand, no rung — so the ladder has one game object for its whole length (D-2, D-3).
- Refuses nothing: it has no argument, and there is no parameter by which the game can be varied (D-2, `e2e-surface.md` §3.1).

## 4. `new_hand` — deal one hand

- Takes a `seed`, an integer, and returns a hand handle: it seeds Python's global `random` with it and deals the hand, and it is the project's single seeding point (ASM-2, `protocol.md` §4).
- The same seed deals the same hand, a different seed deals a different one, and a deal depends on its seed and not on the hands dealt before it (ASM-2, `battery.md` §3 FAM-4).
- The whole deck order is fixed when the hand is created, because `pokerkit` shuffles at state creation; after that nothing a caller does can change which cards this hand gets, though the library's own dealing draws from the stream, which is why §1's fourth rule requires every later call to hand it back (`strata/platform.md`, ASM-2).
- Seat 0 holds the button and posts the small blind in every hand, so a caller alternates seats by swapping the two policies it hands to `play_hand` (`league.md` §3, D-16).
- Refuses a seed that is not an integer: the seed set this project records is integer (`protocol.md` §2, ASM-2).

## 5. `readout` — the acting seat's facts

- Takes a non-terminal hand handle and returns the mapping of ten facts declared in `environment.md` §2 (`e2e-surface.md` §2, D-3).
- Exactly those ten keys and no others: the information set is closed, and a fact outside it is a D-3 violation (`battery.md` §3 FAM-2, D-3).
- Refuses a hand that is over, because a hand with no acting seat has no readout (`e2e-surface.md` §2).
- Deterministic and hermetic: one hand at one state reads one mapping, and reading draws no randomness (ASM-2, `battery.md` §3 FAM-4).

## 6. `legal_actions` — what the acting seat may do

- Takes a non-terminal hand handle and returns an ordered, indexable sequence of at least one descriptor (`e2e-surface.md` §2, `battery.md` §3 FAM-1).
- The order is §2's — fold, check/call, raise — and the sequence is the same in value and order as `readout`'s `legal` fact for that hand (`e2e-surface.md` §2).
- Refuses a hand that is over, where nothing is legal and nobody acts (`e2e-surface.md` §2).
- Deterministic and free of randomness: two calls on one hand return equal sequences (ASM-2).

## 7. `apply_action` — advance by one chosen action

- Takes a hand handle and a descriptor, and returns the advanced hand as a new handle, leaving its argument at its own state (rule 6 of §1, `battery.md` §3 FAM-5).
- Refuses a descriptor that is not one of `legal_actions` for that hand: an illegal action is a contract violation and never a fold or a call on the violator's behalf (D-2, `e2e-surface.md` §2).
- Refuses a hand that is over, and hands the global stream back as it found it — restoring whatever the library drew from it while the step dealt a street — because the deck was fixed when the hand was created (ASM-2, `strata/platform.md`, §1 rule 4).
- One applied action appends exactly one entry to the hand's public `history`, whatever the action (`e2e-surface.md` §2, `battery.md` §3 FAM-16).
- Applying the last action of a hand returns a handle for which `is_terminal` is true (`battery.md` §3 FAM-16).

## 8. `is_terminal` — is the hand over

- Takes a hand handle and returns a boolean, not a truthy object (`e2e-surface.md` §3.1, `battery.md` §3 FAM-1).
- A freshly dealt hand is not terminal, and every hand ends: short stacks and the raise cap bound it, and a hand that has not ended after 200 decisions is a defect (`battery.md` §3 FAM-16, ASM-6).
- Pure: it needs no randomness, mutates nothing and leaves the global stream as it found it (ASM-2).
- Refuses only a value that is not a hand handle: every handle states whether it is over, a freshly dealt one included (`e2e-surface.md` §2).

## 9. `payoffs` — what the hand paid

- Takes a completed hand handle and returns the net chip delta per seat: exactly one number per seat and nothing else numeric, and the numbers sum to zero (`e2e-surface.md` §3.1, `battery.md` §3 FAM-16).
- The record is keyed by seat and carries no total, because a second number in it would no longer be a per-seat payoff (ASM-12, `battery.md` §3 FAM-16).
- Refuses a hand that is still running: a running hand has paid nothing (`e2e-surface.md` §3.1).
- Deterministic: the payoffs are a function of the completed hand alone (ASM-12, ASM-2).

## 10. `play_hand` — one whole episode

- Takes a seed and the two policies — seat 0's then seat 1's — and returns an episode record (`records.md` §5): it deals the hand through `new_hand` at that seed and drives it to its end, so one seed deals one hand however that hand is played (`e2e-surface.md` §3.1, ASM-2).
- It calls the acting seat's policy as the policy protocol states — with the readout and the legal descriptors — and applies the descriptor the policy returns (`e2e-surface.md` §2, D-2).
- Refuses a policy that is not callable, and a policy whose answer is outside `legal_actions`: a contract violation is never a fold (D-2, `e2e-surface.md` §2).
- It does not catch a policy's own exception and turn it into an action (`e2e-surface.md` §2, D-2).
- One seed and one pair of policies give one record; a different seed gives a different one (ASM-2, `battery.md` §3 FAM-4).
- The record's shape, its decisions and its rewards are `environment.md` §3's, and it names no hand handle because nothing below an entry point is surface (`e2e-surface.md` §1, brief §5).

## 11. `equity` — the oracle's question

- Takes the decision in question, a seed and a sample count, and returns the acting seat's win probability against a uniformly random opponent hand, from `pokerkit`'s equity calculation, as a number in [0, 1] (ASM-4, `e2e-surface.md` §3.1).
- Its first argument is a hand handle **or** that hand's readout: both denote the same decision and return the same number, because the readout already carries the acting seat's cards and the board (`environment.md` §2, ASM-4).
- A mapping is a decision only when it carries two distinct cards under `hole` and 0, 3, 4 or 5 distinct cards under `board`; any other mapping is refused rather than sampled, and a fact beyond those two is ignored, so a hand and its own readout are the two shapes that answer (`environment.md` §2, `e2e-surface.md` §2).
- Refuses a decision that is over, a seed that is not an integer, and a sample count that is not a positive integer (`e2e-surface.md` §2, ASM-4).
- One decision, seed and sample count give one estimate, and a coarse sample count is a legal call and not an error (`battery.md` §3 FAM-16, ASM-4).
- It is a query and not a step: it neither advances nor mutates the hand, it hands the global stream back in the state it found, and its estimate is a function of the decision, its seed and the sample count and of nothing else — which is what makes it repeatable and what keeps the deal out of an equity question (ASM-2, ASM-4).
