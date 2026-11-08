# evaluation — the scheduler, one cell at a time

- **Owner:** `match` and `policy_from` — one cell and the sides it plays: seat alternation, the **seed derivations** (§3),
  win/tie/loss from net chips, the seat split, the zero-sum directions, how a side becomes a policy and **the rule it
  carries** (§5), the **two facts a checkpoint records** (§5.1), and every refusal (`surface.md` §9, §12, `league.md`, D-19)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `pool.md` §7, `families.md` §6, `matrix.md` §3–§4, `rating.md` §4, `errors.md` §2–§4

## 1. The cell

A cell is one unordered pair of members, played at one hand count and reported in both directions (`league.md` §2,
`e2e-surface.md` §2). `match(left, right, hands, seed)` returns one `records.md` §9 record, a loop pass per hand:

    s_i     = seeds._hand_seed(seed, i)                              # §3 — one pass per hand, i < hands
    seats   = (left, right) if i is even else (right, left)          # §2
    episode = engine.play_hand(s_i, seats[0].policy, seats[1].policy)  # engine/surface.md §10

One call per hand, so a cell costs its hand count and not twice it, and **two cells are never interleaved**: concurrency is
no cost fix, because one global `random` stream deals every hand (`league.md` §2, ASM-2).

## 2. Seats alternate, and the split says so

Seat 0 holds the button and posts the small blind in every hand (`engine/surface.md` §4), so alternating which member is
handed over as seat 0 alternates the button: `left` holds it `ceil(hands/2)` times and `right` `floor(hands/2)`, and one
member holding it throughout would be a positional artefact and not a measurement (D-16). Each direction reports its own
`seat_split` — the hands **that member** played in engine seat 0 (the button) and seat 1 (the big blind), summing to
`hands`, keyed by the engine's seat order and never `button`/`big blind` (`features/surface.md` §5).

## 3. The seeds — five derivations, and no stream

Four are `hashlib.sha256` digests of a fixed payload — the idiom `docs/L3/agents/rule.md` §4 uses for a keyed draw — and
the fifth is one modulo, so one seed and one position give one result on any host, whatever was played before:

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

**A checkpoint's policy seed is derived here in no way at all**: its container records it (§5.1, `records.md` §7), and no
rule moves any of the five.

## 4. What a hand was, and what the two directions are

From the episode record's `payoffs` — one number per seat, summing to zero (`records.md` §5, `engine/surface.md` §9) — the
cell reads `d0 = payoffs[0]` and `d1 = payoffs[1]`, and each member's delta is its own seat's number:

- a **win** is a hand whose delta for the member is **positive**, a **loss** where **negative**, a **tie** where **zero**
  (`protocol.md` §2, ASM-6 — short stacks make ties common, so a win rate alone would hide them);
- `mean_chip_delta` is `sum(deltas) / hands` as a plain `float` — chips **per hand**, so two cells of different hand counts
  are comparable, and the record carries no total;
- `directions` holds two entries **position-aligned with `members`**, entry 0 `left`'s side, so a tied hand is a tie for
  both and the two means are exact negations: `d0 + d1 == 0` for every hand and both divide by the same `hands` (ASM-12,
  `league.md` §2, FAM-7.4).

A cell carries `records.md` §9's six required keys — `members`, `hands`, `directions`, `params`, `rules`, `seed` — plus
`unlabelled`, this module's own: the ids whose `params` is an **unmeasured** `0` (`surface.md` §2, ASM-10). `rules` maps
each member's **id** to the rule its policy carries — `None` for a baseline and for an opaque policy that carries none —
so a cell says which two estimators met (`records.md` §9, §5, D-19). A direction carries `wins`, `ties`, `losses`,
`mean_chip_delta` and `seat_split` (§2), nothing else, and counts summing to `hands`.

## 5. The sides: a member record, a baseline name, or a policy

`match` accepts "two policies or two member records — a `records.md` §7 version record, or one of the three baseline
names" (`surface.md` §9). `_side(value, label, entry, seed=None, position=1)` resolves one side to
`(id, policy, params, unlabelled, rule)`:

| `value` | id | policy | `params` | `unlabelled` | `rule` |
|---|---|---|---|---|---|
| one of `random`, `always-call`, `oracle` | the name itself | `agents.build_baseline(name, seed)` | `0` | `False` | `None` — a fixed rule, not an estimator |
| a `records.md` §7 version record (a mapping with `id`) | `record["id"]` | `_member_policy(record)` | `agents.param_count` of the restored learner | `False` | the rule the built policy carries |
| a `_MemberPolicy` this module built | its `member_id` | the policy itself | its `params` | its `unlabelled` | its `learning_rule` |
| any other callable | `policy-1`, `policy-2` in argument order | the callable, as given | `0` | `True` | its own `learning_rule` if it declares one, else `None` |
| anything else | — | refused, `MemberInvalid` | — | — | — |

**Who carries which rule**, the three cases the record turns on (`e2e-surface.md` §2, `rules.md` §7, D-19): a **baseline**
carries none, because it is a fixed rule and not a trained estimator, so `rules` names it `None`; a **version** carries
the rule its checkpoint records, reported by the policy `agents.as_policy` built (§5.1), and a record declaring a `rule` is
held to it — a disagreement is `RuleMismatch` naming the member and both, after the load and before a hand
(`families.md` §6, ASM-20); and an **opaque callable** carries whatever its own `learning_rule` says, `None` for a plain
function (ASM-10).

A baseline named in a call is built **at that call's seed**, so one cell is reproduced from its seed alone. A version is
built by `_member_policy(record)` at the **seed its checkpoint records** (§5.1) — the only seed at which it decides as its
learner did (`protocol.md` §5) — and a record whose own `seed` disagrees is **not** refused: the container decides
(`errors.md` §5).

    def _checkpoint_policy(member_id, path):
        seed, names    = _checkpoint_facts(path)      # §5.1 — the recorded seed and the name candidates
        name, encoder  = _built_encoder(names, path)  # the first features.build_encoder accepts, or UnknownEncoding
        learner        = agents.load(None, path)      # agents' own refusal, propagated unchanged
        policy         = agents.as_policy(learner, encoder, seed)
        return _MemberPolicy(member_id = member_id, params = agents.param_count(learner), policy = policy,
                             learning_rule = getattr(policy, "learning_rule", None))      # §5.1

`policy_from(path)` is that builder with a bare-artefact id, `"ckpt-" + sha256(path).hexdigest()[:12]`.

### 5.1 The two facts a checkpoint records, and the reader that finds them

`surface.md` §12 makes the checkpoint's own container the source of the seed and of the encoding name; this module reads
**exactly those two and nothing else** — not the learner, its parameters, its rule or its format version, which are
`agents.load`'s alone (`agents/surface.md` §9–§10, ASM-20) — and it never substitutes a seed, a path digest included
(§3). **The rule is not a third fact read here**: it is the `learning_rule` attribute of the policy `agents.as_policy`
built, which is the rule the file records, so a version-1 container legitimately reads as `masked-q-learning`
(`rules.md` §6, ASM-20, D-19, G20).

The container was established **empirically** — a learner built through the declared entry points, saved, and the file
inspected, never `agents`' source — and it is a plain **zip** of `metadata.json` then `parameters.npy`, a bare `.npy`
carrying neither fact. `metadata.json` records the seed at `"seed"` and the encoding name at `"representation"` →
`"encoding"`. The reader tolerates names it did not observe: it walks every `.json` member depth-first to depth 8, matching
a key by its **normalized form** (lowercased, `[a-z0-9]` only) first exactly (`seed`, `encoding`), then by suffix
(`learner_seed`). **The name is checked by building it**: the candidates go to `features.build_encoder` in order and the
first it accepts is the encoder — the granted arrow, so no catalogue is read (`module-map.md` §2) — and a name it refuses
is `UnknownEncoding` (§6); a fact the walk finds nowhere is `CheckpointRecordMissing` (§6).

## 6. Refusals

| Class | Raised when | Named in the message |
|---|---|---|
| `MemberInvalid` | a side is neither a callable nor a §7 record nor a baseline name; a record carries no `id` | the value and the three contracts |
| `MemberUnloadable` | a §7 record carries no `path`, or its `path` names no readable file | the member and the path |
| `UnknownRule` | a §7 record's declared `rule` is not one the catalogue carries | the member, the name and the catalogue (`families.md` §6) |
| `RuleMismatch` | a §7 record's declared `rule` disagrees with the rule its policy carries — after the load, before a hand | the member, both values and the path |
| `InvalidHandCount` | `hands` is not a positive integer, or is a `bool` | the count |
| `InvalidSeed` | `seed` is not an integer (a `bool` included) | the seed |
| `SameMemberPair` | the two sides carry one id — a cell pairs two **distinct** members | the id |
| `CheckpointUnreadable` | `policy_from`'s path names no readable file, or no readable zip | the path |
| `CheckpointRecordMissing` | the container records no seed or no encoding name, **or records it in a form this module does not read** | the fact and the path |
| `UnknownEncoding` | the recorded encoding name `features.build_encoder` refuses, or `agents.as_policy` refuses the encoder that name builds | the path and the name |

An illegal descriptor from either policy is `engine`'s refusal, never caught or repaired here (D-2), and the one catch this
module declares is the encoder's, re-raised as `UnknownEncoding` (§5.1). Only `RuleMismatch` cannot precede its load.

## 7. Determinism

One pair, one hand count and one seed give one cell **whatever was played before it**, because every hand's seed is a
function of the cell's seed and the hand's index alone (§3), and `match` seeds no stream — the only seeding is
`engine.new_hand`, inside `engine.play_hand` (`protocol.md` §4) — so two runs of one cell are equal value for value,
`rules` included (FAM-7.7), and `policy_from` answers what `agents.act` answers at the learner's own seed (FAM-12.3).

## 8. What is deliberately free

- the directions' container, a `_MemberPolicy`'s repr, a cell's `rules` mapping order, and whether `_checkpoint_facts`
  reads a container per member or per table (§5.1) — only that no fact is guessed.
