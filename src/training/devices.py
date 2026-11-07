"""What this platform offers, and the device a run uses when none is named (D-8).

`cpu` is always available and is the default, and every rung and both table budgets run
on it (D-8, ASM-15). `available` is therefore the device names `run` accepts, built from
the declared `AVAILABLE` and never from the probe, and `gpu` reports what the platform
exposes beside it: a GPU is reported available only when a **read-write** open of one of
its device nodes succeeds **and** a backend reports the device usable, because read-write
is the open a driver performs and a read-only one is no evidence that a process could use
the card (devices.md §2, `strata/platform.md`, `protocol.md` §6).

The probe is a fact about the platform, so it is taken once per process and cached: asking
twice in one run cannot answer differently. No backend is imported before a read-write
open has succeeded, so a CPU-only platform never pays for a framework import to be told it
has no GPU (G18). Every `False` names the node it measured, the operation that failed and
`errno.errorcode` with its number, so a reader tells a file sandbox's denial of the
read-write open from an absent node, another errno, or a permissions fault without
inferring one from another (devices.md §2).
"""

import errno
import os

#: The device names `run` accepts, in the order this module reports them.
AVAILABLE = ("cpu",)

#: The one a run uses when none is named.
DEFAULT = "cpu"

#: The nodes a probe opens read-write, in the order it tries them (devices.md §2).
GPU_NODES = ("/dev/kfd", "/dev/dri/renderD128")

#: The probe's answer, once per process; empty at import, so clearing it re-probes.
_PROBED = {}

#: The backend `_backend()` imported, once per process and only after an open (G18).
_BACKEND = {}


def _errno(error):
    """One `OSError`'s errno as its name and number — never a bare code (devices.md §2)."""
    code = error.errno
    if code is None:
        return type(error).__name__
    return "%s (%d)" % (errno.errorcode.get(code, "errno"), code)


def _close(handle):
    """Close one handle the probe opened, and let no close failure escape `devices()`."""
    try:
        os.close(handle)
    except OSError:
        pass


def _denied(node, error):
    """One node's denied read-write open, and what a control read-only open says of it.

    The control open is what separates the sandbox's read-write split from a permissions
    fault: the denial is a plain `PermissionError`, never a sandbox marker, so the two
    situations are told apart by whether the same node still opens for reading
    (devices.md §2).
    """
    failed = "%s: the read-write open (os.O_RDWR) is denied %s" % (node, _errno(error))
    try:
        control = os.open(node, os.O_RDONLY)
    except OSError as denied_too:
        return (
            "%s, and a control read-only open (os.O_RDONLY) of the same node is also "
            "denied %s — a permissions fault on the node itself, so no driver could use "
            "it either" % (failed, _errno(denied_too))
        )
    _close(control)
    return (
        "%s, while a control read-only open (os.O_RDONLY) of the same node succeeds — "
        "the sandbox denies read-write opens under /dev, so a read-only open reports "
        "nothing about a device a driver could use" % (failed,)
    )


def _unopened(node, error):
    """One node's failed open that was no denial, named by its errno (devices.md §2)."""
    if error.errno == errno.ENOENT:
        return "%s is absent: os.open(%s, os.O_RDWR) raises %s" % (
            node,
            node,
            _errno(error),
        )
    return "%s: the read-write open (os.O_RDWR) raises %s" % (node, _errno(error))


def _backend():
    """The GPU backend, imported at most once per process — after a node opened (G18)."""
    if "module" not in _BACKEND:
        import torch

        _BACKEND["module"] = torch
    return _BACKEND["module"]


def _opened(node):
    """The probe's answer once a node opened read-write: the backend's to give (§2)."""
    opened = "%s opens read-write" % (node,)
    try:
        backend = _backend()
    except Exception as error:
        return {
            "available": False,
            "name": None,
            "reason": "%s, but the torch backend is not importable (%s: %s)"
            % (opened, type(error).__name__, error),
        }
    try:
        usable = bool(backend.cuda.is_available())
    except Exception:
        usable = False
    if not usable:
        return {
            "available": False,
            "name": None,
            "reason": "%s, but the torch backend reports no usable device" % (opened,),
        }
    try:
        name = backend.cuda.get_device_name(0)
    except Exception:
        return {
            "available": True,
            "name": None,
            "reason": "%s and the backend reports the device usable, but it does not "
            "name it" % (opened,),
        }
    return {
        "available": True,
        "name": name,
        "reason": "%s and the torch backend reports it usable; a run started by this "
        "workflow is still CPU-bound, because a GPU run is the user's, started outside "
        "the sandbox (D-8)" % (opened,),
    }


def _probe():
    """One measurement of the GPU: the nodes' read-write open first, the backend after."""
    blocked = []
    for node in GPU_NODES:
        try:
            handle = os.open(node, os.O_RDWR)
        except PermissionError as error:
            blocked.append(_denied(node, error))
        except OSError as error:
            blocked.append(_unopened(node, error))
        else:
            _close(handle)
            return _opened(node)
    return {
        "available": False,
        "name": None,
        "reason": "; ".join(blocked) or "no GPU device node was examined",
    }


def _gpu():
    """The GPU's state on this platform, probed once and remembered."""
    if "gpu" not in _PROBED:
        _PROBED["gpu"] = _probe()
    return dict(_PROBED["gpu"])


def devices():
    """The devices a run accepts, the default, and the GPU's state (surface.md §6)."""
    return {
        "available": list(AVAILABLE),
        "default": DEFAULT,
        "gpu": _gpu(),
    }
