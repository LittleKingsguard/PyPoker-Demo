# agents — the game shape

- **Owner:** the second declared game shape at this module's edge (D-29, ASM-37, ASM-40): the catalogue restated in
  `declarations.py` and why the width is a **reading**, the head `W → A` and the layout's `actions` field (§1–§2), the
  `A`-index decision space, `rule.decide`/`decide_greedy` and the `tie` flag (§3), the two exploration modes (§4), the
  container's format 4 and `game` field (§5), the refusals (§6) and what the shape does not move (§7)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `docs/L2/agents/shapes.md` §1–§7 (the contract this realises), `architecture.md` §1–§2, §5,
  `checkpoint.md` §2.1–§3, `restore.md` §2, `rule.md` §4–§5, §7, `errors.md` §2–§3, `guardrails.md` §G5, §G10, §G18

Split out of the seven documents that each stated the fixed game's three-index head as **the** head, when the second
shape reached them (`docs/L2/agents/shapes.md` §1). Each of those keeps its section and one-line pointers here.

## 1. The catalogue is restated once, and the width is read

Nothing below an entry point imports another project module (`module-map.md` §2, D-13), so the shape catalogue is
**restated** in `src/agents/declarations.py` — the two names and their order, default first:

    SHAPE_NAMES = ("fixed-limit-20", "no-limit-100")      DEFAULT_SHAPE = SHAPE_NAMES[0]
    EXPLORATION_MODES = ("schedule", "off")

`engine.game_shapes()` is **not** granted to this module (`module-map.md` §2, `docs/L2/agents/learner.md` §7), and only
the names are restated: the join battery holds `SHAPE_NAMES` equal to that catalogue's key order, the same restatement
`features` makes for the same reason (`docs/L2/agents/shapes.md` §1). A third shape would be a third name here.

**`A` is a reading, never a literal.** `declarations.actions_for(shape=None)` returns
`len(features.action_space(shape=require_game(shape)))`, so the head's width — and with it the parameter count — is the
shape's **descriptor count**, one entry per descriptor of that shape's declared index order. That is why no backend, no
table and no formula in this module carries a `3` or a `6`: a per-backend constant is one shape's head spelled twice,
which D-19's "no caller branches on it" forbids (`docs/L2/agents/shapes.md` §2, ASM-40, `sizing.md` §6). `features` is
imported inside `actions_for` and nowhere else, so the one granted call is the one statement of the width.

`require_game(value, entry)` resolves a name on the same rule `features` resolves it: `None` **is** the default shape —
the absence of a name, not a defaulting of one — while a name the catalogue does not carry, a non-string included, is
refused naming the entry point, the value and `tuple(SHAPE_NAMES)`. Nothing is ever substituted for a name.

## 2. The head is the shape's: `W → A`, and `A·W + A`

`model.Layout` carries an `actions` field, one `int`, and it is the only thing about the output layer that is not a
constant of the kind: `w_out` is `(offset, actions·W)`, `b_out` takes `actions` slots, and `count` ends with
`A·W + A` (`architecture.md` §2, §5). Both backends therefore read `layout.actions` where they read a `3` before —
`reshape(W, A)`, the bias slice, the one-hot `chosen` vector of the backward pass and its bias block — so the two
arithmetic orders of `backends.md` §2 stay one order at either width.

| Shape | `A` | The output term | `param_count` at `I = 203`, `W = 36`, `D = 2` |
|---|---|---|---|
| `fixed-limit-20` (default) | 3 | `3·W + 3`, today's formula | `7344 + 2664 + 111 = 10,119` — today's six rungs unmoved |
| `no-limit-100` (D-29) | 6 | `6·W + 6` | `7344 + 2664 + 222 = 10,230`, which `training`'s budget re-matches |

**At `A = 3` the arithmetic is bit-identical to the formula it replaces**: the same `count`, the same offsets, the same
draw sequence — the output matrix is drawn at `(W, 3)` exactly as before — and the same parameter values, which is what
keeps a default-shape training run's checkpoints byte-identical (`architecture.md` §4, ASM-40). The three private
signatures `tests/agents/` imports keep their positional arity and gain a trailing `actions=None`:
`_param_count_for(kind, width, depth, sparsity=0.0, actions=None)`, `_initial_parameters(kind, width, depth, sparsity,
seed, actions=None)` and `layout_for`/`initial_draw`, where `None` resolves through `declarations.actions_for(None)` —
the default shape's count, still a reading (`rule.md` §8). A learner resolves `A` once, at construction, from its spec's
`game`; `learners()` keeps its five keys and gains no sixth (`docs/L2/agents/surface.md` §3, §4).

## 3. The `A`-index decision space, `decide`/`decide_greedy`, and the `tie` flag

`act` and `learn` decide over `0 .. A−1` in the shape's **declared** order, which this module never defines and never
re-derives: `fold` 0, `check-call` 1, then the raise bands, and on the second shape `raise-quarter` 2, `raise-half` 3,
`raise-all-in` 4, `raise-minimum` 5 — the measured price order, worst first, deliberately not monotone in amount
(`sizing.md` §3, ASM-37). The mask is `features.legal_indices`' position-aligned, distinct, never-empty sequence.

- **The mask is checked against the learner's own range**, which is how a decision from another shape is caught: an
  observation cannot betray its shape, both declaring the same widths, dtype and token vocabulary, so an index outside
  the learner's vocabulary is refused naming `act`, the learner's shape, that shape's range and the offending index,
  before any arithmetic (`docs/L2/agents/shapes.md` §3, §6). `learn` applies the same range to `action`, `legal` and
  `next_legal`, so a transition recorded on another shape is refused rather than read as one of this learner's indices.
- **`rule.decide` returns `(index, tie)`** and `rule.decide_greedy(values, mask)` returns the same pair: the greedy arm
  is **one function**, which `decide` falls through to, so the two modes cannot disagree on an index. `decide_greedy`
  consults `_tie_break` and the tolerance and nothing else — no payload, no key, no generator.
- **The `tie` flag** is true exactly when the **greedy arm** chose the index **and** at least two masked values sat
  within `TOLERANCE` of the masked maximum, so the tie-break and not a strict maximum chose it; false on a one-element
  mask, and false wherever the exploring arm drew the index, no maximum having been consulted (`records.md` §6, §15,
  `sizing.md` §3). `act` returns `{"action": <plain int>, "tie": <bool>}`; it is the learner's own record and not
  surface (`records.md` §6), and the census reads it to recompute its distributional conjuncts twice.
- **The tie-break is unmoved.** `rule._tie_break` still returns the **smallest** masked index within
  `1e-9 × max(1, |best|)` of the masked maximum (`rule.md` §5, `backends.md` §3); only the order it is applied to is
  the shape's, which is what keeps a tie resolving toward a worse-priced band (`sizing.md` §3, ASM-37).

## 4. The exploration mode is the policy's

`as_policy(learner, encoder, seed, exploration="schedule")` takes one mode with two declared values, and
`declarations.require_exploration(value, entry)` refuses anything else naming `as_policy`, the value and both modes:

- **`schedule`** — the default and today's behaviour exactly: `rule.decide`'s keyed draw at the learner's snapshotted
  position and the policy's own seed, the exploring arm below the annealed rate and the tie-break above it
  (`rule.md` §4–§5).
- **`off`** — the decision is `rule.decide_greedy`, and **no generator is constructed at all**: `rule.decide`,
  `rule._draws` and the PCG64 construction are unreachable on that path, so two `off` policies built from one learner
  and one encoder at **different seeds decide identically**, and an `off` policy advances no generator position
  (`docs/L2/agents/shapes.md` §4, `sizing.md` §4).

**The mode is the policy's, and never the hyper block's.** `declarations.HYPER["exploration"]` stays the six
declarations' one schedule, annealed to 0.05 and never to 0, `learners()` grows no key, and no mode edits it: a mode
that changed the schedule would change training itself (`rule.md` §6, D-19, D-20). Rejected: reading the ε = 0.05 tail
as "nearly greedy" — 5 % of a six-index space is a systematic contamination of exactly the classes a census counts.
The policy carries the learner's `game` beside its `learning_rule` and `utility` and decodes with
`features.decode_action(index, shape=<the learner's game>)`, so a six-index learner returns one of that shape's six
descriptors; `game` is named clearly because it is **not** one of the two attributes `e2e-surface.md` §2 declares
(`rule.md` §7).

## 5. The container: format 3 for the default shape, format 4 with a `game` field

| Written by | `format_version` | `game` | Read as |
|---|---|---|---|
| the default shape | `3`, today's container | **absent**, so a fixed-limit save's two members are byte-identical to today's | the default shape |
| any other declared shape | `4` | **required**, written immediately after `kind` | the shape it names |
| a version 1, 2 or 3 file, the 18 shipped ones included | unchanged | must not carry one | the **default** shape, as an absent `learning_rule` reads as the catalogue's first |

`SUPPORTED_VERSIONS` is `(1, 2, 3, 4)`, and the version rules are `checkpoint.md` §3's, one row per field:
`load` **requires** `game` on version 4, refuses a version-4 container **naming the default shape** — a field its writer
would never have written, a default-shape save writing version 3 — refuses a version-1-to-3 container that **carries**
one, and refuses a version-4 `game` outside the catalogue naming it and the declared names, never defaulting it. A
`load` spec naming a shape its container contradicts is refused **naming both** shapes, as a contradictory `seed`,
`learning_rule` or `utility` already is (`checkpoint.md` §3, `docs/L2/agents/surface.md` §9, ASM-40).

`_rebuild` resolves `actions` from the container's shape and hands it to the layout, so `params.count`, `params.length`
and the carried array's own length are all checked against the head that shape declares — the check a restore already
makes, now against `A`, so a file whose `game` and whose `params` disagree is refused naming the field and both values
(`restore.md` §2). **The 18 shipped version-1 containers load unchanged as the default shape and none is rewritten**
(`docs/L1/shapes.md` §5, ASM-40); rejected: always writing version 4, which moves every future fixed-limit save's bytes.

## 6. The refusals the shape adds

| Where | What is refused | The message names |
|---|---|---|
| `build_learner` | a spec's `game` outside the catalogue, a non-string included | `build_learner`, the value and `tuple(SHAPE_NAMES)` |
| `act`, `learn` | a mask, an `action` or a `next_legal` naming an index the learner's shape does not have | the entry point, the learner's shape, that shape's range and the index |
| `as_policy` | an exploration mode outside the two | `as_policy`, the value and both modes |
| `load(path)` | a version-4 container without `game`, one naming the default shape, a version-1-to-3 one carrying it, or a `game` outside the catalogue | the field, the value and the declared names |
| `load(spec)` | a spec whose `game` disagrees with the shape the container is read as | the key and **both** shapes |

`UnknownShape` and `UnknownExploration` are the two new classes of `errors.py`, which is why it holds twenty-one
(`errors.md` §2). Every refusal is raised before a parameter is drawn, before a file is rebuilt and before a step is
taken, and none is coerced onto the default (`docs/L2/agents/surface.md` §1, §2).

## 7. What does not move, and what is left to L4

Both encodings keep their slot counts, block widths, dtype and token vocabulary; the readout keeps its eleven facts; the
two learning rules, the two utilities, the six hyper-declarations and the six baselines stay one declaration
(`docs/L2/agents/shapes.md` §7). What moves is the head's width, the container's version and the exploration mode —
this module's — and the amount normalisers and index order, which are `features`' and the shape's.

L4 implements `SHAPE_NAMES`' spelling, `require_game`, `actions_for`, `require_exploration`, the layout's `actions`
field, `decide_greedy`, the `tie` count, the two-mode policy and the version rules **as stated**; it may not write a `3`
into a backend, take a draw on the `off` path, or write a `game` field into a default-shape container (`guardrails.md`
G5, G10, G18). The shape's own consequences for `evaluation` and `training` are those documents' (`guardrails.md` G18).
