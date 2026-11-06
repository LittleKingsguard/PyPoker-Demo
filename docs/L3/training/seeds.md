# training — the seeds

- **Layer:** L3 · **Module:** `training` · **Unit:** phase1 · **Rev:** 1 · **Date:** 2026-11-05
- **Owner:** the deal-seed and opponent-seed derivation (§2), why both arms of a pair get the same deals and opponents (§3), the
  learner's seed (§4), the determinism claims and what `sha256` is computed over (§5)
- **Ceiling:** 90 lines. At the ceiling, split by owner — never append
- **Read with:** `loop.md` §1 step 4, `episode.md` §1, `registry.md` §3, `checkpoints.md` §3, `errors.md` §4

## 1. Three seeds, and which one is a draw

A run at seed `s` needs three things seeded, and none of them is drawn from a stream (`protocol.md` §4, ASM-2):

1. **the deal of hand *i*** — `_deal_seed(s, i)`, handed to `engine.play_hand` as its seed, which deals through
   `engine.new_hand`, the project's single seeding point (`engine/surface.md` §4);
2. **the opponent of hand *i*** — `_opponent_seed(s, i)`, handed to `evaluation.opponent(pool, seed)`, which reduces it modulo
   the membership's size (`evaluation/surface.md` §8);
3. **the learner's own generator** — the run seed `s` itself, handed to `agents.build_learner` as the spec's `seed` (§4).

The global `random` stream is therefore moved by dealing and nothing else: `training` never seeds it, never reads it and never
advances it, and every draw a learner or a baseline makes comes from its own generator keyed by the decision it faces
(`agents/surface.md` §1, `engine/surface.md` §1). Hand *i* is the hand at 0-based index *i*, so `i ∈ [0, budget)`.

## 2. The derivation (D6)

    payload(domain, seed, index) = b"pypoker-training/" + domain.encode("ascii") + b"/v1"
                                 + b"\x1f" + str(int(seed)).encode("ascii")
                                 + b"\x1f" + str(int(index)).encode("ascii")
    derived = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % (2**63)

with `domain` one of `b"deal"` and `b"opponent"`. The three private names are contract for `tests/training/`
(`README.md` §4) and their bodies stay L4's; their signatures do not:

| Name | Signature | One-line contract |
|---|---|---|
| `seeds._derive` | `_derive(domain, seed, index)` | §2's payload for that domain, seed and index, `sha256`'d, the first eight bytes big-endian, reduced modulo `2**63` |
| `seeds._deal_seed` | `_deal_seed(seed, index)` | `_derive(b"deal", seed, index)` — the seed `engine.play_hand` is called with |
| `seeds._opponent_seed` | `_opponent_seed(seed, index)` | `_derive(b"opponent", seed, index)` — the seed `evaluation.opponent` is called with |

**Why a derivation and not a draw.** A draw is a position in a stream, so it would carry the *order* of the calls into the
record: a snapshot, a timing, a different variant count or a resumed run would move the stream and change the hands. A
derivation is a function of `(seed, index)`, so hand *i* of a run is the hand `(s, i)` names whatever came before it, whatever
arm is training and whatever process runs it (`protocol.md` §4, ASM-2, FAM-4.3). It is what makes the two arms of a pair
comparable (§3) and what lets a run be reproduced from `(configuration, seed set, budget, pool membership)` alone.

**Why two domains.** The deal and the opponent are two independent questions about one hand, and one digest per question keeps
them from coinciding: with one domain, hand *i*'s opponent seed would equal its deal seed, and the opponent draw would be a
function of the deal rather than an independent draw over the membership (`evaluation/surface.md` §8). The `\x1f` separator is
a byte no ASCII domain and no decimal integer contains, so `("deal", 1, 23)` and `("deal", 12, 3)` cannot collide by
concatenation. The domain version `v1` is in the payload so a changed derivation is a new domain and not a silent rewrite.

**Why `seed + i` is rejected.** Two defects, each fatal on its own: adjacent hands are *correlated* — hand *i+1* is dealt at
`seed + i + 1`, so two runs whose seeds differ by one swap their hands and a battery that changes a seed by one sees a
shifted copy of the same deals rather than a different sample (FAM-4.8) — and **two rungs' hand *i* collide**, because every
rung at one seed would pass the engine the same sequence of seeds, so R1's and R4's hands would be identical in every respect
the seed controls. A `sha256` derivation has neither property: the outputs of distinct `(seed, index)` pairs are unrelated, and
the only structure the integers keep is the one `% 2**63` imposes on the top bits. Rejected too: `random.Random(s).random()`
per hand, which is a stream again, and `hash((seed, i))`, which is process-salted and differs between runs
(`agents/rule.md` §4 makes the same argument for the exploration key).

## 3. Why both arms of a pair get the same deals and opponents

`_deal_seed` and `_opponent_seed` do not see the variant, the learner or the arm: they see the run seed and the hand index. So
for one seed, R4's `wide` arm and R4's `deep` arm play the **same hands in the same order against the same opponents**, and the
only thing left to differ between their curves is the configuration (`ladder.md` §5, ASM-8, D-3). The pool is frozen before
the first hand and the same frozen pool draws both arms' opponents, so the draw's *result* is equal as well and not merely its
input (`registry.md` §3, ASM-16, FAM-3.18). That is the property §2's derivation buys and `seed + i` would not.

The learner's own exploration differs between the arms even at one seed, because `agents.act` keys its draw on the learner's
seed **and the observation and the mask** (`agents/rule.md` §4): one seed and two models is two exploration sequences, which is
intended — the arms are two models, not two runs of one model.

## 4. The learner's seed

The learner is built at **the run seed itself** — `agents.build_learner`'s `seed` is the seed of the run's seed set that the
pair is training at, not a derived value and not `0` (`loop.md` §1 step 3, `agents/surface.md` §4). Each seed in the set is one
training run, so a three-seed run trains three learners per variant, and the seed in each checkpoint is that run's seed: a
shipped member loads at the seed its container records (`evaluation/surface.md` §12, `agents/checkpoint.md` §2.1). Nothing
here derives a learner seed, because a derivation would make the recorded seed disagree with the seed the generator used.

## 5. Determinism, stated testably

For one configuration, one seed set and one frozen pool, two runs give equal curves and equal checkpoint paths (`loop.md` §7).
Three claims are separately observable: the same seed derives the same pair of seeds for the same index (unit:
`test_seeds.py::TRN-3.1`), a different index or a different seed derives a different pair (TRN-3.2, TRN-3.3), and no call here
touches `random`'s state (TRN-3.4 — sample `random.getstate()`, call every private name, compare; e2e counterpart FAM-4.4).

## 6. What is left to L4

Whether the payload is assembled by concatenation or by `join`, whether the digest is sliced before or after the byte-order conversion, and the constant `2**63`'s spelling. Not L4's: the five payload parts and their order, the `\x1f` separator, the two domain strings, the eight-byte prefix, the modulo, and §2's three signatures (`guardrails.md` G9).
