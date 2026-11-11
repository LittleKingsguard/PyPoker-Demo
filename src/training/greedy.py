"""The one decision stream a run retains: the exploration-off pass (`records.md` §15).

`training.run` retains **no** training decisions: the loop consumes a hand's batch and
discards it, so a log of the behaviour policy would be a log of the exploration schedule —
the defect D-28 recorded as fatal, because at the live budget almost the whole sample sits
on the ε ramp and every class clears a floor by construction (`sizing.md` §4, ASM-38,
D-29).  What a run retains instead is exactly one stream: after a variant's training at a
seed ends, it plays that variant's **greedy pass** — the run's own sample, its first
`min(budget, 2,000)` hands, against the same frozen pool, on the run's own seed — and
records it under the run record's `greedy` block.

**The sample is the run's own prefix.**  Hand *j* of the pass is the run's own hand *j*:
`episode._hand(pool, shape, seed, j, policy)` deals it at the seed training dealt hand *j*
at, draws its opponent with the same derivation, and puts the learner in the same seat
(`seeds.md` §2, `episode.md` §1), so the pass of length `min(budget, 2,000)` is the training
sample's **prefix** replayed against the model training finished with.  At or below 2,000
hands `S = budget`, so a live-budget run yields a 1,000-hand pass and a ten-hand battery run
a ten-hand pass; above it the pass stops after the run's 2,000th hand and the seat split and
opponent membership are still the ones the run's hands have (`sizing.md` §4, `ladder.md`
§6).  Which hands the sample was is therefore stated exactly by the record's own `budget`,
the block's `hands` and the block's `seed` together with `_sample`, and no field beyond the
five the block carries is needed to say it (D-36).  The pass is therefore cheap in the
proportion the run is up to the bound, which is why the small budgets every battery uses
stay small (`battery.md` §2).

**The mode is the policy's and it is `off`.**  The decision is `agents.as_policy`'s policy
at `exploration="off"`: the masked maximum and `rule.md` §5's tie-break alone, with **no
generator drawn from**, so two passes over one model decide identically and the block is a
function of the model and of the hands and not of a seed (`sizing.md` §4,
`docs/L3/agents/rule.md` §4, §7, D-19).

**The hand bound bounds the sample, and no run is refused for its budget.**  A pass is at
most 2,000 hands and at most 1,000 decision records **per slot of the shape's history
capacity**, per variant per seed — 24,000 at the default shape, 66,000 and 98,000 on the
uncapped ones — and a pass that would exceed either is refused naming both counts and the
shape's capacity, because a truncated log silently reports a different sample (`sizing.md`
§4, `records.md` §15, `shapes.md` §8, ASM-38, ASM-42,
`docs/L3/features/flat-numeric.md` §5's rule for the history block).  The hand bound is
refused on the **pass's request**: `_pass` calls `_check_hands` on the number of hands it is
asked to play, so a request above 2,000 names the count asked for and the bound, while `run`
asks only for `_sample(budget)` — at most the bound — and so trains and passes over the
run's first 2,000 hands whatever the budget is (`sizing.md` §4, `records.md` §15, ASM-38,
D-36).  A request that is **not a positive integer** — a `bool`, a float, a string, 0 or a
negative — is refused by the same seam before the first hand is dealt, naming the request
and the two ends of the contract, so no block is returned whose `hands` is not a positive
whole number of hands it played (`errors.md` §4, D-36).  The record bound can only be known
as the pass accumulates and is therefore refused the moment a decision record would cross
it.
"""

import features

from . import declarations, episode, errors

#: The two bounds one pass must stay inside, read off the module's declaration so the
#: refusal and the check cannot drift apart (`sizing.md` §4, `records.md` §15, ASM-38).
#: `DECISIONS_BOUND` is the **default shape's** record bound; a pass on another shape reads
#: its own through `declarations.greedy_decisions(shape)` (`shapes.md` §8).
HANDS_BOUND = declarations.GREEDY_HANDS
DECISIONS_BOUND = declarations.GREEDY_DECISIONS

#: The one mode a retained decision carries.  A block whose `mode` is anything else — or a
#: census computed over training decisions — is refused by name rather than read
#: (`records.md` §15, `sizing.md` §7's exploration artefact, D-28).
MODE = "off"


def _sample(budget):
    """How many hands one pass plays: `min(int(budget), HANDS_BOUND)`, and no more.

    One pass plays `min(budget, HANDS_BOUND)` hands, so at or below the bound the rule is
    the identity — the pass replays exactly the hands such a run always replayed — and above
    it the pass is a 2,000-hand sample of the run's own hands, its first `HANDS_BOUND` ones
    (`greedy.md` §1, §4).  The hand bound therefore bounds the **sample** and never the run:
    a 200,000-hand budget trains and passes over its first 2,000 hands, so a run is never
    refused for its budget (`sizing.md` §4, `records.md` §15, ASM-38, D-36).  Its argument is
    the run's own budget, which `run` validates as a positive integer of at least ten hands
    (`InvalidBudget`, `loop.md` §6), and its result is the pass request that `_check_hands`
    bounds (`greedy.md` §4, D-36).
    """
    return min(int(budget), HANDS_BOUND)


def _check_hands(hands, where):
    """Refuse a pass asked for more hands than the bound, naming both counts.

    The bound is on the **pass's request**, raised by `_pass` on the number of hands it is
    asked to play: a request above 2,000 could never produce a block this module is allowed
    to write, so it is refused before the pass deals its first hand (`errors.md` §4,
    ASM-38).  `run` never asks for the budget — it asks for `_sample(budget)`, which is at
    most the bound — so an over-bound budget reaches this check only when a caller of `_pass`
    asks for more hands than the bound, which the loop never does: the run trains and passes
    over its first 2,000 hands (`D-36`).

    The request must also be a **positive integer**: a `bool`, a float, a string, 0 or a
    negative is refused naming the request and the contract — a pass plays at least one hand
    and at most `HANDS_BOUND` — before the pass deals its first hand, which is what keeps
    `int()` from truncating a float into an honest-looking count and keeps every returned
    block's `hands` a positive integer equal to `len(net_chips)` (`errors.md` §4, D-36).
    """
    if isinstance(hands, bool) or not isinstance(hands, int) or hands < 1:
        raise errors.GreedyPassRefused(
            "%s refused the greedy pass: the pass was asked for %r hands, and a pass "
            "plays at least 1 hand and at most %d (sizing.md §4, records.md §15, "
            "ASM-38, D-36)"
            % (where, hands, HANDS_BOUND)
        )
    if int(hands) > HANDS_BOUND:
        raise errors.GreedyPassRefused(
            "%s refused the greedy pass: the pass was asked for %d hands, and one pass "
            "plays at most %d (sizing.md §4, records.md §15, ASM-38)"
            % (where, int(hands), HANDS_BOUND)
        )


def _check_decisions(recorded, where, shape=None):
    """Refuse the moment one more decision record would cross the record bound.

    The record bound is a property of the sample and of the run's **own** shape: a hand
    holds a handful of decisions, the shape's history capacity bounds how many the learner
    can have made before the block overflowed, and `records.md` §15 makes the pass's bound
    1,000 × that capacity — so it is read through `declarations.greedy_decisions(shape)` and
    checked as the pass accumulates, never guessed from the hand count (`sizing.md` §4,
    `records.md` §15, `shapes.md` §8, ASM-38, ASM-42).
    """
    bound = declarations.greedy_decisions(shape)
    if recorded > bound:
        raise errors.GreedyPassRefused(
            "%s refused the greedy pass: it would record %d decisions, and one pass on "
            "the shape %r records at most %d — 1,000 × its history capacity of %d slots "
            "(sizing.md §4, records.md §15, shapes.md §8, ASM-38, ASM-42)"
            % (
                where,
                int(recorded),
                declarations.require_game(shape, "greedy._check_decisions"),
                bound,
                declarations.shape_history(shape),
            )
        )


def _net_chips(payoffs, seat):
    """One hand's net chip delta for the learner's seat (`records.md` §15).

    Read off the episode's own `payoffs` — the engine's zero-sum outcome — and never
    recomputed here: the pass reports the sample's price and computes no average
    (`records.md` §5, §15, ASM-23).
    """
    value = payoffs.get(int(seat))
    if value is None:
        value = payoffs.get(str(int(seat)))
    return float(value) if value is not None else 0.0


def _decision_record(decision, shape):
    """One `records.md` §15 decision record, from the episode decision it was resolved at.

    `index`/`descriptor` are the chosen index and the descriptor it decodes to in **the
    run's shape's** declared order; `amount`/`minimum`/`maximum` are the raise-to the engine
    resolved and the two bounds it was resolved between, all three `None` on a decision
    where no raise was legal; `legal` is the decision's legal index set, so a census
    re-derives no mask (`sizing.md` §2–§3, `records.md` §5, §15).

    `tie` is the one key the exploration-off surface does not report (see `_pass`).
    """
    index = episode._index(decision["legal"], decision["action"])
    return {
        "index": int(index),
        "descriptor": features.decode_action(int(index), shape=shape),
        "amount": decision.get("amount"),
        "minimum": decision.get("minimum"),
        "maximum": decision.get("maximum"),
        "legal": [int(member) for member in features.legal_indices(decision["legal"])],
        "tie": False,
    }


def _pass(pool, shape, seed, hands, policy, where):
    """One variant's greedy pass at one seed: `records.md` §15's block, bounded.

    The fourth argument is the number of hands the pass is **asked** for: `loop` hands it
    `_sample(budget)`, so it is the sample's count and not the run's budget.  It is a
    **positive-integer request**: `_check_hands` refuses anything else by name before the
    first hand is dealt, so `hands` is always a positive whole number and the block's
    `hands` always equals `len(net_chips)` (`errors.md` §4, D-36).  The block is
    therefore the run's **prefix** — hand *j* is the run's own hand *j*, dealt by
    `episode._hand` below, so a pass of `S` hands is the first `S` hands training played and
    `hands` reports that sample's count (`greedy.md` §1, §4, D-36).

    The learner's side is `policy` — `agents.as_policy` at `exploration="off"` — and the
    other side is the hand's opposition, drawn by `episode._hand` from
    `evaluation.opponent(pool, _opponent_seed(seed, i))` exactly as training drew it at the
    same (evaluation/surface.md §8, ASM-16, `seats.md` §4).  The hand is
    `engine.play_hand(hand_seed, seat0, seat1, shape=shape)` on a two-seat shape and
    `engine.play_hand(hand_seed, seats=(...), shape=shape)` on a shape with more seats, so
    both sides play **the run's own shape** and a six-descriptor learner's decisions are
    six-descriptor ones (`engine/surface.md` §10, `shapes.md` §2, D-29).  The learner's seat
    is `episode._seat(i, shape)` — `i mod seats` — and the pass therefore rotates through
    the shape's seats exactly as training does, which is why a six-seat run's block is the
    same sample training played (`episode.md` §1, `seats.md` §4, ASM-43).

    **On `tie`, and the one thing this module cannot observe.**  `records.md` §15 makes
    `tie` "whether the tie-break, and not a strict maximum, chose the index".  The
    exploration-off surface returns a *policy*: a callable from `(readout, legal)` to one
    descriptor, and nothing else — `agents.as_policy`'s decision and
    `evaluation.policy_from`'s discard the flag their rule returns, while `agents.act`'s
    record carries it only on the *schedule* arm, whose decision is not this pass's.  No
    granted call therefore reports the flag for an exploration-off decision, so the block
    carries `False` and this module claims exactly that: no tie-resolved decision is
    *reported*.  Since the tie-break decides only where two masked values stand within
    `rule.md` §5's `1e-9` relative tolerance of the masked maximum, the sample's `tie`
    share is a measure-zero corner rather than a systematic omission — but the omission is
    named here and returned to L1 as an `ADJUDICATION` rather than papered over
    (`modules.md` §3, D-13, `sizing.md` §7's tie artefact).
    """
    _check_hands(hands, where)
    hands = int(hands)
    net_chips = []
    decisions = []
    for index in range(hands):
        played, seat = episode._hand(pool, shape, int(seed), index, policy)
        net_chips.append(_net_chips(played.get("payoffs") or {}, seat))
        for decision in played["decisions"]:
            if episode._decision_seat(decision) != int(seat):
                continue
            decisions.append(_decision_record(decision, shape))
            _check_decisions(len(decisions), where, shape)
    return {
        "mode": MODE,
        "seed": int(seed),
        "hands": hands,
        "net_chips": net_chips,
        "decisions": decisions,
    }
