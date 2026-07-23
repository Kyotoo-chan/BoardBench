#!/usr/bin/env python3
"""Evaluator-neutral complete-payload reconstruction checks for the CATAN profile."""

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
    assert game.state_to_data(rebuilt) == payload, f"{label} did not round-trip"
    game.current_player(rebuilt)
    game.is_terminal(rebuilt)
    game.returns(rebuilt)
    actions = list(game.legal_actions(rebuilt))
    for action in actions:
        encoded = game.action_to_data(action)
        assert game.action_to_data(game.action_from_data(copy.deepcopy(encoded))) == encoded
    for player in range(4):
        game.observation_to_data(rebuilt, player)


def pending_for(phase):
    zero = {"wood": 0, "brick": 0, "wool": 0, "grain": 0, "ore": 0}
    variants = {
        "discard": {"type": "discard", "required": {"1": 1}, "submitted": {"1": zero}, "resume": "robber_move"},
        "robber_move": {"type": "robber_move", "resume_phase": "trade", "source": "seven"},
        "robber_steal": {"type": "robber_steal", "resume_phase": "trade", "victims": [1], "source": "seven"},
        "trade_offer": {"type": "domestic_trade", "legs": [], "resume_phase": "trade"},
        "road_building": {"type": "road_building", "resume_phase": "build", "remaining": 2},
    }
    return variants.get(phase)


def main():
    module = load_module()
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    game = module.Game(num_players=4, seed=1)
    base = game.state_to_data(game.initial_state())
    assert base["schema"] == profile["state_schema"]
    assert set(base["data"]) == set(profile["state_data"]["required"])
    roundtrip(game, base, "initial state")

    for phase in profile["phase_ids"]:
        payload = copy.deepcopy(base)
        data = payload["data"]
        data["phase"] = phase
        data["pending"] = pending_for(phase)
        data["terminal"] = phase == "terminal"
        data["winner"] = 0 if data["terminal"] else None
        data["current_player"] = 1 if phase == "discard" else data["active_player"]
        roundtrip(game, payload, f"phase {phase}")

    payload = copy.deepcopy(base)
    payload["data"]["chance"]["scripted_rolls"] = [[3, 4], [6, 6]]
    payload["data"]["chance"]["scripted_steals"] = ["wood", "ore"]
    roundtrip(game, payload, "scripted chance")
    print("catan-profile-fixture-self-check OK")


if __name__ == "__main__":
    main()
