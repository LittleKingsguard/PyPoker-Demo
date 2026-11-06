"""What this platform offers, and the device a run uses when none is named (D-8).

`cpu` is always available and is the default, and every rung and both table budgets run
on it (D-8, ASM-15). `available` is therefore the device names `run` accepts, and `gpu`
reports what the platform exposes beside it: a GPU is reported available only when it
actually opens **and** a backend reports it usable, and the record states the reason when
it does not (D-8, `strata/platform.md`, protocol.md §6).

The probe is a fact about the platform, so it is taken once per process and cached: asking
twice in one run cannot answer differently. No backend is imported unless a device node
opened first, so a CPU-only platform never pays for a framework import to be told it has
no GPU.
"""

import os

#: The device names `run` accepts, in the order this module reports them.
AVAILABLE = ("cpu",)

#: The one a run uses when none is named.
DEFAULT = "cpu"

#: The GPU the brief's machine carries, and the nodes a probe has to open (D-8).
GPU_NAME = "AMD Radeon RX 9070 XT"
GPU_NODES = ("/dev/kfd", "/dev/dri/renderD128")

_PROBED = {}


def _open_nodes():
    """Whether one of the GPU device nodes opens here, and why none does when none does."""
    blocked = []
    for node in GPU_NODES:
        if not os.path.exists(node):
            blocked.append("%s is absent" % (node,))
            continue
        try:
            handle = open(node, "rb", buffering=0)
        except OSError as error:
            blocked.append("%s raises %s" % (node, type(error).__name__))
            continue
        handle.close()
        return True, ""
    return False, "; ".join(blocked) or "no GPU device node opened"


def _probe():
    """One measurement of the GPU's state: the nodes first, the backend only after them."""
    opened, why_not = _open_nodes()
    if not opened:
        return {
            "available": False,
            "name": None,
            "reason": "%s is present but unreachable from this sandbox: %s"
            % (GPU_NAME, why_not),
        }
    try:
        import torch
    except Exception as error:  # a platform without a backend is a platform without a GPU
        return {
            "available": False,
            "name": None,
            "reason": "a device node opens, but the torch backend is not importable (%s)"
            % (type(error).__name__,),
        }
    if not torch.cuda.is_available():
        return {
            "available": False,
            "name": None,
            "reason": "a device node opens, but torch reports no usable device",
        }
    return {
        "available": True,
        "name": torch.cuda.get_device_name(0),
        "reason": "the device opens and torch reports it usable; a run started by this "
        "workflow is still CPU-bound, because a GPU run is the user's, started outside "
        "the sandbox (D-8)",
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
