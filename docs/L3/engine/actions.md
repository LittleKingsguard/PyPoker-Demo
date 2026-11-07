# engine — the action vocabulary

- **Owner:** the three descriptions of an action — their type, value equality, stable text, and the one place an amount is resolved — and nothing else. The two entry points that carry them are `stepping.md`’s
- **Ceiling:** 60 lines. At the ceiling, split by owner — never append

## 1. The descriptor is a plain string

    ACTIONS = ("fold", "check-call", "raise")     # indices 0, 1, 2 — the vocabulary of e2e-surface §2

A descriptor is one of those three `str` values and nothing else: not a class, not an enum, not a pair
carrying an amount. `legal_actions` returns a `tuple[str, ...]`, a readout’s `legal` fact is that same
tuple, and a record holds the member itself (`stepping.md` §1).

Four consequences, each of which a contract at the edge needs (`e2e-surface.md` §2):

- **value equality** — two descriptors for one action are equal because two equal `str`s are equal;
  nothing has to be taught to compare them, so a policy’s answer can be checked with `in` and a record
  compares across two calls (`battery.md` §3 FAM-2, FAM-16);
- **stable text** — `str(d)` and `repr(d)` are the same three words everywhere, so a record holding one
  prints identically on every run and every machine;
- **hand-independent** — `features.decode_action(i)` returns `ACTIONS[i]` and needs neither a hand nor
  an import of this module: the encoding’s three indices and these three words are one declared
  vocabulary (`e2e-surface.md` §2, `features/encodings.md`);
- **plain data** — hashable, sortable, JSON-shaped, and it survives being stored in an episode record
  that outlives the hand.

Rejected: an `Action` class carrying its amount. It would need a module-level name for `features` to
construct (a tenth entry point, `layout.md` §2), would attach an amount to a value shared across every
decision, and would leave `decode_action` — which knows an index and nothing else — unable to build
one.

## 2. No amount is carried, and `raise` is the minimum legal completion

A descriptor names the action and never its size. Fixed-limit makes the size unique: the completion is
the street’s bet size in force, so "raise" means *the smallest legal completion for this decision*
(`e2e-surface.md` §2, D-2, ASM-6). The resolution happens in `apply_action`, by calling
`complete_bet_or_raise_to()` with no argument (`stepping.md` §2); it never happens in the descriptor,
which is why one `"raise"` serves every decision of every hand.

Two things this rules out: a descriptor that grows a `"raise to 8"` variant (an amount in the
vocabulary would put the game’s numbers in the action space, and `features.action_space()` is three
indices for the whole ladder), and a `legal_actions` that lists one descriptor per size (`fold`,
`check-call`, `raise`, `raise-to-8`, …) — the vocabulary is the game’s and is fixed (D-2, D-3).

## 3. What is not a descriptor

Anything else is refused with the contract named (`messages.md` §1, `InvalidAction`): an integer index,
a `pokerkit` operation, a differently-cased spelling (`"Fold"`), a synonym (`"call"`, `"check"`,
`"bet"`), `None`. There is no coercion and no normalisation — a caller that means an action passes one
of the three strings, and a caller that passes an index has confused this module with `features`
(`decode_action` is `features`’ entry point, not this one).
