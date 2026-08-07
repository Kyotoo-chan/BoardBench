"""Abalone, implemented only from the supplied German rulebook."""
from __future__ import annotations

from typing import Any, NamedTuple, Optional

Coord = tuple[int, int]
DIRS: dict[str, Coord] = {
    "E": (1, 0), "NE": (1, -1), "NW": (0, -1),
    "W": (-1, 0), "SW": (-1, 1), "SE": (0, 1),
}
COLORS = ("black", "white")
STATE_SCHEMA = "boardbench/abalone/state/1"
ACTION_SCHEMA = "boardbench/abalone/action/1"
OBS_SCHEMA = "boardbench/abalone/observation/1"


def _cells() -> tuple[Coord, ...]:
    return tuple((q, r) for r in range(-4, 5) for q in range(-4, 5)
                 if max(abs(q), abs(r), abs(q + r)) <= 4)


CELLS = _cells()
CELL_SET = set(CELLS)


class Action(NamedTuple):
    type: str
    actor: int
    group: tuple[Coord, ...] = ()
    direction: Optional[str] = None


class GameState:
    def __init__(self, configuration: dict[str, Any], board: dict[Coord, Optional[str]],
                 current: int, captures: list[int], terminal: bool,
                 winner: Optional[int], phase: str, move_number: int,
                 pending: None = None, chance: dict[str, Any] | None = None):
        self.configuration = configuration
        self.board = board
        self.current = current
        self.captures = captures
        self.terminal = terminal
        self.winner = winner
        self.phase = phase
        self.move_number = move_number
        self.pending = pending
        self.chance = chance


def _add(a: Coord, b: Coord) -> Coord:
    return a[0] + b[0], a[1] + b[1]


def _sub(a: Coord, b: Coord) -> Coord:
    return a[0] - b[0], a[1] - b[1]


def _coord_name(c: Coord) -> str:
    return f"{c[0]},{c[1]}"


def _parse_coord(text: str) -> Coord:
    parts = text.split(",")
    if len(parts) != 2:
        raise ValueError("invalid coordinate")
    try:
        c = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ValueError("invalid coordinate") from exc
    if _coord_name(c) != text or c not in CELL_SET:
        raise ValueError("invalid coordinate")
    return c


def _line_direction(group: tuple[Coord, ...]) -> Optional[Coord]:
    if len(group) == 1:
        return None
    s = set(group)
    for d in DIRS.values():
        starts = [c for c in group if _sub(c, d) not in s]
        if len(starts) == 1 and all(_add(starts[0], (d[0] * i, d[1] * i)) in s
                                    for i in range(len(group))):
            return d
    return None


class Game:
    def __init__(self, num_players: int | None = None, seed: int | None = None):
        players = 2 if num_players is None else num_players
        if type(players) is not int or players != 2:
            raise ValueError("Abalone supports exactly two players")
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer or None")
        self.num_players = players
        self.seed = seed

    def initial_state(self) -> GameState:
        board = {c: None for c in CELLS}
        black = ({(q, -4) for q in range(0, 5)} |
                 {(q, -3) for q in range(-1, 5)} | {(q, -2) for q in range(0, 3)})
        white = {(-q, -r) for q, r in black}
        for c in black:
            board[c] = "black"
        for c in white:
            board[c] = "white"
        return GameState({"players": 2, "seed": self.seed, "variant": "base"},
                         board, 0, [0, 0], False, None, "play", 0,
                         chance={"seed": self.seed})

    def current_player(self, state: GameState) -> int:
        return state.current

    def is_terminal(self, state: GameState) -> bool:
        return state.terminal

    def returns(self, state: GameState) -> list[int]:
        if not state.terminal or state.winner is None:
            return [0, 0]
        return [1 if i == state.winner else -1 for i in range(2)]

    def _result(self, state: GameState, action: Action):
        if action.type != "move" or action.actor != state.current:
            return None
        group = action.group
        if not (1 <= len(group) <= 3) or len(set(group)) != len(group):
            return None
        color = COLORS[state.current]
        if any(c not in CELL_SET or state.board[c] != color for c in group):
            return None
        axis = _line_direction(group)
        if len(group) > 1 and axis is None:
            return None
        d = DIRS.get(action.direction or "")
        if d is None:
            return None
        inline = axis is not None and (d == axis or d == (-axis[0], -axis[1]))
        if not inline:
            targets = [_add(c, d) for c in group]
            if any(t not in CELL_SET or state.board[t] is not None for t in targets):
                return None
            return targets, (), None

        front = next(c for c in group if _add(c, d) not in set(group))
        cursor = _add(front, d)
        opponents: list[Coord] = []
        other = COLORS[1 - state.current]
        while cursor in CELL_SET and state.board[cursor] == other:
            opponents.append(cursor)
            cursor = _add(cursor, d)
        if not opponents:
            if cursor not in CELL_SET or state.board[cursor] is not None:
                return None
            return tuple(_add(c, d) for c in group), (), None
        if len(opponents) >= len(group) or len(opponents) > 2:
            return None
        if cursor in CELL_SET and state.board[cursor] is not None:
            return None
        pushed_to = tuple(_add(c, d) for c in opponents)
        ejected = opponents[-1] if pushed_to[-1] not in CELL_SET else None
        return tuple(_add(c, d) for c in group), tuple(opponents), ejected

    def legal_actions(self, state: GameState) -> list[Action]:
        if state.terminal:
            return []
        own = [c for c in CELLS if state.board[c] == COLORS[state.current]]
        groups: set[tuple[Coord, ...]] = {(c,) for c in own}
        own_set = set(own)
        for c in own:
            for d in DIRS.values():
                for n in (2, 3):
                    g = tuple(_add(c, (d[0] * i, d[1] * i)) for i in range(n))
                    if all(x in own_set for x in g):
                        groups.add(tuple(sorted(g)))
        actions = [Action("move", state.current, g, name)
                   for g in sorted(groups) for name in DIRS
                   if self._result(state, Action("move", state.current, g, name)) is not None]
        return actions

    def apply_action(self, state: GameState, action: Action) -> GameState:
        result = self._result(state, action)
        if state.terminal or result is None:
            raise ValueError("illegal action")
        targets, opponents, ejected = result
        board = dict(state.board)
        color = COLORS[state.current]
        for c in action.group:
            board[c] = None
        for c in opponents:
            board[c] = None
        for c in targets:
            board[c] = color
        other = COLORS[1 - state.current]
        for c in opponents:
            t = _add(c, DIRS[action.direction or ""])
            if t in CELL_SET:
                board[t] = other
        captures = list(state.captures)
        if ejected is not None:
            captures[state.current] += 1
        terminal = captures[state.current] >= 6
        return GameState(dict(state.configuration), board,
                         state.current if terminal else 1 - state.current,
                         captures, terminal, state.current if terminal else None,
                         "terminal" if terminal else "play", state.move_number + 1,
                         chance=dict(state.chance or {"seed": self.seed}))

    def action_to_name(self, action: Action) -> str:
        if action.type == "pass":
            return f"pass actor={action.actor}"
        return (f"move actor={action.actor} group=" + ";".join(_coord_name(c) for c in action.group)
                + f" direction={action.direction}")

    def name_to_action(self, name: str) -> Action:
        if name.startswith("pass actor="):
            try:
                actor = int(name[11:])
            except ValueError as exc:
                raise ValueError("invalid action name") from exc
            action = Action("pass", actor)
        elif name.startswith("move actor=") and " group=" in name and " direction=" in name:
            head, tail = name.split(" group=", 1)
            group_text, direction = tail.split(" direction=", 1)
            try:
                actor = int(head[11:])
                group = tuple(_parse_coord(x) for x in group_text.split(";"))
            except (ValueError, TypeError) as exc:
                raise ValueError("invalid action name") from exc
            action = Action("move", actor, group, direction)
        else:
            raise ValueError("invalid action name")
        if self.action_to_name(action) != name:
            raise ValueError("non-canonical action name")
        return action

    def state_to_data(self, state: GameState) -> dict[str, Any]:
        data = {"configuration": dict(state.configuration),
                "board": {_coord_name(c): state.board[c] for c in CELLS},
                "current_player": state.current, "captures": list(state.captures),
                "terminal": state.terminal, "winner": state.winner, "phase": state.phase,
                "move_number": state.move_number, "pending": None,
                "chance": dict(state.chance or {})}
        return {"schema": STATE_SCHEMA, "data": data}

    def state_from_data(self, payload: dict) -> GameState:
        self._envelope(payload, STATE_SCHEMA)
        d = payload["data"]
        required = {"configuration", "board", "current_player", "captures", "terminal",
                    "winner", "phase", "move_number", "pending", "chance"}
        if set(d) != required:
            raise ValueError("invalid state fields")
        cfg = d["configuration"]
        if (type(cfg) is not dict or set(cfg) != {"players", "seed", "variant"} or
                type(cfg["players"]) is not int or cfg["players"] != 2 or
                (cfg["seed"] is not None and type(cfg["seed"]) is not int) or cfg["variant"] != "base"):
            raise ValueError("invalid configuration")
        if type(d["board"]) is not dict or set(d["board"]) != {_coord_name(c) for c in CELLS}:
            raise ValueError("invalid board")
        board = {_parse_coord(k): v for k, v in d["board"].items()}
        if any(v not in (None, "black", "white") for v in board.values()):
            raise ValueError("invalid board value")
        if type(d["current_player"]) is not int or d["current_player"] not in (0, 1):
            raise ValueError("invalid current player")
        if (type(d["captures"]) is not list or len(d["captures"]) != 2 or
                any(type(x) is not int or x < 0 for x in d["captures"])):
            raise ValueError("invalid captures")
        if type(d["terminal"]) is not bool or d["winner"] not in (None, 0, 1):
            raise ValueError("invalid terminal fields")
        if d["phase"] not in ("play", "terminal") or type(d["move_number"]) is not int or d["move_number"] < 0:
            raise ValueError("invalid phase or move number")
        if d["pending"] is not None:
            raise ValueError("pending must be null")
        chance = d["chance"]
        if (type(chance) is not dict or set(chance) != {"seed"} or
                (chance["seed"] is not None and type(chance["seed"]) is not int)):
            raise ValueError("invalid chance")
        return GameState(dict(cfg), board, d["current_player"], list(d["captures"]),
                         d["terminal"], d["winner"], d["phase"], d["move_number"],
                         chance=dict(chance))

    def action_to_data(self, action: Action) -> dict[str, Any]:
        if action.type == "move":
            args: dict[str, Any] = {"group": [_coord_name(c) for c in action.group],
                                    "direction": action.direction}
        elif action.type == "pass":
            args = {}
        else:
            raise ValueError("invalid action type")
        return {"schema": ACTION_SCHEMA, "data": {"type": action.type,
                "actor": action.actor, "args": args}}

    def action_from_data(self, payload: dict) -> Action:
        self._envelope(payload, ACTION_SCHEMA)
        d = payload["data"]
        if set(d) != {"type", "actor", "args"} or type(d["actor"]) is not int or d["actor"] not in (0, 1):
            raise ValueError("invalid action fields")
        if d["type"] == "pass" and type(d["args"]) is dict and not d["args"]:
            return Action("pass", d["actor"])
        if d["type"] != "move" or type(d["args"]) is not dict or set(d["args"]) != {"group", "direction"}:
            raise ValueError("invalid action")
        a = d["args"]
        if (type(a["group"]) is not list or not 1 <= len(a["group"]) <= 3 or
                any(type(x) is not str for x in a["group"]) or a["direction"] not in DIRS):
            raise ValueError("invalid move arguments")
        group = tuple(_parse_coord(x) for x in a["group"])
        if len(set(group)) != len(group):
            raise ValueError("duplicate group coordinate")
        return Action("move", d["actor"], group, a["direction"])

    def observation_to_data(self, state: GameState, player: int) -> dict[str, Any]:
        if type(player) is not int or player not in (0, 1):
            raise ValueError("invalid player")
        d = self.state_to_data(state)["data"]
        obs = {k: d[k] for k in ("board", "current_player", "captures", "terminal",
                                  "winner", "phase", "move_number")}
        obs["player"] = player
        return {"schema": OBS_SCHEMA, "data": obs}

    @staticmethod
    def _envelope(payload: Any, schema: str) -> None:
        if type(payload) is not dict or set(payload) != {"schema", "data"} or payload.get("schema") != schema or type(payload.get("data")) is not dict:
            raise ValueError("invalid canonical envelope")

    def render(self, state: GameState) -> str:
        rows = []
        glyph = {None: ".", "black": "B", "white": "W"}
        for r in range(-4, 5):
            row = [glyph[state.board[(q, r)]] for q in range(-4, 5) if (q, r) in CELL_SET]
            rows.append(" " * abs(r) + " ".join(row))
        return (f"Abalone move {state.move_number}; player {state.current} "
                f"({COLORS[state.current]}); captures {state.captures}\n" + "\n".join(rows))
