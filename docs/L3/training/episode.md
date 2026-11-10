# training — one episode into transitions

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 4 · **Date:** 2026-11-09
- **Owner:** how one `engine.play_hand` episode becomes `records.md` §4 transitions for the learner's seat — the seat alternation (§1), the assembled policy and the vocabulary it decodes in (§2), the decision ordering, the index and the run's own chips in play (§3), `reward` and `next_legal` (§4), and the one batch per hand handed to `agents.learn` (§5); **Rev 2** counts the five granted `agents` calls, `learners()` included (D-19); **Rev 3** states that this step is the one place a utility is applied and hands its arithmetic to `reward.md` (D-20); **Rev 4** threads the run's own **shape** through the policy and the transition step, so the decode, the conservation guard and the shortfall normaliser read that shape's chips in play — 40 on the default shape and 200 on the six-descriptor one (`shapes.md` §2–§3, `sizing.md` §5, D-29)
- **Ceiling:** 110 lines. At the ceiling, split by owner — never append
- **Read with:** `loop.md` §1 steps 5–6, `reward.md` §1–§5, `greedy.md` §1–§2, `seeds.md` §2, `curves.md` §3, `agents/rule.md` §2–§4, `errors.md` §4

## 1. The learner's seat: `_seat(index)`

    _seat(index) -> int          # 0 or 1: the seat the learner plays in hand `index`

`_seat(i)` is `i % 2`. Seat 0 holds the button and posts the small blind in **every** hand (`engine/surface.md` §4), so alternating the seat the learner plays is how the run alternates the button: half its hands on the button and half in the big blind, which is the same seat alternation a table cell makes and the same fairness the league reports (`league.md` §3, D-16). The index is the hand's 0-based index in that pair's pass, so the same index names the same seat for both arms of a pair, for every rung at one seed, and for the greedy pass that replays the pair's own hands (`seeds.md` §3, `greedy.md` §1).

Rejected: drawing the seat, which makes a run's seat assignment a second stream; a fixed seat, which hands one arm the button throughout and makes a curve a positional artefact (`protocol.md` §1); and alternating inside a hand, which is the engine's business and no caller's (`engine/surface.md` §4).

## 2. The learner's side is a policy assembled here: `_learner_policy`

    _learner_policy(learner, encoder, shape=None) -> callable     # a policy in the sense of e2e-surface.md §2

The returned callable takes `(readout, legal_actions)` and answers one descriptor of `legal_actions`, built from the four granted calls and nothing else:

    mask  = features.legal_indices(legal_actions)        # the decision's legal indices, position-aligned
    obs   = features.encode(encoder, readout)            # one observation for this readout
    index = agents.act(learner, obs, mask)["action"]     # the training-time decision
    return features.decode_action(index, shape=shape)    # the descriptor of the run's own vocabulary

**The index decodes in the run's own shape's vocabulary.** An index is one of its own shape's descriptors and of no other's, so `decode_action` is handed the shape the learner was built on: the `{0, 1, 2}` a run has always used on the default shape, and that shape's own six on the second (`shapes.md` §2–§3, `sizing.md` §3, `features/surface.md` §9). A closure that decoded with no shape would hand `engine` a default-shape descriptor for a six-index decision, which the engine refuses as an illegal action — so the shape is a parameter of the policy and is never left to default (`engine/surface.md` §10, D-29). The greedy pass's policy is `agents.as_policy` on the same encoder and the same name, so it decides in the same vocabulary (`greedy.md` §1).

This is why `agents.as_policy` is not the training-time decision: the one exploration-off policy this module is granted is the **pass's**, at `exploration="off"` and at the finished model (`greedy.md` §1, `docs/L2/training/surface.md` §1), and the policy above is the training-time decision — `act` at the learner's own seed and its own state, built from the four `features` and `agents` calls this step is granted (`module-map.md` §2, `agents/surface.md` §6, `agents/rule.md` §4). Nothing is recorded here: the policy keeps no log and returns no index, so the transitions are derived from the episode record alone and a unit case can build them without a learner (`tests/training/test_episode.py::TRN-4.1`).

Rejected: `agents.as_policy(learner, encoder, seed)` as the training-time policy, a call outside the grant; catching its absence and falling back, which would be two policies in one loop; decoding with no `shape`, which is the default shape's vocabulary for every run and a descriptor the engine refuses on the other (D-29); and recording the index inside the closure, which would make the batch a side channel of the policy rather than a function of the episode.

## 3. `_transitions(episode, seat, encoder, utility=None, shape=None)`

    _transitions(episode, seat, encoder, utility=None, shape=None) -> list[Mapping]   # records.md §4 records, in decision order

For the decisions where the learner's seat acted, **in the order the hand played them**:

1. `observation` — `features.encode(encoder, decision["readout"])`, the state that seat faced;
2. `legal` — `features.legal_indices(decision["legal"])`, the mask of that decision;
3. `action` — the vocabulary **index** of the descriptor the hand applied: `legal_indices` is position-aligned with its argument (`features/surface.md` §8), so the index is `legal[legal_actions.index(decision["action"])]` and no second legality channel is invented. `agents.learn` takes indices, and an index outside `legal` is its refusal (`agents/surface.md` §7, §2);
4. `next_observation`, `next_legal` — the **next decision of that seat** in the same hand, encoded and masked the same way;
5. `terminal`, `reward` — §4.

The successor is the learner's next decision and never the opponent's interleaved one: the chain is the seat's own states, so the update never bootstraps on a value computed for the other seat's decision (`agents/rule.md` §2). Rejected: taking every decision of the hand and marking one seat's, which would put the opponent's state in the learner's successor and make the update depend on who happened to act next.

**`shape` is the run's own, and it reaches every arithmetic that reads the game.** The three reward functions take it: `_chips_in_play(decision, seed, seat, shape=None)` totals `sum(readout['stacks']) + readout['pot']` and compares it with `engine.game_config(shape)`'s seats × starting stack, `_stack_shortfall(decision, seed, seat, shape=None)` normalises against that same starting stack, and `_net_chips(decision, seed, seat, shape=None)` reads the decision's own reward and needs none of it (`utilities.md` §4, `shapes.md` §2, `reward.md` §4, D-20, D-29). So a run conserves **40 chips on the default shape and 200 on the six-descriptor one**, and `utilities.md` §2's ±2-chip and all-in scores are that shape's own arithmetic. **A readout of one shape read against the other is `ChipConservationBroken`**, naming the hand's seed and both totals: a 200-chip decision read against the default's 40, or a 40-chip one against 200, is refused rather than normalised, because a normaliser that is not the game's own would make one reward incommensurable with the next (ASM-6, ASM-28, `errors.md` §2, `loop.md` §6, D-29).

**A hand in which the learner's seat never acted yields an empty list.** That is a real hand — the opponent on the button may fold preflop before the big blind acts — and it is not an error: the run makes no `learn` call, the hand contributes no signal, and `loop.md` §1 step 6 says so (`agents/surface.md` §7 refuses an empty batch, and nothing here asks it to).

## 4. `terminal`, `reward`, and the terminal transition's own mask

- **`terminal` is positional**: the last transition of the list — the last decision that seat made in the hand — carries `terminal=True`, and every earlier one carries `False`. The seat's last decision is its terminal one even when the opponent folded afterwards, because the hand's outcome arrives at the seat's own terminal decision (`records.md` §5, ASM-12).
- **`reward` is the decision's own at every decision but the terminal one**: those keep the episode's `0.0` — the engine places the hand's delta at the seat's terminal decision alone, and no intermediate term is added (`records.md` §5, ASM-12). At the terminal decision the reward is re-expressed by the variant's **utility**: **this is the one place a utility is applied**, and `reward.md` §1–§4 owns the arithmetic, the selection of it by the catalogue's reward token and the chips-in-play guard (D-20, `utilities.md` §4).
- **No reward arithmetic in `src/agents/learner.py` is touched by any of it**: its terminal branch stays `target = record["reward"]` and its non-terminal branch stays the rule's, so the utility never enters the update — the learner carries the utility's name and reads no arithmetic from it (`utilities.md` §3, §4, D-19, D-20).
- **The terminal transition's `next_observation` and `next_legal` are its own**: it has no successor and `agents.learn` reads neither, and an empty mask is illegal, so the mask it carries is the mask of the decision it is (`features/surface.md` §8, `agents/rule.md` §3, `tests/e2e/_surface.py` `transitions`).
- **A zero-reward terminal decision is normal**: a split pot pays nothing, so `reward == 0.0` at a terminal transition is not a sign the flag is wrong — the flag is positional and never inferred from the reward (§4's first bullet).

## 5. The batch, and what a hand costs the learner

`agents.learn(learner, transitions)` is called **once per hand** with that hand's list, in the order §3 built it: the caller's order, neither sampled nor shuffled nor replayed (`loop.md` §1 step 6, `agents/surface.md` §7, ASM-7). That is what lets two arms declare one sample order (`ladder.md` §5). One hand holds a handful of decisions — the fixed-limit cap bounds it at about eight applied actions per street, and the game's own ceiling at 23 a hand (`ASM-6`, `ASM-15`, `sizing.md` §4) — so a hand's batch is **smaller than the declared `batch_size` of 32**, and that is legal by construction: `batch_size` is the ladder's declared granularity and never a precondition, and a rule stated per transition consumes any non-empty batch in the caller's order (`agents/rule.md` §3, §6).

The batch's `td_error` — the mean absolute TD error over the hand's transitions (`agents/surface.md` §7) — is the hand's learning signal and is filed into the run's current interval (`curves.md` §3). Nothing here keeps a replay buffer, a priority or a second pass, and no transition survives its hand.

## 6. What is left to L4

Whether the descriptor's position is found by `list.index` or by an enumerate over the pairs, whether the observations are computed once and reused for the successor, how `shape` reaches the three reward functions, and the internals of those functions. Not L4's: `_seat`'s parity, the four calls of §2 and the descriptor round trip, the index decoding in the run's own vocabulary, the successor rule of §3, the terminal flag's positional definition, the terminal reward being the utility's number and `0.0` at every other decision, the guard and the normaliser reading the run's own chips in play and refusing the other shape's readout by name, the terminal mask, and the empty-batch rule (`reward.md` §1–§5, `guardrails.md` G7, G10, G17, G25, D-29). The two signatures of §1 and §3 — `_transitions`' `utility` and `shape` arguments and `_learner_policy`'s `shape` included — are contract for `tests/training/` (`README.md` §4).
