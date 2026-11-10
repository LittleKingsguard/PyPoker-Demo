# PyPoker-Demo — L1 end-to-end I/O surface

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 7 · **Date:** 2026-11-09
- **Purpose:** the entry points the L1 e2e battery drives, named precisely enough to call (brief §5)
- **Ceiling:** 180 lines. At the ceiling, split by owner — never append

## 1. How binding this is

The names and counts below are the contract. L2 may refine types, defaults and error classes and may not add, remove or rename an entry point: needing one is an L2 defect and returns as an `ADJUDICATION` to L1 (modules.md §3, D-12). Each module's count here equals its `endpoints` in `modules.json`.

Rev 7 declares the second game shape beside D-2's fixed-limit one (D-29, `shapes.md` §2–§4) and raises this page's ceiling from 160 to 180 lines to hold it: what the shape adds is one row of §3.1 and an optional argument or key on eight existing rows, and splitting the surface across two documents would leave two lists that must agree rather than one (`shapes.md` §4).

Every entry point is a module-level name of the module's package: `engine.new_hand` is `src/engine/`. Nothing below the entry point is part of the surface, and no battery may reach past an entry point (brief §5).

## 2. Shared contracts

**Policy protocol.** A policy is a callable taking `(readout, legal_actions)` and returning one action descriptor from `legal_actions`. `engine` calls policies and never imports one; `agents.as_policy` and `evaluation.policy_from` return one. A policy that returns an illegal action is a contract violation, not a fold (D-2). A policy built from a learner also carries `learning_rule`, the catalogue member its model learned under, and `utility`, the catalogue member whose reward it was trained on, so a table can name the population and the objectives it measured; a baseline policy and a policy handed in from outside carry neither (D-19, D-20, `rules.md` §7, `utilities.md` §7).

**Game shape.** A shape is a declared row of `engine.game_shapes()` — the seats, blinds, starting stack, chips in play, bet structure, action vocabulary, head width and amount normalisers of one game — and `fixed-limit-20` is the first and the **default**, so a caller that names no shape gets today's game (`shapes.md` §2). Every entry point that can differ by shape takes the shape's name as an optional argument or key whose absence means the default: `engine.game_config`, `engine.new_hand`, `engine.play_hand`, `features.action_space`, `features.build_encoder`, `features.decode_action`, `agents.build_learner`'s spec, `agents.as_policy`, `evaluation.build_pool`'s declaration, `evaluation.policy_from` and `training.run`'s configuration (`shapes.md` §4 lists the three the design's first list left out and why a hand cannot be told its shape any other way). A name outside the catalogue is refused **naming it and the declared names** — never defaulted — and a record, a pool or a container the named shape contradicts is refused naming both; absence is the default, and no record names a shape it did not measure (`shapes.md` §3, D-13). The chips in play are the shape's own total, so `pot + sum(stacks)` is 40 in the default shape and the shape's total elsewhere (`shapes.md` §2).

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
| `limit` | the fixed bet size in force and the bet-or-raise actions made this street — 0 to 4, the cap in bet-and-raise actions of ASM-6, not a count of raises after an opening bet; the cap is the fixed-limit shape's, and a shape without one bounds the count by its own stack (`shapes.md` §2) |
| `history` | the ordered public actions of this hand |
| `legal` | the legal action descriptors, in the engine's order |
| `hand_class` | the acting seat's best five-card hand of hole plus board as an integer — 0 high card, 1 one pair, 2 two pair, 3 three of a kind, 4 straight, 5 flush, 6 full house, 7 four of a kind, 8 straight flush — and `None` before the flop, where fewer than five cards are known (`folders.md` §3, ASM-30, D-21). A derived fact of factors already present, not a wider information set, and no encoding carries it |

**Observation spec.** `features.observation_spec(encoder)` declares `representation` (`flat-numeric` for R1/R2, `card-tokens` for R3–R6), `fields` (the subset of the readout facts the encoding carries), `vocabulary` (the token-id cardinality a learner is sized from, and null for the flat encoding), and the shape and dtype of one observation. `fields` is identical for every encoding: the ladder never changes what the agent may know, only how it is represented (D-3). A fact's *value* is `engine`'s spelling of it and `features` encodes it as given, so no second spelling of the deal exists in the project (D-2, D-13).

**Action vocabulary.** `features.action_space(shape)` declares the shape's descriptors in the shape's own index order. The **fixed-limit shape's** is the three indices `0` fold, `1` check/call, `2` raise — unchanged, and what a caller naming no shape gets; the no-limit shape's is six, in an order the measurement sets and not the amount (`sizing.md` §2–§3). An action descriptor is the vocabulary's own name and carries no amount: `engine` resolves a raise to an amount, which fixed-limit makes unique (the minimum legal completion) and a sized shape makes the band's own maximum (`sizing.md` §2). `features.legal_indices` returns the indices in the descriptors' order, one per descriptor, and `decode_action` maps an index back to the descriptor `engine.apply_action` accepts. The vocabulary is the shape's, not a rung's (D-2, D-29).

**Pool.** A pool is an ordered member list plus its bound. A member is either a `version` — a checkpoint of a run, carrying an id, the lineage it came from, its path, the **rule** it was trained under and the **utility** whose reward it was trained on — or one of the catalogue's fixed baselines, which carries neither: the three of D-6 always, and the three folders of D-21 when the declaration names them (D-16, D-21). A pool holds at most M versions and always holds the baselines, which are never evicted; a frozen pool's membership does not change while it is used (D-16, ASM-16, D-20). Versions are grouped into families — one lineage chain each, all its members under one rule and one utility — and a full window evicts fair-share, so no family is emptied while another holds two or more (D-19, ASM-26). The same pool object is the training opposition and the evaluation opposition (D-16).

**Utility.** `agents.learners()` publishes the utility catalogue a learner spec selects from: `net-chips`, the seat's unshaped net chip delta and the declared default, and `stack-shortfall`, the delta of the squared stack shortfall over the chips in play, normalised by the shortfall a hand begins with — each stated with the reward it delivers, both consuming one `hyper` declaration and one state layout (`utilities.md` §2, §3, D-20). A spec naming none builds the catalogue's **first** member, and a name outside the catalogue is refused by name — in a spec, a variant entry, a pool member and a `load` spec alike. The reward is terminal only and the TD bootstrap stays the rule's business, so a caller never branches on a utility to learn (D-19, D-20).

**Learning rule.** `agents.learners()` publishes the catalogue a learner spec selects from: `masked-q-learning` and `double-q-learning`, each stated with the target it aims at, and both consuming one `hyper` declaration and one state layout (`rules.md` §2, §3, D-19). A spec naming none builds the catalogue's **first** member, and a name outside the catalogue is refused by name — in a spec, in a variant entry, in a pool member and in a `load` spec alike. Whatever the rule, a learner answers `act`, `learn`, `save`, `load`, `param_count` and `as_policy` with one shape, so no caller branches on it (D-19, `rules.md` §3).

**Cell.** A cell is one unordered pair of members played at one hand count, with seats alternating across hands, and reported in both directions: each member's wins, ties, losses, mean chip delta per hand and seat split (D-16, ASM-14). Every cell of one table is played at the same hand count, the three baseline cells included, so no member's row is measured more precisely than another's (D-16).

**Rating.** A rating is fitted over a matrix, yields one value and a 95% confidence interval per member, and is anchored so the **three anchor baselines of D-6** sit at zero — the catalogue's `anchor` flag, never a folding baseline D-21 adds: a rating therefore reads as a distance from the only fixed standard in the table (D-16, ASM-17, ASM-32). A rating is a statement about the table's named members and never a claim of poker skill (D-16).

**Table budgets.** `live` and `full` are the two table budgets: one membership, two hand counts per cell. The live table is produced during a talk; the full table is precomputed offline and shipped under `tables/` (D-16, D-8, ASM-14).

**Determinism and device.** A run is reproducible from `(config, seeds, budget, pool membership)`: `engine.new_hand(seed)` seeds Python's global `random`, which is what `pokerkit` shuffles with (ASM-2), so every cell runs sequentially — one stream deals every hand and concurrency is not available (D-16). A learner draws its exploration randomness from an explicitly seeded generator recorded in the run record. Exactness is promised on CPU, which is what the sandbox and an audience laptop are (D-8); a user-started GPU run records its device in the run record so a third party can tell the two apart (D-6, `strata/platform.md`).

**Failure.** An invalid argument raises an error naming the violated contract (unknown rung, illegal action, mismatched seed set, incomplete evidence, a cell whose hand count differs, a pool missing a baseline). No entry point silently coerces, substitutes, or returns a partial record. The mapping each entry point exchanges is declared key by key in `records.md`, and a **required** key there is part of this contract (D-13).

## 3. Entry points

### 3.1 `engine` — 10

| Entry point | Inputs | Returns | Kind |
|---|---|---|---|
| `game_shapes` | — | the declared shapes, `fixed-limit-20` first and the default, each with its seats, blinds, starting stack, chips in play, bet structure, action vocabulary, head width and amount normalisers (`shapes.md` §2, D-29) | fixed |
| `game_config` | a shape name, optional | the named shape's parameters — with no argument, the fixed game's: two seats, blinds 1/2, one blind level, stacks 20, fixed bets 2 and 4, raise cap 4 (ASM-6), unchanged; a name outside `game_shapes` is refused by name (D-29) | fixed |
| `new_hand` | seed, a shape name, optional | a hand handle dealt on that shape — the default game when none is named; seeds the global `random` (ASM-2, `shapes.md` §4) | general |
| `readout` | hand | the facts of §2 for the acting seat | general |
| `legal_actions` | hand | ordered action descriptors, the engine's order | general |
| `apply_action` | hand, action descriptor | the advanced hand; the hand it was given is unchanged, so a caller may keep an earlier handle | general |
| `is_terminal` | hand | whether the hand is over | general |
| `payoffs` | hand | net chips per seat for the completed hand, summing to zero | general |
| `play_hand` | seed, the seat-0 policy, the seat-1 policy, a shape name, optional | an episode record on that shape — the default game when none is named — of the ordered decisions with their facts, chosen descriptors, the amount the engine resolved for a raise and the raise's own bounds, and rewards, plus the payoffs (`records.md` §5, `shapes.md` §4) | general |
| `equity` | the hand or that hand's readout, seed, sample count | the acting seat's win probability against a uniformly random opponent hand, from `pokerkit`'s equity calculation (ASM-4); a policy-based caller has no hand, so the readout of the decision is an accepted argument (D-6) | general |

### 3.2 `features` — 7

| Entry point | Inputs | Returns | Kind |
|---|---|---|---|
| `encodings` | — | the declared encoding names with their representation kind | fixed |
| `build_encoder` | encoding name, a shape name, optional | an encoder for that encoding on that shape — the default shape when none is named — since the amount normalisers and bucket edges are the shape's (`sizing.md` §5, `shapes.md` §2) | fixed |
| `observation_spec` | encoder | representation, carried `fields`, shape, dtype (§2) | fixed |
| `encode` | encoder, readout | one observation for that readout | general |
| `action_space` | a shape name, optional | the named shape's vocabulary of §2 in its own index order — the three indices when none is named | fixed |
| `legal_indices` | legal action descriptors | the legal indices for that decision | general |
| `decode_action` | index, a shape name, optional | the action descriptor `engine.apply_action` accepts, in that shape's order — the default shape's three when none is named | general |

### 3.3 `agents` — 10

| Entry point | Inputs | Returns | Kind |
|---|---|---|---|
| `learners` | — | the learner backends (`numpy`, `torch`), the architecture kinds the ladder uses, the **learning-rule catalogue** under the key `learning_rules` with each member's target, the **utility catalogue** under the key `utilities` with each member's reward and normaliser, and the one `hyper` block both catalogues consume — five keys in all (`rules.md` §2, `utilities.md` §2, ASM-7, D-19, D-20) | fixed |
| `build_learner` | a learner spec (backend, architecture, sizes, seed, the rule it learns under, the utility it is trained on, the shape it decides in, and the encoder when the caller has one) | a learner under the declared rule, utility and shape — each catalogue defaulting to its first and the shape to the default game when the spec names none; the head is as wide as that shape's vocabulary, so the parameter count follows the shape (`sizing.md` §6); with no encoder it is sized from the `observation_size` its architecture kind declares, and `observation_spec` is the cross-check that keeps the two equal (D-3, D-19, D-20, D-29) | general |
| `param_count` | learner | trainable parameter count — the matched-budget measurement, which no rule and no utility changes, and which the shape's head width sets (ASM-10, D-19, D-20, D-29) | general |
| `act` | learner, observation, legal mask | one action index plus the learner's own record of the decision | general |
| `learn` | learner, transitions | the update's own statistics (loss or TD error) for the curve, under whichever rule the learner was built with and on the terminal reward its utility defines | general |
| `save` | learner, path | the written checkpoint path; the container records the rule and the utility beside the seed and the encoding, and the shape is what its format version says it carries (`sizing.md` §6, D-19, D-20, D-29) | general |
| `load` | learner spec, path | the restored learner, under the rule, utility and shape its container records; a spec carrying a rule, a utility or a shape the file contradicts is refused naming both | general |
| `as_policy` | learner, encoder, seed, an exploration mode, optional | a policy in the sense of §2, carrying the rule and the utility its learner was built under; the mode is `schedule` — the default, and today's behaviour — or `off`, where the decision is the masked maximum and the tie-break alone and no generator is drawn from (`sizing.md` §4) | general |
| `baselines` | — | the six fixed names of `protocol.md` §3 — `random`, `always-call`, `oracle`, `fold-no-pair-or-face`, `fold-no-pair-or-better`, `fold-large-bet` — each carrying its rule, `params: 0` and an `anchor` flag that is true for the three of D-6 and false for D-21's folders (D-6, D-21) | fixed |
| `build_baseline` | baseline name, seed | a policy in the sense of §2 (ASM-4); a folder folds only where folding is legal and never raises while check/call is legal (`folders.md` §2, ASM-31) | fixed |

### 3.4 `evaluation` — 11

| Entry point | Inputs | Returns | Kind |
|---|---|---|---|
| `protocol` | — | the evidence contract a report is judged against: the seven families of `protocol.md` §1, the seed set, the required header (D-6, D-16) | fixed |
| `league` | — | the league's parameters: M, the three pinned anchor baselines and the catalogue names a declaration may add, the cell count for a given membership, the live and full cell sizes, the table seed, the rating method (D-16, ASM-14, ASM-32, D-21) | fixed |
| `build_pool` | a membership declaration (versions with lineage, rule and utility, plus the shape the pool is on, M, whether the pool is frozen, and the catalogue baseline names it declares beyond the three of D-6) | a pool in the sense of §2; the three anchor baselines are added and pinned, each declared folder joins pinned alongside them, and a version's rule or utility or shape, or a declared baseline name the catalogue does not carry, is refused by name (D-16, ASM-16, ASM-26, D-20, ASM-32, D-21, D-29) | general |
| `pool_members` | pool | the ordered members with their metadata — each version's rule and utility included — the `rules` and `utilities` the pool holds, and the bound M the pool holds to (D-19, D-20) | general |
| `offer` | pool, one version | the pool advanced by one version: the version extends one family and a full window evicts fair-share, so no family is emptied while another holds two or more, and a version whose rule or utility differs from its family's is refused (D-19, D-20, ASM-18, ASM-26) | general |
| `opponent` | pool, seed | one policy drawn from the pool, for one training hand | general |
| `match` | two policies or two members, hand count, seed | one cell in the sense of §2, with both seats' parameter counts, each member's rule and utility, and the seed used (D-16, D-20) | general |
| `matrix` | pool, the rung's variant policies, a table budget (`live` or `full`) | the pairwise matrix: ordered members, one cell per unordered pair, each member's rule and utility, the `population` and the `utility_population` they make up, the shape its pool is on, the table seed and the per-cell hand count (D-16, D-19, D-20, D-29) | general |
| `rating` | matrix | the fitted rating per member with its 95% interval, the method, the anchor, the hands behind each rating and the fit's convergence (D-16, ASM-17) | general |
| `policy_from` | checkpoint path, an exploration mode, optional | a policy in the sense of §2, loaded in evaluation mode, carrying the rule and the utility its container records; the mode is `schedule` by default and `off` is the greedy policy the sized census reads (`sizing.md` §4, §7) | general |
| `report` | rung name, run record, matrix, rating | the complete per-rung report, or a failure naming the missing evidence family or the violated league rule — a run, a pool and a matrix that do not name one shape included; its pool family and header carry the rules, the utilities and the shape the measured population held (D-6, D-16, D-19, D-20, D-29) | general |

### 3.5 `training` — 6

| Entry point | Inputs | Returns | Kind |
|---|---|---|---|
| `rungs` | — | the six rung declarations in brief §2's order, each with its variants, its lineage and its budget | fixed |
| `rung` | rung name | one resolved rung configuration, or an error naming the unknown rung | general |
| `run` | rung name or rung config, seed set, budget, device | the run record: per-seed curves, throughput, the frozen pool's id and membership it trained against, the snapshot paths, each variant's rule and utility, the run's rule set and utility set, the **shape** it played and its greedy evaluation pass, and the seed, budget and device actually used (D-6, D-16, D-19, D-20, D-29, `sizing.md` §4) | general |
| `fairness` | two rung configurations or two variants | what a comparison pair holds constant — the pool each arm used, one pool for both arms of a two-variant rung, and the **set** of rules and of utilities both sides declare — and the single axis on which it differs (D-3, D-16, D-19, D-20) | general |
| `devices` | — | the available devices and the default, CPU inside the sandbox and GPU only for a user-started run (D-8) | fixed |
| `checkpoints` | — | the shipped checkpoint index: each rung variant's final model, and the pool's retained versions, each with the rule and the utility it was trained under (D-16, ASM-5, ASM-18, D-19, D-20) | general |

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
| `engine` | 10 | 150 |
| `features` | 7 | 120 |
| `agents` | 10 | 150 |
| `evaluation` | 11 | 160 |
| `training` | 6 | 110 |
| `harness` | 6 | 110 |
| **Total** | **50** | — |

The ceiling column is `50 + 10×N` (brief §5); `modules.json` carries the `endpoints` column and these row counts are the same numbers once that file is re-declared for this revision. The second game shape takes `engine` from 9 to 10 and the map from 49 to 50 — one new name, `game_shapes`, and eight rows widened by an optional argument whose absence is today's value (`shapes.md` §4). `modules.json`'s `engine` row must be re-declared 9 → 10 with this revision; that file is not this layer's to edit and this revision does not edit it.

## 5. General-purpose surfaces and the blind instance

A row marked `general` is defined for any valid instance; a row marked `fixed` has one instance that is the project's whole point (the two declared game shapes of D-2 and D-29, the two encodings of D-3, the six baselines of D-6 and D-21, the six rungs of brief §2, the one league of D-16, the two learning rules of D-19 and the two utilities of D-20). The battery's blind instance rule applies to the `general` rows only: for each of them the test writer authors at least one case whose instance appears in no design document, invented from this surface alone (D-15, examiner.md §3). A row is `fixed` when no instance of it can be invented through the declared surface — an encoder exists only by one of the two declared encodings, so `observation_spec` is a fixed row and is tested, not blinded.

There are 37 `general` rows — 8 in `engine`, 3 in `features`, 7 in `agents`, 9 in `evaluation`, 4 in `training`, 6 in `harness` — so the battery carries at least 37 blind instances. One case may name one `general` row as its subject and exercise other rows as a path; being the subject is what counts. The **13** `fixed` rows are the count of §3 less those 37; `game_shapes` joins them, because its instances are the declaration itself and no caller can invent a shape through this surface (`shapes.md` §2).
