#!/usr/bin/env python3
"""Evaluator-neutral canonical fixture reconstruction check for Exploding Kittens V2."""

from __future__ import annotations

import copy
import importlib.util
import json
from collections import Counter
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("implementation.py")
PROFILE_PATH = Path(__file__).with_name("GAME_PROFILE.json")
COUNTS = {
    "exploding_kitten": 4, "defuse": 6, "attack": 4, "nope": 5, "skip": 4,
    "favor": 4, "shuffle": 4, "see_future": 5, "cat_beard": 4,
    "cat_cattermelon": 4, "cat_hairy_potato": 4, "cat_rainbow": 4, "cat_tacocat": 4,
}


def load_module():
    spec = importlib.util.spec_from_file_location("fixture_checked_implementation", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cards(data):
    result = [card for player in data["players"] for card in player["hand"]]
    for zone in ("deck", "discard", "box"):
        result.extend(data["zones"][zone])
    pending = data.get("pending")
    if isinstance(pending, dict) and pending.get("type") == "defuse":
        result.append(pending["kitten"])
    return result


def roundtrip(game, payload, label):
    rebuilt = game.state_from_data(copy.deepcopy(payload))
    actual = game.state_to_data(rebuilt)
    assert actual == payload, f"{label} did not round-trip"
    game.current_player(rebuilt)
    game.is_terminal(rebuilt)
    game.returns(rebuilt)
    for action in game.legal_actions(rebuilt):
        encoded = game.action_to_data(action)
        assert game.action_to_data(game.action_from_data(copy.deepcopy(encoded))) == encoded
    for player in range(payload["data"]["configuration"]["players"]):
        observation = game.observation_to_data(rebuilt, player)
        assert observation["schema"] == "boardbench/exploding-kittens/observation/1"


def fixture(base, phase, pending=None):
    payload = copy.deepcopy(base)
    data = payload["data"]
    for player in data["players"]:
        player["hand"] = []
        player["preview"] = []
        player["alive"] = True
    data["zones"] = {"deck": [], "discard": [], "box": sorted(Counter(cards(data)).elements())}
    data["current_player"] = 0
    data["turns_owed"] = 1
    data["phase"] = phase
    data["pending"] = copy.deepcopy(pending)
    data["terminal"] = phase == "terminal"
    data["winner"] = 0 if phase == "terminal" else None
    if phase == "terminal":
        data["players"][1]["alive"] = False
    return payload


def move(data, target, card):
    data["zones"]["box"].remove(card)
    target.append(card)


def main():
    module = load_module()
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    for count in profile["player_counts"]["supported"]:
        game = module.Game(num_players=count, seed=1)
        payload = game.state_to_data(game.initial_state())
        assert payload["schema"] == profile["state_schema"]
        assert Counter(cards(payload["data"])) == Counter(COUNTS)
        roundtrip(game, payload, f"{count}-player initial")

    game = module.Game(num_players=2, seed=1)
    base = game.state_to_data(game.initial_state())
    pending_by_phase = {
        "play": None,
        "reaction": {"type": "reaction", "proposed": {"type": "play_card", "actor": 0, "args": {"card": "attack", "target": None}}, "cards": ["attack"], "nope_count": 0, "responder": 1, "remaining_responders": [1]},
        "favor_give": {"type": "favor", "actor": 0, "target": 1},
        "defuse_reinsert": {"type": "defuse", "actor": 0, "kitten": "exploding_kitten"},
        "terminal": None,
    }
    for phase, pending in pending_by_phase.items():
        payload = fixture(base, phase, pending)
        data = payload["data"]
        if phase == "reaction":
            move(data, data["zones"]["discard"], "attack")
            move(data, data["players"][1]["hand"], "nope")
        elif phase == "favor_give":
            move(data, data["players"][1]["hand"], "skip")
        elif phase == "defuse_reinsert":
            data["zones"]["box"].remove("exploding_kitten")
            move(data, data["zones"]["deck"], "attack")
            move(data, data["zones"]["discard"], "defuse")
        assert Counter(cards(data)) == Counter(COUNTS)
        roundtrip(game, payload, phase)
    print("profile-fixture-self-check OK")


if __name__ == "__main__":
    main()
