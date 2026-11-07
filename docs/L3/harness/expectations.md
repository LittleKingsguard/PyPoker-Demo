# harness — the expectations

- **Layer:** L3 · **Module:** `harness` · **Unit:** phase1 · **Rev:** 4 · **Date:** 2026-11-05 · §3 scoped (surface.md Rev 2)
- **Owner:** `expect(kind, observation)` — the verdict record (§1), the four kinds in their declared order with each
  reader's order and the fact it names when it fails (§2), the two rules that make a verdict a verdict (§3), and the two
  edges where the surface reports instead of raising (§4)
- **Ceiling:** 130 lines. At the ceiling, split by owner — never append
- **Read with:** `driver.md` §3, `errors.md` §2, §4, `layout.md` §1, `docs/L2/harness/surface.md` §6

## 1. The verdict record

`expect(kind, observation)` returns three keys, in this order (`surface.md` §6):

| Key | Content |
|---|---|
| `kind` | the kind as handed, verbatim — a layer return cites it |
| `verdict` | `"pass"` or `"fail"` |
| `reason` | `None` on a pass; on a failure one sentence naming the kind **verbatim**, the contract it judges and the fact that did not hold |

The failure sentence is one form for all four kinds, built in one place:

    harness.expect failed the kind '<kind>': <the fact that did not hold>

so a reader can find the kind by alphanumeric token, which the battery does for a kind it invented
(`tests/e2e/test_fam14_harness.py`'s `_family_token` test, FAM-14.8, FAM-16.36). `verdict` is a string and sits in the
record where a tolerant pass/fail scan reads it (`surface.md` §1).

## 2. The four kinds, in this order

`KINDS = ("zero-sum", "legal-choice", "counted", "refused")` — the order is contract, because `fixtures()` lists them in
it and a battery that takes the first listed kind gets `zero-sum`, the kind that judges an episode record, which is the
value most cases drive (L2's H-1, FAM-14.8). `_CHECKS` binds each name to its reader; a reader returns `None` when the
value satisfies the kind and a **fact** string when it does not.

### 2.1 `zero-sum` — the per-seat chip deltas balance

The value's per-seat chip deltas sum to zero. The deltas are read in this order, and the first shape that applies is the
one used (`surface.md` §6):

1. a mapping carrying `payoffs` — an episode record — gives the numbers under it (`records.md` §5);
2. a mapping carrying `directions` — a cell record — gives each direction's `mean_chip_delta` as a quantity, and nothing a
   direction states that is not one (`records.md` §9, §2.5 here);
3. a mapping of two per-seat numbers gives its numeric values — `{"seat 0": 12, "seat 1": -12}`, and equally
   `engine.payoffs`' own `{0: x, 1: y}` mapping;
4. a sequence of two numbers gives its numbers — `[7, -7]`.

Pass iff exactly **two** deltas were read, both are finite, and `abs(sum(deltas)) <= 1e-9` — the pass predicate, read as
written. The tolerance is absolute and not a rounded comparison: a cell's two directions are each other's negative, so a
float sum may land on `1e-17` rather than `0` (`protocol.md` §2, ASM-12, FAM-7). Finiteness is part of the predicate: a
non-finite pair does not balance, yet no comparison with its sum is true — `NaN + NaN`, `+inf + (-inf)` — so testing the
*negation* (`abs(sum) > 1e-9`) is **rejected**: the predicate is evaluated, never negated. Fail facts: *the value states no
two per-seat chip deltas* (a bare number, a record with no `payoffs`, no `directions` and more than two numbers) and *the
chip deltas `<deltas>` do not sum to zero* — also the fact a `NaN`, `+inf` or `-inf` pair gets.

### 2.2 `legal-choice` — the chosen descriptor is one of the legal ones

Pass iff the value is a mapping carrying a non-empty `legal` and a `chosen`, and `chosen` is one of the elements of
`legal` — membership by equality, in the order the value states them. The harness decides **no** legality: it asks
whether the descriptor the work returned is one of the descriptors it was handed, and a policy that returned an illegal
action is a contract violation and not a fold (`e2e-surface.md` §2, D-2). Fail facts: *the value states no legal
descriptors* (absent, empty, or not a mapping) and *the chosen descriptor is outside the legal set*.

### 2.3 `counted` — a cell accounts for every hand it reports

Pass iff the value is a mapping carrying a numeric `hands` and a non-empty `directions`, and every direction's
wins + ties + losses equals that `hands` (`records.md` §9, `protocol.md` §2). The counts are read under either spelling
— `COUNTS = ("wins", "win", "ties", "tie", "losses", "loss")` — and only under those keys: a row's `seat_split`,
`mean_chip_delta` and any other field are not counts and are never summed. Fail facts: *the value is not a cell record
carrying its directions and hands* and *a direction counts `<n>` outcomes and the cell reports `<hands>` hands*.

### 2.4 `refused` — the observed work refused

Pass iff the value is a mapping whose `refused` flag **is the boolean `True`** — `is True`, and not "truthy": a string
flag (`{"refused": "yes"}`) and a numeric one (`{"refused": 1}`) are *failures*, because `surface.md` §6 declares a flag
and a flag is a boolean. The flag is **declared**, never inferred: the driver builds `{"refused": True, "error":
"<Class>: <message>"}` for a step that raised (`driver.md` §2), so a verdict of refusal depends on a flag and not on which
words an entry point chose — a kind that read the text would invent a refusal semantics no entry point declared (D-13,
L2's H-1). Fail fact: *the observed work returned a value rather than refusing* — a returned record is a value, even one
that carries the word "refused" in its text or a flag that is merely a true value.

### 2.5 The three readers the kinds share

`_quantity(value)` — `True` for a real number that is not a `bool`; a bool is a flag and not a quantity, and an integer
count, a float mean and a per-hand seconds figure are all quantities.

`_numbers(value)` — the quantities a value states **directly**, in its own order: a mapping's numeric values, a
sequence's numeric entries, or the value itself when it is one quantity; anything else is `[]`. It never descends: a
nested record's numbers are not the record's deltas, which is why §2.1 names the two nests it *does* read.

`_deltas(value)` — the per-seat deltas of §2.1, applying its four shapes in its order and returning `_numbers` of the
shape it found. Shape 2 states what it keeps: each direction's `mean_chip_delta` **iff `_quantity` reads it** — a string,
a `None` and a boolean mean are dropped before §2.1 counts the pair, which only ever lowers the count, so such a cell
reaches *no two per-seat chip deltas* and never `sum`. A direction count other than two is still §2.1's *exactly two*
predicate: the drop decides which deltas are counted and never waives the count. Returning the raw means is **rejected**,
and it is what shipped once: a `True`/`-1` pair summed as `1 + -1` and passed a kind that reads chip deltas.

## 3. Two rules that make a verdict a verdict

- **Total, and enforced in one place.** Every listed kind yields a verdict for *any* observed value — the plain data of
  `surface.md` §1, one a reader raised on included — so a value a kind cannot read is a named failure, never a pass or a
  silence (`surface.md` §6, `records.md` §14, FAM-14.8). The guard is written **once**, in `expect`, around its one call
  into `_CHECKS`: whatever a reader raises becomes that kind's named failure, the reason carrying its class and message
  (§1's form) — for any exception whose text the harness can format. The reason is built **inside** the guard, so an
  exception whose own `__str__` raises escapes as a raise, and a `BaseException` is not caught (both out of scope,
  `surface.md` §6, Rev 2). A reader is the plain expression it reads like, with no `try`, and `drive` inherits the rule
  with no second guard (`driver.md` §3). **Rejected:** a `try`/`except` per reader, and a battery that enumerates more
  "odd values" — an enumeration misses the next value by construction and a per-reader guard leaves the next reader
  unguarded; the raw-mean `mean_chip_delta` pair, `(10**999, 1.5)` and a descriptor whose `==` raises each shipped a raise
  out of `expect` and `drive` (§2.1, §2.2, §2.5). The rule reaches what a **kind** reads; `_hands` counts a mapping's
  declared keys and is no kind's reader, so it sits outside the guard too: `expect` stays total over an object whose own
  mapping protocol raises, where `drive`'s counter raises on it (`driver.md` §5, to L2).
- **Deterministic.** One kind and one observed value give one verdict, in one process and across processes: a verdict
  reads only the value it was handed — never a clock, a stream, a file, an ambient fixture or a second observation —
  and never mutates it. Two calls on two equal values give two equal records (FAM-16.36).

A verdict is a statement about the value and never a claim about a rung's worth: `zero-sum` says the engine's payoffs
balance, not that the hand was played well; `counted` says a cell's arithmetic closes, not that the cell measured
anything worth having (`battery.md` §5, D-6). Nothing here measures a cell, plays a hand, encodes an observation or
fits a rating (`module-map.md` §3).

## 4. The two refusal edges

| The argument | What happens |
|---|---|
| a `kind` that is **not a string** | raises `UnknownExpectationKind` naming the value and the kind set — `surface.md` §1's rule for an invalid argument (`errors.md` §4) |
| a string `kind` `KINDS` does not carry | returns `{"kind": <the string>, "verdict": "fail", "reason": "harness.expect failed the kind '<the string>': fixtures() lists zero-sum, legal-choice, counted, refused"}` |

The asymmetry is contract and not an accident: `e2e-surface.md` §3.6's named-failure edge is about a kind **name**, and
L1 contracts exactly that named failure so that the driver can report the case that rested on it (`drive`'s §3, FAM-14.10,
FAM-16.36). A non-name is not a kind at all, so it is an invalid argument and is refused rather than judged.
