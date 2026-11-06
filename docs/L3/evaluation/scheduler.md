# evaluation — the scheduler, one cell at a time

- **Owner:** `match` and `policy_from` — one cell and the sides it plays: seat alternation, the **seed derivations**
  (§3, the home of `seeds.py`), win/tie/loss from net chips, the seat split, the zero-sum directions, how a side
  becomes a policy, the **two facts a checkpoint records** (§5.1), and every refusal (`surface.md` §9, §12, `league.md` §2–§3)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `pool.md` §7, `matrix.md` §3–§4, `rating.md` §4, `errors.md` §2–§4

## 1. The cell

A cell is one unordered pair of members, played at one hand count and reported in both directions (`league.md` §2,
`e2e-surface.md` §2). `match(left, right, hands, seed)` returns one `records.md` §9 record, a loop pass per hand:

    s_i     = seeds._hand_seed(seed, i)                              # §3 — one pass per hand, i < hands
    seats   = (left, right) if i is even else (right, left)          # §2
    episode = engine.play_hand(s_i, seats[0].policy, seats[1].policy)  # engine/surface.md §10

One call per hand, so a cell costs its hand count and not twice it, and **two cells are never interleaved**: nothing
threads and concurrency is no cost fix, because one global `random` stream deals every hand (`league.md` §2, ASM-2).

## 2. Seats alternate, and the split says so

Seat 0 holds the button and posts the small blind in every hand (`engine/surface.md` §4), so alternating which member
is handed over as seat 0 alternates the button: `left` holds it `ceil(hands/2)` times and `right` `floor(hands/2)`, and
one member holding it throughout would be a positional artefact and not a measurement (D-16).

Each direction reports its own split as `seat_split`, a two-key record of the hands **that member** played in engine
seat 0 (the button) and engine seat 1 (the big blind), summing to `hands` and keyed by the engine's seat order, not
`button`/`big blind`: a reader looking for a seat-named key must find **two** counts (`features/surface.md` §5, §8):

    "seat_split": {"seat 0": <hands this member was seat 0>, "seat 1": <hands it was seat 1>}

## 3. The seeds — five derivations, and no stream

Four are `hashlib.sha256` digests of a fixed payload — the idiom `docs/L3/agents/rule.md` §4 uses for a keyed draw —
and the fifth is one modulo, so one seed and one position give one result on any host, whatever was played before:

    def _seed(tag, *parts):                    # the tag and the parts joined by \x1f, UTF-8, none trailing
        payload = tag + b"\x1f" + b"\x1f".join(str(p).encode("utf-8") for p in parts)
        return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % (2 ** 31)

| Function | Tag | Parts | What it seeds |
|---|---|---|---|
| `_hand_seed(seed, index)` | `b"pypoker-evaluation/hand/v1"` | `(seed, index)` | one hand of a cell (§1) |
| `_cell_seed(table_seed, i, j)` | `b"pypoker-evaluation/cell/v1"` | `(table_seed, i, j)` | one cell's own seed (`matrix.md` §3) |
| `_member_seed(table_seed, position)` | `b"pypoker-evaluation/member/v1"` | `(table_seed, position)` | one of the three **baselines**' policies, and nothing else (`matrix.md` §4) |
| `_bootstrap_seed(table_seed)` | `b"pypoker-evaluation/bootstrap/v1"` | `(table_seed,)` | the rating's bootstrap (`rating.md` §4) |
| `_draw_index(seed, n)` | — | `(seed,)` | the opponent draw, `seed % n` (`pool.md` §7) — arithmetic, not a digest |

The digest-derived seeds are integers in `[0, 2**31)`; `_draw_index` is the exception — `seed % n`, the seed's position in
the membership's order, Python's modulo — and each is a plain `int`, recorded wherever it is used as a `seed` (`records.md`
§9, §10). **A checkpoint's policy seed is derived here in no way at all**: its container records it (§5.1, `records.md` §7).

## 4. What a hand was, and what the two directions are

From the episode record's `payoffs` — one number per seat, summing to zero (`records.md` §5, `engine/surface.md` §9) —
the cell reads `d0 = payoffs[0]` and `d1 = payoffs[1]`, and each member's delta is its own seat's number:

- a **win** is a hand whose delta for the member is **positive**, a **loss** where it is **negative**, a **tie** where
  it is **zero** (`protocol.md` §2, ASM-6 — short stacks make ties common, so a win rate alone would hide them);
- `mean_chip_delta` is `sum(deltas) / hands` as a plain `float` — chips **per hand**, so two cells of different hand
  counts are comparable, and the record carries no total;
- `directions` holds two entries **position-aligned with `members`**: entry 0 is `left`'s side, entry 1 is `right`'s. So a
  tied hand is a tie for both, one direction's wins are the other's losses, and the two means are exact negations, because
  `d0 + d1 == 0` for every hand and both are divided by the same `hands` (ASM-12, `league.md` §2, FAM-7.4).

A cell carries `records.md` §9's five required keys — `members`, `hands`, `directions`, `params`, `seed` — plus
`unlabelled`, this module's own: the ids whose `params` is an **unmeasured** `0` (`surface.md` §2, ASM-10). A direction
carries `wins`, `ties`, `losses`, `mean_chip_delta` and `seat_split` (§2), nothing else, and counts summing to `hands`.

## 5. The sides: a member record, a baseline name, or a policy

`match` accepts "two policies or two member records — a `records.md` §7 version record, or one of the three baseline
names" (`surface.md` §9). `_side(value, seed)` resolves one side to `(id, policy, params, unlabelled)`:

| `value` | id | policy | `params` | `unlabelled` |
|---|---|---|---|---|
| one of `random`, `always-call`, `oracle` | the name itself | `agents.build_baseline(name, seed)` | `0` | `False` |
| a `records.md` §7 version record (a mapping with `id`) | `record["id"]` | `_member_policy(record)` | `agents.param_count` of the restored learner | `False` |
| a `_MemberPolicy` this module built | its `member_id` | the policy itself | its `params` | `False` |
| any other callable | `policy-1`, `policy-2` in argument order | the callable, as given | `0` | `True` |
| anything else | — | refused, `MemberInvalid` | — | — |

A baseline named in a call is built **at that call's seed**, so one cell is reproduced from its seed alone. A version is
built by `_member_policy(record)` at the **seed its checkpoint records**, read from the container (§5.1) — the only seed
at which a member decides as its learner did (`agents/surface.md` §10, `protocol.md` §5, `surface.md` §12) — and a
record whose own `seed` disagrees is **not** refused: the container decides, and over-refusal is a defect (`errors.md` §5).

    def _checkpoint_policy(member_id, path):
        seed, names    = _checkpoint_facts(path)      # §5.1 — the recorded seed and the name candidates
        name, encoder  = _built_encoder(names, path)  # the first features.build_encoder accepts, or UnknownEncoding
        learner        = agents.load(None, path)      # agents' own refusal, propagated unchanged
        return _MemberPolicy(member_id = member_id, params = agents.param_count(learner),
                             policy = agents.as_policy(learner, encoder, seed))

`policy_from(path)` is that builder with a **bare-artefact** id — `"ckpt-" + sha256(path).hexdigest()[:12]`, so two
cells naming one checkpoint name one member — reading the same two facts from the same file.

### 5.1 The two facts a checkpoint records, and the reader that finds them

`surface.md` §12 makes the checkpoint's own container the source of the seed and of the encoding name; this module reads
**exactly those two facts and nothing else** — not the learner, its parameters, its rule or its format version, which are
`agents.load`'s alone (`agents/surface.md` §9–§10, ASM-20) — and it never substitutes a seed, a path digest included (§3).

The container was established **empirically** — a learner built through the declared entry points, saved, and the file
inspected, never `agents`' source — and it is a plain **zip** (`PK\x03\x04`, stored) of `metadata.json` then
`parameters.npy`, a bare `.npy` carrying neither fact. `metadata.json` records the seed at `"seed"` (a JSON `int`) and the
encoding name at `"representation"` → `"encoding"` (a JSON `str`), unconditionally, since `build_learner` refuses a spec
without `seed` and `architecture`; it follows the kind.

The reader tolerates names it did not observe, because the container is `agents`' own (§12): it opens the path with
`zipfile.ZipFile` (a path that is not a readable zip is `CheckpointUnreadable`, §6), takes **every** member whose basename
ends `.json` in `namelist()` order, and walks each decoded value depth-first in document order to a depth of 8. A key is
matched by its **normalized form** — lowercased, every character outside `[a-z0-9]` removed — first exactly (`seed`,
`encoding`), then by suffix (`learner_seed`, `checkpointseed`); its value must be the form we read: an `int` that is not a
`bool` for the seed, a `str` for the name. **The name is checked by building it**: the candidates the walk collects are
offered to `features.build_encoder` in order and the first it accepts is the encoder — the granted arrow, so no catalogue
is read (`module-map.md` §2) — and a name it refuses is this module's own `UnknownEncoding` (§6). First match wins, so one
checkpoint yields one pair and a fact the walk finds nowhere is `CheckpointRecordMissing`, naming the fact and the path
(§6). That is what lets `policy_from` answer what `agents.act` answers at the learner's own seed — `protocol.md` §5's
loss-free decision boundary, from a bare path (FAM-12.3).

## 6. Refusals

| Class | Raised when | Named in the message |
|---|---|---|
| `MemberInvalid` | a side is neither a callable nor a §7 record nor a baseline name; a record carries no `id` | the value and the three contracts |
| `MemberUnloadable` | a §7 record carries no `path`, or its `path` names no readable file | the member and the path |
| `InvalidHandCount` | `hands` is not a positive integer, or is a `bool` | the count |
| `InvalidSeed` | `seed` is not an integer (a `bool` included) | the seed |
| `SameMemberPair` | the two sides carry one id — a cell pairs two **distinct** members | the id |
| `CheckpointUnreadable` | `policy_from`'s path names no readable file, or no readable zip | the path |
| `CheckpointRecordMissing` | the container records no seed or no encoding name, **or records it in a form this module does not read** | the fact and the path |
| `UnknownEncoding` | the recorded encoding name `features.build_encoder` refuses, or `agents.as_policy` refuses the encoder that name builds | the path and the name |

An illegal descriptor from either policy is `engine`'s refusal, never caught or repaired here (D-2); the one catch this
module declares is the encoder's: `features.build_encoder`'s and `agents.as_policy`'s refusals, both re-raised as
`UnknownEncoding` (§5.1). Order: path, facts, name, load; `errors.md` §4 has the strings.

## 7. Determinism

One pair, one hand count and one seed give one cell **whatever was played before it**, because every hand's seed is a
function of the cell's seed and the hand's index alone (§3) and a policy's answer is a function of the decision
(`agents/surface.md` §1); a different seed deals different hands. `match` seeds no stream — the only seeding is
`engine.new_hand`, inside `engine.play_hand` (`protocol.md` §4) — so two runs of one cell are equal value for value: FAM-7.7.

## 8. What is deliberately free

- the directions' container, whether a direction is one mapping per member or keyed by member, a `_MemberPolicy`'s repr,
  and whether `_checkpoint_facts` reads a container per member or per table (§5.1) — only that no fact is guessed.
