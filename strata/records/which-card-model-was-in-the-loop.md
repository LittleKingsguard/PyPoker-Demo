# Which card model the policy used — and the attribution error that follows · measured 2026-11-08

The user asked for the **less-converged, better-midrange** model rather than the overfitted 400-epoch one. Verified from
the artefacts: **that is already what every policy run used.**

| artefact | recorded source |
|---|---|
| the strength-arm checkpoint | `seeding = {source: 'attn-60', rows: 'cards', digest: b6a7e090c6cc7bd6}` |
| every probe that drove a policy (`.probe/deep_integration.py`, `dilution_test.py`, `equal_budget.py`, `fold_behaviour.py`, `isolate.py`, `league_integration.py`) | `torch.load('.probe/attn60.pt')` |
| the 400-epoch model | used **only** in the card-model battery (`battery400.py`) — never behind a policy |

## The two models on the battery states

| state | truth | **attn-60** (in the loop) | attn-400 (not used) |
|---|---|---|---|
| quad aces | 100.0 % | **93.6 %** | 99.7 % |
| nut flush | 100.0 % | **99.7 %** | 99.6 % |
| ace-high straight | 97.8 % | **63.9 %** | **11.2 %** |
| trip aces | 91.8 % | **70.6 %** | **2.7 %** |
| pair of kings | 45.1 % | 12.0 % | 28.0 % |
| 2-3 junk / 2-7 junk | 0.0 % | 0.0 / 0.1 % | 0.0 / 0.0 % |

**attn-60 does rank hands**, roughly and with compression: locks at 93–100 %, trip aces 71 %, a dry pair of kings 12 %,
junk ~0 %. It is a usable ordering, not a lock detector.

## The attribution error this corrects

**D-116 said the policy's failure to rank hands was "the card model's binary-target defect arriving in the policy",
citing D-95's 2.7 % for trip aces.** That citation was wrong: **the policy was fed attn-60, which predicts trip aces at
70.6 %**, not the 400-epoch model's 2.7 %. So the input the policy received *did* distinguish quads from trip aces from
kings from junk — and the policy still played **quads and 2-3 offsuit identically**.

**The corrected conclusion is stronger, not weaker:** the failure is **in the policy's use of the signal**, not in the
signal's quality. A policy handed a monotone-ish ordering and producing a flat or inverted response is a
**credit-assignment** failure (D-84), not an input-quality failure — which is also why the strength input has never
helped at any budget (D-104, D-109) and why D-115's one distinction was keyed to a single hand shape rather than to the
ranking it was given.

**And it keeps D-95 alive as a separate result**: the 400-epoch model *is* a lock detector, it simply never drove a
policy. Its record stands as a card-model finding; it must not be cited as an explanation of policy behaviour.
