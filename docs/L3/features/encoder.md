# features — the encoder and the observation spec

- **Owner:** the opaque `Encoder` value, the three names that produce and describe one
  (`build_encoder`, `observation_spec`, `encodings`), the six keys of a spec record, and the **one
  declaration table** both encodings are rows of, on either declared shape
- **Rev:** 2 · **Date:** 2026-11-09
- **Ceiling:** 165 lines. At the ceiling, split by owner — never append

## 1. The encoder is an opaque value, and it is a class

    class Encoder:                       # src/features/encoder.py, not surface (layout.md §2)
        __slots__ = ("_name", "_shape", "_declaration")

`Encoder` holds three things and offers no way to read any of them: the encoding's **name**, the **shape**
it was built for, and the **declaration record** `build_encoder` found under that pair (`declarations.py`,
§4). The shape is not readable from outside either — a caller names it to `build_encoder` and reads its
effect through `encode` — and the type is not a `dict`, not a `str`, not a tuple, not a `namedtuple`:

- not a **plain mapping**, because a mapping cannot be told from a spec, and `observation_spec` must refuse
  "a value that is not an encoder this module built" (`surface.md` §5) — decidable only if it is a type;
- not a **name string**, because then any caller could manufacture an encoder without `build_encoder`, and
  "an encoder exists only by a declared encoding" (`surface.md` §4, `e2e-surface.md` §5) would be a
  convention instead of a fact — nor a **frozen dataclass or a `Mapping` subclass**, which hand a caller the
  internals the contract says no caller may inspect (`surface.md` §1).

Two consequences L4 must respect, and the battery holds (`guardrails.md` G2): **equality is identity** —
`Encoder` defines no `__eq__` and no `__hash__` override, so two encoders built from one name are two values
that declare **equal specs** and encode one readout to **equal observations** (`surface.md` §4), and nothing
compares encoders; and **`__repr__` names the encoding and nothing else** — `Encoder('flat-numeric')`, a
debugging aid and not a surface, since no entry point returns an encoder and no case reads one.

## 2. `build_encoder(name, *, shape=None)`

    def build_encoder(name: str, *, shape=None) -> Encoder

    refuse unless isinstance(name, str) and name in ENCODING_NAMES        # UnknownEncoding, errors.md §3
    shape = the default shape when the argument is absent                 # absence, not a defaulted name
    refuse a name outside the catalogue, naming it and the declared names              # UnknownShape
    return Encoder(name, shape, declaration(name, shape))                 # draws nothing, holds no state

The name is matched **exactly**: one of `"flat-numeric"` and `"card-tokens"`, case-sensitive and not
stripped, because a spelling that is not the declared one is a different thing (`ladder.md` §3, `surface.md`
§4). There is no seed, size or rung parameter by which a representation could be varied (ASM-2).

**Why `shape` is keyword-only.** The pre-existing arity cases pin `build_encoder`'s one positional argument,
and a keyword-only optional adds the shape without moving it, so no fixed-limit case is weakened to admit
the second shape (D-11, `shapes.md` §5, `vocabulary.md` §4). An absent shape is the **default** shape; a name
outside the catalogue is refused, never defaulted (`shapes.md` §2).

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

No seventh key, and none naming a shape or a divisor: the six values are **shape-invariant** — slot counts,
block widths, dtype and token vocabulary are the same on both shapes (`sizing.md` §5,
`docs/L2/features/shapes.md` §5) — so the record never names the shape that built it (`encodings()`, §6).

### 3.1 The `fields` tuple, and why its order is fixed

    ("street", "seat", "hole", "board", "stacks", "pot", "to_call", "limit", "history")

The readout's eleven facts less `legal` and D-21's derived `hand_class`, **in the readout's own
order** (`README.md` §4, `encodings.md` §2, `folders.md` §3, ASM-30). Neither is carried: a decision's
legal set reaches a policy beside the observation, as `legal_indices`' mask (`vocabulary.md` §3), and
`hand_class` is a function of `hole` and `board`, which the nine below already carry (FAM-2.13).

This tuple is also the **block order of both encodings**, on both shapes (§4): one order exists in the
project for one fact set, so a reader who knows the field order knows where every fact sits
(`README.md` §5). Rejected: the L2 table's row order for `card-tokens` (cards first), which would give one
fact set two orders.

## 4. The declaration table — `src/features/declarations.py`, keyed encoding × shape

    SHAPE_ROWS = {                       # the catalogue's order, default first (shapes.md §2)
        "fixed-limit-20": <shape row>,   # three descriptors, ASM-6's normalisers and ladders
        "no-limit-100":   <shape row>,   # six descriptors, the sized bands' (D-27, D-29)
    }                                    # and ENCODING_NAMES = ("flat-numeric", "card-tokens"), ladder order

A **shape row** is this module's single statement of what a shape varies (`shapes.md` §2, `sizing.md` §5):

| Key | Content |
|---|---|
| `actions` | the descriptors in the shape's own index order (`vocabulary.md` §1) |
| `normalisers` | the five divisors under `engine`'s own key names — `stack`, `pot`, `to_call`, `amount`, `count` (`flat-numeric.md` §4) |
| `ladders` | the five bucket ladders of the token encoding, over the ids `card-tokens.md` §4 fixes |
| `default` | the flag that makes exactly one row the default (§2) |

Those divisors and edges are **restated, not imported**: this module imports no other project module
(`layout.md` §3, `guardrails.md` G12), so `SHAPE_ROWS` repeats what `engine.game_shapes()` publishes and the
join battery is what holds the two statements equal (D-13, `guardrails.md` G16).

A **declaration** is one encoding **on one shape** — a plain record with the six spec keys of §3 plus one:

| Key | Content |
|---|---|
| `representation`, `kind`, `fields`, `shape`, `dtype`, `vocabulary` | the six values §3 fixes, verbatim |
| `blocks` | a `tuple` of block records, one per entry of `fields`, **in that order**, whose widths sum to `shape[0]` |

A **block record** is a 6-tuple `(field, offset, width, writer, reads, params)`:

- `field`, `offset`, `width` — the readout key it writes (one of §3.1's nine); the first slot it writes,
  `sum of the widths before it`; and the slots it writes (for `card-tokens`, how many tokens);
- `writer` — one **tag** naming a block writer of `encode.py`'s closed `WRITERS` table (§5);
- `reads` — the readout keys that writer reads: `(field,)` for every block but one, the dense `stacks` block
  declaring `("stacks", "seat")` because L2 fixes its slot order (`encodings.md` §3), keeping that one
  dependency visible in the table;
- `params` — the writer's own constants, and for the five amount blocks **the shape row's**: the normalisers
  of `flat-numeric.md` §4 and the ladders of `card-tokens.md` §4.

The offsets are **derived, never chosen**: `flat-numeric`'s are `0, 4, 6, 40, 125, 127, 128, 129, 131` and
`card-tokens`'s `0, 1, 3, 5, 10, 12, 13, 14, 16` — the same on both shapes (`flat-numeric.md` §2,
`card-tokens.md` §2). A third encoding, or a third shape, is a row in this one table — never a new module.

## 5. `encode` — one loop, two writer families

    def encode(encoder: Encoder, readout: Mapping) -> numpy.ndarray

    refuse unless isinstance(encoder, Encoder)                              # InvalidEncoder
    refuse unless isinstance(readout, Mapping)                              # InvalidReadout
    declaration = encoder's declaration                                     # encoding x its shape
    for field in declaration.fields:
        refuse unless field in readout, naming that field                   # InvalidReadout
    out = numpy.zeros(declaration.shape, dtype=declaration.dtype)           # FRESH, every call
    for (field, offset, width, writer, reads, params) in declaration.blocks:
        values = WRITERS[writer](readout, reads, params)                    # width values, a list
        out[offset : offset + width] = values
    return out

Four rules hold of this loop and are what makes "one design, two encodings" true rather than a slogan:

1. **Nothing in the loop names an encoding or a shape.** It reads the declaration; the only per-encoding and
   per-shape data are the block tables and the `params` they carry (`README.md` §5).
2. **A writer is a pure function of the values it declares it reads.** It returns exactly `width` values,
   refuses a value it cannot represent instead of clamping or substituting, returns a **fresh** sequence, and
   reads no readout key outside its block's `reads` (`errors.md` §3).
3. **Zeroed first, written second**: a slot no writer touches stays `0` — the undealt board slots, the
   past-the-end history slots and `card-tokens`' pad (`card-tokens.md` §3).
4. **Fresh array, untouched argument**: never a module-level buffer, never an in-place write back into
   `readout`, never a cached observation (FAM-16.9 compares two encodes of one readout value for value).

`legal` and `hand_class` are in every readout and are never read: a key the encoding does not carry is
**ignored and not refused**, and any other extra key with it (`surface.md` §6, `folders.md` §3).

## 6. `encodings()`

    def encodings() -> dict

    return {name: observation_spec(build_encoder(name)) for name in ENCODING_NAMES}   # fresh dict

No argument, and it needs none: a spec record is shape-invariant (§3), so the catalogue is one mapping for
both shapes and a shape parameter would declare a difference that does not exist (`sizing.md` §5). Its order
is the ladder's — `flat-numeric` then `card-tokens` (`ladder.md` §2) — and each value equals both
`observation_spec(build_encoder(name))` and the other shape's encoder's spec, which pins the invariance.
