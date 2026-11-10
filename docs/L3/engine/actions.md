# engine — the action vocabulary

- **Owner:** the shape's descriptions of an action — their type, value equality, stable text, and the one place an amount is resolved — and nothing else. The two entry points that carry them are `stepping.md`'s
- **Ceiling:** 62 lines — raised from 60 to hold the second vocabulary. At the ceiling, split by owner — never append

## 1. The descriptor is a plain string

    BASES = ("fold", "check-call")                       # indices 0 and 1, in every declared shape
    SIZED = ("raise-quarter", "raise-half", "raise-all-in", "raise-minimum")   # indices 2 to 5

A descriptor is a plain `str` and nothing else: not a class, not an enum, not a pair carrying an
amount. The **vocabulary is the shape's** — three descriptors in `fixed-limit-20`, six in
`no-limit-100`, each returned by `vocabulary(hand)` in that row's own index order (`config.md` §2, §6).
`legal_actions` returns a `tuple[str, ...]`, a readout's `legal` fact is that same tuple, and a record
holds the member itself (`stepping.md` §1).

Four consequences, each of which a contract at the edge needs (`e2e-surface.md` §2):

- **value equality** — two descriptors for one action are equal because two equal `str`s are equal, so a
  policy’s answer can be checked with `in` and a record compares across two calls (`battery.md` §3 FAM-2);
- **stable text** — `str(d)` and `repr(d)` are the same words everywhere, so a record holding one prints
  identically on every run and every machine;
- **hand-independent** — `features.decode_action(i)` returns the shape's `actions[i]` and needs neither
  a hand nor an import of this module: the encoding's indices and these words are one declared
  vocabulary (`e2e-surface.md` §2, `features/encodings.md`);
- **plain data** — hashable, sortable, JSON-shaped, and it survives in a record that outlives the hand.

Rejected: an `Action` class carrying its amount. It would need a module-level name for `features` to
construct (an eleventh entry point, `layout.md` §2), would attach an amount to a value shared across
every decision, and would leave `decode_action` — which knows an index — unable to build one.

## 2. No amount is carried — the engine resolves every raise

A descriptor names the action and never its size. Fixed-limit makes the size unique: the completion is
the street’s bet size in force, so `raise` means *the smallest legal completion* for this decision
(`e2e-surface.md` §2, D-2, ASM-6) — a meaning it keeps, its step staying amount-less (`advance.md` §1). A
shape with no fixed bet declares four raise descriptors partitioning the legal interval: with `m` the
minimum legal raise-to, `A` the all-in raise-to and `L = A − m`, they own

| Descriptor | Owns | Resolves to | Legal iff |
|---|---|---|---|
| `raise-minimum` | `{m}` | `m` | a raise is legal at all |
| `raise-quarter` | `(m, m + L//4]` | `m + L//4` | `L//4 >= 1` |
| `raise-half` | `(m + L//4, m + L//2]` | `m + L//2` | `L//2 > L//4` |
| `raise-all-in` | `(m + L//2, A]` | `A` | `A > m + L//2` |

Every legal amount lies in exactly one band, so two descriptors never resolve to one amount and an empty
band is **masked out of `legal_actions`, never collapsed onto its neighbour** (`config.md` §5, `sizing.md`
§2). The resolution happens in `apply_action`, which hands the amount to the step (`stepping.md` §2); it
never happens in the descriptor, which is why one `"raise-quarter"` serves every hand of its shape.

Rejected: a nominal pot-fraction ladder — ½ pot, 1 pot, all-in. Its rungs are not legal amounts, so at a
small pot a fraction's integer falls below the minimum completion and two rungs bet the same amount: the
measured collapse, and the reason the withdrawn ladder's rungs overlapped (`sizing.md` §2, D-29).
Rejected on the same ground: a `"raise to 8"` variant, which puts the game's numbers in the action space.

## 3. What is not a descriptor

Anything else is refused with the contract named (`messages.md` §1, `InvalidAction`): an integer index, a
`pokerkit` operation, a differently-cased spelling (`"Fold"`), a synonym (`"call"`, `"check"`, `"bet"`), a
descriptor of another shape (`"raise"` on the no-cap row, `"raise-half"` on the fixed one), `None`. There
is no coercion: a caller that passes an index has confused this module with `features` (`decode_action`).
