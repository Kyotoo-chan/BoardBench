#!/usr/bin/env python3
"""Evaluator-neutral contract-v2 round-trip check for the 6 nimmt! data profile."""

from __future__ import annotations

import copy
import importlib.util
import json
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


def roundtrip(game, payload, label):
    rebuilt = game.state_from_data(copy.deepcopy(payload))
    assert game.state_to_data(rebuilt) == payload, f"{label} state did not round-trip"
    game.is_terminal(rebuilt)
    game.returns(rebuilt)
    for action in game.legal_actions(rebuilt):
        encoded = game.action_to_data(action)
        assert game.action_to_data(game.action_from_data(copy.deepcopy(encoded))) == encoded
    for player in range(payload["data"]["configuration"]["players"]):
        observation = game.observation_to_data(rebuilt, player)
        assert observation["schema"] == "boardbench/six-nimmt/observation/2"


def low_choice_fixture(base):
    payload = copy.deepcopy(base)
    data = payload["data"]
    actor = 0
    card = data["players"][actor]["hand"].pop()
    data["players"][actor]["committed_card"] = None
    data["phase"] = "choose_row"
    data["current_player"] = actor
    data["zones"]["revealed"] = [{"player": actor, "card": card}]
    data["zones"]["resolved"] = []
    data["pending"] = {"type": "low_choice", "player": actor, "card": card, "remaining": []}
    return payload


def terminal_fixture(base):
    payload = copy.deepcopy(base)
    data = payload["data"]
    data["phase"] = "terminal"
    data["current_player"] = None
    data["pending"] = None
    data["terminal"] = True
    data["winners"] = [0]
    return payload


def main():
    module = load_module()
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    game = module.Game(num_players=4, seed=1)
    initial = game.state_to_data(game.initial_state())
    assert initial["schema"] == profile["state_schema"]
    roundtrip(game, initial, "initial")
    roundtrip(game, low_choice_fixture(initial), "low_choice shape")
    roundtrip(game, terminal_fixture(initial), "terminal shape")
    print("6-nimmt-v2-profile-fixture-self-check OK")


if __name__ == "__main__":
    main()
