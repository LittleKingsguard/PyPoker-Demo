#!/usr/bin/env python3
"""Regenerate `checkpoints/evidence/r1-live.json` from the current build.

The bundle is evidence and not an interface (`docs/L3/training/evidence.md` §1): no entry
point reads it and none writes it, so its producer is a script and not a module.  `scripts/`
is claimed by no module (`docs/L1/module-map.md` §5), which is why the producer lives here
and why shipping it turns the file into no interface: nothing imports it.

This script is the executable form of `docs/L3/training/evidence.md` §6, and it calls only
the declared entry points of `e2e-surface.md` §3:

1. `training.run("R1")` at the declared live budget — seeds `0, 1, 2`, 1,000 hands per
   variant per seed, `cpu`, from the repository root (`loop.md` §5);
2. `evaluation.build_pool({"members": [], "m": 5, "frozen": True})`, then
   `evaluation.pool_members(pool)` — R1's baselines-only declaration (`records.md` §8);
3. `evaluation.policy_from(<the seed-0 final>)` — the trained member a live table plays;
4. `evaluation.matrix(pool, [member], "live")` — four members, six cells, 120 hands each;
5. `evaluation.rating(matrix)` — the Bradley-Terry fit over those cells;
6. `record["matrix"]`, `record["rating"]`, then
   `evaluation.report("R1", record, matrix, rating)`;
7. the seventeen keys of §2, with `rungs()`, `devices()`, `rung("R2")` and `checkpoints()`
   read once beside them, the curves hoisted to §4's bundle layout; and the `provenance`
   key, which names the build the file came from — a source digest, the git commit and
   whether the tree was dirty, the interpreter's and the two pinned packages' versions, the
   device and a UTC timestamp.

It writes **one** file of its own, the evidence bundle, and prints a summary to stdout.  The
run it drives writes the shipped `checkpoints/R1/naive-numeric/seed-{0,1,2}/` tree, because
that is what a run at the declared budget does (`checkpoints.md` §3, §5); the script itself
creates no second artefact, no log and no cache.

Three refusals, all before the first hand is dealt:

* `PYPOKER_CHECKPOINT_ROOT` set — the bundle names the *shipped* layout, so a redirected
  write root would fill it with absolute paths (`checkpoints.md` §2, `write-root.md` §3).
* `PYTHONHASHSEED` not `0` — see `HASH_SEED` below: without the pin this file is a function
  of the interpreter's per-process hash seed and of nothing else the record names.
* a run whose record is not the declared one — seeds `0, 1, 2`, 1,000 hands, `cpu`, one
  variant — because a bundle that named another budget would be a different measurement.

Usage — from the repository root, and the pin is the producer's own condition, not a
convenience (it re-roots itself at the repository root, so the working directory does not
matter):

    PYTHONHASHSEED=0 .venv/bin/python scripts/regenerate-evidence.py
    PYTHONHASHSEED=0 .venv/bin/python scripts/regenerate-evidence.py --preflight
"""

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from importlib import metadata

#: The repository root, derived from this file's own location (`layout.py`'s rule).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: The source tree every entry point is imported from, without needing `PYTHONPATH`.
SRC = os.path.join(ROOT, "src")

#: The one artefact this script writes.
EVIDENCE = os.path.join(ROOT, "checkpoints", "evidence", "r1-live.json")

#: The ambient write-root override a run reads; this producer refuses it (`layout.OVERRIDE`).
OVERRIDE = "PYPOKER_CHECKPOINT_ROOT"

#: The pinned hash seed, and the one measurement condition besides the device.
#:
#: `engine.equity` prices a decision by sampling `pokerkit`'s equities, and the order of the
#: universe that sampling draws from follows a set whose iteration order is Python's
#: *per-process* string-hash seed.  Two processes therefore report different equity
#: estimates for one `(readout, seed, samples)` triple, and the `oracle` baseline — whose
#: decisions compare that estimate against the pot odds — moves a hand with them: measured
#: on this tree, one live cell read `57/3/60` in one process and `58/3/59` in another, and
#: two 60-hand runs of one `(configuration, seed set, budget)` differed in their last two
#: curve points.  Pinning the seed is what makes this file a function of the build alone;
#: it changes no seed, hand, budget, arithmetic or membership, and it is recorded in the
#: bundle's `provenance` so a reader can reproduce the measurement instead of guessing at it.
HASH_SEED = "0"

#: `docs/L3/training/evidence.md` §2's seventeen top-level keys, in the file's own order.
KEYS = (
    "stages", "errors", "rungs", "devices", "run",
    "run_wall_clock_seconds", "run_hands", "pool_versions", "pool_record",
    "r2_pool", "matrix", "rating", "report_families", "report",
    "index_summary", "index_missing", "provenance",
)

#: The run this bundle is the evidence of: the R1 live budget's declared set (`protocol.md` §2).
SEEDS = [0, 1, 2]
BUDGET = 1000
VARIANT = "naive-numeric"

#: The build digest's covered set and its exact recipe, stated in the file itself.
COVERED = "every `src/**/*.py` file plus `pyproject.toml`"
DIGEST_RECIPE = (
    "sha256 of the byte string formed by concatenating, in ascending order of "
    "repository-relative POSIX path, each covered file's path, one NUL byte (0x00) and "
    "that file's exact bytes; `__pycache__` is not a covered directory"
)

#: The declared entry points this producer calls, and no other (`e2e-surface.md` §3).
ENTRY_POINTS = [
    "training.rungs", "training.rung", "training.run", "training.devices",
    "training.checkpoints", "evaluation.build_pool", "evaluation.pool_members",
    "evaluation.policy_from", "evaluation.matrix", "evaluation.rating",
    "evaluation.report",
]


def _importable():
    """Put `src/` on the import path, so the script needs no `PYTHONPATH` (`README.md` §5)."""
    if SRC not in sys.path:
        sys.path.insert(0, SRC)


def _source_files():
    """`COVERED` as repository-relative POSIX paths, sorted — the digest's one order."""
    found = []
    for base, folders, names in os.walk(os.path.join(ROOT, "src")):
        folders[:] = sorted(folder for folder in folders if folder != "__pycache__")
        for name in sorted(names):
            if name.endswith(".py"):
                path = os.path.join(base, name)
                found.append(os.path.relpath(path, ROOT).replace(os.sep, "/"))
    found.append("pyproject.toml")
    return sorted(found)


def _source_digest(files):
    """The build digest, by `DIGEST_RECIPE` exactly."""
    digest = hashlib.sha256()
    for path in files:
        with open(os.path.join(ROOT, path), "rb") as handle:
            body = handle.read()
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(body)
    return digest.hexdigest()


def _git(*arguments):
    """One git command's stdout, or `None` when git cannot answer (`protocol.md` §5)."""
    try:
        done = subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    return done.stdout


def _git_facts():
    """The commit and the tree's state at generation, or `"unavailable"` where git cannot answer.

    A staged clone has no history, so `commit` is `"unavailable"` there; a repository git
    cannot inspect gets the same word for `working_tree_dirty`, and neither is an exception:
    a bundle that failed to be written for lack of git would be evidence nobody can make.
    """
    commit = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain")
    if commit is None or not commit.strip():
        return {"commit": "unavailable", "working_tree_dirty": "unavailable"}
    return {
        "commit": commit.strip(),
        "working_tree_dirty": "unavailable" if status is None else bool(status.strip()),
    }


def _package(name):
    """One installed distribution's version, or `"unavailable"` (`pokerkit` exports none)."""
    try:
        return str(metadata.version(name))
    except metadata.PackageNotFoundError:
        return "unavailable"


def _provenance(files, digest, device):
    """The seventeenth key: the build this file came from, readable from the file alone."""
    return {
        "producer": "scripts/regenerate-evidence.py",
        "recipe": "docs/L3/training/evidence.md §6",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_digest": {
            "sha256": digest,
            "covered": COVERED,
            "recipe": DIGEST_RECIPE,
            "file_count": len(files),
            "files": list(files),
        },
        "git": _git_facts(),
        "versions": {
            "python": platform.python_version(),
            "numpy": _package("numpy"),
            "pokerkit": _package("pokerkit"),
        },
        "environment": {"PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED", "unset")},
        "device": str(device),
        "entry_points": list(ENTRY_POINTS),
    }


def _hoist(curves):
    """A run record's per-seed curves as §4's bundle layout: one spread per variant.

    `curves[variant][str(seed)] = {samples, td_error, spread}` becomes
    `curves[variant] = {samples, seeds: {str(seed): {samples, td_error}}, spread}`: the axis
    and the one spread at variant level, the per-seed signals under `seeds`, and no `spread`
    key inside a seed's entry (`curves.md` §4, `docs/L3/training/evidence.md` §4).
    """
    hoisted = {}
    for variant, points in curves.items():
        seeds = {}
        axis = None
        spread = None
        for seed, entry in points.items():
            seeds[str(seed)] = {
                "samples": list(entry["samples"]),
                "td_error": [float(point) for point in entry["td_error"]],
            }
            if axis is None:
                axis = list(entry["samples"])
            repeated = [float(point) for point in entry["spread"]]
            if spread is None:
                spread = repeated
            elif repeated != spread:
                raise SystemExit(
                    "regenerate-evidence.py: %r seed %s carries a different spread array; "
                    "a run record repeats one array at each seed (`curves.md` §4)"
                    % (variant, seed)
                )
        hoisted[variant] = {
            "samples": axis if axis is not None else [],
            "seeds": seeds,
            "spread": spread if spread is not None else [],
        }
    return hoisted


def _present(path):
    """Whether the repository carries the artefact a recorded path names.

    A recorded path is repository-relative with POSIX separators (`checkpoints.md` §2), so
    it is joined to the root here rather than resolved from the working directory — the one
    subtraction this script makes from `layout._resolve`, which is no entry point.
    """
    spelling = str(path)
    if not os.path.isabs(spelling):
        spelling = os.path.join(ROOT, spelling)
    return os.path.isfile(spelling)


def _index(training):
    """`checkpoints()` read once: the summary and the entries the repository lacks (§2, §5)."""
    index = training.checkpoints()
    entries = list(index["entries"])
    missing = [str(entry["id"]) for entry in entries if not _present(entry["path"])]
    summary = {
        "shipped": list(index["shipped"]),
        "pending": list(index["pending"]),
        "entries": len(entries),
        "all_exist": not missing,
    }
    return summary, missing


def _r2_pool(training):
    """The pool `R2`'s declaration carries: its id and its retained version members (§2)."""
    pool = training.rung("R2")["pool"]
    members = pool.get("members") or ()
    return {"id": str(pool["id"]), "versions": [str(member["id"]) for member in members]}


def _timed(stages, errors, name, call):
    """Run one stage, record its wall clock, and file a refusal by name if it raises."""
    started = time.perf_counter()
    try:
        return call()
    except Exception as error:  # noqa: BLE001 - the stage's own class is recorded, not caught
        errors.append({"stage": name, "error": "%s: %s" % (type(error).__name__, error)})
        raise
    finally:
        stages[name] = {"seconds": time.perf_counter() - started}


def _check_record(record):
    """Refuse to write a bundle that is not the R1 live measurement this file declares."""
    if str(record["rung"]) != "R1":
        raise SystemExit("regenerate-evidence.py: the run's rung is %r, not 'R1'" % (record["rung"],))
    if [int(seed) for seed in record["seeds"]] != SEEDS:
        raise SystemExit(
            "regenerate-evidence.py: the run's seeds are %r, not %r (protocol.md §2)"
            % (record["seeds"], SEEDS)
        )
    if int(record["budget"]) != BUDGET:
        raise SystemExit(
            "regenerate-evidence.py: the run's budget is %r, not the declared live budget %d"
            % (record["budget"], BUDGET)
        )
    if str(record["device"]) != "cpu":
        raise SystemExit(
            "regenerate-evidence.py: the run used %r, and the shipped measurement is CPU "
            "(protocol.md §6, D-8)" % (record["device"],)
        )
    if list(record["curves"]) != [VARIANT]:
        raise SystemExit(
            "regenerate-evidence.py: the run trained %r, and this bundle is the evidence of "
            "%r (ladder.md §2)" % (list(record["curves"]), VARIANT)
        )


def _spread_deviation(bundle):
    """The worst gap between a stored spread value and the max minus min of its own series.

    The one arithmetic claim §3 and §4 of `docs/L3/training/evidence.md` make about the
    regenerated file, checked before it is written: at every point the array **is** the max
    minus the min of the seeds' `td_error` at that index (`curves.md` §4, FAM-4.8).
    """
    worst = 0.0
    for variant, block in bundle["run"]["curves"].items():
        series = [entry["td_error"] for entry in block["seeds"].values()]
        for index, recorded in enumerate(block["spread"]):
            wanted = max(signal[index] for signal in series) - min(
                signal[index] for signal in series
            )
            gap = abs(float(recorded) - wanted)
            if round(float(recorded), 12) != round(wanted, 12):
                raise SystemExit(
                    "regenerate-evidence.py: %r point %d stores %r where the max minus min of "
                    "its own series is %r (curves.md §4)" % (variant, index, recorded, wanted)
                )
            worst = max(worst, gap)
    return worst


def _check_keys(bundle):
    """The bundle is one object of §2's seventeen keys, in §2's order, and no other."""
    if tuple(bundle) != KEYS:
        raise SystemExit(
            "regenerate-evidence.py: the bundle's keys are %r, and docs/L3/training/evidence.md "
            "§2 declares %r" % (tuple(bundle), KEYS)
        )


def _write(bundle):
    """Write the bundle, and only the bundle (`_write_document`'s rule, `tables.py`)."""
    folder = os.path.dirname(EVIDENCE)
    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    with open(EVIDENCE, "w", encoding="utf-8") as handle:
        json.dump(bundle, handle, indent=1)
        handle.write("\n")
    return EVIDENCE


def _summary(bundle, deviation):
    """The numbers a reader of the run needs, printed once for the record."""
    run = bundle["run"]
    matrix = bundle["matrix"]
    fitted = bundle["rating"]
    timings = {
        str(seed): {
            "hands": int(entry["hands"]),
            "wall_clock_seconds": float(entry["wall_clock_seconds"]),
            "seconds_per_hand": float(entry["seconds_per_hand"]),
            "hands_per_second": float(entry["hands_per_second"]),
        }
        for seed, entry in run["timings"][VARIANT].items()
    }
    cells = [
        {
            "members": list(cell["members"]),
            "hands": int(cell["hands"]),
            "directions": [
                {
                    "wins": int(direction["wins"]),
                    "ties": int(direction["ties"]),
                    "losses": int(direction["losses"]),
                    "mean_chip_delta": float(direction["mean_chip_delta"]),
                }
                for direction in cell["directions"]
            ],
        }
        for cell in matrix["cells"]
    ]
    table_hands = sum(cell["hands"] for cell in cells)
    matrix_seconds = float(bundle["stages"]["matrix_live"]["seconds"])
    hands = int(bundle["run_hands"])
    wall = float(bundle["run_wall_clock_seconds"])
    return {
        "keys": len(bundle),
        "key_names": list(bundle),
        "provenance": bundle["provenance"],
        "timings": timings,
        "run_hands": hands,
        "run_wall_clock_seconds": wall,
        "run_seconds_per_hand": wall / hands if hands else 0.0,
        "stages": bundle["stages"],
        "table_hands": table_hands,
        "matrix_seconds": matrix_seconds,
        "matrix_seconds_per_hand": matrix_seconds / table_hands if table_hands else 0.0,
        "pool": bundle["pool_record"]["id"],
        "pool_record": bundle["pool_record"],
        "pool_versions": list(bundle["pool_versions"]),
        "r2_pool": bundle["r2_pool"],
        "matrix_members": list(matrix["members"]),
        "table": matrix["table"],
        "table_seed": matrix["table_seed"],
        "hands_per_cell": matrix["hands_per_cell"],
        "cell_count": matrix["cell_count"],
        "cells": cells,
        "rating": {
            str(member): {
                "value": float(entry["value"]),
                "interval": [float(edge) for edge in entry["interval"]],
                "hands": int(entry["hands"]),
            }
            for member, entry in fitted["values"].items()
        },
        "rating_iterations": int(fitted["iterations"]),
        "rating_resamples": int(fitted["resamples"]),
        "rating_converged": bool(fitted["converged"]),
        "bootstrap_seed": fitted["bootstrap_seed"],
        "report_families": list(bundle["report_families"]),
        "report_family_count": len(bundle["report_families"]),
        "index_summary": bundle["index_summary"],
        "index_missing": bundle["index_missing"],
        "spread_max_abs_deviation": deviation,
    }


def _print_summary(bundle, deviation):
    """Print the summary between two markers, so it can be quoted as it was printed."""
    print("=== evidence summary (json) ===")
    json.dump(_summary(bundle, deviation), sys.stdout, indent=1)
    print()
    print("=== end evidence summary ===")


def main(argv):
    """The producer: preflight, or the run and the write (§6 steps 1-7)."""
    preflight = "--preflight" in list(argv)
    if os.environ.get("PYTHONHASHSEED") != HASH_SEED:
        print(
            "regenerate-evidence.py: PYTHONHASHSEED is %r and this producer needs %r. "
            "`engine.equity`'s sampling universe follows Python's per-process hash seed, so "
            "an unpinned interpreter gives a different `oracle` estimate — and therefore a "
            "different evidence bundle — from one process to the next. Run it as:\n\n"
            "    PYTHONHASHSEED=%s .venv/bin/python scripts/regenerate-evidence.py%s\n"
            % (
                os.environ.get("PYTHONHASHSEED"),
                HASH_SEED,
                HASH_SEED,
                " --preflight" if preflight else "",
            ),
            file=sys.stderr,
        )
        return 2
    if os.environ.get(OVERRIDE):
        print(
            "regenerate-evidence.py: %s is set to %r. This producer writes the shipped "
            "evidence bundle, which names the shipped layout under <repo>/checkpoints; a "
            "redirected write root would fill it with absolute paths "
            "(docs/L3/training/checkpoints.md §2, write-root.md §3). Unset it and re-run."
            % (OVERRIDE, os.environ[OVERRIDE]),
            file=sys.stderr,
        )
        return 2
    os.chdir(ROOT)
    _importable()
    import evaluation
    import training

    files = _source_files()
    digest = _source_digest(files)

    if preflight:
        pool = evaluation.build_pool({"members": [], "m": 5, "frozen": True})
        pool_record = evaluation.pool_members(pool)
        index_summary, index_missing = _index(training)
        r2_pool = _r2_pool(training)
        print("=== evidence preflight (json) ===")
        json.dump(
            {
                "source_digest": {
                    "sha256": digest,
                    "covered": COVERED,
                    "recipe": DIGEST_RECIPE,
                    "file_count": len(files),
                },
                "provenance": _provenance(files, digest, training.devices()["default"]),
                "pool": pool_record["id"],
                "pool_record": pool_record,
                "r2_pool": r2_pool,
                "index_summary": index_summary,
                "index_missing": index_missing,
                "keys": list(KEYS),
                "entry_points_reachable": list(ENTRY_POINTS),
            },
            sys.stdout,
            indent=1,
        )
        print()
        print("=== end evidence preflight ===")
        return 0

    stages = {}
    errors = []
    try:
        record = _timed(stages, errors, "run_R1_live", lambda: training.run("R1"))
        _check_record(record)
        record["curves"] = _hoist(record["curves"])
        pool = _timed(
            stages,
            errors,
            "build_pool",
            lambda: evaluation.build_pool({"members": [], "m": 5, "frozen": True}),
        )
        pool_record = evaluation.pool_members(pool)
        member = evaluation.policy_from(record["checkpoints"][VARIANT]["0"]["final"])
        table = _timed(
            stages, errors, "matrix_live", lambda: evaluation.matrix(pool, [member], "live")
        )
        fitted = _timed(stages, errors, "rating", lambda: evaluation.rating(table))
        record["matrix"] = table
        record["rating"] = fitted
        assembled = _timed(
            stages,
            errors,
            "report",
            lambda: evaluation.report("R1", record, table, fitted),
        )
        index_summary, index_missing = _index(training)
        r2_pool = _r2_pool(training)
    except Exception as error:  # noqa: BLE001 - the stage's own class is what is reported
        print(
            "regenerate-evidence.py: a stage raised, so no bundle was written: %s: %s"
            % (type(error).__name__, error),
            file=sys.stderr,
        )
        print(json.dumps({"errors": errors, "stages": stages}, indent=1), file=sys.stderr)
        return 3

    timings = record["timings"]
    bundle = {
        "stages": stages,
        "errors": errors,
        "rungs": training.rungs(),
        "devices": training.devices(),
        "run": record,
        "run_wall_clock_seconds": sum(
            float(entry["wall_clock_seconds"])
            for variant in timings.values()
            for entry in variant.values()
        ),
        "run_hands": sum(
            int(entry["hands"]) for variant in timings.values() for entry in variant.values()
        ),
        "pool_versions": [
            str(member_record["id"])
            for member_record in pool_record["members"]
            if not member_record.get("baseline")
        ],
        "pool_record": pool_record,
        "r2_pool": r2_pool,
        "matrix": table,
        "rating": fitted,
        "report_families": sorted(assembled),
        "report": assembled,
        "index_summary": index_summary,
        "index_missing": index_missing,
        "provenance": _provenance(files, digest, record["device"]),
    }
    _check_keys(bundle)
    deviation = _spread_deviation(bundle)
    written = _write(bundle)
    print("wrote %s" % (written,))
    _print_summary(bundle, deviation)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
