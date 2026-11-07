# PyPoker-Demo — the GPU: what works today, and what you run yourself

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 5 · **Date:** 2026-11-08
- **Covers:** D-17's feasibility check, its measured result, and the user-side instructions that replace it — with the device rule of D-8 and the **measured** R1/R2 speed comparison of D-7 (0.1111 → 0.0451 s/hand, 2.46×)
- **Ceiling:** 80 lines. At the ceiling, split by owner — never append

## 1. What works today: the CPU, and only the CPU

Every rung trains and evaluates on CPU, and that is the supported path. The evidence the repository ships was produced on CPU — `checkpoints/evidence/r1-live.json` is R1 at 1,000 hands per variant per seed, 3,000 hands inside ASM-21's 0.105–0.120 s/hand run band, and the file carries that build's own seconds — and no part of the protocol requires a GPU (D-8, `protocol.md` §6, ASM-15, ASM-21). `training.devices()` reports `available: ['cpu']` with `default: 'cpu'`, and `training.run`'s `device` argument accepts nothing outside that list.

## 2. An agent cannot run the GPU path, and that is why this page exists

D-17 asks for the feasibility check before the PyTorch rung's live-speed measurement, and the check was made and failed: a delegated agent cannot use the card. The reason is one line long — **the file sandbox denies read-write opens under `/dev`** — and it is neither a driver fault nor a permissions fault. `/dev/kfd` is `root:render`, mode 0660, and the user is in `render`; read-only opens of both nodes succeed; a read-write open is denied, and a control open of world-writable `/dev/urandom` (0666) is denied exactly as `/dev/kfd` is. `torch 2.13.0+rocm7.1` imports, the HIP runtime loads, `ldd libtorch_hip.so` reports no missing library, and `torch.cuda.is_available()` is still `False` with `device_count()` at `0`.

Two consequences mislead a reader once, so both are stated. The denial arrives as an ordinary `PermissionError`, **not** as a `[sandbox: file access denied]` marker, so it reads like a broken driver when it is a policy decision. And **nothing torch prints names the cause**: torch reports `False`, and `RuntimeError: No CUDA GPUs are available` when forced onto the device, because it never reaches it — the line that does name the cause, `Unable to open /dev/kfd read-write: Permission denied`, is `rocminfo`'s, and §4 shows where it appears. The project's own probe takes the same measurement: `training.devices()` opens each node read-write and, when that is denied, reports the node, the operation and the errno — measured here, `gpu.reason` begins `/dev/kfd: the read-write open (os.O_RDWR) is denied EACCES (13)` — and then reports that a control read-only open of the same node succeeds, which is what separates a sandbox denial from a permissions fault on the node or from a card that is not there (D-8, `protocol.md` §6).

## 3. The code is CPU-only regardless, so a working card is not enough

Nothing in the tree would use a GPU even with one reachable: `training.run('R2', device='cuda')` refuses with `UnknownDevice`, `devices() lists cpu`, and `src/agents/torch_backend.py` creates every tensor on CPU. Pointing this project at a card therefore needs a code change — device plumbing in the torch backend *and* in `run`'s device validation — and that change is not shipped and is not part of this page (D-17, D-8). D-17's fallback is instructions, not a promise about the path they describe.

## 4. Verify the card with this project's interpreter

Run these from the repository root in **your own** shell with the project venv — not inside the workflow's sandbox, which is where §2's denial comes from:

```sh
.venv/bin/python -c "import torch; print(torch.__version__, torch.version.hip, torch.cuda.is_available(), torch.cuda.device_count())"
.venv/bin/python -c "import torch; print(torch.cuda.get_device_name(0))"
rocm-smi
rocminfo
```

**Healthy**, and the record for it is `strata/platform.md` (Compute): the venv's torch is `2.13.0+rocm7.1` reporting HIP `7.1.52802` against system ROCm 7.2.3, and with the device nodes open `torch.cuda.is_available()` is `True` and the device names itself `AMD Radeon RX 9070 XT`. Five further observations come from the user-side check — an operator in a normal shell on this host, not a workflow process, which cannot leave the sandbox (§2) — and they are **not yet written into that record**: the ROCm binaries resolve at `/usr/bin`, a device count of `1`, `rocm-smi` listing the card and its current use, `rocminfo` listing the agent it exposes, and no environment variable needed — the venv's torch carries its own HIP libraries and loads with `LD_LIBRARY_PATH` unset (D-17). Read the record as the standard and those five as this machine's evidence, which belongs in `strata/platform.md` when that record is next replaced.

**Denied**, which is what the agent sees, measured here in the sandbox: the first command prints `False` and `0`, the second raises `RuntimeError: No CUDA GPUs are available`, and `rocminfo` is the command that says why — on stdout, exit status 1, three lines reading `ROCk module is loaded`, `Unable to open /dev/kfd read-write: Permission denied` and `ryanr is member of render group` (`rocm-smi` fails beside it, exit 8, with a shared-memory error — `fchmod` or `shm_open`, `Bad file descriptor` or `Invalid argument` — instead of a card listing). If that is your output, check `id -nG` for `render` and `ls -l /dev/kfd` for `root:render` mode `0660`: when both already hold, the process is inside a sandbox and no reinstall will help, because it is not permitted to open the device for writing.

Then time the arithmetic a card is for — warm-up outside the clock and `synchronize` inside it, because torch queues kernels and an unsynchronised loop times the enqueue rather than the product:

```sh
.venv/bin/python - <<'PY'
import time, torch
d = "cuda" if torch.cuda.is_available() else "cpu"
a, b = torch.randn(2048, 2048, device=d), torch.randn(2048, 2048, device=d)
torch.matmul(a, b)                                   # warm-up, not timed
if d == "cuda":
    torch.cuda.synchronize()
start = time.perf_counter()
for _ in range(20):
    torch.matmul(a, b)
if d == "cuda":
    torch.cuda.synchronize()
print(d, round((time.perf_counter() - start) * 1000, 1), "ms for 20 matmuls")
PY
```

`strata/platform.md` records the measured pair at that shape: **107.7 ms on the GPU against 269.3 ms on CPU**. Both are this host's clocks at one moment, and the CPU side is load-sensitive — the same loop re-run here, in the sandbox and under load, measured 364–403 ms — so read the device the script names, and keep your own figure rather than quoting this one.

## 5. Measure the PyTorch-versus-NumPy difference on your own machine

D-7 recreates R1 in PyTorch so the ladder's speed difference is measured on identical work: R1 and R2 declare the same encoding, model shapes, update rule and sample order and differ only in `backend`, and their evidence is throughput and wall-clock per hand from the run record and `harness.timings`, with a same-work check that both choose the same actions on the same seeded hands (`ladder.md` §5, D-7). One run of each, each to its own write root, is that measurement:

```sh
PYTHONHASHSEED=0 PYPOKER_CHECKPOINT_ROOT=/tmp/pypoker-r1 PYTHONPATH=src .venv/bin/python -c "import training; r=training.run('R1'); print(r['device'], r['timings'])"
PYTHONHASHSEED=0 PYPOKER_CHECKPOINT_ROOT=/tmp/pypoker-r2 PYTHONPATH=src .venv/bin/python -c "import training; r=training.run('R2'); print(r['device'], r['timings'])"
```

The pin is what makes the two runs identical work: two processes of this build otherwise differ where the oracle's sampled equity decides an action (`protocol.md` §4, `ladder.md` §5).

Both commands are valid today and both record `device: 'cpu'`; `timings` is keyed by variant name, so R1's block sits under `naive-numeric` and R2's under `naive-numeric-torch`, each seed carrying `hands`, `wall_clock_seconds`, `seconds_per_hand` and `hands_per_second` (measured). R1's live budget measured 3,000 hands that way inside ASM-21's 0.105–0.120 s/hand run band (`league.md` §7; the bundle carries the current seconds), and **the R2 side of the comparison has since been measured on this host, on the same 3,000 hands at the same three seeds and the same `cpu` device: 0.0451 s/hand against R1's 0.1111 — 2.46×, 333.2 s → 135.4 s for identical work.** Both figures are in `strata/records/r2-speed.md`, the D-7 record of that pair: this project measured them by starting the two runs above on this host — each written to its own `PYPOKER_CHECKPOINT_ROOT`, so the shipped set was untouched — and the record carries the seeds, the device, the curves and the wall clock beside the figure (D-7, D-8). It also states the mean |TD error| both backends' curves end at, measured side by side in that record, so the backends differ in arithmetic and not in rule — the pair's figures stay there and not here, because a move of the encoding shifts R1's curve ends and this page would then quote one build's. The root `README.md` §Using a GPU quotes the same speed-up (333 s → 135 s), and because no R2 checkpoint set ships, the measurement lives in that record and in no artefact's `cost` block. Re-measured through the two commands above, R2 came in at **0.0451–0.0453 s/hand** and **2.45–2.46×** — the same figure twice on the same machine, the D-7 pair's measurement carried in `strata/records/r2-speed.md` beside this section's recipe — which is the point that was right all along: **your own run will differ from both figures — the number that applies to your machine is the one your run records**, and quoting someone else's is how one CPU figure and one GPU figure end up in a single series. Once a GPU path exists, the same two calls carry `device='cuda'`, and that is the GPU-versus-CPU measurement.

Every run records the device it used (`records.md` §12), and that key is what keeps the two apart: quote it beside every figure, and never set a figure that says `cpu` against one that says `cuda` as though they were one series (D-6, D-8). R1 against R2 is one interpreter against another on the same CPU, so the 2.46× measures the backend and says nothing about the card (D-7); the GPU half of that comparison is still the user's to take. Expect the arithmetic to move and the hand not to: a hand's cost is mostly work a GPU would not touch — the oracle's per-decision equity sample is nearly all of a table's cost, an oracle-bearing cell measuring 0.255–0.315 s/hand against 0.002–0.004 for an oracle-free one, and every hand is dealt by pure-Python `pokerkit` (`league.md` §7, `ladder.md` §6, ASM-15, ASM-21). So how far a GPU moves a *hand* is an inference from those costs and not a measurement, and §4's matmul pair is the only GPU arithmetic this repository has measured.
