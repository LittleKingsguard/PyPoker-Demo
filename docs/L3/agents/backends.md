# agents — the R1↔R2 axis

- **Owner:** the two backends (D-7): what the swap may and may not change, the one initialisation order, the
  one forward-pass arithmetic order, the parity mechanism and its tolerance, the dtype, and the lazy `torch`
  import
- **Ceiling:** 95 lines. At the ceiling, split by owner — never append
- **Read with:** `architecture.md` §2–§5, `rule.md` §5, `checkpoint.md` §2

## 1. What the axis is

R1 is hand-rolled NumPy and R2 recreates it in PyTorch so the speed difference is measured on identical work
(D-7, `strata/brief.md` §2); R2 is the recreation and R3–R6 stay on `torch` (`ladder.md` §2). At this module's
edge that is one learner family with one switch, and the switch is the spec's `backend`
(`surface.md` §4). `numpy` and `torch` are the only two values, they are `learners()`'s `backends` keys in that
order, and nothing else in the project branches on them (`surface.md` §3, D-7).

| The swap may change | The swap may **not** change |
|---|---|
| which library performs the arithmetic, and so its cost (D-7, D-8) | the kind, its four settings, or the sizing record — one model shape and one declared family (`learner.md` §2, D-3) |
| the checkpoint's own bytes, provided `save`/`load` stay loss-free at the decision boundary (`restore.md` §1) | the rule, the utility, the hyper-declarations or the sample order (`rule.md` §2–§6, `utility.md` §4, `ladder.md` §5) |
| — | the initialisation the seed defines, the exploration schedule and the keyed draws, and the tie-break (`rule.md` §4–§5) |
| — | the decision: one observation and one mask give one index, and a policy at the learner's own seed decides as `act` does (`surface.md` §6, §10) |
| — | the capacity: one shape is one model, so both counts coincide (§3, ASM-10) |

The check the ladder asks for is on **decisions and not on values**: two independent numerical libraries are not
guaranteed to round identically and the interface promises nothing about that (`learner.md` §2, `ladder.md` §5).
What is forbidden is a backend that differs in the model, the rule, the order or the tie-break, and a decision reads
`A` values and one comparison — `A` the shape's descriptor count, `3` on the default shape (`shapes.md` §2) — so that is where the parity obligation lands.

## 2. One arithmetic order, expressed twice

The two backends evaluate **the same expressions in the same sequence**; only the library that evaluates them
changes (`architecture.md` §2):

1. the input block — `relu(x @ W_in + b_in)`, or the embedding gather and the mean-pool over positions in
   ascending position order divided by the position count;
2. trunk layers in ascending order — `h @ (W_ℓ ⊙ B_ℓ) + b_ℓ`, then `relu`, then either replace the carried
   vector (`plain`, `sparse`, and the kinds that read neither setting) or add the delta to it (`residual`);
3. the output layer — `h @ W_out + b_out`, `A` `float64` values, `A` read off `layout.actions` in both backends and
   never written down (`shapes.md` §2);
4. for `learn`, the same expressions again for `next_observation`, from the target copy (`rule.md` §3);
5. the backward pass — the explicit semi-gradient expression of `rule.md` §3, layer by layer in descending
   order, with the ReLU derivative taken from the pre-activation's sign and the sparse mask applied to the
   gradient as well as to the weight.

**`torch.autograd` is not used.** The backward pass is written out in both backends, because an autograd graph's summation
order is the framework's and not this design's, and holding one arithmetic order is the whole point of the axis. The torch
path therefore performs the same matrix products with torch's operators; that is what D-7's speed comparison is about, and
it keeps the parity claim a claim about expressions rather than about a framework's internals.

## 3. The parity mechanism: the tie-break's tolerance

Because §2's two evaluations can differ in the last units in the last place, the decision takes its answer
through the tolerance rule of `rule.md` §5 and never through a bare `argmax`:

    best  = max(values[i] for i in mask)
    tol   = 1e-9 × max(1.0, abs(best))
    index = min(i for i in mask if values[i] >= best − tol)

The smallest masked index within `tol` of the masked maximum. This is what makes the comparison backend-independent:
float64 drift over a chain of a few hundred multiply-adds is of order `1e-15` to `1e-13` relative, five or more orders
below `1e-9`; so a genuine difference larger than `tol` orders the two values the same way in both backends, and a
difference inside `tol` is inside it in both, where the smallest index wins. The rule is total, stateless and defined on
the mask alone — the index order it runs in is the **shape's** and never this module's (`shapes.md` §3) — and it is the
**only** place a comparison decides an action (`rule.md` §5). The exploration draw of `rule.md` §4 is a `hashlib` payload
precisely so it, too, is byte-identical across backends and hosts.

**What this does not promise.** Not equal values, not equal `td_error` to the last digit, and not equal
checkpoint bytes: two backends that have learned for a thousand steps will drift apart in their parameters, and
`learn`'s `td_error` is each backend's own arithmetic (`rule.md` §3). The parity assertion is FAM-13's: two
learners from one spec at one seed, differing only in `backend`, choose the same actions on the same readouts
(`battery.md` §3 FAM-13, `ladder.md` §5).

## 4. The dtype, and the one lazy import

**dtype.** Every parameter, every intermediate and every accumulation is `float64` — `numpy.float64` and
`torch.float64`, stated explicitly and never left to a default. The observation arrives as the encoder declares
it (`float32` or `int32`, `features/surface.md` §5) and is **cast** to the arithmetic's type on entry: exact for
`float32`→`float64` and for an `int32` id. `float64` is the choice because the drift argument of §3 needs
headroom: at `float32` a chain of a few hundred accumulate steps drifts at `1e-7`, which is close enough to a
tolerance wide enough to be meaningful that a genuine near-tie could fall on either side.

**The lazy import.** `import torch` happens **inside** `torch_backend.py`, on the first torch learner's build;
`engine`'s one granted call, `equity`, is imported the same way — inside the oracle's policy — because
`engine`'s modules hold `pokerkit` at module level and an eager import would leak it. Consequences L4 must
hold: `__init__.py`, `declarations.py`, `model.py`, `rule.py`, `checkpoint.py`, `policy.py` and `baselines.py`
import neither at module level; a numpy learner's every path is torch-free; and a unit case asserts both
absent from `sys.modules` after a numpy build and a numpy `load` (`README.md` §6, `guardrails.md` G6).

**CPU only.** Every tensor is created on CPU — no `.to(device)`, no `torch.set_default_device`, no
`torch.cuda.*`, no `device=` argument anywhere, and `torch.cuda.is_available()` is never consulted. Exactness is
promised on CPU, which is the sandbox and an audience laptop (D-8, `protocol.md` §6), and no test may depend on
a GPU: the sandbox denies the device nodes, so a GPU-dependent case would fail for the environment's reason and
not for the design's (`strata/platform.md`). A user-started GPU run is the run's business and its device is
recorded by `training`, not here (`learner.md` §8).
