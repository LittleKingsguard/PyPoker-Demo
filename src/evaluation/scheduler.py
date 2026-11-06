"""The scheduler: one cell at a time (`docs/L3/evaluation/scheduler.md` §1-§4).

A cell is one unordered pair of members, played at one hand count and reported in both
directions (`league.md` §2).  The i-th hand is dealt at a seed derived from the cell's
seed and the index alone, so one pair, one hand count and one seed give one cell however
much was played before it.  Seats alternate hand by hand, and a cell costs its hand count
and not twice it: the two directions are the same hands seen from each seat.

Two cells are never interleaved and none runs concurrently -- one global `random` stream
deals every hand and `engine.new_hand` is its single seeding point (ASM-2, D-16).
"""

import engine

from .errors import InvalidHandCount, InvalidSeed, SameMemberPair
from .policy import _is_int, _side
from .seeds import _hand_seed


def match(left, right, hands, seed):
    """One `records.md` §9 cell: two policies or two members, a hand count and a seed.

    Its `members` are the two ids in argument order, its `directions` are position-aligned
    with them, and its `params` carries one integer per member with the unmeasured zeros
    named in `unlabelled` (`surface.md` §9, `scheduler.md` §4-§5).
    """
    if not _is_int(hands) or int(hands) < 1:
        raise InvalidHandCount(
            "match(hands): the hand count must be a positive integer, got %r" % (hands,)
        )
    if not _is_int(seed):
        raise InvalidSeed("match(seed): the seed must be an integer, got %r" % (seed,))
    left_side = _side(left, "left", "match", seed=seed, position=1)
    right_side = _side(right, "right", "match", seed=seed, position=2)
    if left_side[0] == right_side[0]:
        raise SameMemberPair(
            "match(left, right): the two sides carry one id %r, and a cell pairs two "
            "distinct members" % (left_side[0],)
        )
    return _play_cell(left_side, right_side, int(hands), int(seed))


def _play_cell(left, right, hands, seed):
    """One cell played hand after hand, from one seed, with the seats alternating.

    A hand's class is the sign of the member's own net chip delta -- positive is a win,
    negative a loss, zero a tie -- and the two means are exact negations because the hand
    was zero-sum and both are divided by the same `hands` (`scheduler.md` §4, G10).
    """
    left_id, left_policy, left_params, left_unlabelled = left
    right_id, right_policy, right_params, right_unlabelled = right

    left_wins = left_ties = left_losses = 0
    right_wins = right_ties = right_losses = 0
    left_total = right_total = 0
    left_seat0 = left_seat1 = right_seat0 = right_seat1 = 0

    for index in range(hands):
        hand_seed = _hand_seed(seed, index)
        if index % 2 == 0:
            episode = engine.play_hand(hand_seed, left_policy, right_policy)
            left_delta = episode["payoffs"][0]
            right_delta = episode["payoffs"][1]
            left_seat0 += 1
            right_seat1 += 1
        else:
            episode = engine.play_hand(hand_seed, right_policy, left_policy)
            left_delta = episode["payoffs"][1]
            right_delta = episode["payoffs"][0]
            left_seat1 += 1
            right_seat0 += 1

        left_total += left_delta
        right_total += right_delta
        if left_delta > 0:
            left_wins += 1
        elif left_delta < 0:
            left_losses += 1
        else:
            left_ties += 1
        if right_delta > 0:
            right_wins += 1
        elif right_delta < 0:
            right_losses += 1
        else:
            right_ties += 1

    unlabelled = tuple(
        member_id
        for member_id, flag in ((left_id, left_unlabelled), (right_id, right_unlabelled))
        if flag
    )
    return {
        "members": (left_id, right_id),
        "hands": hands,
        "directions": (
            {
                "wins": left_wins,
                "ties": left_ties,
                "losses": left_losses,
                "mean_chip_delta": left_total / hands,
                "seat_split": {"seat 0": left_seat0, "seat 1": left_seat1},
            },
            {
                "wins": right_wins,
                "ties": right_ties,
                "losses": right_losses,
                "mean_chip_delta": right_total / hands,
                "seat_split": {"seat 0": right_seat0, "seat 1": right_seat1},
            },
        ),
        "params": [int(left_params), int(right_params)],
        "seed": seed,
        "unlabelled": unlabelled,
    }
