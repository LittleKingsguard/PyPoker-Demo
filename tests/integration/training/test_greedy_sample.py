"""The pass samples the run, and below the bound that is the run it was -- TRNJ-13.

D-36 replaced the pass's hand count with a **sample** of the run's own hands: one pass plays
`S = min(budget, 2,000)` hands and hand *j* of the pass is the run's own hand *j*
(`docs/L3/training/greedy.md` §1, §4).  Below the bound the rule is the **identity**, so a
1,000-hand run must produce, field for field, the record it produced before the rule existed
— and that is a claim about a run, so it is measured here and not argued: this module has one
pre-change tuple replayed again, in a child pinned to the capture's own `PYTHONHASHSEED`, and
holds that child's summary against `_greedy_sample_baseline.json`, a capture of that run taken
**before** the rule landed, field by field (`battery.md` §5, `shapes.md` §5, `records.md` §12,
§15, `greedy.md` §1, §4, §5, `sizing.md` §4, ASM-38, D-36).

| Case | What it reads |
|---|---|
| TRNJ-13.1 | one 1,000-hand run against its pre-change capture, all twenty-one fields |

The capture and the run it is compared with are one tuple, and it is the capture's own rather
than this battery's invented instance: the configuration, the seed `7001` and the 1,000-hand
budget are reproduced verbatim, because a capture compared with a different run would measure
nothing (`docs/L1/battery.md` §4-§5, D-15).  The seed is not one of the shipped `0, 1, 2`.
The capture's own byte length and sha256 are asserted before the comparison, so a fixture
edited to match a changed run makes the case measure nothing rather than pass
(`battery.md` §5, D-6).

**This case is a pinned-interpreter reproduction, and the pin is the case's own job.**  The
captured pool pins the three anchor baselines of D-6 and declares D-21's three folders beside
them, so six members and the `oracle` at index 2 — drawn about one hand in six.  The `oracle`
decides by comparing `engine.equity`'s sampled estimate with the pot odds, and
`docs/L3/engine/stream.md` §1 claims that estimate "is a function of `(decision, seed, samples)`
and of nothing else -- two calls agree to the last bit"; the implementation does not currently
meet that claim, because `pokerkit.analysis.calculate_equities` returns different numbers under
different `PYTHONHASHSEED` values at a fixed seed, so an oracle draw near its threshold flips,
the hand plays differently and both the curves and the `greedy` block move.  The capture was
therefore taken under `PYTHONHASHSEED=0`, and `training/guardrails.md` G20 states exactly what
that leaves: a re-run reproduces "one build's, one pinned interpreter's" result
(`docs/L3/engine/stream.md` §1, `battery.md` §5, D-33).  So the tuple is replayed by
`_greedy_sample_capture.py` in a **child process whose environment carries `PYTHONHASHSEED=0`**,
the pin the capture was taken under, and this module compares that child's summary with the
fixture field for field.  The pin travels with the child rather than with the runner, so the case
is green whatever `PYTHONHASHSEED` the process collecting it was started with, and
`scripts/run-all-tests.sh` need not pin anything (`docs/L3/training/greedy.md` §5, `guardrails.md`
G20, D-33).

**What that equality is: the proof that the run did not move when D-36 landed.**  The 1,000-hand
run's `greedy` block, its curves, its parameters, its header and every checkpoint member's digest
are compared with the capture field for field, and if the child's summary equals the fixture then
that equality **is** the measurement — `greedy.md` §1 and §5 claim the block below the bound is
the pre-change one, and `battery.md` §5 fixes such a claim as judged by a record and not by a
sentence (`battery.md` §5, `records.md` §12, §15, `docs/L3/training/greedy.md` §5, ASM-38, D-36).

That is **not** `TRNJ-12.1`'s situation, whose tuple is chosen so that no hand of its budget draws
the `oracle` and is therefore deterministic by construction.  What this case's pin buys is the
capture's own interpreter and nothing wider: if this process's own unpinned hash seed would move
the same tuple's numbers, that is `engine.equity`'s finding, reported in `engine`, and not
something this battery may absorb by a tolerance, a skip or a dropped field
(`docs/L3/engine/stream.md` §1, `battery.md` §5, D-33).

Two things are deliberately not in the summary, and both are the capture's own choice rather
than this case's: no wall clock enters it — `timings` is read for its `hands` count and its key
set only, because a second is the machine's and not the design's (`records.md` §12, ASM-15) —
and no artefact's absolute path enters it either: the checkpoint paths are relativised against
the write root `tests/conftest.py` points `PYPOKER_CHECKPOINT_ROOT` at, while each container's
decompressed member digests are recorded, so a checkpoint that changed by one byte is caught
and a directory that moved is not (`checkpoints.md` §2, `write-root.md` §3).

Every case states the design section whose claim it reads (`docs/L1/battery.md` §5); none
asserts a value a document leaves to the run (`D-6`).
"""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))

# The support module is loaded under a private name, exactly as every module of this battery
# loads it: the repository's integration batteries share the file name `_join_support.py`, so a
# plain import would hand one battery another's helpers when two test directories are collected
# in one process.
if "training_join_support" in sys.modules:
    J = sys.modules["training_join_support"]
else:
    _spec = importlib.util.spec_from_file_location(
        "training_join_support", os.path.join(_HERE, "_join_support.py")
    )
    J = importlib.util.module_from_spec(_spec)
    sys.modules["training_join_support"] = J
    _spec.loader.exec_module(J)

#: The capture: the pre-change 1,000-hand run this case reproduces (`battery.md` §5,
#: `greedy.md` §1, §4, D-36).  Its digest and length are asserted so the case is a measurement
#: of *that* file and not of a file that happens to be there; it is byte-identical to the
#: authoritative capture the rule was designed against.
CAPTURE = os.path.join(_HERE, "_greedy_sample_baseline.json")
CAPTURE_SHA256 = "6394f22b650ef7f5e31c7534be33d42c653e50b2cc345a16d4412d10020bed12"
CAPTURE_BYTES = 871982

#: The capture's own tuple: one label, one naive-stack variant at width 8 and depth 1, an empty
#: version window whose pool declares D-21's three folding baselines beside the anchor three, one
#: seed, 1,000 hands, the live table and the cpu.  These are the capture's, reproduced as they
#: stand (`battery.md` §5, `shapes.md` §5, `records.md` §8, D-21).
CAPTURE_LABEL = "trnj-greedy-sample"
CAPTURE_VARIANT = "variant-1"
CAPTURE_SEED = 7001
CAPTURE_BUDGET = 1000
CAPTURE_BASELINES = (
    "fold-no-pair-or-face",
    "fold-no-pair-or-better",
    "fold-large-bet",
)

#: The fields the capture holds, in its own order, exactly as this case reads them: TRNJ-12.1's
#: twenty-one, and not one fewer (`battery.md` §5, `records.md` §12).
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

#: The reproduction side of this case: the script whose child runs the capture's tuple under
#: the pin the capture was taken under, and the seconds this case allows it.  The 1,000-hand
#: run behind the capture costs minutes, so the timeout is generous and its expiry is a named
#: failure rather than a hang (`docs/L1/battery.md` §2, §5, D-36).
SCRIPT = os.path.join(_HERE, "_greedy_sample_capture.py")
CHILD_TIMEOUT = 1800

#: The pin the capture was taken under.  Every other variable -- `PYPOKER_CHECKPOINT_ROOT`
#: first among them, because the child writes its checkpoints there and the capture's
#: `checkpoints` block is relativised against it -- is inherited from this session
#: (`docs/L3/engine/stream.md` §1, `docs/L3/training/guardrails.md` G20, D-33).
PINNED_HASH_SEED = "0"


def capture_configuration():
    """The exact configuration the capture was taken from (`battery.md` §5, `greedy.md` §1).

    One variant of the naive stack at width 8 and depth 1, an empty version window, one seed,
    1,000 hands, the live table and the cpu, and **no `game` key**: the run resolves the
    catalogue's default shape, `fixed-limit-20`, which is the shape whose block must not move.
    The pool declares the three folding baselines beside the anchor three `build_pool` pins
    unconditionally, which is what makes its membership six members (`records.md` §8, D-21).
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

    A 1,000-hand run costs minutes and the case reads one record, so the record is built once
    and cached for the process (`docs/L1/battery.md` §2, `docs/L2/training/loop.md` §3).  It now
    runs in the pinned child `_greedy_sample_capture.py`, which loads this module and calls this
    function, so the case reads a child's summary and never an in-process run
    (`docs/L1/battery.md` §5, `guardrails.md` G20, D-33).
    """
    if "record" not in _RUNS:
        _RUNS["record"] = J.run(
            capture_configuration(), seeds=[CAPTURE_SEED], budget=CAPTURE_BUDGET
        )
    return _RUNS["record"]


class GreedySampleCaptureCase(J.JoinCase):
    """TRNJ-13.1 -- one 1,000-hand run against its pre-change capture."""

    def child_summary(self):
        """One pinned child's summary of the captured tuple (`greedy.md` §5, D-33).

        The child is `_greedy_sample_capture.py`: it runs the tuple this module states once,
        summarises the record with the capture's own readers and writes that summary to the
        path it is handed, so what this case compares is a fresh run and not the fixture
        (`battery.md` §5, `checkpoints.md` §2, D-36).  `PYTHONHASHSEED` is set to the
        capture's own pin and every other variable, `PYPOKER_CHECKPOINT_ROOT` first among
        them, is inherited from this session, because the child's artefacts must land under
        the same write root the capture's `checkpoints` block is relativised against
        (`write-root.md` §1, §3, `guardrails.md` G20, D-33).
        """
        out = os.path.join(self.scratch(), "greedy-sample-summary.json")
        environment = {**os.environ, "PYTHONHASHSEED": PINNED_HASH_SEED}
        try:
            finished = subprocess.run(
                [sys.executable, SCRIPT, out],
                cwd=J.ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=CHILD_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            self.fail(
                "the pinned child must replay the 1,000-hand run within %r s and did not, so "
                "the capture is not reproduced rather than not measured (greedy.md §1, §5, "
                "battery.md §5, D-36)" % (CHILD_TIMEOUT,)
            )
        self.assertEqual(
            finished.returncode,
            0,
            "the pinned child must replay the captured tuple and write its summary, because "
            "this case is a measurement of one run and not of a fixture (greedy.md §5, "
            "battery.md §5, D-36); it exited %r and said %r"
            % (finished.returncode, (finished.stderr or "")[-4000:]),
        )
        self.assertTrue(
            os.path.exists(out),
            "the child must write the summary it was handed a path for, so what is compared "
            "below is its run (battery.md §5): its stdout was %r and its stderr %r"
            % ((finished.stdout or "")[-2000:], (finished.stderr or "")[-2000:]),
        )
        with open(out, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_trnj_13_1_the_sampled_pass_reproduces_the_pre_change_run(self):
        """TRNJ-13.1 below the bound the sample rule is the identity, measured against the capture.

        D-36 made the pass play `min(budget, 2,000)` hands of the run's own hands, and
        `greedy.md` §1 states the requirement that fixes its form: at or under 2,000 hands the
        rule must **reduce to the identity**, so a run at or under the bound reproduces its
        pre-change block.  `shapes.md` §5 states the same constraint for every widening —
        "every widening's absence reproduces today's value" — and `battery.md` §5 fixes that
        such a claim is judged by a record and not by a sentence.  So the capture is one
        1,000-hand run's twenty-one-field summary taken before the rule existed, this case has
        that tuple replayed once by the **pinned child** `_greedy_sample_capture.py` — which
        summarises the record with the **capture's own readers** — and the two summaries are
        compared field by field: the record's key set, its seven families, its pool and
        baseline rows, its curves, its `greedy` block, its parameter band, its cost facts' key
        sets, the whole checkpoint listing with every container's member digests, and the
        header without its own checkpoint list.  A differing field is a defect in the sample
        rule and is reported with both values, never absorbed by a tolerance (`records.md` §12,
        §15, `greedy.md` §1, §4, §5, `sizing.md` §4, ASM-38, D-36).

        What it proves is exactly the pass's hand count: `hands` is `min(1,000, 2,000)`, the
        budget, so the block — and with it the curves, the parameters, the header and every
        checkpoint member digest — is the pre-change value field for field, and the child's
        summary equalling the fixture **is** that measurement rather than a preamble to it.
        The caveat is in the module docstring and is stated rather than hidden: the captured
        pool draws the `oracle`, whose `engine.equity` estimate is hash-order sensitive across
        processes, so this is a **pinned-interpreter reproduction** — the child carries
        `PYTHONHASHSEED=0`, the capture's own pin — and it is green whatever the runner's
        environment (`docs/L3/engine/stream.md` §1, `training/guardrails.md` G20,
        `docs/L3/training/greedy.md` §5, `battery.md` §5, D-33).
        """
        with open(CAPTURE, "rb") as handle:
            raw = handle.read()
        self.assertEqual(
            len(raw),
            CAPTURE_BYTES,
            "the capture this case reads is the 871,982-byte file taken before the sample "
            "rule landed, and it is never regenerated (greedy.md §1, §5, battery.md §5): %r "
            "bytes" % (len(raw),),
        )
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            CAPTURE_SHA256,
            "and it is byte-identical to that capture: a fixture edited to match a changed "
            "run would make this case measure nothing (battery.md §5, D-6, D-36): %r"
            % (hashlib.sha256(raw).hexdigest(),),
        )
        capture = json.loads(raw.decode("utf-8"))
        self.assertEqual(
            sorted(str(key) for key in capture),
            sorted(CAPTURE_FIELDS),
            "the capture holds exactly the twenty-one fields this case compares, so no field "
            "of it is read past or left unread (`battery.md` §5, `records.md` §12): %r"
            % (sorted(str(key) for key in capture),),
        )
        # The capture is a *sampled* pass whose sample is the whole budget: at 1,000 hands the
        # rule is the identity, which is the case this fixture exists to hold (greedy.md §1,
        # §4, D-36).
        for variant, per_variant in dict(capture["greedy"]).items():
            for seed, block in dict(per_variant).items():
                self.assertEqual(
                    int(block["hands"]),
                    CAPTURE_BUDGET,
                    "the captured pass of %r at seed %r played the run's own sample of %r "
                    "hands — min(budget, 2,000) is the budget at a 1,000-hand run — so the "
                    "block compared below is the identity case and not a shortened one "
                    "(greedy.md §1, §4, sizing.md §4, D-36): %r"
                    % (variant, seed, CAPTURE_BUDGET, block["hands"]),
                )
                self.assertEqual(
                    len(list(block["net_chips"])),
                    CAPTURE_BUDGET,
                    "and it carries one net chip delta per hand of that sample "
                    "(records.md §15, ASM-23): %r" % (len(list(block["net_chips"])),),
                )
        current = self.child_summary()
        self.assertEqual(
            sorted(str(key) for key in current),
            sorted(CAPTURE_FIELDS),
            "and the summary the pinned child rebuilds holds the same fields and no others, "
            "so the comparison below is the whole of what the capture states (`battery.md` "
            "§5, `records.md` §12): %r" % (sorted(str(key) for key in current),),
        )
        for field in CAPTURE_FIELDS:
            self.assertIn(
                field,
                current,
                "the pinned child's summary of the 1,000-hand run must still state the %r "
                "field the capture holds, because below the bound the sample rule is the "
                "identity (greedy.md §1, §4, battery.md §5, D-36): %r"
                % (field, sorted(current)),
            )
            self.assertEqual(
                current[field],
                capture[field],
                "the %r field of the pinned child's summary of a 1,000-hand run must be the "
                "captured value taken before the sample rule landed — min(budget, 2,000) is "
                "the budget at this size, so nothing may move and this reading is what makes "
                "that a measurement rather than a claim (greedy.md §1, §4, §5, shapes.md §5, "
                "battery.md §5, ASM-38, D-36): current %r against captured %r"
                % (field, current[field], capture[field]),
            )


if __name__ == "__main__":
    unittest.main()
