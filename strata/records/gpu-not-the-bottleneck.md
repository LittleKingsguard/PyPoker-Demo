# Would a GPU speed the integration up? No — the card model is 0.2 % of the cost · 2026-11-08

D-100's question. Three measurements, in order of how much they matter.

**1. No GPU is reachable from here.** `torch 2.13.0+rocm7.1` (HIP 7.1.52802) is installed, but
`torch.cuda.is_available()` is **False** inside this environment — the sandbox denies `/dev/kfd` and
`/dev/dri/renderD128` (D-17). A GPU run is not merely slower to arrange; it is unavailable to the agent doing the work.

**2. Even with one, the card model is not where the time goes.**

| component | measured cost |
|---|---|
| poker engine, 20 decisions/hand | **14.3 ms/hand** |
| **card-model forward**, 197 µs × 20 decisions | **3.9 ms/hand** — 27 % of the engine, 0.2 % of the run |
| the deep arm's actual cost | **~2,100 ms/hand** |

So **99 % of the time was the probe's own Python plumbing** — per-decision tensor assembly, a backward pass and an
Adam step for every decision — not the frozen attention model, and not the engine.

**3. Per-sample GPU work on a 57 k-parameter model would be slower.**

| batch | CPU time per forward | per sample |
|---|---|---|
| 1 | 197 µs | **197 µs** |
| 8 | 275 µs | 34 µs |
| 64 | 672 µs | 10.5 µs |
| 512 | 2,545 µs | **5.0 µs** |

**Batching is the lever, by 40×** — and a GPU at batch 1 is exactly the worst case for it, since a kernel launch
costs more than the 197 µs of CPU arithmetic this model needs. Play is sequential, so a hand's decisions cannot be
batched ahead of time.

**What would actually speed the deep run up**, none of it needing a GPU: use the **product's learner** rather than the
probe (**0.19 s/hand** measured, a 10× gain); take **one update per hand or street** instead of per decision, which
removes most of that 99 %; keep the **process-level parallelism** the six-arm run already used; and batch the card
model over a hand's decision points only if the hand is replayed deterministically afterwards.
