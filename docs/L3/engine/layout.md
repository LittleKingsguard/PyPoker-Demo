# engine — the file layout

- **Owner:** what lives where under `src/engine/`, which names the package exports, and which imports are allowed
- **Ceiling:** 84 lines — raised from 80 for the third seat count: the eighth error subclass, `seat_map()`/`blind_vector()` in the file table, and the widened `play_hand` wrapper. At the ceiling, split by owner — never append

## 1. The files

    src/engine/__init__.py     the ten entry points, and nothing else (§2)
    src/engine/config.py       the shape catalogue, its helpers (seat_count(), shape_row(),
                               require_shape()), game_shapes() / game_config()
    src/engine/errors.py       EngineError and its eight subclasses (errors.md §2)
    src/engine/cards.py        card_spelling() / parse_card() — the one spelling (readout.md §3)
    src/engine/hand.py         Hand, SEAT_TO_PLAYER, seat_map(), blind_vector(), player_index(),
                               seat_of(), AUTOMATIONS, create_state(), new_hand(), advance(),
                               is_terminal(), payoffs()
    src/engine/actions.py      BASES, SIZED, vocabulary(), raise_interval(), raise_amount(),
                               legal_actions(), apply_action()
    src/engine/readout.py      facts(), readout(), hand_class() and CLASS_OF — the eleven-key mapping (readout.md §2)
    src/engine/episode.py      play_hand(), the seating (POSITIONAL) and the reward placement
    src/engine/equity.py       equity(), the seat count's source and the random save/seed/restore

Nine files, one concern each: `config.py` grew an owner — the catalogue — and did not split. A tenth file
is allowed only if a document here says what it owns; one helper is a sign the owner is missing.

## 2. What the package exports

`src/engine/__init__.py` defines (or imports under a private alias and re-exports) **exactly** the ten
entry points of `README.md` §3, in that document's order, and no eleventh name: not a class, not a
constant, not the error base, not `Hand`, not the shape rows.

    from . import config   as _config      # private module binding, so engine.<submodule> stays
    from . import hand     as _hand        # available without becoming part of the surface
    ...

    def game_shapes():                    return _config.game_shapes()
    def game_config(shape=None):          return _config.game_config(shape)
    def new_hand(seed, shape=None):       return _hand.new_hand(seed, shape)
    def readout(hand):                    return _readout.readout(hand)
    def legal_actions(hand):              return _actions.legal_actions(hand)
    def apply_action(hand, action):       return _actions.apply_action(hand, action)
    def is_terminal(hand):                return _hand.is_terminal(hand)
    def payoffs(hand):                    return _hand.payoffs(hand)
    def play_hand(seed, seat0_policy=None, seat1_policy=None, shape=None, seats=None):
                                          return _episode.play_hand(seed, seat0_policy, seat1_policy, shape, seats)
    def equity(decision, seed, samples):  return _equity.equity(decision, seed, samples)

The thin wrapper is deliberate: the entry point is a module-level name of the package (that is what
`e2e-surface.md` §1 says a surface is), and a wrapper keeps the package's namespace from growing a
second export every time an owner module gains a helper. Validation may live in either the wrapper or
the owner module, but each rule has **one** home — never both, and never a re-check that could drift —
so a `None` shape is defaulted in `config.py` and never in a wrapper (`config.md` §1).

`engine.__all__` is the ten names and nothing else (`README.md` §3), in the order that document lists
them, `game_shapes` first. A battery that drives the surface uses `engine.<name>` and nothing else
(`battery.md` §5).

## 3. The import boundary — a hard rule, not a preference

`engine` imports:

- `pokerkit` (`FixedLimitTexasHoldem`, `NoLimitTexasHoldem`, `Automation`, `analysis.calculate_equities`,
  `utilities.Deck`, `hands.StandardHighHand`, `lookups.Label`) and the Python standard library (`random`,
  `copy`, `itertools`, `collections.abc`, `typing`).

and **nothing else**. Never `features`, `agents`, `evaluation`, `training`, `harness`, and never a
`tests/` helper (`module-map.md` §3, D-1, D-13). The no-cap row needs `NoLimitTexasHoldem` beside
`FixedLimitTexasHoldem`, the only name the second shape adds — a bet structure is a library class, and
no shape puts another project module in reach. The module must also not need a `pyproject.toml` to be
imported: it is a plain package under `src/`, which is how `tests/e2e/_surface.py` reaches it and how
`tests/engine/` must reach it (no `tests/conftest.py` exists, and this module's battery may not create
one — it inserts `<repo>/src` on `sys.path` itself, the way the e2e battery does). Nothing here may
import `numpy`, `torch`, `pytest` or `unittest`: a numeric dependency would leak into every caller.

## 4. Where the design stops

Function bodies are L4's. This directory fixes: the ten names and their arguments and returns, the
value types (a `str` card, a `str` descriptor, a `dict` readout with eleven keys, a `tuple` legal set, a
`dict` payoff, an opaque `Hand`), the shape catalogue and the three rows, the seat mapping and its
general formula, the derivations of the eleven facts, the seeding and stream rules, the error grammar,
and the file/import layout. Anything else — helper names, private constants, docstring style, the order of two independent
statements — is L4's and is not a finding against this design unless it breaks one of the rules above
(`guardrails.md`).
