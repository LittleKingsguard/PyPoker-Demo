"""The interactive table: discovery, two- and six-seat play, and the HTTP API.

The table is a viewer over the six packaged modules, so it is exercised through their
public entry points only.  The checkpoint battery discovers whatever is in this working
tree; a probe checkpoint that declares an artefact the tree does not carry must be listed
as unavailable rather than offered and then crashed on.
"""

import http.client
import json
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "ui"
if str(UI) not in sys.path:
    sys.path.insert(0, str(UI))

import serve  # noqa: E402
import table  # noqa: E402


@pytest.fixture(scope="module")
def registry():
    return table.Registry()


def play_out(match, limit=300):
    """Answer every human decision with check/call, never raising."""
    steps = 0
    while not match.hand.over:
        state = match.state()
        legal = state["hand"]["legal"]
        assert legal, "the human's turn must offer at least one action"
        action = next(
            (row["action"] for row in legal if row["kind"] == "check"),
            legal[0]["action"],
        )
        match.act(action)
        steps += 1
        assert steps < limit, "the hand did not terminate"
    return match.state()


def test_every_declared_shape_is_exposed(registry):
    league = registry.opponents()
    assert set(league["shapes"]) == set(table.SHAPES)
    for shape, row in table.SHAPES.items():
        assert league["shapes"][shape]["seats"] == row["seats"]
        assert len(league["shapes"][shape]["positions"]) == row["seats"]
        assert league["shapes"][shape]["label"] == table.shape_label(shape)


def test_shipped_models_keep_their_shape_and_are_available(registry):
    league = registry.opponents()
    shipped = [row for row in league["models"] if row["source"] == "shipped"]
    assert shipped, "the shipped checkpoint set must be visible"
    for row in shipped:
        assert row["shape"] == "fixed-limit-20"
        assert row["available"] is True
        assert row["source_label"] == "Shipped"


def test_a_checkpoint_missing_its_artefact_is_marked_unavailable(registry):
    league = registry.opponents()
    broken = [
        row
        for row in league["models"]
        if row["source"] == "probe"
        and row["available"] is False
        and "artefact" in (row["unavailable_reason"] or "")
    ]
    if not broken:
        pytest.skip("this tree carries every declared probe artefact")
    for row in broken:
        reason = row["unavailable_reason"]
        assert reason and "artefact" in reason
        assert row["backend"] == "torch"


def test_two_seat_fixed_limit_hand_settles_to_zero(registry):
    opponent = registry.get("baseline:always-call")
    match = table.Match(registry, opponent, human_seat=0, seed=101)
    assert match.shape == "fixed-limit-20"
    state = play_out(match)
    result = state["hand"]["result"]

    assert state["hand"]["seats_count"] == 2
    assert [seat["position"] for seat in state["hand"]["seats"]] == [
        "Button · Small blind",
        "Big blind",
    ]
    assert sum(result["deltas"].values()) == 0
    assert result["final_stacks"][0] + result["final_stacks"][1] == 40
    assert state["match"]["score"] == {
        "human": result["human_delta"],
        "opponents": -result["human_delta"],
    }


def test_six_seat_no_limit_hand_settles_to_zero(registry):
    opponent = registry.get("baseline:always-call")
    members = {seat: opponent for seat in range(6) if seat != 4}
    match = table.Match(
        registry,
        opponent,
        human_seat=4,
        seed=7,
        shape="six-seat-no-limit-100",
        members=members,
    )
    state = play_out(match)
    result = state["hand"]["result"]

    assert state["hand"]["seats_count"] == 6
    assert state["hand"]["human"]["position"] == "Hijack"
    assert [seat["position"] for seat in state["hand"]["seats"]] == [
        "Button",
        "Small blind",
        "Big blind",
        "Under the gun",
        "Hijack",
        "Cutoff",
    ]
    assert sum(result["deltas"].values()) == 0
    assert sum(result["final_stacks"].values()) == 600
    assert len(result["deltas"]) == 6
    assert len(result["holes"]) == 6


def test_a_mixed_lineup_fills_every_other_seat(registry):
    anchor = registry.get("baseline:random")
    lineup = registry.mixed_lineup("six-seat-no-limit-100", 123, 5, anchor=anchor)
    assert len(lineup) == 5
    assert lineup[0] is anchor
    assert len({member.id for member in lineup}) == 5
    assert all(
        member.kind == "baseline" or member.meta.get("available", True)
        for member in lineup
    )


def test_a_model_refuses_a_table_of_another_shape(registry):
    model = next(
        row
        for row in registry.opponents()["models"]
        if row["source"] == "shipped" and row["available"]
    )
    opponent = registry.get(model["id"])
    with pytest.raises(table.UIError):
        registry.policy_for(opponent, 1, "six-seat-no-limit-100")


def test_unknown_shape_and_seat_are_refused(registry):
    opponent = registry.get("baseline:always-call")
    with pytest.raises(table.UIError):
        table.Match(registry, opponent, human_seat=2, shape="fixed-limit-20")
    with pytest.raises(table.UIError):
        table.Match(registry, opponent, shape="nonsense")


@pytest.fixture()
def client(registry):
    server = serve.make_server(registry, "127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = {
        "server": server,
        "port": server.server_address[1],
        "cookie": None,
    }

    class Browser:
        def call(self, method, path, body=None):
            conn = http.client.HTTPConnection(
                "127.0.0.1", connection["port"], timeout=120
            )
            headers = {"Accept": "application/json"}
            if connection["cookie"]:
                headers["Cookie"] = connection["cookie"]
            payload = None
            if body is not None:
                payload = json.dumps(body)
                headers["Content-Type"] = "application/json"
            conn.request(method, path, payload, headers)
            response = conn.getresponse()
            raw = response.read()
            cookie = response.getheader("Set-Cookie")
            status = response.status
            conn.close()
            if cookie:
                connection["cookie"] = cookie.split(";", 1)[0]
            parsed = json.loads(raw) if raw[:1] in (b"{", b"[") else raw
            return status, parsed

    yield Browser()
    server.shutdown()
    server.server_close()


def test_http_api_plays_a_hand_to_completion(client):
    status, league = client.call("GET", "/api/opponents")
    assert status == 200
    assert league["default_shape"] in league["shapes"]

    status, state = client.call(
        "POST",
        "/api/start",
        {
            "opponent_id": "baseline:always-call",
            "seat": 0,
            "seed": 11,
            "shape": "fixed-limit-20",
            "lineup_mode": "same",
        },
    )
    assert status == 200
    assert state["match"]["seats"] == 2
    assert state["hand"]["phase"] == "your_turn"

    for _ in range(100):
        if state["hand"]["over"]:
            break
        legal = state["hand"]["legal"]
        action = next(
            (row["action"] for row in legal if row["kind"] == "check"),
            legal[0]["action"],
        )
        status, state = client.call("POST", "/api/action", {"action": action})
        assert status == 200
    assert state["hand"]["over"] is True

    status, state = client.call("POST", "/api/next", {})
    assert status == 200
    assert state["hand"]["hand_number"] == 2


def test_http_api_accepts_a_six_seat_mixed_start(client):
    status, state = client.call(
        "POST",
        "/api/start",
        {
            "opponent_id": "baseline:random",
            "seat": 3,
            "seed": 5,
            "shape": "six-seat-no-limit-100",
            "lineup_mode": "mixed",
        },
    )
    assert status == 200
    assert state["match"]["seats"] == 6
    assert state["match"]["human_seat"] == 3
    assert state["match"]["lineup_mode"] == "mixed"
    assert len(state["match"]["opponents"]) == 5
    assert state["hand"]["human"]["position"] == "Under the gun"


def test_http_api_starts_a_shipped_checkpoint(client, registry):
    row = next(
        model
        for model in registry.opponents()["models"]
        if model["source"] == "shipped" and model["available"]
    )
    status, state = client.call(
        "POST",
        "/api/start",
        {
            "opponent_id": row["id"],
            "seat": 0,
            "seed": 21,
            "shape": "fixed-limit-20",
            "lineup_mode": "same",
        },
    )
    assert status == 200
    assert state["match"]["opponent"]["id"] == row["id"]
    assert state["hand"]["phase"] == "your_turn"
    assert state["hand"]["human"]["hole"]


def test_http_api_refuses_an_unavailable_checkpoint(client, registry):
    row = next(
        (model for model in registry.opponents()["models"] if not model["available"]),
        None,
    )
    if row is None:
        pytest.skip("every discovered checkpoint can be loaded in this environment")
    status, payload = client.call(
        "POST",
        "/api/start",
        {
            "opponent_id": row["id"],
            "seat": 0,
            "seed": 3,
            "shape": row["shape"],
            "lineup_mode": "same",
        },
    )
    assert status == 400
    assert "cannot be loaded" in payload["error"]


def test_http_api_reports_a_bad_seat(client):
    status, payload = client.call(
        "POST",
        "/api/start",
        {
            "opponent_id": "baseline:always-call",
            "seat": 5,
            "shape": "fixed-limit-20",
        },
    )
    assert status == 400
    assert "seat" in payload["error"].lower()


def test_http_static_pages_are_served(client):
    status, page = client.call("GET", "/")
    assert status == 200
    assert b"PyPoker" in page
    status, script = client.call("GET", "/static/app.js")
    assert status == 200
    assert b"api/opponents" in script
    status, icon = client.call("GET", "/favicon.svg")
    assert status == 200
    assert icon.startswith(b"<svg")


def test_top_performer_probe_policies_are_offered_and_playable(registry):
    """The two best-measured integration arms are saved probe heads, not checkpoints; they must appear
    with a readable label and be loadable through the adapter."""
    tops = [m for m in registry._models if m.kind == "probe-policy"]
    assert tops, "the saved probe policies are not discovered"
    names = {m.name for m in tops}
    assert any("exploration floor 0.60" in n for n in names), names
    for member in tops:
        assert member.meta["available"] is True, member.meta.get("unavailable_reason")
        assert member.shape == "six-seat-no-limit-100"
        policy = registry.policy_for(member, 0, "six-seat-no-limit-100")
        assert callable(policy)
        legal = ("fold", "check-call", "raise-quarter", "raise-half", "raise-all-in", "raise-minimum")
        readout = {
            "street": "preflop",
            "seat": (0, True),
            "hole": ("As", "Ad"),
            "board": (),
            "stacks": (100,) * 6,
            "pot": 3,
            "to_call": 2,
            "history": [],
        }
        assert policy(readout, legal) in legal


def test_discovered_groups_carry_readable_labels(registry):
    """A drawer entry says what a model is, not where it lives."""
    labels = {m.name for m in registry._models}
    assert not any(" · card-tokens" in name for name in labels), labels
    assert any("Dead trunk" in name for name in labels), labels
    assert any("Live trunk" in name for name in labels), labels
