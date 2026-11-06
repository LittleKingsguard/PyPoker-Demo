"""`play_hand`: one whole hand as a record (docs/L3/engine/episode.md).

The policy protocol is a callable taking `(readout, legal)` and returning one member
of `legal`; the engine knows no builder by name, does not inspect the policy, and
lets the policy's own exception propagate unchanged (episode.md §1, §4, G8).  One
hand is in flight and no re-entry: `play_hand` deals through `new_hand` and seeds
nothing itself (episode.md §2, D-16).
"""

from __future__ import annotations

from .actions import apply_action
from .errors import InvalidAction, InvalidPolicy
from .hand import is_terminal, new_hand, payoffs, validate_seed
from .readout import readout


def play_hand(seed: int, seat0_policy, seat1_policy) -> dict:
    """One episode: its seed, its decisions and the hand's payoffs (episode.md §3).

    Each decision is created with reward 0; at the end each seat's **last** decision
    takes that seat's net chip delta and every other decision stays 0, so a hand
    carries at most one non-zero reward per seat and it is the hand's outcome
    (episode.md §3, ASM-12, guardrails.md G9).
    """
    validate_seed(seed)
    for argument, policy in (
        ("seat0_policy", seat0_policy),
        ("seat1_policy", seat1_policy),
    ):
        if not callable(policy):
            raise InvalidPolicy(
                "play_hand(%s): the policy must be callable, got %s"
                % (argument, type(policy).__name__)
            )

    hand = new_hand(seed)
    decisions = []
    while not is_terminal(hand):
        facts = readout(hand)
        legal = facts["legal"]
        seat = facts["seat"][0]
        argument = "seat0_policy" if seat == 0 else "seat1_policy"
        policy = seat0_policy if seat == 0 else seat1_policy
        action = policy(facts, legal)
        if action not in legal:
            raise InvalidAction(
                "play_hand(%s): the policy returned %r, which is not legal at this decision"
                % (argument, action)
            )
        decisions.append(
            {
                "seat": facts["seat"],
                "readout": facts,
                "legal": legal,
                "action": action,
                "reward": 0,
            }
        )
        hand = apply_action(hand, action)

    outcome = payoffs(hand)
    last = {}
    for position, decision in enumerate(decisions):
        last[decision["seat"][0]] = position
    for seat, position in last.items():
        decisions[position]["reward"] = outcome[seat]
    return {"seed": seed, "decisions": decisions, "payoffs": outcome}
