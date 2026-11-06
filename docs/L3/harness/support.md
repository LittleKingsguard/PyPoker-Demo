# harness — the fixture, the factory and the seam

- **Layer:** L3 · **Module:** `harness` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-05
- **Owner:** `fixtures()` — the preconditions a case starts from (§1); `factory()` — one declared object built by its
  owner (§2); `seam()` — one policy double for any label (§3)
- **Ceiling:** 130 lines. At the ceiling, split by owner — never append
- **Read with:** `README.md` §5, `expectations.md` §2.4, `errors.md` §2, §4, `layout.md` §1, `docs/L2/harness/surface.md`
  §3–§5

## 1. `fixtures()` — four pinned facts and one scratch root

It takes no argument, and returns one mapping with four keys, in this order (`surface.md` §3):

| Key | Content |
|---|---|
| `root` | the scratch root: an absolute path, created on the first call in the process, reused by every later call |
| `seed` | `0` — the protocol's first seed, so the fixture invents no value a design document owns (`protocol.md` §2) |
| `device` | `"cpu"` — the device the sandbox actually has (D-8, `protocol.md` §6) |
| `expectations` | `list(KINDS)` — the four kind names of `expectations.md` §2, first kind first |

The root is `tempfile.mkdtemp(prefix="pypoker-harness-")`, made on the first call and held in the module-level `ROOT`
list of `layout.md` §1; every later call returns that first path, so a case that writes a file into it and reads it back
in a later case finds it (`surface.md` §3, FAM-14.1, FAM-16.33). Four rules:

- **it is created, not computed.** `mkdtemp` makes the directory, so `root` is writable when it is returned and a case
  need not create it — a case that does `os.makedirs(root, exist_ok=True)` must be harmless (FAM-14.1);
- **it is never deleted, renamed or emptied.** An artefact a case wrote may still be needed after the case ended, and the
  platform's temporary area owns cleanup; a `TemporaryDirectory` deletes what a case still needs (`battery.md` §2,
  `README.md` §7);
- **it is not inside the repository.** A root under `src/`, `checkpoints/` or `tables/` would let a battery write into a
  shipped tree, and `training.checkpoints`' index would list it (`module-map.md` §5, FAM-16.31);
- **one root per process, shared by every case.** A fresh root per call makes a case's own writes unfindable, and a
  caller that wants a fresh directory creates one inside the shared root (`surface.md` §3, L2's H-6).

The other three keys are equal on every call, in every process: a precondition that varied would make a red case
unreproducible (D-6, `protocol.md` §2). `fixtures()` reads no other module: the device catalogue is `training.devices()`'s
and the seed set is `evaluation.protocol()`'s, and a fixture that read either would make a pinned precondition depend on
another module's implementation (`surface.md` §3, D-13).

## 2. `factory(kind, options)` — a dispatch table, not a builder

`OBJECTS` binds the six declared factory kinds to the owning entry point's own callable, built once from the five
package imports (`layout.md` §1, `README.md` §5):

| `kind` | `OBJECTS[kind]` | `options` |
|---|---|---|
| `encoder` | `features.build_encoder` | the encoding name |
| `learner` | `agents.build_learner` | one learner spec (`records.md` §3) |
| `baseline` | `agents.build_baseline` | the name and the seed, **in that order** — the one kind whose entry point takes two arguments |
| `hand` | `engine.new_hand` | the seed |
| `rung` | `training.rung` | the rung name |
| `pool` | `evaluation.build_pool` | one membership declaration (`records.md` §8) |

The body is three steps and nothing more: refuse a `kind` `OBJECTS` does not carry, naming the kind and the six declared
kinds in sorted order (`errors.md` §4); then call `OBJECTS[kind]`, spreading `options` for `baseline` and passing it
whole for the other five; then return what came back. Five rules:

- **it validates no option.** A missing argument is the owning entry point's arity, and the owning entry point is the
  authority on what it accepts: a factory that pre-checked a learner spec would be a second spelling of
  `agents.build_learner`'s argument contract (`surface.md` §4, `records.md` §14, D-13);
- **it supplies no default.** A kind whose entry point requires an argument gets that argument or the owner refuses
  (`surface.md` §4);
- **it returns the owner's object.** Not a copy, not a wrapper, not a subclass — a learner built here *is* the learner
  `agents.build_learner` would have built, with the same `param_count`; an encoder built here is one `features.encode`
  accepts (FAM-14.2, FAM-14.3, FAM-16.34);
- **the owner's refusal propagates unchanged.** `features`' unknown encoding, `agents`' unknown backend or baseline name
  and `evaluation`'s bad declaration arrive in their own classes and are never re-raised as a harness error: the
  catalogue is the owner's (`errors.md` §1, `e2e-surface.md` §2);
- **an undeclared kind is refused, never built.** A factory that built a `deck-of-cards` would be the substitution this
  module never makes (FAM-14.4, `module-map.md` §3, brief §5).

One kind moves the global stream and the other five do not: `hand` is a deal, so `engine.new_hand`'s seeding rule
applies to it and to nothing else here (ASM-2, `protocol.md` §4, `engine/surface.md` §4).

## 3. `seam(label)` — one policy double, for any label

`seam(label)` returns a **closure**, not an object: a function `policy(readout, legal_actions)` that captures the label
and a `calls` list, with `policy.calls` and `policy.label` bound on it as attributes. A class with `__call__` is the
rejected alternative — it costs four more lines for the same two facts, and `callable(policy)` is the only property the
surface asks for (FAM-14.5, FAM-14.7, FAM-16.35).

**The call**, in order (`e2e-surface.md` §2, `surface.md` §5):

1. `legal = list(legal_actions)` — the sequence is read once, so a caller that later mutates its own list cannot change
   what this seam chose or logged;
2. an **empty** legal set raises `NoLegalAction`, naming the label and the contract: a policy returns a member of
   `legal_actions`, and a policy that cannot is a contract violation and never a fold (D-2, `errors.md` §4);
3. the position is `len(calls) % len(legal)` when the label is `synthetic`, and `0` for every other label — including
   `recording` and a label no design document carries, because the label selects a behaviour and is never checked
   against a list (`surface.md` §5, `battery.md` §4, D-15);
4. the entry `{"readout": readout, "legal": legal, "chosen": legal[position]}` is appended to `calls`, in that key order
   — one entry per call answered, in call order, holding what it was handed and what it returned (L2's H-3);
5. `legal[position]` is returned — an element of the list it was handed, drawn in the engine's order, so
   `engine.apply_action` accepts it and `features.legal_indices` gives it an index in `{0, 1, 2}`.

**The two documented behaviours** differ only in the choice rule: `recording` (and any other label) takes the first
descriptor every call; `synthetic` walks the legal descriptors cyclically, so call *n* takes position `n` modulo the
number of legal descriptors, which spreads a case's choices over the vocabulary without a learner (FAM-14.6). Both
record; a `synthetic` seam that logged nothing would contradict §3.6's Returns column (L2's H-3).

**Determinism.** Each `seam(label)` call returns a fresh closure whose log starts empty and whose schedule starts at its
first call, so two seams of one label driven over the same `(readout, legal_actions)` pairs return the same descriptors
and hold the same log (FAM-14.5, FAM-14.6, FAM-16.35). A seam's choice is a function of its label and of the calls it
answered — of no clock, no generator, no global stream and no fixture (ASM-2, D-6). A seeded draw is the rejected
alternative: `seam` takes a label and no seed, so it would have to borrow the stream the engine seeds for the deal
(L2's H-2, `protocol.md` §4).

**What a seam is not.** It doubles a *policy* and nothing else: it deals no hand, encodes no observation, computes no
equity, holds no learner, learns nothing and measures nothing (`module-map.md` §3, brief §5). It reads no field of the
readout to choose — the label alone decides the rule (D-13). The episode it plays is the engine's, so `play_hand` stays
zero-sum because the engine decided the hand and the seam only chose inside the legal set (FAM-14.7, ASM-12).
