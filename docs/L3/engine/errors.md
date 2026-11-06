# engine — refusals

- **Owner:** the error classes and the message grammar every refusal of this module follows
- **Ceiling:** 70 lines. At the ceiling, split by owner — never append

## 1. Why a hierarchy at all

`docs/L2/engine/surface.md` §1: *an invalid argument is refused by raising an error that names the
violated contract; no entry point coerces a value, substitutes a default, swallows an error or
returns part of a record*. The error is therefore the only reporting channel there is: nothing is
returned as a "failure record", nothing is logged and continued, and no refused call has any side
effect (each refusal is checked **before** the first mutation, the first copy and the first
`random.seed`).

A hierarchy exists so that a caller can catch "this module refused me" without catching a `TypeError`
from a bug: a raised `pokerkit` `ValueError` escaping this module would be a leak of an internal
decision, and an `AttributeError` from a mistyped handle would be a crash passed off as a refusal.

## 2. The classes — `src/engine/errors.py`

    class EngineError(Exception)      # base of every refusal of this module
    class InvalidSeed(EngineError)          # a seed that is not an int
    class InvalidHand(EngineError)          # not a hand handle, or a hand that is over
    class InvalidAction(EngineError)        # a descriptor outside legal_actions / not a descriptor
    class InvalidDecision(EngineError)      # equity's first argument
    class InvalidSamples(EngineError)       # an equity sample count that is not a positive int
    class InvalidPolicy(EngineError)        # a play_hand policy that is not callable

The classes are **not** module-level names of the `engine` package: they live below an entry point
and are not surface (`e2e-surface.md` §1). The battery asserts the *behaviour* — that a call raises,
and what the message says — never an exception class, because the class is this module’s freedom.

## 3. The message grammar

Every message has the form

    "<entry point>(<argument>): <the violated contract>, got <what was passed>"

so the violated contract is named in words the design uses. The canonical messages:

| Where | Message |
|---|---|
| `new_hand`, `play_hand` seed | `new_hand(seed): the seed must be an int, got str` |
| hand argument, not a handle | `readout(hand): the argument must be a hand returned by new_hand, got dict` |
| hand that is over | `readout(hand): the hand is over, so there is no acting seat` |
| `apply_action` descriptor | `apply_action(hand, action): 'check' is not one of ('fold', 'check-call', 'raise')` |
| `apply_action` illegal here | `apply_action(hand, action): 'fold' is not legal at this decision, legal are ('check-call', 'raise')` |
| `play_hand` policy | `play_hand(seat0_policy): the policy must be callable, got str` |
| `play_hand` answer | `play_hand(seat0_policy): the policy returned 'raise', which is not legal at this decision` |
| `equity` decision | `equity(decision): the decision must be a hand or its readout, got None` |
| `equity` malformed readout | `equity(decision): a readout must carry two distinct cards in 'hole' and 0, 3, 4 or 5 distinct cards in 'board'` |
| `equity` decision over | `equity(decision): the hand is over, so there is no acting seat` |
| `equity` seed | `equity(seed): the seed must be an int, got float` |
| `equity` samples | `equity(samples): the sample count must be a positive int, got 0` |

Two properties the battery relies on: the message always contains the entry point’s own name and the
argument’s name, so a caller can see which contract it broke; and the message never claims a value
was accepted, so a refusal cannot be mistaken for a result.

## 4. What is *not* refused

Refusing more than the contract refuses is also a defect — a battery may pass any valid instance
(`battery.md` §4, D-15). So this module does not refuse: a seed of any integer size (negative, zero,
larger than 2**63 — Python seeds all of them), a sample count of 1, an empty board at `equity`, a
readout mapping that also carries extra caller keys (they are ignored; the two facts it needs are read
and the other eight are not inspected), a policy that is a bound method, a lambda or a closure, and two
policies that are the same object. It never inspects a policy’s arity or signature: it calls it with
two arguments and lets a `TypeError` from the call propagate as the policy’s own failure, not as a
refusal of this module.

The one shape that *is* refused on a readout is the one that is not a decision at all: `hole` that is
not two distinct cards of the declared spelling, or `board` that is not 0, 3, 4 or 5 distinct ones
(`equity.md` §1, `InvalidDecision`). That is a check on a value’s well-formedness, not on a caller’s
convenience, and it is the only place a readout is validated beyond "it is a mapping".
