"""The reproduction side of TRNJ-13.1: the captured tuple run in a pinned child.

This script is not a battery and holds no case.  It is the **child** half of
`test_greedy_sample.py::TRNJ-13.1`: the case hands it one path, it runs the tuple that module
states, summarises the record with the readers that capture was taken with, and writes that
summary where it was told to.  So it is run by a child interpreter pinned to
**`PYTHONHASHSEED=0`**, the pin the capture `_greedy_sample_baseline.json` was taken under,
because the captured pool pins D-6's three anchors and declares D-21's three folding baselines
beside them, six members with the `oracle` at index 2, and the `oracle` decides by comparing
`engine.equity`'s sampled estimate with the pot odds.  That estimate is claimed to be "a
function of `(decision, seed, samples)` and of nothing else" (`docs/L3/engine/stream.md` §1) and
is not: its sampling universe is ordered by a set, so two processes of one build at one seed
disagree and an oracle draw near its threshold flips.  The guarantee that leaves is
`training/guardrails.md` G20's -- a re-run reproduces "one build's, one pinned interpreter's"
result -- and this child is where the pin is applied (`docs/L3/engine/stream.md` §1,
`training/guardrails.md` G20, `docs/L3/training/greedy.md` §5, D-33, D-36).

**It sets nothing about the write root.**  `PYPOKER_CHECKPOINT_ROOT` -- the one ambient override
`docs/L2/training/write-root.md` §3-§4 gives a single command line -- is inherited from the case
that starts this child, so the run behind the summary writes its ten snapshots and its final
model under the same root this session's battery writes under, and under no other.  That is not
incidental: the capture's `checkpoints` block is **relativised** against that root and records
each container's decompressed member digests, so a child pointed at another root, or at
`<repo>/checkpoints`, would build a summary whose paths are not the capture's and whose
comparison measures a directory rather than a run (`docs/L2/training/write-root.md` §1, §3,
`docs/L3/training/checkpoints.md` §2, `guardrails.md` G20).

**Neither the tuple nor the readers are restated here.**  The configuration, the seed, the
budget and the run cache are `test_greedy_sample.py`'s, and the twenty-one-field summary is
`test_default_baseline.py`'s -- the reader TRNJ-12.1 reads the *same* capture shape with.  Both
are loaded **by path under private names**, because a case module is not importable by its bare
name from a script that knows only its directory -- pytest imports it under the runner's own name
-- and because this repository's integration batteries do share the file name `_join_support.py`
and a bare import would hand this script another battery's helpers; a tuple or a reader restated
here would be a second statement of what the capture is and the comparison would no longer be
with it (`docs/L1/battery.md` §2, §5, D-13).
"""

import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

#: The private module names the two sibling files are loaded under: the repository's
#: integration batteries share file names, so nothing here is imported by its bare name
#: (`docs/L1/battery.md` §2, D-13).
_READERS_NAME = "training_default_baseline_case"
_CASE_NAME = "training_greedy_sample_case"


def _load(name, filename):
    """One sibling file, loaded by path under a private name (`battery.md` §2, D-13)."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def summary_of_one_run():
    """The captured tuple run once, summarised by the capture's own readers.

    `training.run(configuration, seeds=[7001], budget=1000)` -- the case's own tuple, seed and
    budget, called through its `capture_run` -- summarised into the twenty-one fields
    `_greedy_sample_baseline.json` holds, by the reader that capture was taken with
    (`docs/L1/battery.md` §5, `docs/L1/records.md` §12, `docs/L3/training/greedy.md` §5, D-36).
    """
    case = _load(_CASE_NAME, "test_greedy_sample.py")
    readers = _load(_READERS_NAME, "test_default_baseline.py")
    return readers.summary(case.capture_run())


def main(argv):
    """Write that summary to `argv[1]`, indented as the capture is and key order unsorted."""
    if len(argv) != 2:
        raise SystemExit(
            "_greedy_sample_capture.py writes one summary and needs exactly one path to "
            "write it to; it was given %r" % (argv[1:],)
        )
    with open(argv[1], "w", encoding="utf-8") as handle:
        json.dump(summary_of_one_run(), handle, indent=2, sort_keys=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
