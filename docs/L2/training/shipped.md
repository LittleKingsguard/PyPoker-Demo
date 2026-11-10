# training — the checkpoints that ship, and the window they are

- **Layer:** L2 · **Module:** `training` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-09
- **Owner of this file:** the shipped `checkpoints/` set as an integration fact — what ships, what a run writes and where,
  what a window is, and what a loaded version chooses — split out of `loop.md` §7 at that file's ceiling, with the
  numbering kept (D-16, ASM-5, ASM-18, `protocol.md` §5)
- **Reads:** `loop.md` §1, §3; `write-root.md` §1–§6; `docs/L3/training/checkpoints.md` §1–§5; `records.md` §7–§8, §12
- **Ceiling:** 40 lines. At the ceiling, split by owner — never append

## 7. The checkpoints that ship, and the window they are (D-16, ASM-18)

- `checkpoints/` is the tree a run writes its ten snapshots and its final model per variant × seed under, and the one
  whose **shipped** set the repository carries: the window's last five per seed plus each seed's final, 18 for R1's three
  seeds against the 33 a run writes, the pool being a view over that shipped window (ASM-18, D-16, `protocol.md` §5, `records.md` §12, `module-map.md` §5).
- **A run writes under the write root and reads under the declared root.** With `PYPOKER_CHECKPOINT_ROOT` unset the two
  are `<repo>/checkpoints` and nothing changes; set, a run writes the same layout elsewhere while the index, the declared
  windows and `layout._resolve` still read from the repository root (`write-root.md` §1–§3, §6, `protocol.md` §5).
- **What ships is the retained set plus each rung variant's final model per seed** (ASM-5 as D-16 amends it,
  `protocol.md` §5): the nine variants of `loop.md` §1 across three seeds' finals, and for each of R2–R6 the five-version
  window its successor inherits. Nothing else ships and each artefact ships once (`battery.md` §3 FAM-12).
- **The greedy pass reads the model, and adds no artefact.** It is played after the pair's final model is written and it
  writes nothing at all: its block is the record's, its decisions are the run's only retained stream, and no snapshot,
  final or container changes because of it (`docs/L3/training/greedy.md` §1, `sizing.md` §4, ASM-38, D-29).
- **A window is a declaration of `records.md` §7 versions in lineage order.** Within a run snapshot *k+1* descends
  from *k*; a seed's first descends from the last version the run wrote before it and the run's first from its rung's
  own start; the three seeds' windows lie end to end in the recorded seed set's order, so they are one chain (`loop.md` §7).
- **A declaration richer than the bound is windowed, not refused**: a rung's declaration may name more versions than M and the frozen pool holds the newest M of them, which is how a run's ten snapshots become a five-version window (`league.md` §2, `records.md` §8, `evaluation/surface.md` §5).
- **A loaded checkpoint chooses the action its learner chose** on the same readout — which is what makes a shipped
  version a league member — and it is played in evaluation mode and never updated (ASM-5, `protocol.md` §5, `evaluation/surface.md` §12). It plays the shape its container records, so a version-1-to-3 container is the default shape's and a version-4 one names its own (`shapes.md` §3, §5, `sizing.md` §6, D-29).
- **A lineage checkpoint the repository does not carry leaves the pool at the pinned baselines and whatever versions are
  present**, and the record states the membership it used; the index lists no artefact twice and never scans a scratch directory (`protocol.md` §5, `surface.md` §7, FAM-12).
