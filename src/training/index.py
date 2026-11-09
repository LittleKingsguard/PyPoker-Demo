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

An entry is a `records.md` §7 version record and therefore carries the **rule** its
artefact was trained under and the **utility** whose reward it was trained on (D-19,
D-20): both are declared per rung beside the rung and the variant — `SHIPPED_RULES` and
`SHIPPED_UTILITIES` — because each is a fact about the run, and a pool built from this
window has to be able to certify each member's estimator and its objective (records.md
§7, §8, rules.md §6, utilities.md §6, ASM-27).
"""

from . import declarations, layout

#: The one rung whose live run ships today: `R1` at the live budget, three seeds.
SHIPPED = {"R1": "naive-numeric"}

#: The rule each shipped run trained under, declared per rung beside `SHIPPED` and keyed by
#: it (`records.md` §7, D-19): a rung added to `SHIPPED` declares its rule here in the same
#: edit, because a version record's `rule` is required and no default stands in for one.
#: R1's live run was written before the catalogue existed, so its version-1 containers carry
#: no `learning_rule` and `agents` reads them as `masked-q-learning` — the only rule its
#: writer could have used — and the shipped set is not regenerated (rules.md §6, ASM-5).
SHIPPED_RULES = {"R1": "masked-q-learning"}

#: The utility each shipped run trained on, declared per rung beside `SHIPPED_RULES` and
#: keyed by the same rung (`records.md` §7, `utilities.md` §6, §7, D-20): a version
#: record's `utility` is required and no default stands in for one, so a rung added to
#: `SHIPPED` declares its utility here in the same edit.  R1's live run was written before
#: the catalogue existed, so its version-1 containers carry no `utility` and `agents` reads
#: them as `net-chips` — the only utility its writer could have used — and the shipped set
#: is not regenerated (`utilities.md` §6, ASM-5, D-20).
SHIPPED_UTILITIES = {"R1": "net-chips"}

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
    """One retained snapshot as a `records.md` §7 version record.

    The path is `layout._relative`'s spelling even here, where the entry is a window member
    handed to a pool rather than a line of the index: a version record is the same record
    wherever it is read, and one artefact has one spelling (checkpoints.md §2, records.md §7).
    `rule` and `utility` are the catalogue members that run trained under — the two facts
    D-19 and D-20 add to the record — so a pool built from this window certifies each
    member's estimator and its objective and its id covers both (records.md §7, §8,
    rules.md §6, utilities.md §6, ASM-27).
    """
    return {
        "id": layout._version_id(rung, variant, seed, step),
        "path": layout._relative(layout._snapshot_path(rung, variant, seed, step)),
        "rung": rung,
        "variant": variant,
        "seed": int(seed),
        "step": int(step),
        "samples": int(step),
        "lineage": lineage,
        "rule": SHIPPED_RULES[rung],
        "utility": SHIPPED_UTILITIES[rung],
        "kind": "snapshot",
    }


def _final_entry(rung, variant, seed):
    """One variant × seed final model, descending from that pair's last snapshot."""
    return {
        "id": layout._final_id(rung, variant, seed),
        "path": layout._relative(layout._final_path(rung, variant, seed)),
        "rung": rung,
        "variant": variant,
        "seed": int(seed),
        "step": int(declarations.LIVE_BUDGET),
        "samples": int(declarations.LIVE_BUDGET),
        "lineage": layout._version_id(rung, variant, seed, declarations.LIVE_BUDGET),
        "rule": SHIPPED_RULES[rung],
        "utility": SHIPPED_UTILITIES[rung],
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
    record spells the same artefact the same way, so one artefact has one spelling and the
    record travels with the tree (`checkpoints.md` §2, `protocol.md` §5).
    """
    entries = []
    for rung, variant, seed in SHIPPED_FINALS:
        for member in _window_members(variant):
            if member["seed"] == seed:
                entries.append(member)
        entries.append(_final_entry(rung, variant, seed))
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
                "rule": SHIPPED_RULES[rung],
                "utility": SHIPPED_UTILITIES[rung],
                "inherited_by": SUCCESSOR.get(rung),
            }
            for rung, variant in SHIPPED.items()
        },
        "entries": _entries(),
    }
