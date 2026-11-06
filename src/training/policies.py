"""The learner's side of a hand, assembled from this module's granted calls.

`agents.as_policy` is not training's to call (`module-map.md` §2), so the training-time
policy is built here out of the five `features` calls and `agents.act`: encode the
readout, take the decision's legal mask, decide, and decode the index back into the
descriptor `engine` applies (features/surface.md §6, §8, §9; agents/surface.md §6).
`agents.act`'s decision is a function of the learner's state and of the decision — never
of a stream position — so the policy assembled here answers one decision one way however
often it is asked (agents/surface.md §1, ASM-2).
"""

import agents
import features


def _learner_policy(learner, encoder):
    """A policy in the sense of `e2e-surface.md` §2 for one learner over one encoder."""

    def policy(readout, legal_actions):
        observation = features.encode(encoder, readout)
        mask = features.legal_indices(legal_actions)
        decision = agents.act(learner, observation, mask)
        return features.decode_action(int(decision["action"]))

    return policy
