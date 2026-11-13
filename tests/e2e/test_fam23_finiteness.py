"""FAM-23 — the member's finiteness envelope: the target's bound and the update's band.

`docs/L1/battery.md` §3 FAM-23, `docs/L1/counterfactual.md` §10, `docs/L1/records.md` §12 and
D-45.  `strata/records/counterfactual-divergence.md` recorded the defect this family holds:
a six-seat `reveal-counterfactual` run died on a new seed with `LearningDiverged … got -inf`,
because nothing bounded the magnitude of the learner's own parameters.  `counterfactual.md`
§10 answers it with **two bounds** — the target bounded by the chips a hand can produce and
refused by name outside them, and the update bounded by a declared parameter band that makes
a non-finite value unreachable — and with **one record key**: a run whose variants declare a
member other than `none` carries a conditional `finiteness` block, shaped like the `greedy`
one, stating per variant per seed the member, the transitions its episodes resolved, the
steps it took, the largest target it was handed and the bound in force.

The cases are:

* **FAM-23.1** a completed member run's `finiteness` block: present, one entry per variant per
  seed, exactly the five facts, `0 ≤ largest_target ≤ target_bound`, `target_bound` equal to
  the shape's own chips in play, the member each arm was trained under, and no non-finite
  number anywhere in the record (`counterfactual.md` §10, `records.md` §12).
* **FAM-23.2** the conditionality: a run whose variants all declare `none` carries **no**
  `finiteness` key at all, which is what keeps a default declaration's record at the shape
  its capture took (`counterfactual.md` §9, §10, `records.md` §12).
* **FAM-23.3** the bounds at the surface: `agents.learn` refuses a transition whose
  `counterfactual` carries a value past the chips in play, naming the bound and **never** a
  non-finite number, while a value exactly at `+T` and one exactly at `−T` are inside the
  bound and are stepped (`counterfactual.md` §10, §4, `records.md` §4).
* **FAM-23.4** the bound on the shape the member is measured on: a six-seat run's block
  states that shape's own chips in play, 600, and a largest target inside it
  (`counterfactual.md` §10, §8, `seats.md` §2, D-33).

The instances below — the seed, the micro budget, the six-seat configuration's labels and
pool id — are the battery's own (`docs/L1/battery.md` §4, D-15); the two catalogue members,
the shapes and their chips in play are read off `agents.learners()` and `engine.game_config`
and never written down here.

**Red is the expected state of this file** until D-45's implementation lands: every case
asserts an observable outcome of the declared surface and none can pass against the code
that produced `-inf` (`strata/examiner.md` §1, `battery.md` §1).
"""

import math
import os
import sys
import unittest

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _records as R  # noqa: F401
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _records as R  # noqa: E402
    import _surface as S  # noqa: E402

#: The five facts `counterfactual.md` §10 and `records.md` §12 give one `finiteness` entry,
#: in the order the record states them.
FINITENESS_FACTS = ("member", "transitions", "steps", "largest_target", "target_bound")

#: The invented seed every run in this family is played at, and the invented micro budget
#: twelve hands is: the battery's own numbers, and the cheapest budget `training.run` accepts
#: (`_surface.BUDGET_MICRO`, ASM-18, `battery.md` §4).
SEED = S.SEED_A
BUDGET = S.BUDGET_MICRO

#: The two catalogue members whose names the design fixes: `none`, the declared default, and
#: `reveal-counterfactual`, the member whose targets §10 bounds (`counterfactual.md` §6).
NONE = S.COUNTERFACTUAL_DEFAULT
REVEAL = S.COUNTERFACTUAL_SECOND

#: The margin this family drives past the bound: a whole chip over the chips in play, which a
#: `float64` states exactly.  An invented instance (`battery.md` §4).
PROBE_STEP = 1

#: One architecture for the member's learners, as FAM-22's member cases build it: one width and
#: one depth, so the only thing that differs between two of them is the seed the case names
#: (ASM-10, `counterfactual.md` §6).
MEMBER_WIDTH = S.UTILITY_WIDTH
MEMBER_DEPTH = S.UTILITY_DEPTH

#: The six-seat configuration's invented labels and pool id: the battery's own, on the shape
#: `counterfactual.md` §8 measures the member on (`battery.md` §4, D-33).
SIX_SEAT_RUNG = "R23-finiteness-envelope"
SIX_SEAT_ARM = "finiteness-arm"
SIX_SEAT_POOL = "pool-r23-finiteness"


def numbers_in(text):
    """Every number a message states, read by value and not by one spelling of it.

    `docs/L3/agents/errors.md` §3 leaves a refusal's wording to the implementation, so a case
    that asserts "the message names the bound" reads the numbers it states by value: an
    integer, a decimal part and an exponent are all one number here.
    """
    import re

    found = []
    for token in re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", str(text)):
        try:
            found.append(float(token))
        except ValueError:  # pragma: no cover - the pattern admits no such token
            continue
    return found


def facts_of(entry):
    """The five facts of one `finiteness` entry, by the names §12 gives them, or `None`.

    A row is recognised by its **own** keys rather than by a nesting this battery invented,
    exactly as `_surface.run_greedy` reads a `greedy` pass, so the container the record
    chooses is free and a row that dropped a fact is the row the case fails on
    (`records.md` §12, `battery.md` §2).
    """
    if not S.is_mapping(entry):
        return None
    stated = {R.tok(key): value for key, value in entry.items()}
    facts = {}
    for name in FINITENESS_FACTS:
        if R.tok(name) not in stated:
            return None
        facts[name] = stated[R.tok(name)]
    return facts


def finiteness_rows(block):
    """Every `(variant, seed, facts)` row a run record's `finiteness` block states.

    ``records.md`` §12 shapes the block like the ``greedy`` one — variant → seed → facts —
    and both nestings are the implementation's freedom, so the block is walked and every
    mapping that carries all five facts is one row, with the keys it was reached through
    naming its variant and its seed.
    """
    rows = []

    def walk(value, path, depth):
        if depth > 6:
            return
        facts = facts_of(value)
        if facts is not None:
            rows.append((path[0] if path else "", path[1] if len(path) > 1 else "", facts))
            return
        if S.is_mapping(value):
            for key, inner in value.items():
                walk(inner, path + (str(key),), depth + 1)
        elif isinstance(value, (list, tuple)):
            for position, inner in enumerate(value):
                walk(inner, path + (str(position),), depth + 1)

    walk(block, (), 0)
    return rows


def has_finiteness_fact(record):
    """Whether any mapping in a record carries a `largest_target` or a `target_bound` key.

    A run declaring no member must carry **no** `finiteness` key *and* no leak of its facts
    under another name, or "absent" would be a spelling rather than a contract
    (`counterfactual.md` §10, `records.md` §12).
    """
    for needle in ("largest_target", "target_bound"):
        if S.find_values(record, needle):
            return True
    return False


#: The three runs this family reads, built once per process: a run is a record and its
#: artefacts, so a second case that re-read it would pay for the same observable twice
#: (`battery.md` §2, §5).
_RUNS = {}


def pair_run(case):
    """The battery's own two-member configuration at the micro budget: both arms trained.

    `_surface.SurfaceCase.two_counterfactual_rung` declares one architecture twice and differs
    on `counterfactual` alone — the first arm naming the catalogue's first member explicitly,
    the second naming `reveal-counterfactual` — so one run carries the member arm `§10` is
    about **and** the silent arm's own entry beside it, which is what makes the block's
    conditionality visible in one record (`counterfactual.md` §6, §10, D-3).
    """
    if "pair" not in _RUNS:
        configuration = case.two_counterfactual_rung(seeds=(SEED,))
        # The declaration and the run agree on the budget this case hands `training.run`, so
        # the record says what was trained (`records.md` §2, §12): the rung's own declared
        # sample count is the ladder's, and this case drives the micro budget.
        for entry in configuration["variants"]:
            entry["samples"] = BUDGET
            entry["snapshot_every"] = max(1, BUDGET // 10)
        _RUNS["pair"] = (
            configuration,
            case.run_record(configuration, (SEED,), BUDGET),
        )
    return _RUNS["pair"]


def none_run(case):
    """A run whose one variant declares **no** member at all: the declared default.

    The registry's first rung at the same micro budget and the same invented seed, so the
    two records differ in the declaration and not in the work (`counterfactual.md` §9, §10).
    """
    if "none" not in _RUNS:
        _RUNS["none"] = case.run_record("R1", (SEED,), BUDGET)
    return _RUNS["none"]


def six_seat_run(case):
    """A six-seat member run: the shape the member is measured on, at the micro budget.

    `_surface.SurfaceCase.shaped_rung` declares one variant on one named shape and a pool
    with the frozen flag; the two folders beside D-6's three anchors make the five members a
    six-seat hand's draw of five distinct opponents needs, and the member is written into the
    variant entry because a run that declares none writes no `finiteness` block at all
    (`seats.md` §4, ASM-43, `records.md` §8, `counterfactual.md` §8, §10).
    """
    if "six" not in _RUNS:
        shape = case.shape_names()[-1]
        configuration = case.shaped_rung(
            shape=shape,
            seeds=(SEED,),
            samples=BUDGET,
            name=SIX_SEAT_RUNG,
            variant=SIX_SEAT_ARM,
            pool_id=SIX_SEAT_POOL,
            baselines=S.FOLDER_BASELINES[:2],
        )
        configuration["variants"][0]["counterfactual"] = REVEAL
        _RUNS["six"] = (
            configuration,
            case.run_record(configuration, (SEED,), BUDGET),
        )
    return _RUNS["six"]


class FAM23Finiteness(S.SurfaceCase):
    """The target's bound, the update's band, and the record that carries both."""

    # -- the block (counterfactual.md §10, records.md §12) ----------------
    def block(self, record):
        """A run record's `finiteness` block, or a failure naming what it carries."""
        block = S.family_value(record, "finiteness")
        if block is None:
            raise AssertionError(
                "a run whose variants declare a member other than %r carries the "
                "`finiteness` block `counterfactual.md` §10 and `records.md` §12 make "
                "conditional on exactly that, and this record carries %r"
                % (NONE, sorted(str(key) for key in record),)
            )
        return block

    def rows(self, record, what):
        """The block's rows, or a failure naming the record and what it states."""
        block = self.block(record)
        rows = finiteness_rows(block)
        self.assertTrue(
            rows,
            "%s: the `finiteness` block states one row per variant per seed, carrying the "
            "five facts %r, and it states none: %r"
            % (what, FINITENESS_FACTS, block),
        )
        return rows

    def integer(self, value, what):
        """One count of the block, as a plain integer."""
        self.assertTrue(
            S.is_count(value),
            "%s is an integer count (records.md §12, counterfactual.md §10): %r"
            % (what, value),
        )
        return int(value)

    def number(self, value, what):
        """One quantity of the block, as a finite number."""
        self.assertTrue(
            isinstance(value, (int, float)) and not isinstance(value, bool),
            "%s is a number (records.md §12, counterfactual.md §10): %r" % (what, value),
        )
        self.assertTrue(
            math.isfinite(float(value)),
            "%s is finite — the block exists to show that every value the member was handed "
            "was inside a finite bound (counterfactual.md §10): %r" % (what, value),
        )
        return float(value)

    def chips_in_play(self, shape=None):
        """`T = seats × starting_stack`, read off the shape in force (`shapes.md` §2).

        `counterfactual.md` §10 declares the bound in force to be the chips in play, and
        `seats.md` §2 makes the shape's own total `pot + sum(stacks)` at every decision — 40
        on the default row, 200 on the two-seat uncapped one and 600 on the six-seat one — so
        both numbers are read off `engine.game_config` and the product is computed here
        (`e2e-surface.md` §3.1, ASM-28, D-29, D-33).
        """
        config = self.game_config(shape)
        seats = None
        for key, value in config.items():
            if R.tok(key) in ("seats", "playercount") and S.is_count(value):
                seats = int(value)
        self.assertIsNotNone(
            seats,
            "a shape declares its seat count (seats.md §2, e2e-surface.md §3.1): %r"
            % (config,),
        )
        return seats * S.starting_stack(config)

    def declared_member(self, entry, default=NONE):
        """The counterfactual member one variant entry declares, or the declared default."""
        key = None
        for candidate in entry:
            if R.tok(candidate) == "counterfactual":
                key = candidate
        return default if key is None else str(entry[key])

    # -- the learner and the batch a case hands it (records.md §4) --------
    def member_learner(self, shape=None, seed=SEED):
        """One learner built from the battery's spec under the member (`§3.3`, §6)."""
        return self.ep("agents", "build_learner")(
            self.learner_spec(
                width=MEMBER_WIDTH,
                depth=MEMBER_DEPTH,
                seed=seed,
                counterfactual=REVEAL,
                game=shape,
            )
        )

    def resolved_batch(self, value, shape=None, seed=S.SEED_C, count=2):
        """`count` transitions of one hand, each carrying `value` at every legal action.

        `records.md` §4's record, built from the decisions a real hand makes through the
        declared engine entry points: both encoded observations, the applied index, the
        reward, the terminal flag, both legal masks, the episode boundary, and a
        `counterfactual` sequence of `A` entries with `None` exactly where the decision did
        not permit an action — which is the shape `agents.learn` takes `A` steps on
        (`counterfactual.md` §4, §5, §6, §10).
        """
        encoder = self.encoder(shape=shape)
        walk = self.decision_walk(
            seed, self.baseline("always-call", S.SEED_D), limit=count, shape=shape
        )
        self.assertEqual(
            len(walk),
            count,
            "the case must drive %d decisions of one hand for a %d-transition batch "
            "(records.md §4): %d" % (count, count, len(walk)),
        )
        width = len(self.vocabulary(shape))
        records = []
        for position, (_hand, readout, legal, _index, action) in enumerate(walk):
            terminal = position == len(walk) - 1
            next_readout = walk[position + 1][1] if not terminal else readout
            next_legal = walk[position + 1][2] if not terminal else legal
            indices = [int(index) for index in self.ep("features", "legal_indices")(legal)]
            values = [None] * width
            for slot in indices:
                values[slot] = float(value)
            records.append(
                {
                    "observation": self.observation(encoder, readout),
                    "next_observation": self.observation(encoder, next_readout),
                    "action": int(action),
                    "reward": 0.0,
                    "terminal": terminal,
                    "legal": indices,
                    "next_legal": [
                        int(index) for index in self.ep("features", "legal_indices")(next_legal)
                    ],
                    "episode": int(seed),
                    "counterfactual": tuple(values),
                }
            )
        return records

    def refused(self, call):
        """The text of a refusal one declared call **raises**, or ``None`` if it returned.

        ``e2e-surface.md`` §2 makes an invalid argument *raise* an error naming the violated
        contract, and a successful ``agents.learn`` returns statistics whose ``td_error`` key
        holds the word "error" — so a shared reader that looks for a failure word in a
        returned record would read a trained batch as a refused one (``battery.md`` §2).  The
        call is made once and its message kept.
        """
        try:
            call()
        except S.SurfaceAbsent:
            raise
        except Exception as exc:
            return "%s: %s" % (type(exc).__name__, exc)
        return None

    def parameters(self, learner, name):
        """The parameter bytes one container of this learner stores (`checkpoint.md` §2).

        The one quantity the member's update moves is the learner's parameters, and the
        array the container stored is the artefact that shows it: the bytes are compared and
        never parsed, so the battery holds no reader of the array's layout
        (``counterfactual.md`` §6, ``docs/L3/agents/checkpoint.md`` §2).
        """
        import zipfile

        target = os.path.join(self.scratch(), name)
        written = self.ep("agents", "save")(learner, target)
        path = str(written) if written else target
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if "param" in name.lower()]
            self.assertTrue(
                names,
                "a checkpoint container carries its parameter array beside its metadata "
                "(docs/L3/agents/checkpoint.md §2): %r" % (archive.namelist(),),
            )
            return archive.read(names[0])

    # -- FAM-23.1 ----------------------------------------------------------
    def test_fam23_1_a_member_run_carries_its_finiteness_facts_inside_the_bound(self):
        """FAM-23.1 a completed member run carries `finiteness`, five facts per variant per seed, `0 ≤ largest_target ≤ target_bound`, and the bound is the chips in play.

        `counterfactual.md` §10 and `records.md` §12 make the block **conditional** on some
        variant declaring a member other than `none`, and give each entry five facts: the
        `member` that ran, the `transitions` its episodes resolved fully, the `steps` it took
        (`A` per resolved transition), the `largest_target` it was handed and the
        `target_bound` in force — the chips in play, `seats × starting_stack`.  The case reads
        the battery's own paired configuration at the micro budget, so one record carries both
        arms: the declaring arm's entry names `reveal-counterfactual`, resolved transitions
        and steps, and the silent arm's entry names `none` and consumed nothing.  It also
        asserts the other half of "the member still emits only finite values" on this run:
        every number the record reports anywhere — curves, greedy census, timings, the block —
        is finite, so the run is evidence and not a record that merely survived (`§10`,
        `records.md` §12, `battery.md` §3 FAM-23).
        """
        configuration, record = pair_run(self)
        arms = [str(entry["name"]) for entry in configuration["variants"]]
        # The seed set is the declaration's: each variant entry states the seeds its arm is
        # trained at, and `training.run` was handed the same set (`records.md` §2, §12).
        seeds = []
        for entry in configuration["variants"]:
            for seed in entry.get("seeds") or ():
                if str(seed) not in seeds:
                    seeds.append(str(seed))
        self.assertTrue(
            seeds,
            "the paired configuration declares the seeds its arms are trained at "
            "(records.md §2, §12): %r" % (configuration,),
        )
        bound = self.chips_in_play()
        rows = self.rows(record, "the paired member run")
        seen = {}
        for variant, seed, facts in rows:
            seen[(R.tok(variant), str(seed))] = facts
        for arm in arms:
            for seed in seeds:
                self.assertIn(
                    (R.tok(arm), seed),
                    seen,
                    "the `finiteness` block states one row per variant per seed — `%r` at "
                    "seed %r among them — because the facts are the member's and every pair "
                    "of a run that declares one carries its own (records.md §12, "
                    "counterfactual.md §10): %r" % (arm, seed, sorted(seen)),
                )
        for arm, seed, facts in rows:
            with self.subTest(arm=arm, seed=seed):
                declared = None
                for entry in configuration["variants"]:
                    if R.tok(entry["name"]) == R.tok(arm):
                        declared = self.declared_member(entry)
                self.assertIsNotNone(
                    declared,
                    "the block names the variant %r and the configuration declares it "
                    "(records.md §12): %r" % (arm, [e["name"] for e in configuration["variants"]]),
                )
                self.assertEqual(
                    str(facts["member"]),
                    str(declared),
                    "the row names the member that variant was trained under, so a reader "
                    "can see which targets the counts belong to (records.md §12, "
                    "counterfactual.md §6, §10): %r against %r"
                    % (facts["member"], declared),
                )
                transitions = self.integer(
                    facts["transitions"], "finiteness[%r][%r]['transitions']" % (arm, seed)
                )
                steps = self.integer(
                    facts["steps"], "finiteness[%r][%r]['steps']" % (arm, seed)
                )
                largest = self.number(
                    facts["largest_target"],
                    "finiteness[%r][%r]['largest_target']" % (arm, seed),
                )
                stated = self.number(
                    facts["target_bound"],
                    "finiteness[%r][%r]['target_bound']" % (arm, seed),
                )
                self.assertGreaterEqual(
                    transitions,
                    0,
                    "a count of resolved transitions is not negative (counterfactual.md §10)",
                )
                self.assertGreaterEqual(
                    steps,
                    transitions,
                    "the member takes `A` steps on each transition it resolved, `A` its "
                    "legal-action count, so a row's steps are at least its transitions "
                    "(counterfactual.md §6, §10): %r steps against %r transitions"
                    % (steps, transitions),
                )
                self.assertGreaterEqual(
                    largest,
                    0.0,
                    "`largest_target` is the largest **magnitude** the member was handed, so "
                    "it is zero or positive (counterfactual.md §10): %r" % (largest,),
                )
                self.assertLessEqual(
                    largest,
                    stated,
                    "every target the member used was inside the bound in force — the one "
                    "claim the block exists to let a third party read (counterfactual.md "
                    "§10): %r against %r" % (largest, stated),
                )
                self.assertEqual(
                    stated,
                    float(bound),
                    "the bound in force is the chips in play of the shape the run played, "
                    "`seats × starting_stack` — %r on %r — and no case writes that product "
                    "down as a literal (counterfactual.md §10, shapes.md §2, seats.md §2, "
                    "ASM-28): the row states %r"
                    % (bound, self.shape_names()[0], stated),
                )
                if str(facts["member"]) != NONE:
                    self.assertGreater(
                        transitions,
                        0,
                        "a member other than %r resolves at least one episode of a twelve-"
                        "hand run, so its row is evidence and not a column of zeros "
                        "(counterfactual.md §4, §10): %r" % (NONE, facts),
                    )
                    self.assertGreater(
                        largest,
                        0.0,
                        "and it was handed a value of non-zero magnitude on at least one "
                        "resolved transition (counterfactual.md §4, §10): %r" % (facts,),
                    )
                else:
                    self.assertEqual(
                        (transitions, steps, largest),
                        (0, 0, 0.0),
                        "the run's silent arm declares %r, which reads no resolution and "
                        "takes no step of this member's, so its row states zeros and the "
                        "run's bound (counterfactual.md §6, §10): %r" % (NONE, facts),
                    )
        for number in S.numbers(record):
            self.assertTrue(
                math.isfinite(float(number)),
                "every number the run reports is finite — the record of a member run is "
                "evidence that no non-finite value was produced, never the place one is "
                "found (counterfactual.md §10, records.md §12): %r" % (number,),
            )

    # -- FAM-23.2 ----------------------------------------------------------
    def test_fam23_2_a_run_declaring_no_member_carries_no_finiteness_key(self):
        """FAM-23.2 a run whose variants all declare `none` carries no `finiteness` key at all.

        `counterfactual.md` §9 and §10 and `records.md` §12 make the block **conditional**:
        present exactly when some variant declares a member other than `none`, and absent
        otherwise — which is what keeps a default declaration's record at the shape its
        capture took, field for field.  The case reads the registry's first rung at the same
        micro budget and seed as FAM-23.1's pair, asserts the key is absent under any
        spelling, and asserts that no fact of the block leaked in under another name, or
        "absent" would be one writer's spelling rather than the contract.  The record's own
        required families are read beside it, so the case cannot pass on an empty or refused
        run (`counterfactual.md` §9, §10, `records.md` §12, `battery.md` §3 FAM-23).
        """
        record = none_run(self)
        self.assertIsNone(
            S.family_value(record, "finiteness"),
            "a run that declares no member carries no `finiteness` key, under any spelling "
            "(counterfactual.md §10, records.md §12): %r"
            % (sorted(str(key) for key in record),),
        )
        self.assertNotIn(
            "finiteness",
            {R.tok(key) for key in record},
            "and not the key itself either: the block is conditional and this run's variants "
            "all declare the catalogue's first member (counterfactual.md §9, §10): %r"
            % (sorted(str(key) for key in record),),
        )
        self.assertFalse(
            has_finiteness_fact(record),
            "no fact of the block appears in the record under another name, so its absence "
            "is the contract and not a spelling (counterfactual.md §10, records.md §12): %r"
            % (S.find_values(record, "largest_target"),),
        )
        for family in ("curves", "checkpoints", "greedy"):
            self.assertIsNotNone(
                S.family_value(record, family),
                "the run still carries the families records.md §12 requires of it — %r among "
                "them — so `finiteness`'s absence is the only conditional key and not an "
                "empty record (records.md §12, counterfactual.md §9): %r"
                % (family, sorted(str(key) for key in record)),
            )

    # -- FAM-23.3 ----------------------------------------------------------
    def test_fam23_3_an_unbounded_value_is_refused_by_name_and_the_bound_s_edge_is_stepped(self):
        """FAM-23.3 `agents.learn` refuses a value past the chips in play, naming the bound and never a non-finite number, and steps a value exactly at `±T`.

        `counterfactual.md` §10 bounds the member's target by the game: a counterfactual value
        is one seat's whole-hand net chip delta, so it lies inside the chips a hand can
        produce, and a value outside them has no bounded value at all — a stale or hand-edited
        record, or a resolution from another shape.  `learn` therefore **refuses** it by name,
        naming the transition index, the action index, the value and the bound, and never
        reports a non-finite number; a value exactly at `+T` and one exactly at `−T` are inside
        the bound and are stepped.  The case drives both on the shape in force through the
        declared entry points and reads the refusal's **text** — the bound and the absence of
        `inf` and `nan` — because that text is what the fix's argument rests on
        (`counterfactual.md` §4, §10, `records.md` §4, `battery.md` §3 FAM-23).
        """
        bound = self.chips_in_play()
        learner = self.member_learner()
        for sign, value in (("positive", bound + PROBE_STEP),
                            ("negative", -(bound + PROBE_STEP))):
            batch = self.resolved_batch(value)
            text = self.refused(
                lambda batch=batch: self.ep("agents", "learn")(
                    self.member_learner(), [dict(record) for record in batch]
                )
            )
            self.assertIsNotNone(
                text,
                "a %s target of %r lies outside the chips in play, %r, and `agents.learn` "
                "refuses it by name rather than learning from a value no hand can produce "
                "(counterfactual.md §10): the batch trained" % (sign, value, bound),
            )
            lowered = (text or "").lower()
            self.assertIn(
                "learn",
                lowered,
                "the refusal names the call it refused (errors.md §3): %r" % (text,),
            )
            stated = numbers_in(text)
            self.assertTrue(
                any(abs(number - float(bound)) <= 1e-9 for number in stated),
                "the refusal names the bound in force — the chips in play, %r — so a reader "
                "sees which envelope the value left, and the numbers it states are %r: %r"
                % (bound, stated, text),
            )
            for spelling in ("inf", "nan"):
                self.assertNotIn(
                    spelling,
                    lowered,
                    "no refusal of the member reports a non-finite number: the bound refuses "
                    "the value before it is read, so %r cannot appear (counterfactual.md §10, "
                    "docs/L3/agents/divergence.md §2): %r" % (spelling, text),
                )

        # A value exactly at the bound is inside it, and is stepped.
        for sign, value in (("positive", bound), ("negative", -bound)):
            with self.subTest(bound=sign):
                driven = self.member_learner(seed=S.SEED_B)
                before = self.parameters(driven, "fam23-3-%s-before.ckpt" % (sign,))
                statistics = self.ep("agents", "learn")(
                    driven,
                    [dict(record) for record in self.resolved_batch(float(value))],
                )
                self.assertTrue(
                    S.is_mapping(statistics),
                    "a value exactly at ±T is inside the bound and is stepped, so `learn` "
                    "returns the update's statistics (counterfactual.md §10, rule.md §3): %r"
                    % (statistics,),
                )
                for number in S.numbers(statistics):
                    self.assertTrue(
                        math.isfinite(float(number)),
                        "and the statistics of that step are finite (counterfactual.md §10): "
                        "%r" % (number,),
                    )
                after = self.parameters(driven, "fam23-3-%s-after.ckpt" % (sign,))
                self.assertNotEqual(
                    before,
                    after,
                    "the step happened: the parameter array the container stores moved, "
                    "which is the observable consequence of an accepted update under the "
                    "member (counterfactual.md §6, §10): the array is unchanged",
                )

    # -- FAM-23.4 ----------------------------------------------------------
    def test_fam23_4_the_bound_in_force_on_the_six_seat_shape_is_its_chips_in_play(self):
        """FAM-23.4 a six-seat member run's block states that shape's own bound, 600, with every target inside it.

        `counterfactual.md` §8 declares the member on all three shapes and measures it on
        `six-seat-no-limit-100`, and §10 makes the bound in force the chips a hand can
        produce on the shape that played — 600 there, `seats × starting_stack` read off
        `engine.game_config`, and never a number this battery writes down (`shapes.md` §2,
        `seats.md` §2, ASM-28, D-33).  The case reads one six-seat member run at the micro
        budget: the member is named in the block, the bound is that row's own, the
        transitions and steps are the run's, and `largest_target` lies inside the bound — so
        the shape the member exists for is the shape whose envelope the record states
        (`counterfactual.md` §8, §10, `records.md` §12, `battery.md` §3 FAM-23).
        """
        shape = self.shape_names()[-1]
        self.assertGreater(
            self.seats_of(shape),
            2,
            "the catalogue's last row is D-33's six-seat shape, whose bound is the one this "
            "case reads (seats.md §2, D-33): %r" % (shape,),
        )
        configuration, record = six_seat_run(self)
        bound = self.chips_in_play(shape)
        self.assertGreater(
            bound,
            self.chips_in_play(),
            "a six-seat shape's chips in play exceed the default shape's, so the bound this "
            "case reads is not one every shape shares (shapes.md §2, seats.md §2, ASM-28): "
            "%r against %r" % (bound, self.chips_in_play()),
        )
        rows = self.rows(record, "the six-seat member run")
        armed = [row for row in rows if str(row[2]["member"]) != NONE]
        self.assertTrue(
            armed,
            "the six-seat run declares the member, so its block carries a row for it "
            "(counterfactual.md §8, §10): %r" % (rows,),
        )
        for variant, seed, facts in armed:
            with self.subTest(arm=variant, seed=seed):
                self.assertEqual(
                    str(facts["member"]),
                    REVEAL,
                    "the six-seat row names the member the variant declared "
                    "(counterfactual.md §6, §10): %r" % (facts["member"],),
                )
                largest = self.number(
                    facts["largest_target"],
                    "finiteness[%r][%r]['largest_target']" % (variant, seed),
                )
                stated = self.number(
                    facts["target_bound"],
                    "finiteness[%r][%r]['target_bound']" % (variant, seed),
                )
                self.assertEqual(
                    stated,
                    float(bound),
                    "on %r the bound in force is that shape's chips in play, %r, read off "
                    "engine.game_config and never written down here (counterfactual.md §10, "
                    "shapes.md §2, seats.md §2): the row states %r"
                    % (shape, bound, stated),
                )
                self.assertGreater(
                    self.integer(
                        facts["transitions"],
                        "finiteness[%r][%r]['transitions']" % (variant, seed),
                    ),
                    0,
                    "the member resolves at least one episode of a twelve-hand six-seat run, "
                    "so its row is evidence and not a column of zeros (counterfactual.md §4, "
                    "§10): %r" % (facts,),
                )
                self.assertLessEqual(
                    largest,
                    stated,
                    "every target the member used lies inside the chips in play of the "
                    "shape it played, which is the claim `counterfactual.md` §10 makes and "
                    "the record states: %r against %r" % (largest, stated),
                )


if __name__ == "__main__":
    unittest.main()
