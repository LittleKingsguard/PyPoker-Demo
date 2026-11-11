# evaluation — the seat count at this edge

- **Layer:** L3 · **Module:** `evaluation` · **Unit:** phase1 · **Rev:** 7 · **Date:** 2026-11-10
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
- **Owner:** the **seat count** at this edge, split out when the catalogue's third row arrived: the third restated name and the pairwise instrument's own arity (§1), the counted draw's derivation (§2), the four refusals and where each fires (§3), the pool's baselines on the pool's own shape (§4), and what the battery pins and deliberately does not (§5) (`docs/L1/seats.md` §2–§5, `docs/L2/evaluation/seats.md` §1–§4, D-33, ASM-43)
- **Reads:** `docs/L1/seats.md` §2–§6, `docs/L1/league.md` §2, §4, `docs/L1/records.md` §8, §12–§13, `docs/L1/module-map.md` §2, `docs/L1/shapes.md` §2, §8, `docs/L1/assumptions.md` (ASM-2, ASM-31, ASM-43), `docs/L2/evaluation/seats.md` §1–§4 and `docs/L2/agents/baselines.md` §2; at this layer `shape.md` §1–§4, `declarations.md` §1, `pool.md` §2, §7, `scheduler.md` §1, §3, §5, `matrix.md` §1, §4, §7, `rating.md` §1, §6, `report.md` §3, `errors.md` §2, §4
- **Not this file's:** a shape's name, its absence-as-default reading and the three shape refusals are `shape.md` §1–§3's; the pool record's `game` key and the pool's own refusals are `pool.md` §2, §5, §8's; a cell's per-hand seeds are `scheduler.md` §3's (`docs/L2/evaluation/seats.md` §1, D-13)

## 1. The third shape at this edge

The catalogue publishes **three** rows, default first, and this module restates the three **names** and nothing else about them (`docs/L1/seats.md` §2, `shape.md` §1, D-29, D-33):

    SHAPE_NAMES    = ("fixed-limit-20", "no-limit-100", "six-seat-no-limit-100")  # the catalogue's order, default first
    DEFAULT_SHAPE  = SHAPE_NAMES[0]                                             # what an absent `game` reads as (§2)
    PAIRWISE_SEATS = 2                                                          # the instrument's arity, not a game's

**The names are restated and the seat count is not.** `module-map.md` §2 grants this module `engine.game_config` and not `engine.game_shapes`, so the names are a restatement the join battery holds equal to `engine.game_shapes()`'s, in that order (`test_join_shapes.py::JOIN-EVL-15.1`), while a shape's **seats** are read off `engine.game_config(shape)["seats"]` through `declarations.seat_count` and written down nowhere (`module-map.md` §2, `shape.md` §1, D-13, D-33). One of the two may drift and it is the one a join case holds; the other is a call, and a copied `6` would be a game parameter with a second home (`docs/L1/e2e-surface.md` §3.1, D-13).

**`PAIRWISE_SEATS` is the instrument's arity and not a shape's row**, and its name says so: a cell is one unordered pair, a rating is fitted over pairs and a six-way hand produces a placement, so the pairwise instrument is two seats wide and a shape above it is refused (§3, `docs/L1/league.md` §4, D-22, D-33). Rejected: reading the arity off `SHAPE_NAMES`'s first row, which would make the instrument's reach a property of whichever game happened to be first (D-13, D-33).

**Both two-seat shapes pass every rule below untouched**: `fixed-limit-20` and `no-limit-100` have the instrument's seat count, so their cells, matrices, ratings and reports are what they were (`docs/L1/seats.md` §5, D-33).

## 2. The counted draw

`seeds._draw_order(seed, n)` returns the membership's `n` positions in one counted draw's order, from one tag and three steps (`docs/L1/seats.md` §4, `docs/L2/evaluation/seats.md` §2, ASM-43):

    _DRAW_TAG           = b"pypoker-evaluation/draw/v1"        # the derivation's own tag, a fifth beside the four seeds'
    first position      = _draw_index(seed, n) == seed % n    # the member the *uncounted* draw names
    remaining positions = 0 .. n-1 less the first, ascending by (_seed(_DRAW_TAG, seed, position), position)
    result              = (first,) + tuple(remaining)         # a permutation of 0 .. n-1

The first position is the modulo and not a digest, so a draw of one **is** the opponent `opponent(pool, seed)` has always returned; the rest are ordered by a tagged digest of the seed and the position, ties broken by the position, so the result is a permutation and one position never appears twice (ASM-2, ASM-43). **Without replacement is the whole point**: a six-seat hand seats five opponents, and a member seated twice is a seat facing itself (`docs/L1/seats.md` §4, ASM-43). The counted arm returns the members at `_draw_order(seed, n)[:count]`, distinct, in the draw's order (`pool.md` §7).

**Reproducible from `(seed, membership)`.** The order is a function of the seed and the pool's own ordered membership and of nothing else: two calls at one seed over one pool agree, no hand is played, no file is read and no stream is touched, so a draw is reproduced from the seed passed and the membership that pool carries (`pool.md` §7, ASM-2, ASM-43).

**A draw larger than the membership is refused, naming both counts** — `DrawExceedsMembership`: "the draw asks for 5 distinct members and the pool holds 4, and a draw is without replacement because a substitute seat would be an opponent the membership does not carry" (`errors.md` §4, ASM-43). A count that is not a positive integer is `InvalidDrawCount` naming it: a `bool`, a `0`, a `-1`, a `2.0` and a string are each refused, never rounded, never read as "all of them" (`errors.md` §2, §5). Wrapping, padding or truncating a draw to the membership is red, and the three are one defect in three spellings (`docs/L1/records.md` §8, `docs/L1/seats.md` §4).

**The uncounted arm is untouched.** `opponent(pool, seed)` still returns one policy at `seed % n` — a baseline at the caller's seed, a version at the seed its checkpoint records — so every training hand and every one-opponent caller gets today's draw again (`pool.md` §7, `shape.md` §2, ASM-2). **Measured:** a case sweeps **200 seeds** over a seven-member pool and draws five, no member twice, two calls at one seed agreeing, and `count=1` naming the member the uncounted draw names (`docs/L1/seats.md` §4, ASM-43).

## 3. The four refusals

One contract, one class. `match`, `matrix`, `rating` and `report` refuse a shape with more than `PAIRWISE_SEATS` seats as `SeatCountExceeded`, **naming the shape and its seat count** (`errors.md` §2, §4, `docs/L1/seats.md` §5, D-22, D-33):

    <entry>(<argument>): the shape <shape> has <n> seats, and a cell is one pair of two seats,
      so the pairwise instrument refuses a shape with more than 2 seats

The message names the entry point, the field at fault, the shape and **both** counts — the shape's seats and the instrument's arity — because a reader must be able to tell "this shape has six seats" from "this instrument takes two" (`errors.md` §3). One class and not one per site: a caller routes on "the instrument refuses this shape", never on which entry point raised it (`errors.md` §2, `shape.md` §3).

| Entry point | Where the check sits | What is therefore never done |
|---|---|---|
| `match` | after `_cell_shape` resolves the cell's one shape, before `_play_cell` | no hand is dealt, no seat split counted, no cell record exists (`scheduler.md` §1, §5) |
| `matrix` | after the frozen-pool and label checks, before `_variant_list` | no variant is looked at, no checkpoint touched, no member policy built (`matrix.md` §1, §7) |
| `rating` | in `_table_facts`, after the record's one shape is resolved | no value is fitted, no anchor applied, no bootstrap drawn (`rating.md` §1, §6) |
| `report` | the same reader as `_table_facts(matrix, "report")`, after the seven families are found present | no membership judged, no header read, no family assembled — a report is never half-built (`report.md` §1, §3) |

**Nothing else refuses a six-seat shape.** `build_pool`, `pool_members`, `offer`, `opponent`, `policy_from` and `cell_count` take the shape they are given, so a six-seat run keeps its hand, its readout, its encoder, its learner, its pool, its checkpoints and its greedy pass, and has no matrix and therefore no report (`docs/L1/seats.md` §5, `docs/L1/records.md` §12–§13, D-33).

## 4. The pool's baselines on the pool's own shape

A pool pins baselines, so it builds each for the shape the pool is on — `build_pool`'s probe as `agents.build_baseline(name, PROBE_SEED, shape)` and `opponent` as `agents.build_baseline(name, seed, pool.game)` — which is why a six-seat pool's `fold-large-bet` reads that row's declared `starting_stack` and its `oracle` is asked the six-way question the readout's six-entry `stacks` carries (`pool.md` §2, §7, `docs/L1/seats.md` §2, §4, ASM-43, D-33).

The boundary is read and not copied: `fold-large-bet` folds once `2 * to_call` exceeds the shape's `starting_stack`, so `to_call` 11 on the default shape's twenty chips and 51 on the six-seat row's hundred, and no `20` and no `100` stands in this module or in `agents` (`docs/L1/seats.md` §2, §6, ASM-31, `docs/L3/agents/baselines.md` §7). A six-seat `oracle` counts its opponents from `stacks`, whose length is the seat count, so six entries mean five random hands and not one (`docs/L1/seats.md` §3, ASM-44).

**A baseline's member record keeps `game: None`**: a baseline is a policy factory and not a trained estimator, so it records no shape of its own, and the shape it is built for is the pool's and is stated once, in the pool's record (`pool.md` §5, `docs/L1/records.md` §8, `shape.md` §4, D-33). That is what keeps a default-shape pool's records, order, id and behaviour byte-identical: the shape reaches the baseline through the constructor and never through the record.

**A table's sides stay shape-silent**: `matrix` builds each row through `policy._side`, which passes no shape on, so a cell's baseline is silent and a two-seat table's numbers do not move (`matrix.md` §4, `shape.md` §4, D-33). No six-seat table exists for that silence to be wrong about (§3, §5).

## 5. What this battery pins, and what it deliberately does not

`tests/evaluation/test_seats.py` is this document's file, `EVL-15.k` in the order the rules bite
(`guardrails.md` G8, G16), with the two shape constants held by `test_declarations.py`'s `EVL-1.16`:

| Case | Pins |
|---|---|
| `EVL-15.1` | `SHAPE_NAMES` holds the three names in the catalogue's order, `seats_of` answers 2, 2 and 6 out of `engine.game_config`, and `PAIRWISE_SEATS` is the default shape's own seat count (§1) |
| `EVL-15.2` | the uncounted draw is today's draw: one policy, the member at `seed % n`, answering exactly what `agents.build_baseline(name, seed)` and `build_baseline(name, seed, DEFAULT_SHAPE)` answer, so the shape argument moves nothing on the default shape (§2, §4) |
| `EVL-15.3` | `opponent(pool, seed, 5)` over a seven-member pool returns five policies, the 200-seed sweep finds no repeated member, two calls at one seed agree, each seat is the member at `_draw_order`'s position, and `count=1` names the uncounted member (§2) |
| `EVL-15.4` | the draw is a function of the seed and the pool's **ordered** membership: two pools whose windows are permuted draw at the same positions, so their members differ (§2) |
| `EVL-15.5` | `DrawExceedsMembership` above the membership naming both counts, `count = n` accepted, and `InvalidDrawCount` for a `0`, a negative, a float and a `bool` — with no hand played and the stream untouched (§2) |
| `EVL-15.6` | all four of `match`, `matrix`, `rating` and `report` refuse a six-seat shape as `SeatCountExceeded`, naming the shape and its 6 seats, while the same four calls succeed on both two-seat shapes (§3) |
| `EVL-15.7` | a two-seat pool is unchanged: id, membership order and the five member-record keys of a baselines-only pool, the id not moving with the shape, and the uncounted draw still `seed % n` (§1, §4) |
| `EVL-15.8` | a six-seat pool's drawn `fold-large-bet` and `oracle` are that shape's builds: the folder's two boundaries read off the two declared stacks and the oracle answering a legal descriptor on a real six-seat hand (§4) |
| `EVL-15.9` | the league builds no six-seat table in this pass: `matrix` refuses before a variant is reached, and the six-seat pool's own read-back still states its `game`, `rules` and `utilities`, so the run keeps its pool and draws and loses only the table (§3, §5) |

`tests/integration/evaluation/test_join_shapes.py` holds the restatement and the seat count against the real
engine: `JOIN-EVL-15.1` (the three names equal `engine.game_shapes()`'s, default first, and `DEFAULT_SHAPE` that
catalogue's first name) and `JOIN-EVL-15.5` (each declared name's seat count is `engine.game_config`'s,
`PAIRWISE_SEATS` is the default row's, a six-seat pool's folder answers the six-seat boundary the engine's own row
declares, the counted draw over a real frozen pool draws distinct members and refuses one above that membership,
and the four entry points refuse the shape naming it and its seats) (`docs/L1/e2e-surface.md` §3.1, §3.4, D-13,
ASM-43). The two boundaries of §4 are the L1 battery's `FAM-21` (`docs/L1/battery.md` §3).

**What is deliberately not here.** No six-seat matrix, rating or report exists in this pass and no case drives one: a placement is not a pair and no permutation model is designed (`docs/L1/seats.md` §5, D-22, D-33). No seat count is written down in this package and no case reads one off it — a case asks `engine.game_config` through `seat_count`, so a fourth row would move the answer and break no case (§1, D-13). And the only measured numbers this document quotes are §2's 200-seed sweep and §4's two boundaries; a cost figure on this shape is `docs/L1/sizing.md`'s and is not repeated here (ASM-21, ASM-43).
