# features — L4 guardrails

- **Owner:** one note per risk this design identified, in the order they bite, each with the rule L4
  must hold and the symptom of getting it wrong
- **Rev:** 2 · **Date:** 2026-11-09
- **Ceiling:** 175 lines. At the ceiling, split by owner — never append
- **Read with:** `README.md`, `encoder.md`, `flat-numeric.md`, `card-tokens.md`, `vocabulary.md`,
  `errors.md`, `layout.md`

These are not suggestions. Each one is a place where a plausible, tidy-looking implementation breaks a
contract that the unit battery or the L1 battery asserts.

## G1 — One module, one `encode`: the encodings are rows of a table, never two code paths

Everything that differs between `flat-numeric` and `card-tokens` lives in `declarations.py` — the block
tables, and the writer tags they name (`encoder.md` §4, §5). `encode` is **one** function: look up the
declaration through the encoder, zero an array of the declared shape and dtype, walk the blocks, call the
writer each names. D-3's whole claim — a rung-to-rung difference is attributable to the representation
and to nothing else — is this property.

Symptom of getting it wrong: `_encode_flat` and `_encode_tokens` side by side, or an
`if encoder.name == "flat-numeric": … else: …` in `encode`, or a third of the two encodings' logic
duplicated in a "shared" helper used by one of them — the second path is where the two encodings start to
disagree about a fact, so the battery's "one design" cases are written to catch exactly that.

## G2 — The encoder stays opaque

`Encoder` is a class with `__slots__`, no `__eq__`, no dataclass decorator, no `Mapping` base and a
`__repr__` that names only the encoding (`encoder.md` §1). `observation_spec` refuses anything that is not
one; `build_encoder` is the only way to get one.

Symptom: a spec `dict` is accepted by `observation_spec` (the `InvalidEncoder` refusal becomes unreachable);
a caller caches on `build_encoder("card-tokens") == build_encoder("card-tokens")`; or `encoder["shape"]`
works, which means the internals are the surface and D-12 is broken.

## G3 — Widths, offsets and shapes are the design's numbers, not recomputed

`(203,)` and `(40,)`, the block order = the `fields` order, `history` last in both, the offsets of
`flat-numeric.md` §2 and `card-tokens.md` §2, `vocabulary` 96 (`encoder.md` §3, §4). Derive the offsets
from the table — `offset[i] = offset[i-1] + width[i-1]` — and assert nothing: a hard-coded offset that
drifts from the table is the failure mode, so the table is the single source and `encode` walks it.

Symptom: the declared `shape` and `array.shape` disagree (FAM-2.8, FAM-16.9); a history block starting at
131 in one place and 132 in another; a hole block of 33; a `card-tokens` observation whose history is not
the last 24 tokens.

## G4 — A fresh array, an untouched readout, no cache

Return `numpy.zeros(shape, dtype)` built inside the call, every call; write into it once per block; never
keep it, never write into `readout`, never sort or reorder a list that came from the readout
(`encoder.md` §5, `surface.md` §6).

Symptom: two encodes of one readout are equal but the **same object**, so a learner that scales its input
in place corrupts the next observation; `readout["history"]` comes back reversed or sorted because a
writer called `.sort()`; or a refused encode leaves a half-written observation in a module-level buffer
that the next call returns.

## G5 — No randomness, anywhere, ever

No `import random`, no `numpy.random`, no seeding, no hashing that depends on `PYTHONHASHSEED`-order
iteration of a set (`surface.md` §1, ASM-2). Every one of the seven names is a function of its arguments.

Symptom: `random.getstate()` or `np.random.get_state()` differs after a call (the unit battery compares
both); two encodes of one readout differ in one slot — usually because a set was iterated to build a block.

## G6 — `action_space()` carries no integer but the shape's own indices

A shape's indices and prose only (`vocabulary.md` §2): `0`, `1`, `2` on the default shape and `0`–`5` on
`no-limit-100`, each record built from the shape row the caller asked for. No amount, no chip count, no
`"raise to 4"`, no `"sizes": (2, 4)`, no `"size": 3`; a sized band's note is **prose** — `band`, never the
chips it resolves to. **No string in the record contains a digit at all**, which is the form both batteries
can decide: the L1 reader folds integers and all-digit strings, and the unit battery asserts the stronger
"no digit anywhere in any key or value" on the record each shape returns.

Symptom: FAM-2.9 fails with `{0, 1, 2, 4}`, and it looks like a battery bug because the reader folds
digit-only strings and mapping keys too; a digit inside prose escapes the L1 reader and only the unit
battery catches it.

## G7 — `legal_indices` is positional, per shape, and validates before it maps

One index per descriptor, in the argument's order, read off the one `DESCRIPTOR_INDEX` table built from
every shape's row (`vocabulary.md` §3) — it takes no shape and needs none. Build it as a comprehension over
the argument; never `set(...)`, never `sorted(...)`, never a per-shape branch, never a fold for an unknown
descriptor. Refuse a `str`, a `set`, a mapping, an iterator and an empty sequence, each naming what was
refused.

Symptom: `legal_indices(("check-call", "raise-minimum"))` returns `{1, 5}` or a sorted `(1, 5)` because a set
got involved — FAM-2.11's one-to-one and FAM-16.10's `{1, 2}` fail, and `chosen_index` in
`tests/e2e/_surface.py` turns a policy's choice into the wrong index. `("call",)` must raise naming `'call'`.

## G8 — `decode_action` maps an index in one shape's vocabulary, and never coerces

The shape's `actions[index]` after two checks: an `Integral` that is not a `bool`, and `0 <= index <
len(actions)` — `0–2` by default, `0–5` on `no-limit-100` (`vocabulary.md` §4). No `int(index)`, no `try: …
except: return "fold"`, no clamping a `3` to `2`. The shape is an **argument**, never module state: two
callers may decode in two vocabularies in one process, and an index is meaningful only beside the shape
that declared it.

Symptom: `decode_action("1")` returns `"check-call"`; `decode_action(True)` returns `"check-call"`;
`decode_action(6, shape="no-limit-100")` returns a descriptor instead of refusing. It never claims legality,
so it must not consult a decision, a readout or a hand — it has none.

## G9 — Refuse exactly what the contract refuses, before writing anything

Every refusal of `errors.md` §3, and no other (`errors.md` §4). Do not default a missing field to zero, do
not invent a `board` of five pads for a readout that omitted `board` (refuse it by name), do not refuse a
duplicate card, a one-card board, a short history, a `legal` key, or a `numpy` integer. Refuse **before**
the first write so the message is the only observable effect.

Symptom: two directions, and both are failures. Too few: a `KeyError: 'hole'` escapes instead of an
`InvalidReadout` naming the field. Too many: a case that passes a valid instance — a repeated card, `legal`
left in the mapping, a `numpy.int64` pot — is turned into a refusal (`battery.md` §4).

## G10 — The pad is `0`, and only two blocks pad

`card-tokens`: an undealt `board` slot and a `history` slot past the end are `0`; nothing else is
(`card-tokens.md` §3). `to_call` of 0 is id `61`, never `0`; a stack of 0 is `77`, never `0`. The dense
encoding has no pad at all — a zero there is a value (`seat` slot 0 for seat 0, `to_call` 0.0).

Symptom: an observation carrying `-1` or `96`; a checkable `to_call == 0` read as the pad, erasing the
difference between "nothing to call" and "no fact"; a `history` pad written as `93` (fold).

## G11 — Every returned record is plain, fresh data

`observation_spec`, `encodings` and `action_space` each build and return a **new** plain mapping:
`shape` a tuple of `int`, `dtype` a plain `str` (`"float32"` — not `numpy.dtype("float32")`), `fields` a
tuple in the one declared order, `vocabulary` an `int` or `None` (`encoder.md` §3, §6).

Symptom: a caller mutates a returned spec and a second call returns the mutation (the record is shared);
`encodings()`'s entries stop equalling `observation_spec`'s; a `fields` that is a `set`.

## G12 — The import boundary: `numpy` and the standard library, nothing else

`layout.md` §3. In particular **no `pokerkit`** — the card spelling is two characters this module parses
itself — and no other project module, not even `engine`, whose descriptors and shape rows are restated in
`vocabulary.py` and `declarations.py` rather than imported.

Symptom: `import features` leaves `'pokerkit'` or `engine` in `sys.modules`.

## G13 — One grammar for a history entry, read at fixed positions

ASM-E2's four forms (`README.md` §4), and the verb is the entry's fourth token: `folds` → 0, `checks` and
`calls` → 1, `raises` → 2 (`flat-numeric.md` §5, `card-tokens.md` §5) — the action **kind**, never a
vocabulary index. A `raises` entry has two more tokens (`to`, `<amount>`), so a parser that assumes five
breaks on the action the ladder cares most about; a fifth form is refused, naming the entry.

Symptom: a river history mis-read because the street name is compared instead of skipped; a `raises to 8`
entry raising `IndexError`; a `raises` entry's id read as a vocabulary index, which the second shape denies.

## G14 — Nothing below an entry point is surface

`__all__` is exactly the seven names, in `layout.md` §2's order (`README.md` §3) — no eighth, not `Encoder`,
not `FeaturesError`, not `DESCRIPTOR_INDEX`, not `SHAPE_ROWS`.

Symptom: a battery or `agents` starts calling `features.SHAPE_ROWS`, and the module has two surfaces.

## G15 — Run the two batteries, and read the failures

    .venv/bin/python -m pytest tests/features -q                       # this design's unit battery
    .venv/bin/python -m pytest tests/e2e/test_fam02_invariance.py -q    # the L1 share: FAM-2.4-2.11
    .venv/bin/python -m pytest tests/e2e/test_fam16_blind.py -q -k features
    .venv/bin/python -m pytest tests/e2e/test_fam01_surface.py -q -k features

The unit battery is authoritative for the internals; the four e2e commands are the join with the engine and
with `agents`' expectations, and neither may be broken to make the other pass.

## G16 — One shape row, and no `engine` import

Each shape's descriptors, normalisers and ladders are written down **once**, in `declarations.SHAPE_ROWS`
(`encoder.md` §4); a second spelling in `src/features/` — a divisor in a writer, an edge in a block table, a
descriptor tuple in `vocabulary.py` — is the defect, because the two statements then drift and no battery can
say which one an observation was built from. `engine.game_shapes()` is the other statement, joined by the
battery and never by an import (`layout.md` §3, G12).

Symptom: a divisor edited in the shape row but not in the writer that reads it; `engine` in `sys.modules`.
