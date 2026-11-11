# features — module design (L3)

- **Layer:** L3 · **Module:** `features` · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-10
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
- **Realises:** `docs/L2/features/surface.md` (the seven entry points, their refusals and their ordering),
  `docs/L2/features/encodings.md` (the two encodings, the nine carried fields, the contracts at the engine
  and `agents` edges) and `docs/L2/features/shapes.md` (the game shape as this module's own data, three
  rows: the two-seat pair and D-33's six-seat one)
- **Reads:** `docs/L1/e2e-surface.md` §1, §2, §3.2, §5, `docs/L1/shapes.md` §2, §5, §8, `docs/L1/seats.md` §2, §3,
  `docs/L1/sizing.md` §3, §5, `docs/L1/folders.md` §3, `docs/L1/records.md` §1, §2, §4, §6,
  `docs/L1/ladder.md` §2–§5, `docs/L1/module-map.md` §2–§3, `docs/L1/battery.md` §2–§4,
  `docs/L1/assumptions.md` (ASM-2, ASM-6, ASM-7, ASM-9, ASM-10, ASM-30, ASM-39, ASM-42, ASM-44),
  `strata/decisions.md` (D-1, D-2, D-3, D-12, D-13, D-15, D-21, D-33); and at the consumed edge
  `docs/L3/engine/README.md` §4, `docs/L3/engine/{readout,history,actions}.md` §2–§3, §1, §1–§2 (D-13)
- **Implements:** `src/features/` (written by L4, never by L3). `tests/features/` is this design's unit
  battery; `tests/e2e/test_fam0{1,2}_*.py` and `test_fam16_blind.py` are the L1 battery's share for it

## 1. What this module is

`features` is the ladder's representation axis (D-3) and nothing else. It turns one readout into one observation, and one
action index into one action descriptor. The information set and the **shape's** action vocabulary are held constant for
every rung, and the ladder holds one game; what this module varies is how the same nine facts are spelled
(`docs/L2/features/encodings.md` §1). The other two declared shapes are data — rows of `declarations.SHAPE_ROWS`,
restated rather than imported — and never a second module (`docs/L2/features/shapes.md` §1, `capacity.md` §1, `encoder.md` §4).

It imports `numpy` and the Python standard library and **nothing else** — never `pokerkit`, never `torch`, never
another project module (`module-map.md` §3, `layout.md` §3, `guardrails.md` G16). A readout arrives as a mapping, leaves
as an array, and the two encodings are two rows of one declaration table, not two code paths (`encoder.md` §4).

## 2. The documents, one per owner

| Document | Owner of that question | What it fixes |
|---|---|---|
| `encoder.md` | the encoder and the observation spec | the opaque `Encoder` value, `build_encoder`/`observation_spec`/`encodings`, the six spec keys — four shape-invariant, `shape` and `vocabulary` the shape's own — and the one declaration table, keyed encoding × shape |
| `flat-numeric.md` | the dense encoding | block order, slot order inside each block, the card→slot map, the amount normalisers **per shape**, both per-seat blocks' modes, the history slot over the shape's capacity, and the arithmetic that sums to 203, 329 and 433 |
| `card-tokens.md` | the token encoding | token order, the card→id map, the bucket edges of the five bucketed blocks **per shape**, the pad, the shape's token vocabulary, and the arithmetic that sums to 40, 82 and 122 tokens over 96, 96 and 102 ids |
| `vocabulary.md` | the action axis | the shape's vocabulary and its record per shape, `legal_indices`' positional alignment, `decode_action`, and what is not a descriptor |
| `errors.md` | refusals | the error hierarchy and the message grammar every refusal follows, and what is deliberately *not* refused |
| `layout.md` | the files | the file layout of `src/features/`, the seven exported names, and the import boundary |
| `guardrails.md` | L4 | one numbered note per risk this design identified, in the order they bite |

## 3. The seven names, and what is *not* a name

`src/features/__init__.py` exports exactly the seven entry points of `e2e-surface.md` §3.2, declares them in
`__all__`, and adds, removes and renames none (D-12):

    encodings()                        -> Mapping            # name -> spec record, default shape's widths
    build_encoder(name, *, shape=None) -> Encoder            # opaque value, on one declared shape
    observation_spec(encoder)          -> Mapping            # the six keys, `shape` and `vocabulary` the shape's
    encode(encoder, readout)           -> numpy.ndarray       # one observation
    action_space(*, shape=None)        -> Mapping            # the shape's indices, in its declared order
    legal_indices(legal_actions)       -> tuple[int, ...]     # no shape: each descriptor has its index
    decode_action(index, *, shape=None) -> str                # the shape's vocabulary decides 0-2 or 0-5

The three widened names take `shape` as a **keyword-only** argument because the pre-existing arity cases pin each name's
positional argument, and a keyword-only optional adds the shape without moving any of them (D-11, `shapes.md` §5,
`vocabulary.md` §4); an absent one is the default shape, `fixed-limit-20`.

`Encoder`, `FeaturesError` and its seven subclasses, the declaration table, the block tables, the card map, the bucket
edges, the history parser and every helper below an entry point are **not** surface (`e2e-surface.md` §1,
`surface.md` §1). A caller reaches an encoder only through `build_encoder`, and inspects it through
`observation_spec` — never by reading its attributes.

Every rule that holds of all seven — an invalid argument raises an error naming the violated contract, no coercion,
no substituted default, no swallowed error, no partial record, no randomness, no seed argument — is
`docs/L2/features/surface.md` §1 and is not restated here.

## 4. The facts this module inherits, and must not re-derive

`docs/L3/engine/` fixed these, and this design consumes them as values (`encodings.md` §5, D-13):

- **ASM-E1 — the card spelling.** A card is a two-character plain `str`: rank first from
  `"23456789TJQKA"`, suit second from `"cdhs"` — `"As"`, `"Td"`, `"2c"`, `"Kh"`. No `pokerkit` object
  ever leaves the engine (`docs/L3/engine/readout.md` §3). `features` **parses** it in `cards.py`, on every
  row of the catalogue, and never imports the library that produced it.
- **ASM-E2 — the history entry grammar.** A history entry is a plain `str` of one grammar and carries
  no card (`docs/L3/engine/history.md` §1): `"<street> seat <index> folds"`, `"… checks"`,
  `"… calls <amount>"`, `"… raises to <amount>"`. The encoding reads the **verb** (and checks the form's
  own shape) and carries neither the street, the seat nor the amount: a fifth form is refused by name
  (`history.py`, `flat-numeric.md` §5).
- **Seat order.** Engine seat 0 is the button, and every per-seat fact (`seat`, `stacks`, a history
  entry's `<index>`) is in engine seat order (`docs/L3/engine/README.md` §4, `readout.md` §2).
- **The descriptor spelling.** `"fold"`, `"check-call"`, `"raise"` on `fixed-limit-20` — the same `str`s
  `engine.apply_action` accepts, and the shape's own further descriptors (`"raise-quarter"`,
  `"raise-half"`, `"raise-all-in"`, `"raise-minimum"`) on the two uncapped rows, each with its own index
  (`docs/L3/engine/actions.md` §1, `vocabulary.md` §1). That is why `legal_indices` is positional.
- **The readout's value shapes** — the exact types `encode` reads, and the only eleven keys that exist:

| Key | The value this module receives |
|---|---|
| `street` | `str`: `"preflop"`, `"flop"`, `"turn"` or `"river"` |
| `seat` | `tuple[int, bool]`: the acting seat's index — `0` to `seats − 1`, so `0` or `1` on a two-seat row and `0`–`5` on the six-seat one — then whether it holds the button (`seats.md` §3, ASM-44) |
| `hole` | `tuple[str, str]`: the acting seat's two cards |
| `board` | `tuple[str, ...]`: length 0, 3, 4 or 5 |
| `stacks` | `tuple[int, ...]`: chips behind, one entry per seat in seat order — two or six (`seats.md` §3, ASM-44) |
| `pot` | `int`: includes the current street's bets; `pot + sum(stacks)` is the shape's chips in play — 40 on `fixed-limit-20`, 200 on `no-limit-100`, 600 on the six-seat row |
| `to_call` | `int`: 0 when the acting seat may check, never more than its own stack |
| `limit` | `tuple[int, int]`: the amount in force — 2 or 4 on `fixed-limit-20`, the minimum legal raise-to on the two uncapped rows — and the bet-or-raise actions this street (0–4 under ASM-6's cap; bounded by the stack otherwise) |
| `history` | `list[str]`: oldest first, empty before the first action, at most the shape's capacity — 24 on `fixed-limit-20` and 66 and 98 on the two uncapped rows, the block's own capacity and refusal threshold; ASM-6's cap makes 23 the default shape's hand maximum (`capacity.md` §1, `flat-numeric.md` §5) |
| `legal` | `tuple[str, ...]`: carried by the readout and **not** carried by an observation |
| `hand_class` | `int` or `None`: the acting seat's best five-card hand of `hole` plus `board`, `None` before the flop — a derived fact **no** encoding carries (`encodings.md` §2, `folders.md` §3, ASM-30) |

## 5. Decisions a later module must not re-derive

1. **One declaration table is the whole axis.** `src/features/declarations.py` holds one **shape row** per declared
   shape — seats, both per-seat modes, vocabulary, descriptors, five normalisers, five ladders — and one declaration
   per encoding × shape: `flat-numeric` and `card-tokens` on each of the three. `build_encoder` looks a pair up by
   name; a rung is a name in `training`'s registry, never a branch here (D-3, `ladder.md` §2, §4, ASM-44).
2. **One `encode`, one `legal_indices`, one `decode_action`.** Both encodings on all three rows are written by
   the one `encode` of `encode.py`, driven by the block table's writer tags. A second encode path — a
   per-encoding or per-shape function, a subclass, a fork — is a D-3 violation the unit battery holds.
3. **The block order is the field order.** In both encodings the blocks appear in the order of the spec's
   `fields`, which is the readout's own order less `legal` and `hand_class` (`encoder.md` §3).
4. **The pad is id `0`, and only the board, the history and a `one-hot` `seat` block's non-acting slots
   pad** (`card-tokens.md` §3, `seats.md` §3).
5. **`flat-numeric` never buckets an amount; `card-tokens` always does.** The dense encoding divides
   and keeps the magnitude; the token encoding resolves it to one id. Both are the representation, and
   neither is a change of fact set (`ladder.md` §4).
6. **The vocabulary is the shape's indices and carries no amount.** A record holds no integer other than
   that shape's own — `0`, `1`, `2` by default, `0`–`5` on the two uncapped rows (`vocabulary.md` §2, D-33).
