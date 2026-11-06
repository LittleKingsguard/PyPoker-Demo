# PyPoker-Demo — L1 end-to-end I/O surface

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-05
- **Purpose:** the entry points the L1 e2e battery drives, named precisely enough to call (brief §5)
- **Ceiling:** 160 lines. At the ceiling, split by owner — never append

## 1. How binding this is

The names and counts below are the contract. L2 may refine types, defaults and error classes and may not add, remove or rename an entry point: needing one is an L2 defect and returns as an `ADJUDICATION` to L1 (modules.md §3, D-12). Each module's count here equals its `endpoints` in `modules.json`.

Every entry point is a module-level name of the module's package: `engine.new_hand` is `src/engine/`. Nothing below the entry point is part of the surface, and no battery may reach past an entry point (brief §5).

## 2. Shared contracts

**Policy protocol.** A policy is a callable taking `(readout, legal_actions)` and returning one action descriptor from `legal_actions`. `engine` calls policies and never imports one; `agents.as_policy` and `evaluation.policy_from` return one. A policy that returns an illegal action is a contract violation, not a fold (D-2).

**Readout facts — the information set.** `engine.readout(hand)` returns a mapping with exactly these keys, and they are the same facts for every rung (D-3):

| Key | Content |
|---|---|
| `street` | preflop, flop, turn or river |
| `seat` | the acting seat, and whether it is the button |
| `hole` | the acting seat's two cards |
| `board` | zero to five public cards |
| `stacks` | both seats' remaining chips |
| `pot` | chips already committed to the pot |
| `to_call` | chips the acting seat must add to continue |
| `limit` | the fixed bet size in force and the raises made this street |
| `history` | the ordered public actions of this hand |
| `legal` | the legal action descriptors, in the engine's order |

**Observation spec.** `features.observation_spec(encoder)` declares `representation` (`flat-numeric` for R1/R2, `card-tokens` for R3–R6), `fields` (the subset of the readout facts the encoding carries), `vocabulary` (the token-id cardinality a learner is sized from, and null for the flat encoding), and the shape and dtype of one observation. `fields` is identical for every encoding: the ladder never changes what the agent may know, only how it is represented (D-3). A fact's *value* is `engine`'s spelling of it and `features` encodes it as given, so no second spelling of the deal exists in the project (D-2, D-13).

**Action vocabulary.** `features.action_space()` is fixed for the whole ladder: three indices — `0` fold, `1` check/call, `2` raise. An action descriptor is the vocabulary's own name — `fold`, `check-call` or `raise` — and carries no amount: `engine` resolves a raise to its minimum legal completion, which fixed-limit makes unique. `features.legal_indices` returns the indices in the descriptors' order, one per descriptor, and `decode_action` maps an index back to the descriptor `engine.apply_action` accepts. The vocabulary is the game's, not a rung's (D-2).

**Pool.** A pool is an ordered member list plus its bound. A member is either a `version` — a checkpoint of a run, carrying an id, the lineage it came from and its path — or one of the three fixed baselines. A pool holds at most M versions and always holds the baselines, which are never evicted; a frozen pool's membership does not change while it is used (D-16, ASM-16). The same pool object is the training opposition and the evaluation opposition (D-16).

**Cell.** A cell is one unordered pair of members played at one hand count, with seats alternating across hands, and reported in both directions: each member's wins, ties, losses, mean chip delta per hand and seat split (D-16, ASM-14). Every cell of one table is played at the same hand count, the three baseline cells included, so no member's row is measured more precisely than another's (D-16).

**Rating.** A rating is fitted over a matrix, yields one value and a 95% confidence interval per member, and is anchored so the three baselines sit at zero: a rating therefore reads as a distance from the only fixed standard in the table (D-16, ASM-17). A rating is a statement about the table's named members and never a claim of poker skill (D-16).

**Table budgets.** `live` and `full` are the two table budgets: one membership, two hand counts per cell. The live table is produced during a talk; the full table is precomputed offline and shipped under `tables/` (D-16, D-8, ASM-14).

**Determinism and device.** A run is reproducible from `(config, seeds, budget, pool membership)`: `engine.new_hand(seed)` seeds Python's global `random`, which is what `pokerkit` shuffles with (ASM-2), so every cell runs sequentially — one stream deals every hand and concurrency is not available (D-16). A learner draws its exploration randomness from an explicitly seeded generator recorded in the run record. Exactness is promised on CPU, which is what the sandbox and an audience laptop are (D-8); a user-started GPU run records its device in the run record so a third party can tell the two apart (D-6, `strata/platform.md`).

**Failure.** An invalid argument raises an error naming the violated contract (unknown rung, illegal action, mismatched seed set, incomplete evidence, a cell whose hand count differs, a pool missing a baseline). No entry point silently coerces, substitutes, or returns a partial record. The mapping each entry point exchanges is declared key by key in `records.md`, and a **required** key there is part of this contract (D-13).

## 3. Entry points

### 3.1 `engine` — 9

| Entry point | Inputs | Returns | Kind |
|---|---|---|---|
| `game_config` | — | the fixed game's parameters: two seats, blinds 1/2, one blind level, stacks 20, fixed bets 2 and 4, raise cap 4 (ASM-6) | fixed |
| `new_hand` | seed | a hand handle; seeds the global `random` (ASM-2) | general |
| `readout` | hand | the facts of §2 for the acting seat | general |
| `legal_actions` | hand | ordered action descriptors, the engine's order | general |
| `apply_action` | hand, action descriptor | the advanced hand; the hand it was given is unchanged, so a caller may keep an earlier handle | general |
| `is_terminal` | hand | whether the hand is over | general |
| `payoffs` | hand | net chips per seat for the completed hand, summing to zero | general |
| `play_hand` | seed, the seat-0 policy, the seat-1 policy | an episode record: the ordered decisions with their facts, chosen actions and rewards, plus the payoffs | general |
| `equity` | the hand or that hand's readout, seed, sample count | the acting seat's win probability against a uniformly random opponent hand, from `pokerkit`'s equity calculation (ASM-4); a policy-based caller has no hand, so the readout of the decision is an accepted argument (D-6) | general |

### 3.2 `features` — 7

| Entry point | Inputs | Returns | Kind |
|---|---|---|---|
| `encodings` | — | the declared encoding names with their representation kind | fixed |
| `build_encoder` | encoding name | an encoder | fixed |
| `observation_spec` | encoder | representation, carried `fields`, shape, dtype (§2) | fixed |
| `encode` | encoder, readout | one observation for that readout | general |
| `action_space` | — | the three-index vocabulary of §2 | fixed |
| `legal_indices` | legal action descriptors | the legal indices for that decision | general |
| `decode_action` | index | the action descriptor `engine.apply_action` accepts | general |

### 3.3 `agents` — 10

| Entry point | Inputs | Returns | Kind |
|---|---|---|---|
| `learners` | — | the learner backends (`numpy`, `torch`) and the architecture kinds the ladder uses | fixed |
| `build_learner` | a learner spec (backend, architecture, sizes, seed, and the encoder when the caller has one) | a learner; with no encoder it is sized from the `observation_size` its architecture kind declares, and `observation_spec` is the cross-check that keeps the two equal (D-3) | general |
| `param_count` | learner | trainable parameter count — the matched-budget measurement (ASM-10) | general |
| `act` | learner, observation, legal mask | one action index plus the learner's own record of the decision | general |
| `learn` | learner, transitions | the update's own statistics (loss or TD error) for the curve | general |
| `save` | learner, path | the written checkpoint path | general |
| `load` | learner spec, path | the restored learner | general |
| `as_policy` | learner, encoder, seed | a policy in the sense of §2 | general |
| `baselines` | — | the three fixed names: `random`, `always-call`, `oracle` (D-6) | fixed |
| `build_baseline` | baseline name, seed | a policy in the sense of §2 (ASM-4) | fixed |

### 3.4 `evaluation` — 11

| Entry point | Inputs | Returns | Kind |
|---|---|---|---|
| `protocol` | — | the evidence contract a report is judged against: the seven families of `protocol.md` §1, the seed set, the required header (D-6, D-16) | fixed |
| `league` | — | the league's parameters: M, the three pinned baselines, the cell count for a given membership, the live and full cell sizes, the table seed, the rating method (D-16, ASM-14) | fixed |
| `build_pool` | a membership declaration (versions with lineage, plus M and whether the pool is frozen) | a pool in the sense of §2; the baselines are added and pinned (D-16, ASM-16) | general |
| `pool_members` | pool | the ordered members with their metadata, and the bound M the pool holds to | general |
| `offer` | pool, one version | the pool advanced by one version: the rolling window drops its oldest evictable version and the baselines stay (D-16, ASM-18) | general |
| `opponent` | pool, seed | one policy drawn from the pool, for one training hand | general |
| `match` | two policies or two members, hand count, seed | one cell in the sense of §2, with both seats' parameter counts and the seed used (D-16) | general |
| `matrix` | pool, the rung's variant policies, a table budget (`live` or `full`) | the pairwise matrix: ordered members, one cell per unordered pair, the table seed and the per-cell hand count (D-16) | general |
| `rating` | matrix | the fitted rating per member with its 95% interval, the method, the anchor, the hands behind each rating and the fit's convergence (D-16, ASM-17) | general |
| `policy_from` | checkpoint path | a policy in the sense of §2, loaded in evaluation mode | general |
| `report` | rung name, run record, matrix, rating | the complete per-rung report, or a failure naming the missing evidence family or the violated league rule (D-6, D-16) | general |

### 3.5 `training` — 6

| Entry point | Inputs | Returns | Kind |
|---|---|---|---|
| `rungs` | — | the six rung declarations in brief §2's order, each with its variants, its lineage and its budget | fixed |
| `rung` | rung name | one resolved rung configuration, or an error naming the unknown rung | general |
| `run` | rung name or rung config, seed set, budget, device | the run record: per-seed curves, throughput, the frozen pool's id and membership it trained against, the snapshot paths, and the seed, budget and device actually used (D-6, D-16) | general |
| `fairness` | two rung configurations or two variants | what a comparison pair holds constant — the pool each arm used, one pool for both arms of a two-variant rung — and the single axis on which it differs (D-3, D-16) | general |
| `devices` | — | the available devices and the default, CPU inside the sandbox and GPU only for a user-started run (D-8) | fixed |
| `checkpoints` | — | the shipped checkpoint index: each rung variant's final model, and the pool's retained versions (D-16, ASM-5, ASM-18) | general |

### 3.6 `harness` — 6

The harness's consumers are test batteries (brief §5). Each entry point returns support the batteries use; none of them performs work a real module owns.

| Entry point | Inputs | Returns | Kind |
|---|---|---|---|
| `drive` | one case: steps over declared entry points, with the expected observable outcome | the case result record | general |
| `fixtures` | — | the preconditions a battery case starts from: a scratch root, a pinned seed, a pinned device, and the list of expectation kinds `expect` accepts | general |
| `factory` | an object kind the map declares, plus options | that object, built through the owning module's entry point | general |
| `seam` | a seam kind — any label; `recording` and `synthetic` are the documented behaviours and any other label behaves as `recording` | a policy in the sense of §2 that records the readouts it was called with | general |
| `expect` | one of the expectation kinds `fixtures` lists, plus the observed value | a pass or a named failure for the driver's record; an unknown kind is a named failure, never a silent pass | general |
| `timings` | — | the wall-clock, the seconds per hand and the throughput records the driver collected — the R1/R2 speed evidence of D-7 and the per-hand cost ASM-15 and ASM-21 are stated from | general |

A seam's contract is the policy protocol and not its label, so a battery may invent a seam kind; an expectation's kind set is the harness's own and is discovered from `fixtures()`, so a battery invents an observed value and never a kind (records.md §14, D-13).

## 4. Counts

| Module | Endpoints | Harness ceiling |
|---|---|---|
| `engine` | 9 | 140 |
| `features` | 7 | 120 |
| `agents` | 10 | 150 |
| `evaluation` | 11 | 160 |
| `training` | 6 | 110 |
| `harness` | 6 | 110 |
| **Total** | **49** | — |

The ceiling column is `50 + 10×N` (brief §5); `modules.json` carries the `endpoints` column and these row counts are the same numbers.

## 5. General-purpose surfaces and the blind instance

A row marked `general` is defined for any valid instance; a row marked `fixed` has one instance that is the project's whole point (the one game of D-2, the two encodings of D-3, the three baselines of D-6, the six rungs of brief §2, the one league of D-16). The battery's blind instance rule applies to the `general` rows only: for each of them the test writer authors at least one case whose instance appears in no design document, invented from this surface alone (D-15, examiner.md §3). A row is `fixed` when no instance of it can be invented through the declared surface — an encoder exists only by one of the two declared encodings, so `observation_spec` is a fixed row and is tested, not blinded.

There are 37 `general` rows — 8 in `engine`, 3 in `features`, 7 in `agents`, 9 in `evaluation`, 4 in `training`, 6 in `harness` — so the battery carries at least 37 blind instances. One case may name one `general` row as its subject and exercise other rows as a path; being the subject is what counts.
