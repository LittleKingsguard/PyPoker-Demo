# features — refusals

- **Owner:** the error classes and the message grammar every refusal of this module follows, and what
  is deliberately *not* refused
- **Ceiling:** 105 lines. At the ceiling, split by owner — never append

## 1. Why a hierarchy at all

`docs/L2/features/surface.md` §1: *an invalid argument is refused by raising an error that names the
violated contract; no entry point coerces a value, substitutes a default, swallows an error or returns
part of a record*. The error is therefore the only reporting channel: nothing comes back as a "failure
record", nothing is logged and continued, and no refused call has an observable effect — `encode`'s array
is local, so a refusal cannot leave half an observation anywhere, and a refused `decode_action` returns
nothing at all.

A hierarchy exists so a caller can catch "this module refused me" without catching a `TypeError` from a
bug: a `KeyError` from a mistyped readout key, a `ValueError` from `numpy` or an `IndexError` from an
action index escaping this module would each be an internal decision leaking as a crash.

## 2. The classes — `src/features/errors.py`

    class FeaturesError(Exception)          # base of every refusal of this module
    class UnknownEncoding(FeaturesError)    # build_encoder: a name that is not a declared encoding
    class InvalidEncoder(FeaturesError)     # observation_spec / encode: not an encoder this module built
    class InvalidReadout(FeaturesError)     # encode: not a mapping, a missing carried field, or a
                                            #         carried value this encoding cannot represent
    class InvalidActionList(FeaturesError)  # legal_indices: not a sequence of descriptors, or empty
    class UnknownAction(FeaturesError)      # legal_indices: a descriptor outside the three
    class InvalidActionIndex(FeaturesError) # decode_action: not an index, or outside {0, 1, 2}

The classes are **not** module-level names of the `features` package: they live below an entry point and
are not surface (`README.md` §3, `e2e-surface.md` §1). The battery asserts the *behaviour* — that a call
raises, and what the message says — never an exception class, because the class is this module's freedom
(`docs/L3/engine/errors.md` §2 makes the same choice for the same reason).

## 3. The message grammar

Every message has the form

    "<entry point>(<argument>): <the violated contract>, got <what was passed>"

so the violated contract is named in the design's own words, and the offending value is visible. Where
nothing was passed — a field the readout is missing — the message names the missing field instead of
inventing a "got" clause. The canonical messages — L4 follows these spellings, and the unit battery
matches them tolerantly (the entry point's name, the argument's or field's name, and the value):

| Where | Message |
|---|---|
| `build_encoder` name | `build_encoder(name): the encoding must be one of ('flat-numeric', 'card-tokens'), got 'Flat-Numeric'` |
| `observation_spec` argument | `observation_spec(encoder): the argument must be an encoder returned by build_encoder, got dict` |
| `encode` encoder | `encode(encoder): the argument must be an encoder returned by build_encoder, got None` |
| `encode` not a mapping | `encode(readout): the readout must be a mapping with the nine carried facts, got list` |
| `encode` missing field | `encode(readout): the readout is missing 'hole', which this encoding carries` |
| `encode` street | `encode(readout): 'street' must be one of ('preflop', 'flop', 'turn', 'river'), got 'pre-flop'` |
| `encode` seat | `encode(readout): 'seat' must be a seat index 0 or 1 and a bool button flag, got (2, True)` |
| `encode` hole | `encode(readout): 'hole' must be exactly two cards, got ('Td',)` |
| `encode` board | `encode(readout): 'board' must be at most five cards, got 6` |
| `encode` card | `encode(readout): 'hole' must hold cards, and 'Tz' is not one: a rank from '23456789TJQKA' then a suit from 'cdhs'` (the field named is the block's own — `'hole'` or `'board'`) |
| `encode` an amount | `encode(readout): 'stacks' must be two non-negative integers, got (19, -1)` |
| `encode` limit | `encode(readout): 'limit' must be two non-negative integers, got (2,)` |
| `encode` history length | `encode(readout): 'history' must be at most 24 entries, got 25` |
| `encode` history entry | `encode(readout): 'history' must hold the four documented entries, and 'preflop seat 0 bets 5' is not one` |
| `legal_indices` shape | `legal_indices(legal_actions): the argument must be a non-empty sequence of action descriptors, got 'fold'` |
| `legal_indices` empty | `legal_indices(legal_actions): a decision has at least one legal action, got ()` |
| `legal_indices` descriptor | `legal_indices(legal_actions): 'call' is not one of ('fold', 'check-call', 'raise')` |
| `decode_action` non-integer | `decode_action(index): the index must be an integer, got '1'` |
| `decode_action` out of range | `decode_action(index): the index must be one of 0, 1 or 2, got 3` |

Two properties the battery relies on: the message always contains the entry point's own name, the name of
the argument or field at fault, and the offending value, so a caller can see which contract it broke and
with what; and the message never claims a value was accepted, so a refusal cannot be mistaken for a
result.

## 4. What is *not* refused

Refusing more than the contract refuses is also a defect — a battery may pass any valid instance
(`battery.md` §4, D-15). So this module does **not** refuse:

- an extra key in a readout, `legal` above all: a key the encoding does not carry is ignored
  (`surface.md` §6);
- the same card twice in `hole` or `board`, and `hole` equal to a `board` card: the deal's business;
- a `board` of one or two cards: representable (one or two card slots, the rest zeros or pads), and the
  deal does not produce one;
- a `history` shorter than 24 entries, which is the normal case, and a hand with no action at all;
- any non-negative magnitude of any amount: each token ladder is total over the non-negative integers
  (`card-tokens.md` §4), and the dense encoding divides by a fixed divisor (`flat-numeric.md` §4). A
  **negative** count is refused, in both encodings and for one reason: no ladder has a bucket below
  zero, so the token encoding could not spell it, and one fact set has one representable domain in this
  module. The engine never produces one (`readout.md` §2);
- a readout whose `pot + sum(stacks)` is not 40: that invariant is the engine's (`readout.md` §2) and
  re-checking it here would be a second source of truth;
- two encoders built from one name, an encoder held for a long time, and a readout reused across calls:
  the module keeps no state and holds no cache;
- a `numpy` integer where a chip count, a seat index or an action index is expected: `numpy.int64` is an
  `Integral`, and an index is an index whatever its class. A **`bool`** is refused in all three places,
  because the project's house rule is that a flag is not a count (`README.md` §4) — and for the same
  reason the `seat` block's flag must be a real `bool`, not a `numpy.bool_`: a flag is spelled one way
  (`flat-numeric.md` §4).

The three shapes that *are* refused on a readout are the ones that are not a readout at all: it is not a
mapping, it is missing a field the encoding carries, or a carried value has no spelling in the declared
encoding. That is a check on a value's well-formedness, not on a caller's convenience.
