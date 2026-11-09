"""The D-20 utility ablation at the live budget — `docs/L1/utilities.md` §10.

Two variants that differ **only** in `utility`: one trained on `net-chips` and one on
`stack-shortfall`, at one backend, one encoding, one architecture, one learning rule and
one declared hyper, on the fixed seeds `0, 1, 2`, at the live budget of 1,000 hands per
variant per seed (D-20, `protocol.md` §2, ASM-8).  The two arms train in one
`training.run` call, against one frozen pool, so nothing but the utility can differ
between them (D-16, D-19).

It then answers the question the change exists for, by the action-census method of
`strata/records/r2-plateau-diagnosis.md`: one match per trained model, seats alternating,
the model's own decisions counted by action descriptor, and the chips per hand that same
match paid — against `always-call`, and against the other variant's model at the same
seed.  Every mean is reported with a 95% interval from its standard error over hands.

Nothing here is an interface: it reads the declared entry points and prints a record
(D-12).  It **writes nothing under the repository's `checkpoints/`** — the write root is
redirected to a private temporary directory before `training` is imported, which is the
one ambient override `training.layout` reads (`battery.md` §2, `protocol.md` §5).

    PYTHONPATH=src .venv/bin/python notebooks/utility-ablation.py

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
        prefix="pypoker-utility-ablation-"
    )

import agents  # noqa: E402
import engine  # noqa: E402
import evaluation  # noqa: E402
import features  # noqa: E402
import training  # noqa: E402

#: The two utilities of `utilities.md` §2, in the catalogue's declared order.
UTILITIES = ("net-chips", "stack-shortfall")

#: The one thing that differs between the arms, and everything they share (D-20, D-3).
SHARED = {
    "backend": "numpy",
    "encoding": "flat-numeric",
    "learning_rule": "masked-q-learning",
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
CENSUS_HANDS = 1000
PARAM_BUDGET = 10000
TABLE = "live"

#: The three action descriptors of `e2e-surface.md` §2, by index.
DESCRIPTORS = {index: str(features.decode_action(index)) for index in (0, 1, 2)}


def configuration():
    """The two-variant configuration: one utility each, everything else shared."""
    variants = []
    for utility in UTILITIES:
        variants.append(
            {
                "name": "%s-arm" % (utility,),
                "backend": SHARED["backend"],
                "encoding": SHARED["encoding"],
                "architecture": dict(ARCHITECTURE),
                "learning_rule": SHARED["learning_rule"],
                "utility": utility,
                "param_budget": PARAM_BUDGET,
                "samples": TRAIN_HANDS,
                "seeds": list(SEEDS),
                "device": "cpu",
                "snapshot_every": TRAIN_HANDS // 10,
                "table": TABLE,
            }
        )
    return {
        "name": "U1-utility-ablation",
        "axis": "the terminal reward at one architecture and one rule",
        "carried_from": None,
        "primary": variants[0]["name"],
        "pool": {"lineage": None, "m": 5, "frozen": True, "members": []},
        "variants": variants,
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
    """One match, seats alternating: the model's action shares and its chips per hand.

    The method is `strata/records/r2-plateau-diagnosis.md`'s — seats swap hand by hand, so
    a positional artefact cannot pass for a measurement (D-16) — and the counts are the
    model's **own** decisions, never its opponent's.  The opponent `always-call` is the
    fixed anchor D-6 pins, so the chips it is paid are the game's own currency.
    """
    counts = {name: 0 for name in DESCRIPTORS.values()}
    payoffs = []
    for index in range(int(hands)):
        seat = index % 2
        deal = int(base_seed) + index
        if seat == 0:
            episode = engine.play_hand(deal, policy, opponent)
        else:
            episode = engine.play_hand(deal, opponent, policy)
        for decision in episode["decisions"]:
            acting = decision["seat"][0]
            if acting != seat:
                continue
            indices = list(features.legal_indices(decision["legal"]))
            for position, descriptor in enumerate(decision["legal"]):
                if descriptor == decision["action"]:
                    counts[DESCRIPTORS[int(indices[position])]] += 1
                    break
        payoffs.append(float(episode["payoffs"][seat]))
    total = sum(counts.values())
    shares = {
        name: (100.0 * counts[name] / total if total else 0.0) for name in counts
    }
    result = {"decisions": total, "counts": counts, "shares": shares}
    result.update(interval(payoffs))
    return result


def duel(left, right, hands, base_seed):
    """One match between two models, seats alternating; chips per hand for each side."""
    taken = []
    for index in range(int(hands)):
        first = index % 2
        deal = int(base_seed) + index
        if first == 0:
            episode = engine.play_hand(deal, left, right)
        else:
            episode = engine.play_hand(deal, right, left)
        payoffs = episode["payoffs"]
        taken.append((float(payoffs[0]), float(payoffs[1])))
    return {"left": interval([pair[0] for pair in taken]),
            "right": interval([pair[1] for pair in taken])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-hands", type=int, default=TRAIN_HANDS)
    parser.add_argument("--census-hands", type=int, default=CENSUS_HANDS)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    parser.add_argument("--out", default=os.path.join(tempfile.gettempdir(),
                                                     "pypoker-utility-ablation.json"))
    arguments = parser.parse_args()

    seed_set = [int(seed) for seed in arguments.seeds]
    config = configuration()
    print("training %s: %d variants, seeds %r, %d hands each -- write root %s"
          % (config["name"], len(config["variants"]), seed_set, arguments.train_hands,
             os.environ["PYPOKER_CHECKPOINT_ROOT"]), flush=True)

    record = training.run(config, seed_set, arguments.train_hands, "cpu")
    finals = {}
    for variant in record["variants"]:
        name = str(variant["name"])
        finals[name] = {
            "utility": variant["utility"],
            "learning_rule": variant["learning_rule"],
            "checkpoints": {},
        }
    for name in finals:
        block = record["checkpoints"][name]
        for seed in seed_set:
            finals[name]["checkpoints"][seed] = block[str(seed)]["final"]

    report = {
        "configuration": config["name"],
        "utilities": list(UTILITIES),
        "seeds": seed_set,
        "train_hands": int(arguments.train_hands),
        "census_hands": int(arguments.census_hands),
        "device": "cpu",
        "run_utilities": record.get("utilities"),
        "variants": {},
        "census": {},
        "duel": {},
    }
    for variant in record["variants"]:
        report["variants"][str(variant["name"])] = {
            "utility": variant["utility"],
            "learning_rule": variant["learning_rule"],
            "final": finals[str(variant["name"])]["checkpoints"],
        }
    print("trained: %r" % (sorted(report["variants"]),), flush=True)

    # The census: each trained model against the fixed caller, seats alternating.
    policies = {}
    for name, block in finals.items():
        policies[name] = {}
        for seed in seed_set:
            path = block["checkpoints"][seed]
            policy = evaluation.policy_from(path)
            policies[name][seed] = policy
            print("census %s seed %d from %s" % (name, seed, path), flush=True)
            report["census"]["%s/%d" % (name, seed)] = census(
                policy,
                agents.build_baseline("always-call", int(seed)),
                arguments.census_hands,
                900000 + 1000 * seed,
            )
            report["census"]["%s/%d" % (name, seed)]["utility"] = block["utility"]
            _write(report, arguments.out)

    # The duel: the two trained models of one seed, seats alternating.
    left, right = UTILITIES[0], UTILITIES[1]
    for seed in seed_set:
        print("duel %s against %s at seed %d" % (left, right, seed), flush=True)
        report["duel"][str(seed)] = duel(
            policies["%s-arm" % (left,)][seed],
            policies["%s-arm" % (right,)][seed],
            arguments.census_hands,
            800000 + 1000 * seed,
        )
        _write(report, arguments.out)

    _write(report, arguments.out)
    print(json.dumps(_summary(report), indent=2, sort_keys=True))
    return report


def _write(report, path):
    """Write the whole record to ``path``, so a long measurement survives a stop."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _summary(report):
    """The mean share and chips per hand of each variant, over its seeds together."""
    summary = {}
    for variant in report["utilities"]:
        name = "%s-arm" % (variant,)
        entries = [
            value
            for key, value in report["census"].items()
            if key.startswith(name + "/")
        ]
        if not entries:
            continue
        decisions = sum(entry["decisions"] for entry in entries)
        shares = {}
        for descriptor in DESCRIPTORS.values():
            counted = sum(entry["counts"][descriptor] for entry in entries)
            shares[descriptor] = 100.0 * counted / decisions if decisions else 0.0
        means = [entry["mean"] for entry in entries if entry["mean"] is not None]
        summary[variant] = {
            "decisions": decisions,
            "shares": shares,
            "chips_per_hand_vs_always_call": statistics.fmean(means) if means else None,
            "per_seed": [entry["mean"] for entry in entries],
        }
    return {"summary": summary,
            "duel": report["duel"],
            "run_utilities": report["run_utilities"]}


if __name__ == "__main__":
    main()
    sys.exit(0)
