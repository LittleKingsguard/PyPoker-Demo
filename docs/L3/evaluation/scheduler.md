# evaluation — the scheduler, one cell at a time

- **Owner:** `match` and `policy_from` — one cell, the one **shape** it is played on and the sides it plays: seat
  alternation, the **seed derivations** (§3), win/tie/loss from net chips, the seat split, the zero-sum directions, how a
  side becomes a policy, the **seven** facts a side carries (§5), the **three facts a checkpoint records** (§5.1), and
  every refusal (§6) (`surface.md` §9, §12, `league.md`, `shape.md` §3–§5, D-19, D-20, D-29)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Rev 6:** D-29's second shape — a cell is played on the one shape its two sides name (§1), a side carries seven facts (§5), a checkpoint records three (§5.1), and `policy_from` takes the mode `off` (§6–§7, `shape.md` §3–§5) — and that one shape is the **deal's**, handed to `play_hand` (§1)
- **Read with:** `shape.md` §2–§5, `pool.md` §7, `families.md` §6, `utility.md` §1–§4, `matrix.md` §3–§4, `rating.md` §4,
  `errors.md` §2–§4

## 1. The cell, and the one shape it is played on

A cell is one unordered pair of members, played at one hand count and on **one shape**, reported in both directions (`league.md` §2, `e2e-surface.md` §2). `match(left, right, hands, seed)` returns one `records.md` §9 record, a loop pass per hand, and its **signature is unchanged: there is no shape argument** — the cell is played on the one shape its two sides name, which `_play_cell` hands `engine.play_hand` as its fourth argument, `shape=game` (§5, `surface.md` §9, `shape.md` §4):

    s_i     = seeds._hand_seed(seed, i)                              # §3 — one pass per hand, i < hands
    seats   = (left, right) if i is even else (right, left)          # §2
    episode = engine.play_hand(s_i, seats[0].policy, seats[1].policy, shape=game)  # engine/surface.md §10 — `game` is the cell's (§5)

One call per hand, so a cell costs its hand count and not twice it, and **two cells are never interleaved**: concurrency is no cost fix, because one global `random` stream deals every hand (`league.md` §2, ASM-2). The shape is a fact about **the deal**: every hand of the cell is dealt on the cell's one shape, its fourth argument, so a version member of `no-limit-100` decodes its six-index vocabulary against that shape's legal descriptors and never a fixed-limit deal's three — and since `engine` reads an absent shape as the default, passing the default's own name and passing none deal identically, which is why no default-shape number moved.

## 2. Seats alternate, and the split says so

Seat 0 holds the button and posts the small blind in every hand (`engine/surface.md` §4), so alternating which member is handed seat 0 alternates the button: `left` holds it `ceil(hands/2)` times and `right` `floor(hands/2)`, and one member holding it throughout would be a positional artefact (D-16). Each direction reports its own `seat_split`: that member's hands in seat 0 and seat 1, summing to `hands` and never `button`/`big blind` (`features/surface.md` §5).

## 3. The seeds — five derivations, and no stream

Four are `hashlib.sha256` digests of a fixed payload — the idiom `docs/L3/agents/rule.md` §4 uses for a keyed draw — and the fifth is one modulo, so one seed and one position give one result on any host, whatever was played before:

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

**No shape reaches any of them**: every derivation is a function of the table seed and the pair or the position alone, so a table on the second shape is played from the same seeds as one on the default (`shape.md` §4, `matrix.md` §3). **A checkpoint's policy seed is derived here in no way at all**: its container records it (§5.1, `records.md` §7).

## 4. What a hand was, and what the two directions are

From the episode record's `payoffs` — one number per seat, summing to zero (`records.md` §5, `engine/surface.md` §9) — the
cell reads `d0 = payoffs[0]` and `d1 = payoffs[1]`, and each member's delta is its own seat's number:

- a **win** is a hand whose delta for the member is **positive**, a **loss** where **negative**, a **tie** where **zero** (`protocol.md` §2, ASM-6 — short stacks make ties common, so a win rate alone would hide them);
- `mean_chip_delta` is `sum(deltas) / hands` as a plain `float` — chips **per hand**, so two cells of different hand counts are comparable, and the record carries no total;
- `directions` holds two entries **position-aligned with `members`**, entry 0 `left`'s side, so a tied hand is a tie for both and the two means are exact negations: `d0 + d1 == 0` per hand, both divided by one `hands` (ASM-12, `league.md` §2, FAM-7.4).

A cell carries `records.md` §9's seven required keys — `members`, `hands`, `directions`, `params`, `rules`, `utilities`, `seed` — plus `unlabelled` and **`game`**, this module's own: the one shape the hands were played on, which `records.md` §9 does not require and which a cell of two shape-silent sides carries as the default (`shape.md` §2, §4). `rules` and `utilities` map each member's **id** to the rule and the utility its policy carries, `None` for a baseline or an opaque policy that carries neither, so a cell says which two estimators met and which two objectives (`records.md` §9, `utility.md` §3, D-19, D-20). A direction carries `wins`, `ties`, `losses`, `mean_chip_delta` and `seat_split` (§2).

## 5. The sides: a member record, a baseline name, or a policy

`match` accepts "two policies or two member records — a `records.md` §7 version record, or one of the three baseline names"
(`surface.md` §9). `_side(value, label, entry, seed=None, position=1)` resolves one side to
`(id, policy, params, unlabelled, rule, utility, game)` — **seven** elements, and every reader of a side unpacks seven
(`_play_cell`, `_membership`, `matrix._variant_shape`):

| `value` | id | policy | `params` | `unlabelled` | `rule` | `utility` | `game` |
|---|---|---|---|---|---|---|---|
| one of `random`, `always-call`, `oracle` | the name itself | `agents.build_baseline(name, seed)` | `0` | `False` | `None` — a fixed rule, not an estimator | `None` — a fixed policy, not a trained objective | `None` — a baseline is **shape-silent** (`shape.md` §4) |
| a `records.md` §7 version record (a mapping with `id`) | `record["id"]` | `_member_policy(record)` | `agents.param_count` of the restored learner | `False` | the rule the built policy carries | the utility the built policy carries | the shape the built policy carries, and `record["game"]` is held to it (absent reads as the default) |
| a `_MemberPolicy` this module built | its `member_id` | the policy itself | its `params` | its `unlabelled` | its `learning_rule` | its `utility` | its `game` — the shape its container records (§5.1) |
| any other callable | `policy-1`, `policy-2` in argument order | the callable, as given | `0` | `True` | its own `learning_rule` if it declares one, else `None` | its own `utility` if it declares one, else `None` | `getattr(value, "game", None)` — its own shape if it declares one, else none |
| anything else | — | refused, `MemberInvalid` | — | — | — | — | — |

**Who carries which rule, utility and shape** (`e2e-surface.md` §2, `utilities.md` §7, D-19, D-20, `shape.md` §4): a **baseline** carries none of the three, being a fixed policy and not a trained member, so `rules` and `utilities` name it `None` and its side names no shape; a **version** carries the rule, the utility and the shape its checkpoint records, reported by the policy `agents.as_policy` built (§5.1), and a record declaring any of them is held to it — `RuleMismatch`, `UtilityMismatch` or `ShapeMismatch` naming the member and both values, after the load and before a hand (`utility.md` §4, ASM-20); an **opaque callable** carries whatever its own `learning_rule`, `utility` and `game` say, `None` for a plain function (ASM-10).

**The cell's shape is then fixed, and it is one shape.** A cell between two shape-silent sides — two baselines, two plain functions
— is played on `DEFAULT_SHAPE` with exactly the numbers it had before the shape existed; a baseline opposite a version is played on
that version's shape; and a pair whose two sides name **two shapes** is refused naming both sides and both shapes (`ShapeMismatch`),
because a cell is played on one game (`shape.md` §3, `docs/L1/shapes.md` §6). A baseline named in a call is built **at that call's
seed**; a version is built by `_member_policy(record)` at the **seed its checkpoint records** (§5.1) — the only seed at which it
decides as its learner did (`protocol.md` §5) — and a record whose own `seed` disagrees is **not** refused: the container decides
(`errors.md` §5).

    def _checkpoint_policy(member_id, path, exploration="schedule"):
        seed, encodings, game = _checkpoint_facts(path)         # §5.1 — the three recorded facts
        name, encoder  = _built_encoder(encodings, game, path)  # build_encoder(name, shape=game), or UnknownEncoding
        learner        = agents.load(None, path)                # agents' own refusal, propagated unchanged
        policy         = agents.as_policy(learner, encoder, seed, exploration)   # shape.md §5
        return _MemberPolicy(member_id = member_id, params = agents.param_count(learner), policy = policy,
                             learning_rule = getattr(policy, "learning_rule", None),   # §5.1
                             utility       = getattr(policy, "utility", None),          # §5.1, utility.md §3
                             game          = game)                                     # §5.1, shape.md §4

`policy_from(path, exploration="schedule")` is that builder with a bare-artefact id, `"ckpt-" + sha256(path).hexdigest()[:12]`,
and with the mode it was handed (`shape.md` §5).

### 5.1 The three facts a checkpoint records, and the reader that finds them

`surface.md` §12 makes the checkpoint's own container the source of the seed, the encoding name and **the shape**; this module
reads **exactly those three and nothing else** — not the learner, its parameters, its rule, its utility or its format version,
which are `agents.load`'s alone (`agents/surface.md` §9–§10, ASM-20) — and it never substitutes a seed, a path digest included
(§3). The **rule and the utility** are the attributes of the policy `agents.as_policy` built and are not parsed here; the **shape**
is read by the walk, because a container's shape has no attribute to read it back from.

The container was established **empirically** — a learner built through the declared entry points, saved, and the file
inspected, never `agents`' source — and it is a plain **zip** of `metadata.json` then `parameters.npy`, a bare `.npy` carrying
none of the facts. `metadata.json` records the seed at `"seed"`, the encoding name at `"representation"` → `"encoding"` and, in a
**version-4** container only, the shape at `"game"`. The walk visits every `.json` member depth-first to depth 8 and matches a
key by its **normalized form** (lowercased, `[a-z0-9]` only): exactly (`seed`, `encoding`), then by suffix (`learner_seed`) — while
the **shape** is matched by that form being **exactly `game`** with a string value, never by suffix, so a key that merely ends in
`game` cannot move a member to another shape. **Absent means `DEFAULT_SHAPE`**, which is what keeps the 18 shipped version-1
containers loadable (`docs/L1/shapes.md` §3, §5, `sizing.md` §6), and a recorded shape the catalogue lacks is `UnknownShape`
naming it and `SHAPE_NAMES` (`shape.md` §2). **The name is checked by building it for the recorded shape**: the candidates go to
`features.build_encoder(name, shape=game)` in order and the first it accepts is the encoder — the granted arrow, so no catalogue is
read (`module-map.md` §2) — a name it refuses is `UnknownEncoding`, and a seed or an encoding the walk finds nowhere is
`CheckpointRecordMissing` (§6).

## 6. Refusals

| Class | Raised when | Named in the message |
|---|---|---|
| `InvalidHandCount` | `hands` is not a positive integer, or is a `bool` | the count |
| `InvalidSeed` | `seed` is not an integer (a `bool` included) | the seed |
| `MemberInvalid` | a side is neither a callable nor a §7 record nor a baseline name; a record carries no `id` | the value and the three contracts |
| `MemberUnloadable` | a §7 record carries no `path`, or its `path` names no readable file | the member and the path |
| `UnknownRule`, `UnknownUtility` | a §7 record's declared `rule` or `utility` is not one its catalogue carries | the member, the name and the catalogue (`families.md` §6, `utility.md` §4) |
| `RuleMismatch`, `UtilityMismatch`, `ShapeMismatch` | a §7 record's declared `rule`, `utility` or `game` disagrees with the one its policy carries — after the load, before a hand | the member, both values and the path (`utility.md` §4, `shape.md` §3) |
| `SameMemberPair` | the two sides carry one id — a cell pairs two **distinct** members | the id |
| `ShapeMismatch` | the pair's two sides name **two shapes** — a cell is played on one game | both sides and both shapes (`shape.md` §3) |
| `CheckpointUnreadable` | `policy_from`'s path names no readable file, or no readable zip | the path |
| `CheckpointRecordMissing` | the container records no seed or no encoding name, **or records it in a form this module does not read** | the fact and the path |
| `UnknownEncoding` | the recorded encoding name `features.build_encoder` refuses for the recorded shape, or `agents.as_policy` refuses the encoder it builds | the path, the name and the shape |
| `UnknownShape` | the shape a container records is not one `SHAPE_NAMES` carries | the path, the name and the declared shapes (`shape.md` §2) |
| `UnknownExploration` | `policy_from`'s mode is neither `schedule` nor `off` | the mode and both modes (`shape.md` §5) |

The order is the load's: the cheap checks, then `policy_from`'s **mode** (which has no file and is refused before one is touched),
then the path, then the three recorded facts, then the load, then the record-versus-container disagreements — so a two-shape pair
is refused before a hand is dealt and an uncatalogued mode before a checkpoint is opened. An illegal descriptor from either policy
is `engine`'s refusal, never caught or repaired here (D-2); the one catch this module declares is the encoder's, re-raised as
`UnknownEncoding` (§5.1). Only the three mismatches cannot precede their load.

## 7. Determinism

One pair, one hand count and one seed give one cell **whatever was played before it**, because every hand's seed is a function of
the cell's seed and the index alone (§3) and `match` seeds no stream: `engine.new_hand` is the only seeding (`protocol.md` §4). Two
runs of one cell are therefore equal value for value, `rules`, `utilities` and `game` included (FAM-7.7), and `policy_from` answers
what `agents.act` answers at the learner's seed (FAM-12.3). **The mode changes the decision and not the derivation**: in `off` two
policies at two seeds decide **identically** on one readout and **no draw is taken at all**, so the greedy reading is a function of
the model and not of a seed; in `schedule` the keyed draw is the one `agents.as_policy` already makes (`shape.md` §5,
`docs/L1/sizing.md` §4).

## 8. What is deliberately free

- the directions' container, a `_MemberPolicy`'s repr, a cell's `rules` mapping order, and whether `_checkpoint_facts` reads a container per member or per table (§5.1) — only that no fact is guessed and that a side unpacks seven; and whether a side's `game` is stored resolved (the one shape the cell is played on) or as the declarations it came from, provided the cell's `game` is the resolved shape and a disagreement is `ShapeMismatch` (`shape.md` §3).
