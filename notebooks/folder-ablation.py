"""The D-21 folding-baseline ablation at the live budget — `docs/L1/folders.md` §6.

Two `training.run` calls of **one** variant — one backend, one encoding, one
architecture, one learning rule, one utility, one hyper declaration, one seed set and
one sample budget — differing in exactly one thing: whether the configuration's pool
declaration names the three folding baselines of D-21.  So nothing but the population a
learner faces can move between the two arms (D-3, D-16, D-21).

It then answers the question the change exists for, by the action-census method of
`strata/records/r2-plateau-diagnosis.md`: one match per trained model, seats alternating,
the model's **own** decisions counted by action descriptor, and the chips per hand that
same match paid — against `always-call`, and against each folding baseline.  Every mean
is reported with a 95% interval from its standard error over hands, and the folders' own
fold rates are measured on hands no learner plays, at every street, beside `always-call`
(which never folds) and the `oracle` (which folds only when a raise crosses its odds).

Nothing here is an interface: it reads the declared entry points and prints a record
(D-12).  It **writes nothing under the repository's `checkpoints/`** — the write root is
redirected to a private temporary directory before `training` is imported, which is the
one ambient override `training.layout` reads (`battery.md` §2, `protocol.md` §5).

    PYTHONPATH=src .venv/bin/python notebooks/folder-ablation.py

The JSON it prints is one generation of one measurement: a re-run produces its own
numbers and no document quotes these as current (`protocol.md` §2, ASM-23).
"""

import argparse
import json
import math
import os
import statistics
import sys
import tempfile

# The write root, before any project module is imported: a run here must not touch the
# shipped checkpoint set (`battery.md` §2, `protocol.md` §5).
if not os.environ.get("PYPOKER_CHECKPOINT_ROOT"):
    os.environ["PYPOKER_CHECKPOINT_ROOT"] = tempfile.mkdtemp(
        prefix="pypoker-folder-ablation-"
    )

import agents  # noqa: E402
import engine  # noqa: E402
import evaluation  # noqa: E402
import features  # noqa: E402
import training  # noqa: E402

#: The three folding baselines of D-21 (`folders.md` §2), in the catalogue's order.
FOLDERS = ("fold-no-pair-or-face", "fold-no-pair-or-better", "fold-large-bet")

#: The one fixed opponent the chips are measured against, and the anchor D-6 pins.
ANCHOR = "always-call"

#: The opponents a folder's own fold rate is measured against: the caller that never
#: raises and the uniform draw that raises a third of its decisions, so a rule keyed on
#: the size of the bet is exercised (`folders.md` §6, D-6).
FOLD_OPPONENTS = (ANCHOR, "random")

#: What both arms share, and the one thing they do not (D-3, D-21).
SHARED = {
    "backend": "numpy",
    "encoding": "flat-numeric",
    "learning_rule": "masked-q-learning",
    "utility": "net-chips",
}
ARCHITECTURE = {
    "kind": "naive-stack",
    "width": 36,
    "depth": 2,
    "sparsity": 0.0,
    "residual": False,
}
SEEDS = (0, 1, 2)
TRAIN_HANDS = 1000
CENSUS_HANDS = 500
FOLDER_HANDS = 400
PARAM_BUDGET = 10000
TABLE = "live"

#: The three action descriptors of `e2e-surface.md` §2, by index.
DESCRIPTORS = {index: str(features.decode_action(index)) for index in (0, 1, 2)}


def configuration(label, baselines):
    """One single-variant configuration whose pool declares ``baselines`` and nothing else.

    The pool holds no version: a run's pool is the baselines alone when the window is
    empty, which is R1's case and the one that isolates the population from a lineage
    (`league.md` §2, ASM-16).  ``baselines`` is `records.md` §8's declaration key, so the
    folders join by declaration and the arm that names none is the league as it stands
    (ASM-32, D-21).
    """
    variant = {
        "name": "learner",
        "backend": SHARED["backend"],
        "encoding": SHARED["encoding"],
        "architecture": dict(ARCHITECTURE),
        "learning_rule": SHARED["learning_rule"],
        "utility": SHARED["utility"],
        "param_budget": PARAM_BUDGET,
        "samples": TRAIN_HANDS,
        "seeds": list(SEEDS),
        "device": "cpu",
        "snapshot_every": TRAIN_HANDS // 10,
        "table": TABLE,
    }
    return {
        "name": label,
        "axis": "the population the learner faces, at one learner and one budget",
        "carried_from": None,
        "primary": variant["name"],
        "pool": {
            "lineage": None,
            "m": 5,
            "frozen": True,
            "members": [],
            "baselines": list(baselines),
        },
        "variants": [variant],
    }


def interval(values):
    """The mean and its 95% interval from the standard error over hands."""
    count = len(values)
    if count == 0:
        return {"hands": 0, "mean": None, "se": None, "low": None, "high": None}
    mean = statistics.fmean(values)
    se = statistics.stdev(values) / math.sqrt(count) if count > 1 else 0.0
    return {
        "hands": count,
        "mean": mean,
        "se": se,
        "low": mean - 1.96 * se,
        "high": mean + 1.96 * se,
    }


def census(policy, opponent, hands, base_seed):
    """One match, seats alternating: the policy's action shares and its chips per hand.

    The counts are the policy's **own** decisions, never its opponent's, so a folder's
    folds are never counted as the learner's (D-16, `folders.md` §6).
    """
    counts = {name: 0 for name in DESCRIPTORS.values()}
    per_street = {}
    payoffs = []
    for index in range(int(hands)):
        seat = index % 2
        deal = int(base_seed) + index
        if seat == 0:
            episode = engine.play_hand(deal, policy, opponent)
        else:
            episode = engine.play_hand(deal, opponent, policy)
        for decision in episode["decisions"]:
            if decision["seat"][0] != seat:
                continue
            indices = list(features.legal_indices(decision["legal"]))
            for position, descriptor in enumerate(decision["legal"]):
                if descriptor == decision["action"]:
                    name = DESCRIPTORS[int(indices[position])]
                    counts[name] += 1
                    street = str(decision["readout"]["street"])
                    bucket = per_street.setdefault(street, {"decisions": 0, "fold": 0})
                    bucket["decisions"] += 1
                    if name == "fold":
                        bucket["fold"] += 1
                    break
        payoffs.append(float(episode["payoffs"][seat]))
    total = sum(counts.values())
    result = {
        "decisions": total,
        "counts": counts,
        "shares": {name: (100.0 * counts[name] / total if total else 0.0)
                   for name in counts},
        "fold_rate": (100.0 * counts["fold"] / total if total else 0.0),
        "fold_by_street": {
            street: {
                "decisions": bucket["decisions"],
                "fold": bucket["fold"],
                "rate": (100.0 * bucket["fold"] / bucket["decisions"]
                         if bucket["decisions"] else 0.0),
            }
            for street, bucket in per_street.items()
        },
    }
    result.update(interval(payoffs))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-hands", type=int, default=TRAIN_HANDS)
    parser.add_argument("--census-hands", type=int, default=CENSUS_HANDS)
    parser.add_argument("--folder-hands", type=int, default=FOLDER_HANDS)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    parser.add_argument("--out", default=os.path.join(tempfile.gettempdir(),
                                                     "pypoker-folder-ablation.json"))
    arguments = parser.parse_args()

    seed_set = [int(seed) for seed in arguments.seeds]
    report = {
        "seeds": seed_set,
        "train_hands": int(arguments.train_hands),
        "census_hands": int(arguments.census_hands),
        "folder_hands": int(arguments.folder_hands),
        "device": "cpu",
        "folders": list(FOLDERS),
        "shared": dict(SHARED),
        "runs": {},
        "folders_measured": {},
    }
    finals = {}
    for label, baselines in (("current-pool", ()), ("folder-pool", FOLDERS)):
        config = configuration("F1-" + label, baselines)
        print("training %s: pool baselines %r, seeds %r, %d hands -- write root %s"
              % (label, baselines, seed_set, arguments.train_hands,
                 os.environ["PYPOKER_CHECKPOINT_ROOT"]), flush=True)
        record = training.run(config, seed_set, arguments.train_hands, "cpu")
        report["runs"][label] = {
            "pool_id": record["pool"]["id"],
            "pool_members": [
                str(member.get("id") if isinstance(member, dict) else member)
                for member in record["pool"]["members"]
            ],
            "timings": record["timings"],
            "checkpoints": {},
        }
        block = record["checkpoints"]["learner"]
        for seed in seed_set:
            path = block[str(seed)]["final"]
            report["runs"][label]["checkpoints"][str(seed)] = path
            finals[(label, seed)] = evaluation.policy_from(path)
        _write(report, arguments.out)

    # The census: each trained model against the fixed caller, seats alternating.
    for label in report["runs"]:
        report["runs"][label]["census"] = {}
        for seed in seed_set:
            print("census %s seed %d" % (label, seed), flush=True)
            report["runs"][label]["census"][str(seed)] = census(
                finals[(label, seed)],
                agents.build_baseline(ANCHOR, int(seed)),
                arguments.census_hands,
                900000 + 1000 * seed,
            )
            _write(report, arguments.out)

    # The chips each trained model pays against each folding baseline.
    for label in report["runs"]:
        report["runs"][label]["versus_folders"] = {}
        for folder in FOLDERS:
            entries = []
            for seed in seed_set:
                print("chips %s against %s at seed %d" % (label, folder, seed),
                      flush=True)
                entries.append(census(
                    finals[(label, seed)],
                    agents.build_baseline(folder, int(seed)),
                    arguments.census_hands,
                    700000 + 1000 * seed,
                ))
            report["runs"][label]["versus_folders"][folder] = {
                "per_seed": entries,
                "pooled": _pooled(entries),
            }
            _write(report, arguments.out)

    # The folders' own fold rates, on hands no learner plays.  Two opponents, because a
    # folder's trigger is not the same against both: `fold-large-bet` folds only when a
    # bet exceeds half the stack, and `always-call` never makes one, so its rate against a
    # caller is 0 % by arithmetic and says nothing (`folders.md` §2, §6).
    for name in list(FOLDERS) + [ANCHOR, "oracle"]:
        for opponent in FOLD_OPPONENTS:
            entries = []
            for seed in seed_set:
                print("fold rate %s against %s at seed %d" % (name, opponent, seed),
                      flush=True)
                entries.append(census(
                    agents.build_baseline(name, int(seed)),
                    agents.build_baseline(opponent, int(seed) + 1),
                    arguments.folder_hands,
                    500000 + 1000 * seed,
                ))
            report["folders_measured"]["%s/vs-%s" % (name, opponent)] = {
                "per_seed": entries,
                "pooled": _pooled(entries),
            }
            _write(report, arguments.out)

    _write(report, arguments.out)
    print(json.dumps(_summary(report), indent=2, sort_keys=True))
    return report


def _seconds(timings):
    """The seconds per hand a run record's ``timings`` block carries, however it is keyed.

    `records.md` §12 requires the block to carry hands and seconds per hand and leaves
    its nesting to `training`, so this reader asks the block for the fact and never
    assumes a per-seed shape (`protocol.md` §2, ASM-23).
    """
    found = []

    def walk(value, depth=0):
        if depth > 6:
            return
        if isinstance(value, dict):
            for key, inner in value.items():
                if "second" in str(key).lower() and isinstance(inner, (int, float)):
                    found.append(float(inner))
                else:
                    walk(inner, depth + 1)
        elif isinstance(value, (list, tuple)):
            for inner in value:
                walk(inner, depth + 1)

    walk(timings)
    return found


def _pooled(entries):
    """One entry's per-seed counts and payoffs, pooled across the seeds."""
    decisions = sum(entry["decisions"] for entry in entries)
    counts = {name: 0 for name in DESCRIPTORS.values()}
    for entry in entries:
        for name, count in entry["counts"].items():
            counts[name] += count
    shares = {name: (100.0 * counts[name] / decisions if decisions else 0.0)
              for name in counts}
    means = [entry["mean"] for entry in entries if entry["mean"] is not None]
    return {
        "decisions": decisions,
        "counts": counts,
        "shares": shares,
        "fold_rate": (100.0 * counts["fold"] / decisions if decisions else 0.0),
        "fold_by_street": _pooled_streets(entries),
        "mean_chips_per_hand": statistics.fmean(means) if means else None,
        "per_seed_means": [entry["mean"] for entry in entries],
        "per_seed_low": [entry["low"] for entry in entries],
        "per_seed_high": [entry["high"] for entry in entries],
    }


def _pooled_streets(entries):
    """The fold counts per street, pooled across the seeds a container was measured at."""
    pooled = {}
    for entry in entries:
        for street, bucket in entry["fold_by_street"].items():
            slot = pooled.setdefault(street, {"decisions": 0, "fold": 0})
            slot["decisions"] += bucket["decisions"]
            slot["fold"] += bucket["fold"]
    for slot in pooled.values():
        slot["rate"] = (100.0 * slot["fold"] / slot["decisions"]
                        if slot["decisions"] else 0.0)
    return pooled


def _write(report, path):
    """Write the whole record to ``path``, so a long measurement survives a stop."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _summary(report):
    """The shares, the fold rates and the chips per hand of both arms, over their seeds."""
    summary = {"arms": {}, "folders": {}}
    for label, block in report["runs"].items():
        entries = [block["census"][str(seed)] for seed in sorted(block["census"])]
        summary["arms"][label] = {
            "pool_id": block["pool_id"],
            "pool_members": block["pool_members"],
            "versus_always_call": _pooled(entries),
            "versus_folders": {
                folder: value["pooled"]
                for folder, value in block["versus_folders"].items()
            },
            "seconds_per_hand": _seconds(block["timings"]),
        }
    for name, block in report["folders_measured"].items():
        summary["folders"][name] = block["pooled"]
    return summary


if __name__ == "__main__":
    main()
    sys.exit(0)
