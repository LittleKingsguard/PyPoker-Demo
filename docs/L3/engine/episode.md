# engine — `play_hand` and the episode record

- **Owner:** one whole hand as a record — the policy protocol it drives, the shape's seating, the episode and decision shapes, where the reward lands, and the post-hand facts D-43 adds
- **Rev:** 3 — the resolution is **self-checking**: `payoffs(hand)` is handed to it and a hand whose pot was built in levels (any seat's take neither `0` nor the whole pot) carries no values, exactly as a `split` one does (§5, `counterfactual.md` §4's last paragraph). Rev 2 — D-43's resolution: each decision record gains `amounts` and `counterfactual`, the episode record gains `reveal`, and the cards are captured inside the loop because the library clears them when the hand ends (§5); §5's battery paragraph moved whole to `episode-battery.md` and left the redirect (§6) (`counterfactual.md` §2, §4, `records.md` §5)
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
stream and the policy set untouched (`hand.md` §2, `errors.md` §1). Measured, on the six-seat shape: two positional policies raise `play_hand(shape): the shape 'six-seat-no-limit-100' seats 6, so its hand needs 6 policies and the two positional policies seat 2`; a five-long seating raises `… seats 6, so the seating must hold 6 policies in seat order, got 5`; a seating beside a positional policy and a non-callable at index 5 raise `InvalidSeating` and `InvalidPolicy` (`episode-battery.md` §1).

## 2. The loop

    hand = new_hand(seed, shape)               # the ONLY seeding point; play_hand never seeds
    seating = the shape's policies, in seat order    # §1's two forms, one sequence
    decisions = []
    holes = None                                # every seat's two cards, captured once, at the first decision
    while not is_terminal(hand):
        readout = readout(hand)                # readout.md — a fresh mapping, and the same in every shape
        legal = readout["legal"]               # the same tuple legal_actions returns
        seat = readout["seat"][0]              # 0 .. seats − 1, the readout's own fact
        action = seating[seat](readout, legal) # the policy protocol of e2e-surface §2
        if action not in legal: refuse         # InvalidAction, errors.md
        bounds = raise_interval(hand)          # (minimum, maximum), or None when no raise is legal
        amounts = {d: raise_amount(hand, d) for d in legal}   # §5 — one entry per legal d, before the step
        if holes is None: holes = capture(hand)               # §5 — before any seat can muck
        own_bet = state.bets[player_index(seat, seats)]       # §5 — before the step, and never recorded
        decisions.append({seat, readout, legal, action, reward=0, amount=amounts[action],
                          minimum=..., maximum=..., amounts=amounts, counterfactual=None})
        hand = apply_action(hand, action)      # stepping.md §2 — one history entry per decision
    payoff = payoffs(hand)                     # hand.md §5 — one entry per seat
    place the reward (§3)
    return {seed, decisions, payoff, reveal=resolve(decisions, holes)}    # §5 — after the hand

One sequence indexes both forms, so nothing below the seating asks how many seats there are and the
loop is the same loop in every shape (`seats.md` §4). There is one hand in flight and no re-entry: one
global `random` stream deals every hand, so sequential play is a contract and not a choice, and
`play_hand` calls `new_hand` rather than seeding itself, so no call seeds twice (D-16, ASM-2, `L2
surface.md` §1). The three amount facts and `amounts` are read before the step (`sizing.md` §2), and so
are the two captures §5 needs — the hole cards and the actor's own street bet, which a finished hand no
longer reports.

## 3. The episode record

The four required keys of `records.md` §5, and beyond them nothing a caller may depend on:

| Key | Content |
|---|---|
| `seed` | the seed the call was made with, unchanged — an `int` |
| `decisions` | a `list` of decision records, in the order they were taken |
| `payoffs` | the mapping `payoffs(hand)` returned for this completed hand: one net delta per seat — `{0: p0, 1: p1}` on a two-seat shape, six entries on the six-seat one (`seats.md` §3) |
| `reveal` | the hand's cards and who held the best of them — `board`, `showdown`, `split`, and one entry per seat in seat order carrying `seat`, `hole`, `shown` and `won` (§5, `records.md` §5) |

Each decision record carries the ten facts `records.md` §5 requires — the five below, the three amount
facts, `amounts` and `counterfactual` — and an eleventh key would be this module's own and no caller may
depend on one (`L2 surface.md` §1, D-13).

- `seat` — the decision’s acting seat in the shape of `readout`’s `seat` fact, `(index, on_button)` with the index in `0 .. seats − 1`, taken from that fact and not derived again (`records.md` §5, `seats.md` §3);
- `readout` — the whole eleven-fact mapping of that decision, taken **before** the action, so a record can be encoded after the hand is over — eleven facts in every shape (D-3, `shapes.md` §5);
- `legal` — that decision’s ordered descriptor tuple;
- `action` — the descriptor the policy returned and the engine applied;
- `reward` — see below;
- `minimum`, `maximum` — the bounds of the legal raise interval at that decision, `None` **exactly** when no raise was legal (`config.md` §5, `sizing.md` §2);
- `amount` — the raise-to resolved from the descriptor, `None` **whenever it is not a raise** — the fixed row's `raise` resolving to its minimum completion; it **is** `amounts[action]`, one value and not two derivations (`actions.md` §2, §5);
- `amounts` — the raise-to every legal descriptor resolves to at that decision, `None` for the two bases (§5, `sizing.md` §2);
- `counterfactual` — each legal descriptor's whole-hand net chip delta for the acting seat, or `None` throughout a hand the reveal cannot resolve (§5, `counterfactual.md` §4).

**Where the reward lands (ASM-12).** Every decision is created with `reward` 0. When the hand ends, each
seat’s **last** decision takes that seat’s net chip delta and every other decision stays 0, so a hand
carries at most one non-zero reward per seat and it is the hand’s outcome, never a shaped per-decision
term. A split leaves both rewards 0 — which is why the battery asserts "at most one non-zero reward per
seat", not "exactly one". A seat that never acted (the big blind after a pre-flop fold) carries no
decision and no reward, and the rule is per seat and not per hand, so a six-seat hand carries at most six
(`L2 environment.md` §3, `episode-battery.md` §3, `seats.md` §3, ASM-43). Rewards are plain `int` chips,
unscaled (D-3, `records.md` §4).

The record names **no hand handle**, no state and no card outside a readout or the reveal — nothing below an entry point is surface (`e2e-surface.md` §1) — and it is not re-opened: a caller that wants the hand advanced further drives `new_hand`/`apply_action` itself (`L2 environment.md` §3).

## 4. Policy independence

`play_hand` knows no builder by name: `agents.as_policy`, `agents.build_baseline`, `evaluation.policy_from`
and `harness.seam` all return "a callable taking `(readout, legal)` and returning one member of `legal`",
and that is the whole protocol (`e2e-surface.md` §2, D-13). The engine imports none of them and does not
inspect the policy, count its calls or memoise anything: one readout is handed over as often as asked.
The seating is a sequence of such callables and nothing else — it is not a policy builder, a pool, a seat
map or a set of weights (`seats.md` §4).

One seed and one seating give one record, a different seed gives a different one, and two seats may hold
the same policy object (a self-play episode) (ASM-2, FAM-4).

## 5. What D-43 adds: `amounts`, `reveal` and `counterfactual`

Three post-hand read-only facts and nothing else: no entry point is added, no twelfth readout fact, no twelfth descriptor, and `legal`, `amount`, `minimum`, `maximum`, the hand, its actions and its payoffs are unchanged (`records.md` §5, `counterfactual.md` §2, §9).

**`amounts`** — a `dict` over **every** descriptor of that decision's `legal` tuple, computed inside the loop **before** the step from the same handle `legal` came from: `raise_amount(hand, descriptor)` for each member, so a raise maps to the raise-to it resolves to there and `fold`/`check-call` map to `None`; a descriptor that was not legal has no entry, its band being empty and masked out and never a value borrowed from its neighbour (`sizing.md` §2, §3). `amount` **is** `amounts[action]`. Bound: `A` entries a decision — 3 on the fixed row, 6 on the two uncapped ones.

**`reveal`** — `board` (the board as dealt up to the hand's last decision, 0–5 card spellings — see the capture paragraph below), `showdown`, `split`, and `seats`: one entry per seat **in seat order**, each `{"seat", "hole", "shown", "won"}`, `hole` being that seat's two spellings however it finished, a folded seat's included (`records.md` §5). `shown` is **"never applied a `fold` descriptor at any of its decisions"** and **not** `state.statuses`, which reads `False` for a seat that mucks at showdown exactly as for a folder (`state.py:2414-2422`). `showdown` is two or more seats `shown` **and** a five-card board; `won` is that seat's `hole` plus `board` forming a best five-card hand **at least as good as every shown seat's** — `StandardHighHand.from_game_or_none(hole, board)` compared by the `Hand`'s own `__lt__`/`__eq__`, entry order, never `CLASS_OF`'s 0–8 class, which cannot see a kicker and so cannot see a tie. The **direction** of that comparison is the library's and must not be flipped: `StandardHighHand` is not a low hand, so `a < b` reads "`a` is the weaker hand", which is why "at least as good as `other`" is `not (best < other)` and a tie is `not (best < other) and not (other < best)` (`hands.py:96-188`). `won` is a plain `bool`, `False` for every seat when no five-card hand can be formed (fewer than three board cards), never `None`; `split` is `showdown` **and** two or more shown seats tied for best, so a four-card board is never a split. Bound: at most `2·seats + 5` card spellings and `seats + 3` other facts a hand.

**The cards are captured during the loop, and must be.** `State._muck_hole_cards` **clears** `hole_cards[i]` and sets `statuses[i] = False` (`state.py:2414-2422`, reached from `:5711-5740`), so a finished state is not a record of who held what. Every seat's two cards are therefore read at the **first** decision with `card_spelling`, the module's one spelling, and `player_index(seat, seats)` where `seats = seat_count(hand._shape)`; and the final board is the **last** decision's `board` fact. That board is the board **as dealt up to the hand's last betting decision** and is the final one only because a hand that still has a decision to take has its next card dealt before it: a hand whose betting closes **all-in** has its remaining board dealt in the terminal transition, after its last decision, so its recorded `board` is short (empty in the extreme) and its `showdown` is `false` — the reveal never names a card the last decision did not have. A later reader must not "simplify" this back to the finished state.

**`counterfactual`** — `None` at **every** decision of a hand whose `showdown` is false, whose `split` is true, or whose pot was built in **levels**; otherwise a mapping over **exactly** that decision's legal descriptors, computed **once after the hand** from the recorded decisions and the facts captured above, never at decision time and never inside the loop's action choice. The arithmetic is `counterfactual.md` §4's and is not re-derived: `C = s_0 − stacks[s]` and `to_call` at the decision, `added(a)` = `0` for `fold`, `to_call` for `check-call`, `amounts[a] − own_street_bet` for a raise, `C_R(t)` from the **last** decision's `stacks` with the acting seat's own `added` restored, `O` the other seats' contributions, `later` the seat's own commitments after the decision, and `fold → −C`, a live action on a seat that is **`won` and `shown`** `→ O`, on any other `→ −(C + added(a) + later)`. The `shown` conjunct is load-bearing and is not a second spelling of anything: a seat that makes a live decision and then **folds on a later street** is not live at the end, so that decision still ends in a fold, commits `C + added + later` and wins nothing — however good its cards were, which is the one thing `won` alone reports (`counterfactual.md` §4). This module supplies the three things that arithmetic needs from below an entry point: `own_street_bet` (`state.bets[player_index(seat, seats)]`, read before the step and kept out of the record), `C_R`'s last-decision correction, and a `try` that degrades **every** decision of the hand to `None` on a fact missing or undefined while never catching the loop's own exceptions, with `amounts` still written.

**The third case is the resolution's own self-check, computed and never assumed.** `payoffs(hand)`'s mapping is handed to the resolution — it is not recomputed — and the arithmetic above is taken only when, for **every** seat, the chips that seat took from the pot, `payoffs[seat] + C_R(seat)`, are exactly `0` or exactly the whole pot `Σ C_R(seat)`; which is `Δ` being exactly `−C_R(seat)` or exactly `O(seat)`, the two values §4's table can produce. A seat paid a **side pot** — an all-in for less, so a seat is paid by its eligibility as well as by its rank — satisfies neither, and such a hand carries no values rather than wrong ones, exactly as a `split` one does (`counterfactual.md` §4's last paragraph, `hand.md` §5).

**Its cost, and the invariant it must satisfy.** One best-five search per seat on the final board — the search `readout.md` §2 already prices, nothing pre-flop and no equity sample — and `A` integer comparisons a decision, once per hand however many decisions it holds (`cost.md` §G6.1). And `v` at the descriptor the hand **applied** equals `payoffs[seat]` at every decision of a resolved hand, that seat's last decision included: a realised fold gives `−C`, a realised live action on a `won` **and `shown`** seat `O = Δ`, on any other `−(C + added + later) = Δ` (`counterfactual.md` §4, `episode-battery.md` §4). It is exact because the two unresolvable cases are **checked and not assumed** — a `split` hand, and the self-check above against the hand's own `payoffs` — so a hand the identity would not hold on carries no values instead of wrong ones.

**Measured, this build on this host** (a measurement beside the artefact, never a bound): the reveal's search prices at 2.5 µs with 3 board cards, 26.7 with 4 and 98.8 with 5, so ≈0.20 ms a hand at two seats and ≈0.59 at six, and 200 always-check-call hands cost 4.88 ms a hand at two seats and 19.40 at six against 4.37 and 17.00 for the same hands driven through the public loop alone — **+0.52 and +2.40 ms a hand, +1.4 % and +0.8 %** of the 36.09 and 302.56 ms a hand those two shapes measured before the change, so ASM-21's band does not move (`cost.md` §G6.1).

## 6. What the battery may assert of an episode — `episode-battery.md`

The battery paragraph that lived here by owner has moved whole to `episode-battery.md`: the refusals and their measured messages, the record's keys and per-decision facts with the replay, the six-seat readings, and the bounds, `amounts`, `reveal` and `counterfactual` assertions D-43 adds. Nothing was dropped.
