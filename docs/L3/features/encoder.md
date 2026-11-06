# features — the encoder and the observation spec

- **Owner:** the opaque `Encoder` value, the three names that produce and describe one
  (`build_encoder`, `observation_spec`, `encodings`), the six keys of a spec record, and the **one
  declaration table** both encodings are rows of
- **Ceiling:** 165 lines. At the ceiling, split by owner — never append

## 1. The encoder is an opaque value, and it is a class

    class Encoder:                       # src/features/encoder.py, not surface (layout.md §2)
        __slots__ = ("_name", "_declaration")

`Encoder` holds two things and offers no way to read either: the encoding's **name** and the
**declaration record** `build_encoder` found under it (`declarations.py`, §4). It is not a `dict`, not
a `str`, not a tuple, and not a `namedtuple`:

- not a **plain mapping**, because a mapping cannot be told from a spec, and `observation_spec` must
  refuse "a value that is not an encoder this module built" (`surface.md` §5) — a refusal that is only
  decidable if an encoder is a type of its own;
- not a **name string**, because then any caller could manufacture an encoder without
  `build_encoder`, and "an encoder exists only by a declared encoding" (`surface.md` §4,
  `e2e-surface.md` §5) would be a convention instead of a fact;
- not a **frozen dataclass or a `Mapping` subclass**, because both hand a caller the internals the
  contract says no caller may inspect (`surface.md` §1).

Two consequences L4 must respect, and the battery holds (`guardrails.md` G2):

- **equality is identity.** `Encoder` defines no `__eq__` and no `__hash__` override, so two encoders
  built from one name are two values that declare **equal specs** and encode one readout to **equal
  observations** (`surface.md` §4). Nothing compares encoders, and the battery never does.
- **`__repr__` names the encoding and nothing else** — `Encoder('flat-numeric')`. It is a debugging
  aid, not a surface: no entry point returns an encoder, and no case reads one.

## 2. `build_encoder(name)`

    def build_encoder(name: str) -> Encoder

    refuse unless isinstance(name, str) and name in ENCODINGS      # UnknownEncoding, errors.md §3
    return Encoder(name, ENCODINGS[name])                          # draws nothing, holds no state

The name is matched **exactly**: one of `"flat-numeric"` and `"card-tokens"`, case-sensitive and not
stripped, because a variant entry names an encoding and a spelling that is not the declared one is a
different thing (`ladder.md` §3, `surface.md` §4). There is no seed, size or rung parameter by which a
representation could be varied (`ladder.md` §2, ASM-2).

## 3. `observation_spec(encoder)` and the six keys

    def observation_spec(encoder: Encoder) -> dict

    refuse unless isinstance(encoder, Encoder)                     # InvalidEncoder, errors.md §3
    return a FRESH plain dict built from the declaration           # plain data, equal on every call

| Key | Value | Why it is that value |
|---|---|---|
| `representation` | `"flat-numeric"` or `"card-tokens"` — a plain `str` | the encoding's own name; FAM-2.6 reads it as that name |
| `kind` | `"dense-numeric"` or `"token-sequence"` | the representation family (`encodings.md` §1) |
| `fields` | a `tuple` of the nine field names, §3.1 | identical for both encodings; that identity is the ladder's fairness condition (FAM-2.4, FAM-2.5) |
| `shape` | a `tuple[int, ...]`: `(203,)` or `(40,)` | one observation's shape (FAM-2.7, FAM-2.8) |
| `dtype` | a plain `str`: `"float32"` or `"int32"` | `agents` does `numpy.dtype(spec["dtype"])`; a numpy dtype object would be a value the spec does not need to carry (`encodings.md` §6) |
| `vocabulary` | `96` for `card-tokens`, `None` for `flat-numeric` | the embedding table's row count `agents` sizes from; `None` because a dense vector has no ids at all (`surface.md` §5) |

No seventh key. The record is plain data on purpose: `encodings()`'s entries are quoted in a report's
header family beside `game_config` (`protocol.md` §1, `surface.md` §1), so every value in it is a
`str`, an `int`, a `tuple` of those, or `None`.

### 3.1 The `fields` tuple, and why its order is fixed

    ("street", "seat", "hole", "board", "stacks", "pot", "to_call", "limit", "history")

The readout's ten facts less `legal`, **in the readout's own order** (`README.md` §4,
`encodings.md` §2). `legal` is not carried: a decision's legal set reaches a policy beside the
observation, as `legal_indices`' mask (`vocabulary.md` §2, FAM-2.9–FAM-2.11).

This tuple is also the **block order of both encodings** (§4): one order exists in the project for one
fact set, so a reader who knows the field order knows where every fact sits in either representation
(`README.md` §5). Rejected: the L2 table's row order for `card-tokens` (cards first). It would give
one fact set two orders and make the token stream's layout a second thing to document and to keep in
step with the dense vector's.

## 4. The declaration table — `src/features/declarations.py`

    ENCODINGS = {                       # ladder order, and the only place an encoding is declared
        "flat-numeric": <declaration>,  # R1, R2 (ladder.md §2)
        "card-tokens":  <declaration>,  # R3-R6
    }

A declaration is a plain record with exactly the six spec keys of §3 plus one more:

| Key | Content |
|---|---|
| `representation`, `kind`, `fields`, `shape`, `dtype`, `vocabulary` | the six values §3 fixes, verbatim |
| `blocks` | a `tuple` of block records, one per entry of `fields`, **in that order**, whose widths sum to `shape[0]` |

A **block record** is a 6-tuple `(field, offset, width, writer, reads, params)`:

- `field` — the readout key it writes, one of §3.1's nine;
- `offset` — the first slot it writes: `sum of the widths before it`, and `0` for the first block;
- `width` — the number of slots it writes (for `card-tokens`, the number of tokens);
- `writer` — one **tag** naming a block writer of `encode.py`'s closed `WRITERS` table (§5);
- `reads` — the readout keys that writer reads: `(field,)` for every block but one; the dense `stacks`
  block declares `("stacks", "seat")` because L2 fixes its slot order as *the acting seat's stack, then
  the other's* (`encodings.md` §3). `reads` is what makes that one dependency visible in the table
  instead of hidden inside a function;
- `params` — the writer's own constants: a divisor, a slot width, a base id, or the edge table of a
  bucket ladder. Plain data, so a reader of the table can check the encoding by reading it.

The offsets are therefore **derived, never chosen**: `flat-numeric`'s are `0, 4, 6, 40, 125, 127,
128, 129, 131` and `card-tokens`'s are `0, 1, 3, 5, 10, 12, 13, 14, 16` (`flat-numeric.md` §2,
`card-tokens.md` §2). The two encodings are two rows of **one** table, and a third encoding would be a
third row — never a third module (D-3, `ladder.md` §2).

## 5. `encode` — one loop, two writer families

    def encode(encoder: Encoder, readout: Mapping) -> numpy.ndarray

    refuse unless isinstance(encoder, Encoder)                              # InvalidEncoder
    refuse unless isinstance(readout, Mapping)                              # InvalidReadout
    declaration = encoder's declaration
    for field in declaration.fields:
        refuse unless field in readout, naming that field                   # InvalidReadout
    out = numpy.zeros(declaration.shape, dtype=declaration.dtype)            # FRESH, every call
    for (field, offset, width, writer, reads, params) in declaration.blocks:
        values = WRITERS[writer](readout, reads, params)                     # width values, a list
        out[offset : offset + width] = values
    return out

Four rules hold of this loop and are what makes "one design, two encodings" true rather than a slogan:

1. **Nothing in the loop names an encoding.** The loop reads the declaration; the only per-encoding
   data are the block tables and the writer tags they name (`README.md` §5 rule 2).
2. **A writer is a pure function of the values it declares it reads.** It returns exactly `width`
   values, it refuses a value it cannot represent (naming the field, `errors.md` §3) instead of
   clamping, defaulting or substituting, it returns a **fresh** sequence, and it reads no readout key
   outside its block's `reads`. A writer that needs another fact declares it in `reads` — which is why
   the dense `stacks` block declares two — and a writer reading a key it did not declare is a defect,
   because the table would then no longer describe the encoding.
3. **Zeroed first, written second**: a slot no writer touches stays `0`, which is what the undealt
   board slots, the past-the-end history slots and `card-tokens`' pad all are (`card-tokens.md` §3).
4. **Fresh array, untouched argument**: never a module-level buffer, never an in-place write back into
   `readout`, never a cached observation. FAM-16.9 compares two encodes of one readout value for value
   (`battery.md` §3).

`legal` is in every readout and is never read: a key the encoding does not carry is **ignored and not
refused** (`surface.md` §6). Any other extra key is ignored the same way.

## 6. `encodings()`

    def encodings() -> dict

    return {name: observation_spec(build_encoder(name)) for name in ENCODINGS}   # fresh dict

No argument, no refusal (`surface.md` §3). The mapping's iteration order is the ladder's: `flat-numeric`
then `card-tokens` (`ladder.md` §2). Each value is **equal to** `observation_spec(build_encoder(name))`
— the same six keys and the same six values, because both are built from the one declaration table,
and a battery may assert that equality directly.
