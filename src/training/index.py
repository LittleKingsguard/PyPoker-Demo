"""The shipped checkpoint index — declared data over `checkpoints/`, never a scan.

What ships is the retained window of each rung plus each rung variant's final model per
seed (protocol.md §5, ASM-5 as D-16 amends it, ASM-18). This module states that set as
`SHIPPED` — tuples of `(rung, variant, seed, step)` — and derives every path with the one
naming function a run writes with (`layout.py`), so the index cannot drift from the
directory and a scratch file the battery wrote is never a shipped artefact
(protocol.md §5, FAM-12, FAM-16.31).

Each artefact appears **once**: the index is one ordered `entries` list, and no path is
named twice anywhere in the record (FAM-12.6). A rung whose run does not exist yet
contributes no entry at all, because the index is not filtered to what happens to be on
disk and it never invents a path it cannot point at (protocol.md §5).
"""

from . import declarations, layout

#: The one rung whose live run ships today: `R1` at the live budget, three seeds.
SHIPPED = {"R1": "naive-numeric"}

#: Which rung inherits each rung's retained window (ladder.md §2, ASM-16).
SUCCESSOR = {"R1": "R2", "R2": "R3", "R3": "R4", "R4": "R5", "R5": "R6", "R6": None}

#: The live run's snapshot interval and the steps its window retains (ASM-18).
INTERVAL = declarations.LIVE_BUDGET // declarations.SNAPSHOTS
RETAINED_STEPS = tuple(
    INTERVAL * (declarations.SNAPSHOTS - declarations.RETAINED + 1 + offset)
    for offset in range(declarations.RETAINED)
)

#: The final models that ship: one per rung variant per seed of a run that exists.
SHIPPED_FINALS = tuple(
    (rung, variant, seed) for rung, variant in SHIPPED.items() for seed in declarations.SEEDS
)

#: The retained window that ships, in lineage order, keyed by the **primary variant** whose
#: snapshots it is — that is the name a successor rung's `carried_from` gives it. The seeds'
#: windows lie end to end in the recorded seed set's order, so a rung's retained versions are
#: one chain (docs/L2/training/loop.md §7, records.md §7, registry.md §3).
SHIPPED_WINDOWS = {
    variant: tuple(
        (rung, variant, seed, step)
        for seed in declarations.SEEDS
        for step in RETAINED_STEPS
    )
    for rung, variant in SHIPPED.items()
}


def _snapshot_entry(rung, variant, seed, step, lineage):
    """One retained snapshot as a `records.md` §7 version record."""
    return {
        "id": layout._version_id(rung, variant, seed, step),
        "path": layout._snapshot_path(rung, variant, seed, step),
        "rung": rung,
        "variant": variant,
        "seed": int(seed),
        "step": int(step),
        "samples": int(step),
        "lineage": lineage,
        "kind": "snapshot",
    }


def _final_entry(rung, variant, seed):
    """One variant × seed final model, descending from that pair's last snapshot."""
    return {
        "id": layout._final_id(rung, variant, seed),
        "path": layout._final_path(rung, variant, seed),
        "rung": rung,
        "variant": variant,
        "seed": int(seed),
        "step": int(declarations.LIVE_BUDGET),
        "samples": int(declarations.LIVE_BUDGET),
        "lineage": layout._version_id(rung, variant, seed, declarations.LIVE_BUDGET),
        "kind": "final",
    }


def _window_members(variant):
    """One primary variant's retained window, as the version records its successor inherits."""
    members = []
    previous = "%s-start" % (variant,)
    for owner, produced_by, seed, step in SHIPPED_WINDOWS.get(variant, ()):
        member = _snapshot_entry(owner, produced_by, seed, step, previous)
        members.append(member)
        previous = member["id"]
    return members


def _entries():
    """Every shipped artefact, once each, in the declared order.

    The order is the declaration's and never a directory listing: rung in brief §2's
    order, variant in the registry's order, seed ascending, step ascending, and that pair's
    `final` last (`checkpoints.md` §4). A shipped path is spelled relative to the repository
    root, because the index is a declaration about what travels with the repository; a run
    record spells the same artefact absolutely, as `agents.save` wrote it.
    """
    entries = []
    for rung, variant, seed in SHIPPED_FINALS:
        for member in _window_members(variant):
            if member["seed"] == seed:
                entries.append(member)
        entries.append(_final_entry(rung, variant, seed))
    for entry in entries:
        entry["path"] = layout._relative(entry["path"])
    return entries


def checkpoints():
    """The shipped index: every final model and every retained window, each listed once."""
    return {
        "format": "pypoker-training-checkpoint-index",
        "version": 1,
        "root": layout._relative(layout.CHECKPOINT_ROOT),
        "shipped": [rung for rung in declarations.RUNG_NAMES if rung in SHIPPED],
        "pending": [rung for rung in declarations.RUNG_NAMES if rung not in SHIPPED],
        "successor": dict(SUCCESSOR),
        "windows": {
            variant: {
                "rung": rung,
                "retained": declarations.RETAINED,
                "seeds": list(declarations.SEEDS),
                "inherited_by": SUCCESSOR.get(rung),
            }
            for rung, variant in SHIPPED.items()
        },
        "entries": _entries(),
    }
