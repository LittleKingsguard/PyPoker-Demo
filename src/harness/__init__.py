"""harness — test support (surface.md §1): it calls declared entry points and never reimplements one."""
import tempfile, time
from collections.abc import Mapping

import agents, engine, evaluation, features, training

__all__ = ["drive", "expect", "factory", "fixtures", "seam", "timings"]
KINDS = ("zero-sum", "legal-choice", "counted", "refused")
COUNTS = ("wins", "win", "ties", "tie", "losses", "loss")
OBJECTS = {"encoder": features.build_encoder, "learner": agents.build_learner, "baseline": agents.build_baseline,
           "hand": engine.new_hand, "rung": training.rung, "pool": evaluation.build_pool}
ROOT, COST = [], {"hands": 0, "wall_clock_seconds": 0.0, "cases": 0, "steps": 0}

class HarnessError(Exception): pass    # the base of every refusal this module raises (errors.md §2)
class UnknownFactoryKind(HarnessError): pass    # factory: the kind is not one of the six
class UnknownExpectationKind(HarnessError): pass    # expect: the kind is not a string
class NoLegalAction(HarnessError): pass    # seam: the legal set it was handed is empty

def _quantity(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)
def _numbers(value):
    items = [value] if _quantity(value) else value.values() if isinstance(value, Mapping) else value if isinstance(value, (list, tuple)) else ()
    return [item for item in items if _quantity(item)]
def _deltas(value):
    if isinstance(value, Mapping) and "payoffs" in value:
        return _numbers(value["payoffs"])
    if isinstance(value, Mapping) and "directions" in value:
        rows = value["directions"] if isinstance(value["directions"], (list, tuple)) else ()
        return _numbers([row.get("mean_chip_delta") for row in rows if isinstance(row, Mapping)])
    return _numbers(value)
def _zero_sum(value):
    deltas = _deltas(value)
    if len(deltas) != 2:
        return "the value states no two per-seat chip deltas"
    return None if abs(sum(deltas)) <= 1e-9 else "the chip deltas %r do not sum to zero" % (deltas,)
def _legal_choice(value):
    legal = value.get("legal") if isinstance(value, Mapping) else None
    if not isinstance(legal, (list, tuple)) or not legal or "chosen" not in value:
        return "the value states no legal descriptors"
    return None if any(value["chosen"] == candidate for candidate in legal) else "the chosen descriptor is outside the legal set"
def _counted(value):
    hands = value.get("hands") if isinstance(value, Mapping) else None
    rows = value.get("directions") if isinstance(value, Mapping) else None
    if not isinstance(rows, (list, tuple)) or not rows or not _quantity(hands) or not all(isinstance(row, Mapping) for row in rows):
        return "the value is not a cell record carrying its directions and hands"
    for row in rows:
        counted = sum(row[key] for key in COUNTS if _quantity(row.get(key)))
        if counted != hands:
            return "a direction counts %r outcomes and the cell reports %r hands" % (counted, hands)
    return None
def _refused(value):
    return None if isinstance(value, Mapping) and value.get("refused") is True else "the observed work returned a value rather than refusing"
_CHECKS = {"zero-sum": _zero_sum, "legal-choice": _legal_choice, "counted": _counted, "refused": _refused}

def expect(kind, observation):
    """`expect(kind, observation)` — one verdict for one observed value (surface.md §6)."""
    if not isinstance(kind, str):
        raise UnknownExpectationKind("harness.expect refused the kind %r: a kind is a name fixtures() lists, %s" % (kind, ", ".join(KINDS)))
    if kind not in _CHECKS:
        return {"kind": kind, "verdict": "fail", "reason": "harness.expect failed the kind %r: fixtures() lists %s" % (kind, ", ".join(KINDS))}
    try:
        fact = _CHECKS[kind](observation)
    except Exception as exc:
        fact = "the value could not be read: %s: %s" % (type(exc).__name__, exc)
    return {"kind": kind, "verdict": "pass" if fact is None else "fail", "reason": None if fact is None else "harness.expect failed the kind %r: %s" % (kind, fact)}

def fixtures():
    """`fixtures()` — the preconditions a case starts from (surface.md §3)."""
    if not ROOT:
        ROOT.append(tempfile.mkdtemp(prefix="pypoker-harness-"))
    return {"root": ROOT[0], "seed": 0, "device": "cpu", "expectations": list(KINDS)}

def factory(kind, options):
    """`factory(kind, options)` — one declared object, built by its owner (surface.md §4)."""
    if not isinstance(kind, str) or kind not in OBJECTS:
        raise UnknownFactoryKind("harness.factory refused the kind %r: the map declares %s" % (kind, ", ".join(sorted(OBJECTS))))
    return OBJECTS[kind](*options) if kind == "baseline" else OBJECTS[kind](options)

def seam(label):
    """`seam(label)` — one policy double, for any label (surface.md §5)."""
    calls = []
    def policy(readout, legal_actions):
        legal = list(legal_actions)
        if not legal:
            raise NoLegalAction("harness.seam(%r) refused the empty legal set: a policy returns a member of legal_actions" % (label,))
        position = len(calls) % len(legal) if label == "synthetic" else 0
        calls.append({"readout": readout, "legal": legal, "chosen": legal[position]})
        return legal[position]
    policy.calls, policy.label = calls, label
    return policy

def timings():
    """`timings()` — the cost the driver collected (surface.md §7)."""
    hands, clock = COST["hands"], COST["wall_clock_seconds"]
    return dict(COST, seconds_per_hand=clock / hands if hands else 0.0, hands_per_second=hands / clock if clock else 0.0)

def _hands(value):
    declared = value.get("hands") if isinstance(value, Mapping) and "directions" in value else None
    return 1 if isinstance(value, Mapping) and "payoffs" in value and "decisions" in value else declared if type(declared) is int and declared >= 0 else 0
def _problem(case):
    if not isinstance(case, Mapping):
        return "harness.drive refused the case: it is not a mapping"
    if not isinstance(case.get("id"), str) or not case["id"]:
        return "harness.drive refused the case: it carries no non-empty 'id'"
    for key in ("steps", "expect"):
        if not isinstance(case.get(key), (list, tuple)) or not case[key]:
            return "harness.drive refused the case: it carries no non-empty %r" % (key,)
    return None if all(callable(step) for step in case["steps"]) else "harness.drive refused the case: a step is not a zero-argument callable"
def _judge(entries, result):
    reason, steps = None, len(result["steps"])
    for entry in entries:
        name = entry if isinstance(entry, str) else entry.get("kind") if isinstance(entry, Mapping) else None
        step = steps - 1 if isinstance(entry, str) else entry.get("step") if isinstance(entry, Mapping) else None
        if not isinstance(name, str):
            failure = "harness.drive refused the expectation %r: an entry is a kind name or a {\"kind\",\"step\"} mapping" % (entry,)
        elif not isinstance(step, int) or isinstance(step, bool) or not 0 <= step < steps:
            failure = "harness.drive refused the expectation %r: it names no step of this case" % (name,)
        else:
            verdict = expect(name, result["steps"][step]["outcome"])
            result["expectations"].append({"kind": verdict["kind"], "step": step, "verdict": verdict["verdict"], "reason": verdict["reason"]})
            failure = None if verdict["verdict"] == "pass" else "harness.drive failed step %d: %s" % (step, verdict["reason"])
        reason = reason if reason is not None else failure
    return reason

def drive(case):
    """`drive(case)` — one case, one verdict (surface.md §2)."""
    began = time.perf_counter()
    record = {"id": case.get("id") if isinstance(case, Mapping) else None, "steps": [], "expectations": [], "hands": 0, "wall_clock_seconds": 0.0, "verdict": "fail", "reason": _problem(case)}
    if record["reason"] is None:
        for index, step in enumerate(case["steps"]):
            started = time.perf_counter()
            try:
                outcome, refused = step(), False
            except Exception as exc:
                outcome, refused = {"refused": True, "error": "%s: %s" % (type(exc).__name__, exc)}, True
            record["steps"].append({"index": index, "outcome": outcome, "refused": refused, "seconds": time.perf_counter() - started})
            record["hands"] += _hands(outcome)
        record["reason"] = _judge(case["expect"], record)
        unjudged = [index for index in range(len(record["steps"])) if index not in {entry["step"] for entry in record["expectations"]}]
        record["reason"] = record["reason"] or ("harness.drive ran step %d, and no expectation judges it" % unjudged[0] if unjudged else None)
        record["verdict"] = "pass" if record["reason"] is None else "fail"
    record["wall_clock_seconds"] = time.perf_counter() - began
    COST["hands"] += record["hands"]
    COST["wall_clock_seconds"] += record["wall_clock_seconds"]
    COST["cases"] += 1
    COST["steps"] += len(record["steps"])
    return record
