"""Contract-v2 Abalone scenario adapter; expected results stay in scenario JSON."""

from __future__ import annotations

import copy
from typing import Any

DIRECTIONS = {"E": (1, 0), "NE": (1, -1), "NW": (0, -1), "W": (-1, 0), "SW": (-1, 1), "SE": (0, 1)}


def cells() -> list[str]:
    return [f"{q},{r}" for q in range(-4, 5) for r in range(-4, 5) if abs(q + r) <= 4]


def _data(game: Any, state: Any) -> dict[str, Any]:
    payload = game.state_to_data(state)
    if payload.get("schema") != "boardbench/abalone/state/1" or not isinstance(payload.get("data"), dict):
        raise NotImplementedError("state_to_data does not expose the frozen Abalone schema")
    return payload["data"]


def _action_data(game: Any, action: Any) -> dict[str, Any]:
    payload = game.action_to_data(action)
    if payload.get("schema") != "boardbench/abalone/action/1" or not isinstance(payload.get("data"), dict):
        raise NotImplementedError("action_to_data does not expose the frozen Abalone schema")
    return payload["data"]


def _move_matches(data: dict[str, Any], spec: dict[str, Any]) -> bool:
    if data.get("type") != "move" or data.get("actor") != int(spec.get("actor", 0)):
        return False
    args = data.get("args", {})
    return set(args.get("group", [])) == set(spec["group"]) and args.get("direction") == spec["direction"].upper()


def setup(module: Any, game: Any, fixture: dict[str, Any]) -> Any:
    board = {cell: None for cell in cells()}
    for color in ("black", "white"):
        for cell in fixture.get(color, []):
            if cell not in board or board[cell] is not None:
                raise NotImplementedError(f"invalid fixture cell: {cell}")
            board[cell] = color
    active = 0 if fixture.get("active", "black") == "black" else 1
    terminal = bool(fixture.get("terminal", False))
    payload = {
        "schema": "boardbench/abalone/state/1",
        "data": {
            "configuration": {"players": 2, "seed": fixture.get("seed", 1), "variant": "base"},
            "board": board,
            "current_player": int(fixture.get("current_player", active)),
            "captures": [int(value) for value in fixture.get("captures", [0, 0])],
            "terminal": terminal,
            "winner": fixture.get("winner"),
            "phase": "terminal" if terminal else "play",
            "move_number": int(fixture.get("move_number", 0)),
            "pending": None,
            "chance": {"seed": fixture.get("seed", 1)}
        }
    }
    return game.state_from_data(copy.deepcopy(payload))


def resolve_action(module: Any, game: Any, state: Any, actions: list[Any], spec: dict[str, Any]) -> Any:
    if spec.get("type") == "pass":
        matches = [action for action in actions if _action_data(game, action).get("type") == "pass"]
    else:
        matches = [action for action in actions if _move_matches(_action_data(game, action), spec)]
    if len(matches) != 1:
        raise NotImplementedError(f"expected exactly one canonical action match, got {len(matches)}")
    return matches[0]


def _assert_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def _legal_matches(game: Any, state: Any, spec: dict[str, Any]) -> list[Any]:
    return [action for action in game.legal_actions(state) if _move_matches(_action_data(game, action), spec)]


def check(module: Any, game: Any, state: Any, expected: dict[str, Any]) -> None:
    data = _data(game, state)
    board = data["board"]
    if "playable_cell_count" in expected:
        _assert_equal("playable_cell_count", len(board), int(expected["playable_cell_count"]))
    if "marble_counts" in expected:
        actual = {color: sum(value == color for value in board.values()) for color in ("black", "white")}
        _assert_equal("marble_counts", actual, expected["marble_counts"])
    if "empty_count" in expected:
        _assert_equal("empty_count", sum(value is None for value in board.values()), int(expected["empty_count"]))
    if "captures" in expected:
        _assert_equal("captures", data["captures"], expected["captures"])
    if "positions" in expected:
        actual = {color: sorted(cell for cell, value in board.items() if value == color) for color in ("black", "white")}
        wanted = {color: sorted(expected["positions"][color]) for color in ("black", "white")}
        _assert_equal("positions", actual, wanted)
    if "occupancy" in expected:
        for cell, color in expected["occupancy"].items():
            _assert_equal(f"occupancy[{cell}]", board[cell] or "empty", color)
    for spec in expected.get("move_legal_cases", []):
        matches = _legal_matches(game, state, spec)
        _assert_equal(f"move match count {spec}", len(matches), int(spec["match_count"]))
    if "move_legal" in expected:
        spec = expected["move_legal"]
        matches = _legal_matches(game, state, spec)
        wanted = int(spec.get("match_count", 1 if spec.get("expected", True) else 0))
        _assert_equal("move match count", len(matches), wanted)
    if "pass_match_count" in expected:
        count = sum(_action_data(game, action).get("type") == "pass" for action in game.legal_actions(state))
        _assert_equal("pass_match_count", count, int(expected["pass_match_count"]))
    if "successor_unique" in expected:
        outcomes: dict[str, int] = {}
        for action in game.legal_actions(state):
            probe = game.state_from_data(copy.deepcopy(game.state_to_data(state)))
            result = game.apply_action(probe, action)
            successor = probe if result is None else result
            key = repr(game.state_to_data(successor))
            outcomes[key] = outcomes.get(key, 0) + 1
        _assert_equal("maximum duplicate successor count", max(outcomes.values(), default=1), int(expected["successor_unique"]))
    if "player_count_probe" in expected:
        probe = expected["player_count_probe"]
        for count in probe["supported"]:
            other = module.Game(num_players=int(count), seed=int(probe["seed"]))
            other_state = other.initial_state()
            if other.is_terminal(other_state) or not other.legal_actions(other_state):
                raise AssertionError(f"supported {count}-player initial state is not playable")
            for _ in range(int(probe["bounded_actions"])):
                if other.is_terminal(other_state):
                    break
                actions = list(other.legal_actions(other_state))
                if not actions:
                    raise AssertionError(f"supported {count}-player nonterminal state has no action")
                result = other.apply_action(other_state, actions[0])
                if result is not None:
                    other_state = result
        exception_name = probe["exception"]
        exception_type = __builtins__[exception_name] if isinstance(__builtins__, dict) else getattr(__builtins__, exception_name)
        for count in probe["unsupported"]:
            try:
                module.Game(num_players=int(count), seed=int(probe["seed"]))
            except exception_type:
                pass
            else:
                raise AssertionError(f"unsupported player count accepted: {count}")
