# engine — the environment, and the contracts at its edge

- **Layer:** L2 · **Module:** `engine` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-05
- **Owner of this file:** the environment — one hand's life and the facts it exposes (§1–§4) — and the contracts this module's four callers hold at its edge (§5–§6), with the battery invariants this module carries (§7) (D-2, D-3, D-13)
- **Ceiling:** 130 lines. At the ceiling, split by owner — never append

## 1. A hand's life: dealt, advanced, ended, paid

- **Dealt.** `new_hand` seeds the global `random` and creates the state, and `pokerkit` shuffles the deck at state creation, so the hand's whole card order is fixed in that call (ASM-2, `strata/platform.md`).
- **Seated.** Seat 0 holds the button and posts the small blind of 1; seat 1 posts the big blind of 2; seat 0 acts first preflop and seat 1 acts first on the flop, the turn and the river (D-2, ASM-6).
- **Opened.** At the first decision the street is preflop, the pot holds the two blinds, the stacks hold 19 and 18 chips behind, and the button owes the big blind one chip (ASM-6, `battery.md` §3 FAM-2).
- **Conserved.** The facts partition the table's chips: at every decision `pot` plus the two `stacks` is the 40 chips the hand began with, because committed chips sit in `pot` and never in a stack (`e2e-surface.md` §2, ASM-6).
- **Advanced.** A decision is one acting seat with one legal set; applying a descriptor appends one public action and may close a street, which reveals the next public cards, so successive decisions read a board of 0, 3, 4 or 5 cards and one street may follow another immediately once no seat can act for more (D-2, `e2e-surface.md` §2).
- **Ended.** A hand ends when a seat folds, or at showdown — which comes when the last street's betting closes, or sooner when no seat can act for more because a stack is committed — and from then on `is_terminal` is true and no seat is acting (D-2, ASM-1, ASM-6).
- **Paid.** The payoff is a seat's net chip delta over the hand, the two sum to zero, and a tied hand splits the pot — ties and splits are common at these stacks, so a payoff may be zero (ASM-12, `protocol.md` §2).
- **Stateless.** The whole state of a hand lives in its handle and no state survives a call, so two handles are independent and a hand dealt earlier is unaffected by a hand dealt later (ASM-2, `e2e-surface.md` §1).

## 2. `readout` — D-3's information set

The readout is a function of the hand alone: it takes no rung, encoder, learner, opponent or seed, so
what an agent may know cannot differ between rungs (D-3, `e2e-surface.md` §2). It holds exactly these
ten keys (D-3, `battery.md` §3 FAM-2):

| Key | Content, and the shape a caller may rely on |
|---|---|
| `street` | one of `preflop`, `flop`, `turn`, `river` — those four strings and no others (`battery.md` §3 FAM-2) |
| `seat` | the acting seat: its index, 0 or 1, as the fact's first number, and a boolean saying whether it holds the button (`e2e-surface.md` §2, `battery.md` §3 FAM-16) |
| `hole` | the acting seat's two cards (`e2e-surface.md` §2, `battery.md` §3 FAM-16) |
| `board` | 0, 3, 4 or 5 public cards (`e2e-surface.md` §2, ASM-6) |
| `stacks` | one number per seat in seat order: the chips that seat holds behind (`e2e-surface.md` §2, `battery.md` §3 FAM-2) |
| `pot` | one number: the chips both seats have committed, the current street's bets included (`e2e-surface.md` §2, `battery.md` §3 FAM-2) |
| `to_call` | one number: the chips the acting seat must add to continue, 0 when it may check for nothing, and never more than its own stack, which bounds a call for less (`e2e-surface.md` §2, `battery.md` §3 FAM-16) |
| `limit` | the fixed bet size in force and the raises made so far on this street; a posted blind is not a raise, so a street's first decision reads none made, and a caller reads the bet size numerically (2 on the preflop and the flop, 4 on the turn and the river) (`e2e-surface.md` §2, ASM-6) |
| `history` | a list of this hand's public actions, one per applied action, printing stably so two records of one deal compare, and empty — the empty list — before the first one (`e2e-surface.md` §2, `battery.md` §3 FAM-16) |
| `legal` | the ordered descriptors `legal_actions` returns for the same hand, in the same order (`e2e-surface.md` §2) |

A card is a value that names a rank and a suit, compares by value and prints stably; one spelling is
used in `hole`, in `board` and in `history`, and which spelling that is is L3's (D-1, `e2e-surface.md` §2).

The readout never carries a fact outside those ten, and in particular never does the following
(D-3, `battery.md` §3 FAM-2):

- never the non-acting seat's hole cards, in any form (`e2e-surface.md` §2, D-3);
- never the undealt deck, its order, or a board card the hand has not yet revealed (D-3, `e2e-surface.md` §2);
- never a rung, an encoding, a learner, an opponent, a seed or an episode count, because the information set is the same for every rung (D-3, `ladder.md` §4);
- never an eleventh key, since the set of facts is closed and the invariance family compares it exactly (D-3, `battery.md` §3 FAM-2).

## 3. `play_hand` — the episode record

`records.md` §5 fixes the record, and this module returns exactly that shape (`records.md` §1, §5):

| Key | Content |
|---|---|
| `seed` | **required** — the seed the call was made with, unchanged (`records.md` §5, ASM-2) |
| `decisions` | **required** — the ordered decisions, one entry per decision in the order they were taken (`records.md` §5) |
| `payoffs` | **required** — net chips per seat summing to zero, the same record `payoffs` returns for that completed hand (`records.md` §5, ASM-12) |

Each decision carries the five facts `records.md` §5 requires, and this module states what each of
them is at the edge (`records.md` §5, `battery.md` §3 FAM-16):

- `seat`, the decision's own acting seat, in the shape of §2's `seat` fact;
- `readout`, the whole ten-fact mapping of §2 for that decision, so an encoder can encode a decision after the hand is over (D-3, `records.md` §5);
- `legal`, that decision's ordered descriptor list, and `action`, the descriptor the policy returned and the engine applied (`e2e-surface.md` §2);
- `reward`, the seat's net chip delta for the completed hand at that seat's last decision, and zero at every other decision (ASM-12, `records.md` §5).

A seat that never acted — the big blind when the button folds preflop — carries no decision and
therefore no reward; the reward is the hand's outcome and never a shaped per-decision term
(ASM-12, `records.md` §5). The episode is a record of what happened and is not re-opened: a caller
that wants the hand advanced further plays it through `new_hand` and `apply_action` instead
(`e2e-surface.md` §1, `module-map.md` §3).

## 4. `equity` — how the oracle's question is answered

- The question is conditional on what the acting seat can see: if the opponent's two cards were a uniform draw from the cards this seat has not seen, what share of the pot does it win on average (ASM-4, `protocol.md` §3).
- That is why the answer needs only the acting seat's `hole`, the `board` and the unseen deck, and why the same question can be asked from a readout as from a hand (ASM-4, `e2e-surface.md` §2).
- The answer is a share of the pot and not a win-or-lose flag: a split counts as its share, which is what lets the oracle compare it with `to_call / (pot + to_call)` (ASM-6, `protocol.md` §3).
- It is an estimate over the caller's sample count, seeded so that it repeats, and the oracle asks it at every decision of a hand it is playing (ASM-4, `battery.md` §3 FAM-16).
- Because the oracle asks it mid-hand and `play_hand` then applies the returned action to that same hand, the query must leave both the hand and the deal stream exactly as it found them (ASM-4, ASM-2).

## 5. Seeding and the sequential rule

- One global stream deals every hand: `pokerkit` shuffles with Python's `random` and takes no seed, so `new_hand` is the one point at which the deal stream is set, `play_hand` deals through it, and no other module sets it (ASM-2, `protocol.md` §4).
- Therefore hands are played one at a time. A cell is played hand after hand, and two cells are never interleaved or threaded; sequential play is a contract and not an implementation choice (D-16, `protocol.md` §4).
- Because each hand is seeded, a cell's hands are reproducible from the cell's seed, and a cell does not depend on what was played between two of its own runs (`battery.md` §3 FAM-7, ASM-2).
- The engine remembers no seed and reuses none: a caller that wants reproducibility passes the seed it records, and a run is reproducible from its configuration, seed set, budget and pool membership (`protocol.md` §2, `protocol.md` §4).
- There is no way to share, fork or thread a deal, so cost is bought with cell size and never with parallelism (D-16, `league.md` §3).

## 6. The contracts at this edge (D-13)

Each caller's obligation is stated as what it may rely on from this module, not as a description of
its internals (`module-map.md` §2, D-13):

- `features` encodes a readout and nothing else, so the readout is self-contained: an encoder that needed the hand could not be written against §2 (D-3, `e2e-surface.md` §2).
- `features.observation_spec`'s `fields` is a subset of §2's ten names, so those names are the edge's shared vocabulary and may be neither renamed nor extended (D-3, `battery.md` §3 FAM-2).
- `features.legal_indices` maps this module's descriptor sequence to indices position by position, and `features.decode_action` returns a descriptor `apply_action` accepts, which is why a descriptor is hand-independent and compares by value (`e2e-surface.md` §2, D-2).
- `agents.as_policy`, `agents.build_baseline`, `evaluation.policy_from` and `harness.seam` all return a callable taking the readout and the legal descriptors and returning one member of that list; `play_hand` accepts that protocol and knows none of those builders by name (`e2e-surface.md` §2, D-13).
- The oracle baseline reads `pot` and `to_call` from the readout and asks `equity` with the readout it was handed, which is why `equity` accepts one (ASM-4, `protocol.md` §3).
- `evaluation.match` plays a cell through `new_hand` and `play_hand` one hand at a time, alternates seats by swapping the two policies, and reads `payoffs` for the chip deltas; the cell, its hand count, its seat split and its opponent are `evaluation`'s and never this module's (D-16, `league.md` §3).
- `training.run` draws each training hand's deal and its opponent's play the same way, so a run's data is a sequence of `play_hand` calls at the run's own seeds (D-16, `module-map.md` §2).

## 7. The invariants the battery asserts against this module

The families of `battery.md` §3 that land on `engine` are asserted at the observable edge, and each
one is carried by the entry points named beside it — this table is what an implementer reads to see
what FAM-1, FAM-2, FAM-4 and FAM-16 require of this module (`battery.md` §3, D-11):

| Family | What it asserts | Carried by |
|---|---|---|
| FAM-1 | the nine names exist, are callable, and a minimal call returns the declared kind | all nine (`e2e-surface.md` §3.1, `battery.md` §3) |
| FAM-2 | the game is one deterministic declaration; a first decision reads preflop with a pot of 3, stacks summing to 37 and a call of 1; the readout holds exactly the ten facts; every legal descriptor has one index and `decode_action`'s descriptor is accepted | `game_config`, `readout`, `legal_actions`, `apply_action` (`battery.md` §3, §2) |
| FAM-4 | one seed deals one hand twice, another seed another hand, a deal ignores earlier hands, `new_hand` seeds the global random, and one seed with one policy pair gives one episode | `new_hand`, `play_hand` (`battery.md` §3, ASM-2) |
| FAM-16 | eight invented instances — an invented seed, a first decision, a descriptor list, one applied action, a hand played out, its payoffs, its episode and an equity estimate | `new_hand`, `readout`, `legal_actions`, `apply_action`, `is_terminal`, `payoffs`, `play_hand`, `equity` (`battery.md` §4, D-15) |
| FAM-5 | at the edge of this module: the oracle's pot-odds decision agrees with `equity` at the decision it was taken at | `equity`, `readout` (`battery.md` §3, ASM-4) |
