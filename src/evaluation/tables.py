"""The two table budgets and the one shipped artefact (`docs/L3/evaluation/tables.md`).

`tables/league-full.json` is UTF-8 JSON: one object whose keys are `schema`, `table`,
`pool`, `matrix`, `rating`, `provenance` and `cost`.  `pool`, `matrix` and `rating` are
the three records unchanged, so a reader can compare the file's matrix against its own
`matrix` call record for record (`tables.md` §3).

No entry point reads or writes this file (D-12, G19): the producer is this module's
``__main__``, so the recipe is one command and not a notebook that knows the schema::

    PYTHONPATH=src .venv/bin/python -m evaluation.tables

The membership is the one this repository can build and measure today: the three pinned
baselines -- a frozen pool declared as ``{"members": [], "m": 5, "frozen": True}``, which
is R1's pool -- and one variant member, ``variant-1``, built deterministically from its
own recipe at the module's own `VARIANT_SEED`.  It never names a version it could not
load, and its provenance says which membership it is (`tables.md` §2, §5-§6).
"""

import json
import os
import time

from .declarations import M
from .matrix import matrix
from .pool import build_pool, pool_members
from .rating import rating

#: The format's name and version, so a reader can refuse a different one (`tables.md` §3).
SCHEMA = "pypoker-evaluation-league-table/1"

#: The module's own path for the artefact -- the one home of its name (`module-map.md` §5).
SHIPPED_PATH = os.path.join("tables", "league-full.json")

#: The seed the shipped variant's learner and policy are built at: the module's own
#: constant, never a table-derived seed (`tables.md` §2, §5, `matrix.md` §4).
VARIANT_SEED = 31415

#: The variant's recipe: the R1-shaped backend, encoding and architecture the job ran
#: with.  This module chooses none of them; they are recorded so a third party can
#: rebuild the same member (`tables.md` §5).
VARIANT_BACKEND = "numpy"
VARIANT_ENCODING = "flat-numeric"
VARIANT_ARCHITECTURE = {"kind": "naive-stack", "width": 96, "depth": 2}

#: ASM-15's per-hand **bound**, carried beside the measurement so the two are never
#: confused (`tables.md` §5, `declarations.md` §4.1).
PER_HAND_CEILING_SECONDS = 0.04


def _cost_block(hands, wall_clock_seconds):
    """The measured cost of one run: hands, per-hand seconds, throughput and wall clock.

    Every number here was observed around the `matrix` call on the device that ran it;
    `measured: true` says so, and `per_hand_ceiling_seconds` is the bound carried beside
    them (`tables.md` §5, D-8).
    """
    hands = int(hands)
    wall = float(wall_clock_seconds)
    seconds_per_hand = wall / hands if hands else 0.0
    hands_per_second = hands / wall if wall > 0.0 else 0.0
    return {
        "hands": hands,
        "seconds_per_hand": seconds_per_hand,
        "hands_per_second": hands_per_second,
        "wall_clock_seconds": wall,
        "device": "cpu",
        "per_hand_ceiling_seconds": PER_HAND_CEILING_SECONDS,
        "measured": True,
    }


def _membership_kind(pool_record):
    """Which membership the file names: `baselines+variant` or `pool+variant` (§2, §6)."""
    versions = [
        member["id"]
        for member in pool_record["members"]
        if not member.get("baseline")
    ]
    return "pool+variant" if versions else "baselines+variant"


def _build_document(pool_record, matrix_record, rating_record, variants, cost):
    """The seven-key document of `tables.md` §3, its provenance block included (§5)."""
    hands = len(matrix_record["cells"]) * int(matrix_record["hands_per_cell"])
    provenance = {
        "module": "evaluation",
        "entry_points": ["build_pool", "matrix", "rating"],
        "schema": SCHEMA,
        "table_seed": int(matrix_record["table_seed"]),
        "budget": matrix_record["table"],
        "hands_per_cell": int(matrix_record["hands_per_cell"]),
        "cell_count": len(matrix_record["cells"]),
        "hands_played": hands,
        "membership_kind": _membership_kind(pool_record),
        "members": list(matrix_record["members"]),
        "variants": list(variants),
        "pool": {
            "id": pool_record["id"],
            "m": int(pool_record["m"]),
            "frozen": bool(pool_record["frozen"]),
        },
    }
    return {
        "schema": SCHEMA,
        "table": matrix_record["table"],
        "pool": pool_record,
        "matrix": matrix_record,
        "rating": rating_record,
        "provenance": provenance,
        "cost": cost,
    }


def _write_document(document, path=SHIPPED_PATH):
    """Write one document to its path, creating the directory it lives in if need be."""
    folder = os.path.dirname(str(path))
    if folder and not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return path


def _json_safe(value):
    """The document's values as plain JSON data: tuples are arrays, nothing else moves."""
    if isinstance(value, dict):
        return {str(key): _json_safe(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(inner) for inner in value]
    return value


def _variant_member():
    """The shipped variant: one untrained learner as a policy, and its measured capacity.

    The one carve-out of the import boundary (`README.md` §5): this offline recipe calls
    `agents.build_learner` for the artefact's variant.  No entry point may, and no talk
    does -- a variant handed to `matrix` is a policy already built (`matrix.md` §4).
    """
    import agents
    import features

    encoder = features.build_encoder(VARIANT_ENCODING)
    learner = agents.build_learner(
        {
            "backend": VARIANT_BACKEND,
            "architecture": dict(VARIANT_ARCHITECTURE),
            "seed": VARIANT_SEED,
            "encoder": encoder,
        }
    )
    policy = agents.as_policy(learner, encoder, VARIANT_SEED)
    recipe = {
        "id": "variant-1",
        "backend": VARIANT_BACKEND,
        "encoding": VARIANT_ENCODING,
        "architecture": dict(VARIANT_ARCHITECTURE),
        "seed": VARIANT_SEED,
        "params": int(agents.param_count(learner)),
    }
    return policy, recipe


def _produce(path=SHIPPED_PATH):
    """Build the pool, play the full table, fit the rating and write the artefact.

    The `matrix` call is timed with `time.perf_counter` and the hands it played are
    counted, which is what the cost block records (`tables.md` §4-§5).
    """
    pool = build_pool({"members": [], "m": M, "frozen": True})
    policy, recipe = _variant_member()
    started = time.perf_counter()
    table = matrix(pool, [policy], "full")
    wall_clock_seconds = time.perf_counter() - started
    fitted = rating(table)
    hands = len(table["cells"]) * int(table["hands_per_cell"])
    document = _build_document(
        pool_members(pool),
        table,
        fitted,
        [recipe],
        _cost_block(hands, wall_clock_seconds),
    )
    written = _write_document(_json_safe(document), path)
    print(
        "evaluation: wrote %s -- %s table, %d members, %d cells, %d hands in %.2f s "
        "(%.4f s/hand, %.2f hands/s)"
        % (
            written,
            table["table"],
            len(table["members"]),
            len(table["cells"]),
            hands,
            wall_clock_seconds,
            hands and wall_clock_seconds / hands or 0.0,
            hands and hands / wall_clock_seconds or 0.0,
        )
    )
    return written


if __name__ == "__main__":
    _produce()
