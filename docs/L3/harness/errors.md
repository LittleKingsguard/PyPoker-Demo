# harness — refusals

- **Layer:** L3 · **Module:** `harness` · **Unit:** phase1 · **Rev:** 3 · **Date:** 2026-11-05 · §1 scoped (surface.md Rev 2)
- **Owner:** the refusal classes (§2), the message grammar every refusal follows (§3), and one canonical message per
  refusal this module raises (§4)
- **Ceiling:** 100 lines. At the ceiling, split by owner — never append
- **Read with:** `README.md` §7, `support.md` §2, §3, `expectations.md` §4, `driver.md` §1, §7

## 1. Four classes, and exactly two catches

`surface.md` §1 says a violated contract is refused with an error naming it, except where an entry point is contracted
to *report* the failure instead — `drive` for the case it is handed (`driver.md` §1) and `expect` for a kind `fixtures()`
does not list (`expectations.md` §4) — because L1 contracts a verdict there and a battery must be able to read it
(`e2e-surface.md` §2, `records.md` §14).

So exactly three refusals raise, one each in `factory`, `expect` and `seam`; `timings` raises nothing, and `drive` no
refusal of its own — its never-raise is scoped as `surface.md` §2 scopes it, with `hands`' counter over an outcome that is
not §1's plain data the one boundary (`driver.md` §7).
The hierarchy exists so a caller can catch "this module refused me" without catching a `KeyError` from its own bug.
**Exactly two exceptions are caught, and neither hides an owner's refusal**: `drive`'s is around a **step**, which is
a case's own call and not a call this module makes (`driver.md` §2), and `expect`'s is around its one reader call,
which turns a reader's exception into the kind's named failure while keeping the exception's class and message in the
reason (`expectations.md` §3). The five packages' refusals — an unknown encoding, an unknown backend, an unknown
baseline name, a bad pool declaration, a non-integer seed — propagate unchanged, because a refusal this module
re-wrapped would hide which module owns the catalogue (`e2e-surface.md` §2, `module-map.md` §2, D-13).

## 2. The classes — the top of `src/harness/__init__.py`

    class HarnessError(Exception)                # base of every refusal this module raises
    class UnknownFactoryKind(HarnessError)       # factory: the kind is not one of the six
    class UnknownExpectationKind(HarnessError)   # expect: the kind is not a string
    class NoLegalAction(HarnessError)            # seam: the legal set it was handed is empty

One base and three subclasses — one per entry point that can refuse, and no subclass without a raise site. They are
module-level names of the `harness` package and are the only names besides the six that `tests/harness/` may import
(`README.md` §3); nothing below them is surface. A class per *contract clause* is the rejected alternative: it is
thirteen classes for four entry points, and a battery that reads a message needs no more than three families
(`README.md` §7).

## 3. The message grammar

Every message is one line with the same four parts, in this order:

    harness.<entry point> refused <what it was given>: <the contract that was violated> — <the offending value, named>

    harness.factory refused the kind 'deck-of-cards': the map declares baseline, encoder, hand, learner, pool, rung
    harness.expect refused the kind 3: a kind is a name fixtures() lists, zero-sum, legal-choice, counted, refused
    harness.seam('recording') refused the empty legal set: a policy returns a member of legal_actions

Four rules hold of every message:

- **the offending value is named**, as a `%r` of what the caller passed — FAM-14.4 reads the text of the undeclared
  factory kind and FAM-16.36 compares the invented kind's token against the named failure, so a class name alone is not
  a refusal (`tests/e2e/_surface.py`'s `refusal_text`, `_family_token`);
- **the entry point is named by its module path**, `harness.factory`, so a caller learns which of the six refused it —
  and for `seam`, which is the one entry point whose refusals happen inside an instance, the path is qualified by the
  label that instance carries: `harness.seam('recording') refused the empty legal set: …`. That is still the four-part
  grammar with `<what it was given>` and `<the offending value>` merged, because a seam's label *is* what it was built
  with and the readout it answered with nothing legal is the state, not an argument (G24 of `guardrails.md`);
- **no traceback text, no `repr` of an internal object, no learner, pool, encoder, hand or policy** — a message names
  arguments and contracts and nothing a caller could not have passed (`e2e-surface.md` §1, D-1);
- **one language and no abbreviations**: the contract is quoted in the words this design uses (`a policy returns a
  member of legal_actions`, `the map declares …`, `a kind is a name fixtures() lists`), so a reader can match a message
  to the § that fixed it.

The facts `expect` reports are *not* errors and follow `expectations.md` §1's form instead. A reported fact is a
sentence about a value the harness was handed; an error is a statement that the harness would not run at all, and the
two must not read alike.

## 4. One canonical message per refusal

| Class | When | Canonical message |
|---|---|---|
| `UnknownFactoryKind` | `factory`'s kind is not one of the six | `harness.factory refused the kind 'deck-of-cards': the map declares baseline, encoder, hand, learner, pool, rung` |
| `UnknownFactoryKind` | the kind is not a string | `harness.factory refused the kind 7: the map declares baseline, encoder, hand, learner, pool, rung` |
| `UnknownExpectationKind` | `expect`'s kind is not a string | `harness.expect refused the kind 3: a kind is a name fixtures() lists, zero-sum, legal-choice, counted, refused` |
| `NoLegalAction` | `seam`'s legal set is empty | `harness.seam('recording') refused the empty legal set: a policy returns a member of legal_actions` |

The six declared kinds are listed **sorted** and the four expectation kinds in `KINDS`' order, because a sorted list is
stable across builds and the kind set's order is contract (`expectations.md` §2). Neither list is spelled anywhere else
in the module: the message formats `sorted(OBJECTS)` and `KINDS`, so a seventh factory kind or a fifth expectation kind
would appear in the message that names it (`layout.md` §1, §4).

The refusals this module delegates keep their owner's message verbatim — `features.build_encoder`'s unknown encoding,
`agents.build_learner`'s unknown backend or kind, `agents.build_baseline`'s unknown name, `evaluation.build_pool`'s bad
declaration, `training.rung`'s unknown rung and `engine.new_hand`'s non-integer seed — and are never re-raised in a
`HarnessError`, because the catalogue is the owner's and the value is named there (`support.md` §2, `module-map.md` §2).

## 5. What is left to L4

A refusal's `__str__` versus its `args[0]`, whether a message is one f-string or a `%` tuple, and where the classes sit
in the file (above the readers, `layout.md` §1). Not L4's: the four class names and the base, the four parts of §3 and
their order, the four rules, and §4's messages. `tests/harness/test_harness_errors.py` (`HRN-8.k`) drives every row of
§4 and each raise site; `test_fam14_harness.py` (FAM-14.4) and `test_fam16_blind.py` (FAM-16.36) read the text.
