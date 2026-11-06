# agents — the seven kinds

- **Owner:** the seven architecture kinds, each kind's layer stack, how `width`, `depth`, `sparsity` and
  `residual` are read, the one initialisation order, the parameter formula, and the sizing contract
- **Ceiling:** 160 lines. At the ceiling, split by owner — never append
- **Read with:** `README.md` §5, `rule.md` §4–§5, `backends.md` §2–§3, `checkpoint.md` §2

## 1. The seven names, and the two families

The seven kind names are `learners()`'s catalogue keys, spelled exactly: `naive-stack`, `token-embedding`,
`wide`, `deep`, `sparse`, `residual`, `plain` (`surface.md` §3). A variant entry's `architecture.kind` uses one
of these spellings and no other, and this module never infers a kind from a variant's *name* — `dense` and
`deep` are rung variant labels (`ladder.md` §2), not kind names (D-3, `records.md` §2).

| Kind | `observation` | `observation_size` | Input block | Trunk | Reads |
|---|---|---|---|---|---|
| `naive-stack` | `dense-numeric` | 203 | dense `I → W`, bias, ReLU | `D` layers `W → W` | `width`, `depth` |
| `token-embedding` | `token-sequence` | 96 | embedding `V → W`, mean-pooled | same | `width`, `depth` |
| `wide` | `token-sequence` | 96 | embedding `V → W`, mean-pooled | **one** layer `W → W` | `width` |
| `deep` | `token-sequence` | 96 | embedding `V → W`, mean-pooled | `D` layers `W → W` | `width`, `depth` |
| `sparse` | `token-sequence` | 96 | embedding `V → W`, mean-pooled | `D` masked layers `W → W` | `width`, `depth`, `sparsity` |
| `residual` | `token-sequence` | 96 | embedding `V → W`, mean-pooled | `D` layers `W → W`, each added to the carried vector | `width`, `depth` |
| `plain` | `token-sequence` | 96 | embedding `V → W`, mean-pooled | `D` layers `W → W`, replacing the carried vector | `width`, `depth` |

Every kind ends in the same output layer, `W → 3` with a bias and no activation: the three values `rule.md` §5
takes a mask over. Every trunk layer is `W → W` with a bias and a ReLU (`residual` excepted only in *how* its
output is combined, §2). `I` is the dense input width and `V` the token vocabulary; both come from the learner's
sizing record, never from a document (§6, D-3).

The catalogue value for each kind is a plain record of three keys, `name`, `observation` and
`observation_size`, in that order (`surface.md` §3). `naive-stack`'s 203 and the six token kinds' 96 are the
declared sizes; each is the value an encoder-less build is sized from, and each is what an encoder's
`observation_spec` is checked against (§6).

## 2. The layer stacks, exactly

**The input block.** `naive-stack` applies `relu(x @ W_in + b_in)` to a dense observation of width `I`, with
`W_in` of shape `(I, W)` and `b_in` of shape `(W,)`. The six token kinds gather the embedding table's rows for
the observation's token ids, in the observation's own position order, and **mean-pool** them: `h = mean(E[ids],
axis=0)`, a sum over positions divided by the number of positions. The table `E` has shape `(V, W)` and no bias;
row `0` is a row like any other, because `features`' pad is an id and not a mask (`docs/L3/features/README.md`
§5, `learner.md` §3).

**The trunk.** For layer `ℓ = 1..D`: `z_ℓ = h @ W_ℓ + b_ℓ` with `W_ℓ` of shape `(W, W)` and `b_ℓ` of shape
`(W,)`, then `h ← relu(z_ℓ)`. The three bullets below state the kinds that differ from that default, and the
difference is the rung's axis (`ladder.md` §2, D-3):

- `residual`: `h ← h + relu(z_ℓ)` — each sublayer **adds a delta to the carried representation**, so "do nothing"
  is the default and the path adds no parameter (`strata/brief.md` §2, R6);
- `plain`: `h ← relu(z_ℓ)` — the same stack without the residual connection, which is R6's control;
- `sparse`: `z_ℓ = h @ M_ℓ + b_ℓ`, where `M_ℓ` is `W_ℓ` with exactly `k` of its `W²` slots kept and the rest
  pinned to `0.0` by a fixed boolean mask `B_ℓ`; `M_ℓ = W_ℓ ⊙ B_ℓ` is materialised before the matmul so the
  expression evaluated is one expression in both backends (§4, `backends.md` §2).

`wide` is the kind whose trunk is **one** hidden layer of the declared width: its `depth` is declared (the spec
carries it, and `build_learner` requires a positive integer for it) and is **not read**, because a setting the
kind does not read is ignored (`surface.md` §4). `token-embedding`, `deep`, `plain` and `residual` are one
topology at three declared settings; what makes them distinct kinds is that a rung names the kind it varies and
`learners()` publishes it as one of the seven (`surface.md` §3, `ladder.md` §3).

**The output.** `q = h @ W_out + b_out`, `W_out` of shape `(W, 3)` and `b_out` of shape `(3,)`, no activation,
returned as three `float64` values in index order — index 0 fold, 1 check/call, 2 raise
(`features/surface.md` §2). The output layer is never sparse and never residual.

## 3. How the four settings are read

`width` and `depth` are **required** for every kind, both positive integers, refused otherwise naming the
setting (`surface.md` §4). `sparsity` and `residual` are optional: they are a setting the kind may not read, so
the kind's own value stands when the spec does not carry them — `0.0` connectivity and no residual path for the
kinds that read neither. No width or depth is ever defaulted; a bare kind name with no `sizes` carrying them is
refused (D-12, `surface.md` §4).

| Setting | Read by | Meaning |
|---|---|---|
| `width` | all seven | `W`: the embedding width, the trunk width and the output layer's fan-in |
| `depth` | all but `wide` | `D`: the number of `W → W` trunk layers |
| `sparsity` | `sparse` | `s ∈ [0, 1]`: the fraction of a trunk layer's `W²` weights pinned to zero, `k = round((1 − s)·W²)` kept. `k` is a function of `(W, s)` and the seed picks *which* slots, so a count never depends on the seed |
| `residual` | none | the kind *is* the statement: `residual` adds the delta, `plain` replaces. The setting in a variant entry mirrors the kind and is accepted and ignored |

`sparsity` is refused outside `[0, 1]` for every kind, whether or not that kind reads it (`surface.md` §4), and
`s = 0` and `s = 1` are legal: they are the dense layer and the bias-only layer, both well defined.

**The kind decides the connection; the spec's `residual` flag decides nothing.** `residual` adds the delta and
`plain` replaces whatever the flag says; the flag mirrors the kind and is not a fifth setting (`ladder.md` §2, R6).
A checkpoint's "in force" value is the resolved one: `kind == "residual"`, `0.0` for an unread `sparsity`.

## 4. The one initialisation order

Every learner is initialised in one documented order, from one generator, `numpy.random.Generator(
numpy.random.PCG64(seed))` with `seed` the spec's integer (`surface.md` §4, ASM-2). Both backends use **these**
values: the torch backend copies them into its tensors (`backends.md` §2), so two backends at one seed start
from bit-identical parameters.

1. The **input block**: the dense matrix `W_in` of shape `(I, W)`, or the embedding table `E` of shape `(V, W)`.
2. The **trunk layers** `ℓ = 1..D` in ascending order, each `(W, W)`.
3. The **output layer** `W_out`, `(W, 3)`.
4. The **sparse masks** (`sparse` only), layers `ℓ = 1..D` in ascending order: `B_ℓ` keeps the positions of
   `g.permutation(W²)[:k]`, sorted ascending. This step comes last, so the weight draws of a `sparse` learner are
   the draws its shapes would give any other kind.
5. The **target copy** is a copy of every value in 1–4's parameter order (§5, `rule.md` §3).

Each matrix is **He-normal**: `M = g.standard_normal(shape) * sqrt(2 / fan_in)`, `fan_in` the matrix's first
dimension. Each **bias** is exactly `0.0` and draws nothing, so the order is over weight matrices only. `D` and
`W` are read from the resolved settings of §3, so one spec's draw sequence is a function of its kind and its
numbers and of nothing else — which is what makes two learners from one spec one learner in every decision
(`surface.md` §4, ASM-10).

## 5. The parameter formula

`param_count` counts every value the update can change, and nothing else (`surface.md` §5, ASM-10). With `I` the
dense input width, `V` the vocabulary, `W` the width, `D` the depth and `k = round((1 − s)·W²)`:

    input block      naive-stack:  I·W + W            any token kind:  V·W
    trunk            D·(W²  + W)                      sparse:          D·(k + W)
    output           3·W + 3
    param_count      the sum of the three lines

So `naive-stack` is `I·W + W + D·(W² + W) + 3W + 3`, each dense token kind is `V·W + D·(W² + W) + 3W + 3`, and
`sparse` replaces the trunk term with `D·(k + W)` — the formula covers `s = 0` too, where `k = W²`. A kind's
count is a function of its kind and its four settings, and of nothing else: **not** a decision, **not** a step,
**not** a seed (the mask's size is `k`, not its contents), and the same number in both backends for one shape
(D-7, `ladder.md` §5).

**Not counted:** the target copy, the mask buffers, the schedule's constants and the position
(`learner.md` §3). **Counted:** the input block first, because the embedding table is trainable
(`learner.md` §3).

**An arithmetic check, not a declaration.** At `I = 203`, `W = 36`, `D = 2`: `7344 + 2664 + 111 = 10,119`. At
`V = 96`, `W = 50`, `D = 2`: `4800 + 5100 + 153 = 10,053`, and at `V = 96`, `W = 39`, `D = 4`: `3744 + 6240 +
120 = 10,104` — two token kinds at two widths and depths within 0.5% of one another, which is how ASM-10's
10,000 ±2% budget is reachable at all. Which numbers a rung declares is `training`'s (`ladder.md` §3, §4); note
that `sparse`'s trunk term `D·(k + W)` shrinks with `s`, so a sparse arm matches its dense mate by being declared
**wider** — that is what "connectivity varied at a matched budget" means (`strata/brief.md` §2, R5, ASM-10).

## 6. The sizing contract

A learner is complete when it is built, and it is sized one of two ways (`surface.md` §3–§4, D-3):

- **With an encoder:** from its `observation_spec`. A `dense-numeric` spec sizes the dense input as its
  `shape[0]` and a `token-sequence` spec sizes the embedding table as its `vocabulary`; the learner records
  the spec's `kind`, `representation`, `shape`, `dtype` and size as its **sizing record**. The spec's `kind`
  must equal the kind's declared family and its size the kind's declared `observation_size`, or the build is
  **refused naming both** — the declaration and the encoding are held equal by a refusal and not by a comment
  (`surface.md` §4, `learner.md` §6).
- **With no encoder:** from the kind's declared `observation_size` — 203 for `naive-stack`, 96 for the six
  token kinds — and the sizing record's `representation` is the encoding the kind's row declares
  (`flat-numeric`, `card-tokens`), with `shape` and `dtype` recorded as `null`, the encoder being the only
  thing that knows them (`e2e-surface.md` §3.3, `learner.md` §4).

That record is what `act`, `learn`, `as_policy` and `load` check an argument against, and what a checkpoint
carries so a member loads from its path alone (`checkpoint.md` §2, `surface.md` §9). An observation of the wrong
family, a dense one of the wrong width, or a token one carrying an id outside `[0, V)` is refused naming both
the observation and the learner (`errors.md` §3).

## 7. What is left to L4

Whether the trunk is a list of matrices or named attributes, whether the mask is a boolean array or a pair of index
arrays, and the rest of the private names — `_param_count_for` and `_initial_parameters` excepted (`rule.md` §8). Not
L4's: the seven names and their order, each kind's stack and what it reads, `k`'s definition, the five initialisation
steps, the formula of §5, and the both-names refusal of §6 (`guardrails.md`).
