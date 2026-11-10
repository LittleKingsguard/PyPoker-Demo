# agents — refusals

- **Owner:** the error classes and the message grammar every refusal of this module follows, the canonical message per
  refusal of `docs/L2/agents/surface.md` §4–§12 and of `divergence.md`'s, and what is deliberately *not* refused
- **Ceiling:** 130 lines. At the ceiling, split by owner — never append

## 1. Why a hierarchy

`docs/L2/agents/surface.md` §1: *an invalid argument is refused by raising an error that names the violated
contract; no entry point coerces a value, substitutes a default, swallows an error or returns part of a record*.
The error is therefore the only reporting channel: nothing comes back as a failure record, nothing is logged and
continued, and no validation refusal has an observable effect — `learn` validates the batch before its first step,
`save` before it opens a handle, `act` before it computes a value (`rule.md` §3, `checkpoint.md` §3). A hierarchy
lets a caller catch "this module refused me" without catching a `TypeError` from a bug in it.

## 2. The classes — `src/agents/errors.py`

    class AgentsError(Exception)             # base of every refusal of this module
    class InvalidLearner(AgentsError)        # param_count, act, learn, save, as_policy: not a learner
    class InvalidSpec(AgentsError)           # build_learner: not a mapping, a missing key, a bare kind with no sizes
    class UnknownBackend(AgentsError)        # build_learner: not one of learners()['backends']
    class UnknownArchitecture(AgentsError)   # build_learner: not one of learners()['architectures']
    class UnknownRule(AgentsError)           # build_learner, load: not one of learners()['learning_rules']
    class UnknownUtility(AgentsError)        # build_learner, load: not one of learners()['utilities']
    class UnknownShape(AgentsError)          # build_learner, load: not one of declarations.SHAPE_NAMES (shapes.md §6)
    class UnknownExploration(AgentsError)    # as_policy: a mode outside {"schedule", "off"} (shapes.md §4, §6)
    class InvalidSetting(AgentsError)        # build_learner: width/depth not positive integers, sparsity outside [0,1]
    class InvalidSeed(AgentsError)           # build_learner, as_policy, build_baseline: not an integer
    class InvalidEncoder(AgentsError)        # build_learner, as_policy: not an encoder features built
    class EncoderMismatch(AgentsError)       # build_learner, as_policy: encoder kind/size contradicts the learner's
    class InvalidObservation(AgentsError)    # act, learn: shape/dtype/family/finiteness contradicts the learner's
    class InvalidMask(AgentsError)           # act, learn: an empty or repeated index, or one outside 0 .. A-1
    class InvalidBatch(AgentsError)          # learn: an empty batch, a missing key, an action outside its own mask
    class InvalidReadout(AgentsError)        # a policy: not a mapping, or a fact it needs missing or malformed
    class UnknownBaseline(AgentsError)       # build_baseline: a name the six do not include
    class CheckpointUnwritable(AgentsError)  # save: a path that is not a writable file location
    class CheckpointUnreadable(AgentsError)  # load: missing, unreadable, or a form this module does not read
    class CheckpointMismatch(AgentsError)    # load: the spec disagrees with the file on a compared key
    class LearningDiverged(AgentsError)      # learn, act, a policy: the state went non-finite, raised by decide/
                                             #   decide_greedy/_tie_break (divergence.md §2)

Twenty-one subclasses, one per refusal family of `surface.md` §4–§12, `shapes.md` §6 and `divergence.md` §1. They are
**not** module-level names of the `agents` package — below an entry point is not surface (`README.md` §3,
`e2e-surface.md` §1) — and a battery asserts the *behaviour*, never the class, which is this module's freedom
(`docs/L3/features/errors.md` §2).

## 3. The message grammar

Every message has the form `"<entry point>(<argument or field>): <the violated contract>, got <what was passed>"`, so
the contract is named in the design's own words and the offending value is visible; where nothing was passed — a key a
record is missing — the message names the missing key instead of inventing a `got` clause. L4 follows these spellings,
and the unit battery matches them tolerantly (the raising site's name, the key's name, and the value):

| Where | Message |
|---|---|
| `build_learner` not a mapping | `build_learner(spec): the spec must be a mapping, got list` |
| `build_learner` missing key | `build_learner(spec): the spec is missing the required key 'seed'` |
| `build_learner` bare kind, no sizes | `build_learner(spec): the kind 'deep' names no width or depth, and 'sizes' is absent` |
| `build_learner` backend | `build_learner(spec): the backend must be one of ('numpy', 'torch'), got 'jax'` |
| `build_learner` kind | `build_learner(spec): the kind must be one of ('naive-stack', 'token-embedding', 'wide', 'deep', 'sparse', 'residual', 'plain'), got 'naivestack'` |
| `build_learner` learning rule | `build_learner(spec): 'learning_rule' must be one of ('masked-q-learning', 'double-q-learning'), got 'monte-carlo'` |
| `build_learner` utility | `build_learner(spec): 'utility' must be one of ('net-chips', 'stack-shortfall'), got 'sharpe'` |
| `build_learner` game (shape) | `build_learner('game'): 'no-limit-6' is not one of the declared shapes ('fixed-limit-20', 'no-limit-100'), and a shape name is never defaulted` |
| `as_policy` exploration | `as_policy(exploration): the mode must be one of ('schedule', 'off'), got 'greedy'` |
| `build_learner` seed | `build_learner(spec): the seed must be an integer, got '6174'` |
| `build_learner` width or depth | `build_learner(spec): 'width' must be a positive integer, got 0` |
| `build_learner` sparsity | `build_learner(spec): 'sparsity' must be in [0, 1], got 1.5` |
| `build_learner` encoder | `build_learner(spec): 'encoder' must be an encoder from features.build_encoder, got dict` |
| `build_learner` encoder kind | `build_learner(spec): the encoder is 'card-tokens' (token-sequence, vocabulary 96) and the kind 'naive-stack' is dense-numeric at 203` |
| `build_learner` encoder size | `build_learner(spec): the encoder declares width 200 and the kind 'naive-stack' declares 203` |
| any, not a learner | `act(learner): the argument must be a learner from build_learner, got dict` |
| `act`/`learn` observation | `act(observation): the observation is (40,) int32 token-sequence and the learner is (203,) float32 dense-numeric` |
| `act`/`learn` mask | `act(legal_mask): the mask names the index 3, which is outside the index range 0..2 of the shape 'fixed-limit-20' the learner decides in, got (0, 1, 3)`; and `act(legal_mask): the mask must be non-empty, distinct indices of 0..2 on the shape 'fixed-limit-20', got (0, 1, 1)` |
| `learn` empty batch | `learn(transitions): a batch holds at least one transition, got ()` |
| `learn` missing key | `learn(transitions): the transition is missing the required key 'next_legal'` |
| `learn` action | `learn(transitions): 'action' 2 is not in that transition's legal mask (0, 1)`; and `'action' 5 is outside the index range 0..2 of the shape 'fixed-limit-20'` (shapes.md §3) |
| `param_count` baseline | `param_count(learner): a baseline is not a learner, and its parameter count is the 0 baselines() declares` |
| `save` path | `save(path): the path '/ckpt/missing/x.pt' is not a writable file location` |
| `load` path | `load(path): '/ckpt/x.pt' cannot be read: No such file or directory` |
| `load` form | `load(path): '/ckpt/x.pt' is not a pypoker-agents-checkpoint of format version 1, 2, 3 or 4` |
| `load` version | `load(path): '/ckpt/x.pt' records the field 'format_version', which must be 1, 2, 3 or 4, got 4242` |
| `load` rule, utility and game | `load(path): '/ckpt/x.pt' has a metadata.json without the field 'learning_rule'`; `load(path): '/ckpt/x.pt' records the field 'learning_rule', which must be absent from a format version 1 container, got 'masked-q-learning'`; `load(path): '/ckpt/x.pt' records the field 'learning_rule', which must be one of ('masked-q-learning', 'double-q-learning'), got 'monte-carlo'`; and for the utility: `… has a metadata.json without the field 'utility'`, `… which must be absent from a format version 2 container, got 'net-chips'`, and `… which must be one of ('net-chips', 'stack-shortfall'), got 'sharpe'`; and for the shape: `… has a metadata.json without the field 'game'`, `… records the field 'game', which must be one of ('fixed-limit-20', 'no-limit-100'), got 'no-limit-6'`, and `… which must be absent from a format version 3 container, got 'no-limit-100'` |
| `load` field value | `load(path): '/ckpt/x.pt' records the field 'backend', which must be one of ('numpy', 'torch'), got 'jax'` |
| `load` mismatch | `load(spec): the spec's seed 4711 is not the checkpoint's seed 6174`; a rule: `load(spec): the spec's learning_rule 'masked-q-learning' is not the checkpoint's learning_rule 'double-q-learning'`; a utility: `load(spec): the spec's utility 'net-chips' is not the checkpoint's utility 'stack-shortfall'`; a shape: `load(spec): the spec's game 'no-limit-100' is not the shape 'fixed-limit-20' the checkpoint is read as` |
| `as_policy` seed | `as_policy(seed): the seed must be an integer, got None` |
| `as_policy` encoder | `as_policy(encoder): the encoder declares vocabulary 96 and the learner is dense-numeric at 203` |
| a policy's readout | `policy(readout): the readout is missing 'to_call', which the rule needs` |
| a malformed readout | `policy(readout): the readout's 'stacks' must be one number per seat, got (1, 2, 3)`; and `'hole'` must be two cards, got 1; and `'hand_class'` must be None or an integer 0-8, got 9 |
| `build_baseline` name | `build_baseline(name): the name must be one of ('random', 'always-call', 'oracle', 'fold-no-pair-or-face', 'fold-no-pair-or-better', 'fold-large-bet'), got 'gto'` |
| `learn`, a non-finite td_error, and a step that left a parameter non-finite (`divergence.md` §2–§3) | `learn(transitions): transition index 41 computed a non-finite td_error and the learner has diverged, got nan`; `learn(transitions): transition index 41 drove parameter index 118 out of finite range and the learner has diverged, got nan` |
| the decision: `act`, every policy, and `learn`'s bootstrap — one raise per site (`divergence.md` §2–§3) | `decide(values): the masked value at index 2 is not finite and the learner has diverged, got nan`; `decide_greedy(values): …` on an `off` policy's path; `_tie_break(values): …` for `double-q-learning`'s bootstrap |

Three properties the battery relies on: the message always contains the raising site's own name, the name of the argument
or key at fault, and the offending value; it never claims a value was accepted (`docs/L3/features/errors.md` §3); and a
refusal raised while a policy works is **this** module's, named `policy(readout)` rather than another module's class (§2).

## 4. What is *not* refused

Refusing more than the contract refuses is also a defect — a battery may pass any valid instance (`battery.md` §4, D-15):

- an **extra key in a learner spec**, `hyper`, `param_budget`, `samples`, `seeds`, `device` and `name` included:
  those are a run record's data and not a per-learner argument (`surface.md` §4, `records.md` §2).
  `variant_learner` in `tests/e2e/_surface.py` hands exactly such an entry over;
- an **absent `learning_rule`**, an **absent `utility`** and an **absent `game`**: a spec naming none is built under that
  catalogue's first member — `masked-q-learning`, `net-chips` — or the default shape, never an inference from silence
  (`records.md` §3, `shapes.md` §1, D-19, D-20, D-29);
- **`sizes` when `architecture` is present**: redundant — `architecture` is authoritative (`records.md` §3);
- a **`sparsity` or `residual` a kind does not read** — `sparsity: 0.5` on a `deep` kind is accepted and ignored
  (`architecture.md` §3, `surface.md` §4);
- a **`numpy` integer for a seed**, a width, a depth or an index: `numpy.int64` is an `Integral`, and a **`bool`**
  is refused in every one of those places because a flag is not a count (`docs/L3/features/errors.md` §4);
- a **policy's readout carrying extra facts**: the eleven facts of `README.md` §7 are inspected, so an extra one is
  ignored but a malformed one is refused rather than defaulted (`baselines.md` §1);
- a **batch longer or shorter than `batch_size`**, a batch of one, and a transition whose `terminal` is true and
  whose `next_observation` equals its `observation` (`rule.md` §3);
- a **non-finite `reward`, and a non-finite parameter a container carries**: the batch passes validation and `load` reads
  the file as it always did, so what a step or a decision produced is refused at that site instead (`divergence.md` §4);
- **`sparsity` of exactly `0` or `1`**, and a width or depth of `1` (`architecture.md` §3);
- two learners from one spec, a learner saved twice, a checkpoint loaded twice, and a policy kept for a long time: the
  module keeps no cache and no registry (`surface.md` §4, §8).

The only shapes refused on a record are the ones that are not that record at all: not a mapping, a missing required
key, or a value the contract forbids (`surface.md` §1).

## 5. Where the messages are asserted

FAM-1.17–1.26 assert only that each name is callable with a valid instance; the refusals are asserted by the blind
instances and by this design's unit battery (`battery.md` §3–§4). A message that omits the entry point, the key at
fault or the offending value passes the L1 battery and fails the unit battery, so §3 exists (`guardrails.md`), and
AGT-16.1–16.6 assert this §3's last two rows (`divergence.md` §5, `tests/agents/test_divergence.py`).
