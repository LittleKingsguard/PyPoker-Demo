# features — L4 guardrails

- **Owner:** one note per risk this design identified, in the order they bite, each with the rule L4
  must hold and the symptom of getting it wrong
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
duplicated in a "shared" helper used by one of them. The battery's "one design" cases are written to
catch exactly that; and the failure is not cosmetic, because the second path is where the two encodings
start to disagree about a fact.

## G2 — The encoder stays opaque

`Encoder` is a class with `__slots__`, no `__eq__`, no dataclass decorator, no `Mapping` base and a
`__repr__` that names only the encoding (`encoder.md` §1). `observation_spec` refuses anything that is not
one; `build_encoder` is the only way to get one.

Symptom: a spec `dict` is accepted by `observation_spec` (the `InvalidEncoder` refusal becomes
unreachable); a caller does `build_encoder("card-tokens") == build_encoder("card-tokens")` and caches on
it; or `encoder["shape"]` works, which means the internals are the surface and D-12 is broken.

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
both); two encodes of one readout differ in one slot. A set used to build a block is the usual cause —
iterate the declared tuple, never a set.

## G6 — `action_space()` carries no integer but `0`, `1` and `2`

The three indices and prose only (`vocabulary.md` §2). No amount, no chip count, no `"raise to 4"`, no
`"sizes": (2, 4)`. **No string in the record contains a digit at all**, which is the form both batteries
can decide: the L1 reader folds integers and all-digit strings, and the unit battery asserts the stronger
"no digit anywhere in any key or value".

Symptom: FAM-2.9 fails with `{0, 1, 2, 4}` — and it fails in a way that looks like a battery bug, because
the reader also folds digit-only strings and mapping keys into the vocabulary it reports. A digit inside
prose escapes the L1 reader and is caught only by the unit battery, which is why the stronger rule is the
one L4 must hold.

## G7 — `legal_indices` is positional, and validates before it maps

One index per descriptor, in the argument's order (`vocabulary.md` §3). Build it as a comprehension over
the argument; never `set(...)`, never `sorted(...)`, never `ACTIONS.index` inside a set, never a fold for
an unknown descriptor. Refuse a `str`, a `set`, a mapping, an iterator and an empty sequence, each naming
what was refused.

Symptom: `legal_indices(("check-call", "raise"))` returns `{0, 1}` or `(0, 1)` because something sorted
the indices — FAM-2.11's one-to-one and FAM-16.10's `{1, 2}` both fail, and `chosen_index` in
`tests/e2e/_surface.py` turns a policy's choice into the wrong index, which shows up as a *later* case
disagreeing about a trajectory rather than as a mask error. `("call",)` must raise naming `'call'`, never
return `(0,)`.

## G8 — `decode_action` maps an index and nothing else, and never coerces

`ACTIONS[index]` after two checks: an `Integral` that is not a `bool`, and `0 <= index <= 2`
(`vocabulary.md` §4). No `int(index)`, no `try: … except: return "fold"`, no clamping a `3` to `2`.

Symptom: `decode_action("1")` returns `"check-call"`; `decode_action(True)` returns `"check-call"`;
`decode_action(3)` returns `"raise"`. It never claims legality, so it must not consult a decision, a
readout or a hand — it has none.

## G9 — Refuse exactly what the contract refuses, before writing anything

Every refusal of `errors.md` §3, and no other (`errors.md` §4). Do not default a missing field to zero, do
not invent a `board` of five pads for a readout that omitted `board` (refuse it by name), do not refuse a
duplicate card, a one-card board, a short history, a `legal` key, or a `numpy` integer. Refuse **before**
the first write so the message is the only observable effect.

Symptom: two directions, and both are failures. Too few: a `KeyError: 'hole'` escapes instead of an
`InvalidReadout` naming the field, or `encode` happily returns an all-zero board for a readout with no
board. Too many: a case that passes a valid instance — a repeated card, `legal` left in the mapping, a
`numpy.int64` pot — is turned into a refusal, and a refusal where the contract has none is a defect
(`battery.md` §4).

## G10 — The pad is `0`, and only two blocks pad

`card-tokens`: an undealt `board` slot and a `history` slot past the end are `0`; nothing else is
(`card-tokens.md` §3). `to_call` of 0 is id `61`, never `0`; a stack of 0 is `77`, never `0`. The dense
encoding has no pad at all — a zero there is a value (`seat` slot 0 for seat 0, `to_call` 0.0).

Symptom: an observation carrying `-1` or `96`; a checkable `to_call == 0` read as the pad, which erases
the difference between "nothing to call" and "no fact"; `history` pad written as `93` (fold).

## G11 — Every returned record is plain, fresh data

`observation_spec`, `encodings` and `action_space` each build and return a **new** plain mapping:
`shape` a tuple of `int`, `dtype` a plain `str` (`"float32"` — not `numpy.dtype("float32")`), `fields` a
tuple in the one declared order, `vocabulary` an `int` or `None` (`encoder.md` §3, §6).

Symptom: a caller mutates a returned spec and a second call returns the mutation (the record is shared);
`encodings()["flat-numeric"] == observation_spec(build_encoder("flat-numeric"))` is `False` because one
path builds a numpy dtype and the other a string; `fields` is a `set` and its order is not stable across
processes.

## G12 — The import boundary: `numpy` and the standard library, nothing else

`layout.md` §3. In particular **no `pokerkit`** — the card spelling is two characters this module parses
itself — and no other project module, not even `engine`, whose three descriptors are restated in
`vocabulary.py` rather than imported.

Symptom: `import features` leaves `'pokerkit' in sys.modules` (the boundary check fails), or `cards.py`
begins `from pokerkit import Card` to understand a readout, which is the D-3 violation G3 of the engine's
own guardrails exists to prevent.

## G13 — One grammar for a history entry, read at fixed positions

ASM-E2's four forms (`README.md` §4), and the verb is the entry's fourth token: `folds` → 0, `checks` and
`calls` → 1, `raises` → 2 (`flat-numeric.md` §5, `card-tokens.md` §5). A `raises` entry has two more
tokens (`to`, `<amount>`), so a parser that assumes five tokens breaks on the one action the ladder cares
most about. A fifth form is refused, naming the entry.

Symptom: a river history mis-read because the street name is compared instead of skipped; a `raises to 8`
entry raising `IndexError`; a `checks` entry counted as a fold because the parser looked for `call`.

## G14 — Nothing below an entry point is surface

`__all__` is exactly the seven names, in the order `layout.md` §2 gives (`README.md` §3). No eighth name
for convenience: not `Encoder`, not `FeaturesError`, not `ACTIONS`, not `ENCODINGS`.

Symptom: a battery or `agents` starts calling `features.ACTIONS`, and the module now has two surfaces, one
of which is not in any L2 document. A caller that needs the vocabulary calls `action_space()`; a caller
that needs an encoder calls `build_encoder`.

## G15 — Run the two batteries, and read the failures

    .venv/bin/python -m pytest tests/features -q                       # this design's unit battery
    .venv/bin/python -m pytest tests/e2e/test_fam02_invariance.py -q    # the L1 share: FAM-2.4-2.11
    .venv/bin/python -m pytest tests/e2e/test_fam16_blind.py -q -k features
    .venv/bin/python -m pytest tests/e2e/test_fam01_surface.py -q -k features

The unit battery is written against this design and is authoritative for the internals; the four e2e
commands are the join with the engine and with `agents`' expectations, and nothing in this module may be
changed to make one of them pass by breaking the other. `tests/e2e/` is read-only for this module.
