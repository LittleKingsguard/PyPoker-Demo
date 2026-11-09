# agents — the restore's promise

- **Owner:** what `load` promises about a decision (D-16, ASM-5, ASM-20): the loss-free equality stated testably,
  why the file must carry more than the parameters, what is free to L4 on this path, and where the promise is asserted
- **Ceiling:** 50 lines. At the ceiling, split by owner — never append
- **Read with:** `checkpoint.md` §1–§3, `backends.md` §3, `utility.md` §7

## 1. The equality, stated testably

`checkpoint.md` §1 fixes what a restore recovers and §2–§3 the bytes it recovers them from; this document fixes what
the restore then **promises**, in a form a battery can assert. For one learner `L`, its saved file `save(L, path)`,
and any observation and mask of `L`'s family:

    act(load(spec, path), observation, mask)["action"] == act(L, observation, mask)["action"]
    param_count(load(spec, path)) == param_count(L)
    load(None, path) is a learner of the same kind, settings, representation, backend, rule and utility as L

and, with `pol = as_policy(L, encoder, seed)` and `pol2 = as_policy(load(None, path), encoder, seed)`, the two
policies choose the same descriptor on one readout and report one `learning_rule` and one `utility`
(`surface.md` §10, `utility.md` §7, ASM-5).

**Why "loss-free" is said of the decision.** Two independent numerical libraries round differently and a checkpoint
is read by whichever one wrote it, so the promise is about the decision — one observation and one mask give one
index — and not about the floats (`backends.md` §3, `learner.md` §2). Equal parameters at equal state are the
mechanism: every value the update can change is written and read back as one `float64` array unchanged, and the
target copy, the masks, the position and the counter ride with it (`checkpoint.md` §2, §2.1, ASM-10).

## 2. Why the promise needs the file to carry what it does

A decision reads the parameters, the schedule position and the learner's own seed, so a file holding only the
parameters would restore a learner that decides differently as soon as any exploration is in play, and would leave
`as_policy` without the seed it must be handed (`rule.md` §4, §7, ASM-2, ASM-20). The two catalogue members are
carried for another reason: no arithmetic here reads them, and a table still has to name the population and the
objectives it measured, which a member restored from a path alone could not otherwise declare (`utility.md` §7,
`rules.md` §6, D-19, D-20).

## 3. What is left to L4

The compression method's default, the JSON's key order and an `indent`, and the helper that flattens the array and the
one that scatters it back — `_read_metadata` excepted (`rule.md` §8). Not L4's: the two member names, the container,
the version rules, `checkpoint.md` §2.1's field names and their order, the array's three sections, §1's equality and
§2's reasons (`checkpoint.md` §2–§3, `guardrails.md` G11–G13).

## 4. Where the equality is asserted

`tests/agents/test_checkpoint.py` AGT-7.2 (the round trip keeps the decision), AGT-7.14 (the container records the
rule and the utility), AGT-7.15 (a version-1 container is read as the two defaults) and AGT-7.17 (the shipped set
loads from its path alone); `tests/agents/test_utility.py` AGT-15.5 (a version-3 member round-trips its utility);
`tests/e2e/test_fam12_checkpoints.py` FAM-12.2 and `tests/e2e/test_fam18_utilities.py` FAM-18.4. A case that disagrees
with this design is a finding against the design or the case, never a file to edit (`battery.md` §2).
