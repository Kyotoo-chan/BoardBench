#!/usr/bin/env python3
"""Evaluator-neutral canonical fixture reconstruction check for the supplied game profile."""

from __future__ import annotations

import copy
import importlib.util
import json
from collections import Counter
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("implementation.py")
PROFILE_PATH = Path(__file__).with_name("GAME_PROFILE.json")


def load_module():
    spec = importlib.util.spec_from_file_location("fixture_checked_implementation", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cards(data):
    result = []
    for player in data["players"]:
        result.extend(player["hand"])
        for field in player["fields"]:
            result.extend(field)
    for name in ("deck", "discard", "revealed", "reserve"):
        result.extend(data["zones"][name])
    for group in data["zones"]["pending_received"]:
        result.extend(group)
    return result


def roundtrip(game, payload, label):
    rebuilt = game.state_from_data(copy.deepcopy(payload))
    actual = game.state_to_data(rebuilt)
    assert actual == payload, f"{label} did not round-trip"
    game.current_player(rebuilt)
    game.is_terminal(rebuilt)
    game.returns(rebuilt)
    game.legal_actions(rebuilt)


def blank(base):
    payload = copy.deepcopy(base)
    data = payload["data"]
    inventory = Counter(cards(data))
    for player in data["players"]:
        player["hand"] = []
        player["fields"] = [[] for _ in player["fields"]]
        player["coins"] = 0
        if "third_field" in player:
            player["third_field"] = False
        if "alive" in player:
            player["alive"] = True
    data["zones"] = {"deck": [], "discard": [], "revealed": [], "pending_received": [[] for _ in data["players"]], "reserve": sorted(inventory.elements())}
    data["depletions"] = 0
    data["pending"] = None
    data["terminal"] = False
    data["current_player"] = 0
    data["active_player"] = 0
    return payload


def move_from_reserve(data, bean, target):
    data["zones"]["reserve"].remove(bean)
    target.append(bean)


def main():
    module = load_module()
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    game = module.Game(num_players=4, seed=1)
    base = game.state_to_data(game.initial_state())
    assert base["schema"] == profile["state_schema"]
    roundtrip(game, base, "initial state")

    template = blank(base)
    beans = profile["bean_ids"]
    for phase in profile["phase_ids"]:
        payload = copy.deepcopy(template)
        data = payload["data"]
        data["phase"] = phase
        data["terminal"] = phase == "terminal"
        if not data["terminal"]:
            move_from_reserve(data, beans[0], data["players"][0]["hand"])
            move_from_reserve(data, beans[1], data["zones"]["deck"])
        roundtrip(game, payload, f"phase {phase}")

    payload = copy.deepcopy(template)
    data = payload["data"]
    data["phase"] = "trade_response"
    data["current_player"] = 1
    move_from_reserve(data, beans[0], data["players"][0]["hand"])
    data["pending"] = {
        "type": "gift", "actor": 0, "partner": 1,
        "offered": [{"owner": 0, "zone": "hand", "index": 0, "bean": beans[0]}],
        "requested": [], "awaiting_player": 1,
    }
    roundtrip(game, payload, "pending consent")

    payload = copy.deepcopy(template)
    data = payload["data"]
    if "third_field" in data["players"][0]:
        data["players"][0]["third_field"] = True
        data["players"][0]["fields"] = [[], [], []]
    for target in (data["players"][0]["hand"], data["players"][0]["fields"][0], data["zones"]["deck"], data["zones"]["discard"], data["zones"]["revealed"], data["zones"]["pending_received"][1]):
        move_from_reserve(data, beans[0], target)
    data["depletions"] = 2
    roundtrip(game, payload, "zones and optional fields")

    five = module.Game(num_players=5, seed=1)
    five_data = five.state_to_data(five.initial_state())
    assert len(five_data["data"]["players"]) == 5, "five-player constructor ignored num_players"
    roundtrip(five, five_data, "five-player initial state")
    print("profile-fixture-self-check OK")


if __name__ == "__main__":
    main()
