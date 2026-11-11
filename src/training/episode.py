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

**This is also where one hand is seated** (`seats.md` §4, ASM-43).  `_hand` is the loop's
and the greedy pass's one way of dealing hand *i*: it derives the two seeds, puts the
learner in `_seat(i, shape)` — `i mod seats`, with the seat count read from
`engine.game_config` and never written down here — and fills the other seats with the
hand's opponents.  On a two-seat shape that is the two positional policies a run has always
handed `engine.play_hand`; on a shape with more seats it is `seats − 1` **distinct**
opponents from one `evaluation.opponent(pool, seed, seats - 1)` draw, seated in the draw's
order in seat order and played through `play_hand`'s `seats` argument (`seats.md` §4,
`e2e-surface.md` §3.1, ASM-43).  Because training and the pass both call it, they cannot
drift into two samples.
"""

import agents
import engine
import evaluation
import features

from . import errors, seeds as seeds_module

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


def _chips_in_play(decision, seed, seat, shape=None):
    """`T` from one decision's readout, or the refusal naming the hand and both totals.

    `T` is `sum(readout['stacks']) + readout['pot']`: the pot is un-awarded and chips are
    conserved at every decision, so every seat's stack and the pot are all the chips the
    hand holds (`utilities.md` §4, ASM-6, `seats.md` §3).  The total the readout must
    agree with is the **run's own shape's** — `engine.game_config(shape)`'s seats and
    starting stack, so 40 chips in the default shape, 200 on the two-seat uncapped one and
    600 on the six-seat one — and never the default shape's, which is why a no-limit run
    conserves 200 and not 40 (`shapes.md` §2, `seats.md` §2, D-29, ASM-44).  A hand whose
    total disagrees is refused by name with the hand's seed and both totals, because a
    normaliser that is not the game's own would make one reward incommensurable with the
    next (ASM-28).
    """
    config = engine.game_config(shape)
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


def _net_chips(decision, seed, seat, shape=None):
    """`r = delta`: the decision's own reward, unshaped (`utilities.md` §2, ASM-12)."""
    del seed, seat, shape  # the net chip delta needs neither the hand nor the readout
    return float(decision["reward"])


def _stack_shortfall(decision, seed, seat, shape=None):
    """`r = (U(s_0) − U(s_0 + delta)) / U(s_0)`: the shortfall delta, normalised (§4, D-20).

    `s_before` is the stack the run's shape deals every hand from and `s_after` is that
    stack plus the decision's own reward, the hand's net chip delta for the seat (D-2,
    ASM-6, `shapes.md` §2).  The normaliser is the shortfall a hand begins with, which is
    what keeps the objective on the scale the learner was tuned for: a ±2-chip hand scores
    +0.190 / −0.210 and an all-in +1.000 / −3.000 in the default shape, and the same
    arithmetic on the shape's own chips in play elsewhere (`utilities.md` §2, D-20).
    """
    total, starting_stack = _chips_in_play(decision, seed, seat, shape)
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


#: The two positional policies `engine.play_hand` takes — `seat0_policy` and
#: `seat1_policy` — which is the form a hand is played in when the shape seats that many
#: policies, and the form every caller has taken.  Every other shape is played through that
#: entry point's `seats` sequence (`e2e-surface.md` §3.1, §3.5, `seats.md` §4).  It is the
#: **call's** arity and not a shape's seat count: a seat count is read from
#: `engine.game_config` and never written down here (`seats.md` §2–§3, ASM-44, D-29).
POSITIONAL_POLICIES = 2


def _seats(shape=None):
    """The seat count of the shape a run plays, read from `engine.game_config`.

    `engine.game_config(shape)["seats"]` is the one place a hand's seat count is declared,
    so neither this module nor a caller of `_seat` writes a `2` or a `6` down as the game's
    (`seats.md` §2–§3, `engine/surface.md` §3, ASM-44, D-29).
    """
    return int(engine.game_config(shape)["seats"])


def _seat(index, shape=None):
    """The seat the learner plays in hand `index`: `index mod seats` (`seats.md` §4).

    Seat 0 posts the small blind and holds the button in **every** hand
    (`engine/surface.md` §4), and a shape seats `_seats(shape)` policies, so the learner
    rotates through every seat of the run's own shape and each seat holds it for one hand
    in `seats`: position is a real and unequal advantage in a multi-way pot, and rotating it
    keeps a seed's chips from being a measurement of the seat it drew (ASM-43,
    `seats.md` §4, `league.md` §3).  On a two-seat shape this is the alternation a run has
    always had — `index % 2` — so no default-shape hand moves (`shapes.md` §5).
    """
    return int(index) % _seats(shape)


def _hand(pool, shape, seed, index, policy):
    """Hand `index` of the run at `seed`, and the seat the learner held in it.

    Hand *i*'s deal seed and opponent draw seed are `seeds._deal_seed(seed, i)` and
    `seeds._opponent_seed(seed, i)`, so the hand is a function of the tuple and of its index
    alone and training and the greedy pass replay one sample (`seeds.md` §2, ASM-2, ASM-8,
    `greedy.md` §1).  The learner is at `_seat(index, shape)` (`seats.md` §4).

    **A two-seat shape is played exactly as every run has played it**: one opponent from
    `evaluation.opponent(pool, draw_seed)` on the other side, and the two positional
    policies swapped hand by hand because seat 0 holds the button in every hand
    (`e2e-surface.md` §3.5, `engine/surface.md` §4, §10, `shapes.md` §5).

    **A shape with more seats draws `seats − 1` distinct opponents** — one per seat the
    learner does not hold — with `evaluation.opponent(pool, draw_seed, seats - 1)`, seats
    them in the draw's order in the remaining seats **in seat order**, and plays the hand
    through `engine.play_hand(..., seats=(...))`, so no seat faces itself and no policy is
    seated twice (`seats.md` §4, ASM-43, `e2e-surface.md` §3.1).  A pool holding fewer
    members than the draw is `evaluation`'s refusal and propagates unchanged in its owner's
    class, because a refusal re-wrapped here would hide which module owns the contract
    (`records.md` §8, `module-map.md` §2).
    """
    hand_seed = seeds_module._deal_seed(int(seed), int(index))
    draw_seed = seeds_module._opponent_seed(int(seed), int(index))
    seat = _seat(index, shape)
    seats = _seats(shape)
    if seats == POSITIONAL_POLICIES:
        opponent = evaluation.opponent(pool, draw_seed)
        if seat == 0:
            played = engine.play_hand(hand_seed, policy, opponent, shape=shape)
        else:
            played = engine.play_hand(hand_seed, opponent, policy, shape=shape)
        return played, seat
    seating = list(evaluation.opponent(pool, draw_seed, seats - 1))
    seating.insert(seat, policy)
    return engine.play_hand(hand_seed, seats=tuple(seating), shape=shape), seat


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


def _transitions(episode, seat, encoder, utility=None, shape=None):
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

    `shape` is the run's own shape and reaches the arithmetic that reads the game — the
    chips in play and the starting stack a shortfall is normalised against — so a run on
    the six-descriptor shape normalises against that shape's 200 chips and never against
    the default shape's 40 (`shapes.md` §2, `reward.md` §4, D-29).  The transitions
    themselves hold indices and observations only, and both are the shape's own.
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
            reward = arithmetic(decision, hand_seed, seat, shape)
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
