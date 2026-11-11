# training — the one decision stream a run retains

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-10 · **Rev 1** documents the exploration-off pass `records.md` §15 requires of every run — its sample, its block, its two bounds, what reproduces it, and the `tie` flag this module cannot observe (`sizing.md` §4, §7, ASM-38, D-28, D-29); **Rev 2** makes the sample the seating `episode._hand` deals and the record bound the run's **own shape's** — `greedy_decisions(shape)`, 1,000 × that shape's history capacity, so 24,000 at the default shape and 66,000 and 98,000 on the uncapped ones (`seats.md` §4–§5, `shapes.md` §8, `records.md` §15, ASM-38, ASM-42, ASM-43, D-33)
- **Owner:** `src/training/greedy.py` — the pass and the sample it replays (§1), `records.md` §15's block key by key and the decision record (§2), why nothing else is retained (§3), the two bounds and the two refusals (§4), what reproduces the block (§5), the `tie` limitation and the `ADJUDICATION` it returns to L1 (§6), what is left to L4 and which private names are contract (§7)
- **Ceiling:** 150 lines. At the ceiling, split by owner — never append
- **Read with:** `loop.md` §1 steps 1 and 8, §2, §3, `episode.md` §1–§3, `reward.md` §4, `seeds.md` §2, `errors.md` §2, §4, `docs/L2/training/surface.md` §4, `records.md` §5, §12, §15, `sizing.md` §4, §7, `shapes.md` §8, `docs/L3/agents/rule.md` §4–§5

## 1. The pass, and the sample it replays

A run keeps one decision stream and it is the pass. The loop consumes a hand's batch and discards it (§3), so after a variant's training at a seed ends the run plays that variant's **greedy pass** — at the run's own seed, on the run's own shape, against the same frozen pool — and records it under the run record's `greedy` block (`sizing.md` §4, `records.md` §15, ASM-38, D-29):

    _pass(pool, shape, seed, budget, policy, where) -> {mode, seed, hands, net_chips, decisions}

`_pass` returns those five keys and no sixth, one block per variant per seed, keyed in the record exactly as `curves` is (`record.md` §1, `docs/L2/training/surface.md` §4).

**The sample is the run's own, and the hand is `episode._hand`'s.** Hand *i* of the pass is the hand training played at hand *i*: `episode._hand(pool, shape, seed, i, policy)` derives the deal seed and the opponent draw seed from `(seed, i)`, takes the learner's seat as `_seat(i, shape)` — `i mod seats`, over the seat count `engine.game_config` declares — and fills every other seat with the hand's opponents (`episode.md` §1, `seeds.md` §2, `seats.md` §4, ASM-2, ASM-43). Because the loop and the pass call that one function, the pass's hand count **is** the run's budget, its seat split is the run's, and its opponent membership is the pool's (`sizing.md` §4, `ladder.md` §6): a live-budget run yields a 1,000-hand pass, a ten-hand battery run a ten-hand pass, and the hand count, seat split and opponent membership a record states are the ones the pass replayed (`evaluation/pool.md` §4, ASM-16).

**Both sides play the run's shape, and its seating is the shape's.** On a two-seat shape the hand is `engine.play_hand(hand_seed, seat0, seat1, shape=shape)`, the two positional policies swapped so the learner holds `_seat(i, shape)`; on a shape with more seats it is `engine.play_hand(hand_seed, seats=(...), shape=shape)`, the learner's policy inserted at that seat and `seats − 1` distinct members drawn in one `evaluation.opponent(pool, draw_seed, seats - 1)` call (`e2e-surface.md` §3.1, §3.4, `seats.md` §4, ASM-43). Either way the learner's six-index decisions are made and applied in the run's own vocabulary and every opponent meets them on the same game — never on the engine's default — so a six-seat run's block is the same sample training played, at six seats and 600 chips in play (`engine/surface.md` §10, `shapes.md` §2, §8, D-29, D-33).

**The mode is the policy's, and it is `off`.** `MODE = "off"` is the one mode a retained decision carries: the decision is `agents.as_policy`'s policy at `exploration="off"` — the masked maximum and `rule.md` §5's tie-break alone, with **no generator drawn from** — so two passes over one model decide identically and the block is a function of the model, the hands and the pool and not of a seed (`docs/L3/agents/rule.md` §4, §7, D-19). A block whose `mode` is anything else, or a census computed over training decisions, is refused by name rather than read (`sizing.md` §7).

**It writes nothing, and it reads the model the record names.** The pass is played after `agents.save` of the pair's final model (`loop.md` §1 step 8), so the block is reproducible from the checkpoint the record's `checkpoints` block points at, and the pass itself adds no artefact, no path and no file (`checkpoints.md` §3, `records.md` §15).

## 2. The block, key by key, and the decision record

`records.md` §15's five block keys, and where each number comes from:

| Key | Content |
|---|---|
| `mode` | `off`, `MODE`'s one value — the policy's mode and never the schedule's (`sizing.md` §4, D-28) |
| `seed` | the run seed the pass was played at, which is the seed the record's `seeds` list carries (`records.md` §15, ASM-2) |
| `hands` | the hands played: the run's budget, and at most 2,000 (§4) |
| `net_chips` | one net chip delta per hand for the learner's seat, so the sample's price can be recomputed and not only quoted (`records.md` §5, §15, ASM-23) |
| `decisions` | the ordered decision records of the learner's own seat, at most `declarations.greedy_decisions(shape)` — 1,000 × the run's shape's history capacity: 24,000 at the default shape, 66,000 and 98,000 on the uncapped ones (§4, `shapes.md` §8, ASM-42) |

`_net_chips(payoffs, seat)` reads the hand's zero-sum outcome at the learner's seat, accepts the seat index the readout keys it by, and recomputes nothing: the pass reports the sample's price, averages nothing and thresholds nothing (`records.md` §5, §15, ASM-23, D-24). A six-seat hand's `payoffs` hold one net delta per seat and the block records the learner's own, so `net_chips` is the seat's price and not the hand's (`seats.md` §3, ASM-43).

`_decision_record(decision, shape)` returns §15's seven keys and no eighth, read off the episode decision the hand resolved (`records.md` §5, §15):

| Key | Content |
|---|---|
| `index`, `descriptor` | the chosen index, and the descriptor it decodes to through `features.decode_action(index, shape=shape)` — **the run's shape's** declared order, and never the default shape's three (`features/surface.md` §9, `sizing.md` §3) |
| `amount`, `minimum`, `maximum` | the raise-to the engine resolved and the two bounds it was resolved between, all three `None` on a decision where no raise was legal (`sizing.md` §2, `records.md` §5) |
| `legal` | the decision's legal index set through `features.legal_indices`, so a census re-derives no mask (`sizing.md` §7, `features/surface.md` §8) |
| `tie` | `false` on every decision — the one key the exploration-off surface does not report, and §6 says exactly what that is worth (`sizing.md` §3, V-F13) |

The index is the applied descriptor's position in that decision's own `legal` list (`episode._index`, `features/surface.md` §8), so the ordered log and the mask beside it are one vocabulary's: every retained index is a member of its own `legal` set and one of the shape's declared indices (`sizing.md` §3).

## 3. Why nothing else is retained (D-28)

A log of the behaviour policy would be a log of the **exploration schedule**: at the live budget almost the whole sample sits on the ε ramp, so every action class clears a floor by construction and a census of it cannot tell a learner that found a band from one that learned nothing — the defect D-28 records as fatal (`sizing.md` §4, `docs/L3/agents/rule.md` §6, ASM-38). So training decisions are not retained: the loop keeps its batch aggregate, the hand's `td_error`, and the curve, and nothing per decision (`curves.md` §3, D-28).

The record tree therefore holds an ordered decision log in **exactly one** place, and it is `greedy` (`records.md` §12, §15, ASM-38). A second log anywhere in the record is the defect D-28 named, not an addition to it.

**What a run retains instead is a function of what it already fixed.** The block is read off the finished model, over the run's own hands and the frozen pool, with no generator drawn from — so it inherits the tuple's determinism instead of adding a stream of its own, and §5 states that guarantee together with the one caveat it carries.

## 4. The two bounds and the two refusals

The hand bound is `declarations.GREEDY_HANDS = 2000` hands per variant per seed, and the record bound is **the run's own shape's**: `declarations.GREEDY_DECISIONS_PER_SLOT = 1000` records per slot of that shape's history capacity, read through `declarations.greedy_decisions(shape) = 1000 × declarations.shape_history(shape)` — 24,000 at the default shape, 66,000 and 98,000 on the uncapped ones (`sizing.md` §4, `records.md` §15, `shapes.md` §8, ASM-38, ASM-42). `greedy.HANDS_BOUND` reads the hand bound and `greedy.DECISIONS_BOUND` names the **default shape's** 24,000, so a reader who holds no shape has the shipped number in one place; the check reads `greedy_decisions`, so the check and the refusal cannot drift apart on any shape (`declarations.py`, `shapes.md` §8, D-33).

- **`_check_hands(hands, where)` — the hand bound, refused before the run trains.** The pass's hand count is the budget, so it is known up front: `loop.run` calls this at §1 step 1, before the pool is built and before the first hand is dealt, and nothing is written for a run that could not produce its own record (`loop.md` §1 step 1, `sizing.md` §4, `e2e-surface.md` §2, ASM-38).
- **`_check_decisions(recorded, where, shape=None)` — the record bound, refused as the pass accumulates.** The bound is read per call from `declarations.greedy_decisions(shape)`, so a pass on a shape with a wider history block is bounded by that block and not by the default shape's: a hand holds a handful of decisions, the shape's capacity bounds how many the learner can have made before its block overflowed, and `records.md` §15 makes the pass's bound 1,000 × that capacity — never guessed from the hand count (`sizing.md` §4, `records.md` §15, `shapes.md` §8, ASM-38, ASM-42). `shape` omitted is the default shape, which is the bound `tests/training/` drives.

Both raise `errors.GreedyPassRefused` and neither clamps anything: a truncated log silently reports a **different sample**, so the refusal is the record's protection and not an inconvenience (`records.md` §15, `sizing.md` §4, `errors.md` §2). The hand refusal names the run's budget and the 2,000-hand bound; the record refusal names **the count the pass would reach, the bound, the shape and that shape's history capacity**, so a reader learns which shape's bound was crossed (`errors.md` §4, `declarations.greedy_decisions`, ASM-42). **A pass of exactly a bound is inside it**: 2,000 hands and 24,000 records are legal at the default shape, and 2,001 hands, 24,001 records, 66,001 on `no-limit-100` and 98,001 on `six-seat-no-limit-100` are refused (`shapes.md` §8, ASM-42, D-33).

**The consequence at the shipped budget is a refusal, and it is the design's own.** Because the pass's hand count *is* the run's budget, a **200,000-hand** run — the shipped checkpoint budget of `ladder.md` §6 — is refused at step 1 with `GreedyPassRefused` naming 200,000 and 2,000: no run at that budget can produce a record `sizing.md` §4 allows this module to write, so it is refused before it spends itself training for one. Lifting the bound, or replaying a smaller sample than the run trained, is a change to `sizing.md` §4's bound and to `declarations.GREEDY_HANDS` — L1's to make and L0's to authorise, and never a caller's, a truncation here, or a silent sample mismatch (D-13, `module-map.md` §2, ASM-38).

## 5. What reproduces the block

Two runs of one `(configuration, seed set, budget, pool membership)` **in one process** produce an identical `greedy` block — the same seed, hands, chip deltas and ordered decisions — because the pass's hands, seats and opponents are derivations of `(seed, i)` and of the run's shape, because it reads the finished model whose training that tuple fixed, and because `exploration="off"` draws from no generator (`seeds.md` §2, `episode.md` §1, `docs/L3/agents/rule.md` §4, §7, ASM-2, ASM-38). The seating is the shape's, so the rotation is too: a six-seat block rotates the learner through six seats in the order `_seat` names, and the seat each hand was played in is a function of the index and of the shape and of nothing else (`seats.md` §4, ASM-43, D-33). The record's `timings` stay the one field two such runs differ in (`docs/L2/training/surface.md` §4, `loop.md` §7).

**The guarantee is exactly the one the record already has, and no wider.** The whole training path is hash-order sensitive across processes — a pre-existing property `/tmp/pypoker-baseline/verify.py`'s `UNSTABLE_NUMERICS` records — so this document promises one block per tuple **within a process**, which is the guarantee `docs/L2/training/surface.md` §4 states, and promises nothing about two processes (`loop.md` §7).

**And the stream a run leaves is where it was.** The pass replays the sample rather than extending it: its last hand is dealt at the seed training's last hand was dealt at, and `engine.play_hand` seeds the global `random` stream from that deal seed, so a run that passes leaves the global stream exactly where its training left it and a later run in the same process is not perturbed by it (`seeds.md` §2, `engine/surface.md` §4, ASM-2).

## 6. The `tie` key — the one thing this module cannot observe

`records.md` §15 makes `tie` "whether the tie-break, and not a strict maximum, chose the index" (`sizing.md` §3, validity V-F13). **No granted surface reports that flag for an exploration-off decision**, and this is a named limitation rather than a reading of the sample:

- `agents.as_policy` returns a **policy** — a callable from `(readout, legal)` to one descriptor and nothing else — and the flag its rule computes is discarded before the descriptor is returned;
- `evaluation.policy_from`'s policy is that same callable with that same discard, so the other exploration-off surface does not report it either;
- `agents.act`'s decision record, the one record in the tree that carries the flag, carries it on the **schedule** arm, whose decision is not this pass's (`e2e-surface.md` §3.3–§3.4, `docs/L3/agents/rule.md` §5, `agents/surface.md` §6, D-19).

So `_decision_record` writes `tie: False` for every decision, and the block claims exactly what that is worth: **no tie-resolved decision is reported**. That is not the claim that none occurred — the tie-break decides wherever two masked values stand within `rule.md` §5's `1e-9` relative tolerance of the masked maximum — so a reader must not treat the block's `tie` column as evidence of a strict maximum, and a census must not divide by it.

**The census's tie-excluded conjunct is therefore not computable from this block.** `sizing.md` §7's conjunct 7 re-runs conjuncts 3–6 with `T(s)`, the seed's tie-resolved decision count, excluded; with no reported flag `T(s)` reads as 0 from this artefact, which makes the conjunct either vacuous or a claim about a number this module never measured. That gap is an `ADJUDICATION` and it is returned to L1, on `modules.md` §3 / D-13's route: this module's granted interface cannot meet a claim its record makes, which is an interface defect answered above this layer and never repaired here by inventing a field, a seventh entry point or an inference (D-12, D-13, `module-map.md` §2).

**What would close it, and whose it is.** The flag must reach the policy protocol: `agents.as_policy` — and `evaluation.policy_from` with it — returning the tie flag beside the descriptor, one word wider and no new name in this module (`e2e-surface.md` §3.3–§3.4, `agents/surface.md` §6). Until that lands, a census that excludes tie-resolved decisions must read them from somewhere other than this block, and `sizing.md` §7's conjunct 7 is L1's to hold, re-price or withhold.

## 7. What is left to L4

Whether the pass accumulates its decision records in a list or a generator the block copies, how `where` is spelled, whether the two bounds are read at the call or once at import, and every private name other than `MODE`, `HANDS_BOUND`, `DECISIONS_BOUND`, `_check_hands`, `_check_decisions`, `_pass`, `_decision_record` and `_net_chips`, whose spellings and signatures are contract for `tests/training/` (`README.md` §4) — `_check_decisions`' `shape` argument among them.

Not L4's: the sample — the run's own hands, its shape's rotation and its opponents, seated by `episode._hand` — the mode being `off` and the policy's, the five block keys and the seven decision keys, `tie` being `False` with §6's statement of what that means, the two bounds with the record bound the run's own shape's and their two refusals with their counts, the pass writing nothing and coming after the save, the refusal of a budget above 2,000 before a hand is dealt, and the reproduction claim of §5 with its caveat (`guardrails.md` G21–G23, `seats.md` §4–§5, `shapes.md` §8, ASM-38, ASM-42, ASM-43, D-28, D-33).
