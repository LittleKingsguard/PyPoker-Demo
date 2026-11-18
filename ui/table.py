"""Interactive table logic for the PyPoker demo UI.

This module is a demo tool that lives outside the six packaged modules under ``src/``.
It drives the project's public entry points -- ``engine.new_hand``, ``readout``,
``apply_action``, ``is_terminal`` and ``payoffs``, plus ``agents`` and ``evaluation``
for the league members -- one decision at a time, so a human can occupy one seat.

The shipped checkpoints are a heads-up fixed-limit set.  The research checkpoints in
``.probe`` are six-seat no-limit models, so the table carries the shape its opponent was
trained on instead of assuming the default shape.  Both roots are discovered; a probe
checkpoint is shown as a probe member and never silently replaces a shipped one.

Two facts the public readout deliberately hides are read from the hand handle here:

* every seat's hole cards, captured at the first decision.  ``pokerkit`` clears a
  mucking seat's cards when the hand ends, so they cannot be read afterwards
  (``src/engine/episode.py`` makes the same point);
* the current street bets, for display.

Nothing under ``src/`` is changed.  The UI is a viewer, not a seventh module.
"""

from __future__ import annotations

import importlib.util
import json
import os
import random
import sys
import threading
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import agents  # noqa: E402
import engine  # noqa: E402
import evaluation  # noqa: E402
from engine.hand import player_index  # noqa: E402
from pokerkit.hands import StandardHighHand  # noqa: E402
from pokerkit.utilities import Card  # noqa: E402

#: Every declared shape, default first.  A checkpoint is listed only if its metadata
#: names one of these.
SHAPES: dict[str, dict] = engine.game_shapes()

#: The shape the shipped league was trained on.
DEFAULT_SHAPE = next(
    (name for name, row in SHAPES.items() if row.get("default")),
    "fixed-limit-20",
)

#: The seat names of the two shapes the league actually lives on.  Engine seat 0 is
#: always the button; on the heads-up shape it also posts the small blind.
POSITION_NAMES = {
    2: ("Button · Small blind", "Big blind"),
    6: ("Button", "Small blind", "Big blind", "Under the gun", "Hijack", "Cutoff"),
}

#: Readable names for the fixed rules, kept here and not in ``agents``.
BASELINE_NAMES = {
    "random": "Random",
    "always-call": "Always call",
    "oracle": "Oracle",
    "fold-no-pair-or-face": "Fold no pair or face",
    "fold-no-pair-or-better": "Fold no pair or better",
    "fold-large-bet": "Fold large bet",
}

RAISE_NAMES = {
    "raise": "Raise",
    "raise-minimum": "Minimum raise",
    "raise-quarter": "Quarter-pot raise",
    "raise-half": "Half-pot raise",
    "raise-all-in": "All-in",
}


class UIError(Exception):
    """A refusal the HTTP layer can turn into a 400 with its own message."""


def _signed(number: int) -> str:
    return "%+d" % (int(number),)


def _clean_step(stem: str) -> str:
    """``final`` or ``step-0600`` as a short label, and anything else unchanged."""
    if stem == "final":
        return "final"
    if stem.startswith("step-") and stem[5:].isdigit():
        return "step %d" % (int(stem[5:]),)
    return stem


def _read_metadata(path: Path) -> dict:
    """The metadata.json of one checkpoint container, read without loading parameters."""
    with zipfile.ZipFile(path) as archive:
        return json.loads(archive.read("metadata.json").decode("utf-8"))


def _missing_artefact(metadata: dict) -> str | None:
    """A reason this checkpoint cannot load even with torch installed, or ``None``.

    Some probe checkpoints were trained from a frozen strength estimator rather than from a
    freshly fitted one.  Their metadata names the estimator, and the estimator's declared
    artefact lives outside the checkpoint.  When the artefact was never written the
    checkpoint is real but unloadable, so the drawer says so instead of offering a member
    that fails on the first decision.  This is a metadata-only check: it never imports
    torch and never reads parameters.
    """
    seeding = metadata.get("seeding")
    if not isinstance(seeding, dict):
        return None
    source = seeding.get("source")
    if not source:
        return None
    try:
        from features import cardmodel

        row = cardmodel.sources().get(str(source))
    except Exception:
        return None
    if row is None:
        return "This checkpoint names the strength source %r, which this build does not declare." % (
            source,
        )
    relative = str(row.get("path", ""))
    if relative and not (PROJECT_ROOT / relative).is_file():
        return (
            "This checkpoint was trained on the strength source %r, whose artefact %r "
            "is not present, so it cannot be loaded." % (source, relative)
        )
    return None


def shape_config(shape: str) -> dict:
    if shape not in SHAPES:
        raise UIError("Unknown game shape %r" % (shape,))
    return engine.game_config(shape)


def shape_label(shape: str | None) -> str:
    if not shape:
        return "Any shape"
    row = SHAPES.get(shape)
    if not row:
        return shape
    seats = int(row.get("seats", 2))
    structure = row.get("bet_structure", "fixed-limit")
    return "%d-seat %s" % (seats, "fixed-limit" if structure == "fixed-limit" else "no-limit")


def seat_positions(shape: str) -> tuple[str, ...]:
    row = SHAPES.get(shape)
    seats = int(row.get("seats", 2)) if row else 2
    names = POSITION_NAMES.get(seats)
    if names is not None:
        return names
    return tuple("Seat %d" % (seat + 1,) for seat in range(seats))


def position_name(seat: int, seats: int) -> str:
    names = POSITION_NAMES.get(seats)
    if names is not None and 0 <= seat < len(names):
        return names[seat]
    return "Seat %d" % (seat + 1,)


def _torch_available() -> bool:
    try:
        return importlib.util.find_spec("torch") is not None
    except Exception:
        return False


@dataclass
class Opponent:
    """One league member: a checkpoint or a fixed baseline policy."""

    id: str
    kind: str  # "model" or "baseline"
    name: str
    subtitle: str
    description: str
    params: int = 0
    path: str | None = None
    shape: str | None = None
    source: str = "shipped"  # "shipped", "probe" or "baseline"
    meta: dict[str, Any] = field(default_factory=dict)

    def public(self) -> dict[str, Any]:
        """The JSON-safe record the browser receives."""
        record: dict[str, Any] = {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "subtitle": self.subtitle,
            "description": self.description,
            "params": int(self.params),
            "shape": self.shape,
            "shape_label": shape_label(self.shape),
            "source": self.source,
            "short": self.short_name(),
        }
        record.update({key: value for key, value in self.meta.items() if value is not None})
        return record

    def short_name(self) -> str:
        if self.kind == "baseline":
            return self.name
        seed = self.meta.get("seed")
        step = self.meta.get("step") or "checkpoint"
        rung = self.meta.get("rung") or "Model"
        return "%s s%s %s" % (rung, "?" if seed is None else seed, step)


class Registry:
    """The league's members, discovered once and shared by every browser session."""

    def __init__(
        self,
        checkpoint_root: str | os.PathLike | None = None,
        probe_root: str | os.PathLike | None = None,
    ) -> None:
        shipped = (
            Path(checkpoint_root).expanduser().resolve()
            if checkpoint_root is not None
            else PROJECT_ROOT / "checkpoints"
        )
        probe = (
            Path(probe_root).expanduser().resolve()
            if probe_root is not None
            else PROJECT_ROOT / ".probe"
        )
        self.roots: list[tuple[Path, str]] = [(shipped, "shipped")]
        if probe != shipped and probe.is_dir():
            self.roots.append((probe, "probe"))
        self.torch_available = _torch_available()
        self._lock = threading.Lock()
        self._policies: dict[str, Callable] = {}
        self._baselines: list[Opponent] = self._discover_baselines()
        self._models: list[Opponent] = self._discover_models()
        self._by_id: dict[str, Opponent] = {
            opponent.id: opponent for opponent in (*self._models, *self._baselines)
        }

    # -- discovery ---------------------------------------------------------

    def _discover_baselines(self) -> list[Opponent]:
        rows = agents.baselines()
        found = []
        for name, record in rows.items():
            anchor = bool(record.get("anchor"))
            found.append(
                Opponent(
                    id="baseline:" + name,
                    kind="baseline",
                    name=BASELINE_NAMES.get(name, name),
                    subtitle="Fixed policy · any shape",
                    description=str(record.get("rule", "")),
                    params=0,
                    shape=None,
                    source="baseline",
                    meta={
                        "baseline": name,
                        "anchor": anchor,
                        "seed": None,
                        "step": None,
                        "rung": None,
                        "variant": None,
                        "group": "Deterministic policies",
                        "encoding": None,
                        "learning_rule": None,
                        "utility": None,
                        "backend": "policy",
                        "available": True,
                        "unavailable_reason": None,
                        "path": None,
                    },
                )
            )
        return found

    def _group_parts(self, relative: Path) -> list[str]:
        """A readable group name from a checkpoint path.

        ``checkpoints/R1/naive-numeric/seed-0/final.ckpt`` -> ``R1 · naive-numeric``;
        ``.probe/strength-strength-s2/.../card-tokens/seed-2/step-5000.ckpt`` ->
        ``strength-strength-s2 · card-tokens``.
        """
        parts = list(relative.parts[:-1])
        if parts and parts[-1].startswith("seed-"):
            parts.pop()
        unique: list[str] = []
        for part in parts:
            if part not in unique:
                unique.append(part)
        return unique

    def _discover_models(self) -> list[Opponent]:
        found: list[tuple[tuple, Opponent]] = []
        source_rank = {"shipped": 0, "probe": 1}
        for root, source in self.roots:
            if not root.is_dir():
                continue
            for path in sorted(root.rglob("*.ckpt")):
                try:
                    metadata = _read_metadata(path)
                except Exception:
                    continue
                if not isinstance(metadata, dict):
                    continue
                shape = metadata.get("game", DEFAULT_SHAPE)
                if shape not in SHAPES:
                    continue
                try:
                    relative = path.relative_to(root)
                except ValueError:
                    relative = path
                group_parts = self._group_parts(relative)
                group = " · ".join(group_parts) if group_parts else path.parent.name
                rung = group_parts[0] if group_parts else "Checkpoint"
                variant = group_parts[-1] if len(group_parts) > 1 else path.parent.name

                seed = metadata.get("seed")
                if seed is None:
                    for part in relative.parts:
                        if part.startswith("seed-"):
                            try:
                                seed = int(part[5:])
                            except ValueError:
                                seed = None
                            break
                representation = metadata.get("representation", {})
                params = int(metadata.get("params", {}).get("count", 0))
                stem = path.stem
                step = _clean_step(stem)
                backend = str(metadata.get("backend", "numpy"))
                available = backend != "torch" or self.torch_available
                reason = None
                if not available:
                    reason = "This is a PyTorch checkpoint, and torch is not installed."
                else:
                    reason = _missing_artefact(metadata)
                    available = reason is None
                subtitle = " · ".join(
                    part
                    for part in (
                        "seed %d" % (seed,) if isinstance(seed, int) else "seed ?",
                        step,
                        "%s params" % (format(params, ","),),
                    )
                    if part
                )
                description = " · ".join(
                    part
                    for part in (
                        str(metadata.get("kind", "checkpoint")),
                        str(representation.get("encoding", "")),
                        str(metadata.get("learning_rule", "masked-q-learning")),
                        str(metadata.get("utility", "net-chips")),
                    )
                    if part
                )
                if path.is_relative_to(PROJECT_ROOT):
                    member_id = "ckpt:" + path.relative_to(PROJECT_ROOT).as_posix()
                else:
                    member_id = "ckpt:" + path.as_posix()
                opponent = Opponent(
                    id=member_id,
                    kind="model",
                    name=group,
                    subtitle=subtitle,
                    description=description,
                    params=params,
                    path=str(path),
                    shape=shape,
                    source=source,
                    meta={
                        "seed": seed,
                        "step": step,
                        "rung": rung,
                        "variant": variant,
                        "group": group,
                        "encoding": representation.get("encoding"),
                        "learning_rule": metadata.get("learning_rule", "masked-q-learning"),
                        "utility": metadata.get("utility", "net-chips"),
                        "format_version": metadata.get("format_version"),
                        "backend": backend,
                        "available": available,
                        "unavailable_reason": reason,
                        "source_label": "Shipped" if source == "shipped" else "Probe",
                        "path": opponent_path(path),
                    },
                )
                step_number = (
                    10**9
                    if stem == "final"
                    else (
                        int(stem[5:])
                        if stem.startswith("step-") and stem[5:].isdigit()
                        else 0
                    )
                )
                found.append(
                    (
                        (
                            source_rank.get(source, 2),
                            0 if available else 1,
                            group,
                            seed if isinstance(seed, int) else -1,
                            step_number,
                        ),
                        opponent,
                    )
                )
        found.sort(key=lambda pair: pair[0])
        return [opponent for _key, opponent in found]

    # -- read-back ---------------------------------------------------------

    def opponents(self) -> dict[str, Any]:
        shapes = {}
        for name, row in SHAPES.items():
            shapes[name] = {
                **row,
                "label": shape_label(name),
                "positions": list(seat_positions(name)),
            }
        return {
            "models": [opponent.public() for opponent in self._models],
            "baselines": [opponent.public() for opponent in self._baselines],
            "shapes": shapes,
            "default_shape": DEFAULT_SHAPE,
            "featured": self._featured(),
            "roots": [{"path": str(root), "source": source} for root, source in self.roots],
            "torch_available": self.torch_available,
        }

    def _featured(self) -> list[str]:
        """A small, stable set of playable starters for the welcome drawer."""
        featured: list[str] = []

        def add(member_id: str | None) -> None:
            if not member_id or member_id in featured:
                return
            opponent = self._by_id.get(member_id)
            if opponent is not None and opponent.meta.get("available", True):
                featured.append(member_id)

        add("ckpt:checkpoints/R1/naive-numeric/seed-0/final.ckpt")
        probe_groups = (
            "strength-control-s2 · card-tokens",
            "strength-control-s1 · card-tokens",
            "strength-control-s0 · card-tokens",
            "naive · naive6 · card-tokens",
            "dead · dead-ckpt · card-tokens",
            "ckpt · wire-sup-emb · card-tokens",
        )
        add(
            next(
                (
                    member.id
                    for group in probe_groups
                    for member in self._models
                    if member.meta.get("group") == group
                    and member.meta.get("step") == "final"
                    and member.meta.get("available", True)
                ),
                None,
            )
        )
        add("baseline:oracle")
        add("baseline:always-call")
        for member in self._models:
            if len(featured) >= 4:
                break
            add(member.id)
        for member in self._baselines:
            if len(featured) >= 4:
                break
            add(member.id)
        return featured[:4]

    def get(self, opponent_id: str) -> Opponent:
        try:
            return self._by_id[opponent_id]
        except KeyError:
            raise UIError("Unknown opponent %r" % (opponent_id,)) from None

    # -- policies ----------------------------------------------------------

    def policy_for(self, opponent: Opponent, seed: int, shape: str) -> Callable:
        """One opponent as a callable ``(readout, legal) -> descriptor``.

        A baseline is built for this hand's seed and table shape, because ``random``,
        ``oracle`` and ``fold-large-bet`` key on one or both.  A model is built once
        with exploration **off**, so it plays the masked maximum and not its old
        exploration schedule; the resulting policy is stateless and can be shared.
        """
        if opponent.kind == "baseline":
            name = opponent.meta["baseline"]
            return agents.build_baseline(name, int(seed), shape)

        if opponent.shape != shape:
            raise UIError(
                "%s is a %s checkpoint and cannot play a %s table"
                % (opponent.name, shape_label(opponent.shape), shape_label(shape))
            )
        if not opponent.meta.get("available", True):
            raise UIError(
                "%s cannot be loaded: %s"
                % (opponent.name, opponent.meta.get("unavailable_reason") or "unknown reason")
            )

        with self._lock:
            cached = self._policies.get(opponent.id)
        if cached is not None:
            return cached
        if not opponent.path:
            raise UIError("The opponent %r has no checkpoint path" % (opponent.name,))
        try:
            policy = evaluation.policy_from(opponent.path, exploration="off")
        except Exception as error:
            # A checkpoint can pass the metadata-only checks and still fail to load (a
            # missing external artefact, a layout mismatch).  Record the real reason so
            # the drawer stops offering it after one attempt.
            opponent.meta["available"] = False
            opponent.meta["unavailable_reason"] = str(error)
            raise UIError("Could not load %s: %s" % (opponent.name, error)) from error
        with self._lock:
            self._policies[opponent.id] = policy
        return policy

    def mixed_lineup(
        self,
        shape: str,
        seed: int,
        count: int,
        anchor: Opponent | None = None,
    ) -> list[Opponent]:
        """A deterministic, seed-keyed mix of the league for a multi-seat table.

        The selected member is kept at one seat, then one or two fast deterministic
        policies join, then the rest is filled from the models trained on this shape.
        ``oracle`` is deliberately not sampled here: it samples equity at every
        decision, and five of it would make the demo crawl.  It remains playable on
        its own.
        """
        rng = random.Random(int(seed))
        chosen: list[Opponent] = []
        if anchor is not None:
            chosen.append(anchor)

        baselines = [
            member
            for member in self._baselines
            if member.meta.get("baseline") != "oracle"
        ]
        rng.shuffle(baselines)
        baseline_target = min(len(baselines), max(1, count // 3))
        for member in baselines:
            if len(chosen) >= count or baseline_target <= 0:
                break
            if member.id not in {row.id for row in chosen}:
                chosen.append(member)
                baseline_target -= 1

        models = [
            member
            for member in self._models
            if member.shape == shape and member.meta.get("available", True)
        ]
        rng.shuffle(models)
        for member in models:
            if len(chosen) >= count:
                break
            if member.id not in {row.id for row in chosen}:
                chosen.append(member)

        # A tree without torch has no playable probe models.  Fill the remaining seats
        # with the deterministic policies rather than repeating the anchor; only repeat a
        # member when the league is smaller than the table.
        if len(chosen) < count:
            spare = [
                member
                for member in self._baselines
                if member.meta.get("baseline") != "oracle"
                and member.id not in {row.id for row in chosen}
            ]
            rng.shuffle(spare)
            for member in spare:
                if len(chosen) >= count:
                    break
                chosen.append(member)

        fallback = anchor or (self._baselines[0] if self._baselines else None)
        while len(chosen) < count and fallback is not None:
            chosen.append(fallback)
        return chosen[:count]


def opponent_path(path: Path) -> str:
    """A short path for display, relative to the repository when it lives inside it."""
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


class HandPlay:
    """One hand, one decision at a time, with the human on a fixed seat."""

    def __init__(
        self,
        match: "Match",
        seed: int,
        policies: dict[int, Callable],
    ) -> None:
        self.match = match
        self.seed = int(seed)
        self.policies = policies
        self.human_seat = match.human_seat
        self.seats = match.seats
        self.hand = engine.new_hand(self.seed, match.shape)
        self.holes = self._capture_holes()
        self.history: list[dict[str, Any]] = []
        self.folded: set[int] = set()
        self.over = False
        self.result: dict[str, Any] | None = None
        self.pending: dict[str, Any] | None = None
        self.last_pot = 0
        self.final_board: tuple[str, ...] = ()
        self.final_stacks: dict[int, int] = {}
        self._advance()

    # -- reading the deal --------------------------------------------------

    def _capture_holes(self) -> dict[int, tuple[str, ...]]:
        """Every seat's two cards, read once at the first decision.

        The public readout only carries the acting seat's hole cards, and a finished
        hand may have cleared the mucker's.  The UI needs the other seats for a
        showdown, so this is the one place it reaches into the handle.
        """
        state = self.hand._state
        return {
            seat: tuple(
                repr(card) for card in state.hole_cards[player_index(seat, self.seats)]
            )
            for seat in range(self.seats)
        }

    def _bets(self) -> list[int]:
        state = self.hand._state
        return [
            int(state.bets[player_index(seat, self.seats)]) for seat in range(self.seats)
        ]

    @staticmethod
    def _seat_of(facts: dict[str, Any]) -> int:
        seat = facts["seat"]
        if isinstance(seat, (tuple, list)):
            return int(seat[0])
        return int(seat)

    @staticmethod
    def _rank(hole: tuple[str, ...], board: tuple[str, ...]) -> str | None:
        if len(board) < 5 or len(hole) < 2:
            return None
        best = StandardHighHand.from_game_or_none(
            [Card(card[0], card[1]) for card in hole],
            [Card(card[0], card[1]) for card in board],
        )
        if best is None:
            return None
        return best.entry.label.value

    # -- names -------------------------------------------------------------

    def _member(self, seat: int) -> Opponent | None:
        return self.match.members.get(seat)

    def _short_name(self, seat: int) -> str:
        if seat == self.human_seat:
            return "You"
        member = self._member(seat)
        return member.short_name() if member is not None else "Seat %d" % (seat + 1,)

    def _display_name(self, seat: int) -> str:
        if seat == self.human_seat:
            return "You"
        member = self._member(seat)
        return member.name if member is not None else "Seat %d" % (seat + 1,)

    def _name_list(self, seats: list[int]) -> str:
        names = [self._display_name(seat) for seat in seats]
        if len(names) <= 2:
            return " and ".join(names)
        return ", ".join(names[:-1]) + " and " + names[-1]

    # -- decisions ---------------------------------------------------------

    def _action_label(
        self,
        action: str,
        facts: dict[str, Any],
        amount: int | None,
    ) -> str:
        if action == "fold":
            return "Fold"
        if action == "check-call":
            return (
                "Check"
                if int(facts["to_call"]) == 0
                else "Call %d" % (int(facts["to_call"]),)
            )
        if amount is None:
            return RAISE_NAMES.get(action, action.replace("-", " ").title())
        if action == "raise-all-in":
            return "All-in %d" % (amount,)
        if action == "raise-minimum":
            return "Min raise to %d" % (amount,)
        return "Raise to %d" % (amount,)

    def _contribution(
        self,
        facts: dict[str, Any],
        action: str,
        amount: int | None,
    ) -> int:
        if action == "fold":
            return 0
        if action == "check-call":
            return int(facts["to_call"])
        if amount is None:
            raise UIError("The raise %r resolved to no amount" % (action,))
        seat = self._seat_of(facts)
        own = int(self.hand._state.bets[player_index(seat, self.seats)])
        return int(amount) - own

    def _apply(
        self,
        seat: int,
        action: str,
        facts: dict[str, Any],
    ) -> None:
        legal = tuple(facts["legal"])
        if action not in legal:
            raise UIError(
                "The policy chose %r, which is not legal at this decision (%r)"
                % (action, legal)
            )
        amount = None
        if action not in ("fold", "check-call"):
            amount = engine.actions.raise_amount(self.hand, action)
        pot_after = int(facts["pot"]) + self._contribution(facts, action, amount)
        self.history.append(
            {
                "seat": seat,
                "name": self._display_name(seat),
                "short": self._short_name(seat),
                "street": facts["street"],
                "action": action,
                "amount": amount,
                "label": self._action_label(action, facts, amount),
                "pot": pot_after,
            }
        )
        if action == "fold":
            self.folded.add(seat)
        self.hand = engine.apply_action(self.hand, action)
        self.last_pot = pot_after
        if engine.is_terminal(self.hand):
            self._finish()

    def _advance(self) -> None:
        """Let the models act until it is the human's turn, or the hand ends."""
        while not self.over:
            if engine.is_terminal(self.hand):
                self._finish()
                return
            facts = engine.readout(self.hand)
            seat = self._seat_of(facts)
            if seat == self.human_seat:
                self.pending = facts
                self.last_pot = int(facts["pot"])
                return
            policy = self.policies.get(seat)
            if policy is None:
                raise UIError("No policy is seated at seat %d" % (seat + 1,))
            try:
                action = policy(facts, facts["legal"])
            except UIError:
                raise
            except Exception as error:
                raise UIError(
                    "%s could not decide: %s" % (self._short_name(seat), error)
                ) from error
            if action not in facts["legal"]:
                raise UIError(
                    "%s returned %r, which is not legal (%r)"
                    % (self._short_name(seat), action, facts["legal"])
                )
            self._apply(seat, action, facts)

    # -- end of hand -------------------------------------------------------

    def _finish(self) -> None:
        if self.over:
            return
        self.over = True
        self.pending = None
        payoffs = {
            int(seat): int(value) for seat, value in engine.payoffs(self.hand).items()
        }
        self.final_board = tuple(
            repr(card) for card in self.hand._state.get_board_cards(0)
        )
        starting_stacks = list(self.match.config["starting_stacks"])
        self.final_stacks = {
            seat: int(starting_stacks[seat]) + payoffs[seat] for seat in range(self.seats)
        }
        live = [seat for seat in range(self.seats) if seat not in self.folded]
        showdown = len(self.final_board) == 5 and len(live) >= 2
        ranks: dict[int, str] = {}
        revealed: dict[int, tuple[str, ...] | None] = {
            seat: None for seat in range(self.seats)
        }
        revealed[self.human_seat] = self.holes[self.human_seat]
        if showdown:
            for seat in live:
                rank = self._rank(self.holes[seat], self.final_board)
                if rank is not None:
                    ranks[seat] = rank
                revealed[seat] = self.holes[seat]

        human_delta = payoffs[self.human_seat]
        opponents_delta = sum(
            payoffs[seat] for seat in range(self.seats) if seat != self.human_seat
        )
        winners = [seat for seat in range(self.seats) if payoffs[seat] > 0]
        won_total = sum(payoffs[seat] for seat in winners)
        if human_delta > 0:
            message = "You win %d chip%s." % (
                human_delta,
                "" if human_delta == 1 else "s",
            )
            if showdown and self.human_seat in ranks:
                message += " %s." % (ranks[self.human_seat],)
            else:
                message += " The rest of the table folded."
        elif human_delta < 0:
            if len(winners) == 1:
                message = "%s wins %d chip%s. You lose %d." % (
                    self._display_name(winners[0]),
                    won_total,
                    "" if won_total == 1 else "s",
                    -human_delta,
                )
                if showdown and winners[0] in ranks:
                    message += " %s." % (ranks[winners[0]],)
            elif winners:
                message = "%s split the %d-chip pot. You lose %d." % (
                    self._name_list(winners),
                    won_total,
                    -human_delta,
                )
            else:
                message = "You lose %d chip%s." % (
                    -human_delta,
                    "" if -human_delta == 1 else "s",
                )
        elif showdown and len(winners) > 1:
            message = "Split pot."
            if self.human_seat in ranks:
                message += " Your %s takes a share." % (ranks[self.human_seat],)
        else:
            message = "You break even."

        street = self.history[-1]["street"] if self.history else "preflop"
        self.result = {
            "winner": "human" if human_delta > 0 else "opponents" if human_delta < 0 else "split",
            "showdown": bool(showdown),
            "board": self.final_board,
            "street": street,
            "pot": self.last_pot,
            "human_delta": human_delta,
            "opponents_delta": opponents_delta,
            "deltas": {seat: payoffs[seat] for seat in range(self.seats)},
            "final_stacks": {
                seat: self.final_stacks[seat] for seat in range(self.seats)
            },
            "holes": {
                seat: revealed[seat] for seat in range(self.seats)
            },
            "ranks": {seat: ranks[seat] for seat in ranks},
            "winners": winners,
            "message": message,
            "folded": sorted(self.folded),
            "label": self.match.label,
        }
        self.match._record_result(self)

    # -- human input -------------------------------------------------------

    def act(self, action: str) -> None:
        if self.over:
            raise UIError("This hand is over; start the next one")
        if self.pending is None:
            raise UIError("The hand is not waiting for your action")
        facts = self.pending
        if self._seat_of(facts) != self.human_seat:
            raise UIError("It is not your turn")
        self.pending = None
        self._apply(self.human_seat, action, facts)
        if not self.over:
            self._advance()

    # -- read-back ---------------------------------------------------------

    def _legal_payload(self, facts: dict[str, Any]) -> list[dict[str, Any]]:
        rows = []
        for action in facts["legal"]:
            amount = None
            if action not in ("fold", "check-call"):
                amount = engine.actions.raise_amount(self.hand, action)
            rows.append(
                {
                    "action": action,
                    "label": self._action_label(action, facts, amount),
                    "kind": (
                        "fold"
                        if action == "fold"
                        else "check"
                        if action == "check-call"
                        else "raise"
                    ),
                    "amount": amount,
                    "detail": {
                        "raise-quarter": "¼ pot",
                        "raise-half": "½ pot",
                        "raise-minimum": "minimum",
                        "raise-all-in": "all-in",
                    }.get(action),
                }
            )
        return rows

    @staticmethod
    def _last_action(history: list[dict[str, Any]], seat: int) -> dict | None:
        for entry in reversed(history):
            if entry["seat"] == seat:
                return entry
        return None

    def _hint(self) -> str:
        if self.over and self.result:
            return self.result["message"]
        facts = self.pending
        if facts is None:
            return "Waiting for the table."
        to_call = int(facts["to_call"])
        if to_call > 0:
            return "You are facing %d. Call, raise, or fold." % (to_call,)
        return "Checked to you. Check or bet."

    def _seat_state(
        self,
        seat: int,
        actor: int | None,
        stacks: list[int],
        bets: list[int],
        over: bool,
        result: dict[str, Any] | None,
    ) -> dict[str, Any]:
        member = self._member(seat)
        is_human = seat == self.human_seat
        if over and result is not None:
            hole = result["holes"].get(seat)
            delta = int(result["deltas"].get(seat, 0))
            rank = result["ranks"].get(seat)
            folded = seat in self.folded
        else:
            hole = self.holes[seat] if is_human else None
            delta = None
            rank = None
            folded = seat in self.folded
        return {
            "seat": seat,
            "position": position_name(seat, self.seats),
            "name": "You" if is_human else (member.name if member else "Seat %d" % (seat + 1,)),
            "short": self._short_name(seat),
            "kind": "human" if is_human else ("model" if member and member.kind == "model" else "baseline"),
            "is_human": bool(is_human),
            "is_button": seat == 0,
            "hole": list(hole) if hole else None,
            "stack": int(stacks[seat]),
            "bet": int(bets[seat]),
            "last_action": self._last_action(self.history, seat),
            "turn": bool(not over and actor == seat),
            "folded": bool(folded),
            "rank": rank,
            "delta": delta,
            "winner": bool(delta is not None and delta > 0),
        }

    def state(self) -> dict[str, Any]:
        over = self.over
        result = self.result or {}
        if over:
            board = list(result.get("board", ()))
            street = result.get("street", "preflop")
            pot = int(result.get("pot", 0))
            to_call = 0
            stacks = [
                int(result.get("final_stacks", {}).get(seat, 0))
                for seat in range(self.seats)
            ]
            bets = [0] * self.seats
            legal: list[dict[str, Any]] = []
            actor = None
            phase = "hand_over"
        else:
            facts = self.pending
            if facts is None:
                raise UIError("No decision is pending")
            board = list(facts["board"])
            street = facts["street"]
            pot = int(facts["pot"])
            to_call = int(facts["to_call"])
            stacks = [int(value) for value in facts["stacks"]]
            bets = self._bets()
            legal = (
                self._legal_payload(facts)
                if self._seat_of(facts) == self.human_seat
                else []
            )
            actor = self._seat_of(facts)
            phase = "your_turn" if actor == self.human_seat else "opponent_turn"

        seats = [
            self._seat_state(seat, actor, stacks, bets, over, result if over else None)
            for seat in range(self.seats)
        ]
        human = seats[self.human_seat]
        settled = sum(self.match.record.values())

        return {
            "seed": self.seed,
            "hand_number": self.match.hands_started,
            "shape": self.match.shape,
            "shape_label": shape_label(self.match.shape),
            "seats_count": self.seats,
            "street": street,
            "board": board,
            "pot": pot,
            "to_call": to_call,
            "phase": phase,
            "human": human,
            "seats": seats,
            "legal": legal,
            "history": list(self.history),
            "hint": self._hint(),
            "over": bool(over),
            "result": result if over else None,
            "match": {
                "score": dict(self.match.score),
                "record": dict(self.match.record),
                "hands_started": self.match.hands_started,
                "hands_finished": settled,
                "label": self.match.label,
                "lineup_mode": self.match.lineup_mode,
            },
        }


class Match:
    """One human against one league member or a mixed table, across hands."""

    def __init__(
        self,
        registry: Registry,
        opponent: Opponent,
        human_seat: int = 0,
        seed: int | None = None,
        shape: str | None = None,
        members: dict[int, Opponent] | None = None,
        lineup_mode: str = "same",
    ) -> None:
        if shape is None:
            shape = opponent.shape or DEFAULT_SHAPE
        config = shape_config(shape)
        seats = int(config["seats"])
        if human_seat not in range(seats):
            raise UIError("The seat must be between 0 and %d for this table" % (seats - 1,))
        if seed is None:
            seed = random.SystemRandom().randrange(1, 2**31)
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise UIError("The seed must be an integer")
        if lineup_mode not in ("same", "mixed"):
            raise UIError("The lineup mode must be 'same' or 'mixed'")
        if seats <= 2:
            lineup_mode = "same"

        self.registry = registry
        self.opponent = opponent
        self.shape = shape
        self.config = config
        self.seats = seats
        if opponent.kind == "model" and opponent.shape != shape:
            raise UIError(
                "%s is a %s checkpoint and cannot sit at a %s table"
                % (opponent.name, shape_label(opponent.shape), shape_label(shape))
            )
        self.human_seat = int(human_seat)
        self.seed = int(seed)
        self.lineup_mode = lineup_mode
        self.members: dict[int, Opponent] = dict(members or {})
        if not self.members:
            self.members = {
                seat: opponent for seat in range(seats) if seat != self.human_seat
            }
        else:
            for seat in range(seats):
                if seat != self.human_seat and seat not in self.members:
                    self.members[seat] = opponent
        for seat, member in self.members.items():
            if not 0 <= seat < seats or seat == self.human_seat:
                raise UIError("The lineup names an invalid seat")
            if member.kind == "model" and member.shape != shape:
                raise UIError(
                    "%s is a %s checkpoint and cannot sit at a %s table"
                    % (member.name, shape_label(member.shape), shape_label(shape))
                )
        self.label = "League mix" if lineup_mode == "mixed" else opponent.name
        self.hands_started = 0
        self.score = {"human": 0, "opponents": 0}
        self.record = {"wins": 0, "losses": 0, "ties": 0}
        self.hand: HandPlay | None = None
        self._new_hand()

    def _new_hand(self) -> None:
        seed = self.seed + self.hands_started
        policies = {
            seat: self.registry.policy_for(member, seed, self.shape)
            for seat, member in self.members.items()
        }
        self.hands_started += 1
        self.hand = HandPlay(self, seed, policies)

    def _record_result(self, play: HandPlay) -> None:
        assert play.result is not None
        delta = int(play.result["human_delta"])
        self.score["human"] += delta
        self.score["opponents"] -= delta
        if delta > 0:
            self.record["wins"] += 1
        elif delta < 0:
            self.record["losses"] += 1
        else:
            self.record["ties"] += 1

    def act(self, action: str) -> dict[str, Any]:
        if self.hand is None:
            raise UIError("No hand is in play")
        self.hand.act(str(action))
        return self.state()

    def next_hand(self) -> dict[str, Any]:
        if self.hand is not None and not self.hand.over:
            raise UIError("Finish the hand before dealing the next one")
        self._new_hand()
        return self.state()

    def state(self) -> dict[str, Any]:
        if self.hand is None:
            raise UIError("No hand is in play")
        opponents = [
            {
                "seat": seat,
                "position": position_name(seat, self.seats),
                **member.public(),
            }
            for seat, member in sorted(self.members.items())
        ]
        return {
            "match": {
                "seed": self.seed,
                "shape": self.shape,
                "shape_label": shape_label(self.shape),
                "seats": self.seats,
                "human_seat": self.human_seat,
                "human_position": position_name(self.human_seat, self.seats),
                "hands_started": self.hands_started,
                "score": dict(self.score),
                "record": dict(self.record),
                "label": self.label,
                "lineup_mode": self.lineup_mode,
                "opponent": self.opponent.public(),
                "opponents": opponents,
                "config": {
                    "blinds": list(self.config.get("blinds", ())),
                    "starting_stack": self.config.get("starting_stack"),
                    "bet_structure": self.config.get("bet_structure"),
                    "small_bet": self.config.get("small_bet"),
                    "big_bet": self.config.get("big_bet"),
                    "raise_cap": self.config.get("raise_cap"),
                },
            },
            "hand": self.hand.state(),
            "game": self.config,
        }


def parse_seed(value: Any) -> int | None:
    """An optional seed from JSON, or ``None`` for a fresh random one."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise UIError("The seed must be an integer")
    if isinstance(value, int):
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    raise UIError("The seed must be an integer")
