# features — module design (L3)

- **Layer:** L3 · **Module:** `features` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-09
- **Realises:** `docs/L2/features/surface.md` (the seven entry points, their refusals and their ordering),
  `docs/L2/features/encodings.md` (the two encodings, the nine carried fields, the contracts at the engine
  and `agents` edges) and `docs/L2/features/shapes.md` (the game shape as this module's own data)
- **Reads:** `docs/L1/e2e-surface.md` §1, §2, §3.2, §5, `docs/L1/shapes.md` §2, §5, `docs/L1/sizing.md` §3, §5,
  `docs/L1/folders.md` §3, `docs/L1/records.md` §1, §2, §4, §6, `docs/L1/ladder.md` §2–§5,
  `docs/L1/module-map.md` §2–§3, `docs/L1/battery.md` §2–§4, `docs/L1/assumptions.md` (ASM-2, ASM-6, ASM-7,
  ASM-9, ASM-10, ASM-30, ASM-39), `strata/decisions.md` (D-1, D-2, D-3, D-12, D-13, D-15, D-21); and, as
  inherited fact and never as code, `docs/L3/engine/README.md` §4, `docs/L3/engine/readout.md` §2–§3,
  `docs/L3/engine/history.md` §1, `docs/L3/engine/actions.md` §1–§2
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
- **Implements:** `src/features/` (written by L4, never by L3). `tests/features/` is this design's unit
  battery; `tests/e2e/test_fam0{1,2}_*.py` and `test_fam16_blind.py` are the L1 battery's share for it

## 1. What this module is

`features` is the ladder's representation axis (D-3) and nothing else. It turns one readout into one
observation, and one action index into one action descriptor. The information set and the **shape's** action
vocabulary are held constant for every rung, and the ladder holds one shape; what this module varies is how
the same nine facts are spelled (`docs/L2/features/encodings.md` §1). The second declared shape is data — a
row of `declarations.SHAPE_ROWS`, restated rather than imported — and never a second module
(`docs/L2/features/shapes.md` §1, `encoder.md` §4).

It imports `numpy` and the Python standard library and **nothing else** — never `pokerkit`, never
`torch`, never another project module (`module-map.md` §3, `layout.md` §3, `guardrails.md` G16). A readout
arrives as a mapping and leaves as an array; the two encodings are two rows of one declaration table, not two
code paths (`encoder.md` §4, `card-tokens.md` §1).

## 2. The documents, one per owner

| Document | Owner of that question | What it fixes |
|---|---|---|
| `encoder.md` | the encoder and the observation spec | the opaque `Encoder` value, `build_encoder`/`observation_spec`/`encodings`, the six shape-invariant spec keys, and the one declaration table, keyed encoding × shape |
| `flat-numeric.md` | the dense encoding | block order, slot order inside each block, the card→slot map, the amount normalisers **per shape**, the history slot, and the arithmetic that sums to 203 |
| `card-tokens.md` | the token encoding | token order, the card→id map, the bucket edges of the five bucketed blocks **per shape**, the pad, and the arithmetic that sums to 40 tokens over 96 ids |
| `vocabulary.md` | the action axis | the shape's vocabulary, `action_space`'s record per shape, `legal_indices`' positional alignment, `decode_action`, and what is not a descriptor |
| `errors.md` | refusals | the error hierarchy and the message grammar every refusal follows, and what is deliberately *not* refused |
| `layout.md` | the files | the file layout of `src/features/`, the seven exported names, and the import boundary |
| `guardrails.md` | L4 | one numbered note per risk this design identified, in the order they bite |

## 3. The seven names, and what is *not* a name

`src/features/__init__.py` exports exactly the seven entry points of `e2e-surface.md` §3.2, declares
them in `__all__`, and adds, removes and renames none (D-12):

    encodings()                        -> Mapping            # name -> spec record, ladder order
    build_encoder(name, *, shape=None) -> Encoder            # opaque value, on one declared shape
    observation_spec(encoder)          -> Mapping            # the six shape-invariant keys
    encode(encoder, readout)           -> numpy.ndarray       # one observation
    action_space(*, shape=None)        -> Mapping            # the shape's indices, in its declared order
    legal_indices(legal_actions)       -> tuple[int, ...]     # no shape: each descriptor has its index
    decode_action(index, *, shape=None) -> str                # the shape's vocabulary decides 0-2 or 0-5

The three widened names take `shape` as a **keyword-only** argument because the pre-existing arity cases pin
each name's positional argument, and a keyword-only optional adds the shape without moving any of them (D-11,
`shapes.md` §5, `vocabulary.md` §4); an absent one is the default shape, `fixed-limit-20`.

`Encoder`, `FeaturesError` and its seven subclasses, the declaration table, the block tables, the card
map, the bucket edges, the history parser and every helper below an entry point are **not** surface
(`e2e-surface.md` §1, `surface.md` §1). A caller reaches an encoder only through `build_encoder`, and
inspects it through `observation_spec` — never by reading its attributes.

Every rule that holds of all seven — an invalid argument raises an error naming the violated contract,
no coercion, no substituted default, no swallowed error, no partial record, no randomness, no seed
argument — is `docs/L2/features/surface.md` §1 and is not restated here.

## 4. The facts this module inherits, and must not re-derive

`docs/L3/engine/` fixed these, and this design consumes them as values (`encodings.md` §5, D-13):

- **ASM-E1 — the card spelling.** A card is a two-character plain `str`: rank first from
  `"23456789TJQKA"`, suit second from `"cdhs"` — `"As"`, `"Td"`, `"2c"`, `"Kh"`. No `pokerkit` object
  ever leaves the engine (`docs/L3/engine/readout.md` §3). `features` **parses** it in `cards.py`, on both
  shapes, and never imports the library that produced it.
- **ASM-E2 — the history entry grammar.** A history entry is a plain `str` of one grammar and carries
  no card (`docs/L3/engine/history.md` §1): `"<street> seat <index> folds"`, `"… checks"`,
  `"… calls <amount>"`, `"… raises to <amount>"`. The encoding reads the **verb** (and checks the form's
  own shape) and carries neither the street, the seat nor the amount: a fifth form is refused by name
  (`history.py`, `flat-numeric.md` §5).
- **Seat order.** Engine seat 0 is the button, and every per-seat fact (`seat`, `stacks`, a history
  entry's `<index>`) is in engine seat order (`docs/L3/engine/README.md` §4, `readout.md` §2).
- **The descriptor spelling.** `"fold"`, `"check-call"`, `"raise"` on `fixed-limit-20` — the same `str`s
  `engine.apply_action` accepts, and the shape's own further descriptors (`"raise-quarter"`,
  `"raise-half"`, `"raise-all-in"`, `"raise-minimum"`) on `no-limit-100`, each with its own index
  (`docs/L3/engine/actions.md` §1, `vocabulary.md` §1). That is why `legal_indices` is positional.
- **The readout's value shapes** — the exact types `encode` reads, and the only eleven keys that exist:

| Key | The value this module receives |
|---|---|
| `street` | `str`: `"preflop"`, `"flop"`, `"turn"` or `"river"` |
| `seat` | `tuple[int, bool]`: the acting seat's index, then whether it holds the button |
| `hole` | `tuple[str, str]`: the acting seat's two cards |
| `board` | `tuple[str, ...]`: length 0, 3, 4 or 5 |
| `stacks` | `tuple[int, int]`: chips behind, seat order |
| `pot` | `int`: includes the current street's bets; `pot + sum(stacks)` is the shape's chips in play — 40 on `fixed-limit-20`, 200 on `no-limit-100` |
| `to_call` | `int`: 0 when the acting seat may check, never more than its own stack |
| `limit` | `tuple[int, int]`: the amount in force — 2 or 4 on `fixed-limit-20`, the minimum legal raise-to on `no-limit-100` — and the bet-or-raise actions this street (0–4 under ASM-6's cap; bounded by the stack otherwise) |
| `history` | `list[str]`: oldest first, empty before the first action, at most 24 entries — the block's own capacity; ASM-6's cap makes 23 the default shape's hand maximum (`flat-numeric.md` §5) |
| `legal` | `tuple[str, ...]`: carried by the readout and **not** carried by an observation |
| `hand_class` | `int` or `None`: the acting seat's best five-card hand of `hole` plus `board`, `None` before the flop — a derived fact **no** encoding carries (`encodings.md` §2, `folders.md` §3, ASM-30) |

## 5. Decisions a later module must not re-derive

1. **One declaration table is the whole axis.** `src/features/declarations.py` holds one **shape row** per
   declared shape — descriptors, five normalisers, five ladders — and one declaration per encoding × shape:
   `flat-numeric` and `card-tokens` on each. `build_encoder` looks a pair up by name; a rung is a name in
   `training`'s registry, never a branch here (D-3, `ladder.md` §2, §4, `encoder.md` §4).
2. **One `encode`, one `legal_indices`, one `decode_action`.** Both encodings and both shapes are written by
   the one `encode` of `encode.py`, driven by the block table's writer tags. A second encode path — a
   per-encoding or per-shape function, a subclass, a fork — is a D-3 violation the unit battery holds.
3. **The block order is the field order.** In both encodings the blocks appear in the order of the spec's
   `fields`, which is the readout's own order less `legal` and `hand_class` (`encoder.md` §3).
4. **The pad is id `0`, and only the board and the history pad** (`card-tokens.md` §3).
5. **`flat-numeric` never buckets an amount; `card-tokens` always does.** The dense encoding divides
   and keeps the magnitude; the token encoding resolves it to one id. Both are the representation, and
   neither is a change of fact set (`ladder.md` §4).
6. **The vocabulary is the shape's indices and carries no amount.** A record holds no integer other than
   that shape's own — `0`, `1`, `2` by default, `0`–`5` on `no-limit-100` (`vocabulary.md` §2).
