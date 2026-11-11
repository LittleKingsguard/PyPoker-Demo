"""The default shape did not move -- TRNJ-12.

D-29 declares a second game shape and D-33 a third, and both are held to the constraint
`shapes.md` §5 states: "every widening's absence reproduces today's value".  A widening's
absence reproducing a value is a claim about a run, so it is measured here and not argued:
`_default_shape_baseline.json` is a capture of one default-shape run taken **before** the
six-seat shape landed, and this module runs that run's exact tuple again and holds the two
summaries against each other field by field (`shapes.md` §5, `battery.md` §5, D-29, D-33).

| Case | What it reads |
|---|---|
| TRNJ-12.1 | one default-shape run against its pre-change capture, field by field |

The capture and the run it is compared with are one tuple, and it is the capture's own
rather than this battery's invented instance: the configuration, the seed and the budget are
reproduced verbatim, because a capture compared with a different run would measure nothing
(`docs/L1/battery.md` §4-§5, D-15).  The seed is not one of the shipped `0, 1, 2`.

**Why the captured tuple draws no `oracle`, and why that is not a weakening.**  A run is a
record about a sequence of hands, and a comparison of two records is only repeatable when
every hand of both is.  `training.run` freezes a pool whose pinned members are the three
anchor baselines -- `random`, `always-call` and `oracle` -- whether a configuration names
them or not, and `evaluation.opponent` draws one of them per hand.  `random` decides from
its own seeded generator, `always-call` and the folding baselines are pure functions of the
readout, and the learner's `agents.act` draws from its own seeded generator, so all of those
hands are deterministic by construction; the `oracle` baseline is not, because it decides by
comparing `engine.equity`'s estimate with the pot odds, and `docs/L3/engine/stream.md` §1
claims that estimate "is a function of `(decision, seed, samples)` and of nothing else -- two
calls agree to the last bit".  The implementation does not currently meet that claim:
calling `pokerkit.analysis.calculate_equities` exactly as `src/engine/equity.py` does, at a
fixed `random.seed`, returns different numbers under different `PYTHONHASHSEED` values, so an
oracle draw that lands near its threshold flips its decision, its hand plays differently, and
the record's `greedy` block differs.  That is a finding about `engine` and not about
`training`, and it is reported there; this battery may not absorb it by a tolerance, a skip
or a dropped field (`battery.md` §5, D-33).

So the tuple is chosen so that **no hand of its budget draws `oracle`**: the pool pins the
three anchors **and** the three folding baselines of D-21, six members in the catalogue's
order, the oracle at index 2 and therefore drawn one hand in six; the seed is the smallest
at or above 5600 whose twenty-four draws -- `seeds._opponent_seed(seed, i)` reduced by
`evaluation`'s `seed % n` -- never name that index, and that is verified by walking the
draw rather than by hoping.  Every hand of the compared run is then a pure function of
`(configuration, seed, index)` on any interpreter, so the case is deterministic by
construction instead of by a `PYTHONHASHSEED` a caller happened to pass.  Not one field is
relaxed by this: all twenty-one fields below are still compared with `assertEqual`, and the
capture's own byte length and digest are still asserted before the comparison (`shapes.md`
§5, `battery.md` §5, D-33, `docs/L3/engine/stream.md` §1).

Two things are deliberately not in the summary.  No wall clock enters it -- `timings` is read
for its `hands` count and its key set only, because a second is the machine's and not the
design's (`records.md` §12, ASM-15) -- and no artefact's absolute path enters it either: the
paths are relativised against the write root `tests/conftest.py` points
`PYPOKER_CHECKPOINT_ROOT` at, while each container's decompressed member digests are
recorded, so a checkpoint that changed by one byte is caught and a directory that moved is
not (checkpoints.md §2, write-root.md §3).

Every case states the design section whose claim it reads (`docs/L1/battery.md` §5); none
asserts a value a document leaves to the run (`D-6`).
"""

import hashlib
import importlib.util
import json
import os
import sys
import unittest
import zipfile

_HERE = os.path.dirname(os.path.abspath(__file__))
# The support module is loaded under a private name: this repository's integration
# batteries share the file name `_join_support.py`, so a plain import would hand one
# battery another's helpers when two test directories are collected in one process.
if "training_join_support" in sys.modules:
    J = sys.modules["training_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "training_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["training_join_support"] = J
    _spec.loader.exec_module(J)

#: The capture: the pre-change default-shape run this case reproduces (`battery.md` §5,
#: `shapes.md` §5).  Its digest and length are asserted so the case is a measurement of
#: *that* file and not of a file that happens to be there.
CAPTURE = os.path.join(_HERE, "_default_shape_baseline.json")
CAPTURE_SHA256 = "57d01e3e8d6975af19b0dcab37c2ebb50f198a64f12b942431a056ae5f8f9c00"
CAPTURE_BYTES = 28405

#: The folding baselines the captured pool pins beside the anchor three, in the
#: catalogue's order -- the pool's members 3, 4 and 5, so six members and the `oracle`
#: at index 2 is drawn one hand in six (`records.md` §8, `D-21`, `D-33`).
CAPTURE_BASELINES = (
    "fold-no-pair-or-face",
    "fold-no-pair-or-better",
    "fold-large-bet",
)

#: The captured run's own tuple: one label, one variant, an empty window, one seed,
#: twenty-four hands, the live table and the cpu.  These are the capture's, reproduced as
#: they stand.  The seed is the smallest at or above 5600 whose budget draws no `oracle`
#: (`docs/L3/engine/stream.md` §1, `battery.md` §5, D-33).
CAPTURE_LABEL = "trnj-baseline-default"
CAPTURE_VARIANT = "variant-1"
CAPTURE_SEED = 5681
CAPTURE_BUDGET = 24

#: The fields the capture holds, in its own order, exactly as this case reads them.
CAPTURE_FIELDS = (
    "record_keys",
    "rung",
    "game",
    "seeds",
    "budget",
    "device",
    "table",
    "rules",
    "utilities",
    "curves",
    "greedy",
    "params",
    "pool",
    "variants",
    "baselines",
    "axis row",
    "timings",
    "checkpoints",
    "header",
    "header_checkpoint_count",
    "header_checkpoint_suffixes",
)


def plain(value):
    """One record as value only, so a tuple and a list compare equal (`records.md` §1).

    A record is `records.md`'s data and the containers it uses are the design's freedom --
    a member list may be a tuple, a descriptor a `str` -- so a summary compares values and
    never container classes; a `set` becomes its sorted list, because a declaration that is
    a set of catalogue names is a set and not an order (`fairness.md` §4, `utilities.md` §8).
    """
    if isinstance(value, dict) or hasattr(value, "items"):
        return {str(key): plain(inner) for key, inner in dict(value).items()}
    if isinstance(value, (set, frozenset)):
        return sorted(plain(inner) for inner in value)
    if isinstance(value, (list, tuple)):
        return [plain(inner) for inner in value]
    if hasattr(value, "__fspath__"):
        return os.fspath(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    try:
        return os.fspath(value)
    except TypeError:
        return str(value)


def rel(path):
    """One artefact path under the run's write root, relative and POSIX-spelled.

    The write root is the ambient `PYPOKER_CHECKPOINT_ROOT` `tests/conftest.py` establishes
    for the session, which is where a battery's writes land and never `<repo>/checkpoints`
    (`docs/L2/training/write-root.md` §1, §3, `checkpoints.md` §2, §5).  A path outside it is
    reported as it stands rather than silently shortened.
    """
    text = os.path.abspath(os.fspath(path))
    base = os.path.abspath(os.environ["PYPOKER_CHECKPOINT_ROOT"])
    if text == base:
        return "."
    if text.startswith(base + os.sep):
        return os.path.relpath(text, base).replace(os.sep, "/")
    return text.replace(os.sep, "/")


def members(path):
    """One checkpoint container's members and their digests (`checkpoints.md` §1-§3).

    A version-4 container records the shape it was trained on and a version-1 one is read as
    the default shape's, so the container's **content** is what this case holds: one row per
    member, sorted by name, each the sha256 of the member's decompressed bytes -- which is
    the one reading that is blind to compression level and time and sensitive to a changed
    parameter (`checkpoints.md` §1-§2, `sizing.md` §6, ASM-18).
    """
    rows = []
    with zipfile.ZipFile(os.fspath(path)) as container:
        for name in sorted(container.namelist()):
            rows.append(
                {
                    "member": name,
                    "sha256": hashlib.sha256(container.read(name)).hexdigest(),
                }
            )
    return rows


def capture_configuration():
    """The exact configuration the capture was taken from (`shapes.md` §5, `battery.md` §5).

    One variant of the naive stack at width 8 and depth 1, an empty window, one seed,
    twenty-four hands, the live table and the cpu -- written as `records.md` §2's
    configuration and as the capture's own tuple, so the run this case reproduces is the
    run that was captured.  The pool declares the three folding baselines beside the
    anchor three `build_pool` pins unconditionally, which is what makes its membership six
    members and what lets the seed be one whose draws never name the `oracle`
    (`records.md` §8, D-21, D-33).
    """
    return {
        "name": CAPTURE_LABEL,
        "variants": [
            {
                "name": CAPTURE_VARIANT,
                "backend": "numpy",
                "encoding": "flat-numeric",
                "architecture": {"kind": "naive-stack", "width": 8, "depth": 1},
            }
        ],
        "pool": {
            "members": [],
            "m": 5,
            "frozen": True,
            "baselines": list(CAPTURE_BASELINES),
        },
        "seeds": [CAPTURE_SEED],
        "samples": CAPTURE_BUDGET,
        "table": "live",
        "device": "cpu",
    }


_RUNS = {}


def capture_run():
    """One run of that configuration, built once per process and shared.

    A run is this battery's expensive observable and the case reads one record, so the
    record is built once and cached for the process (`docs/L1/battery.md` §2,
    `docs/L2/training/loop.md` §3).
    """
    if "record" not in _RUNS:
        _RUNS["record"] = J.run(
            capture_configuration(),
            seeds=[CAPTURE_SEED],
            budget=CAPTURE_BUDGET,
        )
    return _RUNS["record"]


def summary(record):
    """One run record's summary, field for field as the capture holds it.

    Every field is a value the record states and not a re-derivation: the record's key set,
    the seven families `records.md` §12 declares, the pool and the baselines block, the axis
    row, the cost facts' key sets with their hand counts, the whole checkpoint listing
    relativised against the write root, and the header without its own checkpoint list
    (`records.md` §12, `protocol.md` §1, `checkpoints.md` §2-§3, `battery.md` §5).
    """
    built = {}
    built["record_keys"] = sorted(str(key) for key in record)
    for key in ("rung", "game", "seeds", "budget", "device", "table", "rules", "utilities",
                "axis row"):
        built[key] = plain(record[key])
    built["curves"] = plain(record["curves"])
    built["greedy"] = plain(record["greedy"])
    built["params"] = plain(record["params"])
    built["pool"] = plain(record["pool"])
    built["variants"] = plain(record["variants"])
    built["baselines"] = plain(record["baselines"])
    timings = {}
    for variant, per_variant in dict(record["timings"]).items():
        timings[str(variant)] = {
            str(seed): {
                "hands": int(block["hands"]),
                "keys": sorted(str(key) for key in block),
            }
            for seed, block in dict(per_variant).items()
        }
    built["timings"] = timings
    checkpoints = {}
    for variant, per_variant in dict(record["checkpoints"]).items():
        checkpoints[str(variant)] = {}
        for seed, block in dict(per_variant).items():
            ordered = list(block["snapshots"]) + [block["final"]]
            checkpoints[str(variant)][str(seed)] = [
                {"path": rel(path), "members": members(path)} for path in ordered
            ]
    built["checkpoints"] = checkpoints
    header = dict(record["header"])
    built["header"] = {
        str(key): plain(value) for key, value in header.items() if str(key) != "checkpoints"
    }
    listed = list(header.get("checkpoints") or ())
    built["header_checkpoint_count"] = len(listed)
    built["header_checkpoint_suffixes"] = sorted(rel(path) for path in listed)
    return built


class DefaultShapeCaptureCase(J.JoinCase):
    """TRNJ-12.1 -- one default-shape run against its pre-change capture."""

    def test_trnj_12_1_the_default_shape_run_is_the_capture_field_by_field(self):
        """TRNJ-12.1 nothing about the default shape moved, measured against the capture.

        The fixture is a capture of `training.run` on one default-shape tuple taken **before**
        the six-seat shape landed, and this case is what makes "nothing about the default
        shape may move" a measurement rather than a claim: `shapes.md` §5 requires every
        widening to reproduce today's value in its absence, and `battery.md` §5 fixes that a
        widening's absence is judged by a record and not by a sentence.  So one run of the
        same tuple is rebuilt in this process, summarised with the capture's own readers, and
        compared field by field -- the record's key set, its seven families, its pool and its
        baseline rows, its curve, its retained pass, its parameter band, its cost facts' key
        sets, the whole checkpoint listing with each container's member digests, and the
        header without its own checkpoint list.  A differing field is a defect in the
        widening and is reported with both values, never absorbed by a tolerance
        (`shapes.md` §5, `battery.md` §5, `records.md` §12, `checkpoints.md` §2-§3, D-29,
        D-33).

        The tuple is one whose every hand is deterministic by construction: the pool pins
        the anchor three **and** the three folding baselines, and the seed is the smallest
        at or above 5600 whose twenty-four draws -- `evaluation`'s `seed % n` over the
        membership's order -- never name the `oracle` at index 2.  That matters because
        `docs/L3/engine/stream.md` §1 claims `engine.equity`'s estimate is a function of
        `(decision, seed, samples)` and of nothing else, and the implementation does not
        currently meet the claim: `calculate_equities` returns different numbers under
        different `PYTHONHASHSEED` values at a fixed seed, so an oracle draw near the pot
        odds flips, the hand plays differently and this record's `greedy` block moves.  The
        finding is `engine`'s and is reported there; this case stays a measurement of the
        default shape by not drawing the one member whose decision is hash-order fragile,
        and it relaxes nothing -- all twenty-one fields are compared field for field
        (`battery.md` §5, D-33).
        """
        with open(CAPTURE, "rb") as handle:
            raw = handle.read()
        self.assertEqual(
            len(raw),
            CAPTURE_BYTES,
            "the capture this case reads is the 28,405-byte file taken before the six-seat "
            "shape landed, and it is never regenerated (shapes.md §5, battery.md §5): %r "
            "bytes" % (len(raw),),
        )
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            CAPTURE_SHA256,
            "and it is byte-identical to the capture: a fixture edited to match a changed "
            "run would make this case measure nothing (battery.md §5, D-6, D-33): %r"
            % (hashlib.sha256(raw).hexdigest(),),
        )
        capture = json.loads(raw.decode("utf-8"))
        self.assertEqual(
            sorted(str(key) for key in capture),
            sorted(CAPTURE_FIELDS),
            "the capture holds exactly the twenty-one fields this case compares, so no field "
            "of it is read past or left unread (battery.md §5, shapes.md §5): %r"
            % (sorted(str(key) for key in capture),),
        )
        current = summary(capture_run())
        self.assertEqual(
            sorted(str(key) for key in current),
            sorted(CAPTURE_FIELDS),
            "and the summary this case rebuilds holds the same fields and no others, so the "
            "comparison below is the whole of what the capture states (battery.md §5, "
            "records.md §12): %r" % (sorted(str(key) for key in current),),
        )
        for field in CAPTURE_FIELDS:
            self.assertIn(
                field,
                current,
                "the default-shape run must still state the %r field the capture holds, "
                "because every widening's absence reproduces today's value (shapes.md §5, "
                "battery.md §5, D-33): %r" % (field, sorted(current)),
            )
            self.assertEqual(
                current[field],
                capture[field],
                "the %r field of a default-shape run must be the captured value taken "
                "before the six-seat shape landed -- nothing about the default shape may "
                "move, and this reading is what makes that a measurement rather than a "
                "claim (shapes.md §5, battery.md §5, D-29, D-33): current %r against "
                "captured %r" % (field, current[field], capture[field]),
            )


if __name__ == "__main__":
    unittest.main()
