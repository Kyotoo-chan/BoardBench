"""Evaluator-only state adapter for Abalone's axial-coordinate fixtures."""

from __future__ import annotations

import copy
from dataclasses import is_dataclass, replace
from typing import Any

DIRECTIONS = {
    "E": (1, 0),
    "W": (-1, 0),
    "SE": (0, 1),
    "NW": (0, -1),
    "SW": (-1, 1),
    "NE": (1, -1),
}
BOARD_FIELDS = ("board", "grid", "cells")
PLAYER_FIELDS = ("current_player", "player", "active_player", "turn")


def _coord(value: str | list[int] | tuple[int, int]) -> tuple[int, int]:
    if isinstance(value, str):
        q, r = value.split(",")
        return int(q), int(r)
    return int(value[0]), int(value[1])


def _valid_cells() -> list[tuple[int, int]]:
    return [
        (q, r)
        for r in range(-4, 5)
        for q in range(max(-4, -r - 4), min(4, -r + 4) + 1)
    ]


def _field(state: Any, names: tuple[str, ...]) -> str:
    name = next((name for name in names if hasattr(state, name)), None)
    if name is None:
        raise NotImplementedError(f"state has none of {names!r}")
    return name


def _with_changes(state: Any, changes: dict[str, Any]) -> Any:
    if is_dataclass(state):
        return replace(state, **changes)
    result = copy.deepcopy(state)
    for name, value in changes.items():
        setattr(result, name, value)
    return result


def _board_info(game: Any, state: Any) -> tuple[str, Any, Any, Any, str]:
    cached = getattr(game, "_boardbench_abalone_tokens", None)
    board_name = _field(state, BOARD_FIELDS)
    board = getattr(state, board_name)
    if cached is not None:
        black, white, empty, kind = cached
        return board_name, board, black, white, kind

    if isinstance(board, dict):
        if (0, -4) not in board or (-4, 4) not in board:
            raise NotImplementedError("mapping board must use radius-4 axial (q, r) keys")
        black, white = board[(0, -4)], board[(-4, 4)]
        empty = board.get((0, 0))
        kind = "mapping"
    elif isinstance(board, (list, tuple)) and board and all(
        isinstance(entry, (list, tuple)) and len(entry) == 3 for entry in board
    ):
        values = {(int(q), int(r)): value for q, r, value in board}
        if (0, -4) not in values or (-4, 4) not in values:
            raise NotImplementedError("triple board must use radius-4 axial (q, r, value) entries")
        black, white, empty = values[(0, -4)], values[(-4, 4)], None
        kind = "triples"
    elif isinstance(board, (list, tuple)) and len(board) == 9:
        black, white = board[0][0], board[8][0]
        empty = board[4][0]
        kind = "rows"
    else:
        raise NotImplementedError("board must use an axial mapping, axial triples, or nine variable-length rows")

    setattr(game, "_boardbench_abalone_tokens", (black, white, empty, kind))
    return board_name, board, black, white, kind


def _positions(game: Any, state: Any) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    _, board, black, white, kind = _board_info(game, state)
    blacks: set[tuple[int, int]] = set()
    whites: set[tuple[int, int]] = set()
    if kind == "mapping":
        for cell, value in board.items():
            if value == black:
                blacks.add(_coord(cell))
            elif value == white:
                whites.add(_coord(cell))
    elif kind == "triples":
        for q, r, value in board:
            if value == black:
                blacks.add((int(q), int(r)))
            elif value == white:
                whites.add((int(q), int(r)))
    else:
        for row, values in enumerate(board):
            r = row - 4
            q0 = max(-4, -r - 4)
            for col, value in enumerate(values):
                cell = (q0 + col, r)
                if value == black:
                    blacks.add(cell)
                elif value == white:
                    whites.add(cell)
    return blacks, whites


def _new_board(game: Any, state: Any, blacks: set[tuple[int, int]], whites: set[tuple[int, int]]) -> tuple[str, Any]:
    name, board, black, white, kind = _board_info(game, state)
    if kind == "mapping":
        if set(board) >= set(_valid_cells()):
            result = type(board)(board)
            for cell in _valid_cells():
                result[cell] = None if board.get((0, 0)) is None else board[(0, 0)]
        else:
            result = type(board)()
        for cell in blacks:
            result[cell] = black
        for cell in whites:
            result[cell] = white
        return name, result
    if kind == "triples":
        entry_type = type(board[0])
        entries = [entry_type((q, r, black)) for q, r in sorted(blacks)]
        entries += [entry_type((q, r, white)) for q, r in sorted(whites)]
        return name, tuple(entries) if isinstance(board, tuple) else entries

    rows = []
    empty = board[4][0]
    for row, values in enumerate(board):
        r = row - 4
        q0 = max(-4, -r - 4)
        current = []
        for col in range(len(values)):
            cell = (q0 + col, r)
            current.append(black if cell in blacks else white if cell in whites else empty)
        rows.append(tuple(current) if isinstance(values, tuple) else current)
    return name, tuple(rows) if isinstance(board, tuple) else rows


def _player_value(state: Any, color: str) -> Any:
    name = _field(state, PLAYER_FIELDS)
    current = getattr(state, name)
    if color == "black":
        return current
    if isinstance(current, bool):
        return not current
    if isinstance(current, int):
        return 1 - current
    if isinstance(current, str):
        return "white" if current.casefold() in {"black", "schwarz", "b"} else current
    raise NotImplementedError("cannot infer white current-player value")


def _capture_layout(game: Any, state: Any) -> tuple[str, int]:
    cached = getattr(game, "_boardbench_abalone_capture_layout", None)
    if cached is not None:
        return cached
    for name in ("captures_by_player", "captured_by_player", "scores_by_player"):
        value = getattr(state, name, None)
        if isinstance(value, (list, tuple)) and len(value) == 2:
            result = (name, 0)
            setattr(game, "_boardbench_abalone_capture_layout", result)
            return result

    for name in ("captures", "captured", "ejected", "scores"):
        value = getattr(state, name, None)
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            continue
        board_name, board = _new_board(game, state, {(2, 0), (3, 0)}, {(4, 0)})
        changes: dict[str, Any] = {
            board_name: board,
            name: (0, 0) if isinstance(value, tuple) else [0, 0],
            _field(state, PLAYER_FIELDS): _player_value(state, "black"),
        }
        for winner_name in ("winner", "victor"):
            if hasattr(state, winner_name):
                changes[winner_name] = None
        probe = _with_changes(state, changes)
        matches = [
            action
            for action in game.legal_actions(probe)
            if _matches_move(game, probe, action, {"group": ["2,0", "3,0"], "direction": "E"})
        ]
        if not matches:
            continue
        after = _after(game, probe, matches[0])
        observed = list(getattr(after, name))
        changed = [index for index, amount in enumerate(observed) if int(amount) == 1]
        if len(changed) == 1 and all(int(amount) in {0, 1} for amount in observed):
            result = (name, changed[0])
            setattr(game, "_boardbench_abalone_capture_layout", result)
            return result
    raise NotImplementedError("cannot infer player-indexed capture counts")


def setup(module: Any, game: Any, fixture: dict[str, Any]) -> Any:
    state = game.initial_state()
    blacks = {_coord(cell) for cell in fixture.get("black", [])}
    whites = {_coord(cell) for cell in fixture.get("white", [])}
    if blacks & whites or not (blacks | whites) <= set(_valid_cells()):
        raise NotImplementedError("fixture contains overlapping or off-board marbles")

    board_name, board = _new_board(game, state, blacks, whites)
    changes: dict[str, Any] = {board_name: board}
    player_name = _field(state, PLAYER_FIELDS)
    changes[player_name] = _player_value(state, str(fixture.get("active", "black")))

    for name in ("winner", "victor"):
        if hasattr(state, name):
            changes[name] = None
    wanted_captures = [int(value) for value in fixture.get("captures", [0, 0])]
    if any(wanted_captures):
        capture_field, black_index = _capture_layout(game, state)
        value = getattr(state, capture_field)
        physical = [0, 0]
        physical[black_index] = wanted_captures[0]
        physical[1 - black_index] = wanted_captures[1]
        changes[capture_field] = tuple(physical) if isinstance(value, tuple) else physical

    configured = _with_changes(state, changes)
    try:
        if hasattr(game, "is_terminal") and game.is_terminal(configured):
            raise NotImplementedError("implementation treats sparse evaluator fixture as terminal")
        if hasattr(game, "legal_actions"):
            game.legal_actions(configured)
    except NotImplementedError:
        raise
    except Exception as exc:
        raise NotImplementedError(f"implementation rejects sparse evaluator fixture: {exc}") from exc
    return configured


def _after(game: Any, state: Any, action: Any) -> Any:
    probe = copy.deepcopy(state)
    result = game.apply_action(probe, action)
    return probe if result is None else result


def _matches_move(game: Any, state: Any, action: Any, spec: dict[str, Any]) -> bool:
    before_black, before_white = _positions(game, state)
    color = str(spec.get("color", "black"))
    before = before_black if color == "black" else before_white
    group = {_coord(cell) for cell in spec["group"]}
    dq, dr = DIRECTIONS[str(spec["direction"]).upper()]
    destinations = {(q + dq, r + dr) for q, r in group}
    if not group <= before:
        return False
    after_state = _after(game, state, action)
    after_black, after_white = _positions(game, after_state)
    after = after_black if color == "black" else after_white
    return after == (before - group) | destinations


def resolve_action(module: Any, game: Any, state: Any, actions: list[Any], spec: dict[str, Any]) -> Any:
    matches = [action for action in actions if _matches_move(game, state, action, spec)]
    if not matches:
        raise NotImplementedError("semantic move matched no legal action")
    if len(matches) > 1:
        outcomes = {
            tuple(frozenset(cells) for cells in _positions(game, _after(game, state, action)))
            for action in matches
        }
        if len(outcomes) != 1:
            raise NotImplementedError(f"semantic move matched {len(matches)} different transitions")
    return matches[0]


def check(module: Any, game: Any, state: Any, expected: dict[str, Any]) -> None:
    black, white = _positions(game, state)
    if "marble_counts" in expected:
        actual = {"black": len(black), "white": len(white)}
        wanted = {key: int(value) for key, value in expected["marble_counts"].items()}
        if actual != wanted:
            raise AssertionError(f"marble_counts: expected {wanted}, got {actual}")
    if "captures" in expected:
        field, black_index = _capture_layout(game, game.initial_state())
        physical = [int(value) for value in getattr(state, field)]
        actual = [physical[black_index], physical[1 - black_index]]
        wanted = [int(value) for value in expected["captures"]]
        if actual != wanted:
            raise AssertionError(f"captures: expected {wanted}, got {actual}")
    if "positions" in expected:
        wanted_black = {_coord(cell) for cell in expected["positions"]["black"]}
        wanted_white = {_coord(cell) for cell in expected["positions"]["white"]}
        if (black, white) != (wanted_black, wanted_white):
            raise AssertionError(
                f"positions: expected black={sorted(wanted_black)}, white={sorted(wanted_white)}; "
                f"got black={sorted(black)}, white={sorted(white)}"
            )
    if "occupancy" in expected:
        for raw_cell, color in expected["occupancy"].items():
            cell = _coord(raw_cell)
            actual = "black" if cell in black else "white" if cell in white else "empty"
            if actual != color:
                raise AssertionError(f"occupancy[{raw_cell}]: expected {color}, got {actual}")
    if "move_legal" in expected:
        spec = expected["move_legal"]
        matches = [action for action in game.legal_actions(state) if _matches_move(game, state, action, spec)]
        wanted = bool(spec.get("expected", True))
        if bool(matches) != wanted:
            raise AssertionError(f"move_legal: expected {wanted}, matched {len(matches)} actions")
