"""AGT-17 — the declared game shape at this surface: the head, the count, the index space, the tie and the mode.

Drives `docs/L2/agents/shapes.md` §1-§4, §6-§7 and `docs/L3/agents/shapes.md` §1-§4, §6
beside the L1 statements the same contracts are published under — `docs/L1/shapes.md` §2,
§5, `docs/L1/sizing.md` §3, §4, §6, `docs/L1/architecture.md` §2, §5, `docs/L1/records.md`
§6, §15, `docs/L1/ladder.md` §3-§4 — and `strata/decisions.md` D-29, ASM-37 and ASM-40: the
catalogue's two names are restated once and default first, while the head's width is a
**reading** of the shape's descriptor count (`shapes.md` §1); every kind ends in `W → A`, so
the parameter count's output term is `A·W + A`, and at `A = 3` the formula is arithmetically
today's, which is why no recorded count moves (§2); `act` and `learn` decide over `0 .. A−1`
in the shape's declared order, which is the measured price order and deliberately not
monotone in amount, and a mask naming an index the learner's shape does not have is refused
naming that shape, its range and the index before any arithmetic (§3); `act` records `tie`,
true exactly when the greedy arm's tie-break and not a strict maximum chose the index (§3,
`records.md` §6, §15); and `as_policy`'s mode is `schedule` or `off`, `off` taking the
masked maximum and the tie-break alone and constructing no generator at all (§4).

What is **not** asserted here belongs to the two neighbour files: the container's
`format_version` 3 and 4 and its `game` field are AGT-7.18-7.23 in `test_checkpoint.py`,
because a shape case there reads the same container surgery the rest of AGT-7 does, and the
width's *values* are `features`' and `engine`'s (`docs/L2/features/shapes.md` §2, §5): this
battery reads them through `features.action_space(shape=...)` and `engine.new_hand(seed,
shape=...)`, the two granted calls, and writes a `3` or a `6` down only where a design
document states one (`docs/L2/agents/shapes.md` §2's table).

Two spellings below the ten entry points are read, and both are contract:
`model._param_count_for` and `model._initial_parameters`, which `rule.md` §8 declares and
whose trailing `actions=None` is `docs/L3/agents/shapes.md` §2's, and the layout field
`actions` with the `w_out`/`b_out` offsets beside it, which `docs/L3/agents/shapes.md` §2
states as the one thing about the output layer that is not a constant of the kind. The one
internal a case stands **aside** — `rule._draws` — is reached through `declared_internal`
and restored by `addCleanup`, so the `off` mode's "not constructed at all" is observed
rather than assumed (`shapes.md` §4, `sizing.md` §4).
"""

import unittest

from _agents_support import (
    ALL_MASK,
    DEFAULT_SHAPE,
    LEARNER_SEED,
    NONEMPTY_MASKS,
    OTHER_SEED,
    OTHER_SHAPE,
    SIX_MASK,
    SIX_MASKS,
    TIE_SEEDS,
    AgentsCase,
    declared_internal,
    declared_module,
    decision_draw,
    features,
    flat_encoder,
    learner_spec,
    observation_template,
    plain_int,
    schedule,
    shape_decisions,
    transition,
)

#: The six recorded rung counts `docs/L2/agents/shapes.md` §2's table fixes at `A = 3`, as
#: `(variant, kind, width, depth, sparsity, count)` rows read off `ladder.md` §3 and §4:
#: 10,119 at R1 and R2; 10,053 at R3; 10,047 and 10,053 at R4; 10,053 and 10,109 at R5; and
#: 10,053 at both R6 variants.  Nothing here is a new number: every count is the table's and
#: every setting is the variant's own declaration (`ladder.md` §3, ASM-10, ASM-40).
RUNG_VARIANTS = (
    ("R1 naive-numeric", "naive-stack", 36, 2, 0.0, 10119),
    ("R2 naive-numeric-torch", "naive-stack", 36, 2, 0.0, 10119),
    ("R3 card-tokens", "token-embedding", 50, 2, 0.0, 10053),
    ("R4 wide", "wide", 62, 1, 0.0, 10047),
    ("R4 deep", "deep", 50, 2, 0.0, 10053),
    ("R5 dense", "deep", 50, 2, 0.0, 10053),
    ("R5 sparse", "sparse", 62, 2, 0.5, 10109),
    ("R6 residual", "residual", 50, 2, 0.0, 10053),
    ("R6 plain", "plain", 50, 2, 0.0, 10053),
)

#: The two shapes as a case walks them: the default named by absence, the other by name
#: (`shapes.md` §1, `surface.md` §4, D-29).
SHAPES = (None, OTHER_SHAPE)


def head_width(shape=None):
    """`A`, the shape's descriptor count, **read** off `features.action_space` (`shapes.md` §1-§2).

    This is the granted call `declarations.actions_for` makes and the only statement of the
    width: three on the default shape and six on the other, never a literal of a backend's,
    a table's or a formula's (`sizing.md` §6, ASM-40, `docs/L3/agents/shapes.md` §1).
    """
    return len(features().action_space(shape=shape))


def declared_count(architectures, kind, width, depth, sparsity, actions):
    """`architecture.md` §5's sum arithmetic, from the kind's declared row and `A = actions`.

    The input block first (`I·W + W` for the dense family, `V·W` for a token one, `I` and `V`
    being the kind's own declared `observation_size`), then `D·(W² + W)` — `D·(k + W)` for
    `sparse`, `k = round((1 − s)·W²)` — then the output term `A·W + A`.  No part of this
    arithmetic is a copied count: the caller states the width, the depth, the sparsity and
    the shape's `A`, and the constant that remains is `architecture.md` §5's formula itself.
    """
    row = architectures[kind]
    size = int(row["observation_size"])
    dense = row["observation"] == "dense-numeric"
    layer_width = int(width)
    input_term = size * layer_width + (layer_width if dense else 0)
    if kind == "sparse":
        kept = round((1.0 - float(sparsity)) * layer_width * layer_width)
        trunk_term = int(depth) * (kept + layer_width)
    else:
        trunk_term = int(depth) * (layer_width * layer_width + layer_width)
    return input_term + trunk_term + int(actions) * layer_width + int(actions)


class ShapeAxisTest(AgentsCase):
    """The head, the count, the six-index decision space, the `tie` flag and the exploration mode."""

    def test_agt17_1_the_head_is_the_shapes(self):
        """AGT-17.1 a spec naming `no-limit-100` builds a learner whose `actions` is that shape's six and whose `param_count` is `A·W + A` with `A = 6`, while the same spec with no `game` reports the default shape's three and today's count — each computed from the spec's `width`, its `depth` and the kind's declared `observation_size`, never from a copied constant, and the two counts differ by exactly the extra head term (`docs/L2/agents/shapes.md` §1-§2, `docs/L3/agents/shapes.md` §1-§2, `sizing.md` §6, `architecture.md` §5, ASM-40, D-29).

        The two shapes' widths are the design's — three and six, `docs/L2/agents/shapes.md` §2's
        table — and they are read here through `features.action_space` as well, so a shape
        whose declared descriptor count moved is red in this case and not in a copied
        literal.  `Learner.game` and `Learner.actions` are the two fields `shapes.md` §2 makes
        the learner's own: it "carries the resolved `A` and its shape's name", which is what
        `act`, `learn`, `as_policy` and `save` read and what no arithmetic branches on.
        """
        package = self.agents()
        architectures = package.learners()["architectures"]
        three, six = head_width(None), head_width(OTHER_SHAPE)
        self.assertEqual(
            three,
            3,
            "the default shape's head is three descriptors wide (docs/L2/agents/shapes.md "
            "§2's table, D-29)",
        )
        self.assertEqual(
            six,
            6,
            "the second shape's head is six descriptors wide (docs/L2/agents/shapes.md §2's "
            "table, D-29)",
        )
        self.assertEqual(
            head_width(DEFAULT_SHAPE),
            three,
            "the default shape named explicitly is the shape absence reads as (shapes.md "
            "§1)",
        )
        cases = (
            ("naive-stack", 6, 2),
            ("naive-stack", 12, 1),
            ("deep", 6, 2),
            ("deep", 10, 3),
        )
        for kind, width, depth in cases:
            with self.subTest(kind=kind, width=width, depth=depth):
                other = self.build(kind=kind, width=width, depth=depth, game=OTHER_SHAPE)
                default = self.build(kind=kind, width=width, depth=depth)
                self.assertEqual(
                    getattr(other, "game", None),
                    OTHER_SHAPE,
                    "a learner built from a spec naming %r does not carry that shape's name "
                    "(shapes.md §2, D-29)" % (OTHER_SHAPE,),
                )
                self.assertEqual(
                    getattr(default, "game", None),
                    DEFAULT_SHAPE,
                    "a learner built from a spec naming no shape does not carry the default "
                    "shape's name, which is the absence of a name and not a defaulting of one "
                    "(shapes.md §1, D-29)",
                )
                self.assertEqual(
                    plain_int(getattr(other, "actions", None), "Learner.actions"),
                    six,
                    "a %r learner reports %r actions and the shape's head is %d wide "
                    "(docs/L3/agents/shapes.md §2, ASM-40)"
                    % (OTHER_SHAPE, getattr(other, "actions", None), six),
                )
                self.assertEqual(
                    plain_int(getattr(default, "actions", None), "Learner.actions"),
                    three,
                    "a default-shape learner reports %r actions and its head is %d wide "
                    "(docs/L2/agents/shapes.md §2)"
                    % (getattr(default, "actions", None), three),
                )
                self.assertEqual(
                    plain_int(package.param_count(other), "param_count"),
                    declared_count(architectures, kind, width, depth, 0.0, six),
                    "the %r learner's count is not architecture.md §5's sum with the "
                    "output term A·W + A at A = %d" % (kind, six),
                )
                self.assertEqual(
                    plain_int(package.param_count(default), "param_count"),
                    declared_count(architectures, kind, width, depth, 0.0, three),
                    "the default-shape %r learner's count is not the same formula at A = %d, "
                    "which is today's (sizing.md §6, ASM-40)" % (kind, three),
                )
                self.assertEqual(
                    package.param_count(other) - package.param_count(default),
                    (six - three) * width + (six - three),
                    "the shape moves the output term alone, so the two counts differ by "
                    "exactly the three extra head rows and their bias (docs/L3/agents/shapes.md "
                    "§2, ASM-40)",
                )

    def test_agt17_2_the_output_block_is_actions_times_width_plus_actions(self):
        """AGT-17.2 on a dense kind and a token kind at both shapes the output block's contribution is `actions·width + actions`: `layout.w_out` is `(offset, A·W)`, `b_out` begins where it ends and sits `A` slots before `count`, `model._param_count_for` reports the `param_count` the entry point does, and `model._initial_parameters` is as long as the count — the `W → A` output layer of `docs/L3/agents/shapes.md` §2 (`architecture.md` §2, §5, `sizing.md` §6, `rule.md` §8, ASM-40).

        The layout is the object `docs/L3/agents/shapes.md` §2 makes the statement about —
        "`w_out` is `(offset, actions·W)`, `b_out` takes `actions` slots, and `count` ends with
        `A·W + A`" — and both backends read `layout.actions` where they read a `3` before.  The
        two internals are `rule.md` §8's, called with the trailing `actions` that
        `docs/L3/agents/shapes.md` §2 adds to them, and `actions=None` is asserted to be the
        default shape's reading rather than a constant of its own.
        """
        package = self.agents()
        count_for = declared_internal("model", "_param_count_for")
        initial = declared_internal("model", "_initial_parameters")
        cases = (
            ("naive-stack", 6, 2, 0.0),
            ("deep", 8, 2, 0.0),
            ("sparse", 6, 2, 0.5),
        )
        for kind, width, depth, sparsity in cases:
            for shape in SHAPES:
                with self.subTest(kind=kind, shape=shape):
                    architecture = {"kind": kind, "width": width, "depth": depth}
                    if sparsity:
                        architecture["sparsity"] = sparsity
                    learner = package.build_learner(
                        learner_spec(architecture=architecture, game=shape)
                    )
                    expected = head_width(shape)
                    layout = getattr(learner, "layout", None)
                    self.assertIsNotNone(
                        layout,
                        "the learner carries no layout, so the w_out/b_out offsets "
                        "docs/L3/agents/shapes.md §2 states cannot be read",
                    )
                    self.assertEqual(
                        plain_int(getattr(layout, "actions", None), "layout.actions"),
                        expected,
                        "the layout's `actions` is not the shape's descriptor count "
                        "(docs/L3/agents/shapes.md §2, ASM-40)",
                    )
                    offset, length = layout.w_out
                    self.assertEqual(
                        plain_int(length, "layout.w_out's length"),
                        expected * int(layout.width),
                        "the output matrix's block is A·W long and it is not (A = %d, W = %d)"
                        % (expected, int(layout.width)),
                    )
                    self.assertEqual(
                        plain_int(layout.b_out, "layout.b_out"),
                        int(offset) + int(length),
                        "the output bias does not begin where the output weights end, so the "
                        "output block is not one (A·W, A) pair (docs/L3/agents/shapes.md §2)",
                    )
                    self.assertEqual(
                        plain_int(layout.count, "layout.count") - int(layout.b_out),
                        expected,
                        "`count` does not end A slots after b_out, so the output bias is not "
                        "A wide (docs/L3/agents/shapes.md §2, ASM-40)",
                    )
                    self.assertEqual(
                        package.param_count(learner),
                        plain_int(layout.count, "layout.count"),
                        "param_count is not the layout's own count (surface.md §5)",
                    )
                    self.assertEqual(
                        int(count_for(kind, width, depth, sparsity, actions=expected)),
                        package.param_count(learner),
                        "model._param_count_for and param_count disagree at A = %d, so the "
                        "formula's output term is not the head's (rule.md §8, "
                        "docs/L3/agents/shapes.md §2)" % (expected,),
                    )
                    values = initial(
                        kind, width, depth, sparsity, LEARNER_SEED, actions=expected
                    )
                    self.assertEqual(
                        int(values.shape[0]),
                        package.param_count(learner),
                        "the initial draw is not as long as the count, so the output layer "
                        "was not drawn at (W, A) (architecture.md §4's step 3, "
                        "docs/L3/agents/shapes.md §2)",
                    )
                    if shape is None:
                        # The trailing `actions=None` resolves through
                        # `declarations.actions_for(None)`: the default shape's count, which is
                        # a reading and not a constant of the internal's own (`shapes.md` §2).
                        self.assertEqual(
                            int(count_for(kind, width, depth, sparsity)),
                            package.param_count(learner),
                            "the declared three-positional-argument call is not the default "
                            "shape's count (rule.md §8, docs/L3/agents/shapes.md §2)",
                        )

    def test_agt17_3_the_rung_counts_at_the_default_head_are_unmoved(self):
        """AGT-17.3 the six rung counts `docs/L2/agents/shapes.md` §2's table records are what `param_count` reports for specs built as the rungs declare them — 10,119 at R1 and R2, 10,053 at R3, 10,047 and 10,053 at R4, 10,053 and 10,109 at R5, and 10,053 at both R6 variants — so `A·W + A` at `A = 3` is bit-identical to the `3·W + 3` it replaces and no recorded count moves (`sizing.md` §6, `architecture.md` §5, `ladder.md` §3-§4, ASM-10, ASM-40, D-29).

        Each row is one variant's own declaration — its kind, width, depth and sparsity — read
        at the default shape, which is the shape all six rungs share, and the count is the one
        written beside it.  The backend is `numpy` throughout, because §5's count is one number
        in both backends (D-7, `backends.md` §2) and a capacity battery may not import `torch`
        to say so.
        """
        package = self.agents()
        for variant, kind, width, depth, sparsity, recorded in RUNG_VARIANTS:
            with self.subTest(variant=variant):
                architecture = {"kind": kind, "width": width, "depth": depth}
                if sparsity:
                    architecture["sparsity"] = sparsity
                learner = package.build_learner(learner_spec(architecture=architecture))
                self.assertEqual(
                    plain_int(getattr(learner, "actions", None), "Learner.actions"),
                    3,
                    "%r is a rung of the default shape and its learner's head is not three "
                    "wide (docs/L2/agents/shapes.md §2, shapes.md §2)" % (variant,),
                )
                self.assertEqual(
                    plain_int(package.param_count(learner), "param_count"),
                    recorded,
                    "the %r variant reports %r parameters and the count the rung's own row "
                    "records is %d: at A = 3 the output term is arithmetically today's, so no "
                    "recorded count moves (docs/L2/agents/shapes.md §2, sizing.md §6, ASM-10, "
                    "ASM-40)" % (variant, package.param_count(learner), recorded),
                )

    def test_agt17_4_the_decision_space_is_the_shapes_six_indices(self):
        """AGT-17.4 `act` on a `no-limit-100` learner accepts a mask carrying 3, 4 and 5 and answers one of its members, an index at or beyond that shape's range is refused naming the learner's shape and the index, and an index legal on one shape is refused on the other — `learn` applying the same range to `action` and to `next_legal` (`docs/L2/agents/shapes.md` §3, §6, `docs/L3/agents/shapes.md` §3, `sizing.md` §3, `surface.md` §2, §6-§7, ASM-37, D-2).

        The decisions are real ones dealt on the second shape — `engine.new_hand(seed,
        shape=...)` — so their masks are that shape's own `legal_indices` sequence, all six
        indices on a first decision, and the learner the case drives was built on the same
        shape.  The cross-shape half is what the shape's arrival is *for*: an observation
        cannot betray its shape, both declaring the same widths, dtype and vocabulary, so an
        index outside the learner's own range is the one visible contradiction and it is
        refused before any arithmetic (`docs/L2/agents/shapes.md` §3's last bullet).
        """
        package = self.agents()
        rows = shape_decisions(OTHER_SHAPE, 4)
        other = self.build(kind="naive-stack", width=6, depth=1, game=OTHER_SHAPE)
        default = self.build(kind="naive-stack", width=6, depth=1)
        probes = ((3,), (4, 5), (3, 4, 5), (0, 1, 3, 4, 5), SIX_MASK)
        for position, row in enumerate(rows):
            for mask in probes:
                with self.subTest(hand=position, mask=mask):
                    action = plain_int(
                        package.act(other, row["dense"], mask)["action"], "act(...)['action']"
                    )
                    self.assertIn(
                        action,
                        mask,
                        "a six-index learner answered an index outside the mask it was handed "
                        "(surface.md §2, §6, D-2)",
                    )
                    self.assertIn(
                        action,
                        SIX_MASK,
                        "the answer is not one of the second shape's declared indices "
                        "(sizing.md §3, ASM-37)",
                    )
                    self.assertIn(
                        action,
                        tuple(row["mask"]),
                        "the answer is not one of the decision's legal indices "
                        "(features/surface.md §8, surface.md §2)",
                    )
        self.assertEqual(
            plain_int(package.act(other, rows[0]["dense"], (3,))["action"], "act(...)['action']"),
            3,
            "index 3 is a declared index of the second shape and a one-element mask over it "
            "must answer it (docs/L2/agents/shapes.md §3, ASM-37)",
        )
        for mask, token in (
            ((0, 1, 6), "6"),
            ((6,), "6"),
            ((7,), "7"),
            ((-1, 5), "-1"),
        ):
            with self.subTest(mask=mask):
                self.assert_agents_refusal(
                    package.act,
                    other,
                    rows[0]["dense"],
                    mask,
                    entry="act",
                    groups=(("no-limit-100",), ("0..5",), (token,)),
                    label="act on a six-index learner with the mask %r" % (mask,),
                )
        self.assert_agents_refusal(
            package.act,
            default,
            rows[0]["dense"],
            (5,),
            entry="act",
            groups=(("fixed-limit-20",), ("0..2",), ("5",)),
            label="index 5 on a default-shape learner",
        )
        self.assert_agents_refusal(
            package.act,
            default,
            rows[0]["dense"],
            (0, 1, 3),
            entry="act",
            groups=(("fixed-limit-20",), ("3",)),
            label="index 3 on a default-shape learner",
        )
        # `learn` applies the same range to the transition's `action`, `legal` and
        # `next_legal`, so a transition recorded on another shape is refused rather than read
        # as one of this learner's indices (`docs/L2/agents/shapes.md` §3, `surface.md` §7).
        six_index = self.build(kind="naive-stack", width=6, depth=1, game=OTHER_SHAPE)
        result = package.learn(
            six_index,
            [
                transition(
                    rows[0]["dense"], action=5, legal=SIX_MASK, next_legal=SIX_MASK
                )
            ],
        )
        self.assertEqual(
            plain_int(result["transitions"], "learn(...)['transitions']"),
            1,
            "a transition whose action is index 5 was not consumed by a six-index learner "
            "(surface.md §7, docs/L2/agents/shapes.md §3)",
        )
        self.assert_agents_refusal(
            package.learn,
            six_index,
            [transition(rows[0]["dense"], action=5, legal=SIX_MASK, next_legal=(0, 6))],
            entry="learn",
            groups=(("no-limit-100",), ("6",)),
            label="a next_legal naming an index the shape does not have",
        )
        self.assert_agents_refusal(
            package.learn,
            default,
            [transition(rows[0]["dense"], action=5)],
            entry="learn",
            groups=(("fixed-limit-20",), ("5",)),
            label="an action legal on the second shape and refused on the default one",
        )

    def test_agt17_5_the_tie_flag_on_a_flat_value_vector_and_not_on_a_strict_maximum(self):
        """AGT-17.5 with a zero observation of the declared shape, dtype and family — every masked value exactly 0.0 — `act` records `tie` true for every mask of two or more members the greedy arm decides and false on a one-element mask and wherever the exploring arm drew the index, while a strict maximum records false: the flag `records.md` §6, §15 makes the learner's own record is a plain `bool` beside a plain `int` (`docs/L2/agents/shapes.md` §3, `docs/L3/agents/shapes.md` §3, `rule.md` §4-§5, §8, `surface.md` §6, ASM-37).

        Three readings of the one rule.  A learner at schedule position 0 explores at the
        schedule's `start`, which is 1.0, so every decision it takes is the exploring arm's and
        no maximum is consulted: `tie` is false on every mask, one-element or not
        (`rule.md` §4).  A learner held at the annealed end by a quiet batch explores at 5 %, so
        each decision's own keyed draw says which arm decided it — `_epsilon` and
        `_decision_key` are `rule.md` §8's, so the arm is a computation and not a guess — and
        the flag is asserted against it, with the tie-break's smallest-masked-index answer
        where the greedy arm decided.  The strict-maximum half is `rule.decide_greedy`'s own
        input, invented vectors of four and six values, because a learned learner's values are
        not observable through an entry point at all.
        """
        package = self.agents()
        zero, spec = observation_template("dense-numeric")
        self.assertEqual(
            tuple(zero.shape),
            tuple(spec["shape"]),
            "the flat observation is not the shape features.observation_spec declares "
            "(architecture.md §6)",
        )
        self.assertEqual(
            spec["dtype"],
            zero.dtype.name,
            "the flat observation is not the dtype the encoding declares (architecture.md §6)",
        )
        greedy = self.build(kind="naive-stack", width=4, depth=1)
        # (a) At position 0 the rate is the schedule's `start`, so every decision explores.
        epsilon = declared_internal("rule", "_epsilon")
        start = float(schedule()["start"])
        self.assertEqual(
            float(epsilon(0)),
            start,
            "the rate at position 0 is not the schedule's start (rule.md §4, §8)",
        )
        for learner, masks, label in (
            (greedy, NONEMPTY_MASKS, DEFAULT_SHAPE),
            (
                self.build(kind="naive-stack", width=4, depth=1, game=OTHER_SHAPE),
                SIX_MASKS,
                OTHER_SHAPE,
            ),
        ):
            self.assertEqual(
                plain_int(getattr(learner, "position", None), "Learner.position"),
                0,
                "the exploring-arm half reads a learner at position 0 (rule.md §4)",
            )
            for mask in masks:
                with self.subTest(shape=label, mask=mask, arm="exploring"):
                    record = package.act(learner, zero, mask)
                    action = plain_int(record["action"], "act(...)['action']")
                    self.assertIn(action, mask)
                    self.assertIs(
                        type(record["tie"]),
                        bool,
                        "the record's `tie` is not a plain bool (records.md §6, §15, "
                        "surface.md §6)",
                    )
                    self.assertIs(
                        record["tie"],
                        False,
                        "the exploring arm consulted no maximum, so its `tie` flag is false "
                        "whatever the mask (rule.md §4, records.md §15)",
                    )
        # (b) At the annealed end each decision's own keyed draw says which arm decided it,
        # and a zero observation makes every masked value exactly 0.0, so a greedy decision
        # is a tie of the whole mask and answers its smallest index.
        rate = float(epsilon(int(schedule()["samples"])))
        decided = 0
        for shape, masks in ((None, NONEMPTY_MASKS), (OTHER_SHAPE, SIX_MASKS)):
            for seed in TIE_SEEDS:
                learner = self.annealed_learner(
                    "shape-tie-%s-%d" % (shape, seed),
                    {
                        "kind": "naive-stack",
                        "width": 4,
                        "depth": 1,
                        "seed": seed,
                        "game": shape,
                    },
                    quiet=True,
                )
                for mask in masks:
                    with self.subTest(shape=shape, seed=seed, mask=mask):
                        record = package.act(learner, zero, mask)
                        action = plain_int(record["action"], "act(...)['action']")
                        tie = record["tie"]
                        self.assertIs(type(tie), bool)
                        self.assertIn(action, mask)
                        exploring, _draw = decision_draw(
                            seed, "dense-numeric", zero, mask
                        )
                        if exploring < rate:
                            self.assertIs(
                                tie,
                                False,
                                "this decision took the exploring arm (its keyed draw is "
                                "below the annealed rate) and it recorded a tie: no maximum "
                                "having been consulted the flag is false (rule.md §4)",
                            )
                            continue
                        decided += 1
                        self.assertIs(
                            tie,
                            len(mask) >= 2,
                            "a greedy decision over a flat value vector recorded %r: the flag "
                            "is true exactly when two or more masked values sat within the "
                            "tolerance, so a mask of %d member(s) is %r (rule.md §5, "
                            "records.md §6, §15, ASM-37)"
                            % (tie, len(mask), len(mask) >= 2),
                        )
                        self.assertEqual(
                            action,
                            min(mask),
                            "a tie over equal masked values did not answer the smallest "
                            "masked index (rule.md §5)",
                        )
        self.assertGreaterEqual(
            decided,
            60,
            "only %d of these decisions were in the greedy arm, so this case would decide "
            "almost nothing about the tie-break (rule.md §4)" % (decided,),
        )
        # (c) A strict maximum records no tie, at either width and at every mask.
        decide_greedy = declared_internal("rule", "decide_greedy")
        for values, mask, index in (
            ((0.0, 5.0, 4.0), ALL_MASK, 1),
            ((5.0, 4.0, 0.0), ALL_MASK, 0),
            ((0.0, 4.0, 5.0), ALL_MASK, 2),
            ((0.0, 5.0, 4.0), (1,), 1),
            ((0.1, 0.9, 0.5, 0.7, 0.3, 0.2), (2, 3, 4), 3),
            ((-1.0, -2.0, -3.0, -4.0, -0.5, -6.0), (0, 1, 2, 3, 4, 5), 4),
        ):
            with self.subTest(values=values, mask=mask):
                answer, tie = decide_greedy(values, mask)
                self.assertEqual(
                    plain_int(answer, "decide_greedy(...)[0]"),
                    index,
                    "the greedy arm did not answer the strict maximum (rule.md §5)",
                )
                self.assertIs(type(tie), bool)
                self.assertIs(
                    tie,
                    False,
                    "a strict maximum recorded a tie: the flag is true only where two or more "
                    "masked values sat within the tolerance (rule.md §5, records.md §6, §15)",
                )
        for values, mask in (
            ((0.0, 0.0, 0.0), ALL_MASK),
            ((0.0, 0.0, 0.0), (1, 2)),
            ((0.0, 0.0, 0.0, 0.0, 0.0, 0.0), SIX_MASK),
            ((0.0, 0.0, 0.0), (2,)),
        ):
            with self.subTest(values=values, mask=mask, flat=True):
                _answer, tie = decide_greedy(values, mask)
                self.assertIs(
                    tie,
                    len(mask) >= 2,
                    "a flat vector of %d masked value(s) recorded %r (rule.md §5)"
                    % (len(mask), tie),
                )

    def test_agt17_6_the_off_mode_decides_identically_at_two_seeds_and_draws_nothing(self):
        """AGT-17.6 two `as_policy(..., exploration="off")` policies built from one learner and one encoder at two different seeds decide identically over a sequence of real decisions on both shapes, and no generator is drawn from at all: with `rule._draws` replaced by a stub that raises, an `off` policy still decides while a `schedule` policy raises (`docs/L2/agents/shapes.md` §4, `docs/L3/agents/shapes.md` §4, `sizing.md` §4, `rule.md` §4, §7, `surface.md` §10, ASM-2).

        Two halves, each stated as testable: the seed is not read, so two `off` policies at
        different seeds answer one decision alike; and "the draw `schedule` takes is not
        constructed", so the declared internal is the observable — `rule._draws` is reached
        through `declared_internal`, stood aside for one call and restored by `addCleanup`, and
        the `schedule` policy's refusal under it is what shows the stub was standing.  A policy
        of the six-index learner answers one of that shape's own descriptors, which is what
        `features.decode_action(index, shape=<the learner's game>)` means (`rule.md` §7).
        """
        package = self.agents()
        encoder = flat_encoder()
        other_rows = shape_decisions(OTHER_SHAPE, 6)
        default_rows = self.decisions(6)
        learners = (
            (
                "no-limit-100",
                self.build(kind="naive-stack", width=6, depth=1, game=OTHER_SHAPE),
                other_rows,
            ),
            (
                "fixed-limit-20",
                self.build(kind="naive-stack", width=6, depth=1),
                default_rows,
            ),
        )
        for label, learner, rows in learners:
            with self.subTest(shape=label):
                first = package.as_policy(learner, encoder, LEARNER_SEED, exploration="off")
                second = package.as_policy(learner, encoder, OTHER_SEED, exploration="off")
                for row in rows:
                    answer = first(row["readout"], row["legal"])
                    self.assertEqual(
                        answer,
                        second(row["readout"], row["legal"]),
                        "two `off` policies at different seeds answered one decision "
                        "differently, so the mode's seed is being read (shapes.md §4, "
                        "surface.md §10, ASM-2)",
                    )
                    self.assertIn(
                        answer,
                        tuple(row["legal"]),
                        "an `off` policy answered a descriptor outside `legal_actions` "
                        "(surface.md §10, D-2)",
                    )
        # The draw is genuinely not taken: with `rule._draws` replaced by a stub that raises,
        # `off` decides and `schedule` raises.
        module = declared_module("rule")
        original = declared_internal("rule", "_draws")
        self.assertIs(
            getattr(module, "_draws", None),
            original,
            "agents.rule._draws is not the name `declared_internal` read, so the stub below "
            "would not stand in for the draw a decision takes (rule.md §8)",
        )

        def forbidden(*_args, **_kwargs):
            raise AssertionError(
                "rule._draws was drawn from on a policy whose mode is `off`, and no "
                "generator is constructed there (shapes.md §4, sizing.md §4)"
            )

        setattr(module, "_draws", forbidden)
        self.addCleanup(setattr, module, "_draws", original)
        for label, learner, rows in learners:
            with self.subTest(shape=label, draws="refused"):
                off = package.as_policy(learner, encoder, LEARNER_SEED, exploration="off")
                for row in rows:
                    self.assertIn(
                        off(row["readout"], row["legal"]),
                        tuple(row["legal"]),
                        "an `off` policy stopped deciding once the draw was unreachable, so "
                        "it was taking the draw (shapes.md §4, sizing.md §4)",
                    )
                scheduled = package.as_policy(
                    learner, encoder, LEARNER_SEED, exploration="schedule"
                )
                with self.assertRaises(
                    AssertionError,
                    msg="a `schedule` policy decided although the keyed draw its arm takes "
                    "was unreachable, so this case's stub was not standing and the `off` "
                    "answers above prove nothing (rule.md §4, shapes.md §4)",
                ):
                    scheduled(rows[0]["readout"], rows[0]["legal"])
        self.assertIs(
            getattr(module, "_draws"),
            forbidden,
            "the stub was replaced before the assertions finished, so the `off` answers "
            "were not taken while it stood (rule.md §4)",
        )

    def test_agt17_7_the_mode_refusal_and_the_default_schedule(self):
        """AGT-17.7 an exploration mode outside `{"schedule", "off"}` is refused naming `as_policy`, the offending value and both declared modes, while `exploration="schedule"` and the absent argument behave identically — and no mode edits the hyper block, whose exploration stays the six declarations' one schedule (`docs/L2/agents/shapes.md` §4, §6, `docs/L3/agents/shapes.md` §4, §6, `surface.md` §10, `rule.md` §6, `errors.md` §2-§3, D-19).

        The refusal is `UnknownExploration`'s, one of the two classes `errors.md` §2 gains with
        the second shape, so it is asserted as this module's own — a caller catching
        `AgentsError` must catch it — and the two declared modes are in the message because a
        value the caller wrote is never defaulted onto one (`surface.md` §1).  The identity of
        `schedule` and the absent argument is the default's own claim: the fourth argument is
        already `schedule` when the caller passes none.
        """
        package = self.agents()
        learner = self.build(kind="naive-stack", width=6, depth=1)
        encoder = flat_encoder()
        before = schedule()
        cases = (
            ("an undeclared mode", "greedy", "greedy"),
            ("a mode spelled with a capital", "Schedule", "schedule"),
            ("an empty string", "", "''"),
            ("None", None, "none"),
            ("an integer", 1, "1"),
            ("a bool", True, "true"),
        )
        for label, value, token in cases:
            with self.subTest(case=label):
                self.assert_agents_refusal(
                    package.as_policy,
                    learner,
                    encoder,
                    LEARNER_SEED,
                    value,
                    entry="as_policy",
                    groups=(
                        ("exploration",),
                        ("schedule",),
                        ("off",),
                        (token,),
                    ),
                    label="as_policy(exploration=%r)" % (value,),
                )
        absent = package.as_policy(learner, encoder, LEARNER_SEED)
        explicit = package.as_policy(
            learner, encoder, LEARNER_SEED, exploration="schedule"
        )
        for row in self.decisions(6):
            with self.subTest(hand=row["readout"]["hole"]):
                self.assertEqual(
                    absent(row["readout"], row["legal"]),
                    explicit(row["readout"], row["legal"]),
                    "`exploration='schedule'` and the absent argument did not behave "
                    "identically, and the two name one mode (surface.md §10, shapes.md §4)",
                )
        package.as_policy(learner, encoder, LEARNER_SEED, exploration="off")
        self.assertEqual(
            schedule(),
            before,
            "building an `off` policy moved the hyper block's exploration schedule: the mode "
            "is the policy's and never the hyper block's (rule.md §6, shapes.md §4, D-19)",
        )
        self.assertEqual(
            tuple(package.learners()["hyper"]["exploration"]),
            ("start", "end", "samples"),
            "the schedule's three keys are the declared ones, and no mode adds one "
            "(rule.md §6, surface.md §3)",
        )


if __name__ == "__main__":
    unittest.main()
