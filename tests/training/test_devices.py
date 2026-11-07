"""TRN-8 — the platform: `devices()`.

Drives `docs/L3/training/devices.md` (Rev 3) §1-§3 and `docs/L2/training/surface.md` §6:
the record's three keys, `cpu` first in `available` and as `default`, the probe's record
with a `reason` a reader can quote, two calls that agree, and the identity between the
names `devices()` lists and the names `run` accepts (D-8, `strata/platform.md`).

The probe measures the **read-write** open a driver performs (`devices.md` §2,
`docs/L3/training/guardrails.md` G18), and each of its texts is injected in this process:
`os.open` and `os.close` are replaced together and the backend is replaced through its
declared seam, so the sandbox's denial, an absent node, another errno, a permissions
fault, a backend that declines and a backend that is not importable are asserted without a
GPU, beside one case that reports a reachable GPU through a backend stub (TRN-8.4-8.10).
No case depends on the machine it runs on: the live cases (TRN-8.1-8.3) assert what holds
either way, and every injected case clears the probe cache on both sides of itself, so no
injected record leaks into a later case.
"""

import errno
import os
import types
import unittest
from unittest import mock

from _training_support import (
    INVENTED_DEVICE,
    RUN_SEED,
    TINY_BUDGET,
    TrainingCase,
    as_mapping,
    as_sequence,
    as_text,
    internal_module,
    repeated_run,
    training,
)

#: The nodes `devices.md` §2 names as the probe's, `/dev/kfd` first.
GPU_NODES = ("/dev/kfd", "/dev/dri/renderD128")

#: The fake descriptor a patched `os.open` hands back; `os.close` is patched beside it.
DESCRIPTOR = 7

#: The hardware string a usable backend stub reports: this module holds none of its own.
HARDWARE = "AMD Radeon RX 9070 XT"


# --------------------------------------------------------------------------
# The opens a case injects: `os.open`'s side effect, one per situation
# --------------------------------------------------------------------------
def read_write_opens(path, flags):
    """`os.open` that opens read-write — the operation the probe measures — and nothing else.

    The read-write open of every node succeeds here, so the backend is the only thing left
    to consult, while a read-only open is denied: a probe that measured the wrong
    operation could not reach the backend through this seam (devices.md §2, G18).
    """
    if (flags & os.O_ACCMODE) == os.O_RDWR:
        return DESCRIPTOR
    raise PermissionError(errno.EACCES, "Permission denied", path)


def read_write_denied(path, flags):
    """The sandbox's denial: read-write is denied `EACCES`, read-only of the same node opens.

    A read-only flag is `O_RDONLY`, whose value is `0`, so the two modes are told apart
    through `O_ACCMODE` and never by comparing the flags with `O_RDONLY` (devices.md §2).
    """
    if (flags & os.O_ACCMODE) == os.O_RDWR:
        raise PermissionError(errno.EACCES, "Permission denied", path)
    return DESCRIPTOR


def open_denied(path, flags):
    """Both opens denied `EACCES`: a permissions fault, not the sandbox's split (§2)."""
    del flags

    raise PermissionError(errno.EACCES, "Permission denied", path)


def open_absent(path, flags):
    """The node is not there: `os.open` raises `ENOENT` (devices.md §2)."""
    del flags

    raise FileNotFoundError(errno.ENOENT, "No such file or directory", path)


def open_fails(path, flags):
    """A read-write open that fails with another errno — `ENODEV` here (devices.md §2)."""
    del flags

    raise OSError(errno.ENODEV, "No such device", path)


class DevicesTest(TrainingCase):
    """TRN-8 — the record `devices()` returns, and the probe that fills it."""

    def devices(self):
        """The live catalogue, read from the platform this battery runs on."""
        return as_mapping(training().devices(), "the device catalogue")

    def probe(self, opener, backend):
        """`devices()["gpu"]` with `os.open`, `os.close` and the backend seam replaced.

        `os.open` and `os.close` are patched **together**, because a patched `os.open`
        returns a fake descriptor that the real `os.close` would close as an unrelated
        file descriptor of this process. The backend is replaced through its declared
        seam only, and the probe cache is cleared on both sides of the measurement, so an
        injected record is never read by a live case (devices.md §2, G18).
        """
        module = internal_module("devices")
        module._PROBED.clear()
        try:
            with mock.patch("os.open", side_effect=opener), mock.patch("os.close"):
                with mock.patch.object(module, "_backend", backend):
                    return as_mapping(training().devices()["gpu"], "'gpu'")
        finally:
            module._PROBED.clear()

    def unused_backend(self, label):
        """A backend seam that must not be consulted at all (devices.md §2, G18)."""
        return mock.Mock(
            side_effect=AssertionError(
                "%s: no backend may be reached before a read-write open has succeeded "
                "(devices.md §2, G18)" % (label,)
            )
        )

    def reason(self, opener, backend, label):
        """The `reason` the injected situation produces, as one string."""
        return as_text(self.probe(opener, backend)["reason"], "%s's 'reason'" % (label,))

    def sandbox_reason(self, label):
        """The reason the sandbox's denial produces, for the cases that compare theirs."""
        return self.reason(read_write_denied, self.unused_backend(label), label)

    def absent_reason(self, label):
        """The reason an absent node produces, for the cases that compare theirs."""
        return self.reason(open_absent, self.unused_backend(label), label)

    def test_trn_8_1_the_catalogue_names_cpu_first_and_defaults_to_it(self):
        """TRN-8.1 `devices()` returns `{available, default, gpu}`, `available` is a sequence of names whose first is `cpu`, and `default` is `cpu` (devices.md §1, surface.md §6, D-8, FAM-1.42)."""
        catalogue = self.devices()
        self.assertEqual(
            set(catalogue),
            {"available", "default", "gpu"},
            "the record is read under `available`, `default` and `gpu` (devices.md §1, "
            "surface.md §6): %r" % (sorted(catalogue),),
        )
        available = [
            as_text(name, "a device name")
            for name in as_sequence(catalogue["available"], "'available'")
        ]
        self.assertIn(
            "cpu",
            available,
            "cpu is always present, because every rung and both table budgets run on it "
            "(devices.md §1, surface.md §6, ASM-15): %r" % (available,),
        )
        self.assertEqual(
            available[0],
            "cpu",
            "cpu is always first in `available` (devices.md §1): %r" % (available,),
        )
        self.assertEqual(
            as_text(catalogue["default"], "default"),
            "cpu",
            "the default is cpu, always — the device an omitted argument resolves to "
            "(devices.md §1, loop.md §5, D-8)",
        )
        self.assertEqual(
            len(set(available)),
            len(available),
            "a device name is listed once: %r" % (available,),
        )
        self.assertEqual(
            self.devices(),
            catalogue,
            "two calls on one platform agree, because the answer depends on the platform "
            "and not on the caller (devices.md §1, surface.md §6, FAM-1.42)",
        )

    def test_trn_8_2_the_gpu_record_names_the_node_it_measured(self):
        """TRN-8.2 `gpu` is `{available, name, reason}` with a real `bool`, a `str` or `None` name, and a `reason` naming the node it measured when the device is unavailable (devices.md §1-§2, surface.md §6)."""
        gpu = as_mapping(self.devices()["gpu"], "'gpu'")
        self.assertEqual(
            set(gpu),
            {"available", "name", "reason"},
            "the gpu record is `{available, name, reason}` (devices.md §1, surface.md "
            "§6): %r" % (sorted(gpu),),
        )
        self.assertIsInstance(
            gpu["available"],
            bool,
            "`gpu.available` is a boolean and not a truthy object (devices.md §1, "
            "devices.md §2's probe): %r" % (gpu["available"],),
        )
        self.assertTrue(
            gpu["name"] is None or isinstance(gpu["name"], str),
            "`gpu.name` is the hardware string the backend reports and None otherwise, "
            "never a guess (devices.md §1-§2): %r" % (gpu["name"],),
        )
        reason = as_text(gpu["reason"], "'gpu' reason")
        self.assertTrue(
            reason.strip(),
            "a `reason` string is present whichever way the platform answers, because a "
            "reader quotes it for \"why was this run on CPU\" (devices.md §1-§2, "
            "strata/platform.md): %r" % (reason,),
        )
        if gpu["available"]:
            self.assertTrue(
                isinstance(gpu["name"], str) and gpu["name"].strip(),
                "a device reported usable is named by the backend, so `gpu.name` is a "
                "non-empty string and never None (devices.md §2, D-8): %r"
                % (gpu["name"],),
            )
        else:
            self.assertTrue(
                any(node in reason for node in GPU_NODES),
                "an unavailable device states in `reason` which node the probe measured "
                "— `/dev/kfd` or `/dev/dri/renderD128` — because §2's clause list names "
                "every node examined, so a reader never infers the node from the "
                "situation (devices.md §2): %r" % (reason,),
            )
        self.assertIn(
            "cpu",
            [as_text(name, "a device name") for name in
             as_sequence(self.devices()["available"], "'available'")],
            "no case requires a GPU: cpu is available whatever the probe answers "
            "(devices.md §1, D-8, ASM-15)",
        )

    def test_trn_8_3_available_is_exactly_the_names_run_accepts(self):
        """TRN-8.3 `available` is the names `run` accepts: a device it lists is accepted and recorded, and a name it does not list is refused naming it (devices.md §1, §3, loop.md §5-§6, D-8)."""
        catalogue = self.devices()
        available = [
            as_text(name, "a device name")
            for name in as_sequence(catalogue["available"], "'available'")
        ]
        record = as_mapping(repeated_run(), "a run record at the default device")
        self.assertEqual(
            as_text(record["device"], "a run record's device"),
            "cpu",
            "a run naming a listed device records the device it used (devices.md §3, "
            "loop.md §3, D-8): %r" % (record["device"],),
        )
        self.assertIn(
            as_text(record["device"], "a run record's device"),
            available,
            "the device a run records is one devices() lists, so a GPU run and a CPU run "
            "are never confused (devices.md §3, protocol.md §6)",
        )
        self.assertNotIn(
            INVENTED_DEVICE,
            available,
            "the invented device name is not one the platform lists, so it is the refusal "
            "below and not an accepted name (devices.md §1)",
        )
        self.refuse(
            lambda: training().run(
                "R1", seeds=(RUN_SEED,), budget=TINY_BUDGET, device=INVENTED_DEVICE
            ),
            "UnknownDevice",
            groups=((INVENTED_DEVICE,), ("cpu",)),
            label="run at a device devices() does not list",
        )

    def test_trn_8_4_a_read_write_denial_read_only_survives_is_the_sandbox(self):
        """TRN-8.4 A read-write open denied `EACCES` while a control read-only open succeeds is the sandbox's denial, and no backend is consulted (devices.md §2, G18)."""
        backend = self.unused_backend("TRN-8.4")
        gpu = self.probe(read_write_denied, backend)
        self.assertFalse(
            gpu["available"],
            "the read-write open, and only that one, was denied, so no GPU is reported "
            "usable (devices.md §2): %r" % (gpu,),
        )
        self.assertIsNone(
            gpu["name"],
            "no backend ran, so no hardware string was reported and `gpu.name` is None "
            "(devices.md §1-§2): %r" % (gpu["name"],),
        )
        reason = as_text(gpu["reason"], "'gpu' reason")
        for token in ("read-write", "denied", "read-only", "EACCES", "13", "sandbox"):
            self.assertIn(
                token,
                reason,
                "the sandbox's denial states the operation, its errno with the number, "
                "the control open that succeeded and the situation it is in — `%s` is "
                "missing (devices.md §2): %r" % (token, reason),
            )
        self.assertNotIn(
            "also denied",
            reason,
            "the control read-only open succeeded, so the reason states no second denial "
            "— a permissions fault is another text (devices.md §2): %r" % (reason,),
        )
        backend.assert_not_called()

    def test_trn_8_5_an_absent_node_is_absent_and_not_a_denial(self):
        """TRN-8.5 An `ENOENT` open says the node is absent with `ENOENT` and `2`, and not the sandbox's denial (devices.md §2)."""
        backend = self.unused_backend("TRN-8.5")
        gpu = self.probe(open_absent, backend)
        self.assertFalse(
            gpu["available"],
            "no node opened, so no GPU is available (devices.md §2): %r" % (gpu,),
        )
        self.assertIsNone(
            gpu["name"],
            "no backend ran, so `gpu.name` is None (devices.md §1-§2): %r"
            % (gpu["name"],),
        )
        reason = as_text(gpu["reason"], "'gpu' reason")
        for token in ("absent", "ENOENT", "2"):
            self.assertIn(
                token,
                reason,
                "an absent node is named as absent with the errno and its number, never "
                "as a denial — `%s` is missing (devices.md §2): %r" % (token, reason),
            )
        self.assertNotEqual(
            reason,
            self.sandbox_reason("TRN-8.5's sandbox control"),
            "an absent node and the sandbox's denial never share one reason, or the "
            "answer is no measurement (devices.md §2, docs/L2/training/devices.md §2): "
            "%r" % (reason,),
        )
        backend.assert_not_called()

    def test_trn_8_6_another_errno_is_named_and_is_no_sandbox(self):
        """TRN-8.6 Any other `OSError` reports its own errno name and number — `ENODEV` and `19` — which is neither the sandbox nor an absence (devices.md §2)."""
        backend = self.unused_backend("TRN-8.6")
        gpu = self.probe(open_fails, backend)
        self.assertFalse(
            gpu["available"],
            "no node opened, so no GPU is available (devices.md §2): %r" % (gpu,),
        )
        self.assertIsNone(
            gpu["name"],
            "no backend ran, so `gpu.name` is None (devices.md §1-§2): %r"
            % (gpu["name"],),
        )
        reason = as_text(gpu["reason"], "'gpu' reason")
        self.assertIn(
            "ENODEV",
            reason,
            "another errno is reported by its own name (devices.md §2): %r" % (reason,),
        )
        self.assertIn(
            "19",
            reason,
            "and with its number, never a bare code (devices.md §2): %r" % (reason,),
        )
        self.assertNotIn(
            "sandbox",
            reason,
            "another errno is not the sandbox's denial, and the reason says so by not "
            "claiming it (devices.md §2): %r" % (reason,),
        )
        self.assertNotEqual(
            reason,
            self.sandbox_reason("TRN-8.6's sandbox control"),
            "another errno and the sandbox's denial never share one reason (devices.md "
            "§2): %r" % (reason,),
        )
        self.assertNotEqual(
            reason,
            self.absent_reason("TRN-8.6's absent control"),
            "another errno and an absent node never share one reason (devices.md §2): "
            "%r" % (reason,),
        )
        backend.assert_not_called()

    def test_trn_8_7_a_backend_that_declines_reports_no_usable_device(self):
        """TRN-8.7 A node that opens read-write while the backend reports no usable device is unavailable with that text, and the backend is never asked to name it (devices.md §2)."""
        naming = mock.Mock(return_value=HARDWARE)
        backend = mock.Mock(
            return_value=types.SimpleNamespace(
                cuda=types.SimpleNamespace(
                    is_available=lambda: False, get_device_name=naming
                )
            )
        )
        gpu = self.probe(read_write_opens, backend)
        self.assertFalse(
            gpu["available"],
            "`gpu.available` is true only when a read-write open succeeded **and** the "
            "backend reports the device usable, and here it declines (devices.md §2): "
            "%r" % (gpu,),
        )
        self.assertIsNone(
            gpu["name"],
            "the backend declined, so no device was named and `gpu.name` is None "
            "(devices.md §1-§2): %r" % (gpu["name"],),
        )
        reason = as_text(gpu["reason"], "'gpu' reason")
        self.assertIn(
            "read-write",
            reason,
            "the reason states the operation that did succeed, so the decline is read "
            "and not inferred (devices.md §2): %r" % (reason,),
        )
        self.assertIn(
            "no usable device",
            reason,
            "a backend that declines is reported in those words (devices.md §2): %r"
            % (reason,),
        )
        self.assertNotIn(
            "denied",
            reason,
            "the read-write open succeeded, so the reason claims no denial (devices.md "
            "§2): %r" % (reason,),
        )
        naming.assert_not_called()

    def test_trn_8_8_a_reachable_gpu_is_named_and_adds_no_device_name(self):
        """TRN-8.8 A read-write open plus a backend that reports the device usable yields `available` true and the backend's own hardware string, while `available` stays `["cpu"]` (devices.md §1-§2, §3)."""
        naming = mock.Mock(return_value=HARDWARE)
        backend = mock.Mock(
            return_value=types.SimpleNamespace(
                cuda=types.SimpleNamespace(
                    is_available=lambda: True, get_device_name=naming
                )
            )
        )
        gpu = self.probe(read_write_opens, backend)
        self.assertTrue(
            gpu["available"],
            "a read-write open succeeded and the backend reports the device usable, "
            "which is the one condition under which `gpu.available` is true (devices.md "
            "§2): %r" % (gpu,),
        )
        self.assertEqual(
            gpu["name"],
            HARDWARE,
            "`gpu.name` is the backend's `get_device_name(0)` and never a string this "
            "module carries, because the module holds no hardware string (devices.md §1-"
            "§2, D-8): %r" % (gpu["name"],),
        )
        naming.assert_called_once_with(0)
        self.assertIsInstance(
            gpu["reason"],
            str,
            "the record carries a `reason` string whichever way the platform answers "
            "(devices.md §1-§2): %r" % (gpu["reason"],),
        )
        self.assertTrue(
            gpu["reason"].strip(),
            "and it is a string a reader can quote (devices.md §1-§2): %r"
            % (gpu["reason"],),
        )
        available = [
            as_text(name, "a device name")
            for name in as_sequence(
                training().devices()["available"], "'available'"
            )
        ]
        self.assertEqual(
            available,
            ["cpu"],
            "a reachable GPU adds no name to `available`, which names what `run` accepts "
            "and never what the machine has (devices.md §1, docs/L2/training/surface.md "
            "§6, docs/L1/gpu.md §3, D-8): %r" % (available,),
        )

    def test_trn_8_9_a_permissions_fault_is_not_the_sandbox(self):
        """TRN-8.9 A read-write open and a control read-only open both denied `EACCES` is a permissions fault, and the reason names no sandbox (devices.md §2)."""
        backend = self.unused_backend("TRN-8.9")
        gpu = self.probe(open_denied, backend)
        self.assertFalse(
            gpu["available"],
            "no node opened, so no GPU is available (devices.md §2): %r" % (gpu,),
        )
        self.assertIsNone(
            gpu["name"],
            "no backend ran, so `gpu.name` is None (devices.md §1-§2): %r"
            % (gpu["name"],),
        )
        reason = as_text(gpu["reason"], "'gpu' reason")
        for token in ("read-only", "also denied", "EACCES"):
            self.assertIn(
                token,
                reason,
                "a permissions fault names the control open that was denied too, with "
                "its errno — `%s` is missing (devices.md §2): %r" % (token, reason),
            )
        self.assertNotIn(
            "sandbox",
            reason,
            "the read-only open is denied as well, so the sandbox's read-write split is "
            "not the situation and the reason does not claim it (devices.md §2): %r"
            % (reason,),
        )
        self.assertNotEqual(
            reason,
            self.sandbox_reason("TRN-8.9's sandbox control"),
            "a permissions fault and the sandbox's denial never share one reason, which "
            "is what separates a policy decision from a broken node (devices.md §2): %r"
            % (reason,),
        )
        backend.assert_not_called()

    def test_trn_8_10_a_backend_that_is_not_importable_is_reported_not_raised(self):
        """TRN-8.10 A backend whose import raises is reported as not importable beside the read-write open that succeeded, and no exception escapes `devices()` (devices.md §2, surface.md §6)."""
        backend = mock.Mock(side_effect=ImportError("no module named 'torch'"))
        gpu = self.probe(read_write_opens, backend)
        self.assertFalse(
            gpu["available"],
            "a platform whose backend will not import has no usable device, so `gpu."
            "available` is false (devices.md §2): %r" % (gpu,),
        )
        self.assertIsNone(
            gpu["name"],
            "no backend ran, so `gpu.name` is None (devices.md §1-§2): %r"
            % (gpu["name"],),
        )
        reason = as_text(gpu["reason"], "'gpu' reason")
        self.assertIn(
            "read-write",
            reason,
            "the reason states the operation that did succeed, so the import failure is "
            "read and not inferred (devices.md §2): %r" % (reason,),
        )
        self.assertIn(
            "not importable",
            reason,
            "a backend that will not import is reported in those words, not raised "
            "(devices.md §2): %r" % (reason,),
        )
        self.assertNotIn(
            "denied",
            reason,
            "the read-write open succeeded, so the reason claims no denial (devices.md "
            "§2): %r" % (reason,),
        )


if __name__ == "__main__":
    unittest.main()
