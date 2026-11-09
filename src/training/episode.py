"""One episode, as the transition batch `agents.learn` consumes (records.md §4, ASM-12).

`engine.play_hand` returns the ordered decisions, each carrying its seat, its readout,
its legal descriptors, the action applied and the reward the engine placed at that seat's
terminal decision (engine/surface.md §10, docs/L3/engine/episode.md §3). This module
turns the decisions **of the learner's own seat**, in decision order, into transitions:

- the successor of a decision is the learner's next decision in that hand, not the
  opponent's, because the update is over the learner's own state-action pairs;
- the terminal decision is the learner's last one, and it carries the seat's reward under
  the variant's utility and its own mask, having no successor to read (`records.md` §4,
  ASM-12);
- the batch is the caller's order and is neither sampled nor shuffled, which is what lets
  two arms of a pair declare one sample order (agents/surface.md §7, ladder.md §4, ASM-7).

**This is the one place a utility is applied** (`utilities.md` §4, D-20).  The engine
places the hand's net chip delta at the seat's terminal decision and nothing here rewrites
the hand; the transform re-expresses that number as the reward of the utility the variant
is trained on, at that terminal decision only, and every other decision keeps `0.0`.  The
arithmetic is selected by the **reward token** the catalogue states for the member — the
catalogue's own description of what a member delivers — so no member name is copied into
this module: `net-chip-delta` is the delta itself and `squared-stack-shortfall-delta` is
`(U(s_before) − U(s_after)) / U(s_0)` with `U(s) = (T − s)²` (`utilities.md` §2, §4).
"""

import agents
import engine
import features

from . import errors

#: `U(s) = (T − s)²`: the squared shortfall of one seat's stack from all the chips in play.
def _shortfall(total, stack):
    """`U(s) = (T − s)²`, the squared stack shortfall `utilities.md` §2 defines."""
    return (float(total) - float(stack)) ** 2


def _reward_token(utility):
    """The reward token a utility delivers, read from the catalogue (`utilities.md` §2).

    The catalogue `agents.learners()` publishes is the only source of a member's reward,
    so the arithmetic below is keyed by the token a member states and never by a name
    copied out of a document (D-20, `utilities.md` §2).
    """
    declared = agents.learners()
    catalogue = declared.get("utilities") if isinstance(declared, dict) else None
    if not isinstance(catalogue, dict):
        catalogue = {}
    if utility is None:
        name = next(iter(catalogue), None)
    else:
        name = utility
    entry = catalogue.get(name) if isinstance(name, str) else None
    if not isinstance(entry, dict) or not isinstance(entry.get("reward"), str):
        raise errors.ConfigurationInvalid(
            "training.run refused the utility %r: the catalogue agents.learners() "
            "publishes carries %s, and a utility's reward is what the transition step "
            "reads (utilities.md §2, §5, D-20)"
            % (utility, ", ".join(str(key) for key in catalogue) or "nothing")
        )
    return name, entry["reward"]


def _chips_in_play(decision, seed, seat):
    """`T` from one decision's readout, or the refusal naming the hand and both totals.

    `T` is `sum(readout['stacks']) + readout['pot']`: the pot is un-awarded and chips are
    conserved at every decision, so the two seats' stacks and the pot are all the chips
    the hand holds (`utilities.md` §4, ASM-6).  A hand whose total disagrees with the
    stacks the game declares is refused by name with the hand's seed and both totals,
    because a normaliser that is not the game's own would make one reward
    incommensurable with the next (ASM-28).
    """
    config = engine.game_config()
    starting_stack = float(config["starting_stack"])
    declared = float(config["seats"]) * starting_stack
    readout = decision["readout"]
    total = float(sum(readout["stacks"]) + readout["pot"])
    if total != declared:
        raise errors.ChipConservationBroken(
            "training.run refused the hand at seed %r: the chips in play at seat %r's "
            "decision total %r, and the game declares %d seats at a starting stack of %r, "
            "which is %r (ASM-6, utilities.md §4)"
            % (seed, seat, total, int(config["seats"]), starting_stack, declared)
        )
    return total, starting_stack


def _net_chips(decision, seed, seat):
    """`r = delta`: the decision's own reward, unshaped (`utilities.md` §2, ASM-12)."""
    del seed, seat  # the net chip delta needs neither the hand nor the readout
    return float(decision["reward"])


def _stack_shortfall(decision, seed, seat):
    """`r = (U(s_0) − U(s_0 + delta)) / U(s_0)`: the shortfall delta, normalised (§4, D-20).

    `s_before` is the stack the fixed game deals every hand from and `s_after` is that
    stack plus the decision's own reward, the hand's net chip delta for the seat (D-2,
    ASM-6).  The normaliser is the shortfall a hand begins with, which is what keeps the
    objective on the scale the learner was tuned for: a ±2-chip hand scores +0.190 /
    −0.210 and an all-in +1.000 / −3.000 (`utilities.md` §2, D-20).
    """
    total, starting_stack = _chips_in_play(decision, seed, seat)
    before = _shortfall(total, starting_stack)
    after = _shortfall(total, starting_stack + float(decision["reward"]))
    if before == 0.0:
        raise errors.ChipConservationBroken(
            "training.run refused the hand at seed %r: the shortfall a hand begins with "
            "is 0, so the utility's normaliser is undefined (utilities.md §4)" % (seed,)
        )
    return (before - after) / before


#: The arithmetic each catalogue reward token names (`utilities.md` §2).  A token with
#: no arithmetic here is a reward this module cannot deliver, and is refused by name
#: rather than defaulted to the net chip delta (`utilities.md` §4, D-20).
REWARDS = {
    "net-chip-delta": _net_chips,
    "squared-stack-shortfall-delta": _stack_shortfall,
}


def _reward_function(utility):
    """The reward arithmetic one catalogue member's token names, or the refusal (§4)."""
    name, token = _reward_token(utility)
    arithmetic = REWARDS.get(token)
    if arithmetic is None:
        raise errors.ConfigurationInvalid(
            "training.run refused the utility %r: it delivers the reward %r, and this "
            "module applies %s (utilities.md §4, D-20)"
            % (name, token, ", ".join(REWARDS))
        )
    return name, arithmetic


def _seat(index):
    """The seat the learner plays in hand `index`: seats alternate, seat 0 holds the button.

    Seat 0 posts the small blind and holds the button in **every** hand (`engine/surface.md`
    §4), so a run alternates the learner's seat by swapping the two policies it hands to
    `engine.play_hand` (`docs/L3/training/episode.md` §1, league.md §3).
    """
    return int(index) % 2


def _decision_seat(decision):
    """The acting seat an episode decision records, as one integer.

    `readout`'s `seat` fact is `(index, on_button)`, and a record may carry either the pair
    or the bare index; the index is the first integer inside it (records.md §5).
    """
    value = decision["seat"]
    if isinstance(value, int) and not isinstance(value, bool):
        return int(value)
    try:
        for item in value:
            if isinstance(item, int) and not isinstance(item, bool):
                return int(item)
    except TypeError:
        pass
    raise errors.ConfigurationInvalid(
        "an episode decision carries a seat that is not a seat index: %r" % (value,)
    )


def _index(legal, action):
    """The vocabulary index of the descriptor a decision applied.

    `features.legal_indices` is position-aligned with the descriptors it is given
    (features/surface.md §8), so the chosen descriptor's index is read by its position.
    """
    indices = list(features.legal_indices(legal))
    for position, descriptor in enumerate(legal):
        if descriptor == action:
            return int(indices[position])
    raise errors.ConfigurationInvalid(
        "an episode decision applied a descriptor outside its own legal actions: %r" % (action,)
    )


def _transitions(episode, seat, encoder, utility=None):
    """The learner's transitions for one hand, in decision order (records.md §4).

    `reward` is the decision's own, re-expressed at the seat's **terminal** decision by the
    utility the variant is trained on and left exactly as the episode placed it — `0.0` —
    at every other one (`records.md` §5, `utilities.md` §4, ASM-12, D-20).  No member name
    is spelled here: the arithmetic is selected by the reward token the catalogue states
    for `utility`, and a member naming no token this module applies is refused rather than
    defaulted.  `terminal` is **positional** — the last decision the seat made — and never
    inferred from the reward, because a split pot pays nothing and a zero-reward terminal
    decision is normal (`docs/L3/training/episode.md` §4).  A hand in which the seat never
    acted yields `[]`: no update, and no empty batch handed to `agents.learn`.
    """
    resolved, arithmetic = _reward_function(utility)
    del resolved  # the member's name is checked, its reward token is what the step reads
    hand_seed = episode.get("seed")
    own = [
        decision
        for decision in episode["decisions"]
        if _decision_seat(decision) == int(seat)
    ]
    records = []
    for position, decision in enumerate(own):
        observation = features.encode(encoder, decision["readout"])
        legal = list(features.legal_indices(decision["legal"]))
        terminal = position + 1 == len(own)
        if terminal:
            # A terminal transition has no successor; `learn` reads none, and no empty
            # mask is legal, so it carries the decision's own mask (agents/surface.md §7).
            next_observation = observation
            next_legal = legal
            reward = arithmetic(decision, hand_seed, seat)
        else:
            successor = own[position + 1]
            next_observation = features.encode(encoder, successor["readout"])
            next_legal = list(features.legal_indices(successor["legal"]))
            reward = float(decision["reward"])
        records.append(
            {
                "observation": observation,
                "next_observation": next_observation,
                "action": _index(decision["legal"], decision["action"]),
                "reward": reward,
                "terminal": terminal,
                "legal": legal,
                "next_legal": next_legal,
            }
        )
    return records
