# agents — the restore's promise

- **Owner:** what `load` promises about a decision (D-16, ASM-5, ASM-20): the loss-free equality stated testably, why
  the file must carry more than the parameters — the shape included — what is free to L4, and where it is asserted
- **Ceiling:** 50 lines. At the ceiling, split by owner — never append
- **Read with:** `checkpoint.md` §1–§3, `backends.md` §3, `utility.md` §7, `shapes.md` §5

## 1. The equality, stated testably

`checkpoint.md` §1 fixes what a restore recovers and §2–§3 the bytes it recovers them from; this document fixes what the
restore then **promises**, in a form a battery can assert. For one learner `L` and any observation and mask of it:

    act(load(spec, path), observation, mask)["action"] == act(L, observation, mask)["action"]
    param_count(load(spec, path)) == param_count(L)
    load(None, path) is a learner of the same kind, settings, representation, backend, rule, utility and shape as L

and, with `pol` and `pol2` the two `as_policy` values at one seed, those policies choose the same descriptor on one
readout — in the shape's own vocabulary — and report one `learning_rule` and one `utility` (`surface.md` §10).

**Why "loss-free" is said of the decision.** Two independent numerical libraries round differently and a checkpoint is
read by whichever one wrote it, so the promise is about the decision — one observation and one mask give one index — and
not about the floats (`backends.md` §3, `learner.md` §2). Every value the update can change is read back unchanged as one
`float64` array, with the target copy, the masks, the position and the counter (`checkpoint.md` §2, §2.1, ASM-10).

## 2. Why the promise needs the file to carry what it does

A decision reads the parameters, the schedule position and the learner's own seed, so a file holding only the parameters
would restore a learner that decides differently as soon as any exploration is in play, and would leave `as_policy`
without the seed it must be handed (`rule.md` §4, §7, ASM-2, ASM-20). The rule and the utility ride for another reason:
no arithmetic here reads them, and a table must still name the population and objectives it measured (`utility.md` §7).

**The shape is carried for both reasons at once, and its absence is a meaning.** An index is decided over `0 .. A−1` of
the learner's shape and `A` is the head the layout is rebuilt on, so a restore that lost the shape would scatter a saved
six-index head into a three-wide model — refused by the check `checkpoint.md` §3 already makes on `params.count`, now
against `A` (`shapes.md` §2–§3). A version-1-to-3 container needs **no** `game`, its absence already meaning the default
shape for the one game those writers had; a version-4 one **must** name it (`shapes.md` §5, ASM-40, D-19, D-29).

## 3. What is left to L4

The compression method's default, the JSON's key order and an `indent`, and the helper that flattens the array and the
one that scatters it back — `_read_metadata` excepted (`rule.md` §8). Not L4's: the two member names, the container, the
version rules, §2.1's field names and their order, §1's equality and §2's reasons (`guardrails.md` G11–G13).

## 4. Where the equality is asserted

`tests/agents/test_checkpoint.py` AGT-7.2 (the round trip keeps the decision), AGT-7.14 (the container records the rule
and the utility), AGT-7.15 (a version-1 container is read as the defaults) and AGT-7.17 (the shipped set loads from its
path alone); `tests/agents/test_utility.py` AGT-15.5; `tests/e2e/test_fam12_checkpoints.py` FAM-12.2. The shape's halves
— a version-4 member round-tripping its `game`, a version-4 default-shape refusal, a contradicting spec — are the unit
battery's to add, and a case that disagrees with this design is a finding, never a file to edit (`battery.md` §2).
