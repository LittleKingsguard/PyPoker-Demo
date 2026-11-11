# engine — the message grammar

- **Owner:** the message grammar, and the canonical message per refusal
- **Ceiling:** 48 lines — raised from 45 for the third seat count: the third declared name and the seating's four refusals. At the ceiling, split by owner — never append
- **Split from:** `errors.md` §3, moved here whole when that file passed its 70-line limit

## 1. The message grammar

Every message names the entry point, the argument in parentheses, and then the violated contract; most
go on to name what was passed:

    "<entry point>(<argument>): <the violated contract>, got <what was passed>"

so the violated contract is named in words the design uses. The canonical messages:

| Where | Message |
|---|---|
| `new_hand`, `play_hand` seed | `new_hand(seed): the seed must be an int, got str` |
| hand argument, not a handle | `readout(hand): the argument must be a hand returned by new_hand, got dict` |
| hand that is over | `readout(hand): the hand is over, so there is no acting seat` |
| shape argument | `new_hand(shape): 'no-limit-50' is not one of the declared shapes ('fixed-limit-20', 'no-limit-100', 'six-seat-no-limit-100')` |
| `apply_action` descriptor, fixed row | `apply_action(hand, action): 'check' is not one of ('fold', 'check-call', 'raise')` |
| `apply_action` descriptor, no-cap row | `apply_action(hand, action): 'raise' is not one of ('fold', 'check-call', 'raise-quarter', 'raise-half', 'raise-all-in', 'raise-minimum')` |
| `apply_action` illegal here | `apply_action(hand, action): 'fold' is not legal at this decision, legal are ('check-call', 'raise')` |
| `apply_action`, an empty band | `apply_action(hand, action): 'raise-half' is not legal at this decision, legal are ('fold', 'check-call', 'raise-all-in', 'raise-minimum')` |
| `play_hand` policy | `play_hand(seat0_policy): the policy must be callable, got str` |
| `play_hand` policy in a seating | `play_hand(seats[5]): the policy must be callable, got int` |
| `play_hand` seating, wrong length | `play_hand(seats): the shape 'six-seat-no-limit-100' seats 6, so the seating must hold 6 policies in seat order, got 5` |
| `play_hand` seating beside the pair | `play_hand(seats): the seating is given, so the two positional policies seat0_policy and seat1_policy are absent, and one of them was given; …` |
| `play_hand` answer | `play_hand(seat0_policy): the policy returned 'raise', which is not legal at this decision` |
| `equity` decision | `equity(decision): the decision must be a hand or its readout, got NoneType` |
| `equity` malformed readout | `equity(decision): a readout must carry two distinct cards in 'hole' and 0, 3, 4 or 5 distinct cards in 'board'` |
| `equity` decision over | `equity(decision): the hand is over, so there is no acting seat` |
| `equity` seed | `equity(seed): the seed must be an int, got float` |
| `equity` samples | `equity(samples): the sample count must be a positive int, got 0` |

The shape row is the **head** of its message: the real one continues `, and a shape name is never
defaulted (shapes.md §2, D-29)`, which is the clause no caller may read as an invitation to omit the
name (`config.md` §1). Its declared-names list is the catalogue's own, so the message names what the
refusal would have accepted.

Two properties the battery relies on: the message names the entry point and the argument, so a caller can
see which contract it broke, and where the argument was a value it also says what was passed; and the
message never claims a value was accepted, so a refusal cannot be mistaken for a result. One measured
deviation is a defect to correct and not a licence: `play_hand`'s seed refusal is labelled
`new_hand(seed)`, because the seed check is reached without the calling entry point's name
(`hand.md` §2, `episode.md` §1).
