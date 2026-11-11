# engine — the environment, and the contracts at its edge

- **Layer:** L2 · **Module:** `engine` · **Unit:** phase1 · **Rev:** 5 · **Date:** 2026-11-10
- **Owner of this file:** the environment — one hand's life and the facts it exposes (§1–§4) — and the contracts this module's four callers hold at its edge (§5–§6), with the battery invariants this module carries (§7) (D-2, D-3, D-13, D-21, D-29, D-33)
- **Ceiling:** 128 lines — re-issued from 130 for D-33's seat: one hand's life, its eleven facts and its episode record stated for a shape whose seat count is its own data, so the two facts that are the seat's are stated as `seats` entries and the chips in play as 600. At the ceiling, split by owner — never append

## 1. A hand's life: dealt, advanced, ended, paid

- **Dealt.** `new_hand` seeds the global `random` and creates the state, and `pokerkit` shuffles the deck at state creation, so the hand's whole card order is fixed in that call (ASM-2, `strata/platform.md`). The **seat count is the shape's**: the state is created with the row's `seats`, so a six-seat row deals a six-seat hand (ASM-44, `seats.md` §2).
- **Seated.** **Seat 0 holds the button on every shape**, and the button acts last on every street after the pre-flop (`seats.md` §3, `hand.md` §3). What the button posts is the shape's: on a two-seat shape it posts the small blind of 1 and seat 1 posts the big blind of 2, and seat 0 acts first preflop while seat 1 acts first on the flop, the turn and the river; on the six-seat shape the button posts nothing, seat 1 posts the small blind of 1, seat 2 the big blind of 2, seat 3 acts first preflop and seat 1 acts first on every later street — the same seating rule at six seats and not a second one (D-2, ASM-6, `seats.md` §2–§3, ASM-44).
- **Opened.** At the first decision the street is preflop, the pot holds the posted blinds, and the seat that owes the big blind is told so; in the default shape the stacks hold 19 and 18 chips behind, and on the six-seat shape the first decision is seat 3's, the pot holds 3 and the stacks hold 100, 99, 98, 100, 100 and 100 in seat order (ASM-6, `seats.md` §3, `battery.md` §3 FAM-2).
- **Conserved.** The facts partition the table's chips: at every decision `pot` plus the shape's `stacks` is the **chips in play the hand's own shape declares** — 40 in the default shape, 200 in the two-seat uncapped one and **600** on the six-seat one — because committed chips sit in `pot` and never in a stack (`e2e-surface.md` §2, ASM-6, `shapes.md` §2, `seats.md` §2).
- **Advanced.** A decision is one acting seat with one legal set; applying a descriptor appends one public action and may close a street, which reveals the next public cards, so successive decisions read a board of 0, 3, 4 or 5 cards and one street may follow another immediately once no seat can act for more (D-2, `e2e-surface.md` §2).
- **Ended.** A hand ends when a seat folds, or at showdown — which comes when the last street's betting closes, or sooner when no seat can act for more because a stack is committed — and from then on `is_terminal` is true and no seat is acting (D-2, ASM-1, ASM-6).
- **Paid.** The payoff is a seat's net chip delta over the hand, **one per seat**, they sum to zero, and a tied hand splits the pot — ties and splits are common at these stacks, so a payoff may be zero (ASM-12, `protocol.md` §2, `seats.md` §3).
- **Stateless.** The whole state of a hand lives in its handle and no state survives a call, so two handles are independent and a hand dealt earlier is unaffected by a hand dealt later (ASM-2, `e2e-surface.md` §1).

## 2. `readout` — D-3's information set

The readout is a function of the hand alone: it takes no rung, encoder, learner, opponent or seed, so
what an agent may know cannot differ between rungs (D-3, `e2e-surface.md` §2). It holds exactly these
eleven keys, and the eleven are the same eleven on **every declared shape** — what the seat count
changes is what two of them are worth, never how many there are (D-3, `battery.md` §3 FAM-2,
`shapes.md` §5, `seats.md` §3).

| Key | Content, and the shape a caller may rely on |
|---|---|
| `street` | one of `preflop`, `flop`, `turn`, `river` — those four strings and no others (`battery.md` §3 FAM-2) |
| `seat` | the acting seat: its index — `0` to the shape's seat count less one, so `0..1` on a two-seat shape and `0..5` on the six-seat one — as the fact's first number, and a boolean saying whether it holds the button, which is seat 0 on every shape and is therefore `index == 0` (`e2e-surface.md` §2, `battery.md` §3 FAM-16, `seats.md` §3, ASM-44) |
| `hole` | the acting seat's two cards (`e2e-surface.md` §2, `battery.md` §3 FAM-16) |
| `board` | 0, 3, 4 or 5 public cards (`e2e-surface.md` §2, ASM-6) |
| `stacks` | **one number per seat, in seat order**: the chips that seat holds behind — two entries on a two-seat shape, six on the six-seat one — so `pot + sum(stacks)` is the shape's chips in play and the fact's length is the seat count (`e2e-surface.md` §2, `battery.md` §3 FAM-2, `seats.md` §3, ASM-44) |
| `pot` | one number: the chips the seated players have committed, the current street's bets included (`e2e-surface.md` §2, `battery.md` §3 FAM-2) |
| `to_call` | one number: the chips the acting seat must add to continue, 0 when it may check for nothing, and never more than its own stack, which bounds a call for less (`e2e-surface.md` §2, `battery.md` §3 FAM-16) |
| `limit` | the fixed bet size in force and **the bet-or-raise actions made so far on this street** — 0 to 4 under the cap of ASM-6; a posted blind is not one of them, so a street's first decision reads none made, and a caller reads the bet size numerically (2 on the preflop and the flop, 4 on the turn and the river) (`e2e-surface.md` §2, ASM-6). The cap is the **fixed-limit shape's**, so a shape without one bounds the count by its own stack: the fact keeps its two entries and its derivation, and only the number of actions it can reach differs — its first entry stays a number in every shape, the minimum bet of a street, which the no-cap row states as its big blind of 2 (`shapes.md` §2, D-29) |
| `history` | a list of this hand's public actions, one per applied action, printing stably so two records of one deal compare, and empty — the empty list — before the first one (`e2e-surface.md` §2, `battery.md` §3 FAM-16) |
| `legal` | the ordered descriptors `legal_actions` returns for the same hand, in the same order (`e2e-surface.md` §2) |
| `hand_class` | the acting seat's best five-card hand of hole plus board as an integer — 0 high card, 1 one pair, 2 two pair, 3 three of a kind, 4 straight, 5 flush, 6 full house, 7 four of a kind, 8 straight flush — and `None` before the flop, where fewer than five cards are known; a **derived** fact of `hole` and `board`, so the information set is no wider, and no encoding carries it (`e2e-surface.md` §2, ASM-30, D-21) |

The second `limit` entry is a count of **bet-or-raise actions** — a completion, a bet or a raise — and never of
raises after an opening bet: ASM-6's cap is four such actions a street, the opening bet plus three raises on a
post-flop street and four raises after the posted blind pre-flop, five bet levels, and the posted blind is never
one of them, which is why a street's first decision reads `limit[1] == 0` (`e2e-surface.md` §2, ASM-6).

A card is a value that names a rank and a suit, compares by value and prints stably; one spelling is
used in `hole`, in `board` and in `history`, and which spelling that is is L3's (D-1, `e2e-surface.md` §2).

The readout never carries a fact outside those eleven, and in particular never does the following
(D-3, `battery.md` §3 FAM-2):

- never the non-acting seat's hole cards, in any form (`e2e-surface.md` §2, D-3);
- never the undealt deck, its order, or a board card the hand has not yet revealed (D-3, `e2e-surface.md` §2);
- never a rung, an encoding, a learner, an opponent, a seed or an episode count, because the information set is the same for every rung (D-3, `ladder.md` §4);
- never a twelfth key, since the set of facts is closed and the invariance family compares it exactly (D-3, `battery.md` §3 FAM-2).

## 3. `play_hand` — the episode record

`records.md` §5 fixes the record, and this module returns exactly that shape (`records.md` §1, §5):

| Key | Content |
|---|---|
| `seed` | **required** — the seed the call was made with, unchanged (`records.md` §5, ASM-2) |
| `decisions` | **required** — the ordered decisions, one entry per decision in the order they were taken (`records.md` §5) |
| `payoffs` | **required** — net chips per seat summing to zero, the same record `payoffs` returns for that completed hand (`records.md` §5, ASM-12) |

Each decision carries the five facts `records.md` §5 requires beside the three amount facts, and
this module states what each of them is at the edge (`records.md` §5, `battery.md` §3 FAM-16):

- `seat`, the decision's own acting seat, in the shape of §2's `seat` fact;
- `readout`, the whole eleven-fact mapping of §2 for that decision, so an encoder can encode a decision after the hand is over — **eleven**, in every shape, so `minimum`/`maximum` below are the record's and never a twelfth fact (D-3, `records.md` §5, `shapes.md` §5);
- `legal`, that decision's ordered descriptor list, and `action`, the descriptor the policy returned and the engine applied (`e2e-surface.md` §2);
- `minimum` and `maximum`, the bounds of the **legal raise interval** at that decision, and `None` exactly when no raise was legal — the interval `sizing.md` §2 partitions, so a caller can attribute the amount without a second source of truth (`records.md` §5, `sizing.md` §2);
- `amount`, the raise-to the engine resolved, and `None` whenever the chosen descriptor is not a raise; the fixed-limit shape's `raise` resolves to its minimum legal completion, which for that shape is both bounds (`records.md` §5, `sizing.md` §2);
- `reward`, the seat's net chip delta for the completed hand at that seat's **last** decision, and zero at every other decision — so a hand carries at most one non-zero reward per seat, and on the six-seat shape the six of them are the six payoffs (ASM-12, `records.md` §5, `seats.md` §3).

A seat that never acted carries no decision and therefore no reward; the reward is the hand's outcome
and never a shaped per-decision term (ASM-12, `records.md` §5). The episode is a record of what happened
and is not re-opened: a caller that wants the hand advanced further plays it through `new_hand` and
`apply_action` instead (`e2e-surface.md` §1, `module-map.md` §3).

## 4. `equity` — how the oracle's question is answered

- The question is conditional on what the acting seat can see: if the opponents' two cards were uniform draws from the cards this seat has not seen, what share of the pot does it win on average (ASM-4, `protocol.md` §3).
- **How many opponents is the shape's.** On a two-seat shape the question is heads-up and the answer is the one this module has always given; on a shape with more than two seats the opponents are the **other seats'** hands, each a uniform draw from what this seat has not seen, so a six-seat call is asked against five random hands and its answer is the acting seat's share of a six-way pot (`seats.md` §2, `e2e-surface.md` §3.1, ASM-44).
- That is why the answer needs only the acting seat's `hole`, the `board` and the unseen deck, and why the same question can be asked from a readout as from a hand (ASM-4, `e2e-surface.md` §2), and why the opponent count is read from a fact the readout already carries wherever it is asked of a mapping: `stacks` is one entry per seat, so its length is the seat count (`seats.md` §3).
- The answer is a share of the pot and not a win-or-lose flag: a split counts as its share, which is what lets the oracle compare it with `to_call / (pot + to_call)` (ASM-6, `protocol.md` §3).
- It is an estimate over the caller's sample count, seeded so that it repeats, and the oracle asks it at every decision of a hand it is playing (ASM-4, `battery.md` §3 FAM-16).
- Because the oracle asks it mid-hand and `play_hand` then applies the returned action to that same hand, the query must leave both the hand and the deal stream exactly as it found them (ASM-4, ASM-2).

## 5. Seeding and the sequential rule

- One global stream deals every hand: `pokerkit` shuffles with Python's `random` and takes no seed, so `new_hand` is the one point at which the deal stream is set, `play_hand` deals through it, and no other module sets it (ASM-2, `protocol.md` §4). The **shape** does not move it: `new_hand` seeds with its seed and then creates the state its shape declares, so a default-shape deal is unchanged card for card and a named shape's deal is that shape's alone (`shapes.md` §5, D-29).
- Therefore hands are played one at a time. A cell is played hand after hand, and two cells are never interleaved or threaded; sequential play is a contract and not an implementation choice (D-16, `protocol.md` §4).
- Because each hand is seeded, a cell's hands are reproducible from the cell's seed, and a cell does not depend on what was played between two of its own runs (`battery.md` §3 FAM-7, ASM-2).
- The engine remembers no seed and reuses none: a caller that wants reproducibility passes the seed it records, and a run is reproducible from its configuration, seed set, budget and pool membership (`protocol.md` §2, `protocol.md` §4).
- There is no way to share, fork or thread a deal, so cost is bought with cell size and never with parallelism (D-16, `league.md` §3).

## 6. The contracts at this edge (D-13)

Each caller's obligation is stated as what it may rely on from this module, not as a description of
its internals (`module-map.md` §2, D-13):

- `features` encodes a readout and nothing else, so the readout is self-contained: an encoder that needed the hand could not be written against §2 (D-3, `e2e-surface.md` §2). The **shape** is not a readout fact either — no twelfth key carries it — so a caller that needs it names it at its own entry point (`features.build_encoder`, `features.action_space`), and a hand is never asked which shape it is (`shapes.md` §3, §5).
- `features.observation_spec`'s `fields` is a subset of §2's eleven names — nine facts today, and never `hand_class`, which no encoding carries — so those names are the edge's shared vocabulary and may be neither renamed nor extended (D-3, ASM-30, `battery.md` §3 FAM-2).
- `features.legal_indices` maps this module's descriptor sequence to indices position by position, and `features.decode_action` returns a descriptor `apply_action` accepts, which is why a descriptor is hand-independent and compares by value (`e2e-surface.md` §2, D-2).
- `agents.as_policy`, `agents.build_baseline`, `evaluation.policy_from` and `harness.seam` all return a callable taking the readout and the legal descriptors and returning one member of that list; `play_hand` accepts that protocol and knows none of those builders by name (`e2e-surface.md` §2, D-13).
- The oracle baseline reads `pot` and `to_call` from the readout and asks `equity` with the readout it was handed, which is why `equity` accepts one (ASM-4, `protocol.md` §3).
- `agents`' folding baselines read the readout and nothing below it: `hand_class` for `fold-no-pair-or-better`, a card's rank character for `fold-no-pair-or-face`, and `game_config`'s declared starting stack for `fold-large-bet` — never a second hand evaluator and never a copy of a game parameter (`folders.md` §2, ASM-30, ASM-31, D-21).
- `evaluation.match` plays a cell through `new_hand` and `play_hand` one hand at a time, alternates seats by swapping the two policies, and reads `payoffs` for the chip deltas; the cell, its hand count, its seat split and its opponent are `evaluation`'s and never this module's (D-16, `league.md` §3). A shape seating more than two has no cell: `match`, `matrix`, `rating` and `report` refuse it by name, and what a six-seat caller does instead is seat the whole table through `play_hand`'s `seats` (`seats.md` §4–§5, ASM-43).
- `training.run` draws each training hand's deal and its opponent's play the same way, so a run's data is a sequence of `play_hand` calls at the run's own seeds (D-16, `module-map.md` §2).

## 7. The invariants the battery asserts against this module

The families of `battery.md` §3 that land on `engine` are asserted at the observable edge, and each
one is carried by the entry points named beside it — this table is what an implementer reads to see
what FAM-1, FAM-2, FAM-4 and FAM-16 require of this module (`battery.md` §3, D-11):

| Family | What it asserts | Carried by |
|---|---|---|
| FAM-1 | the ten names exist, are callable, and a minimal call returns the declared kind | all ten (`e2e-surface.md` §3.1, `battery.md` §3) |
| FAM-2 | the game is one deterministic declaration per shape; the default shape's first decision reads preflop with a pot of 3, stacks summing to 37 and a call of 1; the readout holds exactly the eleven facts, and `stacks` holds one entry per seat; every legal descriptor has one index and `decode_action`'s descriptor is accepted | `game_shapes`, `game_config`, `readout`, `legal_actions`, `apply_action` (`battery.md` §3, §2, `shapes.md` §2, `seats.md` §3) |
| FAM-4 | one seed deals one hand twice, another seed another hand, a deal ignores earlier hands, `new_hand` seeds the global random, and one seed with one policy pair gives one episode | `new_hand`, `play_hand` (`battery.md` §3, ASM-2) |
| FAM-16 | eight invented instances — an invented seed, a first decision, a descriptor list, one applied action, a hand played out, its payoffs, its episode and an equity estimate | `new_hand`, `readout`, `legal_actions`, `apply_action`, `is_terminal`, `payoffs`, `play_hand`, `equity` (`battery.md` §4, D-15) |
| FAM-19 | the catalogue's three rows default first with their seats, chips in play, `history` capacity and normalisers; a name outside it refused by name; and `game_config()`'s fifteen keys unchanged | `game_shapes`, `game_config` (`shapes.md` §2, §8, `seats.md` §2, ASM-42, ASM-44) |
| FAM-5 | at the edge of this module: the oracle's pot-odds decision agrees with `equity` at the decision it was taken at | `equity`, `readout` (`battery.md` §3, ASM-4) |
