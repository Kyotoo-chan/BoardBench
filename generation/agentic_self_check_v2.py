#!/usr/bin/env python3
"""Evaluator-neutral self-check copied into isolated implementation workspaces."""

from __future__ import annotations

import copy
import importlib.util
import json
import random
import re
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("implementation.py")
PROFILE_PATH = Path(__file__).with_name("GAME_PROFILE.json")
MAX_ROLLOUTS = 40
MAX_STEPS = 300
MAX_STATES = 300
REQUIRED_METHODS = (
    "initial_state", "current_player", "legal_actions", "apply_action", "is_terminal",
    "returns", "render", "action_to_name", "name_to_action", "state_to_data",
    "state_from_data", "action_to_data", "action_from_data", "observation_to_data",
)


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def validate_envelope(value, suffix, expected_schema=None):
    assert isinstance(value, dict) and set(value) == {"schema", "data"}, f"invalid canonical {suffix} envelope"
    schema = value["schema"]
    assert isinstance(schema, str) and re.fullmatch(rf"boardbench/.+/{re.escape(suffix)}/[1-9][0-9]*", schema), f"invalid canonical {suffix} schema"
    if expected_schema is not None:
        assert schema == expected_schema, f"canonical {suffix} schema differs from GAME_PROFILE.json"
    assert isinstance(value["data"], dict), f"canonical {suffix} data must be an object"
    canonical_json(value)


def validate_state_contract(game, state, profile):
    payload = game.state_to_data(state)
    validate_envelope(payload, "state", profile["state_schema"] if profile else None)
    if profile:
        assert set(payload["data"]) == set(profile["state_data"]["required"]), "canonical state fields differ from GAME_PROFILE.json"
        for player in range(len(payload["data"].get("players", []))):
            observation = game.observation_to_data(state, player)
            validate_envelope(observation, "observation", profile["observation_schema"])
            assert set(observation["data"]) == set(profile["observation_data"]["required"]), "canonical observation fields differ from GAME_PROFILE.json"
    rebuilt = game.state_from_data(copy.deepcopy(payload))
    assert game.state_to_data(rebuilt) == payload, "canonical state does not round-trip"
    assert game.current_player(rebuilt) == game.current_player(state)
    assert bool(game.is_terminal(rebuilt)) == bool(game.is_terminal(state))
    assert list(game.returns(rebuilt)) == list(game.returns(state))
    original_actions = sorted(canonical_json(game.action_to_data(action)) for action in game.legal_actions(state))
    rebuilt_actions = sorted(canonical_json(game.action_to_data(action)) for action in game.legal_actions(rebuilt))
    assert rebuilt_actions == original_actions, "canonical state round-trip changes legal actions"


def validate_action_contract(game, action, profile):
    payload = game.action_to_data(action)
    validate_envelope(payload, "action", profile["action_schema"] if profile else None)
    assert isinstance(payload["data"].get("type"), str) and payload["data"]["type"], "canonical action needs data.type"
    if profile:
        assert set(payload["data"]) == set(profile["action_data"]["required"]), "canonical action fields differ from GAME_PROFILE.json"
        assert payload["data"]["type"] in profile["action_data"]["type_ids"], "unknown canonical action type"
    rebuilt = game.action_from_data(copy.deepcopy(payload))
    assert game.action_to_data(rebuilt) == payload, "canonical action does not round-trip"


def load_module():
    spec = importlib.util.spec_from_file_location("generated_implementation", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_module()
    game = module.Game()
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8")) if PROFILE_PATH.is_file() else None
    missing = [name for name in REQUIRED_METHODS if not callable(getattr(game, name, None))]
    assert not missing, f"missing required methods: {', '.join(missing)}"
    initial = game.initial_state()
    assert isinstance(game.render(initial), str), "render must return str"
    rng = random.Random(1)
    checked_states = 0
    checked_actions = 0

    for _ in range(MAX_ROLLOUTS):
        state = game.initial_state()
        for _ in range(MAX_STEPS):
            validate_state_contract(game, state, profile)
            terminal = bool(game.is_terminal(state))
            actions = list(game.legal_actions(state))
            if terminal:
                assert not actions, "terminal state exposes legal actions"
                break
            assert actions, "nonterminal state has no legal actions"

            raw_names = []
            for action in actions:
                validate_action_contract(game, action, profile)
                name = str(game.action_to_name(action))
                assert name, "empty action name"
                assert game.name_to_action(name) == action, f"action does not round-trip: {name!r}"
                raw_names.append(name)

                cloned_game, cloned_state, cloned_action = copy.deepcopy((game, state, action))
                next_state = cloned_game.apply_action(cloned_state, cloned_action)
                if next_state is None:
                    next_state = cloned_state
                cloned_game.current_player(next_state)
                cloned_game.legal_actions(next_state)
                cloned_game.is_terminal(next_state)
                cloned_game.returns(next_state)
                checked_actions += 1

            assert len(raw_names) == len(set(raw_names)), "duplicate legal action names"
            state = game.apply_action(state, rng.choice(actions))
            if state is None:
                raise AssertionError("apply_action returned None")
            checked_states += 1
            if checked_states >= MAX_STATES:
                print(f"agentic-self-check OK states={checked_states} actions={checked_actions}")
                return

    assert checked_states > 0 and checked_actions > 0
    print(f"agentic-self-check OK states={checked_states} actions={checked_actions}")


if __name__ == "__main__":
    main()
