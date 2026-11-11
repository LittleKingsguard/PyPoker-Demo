# RCA: why the learner folds 0 of ~15,000 decisions · 2026-11-07

The claim to test: folding is correct preflop against raisers and is never chosen, so this is an
algorithm failure rather than a game bias. Four candidates were separated by experiment (D-14).
## Eliminated

1. **Not the reward.** A tabular Q-learner with the *same* terminal chip payoff — no counterfactual, no
   shaping — folds **100 %** against a tight aggressor and profits (+0.75 chips/hand).
2. **Not the hand-strength fact.** The same learner with the strength band **removed from its state**
   (street × facing-a-bet only) also folds **100 %**, so no encoding carrying `hand_class` is not what
   blocks folding.
3. **Not the pool.** A two-seat no-limit learner trained with a trained raiser in the pool folds **0 of
   12,856** greedy decisions. The raiser is there and the fold still does not appear.
## What remains, and why it cannot yet be attributed

4. **Sample efficiency vs value bias.** The one live difference is scale: the probe's tabular learner has
   **8 states** and saw 20,000 hands; the product learner has a **329-slot observation, 14,766
   parameters**, and 1,000 hands per seed (~3,000 decisions, ε annealed to 0.05 over 2,000 of them).

   The separating experiment is more hands, and the build refuses it:

   ```
   training.errors.GreedyPassRefused: the run's budget is 20000 hands per variant per seed, so the
   pass would play 20000 hands, and one pass plays at most 2000
   ```

   **Any budget above 2,000 hands is refused**, so the deep run cannot start and data-starvation cannot
   be tested. This is a regression the greedy pass introduced, not a property of the learner.
## Verdict

The zero-fold rate is **not yet attributable**, and the blocking cause is mechanical: the
instrument refuses every budget large enough to test the hypothesis. The evidence points at
8-state learner with 20,000 hands folds at once; a 14,766-parameter learner with 3,000 decisions does
not — which is the algorithm failure the user describes (it cannot learn the strategy at the budget it is
given) rather than a game bias.

Next: lift the cap by **sampling the pass from the run** instead of truncating the run, then re-run this
at 20,000+ hands with the raiser in the pool. If folding appears, budget is the cause; if it does not, the
max operator's overestimation is, and the implemented Double-Q rule is the untried candidate (D-19).
