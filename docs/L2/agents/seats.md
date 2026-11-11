# agents — the third declared shape: six seats

- **Layer:** L2 · **Module:** `agents` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-10
- **Owner of this file:** D-33's six-seat row where it reaches this surface — the catalogue's third name and the seat
  counts this module restates (§1), the readout the policies read at six seats (§2), `build_baseline(name, seed,
  shape=None)` and the two rules the shape reaches (§3), the head, the input width and the parameter count at 433 (§4),
  the container at 433 (§5), the refusals (§6), and what a seat count does not move (§7) — `shapes.md` §2, §8,
  `seats.md` §2–§6, `sizing.md` §3, §6, ASM-42, ASM-44, D-33
- **Read with:** `shapes.md` §1–§2, §5, §7 (which keep one-line pointers here); `baselines.md` §2–§3; `surface.md` §5,
  §9, §12; `learner.md` §3; at the consumed edge `docs/L2/features/capacity.md` §2, §5 and `docs/L2/engine/surface.md`
  §3, §11; the design at `docs/L3/agents/seats.md`
- **Ceiling:** 160 lines — the third row's whole column at this surface, in one document because a seat count is one
  axis: the catalogue's third name (§1), the readout's seat count (§2), `build_baseline`'s shape (§3), the count (§4),
  the container (§5), the refusals (§6) and what does not move (§7). At the ceiling, split by owner — never append

Split out of `shapes.md`, which was at its ceiling when the catalogue gained its third row: a seat count is a
different kind of shape data from a width, and a document that owns both would have to grow past the budget it
declares (D-12, D-13, D-33).

## 1. The third name, and the three names restated once

`engine.game_shapes()` publishes **three** rows, default first, and the third is `six-seat-no-limit-100`
(`shapes.md` §2, `seats.md` §2, D-33). This module restates the catalogue's **names and their order** once, in
`declarations.SHAPE_NAMES`, and adds **their seat counts** beside them in `declarations.SHAPE_SEATS`, because a readout's
`stacks` fact is one entry per seat and nothing this module is granted for the seated question says how many seats a
name has (`seats.md` §3, ASM-44, `module-map.md` §2, D-13). The join battery holds both sequences equal to the rows
`engine` publishes, in that order (JOIN-AGT-14.1, `battery.md` §3).

| Shape | Seats | `A`, the head | `I`, the dense width | Token vocabulary |
|---|---|---|---|---|
| `fixed-limit-20` (default) | 2 | 3 | 203 — 24 history slots | 96 |
| `no-limit-100` (D-29) | 2 | 6 | 329 — 66 slots | 96 |
| `six-seat-no-limit-100` (D-33) | 6 | 6 | 433 — 98 slots | 102 |

- **A seat count adds no descriptor.** The third row declares the two-seat uncapped row's six descriptors in the same
  index order, so `A` is 6 on both and a seat count changes the price of aggression rather than the vocabulary
  (`shapes.md` §2, `seats.md` §2, ASM-44).
- **`A` and `I` are read, the seat count is restated.** `A` is `len(features.action_space(shape=name))` and `I` is that
  shape's encoder's `observation_spec`, so neither is a number any table here writes (`shapes.md` §1–§2, `sizing.md`
  §6, `docs/L2/features/capacity.md` §2, ASM-40, ASM-44). The seat count cannot be read off a granted call, so it is
  declared here beside the names and checked by the join battery (`seats.md` §3, D-13).
- **Absence is still the default.** A spec, a policy and a container that name no shape are the default row's — the
  first of the three and not a defaulting of a name (`shapes.md` §1, §5, D-13).
- **The catalogue's distinct seat counts are `(2, 6)`**, derived from `SHAPE_SEATS` rather than written a second time,
  and that pair is the range the readout validators of §2 hold themselves to (`seats.md` §3, ASM-44).

## 2. The readout at six seats

Every **fact** stays the one of `e2e-surface.md` §2 and no twelfth is added; the seat count changes what two of them
carry (`seats.md` §3, D-3):

- `seat` is `(index, on_button)` with the index in `0 .. seats − 1` — `0..5` here and `0..1` on the other two rows —
  and the shape's declared `button_seat` the button (`e2e-surface.md` §2, `seats.md` §3);
- `stacks` is one entry per seat in seat order, so six here and two on the others, and `pot + sum(stacks)` is the
  shape's chips in play at every decision — 600 on this row (`e2e-surface.md` §2, `seats.md` §2, ASM-28).

**The validators of `baselines.py` admit the shape's seat count and nothing else.** `stacks` is accepted when its
length is one of the declared seat counts, and the seat index is accepted when it is an index of that many seats; a
length no declared row carries and an index past the seats are refused naming the fact and the value (`seats.md` §3,
ASM-44, `errors.md` §2–§3). The eleven facts, the distinct-card rule and the `hand_class` rule are the ones they were,
on every shape: a six-seat readout naming one card twice, or carrying a `hand_class` of nine, is refused exactly as a
two-seat one is (`folders.md` §2–§3, ASM-30). At the default shape the validators accept the same two-seat readouts
they always did, so nothing at that shape moves (`shapes.md` §7).

`random`'s draw is **keyed by the decision**, and the decision's canonical spelling carries six `stacks` entries and
six legal indices at six seats instead of two and three (`baselines.md` §2, ASM-4). The keying is unchanged as a rule —
one seed repeats, two seeds differ, and an index never leaves the mask it was handed — which is why a six-seat
decision is a decision like any other and a baseline is still a function of the decision it is handed
(`e2e-surface.md` §2, `seats.md` §4).

## 3. `build_baseline(name, seed, shape=None)`

- **Signature:** `build_baseline(name, seed, shape=None)` — the one signature change D-33 makes at this surface, and
  the third argument is the **shape the policy decides in**, absent meaning the default (`baselines.md` §2,
  `e2e-surface.md` §3.3, `seats.md` §6, D-33). The seed and the name keep their contracts: one of the six and an
  integer (`baselines.md` §2, ASM-2, `protocol.md` §3).
- **Absence is today's call.** `build_baseline(name, seed)` and `build_baseline(name, seed, None)` and
  `build_baseline(name, seed, shape=DEFAULT_SHAPE)` take the same decision on every decision of the default shape, so
  no caller that passes two arguments moves (`shapes.md` §5, §7, D-13).
- **A policy carries no rule and no utility on any shape.** What the shape adds is the name of the shape it decides in
  and nothing else: a baseline learns nothing and is trained on no reward, so it carries neither `learning_rule` nor
  `utility` — the two attributes `as_policy` adds and a table reads a population by (`e2e-surface.md` §2,
  `surface.md` §10, `rules.md` §7, `utilities.md` §7, D-6, D-19, D-20).
- **A name outside the catalogue is refused naming it and the declared names**, like every other row that takes a
  shape, and never defaulted (`shapes.md` §2, §6, D-13).

Two of the six rules the shape reaches, and each states its own reason:

- **`fold-large-bet` reads its own shape's starting stack.** Its rule is "fold when `to_call` exceeds half the
  **starting stack**", and the stack is `engine.game_config(shape)["starting_stack"]` read through the granted arrow on
  every decision — 20 on the default shape and 100 a seat here, so "half the stack" is 10 there and 50 here. A folder
  built for this row therefore folds at 51 chips and check/calls at 11, where a folder holding the default shape's 20
  would fold at 11 — which is the whole reason the shape argument exists (`folders.md` §2, ASM-31, `seats.md` §2, §6,
  `module-map.md` §2, D-21, D-33).
- **`oracle`'s equity question is N-way.** `engine.equity` reads the seat count off the readout's `stacks` fact, so a
  six-seat decision is asked against the other **five** seats' uniformly random hands and an equity of about a sixth
  is what the pot-odds inequality is tested against (`e2e-surface.md` §3.1, `seats.md` §2, ASM-4, D-33). The shape makes
  the oracle usable at six seats by admitting the six-seat readout to the inequality at all (§2); no arithmetic here
  counts the opponents, because the readout already says how many seats there are (`seats.md` §3).

## 4. The head, the input width and the count: 433 → 18,510

The shape moves **both** ends of `architecture.md` §5's formula, and on this row neither end is the default's
(`shapes.md` §8, ASM-42, ASM-44):

| Quantity | `fixed-limit-20` | `no-limit-100` | `six-seat-no-limit-100` |
|---|---|---|---|
| `A`, the head | 3 | 6 | 6 |
| `I`, dense | 203 over 24 slots | 329 over 66 | **433** over 98 |
| tokens | 40 over vocabulary 96 | 82 over 96 | **122 over vocabulary 102** |
| `param_count` at `W = 36`, `D = 2` | `7344 + 2664 + 111` = 10,119 | `11880 + 2664 + 222` = 14,766 | `15624 + 2664 + 222` = **18,510** |

- **`433·36 + 36 = 15,624`** is the input block over this shape's own width, `2·(36² + 36) = 2,664` the trunk, and
  `6·36 + 6 = 222` the head `A·W + A` at `A = 6`: one kind at one width and depth costs 18,510 here against 10,119 at
  the default shape and 14,766 on the two-seat uncapped row (`shapes.md` §8, `sizing.md` §6, `architecture.md` §2, §5,
  ASM-10, ASM-40).
- **The difference is the shape's own two facts and nothing else.** 18,510 − 10,119 = `(433 − 203)·36 + 3·36 + 3`, the
  wider input block plus the three extra head rows and their bias (`shapes.md` §8, ASM-44, ASM-40).
- **A token learner on this row is sized by its vocabulary of 102**, not by its 122-token sequence: a token kind's
  input block is `V·W` with `V` the vocabulary, and its observation is checked against the 122 positions its encoder
  declares (`architecture.md` §6, `encodings.md` §1, §4, `docs/L2/features/capacity.md` §2, D-3).
- **An encoder-less build on this row is refused by name**, because a kind's declared `observation_size` is the default
  shape's 203 or 96 and no width here belongs to this shape (`shapes.md` §2, §6, `surface.md` §4, ASM-44).
- **No recorded count moves.** The default shape's 10,119 and the six rungs' counts are the fixed game's and stay so
  (`shapes.md` §5, §7, `ladder.md` §3–§4, ASM-10).

## 5. The container at 433

A learner of this row writes **format version 4** with a `game` field naming the shape, as every non-default row does,
and its `representation.size` and `representation.shape` are **433** and `[433]` — the shape's own width, not the
kind's 203 (`shapes.md` §5, §8, `checkpoint.md` §2.1, §3, ASM-40, ASM-44). A reader checks `params.count` and
`params.length` against the geometry that record gives, so a container of this row restores to the 18,510-parameter
head it was written at and a `game` disagreeing with its own `params` is refused naming the field and both values
(`restore.md` §2, `checkpoint.md` §3). A version-1, 2 or 3 container is still read as the default shape at 203, so the
18 shipped containers load untouched (`shapes.md` §5, ASM-5, ASM-40).

## 6. The refusals, side by side

| Where | What is refused | The message names |
|---|---|---|
| `build_learner` | a `game` the catalogue does not carry, the third row's name included among the declared ones; and a spec naming this row with **no** `encoder` | the entry point, the value and all three declared names in catalogue order (§1, `surface.md` §4); for the second, the shape, the kind's declared default size and the encoder this shape needs (§4) |
| `act`, `learn` | a mask, an `action` or a `next_legal` naming an index past `A = 6`, and an observation of another shape's width | the entry point, the learner's shape and vocabulary, and the index; and both widths, 433 against 203 (§1, `shapes.md` §3) |
| `build_baseline` | a name outside the six, a seed that is not an integer, and a `shape` the catalogue does not carry | the entry point, the offending value and the six names or the three shape names (§3, `baselines.md` §2) |
| a policy's `readout` | `stacks` whose length is no declared seat count, a seat index past the seats, a repeated card, a `hand_class` outside `None` or `0..8` | `policy(readout)`, the fact and the value (§2, ASM-30, ASM-44) |
| `load(path)` | a version-4 container whose `game`, `representation.size` and `params.count` do not describe one geometry | the field and both values (§5, `checkpoint.md` §3) |

## 7. What a seat count does not move

The two learning rules, the two utilities, the six hyper-declarations and the six baselines stay one declaration for
the catalogue; the readout keeps its eleven facts; both encodings keep their nine fields and their block order; the
amount normalisers and the bucket edges stay `features`' (`shapes.md` §2, §8, `utility.md` §1, `rule.md` §6,
`docs/L2/features/shapes.md` §5). What this row moves at this surface is three things and no fourth: the **seat count**
the readout validators admit, the **name** a container of it records, and the **stack** a `shape`-aware folder reads
(§1–§3, §5, `seats.md` §2, §6, ASM-44, D-33).

Two obligations this document states and does not discharge, their rows being other modules' (`module-map.md` §2,
D-13): `evaluation.opponent` must draw five distinct pool members for a six-seat hand and `engine.play_hand` must seat
them, so a run at six seats is `evaluation`'s and `engine`'s to deliver (`e2e-surface.md` §3.1, §3.4, `seats.md` §4,
ASM-43); and `training.run` must record the shape it played, which is the same `game` field a two-seat run records
(`e2e-surface.md` §3.5, `records.md` §12, D-33).
