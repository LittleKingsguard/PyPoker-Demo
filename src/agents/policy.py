"""`as_policy` and the frozen snapshot (`rule.md` §7, `utility.md` §7, `surface.md` §10).

A policy is a callable `policy(readout, legal_actions)` that encodes the readout with
the caller's encoder, takes the mask `features.legal_indices` gives it, decides by
`rule.md` §4-§5 with its **own** seed, and returns `features.decode_action` of the
index it chose — always one of `legal_actions` — in **the learner's shape's** vocabulary.
It holds the learner's state as a copy taken at build time, so a later `learn` cannot
change a policy already built (`surface.md` §10, ASM-5).  It carries the catalogue
member its learner learned under, the one whose reward it was trained on and the one it
took its targets from -- `learning_rule`, `utility` and `counterfactual`, carried and
never read -- and no decision it makes reads any of them (`rules.md` §7, `utilities.md`
§7, `counterfactual.md` §6, D-19, D-20, D-43).  Its **exploration mode** is its own
fourth argument: `schedule` takes `rule.decide`'s keyed draw as it always has, and `off`
takes `rule.decide_greedy` and constructs no generator at all, so two `off` policies at
different seeds decide identically (`shapes.md` §4, `sizing.md` §4).

Its refusals are **this** module's (`errors.md` §2-§3): a readout that is not a
mapping, or that is missing a fact the rule needs, is refused as `agents`'
`InvalidReadout` naming `policy(readout)` — a `features` error escaping
`features.encode` would carry another module's class and another entry point's name,
which a caller cannot catch as `AgentsError`.  The facts are the encoder's own nine
plus the mask's `legal`, and they are checked before `features.encode` is called.
"""

from __future__ import annotations

from collections.abc import Mapping

import features

from . import declarations, learner as _learner, rule
from .errors import EncoderMismatch, InvalidReadout

#: The one readout fact no encoding carries and the rule still needs: the decision's
#: legal actions (`features/surface.md` §8, `rule.md` §7).
LEGAL = "legal"


class Policy:
    """One learner, frozen: its parameters, its position, its own seed, its rule, its
    utility, its counterfactual.

    `learning_rule` is the catalogue member the learner was built under, `utility` the
    catalogue member whose reward its model was trained on, and `counterfactual` the
    catalogue member it took its targets from.  They are the only things a policy carries
    that a decision does not read: `evaluation` reads them to label a table's members, so
    a table names the population and the objectives it measured even when a variant was
    built in process and no record of it exists yet (`e2e-surface.md` §2, `rules.md` §7,
    `utilities.md` §7, `counterfactual.md` §6, D-19, D-20, D-43).

    `game` is the shape whose vocabulary the chosen index is decoded in — the learner's
    own, so a policy of a six-index learner returns one of that shape's six descriptors
    and never the default shape's `raise` (`shapes.md` §3, §7) — and `_exploration` is
    the mode it was built with, `schedule` or `off` (`shapes.md` §4).  Neither is one of
    the three attributes `e2e-surface.md` §2 declares.
    """

    __slots__ = (
        "_backend",
        "_layout",
        "_state",
        "_seed",
        "_position",
        "_encoder",
        "_facts",
        "_exploration",
        "learning_rule",
        "utility",
        "counterfactual",
        "game",
    )

    def __init__(
        self,
        backend,
        layout,
        state,
        seed,
        position,
        encoder,
        facts,
        learning_rule,
        utility,
        counterfactual,
        game,
        exploration,
    ):
        self._backend = backend
        self._layout = layout
        self._state = state
        self._seed = seed
        self._position = position
        self._encoder = encoder
        self._facts = tuple(facts)
        self.learning_rule = learning_rule
        self.utility = utility
        self.counterfactual = counterfactual
        self.game = game
        self._exploration = exploration

    def __repr__(self):
        return "Policy(%r, position %d, seed %d, %s, %s)" % (
            self._layout.kind,
            self._position,
            self._seed,
            self.learning_rule,
            self.utility,
        )

    def __call__(self, readout, legal_actions):
        """One descriptor from `legal_actions` for one readout (`surface.md` §10)."""
        if not isinstance(readout, Mapping):
            raise InvalidReadout(
                "policy(readout): the readout must be a mapping of the decision's "
                "facts, got %s" % type(readout).__name__
            )
        for fact in self._facts:
            if fact not in readout:
                raise InvalidReadout(
                    "policy(readout): the readout is missing %r, which the rule needs"
                    % (fact,)
                )
        try:
            observation = features.encode(self._encoder, readout)
        except Exception as error:
            # `errors.md` §3: a refusal raised while a policy works is this module's,
            # named `policy(readout)`, so it is catchable as `AgentsError`.
            raise InvalidReadout(
                "policy(readout): the readout does not encode: %s" % (error,)
            ) from None
        try:
            mask = tuple(int(index) for index in features.legal_indices(readout[LEGAL]))
        except Exception as error:
            raise InvalidReadout(
                "policy(readout): %r is not a decision's legal actions: %s"
                % (readout[LEGAL], error)
            ) from None
        scored, _cache = self._backend.forward(
            self._state, self._layout, observation, need_cache=False
        )
        if self._exploration == "off":
            # The masked maximum and the tie-break alone, at every seed: `decide_greedy`
            # constructs no generator, so no draw is taken and the policy's seed is not
            # read (`shapes.md` §4, `sizing.md` §4).
            index, _tie = rule.decide_greedy(scored, mask)
        else:
            index, _tie = rule.decide(
                self._seed,
                self._layout.family,
                self._position,
                scored,
                observation,
                mask,
            )
        # The descriptor is the **learner's shape's**: an index decodes only in the
        # vocabulary that declared it (`shapes.md` §3, §7, `features/surface.md` §9).
        return features.decode_action(int(index), shape=self.game)


def as_policy(learner, encoder, seed, exploration="schedule"):
    """One learner as a policy, at its own state and the caller's seed and mode (§10, §7)."""
    held = _learner._require_learner(learner, "as_policy")
    encoded = _learner.encoder_spec(encoder, "as_policy")
    policy_seed = _learner._seed(seed, "as_policy")
    # The exploration mode is the **policy's** and never the hyper block's: `HYPER` keeps
    # its one annealed schedule whatever a policy is built with, so a mode changes no
    # training (`shapes.md` §4, `rule.md` §6, D-19).
    mode = declarations.require_exploration(exploration, "as_policy")
    declared_size = _learner.encoder_size(encoded)
    if encoded["kind"] != held.family or declared_size != held.size:
        raise EncoderMismatch(
            "as_policy(encoder): the encoder is %s and the learner is %s"
            % (
                _learner.encoder_side(encoded),
                _learner.learner_side(held),
            )
        )
    state = held.backend.load_state(
        held.layout,
        held.backend.parameters(held.state),
        held.backend.masks(held.state),
    )
    return Policy(
        held.backend,
        held.layout,
        state,
        policy_seed,
        int(held.position),
        encoder,
        (LEGAL,) + tuple(encoded["fields"]),
        # The rule the frozen model learned under, carried so a table can name the
        # population it measured (`e2e-surface.md` §2, `rules.md` §7, D-19).
        held.rule,
        # ... and the utility it was trained on, so the same table can name the
        # objectives it measured (`e2e-surface.md` §2, `utilities.md` §7, D-20).
        held.utility,
        # ... and the catalogue member its learner took its targets from, so a table can
        # name it as it names the rule and the utility -- and no decision this policy
        # makes reads it (`counterfactual.md` §6, D-43).
        held.counterfactual,
        # ... and the shape whose vocabulary its descriptor is decoded in, together with
        # the mode it decides under (`shapes.md` §3–§4).
        held.game,
        mode,
    )
