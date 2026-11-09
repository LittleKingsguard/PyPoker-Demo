# training — the terminal reward, and the one place a utility is applied

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-09
- **Owner:** the utility axis this module applies — where the transform sits and why (§1), the catalogue's **reward token** as the
  selector and never a member name copied here (§2), the two arithmetics and the four scores (§3), the chips-in-play guard and the
  class it raises (§4), what every other decision keeps and what this module never touches (§5), and what is left to L4 (§6);
  D-20, `utilities.md` §2–§5, `records.md` §4–§5, ASM-12, ASM-28
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append
- **Read with:** `episode.md` §3–§6, `loop.md` §1 steps 3 and 6, §4, `fairness.md` §4, `errors.md` §2, §4, `guardrails.md` G25

## 1. This module is the one place a utility is applied

`_transitions(episode, seat, encoder, utility=None)` is the step that turns one hand's decisions into the batch `agents.learn`
consumes, and its fourth argument is the **name** of the utility the variant is trained on (`episode.md` §3, `loop.md` §1 step 6).
At the seat's **terminal** decision — the last decision that seat made, positionally (`episode.md` §4) — and only there, the
transform replaces the record's `reward` with the number that utility delivers. Every other decision keeps the `0.0` the episode
placed (`records.md` §4, §5, ASM-12, D-20).

Three facts fix *why* the transform is here and not in `learner.py` (D-20, `utilities.md` §4):

- the utility needs the **hand**, not a decision: `s_before`, `s_after` and `T` are facts of a completed hand, while `agents.learn`
  is handed one decision and its successor with nothing that delimits an episode (ASM-25, `records.md` §4);
- the reward is the **environment's** fact before it is the learner's: `engine.play_hand` places the hand's net chip delta and no
  shaped term, so the transform re-expresses a number the engine already computed rather than adding a second outcome (ASM-12, D-2);
- the TD bootstrap stays the rule's business, so two axes never share one arithmetic and a curve can still say which of them moved
  it (D-19, D-20).

**No arithmetic in `src/agents/learner.py` is touched by any of it**: its terminal branch stays `target = record["reward"]` and its
non-terminal branch stays the rule's `target = record["reward"] + discount * bootstrap`, so the utility decides what a terminal transition
is worth while the rule decides how a non-terminal one is bootstrapped, and neither reads the other. The learner carries the utility's
**name** — `agents.build_learner` selects it and refuses an unknown one, and the learner stores it as `self.utility` — and reads no
arithmetic from it (`utilities.md` §3, §4, D-19, D-20).

## 2. The arithmetic is selected by the catalogue's reward token, never by a member name

    _reward_token(utility)       -> (name, token)       # the member's reward token, or ConfigurationInvalid
    _reward_function(utility)    -> (name, arithmetic)  # the callable the token names, or ConfigurationInvalid
    REWARDS                      -> {"net-chip-delta": <delta>, "squared-stack-shortfall-delta": <shortfall delta>}

The catalogue `agents.learners()["utilities"]` is the only source of a member's reward, so the arithmetic is keyed by the **token**
the member states for itself and never by a member name transcribed into this module (D-20, `utilities.md` §2). `_reward_token`
resolves its argument — `None` meaning the catalogue's first member, the declared default of `utilities.md` §5 — and returns the
member's `reward` string; a name the catalogue does not carry, or a member whose `reward` is not a string, is
`ConfigurationInvalid` naming the utility and every name the catalogue does carry. `_reward_function` then looks the token up in
`REWARDS`, and a token no arithmetic here names is a reward this module cannot deliver: it is refused by name, **never defaulted
to the net chip delta** (`utilities.md` §4, §5, D-20).

No member name is spelled in the arithmetic itself: `net-chips` and `stack-shortfall` are names this document states because a
reader needs them, and the code reaches either only through the token the catalogue publishes. That is D-19's precedent applied to
the second axis — a catalogue member is a parameter, and this module reads the catalogue rather than a private copy of it
(`rules.md` §2, §4, `utilities.md` §2, D-19, D-20).

## 3. The two arithmetics, and the four scores

    r = delta                                  # net-chip-delta
    r = (U(s_before) − U(s_after)) / U(s_0)    # squared-stack-shortfall-delta
    U(s) = (T − s)²

Under `net-chips` the terminal reward is `delta` — the decision's own `reward`, the seat's net chip delta for the completed hand,
unnormalised and unshaped (ASM-12). Under `stack-shortfall` it is the shortfall delta normalised by the shortfall a hand begins
with, where `s_before = s_0` is the stack a hand is dealt from, `s_after = s_0 + delta`, and `delta` is the decision's own
`reward`, the hand's net chip delta for that seat (D-20, ASM-6, ASM-28).

Both quantities the transform needs are read and never assumed (`utilities.md` §4, ASM-28):

- `s_0` is `engine.game_config()["starting_stack"]`, the stack the fixed game deals every hand from — **20** (D-2, ASM-6);
- `T` is `sum(readout["stacks"]) + readout["pot"]` at the decision, the pot being un-awarded and the chips conserved, so the two
  seats' stacks and the pot together are all the chips the hand holds — **40 at every decision of the fixed game** (§4, ASM-6).

At the fixed game the four scores are therefore exact, and they are the arithmetic D-20 chose this utility for (D-20, ASM-28):

| `delta` | `U(s_0) = (40 − 20)²` | `U(s_after)` | `r` |
|---|---|---|---|
| `+2` | 400 | `(40 − 22)² = 324` | **+0.190** |
| `−2` | 400 | `(40 − 18)² = 484` | **−0.210** |
| `+20` | 400 | `(40 − 40)² = 0` | **+1.000** |
| `−20` | 400 | `(40 − 0)² = 1600` | **−3.000** |

So a loss of a given size always costs more than a win of the same size pays, and all-in aggression is penalised threefold. The
asymmetry is arithmetic and no claim about play: it prefers the cheaper variance among equal-EV options and makes no model stronger
(D-20, `utilities.md` §2, §9).

## 4. The chips-in-play guard, and the class its refusals carry

    _chips_in_play(decision, seed, seat) -> (total, starting_stack)   # T and s_0, or ChipConservationBroken

`T` is read from one decision's readout and checked against the stacks the game declares: it must equal
`engine.game_config()["seats"] × starting_stack`, or the hand is refused by name with **the hand's seed and both totals**, because a
normaliser that is not the game's own would make one reward incommensurable with the next (ASM-6, ASM-28, `utilities.md` §4).

Both refusals are `errors.ChipConservationBroken`, a `training` class and not a called module's (`errors.md` §2):

- the hand's total disagrees with the stacks the game declares — the message names the seed, the seat, the total, the seat count,
  the starting stack and the declared total;
- `U(s_0)` is `0`, so the normaliser is undefined — the message names the seed.

The guard is reached only by the arithmetic that needs the readout at all: `net-chips` reads the decision's own `reward` and nothing
else, so a hand it scores is never measured for conservation (`utilities.md` §2, §4, ASM-12).

## 5. What every other decision keeps, and what is never done here

- **`terminal` stays positional**: the transform touches exactly one transition per hand — the last decision that seat made — and
  the flag is never inferred from the reward (`episode.md` §4, `records.md` §5). A split pot pays `0.0` and scores `0.0` under
  either arithmetic, and that is a normal terminal transition rather than a missed one.
- **Every non-terminal decision keeps `0.0`**, the value the episode placed there, so no intermediate term and no shaping enters
  the reward (ASM-12, D-20).
- **The transform runs once per hand, before the batch reaches `agents.learn`** (`loop.md` §1 step 6), and it reads the episode's
  record alone: it keeps no state between hands and writes nothing (`records.md` §4, D-13).

## 6. What is left to L4

Whether `REWARDS` is a mapping or a match, whether the member's name is discarded before or after the token's lookup, how the four
quantities are named inside the arithmetic, and the internals of `_shortfall`, `_net_chips`, `_stack_shortfall` and
`_chips_in_play`. Not L4's: the transform's location and its terminal-only delivery, the selection by reward token, both arithmetics
and the four scores, the guard's two refusals and the class both carry, `0.0` at every non-terminal decision, and the untouched
`learner.py` branches (`guardrails.md` G25, `utilities.md` §4, D-20). `_reward_token`, `_reward_function` and `REWARDS` are
contract for `tests/training/`, as is `_transitions`' fourth argument (`README.md` §4).
