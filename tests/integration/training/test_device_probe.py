"""The platform join -- TRNJ-10.

`docs/L2/training/devices.md` §1-§2 (Rev 4) and `docs/L2/training/surface.md` §6 fix three
things about `devices()`, and the third is the one no single module can check about itself:

* the record is `{available, default, gpu}` with `gpu` exactly `{available, name, reason}`,
  `available` beginning with `cpu` and `default` `cpu`;
* `gpu.available` is true only when a **read-write** open of a GPU device node succeeded
  *and* a backend reports the device usable -- "A read-only open is no evidence"
  (`devices.md` §2);
* "No backend is imported before a read-write open has succeeded, so a CPU-only platform
  pays for no framework import" (`devices.md` §2, `docs/L3/training/guardrails.md` G18).

Why this is an integration case and not a module one.  The third rule is a fact about the
*process*, not about the record: it is visible only in the import table of an interpreter
that has done nothing else, and a same-process case cannot see it, because the rest of this
battery has already imported the framework by the time any later case asks -- a run builds a
torch learner (`docs/L2/training/loop.md` §1 step 3).  So the case drives `devices()` in one
child interpreter and weighs its answer against two facts the child measured for itself,
before the call and without asking the module: whether its own `os.O_RDWR` open of the two
GPU nodes succeeded, and whether `torch` was in `sys.modules` before and after
(`docs/L1/gpu.md` §2, D-8, ASM-15).

Neither the expectation nor the assertion is read out of the implementation, so the case
asserts what holds either way and never one particular `reason` text: it passes inside this
workflow's sandbox, where the read-write open is denied `EACCES` and a plain `PermissionError`
is the whole symptom, and on a machine whose card a process can actually use, where the same
open succeeds and a backend reports the device (`docs/L2/training/devices.md` §2's four
situations, `strata/platform.md` Compute, D-17).

The case is written against `devices.md`'s contract and not against the probe this tree
carries today: it is red against a probe that opens the nodes read-only, which is the defect
`docs/L1/gpu.md` §2 records as routed for correction -- measured in this sandbox, both nodes
open `O_RDONLY` while a read-write open of either is denied `EACCES`, so a read-only probe
imports the framework and reports a cause it never measured.

The record's shape is the module battery's TRN-8.1-8.2 (`tests/training/test_devices.py`) in
one process; it is restated here only as the precondition of the cross-process claim, because
a record that will not cross a JSON boundary is not the plain-data mapping `surface.md` §1
requires.  What this case adds is the ordering rule, and `devices.md` §2's own vocabulary --
which of the four situations the platform is in -- is deliberately *not* asserted here: that
is one entry point's record read in one process, and its place is the module battery.
"""

import importlib.util
import json
import os
import subprocess
import sys
import unittest

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

#: The two nodes `devices.md` §2's measured case names, and the flag a driver opens them with.
GPU_NODES = ("/dev/kfd", "/dev/dri/renderD128")

#: The child prints its answer under this marker, so a line a driver writes to stdout or
#: stderr can never be mistaken for it -- a HIP runtime prints diagnostics of its own when
#: it reaches a device (`docs/L1/gpu.md` §2).
MARKER = "TRNJ-10 "


def child_program(nodes):
    """The child's program, for the nodes a probe would open.

    It measures the platform with its own syscalls *before* it calls the module, so the
    case's expectation is a fact about the machine and not a restatement of the probe:
    nothing here reads the module's reason, and the framework is imported by the child only
    when its own read-write open succeeded, so its presence after the call is the
    measurement rather than the child's own doing (`devices.md` §2).
    """
    return r'''
import json, os, sys

NODES = %(nodes)r

opens = {}
for node in NODES:
    if not os.path.exists(node):
        opens[node] = {"state": "absent"}
        continue
    try:
        handle = os.open(node, os.O_RDWR)
    except OSError as error:
        opens[node] = {"state": "denied", "errno": error.errno,
                       "class": type(error).__name__, "message": str(error)}
    else:
        os.close(handle)
        opens[node] = {"state": "opened"}

import training

before = "torch" in sys.modules
record = training.devices()
after = "torch" in sys.modules
again = training.devices()

backend = None
if any(entry["state"] == "opened" for entry in opens.values()):
    try:
        import torch
    except Exception as error:
        backend = {"importable": False, "error": type(error).__name__}
    else:
        backend = {"importable": True,
                   "available": bool(torch.cuda.is_available()),
                   "count": int(torch.cuda.device_count()),
                   "version": str(torch.__version__),
                   "hip": None if torch.version.hip is None
                          else str(torch.version.hip)}

print(%(marker)r + json.dumps({"opens": opens, "before": before, "after": after,
                              "backend": backend, "record": record,
                              "again": again}))
''' % {"nodes": GPU_NODES, "marker": MARKER}


class DeviceProbeJoin(J.JoinCase):
    """TRNJ-10 -- the probe measures a read-write open, and imports no backend before it."""

    def measurement(self):
        """One child interpreter's platform facts and the two records it returned.

        The child runs with this tree's `src/` on `PYTHONPATH` from the repository root,
        the way the batteries are run (`docs/L1/battery.md` §2), so it imports the
        `training` package this case is about and nothing the battery has already loaded.
        """
        environment = dict(os.environ)
        inherited = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = (
            J.SRC if not inherited else J.SRC + os.pathsep + inherited
        )
        try:
            finished = subprocess.run(
                [sys.executable, "-c", child_program(GPU_NODES)],
                cwd=J.ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            self.fail(
                "the child interpreter did not answer within 300 s: `devices()` is a "
                "probe of the platform and must not block on it "
                "(docs/L2/training/devices.md §2, D-8)"
            )
        self.assertEqual(
            finished.returncode,
            0,
            "the child must import `training` and return one record without an error, "
            "because the probe is a fact about the platform and not a caller's "
            "exception (docs/L2/training/devices.md §1-§2); it exited %r and said %r"
            % (finished.returncode, (finished.stderr or finished.stdout)[-3000:]),
        )
        answered = [
            line for line in finished.stdout.splitlines() if line.startswith(MARKER)
        ]
        self.assertTrue(
            answered,
            "the child must print the record it read under the case's marker; its "
            "stdout was %r and its stderr %r"
            % (finished.stdout[-2000:], (finished.stderr or "")[-2000:]),
        )
        measured = json.loads(answered[-1][len(MARKER):])
        self.assertEqual(
            len(answered),
            1,
            "the child prints one answer line, so what this case reads is what the "
            "interpreter returned: %r" % (answered,),
        )
        return measured

    def test_trnj_10_1_the_probe_measures_a_read_write_open_before_it_imports(self):
        """TRNJ-10.1 `devices()` answers the platform, and imports no backend before a read-write open succeeds.

        Both directions are asserted, and neither is a skip: on a platform where no read-write
        open succeeds the record must say unavailable and the framework must still be absent
        from the import table, while on a platform where one does the record's `available`
        must be the backend's report and `available` must still be `cpu` alone
        (`docs/L2/training/devices.md` §1-§2, `docs/L1/gpu.md` §3, D-8, ASM-15).
        """
        measured = self.measurement()
        record = measured["record"]
        gpu = record["gpu"]

        # The record crossed a JSON boundary to get here, so what this case reads is the
        # plain data `surface.md` §1 requires and not a live object dressed as a mapping.
        self.assertEqual(
            set(record),
            {"available", "default", "gpu"},
            "the record is read under `available`, `default` and `gpu` and under no "
            "other key (docs/L2/training/devices.md §1, surface.md §6): %r"
            % (sorted(record),),
        )
        self.assertEqual(
            set(gpu),
            {"available", "name", "reason"},
            "`gpu` is exactly `{available, name, reason}` (docs/L2/training/devices.md "
            "§1): %r" % (sorted(gpu),),
        )
        available = [str(name) for name in record["available"]]
        self.assertEqual(
            available[0],
            "cpu",
            "`cpu` is first in `available` and always present, because every rung and "
            "both table budgets run on it (docs/L2/training/devices.md §1, "
            "docs/L1/protocol.md §6, ASM-15): %r" % (available,),
        )
        self.assertIn(
            "cpu",
            available,
            "`available` names the devices `run` accepts, and `cpu` is always one of "
            "them (docs/L2/training/devices.md §1): %r" % (available,),
        )
        self.assertEqual(
            str(record["default"]),
            "cpu",
            "the default is `cpu`, always -- the device an omitted argument resolves to "
            "(docs/L2/training/devices.md §1, surface.md §6, D-8)",
        )
        self.assertIsInstance(
            gpu["available"],
            bool,
            "`gpu.available` is a boolean and not a truthy object (docs/L2/training/"
            "devices.md §1): %r" % (gpu["available"],),
        )
        self.assertTrue(
            gpu["name"] is None or isinstance(gpu["name"], str),
            "`gpu.name` is the hardware string a backend reports and `None` otherwise, "
            "never a guess (docs/L2/training/devices.md §1, D-8): %r" % (gpu["name"],),
        )
        self.assertIsInstance(
            gpu["reason"],
            str,
            "a `reason` string is present whichever way the platform answers, because a "
            "reader quotes it for \"why was this run on CPU\" (docs/L2/training/"
            "devices.md §1, docs/L1/protocol.md §6): %r" % (gpu["reason"],),
        )
        self.assertEqual(
            J.canonical(record),
            J.canonical(measured["again"]),
            "two calls on one platform agree, because the answer depends on the platform "
            "and not on the caller (docs/L2/training/devices.md §1, surface.md §6)",
        )
        self.assertFalse(
            measured["before"],
            "the framework must not be in the import table when `devices()` is called, "
            "or the rule that no backend is imported before a read-write open cannot be "
            "measured at all (docs/L2/training/devices.md §2, "
            "docs/L3/training/guardrails.md G18)",
        )

        opens = measured["opens"]
        opened = [node for node, entry in opens.items() if entry["state"] == "opened"]

        if not opened:
            # The platform denied the read-write open, or carries no node: the first of
            # the four situations, and a control open of `/dev/urandom` is denied the same
            # way (docs/L2/training/devices.md §2, measured).
            self.assertFalse(
                gpu["available"],
                "no read-write open of a GPU node succeeded here (%r), and a GPU is "
                "reported available only when one does (docs/L2/training/devices.md "
                "§2): %r" % (opens, gpu,),
            )
            self.assertFalse(
                measured["after"],
                "no backend is imported before a read-write open has succeeded, so a "
                "platform whose nodes are absent or whose open is denied pays for no "
                "framework import (docs/L2/training/devices.md §2, "
                "docs/L3/training/guardrails.md G18); the read-write opens measured %r, "
                "and `torch` was in `sys.modules` after the call: %r"
                % (opens, gpu,),
            )
            self.assertIsNone(
                gpu["name"],
                "no backend ran, so no hardware string was reported and `gpu.name` is "
                "`None`, never a guess (docs/L2/training/devices.md §1): %r"
                % (gpu["name"],),
            )
            reason = gpu["reason"].lower()
            self.assertTrue(
                reason.strip(),
                "an unavailable device states in `reason` which operation failed, so it "
                "is a measurement and not a shrug (docs/L2/training/devices.md §2): %r"
                % (gpu["reason"],),
            )
            self.assertTrue(
                any(part in reason
                    for part in ("open", "o_rdwr", "read-write", "read/write",
                                 "/dev/", "stat", "node")),
                "the reason names the operation the probe attempted -- the open, the flag "
                "it opened with, or the node it tried -- rather than a cause it never "
                "measured (docs/L2/training/devices.md §2, docs/L1/gpu.md §2); it read "
                "%r" % (gpu["reason"],),
            )
            return

        # This machine's card opens, so the answer is the backend's to give and the probe
        # had to consult one (docs/L2/training/devices.md §2).
        backend = measured["backend"] or {}
        if not backend.get("importable"):
            # A node opened and the backend would not load: no backend reported the device
            # usable, so it is not available, and the reason states that situation.
            self.assertFalse(
                gpu["available"],
                "a read-write open of %r succeeded but no backend could be consulted "
                "(%r), and a GPU is reported available only when one reports it usable "
                "(docs/L2/training/devices.md §2): %r" % (opened, backend, gpu,),
            )
            self.assertTrue(
                gpu["reason"].strip(),
                "the record states the backend's absence in `reason` (docs/L2/training/"
                "devices.md §2): %r" % (gpu["reason"],),
            )
            return
        self.assertTrue(
            measured["after"],
            "a node opened read-write here (%r) and the backend loads, so `devices()` "
            "must consult it before it can call the device usable (docs/L2/training/"
            "devices.md §2): %r" % (opened, gpu,),
        )
        self.assertIn(
            "version",
            backend,
            "the child records the backend it consulted: %r" % (backend,),
        )
        if backend.get("available"):
            self.assertTrue(
                gpu["available"],
                "a read-write open of %r succeeded and torch reports the device usable "
                "(%r), which is the one condition under which `gpu.available` is true "
                "(docs/L2/training/devices.md §2): %r"
                % (opened, backend, gpu,),
            )
            self.assertEqual(
                sorted(available),
                ["cpu"],
                "a reachable GPU adds no name to `available`, which names what `run` "
                "accepts and never what the machine has -- nothing in the tree uses a "
                "device, and `run` refuses a name this list omits (docs/L2/training/"
                "devices.md §1, docs/L1/gpu.md §3, D-8): %r" % (available,),
            )
            self.assertTrue(
                str(gpu["name"] or "").strip(),
                "`gpu.name` is the hardware string the backend reports when the device "
                "is usable, never `None` (docs/L2/training/devices.md §1, D-8): %r"
                % (gpu["name"],),
            )
            return

        self.assertFalse(
            gpu["available"],
            "a node opened read-write but the backend reported no usable device (%r) -- "
            "the fourth situation -- and a backend's refusal is not evidence of a usable "
            "device (docs/L2/training/devices.md §2): %r" % (backend, gpu,),
        )
        self.assertTrue(
            gpu["reason"].strip(),
            "the record states the backend's refusal in `reason`, because the fourth "
            "situation is still a measurement (docs/L2/training/devices.md §2): %r"
            % (gpu["reason"],),
        )


if __name__ == "__main__":
    unittest.main()
