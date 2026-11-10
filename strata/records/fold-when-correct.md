# Does the learner need counterfactual feedback to fold? · measured 2026-11-07

The user's argument: the model never learns to fold because its reward sees only the chips it
surrenders, not what calling would have cost — the feedback a human gets by seeing the hand out. Tested.

## The test

A tabular Q-learner with **only the terminal chip payoff** — no counterfactual, no opponent model, no
knowledge of what calling would have produced — against a *tight aggressor* that raises only with a
strong hand and folds otherwise, so folding is the correct response to a bet. State = street ×
facing-a-bet × hand-strength band; actions = fold, call, min, pot, all-in, masked by legality; 20,000
hands of ε-greedy training, then a greedy evaluation of 2,000 (D-14).

**Greedy result: fold on 100 % of its decisions, +0.75 chips/hand.** It learned the correct fold from
the ordinary terminal payoff alone.

## Why the inference fails

Folding's value is the loss already committed, which the learner observes directly. Calling's value is
never observed counterfactually, but it need not be: it is **sampled** — the learner calls in similar
states, sees the showdown, and updates `Q(s, call)` from the payoff (D-6). Q-learning's expectation
over futures *is* the counterfactual, estimated by experience rather than read off one deal.

So the missing feedback is real (D-6) — the learner never sees the alternative outcome — but it is
not necessary, and the claim that its absence blocks folding is refuted by the run above.

## Where the argument is right

1. **Efficiency, not possibility** (D-6). Regret-based methods (CFR and its family) use counterfactual
   regret explicitly and are the standard for imperfect-information games precisely because they arrive
   far faster. That is a real and unexplored direction here.
2. **The low fold rate is correct in this game** (D-6). Always-fold loses 0.54 ± 0.06 to a caller and 1.50 ±
   0.02 to a raiser, and the trained agent wins 98.3 % of games against a folder by almost never folding
   (`game-lengths.md`). A 1 % fold rate is the price of a pool whose members fold to *it*.

## What would test the representational question

The probe learner's state carried a hand-strength band; the product's network infers strength from
cards and history instead (D-6). Whether that representation folds selectively is a separate question from the
reward's shape, and it wants a pool where folding is frequently correct — which no member is.
