#!/usr/bin/env python3
"""Evaluator-neutral canonical fixture reconstruction check for Abalone."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("implementation.py")
PROFILE_PATH = Path(__file__).with_name("GAME_PROFILE.json")


def load_module():
    spec = importlib.util.spec_from_file_location("fixture_checked_implementation", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def cells():
    return [f"{q},{r}" for q in range(-4, 5) for r in range(-4, 5) if abs(q + r) <= 4]


def roundtrip(game, payload, label):
    rebuilt = game.state_from_data(copy.deepcopy(payload))
    assert game.state_to_data(rebuilt) == payload, f"{label} did not round-trip"
    game.current_player(rebuilt)
    game.is_terminal(rebuilt)
    game.returns(rebuilt)
    for action in game.legal_actions(rebuilt):
        action_data = game.action_to_data(action)
        assert game.action_to_data(game.action_from_data(copy.deepcopy(action_data))) == action_data
    for player in range(2):
        observation = game.observation_to_data(rebuilt, player)
        assert observation["schema"].endswith("/observation/1")


def main():
    module = load_module()
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    game = module.Game(num_players=2, seed=1)
    initial = game.state_to_data(game.initial_state())
    assert initial["schema"] == profile["state_schema"]
    assert len(initial["data"]["board"]) == 61
    roundtrip(game, initial, "initial state")

    board = {cell: None for cell in cells()}
    black = ["-1,0", "0,0", "0,-4", "1,-4", "2,-4", "3,-4", "4,-4", "-1,-3", "0,-3", "1,-3", "2,-3", "3,-3"]
    white = ["1,0", "-4,4", "-3,4", "-2,4", "-1,4", "0,4", "-4,3", "-3,3", "-2,3", "-1,3", "0,3"]
    board.update({cell: "black" for cell in black})
    board.update({cell: "white" for cell in white})
    fixture = {
        "schema": profile["state_schema"],
        "data": {
            "configuration": {"players": 2, "seed": 1, "variant": "base"},
            "board": board,
            "current_player": 0,
            "captures": [3, 2],
            "terminal": False,
            "winner": None,
            "phase": "play",
            "move_number": 9,
            "pending": None,
            "chance": {"seed": 1}
        }
    }
    roundtrip(game, fixture, "sparse public fixture")

    terminal = copy.deepcopy(fixture)
    terminal["data"]["board"].update({cell: None for cell in white[8:]})
    terminal["data"].update({"captures": [6, 2], "terminal": True, "winner": 0, "phase": "terminal"})
    roundtrip(game, terminal, "terminal state")
    print("profile-fixture-self-check OK")


if __name__ == "__main__":
    main()
