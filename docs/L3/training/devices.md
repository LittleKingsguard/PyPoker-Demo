# training — the devices

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-05
- **Owner:** `devices()` — the record it returns (§1), the probe and its reason (§2), and what a run records about the device it
  used (§3)
- **Ceiling:** 70 lines. At the ceiling, split by owner — never append
- **Read with:** `loop.md` §1 step 9, §5, §6, `errors.md` §4, `strata/platform.md` (Compute)

## 1. The record

    devices() -> {"available": ["cpu", …], "default": "cpu", "gpu": {"available": bool, "name": …, "reason": …}}

`devices()` takes no argument and returns one mapping read under three keys (`surface.md` §6, D8):

| Key | Content |
|---|---|
| `available` | the device names `run` accepts. `"cpu"` is always first and always present; `"cuda"` appears only when §2's probe opened a device node |
| `default` | `"cpu"`, always — the device an omitted argument resolves to (`loop.md` §5) |
| `gpu` | `{"available": bool, "name": <the hardware string or None>, "reason": <why, when unavailable>}` — the record a reader quotes for "why was this run on CPU" |

`cpu` is always available and every rung and both table budgets run on it (`surface.md` §6, ASM-15); no part of the protocol
requires a GPU (D-8, `protocol.md` §6). Two calls on one platform agree, and the answer depends on the platform and not on the
caller (`surface.md` §6, FAM-1.42 reads `cpu` out of the flattened record).

## 2. The probe, and why it is not a `torch` question

`_gpu()` answers one question — **does the device node open for reading?** — and answers it with `os.open` and nothing else:

    for node in ("/dev/kfd", "/dev/dri/renderD128"):
        try:      handle = os.open(node, os.O_RDONLY); os.close(handle) → the node opened
        except OSError as exc: → `reason` = "PERMISSION" when exc is a PermissionError, "ABSENT" when the node is missing,
                                          "OTHER" with the errno's name otherwise

`available` is `True` only when a node opened **and** a backend reports it usable (Rev 2, measured). The three codes are the
record's own vocabulary, so a reader can tell a sandbox denial from a machine without a GPU: on a machine whose sandbox denies
the nodes, `/dev/kfd` and `/dev/dri/renderD128` raise `PermissionError: [Errno 13]`, which is the **first** case — the
sandbox's denial and not the driver's (`strata/platform.md`, D-8). A workflow-started run is therefore CPU-bound by
construction, and a GPU run is one the user starts outside the sandbox (`strata/platform.md`, `protocol.md` §6); `gpu.name`
is the hardware string when the backend names it and `None` otherwise, never a guess.

**Rev 2 — the node is not the device.** Measured on this host: inside the file sandbox both nodes **open** for reading while
`torch` reports no usable device, so a node-only probe reports `available: True` for a GPU the workflow cannot use — a claim
D-8 forbids ("reported available only when the device actually opens"). The probe therefore asks the backend **after** a node
opened, at most once per process, and reports the measured reason when the backend declines. Rejected: keeping the node test
alone, which is false on this machine; also rejected: asking `torch` first, which costs its import on every platform.

**No `torch` on a machine without the nodes.** `devices()` probes, it does not compute: the import happens only after a device
node has opened, is cached in the module, and never moves a parameter. `training` imports no `torch` at module scope
(`README.md` §5, D10). Rejected: `torch.cuda.is_available()` as the first question, which answers the same question only after
a 3-second import and is `False` for a reason it does not report.

## 3. What a run records, and what it does not do with it

`run`'s `device` argument must be one of `devices()["available"]`, or the run refuses it naming the value and the list
(`loop.md` §6). A device that passes is **recorded and nothing else**: `records.md` §12's `device` key carries it, so a GPU run
and a CPU run are never confused and a third party reading the record can tell them apart (D-8, `protocol.md` §6, D-6). Nothing
is threaded further, because no granted `agents` call takes a device — `build_learner`'s spec is `backend`, `architecture`,
`seed`, `sizes` and `encoder` and every other key is ignored (`agents/surface.md` §4, `records.md` §3). The backend is the
*software* axis (`numpy` or `torch`, D-7) and the device is the hardware the run happened on; R1 and R2 differ on the first and
may share the second, which is exactly what the parity row needs (`ladder.md` §5, `fairness.md` §5).

So a run started by this workflow records `"cpu"`, and a user-started GPU run records `"cuda"` — a fact about the machine, never
a claim about speed (`battery.md` §2, ASM-15).
