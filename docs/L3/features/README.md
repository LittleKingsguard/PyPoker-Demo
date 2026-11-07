# features — module design (L3)

- **Layer:** L3 · **Module:** `features` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-05
- **Realises:** `docs/L2/features/surface.md` (the seven entry points, their refusals and their ordering) and
  `docs/L2/features/encodings.md` (the two encodings, the nine carried fields, the contracts at the engine
  and `agents` edges)
- **Reads:** `docs/L1/e2e-surface.md` §1, §2, §3.2, §5, `docs/L1/records.md` §1, §2, §4, §6,
  `docs/L1/ladder.md` §2–§5, `docs/L1/module-map.md` §2–§3, `docs/L1/battery.md` §2–§4,
  `docs/L1/assumptions.md` (ASM-2, ASM-6, ASM-7, ASM-9, ASM-10), `strata/decisions.md` (D-1, D-2, D-3,
  D-12, D-13, D-15); and, as inherited fact and never as code, `docs/L3/engine/README.md` §4,
  `docs/L3/engine/readout.md` §2–§3, `docs/L3/engine/history.md` §1, `docs/L3/engine/actions.md` §1–§2
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
- **Implements:** `src/features/` (written by L4, never by L3). `tests/features/` is this design's unit
  battery; `tests/e2e/test_fam0{1,2}_*.py` and `test_fam16_blind.py` are the L1 battery's share for it

## 1. What this module is

`features` is the ladder's representation axis (D-3) and nothing else. It turns one readout into one
observation, and one action index into one action descriptor. The game, the information set and the
three-index vocabulary are held constant for every rung; what this module varies is how the same nine
facts are spelled (`docs/L2/features/encodings.md` §1).

It imports `numpy` and the Python standard library and **nothing else** — never `pokerkit`, never
`torch`, never another project module (`module-map.md` §3, `layout.md` §3). A readout arrives as a
mapping and leaves as an array; the two encodings are two rows of one declaration table, not two
code paths (`encoder.md` §4, `card-tokens.md` §1).

## 2. The documents, one per owner

| Document | Owner of that question | What it fixes |
|---|---|---|
| `encoder.md` | the encoder and the observation spec | the opaque `Encoder` value, `build_encoder`/`observation_spec`/`encodings`, the six spec keys, and the one declaration table both encodings are rows of |
| `flat-numeric.md` | the dense encoding | block order, slot order inside each block, the card→slot map, the amount normalisers, the history slot, and the arithmetic that sums to 203 |
| `card-tokens.md` | the token encoding | token order, the card→id map, the bucket edges of the five bucketed blocks, the pad, and the arithmetic that sums to 40 tokens over 96 ids |
| `vocabulary.md` | the action axis | the three-index vocabulary, `action_space`'s record, `legal_indices`' positional alignment, `decode_action`, and what is not a descriptor |
| `errors.md` | refusals | the error hierarchy and the message grammar every refusal follows, and what is deliberately *not* refused |
| `layout.md` | the files | the file layout of `src/features/`, the seven exported names, and the import boundary |
| `guardrails.md` | L4 | one numbered note per risk this design identified, in the order they bite |

## 3. The seven names, and what is *not* a name

`src/features/__init__.py` exports exactly the seven entry points of `e2e-surface.md` §3.2, declares
them in `__all__`, and adds, removes and renames none (D-12):

    encodings()                        -> Mapping            # name -> spec record, ladder order
    build_encoder(name)                -> Encoder            # opaque value
    observation_spec(encoder)          -> Mapping            # the six-key spec record
    encode(encoder, readout)           -> numpy.ndarray       # one observation
    action_space()                     -> Mapping            # keys 0, 1, 2
    legal_indices(legal_actions)       -> tuple[int, ...]
    decode_action(index)               -> str

`Encoder`, `FeaturesError` and its six subclasses, the declaration table, the block tables, the card
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
  ever leaves the engine (`docs/L3/engine/readout.md` §3). `features` **parses** this spelling
  (`cards.py`); it never imports the library that produced it.
- **ASM-E2 — the history entry grammar.** A history entry is a plain `str` of one grammar and carries
  no card (`docs/L3/engine/history.md` §1): `"<street> seat <index> folds"`, `"… checks"`,
  `"… calls <amount>"`, `"… raises to <amount>"`. The encoding reads the **verb** (and checks the form's
  own shape) and carries neither the street, the seat nor the amount: a fifth form is refused by name
  (`history.py`, `flat-numeric.md` §5).
- **Seat order.** Engine seat 0 is the button, and every per-seat fact (`seat`, `stacks`, a history
  entry's `<index>`) is in engine seat order (`docs/L3/engine/README.md` §4, `readout.md` §2).
- **The descriptor spelling.** `"fold"`, `"check-call"`, `"raise"` — the same three `str`s
  `engine.apply_action` accepts, in ascending index order, at most one per index
  (`docs/L3/engine/actions.md` §1, `docs/L3/engine/stepping.md` §1). That is why
  `legal_indices` is positional and never a lookup (`vocabulary.md` §2).
- **The readout's value shapes** — the exact types `encode` reads, and the only ten keys that exist:

| Key | The value this module receives |
|---|---|
| `street` | `str`: `"preflop"`, `"flop"`, `"turn"` or `"river"` |
| `seat` | `tuple[int, bool]`: the acting seat's index, then whether it holds the button |
| `hole` | `tuple[str, str]`: the acting seat's two cards |
| `board` | `tuple[str, ...]`: length 0, 3, 4 or 5 |
| `stacks` | `tuple[int, int]`: chips behind, seat order |
| `pot` | `int`: includes the current street's bets; `pot + sum(stacks) == 40` at every decision |
| `to_call` | `int`: 0 when the acting seat may check, never more than its own stack |
| `limit` | `tuple[int, int]`: the bet size in force (2 or 4), the bet-or-raise actions made this street (0–4, the cap of ASM-6) |
| `history` | `list[str]`: oldest first, empty before the first action, at most 23 entries |
| `legal` | `tuple[str, ...]`: carried by the readout and **not** carried by an observation |

## 5. Decisions a later module must not re-derive

1. **One declaration table is the whole axis.** `src/features/declarations.py` holds two rows —
   `flat-numeric` and `card-tokens` — each a plain record of `representation`, `kind`, `fields`,
   `shape`, `dtype`, `vocabulary` and a **block table**. `build_encoder` looks a row up by name; a
   rung is a name in `training`'s registry, never a branch in this module (D-3, `ladder.md` §2, §4).
2. **One `encode`, one `legal_indices`, one `decode_action`.** Both encodings are written by the one
   `encode` of `encode.py`, driven by the block table's writer tags (`encoder.md` §4). A second
   encode path — a per-encoding function, a subclass, or a fork of the module — is a D-3 violation
   and the unit battery holds this.
3. **The block order is the field order.** In both encodings the blocks appear in the order of the
   spec's `fields`, which is the readout's own order less `legal`. One order exists in the project for
   one fact set (`encoder.md` §3).
4. **The pad is id `0`, and only the board and the history pad.** No other block may emit `0`
   (`card-tokens.md` §3).
5. **`flat-numeric` never buckets an amount; `card-tokens` always does.** The dense encoding divides
   and keeps the magnitude; the token encoding resolves it to one id. Both are the representation, and
   neither is a change of fact set (`ladder.md` §4).
6. **The action vocabulary is three indices and carries no amount.** `action_space()`'s record holds
   no integer other than `0`, `1` and `2` (`vocabulary.md` §2, `battery.md` §3 FAM-2.9).
