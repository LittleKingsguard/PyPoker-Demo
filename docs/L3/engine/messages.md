# engine — the message grammar

- **Owner:** the message grammar, and the canonical message per refusal
- **Ceiling:** 45 lines. At the ceiling, split by owner — never append
- **Split from:** `errors.md` §3, moved here whole when that file passed its 70-line limit

## 1. The message grammar

Every message has the form

    "<entry point>(<argument>): <the violated contract>, got <what was passed>"

so the violated contract is named in words the design uses. The canonical messages:

| Where | Message |
|---|---|
| `new_hand`, `play_hand` seed | `new_hand(seed): the seed must be an int, got str` |
| hand argument, not a handle | `readout(hand): the argument must be a hand returned by new_hand, got dict` |
| hand that is over | `readout(hand): the hand is over, so there is no acting seat` |
| shape argument | `new_hand(shape): 'no-limit-50' is not one of the declared shapes ('fixed-limit-20', 'no-limit-100')` |
| `apply_action` descriptor, fixed row | `apply_action(hand, action): 'check' is not one of ('fold', 'check-call', 'raise')` |
| `apply_action` descriptor, no-cap row | `apply_action(hand, action): 'raise' is not one of ('fold', 'check-call', 'raise-quarter', 'raise-half', 'raise-all-in', 'raise-minimum')` |
| `apply_action` illegal here | `apply_action(hand, action): 'fold' is not legal at this decision, legal are ('check-call', 'raise')` |
| `apply_action`, an empty band | `apply_action(hand, action): 'raise-half' is not legal at this decision, legal are ('fold', 'check-call', 'raise-all-in', 'raise-minimum')` |
| `play_hand` policy | `play_hand(seat0_policy): the policy must be callable, got str` |
| `play_hand` answer | `play_hand(seat0_policy): the policy returned 'raise', which is not legal at this decision` |
| `equity` decision | `equity(decision): the decision must be a hand or its readout, got None` |
| `equity` malformed readout | `equity(decision): a readout must carry two distinct cards in 'hole' and 0, 3, 4 or 5 distinct cards in 'board'` |
| `equity` decision over | `equity(decision): the hand is over, so there is no acting seat` |
| `equity` seed | `equity(seed): the seed must be an int, got float` |
| `equity` samples | `equity(samples): the sample count must be a positive int, got 0` |

The shape row is the **head** of its message: the real one continues `, and a shape name is never
defaulted (shapes.md §2, D-29)`, which is the clause no caller may read as an invitation to omit the
name (`config.md` §1). Its declared-names list is the catalogue's own, so the message names what the
refusal would have accepted.

Two properties the battery relies on: the message always contains the entry point’s own name and the
argument’s name, so a caller can see which contract it broke; and the message never claims a value
was accepted, so a refusal cannot be mistaken for a result.
