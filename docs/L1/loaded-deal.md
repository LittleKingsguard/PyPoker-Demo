# PyPoker-Demo — L1 the loaded deal

- **Layer:** L1 · **Unit:** phase1 · **Rev:** 2 · **Date:** 2026-11-15
- **Covers:** the declared loaded-deal capability D-70 requires — the one optional argument the two dealing entry points gain, the deal's two keys and the one card spelling, the six named refusals and what each says, the episode record's `deal` key and the replay it makes possible, the determinism the capability promises, and the four proof obligations a build of it is held to (D-70, D-69)
- **Ceiling:** 120 lines. At the ceiling, split by owner — never append

## 1. What it is, and what it does not add

A hand may be played with **prescribed hole cards per seat and a prescribed board**. The deal is declared data, validated by name, reproducible from its own record, and it is the instrument D-70 makes primary: it replaces an aggregate census with the question the census could not answer, *what does this model do when it holds aces and what does it do when it holds seven-deuce offsuit* (D-70, D-59).

It adds **no entry point**. The map stays at **50 endpoints**, every module keeps its `modules.json` row and its harness ceiling of `50 + 10×N`, and the `fixed`/`general` split stays 13/37, because a deal is an *instance* of a row already marked `general` and not a row (`e2e-surface.md` §4–§5). What it adds is one optional argument on the two entry points that deal a hand:

    engine.new_hand(seed, shape=None, deal=None)
    engine.play_hand(seed, seat0_policy=None, seat1_policy=None, shape=None, seats=None, deal=None)

**Absence is today's call.** With `deal` absent both entry points run the code they run today, and no entry point changes what it returns: the seeded path is **byte-identical**, proved on a captured baseline rather than accepted on the design's word (§6 P1). The obligation is not a courtesy — D-61 changed what an input *means* and paid for it with a proof, and a change that only adds a branch owes the same (`shapes.md` §5, `reward-scale.md` §4).

**How the deal reaches the table, and the two halves the reader must not confuse.** A hand's cards are laid down at four separate moments — the hole cards before the first decision, the flop when the pre-flop betting closes, the turn and the river when theirs do — and three of those four happen **inside `apply_action`'s step**, not inside `new_hand` (Rev 1 stated this wrongly, and the layer's examiner found it). So the capability has two halves:

- **`new_hand` is where the deal enters.** It builds the state it always built and lays the named deal into it — the hole cards by dealing them, and the board by arranging the cards the engine will draw when it deals each street — so the hand `new_hand` returns is *dealt*, and the deal is a property of the hand and of nothing else;
- **the engine deals the rest, unchanged.** The flop, turn and river are laid down by the dealing that `apply_action` already performs, from the state it was handed, and the burn card between streets is drawn the same way.

What that buys is the property the design rests on: no entry point's **code** changes — `readout`, `legal_actions`, `apply_action`, `is_terminal`, `payoffs` and `play_hand`'s loop are the same functions reading a different state, so a loaded hand cannot produce a readout the seeded path could not produce. What it costs is that a five-card deal is not one operation: the board arrives across three streets and three burns, which is why §6 P2 — a seeded hand's own deal replayed through the loaded path — is the proof that the arrangement is right and not an illustration of it.

## 2. The deal, key by key

A deal is a mapping with **exactly two keys**, both required: a deal that carries a third, or omits one, is refused (§3).

| Key | Content |
|---|---|
| `holes` | an ordered sequence of pairs, **one pair per seat in seat order** — the shape's whole seating, so its length is the shape's seat count — each pair the seat's two card spellings in the order that seat's `hole` fact will show them (`readout.md` §2, `seats.md` §3) |
| `board` | **three, four or five** card spellings in **dealing order**: the first three are the flop, the fourth the turn, the fifth the river (`episode.md` §5) |

A **card spelling** is the readout's own and the project has no second one: two characters, rank first from `23456789TJQKA`, suit second from `cdhs` — `"As"`, `"Td"`, `"2c"` (`readout.md` §3). A deal is therefore plain data: it survives JSON, compares by value, and a third party reads it without a library.

A deal constrains **exactly the cards it names**. A three-card deal names a flop and leaves the turn and the river to the stream; a four-card deal leaves the river to it; and every deal leaves the undealt deck and the three burn cards to it. The record keeps that distinction (§4).

Six seats over a five-card board name 17 cards, and the deal must name them all **distinctly**. That check is load-bearing and not defensive: the library enforces no distinctness — its card consumption removes a named card from wherever it sits in the deck, by value — so a duplicated card would be dealt twice and the hand would be two cards short of a hand (D-13's rule that nothing is silently repaired).

## 3. The refusals, each by name

Every malformed deal raises `engine.errors.InvalidDeal`, the module's own class beside `InvalidSeed`, `InvalidPolicy` and `InvalidSeating` (`errors.md` §2). Its message begins with the argument and the entry point that validates it — `new_hand(deal)` on both paths, as the seed check is `new_hand(seed)` when reached through `play_hand` — and **names the rule broken and the fact that broke it**. The rules are a closed set, tried in this order, so one malformed deal has exactly one message:

| Reason | Refused when | The message names |
|---|---|---|
| `not-a-deal` | the deal is not a mapping, or carries a key outside `holes` and `board`, or omits one of the two | the type it was given, or the offending key and the two declared ones, or the missing key |
| `seat-coverage` | `holes` is not an ordered sequence of pairs — a `str`, `bytes` or mapping is refused **naming its type**, since each is iterable and none is a sequence of pairs — or holds a number of pairs other than the shape's seat count | the type, or the shape, its seat count and the count it was handed (`seats.md` §4's form) |
| `hole-size` | a seat's pair is not exactly two cards | that seat's index and the size it was handed |
| `board-length` | `board` is not an ordered sequence, or holds fewer than three or more than five spellings | the length and the interval `3..5` |
| `card-outside-deck` | a spelling is not two characters with a rank from `23456789TJQKA` and a suit from `cdhs` | the spelling and its place — a seat index or a board position |
| `duplicate-card` | one card is named twice anywhere in the deal | the card and **every place it appears**: two seat indices, a seat and a board position, two board positions, or the one seat whose own pair names it twice |

Four properties of that table are contract. **All six precede the deal**, exactly as `new_hand`'s seed refusal does, so a refused deal deals nothing, leaves the global stream where it was, and a caller may retry (`hand.md` §2, ASM-2). **A refusal never repairs**: no card is defaulted, no board truncated to five, no seat filled from the deck, no ordering imposed on the caller's pairs. **One deal, one message**: `seat-coverage` is tried before `hole-size`, so five holes handed for six seats is one refusal and not five, and `duplicate-card` is last, so the duplicate check reads a fully spelled deal. **A name outside the six is not a refusal but a defect**: a build that adds a seventh reason has changed this table and owes a Rev of it (D-13).

## 4. The record

The episode record carries a fifth key, **`deal`**, present **if and only if** a deal was supplied. A seeded call's record is exactly today's, key for key — the precedent is D-43's, where a carrier is absent whenever the member is `none` so a default record stays byte-identical (`records.md` §5, D-43).

`deal` is the deal **as played**, normalised to `holes` a tuple of pairs in seat order and `board` a tuple of spellings: the values the caller handed in, in the input's own order, with no card added and none dropped. Two consequences follow and both are asserted. **It agrees with the reveal**: `reveal`'s per-seat `hole` equals `deal`'s pair for every seat, on a folded seat too, so the deal and the reveal are two views of one fact and never two spellings of it (`records.md` §5). **It replays**: handing it back at the record's own seed gives the record again —

    play_hand(record["seed"], seats=<same seating>, shape=<same shape>, deal=record["deal"]) == record

The deal is everything the record needs from the *cards*, and it is not everything a replay needs: the record's keys are closed and carry **no shape and no seating** (`records.md` §5), so a third party supplies those two from the run it was told about. That boundary is stated rather than papered over, because a record that carried them would change every shipped record.

The recorded `board` is what was **prescribed**, not what was dealt: a three-card deal records three cards while `reveal.board` records the five the hand laid down. Both are recorded because they answer different questions — what was asked, and what happened — and a reader must not take one for the other.

## 5. Determinism, and the stream

A loaded hand is a function of `(seed, deal, seating, shape, that shape's rules)` and of nothing else. The seed stays required and stays validated, because the deal fixes only the cards it names: the undealt deck's order, the burn cards and a three- or four-card deal's remaining street or streets come from the stream, so two calls at one tuple give one record and a different seed at one deal gives a different turn and river.

`new_hand` seeds the global stream and builds its state exactly as it does today; what the deal adds is that the named cards are laid down **where that hand's own dealing would have drawn** them (D-70). Nothing above `new_hand` reads the stream's position, so a loaded hand neither promises nor forbids anything about the stream it leaves — and a refused deal leaves it exactly as `new_hand`'s seed refusal does (§3).

## 6. The four proof obligations

**P1 — the seeded path is byte-identical, on a captured baseline.** A capture taken **before** the change records, for a declared set of seeded calls, every leaf of every record and every observation: `new_hand` and `readout` at several seeds on all three shapes, `play_hand`'s whole episode (decisions, amounts, payoffs, reveal), both encodings' arrays, `game_config`, `action_space`, `observation_spec`, one `training.run`'s `greedy` block and one `evaluation.match`. The same capture on the changed tree must equal it **leaf for leaf** — `N of N`, with `N` reported — and the run's `timings` is the one block exempt, being a wall clock (`docs/L2/training/surface.md` §4, `reward-scale.md` §4, ASM-23). This is the form both earlier byte-identical gates took (`shapes.md` §5, D-34).

**P2 — a loaded path and a seeded path reaching one state encode identically.** Take a seeded hand that reaches the river with an all-check-call seating, read its `reveal` (every seat's hole and five board cards) and replay **that seating at that seed** through `play_hand` with the reveal as the deal. Then at every decision index: the readouts are equal, `features.encode` of them is equal **for both encodings**, and the actions, amounts, payoffs and reveals are equal. This is D-70's "the observation is the one the encoder would produce for that exact state", and it is the real test of the mechanism: a deal laid into the wrong draw position, a burn displaced by one, or a card from the wrong street fails at the first decision that reads the board.

**P3 — a refusal deals nothing.** For each of the six reasons the refusal is raised, its message names the rule and the fact, and the global stream's state after the refused call equals the state before it.

**P4 — the record replays.** §4's identity, asserted on a five-card deal, a four-card one and a three-card one, the last two of which also show their remaining street or streets moving with the seed at one deal while the named cards do not.

## 7. What it costs the battery

One family, **FAM-25** (`battery.md` §3), and no existing assertion weakened: P1's capture, P2's replay at both encodings, P3's six refusals with their messages and the stream check, P4's three replays, a seeded record's `deal`-absent equality, the `holes`-equals-`reveal` agreement, and one loaded hand at each of the three shapes so the argument is not two-seat-only.

## 8. What is left to L2, L3 and L4

How `new_hand` lays the named deal in — the hole cards may be dealt explicitly through the library's own dealing calls, but **a prescribed board cannot be**: the flop, turn and river are drawn when each street's betting closes, inside the step, so a board must be arranged as the cards the engine will draw, in the order it will draw them, around the burn between streets and the round-robin order the hole dealing uses. A design that instead makes `apply_action` deal by hand has changed a third entry point and owes this document a Rev. Also theirs: the error class's place in the hierarchy and every private name. Not theirs: the two keys and the one spelling, the six reasons and their order, an absent `deal` meaning today's call, the record's `deal` with its if-and-only-if, and P1–P4 (D-13).
