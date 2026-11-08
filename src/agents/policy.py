"""`as_policy` and the frozen snapshot (`rule.md` §7, `surface.md` §10).

A policy is a callable `policy(readout, legal_actions)` that encodes the readout with
the caller's encoder, takes the mask `features.legal_indices` gives it, decides by
`rule.md` §4-§5 with its **own** seed, and returns `features.decode_action` of the
index it chose — always one of `legal_actions`.  It holds the learner's state as a
copy taken at build time, so a later `learn` cannot change a policy already built
(`surface.md` §10, ASM-5).

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

from . import learner as _learner, rule
from .errors import EncoderMismatch, InvalidReadout

#: The one readout fact no encoding carries and the rule still needs: the decision's
#: legal actions (`features/surface.md` §8, `rule.md` §7).
LEGAL = "legal"


class Policy:
    """One learner, frozen: its parameters, its position, its own seed, its rule.

    `learning_rule` is the catalogue member the learner was built under.  It is the
    only thing a policy carries that a decision does not read: `evaluation` reads it to
    label a table's members, so a table names the population it measured even when a
    variant was built in process and no record of it exists yet (`e2e-surface.md` §2,
    `rules.md` §7, D-19).
    """

    __slots__ = (
        "_backend",
        "_layout",
        "_state",
        "_seed",
        "_position",
        "_encoder",
        "_facts",
        "learning_rule",
    )

    def __init__(
        self, backend, layout, state, seed, position, encoder, facts, learning_rule
    ):
        self._backend = backend
        self._layout = layout
        self._state = state
        self._seed = seed
        self._position = position
        self._encoder = encoder
        self._facts = tuple(facts)
        self.learning_rule = learning_rule

    def __repr__(self):
        return "Policy(%r, position %d, seed %d, %s)" % (
            self._layout.kind,
            self._position,
            self._seed,
            self.learning_rule,
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
        index = rule.decide(
            self._seed, self._layout.family, self._position, scored, observation, mask
        )
        return features.decode_action(int(index))


def as_policy(learner, encoder, seed):
    """One learner as a policy, at its own state and the caller's seed (§10, §7)."""
    held = _learner._require_learner(learner, "as_policy")
    encoded = _learner.encoder_spec(encoder, "as_policy")
    policy_seed = _learner._seed(seed, "as_policy")
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
    )
