# agents — the learning-rule catalogue

- **Owner:** the catalogue of two rules (D-19, ASM-7, ASM-25): each rule's target, the contract they answer, the mask,
  the reward, the update, the exploration, the draw, the tie-break, the hyper-declarations and `learn`'s return — and
  the third catalogue's member, its step count and its **fallbacks**
- **Ceiling:** 165 lines. At the ceiling, split by owner — never append
- **Rev:** 9 · **Date:** 2026-11-11 — D-43: the member's residual is the **mean** over the steps a transition takes and the terminal transition takes its `A` (§3)
- **Read with:** `README.md` §5, `architecture.md` §2–§5, `backends.md` §3, `checkpoint.md` §3, `utility.md` §2–§4

## 1. Why a catalogue, and what it promises

The learning rule is a **parameter**, not a constant: `rules.md` §2's catalogue holds exactly two members,
`masked-q-learning` and `double-q-learning`, and the spec selects one (D-19, ASM-7, ASM-25). The diagnosis measured what
a maximum of three noisy estimates does to a terminal reward that must resolve a 0.06–0.7 chip difference, and it
converges on raise-almost-always (D-19); the second member decouples selection from evaluation, and the first stays the
declared default, so a spec naming no rule is unchanged (`rules.md` §4).

`utility.md` §2's catalogue is the **sibling axis**: the same spec selects a terminal-reward member the same way; a name
outside either catalogue is refused **by name** — `UnknownRule` or `UnknownUtility` — and a name outside the **third**
catalogue's `counterfactuals`, `none` first and `reveal-counterfactual` second (§3), is `UnknownCounterfactual`
(`utility.md` §3, `rules.md` §4, `counterfactual.md` §6, D-20, D-43).

Both members answer **one contract** (`rules.md` §3): a learner is a function from an observation and a legal mask to `A`
values — the shape's descriptor count, three or six (`shapes.md` §2–§3) — and an index outside the mask is never read,
never a target and never updated (D-2). A rule changes a target's arithmetic and nothing else — not the state layout,
the parameter count, the exploration or the vocabulary — so no caller branches on either axis, and "one state and one
decision give one answer": `act` reads the parameters, the position, the seed and the decision handed, and nothing else
(no counter, no stream, no cache), so two calls at one state return one index and a restored learner answers as its
saved one did (`surface.md` §1, `protocol.md` §5, ASM-5, D-3, D-19, D-20).

## 2. The two targets, the mask and the reward

For one transition record (`records.md` §4) — with a required `episode` and an optional `counterfactual`, D-43 — its
`action` `a` and the online values `q = f(observation)`:

- **`masked-q-learning`** aims at `reward + discount × max(q'[i] for i in next_legal)`, `q'` being the **target
  copy**'s values for `next_observation` — never the online parameters' (§3);
- **`double-q-learning`** lets the **online** parameters choose the index, `rule._tie_break(q_next, next_legal)` over
  their values at `next_observation` (§8), and reads that index's value from the **target copy**: selection by one
  estimate, evaluation by another, so an upward-biased maximum no longer sets the bootstrap (ASM-10, `rules.md` §3);
- **the mask is the contract**: every maximum and index runs over `next_legal` only, so an index outside it is never a
  candidate; `q[a]` is read at the transition's own `action`, validated in its `legal` mask first, a terminal
  transition carries its own `next_legal` and `learn` reads none of it, and no empty mask is legal (`surface.md` §7,
  D-2, `features/surface.md` §8);
- **the reward is the learner's utility's** (ASM-12, ASM-28): that utility's terminal value — `net-chips`' unshaped
  delta, `stack-shortfall`'s re-expression — at the seat's terminal decision and `0.0` at every other one; with
  **terminal**, `target = reward` under either rule: no successor, no term, no clip (`utility.md` §4, D-20).

## 3. The update, and the one place a rule branches

- **One path, one branch.** `learn` reads `learner.rule` inside the target's arithmetic (§2) and nowhere else: the
  validation order, the loop, the `|td|` accumulation, the SGD step, the refresh counter and the position are shared;
  `act`, `param_count`, `save`, `load`, `as_policy` and both callers are rule-free (`rules.md` §3).
- **The batch is the caller's**: consumed in its order, one semi-gradient step per transition, never sampled, sorted,
  shuffled, deduped or replayed — no buffer, no priority (`surface.md` §7, `ladder.md` §5).
- **One step per transition, in order** (or one per legal action of a resolved transition, below). For transition *k*: `q` and `q'` come from the state *before
  step *k*; `target` from §2, then `td = target − q[a]`, `|td|` added to the batch's total, then
  `θ ← θ + α·td·∂q[a]/∂θ` — a **semi**-gradient, the derivative taken with the target held constant, and **plain SGD**:
  no momentum, weight decay, clipping or scaling, in whichever backend owns the parameters (`backends.md` §2).
- **`reveal-counterfactual` is a step count, not a second path**: its target is the transition's own `counterfactual`,
  not a bootstrap; one `forward` pass, **all** its residuals `value − q[i]` read from that pass first in the legal mask's
  ascending order, then **one step per legal index** on that same cache. Its residual is a **mean**: each step applies
  `(v_i − q[i]) / A`, `A` the number of steps **that transition** takes — `len(legal)`, never the shape's descriptor
  count, which would be a fraction of a step — and a **terminal** transition takes its `A` steps exactly as any other,
  the seat's last decision being where the outcome is known. Only `None`, and one carrying `None` at an index of its own
  legal mask, take the ordinary single step — a partial resolution is not a resolution (`counterfactual.md` §4–§6, D-43).
- **Two divergence guards sit inside that order** (`divergence.md` §2): a non-finite `td` refuses **before** `|td|` is
  accumulated and before the step, and a step that left any parameter non-finite refuses **after** it; both name *k* —
  and, on the member's path, the action index too.
- **The target copy and its counter.** A second, non-trainable copy of every parameter, equal at construction, is the
  source of every bootstrapping value under either rule; it is refreshed from the online parameters, in
  `architecture.md` §4's declaration order, every `target_update_interval` consumed **steps** — 200 transitions under
  `none`, `200 / A` of them under the member — and the counter resets. It is never a parameter (ASM-10) and rides in a
  checkpoint (`checkpoint.md` §2).
- **Any non-empty batch is legal**: `batch_size` (§6) is the ladder's granularity, never a precondition — a batch of
  6 or 200 is consumed in the caller's order, each record's own mask passed (`errors.md` §4).
- **The return**: exactly two keys — `td_error`, the batch's mean absolute **raw** residual over its **steps** — the
  magnitude taken **before** the divisor: `len(batch)` under a rule, one per legal action of a resolved transition; `0.0`
  when no step was taken — a plain `float` — and `transitions`, the records consumed as a plain `int` (`surface.md` §7, `records.md` §7).
- **The position advances here and nowhere else**: `len(batch)` is added to the schedule position (§4) last, so a refused
  batch has no effect and no other entry point moves it; it counts **transitions**, never steps (`surface.md` §1, `counterfactual.md` §6).

## 4. The exploration: a schedule and a keyed draw

**The rate.** With `start`, `end`, `samples` from §6 and `n` the position (an `int` from `0`):
`epsilon(n) = start + (end − start) × min(n, samples) / samples`, so the rate is `start` at `n = 0`, `end` from
`n = samples` on, and linear between (`surface.md` §3).

**The key.** One derivation, shared by `act` and `as_policy`, which must decide as `act` does (`surface.md` §10):

    payload = b"pypoker-agents/explore/v1" + b"\x1f" + str(seed).encode("ascii") + b"\x1f"    # the learner's, or the policy's
            + family.encode("ascii") + b"\x1f"       # b"dense-numeric" or b"token-sequence"
            + observation_bytes + b"\x1f" + ",".join(str(i) for i in sorted(mask)).encode("ascii")
    key     = hashlib.sha256(payload).digest()
    draws   = numpy.random.Generator(numpy.random.PCG64(int.from_bytes(key[:16], "big")))
    u, v    = draws.random(), draws.random()   # two float64 draws, u first, both always taken

`observation_bytes` is `numpy.ascontiguousarray(numpy.asarray(observation).astype("<f8" or "<i8")).tobytes()`, `<f8` for
a dense observation and `<i8` for a token one. Three properties are the point: it is **backend-independent** (sha256's
bytes, never `hash()`'s), **order-independent** (mask sorted) and **the learner's own** (seed in the payload) (ASM-2).

**The decision.** `mask` ascends (`features/surface.md` §8); the pair comes back from **one** function per arm —
`rule.decide(...)` takes the draw and falls through to `rule.decide_greedy(values, mask)`, which takes none:

    if u < epsilon(n):  index, tie = mask[min(int(v × len(mask)), len(mask) − 1)], False
    else:               index, tie = rule.decide_greedy(values, mask)      # §5, and whether it was a tie

The exploring arm is a uniform draw over the legal indices and the greedy arm is §5, so `act` advances nothing; the
learner's generator serves construction only (`architecture.md` §4).

**The two exploration modes are the policy's.** `as_policy`'s fourth argument selects one, `schedule` — the default — or
`off`, where the decision is `rule.decide_greedy` alone and **no generator is drawn from at all**: `rule.decide`,
`rule._draws` and PCG64 are unreachable, so two `off` policies decide identically (`shapes.md` §4, `sizing.md` §4, D-19).

## 5. The tie-break among equal masked values

Two values equal — or equal within the rounding — must not let the backend decide: the rule is total and stateless, and
`learn` reads `double-q-learning`'s index with it (§2, `backends.md` §3):

    values = the A online values;  best = max(values[i] for i in mask)   # the masked maximum, as computed
    tol    = 1e-9 × max(1.0, abs(best))              # relative, with an absolute floor
    index  = min(i for i in mask if values[i] >= best − tol)

"The smallest masked index within `tol` of the masked maximum": total, deterministic, and a non-finite masked value
refuses by name before `max` (`backends.md` §3, `divergence.md` §2). The order is the **shape's**, so a tie resolves
toward a worse-priced band, and `tie` is true exactly when that tie-break chose the index (`shapes.md` §3, ASM-37, §15).

## 6. The fixed hyper-declarations `learners()["hyper"]` publishes

Six keys, one value each, for **all three** catalogues — every rule, every utility and every counterfactual member: `hyper` is one declaration, not a per-member block, so a swap on any axis is one axis — but the member's own **step count** is its contract's, and it moves the update count (`rules.md` §2).

| Key | Value | Why this value |
|---|---|---|
| `learning_rate` | `0.001` | a plain-SGD step small enough that a `td_error` of order the hand's stake (ASM-12) does not overshoot a fresh He-initialised network (`architecture.md` §4) |
| `batch_size` | `32` | the granularity the ladder's loop hands `learn`; a rule stated per transition needs no other meaning (§3) |
| `target_update_interval` | `200` | **steps**, not batches: the target copy follows the online parameters every 200 consumed steps — 200 transitions under `none`, `200 / A` of them under the member (§3) |
| `optimiser` | `"sgd"` | plain SGD, the one family both backends express as one expression (§3, D-7) |
| `exploration` | `{"start": 1.0, "end": 0.05, "samples": 2000}` | §4's schedule: full exploration at the first decision, annealed linearly to 5% over the first 2,000 decisions — a live run's first half, a hand being a handful of decisions (`ladder.md` §6) |
| `discount` | `0.99` | the bootstrap's weight, fixed here because `ladder.md` §3 names the others and neither rule's target can be computed without it (ASM-7) |

## 7. The policy, and what the rule never does

`as_policy(learner, encoder, seed, exploration="schedule")` snapshots its parameters, position and encoder at build
time and returns a callable `policy(readout, legal_actions)` that encodes the readout and masks by
`features.legal_indices(readout["legal"])`, decides by §4–§5 with its **own** seed and mode, and returns
`features.decode_action(index, shape=<the learner's game>)`, always in the shape's vocabulary (`surface.md` §10,
`shapes.md` §3). At its own seed and position it decides as `act` does, and a later `learn` cannot change it: the
snapshot is a copy (ASM-5). It also carries `learning_rule`, `utility`, `counterfactual` and `game` — what `evaluation`
labels a table's members by, none of them read by a decision (`e2e-surface.md` §2, D-19, D-20, `counterfactual.md` §6).

## 8. The internals a unit battery may drive, and what is left to L4

Eight spellings are **battery-facing** — nothing exports them, no caller outside `tests/agents/` may use them, and L4
implements exactly these names (`battery.md` §5, D-13); the step tail §3's two paths share is L4's helper, not one of them.

| Name | Signature | One-line contract |
|---|---|---|
| `rule._epsilon` | `_epsilon(position)` | §4's rate at that schedule position: `start` at `0`, `end` from `samples` on, linear between |
| `rule._decision_key` | `_decision_key(seed, family, observation, mask)` | §4's payload's `sha256` digest, from which a caller takes `u` then `v` exactly as §4 does |
| `rule._draws` | `_draws(seed, family, observation, mask)` | §4's two `float64` draws, `u` then `v`, from `_decision_key`'s digest — the one generator a `schedule` arm builds |
| `rule._tie_break` | `_tie_break(values, mask)` | §5's one index for `A` values and a mask: no seed, no state, no backend — the index `learn` reads `double-q-learning`'s bootstrap at, over the online values (§2) — and it refuses a non-finite masked value by name (`divergence.md` §2) |
| `rule.decide_greedy` | `decide_greedy(values, mask)` | §5's greedy arm alone, as `(index, tie)`: the tie-break over the masked maximum and whether it chose — no seed, no state, no draw (`shapes.md` §3) |
| `model._param_count_for` | `_param_count_for(kind, width, depth, sparsity=0.0, actions=None)` | `architecture.md` §5's sum at those settings, `I`/`V` the kind's declared `observation_size` and `A·W + A` its output term (`shapes.md` §2) |
| `model._initial_parameters` | `_initial_parameters(kind, width, depth, sparsity, seed, actions=None)` | `architecture.md` §4's steps 1–3 as one 1-D `float64` array in declaration order — the checkpoint's `[0, P)` — `sparsity` changing nothing |
| `checkpoint._read_metadata` | `_read_metadata(path)` | `checkpoint.md` §2.1's object read from `path`'s `metadata.json`, refusing as `load` does |
