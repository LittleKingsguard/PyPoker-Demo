# agents — the utility catalogue

- **Owner:** the terminal-reward catalogue (D-20, ASM-12, ASM-28): the two members and what each declares, the
  declared default, the one contract both answer, the arithmetic's exact numbers, where the transform is applied
  and where it is not, what a learner and a policy carry, and the `UnknownUtility` refusal
- **Ceiling:** 155 lines. At the ceiling, split by owner — never append
- **Read with:** `rule.md` §1–§3, §7, `checkpoint.md` §2.1–§3, `errors.md` §2–§4, `README.md` §5

## 1. Why the reward is a second parameter

The terminal reward was one constant for the whole ladder: the seat's unshaped net chip delta, placed at that
seat's terminal decision and shaped nowhere (ASM-12). D-20 makes it a **catalogue** a variant selects from,
exactly as D-19 makes the learning rule one, and for a measured reason — raise and call are EV-neutral in the
fixed game, so a max operator over three noisy estimates takes whichever action drew positive noise, and the
ladder's models converged on raise-almost-always at ±20 where ±2 paid the same (D-19, D-20). The second member scores
progress in the square of the stack's shortfall from all the chips in play, so a loss of a given size costs more than a
win of the same size pays (D-20, ASM-28).

**It is a change of preference among equal-EV options and not a change of the game** (D-2, D-20): it creates no
expectation the game does not have, and a model trained under it is not thereby a stronger player — `battery.md` §5
refuses that reading and `utilities.md` §9 states what a table may not say (D-20, ASM-29).

## 2. The catalogue

`learners()["utilities"]` publishes exactly two members, in this order, each a record of exactly three keys — its
`name`, the `reward` it delivers as a stable token and never a sentence, and the `normaliser` that reward is
divided by (`e2e-surface.md` §3.3, `utilities.md` §2, ASM-28):

| Utility | `reward` | `normaliser` | The reward it delivers at the terminal decision |
|---|---|---|---|
| `net-chips` | `net-chip-delta` | `none` | the seat's net chip delta for the completed hand, unshaped (ASM-12) |
| `stack-shortfall` | `squared-stack-shortfall-delta` | `U(s_0)` | `(U(s_before) − U(s_after)) / U(s_0)`, with `U(s) = (T − s)²` (§5) |

The token is the catalogue's own description of what a member delivers, and another module keys its arithmetic by
it — `training`'s transition step selects on `reward` and not on the member's name — so no name is copied out of
a document (`utilities.md` §2, §4). The table is `declarations.UTILITIES` in `src/agents/declarations.py`, a
module-level table whose key order **is** the declared order, and `catalogue()` rebuilds a fresh mapping from it
on every `learners()` call, so no caller can mutate the catalogue through a returned record (`README.md` §5).

## 3. The declared default, and where a utility is named

`DEFAULT_UTILITY = next(iter(UTILITIES))` — the catalogue's **first** member, `net-chips`, derived from that order
so the declaration cannot drift from the table (ASM-28, `utilities.md` §5). A learner spec that names no `utility`
is built under it, and the default is **declared here and in `records.md` §3** and never inferred from the
caller's silence (D-20, `records.md` §3, `learner.py`'s `build_learner`).

`utility` is an **optional** key of a learner spec, beside `learning_rule` (`records.md` §3), and it is one of the
five places a utility is named: a variant entry's `utility` (`records.md` §2), the learner spec's, the
checkpoint's field (`checkpoint.md` §2.1), a pool member's (`records.md` §7) and the attribute a policy built from
a learner carries (§7). They agree wherever a place names one; a place that names none is the declared default and
not a second value, and no entry point substitutes one (`e2e-surface.md` §2, `utilities.md` §5, D-20).

## 4. The one contract both answer

Whatever its utility, a learner is one object built by `build_learner` and answers the same calls with the same
shapes: the two utilities are **one capacity** — one state layout, one `param_count`, one `2·P + M` checkpoint
array — because a utility changes the number a terminal transition carries and nothing of the state, so ASM-10's
±2% budget match holds under either (`utilities.md` §3, ASM-10, D-20).

The reward is **terminal only**: every non-terminal decision carries `0.0`, `learn`'s terminal branch stays
`target = record["reward"]` and its non-terminal branch stays the rule's, so the utility decides what a terminal
transition is worth while the rule decides how a non-terminal one is bootstrapped and neither reads the other
(ASM-12, ASM-28, `rule.md` §2, D-19, D-20). `utility` is consequently read by **no arithmetic in `learner.py`**:
`act`, `learn`, `param_count`, `as_policy`, `save` and `load` carry it and none branches on it, so no caller
branches on a utility to learn either (D-19, D-20, `rule.md` §3).

A utility is never an argument of `learn`: accepting one there would make the record `learn` admits depend on
which utility its learner carries — an interface difference between catalogue members that ASM-25 refuses for the
rules (ASM-25, `utilities.md` §3, D-20).

## 5. The `stack-shortfall` arithmetic, exactly

With `T` the total chips in play, `s` one seat's stack, `s_0` the stack a hand begins from and `delta` the seat's
net chip delta for the completed hand (ASM-12, ASM-6):

    U(s)      = (T − s)²
    r         = (U(s_before) − U(s_after)) / U(s_0)
    s_before  = s_0
    s_after   = s_0 + delta

`T` is `40` at every hand of the fixed game, since two seats begin every hand at `s_0 = 20` chips (D-2, ASM-6), so
the normaliser is `U(s_0) = (40 − 20)² = 400`. The four scores D-20 fixes:

| Hand | `delta` | `s_after` | `U(s_after)` | `r` |
|---|---|---|---|---|
| a ±2 win | `+2` | 22 | 324 | **+0.190** |
| a ±2 loss | `−2` | 18 | 484 | **−0.210** |
| an all-in win | `+20` | 40 | 0 | **+1.000** |
| an all-in loss | `−20` | 0 | 1600 | **−3.000** |

So a loss of a given size is always penalised more than a win of the same size rewards, and an all-in is penalised
threefold (D-20, ASM-28, `utilities.md` §2). The normaliser is the shortfall a hand begins with, which is what
keeps the objective on the scale the learner was tuned for; a hand whose normaliser would not be the game's own is
refused by name **where the transform is applied** (§6, `utilities.md` §4, ASM-28).

## 6. Where the transform is applied, and where it is not

The transform is applied in **`training`'s transition step** — the step that turns one hand's decisions into the
batch `learn` consumes — and **not here** (`utilities.md` §4, ASM-28). Three reasons, in the order they bind: the
utility needs the **hand**, `s_before`, `s_after` and `T`, while `learn` is handed one decision and its successor
with nothing that delimits an episode (`records.md` §4); the reward is the **engine's** fact before it is the
learner's, `engine.play_hand` placing the hand's net chip delta at the seat's terminal decision, so the transform
re-expresses a number already computed rather than adding a second outcome (ASM-12, `records.md` §5); and a reward
transform inside `learn` would put two axes into one arithmetic, so a curve could no longer say which of them moved
it (D-19, D-20).

`agents` still owns the **identity** — this catalogue, the spec's selection, the refusal of an unknown name and the
container's field — because a pool certifies what a member is, and a learner that cannot say which utility it was
trained under cannot be certified whatever arithmetic produced its numbers (`utilities.md` §7, §8, ASM-27). The
split leaves one risk, stated rather than hidden: a caller that builds its own transition records gets the reward it
wrote, because the reward in a record is the caller's — and the loop is the only caller (`records.md` §4, D-13).

## 7. What a learner and a policy carry

A `Learner` holds `utility` beside `rule`: the catalogue member whose reward its training target carries, and the
member it learns under, both fixed at construction, both in its `__slots__` and both in its `__repr__`, and both
written by every checkpoint it writes (`learner.py`, `checkpoint.md` §2.1, D-19, D-20). A `Policy` built by
`as_policy` carries `utility` beside `learning_rule` and reports both: they are the only things it holds that no
decision reads, and `evaluation` reads them to label a table's members, so a table names the objectives and the
population it measured even when a variant was built in process and no record of it exists yet
(`e2e-surface.md` §2, `utilities.md` §7, ASM-29). `load` restores the learner under the utility its container
records, so `evaluation.policy_from`'s playback needs nothing new — it is utility-free and reports the member the
file names (ASM-20, `checkpoint.md` §3).

## 8. The `UnknownUtility` refusals

`errors.py`'s `UnknownUtility` is the refusal of every place a utility name is declared — `build_learner` and
`load`, in a spec and in a variant entry alike — and it is raised before anything is built or restored
(`errors.md` §2, §4). A name outside the catalogue is refused **by name** and is never mapped onto the declared
default, because a silent substitution would train a model on a reward its spec does not name (`errors.md` §3,
`utilities.md` §5, D-20):

    build_learner(spec): 'utility' must be one of ('net-chips', 'stack-shortfall'), got 'sharpe'
    load(spec): 'utility' must be one of ('net-chips', 'stack-shortfall'), got 'sharpe'
    load(path): '<path>' records the field 'utility', which must be one of ('net-chips', 'stack-shortfall'), got 'sharpe'
    load(spec): the spec's utility 'net-chips' is not the checkpoint's utility 'stack-shortfall'

The first two are `learner.utility(value, entry)`'s message, the third `checkpoint._declared`'s and the fourth
`checkpoint._compare`'s `CheckpointMismatch`: a spec's `utility` is **validated against the catalogue before it is
compared**, and a disagreement names both values as a `seed`'s does (`checkpoint.md` §3, ASM-20, D-20). Every one
names the entry point, the key at fault and the offending value, the grammar `errors.md` §3 fixes.

## 9. What is left to L4

The private helper that reads one name beyond its spelling, the wrapping of §8's four messages, and where the two
names sit inside a refusal beyond the order above. Not L4's: `declarations.UTILITIES` and its order, §3's
`DEFAULT_UTILITY` derivation, §2's three keys, §5's arithmetic and its four scores, §4's terminal-only rule, §6's
placement of the transform, §7's two carried fields and §8's four message shapes (`guardrails.md` G17).
