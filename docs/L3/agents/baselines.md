# agents — the six fixed baselines

- **Owner:** the six fixed rules of `protocol.md` §3 (D-6, ASM-4, D-21): `random`'s keyed uniform draw,
  `always-call`'s procedure, `oracle`'s pot-odds inequality at 257 equity samples, the three folders' predicates
  under one legality rule, the `anchor` flag that keeps the rating's scale, and the record `baselines()` returns
- **Ceiling:** 130 lines. At the ceiling, split by owner — never append
- **Read with:** `rule.md` §4, `errors.md` §3, `README.md` §4

## 1. What a baseline is

`random`, `always-call` and `oracle` are D-6's three; `fold-no-pair-or-face`, `fold-no-pair-or-better` and
`fold-large-bet` are D-21's three folders. All six are fixed standards and none learns from a match: each is a
pool member and a matrix column at the same hand count as every league cell (§9, `protocol.md` §3, D-16, D-21).

Four properties hold of all six, and each is a contract rather than a habit:

- **A baseline's state advances nowhere.** Nothing is retained from a hand it played, so its column is the same rule
  at every hand count and at every call order (`surface.md` §1, §12, `learner.md` §5).
- **A baseline has no trainable parameter.** `baselines()` declares `params: 0`, and that declared zero is the count
  a cell records beside every member's (`records.md` §9); `param_count` refuses a baseline (`surface.md` §5, ASM-10).
- **A policy receives only `(readout, legal_actions)`**, so a baseline is a function of the decision it is handed and
  never of the hand it is inside — which is why `engine.equity` accepts a readout as well as a hand (`engine/surface.md` §11).
- **A baseline carries no shape.** It returns the `legal_actions` member at its chosen index's position, never a descriptor decoded
  in some vocabulary: every declared vocabulary begins `fold` 0, `check-call` 1 and a raise at 2 — the only indices these rules
  name — so one rule governs both shapes, while a **learner's** policy decodes in its own shape's vocabulary, its head being that shape's (`shapes.md` §3, §7, `features/surface.md` §8, `docs/L2/agents/baselines.md` §2).
- **A readout is the eleven facts of `README.md` §7, or it is refused.** Every policy checks them all before any rule
  reads one — the pairs, the card counts, the integers, the distinct cards and `hand_class`'s `None`-or-0–8 — refusing a
  malformed one by name as `policy(readout)`, `always-call`'s included (`surface.md` §1, `errors.md` §2–§3, `folders.md` §2, ASM-30).

Nothing here seeds, reads or advances the global `random` stream (ASM-2, `protocol.md` §4); §2's generator is built per decision (`rule.md` §4).

## 2. `random` — a uniform draw over the decision's legal indices

The rule: one index drawn uniformly from the decision's legal indices, from a generator **keyed by the decision** and
never by a stream position — the order of decisions is free, so a position cannot key a per-decision draw (`surface.md` §12, `protocol.md` §3–§4).

The exact procedure, from `(readout, legal_actions)` and the baseline's seed:

1. `indices = features.legal_indices(legal_actions)` — ascending, distinct, non-empty; a refusal of that call propagates, nothing is substituted (`features/surface.md` §8).
2. Canonicalise the decision as one UTF-8 string: `street`, `seat` as `"<index>:<0|1>"`, `hole` comma-joined, `board`
   likewise, `stacks` then `limit` as **one** field, `pot` then `to_call` as **one**, `history` semicolon-joined,
   `indices` comma-joined — **eight fields** joined with `"|"`, and `hand_class` in none (FAM-5.4, `battery.md` §3).
3. `key = hashlib.sha256(b"pypoker-agents/baseline-random/v1\x1f" + str(seed).encode("ascii") + b"\x1f" +
   text.encode("utf-8")).digest()`, then `u = numpy.random.Generator(numpy.random.PCG64(int.from_bytes(key[:16], "big"))).random()`,
   and `index = indices[min(int(u × len(indices)), len(indices) − 1)]`, returned as `legal_actions[indices.index(index)]` — §1's member at that position, never an illegal action (`surface.md` §2, `features/surface.md` §8).

The key is a `hashlib` digest of the decision and the seed, never `hash()`'s salted value, so one seed repeats its choices
on a decision and two seeds differ on it, the decision's bytes being the payload; FAM-5.3–5.4 assert both (`protocol.md` §3, ASM-2, `rule.md` §4, `battery.md` §3).

## 3. `always-call` — index 1 whenever 1 is legal, else the minimum legal completion

The rule: check/call whenever that is legal, never fold, and the minimum legal completion when raising is the only option
(`protocol.md` §3). From `legal_actions` alone: `1` when `1` is legal; else the decision's `raise-minimum` if it offers that
declared spelling, `features.action_space`'s, which this module re-derives no vocabulary for; else `2`, the first raise index
every declared vocabulary carries — never `0`, and §1's member at that index's position comes back (`features/surface.md` §8).

Index `1` is absent only where checking is free and only raise is offered — `{"fold", "raise"}` cannot occur, fold being
absent exactly when `to_call` is 0 (`features/surface.md` §2) — so the branch is a rule, not a fallback; an impossible mask
holding none of them gets its smallest index, and the policy never folds in any hand (FAM-5.5–5.6, D-2). No default-shape
descriptor is `raise-minimum`, so index `2` stands there as it did; on `no-limit-100` index `2` is `raise-quarter`, the
minimum being `raise-minimum` at `5`, so a minimum carrying another name falls back to the first raise (`shapes.md` §3, ASM-37).

## 4. `oracle` — call/continue at or above the pot odds, fold below them

The rule: check/call when the hand's equity is at least the pot odds `to_call / (pot + to_call)`, and fold when that
inequality fails and folding is legal (`protocol.md` §3, ASM-4). From `(readout, legal_actions)` and the seed:

1. `odds = to_call / (pot + to_call)` if `pot + to_call != 0` else `0.0` — a ratio that is `0.0` when the denominator
   is 0, never a division error (`readout["pot"]` and `readout["to_call"]` are the readout's own ints, §5).
2. `equity = engine.equity(readout, seed, 257)` — the readout it was handed, the baseline's own seed, and **257**
   samples (§5). One call per decision, no cache, no smoothing.
3. If `equity >= odds` the index is `1` when `1` is legal, else `2`; if `equity < odds` it is `0` when `0` is legal,
   else `1`; and the policy returns §1's member of `legal_actions` at that index's position (`features/surface.md` §8).

**It never chooses the raise.** A raise is not a pot-odds question, so index `2` appears only where `1` is unavailable
— the mask `engine.legal_actions` produces when a raise is the only completion (`features/surface.md` §2). **It is
blind by construction:** it reads the pot, the amount to call, its own hand, the board and the equity and nothing else,
which is what makes it a baseline, and FAM-5.7 recomputes it from the seed and count (D-6, ASM-4).

## 5. Why 257, and why the count is published

`engine.equity` is a Monte-Carlo estimate and a sample count is part of the question (`engine/surface.md` §11, ASM-4),
so the oracle's rule is checkable only if the caller re-issues **the same query**: `build_baseline("oracle", seed)`
queries `engine.equity(readout, seed, 257)`, and the L1 battery re-issues it at `S.EQUITY_SAMPLES = 257` (`tests/e2e/`).

One number on both sides makes a disagreement a defect and not an estimate's noise; 257 is odd and prime, so a split
half-sample cannot hide in the rounding, and its cost sits in ASM-15's measured band (ASM-4, `surface.md` §11).

## 6. The `baselines()` record

One mapping, keyed by the six names in `protocol.md` §3's order — D-6's three, then D-21's three — each value a plain
record of the columns below, `equity_samples` on the oracle alone (`surface.md` §11):

| `name` | `rule` | `params` | `anchor` | `equity_samples` |
|---|---|---|---|---|
| `random` | §2's uniform draw over the legal indices | `0` | `True` | — |
| `always-call` | §3's call-never-fold procedure | `0` | `True` | — |
| `oracle` | §4's pot-odds inequality | `0` | `True` | `257` (§5) |
| `fold-no-pair-or-face` | §7's pre-flop hole-card fold | `0` | `False` | — |
| `fold-no-pair-or-better` | §7's high-card-only fold | `0` | `False` | — |
| `fold-large-bet` | §7's half-stack bet fold | `0` | `False` | — |

`equity_samples` is the count `build_baseline`'s `oracle` itself uses, so the declared and the used count cannot drift
(`learner.md` §5, ASM-4); `anchor` is the flag `evaluation` reads to zero the rating on the flagged three (§9, ASM-32).

## 7. The three folders — one predicate each, one legality rule shared

Each folder reads one predicate and hands it to the rule below; D-21's "otherwise it calls" is ASM-31's, not here:

| Baseline | Folds when |
|---|---|
| `fold-no-pair-or-face` | the street is `preflop`, the two hole cards are unpaired and neither rank is J, Q, K or A (`FACE_RANKS`); `_rank(card)` is the spelling's first character, from `RANKS = "23456789TJQKA"`, and a spelling not of that shape is refused as `policy(readout)` naming `hole` (`engine/readout.md` §3) |
| `fold-no-pair-or-better` | `readout["hand_class"] == 0`, a high card only; the fact is `None` before the flop, so that one comparison **is** "from the flop onward" (ASM-30) |
| `fold-large-bet` | `2 * to_call > engine.game_config()["starting_stack"]` — more than 10 of the declared 20 — on any street; `engine` is imported inside the policy, so no copy of `20` lives here and no `pokerkit` is imported eagerly (`module-map.md` §2) |

- **One legality rule, `_continue_or_fold`:** `0` only where `fold` is legal, `1` whenever it is, `2` only where a raise is the sole legal action, else the mask's smallest index (`folders.md` §2, ASM-31).
- **No randomness:** `build_baseline` still refuses a non-integer seed, and a built folder decides identically at one seed twice and at two different seeds (`protocol.md` §3).

## 8. `build_baseline`

`build_baseline(name, seed)` returns a policy of `e2e-surface.md` §2 — a callable taking `(readout, legal_actions)` and
returning one of those descriptors — and refuses a non-integer seed and a name outside the six, naming it (`surface.md` §12).
Free to L4: the policies' shape and the private helpers. Not free: §2's payload and `v1` tag, §3's index `1`, its `raise-minimum`
spelling and first-raise fallback, §4's ratio and inequality, 257, §7's three predicates and their one rule, the six names in order (`guardrails.md`).

## 9. The `anchor` flag, and the scale it keeps (ASM-32)

`ANCHORS` is the set the flagged three name, so the declared flag and the anchor cannot drift; `evaluation` reads it
through the granted arrow and zeroes the Bradley-Terry fit on the mean of the flagged three, so a rating recorded before
D-21 and one after it read on one scale, and a folder is a member and never an anchor (`records.md` §8, ASM-32, D-21).
