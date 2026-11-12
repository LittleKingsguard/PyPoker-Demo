# agents — the restore's promise

- **Owner:** what `load` promises about a decision (D-16, ASM-5, ASM-20, D-43): the loss-free equality stated testably,
  why the file must carry more than the parameters — the shape and the counterfactual member included — and what is L4's
- **Ceiling:** 50 lines. At the ceiling, split by owner — never append
- **Rev:** 2 · **Date:** 2026-11-11 — D-43: the member rides in a version-5 required field (§2)
- **Read with:** `checkpoint.md` §1–§3, `backends.md` §3, `rule.md` §3, §7, `utility.md` §7, `shapes.md` §5

## 1. The equality, stated testably

`checkpoint.md` §1 fixes what a restore recovers and §2–§3 the bytes it recovers them from; this fixes what the restore
then **promises**, in a form a battery can assert. For one learner `L`, any observation and mask of it:

    act(load(spec, path), observation, mask)["action"] == act(L, observation, mask)["action"]
    param_count(load(spec, path)) == param_count(L)
    load(None, path) is a learner of the same kind, settings, representation, backend, rule, utility, member and shape as L

and the two `as_policy` values at one seed choose one descriptor on one readout, in the shape's own vocabulary, and
report one `learning_rule`, one `utility` and one `counterfactual` (`surface.md` §10).

**Why "loss-free" is said of the decision.** Two numerical libraries round differently and a checkpoint is read by
whichever one wrote it, so the promise is about the decision — one observation and one mask give one index — and not the
floats (`backends.md` §3). Every value the update can change is read back unchanged as one `float64` array, with the target
copy, the masks, the position and the counter (`checkpoint.md` §2, ASM-10) restored where it was left.

## 2. Why the promise needs the file to carry what it does

A decision reads the parameters, the schedule position and the learner's own seed, so a file holding only the parameters
would restore a learner that decides differently as soon as exploration is in play, and would leave `as_policy` without
the seed it must be handed (`rule.md` §4, §7, ASM-2, ASM-20). The rule, the utility and the counterfactual member ride for
another reason: no arithmetic here reads them, and a table must still name the population, the objectives and the
estimator it measured (`utility.md` §7, `counterfactual.md` §6).

**The shape is carried for both reasons at once, and its absence is a meaning.** An index is decided over `0 .. A−1` of
the learner's shape and `A` is the head the layout is rebuilt on, so a restore that lost the shape would scatter a saved
six-index head into a three-wide model — refused by the check `checkpoint.md` §3 makes on `params.count`. A version-1-to-3
container needs **no** `game`, its absence meaning the default shape; a version-4 one **must** name it, and a version-5
one carries it exactly when its shape is not the default (`shapes.md` §2–§3, §5).

**The member is a format version, and its absence is a reading too.** A learner under a member other than `none` writes
version **5** with a **required** `counterfactual` field, because a restored learner must be able to say what its targets
came from. A learner under `none` writes the version it always wrote and carries **no** field, so its two members stay
byte-identical — so a version-1-to-4 container is read as `none`, and one carrying the field is refused (`§3`, D-43).

## 3. What is left to L4, and where the equality is asserted

The compression method's default, the JSON's key order and an `indent`, and the helper that flattens the array and the one
that scatters it back — `_read_metadata` excepted (`rule.md` §8). Not L4's: the member names, the container, the version
rules, §2.1's field names and their order, §1's equality and §2's reasons (G11–G13). `test_checkpoint.py` AGT-7.2 and
`test_counterfactual.py` AGT-18.9 hold the round trip, AGT-7.14–7.17 the recorded members, FAM-12.2 the end-to-end pair.
