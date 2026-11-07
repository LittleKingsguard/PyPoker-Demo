# R2 live-speed measurement (D-7) and the GPU check (D-17) · 2026-11-06

R2 is the PyTorch recreation of R1 on identical work — same encoding, architecture, learning rule
and matched parameters — so the difference is the backend.

## NumPy versus PyTorch, same 3,000 hands, CPU

| seed | R1 NumPy s/hand | R2 PyTorch s/hand | speed-up |
|---|---|---|---|
| 0 | 0.1170 | 0.0504 | 2.32× |
| 1 | 0.1048 | 0.0418 | 2.50× |
| 2 | 0.1114 | 0.0432 | 2.58× |
| **mean** | **0.1111** | **0.0451** | **2.46×** |

Wall clock for the same work: **333.2 s → 135.4 s**. Both runs device `cpu`, 1,000 hands per seed
at seeds 0/1/2, R2 written under `PYPOKER_CHECKPOINT_ROOT` so the shipped set was untouched. R2's
curves end at mean |TD error| 3.03 / 2.86 / 3.49 against R1's 2.77 / 2.87 / 3.19: the backends
differ in arithmetic, not in rule, and neither rung had converged at 1,000 hands.

## The GPU check (D-17) — an agent cannot run it

`AGENT_CANNOT_USE_GPU`. A delegated agent under the normal sandbox measured:

- `/dev/kfd` and `/dev/dri/renderD128` open read-only but **deny read-write with `EACCES`**;
- the nodes are `root:render` mode 0660 and the agent is in `render`, so POSIX is not the blocker:
  a control read-write open of world-writable `/dev/urandom` is denied the same way, so the rule
  is the sandbox's write restriction under `/dev`;
- torch's HIP runtime loads cleanly and `ldd libtorch_hip.so` shows no missing libraries, yet
  `torch.cuda.is_available()` is `False` and `device_count()` is `0`;
- `rocminfo` confirms "ryanr is member of render group" and "Unable to open /dev/kfd read-write:
  Permission denied".

Denials surface as ordinary `PermissionError`, not the `[sandbox: file access denied]` marker,
which is why the failure reads like a driver fault when it is not. **The project is CPU-only
regardless**: `training.devices()` lists `cpu` alone, `training.run(device="cuda")` raises
`UnknownDevice`, and the torch backend puts every tensor on CPU. User instructions and that
limitation are documented per D-17 in `docs/L1/`.
