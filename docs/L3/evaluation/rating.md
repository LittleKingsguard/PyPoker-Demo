# evaluation — the fitted rating

- **Owner:** `rating` — the Bradley-Terry fit over one matrix: the parameterisation and the anchor (§2), the
  **solver, its tolerance and its bound** (§3), the **hand-level bootstrap** (§4), the record (§5) and every
  refusal (§6) (`surface.md` §11, `records.md` §11, `league.md` §4, ASM-17)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `matrix.md` §5, `scheduler.md` §3, `declarations.md` §2.2, `errors.md` §2–§4

## 1. What is fitted, and what it is not

The rating is Bradley-Terry, fitted over the matrix's cells on each cell's win/tie/loss counts with **a tie counted
as half a win to each side** (ASM-17, `league.md` §4). It states where a member stands among **the table's named
members** on this game at this cell size and is never a claim of poker skill, a ranking of versions alone or a
statement about a member the table does not name (D-16, `league.md` §8, brief §8).

`rating(matrix)` reads `records.md` §10's matrix record — this module's own or a hand-built one, because what is
checked is the record and not its provenance (`surface.md` §11) — and reads only the keys it fits: `members`, `cells`,
`hands_per_cell`, `table_seed` and `table` (`matrix.md` §5). The record's `rules` and `population` are **not read**: they
say which estimators played, not how the fit goes (D-19, `league.md` §4). This module's own keys — `pool`,
`member_records`, `unlabelled`, `cell_count` — are ignored too, so a hand-built table is rated as readily as a played
one. It plays no hand, reads no file and leaves the global `random` stream where it found it (`surface.md` §1).

## 2. The parameterisation, and the anchor

One unknown per member: a log-strength `θ_i`, with `s_i = exp(θ_i)` and `P(i beats j) = s_i / (s_i + s_j)`. A cell
is read through **its own** `members` — `records.md` §9 makes `directions` position-aligned with the cell's pair, not
with the matrix's membership, so a hand-built table may list its pair in either order:

    a, b       = cells[cell]["members"]                     # this cell's pair, in this cell's order
    w_ab       = cells[cell].directions[0].wins + cells[cell].directions[0].ties / 2     # half a win a side
    w_ba       = cells[cell].directions[1].wins + cells[cell].directions[1].ties / 2
    n_ab       = w_ab + w_ba                                # == the cell's hands for a sound cell

so a tie is a half-win to each side and the cell's total is its hands (`league.md` §4, ASM-17). A member's win mass
is `W_a = Σ_b w_ab` and its expected win mass is `E_a = Σ_b n_ab · s_a / (s_a + s_b)`.

**The anchor** is the three baselines' mean fixed at **0** (`league.md` §4, ASM-17). It is applied as a shift after
every iteration — `c = (θ_random + θ_always-call + θ_oracle) / 3`, then `θ_i ← θ_i − c` for every member — because the
likelihood is invariant to adding one constant to every `θ` and the shift therefore changes no probability while it
pins the scale (`records.md` §11, D-16). The three baseline positions are found by **id equality** with
`agents.baselines()`'s names, which is why a baseline's member id is its name (`pool.md` §2).

## 3. The solver, the tolerance and the bound

The fit is **Hunter's minorise-maximise (MM) iteration**, which is Bradley-Terry's standard closed-form solver: each
step maximises a lower bound of the log-likelihood, so the log-likelihood never decreases and the iteration
converges to the maximum. No learning rate and no gradient tolerance is tuned, because there is neither a learning
rate nor a gradient descent. `src/evaluation/rating.py` fixes three constants:

    BOUND          = 10.0        # the largest |θ| the fit may return, in log-strength (a 22,026:1 win ratio)
    TOLERANCE      = 1e-10       # the largest |Δθ| a step may move and still count as converged
    MAX_ITERATIONS = 10_000      # the cap; reaching it is what `converged` false means

One iteration, in this order, `θ` starting at all zeros; `rating._fit` is this whole loop, its argument list L4's:

1. `Δ_a = ln(W_a) − ln(Σ_b n_ab · s_a / (s_a + s_b))` for every member with `W_a > 0`, from the iterate at the start
   of the step; a member with `W_a == 0` has `Δ_a = −∞` and takes no update here — step 4 pins it;
2. `θ_a ← θ_a + Δ_a` for every member step 1 computed: Hunter's update, the closed form the lower bound maximises;
3. `θ_a ← min(BOUND, max(−BOUND, θ_a))`: the **bound** is applied here, and `bound_applied` is set the first time a
   clamp actually changes a value;
4. the anchor's shift of §2 is applied, and **then the two ends are pinned**: a member with `W_a == 0` — it won
   nothing — is `θ_a ← −BOUND`, and one with `W_a == n_a` — no losses and no ties — is `θ_a ← +BOUND`, with
   `bound_applied` set for it. The pin is taken **after** the shift, so the value the record carries is the bound
   itself and not what the shift left of it;
5. the step is done: `converged` is true when `max_a |θ_a − θ_a⁰| ≤ TOLERANCE` (θ⁰ the iterate entering step 1),
   and the loop stops; otherwise it continues, and stopping at `MAX_ITERATIONS` leaves `converged` false.

**The bound is what makes a member with no finite maximum finite, at either end.** A member with no losses and no
ties has `W_a = n_a`, so `ln(W_a / E_a) > 0` at every finite `θ` and its maximum-likelihood value is `+∞`; a member
with no wins and no ties has `W_a = 0` and its value is `−∞`. Step 4 pins each at the bound it tends to and sets
`bound_applied`, and its interval then states that the evidence pinned the member rather than measured it, because
§4's widening keeps the pinned value inside its own bounds (ASM-17, `league.md` §4, FAM-9.6). A bounded fit terminates
by step 5 like any other: both ends are re-pinned at every step, so the pinned member repeats its own value and the free
members reach their fixed point — `|Δθ|` reaches `0` and the loop stops **converged**, because a value pinned at the
bound is a stationary point. Where the pinned member is itself one of the three anchoring baselines the pin also
displaces the mean it was applied after, so that table's baselines' mean is not 0 while its fit still converges:
`bound_applied` is true and step 5 still fires. `records.md` §11's `converged` is therefore about reaching a stationary
point and never about the cap alone (D-6).

## 4. The bootstrap that makes the interval

Each member's interval is a `95%` **hand-level** bootstrap: the hands inside each cell are resampled, the fit is
repeated, and the interval is the 2.5th to 97.5th percentile of the resulting values (`league.md` §4, ASM-17).

- **The generator.** One `numpy.random.Generator(numpy.random.PCG64(seeds._bootstrap_seed(table_seed)))`, taken
  from the matrix's own `table_seed` (`scheduler.md` §3). It is this module's own generator: the global `random`
  stream is untouched, and the seed is recorded as `bootstrap_seed` so the interval can be re-run (`surface.md` §11).
- **The resample.** `rating._resample` draws `RESAMPLES = 200` replicates. In each, the cells are visited in the
  matrix's `cells` order and each cell contributes **one** three-category draw, `counts = generator.multinomial(hands,
  p)` with `p = (wins, ties, losses) / hands` taken from that cell's direction 0 — resampling the cell's hands with
  replacement and recounting exactly that. The replicate's masses are `w' = counts[0] + counts[1] / 2` for the cell's
  first member and `hands − w'` for its second: a resampled cell still partitions its own hands, and direction 1 needs
  no second draw because it is the mirror of direction 0 (`records.md` §9).
- **The refit.** The same solver as §3, from `θ = 0` at every replicate — no warm start, so one replicate's answer
  never depends on another's — with the same anchor and the same bound, so every replicate's values are finite.
- **The percentiles.** The 200 replicate values of one member are sorted ascending, `v[0] … v[199]`, and with
  `position = 199 × q / 100` for `q = 2.5` and `q = 97.5`, `i = floor(position)`, `f = position − i`:
  `bound = v[i] + f × (v[min(i+1, 199)] − v[i])`. So the lower end is `v[4] + 0.975 (v[5] − v[4])` and the upper end
  `v[194] + 0.025 (v[195] − v[194])` — linear interpolation between the two nearest order statistics.
- **The widening.** `lower = min(lower, value)` and `upper = max(upper, value)`, so the fitted value always lies
  inside its own interval (`records.md` §11, FAM-9.2, FAM-9.6).

## 5. The record

`records.md` §11's six keys come first, then this module's own, which no caller may depend on (`records.md` §1):

| Key | Content |
|---|---|
| `values` | keyed by member id, in `members` order, one entry each: `{"value": float, "interval": (lower, upper), "hands": int, "bounded": bool}` |
| `method` | the `str` `Bradley-Terry` — the same string `protocol()["rating"]["method"]` declares (`declarations.md` §2.2) |
| `anchor` | `declarations.md` §2.2's sentence, written there as `the three baselines' mean fixed at 0` — §2.2 is its one home, and `league()["rating"]` carries the same `str` |
| `bound_applied` | `True` iff §3's bound changed a value — a clamp at step 3 or a pin at step 4; a `bool` |
| `bootstrap_seed` | the integer §4's generator was built from |
| `converged` | `True` iff §3 step 5 stopped on `TOLERANCE`; a `bool` |
| `bound`, `tolerance`, `iterations`, `resamples` | `10.0`, `1e-10`, the steps this fit took, and `200` — the fit's own record |
| `hands_per_cell`, `members`, `table_seed`, `table` | the matrix's four own facts, copied, so a rating names the table it was fitted over |

An entry's `hands` is `hands_per_cell × (K − 1)` — one cell against each of the other members — and that is the
number of hands behind the value (`records.md` §11, FAM-9.5). `bounded` repeats `bound_applied` per member, so a
reader can see *which* member was pinned; the record's own `bound_applied` is the union. The interval is one unordered
pair either way: `records.md` §11 fixes neither the bounds' key names nor the order they are stated in
(`_records.rating_interval` tolerates either).

## 6. Refusals — a matrix that is not a table

`rating` refuses before it fits anything, in this order, and fits nothing when it refuses (`surface.md` §11):

| Class | Raised when |
|---|---|
| `InvalidMatrix` | the argument is not a mapping (`records.md` §10) |
| `MissingMatrixKey` | `members`, `cells`, `hands_per_cell`, `table_seed` or `table` is absent — naming the key |
| `CellCountMismatch` | the number of cells is not `K(K−1)/2` for `K = len(members)` (`league.md` §3) |
| `DuplicatePair` | a pair of members appears in two cells — one cell per unordered pair (`league.md` §3) |
| `ForeignMember` | a cell names a member the membership does not — naming it (`records.md` §10) |
| `UnevenCell` | a cell's `hands` differs from the record's `hands_per_cell` — no member's row is measured more precisely than another's (`league.md` §3, FAM-8.7) |
| `MissingBaseline` | the membership lacks `random`, `always-call` or `oracle` — the anchor would not exist (`protocol.md` §3, FAM-8.8) |

A `table` label's **value** is not re-judged here: `matrix` refused anything but `live` or `full` when it built the
record (`matrix.md` §7), and `rating` fits a hand-built record by the rules above and nothing else (`surface.md`
§11). A cell whose two directions disagree with its hand count is not refused either: §2's `n_ij` is the observed
total, so the fit reads what the record says instead of repairing it. Refusing more than `surface.md` §11 refuses is
a defect — a battery may hand any valid table, hand-built ones included.

## 7. What is deliberately free

- the container of `values` — a mapping keyed by member id (this design's choice) or a sequence of entries each
  carrying its member's id (`records.md` §11 fixes one entry per matrix member, not the container);
- the dtype of the returned numbers beyond being plain `float`s, the sign convention of the interval's two ends, and
  the arithmetic order inside a step (a different order moves the last bits, not the answer);
- whether the 200 replicates are collected or reduced as they are drawn — only `RESAMPLES`, §4's draws and percentiles are contract.
