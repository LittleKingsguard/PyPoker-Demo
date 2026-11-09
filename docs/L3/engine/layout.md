# engine — the file layout

- **Owner:** what lives where under `src/engine/`, which names the package exports, and which imports are allowed
- **Ceiling:** 80 lines. At the ceiling, split by owner — never append

## 1. The files

    src/engine/__init__.py     the nine entry points, and nothing else (§2)
    src/engine/config.py       the fixed game's constants and GAME_CONFIG / game_config()
    src/engine/errors.py       EngineError and its six subclasses (errors.md §2)
    src/engine/cards.py        card_spelling() / parse_card() — the one spelling (readout.md §3)
    src/engine/hand.py         Hand, SEAT_TO_PLAYER, player_index(), seat_of(), AUTOMATIONS,
                               new_hand(), advance(), is_terminal(), payoffs()
    src/engine/actions.py      ACTIONS, legal_actions(), apply_action()
    src/engine/readout.py      facts(), readout(), hand_class() and CLASS_OF — the eleven-key mapping (readout.md §2)
    src/engine/episode.py      play_hand() and the reward placement
    src/engine/equity.py       equity() and the random save/seed/restore

Nine files, one concern each, and each file's public-ish names are listed in §2 or in the document
named beside it. A tenth file is allowed only if a document in this directory says what it owns; a
file that exists to hold one helper is a sign the owner is missing, not a sign the layout is wrong.

## 2. What the package exports

`src/engine/__init__.py` defines (or imports under a private alias and re-exports) **exactly** the
nine entry points of `README.md` §3, and declares them in `__all__`. No tenth public name: not a
class, not a constant, not the error base, not `Hand`.

    from . import config   as _config      # private module binding, so engine.<submodule> stays
    from . import hand     as _hand        # available without becoming part of the surface
    ...

    def game_config() -> dict:            return _config.game_config()
    def new_hand(seed):                   return _hand.new_hand(seed)
    def readout(hand):                    return _readout.readout(hand)
    def legal_actions(hand):              return _actions.legal_actions(hand)
    def apply_action(hand, action):       return _actions.apply_action(hand, action)
    def is_terminal(hand):                return _hand.is_terminal(hand)
    def payoffs(hand):                    return _hand.payoffs(hand)
    def play_hand(seed, seat0_policy, seat1_policy):
                                          return _episode.play_hand(seed, seat0_policy, seat1_policy)
    def equity(decision, seed, samples):  return _equity.equity(decision, seed, samples)

The thin wrapper is deliberate: the entry point is a module-level name of the package (that is what
`e2e-surface.md` §1 says a surface is), and a wrapper keeps the package's namespace from growing a
second export every time an owner module gains a helper. Validation may live in either the wrapper
or the owner module, but each rule has **one** home — never both, and never a re-check that could
drift.

`engine.__all__` is the nine names and nothing else (`README.md` §3); their order in it is free. A
battery that drives the surface uses `engine.<name>` and nothing else (`battery.md` §5, brief §5).

## 3. The import boundary — a hard rule, not a preference

`engine` imports:

- `pokerkit` (`FixedLimitTexasHoldem`, `Automation`, `analysis.calculate_equities`,
  `utilities.Deck`, `hands.StandardHighHand`, `lookups.Label`) and the Python standard library (`random`, `copy`,
  `itertools`, `collections.abc`, `numbers`, `typing`).

and **nothing else**. Never `features`, `agents`, `evaluation`, `training`, `harness`, and never a
`tests/` helper (`module-map.md` §3, D-1, D-13). The module must also not need a `pyproject.toml` to
be imported: it is a plain package under `src/`, which is how `tests/e2e/_surface.py` reaches it and
how `tests/engine/` must reach it (no `tests/conftest.py` exists, and this module’s battery may not
create one — it inserts `<repo>/src` on `sys.path` itself, the way the e2e battery does).

Nothing in `src/engine/` may import `numpy`, `torch`, `pytest` or `unittest`: the engine is the bottom
of the map and a test-only or numeric dependency here would leak into every caller.

## 4. Where the design stops

Function bodies are L4's. This directory fixes: the nine names and their arguments and returns, the
value types (a `str` card, a `str` descriptor, a `dict` readout with eleven keys, a `tuple` legal set, a
`dict` payoff, an opaque `Hand`), the seat mapping, the derivations of the eleven facts, the seeding and
stream rules, the error grammar, and the file/import layout. Anything else — helper names, private
constants, docstring style, the order of two independent statements — is L4's and is not a finding
against this design unless it breaks one of the rules above (`guardrails.md`).
