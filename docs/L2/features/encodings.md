# features — the two encodings, and the contracts at this edge

- **Layer:** L2 · **Module:** `features` · **Unit:** phase1 · **Rev:** 4 · **Date:** 2026-11-10
- **Owner of this file:** the representation axis — what each encoding carries and how it spells it (§1–§4)
  — the contracts `engine` and `agents` hold at this edge (§5–§6), the battery invariants this module carries
  (§7) and what is left to L3 (§8) (D-3, D-13, D-33)
- **Ceiling:** 190 lines. At the ceiling, split by owner — never append

## 1. One representation axis, two encodings

The ladder changes how the agent represents what it knows and never what it knows (D-3). Two encodings carry the whole
axis: `flat-numeric` for R1 and R2, `card-tokens` for R3–R6 (`ladder.md` §2, D-3); R1 and R2 declare one encoding, so
their evidence is a speed comparison (D-7), and R3 changes representation alone (§4).

| Encoding | Rungs | Representation family (`kind`) | `shape` | `dtype` | `vocabulary` |
|---|---|---|---|---|---|
| `flat-numeric` | R1, R2 | `dense-numeric` — one fixed-width vector of normalised numbers and one-hots | `(203,)` / `(329,)` / `(433,)` | `float32` | `null` |
| `card-tokens` | R3–R6 | `token-sequence` — a fixed-length sequence of ids a learned embedding maps to vectors | `(40,)` / `(82,)` / `(122,)` | `int32` | `96` / `96` / `102` |

The three values in each column are given in the catalogue's order — `fixed-limit-20`, `no-limit-100`
then `six-seat-no-limit-100` — because one observation's width is the shape's: each encoding declares the shape's
history capacity (24, 66, 98), one slot per seat in both per-seat blocks, and its own token vocabulary (`shapes.md`
§8, `seats.md` §3, ASM-42, ASM-44, `capacity.md` §2).

A variant entry declares which of the two it uses (`ladder.md` §3, `records.md` §2), and the choice is the variant's and
not a run's: there are two encodings and no third, `build_encoder` takes a name and a shape and no seed or size, and no
rung can drift into an encoding of its own (D-3, `e2e-surface.md` §3.2).

## 2. The fields carried, and why they never move

`observation_spec`'s `fields` is the same nine names for both encodings, each one of `engine.readout`'s eleven facts
(`e2e-surface.md` §2, `battery.md` §3 FAM-2): `street`, `seat`, `hole`, `board`, `stacks`, `pot`, `to_call`, `limit` and
`history` — the eleven less `legal` and `hand_class`, the derived fact that no encoding carries (`folders.md` §3, ASM-30).

- The set is identical for every encoding, and that identity is the ladder's fairness condition: a comparison
  pair holds the information set constant and varies one axis (`ladder.md` §4, D-3), so an R2-to-R3 difference is
  attributable to the representation and nothing else — asserted field by field (FAM-2.4, FAM-2.5).
- `legal`, one of the eleven, is **not** carried: a decision's legal set reaches a policy beside the observation,
  as the index mask `legal_indices` returns (`e2e-surface.md` §2, §3.3); carrying it twice would give one
  decision two statements of its legality that could disagree (`battery.md` §3 FAM-2.9).
- A field is carried at the granularity its encoding declares — the pot as one normalised number, the history as
  its ordered action kinds, a card as a rank-and-suit pair — so "identical" means the same nine facts and never
  the same numbers (`e2e-surface.md` §2, D-3, `battery.md` §3 FAM-2).
- Nothing outside the nine is carried: never the other seat's cards, the undealt deck, a rung, an encoder, an
  opponent or a seed (`engine/environment.md` §2, D-3).

## 3. `flat-numeric` — one dense vector

One observation is a `float32` array of shape `(203,)` on the default shape, `(329,)` on `no-limit-100` and `(433,)` on
`six-seat-no-limit-100`, and the width is the sum of one block per carried field. The block **widths** are fixed here;
the block order and the slot order inside a block are L3's (§8), and a caller reads the array through `shape`, `dtype`
and indexing and never through its layout (`e2e-surface.md` §3.2, D-12). Six of the nine widths are the **same on all
three game shapes**; two follow the seat count — one slot per seat in `seat` and in `stacks` — and the ninth is the
history block's, `3 × the shape's capacity` (`shapes.md` §2, §5, §8, `seats.md` §3).

| Field | Block width | What its numbers are |
|---|---|---|
| `street` | 4 | a one-hot over preflop, flop, turn, river |
| `seat` | `seats` — 2 or 6 | on a two-seat row the acting seat's index (0 or 1) then the button flag (1 or 0); above that the acting seat's one-hot over the seat count (`seats.md` §3, ASM-44) |
| `hole` | 34 | two card slots of 17: a 13-wide rank one-hot and a 4-wide suit one-hot per card |
| `board` | 85 | five card slots of the same 17; a slot not yet dealt is all zeros |
| `stacks` | `seats` — 2 or 6 | on a two-seat row the acting seat's stack then the other's; above that one slot per seat in seat order — each divided by the shape's `stack` normaliser (`seats.md` §3, ASM-44) |
| `pot` | 1 | divided by the shape's `pot` normaliser — 40, 200 or 600, the shape's chips in play (`shapes.md` §2) |
| `to_call` | 1 | divided by the shape's `to_call` normaliser |
| `limit` | 2 | the bet size in force over the shape's `amount` normaliser, and the bet-or-raise actions this street over its `count` normaliser — the count's own maximum on the default shape, so that slot spans 0.0–1.0 and no clip is needed |
| `history` | `3 × capacity` — 72 / 198 / 294 | one slot of 3 per applied action: a one-hot over fold, check/call and raise, oldest first; a slot past the history's end is all zeros (`shapes.md` §8, `seats.md` §2) |

- The total is `127 + 2 × seats + 3 × capacity` — `4 + seats + 34 + 85 + seats + 1 + 1 + 2 = 127 + 2 × seats` slots
  before the history: 131 + 72 = 203, 131 + 198 = 329 and 139 + 294 = 433, by shape. The budget is measured by
  `agents.param_count`; this module asserts no width, architecture or parameter count (`module-map.md` §3, ASM-10).
- The capacity is the shape's and it is the block's **refusal threshold** as well as its width: 24 entries encode on
  the default shape, 66 on the two-seat uncapped one and 98 on the six-seat one, and a longer history is refused
  naming the field, the capacity and the count, never truncated — the derivation and the arithmetic are
  `capacity.md` §1–§3's (`shapes.md` §8, ASM-42, `errors.md` §3).

## 4. `card-tokens` — one integer token sequence

One observation is an `int32` array of shape `(40,)` on the default shape, `(82,)` on `no-limit-100` and `(122,)` on
`six-seat-no-limit-100`: one token id per carried occurrence of a fact, and a learned embedding turns each id into a
vector from R3 on (`ladder.md` §2, D-3). Id `0` is the pad, used by the board and history blocks and by the per-seat
`seat` block above two seats; the ids are grouped into one block per field, and which values share an id *inside* a
block is L3's, while a block's size and the id ranges are fixed here because they are the embedding's vocabulary (§1,
§6). **The token counts before the history are 12 plus one per seat in each of the two per-seat blocks**, and the
vocabulary is the shape's: 96 ids on the two-seat rows and 102 on the six-seat one, whose seat block emits six ids of
its own above every id the other rows use (`shapes.md` §5, §8, `seats.md` §3, ASM-42, ASM-44).

| Field | Tokens | Ids | What a token means |
|---|---|---|---|
| `hole` | 2 | 1–52 | one id per card |
| `board` | 5 | 1–52, and the pad `0` | a revealed card, or the pad for a slot not yet dealt |
| `street` | 1 | 53–56 | one id per street |
| `seat` | `seats` — 2 or 6 | two-seat rows: 57–60, the index and the button flag; six-seat row: 96–101, one id per seat slot and the pad elsewhere (`seats.md` §3, ASM-44) |
| `to_call` | 1 | 61–68 | a bucket of the amount to call; `61` is the zero amount, its own id and never the pad, because it is the boundary between checking and folding (`engine/surface.md` §2) |
| `pot` | 1 | 69–76 | a bucket of the pot, on the shape's own ladder |
| `stacks` | `seats` — 2 or 6 | 77–84 | a bucket of each seat's stack, in the readout's seat order (`seats.md` §3) |
| `limit` | 2 | 85–88, 89–92 | the bet size in force, and the bet-or-raise actions this street |
| `history` | the capacity — 24 / 66 / 98 | 93–95, and the pad `0` | one id per applied action — fold, check/call or raise — and the pad past the history's end (`shapes.md` §8) |

- The token count is `12 + 2 × seats + capacity` — 16 + 24 = 40 on `fixed-limit-20`, 16 + 66 = 82 on `no-limit-100`
  and 24 + 98 = 122 on `six-seat-no-limit-100` — where the 12 that no seat count touches are `hole` 2, `board` 5,
  `street` 1, `to_call` 1, `pot` 1 and `limit` 2.
- The vocabulary is the shape's and it is `0`–`95` on the two-seat rows: one pad, 52 cards, four streets, four
  seat-and-button ids, three blocks of eight buckets, two four-id blocks for `limit` and three ids for the history.
  The six-seat row adds **six seat ids, `96`–`101`, one per seat slot**, so its vocabulary is `102` = `0`–`101` and no
  existing id is renamed: no block of one observation can emit another's id, and the wider history block still emits
  only `93`–`95` (`seats.md` §3, ASM-44). `observation_spec` declares the vocabulary of the shape its encoder was
  built for and `agents` sizes an embedding table from it (§1, §6).
- The same nine facts are carried as in `flat-numeric`; the two differ in how each is spelled and, where a block
  buckets a quantity, in how finely it is resolved — a coarsening that is R3's axis (`ladder.md` §4, D-3).

## 5. The contract at the `engine` edge (D-13)

What this module may rely on, stated as the facts it consumes and never as a description of that module's internals
(`module-map.md` §2, D-13):

- a readout is a mapping with exactly the eleven facts declared in `engine/environment.md` §2; this module reads
  nine and ignores `legal` and the derived `hand_class` (`e2e-surface.md` §2, `folders.md` §3);
- `street` is one of `preflop`, `flop`, `turn`, `river`, and those four strings are its whole domain
  (`engine/environment.md` §2);
- `seat` gives the acting seat's index — `0` to `seats − 1`, so `0` or `1` on a two-seat row and `0` to `5` on the
  six-seat one — and a boolean saying whether it holds the button; that is why a two-seat row needs two numbers or
  two tokens for it and a six-seat row one slot per seat (`engine/environment.md` §2, `seats.md` §3, ASM-44);
- `hole` is exactly two cards, `board` is 0, 3, 4 or 5 cards, and a card names a rank and a suit; the spelling of
  a card is that module's to choose, so this module needs a card's **rank and suit as values it can read** — not
  prose it would have to parse — and never re-spells or compares two cards itself (`engine/environment.md` §2);
- `stacks` is one number per seat in seat order — two on the two-seat rows, six on the six-seat one — `pot` and
  those stacks partition the shape's chips in play (40, 200, 600) and `to_call` is never more than the acting
  seat's own stack (`engine/environment.md` §1, §2, `shapes.md` §2);
- `limit` gives the bet size in force and the bet-or-raise actions made this street: 2 or 4 and 0 to 4 under
  ASM-6's cap on the default shape, and the minimum legal raise-to with a count the shape's stack bounds on the
  two uncapped rows (ASM-6, `e2e-surface.md` §2, `shapes.md` §2);
- `history` is an ordered list, the empty list before the first action and one entry per applied action, and at
  most 23 entries can occur under the default shape's raise cap while an uncapped hand applies far more — which is
  why this module's block declares the shape's capacity and refuses one entry past it; an entry prints stably,
  denotes the action applied and is spelled by the engine's own grammar, so this module reads that verb and owes
  no second spelling (`engine/environment.md` §2, `capacity.md` §1, ASM-6, ASM-42, D-13);
- `legal` is the ordered descriptor sequence `legal_actions` returns for the same hand, which is why the mask can
  be taken from either (`engine/surface.md` §6);
- and a descriptor carries no amount, is hand-independent, compares by value and prints stably, which is what lets
  one index decode to one descriptor at every decision — and every fact above is consumed through that module's L2
  interface, because this module reaches past no entry point (`engine/surface.md` §2, `module-map.md` §2, D-13).

Three of those facts are *values* rather than shapes, and `docs/L2/engine/` leaves their spelling to that module's L3
(`docs/L2/engine/README.md` §5): a descriptor, a card, and a `history` entry. This document fixes the descriptor's
spelling, because a descriptor is the policy protocol's currency and both modules exchange it (`surface.md` §2); it does
not fix a card's or a history entry's, so the two owe each other a readable rank-and-suit and an entry that denotes the
applied action (D-13).

## 6. The contract at the `agents` edge (D-13)

What this module promises a learner, again stated at the edge (`module-map.md` §2, D-13):

- `observation_spec` is what a learner is sized from: `shape` gives a dense input's width — the shape's own, 203,
  329 or 433 — and `vocabulary` gives an embedding table's row count, the shape's own 96 or 102, so a learner is
  built from the spec and never from a width copied out of a document (D-3, `module-map.md` §2, `records.md` §1,
  `shapes.md` §8, `seats.md` §3);
- `action_space` fixes an output layer's width — one integer per descriptor of the shape the learner decides
  in: three units on the default shape, six on the two uncapped rows (`shapes.md` §3, `sizing.md` §6). A learner's
  choice is one index of that vocabulary, and `agents.act` reports the chosen one as that index or in a record
  carrying it, never as an index outside it (`e2e-surface.md` §3.3, `records.md` §6);
- the legal mask `agents.act` receives is `legal_indices`' sequence for the decision, and the legal sets a
  transition record carries are expressible as these same index sets, so a masked update re-derives nothing
  (`records.md` §4, `e2e-surface.md` §3.3);
- `decode_action` is the reverse step: the index a learner chooses becomes the descriptor a policy returns and
  `engine` applies (`e2e-surface.md` §2, D-2);
- nothing here is sized, trained or chosen: the budget of ASM-10 is measured by `agents.param_count`
  (`module-map.md` §3, ASM-10).

## 7. The invariants the battery asserts against this module

Each family of `battery.md` §3 that lands here, with its case ids and the entry point that carries it:

| Family | What it asserts | Carried by |
|---|---|---|
| FAM-1 | all seven names exist and are callable, `decode_action(1)` included (cases FAM-1.10–FAM-1.16) | all seven (`e2e-surface.md` §3.2) |
| FAM-2 | both encodings are declared, with their representation kind, and each spec names its own (FAM-2.6); `fields` is identical across encodings (FAM-2.4) and every field is a readout fact (FAM-2.5); the spec declares each shape's `shape` and `dtype` (FAM-2.7); `encode` returns the declared shape (FAM-2.8); the default shape's vocabulary is `{0, 1, 2}` (FAM-2.9); `decode_action`'s descriptor is one `apply_action` accepts (FAM-2.10); a decision's descriptors and indices correspond one to one and its indices are distinct (FAM-2.11) | `encodings`, `observation_spec`, `encode`, `action_space`, `legal_indices`, `decode_action` |
| FAM-16 | three invented instances: one readout encoded twice to one observation of the declared shape (FAM-16.9); a decision's legal indices — `{0, 1, 2}` facing the big blind, `{1, 2}` with nothing to call (FAM-16.10); an index decoded to a descriptor the engine accepts at that decision (FAM-16.11) | `encode`, `legal_indices`, `decode_action`; FAM-16.10 reaches its decision through `agents.build_baseline`, so it turns green with that module and not with this one (`tests/e2e/_surface.py`, measured) |
| FAM-13 | R1 and R2 choose the same actions on the same seeded hands, which needs one encoding behind both backends — `flat-numeric`, built by one name, encoded by one function (at the `features` edge) | `build_encoder`, `encode` (`ladder.md` §5, D-7) |

`features` carries no other join: the pool, the cell and the table are `evaluation`'s, the module's own internals belong
to `tests/features/`, and the per-shape widths are the join's newest assertion (`battery.md` §5, `capacity.md` §2, §5).

## 8. What is left to L3

`role_l3_designer` owns everything below the entry point (D-1, `module-map.md` §5): the encoder's own type and what it
holds, which no caller may inspect (§1 of `surface.md`); the block order, each block's slot order and the two
per-seat writers' declared modes; the bucket edges inside `card-tokens`'s eight- and four-id blocks — **per shape**,
over the same ids — and the pad's spelling beyond its id; the card→slot and card→id maps; and the error classes with
the file layout under `src/features/`. None may change a dtype, a `fields` entry, a shape's vocabulary size or the
derivation of a shape's width, because those are what `agents` is sized from (`battery.md` §3 FAM-2, `seats.md` §3).
