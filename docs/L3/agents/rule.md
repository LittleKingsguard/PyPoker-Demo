# agents — the learning-rule catalogue

- **Owner:** the catalogue of two rules (D-19, ASM-7, ASM-25): each rule's target, the contract they answer, the mask,
  the reward, the update, the exploration, the keyed draw, the tie-break, the hyper-declarations and `learn`'s return
- **Ceiling:** 165 lines. At the ceiling, split by owner — never append
- **Read with:** `README.md` §5, `architecture.md` §2–§5, `backends.md` §3, `checkpoint.md` §3

## 1. Why a catalogue, and what it promises

The learning rule is a **parameter**, not a constant: `rules.md` §2's catalogue holds exactly two members,
`masked-q-learning` and `double-q-learning`, and the learner spec selects one (D-19, ASM-7, ASM-25). One rule held the
whole ladder until the diagnosis measured what a maximum of three noisy estimates does to a ±20-chip terminal reward
that must resolve a 0.06–0.7 chip action-value difference: it takes whichever estimate drew positive noise and
converges on raise-almost-always (`strata/records/r2-plateau-diagnosis.md`). Double Q-learning is the second member
because it decouples action selection from action evaluation, the remedy that diagnosis names; the first stays the
catalogue's first member and so the declared default, which leaves a spec naming no rule unchanged (`rules.md` §4).

Both members answer **one contract** (`rules.md` §3): a learner is a function from an observation and a legal mask to
three values, and the value of an index outside the mask is never read, never a target and never updated (D-2). A rule
changes a target's arithmetic and nothing else — not the state layout, the parameter count, the exploration or the
vocabulary — so no entry point takes a rung, a variant, an opponent or a hyperparameter and no caller branches on the
rule (D-3, D-19); what a rung changes, the input block and the trunk's shape, is outside every rule (`architecture.md`
§2–§3), the mask, reward, step and tie-break being stated over three values every kind produces.

**"One state and one decision give one answer"** means: `act` reads the learner's parameters, its schedule position and
its seed, and the decision `(observation, mask)` it is handed, and nothing else — no call counter, no stream, no cached
previous decision — so two calls at one state and one decision return one index, a restored learner answers as its saved
learner did, and a policy at the learner's own seed answers as `act` does (`surface.md` §1, §6, §10, `protocol.md` §5, ASM-5).

## 2. The two targets, the mask and the reward

For one transition record (`records.md` §4) with `action` `a` and the online values `q = f(observation)`:

- **`masked-q-learning`** aims at `reward + discount × max(q'[i] for i in next_legal)`, `q'` being the **target
  copy**'s values for `next_observation` — never the online parameters' (§3);
- **`double-q-learning`** lets the **online** parameters choose the index, `rule._tie_break(q_next, next_legal)` over
  their values at `next_observation` (§8), and reads that index's value from the **target copy** — selection by one
  estimate, evaluation by another, so an upward-biased maximum no longer sets the bootstrap;
- **terminal** (`terminal` true), under either rule: `target = reward`, and no successor value is read;
- **the mask is the contract**: every maximum and index runs over `next_legal` only, so an index outside it is never a
  candidate; `q[a]` is read at the transition's own `action`, validated in its `legal` mask first (`surface.md` §7, D-2);
- **the reward is unshaped** (ASM-12): the seat's net chip delta for the completed hand, at that seat's terminal
  decision and zero at every other one; no term, no clip, no intermediate reward (`engine/surface.md` §9, `learner.md` §1).

The decoupling is the whole difference: `double-q-learning` is a second `forward(..., target=False)` on the same
observation — no new parameter, no new state slot, no new checkpoint field — so the pair stays capacity-matched
(ASM-10, `rules.md` §3). `discount`, the one number both targets need that `ladder.md` §3 does not name, is fixed by §6.

## 3. The update, and the one place a rule branches

- **One path, one branch.** `learn` reads `learner.rule` inside the target's arithmetic (§2) and nowhere else: the
  validation order, the loop, the `|td|` accumulation, the SGD step, the refresh counter and the schedule position are
  shared; `act`, `param_count`, `save`, `load`, `as_policy` and both callers are rule-free (`rules.md` §3, D-19).
- **The batch is the caller's**: consumed in its order, one semi-gradient step per transition, never sampled, sorted,
  shuffled, deduped or replayed — no replay buffer, no priority, no second pass (`surface.md` §7, `ladder.md` §5).
- **One step per transition, in order.** For transition *k*: `q` and `q'` come from the state *before* step *k*;
  `target` from §2, then `td = target − q[a]`, `|td|` added to the batch's total, then `θ ← θ + α·td·∂q[a]/∂θ` — a
  **semi**-gradient, the derivative taken with the target held constant, and **plain SGD**: no momentum, weight decay,
  clipping or per-parameter scaling, in whichever backend owns the parameters (`backends.md` §2). Step *k+1* sees it.
- **A terminal transition carries the decision's own `next_legal`**, and `learn` reads none of it (§2); no empty mask is
  legal (`features/surface.md` §8), so both batteries pass the decision's own mask there.
- **The target copy and its counter.** A second, non-trainable copy of every parameter, equal at construction, is the
  source of every bootstrapping value under either rule; it is refreshed from the online parameters, in
  `architecture.md` §4's declaration order, when the consumed transitions reach `target_update_interval`, and that
  counter then resets to zero. It is never counted as a parameter (`architecture.md` §5, ASM-10) and it is part of a
  checkpoint (`checkpoint.md` §2).
- **Any non-empty batch is legal**: `batch_size` (§6) is the ladder's declared granularity and never a precondition, so
  a batch of 6 or of 200 is consumed by the same rule, in the caller's order (`errors.md` §4).
- **The return**: exactly two keys — `td_error`, the batch's mean absolute TD error (`sum(|td|) / len(batch)`) as a
  plain `float`, and `transitions`, the records consumed as a plain `int` (`surface.md` §7, `records.md` §7);
  `td_error` is finite, since a non-finite observation is refused before any arithmetic (`errors.md` §3).
- **The position advances here and nowhere else**: `len(batch)` is added to the schedule position (§4) last, so a
  refused batch has no effect and no other entry point moves it (`surface.md` §1).

## 4. The exploration: a schedule and a keyed draw

**The rate.** With `start`, `end`, `samples` from §6 and `n` the position (an `int` from `0`, moved only by §3):

    epsilon(n) = start + (end − start) × min(n, samples) / samples

so the rate is `start` at `n = 0`, `end` from `n = samples` on, and linear between (`surface.md` §3).

**The key.** One derivation, shared by `act` and `as_policy`, which must decide as `act` does (`surface.md` §10):

    payload = b"pypoker-agents/explore/v1"
            + b"\x1f" + str(seed).encode("ascii")      # the learner's own seed, or the policy's
            + b"\x1f" + family.encode("ascii")         # b"dense-numeric" or b"token-sequence"
            + b"\x1f" + observation_bytes              # the canonicalisation below
            + b"\x1f" + ",".join(str(i) for i in sorted(mask)).encode("ascii")
    key     = hashlib.sha256(payload).digest()
    draws   = numpy.random.Generator(numpy.random.PCG64(int.from_bytes(key[:16], "big")))
    u, v    = draws.random(), draws.random()           # two float64 draws, u first, both always taken

`observation_bytes` is `numpy.ascontiguousarray(numpy.asarray(observation).astype("<f8" or "<i8")).tobytes()`, `<f8`
for a dense observation and `<i8` for a token one. Three properties are the point: it is **backend-independent**
(sha256's bytes, never `hash()`'s process-salted value), **order-independent** (mask sorted, the observation's bytes its
own layout) and **the learner's own** (seed in the payload) (`surface.md` §6, ASM-2).

**The decision.** With `mask` ascending (it is, `features/surface.md` §8) and the position read before any change:

    if u < epsilon(n):  index = mask[min(int(v × len(mask)), len(mask) − 1)]
    else:               index = the tie-break of §5 over the masked values

so the exploring arm is a uniform draw over the legal indices, the greedy arm is §5 (`surface.md` §7), and the learner's
own `numpy.random.Generator(PCG64(seed))` serves construction only, so `act` advances nothing (`architecture.md` §4).

## 5. The tie-break among equal masked values

Two values equal — or equal to within the arithmetic's own rounding — must not make the answer depend on which backend
computed them (`backends.md` §3). The rule is total, backend-independent and stateless, and `learn` chooses
`double-q-learning`'s bootstrap index with the same one (§2):

    values = the three online values of the observation
    best   = max(values[i] for i in mask)            # the masked maximum, as computed
    tol    = 1e-9 × max(1.0, abs(best))              # relative, with an absolute floor
    index  = min(i for i in mask if values[i] >= best − tol)

"The smallest masked index within `tol` of the masked maximum": total, deterministic and defined on the mask alone, so
three values and a mask give one index in either backend, and `tol` is a design constant (`backends.md` §3 puts the
backends' drift far below it).

## 6. The fixed hyper-declarations `learners()["hyper"]` publishes

Six keys, one value each, for **both** catalogue members: `hyper` is one declaration for every rule and not a
per-rule block, so a rule swap is one axis and no budget moves with it (D-19, ASM-7, `rules.md` §2):

| Key | Value | Why this value |
|---|---|---|
| `learning_rate` | `0.001` | a plain-SGD step small enough that a `td_error` of order the hand's stake (ASM-12) does not overshoot a fresh He-initialised network (`architecture.md` §4) |
| `batch_size` | `32` | the granularity the ladder's loop hands `learn`; a rule stated per transition needs no other meaning (§3) |
| `target_update_interval` | `200` | transitions, not batches: the target copy follows the online parameters every 200 consumed transitions (§3) |
| `optimiser` | `"sgd"` | plain SGD, the one family both backends express as one expression (§3, D-7) |
| `exploration` | `{"start": 1.0, "end": 0.05, "samples": 2000}` | §4's schedule: full exploration at the first decision, annealed linearly to 5% over the first 2,000 decisions — a live run's first half, a hand being a handful of decisions (`ladder.md` §6) |
| `discount` | `0.99` | the bootstrap's weight, fixed here because `ladder.md` §3 names the others and neither rule's target can be computed without it (ASM-7) |

The record is plain data, rebuilt and equal on every call; a variant entry's `learning_rule` and `hyper`
(`records.md` §2) are the run record's data and never an argument here (`surface.md` §4).

## 7. The policy, and what the rule never does

`as_policy(learner, encoder, seed)` snapshots the learner's parameters, its schedule position and the encoder at build
time and returns a callable `policy(readout, legal_actions)` that encodes the readout with `features.encode`, takes the
mask from `features.legal_indices(readout["legal"])`, decides by §4–§5 with its **own** seed, and returns
`features.decode_action(index)` — always one of `legal_actions` (`surface.md` §10, `features/surface.md` §9). At the
learner's own seed and the snapshotted position it decides exactly as `act` does; a later `learn` cannot change a policy
already built, the snapshot being a copy (`surface.md` §10, ASM-5). It also carries `learning_rule`, the catalogue member
its learner was built under: the one thing a policy holds that no decision reads, and what `evaluation` reads to label a
table's members, so a table names the population it measured (`e2e-surface.md` §2, `rules.md` §7, D-19). Nothing in
§2–§5 keeps state: no replay, no running mean, no cached forward pass, no call to the global `random` stream (ASM-2).

## 8. The internals a unit battery may drive, and what is left to L4

Six names are **private**: nothing in `src/agents/__init__.py` exports them and no caller outside `tests/agents/` may
use them (`battery.md` §5, D-13); an entry point may be refactored around them, but L4 implements exactly these
spellings, since `tests/agents/` imports them. Their bodies stay L4's; §4's payload, §6's values, §5's `tol`, the
aim, the mask, the step and the two returned keys never are (`guardrails.md`):

| Name | Signature | One-line contract |
|---|---|---|
| `rule._epsilon` | `_epsilon(position)` | §4's rate at that schedule position: `start` at `0`, `end` from `samples` on, linear between |
| `rule._decision_key` | `_decision_key(seed, family, observation, mask)` | §4's payload's `sha256` digest, from which a caller takes `u` then `v` exactly as §4 does |
| `rule._tie_break` | `_tie_break(values, mask)` | §5's one index for three values and a mask: no seed, no state, no backend — and the index `learn` reads `double-q-learning`'s bootstrap at, over the online values (§2) |
| `model._param_count_for` | `_param_count_for(kind, width, depth, sparsity=0.0)` | `architecture.md` §5's sum at those settings, `I`/`V` the kind's declared `observation_size` |
| `model._initial_parameters` | `_initial_parameters(kind, width, depth, sparsity, seed)` | `architecture.md` §4's steps 1–3 as one 1-D `float64` array in declaration order — the checkpoint's `[0, P)` — `sparsity` changing nothing |
| `checkpoint._read_metadata` | `_read_metadata(path)` | `checkpoint.md` §2.1's object read from `path`'s `metadata.json`, refusing as `load` does |
