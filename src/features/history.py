"""ASM-E2's history grammar, read as one action index (flat-numeric.md §5).

A history entry is a plain `str` of exactly four documented forms:

    "<street> seat <index> folds"        -> 0
    "<street> seat <index> checks"       -> 1
    "<street> seat <index> calls <n>"    -> 1
    "<street> seat <index> raises to <n>" -> 2

The verb is the entry's fourth whitespace-separated token, and it decides the action
index.  The street, the seat and the amount are other blocks -- or not facts of the
readout at all -- so they are skipped, never carried (README.md §4).  A `raises` entry
carries two more tokens than a `folds`, so the form's own length is checked with the
verb; a fifth form is refused naming the entry, because guessing would silently
mislabel an action (guardrails.md G13, errors.md §3).
"""

from __future__ import annotations

import re

from .errors import InvalidReadout

# The verb a documented entry's fourth token is, and the action index it denotes --
# the vocabulary's own order (vocabulary.md §1, flat-numeric.md §5).
_VERBS = {"folds": 0, "checks": 1, "calls": 1, "raises": 2}

# Each form's token count: the four-token forms carry no amount, `calls` one, and
# `raises` the marker "to" and an amount.
_FORM_TOKENS = {"folds": 4, "checks": 4, "calls": 5, "raises": 6}

# An amount is one or more ASCII decimal digits: `str.isdigit()` alone is true for
# non-ASCII digits, which ASM-E2's grammar does not spell (flat-numeric.md §6).
_AMOUNT = re.compile(r"[0-9]+")


def _is_amount(token):
    """Whether a token is an amount of ASCII decimal digits (flat-numeric.md §6)."""
    return _AMOUNT.fullmatch(token) is not None


def action_of_entry(entry):
    """The vocabulary index of the action one history entry applied (ASM-E2)."""
    if isinstance(entry, str):
        tokens = entry.split()
        verb = tokens[3] if len(tokens) > 3 else None
        if verb in _FORM_TOKENS and _is_documented(tokens, verb):
            return _VERBS[verb]
    raise InvalidReadout(
        "encode(readout): 'history' must hold the four documented entries, and %r is "
        "not one" % (entry,)
    )


def _is_documented(tokens, verb):
    """Whether the tokens are exactly one of the four forms of ASM-E2."""
    if len(tokens) != _FORM_TOKENS[verb]:
        return False
    if tokens[1] != "seat":
        return False
    if verb == "calls":
        return _is_amount(tokens[4])
    if verb == "raises":
        return tokens[4] == "to" and _is_amount(tokens[5])
    return True
