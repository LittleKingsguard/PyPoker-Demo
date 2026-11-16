# Wiring the supervised embeddings into the policy: no effect, and the reason is decisive · 2026-11-08

D-92's integration, first half: the supervised card model's **learned embedding rows** (ids 1–52, 50 dimensions
each, taken from `.probe/attn60.pt`) copied into the token table of a freshly trained product policy learner
(`R3`, six seats, `stack-shortfall`, 5,000 hands, token layout 102 × 50), then scored on the loaded-deal suite
(D-14).

| embedding table | distinct decisions over AA, KQs, 22, 87s, 72o |
|---|---|
| **the policy's own** (trained) | **1 / 5** — every hand `raise-quarter` / `raise-quarter` |
| **the supervised model's** | **1 / 5** — every hand `raise-quarter` / `raise-quarter` |

**Identical.** The copy is exact (52 rows × 50 dimensions, in the right ids) and changes nothing observable,
because **the policy is a constant function of its input** (D-82: every token policy measured so far plays one action
for every hand, at both seats and at 5,000 and 15,000 hands).

## Why a better representation cannot rescue it

The policy's decision ignores the observation. Replacing the *meaning* of the input cannot change a decision rule
that does not read the input — which is exactly the two-layer picture D-84 established:

| layer | status |
|---|---|
| representation | **not** the binding limit — the supervised model reaches 32.4 % of outcome variance with these very embeddings |
| credit assignment | **the binding limit** — no reward, exploration, estimator, schedule or representation change has produced a policy that separates aces from seven-deuce |

So copying the embedding in is **necessary but nowhere near sufficient**: it makes the input *informative* and leaves
the decision *blind*.

## What the other half would take

**The predicted strength as an input** needs a layout slot: the six-seat observation is 122 token ids (vocabulary
102) and the dense layout is 433 slots, all fully allocated — a continuous strength value needs a **tenth fact** or an
extra token band, which is the surface change D-61 measured the cost of and which needs the gate (D-10) and the
three pinned catalogue assertions (D-76).

And by the same argument as above, feeding the strength in will not by itself fix the policy: a constant decision
rule fed a perfect probability still ignores it. **The wiring is worth doing only alongside the credit-assignment
fix** — a supervised auxiliary target or an exploration regime that keeps the other actions sampled (D-72).
