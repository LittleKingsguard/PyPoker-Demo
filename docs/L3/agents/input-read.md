# agents — the token input read

- **Owner:** the token family's input block as D-61 bounds it (`normalisation.md` §3): the one squash every addressed
  embedding row is read through, its derivative and the resolution it costs, the block the forward cache carries and
  the two battery-facing spellings that expose it, what does not move, and where the module's battery asserts it
- **Ceiling:** 90 lines. At the ceiling, split by owner — never append
- **Read with:** `docs/L1/normalisation.md` §1, §3, §5, `architecture.md` §2, §5, `backends.md` §2, §4, `rule.md` §3,
  §8, `finiteness.md` §2, `checkpoint.md` §2, `README.md` §3, §5

## 1. The bounded embedding

The token family's slots are categorical ids and not magnitudes (`normalisation.md` §3), so the token path's only
magnitude is its input block: the embedding row the trunk reads. Each addressed row is now read through **one squash**,

    row = (1 + tanh θ_id) / 2

so every row lies in `(0, 1)` for every **finite** parameter value, and so does any mean of rows, whatever the table
holds. The trunk consumes `carried = mean over the observation's ids of row`, in the observation's own position order
(`architecture.md` §2), hence a value in `[0, 1]`: D-61's invariant, INV-2's second half (`normalisation.md` §5, D-61).
The table keeps its `V × W` slots, **no** bias and no extra parameter, so the input term stays `V·W` (`architecture.md`
§5), and row 0, the pad id, is a row like any other, squashed like any other (`architecture.md` §2, `learner.md` §3).

**It is one monotone squash and nothing else.** Not a clip on the table, not a per-observation renormalisation, not a
centring, and not a divisor: a divisor would need a bound the project cannot state for a learned table, and a clamp on
the table zeroes the gradient exactly where the reward scale has driven it (`normalisation.md` §3, `rule.md` §3). It is
the same function in both backends' forward passes, with its derivative in both backward passes (`normalisation.md` §3,
`backends.md` §2). **The dense family is untouched:** `relu(x @ W_in + b_in)`, with no squash anywhere in its forward or
backward path (`architecture.md` §2, `normalisation.md` §2).

## 2. The derivative, and the declared cost

The derivative of the squash is `d row / d θ = (1 − tanh²θ)/2 = (1 − (2·row − 1)²)/2`, read off the squashed row the
forward pass stored and not recomputed from `θ` (`backends.md` §2 item 5). For the token input block the backward pass
gathers, at each id the observation addresses, `(upstream / len(ids)) · (1 − (2·row − 1)²)/2`, summed over the positions
that carry that id — `upstream` the trunk's gradient at the input block, `rule.md` §3's semi-gradient with the target
held constant (`rule.md` §3). Both backends write out that expression by hand, with no autograd (`backends.md` §2 item 5).

**The cost, stated where the arithmetic lives and not hidden.** The squash compresses a row that has run far from zero,
so resolution is lost exactly where the reward scale pushed hardest: at `|θ| = 3` the slope is already `1e-2`, and at
`|θ| ≈ 20` it is below `1e-17` in `float64`, so a saturated row is `0` or `1` to the last bit with an effectively zero
gradient — `tanh`'s saturation, declared at `normalisation.md` §3 and not newly discovered here. It is why a table far
from zero inside the declared parameter band trains slowly rather than being clipped: a clamp would give exactly zero
there instead (`finiteness.md` §2, `normalisation.md` §3). **The bound is bought with the resolution of the far rows, and
both are the same fact** (`normalisation.md` §3).

## 3. What the forward cache carries

`backend.forward(state, layout, observation, target=False, need_cache=True) -> (values, cache)`, unchanged, and the
cache's keys are unchanged — `carried`, `layers`, `output`, `input` (`backends.md` §2). Only the token family's `input`
block changed meaning: it is now `(rows, ids)` — the `(n, W)` squashed rows **in the observation's own position order**
and the `int64` ids those rows were read at — instead of the raw `(V, W)` table. The rationale is the one the battery
and D-62's instrument read it by: the cache holds the block the backward pass differentiates through, so it holds the
value the trunk actually consumed; the trunk never sees the raw table, so a cache carrying the table would have to
re-apply the squash and would be a second statement of it (`normalisation.md` §6, D-62). The dense family's `input`
stays `(observation, pre-activation)` (`backends.md` §2 item 1).

**The two spellings this document declares are the ninth and tenth of `rule.md` §8's names:**

| Name | Signature | One-line contract |
|---|---|---|
| `numpy_backend.forward` | `forward(state, layout, observation, target=False, need_cache=True)` | §1–§3's block in NumPy: `relu(x @ W_in + b_in)` dense, `(1 + tanh θ_ids)/2` rows then their mean token |
| `torch_backend.forward` | `forward(state, layout, observation, target=False, need_cache=True)` | the same expressions in torch's operators, on CPU, in `float64` (`backends.md` §2, §4) |

Both are driven off a learner's own `state` and `layout` fields — `Learner.state`, `Learner.layout` (`rule.md` §8,
`architecture.md` §2, §5) — and nothing else sits below the ten entry points, since neither name is exported (`README.md` §3).

## 4. What this does not change

Widths, `param_count` — `V·W` for the input block (`architecture.md` §5) — the container's format and every field of it
(`checkpoint.md` §2), the dtype, `float64` in both backends (`backends.md` §4), the vocabulary and the seven kinds
(`architecture.md` §1), and the dense family's forward and backward (`normalisation.md` §2). The map stays at **50**
endpoints and no entry point or key is added (`e2e-surface.md` §4). The target copy is a copy of the same parameters and
is squashed on the same read (`architecture.md` §4, `rule.md` §3). A pre-change container still loads, but its values
mean something different, so it is read-only history (`normalisation.md` §1, D-61). Nothing about the reward, the rule,
the exploration or the tie-break moves (`rule.md` §3–§5, `utility.md` §4).

## 5. Where it is asserted

The module half, in `tests/agents/`, cases `AGT-20.1`–`AGT-20.5`: the cache's `input` is the mean of the addressed rows
read through the squash; a table at magnitudes far past the declared band, `±1e6`, still feeds the trunk a value in
`[0, 1]`; the backward pass carries the squash's derivative, so a step on the table is not zeroed and the gradient
matches the analytic derivative; the two backends agree on the same parameters and observation; and `param_count`, the
container round trip and the dense family's arithmetic are unmoved (§4, `architecture.md` §5, `checkpoint.md` §2).

It is the **module's** battery and not the layer's because no e2e surface exposes the input the trunk consumes, which is
the boundary `battery.md` §5 draws; the layer-level half of the same invariant is FAM-24 (`normalisation.md` §5). One
sentence on the instrument: this block is what D-62's grid reads, because the active-unit count in the trunk after
training is a measurement of the input path §1–§3 describes (`normalisation.md` §6, `battery.md` §5, D-62).
