# features — the file layout

- **Owner:** what lives where under `src/features/`, which names the package exports, and which imports
  are allowed
- **Ceiling:** 95 lines. At the ceiling, split by owner — never append

## 1. The files

    src/features/__init__.py        the seven entry points, and nothing else (§2)
    src/features/errors.py          FeaturesError and its six subclasses (errors.md §2)
    src/features/cards.py           RANKS, SUITS, parse_card(), card_slot(), card_id() — the one
                                    reading of ASM-E1's spelling (README.md §4, flat-numeric.md §3)
    src/features/declarations.py    ENCODINGS: the two declared encodings, their block tables and
                                    the constants those tables are written from (encoder.md §4)
    src/features/encoder.py         Encoder, build_encoder(), observation_spec(), encodings()
    src/features/encode.py          encode(), the one writer loop, and WRITERS — the closed set of
                                    block writers the block tables name (encoder.md §5)
    src/features/history.py         action_of_entry() — ASM-E2's grammar read as one action index
    src/features/vocabulary.py      ACTIONS, action_space(), legal_indices(), decode_action()

Eight files, one concern each. A ninth file is allowed only if a document in this directory says what
it owns; a file that exists to hold one helper is a sign the owner is missing, not a sign the layout is
wrong. `src/features/` holds no test file, no fixture and no data file: the declaration table is code,
and the encodings are declared in it, not in JSON.

## 2. What the package exports

`src/features/__init__.py` defines (or imports under a private alias and re-exports) **exactly** the
seven entry points of `README.md` §3, and declares them in `__all__`, in this order:

    __all__ = (
        "encodings",
        "build_encoder",
        "observation_spec",
        "encode",
        "action_space",
        "legal_indices",
        "decode_action",
    )

    from . import encoder    as _encoder       # private module binding, so features.<submodule>
    from . import encode     as _encode        # stays reachable without becoming surface
    from . import vocabulary as _vocabulary
    ...

    def encodings() -> dict:                  return _encoder.encodings()
    def build_encoder(name):                  return _encoder.build_encoder(name)
    def observation_spec(encoder):            return _encoder.observation_spec(encoder)
    def encode(encoder, readout):             return _encode.encode(encoder, readout)
    def action_space() -> dict:               return _vocabulary.action_space()
    def legal_indices(legal_actions):         return _vocabulary.legal_indices(legal_actions)
    def decode_action(index) -> str:          return _vocabulary.decode_action(index)

No eighth public name: not `Encoder`, not `FeaturesError`, not `ENCODINGS`, not `ACTIONS`, not
`numpy`. The thin wrapper is deliberate and mirrors `docs/L3/engine/layout.md` §2: the entry point is a
module-level name of the package, and each validation rule has **one** home — never both a wrapper and
an owner module, and never a re-check that could drift.

`import features` must leave `pokerkit`, `torch` and every other project module absent from
`sys.modules`; that is the verifiable form of §3 and the first thing the battery checks.

## 3. The import boundary — a hard rule, not a preference

`features` imports:

- `numpy` (array construction and the two dtypes, nothing else), and the Python standard library
  (`collections.abc` for `Mapping`/`Sequence`, `numbers` for `Integral`, `re` for the history grammar,
  `typing`).

and **nothing else**. Never `pokerkit`, never `torch`, never `engine`, `agents`, `evaluation`,
`training` or `harness`, and never a `tests/` helper (`module-map.md` §3, `features/README.md` §3,
D-1, D-13). The module also carries no `random` import and no call into `numpy.random`: the seven names
are functions of their arguments alone (ASM-2, `surface.md` §1).

The package must be importable as a plain package under `src/` with no `pyproject.toml`: the L1 battery
reaches it with `sys.path.insert(0, "<repo>/src")` (`tests/e2e/_surface.py`), and `tests/features/` must
reach it the same way — no `tests/conftest.py` exists and this module's battery may not create one.

## 4. Where the design stops

Function bodies are L4's. This directory fixes: the seven names and their arguments and returns; the
value types (an opaque `Encoder`, a `dict` spec whose shape is a `tuple` and whose dtype is a plain
`str`, a `dict` action space, a `tuple` of indices, three `str` descriptors, a `numpy.ndarray`
observation); the declaration and block tables, including every offset, width, id and bucket edge; the
card map; the error grammar; and the file/import layout. Anything else — helper
names, private constants, docstring style, the order of two independent statements, whether a check sits
in the wrapper or the owner module — is L4's, and is not a finding against this design unless it breaks
one of the rules above (`guardrails.md`).
