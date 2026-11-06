"""Where a run writes: one layout over two roots (ASM-18, protocol.md §5, write-root.md §1).

    <write root>/<rung>/<variant>/seed-<seed>/step-<samples:04d>.ckpt    one snapshot
    <write root>/<rung>/<variant>/seed-<seed>/final.ckpt                 that pair's model

Two roots, and this module is where they meet (docs/L2/training/write-root.md §1-§5):

- the **declared** root is `<repo>/checkpoints`, `CHECKPOINT_ROOT`, derived from this
  file's own location and never from the caller's working directory. Every *read*
  resolves against it — the index's `root`, every declared window, `_resolve` and the two
  naming helpers — because those are declarations about what ships (write-root.md §2);
- the **write** root is what a *run* writes under, `_write_root()`'s answer: the declared
  root unless the one ambient override `OVERRIDE` (`"PYPOKER_CHECKPOINT_ROOT"`) names
  another one, read on every call and never cached, so an override set after
  `import training` still applies (write-root.md §3);
- with the override unset or empty the two roots are one root, so a run started by a
  reader from the repository root writes the shipped layout exactly as before.

`_snapshot_path` and `_final_path` name the *declared* layout and never the write root;
`_write_path` is the one place a declared path becomes a written one, and `_prepare`
makes the pair's directory under the write root because `agents.save` writes only where
it is told and invents no directory (agents/surface.md §8). The naming functions are
pure: naming a path writes nothing, which is what lets `checkpoints()` and `rung()` name
artefacts without touching the tree.

A path is *written* as an absolute filesystem path and *recorded* as `_relative` spells
it — repository-relative with POSIX separators when the artefact is inside the repository
root, otherwise carried unchanged — so a default run's record travels with the tree while
a redirected run's record names a file that exists; `_resolve` reads a recorded path back
from the same root and never from the caller's working directory (write-root.md §5,
docs/L3/training/checkpoints.md §2, protocol.md §5).

The suffix is `.ckpt` on purpose: `.gitignore` ignores `*.pt` and `*.npz`, and the shipped
set has to be committable (protocol.md §5, docs/L3/training/checkpoints.md).
"""

import os

#: The repository root: this file is `<root>/src/training/layout.py`.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#: The directory this module owns for both the shipped models and the intra-run snapshots.
#: This is the **declared** root: every read and the index resolve against it.
CHECKPOINT_ROOT = os.path.join(ROOT, "checkpoints")

#: The name of the one ambient override of docs/L2/training/write-root.md §3: a run writes
#: under `os.environ[OVERRIDE]` when it names a non-empty path. Read from the environment
#: on every call and never cached; it is not an entry point, so the six signatures stand.
OVERRIDE = "PYPOKER_CHECKPOINT_ROOT"

#: The one suffix a checkpoint of this project carries (agents/surface.md §8).
SUFFIX = ".ckpt"


def _write_root():
    """The root a run writes under: the declared root, or what `OVERRIDE` names."""
    value = os.environ.get(OVERRIDE)
    if value:
        return os.path.abspath(value)
    return CHECKPOINT_ROOT


def _write_path(declared):
    """One declared path re-rooted at the write root — and unchanged when roots are one.

    This is the one place a declared path becomes a written path (write-root.md §1, §3).
    """
    root = _write_root()
    if os.path.abspath(root) == os.path.abspath(CHECKPOINT_ROOT):
        return declared
    return os.path.join(root, os.path.relpath(declared, CHECKPOINT_ROOT))


def _name(value):
    """One directory-safe component for a rung or a variant name."""
    return str(value).replace(os.sep, "_").replace("/", "_")


def _directory(rung, variant, seed):
    """The directory one variant × seed pair writes into: a pure path, created nowhere."""
    return os.path.join(
        CHECKPOINT_ROOT, _name(rung), _name(variant), "seed-%d" % (int(seed),)
    )


def _prepare(rung, variant, seed):
    """Make the pair's directory under the write root and return it, because `save` invents none."""
    path = _write_path(_directory(rung, variant, seed))
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
    """How a record spells a written path — two branches, exactly (write-root.md §5).

    An artefact **inside** the repository root is spelled repository-relative with POSIX
    separators, so it travels with the tree; one **outside** it — the declared root of a
    redirected run's write root — is returned unchanged, i.e. the absolute path
    `agents.save` was handed, so a redirected record names a file that exists.
    """
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
