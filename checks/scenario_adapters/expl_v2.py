"""Contract-v2 Exploding Kittens adapter; expected rule results remain in scenario JSON."""

from __future__ import annotations

import copy
from collections import Counter
from typing import Any

CARD_COUNTS = {
    "exploding_kitten": 4,
    "defuse": 6,
    "attack": 4,
    "nope": 5,
    "skip": 4,
    "favor": 4,
    "shuffle": 4,
    "see_future": 5,
    "cat_beard": 4,
    "cat_cattermelon": 4,
    "cat_hairy_potato": 4,
    "cat_rainbow": 4,
    "cat_tacocat": 4,
}
STATE_SCHEMA = "boardbench/exploding-kittens/state/1"
ACTION_SCHEMA = "boardbench/exploding-kittens/action/1"


def _data(game: Any, state: Any) -> dict[str, Any]:
    payload = game.state_to_data(state)
    if payload.get("schema") != STATE_SCHEMA or not isinstance(payload.get("data"), dict):
        raise NotImplementedError("state_to_data does not expose the frozen Exploding Kittens schema")
    return payload["data"]


def _action_data(game: Any, action: Any) -> dict[str, Any]:
    payload = game.action_to_data(action)
    if payload.get("schema") != ACTION_SCHEMA or not isinstance(payload.get("data"), dict):
        raise NotImplementedError("action_to_data does not expose the frozen Exploding Kittens schema")
    return payload["data"]


def _cards(data: dict[str, Any]) -> list[str]:
    result = [card for player in data["players"] for card in player["hand"]]
    for zone in ("deck", "discard", "box"):
        result.extend(data["zones"][zone])
    pending = data.get("pending")
    if isinstance(pending, dict) and pending.get("type") == "defuse":
        result.append(pending["kitten"])
    return result


def setup(module: Any, game: Any, fixture: dict[str, Any]) -> Any:
    hands = fixture.get("hands", {"0": [], "1": []})
    count = int(fixture.get("players", len(hands)))
    players = []
    alive = fixture.get("alive", [True] * count)
    previews = fixture.get("previews", {})
    for player in range(count):
        players.append({
            "id": player,
            "alive": bool(alive[player]),
            "hand": list(hands.get(str(player), hands.get(player, []))),
            "preview": list(previews.get(str(player), previews.get(player, []))),
        })
    zones = {
        "deck": list(fixture.get("deck", [])),
        "discard": list(fixture.get("discard", [])),
        "box": list(fixture.get("box", [])),
    }
    if "box" not in fixture:
        used = Counter(card for player in players for card in player["hand"])
        used.update(zones["deck"])
        used.update(zones["discard"])
        pending = fixture.get("pending")
        if isinstance(pending, dict) and pending.get("type") == "defuse":
            used.update([pending["kitten"]])
        remainder = Counter(CARD_COUNTS) - used
        if used - Counter(CARD_COUNTS):
            raise NotImplementedError("fixture exceeds printed card inventory")
        zones["box"] = sorted(remainder.elements())
    terminal = bool(fixture.get("terminal", False))
    payload = {
        "schema": STATE_SCHEMA,
        "data": {
            "configuration": {"players": count, "seed": fixture.get("seed", 1), "variant": "base"},
            "players": players,
            "zones": zones,
            "current_player": int(fixture.get("current_player", 0)),
            "turns_owed": int(fixture.get("turns_owed", 1)),
            "phase": fixture.get("phase", "terminal" if terminal else "play"),
            "pending": copy.deepcopy(fixture.get("pending")),
            "terminal": terminal,
            "winner": fixture.get("winner"),
            "turn_number": int(fixture.get("turn_number", 0)),
            "chance": {"seed": fixture.get("seed", 1), "counter": int(fixture.get("chance_counter", 0))},
        },
    }
    return game.state_from_data(copy.deepcopy(payload))


def _matches(data: dict[str, Any], spec: dict[str, Any]) -> bool:
    if data.get("type") != spec.get("type"):
        return False
    if "actor" in spec and data.get("actor") != spec["actor"]:
        return False
    args = data.get("args", {})
    for key, expected in spec.get("args", {}).items():
        actual = args.get(key)
        if key == "cards":
            if Counter(actual or []) != Counter(expected):
                return False
        elif actual != expected:
            return False
    return True


def resolve_action(module: Any, game: Any, state: Any, actions: list[Any], spec: dict[str, Any]) -> Any:
    matches = [action for action in actions if _matches(_action_data(game, action), spec)]
    if len(matches) != 1:
        raise NotImplementedError(f"expected exactly one canonical action match for {spec}, got {len(matches)}")
    return matches[0]


def _assert(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def _player(data: dict[str, Any], player: int) -> dict[str, Any]:
    matches = [item for item in data["players"] if item["id"] == player]
    if len(matches) != 1:
        raise AssertionError(f"expected player {player}")
    return matches[0]


def _counter(value: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(value).items()))


def _check_setup_probe(module: Any, probe: dict[str, Any]) -> None:
    count = int(probe["players"])
    game = module.Game(num_players=count, seed=int(probe.get("seed", 1)))
    state = game.initial_state()
    data = _data(game, state)
    _assert("setup player count", data["configuration"]["players"], count)
    _assert("setup hand sizes", [len(item["hand"]) for item in data["players"]], [8] * count)
    for item in data["players"]:
        _assert(f"player {item['id']} starting Defuse", item["hand"].count("defuse"), 1)
        _assert(f"player {item['id']} starting Kitten", item["hand"].count("exploding_kitten"), 0)
    _assert("setup deck size", len(data["zones"]["deck"]), int(probe["deck_size"]))
    for card, wanted in probe["deck_counts"].items():
        _assert(f"setup deck {card}", data["zones"]["deck"].count(card), int(wanted))
    _assert("setup box size", len(data["zones"]["box"]), int(probe["box_size"]))
    for card, wanted in probe.get("box_counts", {}).items():
        _assert(f"setup box {card}", data["zones"]["box"].count(card), int(wanted))
    _assert("complete inventory", Counter(_cards(data)), Counter(CARD_COUNTS))
    if game.is_terminal(state) or not game.legal_actions(state):
        raise AssertionError("supported initial state is not playable")


def _check_player_counts(module: Any, probe: dict[str, Any]) -> None:
    for count in probe["supported"]:
        game = module.Game(num_players=int(count), seed=int(probe.get("seed", 1)))
        state = game.initial_state()
        if game.is_terminal(state) or not game.legal_actions(state):
            raise AssertionError(f"supported count {count} is not initially playable")
        for _ in range(int(probe.get("bounded_actions", 20))):
            if game.is_terminal(state):
                break
            actions = list(game.legal_actions(state))
            if not actions:
                raise AssertionError(f"supported count {count} stalled")
            result = game.apply_action(state, actions[0])
            if result is not None:
                state = result
    for count in probe["unsupported"]:
        try:
            module.Game(num_players=int(count), seed=int(probe.get("seed", 1)))
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsupported player count accepted: {count}")


def check(module: Any, game: Any, state: Any, expected: dict[str, Any]) -> None:
    if "setup_probe" in expected:
        _check_setup_probe(module, expected["setup_probe"])
        return
    if "player_count_probe" in expected:
        _check_player_counts(module, expected["player_count_probe"])
        return
    data = _data(game, state)
    if "hand_sizes" in expected:
        _assert("hand_sizes", {str(p["id"]): len(p["hand"]) for p in data["players"]}, expected["hand_sizes"])
    for player, counts in expected.get("hand_counts", {}).items():
        hand = _player(data, int(player))["hand"]
        for card, wanted in counts.items():
            _assert(f"hand {player} {card}", hand.count(card), int(wanted))
    if "hand_exact" in expected:
        for player, cards in expected["hand_exact"].items():
            _assert(f"hand {player}", _player(data, int(player))["hand"], cards)
    if "deck_size" in expected:
        _assert("deck_size", len(data["zones"]["deck"]), int(expected["deck_size"]))
    if "deck" in expected:
        _assert("deck", data["zones"]["deck"], expected["deck"])
    if "deck_multiset" in expected:
        _assert("deck_multiset", _counter(data["zones"]["deck"]), _counter(expected["deck_multiset"]))
    if "discard" in expected:
        _assert("discard", data["zones"]["discard"], expected["discard"])
    for zone in ("deck", "discard", "box"):
        key = f"{zone}_counts"
        if key in expected:
            for card, wanted in expected[key].items():
                _assert(f"{zone} {card}", data["zones"][zone].count(card), int(wanted))
    if "total_card_counts" in expected:
        actual = Counter(_cards(data))
        for card, wanted in expected["total_card_counts"].items():
            _assert(f"total {card}", actual[card], int(wanted))
        _assert("total cards", sum(actual.values()), int(expected.get("total_cards", sum(expected["total_card_counts"].values()))))
    if "alive" in expected:
        _assert("alive", [p["alive"] for p in data["players"]], expected["alive"])
    if "turns_owed" in expected:
        _assert("turns_owed", data["turns_owed"], int(expected["turns_owed"]))
    if "phase" in expected:
        _assert("phase", data["phase"], expected["phase"])
    if "winner" in expected:
        _assert("winner", data["winner"], expected["winner"])
    if "pending" in expected:
        for key, value in expected["pending"].items():
            _assert(f"pending {key}", (data["pending"] or {}).get(key), value)
    for case in expected.get("action_match_cases", []):
        count = sum(_matches(_action_data(game, action), case["action"]) for action in game.legal_actions(state))
        _assert(f"action matches {case['action']}", count, int(case["count"]))
    for player, wanted in expected.get("observations", {}).items():
        payload = game.observation_to_data(state, int(player))
        if payload.get("schema") != "boardbench/exploding-kittens/observation/1":
            raise NotImplementedError("observation_to_data does not expose the frozen Exploding Kittens schema")
        observation = payload["data"]
        for key, value in wanted.items():
            _assert(f"observation {player} {key}", observation.get(key), value)
