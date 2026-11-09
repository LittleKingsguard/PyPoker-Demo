# agents — the utility axis at this surface

- **Layer:** L2 · **Module:** `agents` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-09
- **Owner of this file:** D-20's terminal-reward *utility* at the `agents` edge — the fifth catalogue
  `learners()` publishes (§1), the spec's optional selection and the declared default (§2), what a learner
  and a policy carry (§3), the container's field and the three format versions (§4), the four refusals
  (§5), and what the rest of the surface does **not** become (§6) — D-19, D-20, `utilities.md` §2–§7
- **Read with:** `surface.md` §3 (the catalogue record), §4 (`build_learner`), §8 (`save`), §9 (`load`),
  §10 (`as_policy`); `learner.md` §1, §4; `docs/L3/agents/utility.md` (the design), `docs/L3/agents/checkpoint.md` §2.1–§3
- **Ceiling:** 110 lines. At the ceiling, split by owner — never append

This file was split out of `surface.md` when D-20 reached five of its sections at once; `surface.md` keeps
one-line pointers here, so the surface's argument contracts and this axis have one owner each (`surface.md`
§1, D-12, D-13).

## 1. The catalogue: one more key, published between the rule's and `hyper`

`learners()` returns **five** keys in this order — `backends`, `architectures`, `learning_rules`,
`utilities`, `hyper` — and `utilities` holds the terminal-reward catalogue (`e2e-surface.md` §3.3,
`utilities.md` §2, D-20). It is plain data rebuilt on every call, and a caller editing the returned
mapping cannot reach the next call's.

| Utility | `reward` (a stable token, never a sentence) | `normaliser` |
|---|---|---|
| `net-chips` | `net-chip-delta` — the seat's unshaped net chip delta (ASM-12) | `none` |
| `stack-shortfall` | `squared-stack-shortfall-delta` — `(U(s_before) − U(s_after)) / U(s_0)`, `U(s) = (T − s)²` | `U(s_0)` |

- **Three keys per member, and the order is contract.** Each member states its own `name`, its `reward` and
  its `normaliser`; the catalogue's order is the surface because its first member is the declared default
  (`utilities.md` §2, §5, D-20).
- **The first member is `net-chips`, the declared default.** A spec naming no `utility` is built under it,
  and the default is declared here and in `utilities.md` §5 and never inferred from a caller's silence
  (§2, `records.md` §3, D-20).
- **One catalogue, not two copies.** `training` and `evaluation` refuse an unknown name against this call:
  `training` through `declarations.utilities()` and `evaluation` through the same granted arrow, so the names
  this module publishes are the only names either accepts (`module-map.md` §2, D-20).

## 2. `build_learner`'s optional `utility`, and the refusal

- **Optional, and validated before anything is drawn.** `utility` is a `records.md` §3 key of the spec: a
  catalogue name, absent meaning the first member. It is read beside `learning_rule` and **before** a
  parameter is drawn, so a refused name leaves nothing built (`surface.md` §4, `errors.md` §1, D-20).
- **`UnknownUtility`.** A name outside the catalogue — a non-string and an uncarried string alike — raises
  `agents`' own `UnknownUtility` naming `build_learner`, the catalogue's two names and the offending value,
  and the name is never mapped onto the declared default (`errors.md` §3, `utilities.md` §5).
- **Two axes, one build.** The rule and the utility are read from one spec, an axis each; neither is an
  argument of another entry point, and no caller branches on either (`surface.md` §1, `rules.md` §3, D-19,
  D-20).

## 3. What a learner and a policy carry

- **The learner** carries `utility` beside `rule`: the catalogue member whose reward its training target
  carries. Nothing in this module's arithmetic reads it — the reward is the caller's and the transform is
  `training`'s (`utilities.md` §4, D-20).
- **The policy** `as_policy` returns carries `utility` beside `learning_rule`, the two attributes
  `e2e-surface.md` §2 makes part of the policy protocol. `evaluation` reads them to label a table's members,
  so a cell names the objectives that met even when a variant was built in process and no record of it exists
  yet (`surface.md` §10, `rules.md` §7, `utilities.md` §7, D-20).
- **A baseline's policy carries neither.** No rule trained it and no reward was its target, and this module
  invents no attribute a policy did not earn (`surface.md` §11, §12, D-6).
- **Neither attribute changes a decision.** Two policies of one learner at one seed answer the same index
  whatever a report reads off them (`surface.md` §10, `protocol.md` §5).

## 4. The container: format version 3, and the two older versions' reading

- **`metadata.json` gains `utility`, written immediately after `learning_rule`.** The container is **format
  version 3** and `SUPPORTED_VERSIONS` is `(1, 2, 3)` (`docs/L3/agents/checkpoint.md` §2.1, `utilities.md`
  §6, D-19, D-20).
- **Version 3 requires both members.** A missing `utility` is the same "metadata.json without the field"
  refusal a missing `learning_rule` gets, and a `utility` the catalogue does not carry is `UnknownUtility`
  naming the field, the catalogue and the value (`docs/L3/agents/checkpoint.md` §3).
- **Version 2 requires `learning_rule` and must not carry `utility`.** A version-2 container carrying it is
  refused by name, exactly as a version-1 container carrying `learning_rule` is; **version 1** requires
  neither and must carry neither (`docs/L3/agents/checkpoint.md` §3, D-20).
- **A version-1 or version-2 container is read as `net-chips`.** The reading is one assignment beside the
  version-1 `learning_rule` default, so a comparison and a rebuild both see the member the file is read as.
  The 18 containers the repository ships are version 1 and load unchanged as `net-chips`; none is
  regenerated and nothing under `checkpoints/` is rewritten (`utilities.md` §6, ASM-5, `protocol.md` §5).
- **A `load` spec's `utility` is validated then compared.** A disagreement with the file's is
  `CheckpointMismatch` naming both values, mirroring the `learning_rule` and `seed` comparisons
  (`surface.md` §9, `docs/L3/agents/checkpoint.md` §3, D-20).

## 5. The four refusals, side by side

| Where | What is refused | The class |
|---|---|---|
| `build_learner` | a spec's `utility` the catalogue does not carry, or not a string | `UnknownUtility`, naming `build_learner`, the catalogue and the value (`surface.md` §4) |
| `load(path)` | a version-3 container whose `utility` the catalogue does not carry | `UnknownUtility`, naming the field, the catalogue and the value (`surface.md` §9) |
| `load(path)` | a version-1 or version-2 container **carrying** `utility` | the file's form, naming the field and the value (`docs/L3/agents/checkpoint.md` §3) |
| `load(spec)` | a spec's `utility` that disagrees with the file's, or one outside the catalogue | `CheckpointMismatch` naming both values, or `UnknownUtility` naming the spec's (§4) |

A refusal is raised by this module and names the violated contract: no entry point coerces a name onto the
default, drops the field, or repairs a container (`e2e-surface.md` §2, `errors.md` §3).

## 6. What the rest of the surface does **not** become

- **Ten entry points, unchanged.** The utility adds no entry point, renames none, and adds no argument to one
  beyond the spec's own key; the count stays 10 and `modules.json` does not move (D-12, `e2e-surface.md` §1,
  §3.3).
- **`learn`'s terminal branch is not this axis's.** `learn` aims at `record["reward"]` at a terminal
  transition and at the rule's bootstrap elsewhere; the utility changes *what number* the caller places in
  that record, in `training`'s transition step, and never *how* this module learns from it (`utilities.md`
  §4, ASM-12, ASM-25, D-19, D-20).
- **`act`, `param_count` and the container's array are utility-free.** One utility changes the number a
  terminal transition carries and nothing of the state layout, so one architecture reports one count and one
  checkpoint carries one `2·P + M` array under either (`utilities.md` §3, ASM-10, D-20).
- **No value is read for a result.** The catalogue states what a member *delivers*; which utility plays
  better is a measurement recorded in a record and never a claim this surface makes (D-20, `battery.md` §5,
  ASM-29).
