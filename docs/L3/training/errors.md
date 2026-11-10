# training — refusals

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 6 · **Date:** 2026-11-09
- **Owner:** the error classes (§2), the message grammar every refusal follows (§3), and one canonical message per refusal the L2 surface declares (§4) — Rev 4 reads a rule against the catalogue `agents.learners()` publishes; **Rev 5** adds `ChipConservationBroken` and reads a utility against its catalogue too (D-19, D-20); **Rev 6** adds `UnknownShape` and `GreedyPassRefused`, so the hierarchy is one base and **eighteen** subclasses, and states both messages' grammar (`shapes.md` §2–§3, `sizing.md` §4, `records.md` §15, ASM-38, D-29)
- **Ceiling:** 100 lines. At the ceiling, split by owner — never append
- **Read with:** `README.md` §3, §5, `registry.md` §5, `loop.md` §6, `fairness.md` §6, `greedy.md` §4, §6, `reward.md` §4, `devices.md` §3

## 1. Why a hierarchy, and why nothing is caught

`surface.md` §1 says an invalid argument is refused by raising an error that names the violated contract, and that no entry point coerces a value, substitutes a default it did not declare, swallows an error or returns part of a record. So the error is the only reporting channel, and no refused call has an observable effect — no `run` deals a hand or writes a file, no `fairness` builds anything (`e2e-surface.md` §2, D-12).

A hierarchy exists so a caller can catch "this module refused me" without catching a `KeyError` from a bug (`errors.md` §2 of `evaluation` makes the same argument). `TrainingError` is the base of every refusal this module raises; the subclasses are **not** module-level names of the `training` package and are not surface (`surface.md` §1, `README.md` §3). **Nothing is caught**: the five `evaluation`, six `agents`, five `features` and four `engine` calls refuse in their own classes and propagate unchanged (`module-map.md` §2, `docs/L2/training/surface.md` §1), because a refusal this module re-wrapped would hide which module owns the contract.

## 2. The classes — `src/training/errors.py`

    class TrainingError(Exception)               # base of every refusal of this module
    class UnknownRung(TrainingError)             # rung: the name is not one RUNG_NAMES carries
    class ConfigurationInvalid(TrainingError)    # run: not a mapping, or `variants` / `pool` / `name` is the wrong thing
    class MissingConfigurationKey(TrainingError)  # run: a configuration missing a key the run reads — the key is named
    class VariantCountInvalid(TrainingError)     # run: a variant count other than one or two
    class VariantSettingInvalid(TrainingError)   # run: a setting the run reads is not a positive integer / a string / in [0, 1]
    class InvalidSeeds(TrainingError)            # run: the seed set is empty, repeats a seed, or holds a non-integer
    class InvalidBudget(TrainingError)           # run: the budget is not a positive integer, or is below ten hands
    class UnknownDevice(TrainingError)           # run: a device devices()["available"] does not list
    class NotAComparisonSide(TrainingError)      # fairness: a side is neither a configuration nor a variant entry
    class SideKindMismatch(TrainingError)        # fairness: one side is a configuration, the other an entry
    class ComparisonKeyMissing(TrainingError)    # fairness: a key the comparison reads is absent — the key is named
    class MultipleAxes(TrainingError)            # fairness: the differences fall in more than one axis — every axis named
    class PoolIdsDiffer(TrainingError)           # fairness: two variants of one configuration declare two pool ids
    class IgnoredDeclaration(TrainingError)      # run: a learning_rule or utility the catalogue does not carry, a hyper key, or a snapshot_every the run would not use
    class ChipConservationBroken(TrainingError)  # run: a hand's chips in play disagree with the shape's declared stacks, or its shortfall is 0, so the utility's normaliser is not the game's own (ASM-6, D-20, D-29)
    class PairDeclarationsDiffer(TrainingError)  # run, fairness: two arms of a pair declare two values for one setting they share — a `game` and a `hyper` block among them
    class UnknownShape(TrainingError)            # run, fairness: a `game` the shape catalogue does not declare, or a value that is not a shape name — the name and the declared names are named, and no name is ever defaulted (shapes.md §2–§3, D-29)
    class GreedyPassRefused(TrainingError)       # run: one variant's greedy pass at one seed would exceed its hand or decision bound, so it is refused with both counts and never truncated (sizing.md §4, records.md §15, ASM-38)

One base and eighteen subclasses, one per refusal family of `surface.md` §4–§5 and `loop.md` §6; the three absent are `features`' encoding, `agents`' backend, kind, rule and utility, and `evaluation`'s pool, each propagating in its owner's class (`agents/surface.md` §4, D-20). The two D-29 classes are the module's own because no owner can raise them: the shape catalogue a run names is restated in `declarations.py`, and the pass's bound is this module's declaration alone (`module-map.md` §2, `shapes.md` §4, D-13, D-29).

## 3. The message grammar

Every message is one line with the same four parts, in this order:

    training.<entry point> refused <what it was given>: <the contract that was violated> — <the offending value, named>

    training.rung refused the rung name 'R7-bottleneck': the registry carries R1, R2, R3, R4, R5, R6
    training.run refused the seed set [7, 7]: the seeds must be distinct integers

Four rules hold of every message:

- **the offending value is always named** — a class name alone is not a refusal, because the battery's `refusal_text` reads the text and FAM-16.28 asserts the unknown rung's own name appears in it (`tests/e2e/_surface.py`, FAM-15.5); the shape refusal names the name **and every declared name**, and the pass refusal names **both counts**;
- **the entry point is named by its module path**, `training.run` or `training.fairness`, so a caller learns which of the six refused it;
- **no traceback text, no `repr` of an internal object, no learner, pool or encoder** — a message names arguments and contracts and nothing a caller could not have passed (`e2e-surface.md` §1, D-1);
- **one language and no abbreviations**: the contract is quoted in the same words the document uses (`seeds must be distinct integers`, `differs on two axes`, `is not a device devices() lists`, `is not one of the declared shapes`), so a reader can match a message to a §.

**One refusal opens with its level in parentheses instead of a `refused` clause, and it is `UnknownShape`'s**: `training.run(game of the configuration 'R7'): …`, because what it names is a **level and an argument** — the configuration's `game` or the entry's — and not a value the run was handed at the top. The four parts still hold of it: the entry point, the name given, the contract with **both declared names**, and the citation; and it is the only message in the set that ends by stating what is never done with the value (`a shape name is never defaulted`, `shapes.md` §3, D-29).

## 4. One canonical message per refusal

| Refusal | Canonical message |
|---|---|
| `UnknownRung` | `training.rung refused the rung name 'R7-bottleneck': the registry carries R1, R2, R3, R4, R5, R6` |
| `ConfigurationInvalid` | `training.run refused the configuration 'R7': 'variants' must be a sequence of variant entries, not a mapping` |
| `MissingConfigurationKey` | `training.run refused the configuration 'R7': it carries no 'pool' key, which the run reads to freeze the pool` |
| `VariantCountInvalid` | `training.run refused the configuration 'R7': it declares 3 variants, and a configuration declares one or two` |
| `VariantSettingInvalid` | `training.run refused the variant 'deep-sparse': 'architecture.sparsity' is 1.5, which is outside [0, 1]` |
| `InvalidSeeds` | `training.run refused the seed set []: a run needs at least one distinct integer seed` |
| `InvalidBudget` | `training.run refused the budget 0: a run needs a positive budget of at least ten hands` |
| `UnknownDevice` | `training.run refused the device 'gpu0': devices() lists cpu` |
| `NotAComparisonSide` | `training.fairness refused 'R1': a side is a configuration (carrying 'variants') or a variant entry (carrying 'architecture')` |
| `SideKindMismatch` | `training.fairness refused the pair: the left side is a configuration and the right is a variant entry` |
| `ComparisonKeyMissing` | `training.fairness refused the pair: the right side carries no 'architecture' key, which the comparison reads` |
| `MultipleAxes` | `training.fairness refused the pair: it differs on two axes, encoding and connectivity, and a reportable pair differs on one` |
| `PoolIdsDiffer` | `training.fairness refused the pair: its two variants declare two pool ids, 'pool-a' and 'pool-b', and both arms train against one frozen pool` |
| `IgnoredDeclaration` | `training.run refused the variant 'deep-sparse' of the configuration 'R7': 'hyper' names 'learning_rate' 0.0005 and the run uses 0.001, because the module's declared hyper is fixed for the whole ladder — vary it in src/training/declarations.py (ASM-7)` |
| `PairDeclarationsDiffer` | `training.run refused the configuration 'R7': its two variants 'deep-sparse' and 'wide-sparse' declare two 'samples' values, 1000 and 2000, and both arms of a pair are trained at one value (ASM-8)` |
| `ChipConservationBroken` | `training.run refused the hand at seed 424242: the chips in play at seat 1's decision total 42.0, and the game declares 2 seats at a starting stack of 20.0, which is 40.0 (ASM-6, utilities.md §4)` |
| `UnknownShape` | `training.run(game of the configuration 'R7'): 'no-limit-50' is not one of the declared shapes ('fixed-limit-20', 'no-limit-100'), and a shape name is never defaulted (shapes.md §2, D-29)` |
| `GreedyPassRefused` | `training.run of the configuration 'R1' refused the greedy pass: the run's budget is 200000 hands per variant per seed, so the pass would play 200000 hands, and one pass plays at most 2000 (sizing.md §4, records.md §15, ASM-38)` |

**The shape that names a catalogue rather than a value in force is a rule's, a utility's or a shape's** (Rev 4, Rev 5, Rev 6, D-19, D-20, D-29), entry-level: `training.run refused the variant 'deep-sparse' of the configuration 'R7': 'learning_rule' is 'masked-q', and the catalogue agents.learners() publishes (src/agents/declarations.py) carries masked-q-learning, double-q-learning — name one of those, or name none for the catalogue's first (rules.md §2, §4, D-19)`; at the configuration's own level the same sentence with `the variant 'deep-sparse' of` dropped, and the same shape again with `'utility'` and the utility catalogue's two names. Each names the **offending member and the catalogue**, never a value the run substitutes, because a second catalogued member is read and forwarded and only a name no member carries is refused (`declarations.md` §2, `utilities.md` §5). `UnknownShape` is the third of them and adds the one clause the other two do not have: **a shape name is never defaulted**, so the message says both which name was given and which names exist, and `fairness`'s copy of it (`_shape` through `declarations.require_game`) is the same sentence with `training.fairness(game)` for its prefix (`shapes.md` §3, D-29, D-13).

The other shapes differ in the key and the two values they name: a `snapshot_every` quotes the interval the declared samples fix (`the interval the declared 1000 samples fix, 100`), an unknown `hyper` key names its own value and the six keys `HYPER` carries, and `fairness`'s pair refusal reads `training.fairness refused the pair: its two sides declare two 'hyper' values, {...} and {...}, and a held constant is not one side's declaration (ASM-7)`; its shape refusal reads `training.fairness refused the pair: its two sides name two shapes, 'fixed-limit-20' and 'no-limit-100', and a comparison pair is one shape's (shapes.md §1, §6, ladder.md §4, D-29)` — both shapes named, the way `PoolIdsDiffer` names both ids. A declared `param_budget` is `VariantSettingInvalid`'s third shape at either level, naming the value and the declared band's contract (ASM-10); `GreedyPassRefused`'s second shape quotes the count the pass would reach and the bound it would cross (`it would record 24001 decisions, and one pass records at most 24000`). Every message names the level it was given, the key or the counts, the value declared and the value in force (`declarations.md` §2–§4, `surface.md` §5, ASM-18, D-20).

The two refusals this module delegates — `features.build_encoder`'s unknown encoding and `agents.build_learner`'s unknown backend, kind, rule or utility — keep their owner's message verbatim and are **never** re-raised in a `TrainingError` (`loop.md` §6, `agents/surface.md` §4).

## 5. What is left to L4

A refusal's `__str__` versus its `args[0]`, whether a subclass carries the offending value as an attribute, and the ordering of the sentences in a message. Not L4's: the eighteen classes and their names, the four parts and their order, the four rules of §3, and §4's eighteen messages (`guardrails.md` G16, G21–G23, G25); `test_errors.py` (`TRN-9.k`) drives every row of §4 but the `ChipConservationBroken` one, which `test_episode.py::TRN-4.12` drives, the `UnknownShape` one, which `test_shapes.py::TRN-13.2` drives, and the `GreedyPassRefused` one, which `test_greedy.py::TRN-14.5` drives.
