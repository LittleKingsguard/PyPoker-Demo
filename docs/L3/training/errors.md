# training — refusals

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-08
- **Owner:** the error classes (§2), the message grammar every refusal follows (§3), and one canonical message per refusal the L2
  surface declares (§4) — Rev 2 adds this module's two declaration refusals, `docs/L2/training/declarations.md` §2–§4
- **Ceiling:** 100 lines. At the ceiling, split by owner — never append
- **Read with:** `README.md` §5, `registry.md` §5, `loop.md` §6, `fairness.md` §6, `devices.md` §3

## 1. Why a hierarchy, and why nothing is caught

`surface.md` §1 says an invalid argument is refused by raising an error that names the violated contract, and that no entry point
coerces a value, substitutes a default it did not declare, swallows an error or returns part of a record. The error is therefore
the only reporting channel: no refusal comes back as a failure record, and no refused call has an observable effect — a refused
`run` deals no hand and writes no file, and a refused `fairness` builds nothing (`e2e-surface.md` §2, D-12).

A hierarchy exists so a caller can catch "this module refused me" without catching a `KeyError` from a bug (`errors.md` §2 of
`evaluation` makes the same argument). `TrainingError` is the base of every refusal this module raises; the subclasses are
**not** module-level names of the `training` package and are not surface (`surface.md` §1, `README.md` §3). **Nothing is
caught**: the five `evaluation` calls, the four `agents` calls, the five `features` calls and the four `engine` calls refuse in
their own classes and their refusals propagate unchanged, because a refusal this module re-wrapped would hide which module owns
the contract (`e2e-surface.md` §2, `module-map.md` §2).

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
    class IgnoredDeclaration(TrainingError)      # run: a declared learning_rule / hyper key / snapshot_every the run would not use
    class PairDeclarationsDiffer(TrainingError)  # run, fairness: two arms of a pair declare two values for one setting they share

One base and fifteen subclasses, one per refusal family of `surface.md` §4–§5 and `loop.md` §6. Three refusals are **not**
here because they are not this module's: `features.build_encoder`'s unknown encoding, `agents.build_learner`'s unknown backend or
kind, and `evaluation.build_pool`'s or `pool_members`' pool declaration — each propagates in its owner's class, and `loop.md` §6
names them for the reader (`module-map.md` §2, `features/surface.md` §4, `agents/surface.md` §4, `evaluation/surface.md` §5).

## 3. The message grammar

Every message is one line with the same four parts, in this order:

    training.<entry point> refused <what it was given>: <the contract that was violated> — <the offending value, named>

    training.rung refused the rung name 'R7-bottleneck': the registry carries R1, R2, R3, R4, R5, R6
    training.run refused the seed set [7, 7]: the seeds must be distinct integers
    training.run refused the budget 6: a run needs at least ten hands, one for each snapshot interval
    training.fairness refused the pair: it differs on two axes, encoding and connectivity

Four rules hold of every message:

- **the offending value is always named** — a class name alone is not a refusal, because the battery's `refusal_text` reads the
  text and FAM-16.28 asserts the unknown rung's own name appears in it (`tests/e2e/_surface.py`, FAM-15.5);
- **the entry point is named by its module path**, `training.run`, so a caller learns which of the six refused it;
- **no traceback text, no `repr` of an internal object, no learner, pool or encoder** — a message names arguments and contracts
  and nothing a caller could not have passed (`e2e-surface.md` §1, D-1);
- **one language and no abbreviations**: the contract is quoted in the same words the document uses (`seeds must be distinct
  integers`, `differs on two axes`, `is not a device devices() lists`), so a reader can match a message to a §.

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

The other two `IgnoredDeclaration` shapes differ only in the key and the two values they name: `training.run refused the variant 'deep-sparse' of the configuration 'R7': 'learning_rule' is 'masked-q' and the run uses 'masked-q-learning', because one learning rule is fixed for the whole ladder — vary it in src/training/declarations.py (ASM-7)`;
a `snapshot_every` reads `... 'snapshot_every' is 200, and the run uses the interval the declared 1000 samples fix, 100, because ASM-18 holds ten equally spaced snapshots — vary it in src/training/declarations.py (ASM-18)`, an unknown `hyper` key names its own value and the six keys `HYPER` carries, and `fairness`'s pair refusal reads `training.fairness refused the pair: its two sides declare two 'hyper' values, {...} and {...}, and a held constant is not one side's declaration (ASM-7)`;
every message names the entry and the configuration it belongs to, the key, the value declared and the value in force (`docs/L2/training/declarations.md` §3–§4, `surface.md` §5).

The two refusals this module delegates keep their owner's message verbatim — `features.build_encoder`'s unknown encoding and
`agents.build_learner`'s unknown backend or kind — and are **never** re-raised in a `TrainingError`, because the catalogue is the
owner's and the value is named there (`loop.md` §6, `features/surface.md` §4, `agents/surface.md` §4).

## 5. What is left to L4

A refusal's `__str__` versus its `args[0]`, whether a subclass carries the offending value as an attribute, and the ordering of
the sentences inside a message. Not L4's: the fifteen classes and their names, the four parts and their order, the four rules of
§3, and §4's fifteen messages (`guardrails.md` G16, G21). `tests/training/test_errors.py` (`TRN-9.k`) drives every row of §4, Rev 2's two with the contract's test writer.
