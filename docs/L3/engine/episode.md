# engine — `play_hand` and the episode record

- **Owner:** one whole hand as a record — the policy protocol it drives, the shape's seating, the episode and decision shapes, and where the reward lands
- **Ceiling:** 140 lines — raised from 100 for the third seat count: the optional `seats` argument, its refusals and their measured messages, and the per-seat record. At the ceiling, split by owner — never append

## 1. The signature and its refusals

    def play_hand(seed: int, seat0_policy=None, seat1_policy=None, shape=None, seats=None) -> dict

Two mutually exclusive forms name the policies. **Absent `seats`** is the form this entry point has
always taken — seat 0's policy then seat 1's, in that order — so today's two-seat call plays today's
hand and no existing caller changes (`e2e-surface.md` §3.1, `shapes.md` §5). With **`seats`** the
positional pair is absent and the sequence is the shape's whole seating, one policy per seat in seat
order, which is how a six-seat hand seats six policies of which one is the learner's (`seats.md` §4,
ASM-43).

- Refuses a seed that is not an integer, as `new_hand` does (`hand.md` §2), **before** the deal, so a
  refused call cannot move the stream.
- Refuses a shape name outside the catalogue — naming it and the declared names, never defaulting it
  (`config.md` §1) — after the seed and **before** the seating, and before the deal.
- Refuses a **seating** that the shape contradicts, all four by raising `InvalidSeating` (`errors.md`
  §2, `seats.md` §4): a sequence whose length is not the shape's seat count and two positional policies
  on a shape with more than two seats, which seat two of six — each naming the shape, its seat count and
  the count it was handed; and a sequence handed beside either positional policy, or a value that is not
  an ordered sequence of policies at all — a `str`, `bytes` or mapping included, since each of those is
  iterable and none is a seating — each naming the two exclusive forms or the type it was given.
- Refuses a policy that is not callable, as `InvalidPolicy`, naming which seat's policy it was: the
  argument's own name on the positional form (`seat0_policy`, `seat1_policy`), and `seats[i]` on the
  seating form, which is why the label travels with the policies out of the seating (`errors.md` §2).
- Refuses an answer outside `legal_actions` for that decision — by value, never by identity, because
  `features.decode_action` builds a fresh equal string (`actions.md` §1).
- Does **not** catch a policy's own exception: it propagates to the caller unchanged, and is never
  turned into a fold (`L2 surface.md` §10, D-2).

Every one of those refusals precedes `new_hand`, so a refused call deals nothing and leaves both the
stream and the policy set untouched (`hand.md` §2, `errors.md` §1). Measured, on the six-seat shape:
two positional policies raise `play_hand(shape): the shape 'six-seat-no-limit-100' seats 6, so its hand
needs 6 policies and the two positional policies seat 2`; a five-long seating raises `… seats 6, so the
seating must hold 6 policies in seat order, got 5`; a seating beside a positional policy and a
non-callable at index 5 raise `InvalidSeating` and `InvalidPolicy` respectively.

## 2. The loop

    hand = new_hand(seed, shape)               # the ONLY seeding point; play_hand never seeds
    seating = the shape's policies, in seat order    # §1's two forms, one sequence
    decisions = []
    while not is_terminal(hand):
        readout = readout(hand)                # readout.md — a fresh mapping, and the same in every shape
        legal = readout["legal"]               # the same tuple legal_actions returns
        seat = readout["seat"][0]              # 0 .. seats − 1, the readout's own fact
        action = seating[seat](readout, legal) # the policy protocol of e2e-surface §2
        if action not in legal: refuse         # InvalidAction, errors.md
        bounds = raise_interval(hand)          # (minimum, maximum), or None when no raise is legal
        decisions.append({seat, readout, legal, action, reward=0, amount=raise_amount(hand, action),
                          minimum=..., maximum=...})   # the three amounts, None where §3 says None
        hand = apply_action(hand, action)      # stepping.md §2 — one history entry per decision
    payoff = payoffs(hand)                     # hand.md §5 — one entry per seat
    place the reward (§3)
    return {"seed": seed, "decisions": decisions, "payoffs": payoff}

One sequence indexes both forms, so nothing below the seating asks how many seats there are and the
loop is the same loop in every shape (`seats.md` §4). There is one hand in flight and no re-entry: one
global `random` stream deals every hand, so sequential play is a contract and not a choice, and
`play_hand` calls `new_hand` rather than seeding itself, so no call seeds twice (D-16, ASM-2, `L2
surface.md` §1). The three amount facts are read before the step (`sizing.md` §2).

## 3. The episode record

The three required keys of `records.md` §5, and beyond them nothing a caller may depend on:

| Key | Content |
|---|---|
| `seed` | the seed the call was made with, unchanged — an `int` |
| `decisions` | a `list` of decision records, in the order they were taken |
| `payoffs` | the mapping `payoffs(hand)` returned for this completed hand: one net delta per seat — `{0: p0, 1: p1}` on a two-seat shape, six entries on the six-seat one (`seats.md` §3) |

Each decision record carries the five facts `records.md` §5 requires beside the three amount facts; an
eighth and ninth key would be this module's own and no caller may depend on one (`L2 surface.md` §1,
D-13).

- `seat` — the decision’s own acting seat, in the shape of `readout`’s `seat` fact, so
  `(index, on_button)` with the index in `0 .. seats − 1`; the index is the first number inside it, and
  it is the readout's own seat fact rather than a second derivation, so a seat index means one thing in
  the record and in the facts (`records.md` §5, `seats.md` §3);
- `readout` — the whole eleven-fact mapping of that decision, taken **before** the action, so a record
  can be encoded after the hand is over — eleven facts in every shape (D-3, `shapes.md` §5);
- `legal` — that decision’s ordered descriptor tuple;
- `action` — the descriptor the policy returned and the engine applied;
- `reward` — see below;
- `minimum`, `maximum` — the bounds of the legal raise interval at that decision, `None` **exactly**
  when no raise was legal (`config.md` §5, `sizing.md` §2);
- `amount` — the raise-to resolved from the descriptor, `None` **whenever it is not a raise** — the fixed
  row's `raise` resolving to its minimum completion, both bounds there (`actions.md` §2).

**Where the reward lands (ASM-12).** Every decision is created with `reward` 0. When the hand ends, each
seat’s **last** decision takes that seat’s net chip delta and every other decision stays 0, so a hand
carries at most one non-zero reward per seat and it is the hand’s outcome, never a shaped per-decision
term. A split leaves both rewards 0 — which is why the battery asserts "at most one non-zero reward per
seat", not "exactly one". A seat that never acted (the big blind after a pre-flop fold) carries no decision
and no reward (`L2 environment.md` §3). Rewards are plain `int` chips, unscaled (D-3, `records.md` §4).
The rule is per seat and not per hand, so a six-seat hand carries at most six non-zero rewards: measured,
one always-check-call six-seat episode has 24 decisions across all six seats and six rewarded decisions
whose rewards are exactly `payoffs(hand)` (`seats.md` §3, ASM-43).

The record names **no hand handle**, no state and no card outside a readout — nothing below an entry point
is surface (`e2e-surface.md` §1) — and it is not re-opened: a caller that wants the hand advanced
further drives `new_hand`/`apply_action` itself (`L2 environment.md` §3).

## 4. Policy independence

`play_hand` knows no builder by name: `agents.as_policy`, `agents.build_baseline`, `evaluation.policy_from`
and `harness.seam` all return "a callable taking `(readout, legal)` and returning one member of `legal`",
and that is the whole protocol (`e2e-surface.md` §2, D-13). The engine imports none of them and does not
inspect the policy, count its calls or memoise anything: one readout is handed over as often as asked.
The seating is a sequence of such callables and nothing else — it is not a policy builder, a pool, a seat
map or a set of weights (`seats.md` §4).

One seed and one seating give one record, a different seed gives a different one, and two seats may hold
the same policy object (a self-play episode) (ASM-2, FAM-4).

## 5. What the battery may assert of an episode

Driving only `play_hand` (and the other nine): the record has `seed`, `decisions`, `payoffs`; the seed is
the seed it was called with; there is at least one decision and at most 200; every decision carries the eight
facts and its readout the eleven, its action is a member of its legal tuple, and `minimum`/`maximum` are
`None` exactly when no raise was legal while `amount` is `None` exactly when it is no raise; the sequence of
actions replays the same hand driven by hand; each seat has at most one non-zero reward equal to its payoff;
the payoffs sum to zero; two identical calls give equal records and two seeds different ones; a non-callable
policy, an illegal answer, an unknown shape and every refusal of §1 are refused; and a policy that raises
propagates.

On `six-seat-no-limit-100` the same battery adds three: a six-long seating plays a hand whose decisions
name all six seats, whose payoffs hold six entries summing to zero, and whose rewards are those payoffs;
the two positional policies are refused on it; and an absent `seats` on a **two-seat** shape still plays
the same hand it played before this shape existed (`e2e-surface.md` §3.1, `seats.md` §4, ASM-43).
