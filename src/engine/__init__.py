"""`engine` — the fixed game of D-2 as an RL environment (docs/L3/engine/README.md).

The package declares exactly the nine entry points of `docs/L2/engine/surface.md` §1
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


def game_config() -> dict:
    """The fixed game's parameters as one mapping (surface.md §3)."""
    return _config.game_config()


def new_hand(seed: int) -> "Hand":
    """Deal one hand from `seed`, the project's single seeding point (surface.md §4)."""
    return _hand.new_hand(seed)


def readout(hand: "Hand") -> dict:
    """The acting seat's ten facts at this decision (surface.md §5)."""
    return _readout.readout(hand)


def legal_actions(hand: "Hand") -> tuple[str, ...]:
    """The ordered descriptors the acting seat may choose (surface.md §6)."""
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


def play_hand(seed: int, seat0_policy, seat1_policy) -> dict:
    """One whole hand driven by the two policies (surface.md §10)."""
    return _episode.play_hand(seed, seat0_policy, seat1_policy)


def equity(decision: "Hand | dict", seed: int, samples: int) -> float:
    """The acting seat's share of the pot against a uniform opponent (surface.md §11)."""
    return _equity.equity(decision, seed, samples)
