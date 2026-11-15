# The cross-condition check failed, and it exposed an era-mixing error · measured 2026-11-08

D-68's remaining question was whether the folding result holds across opposition. The cross-condition replay gave
numbers that **contradict the recorded censuses** — `short-tok-s0` folded **0 %** of 460 decisions where its own
greedy pass recorded **91.8 %** — so the harness was tested before any conclusion was drawn (D-14).
## What the test found

The same checkpoint, same table, two seed ranges, three repeats: `short-tok-s0` played **raise-half on 400 of 400
decisions** every time. Earlier tonight the same file, same table, same seeds folded on **every** decision. The
file did not change; **the code did**.

D-61 added the **bounded embedding** — `row = (1 + tanh θ)/2` — applied at forward time to every token model. A
checkpoint trained before that change is now read through a different function, so it computes different values
and therefore plays a different policy. Every token checkpoint in `/tmp/token-shortfall`,
`/tmp/token-shortfall-seeds36`, `/tmp/token-build` and `/tmp/token-dq` is **pre-squash**, and none of them can be
evaluated meaningfully today.
## What survives, and what does not

**Survives — D-68's token findings**, because they were measured on the `norm-*` models, which were **trained and
evaluated after the squash** and are therefore internally consistent: the nine token runs are one policy reported
nine times, and that policy folds whenever folding is legal on its pool.

**Does not survive as current measurement — every recorded token census from before D-61**, including D-53's
92.7 %, D-56's seven-seed table and D-63's grid. Those numbers were correct **in their era** and remain true
statements about models that no longer exist; they cannot be reproduced by loading the same files today.

**Invalid — my cross-condition table** in this pass: it mixed eras, evaluating pre-squash checkpoints through the
post-squash forward pass, so its `short-*` rows measure nothing.
## What it takes to close D-68 properly

A **post-squash stack-shortfall token model** — one cell, three seeds, the standard configuration — and then the
cross-condition test against the `norm-*` models, all in one era. Until that exists, the conditionality claim
rests on `norm-tok` alone (100 % fold-when-legal on the census pool against 100 % on the passive table in the one
cell measured), which is not a contrast.

The wider lesson: **changing a forward pass silently reinterprets every stored token model**, so a representation
change must declare the era of the containers it invalidates. D-61 declared the dense family comparable — which
the encoder dump proved — but not this, and this is the cost of that omission.
