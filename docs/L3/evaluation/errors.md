# evaluation — refusals

- **Owner:** the error classes and the message grammar every refusal of this module follows, the canonical message
  per refusal the L2 surface declares, and what is deliberately *not* refused
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `declarations.md` §7, `pool.md` §8, `scheduler.md` §6, `matrix.md` §7, `rating.md` §6, `report.md` §3

## 1. Why a hierarchy

`surface.md` §1 says an invalid argument is refused by raising an error that names the violated contract, and that
no entry point coerces a value, substitutes a default, swallows an error or returns part of a record. The error is
therefore the only reporting channel: nothing comes back as a failure record, and no refused call has an observable
effect — `build_pool` validates the whole declaration before it builds a member, `matrix` validates before it loads
a checkpoint, and `rating` and `report` validate before they fit or assemble anything (`pool.md` §8, `rating.md` §6).

A hierarchy exists so a caller can catch "this module refused me" without catching a `KeyError` from a bug: a mistyped
key, a `TypeError` from a helper or a NumPy error from the fit each leak an internal decision as a crash. Nothing else
is caught — the one declared catch is `scheduler.md` §6's — and a bare `Exception` is never the answer to a bad argument.

## 2. The classes — `src/evaluation/errors.py`

    class EvaluationError(Exception)             # base of every refusal of this module
    class InvalidPool(EvaluationError)           # pool_members, offer, opponent, matrix: not a pool this module built
    class PoolDeclarationInvalid(EvaluationError) # build_pool: not a mapping, or missing members / m / frozen
    class PoolBoundInvalid(EvaluationError)      # build_pool: m not a positive integer, a bool, or above the league's M
    class MemberInvalid(EvaluationError)         # a member or a side is not the record it must be; a bad id or lineage
    class MemberUnloadable(EvaluationError)      # a member/version carries no path, or its path is not readable
    class MemberDuplicate(EvaluationError)       # two records carry one id, a declared id is a pinned baseline's name, an
                                                 #   offered version is a member, or a table's membership is not distinct
    class LineageConflict(EvaluationError)       # two members descend from one (surface.md §5)
    class LineageCycle(EvaluationError)          # a chain reaches no start (surface.md §5)
    class PoolFrozen(EvaluationError)             # offer into a frozen pool
    class LineageNotExtended(EvaluationError)    # offer: the lineage is not the window's newest version
    class PoolNotFrozen(EvaluationError)         # matrix: the pool may still change while it is tabled
    class InvalidSeed(EvaluationError)           # opponent, match: the seed is not an integer
    class InvalidHandCount(EvaluationError)      # match: the hand count is not a positive integer
    class SameMemberPair(EvaluationError)        # match: the two sides carry one id
    class VariantCountInvalid(EvaluationError)   # matrix: not one and not two variants
    class VariantInvalid(EvaluationError)        # matrix: a variant is not a policy
    class UnknownTable(EvaluationError)          # matrix: the label is not 'live' or 'full'
    class InvalidMembership(EvaluationError)     # league()'s cell_count: not an int >= 2, a sequence or a members mapping
    class InvalidMatrix(EvaluationError)         # rating: the argument is not a matrix record
    class MissingMatrixKey(EvaluationError)      # rating: a required matrix key is absent — the key is named
    class CellCountMismatch(EvaluationError)     # rating, report: the cell count is not K(K-1)/2
    class DuplicatePair(EvaluationError)         # rating, report: one unordered pair appears in two cells
    class ForeignMember(EvaluationError)         # rating, report: a cell names a member the membership does not hold
    class UnevenCell(EvaluationError)            # rating, report: a cell's hands differ from hands_per_cell
    class MissingBaseline(EvaluationError)       # rating, report: the three-baseline anchor is incomplete
    class CheckpointUnreadable(EvaluationError)  # policy_from, a member's path: no readable file, or no readable zip
    class CheckpointRecordMissing(EvaluationError) # container: no seed or encoding name, or not in a form this module reads — the fact is named
    class UnknownEncoding(EvaluationError)       # a checkpoint: features.build_encoder refuses the recorded name, or as_policy refuses the encoder it builds
    class MissingFamily(EvaluationError)         # report: an absent evidence family — named as protocol() spells it
    class MembershipMismatch(EvaluationError)    # report: the matrix's membership is not the pool's plus the variants
    class RatingMismatch(EvaluationError)        # report: the rating does not name exactly the matrix's members
    class HeaderIncomplete(EvaluationError)      # report: a header item is missing — the item is named
    class InvalidArgument(EvaluationError)       # any: an argument of the wrong type — a record that is not a mapping,
                                                 #   a rung name that is not a str

Thirty-three subclasses under one base, one per refusal family of `surface.md` §5–§13. They are **not** module-level
names of the `evaluation` package: they live below an entry point and are not surface (`README.md` §3,
`e2e-surface.md` §1). Their names and nesting are nonetheless contract, because `README.md` §4 makes `errors.py`'s
contents contract for `tests/evaluation/`: `test_errors.py` (`EVL-9.1`–`EVL-9.2`) is the one case that asserts a
subclass by name, and everywhere else a battery asserts the *behaviour* — that the call raises this module's
`EvaluationError`, and what the message says — never which subclass arrived (`docs/L3/agents/errors.md` §2 agrees).

## 3. The message grammar

Every message has the form

    "<entry point>(<argument or field>): <the violated contract>, got <what was passed>"

so the contract is named in the design's own words and the offending value is visible; where nothing was passed — a
missing key — the message names the key instead of inventing a `got` clause. A `report` reusing `rating.md` §6's table
checks names the violated rule in the **field** slot — `hands` / `cells` / `pair` / the missing baseline — because the check
is the rating's own and not `report`'s (`report.md` §3 item 2), while still leading with its entry point: `report(cells): …`
and `report(members): …`, as §4's rows spell them and `EVL-9.9` asserts, and `cell_count(K): …` names the callable `league()`
returns (`declarations.md` §5). Three properties the battery relies on: the message names the entry point, the rule or
`cell_count`, the argument or key at fault and, where there is one, the offending value; it never claims a value was accepted;
and a member, a family or a baseline is named by its **id**, because a refusal a reader cannot act on is not a refusal.

## 4. The canonical messages

L4 follows these spellings; the unit battery matches them tolerantly (the entry point's name, the field's name and the
value), and `tests/e2e/`'s `refusal_text` reader accepts any wording that names the family, the pool rule or the member.

| Where | Message |
|---|---|
| `build_pool` not a mapping | `build_pool(declaration): the declaration must be a mapping, got list` |
| `build_pool` missing key | `build_pool(declaration): the declaration is missing the required key 'frozen'` |
| `build_pool` bound | `build_pool(m): the bound must be a positive integer no larger than the league's 5, got 6` |
| `build_pool` flag | `build_pool(frozen): the frozen flag must be a boolean, got 'yes'` |
| `build_pool` member key | `build_pool(member 'version-kestrel'): the member is missing the required key 'lineage'` |
| `build_pool` bad id | `build_pool(member 'version-kestrel'): the id must be a non-empty string without a newline, got ''` |
| `build_pool` unreadable | `build_pool(member 'version-kestrel'): the path 'checkpoints/x.pt' names no readable file` |
| `build_pool` two successors | `build_pool(member 'version-quarry'): 'version-bramble' is the lineage of two members, 'version-thistle' and 'version-quarry'` |
| `build_pool` one id twice | `build_pool(member 'version-thistle'): 'version-thistle' appears in two member records, and a pool names one member once` |
| `build_pool` a baseline's name | `build_pool(member 'random'): 'random' is one of the three pinned baselines' names, and a pool names one member once` |
| `build_pool` cycle | `build_pool(member 'version-kestrel'): the lineage order reaches no start, because the chain through 'version-kestrel' closes on itself` |
| `pool_members` | `pool_members(pool): the argument must be a pool from build_pool or offer, got dict` |
| `offer` frozen | `offer(pool): the pool is frozen and a frozen membership does not change while it is used` |
| `offer` duplicate | `offer(version 'version-osprey'): 'version-osprey' is already a member of the pool` |
| `offer` not newest | `offer(version 'version-osprey'): its lineage 'version-kestrel' is not the window's newest member 'version-marlin'` |
| `opponent` seed | `opponent(seed): the seed must be an integer, got '8086'` |
| `opponent` no path | `opponent(member 'version-kestrel'): the drawn member carries no path, so it cannot be an opponent` |
| `match` hands | `match(hands): the hand count must be a positive integer, got 0` |
| `match` side | `match(left): the side must be a policy, a version record or one of ('random', 'always-call', 'oracle'), got 42` |
| `match` one id | `match(left, right): the two sides carry one id 'random', and a cell pairs two distinct members` |
| `matrix` unfrozen | `matrix(pool): the pool is not frozen, and a pool does not change while it is tabled` |
| `matrix` label | `matrix(table): the table label must be 'live' or 'full', got 'medium'` |
| `matrix` variants | `matrix(variants): the variant count must be 1 or 2, got 3` |
| `matrix` not distinct | `matrix(members): 'variant-1' is the id of two members of the table, and a cell pairs two distinct members` |
| `rating` not a record | `rating(matrix): the argument must be a matrix record, got list` |
| `rating` missing key | `rating(matrix): the matrix is missing the required key 'hands_per_cell'` |
| `rating` cell count | `rating(cells): 35 cells are not the 36 pairs of a 9-member membership` |
| `rating` pair twice | `rating(cells): the pair ('random', 'oracle') appears in two cells` |
| `rating` foreign member | `rating(cells): the cell ('random', 'version-nimbus') names 'version-nimbus', which is not a member` |
| `rating` uneven | `rating(cells): the cell ('random', 'oracle') plays 119 hands and the matrix declares 120` |
| `rating` no baseline | `rating(members): the membership holds no 'oracle' baseline, and the three baselines are the anchor` |
| `policy_from` path | `policy_from(path): '/ckpt/x.pt' names no readable file, or no readable zip` |
| `policy_from` no recorded seed | `policy_from(path): the checkpoint '/ckpt/x.pt' records no seed, and no seed is ever substituted for a missing one` |
| `policy_from` encoding | `policy_from(path): the checkpoint '/ckpt/x.pt' records the encoding 'bogus', and features.build_encoder refuses that name` |
| `report` family | `report(record): the record carries no evidence family 'axis row'` |
| `report` foreign | `report(matrix): 'version-outsider-9901' is not a member of the pool the report names` |
| `report` baseline | `report(members): the membership holds no 'oracle' baseline, and the three baselines are the anchor` |
| `report` rating | `report(rating): the rating names 'variant-1' and the matrix does not` |
| `report` header | `report(header): the header is missing the required item 'table seed'` |
| `cell_count` | `cell_count(K): the bound must be an integer of at least 2, a members mapping or a sequence, got 1` |

## 5. What is *not* refused

Refusing more than the contract refuses is also a defect — a battery may pass any valid instance (`battery.md` §4, D-15)
— so this module does **not** refuse:

- a declaration **richer than the bound**: it is windowed to its last `m` (`pool.md` §2, `league.md` §2);
- a member record carrying **extra keys**, and one with no `path` — admitted, and only a loader refuses it (`surface.md` §5);
- a declaration holding **more than one lineage chain**: the chains are taken in the order their starts are declared (`pool.md` §3);
- a **`pool-1`/`policy-2` side**: an opaque callable is a legal side whose capacity is simply unmeasured (`scheduler.md` §5);
- a version record whose own `seed` disagrees with the seed its checkpoint records: the container decides the action and
  the record's `seed` is carried, so nothing is refused (`scheduler.md` §5);
- a **numpy integer** for a seed, a count or a position (`numpy.int64` is an `Integral`), but never a **`bool`**: a flag is not a count;
- a **hand-built matrix** handed to `rating`, and a matrix carrying this module's own keys beside the required ones (`rating.md` §1, `surface.md` §11);
- a **`table` label's value** re-judged by `rating`, and a cell whose two directions disagree with its hand count (`rating.md` §6);
- an **explicit `n/a` family** in a record, and a family whose value is a string rather than a record (`report.md` §1, §3).

## 6. Where the messages are asserted

`tests/e2e/` asserts that each entry point is callable with a valid instance (FAM-1.27–1.37) and that the league's
refusals happen and name what they refused (FAM-8.7–8.9, FAM-11.2–11.8); the grammar of §3 is asserted by
`tests/evaluation/test_errors.py` under `EVL-9.1`–`EVL-9.11`. The rule L4 holds is stronger than the L1 battery can see: a
message omitting the entry point's name, the field at fault or the value passes L1 and fails the unit battery (`guardrails.md` G16).
