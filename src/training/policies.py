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


def _learner_policy(learner, encoder, shape=None, model=None, values=None):
    """A policy in the sense of `e2e-surface.md` §2 for one learner over one encoder.

    `model` is the frozen card estimator an encoder that declares the tenth field needs:
    the decision's readout is **stated** first -- a fresh copy carrying every fact the
    encoder declares and the caller's mapping untouched -- and an encoder that declares
    none is handed the readout as it arrived, so the injection costs nothing where nothing
    is declared.  `shape` is read for `bet_size` alone and `values` for the opponent
    model's two readings alone; a declared fact with no producer is refused by name
    (`ASM-47`, `strength-design.md` §B.3).
    """

    def policy(readout, legal_actions):
        readout = features.stated(
            model, readout, encoder=encoder, shape=shape, values=values
        )
        observation = features.encode(encoder, readout)
        mask = features.legal_indices(legal_actions)
        decision = agents.act(learner, observation, mask)
        return features.decode_action(int(decision["action"]), shape=shape)

    return policy


def _stated_policy(policy, model, encoder=None, shape=None, values=None):
    """One policy with the readout injected before it decides (`ASM-47`).

    The greedy pass plays `agents.as_policy`'s policy, which asks the readout for the facts
    the encoder carries and encodes it itself; so the injection has to happen **outside**
    that policy and not inside `features` or `agents`.  This wrapper is the one place it
    happens for the pass, and `greedy.py` is untouched: its retained records carry an index,
    a descriptor, an amount, a limit, a legal mask and a tie flag and no readout at all, so
    nothing in the retained block changes (`ASM-47`, `records.md` §15).  The wrapper carries
    the **encoder**, so the facts it injects are the facts that encoder declares: an encoder
    that declares none is played without a wrapper at all, exactly as the pass it served
    before the injected facts existed (`strength-design.md` §B.3).
    """
    if model is None and encoder is None:
        return policy

    def wrapped(readout, legal_actions):
        return policy(
            features.stated(
                model, readout, encoder=encoder, shape=shape, values=values
            ),
            legal_actions,
        )

    return wrapped
