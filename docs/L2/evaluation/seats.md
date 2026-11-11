# evaluation — the seat count at the surface

- **Layer:** L2 · **Module:** `evaluation` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-10
- **Ceiling:** 90 lines. At the ceiling, split by owner — never append
- **Owner of this file:** the **seat count** at this edge, split out of `surface.md` and `pool.md` when a third
  declared shape arrived: the third name in the restated catalogue, `opponent`'s optional draw count, the four
  refusals a shape with more than two seats meets, and the pool's own shape reaching the baselines it pins
  (`docs/L1/seats.md` §2–§5, `docs/L1/league.md` §2, §4, D-33, ASM-43)
- **Read with:** `surface.md` §2 (the shape, the policy, the member), §9–§13 (the five entry points this file
  widens), `pool.md` §1 and §4 (`build_pool`, `opponent`), `league.md` §3–§4 (the matrix and the rating)
- **Not this file's:** the draw's derivation and the arithmetic of the four checks are `docs/L3/evaluation/seats.md` §1–§4

## 1. What a seat count adds, and what it does not

A shape already names its seats, its blinds, its stack, its chips in play and its action vocabulary
(`docs/L1/shapes.md` §2, `docs/L1/seats.md` §2). The third declared shape adds **no entry point and no new
argument** — one name in a restatement, one optional argument whose absence is today's call, and four refusals
(`docs/L1/e2e-surface.md` §1, `docs/L1/seats.md` §6, D-12, D-33). The catalogue now publishes **three** rows,
default first, and this module restates the three **names**; the seat count itself is never restated
(`docs/L1/seats.md` §2, D-13, D-33).

- **`SHAPE_NAMES`** holds `fixed-limit-20`, `no-limit-100` and `six-seat-no-limit-100`, in the catalogue's order,
  and `DEFAULT_SHAPE` is the first (`docs/L1/shapes.md` §3, D-29, D-33). The join battery holds the restatement
  equal to `engine.game_shapes()`, which is the only arrow to the catalogue this module does not hold
  (`docs/L1/module-map.md` §2, D-13).
- **The seat count is read, never written:** `engine.game_config(shape)["seats"]` is the granted arrow and the one
  source of a shape's seats, so no literal `2` and no literal `6` stands in this module as a fact about a game
  (`docs/L1/module-map.md` §2, `docs/L1/seats.md` §3, D-13, D-33).
- **`PAIRWISE_SEATS` is the instrument's arity, not a game's:** a cell is one unordered pair and a rating is
  fitted over pairs, so the pairwise instrument is a game with two seats and a shape above it is refused
  (`docs/L1/league.md` §4, D-22, D-33). It is named so a reader cannot mistake it for a shape's row.
- **Two shapes are untouched by all of this:** the default shape and the two-seat no-limit shape produce exactly
  the cells, matrices, ratings and reports they produce today, because their seat count is the instrument's and
  every check below passes them (`docs/L1/seats.md` §5, D-33).
- **The league has no six-seat table in this pass** and builds none: a placement is not a pair and the permutation
  model a six-way table would need is not designed, so what the shape buys is a hand, a readout, an encoder, a
  learner, a pool and a greedy pass, and never a matrix and therefore never a report
  (`docs/L1/seats.md` §5, `docs/L1/records.md` §12–§13, D-22, D-33).

## 2. `opponent` — the optional draw count (`general` row)

- **Signature:** `opponent(pool, seed, count=None)`. The third argument is optional and its absence is **today's
  call** (`docs/L1/e2e-surface.md` §3.4, `docs/L1/seats.md` §4, ASM-43).
- **Without a count:** one policy drawn from the pool's ordered membership by the seed, exactly as `pool.md` §4
  states it — a baseline at the caller's seed, a version at the seed its checkpoint records, and the draw is the
  seed reduced modulo the membership's size (`pool.md` §4, ASM-2).
- **With a count:** that many **distinct** pool members, drawn **without replacement**, in the draw's order — the
  first is the member the uncounted draw names and the rest follow it in the derivation `docs/L3/evaluation/seats.md`
  §2 fixes — so a six-seat hand seats five opponents and never one member twice
  (`docs/L1/seats.md` §4, `docs/L1/league.md` §2, ASM-43).
- **Returns:** one policy without a count, and a tuple of them with one, each in the sense of `surface.md` §2, in
  the draw's order (`docs/L1/e2e-surface.md` §2, §3.4, ASM-43).
- **Refusals:** a value that is not a pool; a seed that is not an integer (`pool.md` §4); a **count that is not a
  positive integer**, naming it (`InvalidDrawCount`); and a **count larger than the membership**, naming **both
  counts** (`DrawExceedsMembership`), because a substitute seat would be an opponent the membership does not carry
  (`docs/L1/records.md` §8, `docs/L1/seats.md` §4, ASM-43).
- **Determinism:** two calls at one seed and one pool agree, and one seed's draw is a function of the pool's own
  ordered membership and of nothing else — no global stream is touched, no hand is played and no seed is
  substituted (`pool.md` §4, `docs/L1/league.md` §2, ASM-2, ASM-43).

## 3. The four refusals — a cell is a pair (`general` rows)

`match`, `matrix`, `rating` and `report` refuse a shape whose seat count is above the instrument's, **naming the
shape and its seat count**, in one class — `SeatCountExceeded` — because it is one contract and this module declares
one class per contract (`docs/L1/seats.md` §5, `docs/L1/league.md` §4, D-22, D-33):

| Entry point | Where the refusal fires | What it names |
|---|---|---|
| `match` | after the cell's one shape is resolved from its two sides and before the first hand of the cell | the shape and its seat count (`surface.md` §9, `docs/L3/evaluation/seats.md` §3) |
| `matrix` | after the pool is read and found frozen and **before a variant is looked at or a checkpoint touched** | the shape and its seat count (`surface.md` §10) |
| `rating` | with the matrix's other table checks, after its one shape is resolved and before a value is fitted | the shape and its seat count (`surface.md` §11) |
| `report` | through the same table checks, before a family is assembled | the shape and its seat count (`surface.md` §13) |

Nothing else about these four rows changes: their signatures, their returned records, their other refusals and
their determinism are `surface.md` §9–§13's and `league.md` §2–§4's (`docs/L1/league.md` §3–§5, D-16).

## 4. The pool's baselines on the pool's own shape

A pool pins baselines, and each is constructed once through `agents.build_baseline(name, seed, shape)` with **the
pool's** shape — both the probe `build_pool` makes and every policy `opponent` builds — so a six-seat pool's
`fold-large-bet` reads that row's declared stack of 100 and its `oracle` is asked the six-way question its readout
carries (`pool.md` §1, §4, `docs/L1/seats.md` §2, §4, §6, ASM-31, D-33).

A baseline's **member record** keeps `game: None`, and for a default-shape pool the records, the order, the id and
the behaviour are exactly what they are today: a baseline is a policy factory and not a trained estimator, so it
records no shape of its own, and the shape it is built for is the pool's (`pool.md` §2, `records.md` §8, D-33).
