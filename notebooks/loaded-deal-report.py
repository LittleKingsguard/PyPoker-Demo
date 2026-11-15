"""The loaded-deal scenario report: D-70's instrument, one generation of its tables.

``docs/L1/scenarios.md`` §6 names this script and ``docs/L1/scenarios.json`` is its whole
input — the sixteen scenarios, the five scripted opponent slots, the two seatings, the six
admitted model cells at seeds 0-2 and the era rule that admits only post-D-61 containers
(D-70, D-69).  Nothing about the table is written here: a scenario, a board, a seating or a
model is an edit to that file.

    PYTHONPATH=src .venv/bin/python notebooks/loaded-deal-report.py docs/L1/scenarios.json

It writes ``<write root>/report.json`` (the file's own ``run.write_root``, ``/tmp/loaded-deal/``)
and never anything under the repository's ``checkpoints/``, ``tables/`` or
``checkpoints/evidence/`` (``docs/L1/battery.md`` §2's write-root rule applied to a script
that is not a battery).

**What it reads, and the one private seam.**  Every model is loaded by its container's path
alone — ``evaluation.policy_from(path, "off")`` — so the seed, the encoding, the shape, the
rule and the utility are the file's own and never inferred from the path, and every decision
is the masked maximum and the tie-break alone (``sizing.md`` §4, ASM-20, D-69).  The scored
values the tables print are the **same forward pass** that policy took: its frozen state, its
layout and its encoder, read from the policy object it built.  Nothing recomputes a score —
the descriptor the record carries is the engine's own record of what the policy chose, and
the vector beside it is checked to reproduce that descriptor under the greedy rule before a
row is written (``scenarios.json``'s ``checks``), so a table cannot silently print a vector
its action does not follow from.

**Nothing here is an interface** (D-12): it plays hands through ``engine.play_hand`` with the
deal the file's data spells, prints a record and returns nothing.
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
if os.path.join(REPO_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

import agents  # noqa: E402
import agents.rule  # noqa: E402
import engine  # noqa: E402
import evaluation  # noqa: E402
import features  # noqa: E402

#: The two seatings the design declares, by the id the file gives them.
PRIMARY = "big-blind"
SUPPLEMENTARY = "opening"

#: The two decisions every row reports, in street order (``scenarios.md`` §6).
REPORTED_STREETS = ("preflop", "flop")


class Refused(Exception):
    """One row the file's own checks refuse, named (``scenarios.json`` ``checks``)."""


# ---------------------------------------------------------------------------
# The declared data, and the checks that keep it honest (§2, ``checks``)
# ---------------------------------------------------------------------------
def load(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise Refused("scenarios: %r is not the declared data mapping" % (path,))
    return data


def cards_of(scenario, boards):
    """Every card one scenario names: the model's two and the board's five."""
    return tuple(scenario["hole"]) + tuple(boards[scenario["board"]]["cards"])


def check_the_data(data):
    """The declared file's own invariants, asserted before a hand is dealt (§2)."""
    boards = data["boards"]
    shape = data["shape"]
    seats = engine.game_config(shape)["seats"]
    opponents = data["opponents"]["slots"]
    opponent_cards = [card for slot in opponents for card in slot["hole"]]
    if len(opponents) != seats - 1:
        raise Refused(
            "the file declares %d opponent slots and the shape seats %d, so one seat is "
            "unfilled" % (len(opponents), seats)
        )
    if len(set(opponent_cards)) != len(opponent_cards):
        raise Refused("the opponent block names a card twice: %r" % (opponent_cards,))
    for scenario in data["scenarios"]:
        named = cards_of(scenario, boards)
        if len(set(named)) != len(named):
            raise Refused(
                "scenario %r names a card twice: %r" % (scenario["id"], named)
            )
        whole = set(named) | set(opponent_cards)
        if len(whole) != 2 + len(boards[scenario["board"]]["cards"]) + len(opponent_cards):
            raise Refused(
                "scenario %r shares a card with the opponent block: the hand's 17 cards "
                "must be distinct, and it names %r over %r"
                % (scenario["id"], named, opponent_cards)
            )
    # a helper is a strictly better flop hand than its partner on common-dry
    by_id = {scenario["id"]: scenario for scenario in data["scenarios"]}
    for scenario in data["scenarios"]:
        if scenario["board_role"] != "helper":
            continue
        partner = by_id[scenario["id"].replace("-helper", "-dry")]
        if scenario["hole"] != partner["hole"]:
            raise Refused(
                "scenario %r and its partner do not hold the same hole" % (scenario["id"],)
            )
        if not scenario["flop_hand_class"] > partner["flop_hand_class"]:
            raise Refused(
                "the helper %r does not beat its partner on hand class" % (scenario["id"],)
            )
    return boards


def seating_of(data, seating_id):
    """The seating row the file declares, and the deal's seat map for it."""
    for seating in data["seatings"]:
        if seating["id"] == seating_id:
            model_seat = seating["model_seat"]
            others = [seat for seat in range(engine.game_config(data["shape"])["seats"])
                      if seat != model_seat]
            slots = data["opponents"]["slots"]
            # ascending seat index among the seats the model does not hold
            mapping = {seat: slot for seat, slot in zip(others, slots)}
            return seating, model_seat, mapping
    raise Refused("the file declares no seating %r" % (seating_id,))


def deal_of(data, boards, scenario, model_seat, mapping):
    """One scenario's deal: the model's hole at its seat, the slots at the rest."""
    seats = engine.game_config(data["shape"])["seats"]
    holes = [None] * seats
    holes[model_seat] = tuple(scenario["hole"])
    for seat, slot in mapping.items():
        holes[seat] = tuple(slot["hole"])
    if any(hole is None for hole in holes):
        raise Refused("the deal leaves a seat without a pair")
    return {
        "holes": tuple(holes),
        "board": tuple(boards[scenario["board"]]["cards"]),
    }


# ---------------------------------------------------------------------------
# One model, as a policy and as the scorer beside it
# ---------------------------------------------------------------------------
class Model:
    """One admitted container: its member policy and the facts its directory declares."""

    def __init__(self, cell, rule, encoding, seed, path):
        self.cell = cell
        self.declared_rule = rule
        self.declared_encoding = encoding
        self.seed = seed
        self.path = path
        self.member = evaluation.policy_from(path, "off")
        self.policy = self.member.policy
        self.game = self.member.game
        self.rule = self.member.learning_rule
        self.counterfactual = self.policy.counterfactual
        self.utility = self.member.utility
        self.encoding = self.policy._encoder._name
        # The shape's own index order, read off the declared action space: one descriptor
        # per index, 0 to 5 on the six-seat row (sizing.md §3, features/surface.md §7).
        space = features.action_space(shape=self.game)
        self.vocabulary = tuple(space[index]["name"] for index in sorted(space))
        if self.game != "six-seat-no-limit-100":
            raise Refused(
                "the container %r records the shape %r, and the file declares "
                "'six-seat-no-limit-100'" % (path, self.game)
            )
        # The directory names the cell's distinguishing member, and a container records
        # it as its learning rule or as its counterfactual member — the `cf` cells learn
        # masked Q-learning and take their targets from `reveal-counterfactual`
        # (counterfactual.md §6, D-43).  The declared member must be one the container
        # actually records, or the container contradicts its directory.
        if self.declared_rule not in (self.rule, self.counterfactual):
            raise Refused(
                "the container %r records the rule %r and the counterfactual %r, and its "
                "directory declares %r"
                % (path, self.rule, self.counterfactual, self.declared_rule)
            )
        if self.utility != "net-chips-normalised":
            raise Refused(
                "the container %r records the utility %r, and every admitted cell is on "
                "net-chips-normalised (scenarios.md §5)" % (path, self.utility)
            )
        if self.encoding != self.declared_encoding:
            raise Refused(
                "the container %r records the encoding %r and its directory declares %r"
                % (path, self.encoding, self.declared_encoding)
            )

    def scores(self, readout):
        """The scored values this model gives one decision, in the shape's index order."""
        observation = features.encode(self.policy._encoder, readout)
        scored, _cache = self.policy._backend.forward(
            self.policy._state, self.policy._layout, observation, need_cache=False
        )
        return tuple(float(value) for value in scored)

    def describe(self):
        return {
            "cell": self.cell,
            "seed": self.seed,
            "path": self.path,
            "member_id": self.member.member_id,
            "params": self.member.params,
            "rule": self.rule,
            "counterfactual": self.counterfactual,
            "utility": self.utility,
            "encoding": self.encoding,
            "game": self.game,
        }


def models_of(data):
    """Every admitted container of the declared era, six cells times its three seeds."""
    era = data["era"]
    root = era["admitted_root"]
    pattern = era["path_pattern"]
    models = []
    for cell in data["models"]["cells"]:
        for seed in data["models"]["seeds"]:
            path = pattern.replace("<admitted_root>", root)
            path = path.replace("<cell>", cell["cell"]).replace("<seed>", str(seed))
            if not os.path.isfile(path):
                raise Refused(
                    "the declared container %r is absent; the era admits only %r"
                    % (path, era["admitted_cells"])
                )
            models.append(Model(cell["cell"], cell["rule"], cell["encoding"], seed, path))
    return models


# ---------------------------------------------------------------------------
# One hand, and the two decisions the table reports
# ---------------------------------------------------------------------------
def decisions_of(data, model, seating, model_seat, mapping, scenario, boards):
    """One played hand: the model's own decisions, with their scored values."""
    deal = deal_of(data, boards, scenario, model_seat, mapping)
    seating_policies = []
    for seat in range(engine.game_config(data["shape"])["seats"]):
        if seat == model_seat:
            seating_policies.append(model.member)
        else:
            slot = mapping[seat]
            seating_policies.append(
                agents.build_baseline(slot["baseline"], data["run"]["seed"], data["shape"])
            )
    record = engine.play_hand(
        data["run"]["seed"],
        shape=data["shape"],
        seats=tuple(seating_policies),
        deal=deal,
    )
    check_the_seating(data, seating, model_seat, record)
    rows = {}
    for position, decision in enumerate(record["decisions"]):
        seat = decision["seat"][0]
        if seat != model_seat:
            continue
        facts = decision["readout"]
        street = facts["street"]
        if street not in REPORTED_STREETS:
            continue
        scored = model.scores(facts)
        mask = tuple(int(index) for index in features.legal_indices(decision["legal"]))
        # The greedy rule the `off` policy itself took, not a second reading of it: the
        # masked maximum and the tie-break, so a vector that does not follow from the
        # descriptor refuses the row instead of printing it (scenarios.json checks).
        best, _tie = agents.rule.decide_greedy(scored, mask)
        if features.decode_action(best, shape=model.game) != decision["action"]:
            raise Refused(
                "scenario %r seat %d on the %s: the reported scores do not reproduce the "
                "reported action %r under the greedy rule (scenarios.json checks)"
                % (scenario["id"], model_seat, street, decision["action"])
            )
        row = {
            "street": street,
            "seat": seat,
            "on_button": bool(facts["seat"][1]),
            "hole": list(facts["hole"]),
            "board": list(facts["board"]),
            "hand_class": facts["hand_class"],
            "legal": list(decision["legal"]),
            "action": decision["action"],
            "index": model.vocabulary.index(decision["action"]),
            "amount": decision["amount"],
            "scores": [
                {
                    "descriptor": descriptor,
                    "legal": descriptor in decision["legal"],
                    "value": scored[position]
                    if descriptor in decision["legal"]
                    else None,
                }
                for position, descriptor in enumerate(model.vocabulary)
            ],
            "position": position,
        }
        if street in rows:
            raise Refused(
                "scenario %r has two %s decisions for the model" % (scenario["id"], street)
            )
        rows[street] = row
        check_the_row(data, scenario, deal, model_seat, row)
    if "preflop" not in rows:
        raise Refused(
            "scenario %r holds no preflop decision for the model, and every hand has one"
            % (scenario["id"],)
        )
    return record, rows


def check_the_seating(data, seating, model_seat, record):
    """The model's preflop decision is the one the declared seating promises (§4, ``checks``)."""
    preflop = [
        decision for decision in record["decisions"]
        if decision["seat"][0] == model_seat and decision["readout"]["street"] == "preflop"
    ]
    if not preflop:
        raise Refused("a hand holds no preflop decision for the model")
    holds_fold = "fold" in preflop[0]["legal"]
    if seating["fold_legal_preflop"] and not holds_fold:
        raise Refused(
            "the seating %r offers the model a fold before the flop and its legal set %r "
            "holds none" % (seating["id"], preflop[0]["legal"])
        )
    if not seating["fold_legal_preflop"] and holds_fold:
        raise Refused(
            "the seating %r makes a fold illegal before the flop and its legal set %r "
            "holds one" % (seating["id"], preflop[0]["legal"])
        )
    to_call = preflop[0]["readout"]["to_call"]
    if not seating["fold_legal_preflop"] and to_call != 0:
        raise Refused(
            "the seating %r promises the model a free preflop decision and its to_call is "
            "%r" % (seating["id"], to_call)
        )


def check_the_row(data, scenario, deal, model_seat, row):
    """One reported decision against the file's own checks (§2, ``checks``)."""
    if tuple(row["hole"]) != tuple(deal["holes"][model_seat]):
        raise Refused(
            "scenario %r: the reported hole is not the deal's pair for seat %d"
            % (scenario["id"], model_seat)
        )
    dealt = min(len(row["board"]), len(deal["board"]))
    if tuple(row["board"][:dealt]) != tuple(deal["board"][:dealt]):
        raise Refused(
            "scenario %r: the reported board is not the deal's prefix" % (scenario["id"],)
        )
    if row["street"] == "flop" and row["hand_class"] != scenario["flop_hand_class"]:
        raise Refused(
            "scenario %r: the flop hand class is %r and the file declares %r"
            % (scenario["id"], row["hand_class"], scenario["flop_hand_class"])
        )


# ---------------------------------------------------------------------------
# The three tables, and the answer (§6, §7)
# ---------------------------------------------------------------------------
def run(data, boards):
    tables = {"T1a": [], "T1b": [], "T2": []}
    rows_by_seating = {PRIMARY: {}, SUPPLEMENTARY: {}}
    for seating_id in (PRIMARY, SUPPLEMENTARY):
        seating, model_seat, mapping = seating_of(data, seating_id)
        for scenario in data["scenarios"]:
            rows_by_seating[seating_id][scenario["id"]] = {
                "scenario": scenario,
                "cells": {},
            }
    models = models_of(data)
    for model in models:
        for seating_id in (PRIMARY, SUPPLEMENTARY):
            seating, model_seat, mapping = seating_of(data, seating_id)
            for scenario in data["scenarios"]:
                record, rows = decisions_of(
                    data, model, seating, model_seat, mapping, scenario, boards
                )
                rows_by_seating[seating_id][scenario["id"]]["cells"][
                    "%s|%d" % (model.cell, model.seed)
                ] = {
                    "model": model.describe(),
                    "preflop": rows.get("preflop"),
                    "flop": rows.get("flop"),
                    "payoffs": {str(k): v for k, v in record["payoffs"].items()},
                    "deal": record["deal"],
                }
    # T1a / T1b: one row per scenario, one column per cell at seed 0
    for seating_id in (PRIMARY, SUPPLEMENTARY):
        table = "T1a" if seating_id == PRIMARY else "T1b"
        seating, _model_seat, _mapping = seating_of(data, seating_id)
        for scenario in data["scenarios"]:
            entry = rows_by_seating[seating_id][scenario["id"]]
            columns = {}
            for cell in data["models"]["cells"]:
                key = "%s|0" % (cell["cell"],)
                column = entry["cells"].get(key)
                columns[cell["cell"]] = {
                    "preflop": cell_of(column, "preflop"),
                    "flop": cell_of(column, "flop"),
                }
            tables[table].append(
                {
                    "scenario": scenario["id"],
                    "hole": scenario["hole"],
                    "board": data["boards"][scenario["board"]]["cards"],
                    "board_role": scenario["board_role"],
                    "flop_hand": scenario["flop_hand"],
                    "seating": seating["id"],
                    "model_seat": seating["model_seat"],
                    "cells": columns,
                }
            )
    # One decision pair per model x scenario x seating, at every seed: the whole table a
    # reader checks a row of T1a or T1b against (scenarios.md §6).
    decisions = []
    for model in models:
        for seating_id in (PRIMARY, SUPPLEMENTARY):
            _seating, _model_seat, _mapping = seating_of(data, seating_id)
            for scenario in data["scenarios"]:
                entry = rows_by_seating[seating_id][scenario["id"]]["cells"][
                    "%s|%d" % (model.cell, model.seed)
                ]
                decisions.append(
                    {
                        "cell": model.cell,
                        "seed": model.seed,
                        "seating": seating_id,
                        "scenario": scenario["id"],
                        "board_role": scenario["board_role"],
                        "flop_hand": scenario["flop_hand"],
                        "preflop": entry["preflop"],
                        "flop": entry["flop"],
                        "payoffs": entry["payoffs"],
                        "deal": {
                            "holes": [list(pair) for pair in entry["deal"]["holes"]],
                            "board": list(entry["deal"]["board"]),
                        },
                        "model": entry["model"],
                    }
                )
    # T2: one row per model per seating
    for model in models:
        for seating_id in (PRIMARY, SUPPLEMENTARY):
            _seating, _model_seat, _mapping = seating_of(data, seating_id)
            vectors = []
            actions = []
            for scenario in data["scenarios"]:
                entry = rows_by_seating[seating_id][scenario["id"]]["cells"][
                    "%s|%d" % (model.cell, model.seed)
                ]
                for street in REPORTED_STREETS:
                    row = entry[street]
                    if row is None:
                        continue
                    vectors.append(
                        tuple(
                            None if part["value"] is None else round(part["value"], 9)
                            for part in row["scores"]
                        )
                    )
                    actions.append(row["action"])
            tables["T2"].append(
                {
                    "cell": model.cell,
                    "seed": model.seed,
                    "seating": seating_id,
                    "decisions": len(actions),
                    "distinct_vectors": len(set(vectors)),
                    "distinct_actions": len(set(actions)),
                    "actions": actions,
                    "model": model.describe(),
                }
            )
    # the seed agreement, folded into T2's rows
    by_cell_seating = {}
    for row in tables["T2"]:
        by_cell_seating.setdefault((row["cell"], row["seating"]), []).append(row)
    for rows in by_cell_seating.values():
        same = len({tuple(row["actions"]) for row in rows}) == 1
        for row in rows:
            row["seeds_agree_action_for_action"] = same
    answer = the_answer(data, rows_by_seating)
    return {"tables": tables, "answer": answer, "decisions": decisions}


def cell_of(column, street):
    """One cell of T1a/T1b: the decision, or the fact that the hand never reached it."""
    if column is None:
        return {"decision": None, "why": "the model's container is absent"}
    row = column[street]
    if row is None:
        return {
            "decision": None,
            "why": "no %s decision - folded preflop" % (street,),
        }
    return {"decision": row}


def the_answer(data, rows_by_seating):
    """§7's two contrasts, per model and per seed, on the declared data."""
    dry = [scenario["id"] for scenario in data["scenarios"]
           if scenario["board"] == "common-dry"]
    pairs = []
    by_id = {scenario["id"]: scenario for scenario in data["scenarios"]}
    for scenario in data["scenarios"]:
        if scenario["board_role"] != "helper":
            continue
        pairs.append((scenario["id"], scenario["id"].replace("-helper", "-dry")))
    out = {}
    for seating_id in (PRIMARY, SUPPLEMENTARY):
        for model_key in sorted(
            {
                key
                for scenario_id in rows_by_seating[seating_id]
                for key in rows_by_seating[seating_id][scenario_id]["cells"]
            }
        ):
            entry = {"seating": seating_id, "model": model_key}
            preflop = {}
            flop = {}
            for scenario_id in dry:
                column = rows_by_seating[seating_id][scenario_id]["cells"][model_key]
                preflop[scenario_id] = None if column["preflop"] is None else column["preflop"]["action"]
                flop[scenario_id] = None if column["flop"] is None else column["flop"]["action"]
            entry["dry_preflop_actions"] = preflop
            entry["dry_flop_actions"] = flop
            entry["dry_holes_separate_preflop"] = len({v for v in preflop.values()}) > 1
            entry["dry_holes_separate_flop"] = len({v for v in flop.values()}) > 1
            board_moves = {}
            for helper_id, dry_id in pairs:
                helper = rows_by_seating[seating_id][helper_id]["cells"][model_key]
                dry_column = rows_by_seating[seating_id][dry_id]["cells"][model_key]
                if helper["flop"] is None or dry_column["flop"] is None:
                    board_moves[helper_id] = None
                else:
                    board_moves[helper_id] = helper["flop"]["action"] != dry_column["flop"]["action"]
            entry["board_contrast"] = board_moves
            entry["any_board_moves"] = any(value for value in board_moves.values())
            # D-70's own two questions, asked of this model alone: aces against
            # seven-deuce offsuit on the one board every hole set shares, and one hole
            # set's helper board against that same dry board (scenarios.md §7).
            def decision(scenario_id, street):
                column = rows_by_seating[seating_id][scenario_id]["cells"][model_key]
                row = column[street]
                return None if row is None else row["action"]

            contrast = {}
            for street in REPORTED_STREETS:
                aces = decision("AA-dry", street)
                seven_deuce = decision("72o-dry", street)
                contrast[street] = {
                    "AA": aces,
                    "72o": seven_deuce,
                    "differ": aces is not None and aces != seven_deuce,
                }
            entry["aa_versus_72o"] = contrast
            shared = {}
            for helper_id, dry_id in pairs:
                helper = rows_by_seating[seating_id][helper_id]["cells"][model_key]
                dry_column = rows_by_seating[seating_id][dry_id]["cells"][model_key]
                if helper["flop"] is None or dry_column["flop"] is None:
                    shared[helper_id] = None
                    continue
                shared[helper_id] = {
                    "hole": list(helper["flop"]["hole"]),
                    "helper_board": helper["flop"]["board"],
                    "helper_action": helper["flop"]["action"],
                    "dry_board": dry_column["flop"]["board"],
                    "dry_action": dry_column["flop"]["action"],
                    "differ": helper["flop"]["action"] != dry_column["flop"]["action"],
                }
            entry["one_hole_two_boards"] = shared
            out["%s|%s" % (seating_id, model_key)] = entry
    return out


# ---------------------------------------------------------------------------
# Printing, and the one artefact
# ---------------------------------------------------------------------------
def short(row):
    """One decision as a table cell: the action and its winning score."""
    if row is None:
        return "-"
    return row["action"]


def print_table(title, rows, cells):
    print()
    print(title)
    header = "%-14s %-8s %-5s " % ("scenario", "hole", "board")
    header += "".join("%-26s" % cell for cell in cells)
    print(header)
    for row in rows:
        line = "%-14s %-8s %-5s " % (
            row["scenario"],
            " ".join(row["hole"]),
            "help" if row["board_role"] == "helper" else "dry",
        )
        for cell in cells:
            column = row["cells"][cell]
            line += "%-26s" % (
                "%s/%s" % (
                    short(column["preflop"]["decision"]),
                    short(column["flop"]["decision"]),
                ),
            )
        print(line)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", nargs="?", default=os.path.join(REPO_ROOT, "docs/L1/scenarios.json"))
    arguments = parser.parse_args()
    data = load(arguments.data)
    boards = check_the_data(data)
    measured = run(data, boards)
    cells = [cell["cell"] for cell in data["models"]["cells"]]
    print_table(
        "T1a the scenario table, primary seating (big-blind), seed 0: preflop/flop action",
        measured["tables"]["T1a"],
        cells,
    )
    print_table(
        "T1b the scenario table, supplementary seating (opening), seed 0: preflop/flop action",
        measured["tables"]["T1b"],
        cells,
    )
    print()
    print("T2 distinct score vectors over the seating's decisions, per model per seating")
    for row in measured["tables"]["T2"]:
        print(
            "  %-20s seed %d %-10s decisions %3d  distinct vectors %3d  distinct actions "
            "%d  seeds agree %s"
            % (
                row["cell"],
                row["seed"],
                row["seating"],
                row["decisions"],
                row["distinct_vectors"],
                row["distinct_actions"],
                row["seeds_agree_action_for_action"],
            )
        )
    print()
    print("the answer rule (scenarios.md §7), per model per seating")
    for key in sorted(measured["answer"]):
        entry = measured["answer"][key]
        print(
            "  %-40s dry holes separate: preflop %-5s flop %-5s   board moves: %s"
            % (
                key,
                entry["dry_holes_separate_preflop"],
                entry["dry_holes_separate_flop"],
                sorted(
                    helper
                    for helper, moved in entry["board_contrast"].items()
                    if moved
                )
                or "none",
            )
        )
    target = os.path.join(data["run"]["write_root"], data["run"]["artefact"].split("/")[-1])
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "unit": data["unit"],
                "decision": data["decision"],
                "rev": data["rev"],
                "era": data["era"],
                "shape": data["shape"],
                "run": data["run"],
                "tables": measured["tables"],
                "decisions": measured["decisions"],
                "answer": measured["answer"],
            },
            handle,
            indent=1,
            sort_keys=True,
        )
    print()
    print("wrote", target)


if __name__ == "__main__":
    main()
