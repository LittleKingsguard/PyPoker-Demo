# features — the three-index action vocabulary

- **Owner:** `action_space`, `legal_indices`, `decode_action` — the three names that carry the action
  axis: the vocabulary's declaration, a decision's legal indices, and an index read back as a descriptor
- **Ceiling:** 135 lines. At the ceiling, split by owner — never append

## 1. The vocabulary is the game's, and it has three indices

    ACTIONS = ("fold", "check-call", "raise")        # src/features/vocabulary.py, indices 0, 1, 2

| Index | Action | What the descriptor denotes |
|---|---|---|
| 0 | fold | give up the hand |
| 1 | check-call | check when `to_call` is 0, otherwise call it |
| 2 | raise | the engine's minimum legal completion for that decision, unique in fixed-limit |

The three descriptor strings are the project's shared spelling: they are the same three `str`s
`engine.apply_action` accepts, `readout["legal"]` carries and `engine.legal_actions` returns in this
order (`docs/L3/engine/actions.md` §1, `docs/L3/engine/stepping.md` §1). This module does not import
that module to compare them — the spelling is inherited fact, restated once here, and the e2e battery's
FAM-2.10 and FAM-2.11 are the check that the two sides agree (`battery.md` §3, D-13).

The vocabulary is held constant across the whole ladder (`ladder.md` §4) and this module never varies it:
there is no parameter here, no per-rung variant and no fourth index. Rejected: a vocabulary that grows a
per-amount raise (`raise-to-4`), which would put the game's chip counts into the action space and make
one index mean two different sizes (`docs/L3/engine/actions.md` §2, D-2).

## 2. `action_space()` — the declaration

    def action_space() -> dict

    return {0: {"name": "fold"},
            1: {"name": "check-call"},
            2: {"name": "raise",
                "completion": "the engine's minimum legal completion for the decision"}}

No argument, no refusal (`surface.md` §7). Keys are the three indices; each value is a plain record
carrying the action's `name`, and the raise's record adds the resolution that it denotes the engine's
minimum legal completion (`surface.md` §7, `encodings.md` §6). Two calls return equal mappings in
ascending index order, and it is plain data because a report's header quotes it (`protocol.md` §1).

**The hard constraint: the only integers anywhere in this record are `0`, `1` and `2`.** The L1 battery's
reader (`tests/e2e/_surface.action_vocabulary`) collects every integer it finds in the keys *and* the
values, and every string that is **all digits**; so an integer `4`, a `1`-as-a-chip-count, or a key
`"raise to 4"` read as a chip count would make the vocabulary `{0, 1, 2, 4}` and fail FAM-2.9
(`battery.md` §3). A digit *inside* prose — `"the engine's minimum legal completion"` has none — escapes
that reader, which is why the unit battery holds the stronger rule: no string in the record contains a
digit at all (`guardrails.md` G6). The record carries no amount, no chip count, no size, no width and no
id beyond the three indices; the raise's `completion` names a mechanism, never a number.

Rejected: a sequence of three names, `("fold", "check-call", "raise")`. The battery would read it
positionally and pass, but L2 §7 asks the record to carry the raise's resolution, and a bare tuple has
nowhere to put it. Also rejected: a mapping keyed by name (`{"fold": 0, …}`), which fails FAM-2.9
outright — the reader finds no integer in its keys and the fallback that saves a positional sequence
applies only to a three-element sequence, not to a mapping.

## 3. `legal_indices(legal_actions)` — one decision's indices

    def legal_indices(legal_actions: Sequence[str]) -> tuple[int, ...]

    refuse unless the argument is a Sequence, not a str/bytes, and not a set or mapping   # InvalidActionList
    refuse if it is empty                                        # a decision has at least one action
    for each descriptor, refuse unless it is one of ACTIONS, naming that descriptor         # UnknownAction
    return tuple(ACTIONS.index(d) for d in legal_actions)         # POSITION-ALIGNED, never reordered

The result is **position-aligned with the argument**: the i-th index is the vocabulary index of the i-th
descriptor (`surface.md` §8). It is therefore one index per descriptor, and — for an argument in the
engine's order, which is the vocabulary's — ascending and distinct. That is a consequence of the
alignment, never a step: this function does not sort, does not de-duplicate and does not look at a
decision, so an argument out of the engine's order yields its indices in that same order
(`("raise", "check-call", "fold")` gives `(2, 1, 0)`). FAM-2.11 and `tests/e2e/_surface.chosen_index`
read it positionally to turn a policy's chosen descriptor back into an index, which is why the alignment
is contract (`battery.md` §2).

Refusals, each naming what was violated:

- a value that is not a sequence of descriptors — a `str` (a sequence of characters, never a descriptor
  list), `bytes`, a `set` (no order to align with), a mapping, an iterator, `None`;
- an empty sequence: a live decision always has at least one legal action (`docs/L3/engine/stepping.md`
  §1), so an empty one is a caller error and not an empty mask;
- a descriptor outside the three, **with that descriptor in the message** (`'call'`, `'Fold'`, `0`). No
  fold is substituted for an unknown action (`surface.md` §8, D-2).

It never decides legality: it takes the descriptors a decision already has and names their indices. A
descriptor this module returns for an index says nothing about whether that index is legal at any
decision — the engine refuses an illegal one (`surface.md` §9, D-2).

## 4. `decode_action(index)` — an index, one descriptor

    def decode_action(index: int) -> str

    refuse unless index is an Integral and not a bool, naming what was passed      # InvalidActionIndex
    refuse unless 0 <= index <= 2                                                  # InvalidActionIndex
    return ACTIONS[index]                        # a plain str, equal by value, stable in text

One index in, one descriptor out, and nothing else: no decision, no hand, no amount, no legality
question (`surface.md` §9). The returned string is the one `engine.apply_action` accepts, so the round
trip `decode_action(legal_indices(legal)[i])` is a descriptor the engine accepts wherever that index is
legal at that decision (FAM-2.10).

Refused: a value that is not an integer (`"1"`, `1.0`, `None`), a `bool` (a flag is not an index — the
house rule that a flag is not a count, `README.md` §4), and any index outside `0, 1, 2` (`-1`, `3`). An
unknown index is never mapped to a default descriptor (`surface.md` §9, D-2).

## 5. What is not a descriptor and what is not an index

A descriptor is exactly one of the three `str` values: not an integer index (that is `decode_action`'s
argument, in the other direction), not a differently-cased spelling (`"Fold"`), not a synonym (`"call"`,
`"check"`, `"bet"`), not a `pokerkit` operation, not `None`, and not a pair carrying an amount. An index
is a plain integer in `0..2`, and this module never accepts a descriptor where it wants an index or an
index where it wants a descriptor — the two directions are two names, and confusing them is refused
rather than guessed (`docs/L3/engine/actions.md` §3).

The descriptor test is **gated on `str` first**, before the value is compared against `ACTIONS`: a
foreign type that defines its own equality protocol must not be able to talk its way into the vocabulary
(a one-element `numpy` array compares equal to a `str`, and a multi-element one raises `ValueError` from
`bool()` instead of refusing). `errors.md` §1 makes the named refusal — never a leaked `ValueError` — the
only reporting channel, and `UnknownAction` names the offending value whether it is a synonym or a
`numpy` array.

## 6. What the unit battery may assert

The three names exist and are callable; `action_space()` declares exactly the three indices, names `fold`
/ `check-call` / `raise` in order, and contains no integer other than `0`, `1`, `2` (walked the way the
battery walks it); two calls are equal. `legal_indices(("fold", "check-call", "raise"))` is `(0, 1, 2)`
and `legal_indices(("check-call", "raise"))` is `(1, 2)` — positionally, not sorted; a shuffled argument
gives the shuffled indices, which is the alignment; an empty sequence, a `str`, a `set` and an unknown
descriptor each refuse with the offending value in the message. `decode_action(i)` round-trips
`legal_indices` for every index and is a plain `str`; a non-integer, a `bool` and `3` each refuse. No
call touches `random`, `numpy.random`, or the readout it was never given.
