"""The D-43 counterfactual pair's criterion, computed from two run records.

`docs/L1/counterfactual.md` §7 pins the criterion **before any number of the member
existed**, and this script is the computer §7 names: `notebooks/counterfactual-criterion.py`
— `training`'s path, as `utilities.md` §10's ablation script is — reads the two arms' run
records, applies §7's three conjuncts verbatim and writes
`<write root>/evidence/counterfactual-pair.json`, which is
`checkpoints/evidence/counterfactual-pair.json` for a run that is not a battery's.

    PYTHONPATH=src .venv/bin/python notebooks/counterfactual-criterion.py <arm-a.json> <arm-b.json>

The **first** argument is the `none` arm — the variant whose training targets are its
rule's own bootstrap — and the second is the `reveal-counterfactual` arm, so the criterion's
two directions ("the member's fold share is at least 5.0 %" and "it exceeds the `none`
arm's by at least 5.0 points") are read off the arguments' order and never guessed.

**What it reads, and from where.** The run record's `greedy` block of the arm's variant at
each pinned seed (`records.md` §15, `sizing.md` §4, D-28, ASM-38): the ordered decision
records, each carrying `descriptor`, `legal` and the `tie` flag, and the block's
`net_chips`, one net chip delta per hand. From those it forms, per seed and per arm, the
decision census **by descriptor with the tie-resolved decisions excluded** (the `tie` flag,
ASM-37), the fold share over those same tie-excluded decisions, the chips per hand from
`net_chips` with a 95 % standard-error interval, the decision count, the block's `mode`, and
the record's `game` and `pool.id` — and then applies §7.

**Nothing here is a training path.** It trains no model, builds no learner, plays no hand
and writes nothing but the one evidence file; a record's curves, pool, checkpoints and
header are read only for the `game`, the `pool.id` and the shape's vocabulary, which the
header's `action space` declares and the census needs in order to name a descriptor that was
never chosen with a count of zero rather than leaving it out (`records.md` §12, §15). A
record missing one of the pinned seeds' blocks is refused by name: a block that is absent is
not a block that failed a conjunct.

The JSON carries both arms' census blocks, the criterion as pinned, the per-seed verdicts
with the conjunct that decided each, and the one pool id the pair held (D-3, D-16).
"""

import argparse
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)

#: The one ambient name `docs/L2/training/write-root.md` §3 gives the write root: read from
#: the environment and never from a `training` internal, exactly as a case reads it, so a
#: redirected run writes outside the repository and the shipped `checkpoints/` gains no file
#: (`write-root.md` §1, §3, `battery.md` §2, `protocol.md` §5).
OVERRIDE = "PYPOKER_CHECKPOINT_ROOT"

#: `checkpoints/evidence/`, the directory the one evidence artefact lands in when the write
#: root is the declared one (`docs/L3/training/evidence.md` §1, `counterfactual.md` §7).
DECLARED_ROOT = os.path.join(REPO_ROOT, "checkpoints")

#: The one file this script writes, relative to the write root (`counterfactual.md` §7).
EVIDENCE = os.path.join("evidence", "counterfactual-pair.json")

#: `counterfactual.md` §7's criterion, **as pinned there and before any run of the member**:
#: the observable, the seeds, the budgets, the shape, the two thresholds and the parity
#: condition. Quoted as data so the artefact carries the criterion it was judged by and a
#: reader never has to take this file's word for it (D-27, ASM-23, `sizing.md` §7).
CRITERION = {
    "observable": (
        "the greedy census by descriptor of the learner's own decisions in the record's "
        "`greedy` block, with the tie-resolved decisions excluded, and the same block's "
        "chips per hand (records.md §15, ASM-37, D-28, ASM-38)"
    ),
    "seeds": [0, 1],
    "hands_per_variant_per_seed": 20000,
    "greedy_block_hands": 2000,
    "shape": "six-seat-no-limit-100",
    "fold_share_min_percent": 5.0,
    "fold_share_advantage_points": 5.0,
    "conjuncts": [
        "the reveal-counterfactual arm's fold share is at least 5.0 % of its "
        "tie-excluded decisions",
        "it exceeds the none arm's fold share over the same 2,000 deals by at least "
        "5.0 percentage points",
        "both records name six-seat-no-limit-100, both blocks carry mode `off`, and both "
        "record one pool id",
    ],
    "not_thresholded": "chips per hand, the decision count and every descriptor's share "
                       "are reported and never thresholded (counterfactual.md §7)",
}

#: The descriptor that index 0 of every declared vocabulary names — `fold`, the first of
#: `sizing.md` §3's declared order — read off the block's own header rather than assumed;
#: this is the fallback spelling when a record carries no `action space` row.
FOLD = "fold"

#: The block's one accepted mode. A block carrying any other value — or a census computed
#: over training decisions — is refused by name (`records.md` §15, D-28, ASM-38).
MODE = "off"

#: The two-sided 95 % normal quantile the chips interval is formed with, the same one
#: `notebooks/utility-ablation.py` uses (`utilities.md` §10, ASM-41).
Z = 1.96


def write_root():
    """The root this evidence file is written under: the ambient override, else the declared one.

    `PYPOKER_CHECKPOINT_ROOT` names another root for a redirected run — that is the whole
    of `docs/L2/training/write-root.md` §3 — and this derives the answer from `os.environ`
    alone so the script depends on no `training` internal to find out where it may write
    (`write-root.md` §5, `docs/L3/training/checkpoints.md` §5).
    """
    value = os.environ.get(OVERRIDE)
    if value:
        return os.path.abspath(value)
    return DECLARED_ROOT


def read_record(path):
    """One run record, read from the JSON file the caller named (`records.md` §12)."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            record = json.load(handle)
    except OSError as error:
        raise SystemExit("counterfactual-criterion: cannot read %r: %s" % (path, error))
    except ValueError as error:
        raise SystemExit("counterfactual-criterion: %r is not JSON: %s" % (path, error))
    if not isinstance(record, dict):
        raise SystemExit(
            "counterfactual-criterion: %r is not a run record, which records.md §12 "
            "makes a mapping" % (path,)
        )
    return record


def variant_rows(record, path):
    """One record's `variants` rows, as `records.md` §12 makes them (`loop.md` §4)."""
    rows = record.get("variants")
    if not isinstance(rows, list) or not rows:
        raise SystemExit(
            "counterfactual-criterion: the record %r carries no `variants` row, so the "
            "arm cannot be named (records.md §12)" % (path,)
        )
    return [row for row in rows if isinstance(row, dict)]


def arm(record, path, position):
    """The variant one arm's record contributes, and the rule that chose it.

    An arm's record may carry one variant — the shape a paired run of two separate
    configurations writes — or two, because a configuration may train two variants in one
    call (`ladder.md` §2). So the arm is chosen by what the record says the variant is
    trained under: the **first** argument is the `none` arm, whose row carries **no**
    `counterfactual` key at all (`loop.md` §3, `counterfactual.md` §6), and the second is an
    arm whose row names one. A record that offers exactly one variant is that variant
    whatever its position, and that is reported as how the arm was chosen.
    """
    rows = variant_rows(record, path)
    if len(rows) == 1:
        return rows[0], "the record's only variant"
    named = [
        row for row in rows
        if (row.get("counterfactual") is None) == (position == 0)
    ]
    if len(named) == 1:
        return named[0], "its `counterfactual` row among the record's two variants"
    return rows[0], "the record's first variant, because the row did not single one out"


def vocabulary(record):
    """The shape's vocabulary as `{index: descriptor}`, read off the record's own header.

    `records.md` §12's `header` carries `action space`, the vocabulary the run's shape
    declares in its own order — three descriptors on the fixed-limit shape, six on either
    uncapped one — so the census names a descriptor no decision chose with a count of zero
    and this script imports nothing to find it (`records.md` §15, `sizing.md` §3, D-13).
    """
    header = record.get("header")
    space = header.get("action space") if isinstance(header, dict) else None
    if not isinstance(space, dict):
        return {}
    declared = {}
    for index, descriptor in space.items():
        try:
            declared[int(index)] = str(descriptor)
        except (TypeError, ValueError):
            continue
    return declared


def block_of(record, variant, seed, path):
    """One variant × one seed's `records.md` §15 block, or the refusal naming what is missing."""
    greedy = record.get("greedy")
    per_variant = greedy.get(variant) if isinstance(greedy, dict) else None
    block = per_variant.get(str(int(seed))) if isinstance(per_variant, dict) else None
    if not isinstance(block, dict):
        raise SystemExit(
            "counterfactual-criterion: the record %r carries no `greedy` block for the "
            "variant %r at seed %r, and the criterion is read off one block per variant per "
            "seed (records.md §15, counterfactual.md §7)" % (path, variant, int(seed))
        )
    return block


def interval(values):
    """The mean and its 95 % interval from the standard error over hands (ASM-41)."""
    count = len(values)
    if count == 0:
        return {"hands": 0, "mean": None, "se": None, "low": None, "high": None}
    mean = statistics.fmean(values)
    se = statistics.stdev(values) / math.sqrt(count) if count > 1 else 0.0
    return {
        "hands": count,
        "mean": mean,
        "se": se,
        "low": mean - Z * se,
        "high": mean + Z * se,
    }


def census(block, declared):
    """One block's census: descriptors, the fold share, the chips and the mode (§7).

    The census is over the block's decision records with the **tie-resolved** ones
    excluded, because a decision the tie-break chose is not a decision the policy preferred
    (`records.md` §15's `tie`, ASM-37); the fold share is a count over those same
    tie-excluded decisions, so the two numbers of a pair are shares of one denominator. A
    descriptor the shape declares and no counted decision chose is reported with a zero
    rather than dropped.
    """
    decisions = [
        decision for decision in (block.get("decisions") or [])
        if isinstance(decision, dict)
    ]
    counted = [decision for decision in decisions if not decision.get("tie")]
    counts = {name: 0 for name in declared.values()}
    for decision in counted:
        descriptor = str(decision.get("descriptor"))
        counts[descriptor] = counts.get(descriptor, 0) + 1
    total = len(counted)
    shares = {
        name: (100.0 * count / total if total else 0.0) for name, count in counts.items()
    }
    fold = declared.get(0, FOLD)
    chips = [
        float(value) for value in (block.get("net_chips") or ())
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ]
    result = {
        "mode": block.get("mode"),
        "seed": block.get("seed"),
        "hands": block.get("hands"),
        "decisions": len(decisions),
        "excluded_ties": len(decisions) - total,
        "counted_decisions": total,
        "census": dict(counts),
        "shares": shares,
        "fold": fold,
        "fold_count": counts.get(fold, 0),
        "fold_share": (100.0 * counts.get(fold, 0) / total if total else 0.0),
        "net_chips": interval(chips),
    }
    result["chips_per_hand"] = result["net_chips"]
    return result


def verdict(seed, none_arm, member_arm, none_record, member_record):
    """§7's three conjuncts for one seed, and the one that decided the verdict.

    The conjuncts are §7's own, in its own order, and the pair is read **at once**: (1) the
    member arm's fold share is at least 5.0 % of its tie-excluded decisions; (2) it exceeds
    the `none` arm's over the same 2,000 deals by at least 5.0 percentage points; (3) both
    records name the pinned shape, both blocks carry `mode: "off"`, and both record one pool
    id. The **first** conjunct that fails is the one the verdict is named with, and a pair
    that passes all three is a PASS; a run whose chips improve does not save it, because
    chips are reported and never thresholded (D-24, D-28).
    """
    shape = CRITERION["shape"]
    pool_a = _pool_id(none_record)
    pool_b = _pool_id(member_record)
    first = member_arm["fold_share"] >= CRITERION["fold_share_min_percent"]
    advantage = member_arm["fold_share"] - none_arm["fold_share"]
    second = advantage >= CRITERION["fold_share_advantage_points"]
    third = (
        str(none_record.get("game")) == shape
        and str(member_record.get("game")) == shape
        and none_arm["mode"] == MODE
        and member_arm["mode"] == MODE
        and pool_a is not None
        and pool_a == pool_b
    )
    detail = {
        1: "the member arm's fold share is %.4f %% of its tie-excluded decisions, against "
           "the pinned %.1f %%" % (member_arm["fold_share"], CRITERION["fold_share_min_percent"]),
        2: "the member arm's fold share exceeds the none arm's by %.4f points, against the "
           "pinned %.1f" % (advantage, CRITERION["fold_share_advantage_points"]),
        3: "the pair is %r and %r on the shape %r, its two blocks carry mode %r and %r, and "
           "its two pool ids are %r and %r, while the pinned shape, mode and parity are one "
           "%r, %r and one id"
           % (none_record.get("game"), member_record.get("game"), shape,
              none_arm["mode"], member_arm["mode"], pool_a, pool_b, shape, MODE),
    }
    results = {1: first, 2: second, 3: third}
    decided = next((number for number in (1, 2, 3) if not results[number]), None)
    return {
        "seed": int(seed),
        "conjuncts": {"1": bool(first), "2": bool(second), "3": bool(third)},
        "fold_advantage": advantage,
        "verdict": "PASS" if decided is None else "FAIL",
        "decided_by": decided,
        "decided": (
            "conjunct %d: %s" % (decided, detail[decided]) if decided is not None
            else "none — all three conjuncts of counterfactual.md §7 hold"
        ),
    }


def _pool_id(record):
    """The one pool id a record declares (`records.md` §12, `loop.md` §3)."""
    pool = record.get("pool")
    identifier = pool.get("id") if isinstance(pool, dict) else None
    return str(identifier) if identifier is not None else None


def measure(record, path, position, seed):
    """One arm's measured block at one seed: the census and what the record says about it."""
    selected, how = arm(record, path, position)
    variant = str(selected.get("name"))
    declared = vocabulary(record)
    block = block_of(record, variant, seed, path)
    measured = census(block, declared)
    measured.update(
        {
            "file": path,
            "variant": variant,
            "selected_by": how,
            "counterfactual": selected.get("counterfactual"),
            "utility": selected.get("utility"),
            "game": record.get("game"),
            "pool": _pool_id(record),
            "vocabulary": {str(index): name for index, name in sorted(declared.items())},
        }
    )
    return measured


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("none_arm", help="the run record of the `none` arm")
    parser.add_argument("member_arm", help="the run record of the reveal-counterfactual arm")
    arguments = parser.parse_args()

    none_record = read_record(arguments.none_arm)
    member_record = read_record(arguments.member_arm)
    root = write_root()
    report = {
        "criterion": CRITERION,
        "write root": root,
        "arms": [
            {"role": "none", "file": arguments.none_arm,
             "game": none_record.get("game"), "pool": _pool_id(none_record)},
            {"role": "reveal-counterfactual", "file": arguments.member_arm,
             "game": member_record.get("game"), "pool": _pool_id(member_record)},
        ],
        "seeds": {},
    }
    for seed in CRITERION["seeds"]:
        none_arm = measure(none_record, arguments.none_arm, 0, seed)
        member_arm = measure(member_record, arguments.member_arm, 1, seed)
        judged = verdict(seed, none_arm, member_arm, none_record, member_record)
        report["seeds"][str(int(seed))] = {
            "none": none_arm,
            "reveal-counterfactual": member_arm,
            "verdict": judged,
        }
        print(
            "seed %d: %s — %s"
            % (int(seed), judged["verdict"], judged["decided"]),
            flush=True,
        )
        print(
            "        fold share %s %.4f %% (%d of %d tie-excluded decisions of %r hands) "
            "against %s %.4f %%; chips per hand %s %s [%s, %s] against %s %s [%s, %s]"
            % (
                none_arm["variant"], none_arm["fold_share"], none_arm["fold_count"],
                none_arm["counted_decisions"], none_arm["hands"],
                member_arm["variant"], member_arm["fold_share"],
                none_arm["variant"],
                _number(none_arm["chips_per_hand"]["mean"]),
                _number(none_arm["chips_per_hand"]["low"]),
                _number(none_arm["chips_per_hand"]["high"]),
                member_arm["variant"],
                _number(member_arm["chips_per_hand"]["mean"]),
                _number(member_arm["chips_per_hand"]["low"]),
                _number(member_arm["chips_per_hand"]["high"]),
            ),
            flush=True,
        )

    verdicts = [entry["verdict"]["verdict"] for entry in report["seeds"].values()]
    report["verdict"] = "PASS" if verdicts and all(item == "PASS" for item in verdicts) else "FAIL"
    report["pool"] = {
        "id": _pool_id(none_record) if _pool_id(none_record) == _pool_id(member_record) else None,
        "ids": [_pool_id(none_record), _pool_id(member_record)],
        "same": _pool_id(none_record) is not None
                and _pool_id(none_record) == _pool_id(member_record),
    }
    report["game"] = CRITERION["shape"]
    path = os.path.join(root, EVIDENCE)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("verdict %s over %r; evidence written to %s"
          % (report["verdict"], CRITERION["seeds"], path), flush=True)
    return report


def _number(value):
    """A measure printed as a number, and `None` printed as `n/a`."""
    return "n/a" if value is None else "%.4f" % (float(value),)


if __name__ == "__main__":
    main()
    sys.exit(0)
