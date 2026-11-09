# engine — `play_hand` and the episode record

- **Owner:** one whole hand as a record — the policy protocol it drives, the episode and decision shapes, and where the reward lands
- **Ceiling:** 100 lines. At the ceiling, split by owner — never append

## 1. The signature and its refusals

    def play_hand(seed: int, seat0_policy, seat1_policy) -> dict

- Refuses a seed that is not an integer, as `new_hand` does (`hand.md` §2), **before** the deal, so a
  refused call cannot move the stream.
- Refuses a policy that is not callable, naming which seat’s policy it was (`errors.md` §2).
- Refuses an answer outside `legal_actions` for that decision — by value, never by identity, because
  `features.decode_action` builds a fresh equal string (`actions.md` §1).
- Does **not** catch a policy’s own exception: it propagates to the caller unchanged, and is never
  turned into a fold (`L2 surface.md` §10, D-2).

## 2. The loop

    hand = new_hand(seed)                      # the ONLY seeding point; play_hand never seeds
    decisions = []
    while not is_terminal(hand):
        readout = readout(hand)                # readout.md — a fresh mapping
        legal = readout["legal"]               # the same tuple legal_actions returns
        seat = readout["seat"][0]
        policy = seat0_policy if seat == 0 else seat1_policy
        action = policy(readout, legal)        # the policy protocol of e2e-surface §2
        if action not in legal: refuse         # InvalidAction, errors.md
        decisions.append({seat, readout, legal, action, reward=0})
        hand = apply_action(hand, action)      # stepping.md §2 — one history entry per decision
    payoff = payoffs(hand)                     # hand.md §5
    place the reward (§3)
    return {"seed": seed, "decisions": decisions, "payoffs": payoff}

There is one hand in flight and no interleaving, threading or re-entry: one global `random` stream
deals every hand, so sequential play is a contract and not an implementation choice, and `play_hand`
calls `new_hand` rather than seeding itself, so no call seeds the stream twice (D-16, ASM-2,
`L2 surface.md` §1).

## 3. The episode record

The three required keys of `records.md` §5, and beyond them nothing a caller may depend on:

| Key | Content |
|---|---|
| `seed` | the seed the call was made with, unchanged — an `int` |
| `decisions` | a `list` of decision records, in the order they were taken |
| `payoffs` | the mapping `payoffs(hand)` returned for this completed hand: `{0: p0, 1: p1}` |

Each decision record carries the five facts `records.md` §5 requires; a sixth key is this module's own
and no caller may depend on one (`L2 surface.md` §1, D-13).

- `seat` — the decision’s own acting seat, in the shape of `readout`’s `seat` fact, so
  `(index, on_button)`; the index is the first number inside it (`records.md` §5);
- `readout` — the whole eleven-fact mapping of that decision, taken **before** the action, so a record
  can be encoded after the hand is over (D-3);
- `legal` — that decision’s ordered descriptor tuple;
- `action` — the descriptor the policy returned and the engine applied;
- `reward` — see below.

**Where the reward lands (ASM-12).** Every decision is created with `reward` 0. When the hand ends,
each seat’s **last** decision has its reward set to that seat’s net chip delta, and every other
decision stays 0, so a hand carries at most one non-zero reward per seat and it is the hand’s outcome,
never a shaped per-decision term. A split leaves both rewards 0 — which is correct and is why the
battery asserts "at most one non-zero reward per seat", not "exactly one". A seat that never acted
(the big blind when the button folds pre-flop) carries no decision and therefore no reward
(`L2 environment.md` §3). Rewards are plain `int` chip counts, not scaled: `agents` owns any scaling
(D-3, `records.md` §4).

The record names **no hand handle**, no state and no card outside a readout: nothing below an entry
point is surface (`e2e-surface.md` §1, brief §5). The episode is a record of what happened and is not
re-opened; a caller that wants the hand advanced further drives `new_hand`/`apply_action` itself
(`L2 environment.md` §3).

## 4. Policy independence

`play_hand` knows no builder by name: `agents.as_policy`, `agents.build_baseline`,
`evaluation.policy_from` and `harness.seam` all return "a callable taking `(readout, legal)` and
returning one member of `legal`", and that is the whole protocol (`e2e-surface.md` §2, D-13). The
engine imports none of them. It also does not inspect the policy, count its calls or memoise
anything: the same readout is handed to a policy as many times as the policy asks to see it.

One seed and one pair of policies give one record, a different seed gives a different one, and the two
policies may be the same object (a self-play episode) (ASM-2, FAM-4).

## 5. What the battery may assert of an episode

Driving only `play_hand` (and the other eight for support): the record has `seed`, `decisions`,
`payoffs`; the seed is the seed it was called with; there is at least one decision and at most 200;
every decision has `seat`, `readout`, `legal`, `action`, `reward`, the readout has the eleven facts, the
action is a member of the decision’s legal tuple, and the sequence of actions replays the same hand
when driven by hand through `new_hand`/`apply_action`; each seat has at most one non-zero reward and
it equals that seat’s payoff; the payoffs are two numbers summing to zero; two identical calls give
equal records; two different seeds give different ones; a non-callable policy and an illegal answer
are refused; and a policy that raises propagates its own exception.
