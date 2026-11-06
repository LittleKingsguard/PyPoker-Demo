"""Where a run writes: the one layout under `checkpoints/` (ASM-18, protocol.md §5).

    checkpoints/<rung>/<variant>/seed-<seed>/step-<samples:04d>.ckpt    one snapshot
    checkpoints/<rung>/<variant>/seed-<seed>/final.ckpt                 that pair's model

`checkpoints/` belongs to this module (module-map.md §5) and `agents.save` writes only
where it is told and invents no directory (agents/surface.md §8), so `_prepare` makes the
directory and a run calls it before it writes. The naming functions are pure: naming a
path writes nothing, which is what lets `checkpoints()` and `rung()` name artefacts
without touching the tree.

A path is *written* as an absolute filesystem path and *recorded* as `_relative` spells
it — relative to the repository root, POSIX separators — so a run record travels with the
tree; `_resolve` reads a recorded path back from the same root and never from the caller's
working directory (docs/L3/training/checkpoints.md §2, protocol.md §5).

The suffix is `.ckpt` on purpose: `.gitignore` ignores `*.pt` and `*.npz`, and the shipped
set has to be committable (protocol.md §5, docs/L3/training/checkpoints.md).
"""

import os

#: The repository root: this file is `<root>/src/training/layout.py`.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#: The directory this module owns for both the shipped models and the intra-run snapshots.
CHECKPOINT_ROOT = os.path.join(ROOT, "checkpoints")

#: The one suffix a checkpoint of this project carries (agents/surface.md §8).
SUFFIX = ".ckpt"


def _name(value):
    """One directory-safe component for a rung or a variant name."""
    return str(value).replace(os.sep, "_").replace("/", "_")


def _directory(rung, variant, seed):
    """The directory one variant × seed pair writes into: a pure path, created nowhere."""
    return os.path.join(
        CHECKPOINT_ROOT, _name(rung), _name(variant), "seed-%d" % (int(seed),)
    )


def _prepare(rung, variant, seed):
    """Make the pair's directory and return it, because `save` invents none."""
    path = _directory(rung, variant, seed)
    os.makedirs(path, exist_ok=True)
    return path


def _snapshot_path(rung, variant, seed, samples):
    """The path snapshot `samples` hands into training is written to."""
    return os.path.join(
        _directory(rung, variant, seed), "step-%04d%s" % (int(samples), SUFFIX)
    )


def _final_path(rung, variant, seed):
    """The path one variant × seed pair's final model is written to."""
    return os.path.join(_directory(rung, variant, seed), "final" + SUFFIX)


def _relative(path):
    """A path as it reads from the repository root, or unchanged when it is outside."""
    absolute = os.path.abspath(str(path))
    if absolute == ROOT or absolute.startswith(ROOT + os.sep):
        return os.path.relpath(absolute, ROOT).replace(os.sep, "/")
    return str(path)


def _resolve(path):
    """A declared path as a filesystem path, a relative one read from the repository root.

    Every path this module records is spelled by `_relative`, so every path it reads back
    is resolved here and never against the caller's working directory: a pool whose
    membership emptied because a talk was started in another directory would pretend a
    version the repository carries is absent (`checkpoints.md` §2, `protocol.md` §5).
    """
    text = os.fspath(path) if not isinstance(path, str) else str(path)
    if os.path.isabs(text):
        return text
    return os.path.join(ROOT, text)


def _resolved(records):
    """The same member records with each declared `path` resolved for a call.

    `evaluation.build_pool` tests a member's path with `os.path.isfile`, and a recorded
    spelling is relative to the repository root; so the pool is handed filesystem paths
    while every record this module returns keeps `_relative`'s spelling
    (`checkpoints.md` §2, `evaluation/surface.md` §5).
    """
    resolved = []
    for record in records:
        member = dict(record)
        if member.get("path") is not None:
            member["path"] = _resolve(member["path"])
        resolved.append(member)
    return resolved


def _version_id(rung, variant, seed, step):
    """A version's id, stable across tables (records.md §7, D-16)."""
    return "%s/%s/seed-%d/step-%04d" % (str(rung), str(variant), int(seed), int(step))


def _final_id(rung, variant, seed):
    """A final model's id, never the id of a snapshot of the same pair."""
    return "%s/%s/seed-%d/final" % (str(rung), str(variant), int(seed))
