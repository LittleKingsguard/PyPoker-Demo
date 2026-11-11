"""`engine` — the declared game shapes as RL environments (docs/L3/engine/README.md).

The package declares exactly the ten entry points of `docs/L2/engine/surface.md` §1
and nothing else public: `Hand`, the error classes, the card and action spellings,
the constants and every helper stay in the submodules (layout.md §2, G11).  Each
entry point is a thin wrapper, so the package's namespace cannot grow a second export
when an owner module gains a helper.
"""

from typing import TYPE_CHECKING as _TYPE_CHECKING

from . import actions as _actions
from . import config as _config
from . import episode as _episode
from . import equity as _equity
from . import hand as _hand
from . import readout as _readout

if _TYPE_CHECKING:  # a type name only; `Hand` is not a module-level name (G11)
    from .hand import Hand

__all__ = (
    "game_shapes",
    "game_config",
    "new_hand",
    "readout",
    "legal_actions",
    "apply_action",
    "is_terminal",
    "payoffs",
    "play_hand",
    "equity",
)


def game_shapes() -> dict:
    """The declared game shapes, default first, each as one row (surface.md §12)."""
    return _config.game_shapes()


def game_config(shape=None) -> dict:
    """The named shape's parameters as one mapping; no name is the default (surface.md §3)."""
    return _config.game_config(shape)


def new_hand(seed: int, shape=None) -> "Hand":
    """Deal one hand from `seed` on `shape`, the project's single seeding point (surface.md §4)."""
    return _hand.new_hand(seed, shape)


def readout(hand: "Hand") -> dict:
    """The acting seat's eleven facts at this decision (surface.md §5)."""
    return _readout.readout(hand)


def legal_actions(hand: "Hand") -> tuple[str, ...]:
    """The ordered descriptors the acting seat may choose, in its shape's order (surface.md §6)."""
    return _actions.legal_actions(hand)


def apply_action(hand: "Hand", action: str) -> "Hand":
    """The advanced hand, as a new handle (surface.md §7)."""
    return _actions.apply_action(hand, action)


def is_terminal(hand: "Hand") -> bool:
    """Whether the hand is over, as a boolean (surface.md §8)."""
    return _hand.is_terminal(hand)


def payoffs(hand: "Hand") -> dict[int, int]:
    """The net chip delta per engine seat of a completed hand (surface.md §9)."""
    return _hand.payoffs(hand)


def play_hand(seed: int, seat0_policy=None, seat1_policy=None, shape=None, seats=None) -> dict:
    """One whole hand driven by the policies, on `shape` (surface.md §10).

    The two positional policies are today's call; the optional `seats` sequence is the
    shape's whole seating, one policy per seat in seat order, and is the form a
    six-seat hand takes (seats.md §4).
    """
    return _episode.play_hand(seed, seat0_policy, seat1_policy, shape, seats)


def equity(decision: "Hand | dict", seed: int, samples: int) -> float:
    """The acting seat's share of the pot against uniform opponents (surface.md §11).

    Heads-up on a two-seat shape, and multi-way on a shape with more seats: a six-seat
    decision is asked against the other five seats' random hands (seats.md §2).
    """
    return _equity.equity(decision, seed, samples)
