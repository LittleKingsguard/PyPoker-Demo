"""The one decision stream a run retains: the exploration-off pass (`records.md` §15).

`training.run` retains **no** training decisions: the loop consumes a hand's batch and
discards it, so a log of the behaviour policy would be a log of the exploration schedule —
the defect D-28 recorded as fatal, because at the live budget almost the whole sample sits
on the ε ramp and every class clears a floor by construction (`sizing.md` §4, ASM-38,
D-29).  What a run retains instead is exactly one stream: after a variant's training at a
seed ends, it plays that variant's **greedy pass** — the same number of hands as the run's
own sample budget, against the same frozen pool, on the run's own seed — and records it
under the run record's `greedy` block.

**The sample is the run's own.**  Hand *i* of the pass is dealt at the seed training dealt
hand *i* at, draws its opponent with the same derivation, and puts the learner in the same
seat (`seeds.md` §2, `episode.md` §1): the pass is the training sample replayed against the
model training finished with, so a live-budget run yields a 1,000-hand pass, a
ten-hand battery run a ten-hand pass, and the run's hand count, seat split and opponent
membership are the ones the record already states (`sizing.md` §4, `ladder.md` §6).  The
pass is therefore cheap in exactly the proportion the run is, which is why the small
budgets every battery uses stay small (`battery.md` §2).

**The mode is the policy's and it is `off`.**  The decision is `agents.as_policy`'s policy
at `exploration="off"`: the masked maximum and `rule.md` §5's tie-break alone, with **no
generator drawn from**, so two passes over one model decide identically and the block is a
function of the model and of the hands and not of a seed (`sizing.md` §4,
`docs/L3/agents/rule.md` §4, §7, D-19).

**The bound is refused and never truncated.**  A pass is at most 2,000 hands and at most
24,000 decision records per variant per seed, and a pass that would exceed either is
refused naming both counts, because a truncated log silently reports a different sample
(`sizing.md` §4, `records.md` §15, ASM-38, `docs/L3/features/flat-numeric.md` §5's rule for
the history block).  The hand bound is checked before the first hand of the run is dealt —
the pass's hand count *is* the budget, so it is known up front and nothing is written for a
run that cannot produce its own record — while the record bound can only be known as the
pass accumulates and is therefore refused the moment a decision record would cross it.
"""

import engine
import evaluation
import features

from . import declarations, episode, errors, seeds as seeds_module

#: The two bounds one pass must stay inside, read off the module's declaration so the
#: refusal and the check cannot drift apart (`sizing.md` §4, `records.md` §15, ASM-38).
HANDS_BOUND = declarations.GREEDY_HANDS
DECISIONS_BOUND = declarations.GREEDY_DECISIONS

#: The one mode a retained decision carries.  A block whose `mode` is anything else — or a
#: census computed over training decisions — is refused by name rather than read
#: (`records.md` §15, `sizing.md` §7's exploration artefact, D-28).
MODE = "off"


def _check_hands(hands, where):
    """Refuse a pass whose hand count would exceed the bound, naming both counts.

    Raised at the top of `training.run`, before the pool is built and before a hand is
    dealt: the pass's hand count is the run's own sample budget (`sizing.md` §4), so a
    budget over 2,000 could never produce a record this module is allowed to write, and a
    refusal that arrived after 200,000 trained hands would have spent the run to learn it
    (`e2e-surface.md` §2, ASM-38).
    """
    if int(hands) > HANDS_BOUND:
        raise errors.GreedyPassRefused(
            "%s refused the greedy pass: the run's budget is %d hands per variant per "
            "seed, so the pass would play %d hands, and one pass plays at most %d "
            "(sizing.md §4, records.md §15, ASM-38)"
            % (where, int(hands), int(hands), HANDS_BOUND)
        )


def _check_decisions(recorded, where):
    """Refuse the moment one more decision record would cross the record bound.

    The record bound is a property of the sample and not of the budget — a hand holds a
    handful of decisions and the fixed game's own ceiling is 23 applied actions — so it is
    checked as the pass accumulates and never guessed from the hand count
    (`sizing.md` §4, `records.md` §15).
    """
    if recorded > DECISIONS_BOUND:
        raise errors.GreedyPassRefused(
            "%s refused the greedy pass: it would record %d decisions, and one pass "
            "records at most %d (sizing.md §4, records.md §15, ASM-38)"
            % (where, int(recorded), DECISIONS_BOUND)
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


def _pass(pool, shape, seed, budget, policy, where):
    """One variant's greedy pass at one seed: `records.md` §15's block, bounded.

    The learner's side is `policy` — `agents.as_policy` at `exploration="off"` — and the
    other side is `evaluation.opponent(pool, _opponent_seed(seed, i))`, the same draw
    training made at the same hand (`evaluation/surface.md` §8, ASM-16).  The hand is
    `engine.play_hand(hand_seed, seat0, seat1, shape=shape)`, so both sides play **the
    run's own shape** and a six-descriptor learner's decisions are six-descriptor ones
    (`engine/surface.md` §10, `shapes.md` §2, D-29).  Seats alternate by swapping the two
    policies, exactly as training alternates them (`episode.md` §1).

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
    hands = int(budget)
    _check_hands(hands, where)
    net_chips = []
    decisions = []
    for index in range(hands):
        hand_seed = seeds_module._deal_seed(int(seed), index)
        opponent = evaluation.opponent(
            pool, seeds_module._opponent_seed(int(seed), index)
        )
        seat = episode._seat(index)
        if seat == 0:
            played = engine.play_hand(hand_seed, policy, opponent, shape=shape)
        else:
            played = engine.play_hand(hand_seed, opponent, policy, shape=shape)
        net_chips.append(_net_chips(played.get("payoffs") or {}, seat))
        for decision in played["decisions"]:
            if episode._decision_seat(decision) != int(seat):
                continue
            decisions.append(_decision_record(decision, shape))
            _check_decisions(len(decisions), where)
    return {
        "mode": MODE,
        "seed": int(seed),
        "hands": hands,
        "net_chips": net_chips,
        "decisions": decisions,
    }
