# agents — the game shape at this surface

- **Layer:** L2 · **Module:** `agents` · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-10
- **Owner of this file:** the declared game shapes where they reach this surface — how this module reads a shape (§1),
  the head and the parameter count that follow (§2), the index space, the mask and the `tie` flag (§3), the exploration
  mode (§4), the container's format versions and `game` field (§5), the refusals (§6), and what a shape does not move
  (§7); the third row's **seat count** is `seats.md`'s — `shapes.md` §2, §3, §5, `sizing.md` §3, §4, §6, ASM-37, ASM-40,
  ASM-42, ASM-44, D-29, D-30, D-33
- **Read with:** `surface.md` §2, §4–§10 (which keep one-line pointers here); `learner.md` §1, §3, §4; `seats.md` §1–§5;
  at the consumed edge `docs/L2/features/shapes.md` §1, §3, §5; the design at `docs/L3/agents/architecture.md` §2, §5,
  `checkpoint.md` §2.1, §3, `restore.md` §2, `rule.md` §4–§5, §7
- **Ceiling:** 150 lines — the budget the peer module's axis document declares for the same shape
  (`docs/L2/features/shapes.md`). At the ceiling, split by owner — never append

Split out of `surface.md`, which keeps one-line pointers, when the second shape reached seven of its rows at once
(D-12, D-13).

## 1. The shape is the learner's, and this module reads three things from a row

A shape is a declared row of `engine.game_shapes()` — the seats, blinds, stack, chips in play, bet structure, action
vocabulary, head width and amount normalisers of one game — and `fixed-limit-20` is first and the **default**, so a
caller and a spec that name no shape get today's game (`shapes.md` §2, §3, D-29, D-33). This module needs three facts
from a row: its **declared name**, the identity a container records (§5); its **descriptor count** `A`, the head's width
and so the parameter count (§2); and its **seat count**, what a readout's `stacks` and `seat` facts are shaped by and the
one `fold-large-bet` reads its own stack for (`seats.md` §1–§3). Absence is the default, never a defaulting of a name; a
name outside the catalogue is refused naming it and the declared names (`shapes.md` §2, §3, D-13).

**The names are restated; the width is read.** Nothing below an entry point imports another project module, so the
catalogue's names and their order live once in `src/agents/declarations.py`, default first, and the join battery holds
them equal to `engine.game_shapes()`'s, as `features` does for the same reason (`docs/L2/features/shapes.md` §1,
`module-map.md` §2, D-13). The width is **not** restated: `A` is the length of `features.action_space(shape=name)`, one
entry per descriptor of that shape's declared index order, and that is a granted call (`e2e-surface.md` §2, §3.2) — so no
backend and no table here carries a `3` of its own and one shape's head is never a second spelling of another's
(`sizing.md` §6, ASM-40). The **seat count** cannot be read off a granted call and is restated beside the names, the join
battery holding it equal to the rows' `seats` (`seats.md` §1, ASM-44, D-13).

## 2. The head and the input width are the shape's: `A·W + A` over that shape's own `I`

Every kind ends in an output layer as wide as the shape's descriptor count, so the design's `W → 3` is `W → A` and
`param_count`'s output term is `A·W + A` (`sizing.md` §6, ASM-40, `docs/L3/agents/architecture.md` §2, §5). The learner
carries the resolved `A` and its shape's name; both backends read the width off the layout, and `learners()` keeps its
five keys and gains no sixth (`surface.md` §3). **The input term is the shape's too**, because a shape's history
capacity is its own and sets its encoder's width: 203 dense over 24 slots on `fixed-limit-20`, **329** over 66 on
`no-limit-100` and **433** over 98 on `six-seat-no-limit-100`, whose token encoding is 122 long over vocabulary 102
(`shapes.md` §8, `seats.md` §2, ASM-42, ASM-44, `capacity.md` §2).

| Shape | `A` | `I`, the dense encoding's width | `param_count` at `W = 36`, `D = 2` |
|---|---|---|---|
| `fixed-limit-20` (default) | 3 | 203 — 24 history slots | `7344 + 2664 + 111 = 10,119`, today's six rungs unmoved |
| `no-limit-100` (D-29) | 6 | 329 — 66 history slots | `11880 + 2664 + 222 = 14,766`, which `training`'s `ladder.md` §4 budget re-matches |
| `six-seat-no-limit-100` (D-33) | 6 | 433 — 98 history slots | `15624 + 2664 + 222 = 18,510`, a seat count moving the width and not `A` |

At the default shape the sum is arithmetically today's — `203·36 + 36 = 7344`, `2·(36² + 36) = 2664` and `3·36 + 3 = 111`
— so **no recorded count moves** (`sizing.md` §6, `shapes.md` §5, ASM-10). At the two others the input term is
`329·36 + 36 = 11,880` and `433·36 + 36 = 15,624` and the head is `6·36 + 6 = 222`, so one kind at one width and depth
costs 14,766 and 18,510 there against 10,119 here: the shape moves both ends of the formula, and neither module writes
its `3`, its `6`, its 203, its 329 or its 433 down (`shapes.md` §8, `seats.md` §4, ASM-44, `architecture.md` §5, D-19, D-20).

## 3. The index space, the mask, and the `tie` flag

`act` and `learn` decide over the index space of the shape their learner was built on — `0 .. A−1`, three indices on the
default shape and six on the two uncapped rows, in that shape's **declared** order, which this module does not define
and never re-derives (`sizing.md` §3, `features/surface.md` §7). The order is the measured price order, worst first and
deliberately not monotone in amount: `fold` 0, `check-call` 1, `raise-quarter` 2, `raise-half` 3, `raise-all-in` 4,
`raise-minimum` 5 (`sizing.md` §2, §3, ASM-37). The mask is `features.legal_indices`' position-aligned, distinct,
ascending, never-empty sequence, and a band with no legal amount in it is simply absent (`surface.md` §2, `features/shapes.md` §4).

- **The tie-break is unchanged.** Among equal masked values it returns the **smallest masked index**, within a relative
  tolerance with an absolute floor so both backends agree (`surface.md` §6, `docs/L3/agents/rule.md` §5); only the order
  it is applied to is the shape's, and that order is what keeps a tie resolving toward a worse-priced band rather than
  toward the best one (`sizing.md` §3, ASM-37).
- **`act`'s record carries a `tie` flag:** `{"action": <plain int>, "tie": <bool>}`, true exactly when the **greedy arm**
  decided the index *and* at least two masked values sat within the tolerance of the masked maximum, so the tie-break
  and not a strict maximum chose it; false on a one-element mask, and false wherever the exploring arm drew the index,
  no maximum having been consulted (`records.md` §6, §15, `sizing.md` §3). It is the learner's own record and not
  surface (`records.md` §6), and the census reads it to recompute its distributional conjuncts twice (`sizing.md` §7).
- **A decision from another shape is refused.** The three shapes' observations do not agree in width — 203, 329 and 433
  dense, 40, 82 and 122 tokens (`shapes.md` §8, `seats.md` §2, ASM-44) — so a dense one of the wrong width is refused
  naming both, and where the widths agree the shape shows in the **mask**: an index outside the learner's vocabulary is
  refused naming the learner's shape, that shape's vocabulary and the index, before any arithmetic and before the
  tie-break (`surface.md` §6, §7, `docs/L2/features/shapes.md` §5), and `learn` refuses it on `action`, `legal` and
  `next_legal` alike.

## 4. The exploration mode is the policy's

`as_policy(learner, encoder, seed, exploration="schedule")` takes one mode with two declared values (`sizing.md` §4,
`e2e-surface.md` §3.3), and no shape changes it (`seats.md` §7):

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
Rejected: reading the ε = 0.05 tail as "nearly greedy" — 5 % of a five- or six-index space is a systematic
contamination of exactly the classes the census counts (`sizing.md` §4).

## 5. The container: format 3, format 4, and the `game` field

The container answers a second and a third shape with a **format version, not a migration** (`sizing.md` §6, ASM-40):

| Written by | `format_version` | `game` | Read as |
|---|---|---|---|
| the default shape | `3`, today's container | **absent**, so a fixed-limit save's decompressed members are byte-for-byte today's (`shapes.md` §5) | the default shape |
| any other declared shape | `4` | **required**, naming the shape it was written on | the shape it names |
| a version 1, 2 or 3 file, the 18 shipped ones included | unchanged | must not carry one | the **default** shape, as an absent `learning_rule` reads as the catalogue's first (D-19) |

- **`load` requires `game` on version 4**, refuses a version-4 container **naming the default shape** — a field its
  writer would never have written, a default-shape save writing version 3 — and refuses a version-1-to-3 container that
  **carries** one, on that same rule (`docs/L3/agents/checkpoint.md` §3).
- **A `load` spec naming a shape its container contradicts is refused naming both**, as a contradictory `seed`,
  `learning_rule` or `utility` already is (`surface.md` §9, `shapes.md` §3).
- **The parameter array's length must agree with the head width the container's shape declares**: the check a restore
  already makes on `params.count` and `params.length`, against the geometry `A` implies, so a file whose `game` and
  `params` disagree is refused naming the field and both values (`docs/L3/agents/restore.md` §2).
- **A version-4 container carries the shape's own width.** `representation.size` and `representation.shape` are the
  shape's — 329 over 66 slots on `no-limit-100`, 433 over 98 on the six-seat row — and a reader checks the geometry
  against that record instead of the kind's 203, so a widened container restores to the head it was written at; the 18
  shipped containers record 203 and are read as it (`shapes.md` §8, `seats.md` §5, ASM-44, `capacity.md` §2).
- **The 18 shipped version-1 containers load unchanged as the default shape and none is rewritten** (`shapes.md` §5,
  `protocol.md` §5, ASM-5). Rejected: always writing version 4, which moves every future fixed-limit save's bytes (ASM-40).

## 6. The refusals, side by side

| Where | What is refused | The message names |
|---|---|---|
| `build_learner` | a `game` the catalogue does not carry, a non-string included; and a spec naming a non-default shape with **no** `encoder` | the entry point, the value and the declared names (§1, `surface.md` §4); for the second, the shape, the kind's declared default size and the encoder that shape needs (§2) |
| `act`, `learn` | a mask, an `action` or a `next_legal` naming an index the learner's shape does not have | the entry point, the learner's shape and vocabulary, and the index (§3) |
| `as_policy` | an exploration mode outside `{"schedule", "off"}` | the entry point, the value and both declared modes (§4) |
| `load(path)` | a version-4 container with no `game`, one naming the default shape, a version-1-to-3 one carrying `game`, or a `game` outside the catalogue | the field, the value and the declared names (§5) |

## 7. What the shape does not move

The two learning rules, the two utilities, the six hyper-declarations and the six baselines stay one declaration for the
catalogue; the readout keeps its eleven facts; both encodings keep their nine fields, their block order, their block
widths before the history and their dtype, and the default and two-seat rows keep the token vocabulary of 96 ids
(`sizing.md` §5, `docs/L2/features/shapes.md` §5, `utility.md` §1, `rule.md` §6, `seats.md` §7). What moves is the amount
normalisers and bucket edges and the history block's capacity — hence the three slot counts, 203/40 and 329/82 and
433/122 — which are `features`', and the head width, the learner's input width and the container's version, which are
this module's, and the index order, which is the shape's own declaration (`shapes.md` §8, `seats.md` §2, §4, ASM-42,
ASM-44, `sizing.md` §3, §5, §6, `capacity.md` §2). The **seat count** and a `shape`-aware folder's stack are
`seats.md`'s and move nothing here (`seats.md` §2, §3, §7, D-33).

Two obligations are other modules' (`module-map.md` §2, D-13): `evaluation.policy_from` carries the same two-valued mode
(`e2e-surface.md` §3.4, `sizing.md` §4, §7), and `training.run` records the shape it played under `greedy` (`records.md` §12, §15).
