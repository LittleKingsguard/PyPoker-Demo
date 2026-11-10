"""The learner's side of a hand, assembled from this module's granted calls.

`agents.as_policy` is the exploration-off policy the greedy pass plays (`greedy.py` §1) and
not the training-time one (`module-map.md` §2): the training-time policy is built here out
of the five `features` calls and `agents.act` — encode the readout, take the decision's
legal mask, decide, and decode the index back into the descriptor `engine` applies
(features/surface.md §6, §8, §9; agents/surface.md §6).  `agents.act`'s decision is a
function of the learner's state and of the decision — never of a stream position — so the
policy assembled here answers one decision one way however often it is asked
(agents/surface.md §1, ASM-2).

**The index decodes in the run's own shape's vocabulary.**  An index is one of its own
shape's descriptors and of no other's, so `decode_action` is handed the shape the learner
was built on: on the default shape that is the `{0, 1, 2}` a run has always used, and on
the six-descriptor shape it is that shape's six (`shapes.md` §2–§3, sizing.md §3).  A
closure that decoded with no shape would hand the engine a default-shape descriptor for a
six-index decision, which the engine refuses as an illegal action — so the shape is
threaded through rather than left to default.
"""

import agents
import features


def _learner_policy(learner, encoder, shape=None):
    """A policy in the sense of `e2e-surface.md` §2 for one learner over one encoder."""

    def policy(readout, legal_actions):
        observation = features.encode(encoder, readout)
        mask = features.legal_indices(legal_actions)
        decision = agents.act(learner, observation, mask)
        return features.decode_action(int(decision["action"]), shape=shape)

    return policy
