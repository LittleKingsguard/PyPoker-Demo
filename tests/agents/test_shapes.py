"""AGT-17 — the declared game shape at this surface: the width, the head, the count, the index space, the tie and the mode.

Drives `docs/L2/agents/shapes.md` §1-§4, §6-§7 and `docs/L3/agents/shapes.md` §1-§4, §6
beside the L1 statements the same contracts are published under — `docs/L1/shapes.md` §2,
§5, **§8**, `docs/L1/sizing.md` §3, §4, §6, `docs/L1/architecture.md` §2, §5, `docs/L1/
records.md` §6, §15, `docs/L1/ladder.md` §3-§4 — `docs/L2/features/capacity.md` §2, §5 and
`strata/decisions.md` D-29, ASM-37, ASM-40 and ASM-44: the catalogue's two names are
restated once and default first, while the head's width is a **reading** of the shape's
descriptor count (`shapes.md` §1); every kind ends in `W → A`, so the parameter count's
output term is `A·W + A`, and at `A = 3` the formula is arithmetically today's, which is why
no recorded count moves (§2); a kind's declared `observation_size` is the **default** shape's
203 or 96 and stays so, while a learner on another shape takes its input width from that
shape's encoder — 329 dense and a vocabulary of 96 on `no-limit-100` — and an encoder-less
build on one is refused by name, so the input term `I·W` is the shape's too
(`docs/L1/shapes.md` §8, ASM-44, `docs/L2/features/capacity.md` §2, §5); `act` and `learn`
decide over `0 .. A−1` in the shape's declared order, which is the measured price order and
deliberately not monotone in amount, and a mask naming an index the learner's shape does not
have is refused naming that shape, its range and the index before any arithmetic (§3); `act`
records `tie`, true exactly when the greedy arm's tie-break and not a strict maximum chose the
index (§3, `records.md` §6, §15); and `as_policy`'s mode is `schedule` or `off`, `off` taking
the masked maximum and the tie-break alone and constructing no generator at all (§4).

What is **not** asserted here belongs to the two neighbour files: the container's
`format_version` 3 and 4 and its `game` field are AGT-7.18-7.23 in `test_checkpoint.py`,
because a shape case there reads the same container surgery the rest of AGT-7 does, and the
width's *values* are `features`' and `engine`'s (`docs/L2/features/shapes.md` §2, §5): this
battery reads them through `features.action_space(shape=...)`,
`features.observation_spec(build_encoder(name, shape=...))` and `engine.new_hand(seed,
shape=...)`, the three granted calls, and writes a `3`, a `6`, a `203` or a `329` down only
where a design document states one (`docs/L2/agents/shapes.md` §2's table,
`docs/L2/features/capacity.md` §2's).  AGT-17.10 does read a container, and only for the one
field the width reaches — `representation.size` — which AGT-7's version cases do not state.

Two spellings below the ten entry points are read, and both are contract:
`model._param_count_for` and `model._initial_parameters`, which `rule.md` §8 declares and
whose trailing `actions=None` is `docs/L3/agents/shapes.md` §2's, and the layout field
`actions` with the `w_out`/`b_out` offsets beside it, which `docs/L3/agents/shapes.md` §2
states as the one thing about the output layer that is not a constant of the kind. Neither
internal carries an input width — both read the kind's declared `observation_size` — so
AGT-17.2 asserts what they report against that size and the learner's own count against the
shape's (`docs/L1/shapes.md` §8, ASM-44). The one internal a case stands **aside** —
`rule._draws` — is reached through `declared_internal` and restored by `addCleanup`, so the
`off` mode's "not constructed at all" is observed rather than assumed (`shapes.md` §4,
`sizing.md` §4).
"""

import os
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
    SIX_SEAT_SHAPE,
    TIE_SEEDS,
    AgentsCase,
    container_document,
    declared_internal,
    declared_module,
    decision_draw,
    family_of,
    features,
    flat_encoder,
    learner_spec,
    observation_template,
    plain_int,
    schedule,
    shape_decisions,
    shape_encoder,
    transition,
    write_container,
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


def declared_count(architectures, kind, width, depth, sparsity, actions, size=None):
    """`architecture.md` §5's sum arithmetic, from a declared row, `A = actions` and `I = size`.

    The input block first (`I·W + W` for the dense family, `V·W` for a token one), then
    `D·(W² + W)` — `D·(k + W)` for `sparse`, `k = round((1 − s)·W²)` — then the output term
    `A·W + A`.  No part of this arithmetic is a copied count: the caller states the width,
    the depth, the sparsity and the shape's `A`, and the constant that remains is
    `architecture.md` §5's formula itself.

    `size` is `I` — or `V`, the token vocabulary — and `None` means the kind's declared
    `observation_size`, which is the **default** shape's 203 or 96 and is the only value an
    encoder-less build is ever sized from (`docs/L1/shapes.md` §8, ASM-44,
    `docs/L2/agents/shapes.md` §2).  A caller on any other shape passes that shape's
    encoder's width or vocabulary, because the input term is the shape's too: 329 dense
    over 66 history slots on `no-limit-100` against the default's 203 over 24
    (`docs/L2/features/capacity.md` §2, ASM-44).
    """
    row = architectures[kind]
    if size is None:
        size = int(row["observation_size"])
    dense = row["observation"] == "dense-numeric"
    layer_width = int(width)
    input_term = int(size) * layer_width + (layer_width if dense else 0)
    if kind == "sparse":
        kept = round((1.0 - float(sparsity)) * layer_width * layer_width)
        trunk_term = int(depth) * (kept + layer_width)
    else:
        trunk_term = int(depth) * (layer_width * layer_width + layer_width)
    return input_term + trunk_term + int(actions) * layer_width + int(actions)


def shape_size(kind, shape=None):
    """`I` — or `V` — the input width a learner of `kind` on `shape` is sized by.

    Read off **that shape's** encoder and never written down: a dense family's width is
    `observation_spec(encoder)["shape"][0]` and a token family's is its `["vocabulary"]`,
    which is the number `build_learner` sizes a token learner by and not its sequence
    length (`docs/L1/shapes.md` §8, ASM-44, `docs/L2/agents/shapes.md` §2,
    `docs/L2/features/capacity.md` §2).  `shape=None` is the default shape's, which is the
    kind's declared `observation_size`.
    """
    family = family_of(kind)
    spec = features().observation_spec(
        shape_encoder("flat-numeric" if family == "dense-numeric" else "card-tokens", shape)
    )
    if family == "dense-numeric":
        return int(tuple(spec["shape"])[0])
    return int(spec["vocabulary"])


def kind_encoder(kind, shape=None):
    """The encoder a learner of `kind` on `shape` must be handed (`shapes.md` §2, §8)."""
    family = family_of(kind)
    return shape_encoder(
        "flat-numeric" if family == "dense-numeric" else "card-tokens", shape
    )


class ShapeAxisTest(AgentsCase):
    """The head, the count, the six-index decision space, the `tie` flag and the exploration mode."""

    def test_agt17_1_the_head_is_the_shapes(self):
        """AGT-17.1 a spec naming `no-limit-100` builds a learner whose `actions` is that shape's six and whose `param_count` is `A·W + A` with `A = 6` over that shape's own input width, while the same spec with no `game` reports the default shape's three and today's count — each computed from the spec's `width`, its `depth`, its shape's input width and its `A`, never from a copied constant — and the two counts differ by exactly the wider input block and the extra head term (`docs/L1/shapes.md` §8, ASM-44, `docs/L2/agents/shapes.md` §1-§2, `docs/L3/agents/shapes.md` §1-§2, `docs/L2/features/capacity.md` §2, `sizing.md` §6, `architecture.md` §5, ASM-40, D-29).

        The two shapes' widths are the design's — three and six, `docs/L2/agents/shapes.md` §2's
        table — and they are read here through `features.action_space` as well, so a shape
        whose declared descriptor count moved is red in this case and not in a copied
        literal.  `Learner.game` and `Learner.actions` are the two fields `shapes.md` §2 makes
        the learner's own: it "carries the resolved `A` and its shape's name", which is what
        `act`, `learn`, `as_policy` and `save` read and what no arithmetic branches on.

        The second shape's learner is handed **that shape's** encoder, because the kind's
        declared `observation_size` is the default shape's: 203 dense over 24 history slots
        against `no-limit-100`'s 329 over 66, so the input term `I·W` is the shape's too and
        the two counts differ by `(I₂ − I₁)·W` as well as by `(A₂ − A₁)·W + (A₂ − A₁)`
        (`docs/L1/shapes.md` §8, ASM-44, `docs/L2/features/capacity.md` §2).  The
        default-shape arm stays **encoder-less** on purpose: absence of a shape and absence
        of an encoder are both the default, and that arm is the "absence is the default" case
        (`docs/L2/agents/shapes.md` §2).
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
                other = self.build(
                    kind=kind,
                    width=width,
                    depth=depth,
                    game=OTHER_SHAPE,
                    encoder=kind_encoder(kind, OTHER_SHAPE),
                )
                default = self.build(kind=kind, width=width, depth=depth)
                input_default = shape_size(kind, None)
                input_other = shape_size(kind, OTHER_SHAPE)
                self.assertEqual(
                    input_default,
                    int(architectures[kind]["observation_size"]),
                    "the default shape's encoder width is the kind's declared "
                    "observation_size, which is that shape's and no other's (docs/L1/"
                    "shapes.md §8, ASM-44): %r against %r"
                    % (input_default, architectures[kind]["observation_size"]),
                )
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
                    declared_count(
                        architectures, kind, width, depth, 0.0, six, input_other
                    ),
                    "the %r learner's count is not architecture.md §5's sum over that "
                    "shape's input width %d with the output term A·W + A at A = %d"
                    % (kind, input_other, six),
                )
                self.assertEqual(
                    plain_int(package.param_count(default), "param_count"),
                    declared_count(architectures, kind, width, depth, 0.0, three),
                    "the default-shape %r learner's count is not the same formula at A = %d, "
                    "which is today's (sizing.md §6, ASM-40)" % (kind, three),
                )
                self.assertEqual(
                    package.param_count(other) - package.param_count(default),
                    (input_other - input_default) * width
                    + (six - three) * width
                    + (six - three),
                    "the shape moves the input block and the output term, so the two counts "
                    "differ by (I₂ − I₁)·W for the wider observation plus the three extra "
                    "head rows and their bias, and by nothing else (docs/L1/shapes.md §8, "
                    "ASM-44, docs/L3/agents/shapes.md §2, ASM-40): %r against %r for "
                    "I = %d and %d at W = %d"
                    % (
                        package.param_count(other) - package.param_count(default),
                        (input_other - input_default) * width
                        + (six - three) * width
                        + (six - three),
                        input_default,
                        input_other,
                        width,
                    ),
                )

    def test_agt17_2_the_output_block_is_actions_times_width_plus_actions(self):
        """AGT-17.2 on a dense kind and a token kind at both shapes the output block's contribution is `actions·width + actions`: `layout.w_out` is `(offset, A·W)`, `b_out` begins where it ends and sits `A` slots before `count`, `model._param_count_for` and `model._initial_parameters` are the default shape's formula, and the shape's own count exceeds it by exactly the wider input block — the `W → A` output layer of `docs/L3/agents/shapes.md` §2 (`architecture.md` §2, §5, `sizing.md` §6, `rule.md` §8, `docs/L1/shapes.md` §8, ASM-44, ASM-40, `docs/L2/features/capacity.md` §2).

        The layout is the object `docs/L3/agents/shapes.md` §2 makes the statement about —
        "`w_out` is `(offset, actions·W)`, `b_out` takes `actions` slots, and `count` ends with
        `A·W + A`" — and both backends read `layout.actions` where they read a `3` before.  The
        two internals are `rule.md` §8's, called with the trailing `actions` that
        `docs/L3/agents/shapes.md` §2 adds to them, and `actions=None` is asserted to be the
        default shape's reading rather than a constant of its own.

        Neither internal carries an input width: both read the kind's declared
        `observation_size`, which `docs/L1/shapes.md` §8 fixes as the **default** shape's, so
        on `no-limit-100` their count is the default shape's and the learner's own count is
        that plus `(I₂ − I₁)·W` — the widened input block and nothing else, since the trunk
        and the head do not read an input width (ASM-44, `docs/L2/features/capacity.md` §2).
        The second shape's learner is handed that shape's encoder, which is the size it is
        built at (`docs/L2/agents/shapes.md` §2).
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
                    spec = learner_spec(architecture=architecture, game=shape)
                    if shape is not None:
                        spec["encoder"] = kind_encoder(kind, shape)
                    learner = package.build_learner(spec)
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
                    # The two internals read the kind's declared observation_size, which is
                    # the default shape's, so what they report is the default shape's count
                    # and the shape's own is that plus the wider input block (`docs/L1/
                    # shapes.md` §8, ASM-44, `docs/L2/features/capacity.md` §2).
                    default_size = int(
                        package.learners()["architectures"][kind]["observation_size"]
                    )
                    shape_input = shape_size(kind, shape)
                    self.assertEqual(
                        shape_input,
                        int(layout.input_dim),
                        "the learner's input width is not the one its shape's encoder "
                        "declares (docs/L1/shapes.md §8, ASM-44): %r against %r"
                        % (int(layout.input_dim), shape_input),
                    )
                    declared = declared_count(
                        package.learners()["architectures"],
                        kind,
                        width,
                        depth,
                        sparsity,
                        expected,
                        default_size,
                    )
                    self.assertEqual(
                        int(count_for(kind, width, depth, sparsity, actions=expected)),
                        declared,
                        "model._param_count_for does not report architecture.md §5's sum at "
                        "the kind's declared observation_size %d, which is the default "
                        "shape's and the only width that internal carries (rule.md §8, "
                        "docs/L1/shapes.md §8, ASM-44)" % (default_size,),
                    )
                    self.assertEqual(
                        package.param_count(learner) - declared,
                        (shape_input - default_size) * width,
                        "the shape's count is not the default shape's formula plus the wider "
                        "input block (I₂ − I₁)·W, so the shape reached the measurement through "
                        "something other than the input width (docs/L1/shapes.md §8, ASM-44): "
                        "%r against %r for I = %d and %d at W = %d"
                        % (
                            package.param_count(learner) - declared,
                            (shape_input - default_size) * width,
                            default_size,
                            shape_input,
                            width,
                        ),
                    )
                    values = initial(
                        kind, width, depth, sparsity, LEARNER_SEED, actions=expected
                    )
                    self.assertEqual(
                        int(values.shape[0]),
                        declared,
                        "the initial draw is not as long as the count architecture.md §5's "
                        "sum at the kind's declared observation_size gives, so the output "
                        "layer was not drawn at (W, A) (architecture.md §4's step 3, "
                        "docs/L3/agents/shapes.md §2)",
                    )
                    if shape is None:
                        self.assertEqual(
                            int(values.shape[0]),
                            package.param_count(learner),
                            "an encoder-less build is sized from the kind's declared "
                            "observation_size, so its count and the draw's length are one "
                            "number (docs/L1/shapes.md §8, ASM-44)",
                        )
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
        shape and handed that shape's encoder.  The cross-shape half is two refusals: an
        observation of one shape handed to the other shape's learner is refused naming both
        widths, since a shape's history capacity is its own and so is its observation's width
        — 329 dense on `no-limit-100` against 203 on the default (`docs/L1/shapes.md` §8,
        ASM-44, `docs/L2/features/capacity.md` §2) — and, where the widths do agree, the shape
        shows in the **mask**: an index outside the learner's own range is the visible
        contradiction and it is refused before any arithmetic (`docs/L2/agents/shapes.md` §3's
        last bullet).
        """
        package = self.agents()
        rows = shape_decisions(OTHER_SHAPE, 4)
        other = self.build(
            kind="naive-stack",
            width=6,
            depth=1,
            game=OTHER_SHAPE,
            encoder=kind_encoder("naive-stack", OTHER_SHAPE),
        )
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
        # The two shapes' observations no longer agree in width, so a second-shape
        # observation is refused by the default-shape learner naming both widths, before any
        # mask is read (`docs/L1/shapes.md` §8, ASM-44, `docs/L2/agents/shapes.md` §3).
        self.assertEqual(
            int(rows[0]["dense"].shape[0]),
            shape_size("naive-stack", OTHER_SHAPE),
            "the second shape's decision is not encoded at that shape's own width, so this "
            "case would not be handing the default-shape learner a %r observation "
            "(docs/L1/shapes.md §8, ASM-44): %r"
            % (OTHER_SHAPE, rows[0]["dense"].shape),
        )
        self.assert_agents_refusal(
            package.act,
            default,
            rows[0]["dense"],
            (5,),
            entry="act",
            groups=(
                (str(shape_size("naive-stack", OTHER_SHAPE)),),
                (str(shape_size("naive-stack", None)),),
            ),
            label="a %r observation handed to a %r learner"
            % (OTHER_SHAPE, DEFAULT_SHAPE),
        )
        # The index range is the learner's shape's **where the widths agree**, which is the
        # half the shape's arrival is for: a default-shape observation and a mask naming an
        # index the default shape does not have is refused naming the shape and the index
        # (`docs/L2/agents/shapes.md` §3, ASM-37).
        default_row = self.decisions(1)[0]
        self.assertEqual(
            int(default_row["dense"].shape[0]),
            shape_size("naive-stack", None),
            "the default shape's decision is not encoded at that shape's own width "
            "(docs/L1/shapes.md §8, ASM-44): %r" % (default_row["dense"].shape,),
        )
        self.assert_agents_refusal(
            package.act,
            default,
            default_row["dense"],
            (5,),
            entry="act",
            groups=(("fixed-limit-20",), ("0..2",), ("5",)),
            label="index 5 on a default-shape learner",
        )
        self.assert_agents_refusal(
            package.act,
            default,
            default_row["dense"],
            (0, 1, 3),
            entry="act",
            groups=(("fixed-limit-20",), ("3",)),
            label="index 3 on a default-shape learner",
        )
        # `learn` applies the same range to the transition's `action`, `legal` and
        # `next_legal`, so a transition recorded on another shape is refused rather than read
        # as one of this learner's indices (`docs/L2/agents/shapes.md` §3, `surface.md` §7).
        six_index = self.build(
            kind="naive-stack",
            width=6,
            depth=1,
            game=OTHER_SHAPE,
            encoder=kind_encoder("naive-stack", OTHER_SHAPE),
        )
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
            [transition(default_row["dense"], action=5)],
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
        other_zero, other_spec = observation_template("dense-numeric", OTHER_SHAPE)
        for shape, observation, declared in (
            (DEFAULT_SHAPE, zero, spec),
            (OTHER_SHAPE, other_zero, other_spec),
        ):
            with self.subTest(shape=shape, flat=True):
                self.assertEqual(
                    tuple(observation.shape),
                    tuple(declared["shape"]),
                    "the flat observation is not the shape features.observation_spec declares "
                    "(architecture.md §6, docs/L1/shapes.md §8, ASM-44): %r on %r"
                    % (observation.shape, shape),
                )
                self.assertEqual(
                    declared["dtype"],
                    observation.dtype.name,
                    "the flat observation is not the dtype the encoding declares "
                    "(architecture.md §6)",
                )
                self.assertEqual(
                    int(observation.shape[0]),
                    shape_size("naive-stack", shape),
                    "the flat observation is not as wide as that shape's dense encoding "
                    "declares, so a learner of that shape would refuse it (docs/L1/shapes.md "
                    "§8, ASM-44, docs/L2/features/capacity.md §2): %r on %r"
                    % (observation.shape, shape),
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
        for learner, masks, sample, label in (
            (greedy, NONEMPTY_MASKS, zero, DEFAULT_SHAPE),
            (
                self.build(
                    kind="naive-stack",
                    width=4,
                    depth=1,
                    game=OTHER_SHAPE,
                    encoder=kind_encoder("naive-stack", OTHER_SHAPE),
                ),
                SIX_MASKS,
                other_zero,
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
                    record = package.act(learner, sample, mask)
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
        for shape, masks, sample in (
            (None, NONEMPTY_MASKS, zero),
            (OTHER_SHAPE, SIX_MASKS, other_zero),
        ):
            for seed in TIE_SEEDS:
                kwargs = {
                    "kind": "naive-stack",
                    "width": 4,
                    "depth": 1,
                    "seed": seed,
                }
                if shape is not None:
                    # A learner of the second shape is sized from that shape's encoder, and
                    # its zero observation is that shape's own width (`docs/L1/shapes.md` §8,
                    # ASM-44, `docs/L2/agents/shapes.md` §2).
                    kwargs["game"] = shape
                    kwargs["encoder"] = kind_encoder("naive-stack", shape)
                learner = self.annealed_learner(
                    "shape-tie-%s-%d" % (shape, seed), kwargs, quiet=True
                )
                for mask in masks:
                    with self.subTest(shape=shape, seed=seed, mask=mask):
                        record = package.act(learner, sample, mask)
                        action = plain_int(record["action"], "act(...)['action']")
                        tie = record["tie"]
                        self.assertIs(type(tie), bool)
                        self.assertIn(action, mask)
                        exploring, _draw = decision_draw(
                            seed, "dense-numeric", sample, mask
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
        other_rows = shape_decisions(OTHER_SHAPE, 6)
        default_rows = self.decisions(6)
        learners = (
            (
                "no-limit-100",
                self.build(
                    kind="naive-stack",
                    width=6,
                    depth=1,
                    game=OTHER_SHAPE,
                    encoder=kind_encoder("naive-stack", OTHER_SHAPE),
                ),
                other_rows,
            ),
            (
                "fixed-limit-20",
                self.build(kind="naive-stack", width=6, depth=1),
                default_rows,
            ),
        )
        for label, learner, rows in learners:
            # The encoder is the shape's learner's own: `as_policy` compares the encoder's
            # size with the learner's, which is 329 for a widened learner and 203 for the
            # default one (`surface.md` §10, `docs/L2/agents/shapes.md` §2).
            encoder = kind_encoder("naive-stack", learner.game)
            self.assertEqual(
                int(features().observation_spec(encoder)["shape"][0]),
                int(learner.size),
                "the policy's encoder is not the one the learner was built with, so "
                "`as_policy` would refuse it rather than decide (surface.md §10, "
                "docs/L1/shapes.md §8, ASM-44): encoders %r and learner %r"
                % (int(features().observation_spec(encoder)["shape"][0]), learner.size),
            )
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
                encoder = kind_encoder("naive-stack", learner.game)
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

    def test_agt17_8_a_learner_on_the_second_shape_is_built_at_that_shapes_width(self):
        """AGT-17.8 a learner built on `no-limit-100` with **that shape's** encoder is built at that shape's own input width — 329 dense over 66 history slots, so `param_count` at width 36, depth 2 is `11880 + 2664 + 222 = 14,766` — while the same spec with no `game` is refused only because 329 ≠ 203, the default shape's equality, and a token learner on that shape is sized by its **vocabulary 96** and never by its 82-token sequence (`docs/L1/shapes.md` §8, ASM-44, `docs/L2/agents/shapes.md` §2, `docs/L2/features/capacity.md` §2, `sizing.md` §6, `architecture.md` §5, `surface.md` §4, ASM-40).

        The kind's declared `observation_size` is the **default** shape's 203 or 96 and stays
        so; a learner on any other shape takes its input width from that shape's encoder, and
        the input term `I·W` moves with it — `329·36 + 36 = 11,880` against the default's
        `203·36 + 36 = 7,344` — while the trunk `2·(36² + 36) = 2,664` and the head
        `6·36 + 6 = 222` follow the shape's own `A` (`docs/L1/shapes.md` §8, ASM-44,
        `docs/L2/agents/shapes.md` §2, `docs/L2/features/capacity.md` §2).  A token learner's
        size is its **vocabulary**, never its sequence length, which is why the widened
        `card-tokens` observation is 82 long and its learner is still 96 wide
        (`architecture.md` §6, `encodings.md` §1, §4, D-3).  Both widths are read out of
        `features.observation_spec`, so no 329 and no 82 is a literal of this case.
        """
        package = self.agents()
        architectures = package.learners()["architectures"]
        six = head_width(OTHER_SHAPE)
        width = shape_size("naive-stack", OTHER_SHAPE)
        default_width = int(architectures["naive-stack"]["observation_size"])
        encoder = shape_encoder("flat-numeric", OTHER_SHAPE)
        spec = learner_spec(
            kind="naive-stack", width=36, depth=2, game=OTHER_SHAPE, encoder=encoder
        )
        learner = package.build_learner(spec)
        layout = getattr(learner, "layout", None)
        self.assertIsNotNone(
            layout,
            "the learner carries no layout, so its input width cannot be read "
            "(docs/L3/agents/shapes.md §2)",
        )
        self.assertEqual(
            plain_int(layout.input_dim, "layout.input_dim"),
            width,
            "a learner on %r is not built at that shape's own input width — the one its "
            "encoder's observation_spec declares — so its input block is not that shape's "
            "(docs/L1/shapes.md §8, ASM-44, docs/L2/features/capacity.md §2): %r against %r"
            % (OTHER_SHAPE, layout.input_dim, width),
        )
        self.assertEqual(
            int(tuple(getattr(learner, "shape", ()))[0]),
            width,
            "the learner's declared `shape` is not one observation of that shape's own "
            "width, which is what an observation is checked against (architecture.md §6, "
            "docs/L1/shapes.md §8, ASM-44): %r against %r"
            % (getattr(learner, "shape", None), (width,)),
        )
        self.assertEqual(
            plain_int(package.param_count(learner), "param_count"),
            14766,
            "a naive-stack learner on %r at width 36 and depth 2 reports %r parameters and "
            "architecture.md §5's sum at that shape's input width is 11880 + 2664 + 222 = "
            "14,766 — the input block 329·36 + 36, the trunk 2·(36² + 36) and the head "
            "6·36 + 6 (docs/L1/shapes.md §8, ASM-44, docs/L2/agents/shapes.md §2, "
            "docs/L2/features/capacity.md §2, sizing.md §6): %r"
            % (
                OTHER_SHAPE,
                package.param_count(learner),
                package.param_count(learner),
            ),
        )
        # The default shape's equality is untouched: the *same* encoder with no `game` is
        # refused only because 329 is not 203 (`docs/L1/shapes.md` §8, ASM-44).
        self.assert_agents_refusal(
            package.build_learner,
            learner_spec(kind="naive-stack", width=36, depth=2, encoder=encoder),
            entry="build_learner",
            groups=(("encoder",), (str(width),), (str(default_width),)),
            label="the second shape's encoder on the default shape, where the kind's "
            "declared %d is still an equality" % (default_width,),
        )
        token = shape_encoder("card-tokens", OTHER_SHAPE)
        token_spec = features().observation_spec(token)
        vocabulary = int(token_spec["vocabulary"])
        sequence = int(tuple(token_spec["shape"])[0])
        token_learner = package.build_learner(
            learner_spec(kind="deep", width=50, depth=2, game=OTHER_SHAPE, encoder=token)
        )
        self.assertEqual(
            plain_int(getattr(token_learner, "size", None), "Learner.size"),
            vocabulary,
            "a token learner on %r is sized by its encoder's **vocabulary** and not by its "
            "sequence length (architecture.md §6, encodings.md §1, §4, D-3): %r against %r"
            % (OTHER_SHAPE, getattr(token_learner, "size", None), vocabulary),
        )
        self.assertEqual(
            int(tuple(getattr(token_learner, "shape", ()))[0]),
            sequence,
            "that learner's declared `shape` is not the token sequence its shape's encoder "
            "encodes, which is a different number from its vocabulary (architecture.md §6, "
            "docs/L2/features/capacity.md §2): %r against %r"
            % (getattr(token_learner, "shape", None), (sequence,)),
        )
        self.assertEqual(
            plain_int(package.param_count(token_learner), "param_count"),
            vocabulary * 50 + 2 * (50 * 50 + 50) + six * 50 + six,
            "a token learner's input block is V·W with V the vocabulary %d, not S·W with S "
            "the sequence length %d, so its count is V·W + D·(W² + W) + A·W + A "
            "(architecture.md §5-§6, sizing.md §6, ASM-44): %r against %r"
            % (
                vocabulary,
                sequence,
                package.param_count(token_learner),
                vocabulary * 50 + 2 * (50 * 50 + 50) + six * 50 + six,
            ),
        )

    def test_agt17_9_an_encoderless_spec_naming_a_non_default_shape_is_refused_by_name(self):
        """AGT-17.9 a spec naming a non-default shape and carrying **no** `encoder` is refused by this module, naming `build_learner`, that shape, the kind's declared 203 and the word `encoder`, and nothing is built at 203 — while the same spec with that shape's encoder builds (`docs/L1/shapes.md` §8, ASM-44, `docs/L2/agents/shapes.md` §2, `docs/L2/features/capacity.md` §2, §5, `surface.md` §4, §9, `errors.md` §2-§3, D-29).

        The declared size is the default shape's and not that shape's, so there is no width
        an encoder-less build could be sized at: the spec is refused **by name** rather than
        sized at a number that belongs to another game, which would be an observation of one
        shape fed to a head of another (`docs/L1/shapes.md` §8, ASM-44).  The refusal is
        `AgentsError`'s, so a caller catching that root catches it, and the encoder-bearing
        twin is built and measured, which is how "nothing is built" is asserted without
        reading the module's internals (`errors.md` §2, `surface.md` §1).  Both families are
        driven, because the kind's declared size is 203 for the dense one and 96 for the
        token ones and neither is that shape's (`architecture.md` §1, §6, ASM-44).
        """
        package = self.agents()
        architectures = package.learners()["architectures"]
        for kind in ("naive-stack", "deep"):
            with self.subTest(kind=kind):
                declared = int(architectures[kind]["observation_size"])
                spec = learner_spec(kind=kind, width=6, depth=1, game=OTHER_SHAPE)
                self.assertNotIn(
                    "encoder",
                    spec,
                    "this case's spec carries an encoder, so it is not the encoder-less "
                    "one `docs/L1/shapes.md` §8 refuses (ASM-44): %r" % (spec,),
                )
                message = self.assert_agents_refusal(
                    package.build_learner,
                    spec,
                    entry="build_learner",
                    groups=((OTHER_SHAPE,), (str(declared),), ("encoder",)),
                    label="an encoder-less spec naming %r for the kind %r"
                    % (OTHER_SHAPE, kind),
                )
                self.assertIn(
                    DEFAULT_SHAPE,
                    message,
                    "the refusal does not name the default shape whose %d the kind declares, "
                    "so a reader cannot tell which shape that number belongs to "
                    "(docs/L1/shapes.md §8, ASM-44): %r" % (declared, message),
                )
                built = package.build_learner(
                    learner_spec(
                        kind=kind,
                        width=6,
                        depth=1,
                        game=OTHER_SHAPE,
                        encoder=kind_encoder(kind, OTHER_SHAPE),
                    )
                )
                self.assertEqual(
                    plain_int(package.param_count(built), "param_count"),
                    declared_count(
                        architectures,
                        kind,
                        6,
                        1,
                        0.0,
                        head_width(OTHER_SHAPE),
                        shape_size(kind, OTHER_SHAPE),
                    ),
                    "the same spec carrying that shape's encoder does not build a learner of "
                    "that shape, so the refusal above is not the encoder's absence alone "
                    "(surface.md §4, docs/L1/shapes.md §8, ASM-44)",
                )
                self.assertEqual(
                    getattr(built, "game", None),
                    OTHER_SHAPE,
                    "the learner built from the twin spec does not carry the shape the "
                    "refused one named (shapes.md §2, D-29)",
                )

    def test_agt17_10_the_container_carries_the_shapes_own_width(self):
        """AGT-17.10 a checkpoint of a `no-limit-100` learner is a version-4 container recording that shape in `game`, its **own** width in `representation.size` and `representation.shape`, and the count that width gives in `params.count`; `load(None, path)` restores a learner at that count which decides as the saved one, while a copy whose `representation.size` still records 329 and whose `params.count` is the default shape's 10,119 is refused naming `params.count` and both numbers (`docs/L1/shapes.md` §8, ASM-44, `docs/L2/agents/shapes.md` §2, `docs/L2/features/capacity.md` §2, `checkpoint.md` §2.1, §3, `restore.md` §2, `surface.md` §8-§9, ASM-5, ASM-40).

        The version and the `game` field are AGT-7.18-7.23's; what is asserted here is the
        **width** a reader holds the geometry to.  A v4 container's `representation.size` is
        the shape's and not the kind's 203, so `_rebuild` builds the layout from the
        container's recorded size and requires `params.count` — and `params.length` — to equal
        what that geometry gives; a disagreement is refused naming the field and both numbers
        (`docs/L1/shapes.md` §8, ASM-44, `docs/L2/features/capacity.md` §2, `restore.md` §2).
        The doctored copy is built with this battery's own container helpers — the document
        re-serialised, the array's bytes kept — so the surgery is one metadata field and no
        zip is written by hand (`checkpoint.md` §2, §3).
        """
        package = self.agents()
        architectures = package.learners()["architectures"]
        width = shape_size("naive-stack", OTHER_SHAPE)
        six = head_width(OTHER_SHAPE)
        learner = package.build_learner(
            learner_spec(
                kind="naive-stack",
                width=36,
                depth=2,
                game=OTHER_SHAPE,
                encoder=shape_encoder("flat-numeric", OTHER_SHAPE),
            )
        )
        count = plain_int(package.param_count(learner), "param_count")
        folder = self.tempdir()
        path = package.save(learner, os.path.join(folder, "v4-no-limit-8127.pt"))
        metadata, parameters = container_document(path)
        self.assertEqual(
            plain_int(metadata["format_version"], "metadata['format_version']"),
            4,
            "a container of any declared shape other than the default is format version 4 "
            "(checkpoint.md §2.1, §3, docs/L2/agents/shapes.md §5, ASM-40)",
        )
        self.assertEqual(
            metadata.get("game"),
            OTHER_SHAPE,
            "the container does not record the shape its learner decides in "
            "(checkpoint.md §2.1, §3): %r" % (metadata.get("game"),),
        )
        self.assertEqual(
            plain_int(
                metadata["representation"]["size"], "metadata['representation']['size']"
            ),
            width,
            "the container records `representation.size` as the kind's declared 203 rather "
            "than the shape's own width %d, so a reader would rebuild the wrong input block "
            "(docs/L1/shapes.md §8, ASM-44, checkpoint.md §2.1, §3, restore.md §2): %r"
            % (width, metadata["representation"]["size"]),
        )
        self.assertEqual(
            metadata["representation"].get("shape"),
            [width],
            "the container does not record `representation.shape` as that shape's own "
            "one-element vector (checkpoint.md §2.1, docs/L1/shapes.md §8, ASM-44): %r"
            % (metadata["representation"].get("shape"),),
        )
        self.assertEqual(
            plain_int(metadata["params"]["count"], "metadata['params']['count']"),
            count,
            "the container's `params.count` is not the count that shape's width gives, so "
            "the file would not check against its own geometry (checkpoint.md §2.1, §3, "
            "restore.md §2, ASM-44): %r against %r"
            % (metadata["params"]["count"], count),
        )
        restored = package.load(None, path)
        self.assertEqual(
            plain_int(package.param_count(restored), "param_count"),
            count,
            "the restored learner does not report the count that shape's width gives, so "
            "the container's recorded width did not reach the rebuild (checkpoint.md §3, "
            "restore.md §2, docs/L1/shapes.md §8, ASM-44)",
        )
        rows = shape_decisions(OTHER_SHAPE, 8)
        for position, row in enumerate(rows):
            with self.subTest(hand=position):
                saved = package.act(learner, row["dense"], row["mask"])
                loaded = package.act(restored, row["dense"], row["mask"])
                self.assertEqual(
                    plain_int(loaded["action"], "act(...)['action']"),
                    plain_int(saved["action"], "act(...)['action']"),
                    "the restored learner did not decide as the saved one, so the widened "
                    "input block's values did not travel (checkpoint.md §1, §4, ASM-5, "
                    "docs/L1/shapes.md §8, ASM-44)",
                )
                self.assertIs(
                    loaded["tie"],
                    saved["tie"],
                    "the restored decision's `tie` flag is not the saved one's, and the flag "
                    "is the learner's own record (records.md §6, §15, checkpoint.md §1)",
                )
        # The doctored copy: the shape's width recorded, the default shape's count under it.
        default_count = declared_count(
            architectures, "naive-stack", 36, 2, 0.0, head_width(DEFAULT_SHAPE)
        )
        self.assertNotEqual(
            default_count,
            count,
            "this case's surgery needs two different counts, and the default shape's %d and "
            "the second shape's %d are one number (docs/L1/shapes.md §8, ASM-44)"
            % (default_count, count),
        )
        recorded = dict(metadata)
        recorded["representation"] = dict(metadata["representation"])
        recorded["params"] = dict(metadata["params"])
        recorded["params"]["count"] = default_count
        doctored = write_container(
            os.path.join(folder, "v4-doctored-8127.pt"), recorded, parameters
        )
        self.assertEqual(
            plain_int(
                container_document(doctored)[0]["representation"]["size"],
                "representation.size",
            ),
            width,
            "the doctored copy no longer records the shape's width, so the refusal below "
            "would be the size's and not the count's (checkpoint.md §2.1, §3)",
        )
        self.assert_agents_refusal(
            package.load,
            None,
            doctored,
            entry="load",
            groups=(("params.count",), (str(default_count),), (str(count),)),
            label="a version-4 container recording the shape's width %d over the default "
            "shape's count %d" % (width, default_count),
        )
        self.assertEqual(
            plain_int(package.param_count(package.load(None, path)), "param_count"),
            count,
            "the container the doctored copy came from must still load, so the refusal above "
            "is the doctored count's and not the file's (checkpoint.md §3)",
        )

    def test_agt17_11_the_default_shape_did_not_move(self):
        """AGT-17.11 a learner built on the default shape with the default encoder at width 36, depth 2 still reports `param_count` 10,119 and `Learner.size` 203, its save records `representation.size` 203, and `load` restores it at 10,119 — the default shape's behaviour is bit-for-bit what it was (`docs/L1/shapes.md` §8, ASM-44, `docs/L2/agents/shapes.md` §2, `docs/L2/features/capacity.md` §2, `checkpoint.md` §2.1, §3, `sizing.md` §6, ASM-10, ASM-40).

        The version-3 half and the absent `game` field are AGT-7.19's, and the six rung counts
        are AGT-17.3's; what is added here is the **width**: an encoder-less build on the
        default shape is sized from the kind's declared `observation_size` and a save of it
        records that same number, so the widened second shape moved nothing on this side
        (`docs/L1/shapes.md` §8, ASM-44).  The count is the table's `7344 + 2664 + 111`, and
        the size is read off the default shape's encoder as well, so neither 203 nor 10,119
        is a literal this case cannot check.
        """
        package = self.agents()
        width = shape_size("naive-stack", None)
        self.assertEqual(
            width,
            int(
                package.learners()["architectures"]["naive-stack"]["observation_size"]
            ),
            "the default shape's encoder width is the kind's declared observation_size, which "
            "did not move (docs/L1/shapes.md §8, ASM-44): %r against %r"
            % (
                width,
                package.learners()["architectures"]["naive-stack"]["observation_size"],
            ),
        )
        learner = package.build_learner(
            learner_spec(kind="naive-stack", width=36, depth=2, encoder=flat_encoder())
        )
        self.assertEqual(
            plain_int(package.param_count(learner), "param_count"),
            10119,
            "the default shape's count at width 36, depth 2 moved: it is architecture.md "
            "§5's sum at 203 — 7344 + 2664 + 111 = 10,119 — and the widened second shape "
            "must not reach it (docs/L1/shapes.md §8, ASM-44, docs/L2/agents/shapes.md §2, "
            "sizing.md §6, ASM-10): %r" % (package.param_count(learner),),
        )
        self.assertEqual(
            plain_int(getattr(learner, "size", None), "Learner.size"),
            203,
            "an encoder-less default-shape build is sized from the kind's declared "
            "observation_size and no other number (docs/L1/shapes.md §8, ASM-44, "
            "docs/L2/features/capacity.md §2): %r" % (getattr(learner, "size", None),),
        )
        self.assertEqual(
            int(tuple(getattr(learner, "shape", ()))[0]),
            width,
            "the default-shape learner's declared observation is not the default encoder's "
            "width (architecture.md §6, docs/L1/shapes.md §8, ASM-44): %r against %r"
            % (getattr(learner, "shape", None), (width,)),
        )
        path = package.save(learner, os.path.join(self.tempdir(), "v3-default-8127.pt"))
        metadata, _parameters = container_document(path)
        self.assertEqual(
            plain_int(
                metadata["representation"]["size"], "metadata['representation']['size']"
            ),
            203,
            "a default-shape container no longer records the default shape's own width 203, "
            "so the second shape's arrival moved this side of the formula as well "
            "(checkpoint.md §2.1, §3, docs/L1/shapes.md §8, ASM-44): %r"
            % (metadata["representation"]["size"],),
        )
        self.assertEqual(
            plain_int(package.param_count(package.load(None, path)), "param_count"),
            10119,
            "a restored default-shape learner does not report the count it was saved at, so "
            "the default shape's behaviour is not bit-for-bit what it was (checkpoint.md §3, "
            "restore.md §2, docs/L1/shapes.md §8, ASM-44)",
        )
    def test_agt17_12_the_six_seat_shape_is_the_catalogues_third_row(self):
        """AGT-17.12 a learner naming `six-seat-no-limit-100` is built on it and carries that name, its head is that shape's descriptor count — six, the same six descriptors the two-seat uncapped row declares in the same index order, read off `features.action_space` and never written down — and a name outside the catalogue is refused naming all **three** declared names in the catalogue's own order, the default first (`docs/L1/shapes.md` §2, `docs/L1/seats.md` §2-§3, `docs/L2/agents/shapes.md` §1-§2, §6, `docs/L3/agents/shapes.md` §1, `sizing.md` §6, ASM-40, ASM-44, D-33).

        The third name is restated rather than read: nothing below an entry point imports
        `engine`, so `declarations.SHAPE_NAMES` is where the catalogue's names and their
        order live and the join battery (JOIN-AGT-14.1) is what holds them equal to
        `engine.game_shapes()`'s (`module-map.md` §2, D-13).  What this case can check on
        its own is what a caller observes: a spec naming the third row builds a learner
        that reports it, its head is that row's descriptor count, and a name the catalogue
        does not carry is refused with every declared name in it, in order, so the third
        row is a name this module offers back.  A seat count **adds no descriptor**: the
        six-seat row's vocabulary is the two-seat uncapped row's six in the same declared
        order, which is why the head's width is the vocabulary's and not the seats'
        (`shapes.md` §2, `seats.md` §2, ASM-44).
        """
        package = self.agents()
        six = head_width(SIX_SEAT_SHAPE)
        self.assertEqual(
            six,
            head_width(OTHER_SHAPE),
            "the six-seat row's descriptor count is not the two-seat uncapped row's, and a "
            "seat count adds no descriptor (shapes.md §2, seats.md §2, ASM-44): %r against "
            "%r" % (six, head_width(OTHER_SHAPE)),
        )
        self.assertEqual(
            tuple(features().action_space(shape=SIX_SEAT_SHAPE)),
            tuple(features().action_space(shape=OTHER_SHAPE)),
            "the third row declares another vocabulary than the two-seat uncapped one, and "
            "the six descriptors are the same in the same index order (shapes.md §2, "
            "sizing.md §3, ASM-37)",
        )
        learner = self.build(
            kind="naive-stack",
            width=6,
            depth=1,
            game=SIX_SEAT_SHAPE,
            encoder=kind_encoder("naive-stack", SIX_SEAT_SHAPE),
        )
        self.assertEqual(
            getattr(learner, "game", None),
            SIX_SEAT_SHAPE,
            "a learner built from a spec naming %r does not carry that shape's name, so no "
            "container of it could record the shape it decides in (shapes.md §1-§2, §5, "
            "D-33): %r" % (SIX_SEAT_SHAPE, getattr(learner, "game", None)),
        )
        self.assertEqual(
            plain_int(getattr(learner, "actions", None), "Learner.actions"),
            six,
            "the six-seat learner's head is not as wide as that shape's descriptor count "
            "(docs/L2/agents/shapes.md §2, ASM-40): %r" % (getattr(learner, "actions", None),),
        )
        message = self.assert_agents_refusal(
            package.build_learner,
            learner_spec(
                kind="naive-stack",
                width=6,
                depth=1,
                game="invented-third-shape",
                encoder=kind_encoder("naive-stack", SIX_SEAT_SHAPE),
            ),
            entry="build_learner",
            groups=(
                ("invented-third-shape",),
                (DEFAULT_SHAPE,),
                (OTHER_SHAPE,),
                (SIX_SEAT_SHAPE,),
            ),
            label="a shape name the catalogue does not carry",
        )
        positions = [
            message.find(name)
            for name in (DEFAULT_SHAPE, OTHER_SHAPE, SIX_SEAT_SHAPE)
        ]
        self.assertNotIn(
            -1,
            positions,
            "the refusal does not name every declared shape, so the third row is not a "
            "name this module offers back (shapes.md §1, §6, D-13): %r" % (message,),
        )
        self.assertEqual(
            positions,
            sorted(positions),
            "the names are listed in the catalogue's own order, default first, so the "
            "third row is read where engine publishes it (shapes.md §2, D-33): %r in %r"
            % (positions, message),
        )

    def test_agt17_13_a_learner_on_the_six_seat_shape_is_built_at_433_and_counts_18510(self):
        """AGT-17.13 a `naive-stack` learner on `six-seat-no-limit-100` at width 36 and depth 2 is built at that shape's **433**-wide input with that shape's six-wide head and reports `param_count` **18,510** — the measured value, which is `433·36 + 36 = 15,624`, `2·(36² + 36) = 2,664` and `6·36 + 6 = 222` — while the same spec with no `game` still reports the default shape's 10,119 (`docs/L1/shapes.md` §2, §8, ASM-42, ASM-44, `docs/L2/agents/shapes.md` §2, `docs/L2/features/capacity.md` §2, `sizing.md` §6, `architecture.md` §5, ASM-10, ASM-40, D-33).

        The width is read off **that shape's** encoder's `observation_spec` and never
        written down here; the arithmetic is `architecture.md` §5's sum with the shape's
        own `I` in the input term and its own `A` in the output term `A·W + A` — the 24
        history slots of the default shape's cap-derived 203 against the six-seat row's
        own 98 slots' 433 (`docs/L1/shapes.md` §8, ASM-42, ASM-44).  The two counts differ
        by exactly `(I₃ − I₁)·W` for the wider input block plus `(A₃ − A₁)·W + (A₃ − A₁)`
        for the three extra head rows and their bias, so the shape reaches the measurement
        through its own width and its own `A` and through nothing else (ASM-10, ASM-40).
        """
        package = self.agents()
        architectures = package.learners()["architectures"]
        width, depth = 36, 2
        six = head_width(SIX_SEAT_SHAPE)
        three = head_width(DEFAULT_SHAPE)
        shape_width = shape_size("naive-stack", SIX_SEAT_SHAPE)
        default_width = shape_size("naive-stack", None)
        self.assertEqual(
            default_width,
            int(architectures["naive-stack"]["observation_size"]),
            "the default shape's width is no longer the kind's declared observation_size, "
            "so this case's two arms are not one formula (docs/L1/shapes.md §8, ASM-44): "
            "%r against %r"
            % (default_width, architectures["naive-stack"]["observation_size"]),
        )
        self.assertNotEqual(
            shape_width,
            default_width,
            "the six-seat shape declares the default shape's observation width, so no case "
            "here can say the input term is the shape's (docs/L2/features/capacity.md §2, "
            "ASM-44, docs/L1/shapes.md §8): %r" % (shape_width,),
        )
        six_seat = self.build(
            kind="naive-stack",
            width=width,
            depth=depth,
            game=SIX_SEAT_SHAPE,
            encoder=kind_encoder("naive-stack", SIX_SEAT_SHAPE),
        )
        default = self.build(kind="naive-stack", width=width, depth=depth)
        layout = getattr(six_seat, "layout", None)
        self.assertIsNotNone(
            layout,
            "the six-seat learner carries no layout, so its input width and its output "
            "block cannot be read (docs/L3/agents/shapes.md §2)",
        )
        self.assertEqual(
            plain_int(layout.input_dim, "layout.input_dim"),
            shape_width,
            "a learner on %r is not built at that shape's own input width — the one its "
            "encoder's observation_spec declares (docs/L1/shapes.md §8, ASM-44, "
            "docs/L2/features/capacity.md §2): %r against %r"
            % (SIX_SEAT_SHAPE, int(layout.input_dim), shape_width),
        )
        self.assertEqual(
            int(tuple(getattr(six_seat, "shape", ()))[0]),
            shape_width,
            "the learner's declared `shape` is not one observation of that shape's own "
            "width, which is what `act` checks an observation against (architecture.md §6, "
            "docs/L1/shapes.md §8, ASM-44): %r against %r"
            % (getattr(six_seat, "shape", None), (shape_width,)),
        )
        counted = plain_int(package.param_count(six_seat), "param_count")
        self.assertEqual(
            counted,
            18510,
            "a naive-stack learner on %r at width %d and depth %d reports %r parameters and "
            "architecture.md §5's sum at that shape's input width is 15624 + 2664 + 222 = "
            "18,510 — the input block %d·%d + %d, the trunk %d·(%d² + %d) and the head "
            "%d·%d + %d (docs/L1/shapes.md §2, §8, ASM-42, ASM-44, docs/L2/agents/shapes.md "
            "§2, sizing.md §6, ASM-40)"
            % (
                SIX_SEAT_SHAPE,
                width,
                depth,
                counted,
                shape_width,
                width,
                width,
                depth,
                width,
                width,
                six,
                width,
                six,
            ),
        )
        self.assertEqual(
            counted,
            declared_count(
                architectures, "naive-stack", width, depth, 0.0, six, shape_width
            ),
            "the count is not architecture.md §5's sum over the shape's own input width %d "
            "with the output term A·W + A at A = %d (docs/L3/agents/shapes.md §2, "
            "docs/L2/agents/shapes.md §2, ASM-40): %r"
            % (shape_width, six, counted),
        )
        offset, length = layout.w_out
        self.assertEqual(
            plain_int(length, "layout.w_out's length"),
            six * width,
            "the six-seat learner's output matrix is not A·W long at A = %d and W = %d "
            "(docs/L3/agents/shapes.md §2, ASM-40): %r" % (six, width, length),
        )
        self.assertEqual(
            plain_int(layout.count, "layout.count") - plain_int(layout.b_out, "layout.b_out"),
            six,
            "the output bias is not A = %d wide, so the head is not A·W + A (docs/L3/agents/"
            "shapes.md §2, ASM-40)",
        )
        self.assertEqual(
            plain_int(package.param_count(default), "param_count"),
            10119,
            "the default shape's count at width %d and depth %d moved, and the third shape "
            "may not reach it (docs/L1/shapes.md §5, §8, ASM-10, ASM-44): %r"
            % (width, depth, package.param_count(default)),
        )
        self.assertEqual(
            counted - plain_int(package.param_count(default), "param_count"),
            (shape_width - default_width) * width + (six - three) * width + (six - three),
            "the two counts differ by something other than the wider input block (I₃ − I₁)·W "
            "plus the head's extra term (A₃ − A₁)·W + (A₃ − A₁), so the shape reached the "
            "measurement through something else (docs/L1/shapes.md §8, ASM-44, ASM-10, "
            "ASM-40): %r against %r for I = %d and %d at A = %d and %d and W = %d"
            % (
                counted - plain_int(package.param_count(default), "param_count"),
                (shape_width - default_width) * width
                + (six - three) * width
                + (six - three),
                default_width,
                shape_width,
                three,
                six,
                width,
            ),
        )

    def test_agt17_14_a_token_learner_on_the_six_seat_shape_is_sized_by_its_vocabulary(self):
        """AGT-17.14 a token learner on `six-seat-no-limit-100` is sized by that shape's **vocabulary 102** and not by its 122-token sequence, and it decides on a real 122-token observation of that shape — the sequence `features.encode` returns for a hand `engine` dealt there — answering a member of the decision's own mask (`architecture.md` §6, `encodings.md` §1, §4, `docs/L1/shapes.md` §8, ASM-44, `docs/L2/agents/shapes.md` §2-§3, `docs/L2/features/capacity.md` §2, D-3, D-33).

        Both numbers are read out of `features.observation_spec` and neither is a literal
        here: the vocabulary is the number `build_learner` sizes a token learner by, and
        the sequence length is the number an observation of that shape is checked against,
        which is why the 122-token observation the case hands `act` is accepted while the
        learner's own size is 102 (`docs/L2/agents/shapes.md` §2).  The observation is
        `features.encode` of a real readout, never a fabricated one, and the mask is
        `features.legal_indices` of that readout's own legal descriptors, so the decision is
        the shape's own (`docs/L2/features/surface.md` §6, §8).
        """
        package = self.agents()
        token = shape_encoder("card-tokens", SIX_SEAT_SHAPE)
        spec = features().observation_spec(token)
        vocabulary = plain_int(spec["vocabulary"], "observation_spec(...)['vocabulary']")
        sequence = plain_int(tuple(spec["shape"])[0], "observation_spec(...)['shape'][0]")
        self.assertEqual(
            vocabulary,
            102,
            "the six-seat row's token vocabulary is not 102, which is the six seat ids it "
            "adds above the current top id (docs/L1/seats.md §3, ASM-44): %r" % (vocabulary,),
        )
        self.assertEqual(
            sequence,
            122,
            "the six-seat row's token observation is not 122 long — the widened history "
            "block plus its six seat slots (docs/L1/shapes.md §8, docs/L2/features/"
            "capacity.md §2): %r" % (sequence,),
        )
        learner = self.build(
            kind="deep",
            width=50,
            depth=2,
            game=SIX_SEAT_SHAPE,
            encoder=token,
        )
        self.assertEqual(
            plain_int(getattr(learner, "size", None), "Learner.size"),
            vocabulary,
            "a token learner on %r is sized by its encoder's **vocabulary** and never by its "
            "sequence length (architecture.md §6, encodings.md §1, §4, D-3): %r against %r"
            % (SIX_SEAT_SHAPE, getattr(learner, "size", None), vocabulary),
        )
        self.assertEqual(
            int(tuple(getattr(learner, "shape", ()))[0]),
            sequence,
            "that learner's declared `shape` is not the token sequence its shape's encoder "
            "encodes, so the 122-token observation below would be refused (architecture.md "
            "§6, docs/L2/features/capacity.md §2): %r against %r"
            % (getattr(learner, "shape", None), (sequence,)),
        )
        self.assertEqual(
            plain_int(package.param_count(learner), "param_count"),
            vocabulary * 50 + 2 * (50 * 50 + 50) + head_width(SIX_SEAT_SHAPE) * 50
            + head_width(SIX_SEAT_SHAPE),
            "a token learner's input block is V·W with V the vocabulary %d, not S·W with S "
            "the sequence length %d, so its count is V·W + D·(W² + W) + A·W + A "
            "(architecture.md §5-§6, sizing.md §6, ASM-44)"
            % (vocabulary, sequence),
        )
        rows = shape_decisions(SIX_SEAT_SHAPE, 4)
        self.assertTrue(
            rows,
            "no hand was dealt on %r, so this case would decide nothing "
            "(docs/L2/engine/surface.md §4)" % (SIX_SEAT_SHAPE,),
        )
        for position, row in enumerate(rows):
            with self.subTest(hand=position):
                self.assertEqual(
                    tuple(row["tokens"].shape),
                    (sequence,),
                    "the decision's observation is not the %d-token sequence that shape's "
                    "encoder declares (docs/L1/shapes.md §8, ASM-44): %r"
                    % (sequence, tuple(row["tokens"].shape)),
                )
                action = plain_int(
                    package.act(learner, row["tokens"], row["mask"])["action"],
                    "act(...)['action']",
                )
                self.assertIn(
                    action,
                    tuple(row["mask"]),
                    "a token learner on the six-seat shape answered an index outside the "
                    "decision's own mask (surface.md §2, §6, D-2): %r at %r"
                    % (action, row["mask"]),
                )
                self.assertLess(
                    action,
                    head_width(SIX_SEAT_SHAPE),
                    "the answer is not one of that shape's %d declared indices "
                    "(sizing.md §3, ASM-37)" % (head_width(SIX_SEAT_SHAPE),),
                )

    def test_agt17_15_an_encoderless_spec_naming_the_six_seat_shape_is_refused_by_name(self):
        """AGT-17.15 an otherwise valid encoder-less spec naming the **third** declared shape is refused by `agents` itself, naming `build_learner`, that shape, the kind's declared 203 and the word `encoder`, while the same spec carrying that shape's encoder builds a learner at that shape's own 433 and reports its 18,510 (`docs/L1/shapes.md` §8, ASM-44, `docs/L2/agents/shapes.md` §2, §6, `docs/L2/features/capacity.md` §2, §5, `surface.md` §4, §9, `errors.md` §2-§3, D-33).

        The rule is one rule for every non-default row and this case is its third
        instance: a kind's declared `observation_size` is the default shape's 203, so a
        spec naming a shape with more seats has no width to be sized at and is refused by
        name rather than silently built at 203 — an observation of one shape fed to a head
        of another (`docs/L1/shapes.md` §8, ASM-44).  The twin differing only by carrying
        that shape's encoder is built and measured, which is how "nothing is built at 203"
        is asserted without reading an internal (`surface.md` §1).
        """
        package = self.agents()
        architectures = package.learners()["architectures"]
        declared = int(architectures["naive-stack"]["observation_size"])
        spec = learner_spec(kind="naive-stack", width=6, depth=1, game=SIX_SEAT_SHAPE)
        self.assertNotIn(
            "encoder",
            spec,
            "this case's spec carries an encoder, so it is not the encoder-less one the "
            "rule refuses (docs/L1/shapes.md §8, ASM-44): %r" % (spec,),
        )
        message = self.assert_agents_refusal(
            package.build_learner,
            spec,
            entry="build_learner",
            groups=((SIX_SEAT_SHAPE,), (str(declared),), ("encoder",)),
            label="an encoder-less spec naming %r" % (SIX_SEAT_SHAPE,),
        )
        self.assertIn(
            DEFAULT_SHAPE,
            message,
            "the refusal does not name the default shape whose declared %d the kind's "
            "observation_size is, so a reader cannot tell which shape that number belongs "
            "to (docs/L1/shapes.md §8, ASM-44): %r" % (declared, message),
        )
        built = package.build_learner(
            learner_spec(
                kind="naive-stack",
                width=6,
                depth=1,
                game=SIX_SEAT_SHAPE,
                encoder=kind_encoder("naive-stack", SIX_SEAT_SHAPE),
            )
        )
        self.assertEqual(
            getattr(built, "game", None),
            SIX_SEAT_SHAPE,
            "the spec that differs from the refused one only by carrying the shape's "
            "encoder does not build a learner of that shape (shapes.md §1-§2, D-33): %r"
            % (getattr(built, "game", None),),
        )
        self.assertEqual(
            int(built.layout.input_dim),
            shape_size("naive-stack", SIX_SEAT_SHAPE),
            "the twin's learner is not built at the shape's own input width, so this case "
            "cannot say the refusal was the encoder's absence rather than the shape's "
            "(docs/L1/shapes.md §8, ASM-44): %r against %r"
            % (int(built.layout.input_dim), shape_size("naive-stack", SIX_SEAT_SHAPE)),
        )
        self.assertNotEqual(
            plain_int(package.param_count(built), "param_count"),
            declared_count(
                architectures, "naive-stack", 6, 1, 0.0, head_width(SIX_SEAT_SHAPE)
            ),
            "the twin reports the count architecture.md §5's sum gives at the **default** "
            "shape's input width, so something sized it at 203 after all (docs/L1/"
            "shapes.md §8, ASM-44, docs/L2/features/capacity.md §5): %r"
            % (package.param_count(built),),
        )

    def test_agt17_16_the_container_of_the_six_seat_shape_is_a_version_4_at_433(self):
        """AGT-17.16 a checkpoint of a `six-seat-no-limit-100` learner is a version-4 container recording that shape in `game`, its own **433** in `representation.size` and `[433]` in `representation.shape`, and **18,510** in `params.count`; `load(None, path)` restores a learner at that count and at that shape which takes the same decisions as the saved one, and the file the case doctored away from is still loadable (`docs/L1/shapes.md` §5, §8, ASM-44, `docs/L2/agents/shapes.md` §2, §5, `docs/L2/features/capacity.md` §2, `checkpoint.md` §2.1, §3, `restore.md` §2, ASM-5, ASM-40, D-33).

        The version, the `game` field and the `params.count` cross-check are the same three
        statements AGT-17.10 makes of the second row; what the third row adds is that the
        geometry a reader holds the file to is **433** and the head it rebuilds is six
        wide, so a container of a six-seat learner restores to the head it was written at
        and not to the kind's 203 (`docs/L1/shapes.md` §8, ASM-44).  Every number read here
        comes out of `features.observation_spec`, `features.action_space` and the container
        itself, so no width and no count is a literal of this battery's.
        """
        package = self.agents()
        width = shape_size("naive-stack", SIX_SEAT_SHAPE)
        six = head_width(SIX_SEAT_SHAPE)
        learner = package.build_learner(
            learner_spec(
                kind="naive-stack",
                width=36,
                depth=2,
                game=SIX_SEAT_SHAPE,
                encoder=shape_encoder("flat-numeric", SIX_SEAT_SHAPE),
            )
        )
        count = plain_int(package.param_count(learner), "param_count")
        self.assertEqual(
            count,
            18510,
            "a naive-stack learner on %r at width 36 and depth 2 reports %r parameters and "
            "architecture.md §5's sum at that shape's input width is 18,510 "
            "(docs/L1/shapes.md §8, ASM-44, docs/L2/agents/shapes.md §2): %r"
            % (SIX_SEAT_SHAPE, count, count),
        )
        folder = self.tempdir()
        path = package.save(learner, os.path.join(folder, "v4-six-seat-8127.pt"))
        metadata, _parameters = container_document(path)
        self.assertEqual(
            plain_int(metadata["format_version"], "metadata['format_version']"),
            4,
            "a container of any declared shape other than the default is format version 4 "
            "(checkpoint.md §2.1, §3, docs/L2/agents/shapes.md §5, ASM-40)",
        )
        self.assertEqual(
            metadata.get("game"),
            SIX_SEAT_SHAPE,
            "the container does not record the six-seat shape its learner decides in "
            "(checkpoint.md §2.1, §3, D-33): %r" % (metadata.get("game"),),
        )
        self.assertEqual(
            plain_int(
                metadata["representation"]["size"], "metadata['representation']['size']"
            ),
            width,
            "the container records `representation.size` as the kind's declared 203 rather "
            "than the six-seat shape's own width %d, so a reader would rebuild the wrong "
            "input block (docs/L1/shapes.md §8, ASM-44, checkpoint.md §2.1, §3, restore.md "
            "§2): %r" % (width, metadata["representation"]["size"]),
        )
        self.assertEqual(
            metadata["representation"].get("shape"),
            [width],
            "the container does not record `representation.shape` as that shape's own "
            "one-element vector (checkpoint.md §2.1, docs/L1/shapes.md §8, ASM-44): %r"
            % (metadata["representation"].get("shape"),),
        )
        self.assertEqual(
            plain_int(metadata["params"]["count"], "metadata['params']['count']"),
            count,
            "the container's `params.count` is not the count that shape's width gives, so "
            "the file would not check against its own geometry (checkpoint.md §2.1, §3, "
            "restore.md §2, ASM-44): %r against %r"
            % (metadata["params"]["count"], count),
        )
        restored = package.load(None, path)
        self.assertEqual(
            plain_int(package.param_count(restored), "param_count"),
            count,
            "the restored learner does not report the count that shape's width gives, so "
            "the container's recorded width did not reach the rebuild (checkpoint.md §3, "
            "restore.md §2, docs/L1/shapes.md §8, ASM-44)",
        )
        self.assertEqual(
            getattr(restored, "game", None),
            SIX_SEAT_SHAPE,
            "the restored learner is not read as the six-seat shape its container records "
            "(checkpoint.md §3, shapes.md §5, D-33): %r"
            % (getattr(restored, "game", None),),
        )
        self.assertEqual(
            plain_int(getattr(restored, "actions", None), "Learner.actions"),
            six,
            "the restored learner's head is not six wide, so the container's shape did not "
            "reach the rebuilt output layer (docs/L3/agents/shapes.md §2, ASM-40)",
        )
        rows = shape_decisions(SIX_SEAT_SHAPE, 8)
        self.assertTrue(
            rows,
            "no hand was dealt on %r, so the restore's decisions cannot be compared "
            "(docs/L2/engine/surface.md §4)" % (SIX_SEAT_SHAPE,),
        )
        for position, row in enumerate(rows):
            with self.subTest(hand=position):
                saved = package.act(learner, row["dense"], row["mask"])
                loaded = package.act(restored, row["dense"], row["mask"])
                self.assertEqual(
                    plain_int(loaded["action"], "act(...)['action']"),
                    plain_int(saved["action"], "act(...)['action']"),
                    "the restored six-seat learner did not decide as the saved one, so the "
                    "widened input block's values did not travel (checkpoint.md §1, §4, "
                    "ASM-5, docs/L1/shapes.md §8, ASM-44)",
                )
                self.assertIs(
                    loaded["tie"],
                    saved["tie"],
                    "the restored decision's `tie` flag is not the saved one's, and the flag "
                    "is the learner's own record (records.md §6, §15, checkpoint.md §1)",
                )
        self.assertEqual(
            plain_int(
                container_document(path)[0]["params"]["count"], "params.count"
            ),
            plain_int(package.param_count(package.load(None, path)), "param_count"),
            "the container the case restored twice no longer reads at its own count "
            "(checkpoint.md §3)",
        )


if __name__ == "__main__":
    unittest.main()
