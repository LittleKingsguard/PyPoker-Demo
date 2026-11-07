# training — the devices

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-06
- **Owner:** `devices()` — the record it returns (§1), the probe and its `reason` (§2), and what a run records about the device
  it used (§3)
- **Ceiling:** 70 lines. At the ceiling, split by owner — never append
- **Read with:** `loop.md` §1 step 9, §5, §6, `errors.md` §4, `docs/L2/training/devices.md` §1–§2, `strata/platform.md` (Compute)

## 1. The record

    devices() -> {"available": ["cpu"], "default": "cpu", "gpu": {"available": bool, "name": …, "reason": …}}

`devices()` takes no argument and returns one mapping read under three keys (`surface.md` §6, D-8):

| Key | Content |
|---|---|
| `available` | the device names `run` accepts: `["cpu"]`, always, on every platform. **A reachable GPU adds no name** — nothing in the tree uses one and `run` refuses any device but `cpu` (Rev 3, `surface.md` §6 Rev 4, `docs/L1/gpu.md` §3, D-8) |
| `default` | `"cpu"`, always — the device an omitted argument resolves to (`loop.md` §5) |
| `gpu` | `{"available": bool, "name": <the hardware string or None>, "reason": <why, when unavailable>}` — the record a reader quotes for "why was this run on CPU" (D-8, `protocol.md` §6) |

`available` is built from the declared `AVAILABLE` and never from the probe, so no measurement can widen what `run` accepts
(Rev 3, `docs/L1/gpu.md` §3); two calls on one platform agree (`surface.md` §6, FAM-1.42, ASM-15, `protocol.md` §6).

## 2. The probe measures the read-write open a driver performs

`_probe()` answers one question — **does a GPU device node open for read-write?** — and imports a backend only after the answer
is yes (`docs/L2/training/devices.md` §2, G18). Read-only is no evidence: measured here, both nodes open for reading while
`torch` reports no usable device, so a read-only probe claims a GPU no process can use (Rev 3, Rev 2's finding, D-8).

    for node in GPU_NODES:              # "/dev/kfd" first, then "/dev/dri/renderD128"
        os.open(node, os.O_RDWR) succeeds → close the handle, go on to the backend
        os.open raises OSError            → record one failure with its errno, try the next node
    no node opened → available False, name None, reason built from the failures
    a node opened   → ask the backend: it names the device, or it declines

**The four situations, and the fifth text.** A `False` states which operation failed, its errno, and which situation the
platform is in, so a reader never infers one from another (`docs/L2/training/devices.md` §2, Rev 4, measured):

| Situation | How the probe knows | `reason` must contain | must not contain |
|---|---|---|---|
| the sandbox's denial | the read-write open is denied and a control `O_RDONLY` open of the same node **succeeds** | `read-write`, `denied`, `read-only`, `EACCES`, `13`, `sandbox` | `also denied` |
| a permissions fault | the read-write open is denied and the control read-only open is **denied too** | `read-only`, `also denied`, `EACCES` | `sandbox` |
| the node is absent | `os.open` raises `ENOENT` | `absent`, `ENOENT`, `2` | `read-write open denied` |
| another errno | any other `OSError` | its name and number, e.g. `ENODEV`, `19` | `sandbox` |
| the backend declined | the read-write open succeeded, and the backend reports no usable device or is not importable | `read-write`, `no usable device` / `not importable` | `denied` |

The situation sentence is the one the **first failing node** in `GPU_NODES` order belongs to and the clause list names every node
examined, so `/dev/kfd` leads. Every failure names the node, the operation and `errno.errorcode` with the number (`EACCES`/`13`)
— never a bare code, and never a `[sandbox: file access denied]` marker, because the denial is a plain `PermissionError`
(measured, `docs/L1/gpu.md` §2). Rev 3 drops Rev 1–2's `PERMISSION`/`ABSENT` codes: a class is not the errno owed a reader.

`gpu.name` is the backend's `get_device_name(0)` on the success path and `None` on every other, because the module holds no
hardware string (`docs/L2/training/devices.md` §1, D-8). `gpu.available` is `True` only when a read-write open succeeded **and**
`is_available()` is true, and no exception escapes `devices()` (`surface.md` §6 lists no refusal).

**No backend before the open.** `_backend()` is the only place the module imports `torch`, caches it for the process, and calls
it only after a read-write open succeeded — so a CPU-only platform pays for no framework import
(`docs/L2/training/devices.md` §2, G18, `README.md` §5); rejected is asking the backend first, which answers after the import with
a reason it never measured.

**Two seams the battery drives.** `_PROBED` (the probe cache, empty at import; clearing it re-probes) and `_backend`, which the
battery replaces beside `os.open`/`os.close` to inject the five texts — so no case needs a GPU or this host (`battery.md` §2).

## 3. What a run records, and what it does not do with it

`run`'s `device` must be one of `devices()["available"]` or the run refuses it naming the value and the list (`loop.md` §6); a
device that passes is **recorded and nothing else** — `records.md` §12's `device` key carries it, so a GPU run and a CPU run are
never confused (D-8, `protocol.md` §6, D-6) and nothing is threaded further, because no granted `agents` call takes a device
(`agents/surface.md` §4). A workflow-started run records `"cpu"` and a user-started GPU run `"cuda"` — a fact about the machine,
never a claim about speed (`battery.md` §2, ASM-15); no rung declares `"cuda"` while nothing uses it (`docs/L1/gpu.md` §3, D-8).
