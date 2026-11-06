# PyPoker-Demo — measured platform constraints

Facts about the live deployment the layers must design within. This is not design: it records what
the platform does, measured on 2026-11-05, and it is **replaced** when a measurement changes, never
annotated. Ceiling: 60 lines.

## Delegation

- Nested delegation is available. A spawned child composes the parent's preset, then
  `toolFilter.allow` narrows it by global tool name (D-1).
- `toolFilter` names resolve as global tools in the granting scope; an unknown name fails the mount
  with `tools.restrict() names unknown global tool`. **Measured:** the `strata` preset's
  `role_l0_research` row allows `web_search` and `web_fetch`, which this deployment does not have,
  so that role cannot be mounted at all. Intake research therefore runs at L0 under
  `strata/research.md` §1, with `bash` and network, and the same finding record (D-15).
- `maxDepth` must be 4 on every recursing row; five layers need it (D-1).
- One layer runs one pass at a time. **Measured:** `interrupt_agent` returned "interrupt requested"
  and the one-shot child kept working to completion; a replacement pass started afterwards ran
  concurrently with it and both rewrote `docs/L1/` and `tests/e2e/`, so the layer's artifacts had
  to be reconciled after the fact.
- Children inherit the parent's workspace and sandbox mode, and approval is pinned to `never` for
  every delegated child. **A child cannot escalate**, so no delegated layer can reach the GPU
  (see Compute); a training run started by this workflow is therefore **CPU-bound**, and a GPU run
  has to be started by the user outside the sandbox (D-8, D-7).

## File walls

- The sandbox enforces **whole-workspace modes only**; it cannot restrict writes to a subdirectory, so layer quarantine is tool wall + `strata-lint` ownership + diff scope, never sandbox-enforced
  (D-13).

## Compute (measured)

- GPU: **AMD Radeon RX 9070 XT** (RDNA4, PCI `1002:7550`). System ROCm 7.2.3; the project venv
  carries `torch 2.13.0+rocm7.1` (HIP 7.1.52802).
- Inside the `workspace-write` sandbox, `/dev/kfd` and `/dev/dri/renderD128` open with
  `PermissionError: [Errno 13]`, `torch.cuda.is_available()` is `False`, and `rocminfo` /
  `rocm-smi` fail. Under `danger-full-access` the devices open, `torch.cuda.is_available()` is
  `True`, and the device reports as above. The denial is the DSH file sandbox, not the driver.
- CPU: AMD Ryzen 9 9900X, 24 threads (torch reports 12). 2048×2048 fp32 matmul, 20 iterations:
  269.3 ms CPU, 107.7 ms on the GPU.
- Python 3.12.3. Project venv at `.venv/` (git-ignored) holds `numpy 2.5.4`, `pokerkit 0.7.7`,
  `matplotlib`, `jupyterlab`.

## `pokerkit` facts the designers need

- `pokerkit` 0.7.7, MIT, Python ≥ 3.11, no runtime dependencies; no `__version__` attribute, so
  read its version with `importlib.metadata` (D-15).
- No gym-style wrapper, `reset`/`step`/`render` or observation encoding: the loop, the encoding and
  the reward are this project's to build (D-1).
- Actions are applied by calling a method once a `can_*` predicate passes: `fold()`,
  `check_or_call()`, `complete_bet_or_raise_to()`, with `actor_index`,
  `min_/max_completion_betting_or_raising_to_amount` and `showdown_index` for state.
- The deck is shuffled with Python's `random.shuffle` at state creation and no seed parameter is
  accepted, so reproducibility comes from seeding the global `random` (`ASM-2`, D-15);
  `pokerkit.analysis`'s `calculate_equities`/`calculate_hand_strength` feed the oracle (`D-6`).

## Returns

- The subagent tool exposes no structured-return parameter: every layer return uses the text envelope of `strata/envelope.md`, validated post hoc by `strata-lint` (D-11); `agentOptions` allows per-role model routing, so L4 can run on a smaller model if L0 wants that.
