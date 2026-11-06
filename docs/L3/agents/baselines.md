# agents — the three fixed baselines

- **Owner:** the three fixed rules of `protocol.md` §3 (D-6, ASM-4): `random`'s keyed uniform draw,
  `always-call`'s procedure, `oracle`'s pot-odds inequality at 257 equity samples, the blindness that makes
  them baselines, and the record `baselines()` returns
- **Ceiling:** 130 lines. At the ceiling, split by owner — never append
- **Read with:** `rule.md` §4, `errors.md` §3, `README.md` §4

## 1. What a baseline is

`random`, `always-call` and `oracle` are D-6's three, and they are the only fixed standard a self-play league
has: they are pool members and matrix columns at the same hand count as every league cell, and their three
mutual cells anchor the rating (`protocol.md` §3, `league.md` §4–§5, D-16). None of them learns from a match.

Four properties hold of all three, and each is a contract rather than a habit:

- **A baseline's state advances nowhere.** Nothing is retained from a hand it played, so its column is the same
  rule at every hand count and at every call order (`surface.md` §1, §12, `learner.md` §5).
- **A baseline has no trainable parameter.** `baselines()` declares `params: 0`, that declared zero is the count
  a cell records beside every member's (`records.md` §9), and `param_count` refuses a baseline because a
  baseline is not a learner (`surface.md` §5, ASM-10).
- **A policy receives only `(readout, legal_actions)`**, so a baseline is a function of the decision it is
  handed and never of the hand it is inside — which is exactly why `engine.equity` accepts a readout as well as a
  hand (`e2e-surface.md` §2, `engine/surface.md` §11).
- **A readout is the ten facts of `README.md` §7, or it is refused.** `random` reads the nine of §2's spelling,
  `always-call` reads none of them, and `oracle` reads `pot`, `to_call`, `hole` and `board` — but each policy
  refuses, as `policy(readout)`, a fact that is missing or not of that shape: `seat`/`limit`/`stacks` pairs, `hole`
  two cards, `board` 0, 3, 4 or 5 cards, `pot`/`to_call` integers, `history` entries, the cards of `hole` and `board`
  distinct. `always-call` refuses one it reads nothing from, because answering a decision nobody described would hide
  a caller's defect and `int("3")` would invent one (`surface.md` §1, `errors.md` §2–§3).

Nothing here seeds, reads or advances the global `random` stream (ASM-2, `protocol.md` §4); `random`'s draw comes
from a `numpy.random.Generator` built for one decision (`rule.md` §4's construction, §2 below).

## 2. `random` — a uniform draw over the decision's legal indices

The rule: one index drawn uniformly from the decision's legal indices, from a generator seeded from the
baseline's seed and **keyed by the decision** — never a stream position, because a uniform draw over each
decision's legal indices cannot come from a position once the order of decisions is free (`surface.md` §12,
`protocol.md` §3, §4, `learner.md` §5).

The exact procedure, from `(readout, legal_actions)` and the baseline's seed:

1. `indices = features.legal_indices(legal_actions)` — ascending, distinct, non-empty
   (`features/surface.md` §8). A refusal of that call propagates; nothing is substituted.
2. Canonicalise the decision as one UTF-8 string, from the readout's facts in the readout's own order and the
   mask: `street`, `seat` as `"<index>:<0|1>"`, `hole` as the cards comma-joined, `board` likewise, `stacks`
   then `limit` as **one** comma-joined field, `pot` then `to_call` as **one**, `history` semicolon-joined, and
   `indices` comma-joined — **eight fields** joined with `"|"`. A missing fact is refused naming it
   (`errors.md` §3); a ten-field reading leaves two seeds folding at one hand's first decision (FAM-5.4).
3. `key = hashlib.sha256(b"pypoker-agents/baseline-random/v1\x1f" + str(seed).encode("ascii") + b"\x1f" +
   text.encode("utf-8")).digest()`, then `u = numpy.random.Generator(numpy.random.PCG64(
   int.from_bytes(key[:16], "big"))).random()`.
4. `index = indices[min(int(u × len(indices)), len(indices) − 1)]`, and the policy returns
   `features.decode_action(index)` — a descriptor from `legal_actions`, never an illegal one
   (`surface.md` §2, §12).

The key is a `hashlib` digest of the decision and the seed and never `hash()`'s process-salted value, so one seed
repeats its choices on one decision and two seeds differ on it (`protocol.md` §3, ASM-2), and the decision's own bytes
are the payload, so call order is irrelevant (`rule.md` §4). FAM-5.3–5.4 assert those two halves (`battery.md` §3).

## 3. `always-call` — index 1 whenever 1 is legal, else index 2

The rule: check/call whenever that is legal, never fold, and the minimum legal completion when raising is the
only option (`protocol.md` §3). The exact procedure, from `legal_actions` alone:

1. `indices = features.legal_indices(legal_actions)`.
2. If `1` is among them, the index is `1`; otherwise the index is `2`; index `0` is never chosen.
3. The policy returns `features.decode_action(index)`.

Index `1` is absent only where checking is free and only raise is offered — `{"fold", "raise"}` cannot occur, fold
being absent exactly when `to_call` is 0 (`features/surface.md` §2) — so the branch on `2` is a rule, not a fallback,
and the policy never folds in any decision of any hand (`battery.md` §3 FAM-5.5–5.6). An impossible mask holding
neither `1` nor `2` gets its smallest index: legality outranks never-fold (D-2). Its seed is accepted and unused.

## 4. `oracle` — call/continue at or above the pot odds, fold below them

The rule: check/call when the hand's equity is at least the pot odds `to_call / (pot + to_call)`, and fold when
that inequality fails and folding is legal (`protocol.md` §3, ASM-4). The exact procedure, `(readout,
legal_actions)` and the baseline's seed:

1. `odds = to_call / (pot + to_call)` if `pot + to_call != 0` else `0.0` — a ratio that is `0.0` when the
   denominator is 0, never a division error (`readout["pot"]` and `readout["to_call"]` are the readout's own
   ints, `engine/surface.md` §5).
2. `equity = engine.equity(readout, seed, 257)` — the readout it was handed, the baseline's own seed, and
   **257** samples (§5). One call per decision, no cache, no smoothing.
3. If `equity >= odds`, the index is `1` when `1` is legal, else `2`; if `equity < odds`, the index is `0` when
   `0` is legal, else `1`.
4. The policy returns `features.decode_action(index)`.

**It never chooses the raise.** A raise is not a pot-odds question, so index `2` appears only where `1` is unavailable
— the mask `engine.legal_actions` produces when a raise is the only completion (`features/surface.md` §2, `learner.md`
§5). **It is blind by construction:** it reads the pot, the amount to call, its own hand, the board and the equity, and
nothing else — no history, no opponent, no adaptation, no state between decisions, which is what makes it a baseline
and not a competitor (D-6, ASM-4). Its choice is recomputable by any caller holding the seed and `baselines()`'s
declared count, which is what FAM-5.7 does (`battery.md` §3 FAM-5).

## 5. Why 257, and why the count is published

`engine.equity` is a Monte-Carlo estimate and a sample count is part of the question (`engine/surface.md` §11, ASM-4),
so the oracle's rule is checkable only if the caller can re-issue **the same query**. The count is therefore pinned to
`257` on both sides: `build_baseline("oracle", seed)` queries `engine.equity(readout, seed, 257)`, and the L1 battery
re-issues `engine.equity(hand, seed, S.EQUITY_SAMPLES)` with `S.EQUITY_SAMPLES = 257` (`tests/e2e/test_fam05_baselines.py`,
`tests/e2e/_surface.py`) before it checks the inequality. One number on both sides makes a disagreement a defect and not
an estimate's noise, a re-issue at any other count being a different query (ASM-4, `surface.md` §11). 257 is odd and
prime, so a split pot's half-sample cannot hide in the rounding, and it is small enough for ASM-15's budget.

## 6. The `baselines()` record

One mapping, keyed by the three names in the order `random`, `always-call`, `oracle`, each value a plain record
(`surface.md` §11):

| Key | `random` | `always-call` | `oracle` |
|---|---|---|---|
| `name` | `"random"` | `"always-call"` | `"oracle"` |
| `rule` | one sentence stating §2's uniform draw over the legal indices | one sentence stating §3's call-never-fold procedure | one sentence stating §4's inequality |
| `params` | `0` | `0` | `0` |
| `equity_samples` | — | — | `257` (§5) |

`equity_samples` is the key a caller reads to re-issue the oracle's query: it is the count `build_baseline`'s
`oracle` itself uses, so the declared count and the used count cannot drift (`surface.md` §11, `learner.md` §5).
The record is plain data, equal on two calls, and a report's header quotes it (`protocol.md` §1, §3).

## 7. `build_baseline`, and what is left to L4

`build_baseline(name, seed)` returns a policy of `e2e-surface.md` §2 — a callable taking `(readout,
legal_actions)` and returning one of those descriptors — and refuses a name the three do not include, naming it,
and a seed that is not an integer (`surface.md` §12). Free to L4: the policies' class, closure or `functools`
choice, and the private helpers; not free: §2's payload and its `v1` tag, §3's two indices, §4's ratio and
inequality, 257, the three names and their order, and the four keys of §6 (`guardrails.md`).
