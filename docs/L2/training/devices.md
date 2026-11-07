# training — the devices record and the probe that fills it

- **Layer:** L2 · **Module:** `training` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-06
- **Owner of this file:** `surface.md` §6's `fixed` row — the record `devices()` returns (§1), the operation its probe
  measures and what `gpu.reason` tells apart (§2), and what a run records of it (§3)
- **Ceiling:** 45 lines. At the ceiling, split by owner — never append
- **Read with:** `surface.md` §6, `loop.md` §5, `docs/L1/protocol.md` §6, `docs/L1/gpu.md` §2–§3, `strata/platform.md` (Compute)

## 1. The record

`devices()` takes no argument and returns one mapping read under three keys (`surface.md` §6, D-8):

| Key | Content |
|---|---|
| `available` | the names `run` accepts: `cpu` first and always present, and no name added by a GPU while nothing in the tree uses one (`docs/L1/gpu.md` §3, D-8, ASM-15) |
| `default` | `cpu`, always — what an omitted `device` argument resolves to (`loop.md` §5, D-8) |
| `gpu` | `{available, name, reason}`: whether the platform exposes a GPU a process can use, the name it goes by, and why not — the record a reader quotes for "why was this run on CPU" (D-8, `protocol.md` §6) |

Two calls on one platform agree, and the answer depends on the platform and not on the caller (`surface.md` §6); `gpu.name`
is the string a backend reports and `None` otherwise, never a guess (D-8).

## 2. The probe measures the open a driver performs

- **The operation.** `gpu.available` is `True` only when a **read-write** open of a GPU device node succeeded **and** a backend
  reports the device usable; read-write is the open a driver performs, so a read-only open is no evidence (Rev 4, D-8).
- **The reason.** A `False` names in `reason` the node, the operation that failed, its errno's name and number, and which
  situation holds, in prose and not a class code: the read-write open denied while a control read-only open of the same node
  succeeds (this sandbox's denial — a plain `PermissionError`, never a sandbox marker); both denied (a permissions fault);
  the node absent; another errno; or the node opened read-write while the backend declined (Rev 4, `docs/L1/gpu.md` §2).
- **No backend before the open.** No backend is imported before a read-write open has succeeded, so a CPU-only platform
  pays for no framework import, and the import happens at most once per process (D-8, `docs/L3/training/guardrails.md` G18).
- **The measured case the rule comes from.** Inside `workspace-write` both nodes open read-only, while a read-write open of
  either is denied `EACCES` (13) — as is one of world-writable `/dev/urandom`, though `/dev/null` opens read-write, so the
  denial is of these nodes' read-write opens and not of `/dev` wholesale; `torch` imports and reports no usable device, its
  own read-write open of `/dev/kfd` being what is denied (Rev 4, measured, `strata/platform.md`, `docs/L1/gpu.md` §2).
- **The cases that carry it.** `tests/training/test_devices.py` `TRN-8.1`–`TRN-8.10` inject the five reasons at unit level;
  `tests/integration/training/test_device_probe.py` `TRNJ-10.1` pins the ordering rule in a child process, the one part no
  single-process case can see (`battery.md` §2, `docs/L3/training/devices.md` §2, D-8).

## 3. What a run records, and what it does not do with it

`run`'s `device` argument must be one `available` lists, or the run refuses it naming the value and the list (`surface.md`
§4, `loop.md` §6). A device that passes is recorded, so a GPU run and a CPU run are never confused (D-6, D-8, `protocol.md`
§6); nothing is threaded further, because no granted `agents` call takes a device (`agents/surface.md` §4). The record is a
fact about the machine, never a claim about speed (`docs/L1/protocol.md` §6, ASM-15).
