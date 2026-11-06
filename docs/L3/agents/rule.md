# agents — the one learning rule

- **Owner:** masked Q-learning (ASM-7): the aim, the mask, the reward, the update, the exploration schedule,
  the keyed draw, the tie-break, the fixed hyper-declarations and what `learn` returns
- **Ceiling:** 165 lines. At the ceiling, split by owner — never append
- **Read with:** `README.md` §5, `architecture.md` §2–§5, `backends.md` §3, `checkpoint.md` §3

## 1. Why one rule, and what it promises

The ladder has one learning rule, the same at every rung: masked Q-learning over the three-index action
vocabulary (ASM-7). A learner is a function from an observation and a legal mask to three values; the value of
an index outside the mask is never read, never a target and never updated (D-2, `learner.md` §1). No entry
point takes a rung, a variant, an opponent or a hyperparameter, so no rung can carry a copy of the rule (D-3,
`surface.md` §1). It survives every rung because what a rung changes — the input block and the trunk's shape —
is outside it: aim, mask, reward, step, schedule and tie-break are all stated over "three values the learner
produced", and every one of the seven kinds produces three values (`architecture.md` §2–§3).

**"One state and one decision give one answer"** means: `act` reads the learner's parameters, its schedule position and
its seed, and the decision `(observation, mask)` it is handed, and nothing else — no call counter, no stream, no cached
previous decision — so two calls at one state and one decision return one index, a restored learner answers as its saved
learner did, and a policy at the learner's own seed answers as `act` does (`surface.md` §1, §6, §10, `protocol.md` §5, ASM-5).

## 2. The aim, the mask and the reward

For one transition record (`records.md` §4) with `action` `a` and the online values `q = f(observation)`:

- **terminal** (`terminal` true): `target = reward`;
- **otherwise**: `target = reward + discount × max(q'[i] for i in next_legal)`, where `q'` is the **target
  copy**'s values for `next_observation` — never the online parameters' (§3);
- **the mask is the contract**: the maximum runs over `next_legal` only, so an index outside it is not a
  bootstrapping candidate, and `q[a]` is read at the transition's own `action`, validated to be a member of
  that transition's `legal` mask before any arithmetic (`surface.md` §7, D-2);
- **the reward is unshaped** (ASM-12): the seat's net chip delta for the completed hand, delivered at that
  seat's terminal decision and zero at every other one; this module adds no term, no clip, no intermediate
  reward (`engine/surface.md` §9, `learner.md` §1).

`discount` is the one number masked Q-learning needs that `ladder.md` §3 does not name; §6 fixes and publishes it.

## 3. The update

- **The batch is the caller's.** `learn(learner, transitions)` consumes the sequence in the caller's order,
  one semi-gradient step per transition, and never samples, sorts, shuffles, dedups or replays it
  (`surface.md` §7, `ladder.md` §5). There is no replay buffer, no priority and no second pass.
- **One step per transition, in order.** For transition *k*: compute `q` and `q'` from the state *before*
  step *k*; form `target` (§2); `td = target − q[a]`; add `|td|` to the batch's total; then apply
  `θ ← θ − α·∇_θ ½(q[a] − target)²`, which is `θ ← θ + α·td·∂q[a]/∂θ`, `α` the learning rate and the
  derivative taken with the target held constant — a **semi**-gradient. Transition *k+1* sees the result.
- **Plain SGD**: no momentum, weight decay, clipping or per-parameter scaling; the step is that one
  expression, evaluated by whichever backend owns the parameters (`backends.md` §2).
- **A terminal transition carries the decision's own `next_legal`.** It has no successor and `learn` reads none (§2),
  and no empty mask is legal (`features/surface.md` §8), so both batteries pass the decision's own mask there.
- **The target copy and its counter.** A second, non-trainable copy of every parameter, equal at construction,
  is the source of every `q'`. It is refreshed from the online parameters only when the transitions consumed
  reach `target_update_interval`, after which that counter resets to zero; it is never counted as a parameter
  (`architecture.md` §5, ASM-10) and it is part of a checkpoint (`checkpoint.md` §2). A refresh copies every
  parameter in the declaration order of `architecture.md` §4.
- **Any non-empty batch is legal.** `batch_size` (§6) is the ladder's declared granularity and never a
  precondition: a batch of 6 or of 200 is consumed by the same rule, in the caller's order (`errors.md` §4).
- **The return.** One mapping with exactly two keys: `td_error`, the batch's mean absolute TD error
  (`sum(|td|) / len(batch)`) as a plain `float`, and `transitions`, the records consumed as a plain `int`
  (`surface.md` §7, `records.md` §7). `td_error` is finite because a non-finite observation is refused before
  any arithmetic (`errors.md` §3).
- **The position advances here and nowhere else.** The update adds `len(batch)` to the schedule position (§4)
  last, so a refused batch has no effect and no other entry point moves it (`surface.md` §1).

## 4. The exploration: a schedule and a keyed draw

The learner explores ε-greedily at a rate the schedule fixes, and the draw is **keyed by the decision**, never
by a stream position (`surface.md` §1, §6, `learner.md` §1).

**The rate.** With `start`, `end` and `samples` from §6 and `n` the schedule position (an `int` starting at
`0`, advanced only by §3):

    epsilon(n) = start + (end − start) × min(n, samples) / samples

so the rate is `start` at `n = 0`, `end` from `n = samples` on, and linear between (`surface.md` §3).

**The key.** One derivation, used by `act` and by `as_policy` — the policy must derive the same key to decide
as `act` does (`surface.md` §10):

    payload = b"pypoker-agents/explore/v1"
            + b"\x1f" + str(seed).encode("ascii")      # the learner's own seed, or the policy's
            + b"\x1f" + family.encode("ascii")         # b"dense-numeric" or b"token-sequence"
            + b"\x1f" + observation_bytes              # the canonicalisation below
            + b"\x1f" + ",".join(str(i) for i in sorted(mask)).encode("ascii")
    key     = hashlib.sha256(payload).digest()
    draws   = numpy.random.Generator(numpy.random.PCG64(int.from_bytes(key[:16], "big")))
    u, v    = draws.random(), draws.random()           # two float64 draws, u first, both always taken

`observation_bytes` is fixed by the family: a dense observation is
`numpy.ascontiguousarray(numpy.asarray(observation).astype("<f8")).tobytes()`, a token observation the same
with `"<i8"` — little-endian, so one decision hashes to one key on any host. Three properties are the point:

- it is **backend-independent**: `hashlib`'s bytes of the payload, never `hash()`'s process-salted value;
- it is **order-independent**: the mask is sorted before hashing and the observation's bytes are its own fixed
  layout, so a decision's key never depends on how many decisions came before it;
- it is **the learner's own**: the seed is in the payload, so two learners at two seeds explore differently on
  one decision, and one learner explores the same way however often it is asked (`surface.md` §6, ASM-2).

**The decision.** With `mask` ascending (it is, `features/surface.md` §8) and the position read before any
change:

    if u < epsilon(n):  index = mask[min(int(v × len(mask)), len(mask) − 1)]
    else:               index = the tie-break of §5 over the masked values

so the exploring arm is a uniform draw over the decision's legal indices and the greedy arm is §5
(`surface.md` §7). The learner's own generator, `numpy.random.Generator(numpy.random.PCG64(seed))`, serves
construction only (`architecture.md` §4); `u` and `v` come from the keyed generator, so `act` advances nothing.

## 5. The tie-break among equal masked values

Two values equal — or equal to within the arithmetic's own rounding — must not make the answer depend on which
backend computed them (`backends.md` §3). The rule is total, backend-independent and stateless:

    values = the three online values of the observation
    best   = max(values[i] for i in mask)            # the masked maximum, as computed
    tol    = 1e-9 × max(1.0, abs(best))              # relative, with an absolute floor
    index  = min(i for i in mask if values[i] >= best − tol)

"The smallest masked index whose value is within `tol` of the masked maximum": total (a masked index always qualifies),
deterministic (no state, no seed) and defined on the mask alone, so three values and a mask give one index in either
backend. `tol` is a design constant, not a tuned tolerance: `backends.md` §3 puts the two backends' drift far below it.

## 6. The fixed hyper-declarations `learners()["hyper"]` publishes

Six keys, one value each for the whole ladder (ASM-7, `surface.md` §3, `ladder.md` §3):

| Key | Value | Why this value |
|---|---|---|
| `learning_rate` | `0.001` | a plain-SGD step small enough that a `td_error` of order the hand's stake (ASM-12) does not overshoot a fresh He-initialised network (`architecture.md` §4) |
| `batch_size` | `32` | the granularity the ladder's loop hands `learn`; a rule stated per transition needs no other meaning (§3) |
| `target_update_interval` | `200` | transitions, not batches: the target copy follows the online parameters every 200 consumed transitions (§3) |
| `optimiser` | `"sgd"` | plain SGD, the one family both backends express as one expression (§3, D-7) |
| `exploration` | `{"start": 1.0, "end": 0.05, "samples": 2000}` | §4's schedule: full exploration at the first decision, annealed linearly to 5% over the first 2,000 decisions — a live run's first half, a hand being a handful of decisions (`ladder.md` §6) |
| `discount` | `0.99` | the bootstrap's weight, fixed here because `ladder.md` §3 names the others and masked Q-learning's target cannot be computed without it (ASM-7) |

The record is plain data, rebuilt and equal on every call; a variant entry's `learning_rule` and `hyper`
(`records.md` §2) are the run record's data and never an argument here (`surface.md` §4).

## 7. The policy, and what the rule never does

`as_policy(learner, encoder, seed)` snapshots the learner's parameters, its schedule position and the encoder at
build time and returns a callable `policy(readout, legal_actions)`: it encodes the readout with
`features.encode`, takes the mask from `features.legal_indices(readout["legal"])`, decides by §4–§5 with its
**own** seed, and returns `features.decode_action(index)` — always one of `legal_actions` (`surface.md` §10,
`features/surface.md` §9). At the learner's own recorded seed and the snapshotted position it decides exactly
as `act` does, §4's payload being identical; a later `learn` cannot change a policy already built, the snapshot
being a copy (`surface.md` §10, ASM-5). Nothing in §2–§5 keeps state: no replay, no running mean, no cached
forward pass, no call to the global `random` stream (ASM-2).

## 8. The internals a unit battery may drive, and what is left to L4

Six names are **private**: nothing in `src/agents/__init__.py` exports them and no caller outside `tests/agents/` may
use them (`battery.md` §5, D-13); an entry point may be refactored around them, but L4 implements exactly these
spellings, since `tests/agents/` imports them. Their bodies stay L4's; §4's payload, §6's values, §5's `tol`, the
aim, the mask, the step and the two returned keys never are (`guardrails.md`):

| Name | Signature | One-line contract |
|---|---|---|
| `rule._epsilon` | `_epsilon(position)` | §4's rate at that schedule position: `start` at `0`, `end` from `samples` on, linear between |
| `rule._decision_key` | `_decision_key(seed, family, observation, mask)` | §4's payload's `sha256` digest, from which a caller takes `u` then `v` exactly as §4 does |
| `rule._tie_break` | `_tie_break(values, mask)` | §5's one index for three values and a mask: no seed, no state, no backend |
| `model._param_count_for` | `_param_count_for(kind, width, depth, sparsity=0.0)` | `architecture.md` §5's sum at those settings, `I`/`V` the kind's declared `observation_size` |
| `model._initial_parameters` | `_initial_parameters(kind, width, depth, sparsity, seed)` | `architecture.md` §4's steps 1–3 as one 1-D `float64` array in declaration order — the checkpoint's `[0, P)` — `sparsity` changing nothing |
| `checkpoint._read_metadata` | `_read_metadata(path)` | `checkpoint.md` §2.1's object read from `path`'s `metadata.json`, refusing as `load` does |
