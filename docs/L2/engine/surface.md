# engine — the callable surface

- **Layer:** L2 · **Module:** `engine` · **Unit:** phase1 · **Rev:** 4 · **Date:** 2026-11-09
- **Owner of this file:** the surface — the ten module-level names of `src/engine/`, each with its argument contract, its return, its refusals and its ordering (D-12, `e2e-surface.md` §1)
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append

## 1. Rules that hold of every entry point

Each of the ten names is a module-level name of the `engine` package, and nothing below one of them
is contract (`e2e-surface.md` §1, brief §5). Six rules are shared and are stated here once (D-12, D-13):

- The ten names are fixed: L2 refines types, defaults and error classes and never adds, removes or renames an entry point (D-12, `e2e-surface.md` §1). A shape is reached through an **optional argument whose absence is today's value**, never through a new row: that is why the count went 9 → 10 by one name, `game_shapes`, and by no widening (`shapes.md` §4, D-29).
- An invalid argument is refused by raising an error that names the violated contract; no entry point coerces a value, substitutes a default, swallows an error or returns part of a record (`e2e-surface.md` §2). A shape name outside the catalogue is refused **naming it and the declared names**, never defaulted — absence is the default and a name is not (`shapes.md` §3, D-13).
- `new_hand` is the project's single seeding point, and `play_hand` deals through it instead of seeding again, so no call seeds the stream twice (ASM-2, `protocol.md` §4).
- Dealing is the only thing that moves a caller's draws: `new_hand` leaves the stream where its own deal left it, `play_hand` leaves it where the deal it made through `new_hand` left it, and every other entry point returns it in the state a caller gave it — `equity`, the one that must sample, included, and `apply_action` included even though `pokerkit` draws from the stream while it deals a street (ASM-2, `battery.md` §3 FAM-4, `strata/platform.md`).
- A hand handle is an opaque value a caller only passes back; a caller never inspects, serialises or compares one, and no record returned here exposes one (`e2e-surface.md` §1, D-1). A handle carries the name of the shape it was dealt from, so no entry point takes a shape beside a hand (`shapes.md` §3).
- No entry point mutates the hand it is given: a step returns an advanced handle and leaves its argument at its own state, because a caller keeps an earlier handle and queries it after the hand has moved on (`battery.md` §3 FAM-5, ASM-2).

A record returned here carries the keys `records.md` marks **required** and, beyond them, only this
module's own keys, which no caller may depend on (`records.md` §1, D-13).

## 2. The action descriptor

A descriptor is a value naming one of its shape's declared actions and it carries no amount
(`e2e-surface.md` §2, `shapes.md` §2). The default shape's vocabulary is `fold`, `check-call` and
`raise`, and its `raise` denotes the minimum legal completion for the decision it is applied to,
which fixed-limit makes unique (D-2, ASM-6); a shape without a cap declares the four raise
descriptors that partition the legal raise interval, and each resolves to its own band's maximum
(`sizing.md` §2–§3). Four consequences bind both sides of the edge (`e2e-surface.md` §2, D-3):

- descriptors compare by value and print stably, so two descriptors for one action at one decision are equal by value and by text, and a record holding one is comparable across two calls (D-2, `battery.md` §3 FAM-16);
- a descriptor is hand-independent, which is what lets `features.decode_action` build one from an index alone and `apply_action` accept it (`e2e-surface.md` §2, `battery.md` §3 FAM-2);
- a decision's descriptors hold at most one entry per vocabulary index, ordered as the hand's own shape declares them — `fold`, then `check/call`, then that shape's raise descriptors in its index order (`shapes.md` §2, `sizing.md` §3);
- fold appears only when `to_call` is non-zero, because folding where checking is free is not an action of that decision (`e2e-surface.md` §2, `battery.md` §3 FAM-16).

## 3. `game_config` — the declared shapes

- Takes a shape name, optionally, and returns that shape's parameters as one mapping: two seats, blinds 1 and 2, one blind level that never rises, the shape's starting stack, its bet sizes, its raise cap and its four streets — its `game` name says which game, and the bet **structure** is §12's row and never a key here (`e2e-surface.md` §3.1, `shapes.md` §2).
- Called with **no argument** it returns the default shape's row, which is byte for byte the mapping this entry point has always returned — stacks 20, a small bet of 2, a big bet of 4 and a raise cap of 4 (ASM-6, `shapes.md` §2, §5).
- A named shape returns the **same fifteen keys with the same value shapes**, differing only in the values that shape declares: the no-limit row states `no-limit texas hold'em`, stacks 100, and `None` for `small_bet`, `big_bet`, `limit` and `raise_cap`, because a shape with no fixed bet and no cap has neither (`shapes.md` §2, D-29).
- Its quantities are stated as numbers and not only as prose, because the report's header and the invariance family read them numerically (`protocol.md` §1, `battery.md` §3 FAM-2).
- Two calls with one argument return equal values and there is no per-call state — no seed, no hand, no rung — so a ladder on one shape has one game object for its whole length (D-2, D-3).
- Refuses a name outside `game_shapes`' catalogue, naming it and the declared names (`shapes.md` §3, D-13).

## 4. `new_hand` — deal one hand

- Takes a `seed`, an integer, and returns a hand handle: it seeds Python's global `random` with it and deals the hand, and it is the project's single seeding point (ASM-2, `protocol.md` §4).
- Takes the **shape** as an optional argument; absence is the default shape, so today's call deals today's hand and the deal is unchanged card for card (`shapes.md` §3, §5). A named shape deals that shape's state: for the no-limit row, blinds 1/2, starting stacks 100, no fixed bet and no cap (`shapes.md` §2).
- The same seed and the same shape deal the same hand, a different seed deals a different one, and a deal depends on its seed and shape and not on the hands dealt before it (ASM-2, `battery.md` §3 FAM-4).
- The whole deck order is fixed when the hand is created, because `pokerkit` shuffles at state creation; after that nothing a caller does can change which cards this hand gets, though the library's own dealing draws from the stream, which is why §1's fourth rule requires every later call to hand it back (`strata/platform.md`, ASM-2).
- Seat 0 holds the button and posts the small blind in every hand of every shape, so a caller alternates seats by swapping the two policies it hands to `play_hand` (`league.md` §3, D-16, `shapes.md` §2).
- Refuses a seed that is not an integer (`protocol.md` §2, ASM-2) and a shape name outside the catalogue, naming it and the declared names, both before the deal (`shapes.md` §3).

## 5. `readout` — the acting seat's facts

- Takes a non-terminal hand handle and returns the mapping of eleven facts declared in `environment.md` §2 (`e2e-surface.md` §2, D-3).
- Exactly those eleven keys and no others, in every shape: the information set is closed, and a fact outside it is a D-3 violation (`battery.md` §3 FAM-2, D-3). The two shapes share every **fact**; what changes is what the facts mean, never how many there are (`shapes.md` §2, §5).
- `hand_class` is the eleventh: `None` before the flop, where fewer than five cards are known, and from the flop onward an integer 0–8 naming the acting seat's best five-card hand of hole plus board — 0 high card through 8 straight flush. It is a **derived** fact of `hole` and `board`, which the readout already carries, so it widens no information set, and no encoding carries it (`environment.md` §2, ASM-30, D-21).
- The legal raise bounds are **not** a twelfth fact: they are the episode record's `minimum` and `maximum` (`records.md` §5, `sizing.md` §2, §10 below).
- Refuses a hand that is over, because a hand with no acting seat has no readout (`e2e-surface.md` §2).
- Deterministic and hermetic: one hand at one state reads one mapping, and reading draws no randomness (ASM-2, `battery.md` §3 FAM-4).

## 6. `legal_actions` — what the acting seat may do

- Takes a non-terminal hand handle and returns an ordered, indexable sequence of at least one descriptor (`e2e-surface.md` §2, `battery.md` §3 FAM-1).
- The order is the **hand's own shape's** index order — §2's — and the sequence is the same in value and order as `readout`'s `legal` fact for that hand (`e2e-surface.md` §2, `sizing.md` §3).
- A raise descriptor appears only when its band holds a legal amount: a band with no legal integer in it is **masked out, never collapsed onto its neighbour**, so a decision may offer one raise descriptor and not the other three (`sizing.md` §2).
- Refuses a hand that is over, where nothing is legal and nobody acts (`e2e-surface.md` §2).
- Deterministic and free of randomness: two calls on one hand return equal sequences (ASM-2).

## 7. `apply_action` — advance by one chosen action

- Takes a hand handle and a descriptor, and returns the advanced hand as a new handle, leaving its argument at its own state (rule 6 of §1, `battery.md` §3 FAM-5).
- Refuses a descriptor that its hand's shape does not declare, and one that is not in `legal_actions` for that hand: an illegal action is a contract violation and never a fold or a call on the violator's behalf (D-2, `e2e-surface.md` §2).
- A raise descriptor is resolved by the engine to an amount and nowhere else: the fixed-limit `raise` to the minimum legal completion, and a sized descriptor to the maximum of its own band (`sizing.md` §2, §10).
- Refuses a hand that is over, and hands the global stream back as it found it — restoring whatever the library drew from it while the step dealt a street — because the deck was fixed when the hand was created (ASM-2, `strata/platform.md`, §1 rule 4).
- One applied action appends exactly one entry to the hand's public `history`, whatever the action (`e2e-surface.md` §2, `battery.md` §3 FAM-16).
- Applying the last action of a hand returns a handle for which `is_terminal` is true (`battery.md` §3 FAM-16).

## 8. `is_terminal` — is the hand over

- Takes a hand handle and returns a boolean, not a truthy object (`e2e-surface.md` §3.1, `battery.md` §3 FAM-1).
- A freshly dealt hand is not terminal, and every hand ends: the stack, the shape's raise cap and its no-cap bound each bound it, and a hand that has not ended after 200 decisions is a defect (`battery.md` §3 FAM-16, ASM-6, `shapes.md` §2).
- Pure: it needs no randomness, mutates nothing and leaves the global stream as it found it (ASM-2).
- Refuses only a value that is not a hand handle: every handle states whether it is over, a freshly dealt one included (`e2e-surface.md` §2).

## 9. `payoffs` — what the hand paid

- Takes a completed hand handle and returns the net chip delta per seat: exactly one number per seat and nothing else numeric, and the numbers sum to zero (`e2e-surface.md` §3.1, `battery.md` §3 FAM-16).
- The record is keyed by seat and carries no total, because a second number in it would no longer be a per-seat payoff (ASM-12, `battery.md` §3 FAM-16).
- Refuses a hand that is still running: a running hand has paid nothing (`e2e-surface.md` §3.1).
- Deterministic: the payoffs are a function of the completed hand alone (ASM-12, ASM-2).

## 10. `play_hand` — one whole episode

- Takes a seed and the two policies — seat 0's then seat 1's — and the **shape** optionally, and returns an episode record (`records.md` §5): it deals the hand through `new_hand` at that seed and shape and drives it to its end, so one seed deals one hand however that hand is played (`e2e-surface.md` §3.1, ASM-2, `shapes.md` §3).
- It calls the acting seat's policy as the policy protocol states — with the readout and the legal descriptors — and applies the descriptor the policy returns (`e2e-surface.md` §2, D-2).
- Every decision carries the legal raise interval's `minimum` and `maximum` — `None` exactly when no raise was legal — and `amount`, the raise-to the engine resolved, `None` whenever the chosen descriptor is not a raise (`records.md` §5, `sizing.md` §2).
- Refuses a policy that is not callable, a policy whose answer is outside `legal_actions`, and a shape name outside the catalogue naming it and the declared names (D-2, D-13, `shapes.md` §3).
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

## 12. `game_shapes` — the declared shapes

- Takes no argument and returns the declared shapes as an **ordered mapping, default first** — the catalogue itself, so no caller can invent a shape through this surface and the row is `fixed` (`shapes.md` §2, `e2e-surface.md` §5, D-29).
- Each row is a mapping carrying `name`, `default`, `seats`, `blinds`, `starting_stack`, `chips_in_play`, `bet_structure`, `small_bet`/`big_bet`/`raise_cap` (`None` for a shape without a cap), `actions` — the vocabulary's descriptor names in that shape's index order — `head_width`, its descriptor count, and `normalisers`, one divisor per key (`shapes.md` §2, `sizing.md` §3, §5, §6).
- `fixed-limit-20` is the first row and the default: seats 2, blinds (1, 2), stack 20, 40 chips in play, fixed bets 2 and 4, cap 4, three descriptors, head width 3 and normalisers `stack` 20, `pot` 40, `to_call` 20, `amount` 4, `count` 4 (ASM-6, `shapes.md` §2).
- `no-limit-100` is the second: the same seats and blinds, stack 100, 200 chips in play, no fixed bet and no cap, six descriptors in the declared index order, head width 6 and normalisers `stack` 100, `pot` 200, `to_call` 100, `amount` 100, `count` 50 (`shapes.md` §2, `sizing.md` §3, §5).
- The chips in play are the row's own total, so `pot + sum(stacks)` is 40 in the default shape and the row's total in any other (`shapes.md` §2, `environment.md` §1).
- Two calls return equal values and the returned mapping is fresh, so a caller's edit of a row cannot reach the catalogue; it refuses nothing, because it takes no argument (`surface.md` §1, D-13).
