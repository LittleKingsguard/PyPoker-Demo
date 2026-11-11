# PyPoker-Demo — L1 the third seat count

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-10
- **Covers:** D-33 after D-32's blocker and the widening `shapes.md` §8 states — the six-seat no-limit shape as a catalogue row, the readout and both layouts as the shape's, five opponents drawn without replacement and one rotating seat, the pairwise instrument's refusals, what it costs in endpoints and cases, and the test it exists for (D-33, D-32, D-23, D-29)
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append

## 1. What this adds, and what it deliberately does not

`shapes.md` §8 states the widened history block and what it costs; this page states the **seat count** — a third
declared shape of six seats, and how a run seats a learner against five opponents (`shapes.md` §2, §8, D-33 §2).
It adds no criterion and no rung, and no figure on this shape is compared with one on another (`shapes.md` §6).

Two things it does not do. It builds **no league table**: a cell is a pair, a six-way hand is a placement, and no
permutation model is designed here (§5, D-22, D-33 §3). And it authorises **no overnight run** (§7, D-26, D-28):
D-23's refusal of six-player seating is superseded **for this test only**, so the shipped artefacts stay heads-up
measurements and keep their meaning (`strata/records/six-seat-probe.md`, D-23, D-33 §4).

## 2. The third shape, as a row of the catalogue

`engine.game_shapes()` publishes **three** rows, default first, and the third is reached as any configuration
outside the registry is — as a value through `training.run`, since no rung of brief §2 declares it and the ladder is
still one game (`shapes.md` §2, `battery.md` §3 FAM-15, D-3, `ladder.md` §2).

| Key | `six-seat-no-limit-100` |
|---|---|
| seats, blinds | six seats, blinds 1/2, one blind level that never rises |
| starting stack, chips in play | 100 chips a seat, 600 in play — `pot + sum(stacks)` at every decision |
| betting | no fixed bet and no cap: any legal amount up to the stack, as the two-seat uncapped row declares |
| action vocabulary | the same six descriptors in the same index order, `fold` and `check-call` then the four bands (`sizing.md` §2–§3) |
| capacity, widths, head | 98 history slots, its own derived bound; 433 dense slots and 122 tokens over a vocabulary of 102; a head of 6 (`shapes.md` §8) |
| amount normalisers | stack ÷100, pot ÷600, `to_call` ÷100, amount in force ÷100, action count ÷50 |
| declared pool additions | the three anchors of D-6 and the three folders of D-21, plus version members of its own shape (§4) |

The stack, the blinds and the divisors are the two-seat uncapped row's, because it is the same game with more
seats; the **pot** divides by the 600 chips in play, since a divisor of 200 on a six-seat pot is a clip rather than a
normalisation (`sizing.md` §5, ASM-39). A seat count adds no descriptor: it changes the price of aggression, because
a bluff must buy five folds (D-26, D-33 §2).

## 3. The readout and both layouts are the shape's

Every readout **fact** stays the one of `e2e-surface.md` §2 and no twelfth is added; the seat count changes what two
of them are worth, and `payoffs` stays one net delta per seat summing to zero (`records.md` §5, D-3):

- `seat` is `(index, on_button)` with the index in `0 .. seats − 1` and the shape's declared `button_seat` the
  button — 0 everywhere, so a seat index means one thing and rotating the learner across seats rotates it across
  **positions** (D-33 §2, `league.md` §3);
- `stacks` is one entry per seat in seat order — six here, two elsewhere — so `pot + sum(stacks)` is the shape's
  chips in play at every decision (ASM-28).

Both layouts declare the **seat** and **stacks** blocks' width as the seat count and keep the shape's history
width: six seat slots and six stack slots here, two apiece on the default shape (`shapes.md` §8, ASM-44). The dense
seat block is the acting seat's one-hot over the seat count, which is the two values it has always held — seat 0
writes `[0, 1]`, seat 1 `[1, 0]` — so the default shape's observations do not move. The token encoding gives this
row **its own ids**, one per seat slot at 96 to 101 above every id the other rows use, over a vocabulary of 102, so
no existing id is renamed (ASM-44, `shapes.md` §5). A per-shape width is the block table's data, not a fork of the
encoder (`docs/L3/features`, D-13).

## 4. Five opponents and one rotating seat

A six-seat hand holds six policies and one is the learner's. `engine.play_hand` takes the seating as an **optional**
`seats` argument — the shape's whole seating, in seat order — and plays exactly the two positional policies it
always played when that argument is absent, so no fixed-limit or two-seat caller changes; a sequence of the wrong
length, or one beside two positional policies, is refused by name (`e2e-surface.md` §3.1).

`evaluation.opponent` takes an optional `count` and returns **that many distinct pool members**, drawn without
replacement from the frozen pool, so a seat never faces itself and the draw is reproducible from the seed and the
membership (`league.md` §2, ASM-43); a pool holding fewer is refused naming both (`records.md` §8, D-16). The
six-seat pool therefore holds both folders and raisers at once — the composition D-32 measured the league missing,
because a raise from a strong-hand opponent is the situation folding is correct in
(`strata/records/fold-when-correct.md`, `strata/records/pool-without-raiser.md` §1, D-33 §2).

The learner sits at `hand index mod seats`, holding each seat for one hand in six while the five opponents fill the
rest in the draw's order — position is a real and unequal advantage in a multi-way pot, and rotating it keeps a
seed's chips from being a measurement of the seat it drew (D-22, ASM-43).

## 5. The pairwise instrument refuses a six-seat table

A cell is a pair and a rating is fitted over pairs; a placement is neither, and the permutation model a six-way
table would need is not designed in this pass (D-22, D-33 §3). So `evaluation.match`, `evaluation.matrix`,
`evaluation.rating` and `evaluation.report` **refuse a shape whose seat count is not two**, naming the shape and its
seat count (`league.md` §4, ASM-43). Everything the test needs — hands, readout, encoder, learner, pool, greedy
pass — works at six seats, and a run still writes its curves, its pool, its checkpoints and its `greedy` block;
what it cannot write is a matrix, and therefore a report's seven families (`records.md` §12–§13, D-16).

## 6. What it costs in the map and in the battery

**No new entry point.** Four rows are widened by an optional argument whose absence is today's value — `seats` on
`play_hand`, `count` on `opponent`, `shape` on `build_baseline`, and the shape already carried by the rows of
`e2e-surface.md` §2 — so the map stays at **50 endpoints**, every module keeps its `modules.json` row and harness
ceiling, and the `fixed`/`general` split stays 13/37; `build_baseline`'s shape lets `fold-large-bet` read its own
shape's starting stack, so "half the stack" is 50 on a hundred-chip table (`e2e-surface.md` §4–§5, ASM-31).

**The e2e battery loses no case.** The ten cases and the one helper that assert one game or three indices become
the same assertions for the shape in force, `FAM-2`'s and `FAM-19`'s per-shape assertions extend to the third row, and
one new family — `FAM-21` — drives the widened capacity, the six-seat hand, the draw without replacement and the
four refusals (`battery.md` §3, §5): nothing dropped, no assertion loosened (D-21's rule, extended).

## 7. The test this exists for

Five seeds (0–4) at the live training budget, against a pool holding the three anchors, the three folders and at
least one trained no-limit version member, each seed's **greedy** pass retained, and the evidence read as two things
and nothing else: the **action census** by descriptor — fold, check-call and each raise band — and the **chips per
hand with an interval** (`sizing.md` §4, ASM-38, D-33 §3), the census computed from the run record's own `greedy`
block by a script and never read by eye (`sizing.md` §7, ASM-23).

**No criterion is pinned**, and that is D-33's decision rather than an omission: the question is behavioural, and a
threshold fixed before the number exists would be D-28's defect at a further locus (D-28, D-31, D-33). Chips are
reported with an interval, never thresholded, because a five-seed live sample cannot resolve a small edge
(`league.md` §7, ASM-21).

**A fold share at zero is a named failure**, reported with its seed and count: the **pool artefact**, raisers that
never fire in the learner's face; the **exploration artefact**, a census read off a behaviour policy instead of the
`off` pass; the **seat artefact**, chips dominated by the seat drawn; the **collapse**, one descriptor holding
nearly every decision (`sizing.md` §7, ASM-38, D-28).

## 8. What stays Phase 1's

The 18 containers, `checkpoints/evidence/r1-live.json`, `tables/league-full.json`, the six rungs and both deep runs are
Phase 1's fixed-limit evidence: not re-measured, not rewritten, never compared with anything here, and the standard this
change is held to is the byte-identical proof the previous build carried (`shapes.md` §5–§6, D-8, ASM-18, D-33 §4).
