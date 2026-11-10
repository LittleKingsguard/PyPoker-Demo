# agents — the six fixed baselines at this surface

- **Layer:** L2 · **Module:** `agents` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-10
- **Owner of this file:** the two surface rows of the fixed baseline catalogue — `baselines` (§1) and `build_baseline`
  (§2): their signatures, arguments, returns, refusals and determinism, and the `anchor` flag the rating is zeroed on
  (`protocol.md` §3, `records.md` §9, ASM-4, ASM-31, ASM-32, D-6, D-21)
- **Read with:** `surface.md` §1 and §11–§12 (which keep one-line pointers here); `learner.md` §5, §8; the design at
  `docs/L3/agents/baselines.md` §1–§9
- **Ceiling:** 110 lines. At the ceiling, split by owner — never append

Split out of `surface.md`, which keeps one-line pointers, when the second game shape's seven rows filled that
document's budget (D-12, D-13); §3 came here from `learner.md` §5 at the same time, so the six baselines have one owner.
**The shape moves nothing here**: the six rules, the `anchor` set, the oracle's sample count and each baseline's
`params` of `0` are what they were, because a baseline is a function of the decision it is handed and not of the game
(`protocol.md` §3, `folders.md` §2, D-6, D-21).

## 1. `baselines` — the six fixed baselines (`fixed` row)

- **Signature:** `baselines()`.
- **Arguments:** none: they are D-6's three and D-21's three folders, so there is no parameter by which the set can be
  varied, and nothing to refuse (`e2e-surface.md` §3.3, D-6, D-21).
- **Returns:** one mapping keyed by the six names in `protocol.md` §3's order — `random`, `always-call`, `oracle`,
  `fold-no-pair-or-face`, `fold-no-pair-or-better`, `fold-large-bet` — each value carrying that baseline's name, the
  rule `protocol.md` §3 states for it, its `params` of `0`, because a baseline has no trainable parameter, and its
  `anchor` flag: `True` for the three of D-6 and `False` for D-21's folders, which is the set the rating is zeroed on
  (`protocol.md` §3, `records.md` §9, ASM-32, D-21). The oracle's value also declares the sample count its equity query
  uses — the count `build_baseline`'s `oracle` itself queries, so a caller that built the baseline at one seed
  re-issues the same query, at that seed and at the declared count, and checks the inequality itself; a re-issue at any
  other count is a different query and cannot falsify the rule (§2, `learner.md` §5, `engine/surface.md` §11, ASM-4).
- **Determinism and ordering:** two calls return equal records, in the order §1's Returns gives the six names; the
  catalogue is plain data a report's header quotes (`protocol.md` §1, §3).

## 2. `build_baseline` — one baseline as a policy (`fixed` row)

- **Signature:** `build_baseline(name, seed)`.
- **Arguments:** one of the six names §1 declares, and a seed for that baseline's own generator
  (`e2e-surface.md` §3.3, ASM-4).
- **Returns:** a policy in the sense of `e2e-surface.md` §2 (ASM-4, `protocol.md` §3). Its rule is
  `learner.md` §5's; it receives only the readout and the legal descriptors, which is why the oracle asks
  `engine.equity` with the readout it was handed rather than with a hand, and why `fold-large-bet` reads the declared
  starting stack through `engine.game_config` rather than holding a copy of it (`e2e-surface.md` §2,
  `engine/surface.md` §11, `folders.md` §2, ASM-31). A baseline's policy carries no `learning_rule` and no `utility`, and
  no shape: it is handed a decision of whichever shape the table plays (`surface.md` §1, `shapes.md` §7).
- **Refusals:** a name the six do not include, with that name in the error (`e2e-surface.md` §2,
  `protocol.md` §3); a seed that is not an integer (ASM-2).
- **Determinism:** one decision gives one descriptor, because no baseline advances any state; for `random` one seed
  repeats its choices and two seeds differ (`protocol.md` §3), while `always-call`, `oracle` and the three folders are
  functions of the decision alone — a folder decides identically at one seed twice and at two different seeds. The draw
  is keyed by the decision as a learner's exploration is, since a uniform draw over a decision's legal indices cannot
  come from a stream position (`surface.md` §1, `protocol.md` §3, §4, ASM-4). A baseline never learns (D-6, D-19, D-20).

## 3. The six rules, and the `anchor` flag

`baselines()` names **six**: `random`, `always-call` and `oracle` are D-6's, and `fold-no-pair-or-face`,
`fold-no-pair-or-better` and `fold-large-bet` are D-21's three folders. None learns from a match, all six are pool
members and matrix columns at one hand count — the only fixed standard a self-play league has — and a baseline policy
carries **no** `learning_rule` (D-6, `protocol.md` §3, D-16, `league.md` §4, D-19).

| Baseline | Its rule | What a battery can assert |
|---|---|---|
| `random` | a uniform draw over the decision's legal indices, from a generator seeded from the baseline's seed (`protocol.md` §3) | it never returns an illegal index; one seed agrees twice and two seeds differ (`protocol.md` §3, `surface.md` §12) |
| `always-call` | check/call whenever that is legal, never fold, and the minimum legal completion when raising is the only option (`protocol.md` §3) | it folds in no decision of any hand (`protocol.md` §3) |
| `oracle` | check/call when the hand's equity is at least the pot odds `to_call / (pot + to_call)`, and fold when that inequality fails and folding is legal (`protocol.md` §3, ASM-4) | its choice is consistent with that inequality at every decision, recomputable from `engine.equity` and the readout (`protocol.md` §3, ASM-4) |

The three folders carry one fold predicate each — `fold-no-pair-or-face` pre-flop on unpaired hole cards with no J, Q,
K or A, `fold-no-pair-or-better` from the flop on a `hand_class` of `0`, and `fold-large-bet` on any street where the
call exceeds half the declared starting stack — and otherwise check/call; each folds only where folding is legal and
never raises while check/call is legal, and consumes no randomness (`protocol.md` §3, `folders.md` §2, ASM-31, D-21).

- **The `anchor` flag keeps the rating's scale.** Every record carries it: true for D-6's three, false for the folders,
  and `evaluation` zeros the fit on the mean of the flagged three, so a rating recorded before D-21 and one recorded
  after it are read on one scale (ASM-32, `league.md` §5, D-16).
- **The oracle is a rule, and a blind one.** Its equity comes from `engine.equity`, queried with the readout it was
  handed, **the seed the baseline was built with** and the sample count §1's catalogue declares — so a caller holding
  that seed and that count re-issues the query and checks the inequality itself (`surface.md` §11, ASM-4). It never
  raises, a raise being no pot-odds question: strong on the pot-odds axis `protocol.md` §3 names and blind on every
  other — no history, no opponent, no adaptation — which is what makes it a baseline and not a competitor (D-6).
- **A baseline never learns, and its state advances nowhere.** `learn` refuses a value that is not a learner, and
  nothing here retains anything from a hand a baseline played, so a baseline's column is the same rule at every hand
  count and every call order (`surface.md` §1, §7, §12, D-6, `protocol.md` §3). Because no state advances, its random
  draw is keyed by the decision as a learner's exploration is (`surface.md` §1, §12).
- **A baseline has no trainable parameters:** `baselines()` declares its `params` as `0`, and that declared zero is
  the count a cell records beside every other member's count — `param_count` refuses a baseline because a baseline
  is not a learner (`surface.md` §5, `records.md` §9).
- **A policy receives only `(readout, legal_actions)`,** so a baseline is a function of the decision it is handed and
  never of the hand it is inside — which is why `engine.equity` accepts a readout as well as a hand
  (`e2e-surface.md` §2, `engine/surface.md` §11, `engine/environment.md` §6).
