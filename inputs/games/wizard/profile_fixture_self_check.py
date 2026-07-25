#!/usr/bin/env python3
"""Evaluator-neutral canonical fixture reconstruction check for Wizard."""

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
    result.extend(data["zones"]["deck"])
    if data["zones"]["revealed_trump"] is not None:
        result.append(data["zones"]["revealed_trump"])
    result.extend(entry["card"] for entry in data["zones"]["trick"])
    for trick in data["zones"]["completed_tricks"]:
        result.extend(trick["cards"])
    result.extend(data["zones"]["reserve"])
    return result


def player(data, player_id):
    matches = [entry for entry in data["players"] if entry["id"] == player_id]
    assert len(matches) == 1, f"expected one player with id {player_id}"
    return matches[0]


def roundtrip(game, payload, label):
    rebuilt = game.state_from_data(copy.deepcopy(payload))
    actual = game.state_to_data(rebuilt)
    assert actual == payload, f"{label} did not round-trip"
    game.current_player(rebuilt)
    game.is_terminal(rebuilt)
    game.returns(rebuilt)
    actions = game.legal_actions(rebuilt)
    for action in actions:
        action_payload = game.action_to_data(action)
        assert game.action_to_data(game.action_from_data(copy.deepcopy(action_payload))) == action_payload
    for player in range(payload["data"]["configuration"]["players"]):
        observation = game.observation_to_data(rebuilt, player)
        assert observation["schema"].endswith("/observation/1")


def blank(base):
    payload = copy.deepcopy(base)
    data = payload["data"]
    inventory = Counter(cards(data))
    for player in data["players"]:
        player["hand"] = []
        player["prediction"] = None
        player["tricks_won"] = 0
        player["score"] = 0
    data["zones"] = {
        "deck": [],
        "revealed_trump": None,
        "trick": [],
        "completed_tricks": [],
        "reserve": sorted(inventory.elements()),
    }
    data["round_number"] = 1
    data["dealer"] = 0
    data["leader"] = 1
    data["current_player"] = 1
    data["phase"] = "predict"
    data["terminal"] = False
    data["trump_suit"] = None
    data["led_suit"] = None
    data["pending"] = None
    return payload


def move(data, target, *, preferred=None):
    reserve = data["zones"]["reserve"]
    index = reserve.index(preferred) if preferred in reserve else 0
    target.append(reserve.pop(index))


def main():
    module = load_module()
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    game = module.Game(num_players=4, seed=1)
    base = game.state_to_data(game.initial_state())
    assert base["schema"] == profile["state_schema"]
    roundtrip(game, base, "initial state")

    template = blank(base)
    for phase in profile["phase_ids"]:
        payload = copy.deepcopy(template)
        data = payload["data"]
        data["phase"] = phase
        data["terminal"] = phase == "terminal"
        if phase == "choose_trump":
            data["current_player"] = data["dealer"]
            data["pending"] = {"type": "trump_choice", "player": data["dealer"]}
            revealed = []
            move(data, revealed, preferred="zauberer")
            data["zones"]["revealed_trump"] = revealed[0]
        elif phase in {"predict", "play"}:
            for player in data["players"]:
                move(data, player["hand"])
                if phase == "play":
                    player["prediction"] = 0
        roundtrip(game, payload, f"phase {phase}")

    payload = copy.deepcopy(template)
    data = payload["data"]
    move(data, player(data, 0)["hand"])
    move(data, data["zones"]["deck"])
    reveal = []
    move(data, reveal)
    data["zones"]["revealed_trump"] = reveal[0]
    trick_card = []
    move(data, trick_card)
    data["zones"]["trick"] = [{"player": 1, "card": trick_card[0]}]
    won = []
    move(data, won)
    data["zones"]["completed_tricks"] = [{"winner": 2, "cards": won}]
    player(data, 2)["tricks_won"] = 1
    roundtrip(game, payload, "all zones")

    for count in (3, 5, 6):
        other = module.Game(num_players=count, seed=1)
        other_data = other.state_to_data(other.initial_state())
        assert len(other_data["data"]["players"]) == count, f"{count}-player constructor ignored num_players"
        roundtrip(other, other_data, f"{count}-player initial state")

    print("profile-fixture-self-check OK")


if __name__ == "__main__":
    main()
