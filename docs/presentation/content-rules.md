# presentation — content rules for the real talk (L3 design)

- **Layer:** L3 · **Artifact:** `presentation/index.html` (content pass) · **Rev:** 1 · **Date:** 2026-11-17 · **Ceiling:** 100 lines
- **Realises D-121 §4**, from `strata/records/presentation-deck-kit-research.md` row 8. Each rule was paid for once already, in another author's deck; these are the ones that transfer to ours.
- **Binding now on two slides, and on the rest from the next content pass.** The six demo slides are placeholder (`DEMO`) and are judged by `docs/presentation/design.md` A1–A15, not by this page; `#s2` and `#s8` are the deck's first real slides (D-129, `docs/presentation/contact.md`) and every rule below binds on them from this pass. The fact-check trace in `docs/presentation/checks.md` §7 is how a rule-3 breach gets caught.
- **Read with:** `docs/presentation/design.md` (§5 shapes, the character budgets), `docs/presentation/presenter.md` (notes and sources), `docs/presentation/checks.md` (§7 the fact-check form), `presentation/README.md`.

## The rules

**R1. Explain, then ask.** One slide says what a thing is; the next asks the room, with the question large. Each act ends on a question.
*Reason:* a room that is asked has to think, and a room that is only told waits for the end; the question is also the only reliable way to find out whether the previous act landed.

**R2. A drawing, a headline and one line.** Every slide carries something to look at, one headline, and one line of text. Detail goes behind More or into the notes.
*Reason:* the room reads the slide before it hears it; a second paragraph competes with the sentence the presenter is speaking, and the drawer is where competition is not paid for.

**R3. The fact is the biggest thing on the slide.** Never a slogan with the fact small underneath it.
*Reason:* a figure set at caption size is decoration, and the numbers rule (`strata/decisions.md` / `strata/records/`, with the date) exists so a figure can be believed; a small figure is not worth its source. Draw a figure in proportion or as a scene rather than setting one giant number with nothing to compare it to.

**R4. One thread through the talk.** The same worked example appears in every act.
*Reason:* recurrence is the only thing that lets a room carry an argument from slide 3 to slide 20 without notes of their own. In our deck the thread is one hand, or one rung of the ladder, seen four ways.

**R5. About 1.2 minutes a slide, counted against the slot.** Count the slides before building them.
*Reason:* a 20-minute slot is about 16 slides (20 ÷ 1.2) and that is a budget, not a target; a deck that overruns by a minute a slide does not get shortened on the day, it gets skipped, and the act that gets skipped is the last one.

**R6. A 14px text floor.** No text on a slide, in the notes or in the sources is smaller than 14px.
*Reason:* 14px on the 1280×720 stage is about 21px on a 1920 wall, which is the last size a back row reads; the gate enforces the same floor (G6), so this rule is the one rule with a mechanical guard rather than a habit.

**R7. Notes carry the dates, the figures and the caveats.** The slide carries the fact; the notes carry what it rests on, who disputes it, and which record says so.
*Reason:* that is the seam the presenter needs at question time, and it is why the notes exist at all (`docs/presentation/presenter.md` §1); a note that repeats the slide's sentence is a prompt, not a note.

**R8. Agree the outline before building.** Propose the acts and the slides per act in plain text, and get a yes.
*Reason:* in the source deck's own account, building first and arguing about content afterwards cost the most time on every earlier deck; the outline is also the only artefact cheap enough to throw away.

**R9. Keep a dated copy of the deck before a content rewrite.** `presentation/index.html` is one file with no source behind it, so the copy is the undo.
*Reason:* a rewrite edits the shipped artefact in place; there is no build step to revert and no diff to read. Copy to `presentation/archive/index-YYYY-MM-DD.html` first, and the fact-check file beside it (`checks.md` §7).

## What this deck already commits to

- **A measured number may be pasted only from `strata/decisions.md` or `strata/records/`, with the record's date beside it** (D-118 Scope, `presentation/README.md` §Numbers). This stands unchanged; `presentation/FACTCHECK.md` is the trace that makes it checkable.
- **Demo content is marked `DEMO`** on every slide that carries it (design A4), and the HUD says `demo slides: placeholder content`. A demo figure and a measured one are never confusable, and the two real slides carry no badge at all (D-129).
- **Sources are per slide, in the file** (`presenter.md` §3), so a figure's record is reachable at the moment it is spoken rather than in an appendix nobody reaches.

## Not adopted from the kit

- **The em-dash ban.** It is that author's typographic house style, adopted after a personal correction; nothing measured here supports it, and our demo copy already uses dashes as a voice. A punctuation rule is a style sheet for the writer, not a constraint the deck can enforce, so it is left to whoever writes the copy. **D-121 records the same conclusion.**
- **The eyebrow-label ban.** It was paid for in a deck whose bottom bar carries the act, the counter and the clock, which is why a per-slide eyeline label was redundant there. Our HUD carries dots, the counter and a static hint (`design.md` §6) and **not** the act, so a small label naming the current act is a live option here, and the ban would remove a tool the HUD does not replace. It stays available; R2's "one line" is what keeps it from becoming a second headline.
- **The kit's fluid layout and build-from-source pipeline** stay rejected in `design.md` §8 (D-118, D-121) and are not content rules at all.

## What these rules do not do

They do not choose the talk's argument, its length, its acts or its figures; they constrain how the chosen content lands on the stage. An outline that satisfies R1–R9 can still be a bad talk, and the gate cannot tell the difference (`checks.md` §5).
