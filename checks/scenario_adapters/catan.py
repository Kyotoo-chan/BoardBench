"""Contract-v2 CATAN adapter using only canonical data and the public Game API."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from typing import Any

STATE_SCHEMA = "boardbench/catan/state/1"
ACTION_SCHEMA = "boardbench/catan/action/1"
OBSERVATION_SCHEMA = "boardbench/catan/observation/1"
RESOURCES = ("wood", "brick", "wool", "grain", "ore")
ACTION_ARGS = {
    "roll_dice": set(),
    "discard_resource": {"resource"},
    "move_robber": {"hex"},
    "steal_resource": {"victim"},
    "begin_domestic_trade": set(),
    "add_trade_item": {"partner", "direction", "resource"},
    "cancel_domestic_trade": set(),
    "commit_domestic_trade": set(),
    "maritime_trade": {"give", "receive"},
    "end_trade": set(),
    "build_road": {"edge"},
    "build_settlement": {"vertex"},
    "build_city": {"vertex"},
    "buy_development": set(),
    "play_knight": {"card"},
    "play_road_building": {"card"},
    "place_free_road": {"edge"},
    "play_year_of_plenty": {"card", "resources"},
    "play_monopoly": {"card", "resource"},
    "end_turn": set(),
}


class AdapterUntestable(Exception):
    """The implementation rejects or omits canonical fixture data."""


def is_untestable(error: Exception) -> bool:
    return isinstance(error, AdapterUntestable)


def _envelope(payload: Any, schema: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"schema", "data"} or payload.get("schema") != schema or not isinstance(payload.get("data"), dict):
        raise AdapterUntestable(f"invalid canonical envelope for {schema}")
    return payload["data"]


def _state(game: Any, state: Any) -> dict[str, Any]:
    return _envelope(game.state_to_data(state), STATE_SCHEMA)


def _action_data(game: Any, actions: list[Any]) -> list[tuple[Any, dict[str, Any]]]:
    result = []
    seen = set()
    for action in actions:
        payload = game.action_to_data(action)
        data = _envelope(payload, ACTION_SCHEMA)
        if set(data) != {"type", "actor", "args"} or not isinstance(data["actor"], int) or not isinstance(data["args"], dict):
            raise AdapterUntestable("invalid canonical action data")
        if data["type"] not in ACTION_ARGS or set(data["args"]) != ACTION_ARGS[data["type"]]:
            raise AdapterUntestable(f"invalid canonical arguments for {data['type']!r}")
        try:
            rebuilt = game.action_from_data(deepcopy(payload))
            if game.action_to_data(rebuilt) != payload:
                raise AdapterUntestable("canonical action does not round-trip")
        except AdapterUntestable:
            raise
        except Exception as error:
            raise AdapterUntestable(f"canonical action reconstruction failed: {error}") from error
        key = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if key in seen:
            raise AdapterUntestable("duplicate canonical legal action data")
        seen.add(key)
        result.append((action, data))
    return result


def _actions(game: Any, state: Any) -> list[tuple[Any, dict[str, Any]]]:
    return _action_data(game, list(game.legal_actions(state)))


def _matches(data: dict[str, Any], selector: dict[str, Any]) -> bool:
    if "actor" in selector and data["actor"] != int(selector["actor"]):
        return False
    if "type" in selector and data["type"] != selector["type"]:
        return False
    if "type_any" in selector and data["type"] not in selector["type_any"]:
        return False
    return all(data["args"].get(key) == value for key, value in selector.get("args", {}).items())


def resolve_action(module: Any, game: Any, state: Any, actions: list[Any], selector: dict[str, Any]) -> Any:
    matches = [action for action, data in _action_data(game, actions) if _matches(data, selector)]
    if not matches:
        raise AssertionError(f"canonical action is not legal: {selector!r}")
    if len(matches) > 1 and not selector.get("choose_first"):
        raise AssertionError(f"canonical action is ambiguous: {selector!r}")
    return matches[0]


def _zero_resources() -> dict[str, int]:
    return {resource: 0 for resource in RESOURCES}


def _vertices(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["id"]: entry for entry in data["board"]["vertices"]}


def _edges(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["id"]: entry for entry in data["board"]["edges"]}


def _hexes(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["id"]: entry for entry in data["board"]["hexes"]}


def _remove_card(reserve: list[str], card: str) -> None:
    try:
        reserve.remove(card)
    except ValueError as error:
        raise AdapterUntestable(f"fixture exceeds development inventory for {card!r}") from error


def _blank(data: dict[str, Any]) -> Counter[str]:
    resource_inventory, development_inventory = _inventory(data)
    data["current_player"] = 0
    data["active_player"] = 0
    data["phase"] = "build"
    data["turn"] = {"number": 1, "development_played": False, "last_roll": None}
    data["terminal"] = False
    data["winner"] = None
    for player in data["players"]:
        player["resources"] = _zero_resources()
        player["development_hand"] = []
        player["played_knights"] = 0
        player["pieces"] = {"roads": 15, "settlements": 5, "cities": 4}
    for vertex in data["board"]["vertices"]:
        vertex["building"] = None
    for edge in data["board"]["edges"]:
        edge["road_owner"] = None
    for hexagon in data["board"]["hexes"]:
        hexagon["robber"] = hexagon["id"] == "h09"
    data["bank"] = {"resources": {resource: resource_inventory[resource] for resource in RESOURCES}, "development_deck": [], "played_development": []}
    data["special_cards"] = {"longest_road_owner": None, "longest_road_length": 0, "largest_army_owner": None}
    data["pending"] = None
    data["chance"] = {"rng_state": 1, "scripted_rolls": [], "scripted_steals": []}
    data["zones"] = {"reserve": {"resources": _zero_resources(), "development_cards": sorted(development_inventory.elements())}}
    return resource_inventory


def _put_building(data: dict[str, Any], vertex_id: str, owner: int, kind: str) -> None:
    vertex = _vertices(data).get(vertex_id)
    if vertex is None:
        raise AdapterUntestable(f"unknown vertex {vertex_id!r}")
    if vertex["building"] is not None:
        raise AdapterUntestable(f"duplicate fixture building at {vertex_id}")
    if kind not in {"settlement", "city"}:
        raise AdapterUntestable(f"unknown building type {kind!r}")
    vertex["building"] = {"owner": owner, "type": kind}
    key = "settlements" if kind == "settlement" else "cities"
    data["players"][owner]["pieces"][key] -= 1


def _put_road(data: dict[str, Any], edge_id: str, owner: int) -> None:
    edge = _edges(data).get(edge_id)
    if edge is None:
        raise AdapterUntestable(f"unknown edge {edge_id!r}")
    if edge["road_owner"] is not None:
        raise AdapterUntestable(f"duplicate fixture road at {edge_id}")
    edge["road_owner"] = owner
    data["players"][owner]["pieces"]["roads"] -= 1


def _setup_resources(data: dict[str, Any], fixture: dict[str, Any], inventory: Counter[str]) -> None:
    used = _zero_resources()
    for raw_player, counts in fixture.get("resources", {}).items():
        player = int(raw_player)
        for resource, raw_count in counts.items():
            count = int(raw_count)
            data["players"][player]["resources"][resource] = count
            used[resource] += count
    requested_bank = fixture.get("bank_resources")
    for resource in RESOURCES:
        total = inventory[resource]
        bank_count = total - used[resource] if requested_bank is None else int(requested_bank.get(resource, 0))
        reserve_count = total - used[resource] - bank_count
        if min(bank_count, reserve_count) < 0:
            raise AdapterUntestable(f"fixture exceeds resource inventory for {resource}")
        data["bank"]["resources"][resource] = bank_count
        data["zones"]["reserve"]["resources"][resource] = reserve_count


def _setup_development(data: dict[str, Any], fixture: dict[str, Any]) -> None:
    reserve = data["zones"]["reserve"]["development_cards"]
    for raw_player, cards in fixture.get("development_hands", {}).items():
        player = int(raw_player)
        for raw in cards:
            card = raw if isinstance(raw, str) else raw["id"]
            bought_turn = 0 if isinstance(raw, str) else int(raw.get("bought_turn", 0))
            _remove_card(reserve, card)
            data["players"][player]["development_hand"].append({"id": card, "bought_turn": bought_turn})
    for card in fixture.get("development_deck", []):
        _remove_card(reserve, card)
        data["bank"]["development_deck"].append(card)
    for raw_player, raw_count in fixture.get("played_knights", {}).items():
        player, count = int(raw_player), int(raw_count)
        data["players"][player]["played_knights"] = count
        for _ in range(count):
            _remove_card(reserve, "knight")
            data["bank"]["played_development"].append({"owner": player, "id": "knight"})
    for item in fixture.get("played_development", []):
        card, owner = item["id"], int(item["owner"])
        _remove_card(reserve, card)
        data["bank"]["played_development"].append({"owner": owner, "id": card})


def setup(module: Any, game: Any, fixture: dict[str, Any]) -> Any:
    try:
        payload = deepcopy(game.state_to_data(game.initial_state()))
        data = _envelope(payload, STATE_SCHEMA)
        resource_inventory = _blank(data)

        _setup_resources(data, fixture, resource_inventory)
        _setup_development(data, fixture)

        for vertex_id, building in fixture.get("buildings", {}).items():
            _put_building(data, vertex_id, int(building["owner"]), building["type"])
        for edge_id, owner in fixture.get("roads", {}).items():
            _put_road(data, edge_id, int(owner))
        for request in fixture.get("harbor_buildings", []):
            matching = [harbor for harbor in data["board"]["harbors"] if harbor["ratio"] == int(request["ratio"]) and harbor.get("resource") == request.get("resource")]
            if not matching:
                raise AdapterUntestable(f"no canonical harbor matches {request!r}")
            vertex_id = matching[0]["vertices"][int(request.get("site", 0))]
            _put_building(data, vertex_id, int(request["owner"]), request.get("type", "settlement"))

        if "robber_hex" in fixture:
            for hexagon in data["board"]["hexes"]:
                hexagon["robber"] = hexagon["id"] == fixture["robber_hex"]
        if "phase" in fixture:
            data["phase"] = fixture["phase"]
        if "active_player" in fixture:
            data["active_player"] = int(fixture["active_player"])
            data["current_player"] = int(fixture["active_player"])
        if "current_player" in fixture:
            data["current_player"] = int(fixture["current_player"])
        if "turn_number" in fixture:
            data["turn"]["number"] = int(fixture["turn_number"])
        if "development_played" in fixture:
            data["turn"]["development_played"] = bool(fixture["development_played"])
        if "last_roll" in fixture:
            data["turn"]["last_roll"] = fixture["last_roll"]
        if "pending" in fixture:
            data["pending"] = deepcopy(fixture["pending"])
        if "special_cards" in fixture:
            data["special_cards"].update(deepcopy(fixture["special_cards"]))
        if "scripted_rolls" in fixture:
            data["chance"]["scripted_rolls"] = deepcopy(fixture["scripted_rolls"])
        if "scripted_steals" in fixture:
            data["chance"]["scripted_steals"] = list(fixture["scripted_steals"])
        if "terminal" in fixture:
            data["terminal"] = bool(fixture["terminal"])
            if data["terminal"]:
                data["phase"] = "terminal"
        if "winner" in fixture:
            data["winner"] = int(fixture["winner"])

        for player in data["players"]:
            if min(player["pieces"].values()) < 0:
                raise AdapterUntestable("fixture exceeds player piece inventory")
        state = game.state_from_data(payload)
        if game.state_to_data(state) != payload:
            raise AdapterUntestable("canonical fixture does not round-trip")
        return state
    except AdapterUntestable:
        raise
    except (KeyError, TypeError, ValueError, AssertionError) as error:
        raise AdapterUntestable(f"state_from_data rejected canonical fixture: {error}") from error


def _assert_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def _inventory(data: dict[str, Any]) -> tuple[Counter[str], Counter[str]]:
    resources = Counter(data["bank"]["resources"]) + Counter(data["zones"]["reserve"]["resources"])
    for player in data["players"]:
        resources.update(player["resources"])
    cards = Counter(data["bank"]["development_deck"])
    cards.update(data["zones"]["reserve"]["development_cards"])
    cards.update(card["id"] for player in data["players"] for card in player["development_hand"])
    cards.update(card["id"] for card in data["bank"]["played_development"])
    return resources, cards


def check(module: Any, game: Any, state: Any, expected: dict[str, Any]) -> None:
    data = _state(game, state)
    vertices, edges, hexes = _vertices(data), _edges(data), _hexes(data)

    if "inventory" in expected:
        spec = expected["inventory"]
        resources, cards = _inventory(data)
        if "resources" in spec:
            _assert_equal("resource inventory", resources, Counter(spec["resources"]))
        if "development" in spec:
            _assert_equal("development inventory", cards, Counter(spec["development"]))
        if "hex_count" in spec:
            _assert_equal("hex count", len(hexes), int(spec["hex_count"]))
        if "vertex_count" in spec:
            _assert_equal("vertex count", len(vertices), int(spec["vertex_count"]))
        if "edge_count" in spec:
            _assert_equal("edge count", len(edges), int(spec["edge_count"]))
        if "harbor_count" in spec:
            _assert_equal("harbor count", len(data["board"]["harbors"]), int(spec["harbor_count"]))

    if "hex_layout" in expected:
        actual = [(entry["id"], entry["terrain"], entry["number"]) for entry in data["board"]["hexes"]]
        wanted = [(entry["id"], entry["terrain"], entry.get("number")) for entry in expected["hex_layout"]]
        _assert_equal("hex_layout", actual, wanted)
    if "harbor_sequence" in expected:
        actual = [(entry["ratio"], entry.get("resource")) for entry in data["board"]["harbors"]]
        wanted = [(entry["ratio"], entry.get("resource")) for entry in expected["harbor_sequence"]]
        _assert_equal("harbor_sequence", actual, wanted)
    if "robber_hex" in expected:
        occupied = [entry["id"] for entry in data["board"]["hexes"] if entry["robber"]]
        _assert_equal("robber_hex", occupied, [expected["robber_hex"]])

    for raw_player, wanted in expected.get("resources", {}).items():
        player = int(raw_player)
        _assert_equal(f"resources[{player}]", data["players"][player]["resources"], {resource: int(wanted.get(resource, 0)) for resource in RESOURCES})
    if "bank_resources" in expected:
        _assert_equal("bank_resources", data["bank"]["resources"], {resource: int(expected["bank_resources"].get(resource, 0)) for resource in RESOURCES})
    for raw_player, wanted in expected.get("resource_total", {}).items():
        player = int(raw_player)
        _assert_equal(f"resource_total[{player}]", sum(data["players"][player]["resources"].values()), int(wanted))

    for vertex_id, wanted in expected.get("buildings", {}).items():
        _assert_equal(f"building[{vertex_id}]", vertices[vertex_id]["building"], wanted)
    for edge_id, wanted in expected.get("roads", {}).items():
        _assert_equal(f"road[{edge_id}]", edges[edge_id]["road_owner"], wanted)
    for raw_player, wanted in expected.get("pieces", {}).items():
        _assert_equal(f"pieces[{raw_player}]", data["players"][int(raw_player)]["pieces"], wanted)

    for raw_player, wanted in expected.get("development_hand", {}).items():
        actual = [card["id"] for card in data["players"][int(raw_player)]["development_hand"]]
        _assert_equal(f"development_hand[{raw_player}]", actual, wanted)
    if "development_deck_size" in expected:
        _assert_equal("development_deck_size", len(data["bank"]["development_deck"]), int(expected["development_deck_size"]))
    if "played_development" in expected:
        _assert_equal("played_development", data["bank"]["played_development"], expected["played_development"])
    for raw_player, wanted in expected.get("played_knights", {}).items():
        _assert_equal(f"played_knights[{raw_player}]", data["players"][int(raw_player)]["played_knights"], int(wanted))

    if "special_cards" in expected:
        for key, wanted in expected["special_cards"].items():
            _assert_equal(f"special_cards.{key}", data["special_cards"][key], wanted)
    if "winner" in expected:
        _assert_equal("winner", data["winner"], expected["winner"])
    if "phase" in expected:
        _assert_equal("phase", data["phase"], expected["phase"])
    if "development_played" in expected:
        _assert_equal("turn.development_played", data["turn"]["development_played"], bool(expected["development_played"]))
    if "last_roll" in expected:
        _assert_equal("turn.last_roll", data["turn"]["last_roll"], expected["last_roll"])
    if "pending_type" in expected:
        _assert_equal("pending_type", None if data["pending"] is None else data["pending"].get("type"), expected["pending_type"])
    if "pending" in expected:
        _assert_equal("pending", data["pending"], expected["pending"])

    actions = [action for _, action in _actions(game, state)]
    if "legal_action_type_any" in expected and not any(action["type"] in expected["legal_action_type_any"] for action in actions):
        raise AssertionError(f"no canonical legal action type in {expected['legal_action_type_any']!r}")
    forbidden = set(expected.get("legal_action_type_not", []))
    if any(action["type"] in forbidden for action in actions):
        raise AssertionError(f"forbidden canonical legal action type in {sorted(forbidden)!r}")
    for item in expected.get("action_legal", []):
        found = any(_matches(action, item["selector"]) for action in actions)
        _assert_equal(f"action_legal[{item['selector']!r}]", found, bool(item["expected"]))

    if "observation" in expected or "public_scores" in expected:
        observer = int(expected.get("observation", {}).get("player", 0))
        observation = _envelope(game.observation_to_data(state, observer), OBSERVATION_SCHEMA)
        if "public_scores" in expected:
            _assert_equal("public_scores", observation["public_scores"], expected["public_scores"])
        spec = expected.get("observation", {})
        if "own_resources" in spec:
            _assert_equal("observation.own_resources", observation["own_resources"], spec["own_resources"])
        if "opponent_counts" in spec:
            actual = {entry["id"]: (entry["resource_count"], entry["development_count"]) for entry in observation["opponents"]}
            wanted = {int(player): tuple(counts) for player, counts in spec["opponent_counts"].items()}
            _assert_equal("observation.opponent_counts", actual, wanted)
        if spec.get("no_opponent_identities"):
            for opponent in observation["opponents"]:
                if any(key in opponent for key in ("resources", "development", "development_hand", "hidden_victory_points")):
                    raise AssertionError("opponent private identities leaked in canonical observation")
        if "pending" in spec:
            _assert_equal("observation.pending", observation["pending"], spec["pending"])
