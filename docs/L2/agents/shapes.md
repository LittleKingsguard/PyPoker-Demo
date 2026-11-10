# agents — the game shape at this surface

- **Layer:** L2 · **Module:** `agents` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-10
- **Owner of this file:** D-29's second game shape where it reaches this surface — how this module reads a shape (§1),
  the head and the parameter count that follow (§2), the index space, the mask and the `tie` flag (§3), the exploration
  mode (§4), the container's format versions and `game` field (§5), the refusals (§6), and what the shape does not move
  (§7) — `shapes.md` §2, §3, §5, `sizing.md` §3, §4, §6, ASM-37, ASM-40, D-29, D-30
- **Read with:** `surface.md` §2, §4–§10 (which keep one-line pointers here); `learner.md` §1, §3, §4; at the consumed
  edge `docs/L2/features/shapes.md` §1, §3, §5; the design at `docs/L3/agents/architecture.md` §2, §5, `checkpoint.md`
  §2.1, §3, `restore.md` §2, `rule.md` §4–§5, §7
- **Ceiling:** 150 lines — the budget the peer module's axis document declares for the same shape
  (`docs/L2/features/shapes.md`). At the ceiling, split by owner — never append

Split out of `surface.md`, which keeps one-line pointers, when the second shape reached seven of its rows at once
(D-12, D-13).

## 1. The shape is the learner's, and this module reads two things from it

A shape is a declared row of `engine.game_shapes()` — the seats, blinds, stack, chips in play, bet structure, action
vocabulary, head width and amount normalisers of one game — and `fixed-limit-20` is first and the **default**, so a
caller and a spec that name no shape get today's game (`shapes.md` §2, §3, D-29). This module needs exactly two facts
from a row: its **declared name**, the identity a container records (§5), and its **descriptor count** `A`, the head's
width and so the parameter count (§2). Absence is the default and is not a defaulting of a name; a name outside the
catalogue is refused naming it and the declared names, never substituted (`shapes.md` §2, §3, D-13).

**The names are restated; the width is read.** Nothing below an entry point imports another project module, so the
catalogue's names and their order live once in `src/agents/declarations.py`, default first, and the join battery holds
them equal to `engine.game_shapes()`'s — the same restatement `features` makes for the same reason
(`docs/L2/features/shapes.md` §1, `module-map.md` §2, D-13). The width is **not** restated: `A` is the length of
`features.action_space(shape=name)`, one entry per descriptor of that shape's declared index order, and that is a
granted call (`e2e-surface.md` §2, §3.2, `module-map.md` §2) — so no backend and no table here carries a `3` of its own
and one shape's head is never a second spelling of the other's (`sizing.md` §6, ASM-40).

## 2. The head is the shape's: `W → A`, and `A·W + A`

Every kind ends in an output layer as wide as the shape's descriptor count, so the design's `W → 3` is `W → A` and
`param_count`'s output term is `A·W + A` (`sizing.md` §6, ASM-40, `docs/L3/agents/architecture.md` §2, §5). The learner
carries the resolved `A` and its shape's name; both backends read the width off the layout, and `learners()` keeps its
five keys and gains no sixth (`surface.md` §3).

| Shape | `A` | The output term | `param_count` |
|---|---|---|---|
| `fixed-limit-20` (default) | 3 | `3·W + 3`, today's formula | today's six rungs: 10,119 at R1/R2; 10,053 at R3; 10,047 and 10,053 at R4; 10,053 and 10,109 at R5; 10,053 at both R6 variants |
| `no-limit-100` (D-29) | 6 | `6·W + 6` | the same formula at that shape's declared widths, which `training`'s `ladder.md` §4 budget re-matches (ASM-10, ASM-40) |

At `A = 3` the sum is arithmetically today's — at `I = 203`, `W = 36`, `D = 2` it is `7344 + 2664 + 111 = 10,119`, and
at `A = 6` the same kind is `7344 + 2664 + 222 = 10,230` — so **no recorded count moves** (`sizing.md` §6, `shapes.md`
§5, ASM-10). A spec naming a shape builds a learner on that shape's head; `param_count` reports it and no caller
branches on the difference (D-19, D-20).

## 3. The index space, the mask, and the `tie` flag

`act` and `learn` decide over the index space of the shape their learner was built on — `0 .. A−1`, three indices on the
default shape and six on the other, in that shape's **declared** order, which this module does not define and never
re-derives (`sizing.md` §3, `features/surface.md` §7). The order is the measured price order, worst first, deliberately
not monotone in amount: `fold` 0, `check-call` 1, `raise-quarter` 2, `raise-half` 3, `raise-all-in` 4, `raise-minimum` 5
(`sizing.md` §2, §3, ASM-37). The mask is `features.legal_indices`' position-aligned, distinct, ascending, never-empty
sequence, and a band with no legal amount in it is simply absent, never collapsed onto its neighbour (`surface.md` §2,
`docs/L2/features/shapes.md` §4).

- **The tie-break is unchanged.** Among equal masked values it returns the **smallest masked index**, within a relative
  tolerance with an absolute floor so both backends agree (`surface.md` §6, `docs/L3/agents/rule.md` §5); only the order
  it is applied to is the shape's, and that order is what keeps a tie resolving toward a worse-priced band rather than
  toward the best one (`sizing.md` §3, ASM-37).
- **`act`'s record carries a `tie` flag:** `{"action": <plain int>, "tie": <bool>}`, true exactly when the **greedy arm**
  decided the index *and* at least two masked values sat within the tolerance of the masked maximum, so the tie-break
  and not a strict maximum chose it; false on a one-element mask, and false wherever the exploring arm drew the index,
  no maximum having been consulted (`records.md` §6, §15, `sizing.md` §3). It is the learner's own record and not
  surface (`records.md` §6), and the census reads it to recompute its distributional conjuncts twice (`sizing.md` §7).
- **A decision from another shape is refused.** An observation alone cannot betray its shape — both declare the same
  widths, dtype, token vocabulary and block table — so the shape shows in the **mask**: an index outside the learner's
  vocabulary is refused naming the learner's shape, that shape's vocabulary and the index, before any arithmetic and
  before the tie-break (`surface.md` §6, §7, `docs/L2/features/shapes.md` §5), and `learn` refuses it on `action`,
  `legal` and `next_legal` alike (`surface.md` §7).

## 4. The exploration mode is the policy's

`as_policy(learner, encoder, seed, exploration="schedule")` takes one mode with two declared values (`sizing.md` §4,
`e2e-surface.md` §3.3):

- **`schedule`** — the default and today's behaviour exactly: the keyed draw at the learner's snapshotted position and
  the policy's own seed, the exploring arm below the annealed rate and the tie-break of §3 above it
  (`docs/L3/agents/rule.md` §4, `surface.md` §10).
- **`off`** — the decision is the masked maximum and §3's tie-break alone, and **no generator is drawn from at all**: the
  draw `schedule` takes is not constructed, so the seed is not read. Two halves, each testable: two `off` policies built
  from one learner and one encoder at **different seeds decide identically**, and an `off` policy **advances no
  generator position**, the exploring arm being unreachable and nothing here sampling a stream (`surface.md` §1, §10).

**The mode is the policy's and never the hyper block's.** `HYPER["exploration"]` stays the six declarations' one
schedule, annealed to 0.05 and never to 0, and no mode changes it: a mode that edited the schedule would change training
itself (`docs/L3/agents/rule.md` §6, D-19). A mode outside the two is refused naming it and both declared modes.
Rejected: reading the ε = 0.05 tail as "nearly greedy" — 5 % of a six-index space is a systematic contamination of
exactly the classes the census counts (`sizing.md` §4).

## 5. The container: format 3, format 4, and the `game` field

The container answers the second shape with a **format version, not a migration** (`sizing.md` §6, ASM-40):

| Written by | `format_version` | `game` | Read as |
|---|---|---|---|
| the default shape | `3`, today's container | **absent**, so a fixed-limit save's decompressed members are byte-for-byte today's (`shapes.md` §5) | the default shape |
| any other declared shape | `4` | **required**, naming the shape it was written on | the shape it names |
| a version 1, 2 or 3 file, the 18 shipped ones included | unchanged | must not carry one | the **default** shape, as an absent `learning_rule` reads as the catalogue's first (D-19) |

- **`load` requires `game` on version 4**, refuses a version-4 container **naming the default shape** — a field its
  writer would never have written, a default-shape save writing version 3 — and refuses a version-1-to-3 container that
  **carries** one, on that same rule (`docs/L3/agents/checkpoint.md` §3). A version-4 `game` outside the catalogue is
  refused naming it and the declared names, never defaulted.
- **A `load` spec naming a shape its container contradicts is refused naming both** — the spec's shape and the shape the
  file is read as — as a contradictory `seed`, `learning_rule` or `utility` already is (`surface.md` §9, `shapes.md` §3).
- **The parameter array's length must agree with the head width the container's shape declares**: the check a restore
  already makes on `params.count` and `params.length`, now against the geometry `A` implies, so a file whose `game` and
  whose `params` disagree is refused naming the field and both values (`docs/L3/agents/restore.md` §2).
- **The 18 shipped version-1 containers load unchanged as the default shape and none is rewritten**: they are the tree's
  version-1 files and stay so (`shapes.md` §5, `protocol.md` §5, ASM-5). Rejected: always writing version 4, which moves
  every future fixed-limit save's bytes (ASM-40).

## 6. The refusals, side by side

| Where | What is refused | The message names |
|---|---|---|
| `build_learner` | a `game` the catalogue does not carry, a non-string included | the entry point, the value and the declared names (§1, `surface.md` §4) |
| `act`, `learn` | a mask, an `action` or a `next_legal` naming an index the learner's shape does not have | the entry point, the learner's shape and vocabulary, and the index (§3) |
| `as_policy` | an exploration mode outside `{"schedule", "off"}` | the entry point, the value and both declared modes (§4) |
| `load(path)` | a version-4 container with no `game`, one naming the default shape, a version-1-to-3 one carrying `game`, or a `game` outside the catalogue | the field, the value and the declared names (§5) |
| `load(spec)` | a spec whose `game` disagrees with the shape the container is read as | the key and both values (§5) |

## 7. What the shape does not move

Both encodings keep their slot counts — 203 dense slots, 40 tokens — every block width, their dtype and their token
vocabulary of 96 ids; the readout keeps its eleven facts; the two learning rules, the two utilities, the six
hyper-declarations and the six baselines stay one declaration for the catalogue (`sizing.md` §5,
`docs/L2/features/shapes.md` §5, `utility.md` §1, `rule.md` §6). What moves is the amount normalisers and bucket edges,
which are `features`', the head width and the container's version, which are this module's, and the index order, which
is the shape's own declaration (`sizing.md` §3, §5, §6).

Two obligations this document states and does not discharge, their rows being other modules' (`module-map.md` §2, D-13):
`evaluation.policy_from` carries the same two-valued mode, since the sized census reads its greedy pass through it
(`e2e-surface.md` §3.4, `sizing.md` §4, §7); and `training.run` records the shape it played, retains the one greedy pass
under `greedy` and repeats `game` in its run record (`e2e-surface.md` §3.5, `records.md` §12, §15).
