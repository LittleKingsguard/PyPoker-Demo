"""One episode, as the transition batch `agents.learn` consumes (records.md §4, ASM-12).

`engine.play_hand` returns the ordered decisions, each carrying its seat, its readout,
its legal descriptors, the action applied and the reward the engine placed at that seat's
terminal decision (engine/surface.md §10, docs/L3/engine/episode.md §3). This module
turns the decisions **of the learner's own seat**, in decision order, into transitions:

- the successor of a decision is the learner's next decision in that hand, not the
  opponent's, because the update is over the learner's own state-action pairs;
- the terminal decision is the learner's last one, and it carries the seat's net chip
  delta and its own mask, having no successor to read (`records.md` §4, ASM-12);
- the batch is the caller's order and is neither sampled nor shuffled, which is what lets
  two arms of a pair declare one sample order (agents/surface.md §7, ladder.md §4, ASM-7).
"""

import features

from . import errors


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


def _transitions(episode, seat, encoder):
    """The learner's transitions for one hand, in decision order (records.md §4).

    `reward` is the decision's own: the episode places `0.0` at every decision and that
    seat's net chip delta at its terminal one (`records.md` §5, ASM-12), so this module
    computes no reward and adds no shaping term. `terminal` is **positional** — the last
    decision the seat made — and never inferred from the reward, because a split pot pays
    nothing and a zero-reward terminal decision is normal (`docs/L3/training/episode.md`
    §4). A hand in which the seat never acted yields `[]`: no update, and no empty batch
    handed to `agents.learn`.
    """
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
        else:
            successor = own[position + 1]
            next_observation = features.encode(encoder, successor["readout"])
            next_legal = list(features.legal_indices(successor["legal"]))
        records.append(
            {
                "observation": observation,
                "next_observation": next_observation,
                "action": _index(decision["legal"], decision["action"]),
                "reward": float(decision["reward"]),
                "terminal": terminal,
                "legal": legal,
                "next_legal": next_legal,
            }
        )
    return records
