# features — the two encodings, and the contracts at this edge

- **Layer:** L2 · **Module:** `features` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-05
- **Owner of this file:** the representation axis — what each encoding carries and how it spells it (§1–§4)
  — the contracts `engine` and `agents` hold at this edge (§5–§6), the battery invariants this module
  carries (§7) and what is left to L3 (§8) (D-3, D-13)
- **Ceiling:** 190 lines. At the ceiling, split by owner — never append

## 1. One representation axis, two encodings

The ladder changes how the agent represents what it knows and never what it knows (D-3). Two encodings
carry the whole axis: `flat-numeric` for R1 and R2, `card-tokens` for R3–R6 (`ladder.md` §2, D-3). R1 and
R2 declare the same encoding, so their evidence is a speed comparison on identical work (D-7, `ladder.md`
§5); R3 is the rung that changes representation, and it changes nothing else (`ladder.md` §2, §4).

| Encoding | Rungs | Representation family (`kind`) | `shape` | `dtype` | `vocabulary` |
|---|---|---|---|---|---|
| `flat-numeric` | R1, R2 | `dense-numeric` — one fixed-width vector of normalised numbers and one-hots | `(203,)` | `float32` | `null` |
| `card-tokens` | R3–R6 | `token-sequence` — a fixed-length sequence of ids a learned embedding maps to vectors | `(40,)` | `int32` | `96` |

A variant entry declares which of the two it uses (`ladder.md` §3, `records.md` §2), and the choice is the
variant's and not a run's: there are two encodings and no third, `build_encoder` takes a name and no seed or
size, and no rung can drift into an encoding of its own (D-3, `ladder.md` §2, `e2e-surface.md` §3.2).

## 2. The fields carried, and why they never move

`observation_spec`'s `fields` is the same nine names for both encodings, each one of `engine.readout`'s
eleven facts (`e2e-surface.md` §2, `battery.md` §3 FAM-2): `street`, `seat`, `hole`, `board`, `stacks`,
`pot`, `to_call`, `limit` and `history` — the eleven less `legal` and `hand_class`, the derived fact
that no encoding carries (`engine/environment.md` §2, `folders.md` §3, ASM-30).

- The set is identical for every encoding, and that identity is the ladder's fairness condition: a
  comparison pair holds the information set constant and varies one axis (`ladder.md` §4, D-3), so an
  R2-to-R3 difference is attributable to the representation and to nothing else (D-3, `battery.md` §3
  FAM-2). The battery asserts the identity field by field (FAM-2.4) and that each field is a readout fact
  and no other (FAM-2.5).
- `legal`, one of the eleven, is **not** carried: a decision's legal set reaches a policy beside the
  observation, as the index mask `legal_indices` returns and as the mask `agents.act` takes beside it
  (`e2e-surface.md` §2, §3.3); carrying it twice would give one decision two statements of its legality
  that could disagree, and the mask is always at the decision (`battery.md` §3 FAM-2.9–FAM-2.11).
- A field is carried at the granularity its encoding declares — the pot as one normalised number, the
  history as its ordered action kinds, a card as a rank-and-suit pair — so "identical" means the same nine
  facts and never the same numbers: the fact set is what the ladder holds constant, and how a fact is
  spelled is the representation the rung varies (`e2e-surface.md` §2, D-3, `battery.md` §3 FAM-2).
- Nothing outside the nine is carried, and the readout offers nothing outside its eleven: never the other
  seat's cards, the undealt deck, a rung, an encoder, an opponent or a seed (`engine/environment.md` §2, D-3).

## 3. `flat-numeric` — one dense vector

One observation is a `float32` array of shape `(203,)`, and the width is the sum of one block per carried
field. The block **widths** are fixed here; the order of the blocks and the slot order inside a block are
L3's (§8), and a caller reads the array through `shape`, `dtype` and indexing and never through its layout
(`e2e-surface.md` §3.2, D-12).

| Field | Block width | What its numbers are |
|---|---|---|
| `street` | 4 | a one-hot over preflop, flop, turn, river |
| `seat` | 2 | the acting seat's index (0 or 1), and the button flag (1 or 0) |
| `hole` | 34 | two card slots of 17: a 13-wide rank one-hot and a 4-wide suit one-hot per card |
| `board` | 85 | five card slots of the same 17; a slot not yet dealt is all zeros |
| `stacks` | 2 | the acting seat's stack then the other's, each divided by 20 |
| `pot` | 1 | divided by the 40 chips a hand begins with (`engine/environment.md` §1) |
| `to_call` | 1 | divided by 20 |
| `limit` | 2 | the bet size in force divided by 4, and the bet-or-raise actions this street divided by 4 — the count's own maximum, so the slot spans 0.0–1.0 and no clip is needed |
| `history` | 72 | 24 slots of 3: a one-hot over fold, check/call and raise, one slot per applied action; a slot past the history's end is all zeros |

- The total is 203. The width is a fixed and modest vector by construction, so the budget of ASM-10 is
  reachable over it — but the budget is measured by `agents.param_count` on a learner, and this module
  asserts no width, architecture or parameter count of its own (`module-map.md` §3, ASM-10).
- 24 history slots are enough: under ASM-6's cap of four bet-or-raise actions a street, a post-flop street
  holds at most six applied actions — a check, the opening bet, three raises and a call — and the pre-flop
  street at most five, so a hand holds at most 3 × 6 + 5 = 23; the history is therefore carried whole, no
  truncation rule needed, and the encoding stays a pure function of the readout (`e2e-surface.md` §2, ASM-6).

## 4. `card-tokens` — one integer token sequence

One observation is an `int32` array of shape `(40,)`: one token id per carried occurrence of a fact, and a
learned embedding turns each id into a vector from R3 on (`ladder.md` §2, D-3). Id `0` is the pad, used by
the board and history blocks and by nothing else; the ids are grouped into one block per field, and which
values share an id *inside* a block is L3's, while a block's size is fixed here because it is the
embedding's vocabulary (§1, §6).

| Field | Tokens | Ids | What a token means |
|---|---|---|---|
| `hole` | 2 | 1–52 | one id per card |
| `board` | 5 | 1–52, and the pad `0` | a revealed card, or the pad for a slot not yet dealt |
| `street` | 1 | 53–56 | one id per street |
| `seat` | 2 | 57–60 | the acting seat's index, and the button flag |
| `to_call` | 1 | 61–68 | a bucket of the amount to call; `61` is the zero amount, its own id and never the pad, because it is the boundary between checking and folding (`engine/surface.md` §2) |
| `pot` | 1 | 69–76 | a bucket of the pot |
| `stacks` | 2 | 77–84 | a bucket of each seat's stack |
| `limit` | 2 | 85–88, 89–92 | the bet size in force, and the bet-or-raise actions this street |
| `history` | 24 | 93–95, and the pad `0` | one id per applied action — fold, check/call or raise — and the pad past the history's end |

- The token count is 40 — `hole` 2, `board` 5, `street` 1, `seat` 2, `to_call` 1, `pot` 1, `stacks` 2,
  `limit` 2, `history` 24 — and it is the declared shape.
- The vocabulary is 96 ids, `0`–`95`: one pad, 52 cards, four streets, four seat-and-button ids, three
  blocks of eight buckets, two four-id blocks for `limit` and three ids for the history.
  `observation_spec`'s `vocabulary` declares `96` and `agents` sizes an embedding table from it (§1, §6,
  `module-map.md` §2).
- The same nine facts are carried as in `flat-numeric`; the two differ in how each is spelled and, where a
  block buckets a quantity, in how finely it is resolved. That coarsening is part of the representation R3
  varies and not a change of fact set, which is what the ladder holds constant (`ladder.md` §4, D-3).

## 5. The contract at the `engine` edge (D-13)

What this module may rely on, stated as the facts it consumes and never as a description of that module's
internals (`module-map.md` §2, D-13):

- a readout is a mapping with exactly the eleven facts declared in `engine/environment.md` §2; this module
  reads nine and ignores `legal` and the derived `hand_class` (`e2e-surface.md` §2, `folders.md` §3);
- `street` is one of `preflop`, `flop`, `turn`, `river`, and those four strings are its whole domain
  (`engine/environment.md` §2);
- `seat` gives the acting seat's index — 0 or 1 — and a boolean saying whether it holds the button, which
  is why the encoding needs two numbers or two tokens for it (`engine/environment.md` §2);
- `hole` is exactly two cards, `board` is 0, 3, 4 or 5 cards, and a card names a rank and a suit, compares
  by value and prints stably; the spelling of a card is that module's to choose, so this module needs a
  card's **rank and suit as values it can read** — not prose it would have to parse — and never constructs,
  re-spells or compares two cards itself (`engine/environment.md` §2, D-13);
- `stacks` is one number per seat in seat order, `pot` and the two stacks partition the 40 chips a hand
  begins with, and `to_call` is never more than the acting seat's own stack (`engine/environment.md` §1,
  §2);
- `limit` gives the bet size in force — 2 or 4 — and the bet-or-raise actions made this street, 0 to 4 under
  the cap of four such actions (ASM-6, `e2e-surface.md` §2, `engine/environment.md` §2);
- `history` is an ordered list, the empty list before the first action and one entry per applied action,
  and at most 23 entries can occur under the raise cap (ASM-6); an entry prints stably, denotes the action
  that was applied, and is spelled by the engine's own grammar — street, seat, verb, amount — so this
  module reads that verb and owes no second spelling of an action (`engine/environment.md` §2, D-13);
- `legal` is the ordered descriptor sequence `legal_actions` returns for the same hand, which is why the
  mask can be taken from either (`engine/surface.md` §6);
- and a descriptor carries no amount, is hand-independent, compares by value and prints stably, which is
  what lets one index decode to one descriptor at every decision (`engine/surface.md` §2);
- and every fact above is consumed through that module's L2 interface — `docs/L2/engine/surface.md` and
  `environment.md` name each one — because this module reaches past no entry point (`module-map.md` §2, D-13).

Three of those facts are *values* rather than shapes, and `docs/L2/engine/` leaves their spelling to that
module's L3 (`docs/L2/engine/README.md` §5): a descriptor, a card, and a `history` entry. This document
fixes the descriptor's spelling, because a descriptor is the policy protocol's currency and both modules
exchange it (`e2e-surface.md` §2, `surface.md` §2); it does not fix a card's or a history entry's, so the
two modules owe each other a readable rank-and-suit on a card and an entry that denotes the applied
action, and a change to either is a change at this edge (D-13).

## 6. The contract at the `agents` edge (D-13)

What this module promises a learner, again stated at the edge (`module-map.md` §2, D-13):

- `observation_spec` is what a learner is sized from: `shape` gives a dense input's width and `vocabulary`
  gives an embedding table's row count, so a learner is built from the spec and never from a width copied
  out of a document (D-3, `module-map.md` §2, `records.md` §1);
- `action_space` fixes an output layer's three units: a learner's choice is one index of `{0, 1, 2}`, and
  `agents.act` reports the chosen one as that index or in a record carrying it, never as an index outside
  the three (`e2e-surface.md` §3.3, `records.md` §6);
- the legal mask `agents.act` receives is `legal_indices`' sequence for the decision, and the legal sets a
  transition record carries are expressible as these same index sets, so a masked update re-derives
  nothing (`records.md` §4, `e2e-surface.md` §3.3);
- `decode_action` is the reverse step: the index a learner chooses becomes the descriptor a policy returns
  and `engine` applies (`e2e-surface.md` §2, D-2);
- and nothing here is sized, trained or chosen: the parameter budget of ASM-10 is measured by
  `agents.param_count`, and this module counts nothing (`module-map.md` §3, ASM-10).

## 7. The invariants the battery asserts against this module

Each family of `battery.md` §3 that lands here, with its case ids and the entry point that carries it (`battery.md` §3, D-11):

| Family | What it asserts | Carried by |
|---|---|---|
| FAM-1 | all seven names exist and are callable, `decode_action(1)` included (cases FAM-1.10–FAM-1.16) | all seven (`e2e-surface.md` §3.2) |
| FAM-2 | both encodings are declared, with their representation kind, and each spec names its own (FAM-2.6); `fields` is identical across encodings (FAM-2.4) and every field is a readout fact (FAM-2.5); the spec declares `shape` and `dtype` (FAM-2.7); `encode` returns the declared shape (FAM-2.8); the vocabulary is `{0, 1, 2}` (FAM-2.9); `decode_action`'s descriptor is one `apply_action` accepts (FAM-2.10); a decision's descriptors and indices correspond one to one and its indices are distinct (FAM-2.11) | `encodings`, `observation_spec`, `encode`, `action_space`, `legal_indices`, `decode_action` |
| FAM-16 | three invented instances: one readout encoded twice to one observation of the declared shape (FAM-16.9); a decision's legal indices — `{0, 1, 2}` facing the big blind, `{1, 2}` with nothing to call (FAM-16.10); an index decoded to a descriptor the engine accepts at that decision (FAM-16.11) | `encode`, `legal_indices`, `decode_action`; FAM-16.10 reaches its decision through `agents.build_baseline`, so it turns green with that module and not with this one (`tests/e2e/_surface.py`, measured) |
| FAM-13 | R1 and R2 choose the same actions on the same seeded hands, which needs one encoding behind both backends — `flat-numeric`, built by one name, encoded by one function (at the `features` edge) | `build_encoder`, `encode` (`ladder.md` §5, D-7) |

`features` carries no other join: the pool, the cell and the table are `evaluation`'s, and the module's own
internals belong to `tests/features/` (`battery.md` §5, `module-map.md` §3).

## 8. What is left to L3

This document stops at the entry point and at each encoding's declared fields, block sizes, shape, dtype
and vocabulary. `role_l3_designer` owns the module design (D-1, `module-map.md` §5):

- the encoder's own type and what it holds, which no caller may inspect (§1 of `surface.md`);
- the order of the blocks and the slot order inside a block, for either encoding;
- the bucket edges inside `card-tokens`'s eight- and four-id blocks, and the pad's spelling beyond its id;
- the map from a card's rank and suit to its slot inside the 17, and the card-to-id order in `1`–`52`;
- the error classes the refusals raise, and the file layout under `src/features/`.

Each of those is free here and is designed there; none of them may change a shape, a dtype, a `fields`
entry or the vocabulary size, because those are what `agents` is sized from and what the battery reads
(`e2e-surface.md` §2, `battery.md` §3 FAM-2).
